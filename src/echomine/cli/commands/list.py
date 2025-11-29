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

from echomine.adapters.openai import OpenAIAdapter
from echomine.cli.formatters import format_json, format_text_table
from echomine.exceptions import ParseError, ValidationError


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
) -> None:
    """List all conversations from export file.

    Streams conversations from the export file and outputs them to stdout
    in either human-readable text table format or machine-readable JSON.

    Examples:
        # List conversations in text table format (default)
        $ echomine list export.json

        # List conversations in JSON format
        $ echomine list export.json --format json

        # Pipeline with grep
        $ echomine list export.json | grep "Python"

        # Pipeline with jq
        $ echomine list export.json --format json | jq '.[0].title'

    Args:
        file_path: Path to OpenAI export JSON file
        format: Output format ('text' or 'json')

    Exit Codes:
        0: Success
        1: File not found, permission denied, parse error, validation error
        2: Invalid arguments (handled by Typer)

    Requirements:
        - CHK031: Data to stdout, errors to stderr
        - CHK032: Exit codes 0/1/2
        - FR-018: Human-readable output
        - FR-019: Pipeline-friendly
    """
    try:
        # Validate format option
        format_lower = format.lower()
        if format_lower not in ("text", "json"):
            typer.echo(
                f"Error: Invalid format '{format}'. Must be 'text' or 'json'.",
                err=True,
            )
            raise typer.Exit(code=1)

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

        # Sort by created_at descending (newest first) per FR-440
        conversations.sort(key=lambda c: c.created_at, reverse=True)

        # Format output based on requested format
        if format_lower == "json":
            output = format_json(conversations)
        else:
            output = format_text_table(conversations)

        # Write output to stdout (CHK031)
        # Use nl=False to avoid extra newline (formatters include trailing newline)
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

    except Exception as e:
        # Unexpected error (catch-all for safety)
        typer.echo(
            f"Error: {e}",
            err=True,
        )
        raise typer.Exit(code=1)
