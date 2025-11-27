"""Main CLI application entry point.

This module defines the Typer application and main() entry point for
the echomine CLI tool.

Architecture:
    - Typer application with registered commands
    - main() function as entry point (referenced in pyproject.toml)
    - Minimal error handling (commands handle their own errors)

Constitution Compliance:
    - Principle I: Library-first (CLI delegates to library)
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2

Entry Point Configuration (pyproject.toml):
    [project.scripts]
    echomine = "echomine.cli.app:main"

Usage:
    # As installed script
    $ echomine list export.json

    # As Python module (development)
    $ python -m echomine.cli.app list export.json
"""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from echomine import __version__
from echomine.cli.commands.export import export_conversation
from echomine.cli.commands.list import list_conversations
from echomine.cli.commands.search import search_conversations


# Create Typer application
app = typer.Typer(
    name="echomine",
    help="Library-first tool for parsing AI conversation exports",
    epilog="""Examples:
  # List all conversations
  echomine list export.json

  # Search by keywords
  echomine search export.json -k python,algorithm

  # Filter by title and date range
  echomine search export.json -t "Debug" --from-date 2024-01-01

  # Export conversation to markdown
  echomine export export.json <conversation-id> --output chat.md

For more help: echomine COMMAND --help""",
    add_completion=False,  # Disable shell completion for simplicity
    no_args_is_help=False,  # Handled manually in callback to support --version
    pretty_exceptions_enable=False,  # Disable pretty exceptions for simpler output
    rich_markup_mode=None,  # Disable Rich markup for cleaner output
)


# Add callback to prevent command collapsing and handle global flags
# This ensures "list" remains a subcommand even though it's the only command
@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Echomine CLI - Library-first tool for parsing AI conversation exports."""
    if version:
        typer.echo(f"echomine version {__version__}")
        raise typer.Exit(0)

    # Show help if no command provided (unless --version was used)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


# Register commands
app.command(name="list", help="List all conversations from export file")(list_conversations)
app.command(name="search", help="Search conversations by keywords")(search_conversations)
app.command(name="export", help="Export conversation to markdown format")(export_conversation)


def main() -> None:
    """Entry point for CLI application.

    This function is referenced in pyproject.toml as the console script
    entry point. It invokes the Typer app and handles any uncaught
    exceptions (though commands should handle their own errors).

    Exit Codes:
        0: Success
        1: Error (user error, file not found, parse error, etc.)
        2: Invalid arguments (Typer handles this)

    Requirements:
        - CHK032: Consistent exit codes
        - Entry point for installed script
    """
    try:
        app()
    except typer.Exit:
        # typer.Exit exceptions are raised by commands to set exit codes
        # Re-raise to preserve exit code
        raise
    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        # Exit cleanly without error message
        typer.echo("", err=True)
        sys.exit(1)
    except Exception as e:
        # Unexpected error not caught by command
        # This is a safety net - commands should handle their own errors
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Allow running as module: python -m echomine.cli.app
if __name__ == "__main__":
    main()
