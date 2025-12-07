"""Search command implementation.

This module implements the 'search' command for searching conversations
by keywords with BM25 relevance ranking.

Constitution Compliance:
    - Principle I: Library-first (delegates to OpenAIAdapter.search)
    - CHK031: Data on stdout, progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (error), 2 (invalid args), 130 (interrupt)
    - FR-291-292: stdout/stderr separation
    - FR-296-299: Exit code specification

Command Contract:
    Usage: echomine search <file_path> [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file

    Options:
        --keywords, -k TEXT: Keywords to search for (can specify multiple)
        --title, -t TEXT: Filter by title (case-insensitive substring)
        --from-date DATE: Filter from date (YYYY-MM-DD format)
        --to-date DATE: Filter to date (YYYY-MM-DD format)
        --limit, -n INTEGER: Limit number of results (default: None/unlimited)
        --format, -f [text|json]: Output format (default: text)
        --quiet, -q: Suppress progress indicators

    Exit Codes:
        0: Success (including zero results)
        1: File not found, permission denied, parse error
        2: Invalid arguments (no filters, invalid date range, etc.)
        130: User interrupt (Ctrl+C)

    Output Streams:
        stdout: Search results (formatted as table or JSON)
        stderr: Progress indicators (unless --quiet), error messages
"""

from __future__ import annotations

import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Literal, cast

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.console import Console

from echomine.adapters.openai import OpenAIAdapter
from echomine.cli.formatters import (
    create_rich_search_table,
    format_search_results,
    format_search_results_json,
    is_rich_enabled,
)
from echomine.exceptions import ParseError, ValidationError
from echomine.export.csv import CSVExporter
from echomine.models.search import SearchQuery


