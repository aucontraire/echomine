"""Integration tests for get messages CLI command.

This module tests the 'get messages' subcommand end-to-end integration with the
OpenAIAdapter, verifying correct message retrieval and output formatting.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle II: CLI interface contract (stdout/stderr/exit codes)
    - CHK031: Results to stdout, progress/errors to stderr

Test Coverage:
    - T074: get messages command executes and returns exit code 0
    - T075: Messages shown in chronological order - oldest first (FR-026)
    - T076: --json flag outputs full message objects (FR-027)
    - T077: Invalid conversation ID exits with code 1 (FR-028)
    - T078: TDD Edge Case - Messages with empty content display gracefully
    - T079: TDD Edge Case - Messages with content < 100 chars not truncated

Phase: RED (tests designed to FAIL initially)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from echomine.cli.app import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def get_messages_test_export(tmp_path: Path) -> Path:
    """Create test export for get messages command.

    Creates an export with 1 conversation containing 5 messages:
    - msg-001-1: user (timestamp: 1700000000.0)
    - msg-001-2: assistant (timestamp: 1700000010.0)
    - msg-001-3: user (timestamp: 1700000020.0)
    - msg-001-4: assistant with empty content (timestamp: 1700000030.0)
    - msg-001-5: user with short content (timestamp: 1700000040.0)
    """
    export_data = [
        {
            "id": "test-conv-001",
            "title": "Test Conversation for Messages",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-001-1": {
                    "id": "msg-001-1",
                    "message": {
                        "id": "msg-001-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "I need help with Python generators and async programming in large-scale applications"
                            ],
                        },
                        "create_time": 1700000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-001-2"],
                },
                "msg-001-2": {
                    "id": "msg-001-2",
                    "message": {
                        "id": "msg-001-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Python generators are a powerful feature that allow you to create iterators in a simple way. They use the yield keyword to produce values lazily, which is memory-efficient for large datasets."
                            ],
                        },
                        "create_time": 1700000010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-1",
                    "children": ["msg-001-3"],
                },
                "msg-001-3": {
                    "id": "msg-001-3",
                    "message": {
                        "id": "msg-001-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Can you show me an example with yield and how it differs from return?"
                            ],
                        },
                        "create_time": 1700000020.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-2",
                    "children": ["msg-001-4"],
                },
                "msg-001-4": {
                    "id": "msg-001-4",
                    "message": {
                        "id": "msg-001-4",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [""],  # Empty content for T078
                        },
                        "create_time": 1700000030.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-3",
                    "children": ["msg-001-5"],
                },
                "msg-001-5": {
                    "id": "msg-001-5",
                    "message": {
                        "id": "msg-001-5",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Thanks!"],  # Short content for T079
                        },
                        "create_time": 1700000040.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-4",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-001-5",
        },
    ]

    export_file = tmp_path / "get_messages_export.json"
    export_file.write_text(json.dumps(export_data, indent=2))
    return export_file


class TestGetMessagesCommand:
    """Integration tests for get messages subcommand (T074-T079)."""

    def test_t074_get_messages_command_executes_successfully(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T074: Verify get messages command executes and returns exit code 0.

        Contract:
        - Command: echomine get messages <file> <conversation_id>
        - Exit code: 0 for success
        - Output: Human-readable table format to stdout
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "test-conv-001"],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\nOutput: {result.stdout}\nError: {result.stderr}"
        )

        # Assert output contains conversation title
        assert "Test Conversation for Messages" in result.stdout

        # Assert output contains message count
        assert "5 messages" in result.stdout

    def test_t075_messages_shown_in_chronological_order_oldest_first(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T075: Verify messages are shown in chronological order - oldest first (FR-026).

        Contract:
        - Messages ordered by timestamp (ascending)
        - First message shown first, last message shown last
        - Format: msg-ID role timestamp content_preview
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "test-conv-001"],
        )

        assert result.exit_code == 0

        output_lines = result.stdout.strip().split("\n")

        # Find lines with message IDs (skip header lines)
        message_lines = [line for line in output_lines if "msg-001-" in line]

        # Assert messages appear in order
        assert len(message_lines) == 5, f"Expected 5 message lines, got {len(message_lines)}"

        # Check order: msg-001-1 appears before msg-001-2, etc.
        assert message_lines[0].startswith("msg-001-1"), (
            f"First message should be msg-001-1, got: {message_lines[0]}"
        )
        assert message_lines[1].startswith("msg-001-2"), (
            f"Second message should be msg-001-2, got: {message_lines[1]}"
        )
        assert message_lines[2].startswith("msg-001-3"), (
            f"Third message should be msg-001-3, got: {message_lines[2]}"
        )
        assert message_lines[3].startswith("msg-001-4"), (
            f"Fourth message should be msg-001-4, got: {message_lines[3]}"
        )
        assert message_lines[4].startswith("msg-001-5"), (
            f"Fifth message should be msg-001-5, got: {message_lines[4]}"
        )

    def test_t076_json_flag_outputs_full_message_objects(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T076: Verify --json flag outputs full message objects (FR-027).

        Contract:
        - Output format: JSON array of message objects
        - Each message has: id, role, timestamp, content
        - Valid JSON parseable by json.loads()
        - Messages in chronological order
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "test-conv-001", "--json"],
        )

        assert result.exit_code == 0

        # Parse JSON output
        messages = json.loads(result.stdout)

        # Assert it's a list
        assert isinstance(messages, list), "JSON output should be an array"

        # Assert correct number of messages
        assert len(messages) == 5, f"Expected 5 messages, got {len(messages)}"

        # Validate first message structure
        first_msg = messages[0]
        assert "id" in first_msg, "Message should have 'id' field"
        assert "role" in first_msg, "Message should have 'role' field"
        assert "timestamp" in first_msg, "Message should have 'timestamp' field"
        assert "content" in first_msg, "Message should have 'content' field"

        # Validate first message values
        assert first_msg["id"] == "msg-001-1", (
            f"Expected first message ID 'msg-001-1', got {first_msg['id']}"
        )
        assert first_msg["role"] == "user", f"Expected role 'user', got {first_msg['role']}"
        assert "Python generators" in first_msg["content"], "Content should match"

        # Validate chronological order
        assert messages[0]["id"] == "msg-001-1"
        assert messages[1]["id"] == "msg-001-2"
        assert messages[2]["id"] == "msg-001-3"
        assert messages[3]["id"] == "msg-001-4"
        assert messages[4]["id"] == "msg-001-5"

    def test_t077_invalid_conversation_id_exits_with_code_1(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T077: Verify invalid conversation ID exits with code 1 (FR-028).

        Contract:
        - Exit code: 1 for operational error (not found)
        - Error message to stderr
        - Error message includes conversation ID
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "invalid-conv-id"],
        )

        # Assert exit code 1
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Assert error message mentions conversation not found
        # Note: CliRunner captures stderr in result.stderr (separate from stdout)
        # Use result.output to get combined stdout+stderr
        output = result.output
        assert "not found" in output.lower() or "error" in output.lower(), (
            f"Expected error message, got: {output}"
        )
        assert "invalid-conv-id" in output, f"Error should mention conversation ID, got: {output}"

    def test_t078_messages_with_empty_content_display_gracefully(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T078: TDD Edge Case - Messages with empty content display gracefully.

        Contract:
        - Empty content messages are shown (not skipped)
        - No error or exception
        - Empty content shown as empty string or placeholder
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "test-conv-001"],
        )

        assert result.exit_code == 0, (
            f"Command should succeed with exit code 0, got {result.exit_code}"
        )

        # Check that msg-001-4 (empty content) is present
        assert "msg-001-4" in result.stdout, "Empty content message should be displayed"

        # Verify no error or exception
        assert "error" not in result.stdout.lower(), "Should not show errors for empty content"

    def test_t079_messages_with_short_content_not_truncated(
        self,
        cli_runner: CliRunner,
        get_messages_test_export: Path,
    ) -> None:
        """T079: TDD Edge Case - Messages with content < 100 chars not truncated.

        Contract:
        - Short messages (< 100 chars) shown in full
        - No "..." truncation marker for short content
        - Full content preserved
        """
        result = cli_runner.invoke(
            app,
            ["get", "messages", str(get_messages_test_export), "test-conv-001"],
        )

        assert result.exit_code == 0

        # Find the line with msg-001-5 (short content "Thanks!")
        output_lines = result.stdout.strip().split("\n")
        msg_005_line = next((line for line in output_lines if "msg-001-5" in line), None)

        assert msg_005_line is not None, "msg-001-5 should be in output"

        # Assert "Thanks!" appears in the line
        assert "Thanks!" in msg_005_line, (
            f"Short content should appear in full, got: {msg_005_line}"
        )

        # Assert no truncation marker for short content
        # (Note: truncation marker is "..." at position 97-100)
        # For short content, we shouldn't see truncation
        if "Thanks!" in msg_005_line:
            # Extract the part after "Thanks!" to check for truncation
            thanks_index = msg_005_line.index("Thanks!")
            after_thanks = msg_005_line[thanks_index + len("Thanks!") :]
            # Should not have "..." immediately after
            assert not after_thanks.strip().startswith("..."), (
                f"Short content should not be truncated, got: {msg_005_line}"
            )
