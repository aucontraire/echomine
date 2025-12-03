"""Get command implementation with subcommands for conversation and message retrieval.

This module implements the hierarchical 'get' command for retrieving and displaying
specific conversations or messages by ID with metadata details.

Constitution Compliance:
    - Principle I: Library-first (delegates to OpenAIAdapter methods)
    - CHK031: Data on stdout (table/json), progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (error), 2 (invalid arguments)
    - FR-155: get_conversation_by_id returns Conversation | None
    - NEW: get_message_by_id returns tuple[Message, Conversation] | None

Command Contract:
    Usage:
        echomine get conversation <file_path> <conversation_id> [OPTIONS]
        echomine get message <file_path> <message_id> [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file
        conversation_id: Conversation ID to retrieve
        message_id: Message ID to retrieve

    Options (both subcommands):
        --format, -f: Output format (table, json) [default: table]

    Options (conversation):
        --verbose, -v: Show full message content (not just counts)

    Options (message):
        --conversation-id, -c: Optional conversation ID hint for faster lookup
        --verbose, -v: Show full message content and conversation context

    Exit Codes:
        0: Success (conversation/message found)
        1: File not found, conversation/message not found, permission denied, parse error
        2: Invalid arguments

    Output Streams:
        stdout: Conversation/message details (formatted as table or JSON)
        stderr: Error messages, progress indicators

Breaking Change:
    The old flat command `echomine get <file> <id>` is replaced by:
    - `echomine get conversation <file> <id>` (explicit subcommand required)
    - `echomine get message <file> <id>` (new functionality)

    This is a hard break with no deprecation period (pre-1.0 project).
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
from echomine.models.message import Message


# Typer app for get subcommands
get_app = typer.Typer(
    name="get",
    help="Retrieve conversation or message by ID",
    no_args_is_help=True,
)

# Console for stderr output (errors only)
console = Console(stderr=True)


# ============================================================================
# Formatting Utilities (shared between conversation and message commands)
# ============================================================================


def _format_conversation_table(conversation: Conversation, verbose: bool = False) -> str:
    """Format conversation as human-readable table.

    Args:
        conversation: Conversation object to format
        verbose: Show full message content (not just counts)

    Returns:
        Formatted text output with conversation details
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

    # Simple text table
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


def _format_message_table(
    message: Message, conversation: Conversation, verbose: bool = False
) -> str:
    """Format message as human-readable table with conversation context.

    Args:
        message: Message object to format
        conversation: Parent conversation providing context
        verbose: Show full content and conversation details

    Returns:
        Formatted text output with message and context details
    """
    lines = []

    # Header
    lines.append("Message Details")
    lines.append("═" * 47)

    # Message metadata
    lines.append(f"ID:          {message.id}")
    lines.append(f"Role:        {message.role}")
    lines.append(f"Timestamp:   {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"Parent ID:   {message.parent_id or 'None (root message)'}")

    # Message content
    lines.append("")
    lines.append("Content:")
    lines.append("─" * 47)
    # Truncate if not verbose
    content = message.content
    if not verbose and len(content) > 200:
        content = content[:197] + "..."
    lines.append(content)

    # Conversation context
    lines.append("")
    lines.append("Conversation Context:")
    lines.append("─" * 47)
    lines.append(f"Conversation ID:    {conversation.id}")
    lines.append(f"Title:              {conversation.title}")
    lines.append(f"Total Messages:     {conversation.message_count}")

    # Verbose mode: show all conversation messages
    if verbose:
        lines.append("")
        lines.append("All Messages in Conversation:")
        lines.append("─" * 47)
        for i, msg in enumerate(conversation.messages, 1):
            marker = " >>> " if msg.id == message.id else "     "
            timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"{marker}{i}. [{msg.role}] {timestamp_str}")

    return "\n".join(lines) + "\n"


def _format_message_json(message: Message, conversation: Conversation) -> str:
    """Format message as JSON with conversation context.

    Args:
        message: Message object to format
        conversation: Parent conversation providing context

    Returns:
        JSON string with message and conversation data
    """
    # Build message dict with conversation context
    msg_dict = {
        "message": {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "parent_id": message.parent_id,
        },
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": conversation.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "message_count": conversation.message_count,
        },
    }

    # Pretty-print JSON with 2-space indentation
    return json.dumps(msg_dict, indent=2, ensure_ascii=False) + "\n"