def parse_date(value: str) -> date:
    """Parse date string in YYYY-MM-DD format.

    Args:
        value: Date string in YYYY-MM-DD format

    Returns:
        date object

    Raises:
        ValueError: If date string is invalid
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}") from e


def _build_search_suggestions(
    keywords: list[str] | None,
    title_filter: str | None,
    from_date: date | None,
    to_date: date | None,
) -> list[str]:
    """Build actionable suggestions for zero search results.

    Args:
        keywords: Search keywords that returned no results
        title_filter: Title filter that returned no results
        from_date: From date filter
        to_date: To date filter

    Returns:
        List of suggestion strings for stderr output
    """
    suggestions = []

    if keywords:
        suggestions.append(
            f"Try broader or alternate keywords: echomine search <file> -k {keywords[0]}"
        )

    if title_filter:
        suggestions.append(
            f'Try a partial title match: echomine search <file> -t "{title_filter.split()[0]}"'
        )

    if from_date or to_date:
        suggestions.append("Try expanding the date range or removing date filters")

    # Always suggest listing all conversations
    suggestions.append("List all conversations to verify file contents: echomine list <file>")

    return suggestions


def search_conversations(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to conversation export file",
            exists=False,  # Manual check for exit code 1
            file_okay=True,
            dir_okay=False,
            readable=False,  # Manual check for exit code 1
            resolve_path=True,
        ),
    ],
    keywords: Annotated[
        list[str] | None,
        typer.Option(
            "--keywords",
            "-k",
            help="Keywords to search for (can specify multiple)",
        ),
    ] = None,
    phrase: Annotated[
        list[str] | None,
        typer.Option(
            "--phrase",
            help="Exact phrase to match (case-insensitive, can specify multiple)",
        ),
    ] = None,
    match_mode: Annotated[
        str,
        typer.Option(
            "--match-mode",
            help="Keyword matching mode: 'any' (OR, default) or 'all' (AND)",
            case_sensitive=False,
        ),
    ] = "any",
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            help="Keywords to exclude from results (can specify multiple)",
        ),
    ] = None,
    role: Annotated[
        str | None,
        typer.Option(
            "--role",
            help="Filter to messages from specific role (user, assistant, system)",
            case_sensitive=False,
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            "-t",
            help="Filter by title (case-insensitive substring)",
        ),
    ] = None,
    from_date: Annotated[
        str | None,
        typer.Option(
            "--from-date",
            help="Filter from date (YYYY-MM-DD)",
        ),
    ] = None,
    to_date: Annotated[
        str | None,
        typer.Option(
            "--to-date",
            help="Filter to date (YYYY-MM-DD)",
        ),
    ] = None,
    min_messages: Annotated[
        int | None,
        typer.Option(
            "--min-messages",
            help="Minimum message count (inclusive, must be >= 1)",
        ),
    ] = None,
    max_messages: Annotated[
        int | None,
        typer.Option(
            "--max-messages",
            help="Maximum message count (inclusive, must be >= 1)",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            help="Limit number of results",
        ),
    ] = None,
    sort: Annotated[
        str,
        typer.Option(
            "--sort",
            help="Sort by: score (default), date, title, or messages",
            case_sensitive=False,
        ),
    ] = "score",
    order: Annotated[
        str,
        typer.Option(
            "--order",
            help="Sort order: asc or desc (default: desc)",
            case_sensitive=False,
        ),
    ] = "desc",
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (text or json)",
            case_sensitive=False,
        ),
    ] = "text",
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress progress indicators",
        ),
    ] = False,
    json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output in JSON format (alias for --format json)",
        ),
    ] = False,
    csv_messages: Annotated[
        bool,
        typer.Option(
            "--csv-messages",
            help="Output message-level CSV (mutually exclusive with --format csv)",
        ),
    ] = False,
) -> None:
    """[bold]Search conversations[/bold] by keywords with BM25 relevance ranking.

    [bold]Filter Logic:[/bold]
        Stage 1 (Content Matching - OR): Phrases OR Keywords
          - [cyan]--phrase[/cyan]: Match ANY phrase (exact, case-insensitive)
          - [cyan]--keywords[/cyan]: Match according to [cyan]--match-mode[/cyan]
            * [cyan]--match-mode any[/cyan] (default): Match ANY keyword
            * [cyan]--match-mode all[/cyan]: Match ALL keywords

        Stage 2 (Post-Filtering - AND): All must match
          - [cyan]--exclude[/cyan]: Remove if ANY excluded term found
          - [cyan]--role[/cyan]: Only search specified role's messages
          - [cyan]--title[/cyan]: Only include matching titles
          - [cyan]--from-date[/cyan]/[cyan]--to-date[/cyan]: Date range filter

    [bold]Examples:[/bold]
        [dim]# Phrase OR keyword[/dim]
        $ [green]echomine search[/green] export.json [cyan]--phrase[/cyan] "api" [cyan]-k[/cyan] python

        [dim]# Multiple keywords (ALL required)[/dim]
        $ [green]echomine search[/green] export.json [cyan]-k[/cyan] python [cyan]-k[/cyan] async [cyan]--match-mode[/cyan] all

        [dim]# Content matching + exclusion[/dim]
        $ [green]echomine search[/green] export.json [cyan]--phrase[/cyan] "api" [cyan]-k[/cyan] python [cyan]--exclude[/cyan] java

        [dim]# Role-specific search[/dim]
        $ [green]echomine search[/green] export.json [cyan]-k[/cyan] python [cyan]--role[/cyan] user

        [dim]# Complex combination[/dim]
        $ [green]echomine search[/green] export.json [cyan]--phrase[/cyan] "tutorial" [cyan]-k[/cyan] python [cyan]-t[/cyan] "Guide" [cyan]--exclude[/cyan] test

        [dim]# Date range[/dim]
        $ [green]echomine search[/green] export.json [cyan]-k[/cyan] python [cyan]--from-date[/cyan] 2024-01-01 [cyan]--to-date[/cyan] 2024-12-31

        [dim]# JSON output[/dim]
        $ [green]echomine search[/green] export.json [cyan]-k[/cyan] python [cyan]--format[/cyan] json

    [bold]Exit Codes:[/bold]
        [green]0[/green]: Success (including zero results)
        [red]1[/red]: File not found, permission denied, parse error
        [yellow]2[/yellow]: Invalid arguments
        130: User interrupt (Ctrl+C)
    """
    try:
        # Validate format option
        format_lower = format.lower()

        # Handle --json flag as alias for --format json
        if json:
            format_lower = "json"

        # Validate mutual exclusion of --format csv and --csv-messages (FR-051a)
        if format_lower == "csv" and csv_messages:
            typer.echo(
                "Error: --format csv and --csv-messages are mutually exclusive. "
                "Use --format csv for conversation-level or --csv-messages for message-level export.",
                err=True,
            )
            raise typer.Exit(code=2)

        if format_lower not in ("text", "json", "csv"):
            typer.echo(
                f"Error: Invalid format '{format}'. Must be 'text', 'json', or 'csv'.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate match_mode option (FR-007)
        match_mode_lower = match_mode.lower()
        if match_mode_lower not in ("any", "all"):
            typer.echo(
                f"Error: Invalid --match-mode '{match_mode}'. Must be 'any' or 'all'.",
                err=True,
            )
            raise typer.Exit(code=2)

        # Validate role option (FR-017)
        role_filter_value: Literal["user", "assistant", "system"] | None = None
        if role is not None:
            role_lower = role.lower()
            if role_lower not in ("user", "assistant", "system"):
                typer.echo(
                    f"Error: Invalid --role '{role}'. Must be 'user', 'assistant', or 'system'.",
                    err=True,
                )
                raise typer.Exit(code=2)
            role_filter_value = cast(Literal["user", "assistant", "system"], role_lower)

        # Validate: at least one filter must be provided (FR-298, FR-009)
        # Accept keywords, phrase, title, or date filters (from_date/to_date)
        if not keywords and not phrase and not title and not from_date and not to_date:
            typer.echo(
                "Error: At least one filter must be specified (--keywords, --phrase, --title, --from-date, or --to-date)",
                err=True,
            )
            raise typer.Exit(code=2)

        # Validate: limit must be positive if specified
        if limit is not None and limit <= 0:
            typer.echo(
                f"Error: --limit must be positive, got {limit}",
                err=True,
            )
            raise typer.Exit(code=2)

        # Validate sort option (FR-043)
        sort_lower = sort.lower()
        if sort_lower not in ("score", "date", "title", "messages"):
            typer.echo(
                f"Error: Invalid --sort '{sort}'. Must be 'score', 'date', 'title', or 'messages'.",
                err=True,
            )
            raise typer.Exit(code=2)

        # Validate order option (FR-044)
        order_lower = order.lower()
        if order_lower not in ("asc", "desc"):
            typer.echo(
                f"Error: Invalid --order '{order}'. Must be 'asc' or 'desc'.",
                err=True,
            )
            raise typer.Exit(code=2)

        # Parse date strings to date objects
        parsed_from_date: date | None = None
        parsed_to_date: date | None = None

        if from_date is not None:
            try:
                parsed_from_date = parse_date(from_date)
            except ValueError as e:
                typer.echo(
                    f"Error: Invalid --from-date: {e}",
                    err=True,
                )
                raise typer.Exit(code=2)

        if to_date is not None:
            try:
                parsed_to_date = parse_date(to_date)
            except ValueError as e:
                typer.echo(
                    f"Error: Invalid --to-date: {e}",
                    err=True,
                )
                raise typer.Exit(code=2)

        # Validate: date range (from_date <= to_date)
        if parsed_from_date is not None and parsed_to_date is not None:
            if parsed_from_date > parsed_to_date:
                typer.echo(
                    f"Error: --from-date ({parsed_from_date}) must be <= --to-date ({parsed_to_date})",
                    err=True,
                )
                raise typer.Exit(code=2)

        # Check file exists (manual check for exit code 1)
        if not file_path.exists():
            typer.echo(
                f"Error: File not found: {file_path}",
                err=True,
            )
            raise typer.Exit(code=1)

        # Build SearchQuery (with default limit handling)
        # If limit not specified, use large default for SearchQuery validation
        query_limit = limit if limit is not None else 1000

        # Handle comma-separated keywords (--keywords "alpha,beta")
        processed_keywords: list[str] | None = None
        if keywords:
            processed_keywords = []
            for kw in keywords:
                # Split on commas and strip whitespace
                parts = [part.strip() for part in kw.split(",")]
                processed_keywords.extend(parts)

        try:
            query = SearchQuery(
                keywords=processed_keywords,
                phrases=phrase,  # Pass phrases to SearchQuery (FR-001)
                match_mode=cast(Literal["all", "any"], match_mode_lower),  # FR-007
                exclude_keywords=exclude,  # FR-012: Pass exclude keywords
                role_filter=role_filter_value,  # FR-017: Pass role filter
                title_filter=title,
                from_date=parsed_from_date,
                to_date=parsed_to_date,
                min_messages=min_messages,  # v1.2.0: Message count filtering (T033)
                max_messages=max_messages,  # v1.2.0: Message count filtering (T034)
                limit=query_limit,
                sort_by=cast(Literal["score", "date", "title", "messages"], sort_lower),  # FR-043
                sort_order=cast(Literal["asc", "desc"], order_lower),  # FR-044
            )
        except PydanticValidationError as e:
            # T035: Handle invalid bounds (min > max) with proper error message
            # Extract validation error message for user-friendly output
            error_msg = str(e)
            # Check if it's the min/max validation error
            if "min_messages" in error_msg and "max_messages" in error_msg:
                # Extract the specific validation error message
                # Pydantic v2 error format includes the message in errors
                if hasattr(e, "errors"):
                    errors = e.errors()
                    for error in errors:
                        if error.get("type") == "value_error":
                            typer.echo(
                                f"Error: {error['msg']}",
                                err=True,
                            )
                            raise typer.Exit(code=2)
            # Fallback for other validation errors
            typer.echo(
                f"Error: Invalid search parameters: {e}",
                err=True,
            )
            raise typer.Exit(code=2)

        # Progress callback (only if not quiet)
        def progress_callback(count: int) -> None:
            if not quiet:
                typer.echo(
                    f"Searching... processed {count} conversations",
                    err=True,
                )

        # Track execution time (FR-303)
        start_time = time.time()

        # Search conversations
        adapter = OpenAIAdapter()
        results = list(
            adapter.search(
                file_path,
                query,
                progress_callback=progress_callback if not quiet else None,
            )
        )

        # Calculate elapsed time
        elapsed_seconds = time.time() - start_time

        # Apply actual limit if specified and different from query limit
        if limit is not None:
            results = results[:limit]

        # Provide zero-results guidance if no matches (FR-097, TTY-aware)
        if len(results) == 0 and sys.stderr.isatty():
            typer.echo(
                "No conversations matched your search criteria.",
                err=True,
            )
            typer.echo("", err=True)  # Blank line for readability
            typer.echo("Suggestions:", err=True)

            suggestions = _build_search_suggestions(
                keywords=processed_keywords,
                title_filter=title,
                from_date=parsed_from_date,
                to_date=parsed_to_date,
            )

            for suggestion in suggestions:
                typer.echo(f"  - {suggestion}", err=True)

            typer.echo("", err=True)  # Blank line for readability

        # Format output based on requested format
        if csv_messages:
            # Message-level CSV output (FR-051, FR-052)
            exporter = CSVExporter()
            output = exporter.export_messages_from_results(results)
            typer.echo(output, nl=False)
        elif format_lower == "csv":
            # Conversation-level CSV output with scores (FR-049, FR-050)
            exporter = CSVExporter()
            output = exporter.export_search_results(results)
            typer.echo(output, nl=False)
        elif format_lower == "json":
            # FR-301-306: Pass metadata to JSON formatter
            # Convert dates to ISO 8601 format for metadata
            query_from_date_str = (
                parsed_from_date.strftime("%Y-%m-%d") if parsed_from_date else None
            )
            query_to_date_str = parsed_to_date.strftime("%Y-%m-%d") if parsed_to_date else None

            output = format_search_results_json(
                results,
                query_keywords=processed_keywords,
                query_phrases=phrase,  # v1.1.0: Pass phrases to JSON output (T019)
                query_match_mode=match_mode_lower,  # v1.1.0: Pass match mode (T028)
                query_exclude_keywords=exclude,  # v1.1.0: Pass exclude keywords (T037)
                query_role_filter=role_filter_value,  # v1.1.0: Pass role filter (T045)
                query_title_filter=title,
                query_from_date=query_from_date_str,
                query_to_date=query_to_date_str,
                query_limit=limit if limit is not None else query_limit,
                total_results=len(results),
                skipped_conversations=0,  # TODO: Track skipped conversations in adapter
                elapsed_seconds=elapsed_seconds,
            )
            # Write JSON output to stdout (CHK031)
            typer.echo(output, nl=False)
        else:
            # Check if Rich formatting should be used (FR-036, FR-040, FR-041)
            use_rich = is_rich_enabled(json_flag=False)

            if use_rich:
                # Rich table output with colored scores (FR-036, FR-037)
                table = create_rich_search_table(results)
                console = Console()
                console.print(table)
            else:
                # Plain text table output (default for pipes/redirects)
                output = format_search_results(results)
                typer.echo(output, nl=False)

        # Return normally for success (exit code 0)
        return

    except FileNotFoundError:
        # File doesn't exist (shouldn't reach here due to manual check, but defensive)
        typer.echo(
            f"Error: File not found: {file_path}",
            err=True,
        )
        raise typer.Exit(code=1)

    except PermissionError:
        # Permission denied when trying to read file (FR-061)
        typer.echo(
            f"Error: Permission denied: {file_path}. Check file read permissions.",
            err=True,
        )
        raise typer.Exit(code=1)

    except ParseError as e:
        # Invalid JSON syntax or malformed export structure
        typer.echo(
            f"Error: Invalid JSON in export file: {e}",
            err=True,
        )
        raise typer.Exit(code=1)

    except (ValidationError, PydanticValidationError) as e:
        # Schema violation (missing fields, wrong types, etc.)
        typer.echo(
            f"Error: Validation failed: {e}",
            err=True,
        )
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        # User interrupted with Ctrl+C (FR-299)
        typer.echo(
            "\nInterrupted by user",
            err=True,
        )
        raise typer.Exit(code=130)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        # This ensures validation errors (exit code 2) are not converted to exit code 1
        raise

    except Exception as e:
        # Unexpected error (catch-all for safety)
        typer.echo(
            f"Error: {e}",
            err=True,
        )
        raise typer.Exit(code=1)
