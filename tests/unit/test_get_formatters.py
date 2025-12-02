"""Unit tests for get command formatting utilities.

Task: Coverage improvement for formatting functions in get.py (lines 83-270)
Phase: TDD RED-GREEN-REFACTOR

This module tests the internal formatting utilities used by the get command:
- _format_conversation_table()
- _format_conversation_json()
- _format_message_table()
- _format_message_json()

Test Pyramid Classification: Unit (70% of test suite)
These tests validate formatting logic in isolation without CLI invocation.

Coverage Target:
- Lines 83-270 in get.py (formatting utilities)
- Table and JSON formatting for conversations and messages
- Verbose mode handling
- Unicode content handling
- Edge cases (null fields, long content, etc.)
"""

from datetime import UTC, datetime

import pytest

from echomine.cli.commands.get import (
    _format_conversation_json,
    _format_conversation_table,
    _format_message_json,
    _format_message_table,
)
from echomine.models.conversation import Conversation
from echomine.models.message import Message


# =============================================================================
# Fixtures for test data
# =============================================================================


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create sample messages for conversation testing."""
    return [
        Message(
            id="msg-1",
            role="user",
            content="First user message",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        ),
        Message(
            id="msg-2",
            role="assistant",
            content="First assistant response",
            timestamp=datetime(2024, 3, 9, 12, 1, 0, tzinfo=UTC),
            parent_id="msg-1",
        ),
        Message(
            id="msg-3",
            role="system",
            content="System message",
            timestamp=datetime(2024, 3, 9, 12, 2, 0, tzinfo=UTC),
            parent_id=None,
        ),
    ]


@pytest.fixture
def sample_conversation(sample_messages: list[Message]) -> Conversation:
    """Create sample conversation for testing."""
    return Conversation(
        id="conv-001",
        title="Test Conversation",
        created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 3, 9, 12, 5, 0, tzinfo=UTC),
        messages=sample_messages,
    )


@pytest.fixture
def conversation_null_updated(sample_messages: list[Message]) -> Conversation:
    """Create conversation with null updated_at."""
    return Conversation(
        id="conv-null",
        title="No Updates",
        created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
        updated_at=None,
        messages=sample_messages,
    )


# =============================================================================
# Unit Tests: _format_conversation_table()
# =============================================================================


@pytest.mark.unit
class TestFormatConversationTable:
    """Unit tests for _format_conversation_table() function."""

    def test_table_format_basic_structure(self, sample_conversation: Conversation) -> None:
        """Test basic table structure is generated correctly.

        Validates:
        - Header "Conversation Details" present
        - Separator lines present
        - All required fields displayed
        """
        # Act
        output = _format_conversation_table(sample_conversation, verbose=False)

        # Assert: Basic structure
        assert "Conversation Details" in output
        assert "═" * 47 in output  # Header separator
        assert "─" * 47 in output  # Section separator

        # Assert: Required fields
        assert "ID:" in output
        assert "conv-001" in output
        assert "Title:" in output
        assert "Test Conversation" in output
        assert "Created:" in output
        assert "2024-03-09" in output
        assert "Updated:" in output
        assert "Messages:" in output
        assert "3 messages" in output

    def test_table_format_message_summary_by_role(
        self, sample_conversation: Conversation
    ) -> None:
        """Test message summary section shows role counts.

        Validates:
        - Message Summary section exists
        - Role counts displayed correctly (user: 1, assistant: 1, system: 1)
        """
        # Act
        output = _format_conversation_table(sample_conversation, verbose=False)

        # Assert: Message summary section
        assert "Message Summary:" in output

        # Assert: Role counts (sample has 1 user, 1 assistant, 1 system)
        lines = output.split("\n")
        summary_section = "\n".join(lines)

        assert "user" in summary_section.lower()
        assert "assistant" in summary_section.lower()
        assert "system" in summary_section.lower()

        # Count should be 1 for each role
        assert "1" in summary_section

    def test_table_format_verbose_shows_messages(
        self, sample_conversation: Conversation
    ) -> None:
        """Test verbose mode displays message details.

        Validates:
        - verbose=True shows "Messages:" section
        - Each message numbered and displayed
        - Role and timestamp shown for each message
        """
        # Act
        output = _format_conversation_table(sample_conversation, verbose=True)

        # Assert: Messages section present
        assert "Messages:" in output

        # Assert: Message details shown
        assert "1. [user]" in output
        assert "2. [assistant]" in output
        assert "3. [system]" in output

        # Assert: Content shown
        assert "First user message" in output
        assert "First assistant response" in output
        assert "System message" in output

    def test_table_format_verbose_truncates_long_content(self) -> None:
        """Test verbose mode truncates content longer than 80 characters.

        Validates:
        - Content > 80 chars truncated to 77 + "..."
        - Ellipsis appended
        """
        # Create message with long content
        long_content = "A" * 100
        long_message = Message(
            id="msg-long",
            role="user",
            content=long_content,
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        conversation = Conversation(
            id="conv-long",
            title="Long content",
            created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            updated_at=None,
            messages=[long_message],
        )

        # Act
        output = _format_conversation_table(conversation, verbose=True)

        # Assert: Content truncated with ellipsis
        assert "..." in output
        # Full 100 char string should not be present
        assert long_content not in output

    def test_table_format_null_updated_at_uses_fallback(
        self, conversation_null_updated: Conversation
    ) -> None:
        """Test null updated_at uses created_at as fallback.

        Validates:
        - updated_at_or_created property works
        - No crash when updated_at is None
        """
        # Act
        output = _format_conversation_table(conversation_null_updated, verbose=False)

        # Assert: Updated field shows created_at (since updated_at is None)
        assert "Updated:" in output
        assert "2024-03-09" in output

    def test_table_format_unicode_content(self) -> None:
        """Test Unicode content is displayed correctly.

        Validates:
        - CHK126: UTF-8 encoding assumption
        - Unicode in title and message content
        """
        # Create conversation with Unicode
        unicode_message = Message(
            id="msg-unicode",
            role="user",
            content="测试 Unicode 🚀",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        conversation = Conversation(
            id="conv-unicode",
            title="测试会话 🚀",
            created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            updated_at=None,
            messages=[unicode_message],
        )

        # Act
        output = _format_conversation_table(conversation, verbose=True)

        # Assert: Unicode displayed
        assert "测试会话 🚀" in output
        assert "测试 Unicode 🚀" in output

    def test_table_format_newline_terminated(self, sample_conversation: Conversation) -> None:
        """Test output ends with newline.

        Validates:
        - Output ends with \n for CLI display
        """
        # Act
        output = _format_conversation_table(sample_conversation, verbose=False)

        # Assert: Ends with newline
        assert output.endswith("\n")


# =============================================================================
# Unit Tests: _format_conversation_json()
# =============================================================================


@pytest.mark.unit
class TestFormatConversationJSON:
    """Unit tests for _format_conversation_json() function."""

    def test_json_format_valid_json(self, sample_conversation: Conversation) -> None:
        """Test output is valid JSON.

        Validates:
        - json.loads() succeeds
        - No syntax errors
        """
        import json

        # Act
        output = _format_conversation_json(sample_conversation)

        # Assert: Valid JSON
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}")

        assert isinstance(data, dict)

    def test_json_format_required_fields(self, sample_conversation: Conversation) -> None:
        """Test all required fields are present.

        Validates:
        - id, title, created_at, updated_at, message_count, messages
        """
        import json

        # Act
        output = _format_conversation_json(sample_conversation)
        data = json.loads(output)

        # Assert: Required fields
        assert data["id"] == "conv-001"
        assert data["title"] == "Test Conversation"
        assert "created_at" in data
        assert "updated_at" in data
        assert data["message_count"] == 3
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 3

    def test_json_format_iso8601_timestamps(self, sample_conversation: Conversation) -> None:
        """Test timestamps are ISO 8601 format with UTC (YYYY-MM-DDTHH:MM:SSZ).

        Validates:
        - Format ends with 'Z' (UTC)
        - Contains 'T' separator
        """
        import json

        # Act
        output = _format_conversation_json(sample_conversation)
        data = json.loads(output)

        # Assert: ISO 8601 format
        assert data["created_at"] == "2024-03-09T12:00:00Z"
        assert data["updated_at"] == "2024-03-09T12:05:00Z"

        # Assert: All message timestamps
        for msg in data["messages"]:
            assert msg["timestamp"].endswith("Z")
            assert "T" in msg["timestamp"]

    def test_json_format_message_structure(self, sample_conversation: Conversation) -> None:
        """Test message structure includes all fields.

        Validates:
        - id, role, content, timestamp, parent_id
        """
        import json

        # Act
        output = _format_conversation_json(sample_conversation)
        data = json.loads(output)

        # Assert: First message structure
        msg = data["messages"][0]
        assert msg["id"] == "msg-1"
        assert msg["role"] == "user"
        assert msg["content"] == "First user message"
        assert msg["timestamp"] == "2024-03-09T12:00:00Z"
        assert msg["parent_id"] is None

        # Assert: Second message has parent_id
        msg2 = data["messages"][1]
        assert msg2["parent_id"] == "msg-1"

    def test_json_format_unicode_not_escaped(self) -> None:
        """Test Unicode is not ASCII-escaped (ensure_ascii=False).

        Validates:
        - Unicode characters preserved (not \\uXXXX)
        """
        import json

        # Create conversation with Unicode
        unicode_message = Message(
            id="msg-unicode",
            role="user",
            content="测试 🚀",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        conversation = Conversation(
            id="conv-unicode",
            title="测试会话",
            created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            updated_at=None,
            messages=[unicode_message],
        )

        # Act
        output = _format_conversation_json(conversation)

        # Assert: Unicode not escaped
        assert "测试" in output
        assert "🚀" in output
        assert "\\u" not in output  # No ASCII escape sequences

    def test_json_format_null_updated_at_uses_fallback(
        self, conversation_null_updated: Conversation
    ) -> None:
        """Test null updated_at uses created_at fallback in JSON.

        Validates:
        - updated_at_or_created property works in JSON format
        """
        import json

        # Act
        output = _format_conversation_json(conversation_null_updated)
        data = json.loads(output)

        # Assert: updated_at shows created_at (fallback)
        assert data["updated_at"] == "2024-03-09T12:00:00Z"

    def test_json_format_pretty_printed(self, sample_conversation: Conversation) -> None:
        """Test JSON is pretty-printed with indentation.

        Validates:
        - indent=2 spacing
        - Human-readable format
        """
        # Act
        output = _format_conversation_json(sample_conversation)

        # Assert: Indented (has multiple spaces)
        assert "  " in output  # 2-space indentation
        assert "\n" in output  # Multiple lines

    def test_json_format_newline_terminated(self, sample_conversation: Conversation) -> None:
        """Test JSON output ends with newline.

        Validates:
        - Output ends with \n
        """
        # Act
        output = _format_conversation_json(sample_conversation)

        # Assert: Newline terminated
        assert output.endswith("\n")


# =============================================================================
# Unit Tests: _format_message_table()
# =============================================================================


@pytest.mark.unit
class TestFormatMessageTable:
    """Unit tests for _format_message_table() function."""

    def test_message_table_basic_structure(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test basic message table structure.

        Validates:
        - Header "Message Details"
        - Message metadata (id, role, timestamp, parent_id)
        - Content section
        - Conversation context section
        """
        message = sample_messages[0]

        # Act
        output = _format_message_table(message, sample_conversation, verbose=False)

        # Assert: Structure
        assert "Message Details" in output
        assert "═" * 47 in output

        # Assert: Message metadata
        assert "ID:" in output
        assert "msg-1" in output
        assert "Role:" in output
        assert "user" in output
        assert "Timestamp:" in output
        assert "2024-03-09" in output
        assert "Parent ID:" in output
        assert "None (root message)" in output

        # Assert: Content section
        assert "Content:" in output
        assert "First user message" in output

        # Assert: Conversation context
        assert "Conversation Context:" in output
        assert "Conversation ID:" in output
        assert "conv-001" in output
        assert "Title:" in output
        assert "Test Conversation" in output

    def test_message_table_parent_id_displayed(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test parent_id is displayed correctly.

        Validates:
        - None parent shows "None (root message)"
        - Non-null parent shows actual ID
        """
        # Test root message (parent=None)
        root_message = sample_messages[0]
        output_root = _format_message_table(root_message, sample_conversation, verbose=False)
        assert "None (root message)" in output_root

        # Test child message (has parent)
        child_message = sample_messages[1]
        output_child = _format_message_table(
            child_message, sample_conversation, verbose=False
        )
        assert "msg-1" in output_child  # parent_id value

    def test_message_table_truncates_long_content(
        self, sample_conversation: Conversation
    ) -> None:
        """Test content truncation in non-verbose mode.

        Validates:
        - Content > 200 chars truncated to 197 + "..."
        """
        # Create long message
        long_content = "A" * 300
        long_message = Message(
            id="msg-long",
            role="user",
            content=long_content,
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        # Act
        output = _format_message_table(long_message, sample_conversation, verbose=False)

        # Assert: Truncated
        assert "..." in output
        assert long_content not in output

    def test_message_table_verbose_shows_full_content(
        self, sample_conversation: Conversation
    ) -> None:
        """Test verbose mode shows full content without truncation.

        Validates:
        - verbose=True disables truncation
        """
        # Create long message
        long_content = "B" * 300
        long_message = Message(
            id="msg-long",
            role="user",
            content=long_content,
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        # Act
        output = _format_message_table(long_message, sample_conversation, verbose=True)

        # Assert: Full content shown
        assert long_content in output
        # No truncation ellipsis before content
        lines = output.split("\n")
        content_section = False
        for line in lines:
            if "Content:" in line:
                content_section = True
            if content_section and long_content in line:
                # Should not have ellipsis in verbose mode
                assert "..." not in line or line.endswith(long_content)

    def test_message_table_verbose_shows_all_conversation_messages(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test verbose mode shows all messages in conversation.

        Validates:
        - verbose=True adds "All Messages in Conversation" section
        - Current message marked with " >>> "
        """
        message = sample_messages[1]  # msg-2

        # Act
        output = _format_message_table(message, sample_conversation, verbose=True)

        # Assert: All messages section
        assert "All Messages in Conversation:" in output

        # Assert: Messages listed with marker for current message
        assert " >>> " in output or "msg-2" in output

    def test_message_table_unicode_handling(self, sample_conversation: Conversation) -> None:
        """Test Unicode in message content and conversation title.

        Validates:
        - CHK126: UTF-8 encoding
        """
        # Create Unicode message
        unicode_message = Message(
            id="msg-unicode",
            role="user",
            content="测试 🚀",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        unicode_conv = Conversation(
            id="conv-unicode",
            title="测试会话",
            created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            updated_at=None,
            messages=[unicode_message],
        )

        # Act
        output = _format_message_table(unicode_message, unicode_conv, verbose=False)

        # Assert: Unicode displayed
        assert "测试 🚀" in output
        assert "测试会话" in output

    def test_message_table_newline_terminated(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test output ends with newline."""
        message = sample_messages[0]

        # Act
        output = _format_message_table(message, sample_conversation, verbose=False)

        # Assert: Newline terminated
        assert output.endswith("\n")


# =============================================================================
# Unit Tests: _format_message_json()
# =============================================================================


@pytest.mark.unit
class TestFormatMessageJSON:
    """Unit tests for _format_message_json() function."""

    def test_message_json_valid_structure(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test JSON structure with message and conversation objects.

        Validates:
        - Top-level keys: "message" and "conversation"
        - Valid JSON
        """
        import json

        message = sample_messages[0]

        # Act
        output = _format_message_json(message, sample_conversation)

        # Assert: Valid JSON
        data = json.loads(output)

        # Assert: Structure
        assert "message" in data
        assert "conversation" in data

    def test_message_json_message_fields(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test message object contains all required fields.

        Validates:
        - id, role, content, timestamp, parent_id
        """
        import json

        message = sample_messages[1]  # msg-2 (has parent)

        # Act
        output = _format_message_json(message, sample_conversation)
        data = json.loads(output)

        # Assert: Message fields
        msg = data["message"]
        assert msg["id"] == "msg-2"
        assert msg["role"] == "assistant"
        assert msg["content"] == "First assistant response"
        assert msg["timestamp"] == "2024-03-09T12:01:00Z"
        assert msg["parent_id"] == "msg-1"

    def test_message_json_conversation_context(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test conversation context includes key fields.

        Validates:
        - id, title, created_at, updated_at, message_count
        """
        import json

        message = sample_messages[0]

        # Act
        output = _format_message_json(message, sample_conversation)
        data = json.loads(output)

        # Assert: Conversation context
        conv = data["conversation"]
        assert conv["id"] == "conv-001"
        assert conv["title"] == "Test Conversation"
        assert conv["created_at"] == "2024-03-09T12:00:00Z"
        assert conv["updated_at"] == "2024-03-09T12:05:00Z"
        assert conv["message_count"] == 3

    def test_message_json_iso8601_timestamps(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test all timestamps are ISO 8601 with UTC.

        Validates:
        - Format: YYYY-MM-DDTHH:MM:SSZ
        """
        import json

        message = sample_messages[0]

        # Act
        output = _format_message_json(message, sample_conversation)
        data = json.loads(output)

        # Assert: ISO 8601 format
        assert data["message"]["timestamp"].endswith("Z")
        assert "T" in data["message"]["timestamp"]
        assert data["conversation"]["created_at"].endswith("Z")
        assert data["conversation"]["updated_at"].endswith("Z")

    def test_message_json_unicode_preserved(
        self, sample_conversation: Conversation
    ) -> None:
        """Test Unicode is not ASCII-escaped.

        Validates:
        - ensure_ascii=False
        """
        # Create Unicode message
        unicode_message = Message(
            id="msg-unicode",
            role="user",
            content="测试 🚀",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        # Act
        output = _format_message_json(unicode_message, sample_conversation)

        # Assert: Unicode not escaped
        assert "测试" in output
        assert "🚀" in output
        assert "\\u" not in output

    def test_message_json_pretty_printed(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test JSON is pretty-printed.

        Validates:
        - indent=2
        """
        message = sample_messages[0]

        # Act
        output = _format_message_json(message, sample_conversation)

        # Assert: Indented
        assert "  " in output
        assert "\n" in output

    def test_message_json_newline_terminated(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test JSON ends with newline."""
        message = sample_messages[0]

        # Act
        output = _format_message_json(message, sample_conversation)

        # Assert: Newline
        assert output.endswith("\n")