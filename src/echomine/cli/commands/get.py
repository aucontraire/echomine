"""Get command implementation with subcommands for conversation and message retrieval.

This module implements the hierarchical 'get' command for retrieving and displaying
specific conversations or messages by ID with metadata details (supports OpenAI and Claude).

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
        echomine get messages <file_path> <conversation_id> [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file
        conversation_id: Conversation ID to retrieve
        message_id: Message ID to retrieve

    Options (conversation):
        --format, -f: Output format (table, json) [default: table]
        --verbose, -v: Show full message content (not just counts)

    Options (message):
        --format, -f: Output format (table, json) [default: table]
        --conversation-id, -c: Optional conversation ID hint for faster lookup
        --verbose, -v: Show full message content and conversation context

    Options (messages - list all):
        --json: Output full message objects as JSON array

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
    - `echomine get messages <file> <conv_id>` (list all messages in conversation)

    This is a hard break with no deprecation period (pre-1.0 project).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.console import Console

from echomine.cli.formatters import get_role_color, is_rich_enabled
from echomine.cli.provider import get_adapter
from echomine.exceptions import ParseError
from echomine.models.conversation import Conversation
from echomine.models.message import Message


# Typer app for get subcommands
get_app = typer.Typer(
    name="get",
    help="[cyan]Retrieve[/cyan] conversation or message by ID",
    no_args_is_help=True,
    rich_markup_mode="rich",
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

    # Count messages by role (use Counter[str] for simpler type handling)
    role_counts: Counter[str] = Counter(msg.role for msg in conversation.messages)

    # Simple text table
    lines.append(f"{'Role':<15} {'Count':>10}")
    lines.append("─" * 47)

    # Display counts for each role
    for role_name in ("user", "assistant", "system"):
        count = role_counts[role_name]  # Counter returns 0 for missing keys
        if count > 0:
            lines.append(f"{role_name:<15} {count:>10}")

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


def _format_messages_table(conversation: Conversation) -> str:
    """Format messages as human-readable table (FR-026).

    Args:
        conversation: Conversation object with messages to format

    Returns:
        Formatted text output with messages in chronological order

    Format:
        Messages in "Title" (N messages)
        ─────────────────────────────────────
        msg-001  user       2024-01-15 10:30:05  Content preview (first 100 chars)...
        msg-002  assistant  2024-01-15 10:30:47  Content preview (first 100 chars)...
    """
    lines = []

    # Header with conversation title and message count
    lines.append(f'Messages in "{conversation.title}" ({conversation.message_count} messages)')
    lines.append("─" * 80)

    # List messages in chronological order (oldest first)
    # Messages are already sorted by timestamp in Conversation model
    for message in conversation.messages:
        # Format timestamp
        timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate content to first 100 characters (FR-026)
        content = message.content
        if len(content) > 100:
            content = content[:97] + "..."

        # Format: ID (left-aligned, 12 chars), role (10 chars), timestamp (19 chars), content
        # Handle empty content gracefully (T078)
        content_display = content if content else "(empty)"

        line = f"{message.id:<12} {message.role:<10} {timestamp_str}  {content_display}"
        lines.append(line)

    return "\n".join(lines) + "\n"


def _format_messages_json(conversation: Conversation) -> str:
    """Format messages as JSON array (FR-027).

    Args:
        conversation: Conversation object with messages to format

    Returns:
        JSON string with array of message objects

    Format:
        [
            {
                "id": "msg-001",
                "role": "user",
                "timestamp": "2024-01-15T10:30:05Z",
                "content": "Full message content",
                "parent_id": null
            },
            ...
        ]
    """
    # Build message array
    messages_data = [
        {
            "id": msg.id,
            "role": msg.role,
            "timestamp": msg.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content": msg.content,
            "parent_id": msg.parent_id,
        }
        for msg in conversation.messages
    ]

    # Pretty-print JSON with 2-space indentation
    return json.dumps(messages_data, indent=2, ensure_ascii=False) + "\n"


# ============================================================================
# Rich Formatting Functions (for TTY output)
# ============================================================================


def _format_messages_rich(conversation: Conversation) -> None:
    """Format messages as Rich table for TTY output.

    Displays messages in a colorful table with:
    - Role-based coloring (user=green, assistant=blue, system=yellow)
    - Dimmed IDs
    - Green timestamps
    - Cyan title in header

    Args:
        conversation: Conversation object with messages to format

    Side Effects:
        Prints Rich table to stdout using Console
    """
    from rich.table import Table

    # Create console for stdout (not stderr)
    stdout_console = Console()

    # Create table with box borders
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title=f'[cyan]Messages in "{conversation.title}"[/cyan] ({conversation.message_count} messages)',
        title_style="bold cyan",
    )

    # Add columns
    table.add_column("ID", style="dim", width=36)
    table.add_column("Role", width=10)
    table.add_column("Timestamp", style="green", width=19)
    table.add_column("Content Preview", style="white")

    # Add rows for each message
    for message in conversation.messages:
        # Format timestamp
        timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Get role color
        role_color = get_role_color(message.role)

        # Truncate content to first 100 characters
        content = message.content
        if len(content) > 100:
            content = content[:97] + "..."

        # Handle empty content gracefully
        content_display = content if content else "(empty)"

        # Add row with colored role
        table.add_row(
            message.id,
            f"[{role_color}]{message.role}[/{role_color}]",
            timestamp_str,
            content_display,
        )

    # Print table to stdout
    stdout_console.print(table)


def _format_conversation_rich(conversation: Conversation, verbose: bool = False) -> None:
    """Format conversation as Rich Panel for TTY output.

    Displays conversation details in a formatted panel with:
    - Cyan title and headers
    - Green timestamps
    - Blue borders
    - Role counts table with colored roles
    - Optional verbose message details

    Args:
        conversation: Conversation object to format
        verbose: Show full message content (not just counts)

    Side Effects:
        Prints Rich Panel to stdout using Console
    """
    from rich.panel import Panel
    from rich.table import Table

    # Create console for stdout (not stderr)
    stdout_console = Console()

    # Build content lines
    content_parts = []

    # Basic metadata
    content_parts.append(f"[bold cyan]ID:[/bold cyan]       {conversation.id}")
    content_parts.append(f"[bold cyan]Title:[/bold cyan]    [cyan]{conversation.title}[/cyan]")

    # Timestamps
    created_str = conversation.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated_str = conversation.updated_at_or_created.strftime("%Y-%m-%d %H:%M:%S")
    content_parts.append(f"[bold cyan]Created:[/bold cyan]  [green]{created_str} UTC[/green]")
    content_parts.append(f"[bold cyan]Updated:[/bold cyan]  [green]{updated_str} UTC[/green]")
    content_parts.append(f"[bold cyan]Messages:[/bold cyan] {conversation.message_count} messages")

    content_parts.append("")  # Blank line

    # Message summary by role
    content_parts.append("[bold cyan]Message Summary:[/bold cyan]")

    # Count messages by role
    role_counts: Counter[str] = Counter(msg.role for msg in conversation.messages)

    # Create small table for role counts
    role_table = Table(show_header=True, header_style="bold", border_style="dim", box=None)
    role_table.add_column("Role", style="bold")
    role_table.add_column("Count", justify="right")

    for role_name in ("user", "assistant", "system"):
        count = role_counts[role_name]
        if count > 0:
            role_color = get_role_color(role_name)
            role_table.add_row(
                f"[{role_color}]{role_name}[/{role_color}]",
                str(count),
            )

    # Verbose mode: show message details
    if verbose:
        content_parts.append("")
        content_parts.append("[bold cyan]Messages:[/bold cyan]")
        for i, msg in enumerate(conversation.messages, 1):
            timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            role_color = get_role_color(msg.role)

            content_parts.append(
                f"{i}. [{role_color}][{msg.role}][/{role_color}] [green]{timestamp_str}[/green]"
            )

            # Truncate long content
            content = msg.content
            if len(content) > 80:
                content = content[:77] + "..."

            content_parts.append(f"   {content}")

            if i < len(conversation.messages):
                content_parts.append("")

    # Build final content
    content = "\n".join(content_parts)

    # Create panel
    panel = Panel(
        content,
        title="[bold cyan]Conversation Details[/bold cyan]",
        border_style="blue",
        padding=(1, 2),
    )

    # Print panel
    stdout_console.print(panel)

    # Print role table separately for better layout
    if not verbose:
        stdout_console.print(role_table)


def _format_message_rich(
    message: Message, conversation: Conversation, verbose: bool = False
) -> None:
    """Format message as Rich Panel for TTY output.

    Displays message details in a formatted panel with:
    - Cyan headers
    - Role-based coloring
    - Green timestamps
    - Blue borders
    - Conversation context
    - Optional verbose conversation messages

    Args:
        message: Message object to format
        conversation: Parent conversation providing context
        verbose: Show full content and conversation details

    Side Effects:
        Prints Rich Panel to stdout using Console
    """
    from rich.panel import Panel

    # Create console for stdout (not stderr)
    stdout_console = Console()

    # Build content lines
    content_parts = []

    # Message metadata
    role_color = get_role_color(message.role)
    timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    content_parts.append(f"[bold cyan]ID:[/bold cyan]         {message.id}")
    content_parts.append(
        f"[bold cyan]Role:[/bold cyan]       [{role_color}]{message.role}[/{role_color}]"
    )
    content_parts.append(f"[bold cyan]Timestamp:[/bold cyan]  [green]{timestamp_str} UTC[/green]")
    content_parts.append(
        f"[bold cyan]Parent ID:[/bold cyan]  {message.parent_id or 'None (root message)'}"
    )

    content_parts.append("")
    content_parts.append("[bold cyan]Content:[/bold cyan]")

    # Message content (truncate if not verbose)
    content = message.content
    if not verbose and len(content) > 200:
        content = content[:197] + "..."

    content_parts.append(content)

    content_parts.append("")
    content_parts.append("[bold cyan]Conversation Context:[/bold cyan]")
    content_parts.append(f"[bold]Conversation ID:[/bold]  {conversation.id}")
    content_parts.append(f"[bold]Title:[/bold]            [cyan]{conversation.title}[/cyan]")
    content_parts.append(f"[bold]Total Messages:[/bold]   {conversation.message_count}")

    # Verbose mode: show all conversation messages
    if verbose:
        content_parts.append("")
        content_parts.append("[bold cyan]All Messages in Conversation:[/bold cyan]")
        for i, msg in enumerate(conversation.messages, 1):
            marker = "[bold yellow]>>>[/bold yellow]" if msg.id == message.id else "   "
            msg_timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            msg_role_color = get_role_color(msg.role)

            content_parts.append(
                f"{marker} {i}. [{msg_role_color}][{msg.role}][/{msg_role_color}] [green]{msg_timestamp_str}[/green]"
            )

    # Build final content
    content = "\n".join(content_parts)

    # Create panel
    panel = Panel(
        content,
        title="[bold cyan]Message Details[/bold cyan]",
        border_style="blue",
        padding=(1, 2),
    )

    # Print panel
    stdout_console.print(panel)


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
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-p",
            help="Export provider (openai or claude). Auto-detected if omitted.",
            case_sensitive=False,
        ),
    ] = None,
) -> None:
    """[bold]Get conversation by ID[/bold] and display metadata.

    Retrieves a specific conversation from an OpenAI export file by its ID
    and displays its metadata in either human-readable table format or JSON.

    [bold]Examples:[/bold]
        [dim]# Get conversation with table format (default)[/dim]
        $ [green]echomine get conversation[/green] export.json [yellow]abc-123-def[/yellow]

        [dim]# Get conversation with JSON format[/dim]
        $ [green]echomine get conversation[/green] export.json [yellow]abc-123-def[/yellow] [cyan]--format[/cyan] json

        [dim]# Get conversation with verbose output (show messages)[/dim]
        $ [green]echomine get conversation[/green] export.json [yellow]abc-123-def[/yellow] [cyan]--verbose[/cyan]

        [dim]# Pipe to jq[/dim]
        $ [green]echomine get conversation[/green] export.json [yellow]abc-123[/yellow] [cyan]-f[/cyan] json | jq '.messages[0].content'
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

        # Retrieve conversation using library method with appropriate adapter
        adapter = get_adapter(provider, file_path)

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
            # Write JSON output to stdout (CHK031)
            print(output, end="")
        # Check if Rich should be enabled (TTY detection)
        elif is_rich_enabled(json_flag=(format_lower == "json")):
            # Use Rich formatter for TTY
            _format_conversation_rich(conversation, verbose=verbose)
        else:
            # Use plain text formatter for pipes/redirects
            output = _format_conversation_table(conversation, verbose=verbose)
            print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        # FR-061: Permission denied when reading export file
        console.print(
            f"[red]Error: Permission denied: {file_path}. Check file read permissions.[/red]"
        )
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
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-p",
            help="Export provider (openai or claude). Auto-detected if omitted.",
            case_sensitive=False,
        ),
    ] = None,
) -> None:
    """[bold]Get message by ID[/bold] and display with conversation context.

    Retrieves a specific message from an OpenAI export file by its ID
    and displays it with parent conversation context in either human-readable
    table format or JSON.

    The message search can be optimized by providing a conversation ID hint.

    [bold]Examples:[/bold]
        [dim]# Get message with table format (default)[/dim]
        $ [green]echomine get message[/green] export.json [yellow]msg-abc-123[/yellow]

        [dim]# Get message with conversation hint (faster)[/dim]
        $ [green]echomine get message[/green] export.json [yellow]msg-abc-123[/yellow] [cyan]-c[/cyan] conv-def-456

        [dim]# Get message with JSON format[/dim]
        $ [green]echomine get message[/green] export.json [yellow]msg-abc-123[/yellow] [cyan]--format[/cyan] json

        [dim]# Get message with verbose output (full content + conversation messages)[/dim]
        $ [green]echomine get message[/green] export.json [yellow]msg-abc-123[/yellow] [cyan]--verbose[/cyan]

        [dim]# Pipe to jq[/dim]
        $ [green]echomine get message[/green] export.json [yellow]msg-123[/yellow] [cyan]-f[/cyan] json | jq '.message.content'

    [bold]Performance:[/bold]
        - With [cyan]--conversation-id[/cyan]: O(N) where N = conversations until match
        - Without [cyan]--conversation-id[/cyan]: O(N*M) where N = conversations, M = messages
        - For large files with many conversations, using [cyan]-c[/cyan] is significantly faster
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

        # Retrieve message using library method with appropriate adapter
        adapter = get_adapter(provider, file_path)

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
            # Write JSON output to stdout (CHK031)
            print(output, end="")
        # Check if Rich should be enabled (TTY detection)
        elif is_rich_enabled(json_flag=(format_lower == "json")):
            # Use Rich formatter for TTY
            _format_message_rich(message, parent_conversation, verbose=verbose)
        else:
            # Use plain text formatter for pipes/redirects
            output = _format_message_table(message, parent_conversation, verbose=verbose)
            print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        # FR-061: Permission denied when reading export file
        console.print(
            f"[red]Error: Permission denied: {file_path}. Check file read permissions.[/red]"
        )
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
# Subcommand: get messages (plural - list all messages in conversation)
# ============================================================================


@get_app.command(name="messages")
def get_messages(
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
            help="Conversation ID to list messages from",
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output full message objects as JSON array",
        ),
    ] = False,
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-p",
            help="Export provider (openai or claude). Auto-detected if omitted.",
            case_sensitive=False,
        ),
    ] = None,
) -> None:
    """[bold]List all messages[/bold] in a conversation.

    Retrieves all messages from a specific conversation and displays them
    in chronological order (oldest first). Messages are shown with ID, role,
    timestamp, and content preview (first 100 characters).

    [bold]Examples:[/bold]
        [dim]# List messages in human-readable format[/dim]
        $ [green]echomine get messages[/green] export.json [yellow]abc-123-def[/yellow]

        [dim]# List messages as JSON[/dim]
        $ [green]echomine get messages[/green] export.json [yellow]abc-123-def[/yellow] [cyan]--json[/cyan]

        [dim]# Pipe to jq[/dim]
        $ [green]echomine get messages[/green] export.json [yellow]abc-123[/yellow] [cyan]--json[/cyan] | jq '.[0].content'

    [bold]Exit Codes:[/bold]
        [green]0[/green]: Success
        [red]1[/red]: Conversation not found, file not found, permission denied
        [yellow]2[/yellow]: Invalid arguments
    """
    try:
        # Check file exists (manual check for exit code 1)
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(code=1)

        # Retrieve conversation using library method with appropriate adapter
        adapter = get_adapter(provider, file_path)

        # Show progress indicator (only for table format, not JSON)
        conversation: Conversation | None = None
        if not json_output:
            with console.status("[bold green]Searching for conversation..."):
                conversation = adapter.get_conversation_by_id(file_path, conversation_id)
        else:
            # No progress indicator for JSON (keeps output clean)
            conversation = adapter.get_conversation_by_id(file_path, conversation_id)

        # Check if conversation was found
        if conversation is None:
            console.print(f"[red]Error: Conversation not found: {conversation_id}[/red]")
            raise typer.Exit(code=1)

        # Format output based on requested format
        if json_output:
            output = _format_messages_json(conversation)
            # Write JSON output to stdout (CHK031)
            print(output, end="")
        # Check if Rich should be enabled (TTY detection)
        elif is_rich_enabled(json_flag=json_output):
            # Use Rich formatter for TTY
            _format_messages_rich(conversation)
        else:
            # Use plain text formatter for pipes/redirects
            output = _format_messages_table(conversation)
            print(output, end="")

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1) from None

    except PermissionError:
        # FR-061: Permission denied when reading export file
        console.print(
            f"[red]Error: Permission denied: {file_path}. Check file read permissions.[/red]"
        )
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
