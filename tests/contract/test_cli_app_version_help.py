"""Contract tests for CLI app.py --version and --help flags.

This module tests the main application entry point, version display,
and help text functionality.

Coverage Target: app.py lines 28-137 (currently 0% coverage)

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2
    - FR-018: Human-readable output
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI in development mode.
    """
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.mark.contract
class TestCLIAppVersionAndHelp:
    """Contract tests for app.py main entry point, version, and help."""

    def test_version_flag_displays_version_number(self, cli_command: list[str]) -> None:
        """Test --version flag displays version and exits with code 0.

        Validates:
        - app.py line 89-91: version callback
        - Exit code 0
        - Version string format
        """
        result = subprocess.run(
            [*cli_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"--version should exit 0, got {result.returncode}"

        # Assert: Version string on stdout
        stdout = result.stdout
        assert "echomine" in stdout.lower(), "Version output should mention 'echomine'"
        assert "version" in stdout.lower(), "Version output should mention 'version'"

        # Version should be semantic versioning (e.g., "0.1.0")
        # At minimum, should contain a number
        assert any(char.isdigit() for char in stdout), "Version should contain version number"

    def test_version_short_flag_works(self, cli_command: list[str]) -> None:
        """Test -v short flag also displays version.

        Validates:
        - app.py line 82: -v short flag alias
        - Same behavior as --version
        """
        result = subprocess.run(
            [*cli_command, "-v"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Version output present
        assert "echomine" in result.stdout.lower()
        assert "version" in result.stdout.lower()

    def test_help_flag_displays_usage_information(self, cli_command: list[str]) -> None:
        """Test --help flag displays usage information.

        Validates:
        - app.py line 94-96: callback shows help
        - Exit code 0
        - Help text contains command list
        """
        result = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"--help should exit 0, got {result.returncode}"

        # Assert: Help text on stdout
        stdout = result.stdout
        assert len(stdout) > 100, "Help text should be substantial"

        # Assert: Help mentions available commands
        assert "list" in stdout.lower(), "Help should mention 'list' command"
        assert "search" in stdout.lower(), "Help should mention 'search' command"
        assert "export" in stdout.lower(), "Help should mention 'export' command"
        assert "get" in stdout.lower(), "Help should mention 'get' command"

    def test_no_command_displays_help(self, cli_command: list[str]) -> None:
        """Test running echomine with no command shows help.

        Validates:
        - app.py line 94-96: no subcommand shows help
        - Exit code 0 (help, not error)
        """
        result = subprocess.run(
            cli_command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (showing help is not an error)
        assert result.returncode == 0, "No command should show help with exit 0"

        # Assert: Help text displayed
        stdout = result.stdout
        assert "echomine" in stdout.lower()
        assert "list" in stdout.lower() or "command" in stdout.lower()

    def test_invalid_command_exits_with_error(self, cli_command: list[str]) -> None:
        """Test invalid command name exits with error.

        Validates:
        - Typer handles invalid commands
        - Exit code 2 (invalid argument)
        - Error message on stderr
        """
        result = subprocess.run(
            [*cli_command, "invalid-command-name"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (invalid argument)
        assert result.returncode == 2, f"Invalid command should exit 2, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error should be on stderr"

    def test_keyboard_interrupt_exits_gracefully(self, cli_command: list[str]) -> None:
        """Test KeyboardInterrupt is handled gracefully in main().

        Validates:
        - app.py line 128-132: KeyboardInterrupt handling
        - Exit code 1

        Note: This is a structural test - actual interrupt tested manually.
        Skipped for automated testing due to complexity.
        """
        pytest.skip("KeyboardInterrupt handling requires manual verification")

    def test_version_flag_takes_precedence_over_commands(self, cli_command: list[str]) -> None:
        """Test --version flag works even with command specified.

        Validates:
        - app.py line 84: is_eager=True on version flag
        - Version shown, command not executed
        """
        result = subprocess.run(
            [*cli_command, "--version", "list"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Version shown (not list output)
        stdout = result.stdout
        assert "version" in stdout.lower()
        # Should NOT show list output headers
        assert "ID" not in stdout or "Title" not in stdout


@pytest.mark.contract
class TestCLIAppExceptionHandling:
    """Contract tests for main() exception handling in app.py."""

    def test_file_not_found_error_exits_with_code_1(self, cli_command: list[str]) -> None:
        """Test file not found error from command exits with code 1.

        Validates:
        - Commands handle errors appropriately
        - Exit code 1 for operational errors
        """
        result = subprocess.run(
            [*cli_command, "list", "/nonexistent/file/path.json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1 (operational error)
        assert result.returncode == 1, f"File not found should exit 1, got {result.returncode}"

        # Assert: Error on stderr
        assert len(result.stderr) > 0, "Error should be on stderr"
        assert "not found" in result.stderr.lower()

    def test_malformed_json_exits_with_code_1(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test malformed JSON file exits with code 1.

        Validates:
        - Parse errors are operational errors
        - Exit code 1
        - Clear error message
        """
        # Create malformed JSON
        malformed = tmp_path / "malformed.json"
        malformed.write_text("{invalid json syntax")

        result = subprocess.run(
            [*cli_command, "list", str(malformed)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Parse error should exit 1, got {result.returncode}"

        # Assert: Error mentions JSON/parse
        stderr = result.stderr
        assert "json" in stderr.lower() or "parse" in stderr.lower()


@pytest.mark.contract
class TestCLIAppStdoutStderrSeparation:
    """Contract tests for stdout/stderr separation in CLI."""

    def test_version_output_on_stdout_not_stderr(self, cli_command: list[str]) -> None:
        """Test --version writes to stdout, not stderr.

        Validates:
        - CHK031: Data on stdout
        - stderr empty for version display
        """
        result = subprocess.run(
            [*cli_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: stdout has version
        assert len(result.stdout) > 0, "Version should be on stdout"

        # Assert: stderr empty or minimal
        # (Some platforms may have warnings, but no version text)
        if result.stderr:
            assert "version" not in result.stderr.lower()

    def test_help_output_on_stdout_not_stderr(self, cli_command: list[str]) -> None:
        """Test --help writes to stdout, not stderr.

        Validates:
        - CHK031: Data on stdout
        - stderr empty for help display
        """
        result = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: stdout has help text
        assert len(result.stdout) > 100, "Help should be on stdout"

        # Assert: Main help content not on stderr
        if result.stderr:
            assert "list" not in result.stderr.lower()
            assert "search" not in result.stderr.lower()
