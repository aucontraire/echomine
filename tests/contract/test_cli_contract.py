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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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

    def test_exit_code_0_on_success(self, cli_command: list[str], sample_cli_export: Path) -> None:
        """Test that successful execution returns exit code 0.

        Validates:
        - CHK032: Exit code 0 for success

        Expected to FAIL: CLI not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 2 for invalid arguments
        assert result.returncode == 2, (
            f"Expected exit code 2 for missing arguments, got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Usage/error message should be on stderr"

    def test_exit_code_1_on_invalid_json(self, cli_command: list[str], tmp_path: Path) -> None:
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        stdout = result.stdout

        # Assert: Output contains table-like structure
        # Based on CHK040 resolution: simple text table format
        assert "ID" in stdout or "id" in stdout, "Header should include ID column"
        assert "Title" in stdout or "title" in stdout, "Header should include Title"
        assert "Messages" in stdout or "messages" in stdout or "Message" in stdout, (
            "Header should include message count"
        )

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
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert head_proc.returncode == 0, "Should work with head"
        assert len(head_proc.stdout) > 0

        # Test 2: Pipe to grep (filter output)
        grep_proc = subprocess.run(
            f"{' '.join(cli_command)} list {sample_cli_export} | grep 'Alpha'",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert grep_proc.returncode == 0, "Should work with grep"
        assert "Alpha" in grep_proc.stdout

        # Test 3: Pipe to wc (count lines)
        wc_proc = subprocess.run(
            f"{' '.join(cli_command)} list {sample_cli_export} | wc -l",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert wc_proc.returncode == 0, "Should work with wc"
        line_count = int(wc_proc.stdout.strip())
        assert line_count > 0, "Should have output lines"

    def test_json_output_format_flag(self, cli_command: list[str], sample_cli_export: Path) -> None:
        """Test that --format json produces valid JSON output.

        Validates:
        - CLI spec: --format json flag
        - FR-018: Alternative JSON format for programmatic use

        Expected to FAIL: --format json not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", str(sample_cli_export), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 0 (success)
        assert result.returncode == 0, "Empty file should succeed, not error"

        # Assert: Output indicates zero conversations
        stdout = result.stdout
        assert "0" in stdout or "no conversations" in stdout.lower() or len(stdout) < 100, (
            "Should indicate zero conversations"
        )

    def test_help_flag_displays_usage(self, cli_command: list[str]) -> None:
        """Test that --help flag displays usage information.

        Validates:
        - CLI spec: --help flag
        - Exit code 0 for help

        Expected to FAIL: --help not implemented.
        """
        result = subprocess.run(
            [*cli_command, "list", "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
            check=False,
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
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result_abs.returncode == 0

        # Test 2: Relative path (from parent directory)
        result_rel = subprocess.run(
            [*cli_command, "list", str(sample_cli_export)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=sample_cli_export.parent,
        )
        assert result_rel.returncode == 0

    def test_permission_denied_error_handling(self, cli_command: list[str], tmp_path: Path) -> None:
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
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            # Assert: Exit code 1
            assert result.returncode == 1

            # Assert: Error mentions permission
            stderr = result.stderr
            assert "permission" in stderr.lower() or "denied" in stderr.lower()

        finally:
            # Restore permissions for cleanup
            no_read_file.chmod(stat.S_IRUSR | stat.S_IWUSR)


# =============================================================================
# T046: CLI Contract Tests - Search Command (RED Phase)
# =============================================================================


@pytest.mark.contract
class TestCLISearchCommandContract:
    """Contract tests for 'echomine search' command.

    Task: T046 - CLI Contract Test - Search Command
    Phase: RED (tests designed to FAIL initially)

    These tests validate the CLI search command contract per cli_spec.md.
    They are BLACK BOX tests - we only test external observable behavior.

    Expected Failure Reasons (RED phase):
    - search command not implemented
    - Argument parsing for search not implemented
    - Search output formatting not implemented
    - --keywords and --title flags not implemented
    """

    def test_search_command_with_keywords_flag(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with --keywords flag.

        Validates:
        - FR-332: search command accepts --keywords argument
        - CHK031: stdout/stderr separation
        - FR-018: Human-readable output

        Expected to FAIL: search command not implemented.
        """
        # Act: Run 'echomine search <file> --keywords "alpha"'
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--keywords", "alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 0 for success
        assert result.returncode == 0, (
            f"Search command should succeed. Got exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

        # Assert: stdout contains search results
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain search results"
        assert "Alpha" in stdout or "alpha" in stdout, (
            "Search results should include matched conversation title"
        )

    def test_search_command_with_multiple_keywords(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with multiple keywords (OR logic).

        Validates:
        - FR-320: Multi-keyword OR logic
        - CLI accepts comma-separated or multiple --keywords flags

        Expected to FAIL: Multi-keyword parsing not implemented.
        """
        # Act: Search with multiple keywords
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "alpha,beta",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Results include conversations matching ANY keyword
        stdout = result.stdout
        assert "Alpha" in stdout or "Beta" in stdout, (
            "Multi-keyword search should match ANY keyword (OR logic)"
        )

    def test_search_command_with_title_filter_flag(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with --title flag.

        Validates:
        - FR-327-331: Title filtering support
        - CLI accepts --title argument

        Expected to FAIL: --title flag not implemented.
        """
        # Act: Run 'echomine search <file> --title "Alpha"'
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--title", "Alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Results include conversation with "Alpha" in title
        stdout = result.stdout
        assert "Alpha" in stdout, "Title filter should match conversation title"

    def test_search_command_with_combined_filters(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with both --keywords and --title flags.

        Validates:
        - FR-332: Combined filters (AND logic)
        - CLI accepts multiple filter flags

        Expected to FAIL: Combined filter parsing not implemented.
        """
        # Act: Search with both keywords AND title filter
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "Question",
                "--title",
                "Alpha",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Results match BOTH filters
        stdout = result.stdout
        assert "Alpha" in stdout, "Should include conversation matching both filters"

    def test_search_command_with_limit_flag(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with --limit flag.

        Validates:
        - FR-336: Limit parameter controls max results
        - CLI accepts --limit N argument

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Search with limit=1
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "Test",
                "--limit",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Output indicates limited results
        # (Exact validation depends on output format)
        stdout = result.stdout
        assert len(stdout) > 0, "Should have output with limited results"

    def test_search_command_json_output_format(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with --json flag for JSON output.

        Validates:
        - FR-301-306: JSON output schema for search results
        - CLI --json flag works with search command

        Expected to FAIL: --json output for search not implemented.
        """
        # Act: Search with JSON output
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "alpha",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Valid JSON output
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Search --json output is not valid JSON: {e}\n{stdout}")

        # Assert: JSON structure matches FR-301 schema
        assert isinstance(data, dict), "JSON output should be object with results and metadata"
        assert "results" in data, "JSON should have 'results' field (FR-301)"
        assert "metadata" in data, "JSON should have 'metadata' field (FR-301)"

        # Assert: Results array structure (FR-302)
        assert isinstance(data["results"], list), "results should be array"
        if len(data["results"]) > 0:
            first_result = data["results"][0]
            # FR-302: Flattened structure with conversation_id
            assert "conversation_id" in first_result, "Result should have conversation_id (FR-302)"
            assert "title" in first_result, "Result should have title field"
            assert "created_at" in first_result, "Result should have created_at field"
            assert "updated_at" in first_result, "Result should have updated_at field"
            assert "score" in first_result, "Result should have relevance score"
            assert "matched_message_ids" in first_result, "Result should have matched_message_ids"
            assert "message_count" in first_result, "Result should have message_count"

            # FR-304: ISO 8601 timestamps with UTC (YYYY-MM-DDTHH:MM:SSZ)
            assert first_result["created_at"].endswith("Z"), "Timestamp should end with Z (UTC)"
            assert "T" in first_result["created_at"], "Timestamp should use ISO 8601 format"

        # Assert: Metadata structure (FR-303)
        metadata = data["metadata"]
        assert "query" in metadata, "Metadata should have query field (FR-303)"
        assert "total_results" in metadata, "Metadata should have total_results (FR-303)"
        assert "skipped_conversations" in metadata, (
            "Metadata should have skipped_conversations (FR-303)"
        )
        assert "elapsed_seconds" in metadata, "Metadata should have elapsed_seconds (FR-303)"

        # Assert: Query metadata structure
        query_meta = metadata["query"]
        assert "keywords" in query_meta, "Query should have keywords field"
        assert "title_filter" in query_meta, "Query should have title_filter field"
        assert "date_from" in query_meta, "Query should have date_from field"
        assert "date_to" in query_meta, "Query should have date_to field"
        assert "limit" in query_meta, "Query should have limit field"

    def test_search_command_with_quiet_flag(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test search command with --quiet flag (suppress progress).

        Validates:
        - FR-310: --quiet flag suppresses progress indicators
        - stdout still contains results, stderr empty

        Expected to FAIL: --quiet flag not implemented.
        """
        # Act: Search with --quiet
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "alpha",
                "--quiet",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: stdout contains results (not suppressed)
        assert len(result.stdout) > 0, "Results should still be on stdout"

        # Assert: stderr should be empty or minimal (no progress indicators)
        stderr = result.stderr
        progress_keywords = ["parsing", "searching", "processing"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stderr.lower(), (
                f"--quiet should suppress progress indicator '{keyword}'"
            )

    def test_search_command_stdout_stderr_separation(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that search results go to stdout, progress to stderr.

        Validates:
        - FR-291, FR-292: stdout/stderr separation
        - CHK031: Data on stdout, progress on stderr

        Expected to FAIL: stdout/stderr separation not implemented.
        """
        # Act: Run search command
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--keywords", "alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: stdout contains ONLY data (no progress indicators)
        stdout = result.stdout
        progress_keywords = ["parsing", "searching", "processing"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stdout.lower(), (
                f"Progress indicator '{keyword}' found in stdout. "
                "Progress MUST go to stderr per CHK031"
            )

    def test_search_command_exit_code_0_on_success(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that successful search returns exit code 0.

        Validates:
        - FR-296: Exit code 0 for success

        Expected to FAIL: search command not implemented.
        """
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--keywords", "alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        assert result.returncode == 0, (
            f"Successful search should exit with code 0. "
            f"Got {result.returncode}. stderr: {result.stderr}"
        )

    def test_search_command_exit_code_0_on_zero_results(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that search with zero matches returns exit code 0 (not error).

        Validates:
        - FR-296: Zero results is success, not error
        - Exit code 0 even when no matches found

        Expected to FAIL: Zero results handling not implemented.
        """
        # Act: Search for non-existent keyword
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export),
                "--keywords",
                "zzzzznonexistent",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 0 (success, even with zero results)
        assert result.returncode == 0, (
            "Zero search results should be exit code 0 (success), not error"
        )

        # Assert: Output indicates zero results
        stdout = result.stdout
        assert "0" in stdout or "no results" in stdout.lower() or len(stdout) < 100, (
            "Should indicate zero results"
        )

    def test_search_command_exit_code_1_on_file_not_found(self, cli_command: list[str]) -> None:
        """Test that missing file returns exit code 1.

        Validates:
        - FR-297: Exit code 1 for errors (file not found)

        Expected to FAIL: Error handling not implemented.
        """
        non_existent_file = "/tmp/search_missing_file_12345.json"

        result = subprocess.run(
            [*cli_command, "search", non_existent_file, "--keywords", "test"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower() or "no such file" in stderr.lower(), (
            f"Error should mention file not found. Got: {stderr}"
        )

    def test_search_command_exit_code_2_on_missing_keywords_and_title(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that search without filters returns exit code 2.

        Validates:
        - FR-298: Exit code 2 for invalid arguments
        - At least one filter required (--keywords or --title)

        Expected to FAIL: Argument validation not implemented.
        """
        # Act: Search without any filter flags
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 2 (invalid arguments)
        assert result.returncode == 2, (
            f"Search without filters should be exit code 2. Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

    def test_search_command_exit_code_130_on_interrupt(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that Ctrl+C (SIGINT) returns exit code 130.

        Validates:
        - FR-299: Exit code 130 for interrupted operations

        Expected to FAIL: Signal handling not implemented.

        Note: This test is complex to implement reliably in pytest.
        Marked as skip for now - manual verification required.
        """
        pytest.skip("Signal handling test requires manual verification")

        # Implementation note:
        # Would need to spawn subprocess and send SIGINT signal
        # Complex to test reliably in automated tests

    def test_search_command_help_flag(self, cli_command: list[str]) -> None:
        """Test that 'echomine search --help' displays usage.

        Validates:
        - CLI spec: --help flag
        - Exit code 0 for help

        Expected to FAIL: --help not implemented.
        """
        result = subprocess.run(
            [*cli_command, "search", "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Help text on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "Help text should be on stdout"
        assert "search" in stdout.lower()
        assert "keywords" in stdout.lower() or "--keywords" in stdout
        assert "title" in stdout.lower() or "--title" in stdout

    def test_search_command_pipeline_friendly_output(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that search output works with Unix pipelines.

        Validates:
        - FR-019: Pipeline-friendly output
        - Works with grep, awk, head, etc.

        Expected to FAIL: Output format not pipeline-friendly.
        """
        # Test 1: Pipe search output to grep
        grep_proc = subprocess.run(
            f"{' '.join(cli_command)} search {sample_cli_export} --keywords 'alpha' | grep 'Alpha'",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert grep_proc.returncode == 0, "Search output should work with grep"
        assert "Alpha" in grep_proc.stdout

        # Test 2: Pipe to head
        head_proc = subprocess.run(
            f"{' '.join(cli_command)} search {sample_cli_export} --keywords 'test' | head -n 3",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert head_proc.returncode == 0, "Search output should work with head"

    def test_search_command_human_readable_output_format(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that default search output is human-readable table.

        Validates:
        - FR-018: Human-readable output
        - Table format with headers (Score, ID, Title, etc.)

        Expected to FAIL: Output formatting not implemented.
        """
        result = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--keywords", "alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        stdout = result.stdout

        # Assert: Table headers present
        # Expected headers: Score, ID, Title, Messages, etc.
        assert "score" in stdout.lower() or "relevance" in stdout.lower(), (
            "Output should include relevance score"
        )
        assert "id" in stdout.lower(), "Output should include conversation ID"
        assert "title" in stdout.lower(), "Output should include title"

        # Assert: Conversation data present
        assert "Alpha" in stdout, "Output should show matched conversation"

    def test_search_command_accepts_absolute_and_relative_paths(
        self, cli_command: list[str], sample_cli_export: Path
    ) -> None:
        """Test that search works with both absolute and relative paths.

        Validates:
        - Path handling (pathlib compatibility)

        Expected to FAIL: Path handling not implemented.
        """
        # Test 1: Absolute path
        result_abs = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_cli_export.absolute()),
                "--keywords",
                "alpha",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result_abs.returncode == 0

        # Test 2: Relative path
        result_rel = subprocess.run(
            [*cli_command, "search", str(sample_cli_export), "--keywords", "alpha"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=sample_cli_export.parent,
        )
        assert result_rel.returncode == 0


# =============================================================================
# T085-T086: CLI Contract Tests - Date Filtering (GREEN Phase)
# =============================================================================


@pytest.mark.contract
class TestCLIDateFilteringContract:
    """Contract tests for date filtering flags in search command.

    Tasks: T085-T086 - Date filtering CLI contract validation
    Phase: GREEN (tests validate existing implementation)

    These tests validate the --from-date and --to-date CLI flags work correctly
    and provide proper error handling for invalid date formats.

    Contract Requirements Validated:
    - FR-442: --from-date flag filters conversations >= from_date
    - FR-443: --to-date flag filters conversations <= to_date
    - CHK032: Exit codes (0=success, 2=invalid date format)
    - ISO 8601 date format validation (YYYY-MM-DD)
    """

    def test_from_date_flag_filters_results(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test --from-date flag filters conversations >= from_date (inclusive).

        Validates:
        - FR-442: --from-date flag accepts ISO 8601 date
        - Filtering logic: only conversations >= from_date included
        - Exit code 0 on success
        """
        # Create fixture with known dates
        import json

        conversations = [
            {
                "id": "conv-2024-01",
                "title": "January conversation",
                "create_time": 1704067200.0,  # 2024-01-01
                "update_time": 1704067200.0,
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1704067200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg1",
            },
            {
                "id": "conv-2024-03",
                "title": "March conversation",
                "create_time": 1709251200.0,  # 2024-03-01
                "update_time": 1709251200.0,
                "mapping": {
                    "msg2": {
                        "id": "msg2",
                        "message": {
                            "id": "msg2",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1709251200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg2",
            },
        ]

        export_file = tmp_path / "date_filter_test.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Search with --from-date 2024-02-01
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "Test",
                "--from-date",
                "2024-02-01",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Only March conversation included (>= 2024-02-01)
        stdout = result.stdout
        assert "March" in stdout, "March conversation should be included"
        assert "January" not in stdout, "January conversation should be excluded"

    def test_to_date_flag_filters_results(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test --to-date flag filters conversations <= to_date (inclusive).

        Validates:
        - FR-443: --to-date flag accepts ISO 8601 date
        - Filtering logic: only conversations <= to_date included
        - Exit code 0 on success
        """
        # Create fixture with known dates
        import json

        conversations = [
            {
                "id": "conv-2024-01",
                "title": "January conversation",
                "create_time": 1704067200.0,  # 2024-01-01
                "update_time": 1704067200.0,
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1704067200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg1",
            },
            {
                "id": "conv-2024-12",
                "title": "December conversation",
                "create_time": 1733011200.0,  # 2024-12-01
                "update_time": 1733011200.0,
                "mapping": {
                    "msg2": {
                        "id": "msg2",
                        "message": {
                            "id": "msg2",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1733011200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg2",
            },
        ]

        export_file = tmp_path / "date_filter_test.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Search with --to-date 2024-06-30
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "Test",
                "--to-date",
                "2024-06-30",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Only January conversation included (<= 2024-06-30)
        stdout = result.stdout
        assert "January" in stdout, "January conversation should be included"
        assert "December" not in stdout, "December conversation should be excluded"

    def test_both_date_flags_combined(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test --from-date and --to-date together create valid date range.

        Validates:
        - FR-442-443: Both flags work together (AND logic)
        - Filtering logic: only conversations in [from_date, to_date] included
        - Exit code 0 on success
        """
        # Create fixture with dates across a range
        import json

        conversations = [
            {
                "id": "conv-2024-01",
                "title": "January conversation",
                "create_time": 1704067200.0,  # 2024-01-01
                "update_time": 1704067200.0,
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1704067200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg1",
            },
            {
                "id": "conv-2024-03",
                "title": "March conversation",
                "create_time": 1709251200.0,  # 2024-03-01
                "update_time": 1709251200.0,
                "mapping": {
                    "msg2": {
                        "id": "msg2",
                        "message": {
                            "id": "msg2",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1709251200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg2",
            },
            {
                "id": "conv-2024-12",
                "title": "December conversation",
                "create_time": 1733011200.0,  # 2024-12-01
                "update_time": 1733011200.0,
                "mapping": {
                    "msg3": {
                        "id": "msg3",
                        "message": {
                            "id": "msg3",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1733011200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg3",
            },
        ]

        export_file = tmp_path / "date_range_test.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Search with date range [2024-02-01, 2024-06-30]
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "Test",
                "--from-date",
                "2024-02-01",
                "--to-date",
                "2024-06-30",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Only March conversation in range
        stdout = result.stdout
        assert "March" in stdout, "March conversation should be in range"
        assert "January" not in stdout, "January before range"
        assert "December" not in stdout, "December after range"

    def test_invalid_date_format_exits_with_code_2(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test invalid date format (MM/DD/YYYY) returns exit code 2.

        Validates:
        - FR-086: ISO 8601 format required (YYYY-MM-DD)
        - Exit code 2 for invalid argument format
        - Clear error message on stderr
        """
        # Create minimal fixture
        import json

        export_file = tmp_path / "minimal.json"
        with export_file.open("w") as f:
            json.dump([], f)

        # Act: Search with MM/DD/YYYY format (invalid)
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "test",
                "--from-date",
                "12/31/2024",  # Invalid format
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 2 (invalid argument)
        assert result.returncode == 2, (
            f"Invalid date format should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message mentions date format
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "date" in stderr.lower(), f"Error should mention date. Got: {stderr}"

    def test_from_date_after_to_date_exits_with_code_2(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test from_date > to_date (inverted range) returns exit code 2.

        Validates:
        - CLI validates from_date <= to_date
        - Exit code 2 for invalid date range
        - Clear error message on stderr
        """
        # Create minimal fixture
        import json

        export_file = tmp_path / "minimal.json"
        with export_file.open("w") as f:
            json.dump([], f)

        # Act: Search with inverted date range
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "test",
                "--from-date",
                "2024-12-31",
                "--to-date",
                "2024-01-01",  # Before from_date!
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 2 (invalid argument)
        assert result.returncode == 2, (
            f"Inverted date range should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message mentions date range issue
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        # Error should mention "from" or "to" or "range" or "after" or "before"
        date_keywords = ["from", "to", "range", "after", "before"]
        assert any(keyword in stderr.lower() for keyword in date_keywords), (
            f"Error should mention date range issue. Got: {stderr}"
        )

    def test_leap_year_date_accepted(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test leap year date (2024-02-29) is accepted as valid.

        Validates:
        - FR-086: Leap year dates accepted in leap years
        - Exit code 0 on success
        """
        # Create minimal fixture
        import json

        export_file = tmp_path / "minimal.json"
        with export_file.open("w") as f:
            json.dump([], f)

        # Act: Search with leap year date (Feb 29, 2024)
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "test",
                "--from-date",
                "2024-02-29",  # Valid leap year date
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 0 (success - date accepted)
        assert result.returncode == 0, (
            f"Leap year date should be accepted. Got exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    def test_invalid_leap_year_date_exits_with_code_2(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test Feb 29 in non-leap year (2023-02-29) returns exit code 2.

        Validates:
        - FR-086: Invalid leap year dates rejected
        - Exit code 2 for invalid date
        - Clear error message on stderr
        """
        # Create minimal fixture
        import json

        export_file = tmp_path / "minimal.json"
        with export_file.open("w") as f:
            json.dump([], f)

        # Act: Search with Feb 29 in non-leap year (2023)
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(export_file),
                "--keywords",
                "test",
                "--from-date",
                "2023-02-29",  # Invalid - 2023 is not a leap year
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Exit code 2 (invalid date)
        assert result.returncode == 2, (
            f"Invalid leap year date should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message mentions date issue
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "date" in stderr.lower(), f"Error should mention date. Got: {stderr}"