# ============================================================================
# Subcommand: get conversation
# ============================================================================


@get_app.command(name="conversation")
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
        $ echomine get conversation export.json abc-123-def

        # Get conversation with JSON format
        $ echomine get conversation export.json abc-123-def --format json

        # Get conversation with verbose output (show messages)
        $ echomine get conversation export.json abc-123-def --verbose

        # Pipe to jq
        $ echomine get conversation export.json abc-123 -f json | jq '.messages[0].content'
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
            console.print(f"[red]Error: Conversation not found with ID: {conversation_id}[/red]")
            raise typer.Exit(code=1)

        # Format output based on requested format
        if format_lower == "json":
            output = _format_conversation_json(conversation)
        else:
            output = _format_conversation_table(conversation, verbose=verbose)

        # Write output to stdout (CHK031)
        print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        console.print(f"[red]Error: Permission denied: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except ParseError as e:
        console.print(f"[red]Error: Invalid JSON in export file: {e}[/red]")
        raise typer.Exit(code=1) from None

    except PydanticValidationError as e:
        console.print(f"[red]Error: Validation failed: {e}[/red]")
        raise typer.Exit(code=1) from None

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from None

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None


# ============================================================================
# Subcommand: get message
# ============================================================================


@get_app.command(name="message")
def get_message(
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
    message_id: Annotated[
        str,
        typer.Argument(
            help="Message ID to retrieve",
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
    conversation_id: Annotated[
        str | None,
        typer.Option(
            "--conversation-id",
            "-c",
            help="Optional conversation ID hint for faster lookup",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show full content and conversation context (table format only)",
        ),
    ] = False,
) -> None:
    """Get message by ID and display with conversation context.

    Retrieves a specific message from an OpenAI export file by its ID
    and displays it with parent conversation context in either human-readable
    table format or JSON.

    The message search can be optimized by providing a conversation ID hint.

    Examples:
        # Get message with table format (default)
        $ echomine get message export.json msg-abc-123

        # Get message with conversation hint (faster)
        $ echomine get message export.json msg-abc-123 -c conv-def-456

        # Get message with JSON format
        $ echomine get message export.json msg-abc-123 --format json

        # Get message with verbose output (full content + conversation messages)
        $ echomine get message export.json msg-abc-123 --verbose

        # Pipe to jq
        $ echomine get message export.json msg-123 -f json | jq '.message.content'

    Performance:
        - With --conversation-id: O(N) where N = conversations until match
        - Without --conversation-id: O(N*M) where N = conversations, M = messages
        - For large files with many conversations, using -c is significantly faster
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

        # Retrieve message using library method
        adapter = OpenAIAdapter()

        # Show progress indicator (only for table format, not JSON)
        result: tuple[Message, Conversation] | None = None
        if format_lower == "table":
            search_msg = (
                f"[bold green]Searching for message in conversation {conversation_id}..."
                if conversation_id
                else "[bold green]Searching for message across all conversations..."
            )
            with console.status(search_msg):
                result = adapter.get_message_by_id(
                    file_path, message_id, conversation_id=conversation_id
                )
        else:
            # No progress indicator for JSON (keeps output clean)
            result = adapter.get_message_by_id(
                file_path, message_id, conversation_id=conversation_id
            )

        # Check if message was found
        if result is None:
            if conversation_id:
                console.print(
                    f"[red]Error: Message not found with ID: {message_id} "
                    f"in conversation {conversation_id}[/red]"
                )
            else:
                console.print(f"[red]Error: Message not found with ID: {message_id}[/red]")
            raise typer.Exit(code=1)

        # Unpack result tuple
        message, parent_conversation = result

        # Format output based on requested format
        if format_lower == "json":
            output = _format_message_json(message, parent_conversation)
        else:
            output = _format_message_table(message, parent_conversation, verbose=verbose)

        # Write output to stdout (CHK031)
        print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        console.print(f"[red]Error: Permission denied: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except ParseError as e:
        console.print(f"[red]Error: Invalid JSON in export file: {e}[/red]")
        raise typer.Exit(code=1) from None

    except PydanticValidationError as e:
        console.print(f"[red]Error: Validation failed: {e}[/red]")
        raise typer.Exit(code=1) from None

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from None

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None
