"""Stats command implementation for conversation statistics.

This module implements the 'stats' command for displaying aggregate statistics
about conversation exports, including message counts, date ranges, and
conversation summaries.

Constitution Compliance:
    - Principle I: Library-first (delegates to echomine.statistics library)
    - CHK031: Data on stdout (table/json), progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (error), 2 (invalid arguments)

Command Contract:
    Usage:
        echomine stats <file_path> [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file

    Options:
        --json: Output as JSON (FR-012)

    Exit Codes:
        0: Success (statistics generated)
        1: File not found, permission denied, parse error
        2: Invalid arguments

    Output Streams:
        stdout: Statistics summary (formatted table or JSON)
        stderr: Progress indicators, error messages

Baseline Enhancement Package (v1.2.0):
    - FR-009: stats command exists
    - FR-010: Display required fields (total conversations, messages, date range, etc.)
    - FR-012: JSON output support
    - FR-014: Progress reporting to stderr
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from echomine.exceptions import ParseError
from echomine.statistics import calculate_statistics


if TYPE_CHECKING:
    from echomine.models.statistics import ConversationStatistics, ExportStatistics


def display_stats_table(stats: ExportStatistics) -> None:
    """Display statistics in human-readable table format using Rich.

    Args:
        stats: ExportStatistics object from calculate_statistics()

    Output:
        Formatted statistics panel to stdout

    Requirements:
        - FR-010: Display all required fields
        - FR-014: Human-readable formatting
    """
    from echomine.models.statistics import ExportStatistics

    # Type assertion for mypy
    assert isinstance(stats, ExportStatistics)

    # Build statistics text with Rich styling
    lines = [
        f"[bold cyan]Total conversations:[/bold cyan]  [green]{stats.total_conversations:,}[/green]",
        f"[bold cyan]Total messages:[/bold cyan]       [green]{stats.total_messages:,}[/green]",
    ]

    # Add date range if available
    if stats.earliest_date and stats.latest_date:
        earliest = stats.earliest_date.strftime("%Y-%m-%d")
        latest = stats.latest_date.strftime("%Y-%m-%d")
        lines.append(
            f"[bold cyan]Date range:[/bold cyan]           [green]{earliest}[/green] to [green]{latest}[/green]"
        )

    # Add average messages
    lines.append(
        f"[bold cyan]Average messages:[/bold cyan]     [yellow]{stats.average_messages:.1f}[/yellow]"
    )

    # Add blank line before largest/smallest
    lines.append("")

    # Add largest conversation
    if stats.largest_conversation:
        lines.append("[bold cyan]Largest conversation:[/bold cyan]")
        lines.append(
            f'  [cyan]"{stats.largest_conversation.title}"[/cyan] '
            f"[dim](id: {stats.largest_conversation.id})[/dim], "
            f"[magenta]{stats.largest_conversation.message_count} messages[/magenta]"
        )

    # Add blank line
    lines.append("")

    # Add smallest conversation
    if stats.smallest_conversation:
        lines.append("[bold cyan]Smallest conversation:[/bold cyan]")
        lines.append(
            f'  [cyan]"{stats.smallest_conversation.title}"[/cyan] '
            f"[dim](id: {stats.smallest_conversation.id})[/dim], "
            f"[magenta]{stats.smallest_conversation.message_count} messages[/magenta]"
        )

    # Create panel with statistics
    content = "\n".join(lines)
    panel = Panel(
        content,
        title="Export Statistics",
        border_style="blue",
        padding=(1, 2),
    )

    # Print to stdout
    console = Console()
    console.print(panel)


def display_stats_json(stats: ExportStatistics) -> None:
    """Display statistics as JSON to stdout.

    Args:
        stats: ExportStatistics object from calculate_statistics()

    Output:
        JSON object to stdout (single line, no trailing newline)

    Requirements:
        - FR-012: JSON output format
        - CHK031: stdout for data, stderr for errors
    """
    import json

    # Convert ExportStatistics to dict using Pydantic's model_dump
    # Use mode='json' to ensure datetime objects are serialized
    stats_dict = stats.model_dump(mode="json")

    # Output JSON to stdout (no trailing newline for pipeline compatibility)
    print(json.dumps(stats_dict), end="")


def display_conversation_stats_table(stats: ConversationStatistics) -> None:
    """Display per-conversation statistics in human-readable format using Rich.

    Args:
        stats: ConversationStatistics object from calculate_conversation_statistics()

    Output:
        Formatted conversation statistics panel to stdout

    Requirements:
        - FR-019: Display conversation ID, title, dates, message breakdown
        - FR-020: Color-coded role display (user=green, assistant=blue, system=yellow)
        - FR-021: Temporal patterns (first/last message, duration, average gap)
    """
    from echomine.models.statistics import ConversationStatistics

    # Type assertion for mypy
    assert isinstance(stats, ConversationStatistics)

    # Build statistics text with Rich styling
    lines = [
        f"[bold cyan]ID:[/bold cyan]                   [dim]{stats.conversation_id}[/dim]",
        f"[bold cyan]Created:[/bold cyan]              [green]{stats.created_at.strftime('%Y-%m-%d %H:%M:%S %Z')}[/green]",
    ]

    # Add updated_at if available
    if stats.updated_at:
        lines.append(
            f"[bold cyan]Updated:[/bold cyan]              [green]{stats.updated_at.strftime('%Y-%m-%d %H:%M:%S %Z')}[/green]"
        )

    # Add blank line before message breakdown
    lines.append("")
    lines.append("[bold cyan]Message Breakdown:[/bold cyan]")

    # Add color-coded role counts (FR-020)
    # user=green, assistant=blue, system=yellow
    lines.append(
        f"  [green]user:[/green]       [green]{stats.message_count_by_role.user} messages[/green]"
    )
    lines.append(
        f"  [blue]assistant:[/blue]  [blue]{stats.message_count_by_role.assistant} messages[/blue]"
    )
    lines.append(
        f"  [yellow]system:[/yellow]     [yellow]{stats.message_count_by_role.system} messages[/yellow]"
    )
    lines.append(f"  [bold]Total:[/bold]      [green]{stats.message_count} messages[/green]")

    # Add temporal patterns (FR-021)
    if stats.first_message and stats.last_message:
        lines.append("")
        lines.append("[bold cyan]Temporal Patterns:[/bold cyan]")
        lines.append(
            f"  [bold]First message:[/bold]      [green]{stats.first_message.strftime('%Y-%m-%d %H:%M:%S %Z')}[/green]"
        )
        lines.append(
            f"  [bold]Last message:[/bold]       [green]{stats.last_message.strftime('%Y-%m-%d %H:%M:%S %Z')}[/green]"
        )

        # Format duration as human-readable (Xh Xm Xs)
        duration = stats.duration_seconds
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"

        lines.append(f"  [bold]Duration:[/bold]           [yellow]{duration_str}[/yellow]")

        # Add average gap if available (2+ messages)
        if stats.average_gap_seconds is not None:
            lines.append(
                f"  [bold]Average gap:[/bold]        [yellow]{stats.average_gap_seconds:.1f} seconds[/yellow]"
            )

    # Create panel with conversation title
    content = "\n".join(lines)
    panel = Panel(
        content,
        title=f'Conversation Statistics: "{stats.title}"',
        border_style="blue",
        padding=(1, 2),
    )

    # Print to stdout
    console = Console()
    console.print(panel)


def display_conversation_stats_json(stats: ConversationStatistics) -> None:
    """Display per-conversation statistics as JSON to stdout.

    Args:
        stats: ConversationStatistics object from calculate_conversation_statistics()

    Output:
        JSON object to stdout (single line, no trailing newline)

    Requirements:
        - FR-024: JSON output for per-conversation stats
        - CHK031: stdout for data, stderr for errors
    """
    import json

    # Convert ConversationStatistics to dict using Pydantic's model_dump
    # Use mode='json' to ensure datetime objects are serialized
    stats_dict = stats.model_dump(mode="json")

    # Output JSON to stdout (no trailing newline for pipeline compatibility)
    print(json.dumps(stats_dict), end="")


def stats_command(
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
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output in JSON format",
        ),
    ] = False,
    conversation_id: Annotated[
        str | None,
        typer.Option(
            "--conversation",
            help="Show statistics for specific conversation ID (FR-018)",
        ),
    ] = None,
) -> None:
    """[bold]Display statistics[/bold] for export or conversation.

    Calculate and display statistics for entire export file or a specific conversation.

    [bold]Export-level statistics[/bold] (default):
    - Total conversations and messages
    - Date range (earliest to latest)
    - Average messages per conversation
    - Largest and smallest conversations

    [bold]Per-conversation statistics[/bold] ([cyan]--conversation[/cyan]):
    - Conversation ID, title, dates
    - Message breakdown by role ([green]user[/green]/[blue]assistant[/blue]/[yellow]system[/yellow])
    - Temporal patterns (duration, average gap)

    [bold]Examples:[/bold]
        [dim]# Show export-level statistics[/dim]
        $ [green]echomine stats[/green] export.json

        [dim]# Show statistics as JSON[/dim]
        $ [green]echomine stats[/green] export.json [cyan]--json[/cyan]

        [dim]# Show per-conversation statistics[/dim]
        $ [green]echomine stats[/green] export.json [cyan]--conversation[/cyan] [yellow]abc-123[/yellow]

        [dim]# Per-conversation stats as JSON[/dim]
        $ [green]echomine stats[/green] export.json [cyan]--conversation[/cyan] [yellow]abc-123[/yellow] [cyan]--json[/cyan]

    [bold]Exit Codes:[/bold]
        [green]0[/green]: Success (statistics displayed)
        [red]1[/red]: File not found, permission denied, parse error, conversation not found
        [yellow]2[/yellow]: Invalid arguments (handled by Typer)
    """
    try:
        # Check file exists (manual check for exit code 1)
        if not file_path.exists():
            typer.echo(f"Error: File not found: {file_path}", err=True)
            raise typer.Exit(code=1)

        # Branch based on --conversation option (FR-018)
        if conversation_id is not None:
            # Per-conversation statistics (FR-018, FR-019, FR-020, FR-021)
            from echomine.adapters.openai import OpenAIAdapter
            from echomine.statistics import calculate_conversation_statistics

            # Get conversation by ID using OpenAIAdapter (Library-first)
            adapter = OpenAIAdapter()
            conversation = adapter.get_conversation_by_id(file_path, conversation_id)

            # Check if conversation was found (FR-018)
            if conversation is None:
                typer.echo(
                    f"Error: Conversation not found: {conversation_id}",
                    err=True,
                )
                raise typer.Exit(code=1)

            # Calculate per-conversation statistics (FR-022)
            conv_stats = calculate_conversation_statistics(conversation)

            # Display statistics (FR-019, FR-024)
            if json_output:
                display_conversation_stats_json(conv_stats)
            else:
                display_conversation_stats_table(conv_stats)

            # Return normally for success (exit code 0)
            return

        # Export-level statistics (FR-009, FR-010, FR-012)
        # Progress callback for stderr (only for non-JSON output)
        # FR-014: Progress reported to stderr
        progress_displayed = False

        def on_progress(count: int) -> None:
            nonlocal progress_displayed
            if not json_output and not progress_displayed:
                # Show progress indicator on stderr
                typer.echo(f"Analyzing conversations... {count} processed", err=True)
                progress_displayed = True

        # Calculate statistics using library function (Principle I: Library-first)
        # Use Rich progress indicator for visual feedback
        if not json_output:
            # Show progress spinner on stderr
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=Console(stderr=True),  # Progress to stderr
            ) as progress:
                task = progress.add_task("Analyzing conversations...", total=None)

                stats = calculate_statistics(
                    file_path,
                    progress_callback=on_progress,
                )

                progress.update(task, completed=True)
        else:
            # No progress indicator for JSON output (stdout must be clean)
            stats = calculate_statistics(file_path)

        # Display statistics (stdout)
        if json_output:
            display_stats_json(stats)
        else:
            display_stats_table(stats)

        # Return normally for success (exit code 0)
        return

    except FileNotFoundError:
        # File doesn't exist (shouldn't reach here due to manual check, but defensive)
        typer.echo(f"Error: File not found: {file_path}", err=True)
        raise typer.Exit(code=1)

    except PermissionError:
        # Permission denied when trying to read file (FR-061)
        typer.echo(f"Error: Permission denied: {file_path}. Check file read permissions.", err=True)
        raise typer.Exit(code=1)

    except ParseError as e:
        # Invalid JSON syntax or malformed export structure
        typer.echo(f"Error: Invalid JSON in export file: {e}", err=True)
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(code=130)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise

    except Exception as e:
        # Unexpected error (catch-all for safety)
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
