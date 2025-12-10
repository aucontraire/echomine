"""Unit tests to improve CLI command coverage to 95%+.

This module targets specific uncovered lines in CLI commands identified by
Codecov coverage reports. Tests focus on error handling paths, conditional
branches, and edge cases that are difficult to reach through integration tests.

Coverage Targets:
    - get.py: 44 missing lines (Rich formatters, error handlers, verbose mode)
    - stats.py: 15 missing lines (per-conversation stats, error paths)
    - search.py: 11 missing lines (validation errors, edge cases)
    - formatters.py: 4 missing lines (edge cases)
    - list.py: 12 missing lines (sorting, error paths)

Constitution Compliance:
    - Principle III: TDD - Tests written to cover missing lines
    - Principle VI: Strict typing - All type hints validated
    - Principle I: Library-first - Tests focus on CLI layer only

Test Strategy:
    - Use mocks to simulate error conditions (FileNotFoundError, PermissionError)
    - Use pytest.raises to verify exception handling
    - Patch sys.stdout.isatty() to test Rich formatting paths
    - Test all error message formatting and exit codes
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import typer
from pydantic import ValidationError as PydanticValidationError

from echomine.cli.commands.get import get_conversation, get_message, get_messages
from echomine.cli.commands.list import list_conversations
from echomine.cli.commands.search import search_conversations
from echomine.cli.formatters import (
    format_json,
    format_search_results,
    format_search_results_json,
    format_text_table,
)
from echomine.exceptions import ParseError
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.search import SearchResult


if TYPE_CHECKING:
    pass


@pytest.fixture
def sample_conversation() -> Conversation:
    """Create a sample conversation for testing."""
    return Conversation(
        id="test-conv-001",
        title="Test Conversation",
        created_at=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
        updated_at=datetime(2024, 1, 15, 14, 45, 20, tzinfo=UTC),
        messages=[
            Message(
                id="msg-001",
                role="user",
                content="Hello, this is a test message",
                timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                parent_id=None,
            ),
            Message(
                id="msg-002",
                role="assistant",
                content="This is a response message",
                timestamp=datetime(2024, 1, 15, 10, 30, 47, tzinfo=UTC),
                parent_id="msg-001",
            ),
        ],
    )


@pytest.fixture
def sample_message() -> Message:
    """Create a sample message for testing."""
    return Message(
        id="msg-test-001",
        role="user",
        content="This is a test message with some content",
        timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
        parent_id=None,
    )


# ============================================================================
# get.py Coverage Tests (44 missing lines)
# ============================================================================


@pytest.mark.unit
class TestGetConversationCoverage:
    """Tests for get conversation command uncovered lines."""

    def test_get_conversation_rich_formatter_path(
        self, tmp_path: Path, sample_conversation: Conversation
    ) -> None:
        """Test Rich formatter path for conversation display.

        Coverage Target: Lines 703-705 (Rich formatter branch)
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with (
            patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get,
            patch("echomine.cli.commands.get.is_rich_enabled", return_value=True),
            patch("echomine.cli.commands.get._format_conversation_rich") as mock_rich,
        ):
            mock_get.return_value = sample_conversation

            # Invoke command with format=table (triggers Rich path when TTY)
            # Successful commands return None, don't raise Exit
            get_conversation(
                file_path=test_file,
                conversation_id="test-conv-001",
                format="table",
                verbose=False,
            )

            # Assert: Rich formatter was called
            mock_rich.assert_called_once()

    def test_get_conversation_verbose_mode(
        self, tmp_path: Path, sample_conversation: Conversation
    ) -> None:
        """Test verbose mode for conversation display.

        Coverage Target: Lines 703-709 (verbose flag propagation)
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with (
            patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get,
            patch("echomine.cli.commands.get.is_rich_enabled", return_value=True),
            patch("echomine.cli.commands.get._format_conversation_rich") as mock_rich,
        ):
            mock_get.return_value = sample_conversation

            # Invoke with verbose=True
            get_conversation(
                file_path=test_file,
                conversation_id="test-conv-001",
                format="table",
                verbose=True,
            )

            # Assert: Rich formatter called with verbose=True
            mock_rich.assert_called_once_with(sample_conversation, verbose=True)

    def test_get_conversation_file_not_found_exception(self, tmp_path: Path) -> None:
        """Test FileNotFoundError exception handler.

        Coverage Target: Lines 714-716
        """
        test_file = tmp_path / "nonexistent.json"

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = FileNotFoundError("File not found")

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 1 for file not found
            assert exc_info.value.exit_code == 1

    def test_get_conversation_permission_error(self, tmp_path: Path) -> None:
        """Test PermissionError exception handler.

        Coverage Target: Lines 718-723
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = PermissionError("Permission denied")

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 1 for permission error
            assert exc_info.value.exit_code == 1

    def test_get_conversation_parse_error(self, tmp_path: Path) -> None:
        """Test ParseError exception handler.

        Coverage Target: Lines 725-727
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = ParseError("Invalid JSON")

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 1 for parse error
            assert exc_info.value.exit_code == 1

    def test_get_conversation_pydantic_validation_error(self, tmp_path: Path) -> None:
        """Test Pydantic ValidationError exception handler.

        Coverage Target: Lines 729-731
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        # Create a proper Pydantic v2 validation error
        # The error field is required in Pydantic v2
        try:
            # Use ValueError wrapper which Pydantic converts properly
            raise PydanticValidationError.from_exception_data(
                title="Conversation",
                line_errors=[
                    {
                        "type": "value_error",
                        "loc": ("field",),
                        "input": "bad_value",
                        "ctx": {"error": ValueError("Test validation error")},
                    }
                ],
            )
        except PydanticValidationError as e:
            mock_error = e

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = mock_error

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 1 for validation error
            assert exc_info.value.exit_code == 1

    def test_get_conversation_keyboard_interrupt(self, tmp_path: Path) -> None:
        """Test KeyboardInterrupt exception handler.

        Coverage Target: Lines 733-735
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = KeyboardInterrupt()

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 130 for keyboard interrupt
            assert exc_info.value.exit_code == 130

    def test_get_conversation_generic_exception(self, tmp_path: Path) -> None:
        """Test generic Exception catch-all handler.

        Coverage Target: Lines 741-743
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(typer.Exit) as exc_info:
                get_conversation(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    format="json",
                    verbose=False,
                )

            # Assert: Exit code 1 for generic error
            assert exc_info.value.exit_code == 1


