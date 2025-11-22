"""CLI package for echomine.

This package provides the command-line interface for echomine, built with
Typer for intuitive command structure and Rich for human-readable output.

Architecture:
    - Library-first: CLI is a thin wrapper around core library functionality
    - Dual output modes: Human-readable (default) and JSON (--format json)
    - Stream separation: Data on stdout, progress on stderr
    - Exit codes: 0 (success), 1 (user error), 2 (invalid arguments)

Constitution Compliance:
    - Principle I: Library-first design (no business logic in CLI)
    - FR-428: Strict stdout/stderr separation
    - FR-429: Consistent exit codes
    - CHK031: Data on stdout, progress on stderr
    - CHK032: Exit codes 0/1/2 for success/error/invalid
"""

__all__: list[str] = []
