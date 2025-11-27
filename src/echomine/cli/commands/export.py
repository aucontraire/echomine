"""Export command implementation.

This module implements the 'export' command for exporting conversations
to markdown format.

Constitution Compliance:
    - Principle I: Library-first (delegates to MarkdownExporter)
    - CHK031: Data on stdout (markdown), progress/errors on stderr
    - CHK032: Exit codes 0 (success), 1 (error), 2 (invalid arguments)
    - FR-018: Export command with file path, conversation ID, --output flag
    - FR-016: Support --title as alternative to conversation ID

Command Contract:
    Usage: echomine export <file_path> [CONVERSATION_ID] [OPTIONS]

    Arguments:
        file_path: Path to OpenAI export JSON file
        conversation_id: Optional conversation ID to export (mutually exclusive with --title)

    Options:
        --title, -t: Export by conversation title (mutually exclusive with ID)
        --output, -o: Output file path (default: stdout)

    Exit Codes:
        0: Success
        1: File not found, conversation not found, permission denied, validation error
        2: Invalid arguments (both ID and --title, or neither provided)

    Output Streams:
        stdout: Markdown content (if no --output) OR empty
        stderr: Progress indicators, success messages, error messages
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from echomine.export import MarkdownExporter


# Console for stderr output (progress, success messages, errors)
console = Console(stderr=True)


def _find_conversation_by_title(file_path: Path, title: str) -> tuple[str, str] | None:
    """Find conversation ID and exact title by title substring match.

    Args:
        file_path: Path to OpenAI export JSON file
        title: Title substring to search for (case-insensitive)

    Returns:
        Tuple of (conversation_id, exact_title) if single match found,
        None if no matches found

    Raises:
        ValueError: If multiple conversations match the title
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        PermissionError: If file cannot be read
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Handle both list and single conversation
    conversations = data if isinstance(data, list) else [data]

    # Find all conversations with matching title (case-insensitive substring)
    matches: list[tuple[str, str]] = []
    title_lower = title.lower()

    for conv in conversations:
        if not isinstance(conv, dict):
            continue

        conv_title = conv.get("title", "")
        conv_id = conv.get("id") or conv.get("conversation_id")

        if conv_id and title_lower in conv_title.lower():
            matches.append((conv_id, conv_title))

    # Return results based on match count
    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]
    # Multiple matches - ambiguous
    raise ValueError(
        f"Multiple conversations found with title containing '{title}': "
        f"{len(matches)} matches. Please use conversation ID instead."
    )


def export_conversation(
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
        str | None,
        typer.Argument(
            help="Conversation ID to export (omit if using --title)",
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            "-t",
            help="Export by conversation title (case-insensitive substring match)",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: stdout)",
        ),
    ] = None,
) -> None:
    """Export conversation to markdown format.

    Exports a single conversation from an OpenAI export file to markdown format,
    either to stdout (default) or to a specified output file.

    Examples:
        # Export to stdout by conversation ID
        $ echomine export export.json abc-123

        # Export to file by conversation ID
        $ echomine export export.json abc-123 --output conversation.md

        # Export by title
        $ echomine export export.json --title "Python Tutorial" -o output.md

        # Pipe to other tools
        $ echomine export export.json abc-123 | pandoc -o output.pdf

    Args:
        file_path: Path to OpenAI export JSON file
        conversation_id: Conversation ID to export (mutually exclusive with --title)
        title: Conversation title to search for (mutually exclusive with ID)
        output: Output file path (default: stdout)

    Exit Codes:
        0: Success
        1: File not found, conversation not found, permission denied, parse error
        2: Invalid arguments (both ID and --title, or neither provided)

    Requirements:
        - FR-018: Export command functionality
        - FR-016: Support --title as alternative identifier
        - CHK031: stdout for data, stderr for progress/errors
        - CHK032: Proper exit codes 0/1/2
    """
    try:
        # Validation: Exactly one of conversation_id or --title must be provided
        if conversation_id is not None and title is not None:
            console.print(
                "[red]Error: Cannot specify both conversation ID and --title. "
                "Use one or the other.[/red]"
            )
            raise typer.Exit(code=2)

        if conversation_id is None and title is None:
            console.print("[red]Error: Must specify either conversation ID or --title.[/red]")
            raise typer.Exit(code=2)

        # Check file exists (manual check for exit code 1)
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(code=1)

        # Resolve conversation ID from title if needed
        actual_conversation_id: str
        if title is not None:
            # Find conversation by title
            try:
                result = _find_conversation_by_title(file_path, title)
                if result is None:
                    console.print(
                        f"[red]Error: No conversation found with title containing '{title}'[/red]"
                    )
                    raise typer.Exit(code=1)

                actual_conversation_id, exact_title = result
                # Show which conversation was matched (helpful feedback)
                if not output:
                    # Only show to stderr if outputting to stdout
                    console.print(f"[dim]Matched conversation: {exact_title}[/dim]")
            except ValueError as e:
                # Multiple matches (ambiguous title)
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(code=1)
        else:
            # Use provided conversation ID
            actual_conversation_id = conversation_id  # type: ignore[assignment]

        # Export conversation using MarkdownExporter
        exporter = MarkdownExporter()

        # Show progress indicator (only if writing to file, not stdout)
        if output:
            with console.status("[bold green]Exporting conversation..."):
                try:
                    markdown = exporter.export_conversation(file_path, actual_conversation_id)
                except ValueError as e:
                    # Conversation not found
                    console.print(f"[red]Error: {e}[/red]")
                    raise typer.Exit(code=1)
        else:
            # No progress indicator when writing to stdout (keeps stdout clean)
            try:
                markdown = exporter.export_conversation(file_path, actual_conversation_id)
            except ValueError as e:
                # Conversation not found
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(code=1)

        # Write output
        if output:
            # Check if file exists and warn (but still overwrite)
            if output.exists():
                console.print(f"[yellow]Warning: Overwriting existing file: {output}[/yellow]")

            # Write to file
            try:
                output.write_text(markdown, encoding="utf-8")
                console.print(f"[green]✓ Exported to {output}[/green]")
            except PermissionError:
                console.print(f"[red]Error: Permission denied: {output}[/red]")
                raise typer.Exit(code=1)
            except OSError as e:
                console.print(f"[red]Error: Failed to write file: {e}[/red]")
                raise typer.Exit(code=1)
        else:
            # Write to stdout (use print, not console, to go to stdout)
            # This allows piping: echomine export ... | pandoc
            print(markdown)

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        # File doesn't exist (shouldn't reach here due to manual check, but defensive)
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    except PermissionError:
        # Permission denied when trying to read export file
        console.print(f"[red]Error: Permission denied: {file_path}[/red]")
        raise typer.Exit(code=1)

    except json.JSONDecodeError as e:
        # Invalid JSON syntax
        console.print(f"[red]Error: Invalid JSON in export file: {e}[/red]")
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        # This ensures validation errors (exit code 2) are not converted to exit code 1
        raise

    except Exception as e:
        # Unexpected error (catch-all for safety)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
