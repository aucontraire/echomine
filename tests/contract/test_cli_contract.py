"""Contract tests for CLI interface compliance.

Task: T027 - CLI Contract Test - List command contract validation
Phase: RED (tests designed to FAIL initially)

This module validates CLI interface contract compliance per cli_spec.md.
These are BLACK BOX tests - we invoke the CLI as subprocess and validate
external behavior (stdout, stderr, exit codes, output format).

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the CLI adheres to its published interface contract.

Contract Requirements Validated:
- CHK031: stdout/stderr separation (data on stdout, progress on stderr)
- CHK032: Exit codes (0=success, 1=error, 2=invalid input)
- FR-018: Human-readable output format (simple text table)
- FR-019: Pipeline-friendly output (works with grep, awk, head)

Architectural Coverage:
- CLI entry point → argument parsing → output formatting
- Unix composability and pipeline integration
- Error message clarity and actionability
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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
    # After installation, could switch to: ["echomine"]
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def sample_cli_export(tmp_path: Path) -> Path:
    """Create sample export for CLI testing (3 conversations).

    Smaller than integration test fixtures - just enough to validate
    CLI output format and contract compliance.
    """
    import json

    conversations = [
        {
            "id": "cli-conv-001",
            "title": "Test Conversation Alpha",
            "create_time": 1710000000.0,
            "update_time": 1710000100.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Question 1"]},
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-1",
        },
        {
            "id": "cli-conv-002",
            "title": "Test Conversation Beta",
            "create_time": 1710100000.0,
            "update_time": 1710100200.0,
            "mapping": {
                "msg-2-1": {
                    "id": "msg-2-1",
                    "message": {
                        "id": "msg-2-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Question 2"]},
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-2-2"],
                },
                "msg-2-2": {
                    "id": "msg-2-2",
                    "message": {
                        "id": "msg-2-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Answer 2"]},
                        "create_time": 1710100100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-2-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-2-2",
        },
        {
            "id": "cli-conv-003",
            "title": "Test Conversation Gamma",
            "create_time": 1710200000.0,
            "update_time": 1710200300.0,
            "mapping": {
                "msg-3-1": {
                    "id": "msg-3-1",
                    "message": {
                        "id": "msg-3-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Question 3"]},
                        "create_time": 1710200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-3-2", "msg-3-3"],
                },
                "msg-3-2": {
                    "id": "msg-3-2",
                    "message": {
                        "id": "msg-3-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Answer 3a"]},
                        "create_time": 1710200100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-3-1",
                    "children": [],
                },
                "msg-3-3": {
                    "id": "msg-3-3",
                    "message": {
                        "id": "msg-3-3",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Answer 3b"]},
                        "create_time": 1710200200.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-3-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-3-3",
        },
    ]

    export_file = tmp_path / "cli_test_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


# =============================================================================
# T027: CLI Contract Tests - stdout/stderr/exit codes (RED Phase)
# =============================================================================


@pytest.mark.contract
class TestCLIListCommandContract:
    """Contract tests for 'echomine list' command.

    These tests validate the CLI contract as specified in cli_spec.md.
    They are BLACK BOX tests - we only test external observable behavior.

    Expected Failure Reasons (RED phase):
    - CLI entry point (cli.app) doesn't exist
    - list command not implemented
    - Argument parsing not implemented
    - Output formatting not implemented
    """

    def test_stdout_contains_conversation_data_on_success(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that successful list writes conversation data to stdout.

        Validates:
        - CHK031: Data output goes to stdout
        - FR-018: Human-readable format

        Expected to FAIL: CLI not implemented yet.
        """
        # Act: Run 'echomine list <file>'
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0 for success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: stdout contains conversation data
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain output"
        assert "Test Conversation Alpha" in stdout
        assert "Test Conversation Beta" in stdout
        assert "Test Conversation Gamma" in stdout

        # Assert: stderr should be empty or only contain progress (no errors)
        stderr = result.stderr
        if stderr:
            # Progress indicators are allowed on stderr
            assert "error" not in stderr.lower(), f"Unexpected error in stderr: {stderr}"

    def test_stderr_used_for_progress_indicators(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that progress/status messages go to stderr, not stdout.

        Validates:
        - CHK031: Progress messages on stderr
        - FR-019: stdout reserved for data (pipeline-friendly)

        Expected to FAIL: Progress indicator not implemented.
        """
        # For small files, progress may not appear. This test verifies
        # that IF progress is shown, it goes to stderr.

        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            capture_output=True,
            text=True,
        )

        # Assert: stdout should ONLY contain conversation data
        # No "Parsing...", "Processing...", etc.
        stdout = result.stdout
        progress_keywords = ["parsing", "processing", "loading", "reading"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stdout.lower(), (
                f"Progress indicator '{keyword}' found in stdout. "
                "Progress MUST go to stderr per CHK031"
            )

    def test_exit_code_0_on_success(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that successful execution returns exit code 0.

        Validates:
        - CHK032: Exit code 0 for success

        Expected to FAIL: CLI not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Expected exit code 0 for successful list. Got {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    def test_exit_code_1_on_file_not_found(self, cli_command: list[str]) -> None:
        """Test that missing file returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for errors (file not found)
        - FR-033: Clear error messages

        Expected to FAIL: Error handling not implemented.
        """
        non_existent_file = "/tmp/this_file_does_not_exist_12345.json"

        result = subprocess.run(
            [*cli_command, "list", non_existent_file],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower() or "no such file" in stderr.lower(), (
            f"Error message should mention file not found. Got: {stderr}"
        )

        # Assert: stdout should be empty on error
        assert len(result.stdout) == 0, "stdout should be empty on error"

    def test_exit_code_2_on_invalid_arguments(self, cli_command: list[str]) -> None:
        """Test that invalid arguments return exit code 2.

        Validates:
        - CHK032: Exit code 2 for invalid input

        Expected to FAIL: Argument validation not implemented.
        """
        # Missing required file argument
        result = subprocess.run(
            [*cli_command, "list"],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2 for invalid arguments
        assert result.returncode == 2, (
            f"Expected exit code 2 for missing arguments, got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Usage/error message should be on stderr"

    def test_exit_code_1_on_invalid_json(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that malformed JSON returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for parse errors
        - FR-033: Fail fast on invalid JSON

        Expected to FAIL: JSON validation not implemented.
        """
        # Create malformed JSON file
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{invalid json syntax")

        result = subprocess.run(
            [*cli_command, "list", str(malformed_file)],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert "json" in stderr.lower() or "parse" in stderr.lower(), (
            f"Error should mention JSON/parse error. Got: {stderr}"
        )

    def test_human_readable_output_format(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that default output is human-readable text table.

        Validates:
        - FR-018: Human-readable output
        - CHK040: Simple text table format (no Rich dependency)

        Expected to FAIL: Output formatting not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            capture_output=True,
            text=True,
        )

        stdout = result.stdout

        # Assert: Output contains table-like structure
        # Based on CHK040 resolution: simple text table format
        assert "ID" in stdout or "id" in stdout, "Header should include ID column"
        assert "Title" in stdout or "title" in stdout, "Header should include Title"
        assert (
            "Messages" in stdout or "messages" in stdout or "Message" in stdout
        ), "Header should include message count"

        # Verify conversation data is present
        assert "cli-conv-001" in stdout
        assert "Test Conversation Alpha" in stdout

    def test_pipeline_friendly_output(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that output works with Unix pipelines (grep, awk, head).

        Validates:
        - FR-019: Pipeline-friendly output
        - CHK040: Works with grep, awk, head

        Expected to FAIL: Output format not implemented.
        """
        # Test 1: Pipe to head (get first N lines)
        head_proc = subprocess.run(
            f"{' '.join(cli_command)} list {sample_cli_export} | head -n 5",
            shell=True,
            capture_output=True,
            text=True,
        )
        assert head_proc.returncode == 0, "Should work with head"
        assert len(head_proc.stdout) > 0

        # Test 2: Pipe to grep (filter output)
        grep_proc = subprocess.run(
            f"{' '.join(cli_command)} list {sample_cli_export} | grep 'Alpha'",
            shell=True,
            capture_output=True,
            text=True,
        )
        assert grep_proc.returncode == 0, "Should work with grep"
        assert "Alpha" in grep_proc.stdout

        # Test 3: Pipe to wc (count lines)
        wc_proc = subprocess.run(
            f"{' '.join(cli_command)} list {sample_cli_export} | wc -l",
            shell=True,
            capture_output=True,
            text=True,
        )
        assert wc_proc.returncode == 0, "Should work with wc"
        line_count = int(wc_proc.stdout.strip())
        assert line_count > 0, "Should have output lines"

    def test_json_output_format_flag(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that --format json produces valid JSON output.

        Validates:
        - CLI spec: --format json flag
        - FR-018: Alternative JSON format for programmatic use

        Expected to FAIL: --format json not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export), "--format", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"JSON output failed: {result.stderr}"

        # Assert: stdout contains valid JSON
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{stdout}")

        # Verify JSON structure
        assert isinstance(data, list), "JSON output should be array of conversations"
        assert len(data) == 3, "Should have 3 conversations"

        # Verify first conversation structure
        first_conv = data[0]
        assert "id" in first_conv
        assert "title" in first_conv
        assert "created_at" in first_conv
        assert "message_count" in first_conv

    def test_empty_file_succeeds_with_zero_conversations(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that empty export file succeeds (not error).

        Validates:
        - Edge case: Empty file is valid, returns 0 results
        - Exit code 0 (success, not error)

        Expected to FAIL: Empty file handling not implemented.
        """
        import json

        empty_file = tmp_path / "empty.json"
        with empty_file.open("w") as f:
            json.dump([], f)

        result = subprocess.run(
            [*cli_command, "list", str(empty_file)],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0 (success)
        assert result.returncode == 0, "Empty file should succeed, not error"

        # Assert: Output indicates zero conversations
        stdout = result.stdout
        assert (
            "0" in stdout or "no conversations" in stdout.lower() or len(stdout) < 100
        ), "Should indicate zero conversations"

    def test_help_flag_displays_usage(self, cli_command: list[str]) -> None:
        """Test that --help flag displays usage information.

        Validates:
        - CLI spec: --help flag
        - Exit code 0 for help

        Expected to FAIL: --help not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", "--help"],
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0, "Help should exit with code 0"

        # Assert: Help text on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "Help text should be on stdout"
        assert "list" in stdout.lower(), "Help should mention 'list' command"
        assert "usage" in stdout.lower() or "options" in stdout.lower(), (
            "Help should show usage/options"
        )


# =============================================================================
# Additional Contract Tests
# =============================================================================


@pytest.mark.contract
class TestCLIContractEdgeCases:
    """Additional CLI contract edge cases."""

    def test_unicode_in_output_does_not_break_display(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that Unicode content displays correctly.

        Validates:
        - CHK126: UTF-8 encoding assumption
        - Unicode handling in output

        Expected to FAIL: Unicode handling not implemented.
        """
        import json

        unicode_conversation = {
            "id": "unicode-conv",
            "title": "测试会话 🚀 Test Émojis",
            "create_time": 1710000000.0,
            "update_time": 1710000100.0,
            "mapping": {
                "msg-u1": {
                    "id": "msg-u1",
                    "message": {
                        "id": "msg-u1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello 世界"]},
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-u1",
        }

        unicode_file = tmp_path / "unicode_export.json"
        with unicode_file.open("w", encoding="utf-8") as f:
            json.dump([unicode_conversation], f, ensure_ascii=False)

        result = subprocess.run(
            [*cli_command, "list", str(unicode_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Should not crash and should display Unicode
        assert result.returncode == 0
        assert "测试会话" in result.stdout or "Test" in result.stdout

    def test_absolute_and_relative_paths_work(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that both absolute and relative file paths work.

        Validates:
        - Path handling (pathlib compatibility)
        - Works from different working directories

        Expected to FAIL: Path handling not implemented.
        """
        # Test 1: Absolute path
        result_abs = subprocess.run(
            [*cli_command, "list", str(sample_cli_export.absolute())],
            capture_output=True,
            text=True,
        )
        assert result_abs.returncode == 0

        # Test 2: Relative path (from parent directory)
        result_rel = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            capture_output=True,
            text=True,
            cwd=sample_cli_export.parent,
        )
        assert result_rel.returncode == 0

    def test_permission_denied_error_handling(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that permission denied errors are handled gracefully.

        Validates:
        - FR-033: Clear error messages for permission errors
        - Exit code 1

        Expected to FAIL: Permission error handling not implemented.

        Note: Skipped on Windows (permission model different).
        """
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        import json
        import stat

        # Create file without read permissions
        no_read_file = tmp_path / "no_read.json"
        with no_read_file.open("w") as f:
            json.dump([], f)

        # Remove read permission
        no_read_file.chmod(stat.S_IWUSR)  # Write-only

        try:
            result = subprocess.run(
                [*cli_command, "list", str(no_read_file)],
                capture_output=True,
                text=True,
            )

            # Assert: Exit code 1
            assert result.returncode == 1

            # Assert: Error mentions permission
            stderr = result.stderr
            assert "permission" in stderr.lower() or "denied" in stderr.lower()

        finally:
            # Restore permissions for cleanup
            no_read_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