@pytest.mark.unit
class TestGetMessageCoverage:
    """Tests for get message command uncovered lines."""

    def test_get_message_rich_formatter_path(
        self, tmp_path: Path, sample_message: Message, sample_conversation: Conversation
    ) -> None:
        """Test Rich formatter path for message display.

        Coverage Target: Lines 880-882
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with (
            patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get,
            patch("echomine.cli.commands.get.is_rich_enabled", return_value=True),
            patch("echomine.cli.commands.get._format_message_rich") as mock_rich,
        ):
            mock_get.return_value = (sample_message, sample_conversation)

            # Invoke command with format=table (triggers Rich path when TTY)
            get_message(
                file_path=test_file,
                message_id="msg-test-001",
                format="table",
                conversation_id=None,
                verbose=False,
            )

            # Assert: Rich formatter was called
            mock_rich.assert_called_once()

    def test_get_message_file_not_found_exception(self, tmp_path: Path) -> None:
        """Test FileNotFoundError exception handler for get message.

        Coverage Target: Lines 891-893
        """
        test_file = tmp_path / "nonexistent.json"

        with patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get:
            mock_get.side_effect = FileNotFoundError("File not found")

            with pytest.raises(typer.Exit) as exc_info:
                get_message(
                    file_path=test_file,
                    message_id="msg-test-001",
                    format="json",
                    conversation_id=None,
                    verbose=False,
                )

            # Assert: Exit code 1 for file not found
            assert exc_info.value.exit_code == 1

    def test_get_message_permission_error(self, tmp_path: Path) -> None:
        """Test PermissionError exception handler for get message.

        Coverage Target: Lines 895-900
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get:
            mock_get.side_effect = PermissionError("Permission denied")

            with pytest.raises(typer.Exit) as exc_info:
                get_message(
                    file_path=test_file,
                    message_id="msg-test-001",
                    format="json",
                    conversation_id=None,
                    verbose=False,
                )

            # Assert: Exit code 1 for permission error
            assert exc_info.value.exit_code == 1

    def test_get_message_parse_error(self, tmp_path: Path) -> None:
        """Test ParseError exception handler for get message.

        Coverage Target: Lines 902-904
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get:
            mock_get.side_effect = ParseError("Invalid JSON")

            with pytest.raises(typer.Exit) as exc_info:
                get_message(
                    file_path=test_file,
                    message_id="msg-test-001",
                    format="json",
                    conversation_id=None,
                    verbose=False,
                )

            # Assert: Exit code 1 for parse error
            assert exc_info.value.exit_code == 1

    def test_get_message_keyboard_interrupt(self, tmp_path: Path) -> None:
        """Test KeyboardInterrupt exception handler for get message.

        Coverage Target: Lines 910-912
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get:
            mock_get.side_effect = KeyboardInterrupt()

            with pytest.raises(typer.Exit) as exc_info:
                get_message(
                    file_path=test_file,
                    message_id="msg-test-001",
                    format="json",
                    conversation_id=None,
                    verbose=False,
                )

            # Assert: Exit code 130 for keyboard interrupt
            assert exc_info.value.exit_code == 130

    def test_get_message_generic_exception(self, tmp_path: Path) -> None:
        """Test generic Exception catch-all handler for get message.

        Coverage Target: Lines 918-920
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_message_by_id") as mock_get:
            mock_get.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(typer.Exit) as exc_info:
                get_message(
                    file_path=test_file,
                    message_id="msg-test-001",
                    format="json",
                    conversation_id=None,
                    verbose=False,
                )

            # Assert: Exit code 1 for generic error
            assert exc_info.value.exit_code == 1


@pytest.mark.unit
class TestGetMessagesCoverage:
    """Tests for get messages (list messages in conversation) command uncovered lines."""

    def test_get_messages_file_not_found_manual_check(self, tmp_path: Path) -> None:
        """Test manual file existence check in get messages.

        Coverage Target: Lines 978-980
        """
        test_file = tmp_path / "nonexistent.json"

        with pytest.raises(typer.Exit) as exc_info:
            get_messages(
                file_path=test_file,
                conversation_id="test-conv-001",
                json_output=False,
            )

        # Assert: Exit code 1 for file not found
        assert exc_info.value.exit_code == 1

    def test_get_messages_rich_formatter_path(
        self, tmp_path: Path, sample_conversation: Conversation
    ) -> None:
        """Test Rich formatter path for messages list display.

        Coverage Target: Lines 1005-1007
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with (
            patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get,
            patch("echomine.cli.commands.get.is_rich_enabled", return_value=True),
            patch("echomine.cli.commands.get._format_messages_rich") as mock_rich,
        ):
            mock_get.return_value = sample_conversation

            # Invoke command without --json (triggers Rich path when TTY)
            get_messages(
                file_path=test_file,
                conversation_id="test-conv-001",
                json_output=False,
            )

            # Assert: Rich formatter was called
            mock_rich.assert_called_once()

    def test_get_messages_file_not_found_exception(self, tmp_path: Path) -> None:
        """Test FileNotFoundError exception handler for get messages.

        Coverage Target: Lines 1016-1018
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = FileNotFoundError("File not found")

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 1 for file not found
            assert exc_info.value.exit_code == 1

    def test_get_messages_permission_error(self, tmp_path: Path) -> None:
        """Test PermissionError exception handler for get messages.

        Coverage Target: Lines 1020-1025
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = PermissionError("Permission denied")

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 1 for permission error
            assert exc_info.value.exit_code == 1

    def test_get_messages_parse_error(self, tmp_path: Path) -> None:
        """Test ParseError exception handler for get messages.

        Coverage Target: Lines 1027-1029
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = ParseError("Invalid JSON")

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 1 for parse error
            assert exc_info.value.exit_code == 1

    def test_get_messages_pydantic_validation_error(self, tmp_path: Path) -> None:
        """Test Pydantic ValidationError exception handler for get messages.

        Coverage Target: Lines 1031-1033
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        # Create a proper validation error with ctx error
        try:
            raise PydanticValidationError.from_exception_data(
                title="Conversation",
                line_errors=[
                    {
                        "type": "value_error",
                        "loc": ("field",),
                        "input": "bad_value",
                        "ctx": {"error": ValueError("Test validation error")},
                    }
                ],
            )
        except PydanticValidationError as e:
            mock_error = e

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = mock_error

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 1 for validation error
            assert exc_info.value.exit_code == 1

    def test_get_messages_keyboard_interrupt(self, tmp_path: Path) -> None:
        """Test KeyboardInterrupt exception handler for get messages.

        Coverage Target: Lines 1035-1037
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = KeyboardInterrupt()

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 130 for keyboard interrupt
            assert exc_info.value.exit_code == 130

    def test_get_messages_generic_exception(self, tmp_path: Path) -> None:
        """Test generic Exception catch-all handler for get messages.

        Coverage Target: Lines 1043-1045
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.get_conversation_by_id") as mock_get:
            mock_get.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(typer.Exit) as exc_info:
                get_messages(
                    file_path=test_file,
                    conversation_id="test-conv-001",
                    json_output=True,
                )

            # Assert: Exit code 1 for generic error
            assert exc_info.value.exit_code == 1


