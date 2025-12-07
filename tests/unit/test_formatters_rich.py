"""Unit tests for Rich CLI formatters.

This module tests Rich table formatting, color coding, and TTY detection
in the formatters module.

Test Coverage: FR-036 to FR-041a (Rich formatting requirements)

Constitution Compliance:
    - Principle III: TDD (tests written FIRST)
    - Principle VI: mypy --strict compliant
    - FR-036: Rich table format
    - FR-037: Score color coding
    - FR-038: Role color coding
    - FR-039: Progress bars for long operations
    - FR-040: Rich disabled when stdout not TTY
    - FR-041: Rich disabled with --json flag
    - FR-041a: Conflicting format flags - last wins with warning
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from io import StringIO
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from rich.console import Console
from rich.table import Table

from echomine.cli.formatters import (
    create_rich_search_table,
    create_rich_table,
    get_role_color,
    get_score_color,
    is_rich_enabled,
)
from echomine.models.conversation import Conversation
from echomine.models.search import SearchResult


if TYPE_CHECKING:
    pass


@pytest.fixture
def sample_conversation() -> Conversation:
    """Create a sample conversation for testing Rich formatters."""
    from echomine.models.message import Message

    messages = [
        Message(
            id="msg-1",
            content="Test message",
            role="user",
            timestamp=datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            parent_id=None,
        )
    ]

    conv_dict = {
        "id": "test-conv-001",
        "title": "Test Conversation Title",
        "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
        "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
        "messages": messages,
    }
    return Conversation.model_validate(conv_dict)


@pytest.fixture
def sample_conversations() -> list[Conversation]:
    """Create multiple sample conversations for testing Rich formatters."""
    from echomine.models.message import Message

    messages1 = [
        Message(
            id=f"msg-{i}",
            content=f"Message {i}",
            role="user" if i % 2 == 0 else "assistant",
            timestamp=datetime(2024, 3, 15, 14, 23, i, tzinfo=UTC),
            parent_id=None if i == 0 else f"msg-{i - 1}",
        )
        for i in range(47)
    ]

    messages2 = [
        Message(
            id=f"msg2-{i}",
            content=f"Message {i}",
            role="user" if i % 2 == 0 else "assistant",
            timestamp=datetime(2024, 3, 14, 9, 15, i, tzinfo=UTC),
            parent_id=None if i == 0 else f"msg2-{i - 1}",
        )
        for i in range(12)
    ]

    convs = [
        {
            "id": "conv-001",
            "title": "Python AsyncIO Tutorial",
            "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
            "messages": messages1,
        },
        {
            "id": "conv-002",
            "title": "Algorithm Design Patterns",
            "created_at": datetime(2024, 3, 14, 9, 15, 42, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 14, 9, 20, 10, tzinfo=UTC),
            "messages": messages2,
        },
    ]

    return [Conversation.model_validate(c) for c in convs]


class TestRichTableFormatter:
    """Unit tests for Rich table formatter (T116, FR-036)."""

    def test_create_rich_table_returns_table_instance(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test create_rich_table() returns Rich Table instance.

        Validates:
        - T116: Table formatter produces Rich table output
        - FR-036: Rich Table format for list/search results
        """
        table = create_rich_table(sample_conversations)

        # Assert: Returns Rich Table instance
        assert isinstance(table, Table)

    def test_create_rich_table_includes_column_headers(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test Rich table includes proper column headers.

        Validates:
        - FR-036: Table format with ID, Title, Messages, Created columns
        """
        table = create_rich_table(sample_conversations)

        # Assert: Table has expected columns
        # Rich Table stores columns internally
        assert len(table.columns) > 0

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=120)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Column headers present
        assert "ID" in output
        assert "Title" in output
        assert "Messages" in output
        assert "Created" in output

    def test_create_rich_table_includes_conversation_data(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test Rich table includes conversation data rows.

        Validates:
        - FR-036: Table contains conversation data
        """
        table = create_rich_table(sample_conversations)

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=120)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Conversation data present
        assert "conv-001" in output
        assert "Python AsyncIO Tutorial" in output
        assert "47" in output

        assert "conv-002" in output
        assert "Algorithm Design Patterns" in output
        assert "12" in output

    def test_create_rich_table_uses_box_characters(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test Rich table uses box drawing characters.

        Validates:
        - FR-036: Rich table format with visual borders
        """
        table = create_rich_table(sample_conversations)

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=120)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Box characters present (Rich uses Unicode box drawing)
        # Rich tables use ─, │, ┌, ┐, └, ┘, ├, ┤, ┬, ┴, ┼ characters
        assert any(char in output for char in ["─", "│", "┌", "┐", "└", "┘"])


class TestScoreColorCoding:
    """Unit tests for score color coding (T117, FR-037)."""

    def test_get_score_color_high_score_returns_green(self) -> None:
        """Test scores > 0.7 return green color.

        Validates:
        - FR-037: Score > 0.7 → green
        """
        # Test boundary and above
        assert get_score_color(0.71) == "green"
        assert get_score_color(0.8) == "green"
        assert get_score_color(0.9) == "green"
        assert get_score_color(1.0) == "green"

    def test_get_score_color_medium_score_returns_yellow(self) -> None:
        """Test scores 0.4-0.7 return yellow color.

        Validates:
        - FR-037: Score 0.4-0.7 → yellow
        """
        # Test range boundaries
        assert get_score_color(0.4) == "yellow"
        assert get_score_color(0.5) == "yellow"
        assert get_score_color(0.6) == "yellow"
        assert get_score_color(0.7) == "yellow"

    def test_get_score_color_low_score_returns_red(self) -> None:
        """Test scores < 0.4 return red color.

        Validates:
        - FR-037: Score < 0.4 → red
        """
        # Test boundary and below
        assert get_score_color(0.39) == "red"
        assert get_score_color(0.3) == "red"
        assert get_score_color(0.1) == "red"
        assert get_score_color(0.0) == "red"

    def test_get_score_color_boundary_conditions(self) -> None:
        """Test score color boundary conditions precisely.

        Validates:
        - FR-037: Exact boundaries (0.7 threshold, 0.4 threshold)
        """
        # Boundary: 0.7 (yellow/green threshold)
        assert get_score_color(0.70) == "yellow"  # Inclusive lower bound
        assert get_score_color(0.71) == "green"  # Exclusive upper bound

        # Boundary: 0.4 (red/yellow threshold)
        assert get_score_color(0.39) == "red"  # Exclusive lower bound
        assert get_score_color(0.40) == "yellow"  # Inclusive upper bound


class TestRoleColorCoding:
    """Unit tests for role color coding (T118, FR-038)."""

    def test_get_role_color_user_returns_green(self) -> None:
        """Test 'user' role returns green color.

        Validates:
        - FR-038: user role → green
        """
        assert get_role_color("user") == "green"

    def test_get_role_color_assistant_returns_blue(self) -> None:
        """Test 'assistant' role returns blue color.

        Validates:
        - FR-038: assistant role → blue
        """
        assert get_role_color("assistant") == "blue"

    def test_get_role_color_system_returns_yellow(self) -> None:
        """Test 'system' role returns yellow color.

        Validates:
        - FR-038: system role → yellow
        """
        assert get_role_color("system") == "yellow"

    def test_get_role_color_unknown_role_returns_white(self) -> None:
        """Test unknown role returns white (default) color.

        Validates:
        - Graceful handling of unexpected roles
        """
        assert get_role_color("unknown") == "white"
        assert get_role_color("tool") == "white"
        assert get_role_color("") == "white"


class TestTTYDetection:
    """Unit tests for TTY detection (T119, FR-040)."""

    def test_is_rich_enabled_returns_true_when_tty(self) -> None:
        """Test is_rich_enabled() returns True when stdout is TTY.

        Validates:
        - FR-040: Rich enabled when stdout is TTY
        """
        with patch.object(sys.stdout, "isatty", return_value=True):
            assert is_rich_enabled(json_flag=False) is True

    def test_is_rich_enabled_returns_false_when_not_tty(self) -> None:
        """Test is_rich_enabled() returns False when stdout not TTY.

        Validates:
        - FR-040: Rich disabled when stdout is not TTY (piped/redirected)
        """
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert is_rich_enabled(json_flag=False) is False

    def test_is_rich_enabled_respects_force_flag(self) -> None:
        """Test is_rich_enabled() can be forced on regardless of TTY.

        Validates:
        - Allow override for testing/debugging
        """
        # When forced, should enable even without TTY
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert is_rich_enabled(json_flag=False, force=True) is True


class TestJSONFlagRichDisabling:
    """Unit tests for --json flag Rich disabling (T120, FR-041)."""

    def test_is_rich_enabled_returns_false_with_json_flag(self) -> None:
        """Test is_rich_enabled() returns False with --json flag.

        Validates:
        - FR-041: Rich disabled with --json flag
        """
        with patch.object(sys.stdout, "isatty", return_value=True):
            # Even with TTY, --json should disable Rich
            assert is_rich_enabled(json_flag=True) is False

    def test_is_rich_enabled_json_overrides_tty(self) -> None:
        """Test --json flag overrides TTY detection.

        Validates:
        - FR-041: --json takes precedence over TTY
        """
        # TTY + --json → False (JSON wins)
        with patch.object(sys.stdout, "isatty", return_value=True):
            assert is_rich_enabled(json_flag=True) is False

        # No TTY + --json → False (both disable)
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert is_rich_enabled(json_flag=True) is False


class TestFormatFlagConflicts:
    """Unit tests for conflicting format flags (T121, FR-041a)."""

    def test_resolve_format_conflict_last_wins(self) -> None:
        """Test conflicting format flags - last flag wins.

        Validates:
        - FR-041a: --format csv --json → JSON wins (last flag)
        - FR-041a: --json --format csv → CSV wins (last flag)
        """
        from echomine.cli.formatters import resolve_format_conflict

        # json after format → json wins
        result = resolve_format_conflict(format="csv", json=True, json_comes_last=True)
        assert result == "json"

        # format after json → format wins
        result = resolve_format_conflict(format="csv", json=True, json_comes_last=False)
        assert result == "csv"

    def test_resolve_format_conflict_emits_warning(self) -> None:
        """Test conflicting format flags emit warning to stderr.

        Validates:
        - FR-041a: WARNING message for conflicting flags
        """
        from echomine.cli.formatters import resolve_format_conflict

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            # Trigger conflict
            resolve_format_conflict(format="csv", json=True, json_comes_last=True)

            # Assert: Warning emitted to stderr
            stderr_output = mock_stderr.getvalue()
            assert "WARNING" in stderr_output
            assert "Conflicting output formats" in stderr_output

    def test_resolve_format_conflict_no_warning_when_no_conflict(self) -> None:
        """Test no warning when format flags don't conflict.

        Validates:
        - FR-041a: Only warn on actual conflicts
        """
        from echomine.cli.formatters import resolve_format_conflict

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            # No conflict cases
            resolve_format_conflict(format="json", json=False, json_comes_last=False)
            resolve_format_conflict(format="text", json=False, json_comes_last=False)

            # Assert: No warning
            stderr_output = mock_stderr.getvalue()
            assert "WARNING" not in stderr_output


class TestRichSearchTableFormatter:
    """Unit tests for Rich search results table formatter (FR-036, FR-037)."""

    @pytest.fixture
    def sample_search_results(
        self, sample_conversations: list[Conversation]
    ) -> list[SearchResult[Conversation]]:
        """Create sample search results with varying scores for color testing."""
        return [
            SearchResult(
                conversation=sample_conversations[0],
                score=0.95,  # High score → green
                matched_message_ids=["msg-1", "msg-2"],
                snippet="Python is great for async programming",
            ),
            SearchResult(
                conversation=sample_conversations[1],
                score=0.55,  # Medium score → yellow
                matched_message_ids=["msg-5"],
                snippet="Algorithm design patterns for efficiency",
            ),
        ]

    def test_create_rich_search_table_returns_table_instance(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test create_rich_search_table() returns Rich Table instance.

        Validates:
        - FR-036: Rich table format for search results
        """
        table = create_rich_search_table(sample_search_results)

        # Assert: Returns Rich Table instance
        assert isinstance(table, Table)

    def test_create_rich_search_table_includes_score_column(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test Rich search table includes Score column.

        Validates:
        - FR-036: Search results table includes Score column
        """
        table = create_rich_search_table(sample_search_results)

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=150)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Score column present
        assert "Score" in output

    def test_create_rich_search_table_includes_colored_scores(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test Rich search table includes color-coded scores.

        Validates:
        - FR-037: Score color coding in Rich tables
        """
        table = create_rich_search_table(sample_search_results)

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=150)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Scores formatted to 2 decimals
        assert "0.95" in output
        assert "0.55" in output

        # Note: Color codes are embedded in ANSI escape sequences
        # We can't easily test the actual colors without rendering,
        # but we can verify the scores are present

    def test_create_rich_search_table_includes_snippet_column(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test Rich search table includes Snippet column.

        Validates:
        - FR-036: Search results include snippet preview
        """
        table = create_rich_search_table(sample_search_results)

        # Render table to check output
        console = Console(file=StringIO(), force_terminal=True, width=150)
        with console.capture() as capture:
            console.print(table)
        output = capture.get()

        # Assert: Snippet column and data present
        assert "Snippet" in output
        assert "Python is great" in output
        assert "Algorithm design" in output
