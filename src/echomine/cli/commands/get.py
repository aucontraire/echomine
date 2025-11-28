"""Get command implementation.

This module implements the 'get' command for retrieving and displaying
a specific conversation by ID with metadata details.

Constitution Compliance:
    - Principle I: Library-first (delegates to OpenAIAdapter.get_conversation_by_id)
    - CHK031: Data on stdout (table/json), progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (error), 2 (invalid arguments)
    - FR-155: get_conversation_by_id returns Conversation | None

Command Contract:
    Usage: echomine get <file_path> <conversation_id> [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file
        conversation_id: Conversation ID to retrieve

    Options:
        --format, -f: Output format (table, json) [default: table]
        --verbose, -v: Show full message content (not just counts)

    Exit Codes:
        0: Success (conversation found)
        1: File not found, conversation not found, permission denied, parse error
        2: Invalid arguments

    Output Streams:
        stdout: Conversation details (formatted as table or JSON)
        stderr: Error messages
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Annotated, Literal

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.console import Console

from echomine.adapters.openai import OpenAIAdapter
from echomine.exceptions import ParseError
from echomine.models.conversation import Conversation


# Console for stderr output (errors only)
console = Console(stderr=True)


def _format_conversation_table(conversation: Conversation, verbose: bool = False) -> str:
    """Format conversation as human-readable table.

    Args:
        conversation: Conversation object to format
        verbose: Show full message content (not just counts)

    Returns:
        Formatted text output with conversation details

    Example Output:
        Conversation Details
        ═══════════════════════════════════════════════
        ID:          abc-123-def
        Title:       Python Async Programming Tips
        Created:     2024-03-15 14:30:22 UTC
        Updated:     2024-03-15 16:45:10 UTC
        Messages:    25 messages

        Message Summary:
        ─────────────────────────────────────────────
        Role         Count
        ─────────────────────────────────────────────
        user           12
        assistant      13
    """
    lines = []

    # Header
    lines.append("Conversation Details")
    lines.append("═" * 47)

    # Basic metadata
    lines.append(f"ID:          {conversation.id}")
    lines.append(f"Title:       {conversation.title}")
    lines.append(f"Created:     {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Updated timestamp (use updated_at_or_created to handle None)
    updated_str = conversation.updated_at_or_created.strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"Updated:     {updated_str} UTC")

    lines.append(f"Messages:    {conversation.message_count} messages")

    # Message summary by role
    lines.append("")
    lines.append("Message Summary:")
    lines.append("─" * 47)

    # Count messages by role
    role_counts = Counter(msg.role for msg in conversation.messages)

    # Simple text table for consistency with list command
    lines.append(f"{'Role':<15} {'Count':>10}")
    lines.append("─" * 47)

    # Type the role list explicitly for mypy --strict
    roles: tuple[Literal["user"], Literal["assistant"], Literal["system"]] = (
        "user",
        "assistant",
        "system",
    )
    for role_literal in roles:
        count = role_counts.get(role_literal, 0)
        if count > 0:
            lines.append(f"{role_literal:<15} {count:>10}")

    # Verbose mode: show message details
    if verbose:
        lines.append("")
        lines.append("Messages:")
        lines.append("─" * 47)
        for i, msg in enumerate(conversation.messages, 1):
            timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"{i}. [{msg.role}] {timestamp_str}")
            # Truncate long content
            content = msg.content
            if len(content) > 80:
                content = content[:77] + "..."
            lines.append(f"   {content}")
            if i < len(conversation.messages):
                lines.append("")

    return "\n".join(lines) + "\n"


def _format_conversation_json(conversation: Conversation) -> str:
    """Format conversation as JSON.

    Args:
        conversation: Conversation object to format

    Returns:
        JSON string with conversation data

    Example Output:
        {
          "id": "abc-123",
          "title": "Python Tips",
          "created_at": "2024-03-15T14:30:22Z",
          "updated_at": "2024-03-15T16:45:10Z",
          "message_count": 25,
          "messages": [
            {
              "id": "msg-1",
              "role": "user",
              "content": "Hello",
              "timestamp": "2024-03-15T14:30:22Z"
            }
          ]
        }
    """
    # Build conversation dict
    conv_dict = {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": conversation.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "message_count": conversation.message_count,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "parent_id": msg.parent_id,
            }
            for msg in conversation.messages
        ],
    }

    # Pretty-print JSON with 2-space indentation
    return json.dumps(conv_dict, indent=2, ensure_ascii=False) + "\n"


def get_conversation(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to OpenAI export file",
            exists=False,  # Manual check for exit code 1
            file_okay=True,
            dir_okay=False,
            readable=False,  # Manual check for exit code 1
            resolve_path=True,
        ),
    ],
    conversation_id: Annotated[
        str,
        typer.Argument(
            help="Conversation ID to retrieve",
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (table or json)",
            case_sensitive=False,
        ),
    ] = "table",
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show full message content (table format only)",
        ),
    ] = False,
) -> None:
    """Get conversation by ID and display metadata.

    Retrieves a specific conversation from an OpenAI export file by its ID
    and displays its metadata in either human-readable table format or JSON.

    Examples:
        # Get conversation with table format (default)
        $ echomine get export.json abc-123-def

        # Get conversation with JSON format
        $ echomine get export.json abc-123-def --format json

        # Get conversation with verbose output (show messages)
        $ echomine get export.json abc-123-def --verbose

        # Pipe to jq
        $ echomine get export.json abc-123 -f json | jq '.messages[0].content'

    Args:
        file_path: Path to OpenAI export JSON file
        conversation_id: Conversation ID to retrieve
        format: Output format (table or json)
        verbose: Show full message content (table format only)

    Exit Codes:
        0: Success (conversation found)
        1: File not found, conversation not found, permission denied, parse error
        2: Invalid arguments

    Requirements:
        - FR-155: get_conversation_by_id returns Conversation | None
        - CHK031: stdout for data, stderr for progress/errors
        - CHK032: Proper exit codes 0/1/2
    """
    try:
        # Validate format option
        format_lower = format.lower()
        if format_lower not in ("table", "json"):
            console.print(
                f"[red]Error: Invalid format '{format}'. Must be 'table' or 'json'.[/red]"
            )
            raise typer.Exit(code=2)

        # Check file exists (manual check for exit code 1)
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(code=1)

        # Retrieve conversation using library method
        adapter = OpenAIAdapter()

        # Show progress indicator (only for table format, not JSON)
        conversation: Conversation | None = None
        if format_lower == "table":
            with console.status("[bold green]Searching for conversation..."):
                conversation = adapter.get_conversation_by_id(file_path, conversation_id)
        else:
            # No progress indicator for JSON (keeps output clean)
            conversation = adapter.get_conversation_by_id(file_path, conversation_id)

        # Check if conversation was found
        if conversation is None:
            console.print(
                f"[red]Error: Conversation not found with ID: {conversation_id}[/red]"
            )
            raise typer.Exit(code=1)

        # Format output based on requested format
        if format_lower == "json":
            output = _format_conversation_json(conversation)
        else:
            output = _format_conversation_table(conversation, verbose=verbose)

        # Write output to stdout (CHK031)
        # Use print() for stdout, not typer.echo() or console.print()
        print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        # File doesn't exist (shouldn't reach here due to manual check, but defensive)
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        # Permission denied when trying to read export file
        console.print(f"[red]Error: Permission denied: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except ParseError as e:
        # Invalid JSON syntax
        console.print(f"[red]Error: Invalid JSON in export file: {e}[/red]")
        raise typer.Exit(code=1) from None

    except PydanticValidationError as e:
        # Schema violation (missing fields, wrong types, etc.)
        console.print(f"[red]Error: Validation failed: {e}[/red]")
        raise typer.Exit(code=1) from None

    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from None

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        # This ensures validation errors (exit code 2) are not converted to exit code 1
        raise

    except Exception as e:
        # Unexpected error (catch-all for safety)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None
