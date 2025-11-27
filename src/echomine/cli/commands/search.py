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
from typing import Annotated

import typer
from pydantic import ValidationError as PydanticValidationError

from echomine.adapters.openai import OpenAIAdapter
from echomine.cli.formatters import format_search_results, format_search_results_json
from echomine.exceptions import ParseError, ValidationError
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
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            help="Limit number of results",
        ),
    ] = None,
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
) -> None:
    """Search conversations by keywords with BM25 relevance ranking.

    Examples:
        # Search for Python-related conversations
        echomine search export.json --keywords python

        # Multiple keywords (OR logic)
        echomine search export.json -k python -k async -k tutorial

        # Title filter
        echomine search export.json -k python --title "best practices"

        # Date range
        echomine search export.json -k python --from-date 2024-01-01 --to-date 2024-12-31

        # Limit results
        echomine search export.json -k python --limit 10

        # JSON output
        echomine search export.json -k python --format json

    Args:
        file_path: Path to OpenAI export JSON file
        keywords: Keywords for full-text search (OR logic)
        title: Partial title match filter
        from_date: Start date filter (inclusive)
        to_date: End date filter (inclusive)
        limit: Maximum results to return
        format: Output format ('text' or 'json')
        quiet: Suppress progress indicators
        json: Output in JSON format (alias for --format json)

    Exit Codes:
        0: Success (including zero results)
        1: File not found, permission denied, parse error
        2: Invalid arguments
        130: User interrupt (Ctrl+C)

    Requirements:
        - FR-291-292: stdout for results, stderr for progress/errors
        - FR-296-299: Exit codes 0/1/2/130
        - FR-301-306: JSON output schema
        - FR-310: --quiet flag suppresses progress
        - CHK031: stdout/stderr separation
        - CHK032: Proper exit codes
    """
    try:
        # Validate format option
        format_lower = format.lower()

        # Handle --json flag as alias for --format json
        if json:
            format_lower = "json"

        if format_lower not in ("text", "json"):
            typer.echo(
                f"Error: Invalid format '{format}'. Must be 'text' or 'json'.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate: at least one of keywords or title must be provided (FR-298)
        if not keywords and not title:
            typer.echo(
                "Error: At least one of --keywords or --title must be specified",
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
                title_filter=title,
                from_date=parsed_from_date,
                to_date=parsed_to_date,
                limit=query_limit,
            )
        except PydanticValidationError as e:
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
        if format_lower == "json":
            # FR-301-306: Pass metadata to JSON formatter
            # Convert dates to ISO 8601 format for metadata
            query_from_date_str = (
                parsed_from_date.strftime("%Y-%m-%d") if parsed_from_date else None
            )
            query_to_date_str = parsed_to_date.strftime("%Y-%m-%d") if parsed_to_date else None

            output = format_search_results_json(
                results,
                query_keywords=processed_keywords,
                query_title_filter=title,
                query_from_date=query_from_date_str,
                query_to_date=query_to_date_str,
                query_limit=limit if limit is not None else query_limit,
                total_results=len(results),
                skipped_conversations=0,  # TODO: Track skipped conversations in adapter
                elapsed_seconds=elapsed_seconds,
            )
        else:
            output = format_search_results(results)

        # Write output to stdout (CHK031)
        # Use nl=False to avoid extra newline (formatters include trailing newline)
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
        # Permission denied when trying to read file
        typer.echo(
            f"Error: Permission denied: {file_path}",
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
