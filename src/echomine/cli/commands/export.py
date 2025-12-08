"""Export command implementation.

This module implements the 'export' command for exporting conversations
to markdown or JSON format.

Constitution Compliance:
    - Principle I: Library-first (delegates to MarkdownExporter / Pydantic serialization)
    - CHK031: Data on stdout (markdown/JSON), progress/errors on stderr
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
        --format, -f: Output format: markdown (default) or json

    Exit Codes:
        0: Success
        1: File not found, conversation not found, permission denied, validation error
        2: Invalid arguments (both ID and --title, or neither provided, or invalid format)

    Output Streams:
        stdout: Markdown/JSON content (if no --output) OR empty
        stderr: Progress indicators, success messages, error messages
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console

from echomine.adapters import OpenAIAdapter
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
    format: Annotated[
        Literal["markdown", "json"],
        typer.Option(
            "--format",
            "-f",
            help="Output format: markdown (default) or json",
            case_sensitive=False,
        ),
    ] = "markdown",
    no_metadata: Annotated[
        bool,
        typer.Option(
            "--no-metadata",
            help="Disable YAML frontmatter and message IDs in markdown export (FR-033)",
        ),
    ] = False,
) -> None:
    """[bold]Export conversation[/bold] to markdown or JSON format.

    Exports a single conversation from an OpenAI export file to either markdown
    or JSON format, either to stdout (default) or to a specified output file.

    [bold]Examples:[/bold]
        [dim]# Export to stdout by conversation ID (markdown default)[/dim]
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow]

        [dim]# Export to JSON format[/dim]
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow] [cyan]--format[/cyan] json

        [dim]# Export to file by conversation ID[/dim]
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow] [cyan]--output[/cyan] conversation.md

        [dim]# Export as JSON to file[/dim]
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow] [cyan]-f[/cyan] json [cyan]-o[/cyan] conversation.json

        [dim]# Export by title[/dim]
        $ [green]echomine export[/green] export.json [cyan]--title[/cyan] "Python Tutorial" [cyan]-o[/cyan] output.md

        [dim]# Pipe to other tools[/dim]
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow] | pandoc -o output.pdf
        $ [green]echomine export[/green] export.json [yellow]abc-123[/yellow] [cyan]-f[/cyan] json | jq '.messages[0]'

    [bold]Exit Codes:[/bold]
        [green]0[/green]: Success
        [red]1[/red]: File not found, conversation not found, permission denied, parse error
        [yellow]2[/yellow]: Invalid arguments (both ID and --title, or neither provided)
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

        # Load conversation using OpenAIAdapter
        adapter = OpenAIAdapter()
        conversation = None

        # Show progress indicator (only if writing to file, not stdout)
        if output:
            with console.status("[bold green]Finding conversation..."):
                try:
                    for conv in adapter.stream_conversations(file_path):
                        if conv.id == actual_conversation_id:
                            conversation = conv
                            break
                except Exception as e:
                    console.print(f"[red]Error: Failed to parse export file: {e}[/red]")
                    raise typer.Exit(code=1)
        else:
            # No progress indicator when writing to stdout (keeps stdout clean)
            try:
                for conv in adapter.stream_conversations(file_path):
                    if conv.id == actual_conversation_id:
                        conversation = conv
                        break
            except Exception as e:
                console.print(f"[red]Error: Failed to parse export file: {e}[/red]")
                raise typer.Exit(code=1)

        # Check if conversation was found
        if conversation is None:
            console.print(
                f"[red]Error: Conversation {actual_conversation_id} not found in {file_path}[/red]"
            )
            raise typer.Exit(code=1)

        # Generate output based on format
        output_content: str
        if format == "json":
            # Export as JSON using Pydantic serialization
            output_content = conversation.model_dump_json(indent=2)
        else:
            # Export as markdown using MarkdownExporter
            # FR-033: --no-metadata flag disables YAML frontmatter and message IDs
            exporter = MarkdownExporter()
            include_metadata = not no_metadata
            output_content = exporter.export_conversation(
                file_path,
                actual_conversation_id,
                include_metadata=include_metadata,
                include_message_ids=include_metadata,  # Disable both when --no-metadata
            )

        # Write output
        if output:
            # Check if file exists and warn (but still overwrite)
            if output.exists():
                console.print(f"[yellow]Warning: Overwriting existing file: {output}[/yellow]")

            # Write to file
            try:
                output.write_text(output_content, encoding="utf-8")
                console.print(f"[green]✓ Exported to {output}[/green]")
            except PermissionError:
                # FR-061: Permission denied on output file write
                console.print(
                    f"[red]Error: Permission denied: {output}. Check file write permissions.[/red]"
                )
                raise typer.Exit(code=1)
            except OSError as e:
                console.print(f"[red]Error: Failed to write file: {e}[/red]")
                raise typer.Exit(code=1)
        else:
            # Write to stdout (use print, not console, to go to stdout)
            # This allows piping: echomine export ... | pandoc / jq
            print(output_content)

        # Success - return normally for exit code 0
        return

    except FileNotFoundError:
        # File doesn't exist (shouldn't reach here due to manual check, but defensive)
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    except PermissionError:
        # Permission denied when trying to read export file (FR-061)
        console.print(
            f"[red]Error: Permission denied: {file_path}. Check file read permissions.[/red]"
        )
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
