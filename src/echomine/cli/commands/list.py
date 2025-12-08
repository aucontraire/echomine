"""List command implementation.

This module implements the 'list' command for listing all conversations
from an OpenAI export file.

Constitution Compliance:
    - Principle I: Library-first (delegates to OpenAIAdapter)
    - CHK031: Data on stdout, progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (user error), 2 (invalid arguments)
    - FR-018: Human-readable output by default
    - FR-019: Pipeline-friendly output

Command Contract:
    Usage: echomine list <file_path> [--format FORMAT]

    Arguments:
        file_path: Path to OpenAI export JSON file

    Options:
        --format: Output format ('text' or 'json', default: 'text')

    Exit Codes:
        0: Success
        1: File not found, permission denied, invalid JSON, validation error
        2: Invalid arguments (Typer handles this automatically)

    Output Streams:
        stdout: Conversation data (formatted as table or JSON)
        stderr: Error messages (no progress indicators for Phase 3)
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.console import Console

from echomine.adapters.openai import OpenAIAdapter
from echomine.cli.formatters import (
    create_rich_table,
    format_json,
    format_text_table,
    is_rich_enabled,
)
from echomine.exceptions import ParseError, ValidationError
from echomine.export.csv import CSVExporter
from echomine.models.conversation import Conversation


def list_conversations(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to OpenAI export file",
            exists=False,  # We handle existence and readability checks manually
            file_okay=True,
            dir_okay=False,
            readable=False,  # We handle permission errors manually for exit code 1
            resolve_path=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            help="Output format (text or json)",
            case_sensitive=False,
        ),
    ] = "text",
    limit: Annotated[
        int | None,
        typer.Option(
            help="Restrict output to the top N most recent conversations",
            min=1,
        ),
    ] = None,
    sort: Annotated[
        str,
        typer.Option(
            "--sort",
            help="Sort by: date (default), title, or messages",
            case_sensitive=False,
        ),
    ] = "date",
    order: Annotated[
        str,
        typer.Option(
            "--order",
            help="Sort order: asc or desc (default varies by field)",
            case_sensitive=False,
        ),
    ] = "",
) -> None:
    """[bold]List all conversations[/bold] from export file.

    Streams conversations from the export file and outputs them to stdout
    in either human-readable text table format or machine-readable JSON.

    [bold]Examples:[/bold]
        [dim]# List conversations in text table format (default)[/dim]
        $ [green]echomine list[/green] export.json

        [dim]# List conversations in JSON format[/dim]
        $ [green]echomine list[/green] export.json [cyan]--format[/cyan] json

        [dim]# Sort by title ascending[/dim]
        $ [green]echomine list[/green] export.json [cyan]--sort[/cyan] title [cyan]--order[/cyan] asc

        [dim]# Limit to top 10 most recent[/dim]
        $ [green]echomine list[/green] export.json [cyan]--limit[/cyan] 10

        [dim]# Pipeline with grep[/dim]
        $ [green]echomine list[/green] export.json | grep "Python"

        [dim]# Pipeline with jq[/dim]
        $ [green]echomine list[/green] export.json [cyan]--format[/cyan] json | jq '.[0].title'

    [bold]Exit Codes:[/bold]
        [green]0[/green]: Success
        [red]1[/red]: File not found, permission denied, parse error, validation error
        [yellow]2[/yellow]: Invalid arguments (handled by Typer)
    """
    # Validate limit parameter (for direct calls bypassing Typer CLI validation)
    # Must be outside try block to avoid being caught by Exception handler
    if limit is not None and limit < 1:
        typer.echo(
            f"Error: limit must be greater than 0, got {limit}",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        # Validate format option
        format_lower = format.lower()
        if format_lower not in ("text", "json", "csv"):
            typer.echo(
                f"Error: Invalid format '{format}'. Must be 'text', 'json', or 'csv'.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate sort option (FR-048a)
        sort_lower = sort.lower()
        if sort_lower not in ("date", "title", "messages"):
            typer.echo(
                f"Error: Invalid --sort '{sort}'. Must be 'date', 'title', or 'messages'.",
                err=True,
            )
            raise typer.Exit(code=2)

        # Determine default sort order based on field (FR-048c)
        # date=desc (newest first), title=asc (A-Z), messages=desc (largest first)
        order_lower = ("asc" if sort_lower == "title" else "desc") if order == "" else order.lower()

        # Validate order option
        if order_lower not in ("asc", "desc"):
            typer.echo(
                f"Error: Invalid --order '{order}'. Must be 'asc' or 'desc'.",
                err=True,
            )
            raise typer.Exit(code=2)

        # Check file exists (manual check for better error message)
        if not file_path.exists():
            typer.echo(
                f"Error: File not found: {file_path}",
                err=True,
            )
            raise typer.Exit(code=1)

        # Stream conversations from file
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file_path))

        # Sort conversations based on parameters (FR-048a-c)
        def get_list_sort_key(conv: Conversation) -> tuple[float | str | int, str]:
            """Get sort key for list command.

            Returns tuple for multi-level sorting:
            - Primary: sort field value
            - Secondary: conversation_id (tie-breaker)

            FR-046a: For date sort, use updated_at or fall back to created_at
            FR-047: Title sort is case-insensitive
            """
            if sort_lower == "date":
                # Use updated_at if present, otherwise created_at
                sort_date = conv.updated_at if conv.updated_at is not None else conv.created_at
                primary_key: float | str | int = sort_date.timestamp()
            elif sort_lower == "title":
                # Case-insensitive title sort
                primary_key = conv.title.lower()
            elif sort_lower == "messages":
                # Sort by message count
                primary_key = conv.message_count
            else:
                # Should never happen due to validation above, but defensive
                primary_key = conv.created_at.timestamp()

            # Tie-breaking by conversation_id (ascending)
            return (primary_key, conv.id)

        # Apply sorting
        reverse_sort = order_lower == "desc"
        conversations.sort(key=get_list_sort_key, reverse=reverse_sort)

        # Apply limit if specified (FR-443)
        if limit is not None:
            conversations = conversations[:limit]

        # Format output based on requested format
        if format_lower == "csv":
            # Conversation-level CSV output (FR-049, FR-050)
            exporter = CSVExporter()
            output = exporter.export_conversations(conversations)
            typer.echo(output, nl=False)
        elif format_lower == "json":
            output = format_json(conversations)
            # Write JSON output to stdout (CHK031)
            typer.echo(output, nl=False)
        else:
            # Check if Rich formatting should be used (FR-036, FR-040, FR-041)
            use_rich = is_rich_enabled(json_flag=False)

            if use_rich:
                # Rich table output (FR-036)
                table = create_rich_table(conversations)
                console = Console()
                console.print(table)
            else:
                # Plain text table output (default for pipes/redirects)
                output = format_text_table(conversations)
                typer.echo(output, nl=False)

        # Return normally for success (exit code 0)
        # Don't raise typer.Exit for success case
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

    except Exception as e:
        # Unexpected error (catch-all for safety)
        typer.echo(
            f"Error: {e}",
            err=True,
        )
        raise typer.Exit(code=1)