# ============================================================================
# stats.py Coverage Tests (15 missing lines)
# ============================================================================
# Note: Stats command error handlers (Lines 414-436) are difficult to test
# in unit tests because the Progress context manager interferes with mocking.
# These lines are covered by integration/contract tests instead.


# ============================================================================
# search.py Coverage Tests (11 missing lines)
# ============================================================================


@pytest.mark.unit
class TestSearchCoverage:
    """Tests for search command uncovered lines."""

    def test_search_pydantic_validation_error_with_min_max_bounds(self, tmp_path: Path) -> None:
        """Test Pydantic validation error for min/max message bounds.

        Coverage Target: Lines 454-470 (validation error with min > max)
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        # This should trigger validation error: min_messages > max_messages
        with pytest.raises(typer.Exit) as exc_info:
            search_conversations(
                file_path=test_file,
                keywords=["python"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date=None,
                to_date=None,
                min_messages=100,  # min > max triggers validation error
                max_messages=10,
                limit=None,
                sort="score",
                order="desc",
                format="text",
                quiet=True,
                json=False,
                csv_messages=False,
            )

        # Assert: Exit code 2 for validation error (invalid arguments)
        assert exc_info.value.exit_code == 2

    def test_search_permission_error_handler(self, tmp_path: Path) -> None:
        """Test PermissionError exception handler for search command.

        Coverage Target: Lines 588-594
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.search") as mock_search:
            mock_search.side_effect = PermissionError("Permission denied")

            with pytest.raises(typer.Exit) as exc_info:
                search_conversations(
                    file_path=test_file,
                    keywords=["python"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    min_messages=None,
                    max_messages=None,
                    limit=None,
                    sort="score",
                    order="desc",
                    format="text",
                    quiet=True,
                    json=False,
                    csv_messages=False,
                )

            # Assert: Exit code 1 for permission error
            assert exc_info.value.exit_code == 1


# ============================================================================
# list.py Coverage Tests (12 missing lines)
# ============================================================================


@pytest.mark.unit
class TestListCoverage:
    """Tests for list command uncovered lines."""

    def test_list_sort_by_date_with_updated_at_none(
        self, tmp_path: Path, sample_conversation: Conversation
    ) -> None:
        """Test sorting by date when updated_at is None.

        Coverage Target: Line 190 (updated_at fallback to created_at)
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        # Create conversation with updated_at=None
        conv_without_update = Conversation(
            id="test-conv-002",
            title="No Updates",
            created_at=datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC),
            updated_at=None,  # This should fall back to created_at
            messages=[
                Message(
                    id="msg-001",
                    role="user",
                    content="Test message",
                    timestamp=datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC),
                    parent_id=None,
                )
            ],
        )

        with (
            patch("echomine.adapters.openai.OpenAIAdapter.stream_conversations") as mock_stream,
            patch("typer.echo"),
        ):  # Suppress output for clean test
            mock_stream.return_value = [conv_without_update]

            # Invoke with date sorting (default) - successful commands return None
            list_conversations(
                file_path=test_file,
                format="json",
                limit=None,
                sort="date",
                order="desc",
            )

    def test_list_file_not_found_exception(self, tmp_path: Path) -> None:
        """Test FileNotFoundError exception handler for list command.

        Coverage Target: Lines 241-247
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.stream_conversations") as mock_stream:
            mock_stream.side_effect = FileNotFoundError("File not found")

            with pytest.raises(typer.Exit) as exc_info:
                list_conversations(
                    file_path=test_file,
                    format="json",
                    limit=None,
                    sort="date",
                    order="",
                )

            # Assert: Exit code 1 for file not found
            assert exc_info.value.exit_code == 1

    def test_list_permission_error(self, tmp_path: Path) -> None:
        """Test PermissionError exception handler for list command.

        Coverage Target: Lines 249-255
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.stream_conversations") as mock_stream:
            mock_stream.side_effect = PermissionError("Permission denied")

            with pytest.raises(typer.Exit) as exc_info:
                list_conversations(
                    file_path=test_file,
                    format="json",
                    limit=None,
                    sort="date",
                    order="",
                )

            # Assert: Exit code 1 for permission error
            assert exc_info.value.exit_code == 1

    def test_list_keyboard_interrupt(self, tmp_path: Path) -> None:
        """Test KeyboardInterrupt exception handler for list command.

        Coverage Target: Lines 273-279
        """
        test_file = tmp_path / "test_export.json"
        test_file.write_text("[]")

        with patch("echomine.adapters.openai.OpenAIAdapter.stream_conversations") as mock_stream:
            mock_stream.side_effect = KeyboardInterrupt()

            with pytest.raises(typer.Exit) as exc_info:
                list_conversations(
                    file_path=test_file,
                    format="json",
                    limit=None,
                    sort="date",
                    order="",
                )

            # Assert: Exit code 130 for keyboard interrupt
            assert exc_info.value.exit_code == 130


# ============================================================================
# formatters.py Coverage Tests (4 missing lines)
# ============================================================================


@pytest.mark.unit
class TestFormattersCoverage:
    """Tests for formatters module uncovered lines."""

    def test_format_text_table_long_title_truncation(
        self, sample_conversation: Conversation
    ) -> None:
        """Test title truncation for titles longer than 30 chars.

        Coverage Target: Line 93 (title truncation with ellipsis)
        """
        # Create conversation with very long title
        long_title_conv = Conversation(
            id="test-conv-003",
            title="This is a very long conversation title that exceeds thirty characters",
            created_at=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, 14, 45, 20, tzinfo=UTC),
            messages=[
                Message(
                    id="msg-001",
                    role="user",
                    content="Test",
                    timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                    parent_id=None,
                )
            ],
        )

        output = format_text_table([long_title_conv])

        # Assert: Title is truncated with ellipsis
        assert "..." in output
        # The formatted title in the output should be truncated
        # Format is: ID (36 chars) + 2 spaces + Title (30 chars) + ...
        # Just verify ellipsis appears which proves truncation happened
        assert "This is a very long convers..." in output

    def test_format_search_results_empty_snippet(self, sample_conversation: Conversation) -> None:
        """Test search result formatting with empty snippet.

        Coverage Target: Line 235 (empty snippet handling)
        """
        # Create search result with empty snippet
        result = SearchResult(
            conversation=sample_conversation,
            score=0.85,
            matched_message_ids=["msg-001"],
            snippet="",  # Empty snippet
        )

        output = format_search_results([result])

        # Assert: Output contains the result
        assert "test-conv-001" in output
        assert "0.85" in output

    def test_format_search_results_json_with_none_values(
        self, sample_conversation: Conversation
    ) -> None:
        """Test JSON formatting with None values for optional fields.

        Coverage Target: Lines 588, 593 (None handling for dates)
        """
        output = format_search_results_json(
            results=[],
            query_keywords=None,
            query_phrases=None,
            query_match_mode="any",
            query_exclude_keywords=None,
            query_role_filter=None,
            query_title_filter=None,
            query_from_date=None,  # Test None handling
            query_to_date=None,  # Test None handling
            query_limit=10,
            total_results=0,
            skipped_conversations=0,
            elapsed_seconds=0.123,
        )

        # Assert: Valid JSON output
        import json

        data = json.loads(output)

        # Assert: Metadata contains null values for dates
        assert data["metadata"]["query"]["date_from"] is None
        assert data["metadata"]["query"]["date_to"] is None

    def test_format_json_empty_conversation_list(self) -> None:
        """Test JSON formatting with empty conversation list.

        Coverage Target: Edge case for empty list handling
        """
        output = format_json([])

        # Assert: Valid JSON array
        import json

        data = json.loads(output)

        # Assert: Empty array
        assert data == []
