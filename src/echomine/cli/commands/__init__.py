"""CLI commands package.

This package contains all CLI command implementations for echomine.
Each command is a thin wrapper around library functionality.

Constitution Compliance:
    - Principle I: Library-first (commands delegate to core library)
    - CHK031: stdout for data, stderr for progress/errors
    - CHK032: Consistent exit codes (0/1/2)
"""

__all__: list[str] = []
