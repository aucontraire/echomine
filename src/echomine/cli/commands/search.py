"""Search command implementation.

This module implements the 'search' command for searching conversations
by keywords with BM25 relevance ranking.

Constitution Compliance:
    - Principle I: Library-first (delegates to OpenAIAdapter.search)
    - CHK031: Data on stdout, progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (user error), 2 (invalid arguments)
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

    Output Streams:
        stdout: Search results (formatted as table or JSON)
        stderr: Progress indicators (unless --quiet), error messages
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Optional

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
        Optional[list[str]],
        typer.Option(
            "--keywords",
            "-k",
            help="Keywords to search for (can specify multiple)",
        ),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option(
            "--title",
            "-t",
            help="Filter by title (case-insensitive substring)",
        ),
    ] = None,
    from_date: Annotated[
        Optional[str],
        typer.Option(
            "--from-date",
            help="Filter from date (YYYY-MM-DD)",
        ),
    ] = None,
    to_date: Annotated[
        Optional[str],
        typer.Option(
            "--to-date",
            help="Filter to date (YYYY-MM-DD)",
        ),
    ] = None,
    limit: Annotated[
        Optional[int],
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

    Requirements:
        - FR-291-292: stdout for results, stderr for progress/errors
        - FR-296-299: Exit codes 0/1/2
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
        parsed_from_date: Optional[date] = None
        parsed_to_date: Optional[date] = None

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
        processed_keywords: Optional[list[str]] = None
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

        # Search conversations
        adapter = OpenAIAdapter()
        results = list(
            adapter.search(
                file_path,
                query,
                progress_callback=progress_callback if not quiet else None,
            )
        )

        # Apply actual limit if specified and different from query limit
        if limit is not None:
            results = results[:limit]

        # Format output based on requested format
        if format_lower == "json":
            output = format_search_results_json(results)
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
