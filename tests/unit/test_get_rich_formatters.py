"""Unit tests for Rich formatters in get.py module.

Task: Coverage improvement for Rich formatting functions (lines 372-607 in get.py)
Phase: TDD RED-GREEN-REFACTOR

This module tests the Rich formatting utilities used by the get command:
- _format_messages_rich() (lines 372-417)
- _format_conversation_rich() (lines 437-520)
- _format_message_rich() (lines 544-607)

Test Pyramid Classification: Unit (70% of test suite)
These tests validate Rich formatting logic in isolation without CLI invocation.

Coverage Target:
- Lines 372-417 in get.py (_format_messages_rich)
- Lines 437-520 in get.py (_format_conversation_rich)
- Lines 544-607 in get.py (_format_message_rich)
- Rich Panel and Table generation
- TTY output formatting with colors
- Verbose mode handling
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO

import pytest
from rich.console import Console

from echomine.cli.commands.get import (
    _format_conversation_rich,
    _format_message_rich,
    _format_messages_rich,
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


@pytest.fixture
def long_content_message() -> Message:
    """Create message with long content for truncation testing."""
    return Message(
        id="msg-long",
        role="user",
        content="A" * 150,  # 150 chars - should be truncated to 97 + "..."
        timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
        parent_id=None,
    )


@pytest.fixture
def empty_content_message() -> Message:
    """Create message with empty content for edge case testing."""
    return Message(
        id="msg-empty",
        role="user",
        content="",
        timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
        parent_id=None,
    )


# =============================================================================
# Unit Tests: _format_messages_rich()
# =============================================================================


@pytest.mark.unit
class TestFormatMessagesRich:
    """Unit tests for _format_messages_rich() function (lines 372-417)."""

    def test_format_messages_rich_creates_table(self, sample_conversation: Conversation) -> None:
        """Test _format_messages_rich() creates and prints a Rich table.

        Validates:
        - Rich Table is created
        - Table is printed to stdout
        - Lines 372-417 executed
        """
        # Capture stdout using Rich Console
        output_buffer = StringIO()

        # Patch Console to capture output
        from unittest.mock import patch

        # Mock Console to capture print calls
        with patch("echomine.cli.commands.get.Console") as mock_console_cls:
            # Create a real console that writes to our buffer
            real_console = Console(file=output_buffer, force_terminal=True, width=120)
            mock_console_cls.return_value = real_console

            # Act
            _format_messages_rich(sample_conversation)

            # Assert: Console was created
            mock_console_cls.assert_called_once()

    def test_format_messages_rich_includes_title_in_header(
        self, sample_conversation: Conversation
    ) -> None:
        """Test table title includes conversation title and message count.

        Validates:
        - Title shows conversation title in cyan
        - Message count shown in title
        - Line 382 executed
        """
        # Capture output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_messages_rich(sample_conversation)

        output = output_buffer.getvalue()

        # Assert: Title and count in output
        # Rich uses ANSI escape codes, but the text should be present
        assert "Test Conversation" in output
        assert "3 messages" in output

    def test_format_messages_rich_includes_message_data(
        self, sample_conversation: Conversation
    ) -> None:
        """Test table includes all message data rows.

        Validates:
        - All messages shown
        - IDs, roles, timestamps, content present
        - Lines 393-414 executed
        """
        # Capture output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_messages_rich(sample_conversation)

        output = output_buffer.getvalue()

        # Assert: Message IDs present
        assert "msg-1" in output
        assert "msg-2" in output
        assert "msg-3" in output

        # Assert: Timestamps present
        assert "2024-03-09 12:00:00" in output
        assert "2024-03-09 12:01:00" in output
        assert "2024-03-09 12:02:00" in output

        # Assert: Content present
        assert "First user message" in output
        assert "First assistant response" in output
        assert "System message" in output

    def test_format_messages_rich_uses_role_colors(self, sample_conversation: Conversation) -> None:
        """Test roles are color-coded using get_role_color().

        Validates:
        - get_role_color() called for each role
        - Lines 398, 411 executed
        """
        from unittest.mock import patch

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        with patch("echomine.cli.commands.get.Console", return_value=console):
            with patch("echomine.cli.commands.get.get_role_color") as mock_get_role_color:
                # Mock returns different colors for each role
                mock_get_role_color.side_effect = lambda role: {
                    "user": "green",
                    "assistant": "blue",
                    "system": "yellow",
                }.get(role, "white")

                # Act
                _format_messages_rich(sample_conversation)

                # Assert: get_role_color called for each message
                assert mock_get_role_color.call_count == 3

    def test_format_messages_rich_truncates_long_content(self) -> None:
        """Test content longer than 100 chars is truncated with ellipsis.

        Validates:
        - Content > 100 chars truncated to 97 + "..."
        - Lines 401-403 executed
        """
        # Create conversation with long message
        long_content = "A" * 150
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

        # Capture output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_messages_rich(conversation)

        output = output_buffer.getvalue()

        # Assert: Truncated with ellipsis
        # Rich uses Unicode ellipsis '…' (U+2026) instead of '...'
        assert "…" in output or "..." in output
        # Full 150 char string should NOT be present
        assert long_content not in output

    def test_format_messages_rich_handles_empty_content(self) -> None:
        """Test empty content displays as '(empty)'.

        Validates:
        - Empty string → '(empty)' display
        - Lines 405-406 executed
        """
        # Create conversation with empty message
        empty_message = Message(
            id="msg-empty",
            role="user",
            content="",
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        conversation = Conversation(
            id="conv-empty",
            title="Empty content",
            created_at=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            updated_at=None,
            messages=[empty_message],
        )

        # Capture output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_messages_rich(conversation)

        output = output_buffer.getvalue()

        # Assert: (empty) shown
        assert "(empty)" in output


# =============================================================================
# Unit Tests: _format_conversation_rich()
# =============================================================================


@pytest.mark.unit
class TestFormatConversationRich:
    """Unit tests for _format_conversation_rich() function (lines 437-520)."""

    def test_format_conversation_rich_creates_panel(
        self, sample_conversation: Conversation
    ) -> None:
        """Test _format_conversation_rich() creates and prints a Rich panel.

        Validates:
        - Rich Panel is created
        - Panel is printed to stdout
        - Lines 437-520 executed
        """
        # Capture stdout
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Output generated
        assert len(output) > 0
        assert "Conversation Details" in output

    def test_format_conversation_rich_includes_metadata(
        self, sample_conversation: Conversation
    ) -> None:
        """Test panel includes conversation metadata.

        Validates:
        - ID, title, created, updated, message count shown
        - Lines 447-457 executed
        """
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Metadata present
        assert "conv-001" in output
        assert "Test Conversation" in output
        assert "2024-03-09 12:00:00" in output  # created
        assert "2024-03-09 12:05:00" in output  # updated
        assert "3 messages" in output

    def test_format_conversation_rich_includes_role_summary(
        self, sample_conversation: Conversation
    ) -> None:
        """Test panel includes message summary by role.

        Validates:
        - Message Summary section shown
        - Role counts table created
        - Lines 462-479 executed
        """
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Role summary present
        assert "Message Summary" in output

    def test_format_conversation_rich_verbose_shows_messages(
        self, sample_conversation: Conversation
    ) -> None:
        """Test verbose mode shows message details.

        Validates:
        - verbose=True adds Messages section
        - Each message numbered with timestamp and role
        - Lines 482-501 executed
        """
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(sample_conversation, verbose=True)

        output = output_buffer.getvalue()

        # Assert: Messages section present
        assert "Messages:" in output

        # Assert: Message details shown
        # Note: exact format may vary with Rich, check for key content
        assert "2024-03-09 12:00:00" in output
        assert "2024-03-09 12:01:00" in output

    def test_format_conversation_rich_verbose_truncates_content(self) -> None:
        """Test verbose mode truncates content > 80 chars.

        Validates:
        - Content > 80 chars truncated to 77 + "..."
        - Lines 494-496 executed
        """
        # Create conversation with long message
        long_content = "B" * 100
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

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(conversation, verbose=True)

        output = output_buffer.getvalue()

        # Assert: Truncated with ellipsis
        assert "..." in output

    def test_format_conversation_rich_null_updated_at(
        self, conversation_null_updated: Conversation
    ) -> None:
        """Test null updated_at uses created_at fallback.

        Validates:
        - updated_at_or_created property works
        - Line 452 executed
        """
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_conversation_rich(conversation_null_updated, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Updated timestamp shown (fallback to created)
        assert "2024-03-09 12:00:00" in output


# =============================================================================
# Unit Tests: _format_message_rich()
# =============================================================================


@pytest.mark.unit
class TestFormatMessageRich:
    """Unit tests for _format_message_rich() function (lines 544-607)."""

    def test_format_message_rich_creates_panel(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test _format_message_rich() creates and prints a Rich panel.

        Validates:
        - Rich Panel created
        - Panel printed to stdout
        - Lines 544-607 executed
        """
        message = sample_messages[0]

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Output generated
        assert len(output) > 0
        assert "Message Details" in output

    def test_format_message_rich_includes_message_metadata(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test panel includes message metadata.

        Validates:
        - ID, role, timestamp, parent_id shown
        - Lines 552-562 executed
        """
        message = sample_messages[1]  # msg-2 (has parent)

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Metadata present
        assert "msg-2" in output
        assert "assistant" in output
        assert "2024-03-09 12:01:00" in output
        assert "msg-1" in output  # parent_id

    def test_format_message_rich_shows_content(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test panel includes message content.

        Validates:
        - Content section shown
        - Lines 564-572 executed
        """
        message = sample_messages[0]

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Content shown
        assert "Content:" in output
        assert "First user message" in output

    def test_format_message_rich_truncates_long_content_non_verbose(
        self, sample_conversation: Conversation
    ) -> None:
        """Test non-verbose mode truncates content > 200 chars.

        Validates:
        - Content > 200 chars truncated to 197 + "..."
        - Lines 569-570 executed
        """
        # Create long message
        long_content = "C" * 250
        long_message = Message(
            id="msg-long",
            role="user",
            content=long_content,
            timestamp=datetime(2024, 3, 9, 12, 0, 0, tzinfo=UTC),
            parent_id=None,
        )

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(long_message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Truncated with ellipsis
        assert "..." in output
        # Full content should NOT be present
        assert long_content not in output

    def test_format_message_rich_includes_conversation_context(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test panel includes conversation context.

        Validates:
        - Conversation ID, title, message count shown
        - Lines 574-578 executed
        """
        message = sample_messages[0]

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Conversation context present
        assert "Conversation Context:" in output
        assert "conv-001" in output
        assert "Test Conversation" in output
        assert "3" in output  # message count

    def test_format_message_rich_verbose_shows_all_messages(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test verbose mode shows all conversation messages.

        Validates:
        - verbose=True adds "All Messages in Conversation" section
        - Current message marked with >>> marker
        - Lines 581-591 executed
        """
        message = sample_messages[1]  # msg-2

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=True)

        output = output_buffer.getvalue()

        # Assert: All messages section present
        assert "All Messages in Conversation:" in output

    def test_format_message_rich_root_message_parent_id(
        self, sample_messages: list[Message], sample_conversation: Conversation
    ) -> None:
        """Test root message (parent=None) displays 'None (root message)'.

        Validates:
        - Line 561 executed
        """
        message = sample_messages[0]  # root message

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True, width=120)

        from unittest.mock import patch

        with patch("echomine.cli.commands.get.Console", return_value=console):
            # Act
            _format_message_rich(message, sample_conversation, verbose=False)

        output = output_buffer.getvalue()

        # Assert: Root message indicator shown
        assert "None (root message)" in output or "root" in output.lower()
