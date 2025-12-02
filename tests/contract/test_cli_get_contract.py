"""Contract tests for CLI 'get' command (conversation and message retrieval).

Task: Coverage improvement for src/echomine/cli/commands/get.py (0% → 80%+)
Phase: TDD RED-GREEN-REFACTOR

This module validates the CLI 'get' command contract per the command specifications.
These are BLACK BOX tests - we invoke the CLI as subprocess and validate
external behavior (stdout, stderr, exit codes, output format).

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the CLI 'get' subcommands adhere to their published interface contract.

Contract Requirements Validated:
- CHK031: stdout/stderr separation (data on stdout, progress on stderr)
- CHK032: Exit codes (0=success, 1=error, 2=invalid input)
- FR-155: get_conversation_by_id returns Conversation | None
- NEW: get_message_by_id returns tuple[Message, Conversation] | None
- Human-readable table format with --verbose option
- JSON output format with --format json flag
- Error handling for file not found, conversation/message not found, parse errors

Coverage Target:
- Lines 50-574 in get.py (currently 0% coverage)
- Focus on both 'get conversation' and 'get message' subcommands
- Format options (table/json), verbose mode, error cases
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
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def get_test_export(tmp_path: Path) -> Path:
    """Create sample export for get command testing.

    Creates a small export with 2 conversations containing multiple messages
    with known IDs for testing retrieval functionality.
    """
    conversations = [
        {
            "id": "conv-get-001",
            "title": "Test Conversation One",
            "create_time": 1710000000.0,  # 2024-03-09
            "update_time": 1710000100.0,
            "mapping": {
                "msg-get-001-1": {
                    "id": "msg-get-001-1",
                    "message": {
                        "id": "msg-get-001-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["First user message"]},
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-get-001-2"],
                },
                "msg-get-001-2": {
                    "id": "msg-get-001-2",
                    "message": {
                        "id": "msg-get-001-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["First assistant response"],
                        },
                        "create_time": 1710000050.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-get-001-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-get-001-2",
        },
        {
            "id": "conv-get-002",
            "title": "Test Conversation Two with 测试 Unicode 🚀",
            "create_time": 1710100000.0,
            "update_time": None,  # Test null updated_at
            "mapping": {
                "msg-get-002-1": {
                    "id": "msg-get-002-1",
                    "message": {
                        "id": "msg-get-002-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["User message with 测试 Unicode 🚀"],
                        },
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-get-002-2", "msg-get-002-3"],
                },
                "msg-get-002-2": {
                    "id": "msg-get-002-2",
                    "message": {
                        "id": "msg-get-002-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Assistant response alpha"],
                        },
                        "create_time": 1710100050.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-get-002-1",
                    "children": [],
                },
                "msg-get-002-3": {
                    "id": "msg-get-002-3",
                    "message": {
                        "id": "msg-get-002-3",
                        "author": {"role": "system"},
                        "content": {"content_type": "text", "parts": ["System message"]},
                        "create_time": 1710100100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-get-002-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-get-002-3",
        },
    ]

    export_file = tmp_path / "get_test_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)

    return export_file


# =============================================================================
# Contract Tests: get conversation command
# =============================================================================


@pytest.mark.contract
class TestCLIGetConversationContract:
    """Contract tests for 'echomine get conversation' command.

    These tests validate the CLI contract for retrieving conversations by ID.
    Expected to cover lines 277-404 in get.py.
    """

    def test_get_conversation_success_table_format(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test successful conversation retrieval with default table format.

        Validates:
        - CHK031: Data on stdout, progress on stderr
        - CHK032: Exit code 0 for success
        - Default table format is human-readable
        """
        # Act: Get conversation with ID conv-get-001
        result = subprocess.run(
            [*cli_command, "get", "conversation", str(get_test_export), "conv-get-001"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: stdout contains conversation data
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain output"
        assert "Conversation Details" in stdout
        assert "conv-get-001" in stdout
        assert "Test Conversation One" in stdout
        assert "2024-03-09" in stdout  # Created timestamp
        assert "Messages:" in stdout or "2 messages" in stdout

        # Assert: Message summary by role
        assert "user" in stdout.lower()
        assert "assistant" in stdout.lower()

    def test_get_conversation_verbose_mode_shows_messages(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test --verbose flag shows full message details.

        Validates:
        - --verbose option displays message content
        - Message list with timestamps and roles
        """
        # Act: Get conversation with --verbose
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-get-001",
                "--verbose",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Message details shown
        stdout = result.stdout
        assert "Messages:" in stdout
        assert "user" in stdout.lower()
        assert "assistant" in stdout.lower()
        # Content should be visible (not just counts)
        assert "First user message" in stdout or "First assistant response" in stdout

    def test_get_conversation_json_format(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test --format json produces valid JSON output.

        Validates:
        - --format json flag works
        - Valid JSON structure on stdout
        - All expected fields present
        """
        # Act: Get conversation with JSON format
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-get-001",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Valid JSON
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{stdout}")

        # Assert: Expected structure
        assert "id" in data
        assert data["id"] == "conv-get-001"
        assert "title" in data
        assert data["title"] == "Test Conversation One"
        assert "created_at" in data
        assert "updated_at" in data
        assert "message_count" in data
        assert data["message_count"] == 2
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 2

        # Assert: Message structure
        first_msg = data["messages"][0]
        assert "id" in first_msg
        assert "role" in first_msg
        assert "content" in first_msg
        assert "timestamp" in first_msg
        assert "parent_id" in first_msg

        # Assert: ISO 8601 timestamps with UTC (YYYY-MM-DDTHH:MM:SSZ)
        assert data["created_at"].endswith("Z")
        assert "T" in data["created_at"]

    def test_get_conversation_not_found_exits_1(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test conversation not found returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for conversation not found
        - Clear error message on stderr
        """
        # Act: Get non-existent conversation
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-nonexistent",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower()
        assert "conv-nonexistent" in stderr

        # Assert: stdout empty on error
        assert len(result.stdout) == 0, "stdout should be empty on error"

    def test_get_conversation_file_not_found_exits_1(
        self, cli_command: list[str]
    ) -> None:
        """Test missing file returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for file errors
        - Clear error message
        """
        # Act: Get conversation from non-existent file
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                "/tmp/nonexistent_file_12345.json",
                "conv-001",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error message mentions file
        stderr = result.stderr
        assert "not found" in stderr.lower() or "no such file" in stderr.lower()

    def test_get_conversation_invalid_json_exits_1(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test malformed JSON returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for parse errors
        - ParseError handling
        """
        # Create malformed JSON file
        malformed = tmp_path / "malformed.json"
        malformed.write_text("{invalid json}")

        # Act: Get conversation from malformed file
        result = subprocess.run(
            [*cli_command, "get", "conversation", str(malformed), "conv-001"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions JSON/parse
        stderr = result.stderr
        assert "json" in stderr.lower() or "parse" in stderr.lower()

    def test_get_conversation_invalid_format_exits_2(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test invalid --format value returns exit code 2.

        Validates:
        - CHK032: Exit code 2 for invalid arguments
        - Format validation
        """
        # Act: Use invalid format
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-get-001",
                "--format",
                "xml",  # Invalid
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"

        # Assert: Error mentions format
        stderr = result.stderr
        assert "format" in stderr.lower()

    def test_get_conversation_help_flag(self, cli_command: list[str]) -> None:
        """Test --help displays usage information.

        Validates:
        - --help flag works
        - Exit code 0
        - Help text on stdout
        """
        # Act: Run with --help
        result = subprocess.run(
            [*cli_command, "get", "conversation", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Help text present
        stdout = result.stdout
        assert len(stdout) > 0
        assert "conversation" in stdout.lower()
        assert "format" in stdout.lower() or "--format" in stdout

    def test_get_conversation_unicode_handling(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test Unicode content displays correctly.

        Validates:
        - CHK126: UTF-8 encoding assumption
        - Unicode in title and content
        """
        # Act: Get conversation with Unicode title
        result = subprocess.run(
            [*cli_command, "get", "conversation", str(get_test_export), "conv-get-002"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Unicode displayed
        stdout = result.stdout
        assert "测试" in stdout or "Unicode" in stdout or "🚀" in stdout

    def test_get_conversation_null_updated_at_handled(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test conversation with null updated_at displays correctly.

        Validates:
        - Pydantic Optional[datetime] handling
        - updated_at_or_created property works
        """
        # Act: Get conversation with null updated_at (conv-get-002)
        result = subprocess.run(
            [*cli_command, "get", "conversation", str(get_test_export), "conv-get-002"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success (no crash)
        assert result.returncode == 0

        # Assert: Updated field shows a valid date (fallback to created)
        stdout = result.stdout
        assert "Updated:" in stdout
        # Should show create_time as fallback
        assert "2024-03-10" in stdout or "2024" in stdout

    def test_get_conversation_short_flag_f(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test -f short flag for --format.

        Validates:
        - Short flag -f works
        - Equivalent to --format json
        """
        # Act: Use -f json
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-get-001",
                "-f",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Valid JSON output
        try:
            data = json.loads(result.stdout)
            assert data["id"] == "conv-get-001"
        except json.JSONDecodeError:
            pytest.fail("Output should be valid JSON")

    def test_get_conversation_short_flag_v(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test -v short flag for --verbose.

        Validates:
        - Short flag -v works
        - Shows message details
        """
        # Act: Use -v
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "conversation",
                str(get_test_export),
                "conv-get-001",
                "-v",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Verbose output
        stdout = result.stdout
        assert "Messages:" in stdout


# =============================================================================
# Contract Tests: get message command
# =============================================================================


@pytest.mark.contract
class TestCLIGetMessageContract:
    """Contract tests for 'echomine get message' command.

    These tests validate the CLI contract for retrieving messages by ID.
    Expected to cover lines 411-574 in get.py.
    """

    def test_get_message_success_table_format(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test successful message retrieval with default table format.

        Validates:
        - CHK031: Data on stdout
        - CHK032: Exit code 0
        - Message details with conversation context
        """
        # Act: Get message by ID
        result = subprocess.run(
            [*cli_command, "get", "message", str(get_test_export), "msg-get-001-1"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Message details shown
        stdout = result.stdout
        assert "Message Details" in stdout
        assert "msg-get-001-1" in stdout
        assert "user" in stdout.lower()
        assert "First user message" in stdout

        # Assert: Conversation context shown
        assert "Conversation Context:" in stdout
        assert "conv-get-001" in stdout
        assert "Test Conversation One" in stdout

    def test_get_message_with_conversation_hint(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test --conversation-id hint for faster lookup.

        Validates:
        - -c / --conversation-id flag works
        - Performance optimization hint accepted
        """
        # Act: Get message with conversation hint
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                str(get_test_export),
                "msg-get-001-1",
                "-c",
                "conv-get-001",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Message found
        stdout = result.stdout
        assert "msg-get-001-1" in stdout

    def test_get_message_verbose_mode_shows_all_messages(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test --verbose shows all messages in conversation.

        Validates:
        - --verbose displays full conversation context
        - Current message marked/highlighted
        """
        # Act: Get message with --verbose
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                str(get_test_export),
                "msg-get-002-2",
                "--verbose",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: All conversation messages shown
        stdout = result.stdout
        assert "All Messages in Conversation:" in stdout
        # Should show multiple messages from conv-get-002
        assert "msg-get-002-1" in stdout or "msg-get-002-2" in stdout

    def test_get_message_json_format(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test --format json produces valid JSON with message and conversation.

        Validates:
        - JSON output structure
        - Nested message and conversation objects
        """
        # Act: Get message as JSON
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                str(get_test_export),
                "msg-get-001-2",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Valid JSON structure
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{result.stdout}")

        # Assert: Two top-level keys: message and conversation
        assert "message" in data
        assert "conversation" in data

        # Assert: Message structure
        msg = data["message"]
        assert msg["id"] == "msg-get-001-2"
        assert msg["role"] == "assistant"
        assert "content" in msg
        assert "timestamp" in msg
        assert msg["timestamp"].endswith("Z")  # UTC

        # Assert: Conversation context
        conv = data["conversation"]
        assert conv["id"] == "conv-get-001"
        assert "title" in conv
        assert "message_count" in conv

    def test_get_message_not_found_exits_1(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test message not found returns exit code 1.

        Validates:
        - CHK032: Exit code 1 for not found
        - Clear error message
        """
        # Act: Get non-existent message
        result = subprocess.run(
            [*cli_command, "get", "message", str(get_test_export), "msg-nonexistent"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error message
        stderr = result.stderr
        assert "not found" in stderr.lower()
        assert "msg-nonexistent" in stderr

    def test_get_message_not_found_with_hint_exits_1(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test message not found in specified conversation returns exit code 1.

        Validates:
        - Conversation hint validation
        - Specific error message mentioning conversation ID
        """
        # Act: Get message with wrong conversation hint
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                str(get_test_export),
                "msg-get-001-1",
                "-c",
                "conv-wrong",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions conversation
        stderr = result.stderr
        assert "not found" in stderr.lower()
        assert "conv-wrong" in stderr or "conversation" in stderr.lower()

    def test_get_message_file_not_found_exits_1(self, cli_command: list[str]) -> None:
        """Test missing file returns exit code 1.

        Validates:
        - File error handling
        """
        # Act: Get message from non-existent file
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                "/tmp/nonexistent_12345.json",
                "msg-001",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: File error
        stderr = result.stderr
        assert "not found" in stderr.lower() or "no such file" in stderr.lower()

    def test_get_message_invalid_format_exits_2(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test invalid --format value returns exit code 2.

        Validates:
        - Argument validation
        """
        # Act: Use invalid format
        result = subprocess.run(
            [
                *cli_command,
                "get",
                "message",
                str(get_test_export),
                "msg-get-001-1",
                "--format",
                "yaml",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2
        assert result.returncode == 2

        # Assert: Format error
        stderr = result.stderr
        assert "format" in stderr.lower()

    def test_get_message_help_flag(self, cli_command: list[str]) -> None:
        """Test --help displays usage information.

        Validates:
        - Help text for message subcommand
        """
        # Act: Run with --help
        result = subprocess.run(
            [*cli_command, "get", "message", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Help text
        stdout = result.stdout
        assert "message" in stdout.lower()
        assert "conversation-id" in stdout.lower() or "-c" in stdout

    def test_get_message_parent_id_none_displayed(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test message with parent_id=None displays 'None (root message)'.

        Validates:
        - Null parent_id handling in formatting
        """
        # Act: Get root message (msg-get-001-1 has parent=None)
        result = subprocess.run(
            [*cli_command, "get", "message", str(get_test_export), "msg-get-001-1"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Parent ID shows None/root
        stdout = result.stdout
        assert "Parent ID:" in stdout
        assert "None" in stdout or "root" in stdout.lower()

    def test_get_message_truncates_long_content_without_verbose(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test long content is truncated in non-verbose mode.

        Validates:
        - Content truncation at 200 characters (non-verbose)
        - Ellipsis (...) appended
        """
        # Create conversation with very long message
        long_content = "A" * 300  # 300 characters
        conversations = [
            {
                "id": "conv-long",
                "title": "Long message test",
                "create_time": 1710000000.0,
                "update_time": 1710000000.0,
                "mapping": {
                    "msg-long": {
                        "id": "msg-long",
                        "message": {
                            "id": "msg-long",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": [long_content]},
                            "create_time": 1710000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-long",
            }
        ]

        export_file = tmp_path / "long_message.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Get message without verbose (should truncate)
        result = subprocess.run(
            [*cli_command, "get", "message", str(export_file), "msg-long"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Content truncated with ellipsis
        stdout = result.stdout
        assert "..." in stdout
        # Full 300 chars should not be present
        assert long_content not in stdout

    def test_get_message_system_role_displayed(
        self, cli_command: list[str], get_test_export: Path
    ) -> None:
        """Test message with system role is displayed correctly.

        Validates:
        - All role types supported (user, assistant, system)
        """
        # Act: Get system message (msg-get-002-3)
        result = subprocess.run(
            [*cli_command, "get", "message", str(get_test_export), "msg-get-002-3"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: System role shown
        stdout = result.stdout
        assert "system" in stdout.lower()
        assert "System message" in stdout


# =============================================================================
# Contract Tests: get command (parent command)
# =============================================================================


@pytest.mark.contract
class TestCLIGetCommandParent:
    """Contract tests for parent 'get' command (no subcommand).

    These tests validate the hierarchical command structure.
    """

    def test_get_without_subcommand_shows_help(self, cli_command: list[str]) -> None:
        """Test 'echomine get' without subcommand shows help.

        Validates:
        - no_args_is_help=True behavior
        - Lists available subcommands (conversation, message)

        Note: Typer's no_args_is_help outputs to stderr with exit code 2.
        """
        # Act: Run 'get' without subcommand
        result = subprocess.run(
            [*cli_command, "get"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2 (Typer's no_args_is_help behavior)
        assert result.returncode == 2

        # Assert: Help text shows subcommands (in stderr for no_args_is_help)
        output = result.stderr or result.stdout
        assert "conversation" in output.lower()
        assert "message" in output.lower()

    def test_get_help_flag_shows_subcommands(self, cli_command: list[str]) -> None:
        """Test 'echomine get --help' shows available subcommands.

        Validates:
        - Help text lists conversation and message
        """
        # Act: Run get --help
        result = subprocess.run(
            [*cli_command, "get", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 0
        assert result.returncode == 0

        # Assert: Subcommands listed
        stdout = result.stdout
        assert "conversation" in stdout.lower()
        assert "message" in stdout.lower()
