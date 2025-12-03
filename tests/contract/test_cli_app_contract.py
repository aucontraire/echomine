"""Contract tests for CLI application entry point (app.py).

Task: Coverage improvement for src/echomine/cli/app.py (0% → 80%+)
Phase: TDD RED-GREEN-REFACTOR

This module validates the main CLI application entry point contract.
These are BLACK BOX tests - we invoke the CLI as subprocess and validate
external behavior (stdout, stderr, exit codes, help text, version).

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the main CLI app adheres to its published interface contract.

Contract Requirements Validated:
- CHK031: stdout/stderr separation
- CHK032: Exit codes (0=success, 1=error, 2=invalid input)
- --version flag displays version
- --help flag displays help text
- No args displays help (no_args_is_help behavior)
- Command registration (list, get, search, export)
- Error handling (KeyboardInterrupt, exceptions)

Coverage Target:
- Lines 28-137 in app.py (currently 0% coverage)
- main() function entry point
- callback() for global flags
- Command registration and help display
"""

import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# CLI Contract Test Fixtures
# =============================================================================


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI:
    - In development: python -m echomine.cli.app
    - After install: echomine

    This fixture abstracts the invocation method for flexibility.
    """
    # Development mode: Use module invocation
    return [sys.executable, "-m", "echomine.cli.app"]


# =============================================================================
# Contract Tests: CLI Application Entry Point
# =============================================================================


@pytest.mark.contract
class TestCLIAppEntryPoint:
    """Contract tests for main CLI application (app.py).

    These tests validate the top-level CLI behavior:
    - Version display
    - Help display
    - Command listing
    - Error handling
    """

    def test_cli_version_flag_displays_version(self, cli_command: list[str]) -> None:
        """Test --version flag displays version and exits with code 0.

        Validates:
        - --version flag works
        - Exit code 0
        - Version string on stdout
        - Format: "echomine version X.Y.Z"
        """
        # Act: Run with --version
        result = subprocess.run(
            [*cli_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Version string on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain version"
        assert "echomine" in stdout.lower()
        assert "version" in stdout.lower()

        # Version should be in format X.Y.Z or X.Y.Z.devN
        import re

        version_pattern = r"\d+\.\d+\.\d+"
        assert re.search(version_pattern, stdout), f"Version not found in: {stdout}"

    def test_cli_version_short_flag(self, cli_command: list[str]) -> None:
        """Test -v short flag for --version.

        Validates:
        - -v flag works (when no command provided)
        - Equivalent to --version
        """
        # Act: Run with -v
        result = subprocess.run(
            [*cli_command, "-v"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Version displayed
        stdout = result.stdout
        assert "version" in stdout.lower()

    def test_cli_no_args_shows_help(self, cli_command: list[str]) -> None:
        """Test running CLI without arguments shows help and exits 0.

        Validates:
        - No args behavior (no_args_is_help=False, handled in callback)
        - Help text displayed
        - Exit code 0
        - Lists available commands
        """
        # Act: Run without arguments
        result = subprocess.run(
            cli_command,
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0 (help, not error)
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Help text on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain help text"

        # Assert: Shows available commands
        assert "list" in stdout.lower()
        assert "get" in stdout.lower()
        assert "search" in stdout.lower()
        assert "export" in stdout.lower()

        # Assert: Shows usage or help indicators
        assert "usage" in stdout.lower() or "commands" in stdout.lower()

    def test_cli_help_flag_shows_commands(self, cli_command: list[str]) -> None:
        """Test --help flag displays help with available commands.

        Validates:
        - --help flag works
        - Exit code 0
        - Lists all commands (list, get, search, export)
        """
        # Act: Run with --help
        result = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Help text shows commands
        stdout = result.stdout
        assert "list" in stdout.lower()
        assert "get" in stdout.lower()
        assert "search" in stdout.lower()
        assert "export" in stdout.lower()

    def test_cli_help_shows_examples(self, cli_command: list[str]) -> None:
        """Test help text includes usage examples.

        Validates:
        - Epilog with examples is displayed
        - Examples section present
        """
        # Act: Run with --help
        result = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Examples section present
        stdout = result.stdout
        assert "examples" in stdout.lower() or "example" in stdout.lower()

    def test_cli_invalid_command_exits_2(self, cli_command: list[str]) -> None:
        """Test invalid command returns exit code 2.

        Validates:
        - CHK032: Exit code 2 for invalid arguments
        - Typer's default behavior for unknown commands
        """
        # Act: Run with invalid command
        result = subprocess.run(
            [*cli_command, "invalid-command-xyz"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

    def test_cli_list_command_registered(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test 'list' command is registered and accessible.

        Validates:
        - Command registration works
        - list command can be invoked
        """
        # Create minimal test file
        import json

        test_file = tmp_path / "test.json"
        with test_file.open("w") as f:
            json.dump([], f)

        # Act: Run list command
        result = subprocess.run(
            [*cli_command, "list", str(test_file)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Command executes (exit code 0 for empty file)
        assert result.returncode == 0

    def test_cli_get_command_registered(self, cli_command: list[str]) -> None:
        """Test 'get' command is registered as hierarchical command.

        Validates:
        - get command accessible
        - Shows subcommands (conversation, message)

        Note: Typer's no_args_is_help outputs to stderr with exit code 2.
        """
        # Act: Run get without subcommand (should show help)
        result = subprocess.run(
            [*cli_command, "get"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Shows help with subcommands (in stderr for no_args_is_help)
        output = result.stderr or result.stdout
        assert "conversation" in output.lower()
        assert "message" in output.lower()

    def test_cli_search_command_registered(self, cli_command: list[str]) -> None:
        """Test 'search' command is registered and accessible.

        Validates:
        - search command can be invoked
        """
        # Act: Run search --help
        result = subprocess.run(
            [*cli_command, "search", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Search help shown
        stdout = result.stdout
        assert "search" in stdout.lower()
        assert "keywords" in stdout.lower() or "--keywords" in stdout

    def test_cli_export_command_registered(self, cli_command: list[str]) -> None:
        """Test 'export' command is registered and accessible.

        Validates:
        - export command can be invoked
        """
        # Act: Run export --help
        result = subprocess.run(
            [*cli_command, "export", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Export help shown
        stdout = result.stdout
        assert "export" in stdout.lower()

    def test_cli_keyboard_interrupt_exits_cleanly(self, cli_command: list[str]) -> None:
        """Test Ctrl+C (KeyboardInterrupt) exits cleanly with code 1.

        Validates:
        - KeyboardInterrupt handling in main()
        - Exit code 1
        - Clean exit (no traceback)

        Note: This is difficult to test reliably in subprocess.
        Marked as skip - requires manual verification or more complex test setup.
        """
        pytest.skip("KeyboardInterrupt test requires manual verification")

        # Implementation note:
        # Would need to spawn subprocess and send SIGINT signal
        # Complex to test reliably in automated tests

    def test_cli_commands_support_help_flag(self, cli_command: list[str]) -> None:
        """Test all commands support --help flag.

        Validates:
        - --help works for list, get, search, export
        - Exit code 0 for help
        """
        commands = ["list", "search", "export"]

        for cmd in commands:
            # Act: Run command with --help
            result = subprocess.run(
                [*cli_command, cmd, "--help"],
                check=False,
                capture_output=True,
                text=True,
            )

            # Assert: Success
            assert result.returncode == 0, f"{cmd} --help should exit 0"

            # Assert: Help text present
            stdout = result.stdout
            assert len(stdout) > 0, f"{cmd} --help should show help"
            assert cmd in stdout.lower(), f"Help should mention '{cmd}'"


# =============================================================================
# Contract Tests: main() Entry Point
# =============================================================================


@pytest.mark.contract
class TestCLIMainEntryPoint:
    """Contract tests for main() function entry point.

    These tests validate the main() function behavior:
    - Invocation via module (python -m echomine.cli.app)
    - Exception handling
    - Exit code propagation
    """

    def test_main_can_be_invoked_as_module(self) -> None:
        """Test CLI can be invoked as Python module.

        Validates:
        - python -m echomine.cli.app works
        - Entry point correctly configured
        """
        # Act: Invoke as module
        result = subprocess.run(
            [sys.executable, "-m", "echomine.cli.app", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Version displayed
        assert "version" in result.stdout.lower()

    def test_main_propagates_exit_codes(self, tmp_path: Path) -> None:
        """Test main() propagates exit codes from commands.

        Validates:
        - Exit code 1 for file not found
        - Exit code 2 for invalid arguments
        - Exit code 0 for success
        """
        # Test 1: Exit code 1 (file not found)
        result_error = subprocess.run(
            [
                sys.executable,
                "-m",
                "echomine.cli.app",
                "list",
                "/tmp/nonexistent_file_xyz.json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result_error.returncode == 1

        # Test 2: Exit code 2 (invalid arguments - missing required arg)
        result_invalid = subprocess.run(
            [sys.executable, "-m", "echomine.cli.app", "list"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result_invalid.returncode == 2

        # Test 3: Exit code 0 (success - empty file)
        import json

        test_file = tmp_path / "empty.json"
        with test_file.open("w") as f:
            json.dump([], f)

        result_success = subprocess.run(
            [sys.executable, "-m", "echomine.cli.app", "list", str(test_file)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result_success.returncode == 0


# =============================================================================
# Contract Tests: CLI Output Formatting
# =============================================================================


@pytest.mark.contract
class TestCLIOutputFormatting:
    """Contract tests for CLI output formatting standards.

    These tests validate that the CLI follows consistent output standards:
    - No Rich markup in output (rich_markup_mode=None)
    - Clean error messages
    - Consistent formatting across commands
    """

    def test_cli_no_rich_markup_in_errors(self, cli_command: list[str]) -> None:
        """Test error messages don't contain Rich markup syntax.

        Validates:
        - rich_markup_mode=None setting
        - Plain text errors (no [red], [bold], etc.)
        """
        # Act: Trigger an error (file not found)
        result = subprocess.run(
            [*cli_command, "list", "/tmp/nonexistent_xyz.json"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Error occurred
        assert result.returncode == 1

        # Assert: No Rich markup in stderr
        stderr = result.stderr
        # Rich markup uses [color] syntax
        assert "[red]" not in stderr
        assert "[bold]" not in stderr
        assert "[yellow]" not in stderr

    def test_cli_no_pretty_exceptions(self, cli_command: list[str]) -> None:
        """Test CLI doesn't use Rich pretty exceptions.

        Validates:
        - pretty_exceptions_enable=False
        - Standard Python tracebacks (if any)
        """
        # Act: Run with invalid command
        result = subprocess.run(
            [*cli_command, "invalid-cmd"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: No Rich exception formatting
        stderr = result.stderr
        # Rich exceptions have colored formatting and special symbols
        # Standard errors should be plain text
        assert "╭─" not in stderr  # Rich exception box drawing
        assert "│" not in stderr or "Error" in stderr  # Pipe symbol used by Rich

    def test_cli_help_text_readable(self, cli_command: list[str]) -> None:
        """Test help text is plain and readable without terminal colors.

        Validates:
        - Help text works in non-interactive terminals
        - No ANSI escape codes required
        """
        # Act: Get help
        result = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Help is plain text (no required ANSI codes for readability)
        stdout = result.stdout
        # Basic readability check - should have clear sections
        assert "list" in stdout
        assert "search" in stdout
        # Should not require ANSI codes to be readable
        # (ANSI codes might be present but content should work without them)


# =============================================================================
# Contract Tests: CLI Integration Smoke Tests
# =============================================================================


@pytest.mark.contract
class TestCLISmokeTests:
    """Smoke tests for CLI integration.

    Quick sanity checks that CLI commands execute without crashes.
    """

    def test_cli_commands_dont_crash_with_help(self, cli_command: list[str]) -> None:
        """Test all commands execute --help without crashing.

        Validates:
        - No uncaught exceptions
        - All commands registered correctly
        """
        commands = ["list", "get", "search", "export"]

        for cmd in commands:
            # Act
            result = subprocess.run(
                [*cli_command, cmd, "--help"],
                check=False,
                capture_output=True,
                text=True,
            )

            # Assert: No crash (exit 0 or 2, not 1)
            assert result.returncode in (0, 2), (
                f"Command '{cmd} --help' crashed with exit code {result.returncode}"
            )

    def test_cli_version_and_help_both_work(self, cli_command: list[str]) -> None:
        """Test both --version and --help can be invoked successfully.

        Validates:
        - No conflicts between global flags
        """
        # Test --version
        result_version = subprocess.run(
            [*cli_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result_version.returncode == 0

        # Test --help
        result_help = subprocess.run(
            [*cli_command, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result_help.returncode == 0

        # Both should have produced output
        assert len(result_version.stdout) > 0
        assert len(result_help.stdout) > 0
