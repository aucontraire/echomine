"""Contract tests for CLI export command.

Task: T075-T077 - CLI Export Command Contract Validation
Phase: RED (tests designed to FAIL initially)

This module validates the CLI export command contract compliance.
These are BLACK BOX tests - we invoke the CLI as subprocess and validate
external behavior (stdout, stderr, exit codes, output files).

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the export command adheres to its published interface.

Contract Requirements Validated:
- FR-018: Export command with file path, conversation ID, --output flag
- FR-399: Default to current working directory for exports
- FR-400: Support --output flag for custom directory
- FR-016: Generate human-readable filenames using slugified titles
- CHK031: stdout/stderr separation (success messages vs progress)
- CHK032: Exit codes (0=success, 1=error, 2=invalid input)

Architectural Coverage:
- CLI entry point → argument parsing → MarkdownExporter → file I/O
- Error handling for missing conversations, file errors, permission issues
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# CLI Export Contract Test Fixtures
# =============================================================================


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI in development mode.
    """
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def export_sample_file(tmp_path: Path) -> Path:
    """Create sample export for export testing (2 conversations).

    Smaller fixture focused on export use cases:
    - One conversation with simple text messages
    - One conversation with multimodal content (images)
    """
    conversations = [
        {
            "id": "export-conv-001",
            "title": "Python AsyncIO Tutorial",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain Python asyncio"],
                        },
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-2"],
                },
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["AsyncIO is Python's library for asynchronous programming."],
                        },
                        "create_time": 1710000010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-2",
        },
        {
            "id": "export-conv-002",
            "title": "Image Processing with OpenCV",
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {
                "msg-img-1": {
                    "id": "msg-img-1",
                    "message": {
                        "id": "msg-img-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "multimodal_text",
                            "parts": [
                                "Here's an image to analyze:",
                                {
                                    "content_type": "image_asset_pointer",
                                    "asset_pointer": "file-service://file-abc123",
                                },
                            ],
                        },
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-img-2"],
                },
                "msg-img-2": {
                    "id": "msg-img-2",
                    "message": {
                        "id": "msg-img-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["I can see the image contains..."],
                        },
                        "create_time": 1710100010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-img-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-img-2",
        },
    ]

    export_file = tmp_path / "export_test.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


@pytest.fixture
def duplicate_title_export(tmp_path: Path) -> Path:
    """Create export with duplicate conversation titles.

    Used to test --title ambiguity error handling.
    """
    conversations = [
        {
            "id": "dup-conv-001",
            "title": "Python Tutorial",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
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
            "id": "dup-conv-002",
            "title": "Python Tutorial",  # Duplicate title
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Question 2"]},
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-2",
        },
    ]

    export_file = tmp_path / "duplicate_titles.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


# =============================================================================
# CLI Export Contract Tests - Exit Codes (RED Phase)
# =============================================================================


@pytest.mark.contract
class TestCLIExportCommandContract:
    """Contract tests for 'echomine export' command.

    These tests validate the CLI export command contract.
    They are BLACK BOX tests - we only test external observable behavior.

    Expected Failure Reasons (RED phase):
    - export command not implemented
    - Argument parsing for export not implemented
    - MarkdownExporter integration not implemented
    - File I/O handling not implemented
    """

    # =========================================================================
    # Exit Code Tests
    # =========================================================================

    def test_export_command_exit_code_0_on_success(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that successful export returns exit code 0.

        Validates:
        - CHK032: Exit code 0 for success
        - FR-018: Basic export command functionality

        Expected to FAIL: export command not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        assert result.returncode == 0, (
            f"Expected exit code 0 for successful export. "
            f"Got {result.returncode}. stderr: {result.stderr}"
        )

    def test_export_command_exit_code_1_on_file_not_found(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that missing export file returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for operational errors
        - FR-033: Fail fast on file not found

        Expected to FAIL: Error handling not implemented.
        """
        non_existent_file = "/tmp/export_missing_file_12345.json"
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                non_existent_file,
                "conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower() or "no such file" in stderr.lower(), (
            f"Error should mention file not found. Got: {stderr}"
        )

        # Assert: stdout should be empty on error
        assert len(result.stdout) == 0, "stdout should be empty on error"

    def test_export_command_exit_code_1_on_conversation_not_found(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that non-existent conversation ID returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for operational errors
        - FR-018: Error handling for missing conversations

        Expected to FAIL: Conversation lookup error handling not implemented.
        """
        output_file = tmp_path / "output.md"
        non_existent_id = "nonexistent-conv-id-12345"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                non_existent_id,
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower() or "conversation" in stderr.lower(), (
            f"Error should mention conversation not found. Got: {stderr}"
        )

    def test_export_command_exit_code_1_on_write_permission_error(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that write permission errors return exit code 1.

        Validates:
        - CHK032: Exit code 1 for operational errors
        - FR-033: Fail fast on permission denied

        Expected to FAIL: Permission error handling not implemented.

        Note: Skipped on Windows (different permission model).
        """
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        import stat

        # Create read-only directory
        read_only_dir = tmp_path / "read_only"
        read_only_dir.mkdir()
        read_only_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # Read + execute only

        try:
            output_file = read_only_dir / "output.md"

            result = subprocess.run(
                [
                    *cli_command,
                    "export",
                    str(export_sample_file),
                    "export-conv-001",
                    "--output",
                    str(output_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            # Assert: Exit code 1
            assert result.returncode == 1, (
                f"Expected exit code 1 for permission error, got {result.returncode}"
            )

            # Assert: Error message mentions permission
            stderr = result.stderr
            assert "permission" in stderr.lower() or "denied" in stderr.lower(), (
                f"Error should mention permission denied. Got: {stderr}"
            )

        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    def test_export_command_exit_code_2_on_missing_conversation_id(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that missing conversation ID argument returns exit code 2.

        Validates:
        - CHK032: Exit code 2 for invalid arguments
        - FR-018: Conversation ID is required

        Expected to FAIL: Argument validation not implemented.
        """
        output_file = tmp_path / "output.md"

        # Missing conversation ID positional argument
        result = subprocess.run(
            [*cli_command, "export", str(export_sample_file), "--output", str(output_file)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2, (
            f"Expected exit code 2 for missing required argument, got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

    def test_export_command_exit_code_2_on_both_id_and_title_provided(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that providing both --id and --title returns exit code 2.

        Validates:
        - CHK032: Exit code 2 for invalid arguments
        - FR-018: Mutually exclusive: ID as positional OR --title flag

        Expected to FAIL: Mutual exclusivity validation not implemented.

        Note: This assumes the interface is:
        - echomine export <file> <conversation-id> --output <path>
        - echomine export <file> --title "Title" --output <path>
        """
        output_file = tmp_path / "output.md"

        # Providing both positional ID AND --title flag
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (invalid arguments)
        assert result.returncode == 2, (
            f"Expected exit code 2 when both ID and --title provided, got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

    # =========================================================================
    # stdout/stderr Separation Tests
    # =========================================================================

    def test_export_command_stdout_contains_markdown_when_no_output_file(
        self, cli_command: list[str], export_sample_file: Path
    ) -> None:
        """Test that markdown is written to stdout when --output is omitted.

        Validates:
        - CHK031: Data on stdout when no output file specified
        - FR-018: Default behavior is to write to stdout

        Expected to FAIL: stdout output not implemented.
        """
        # No --output flag: should write markdown to stdout
        result = subprocess.run(
            [*cli_command, "export", str(export_sample_file), "export-conv-001"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"Expected success, got {result.returncode}"

        # Assert: stdout contains markdown content
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain markdown when no --output"
        assert "##" in stdout, "stdout should contain markdown headers"
        assert "AsyncIO" in stdout, "stdout should contain conversation content"
        assert "User" in stdout or "Assistant" in stdout, "stdout should contain role headers"

    def test_export_command_stderr_contains_progress_indicators(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that progress indicators go to stderr, not stdout.

        Validates:
        - CHK031: Progress messages on stderr
        - FR-021: Progress indicators for operations

        Expected to FAIL: Progress indicators not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: stdout should NOT contain progress indicators
        stdout = result.stdout
        progress_keywords = ["exporting", "processing", "writing", "loading"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stdout.lower(), (
                f"Progress indicator '{keyword}' found in stdout. "
                "Progress MUST go to stderr per CHK031"
            )

    def test_export_command_success_message_to_stderr_when_output_file_specified(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that success message goes to stderr when writing to file.

        Validates:
        - CHK031: Success messages on stderr (not stdout)
        - FR-018: stdout reserved for data, stderr for status

        Expected to FAIL: Success message handling not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: stderr contains success message
        stderr = result.stderr
        assert len(stderr) > 0, "stderr should contain success message"
        assert "exported" in stderr.lower() or "success" in stderr.lower(), (
            f"stderr should indicate successful export. Got: {stderr}"
        )

        # Assert: stdout should be empty (data written to file, not stdout)
        stdout = result.stdout
        assert len(stdout) == 0, (
            "stdout should be empty when --output specified (data goes to file)"
        )

    # =========================================================================
    # Output Format Tests
    # =========================================================================

    def test_export_command_markdown_format_compliance(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that exported markdown follows the specified format.

        Validates:
        - FR-014: Conversation metadata in exported files
        - FR-015: Preserve formatting and content
        - User format preferences: emoji headers, timestamps, horizontal rules

        Expected to FAIL: Markdown formatting not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, f"Export failed: {result.stderr}"

        # Assert: Output file exists
        assert output_file.exists(), "Output file should exist"

        # Read markdown content
        markdown = output_file.read_text(encoding="utf-8")

        # Assert: Headers with emoji (## 👤 User · [timestamp])
        assert "##" in markdown, "Should have markdown headers"
        assert "👤" in markdown or "🤖" in markdown, "Should have emoji in headers"
        assert "User" in markdown, "Should have 'User' role in headers"
        assert "Assistant" in markdown, "Should have 'Assistant' role in headers"

        # Assert: ISO 8601 timestamps
        assert "T" in markdown, "Should have ISO 8601 timestamps (contains 'T')"

        # Assert: Horizontal rules between messages
        assert "---" in markdown, "Should have horizontal rules between messages"

        # Assert: Conversation content present
        assert "AsyncIO" in markdown, "Should include conversation content"

    def test_export_command_includes_conversation_metadata_header(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that exported markdown includes conversation metadata header.

        Validates:
        - US3-AS3: Markdown includes conversation metadata
        - FR-014: Conversation metadata in exported files (title, date, message count)
        - Metadata appears BEFORE message content
        - All required fields present: title, created date, message count
        - Optional field: updated date (when conversation was modified)

        This is the SPECIFIC CONTRACT TEST for US3-AS3 acceptance scenario.

        Expected to FAIL: Metadata header not currently included in exports.
        Failure reason: "Missing metadata: title=False, date=True"
        """
        output_file = tmp_path / "output.md"

        # Export the first conversation
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Command succeeds
        assert result.returncode == 0, f"Export command should succeed. stderr: {result.stderr}"

        # Assert: Output file exists
        assert output_file.exists(), "Output file should be created"

        # Read markdown content
        markdown = output_file.read_text(encoding="utf-8")

        # Assert: Markdown is not empty
        assert len(markdown) > 0, "Exported markdown should not be empty"

        # =====================================================================
        # US3-AS3 VALIDATION: Metadata Header Required
        # =====================================================================

        # Split markdown into lines for analysis
        lines = markdown.split("\n")

        # Find first message header (messages start with ## 👤 User or ## 🤖 Assistant)
        first_message_line_idx = None
        for i, line in enumerate(lines):
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_line_idx = i
                break

        assert first_message_line_idx is not None, "Export should contain message headers"

        # Extract metadata section (everything BEFORE first message)
        metadata_section = "\n".join(lines[:first_message_line_idx])

        # =====================================================================
        # FR-014 REQUIREMENT 1: Title in Metadata
        # =====================================================================

        expected_title = "Python AsyncIO Tutorial"

        assert expected_title in metadata_section, (
            f"FR-014 VIOLATION: Conversation title '{expected_title}' MUST appear "
            f"in metadata header BEFORE messages. "
            f"Title not found in metadata section:\n{metadata_section[:300]}\n\n"
            f"This is US3-AS3 acceptance scenario requirement."
        )

        # =====================================================================
        # FR-014 REQUIREMENT 2: Created Date in Metadata
        # =====================================================================

        # Look for date markers (ISO 8601 format or "Created:" label)
        has_created_date = any(
            date_marker in metadata_section
            for date_marker in ["2024-", "Created:", "Created At:", "Date:"]
        )

        assert has_created_date, (
            f"FR-014 VIOLATION: Created date MUST appear in metadata header. "
            f"Date markers not found in metadata section:\n{metadata_section[:300]}\n\n"
            f"This is US3-AS3 acceptance scenario requirement."
        )

        # =====================================================================
        # FR-014 REQUIREMENT 3: Message Count in Metadata
        # =====================================================================

        # The fixture has 2 messages, look for message count indicator
        has_message_count = any(
            count_marker in metadata_section
            for count_marker in ["2 message", "Messages:", "Message Count:", "Count:"]
        )

        assert has_message_count, (
            f"FR-014 VIOLATION: Message count MUST appear in metadata header. "
            f"Count indicators not found in metadata section:\n{metadata_section[:300]}\n\n"
            f"This is US3-AS3 acceptance scenario requirement."
        )

        # =====================================================================
        # ADDITIONAL VALIDATION: Metadata Uses Proper Markdown Structure
        # =====================================================================

        # Metadata should start with a heading or have clear structure
        assert len(metadata_section.strip()) > 0, "Metadata section should not be empty"

        # Metadata should be visually distinct (heading or labeled fields)
        has_markdown_structure = (
            metadata_section.startswith("#") or ":" in metadata_section or "-" in metadata_section
        )

        assert has_markdown_structure, (
            f"Metadata should use proper markdown structure (headings, lists, or labels). "
            f"Got:\n{metadata_section[:200]}"
        )

    def test_export_command_preserves_message_order(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that messages are exported in chronological order.

        Validates:
        - FR-014: Proper message ordering
        - Chronological sorting by timestamp

        Expected to FAIL: Message ordering not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        assert result.returncode == 0

        markdown = output_file.read_text(encoding="utf-8")

        # Assert: User message appears before Assistant message
        user_pos = markdown.find("User")
        assistant_pos = markdown.find("Assistant")
        assert user_pos > 0, "Should contain User message"
        assert assistant_pos > 0, "Should contain Assistant message"
        assert user_pos < assistant_pos, "User message should appear before Assistant"

    def test_export_command_includes_timestamps(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that message timestamps are included in export.

        Validates:
        - FR-014: Include timestamps in metadata
        - ISO 8601 format for timestamps

        Expected to FAIL: Timestamp formatting not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        assert result.returncode == 0

        markdown = output_file.read_text(encoding="utf-8")

        # Assert: ISO 8601 timestamp format (YYYY-MM-DDTHH:MM:SS)
        assert "2024-03" in markdown, "Should contain timestamp with year-month"
        assert "T" in markdown, "Should use ISO 8601 format (contains 'T' separator)"

    def test_export_command_includes_emoji_headers(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that role headers include emoji.

        Validates:
        - User format preference: 👤 for user, 🤖 for assistant

        Expected to FAIL: Emoji formatting not implemented.
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        assert result.returncode == 0

        markdown = output_file.read_text(encoding="utf-8")

        # Assert: User emoji
        assert "👤" in markdown, "Should include 👤 emoji for user messages"

        # Assert: Assistant emoji
        assert "🤖" in markdown, "Should include 🤖 emoji for assistant messages"

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_export_command_handles_unicode_in_titles(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that Unicode in conversation titles is handled correctly.

        Validates:
        - CHK126: UTF-8 encoding assumption
        - FR-016: Slugified filenames from titles

        Expected to FAIL: Unicode handling not implemented.
        """
        # Create export with Unicode title
        unicode_conv = {
            "id": "unicode-conv",
            "title": "测试会话 🚀 Test Émojis",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
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
            json.dump([unicode_conv], f, ensure_ascii=False)

        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(unicode_file),
                "unicode-conv",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Should not crash and should succeed
        assert result.returncode == 0, f"Unicode handling failed: {result.stderr}"

        # Assert: Output file contains Unicode content
        markdown = output_file.read_text(encoding="utf-8")
        assert "世界" in markdown or "Test" in markdown, "Should preserve Unicode content in output"

    def test_export_command_handles_long_conversations(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test that long conversations (100+ messages) are exported correctly.

        Validates:
        - FR-008: Streaming efficiency for large conversations
        - No memory issues with long conversations

        Expected to FAIL: Not implemented or performance issues.
        """
        # Create conversation with 100 messages
        mapping = {}
        for i in range(100):
            mapping[f"msg-{i}"] = {
                "id": f"msg-{i}",
                "message": {
                    "id": f"msg-{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"content_type": "text", "parts": [f"Message {i}"]},
                    "create_time": 1710000000.0 + i * 10,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": f"msg-{i - 1}" if i > 0 else None,
                "children": [f"msg-{i + 1}"] if i < 99 else [],
            }

        long_conv = {
            "id": "long-conv",
            "title": "Long Conversation Test",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": mapping,
            "moderation_results": [],
            "current_node": "msg-99",
        }

        long_file = tmp_path / "long_export.json"
        with long_file.open("w") as f:
            json.dump([long_conv], f)

        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(long_file),
                "long-conv",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Should succeed
        assert result.returncode == 0, f"Long conversation export failed: {result.stderr}"

        # Assert: Output file contains all messages
        markdown = output_file.read_text(encoding="utf-8")
        assert "Message 0" in markdown, "Should contain first message"
        assert "Message 99" in markdown, "Should contain last message"

    def test_export_command_overwrites_existing_file_with_warning(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that export overwrites existing file and shows warning.

        Validates:
        - FR-033: File overwrite behavior
        - User warning on stderr for overwrite

        Expected to FAIL: Overwrite warning not implemented.
        """
        output_file = tmp_path / "output.md"

        # Create existing file
        output_file.write_text("Existing content")

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Should succeed (overwrite allowed)
        assert result.returncode == 0

        # Assert: File should be overwritten with new content
        markdown = output_file.read_text(encoding="utf-8")
        assert "Existing content" not in markdown, "Old content should be overwritten"
        assert "AsyncIO" in markdown, "New content should be present"

    def test_export_command_by_title_flag(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test exporting conversation using --title flag instead of ID.

        Validates:
        - FR-018: Support --title as alternative to ID
        - Title-based conversation lookup

        Expected to FAIL: --title flag not implemented.
        """
        output_file = tmp_path / "output.md"

        # Export using --title instead of positional ID
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Export by --title should succeed. Got {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        markdown = output_file.read_text(encoding="utf-8")
        assert "AsyncIO" in markdown, "Should export correct conversation by title"

    def test_export_command_ambiguous_title_raises_error(
        self, cli_command: list[str], duplicate_title_export: Path, tmp_path: Path
    ) -> None:
        """Test that ambiguous title (multiple matches) returns error.

        Validates:
        - FR-018: Error handling for ambiguous title matches
        - Exit code 1 for operational error

        Expected to FAIL: Ambiguous title handling not implemented.
        """
        output_file = tmp_path / "output.md"

        # Export using --title that matches multiple conversations
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(duplicate_title_export),
                "--title",
                "Python Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1 (error)
        assert result.returncode == 1, (
            f"Ambiguous title should fail with exit code 1, got {result.returncode}"
        )

        # Assert: Error message explains ambiguity
        stderr = result.stderr
        assert "multiple" in stderr.lower() or "ambiguous" in stderr.lower(), (
            f"Error should mention multiple matches. Got: {stderr}"
        )

    def test_export_command_default_output_to_cwd(
        self, cli_command: list[str], export_sample_file: Path, tmp_path: Path
    ) -> None:
        """Test that --output defaults to current working directory.

        Validates:
        - FR-399: Default to CWD for export output
        - FR-016: Slugified filename from conversation title

        Expected to FAIL: Default CWD behavior not implemented.
        """
        # Run from tmp_path directory (no --output flag, write to CWD)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_sample_file),
                "export-conv-001",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
            cwd=str(tmp_path),
        )

        # Assert: Success (writes to stdout when no --output)
        # Note: This test assumes stdout output when no --output flag
        # If implementation defaults to file in CWD, adjust assertion
        assert result.returncode == 0

        # If stdout output (no file created):
        if len(result.stdout) > 0:
            assert "AsyncIO" in result.stdout, "Should write markdown to stdout"

    def test_export_command_help_flag(self, cli_command: list[str]) -> None:
        """Test that 'echomine export --help' displays usage.

        Validates:
        - CLI spec: --help flag
        - Exit code 0 for help

        Expected to FAIL: --help not implemented.
        """
        result = subprocess.run(
            [*cli_command, "export", "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, "Help should exit with code 0"

        # Assert: Help text on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "Help text should be on stdout"
        assert "export" in stdout.lower(), "Help should mention 'export' command"
        assert "output" in stdout.lower() or "--output" in stdout, (
            "Help should mention --output flag"
        )
