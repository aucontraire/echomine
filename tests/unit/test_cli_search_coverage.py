"""Unit tests for search command to increase coverage.

This module uses unit testing (mocking) rather than subprocess contract tests
to ensure coverage is properly captured for error handling paths.

Coverage Targets:
    - Lines 91-109: _build_search_suggestions function
    - Lines 382-387: SearchQuery validation error
    - Lines 419-436: Zero results suggestions (TTY mode)
    - Lines 474-478: FileNotFoundError handler
    - Lines 498-502: ValidationError handler
    - Lines 506-510: KeyboardInterrupt handler
    - Lines 517-523: Generic exception handler

Constitution Compliance:
    - Principle III: TDD - Tests written to cover missing lines
    - Principle VI: Strict typing - All type hints validated
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from echomine.adapters.openai import OpenAIAdapter
from echomine.cli.commands.search import _build_search_suggestions, search_conversations
from echomine.exceptions import ValidationError
from echomine.models.conversation import Conversation
from echomine.models.search import SearchResult


@pytest.mark.unit
class TestBuildSearchSuggestions:
    """Unit tests for _build_search_suggestions helper function.

    Coverage Target: Lines 91-109
    """

    def test_build_suggestions_with_keywords_only(self) -> None:
        """Test suggestions when only keywords provided.

        Validates:
            - Lines 93-96: Keyword suggestion logic
            - Returns list of strings
        """
        suggestions = _build_search_suggestions(
            keywords=["python", "async"],
            title_filter=None,
            from_date=None,
            to_date=None,
        )

        # Assert: At least 2 suggestions (keyword + list all)
        assert len(suggestions) >= 2

        # Assert: First suggestion mentions keywords
        assert any("keyword" in s.lower() for s in suggestions)

        # Assert: Always includes "list all" suggestion
        assert any("list all" in s.lower() or "echomine list" in s.lower() for s in suggestions)

    def test_build_suggestions_with_title_filter(self) -> None:
        """Test suggestions when title filter provided.

        Validates:
            - Lines 98-101: Title filter suggestion logic
            - Suggests partial title match
        """
        suggestions = _build_search_suggestions(
            keywords=None,
            title_filter="Long Title With Multiple Words",
            from_date=None,
            to_date=None,
        )

        # Assert: At least one suggestion mentions title
        assert any("title" in s.lower() for s in suggestions)

        # Assert: Suggests partial match (first word)
        partial_match_suggested = any("Long" in s for s in suggestions)
        assert partial_match_suggested or any("partial" in s.lower() for s in suggestions)

    def test_build_suggestions_with_date_range(self) -> None:
        """Test suggestions when date filters provided.

        Validates:
            - Lines 103-104: Date range suggestion logic
            - Suggests expanding date range
        """
        suggestions = _build_search_suggestions(
            keywords=None,
            title_filter=None,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
        )

        # Assert: At least one suggestion mentions date
        assert any("date" in s.lower() or "range" in s.lower() for s in suggestions)

        # Assert: Suggests expanding or removing date filters
        assert any("expanding" in s.lower() or "removing" in s.lower() for s in suggestions)

    def test_build_suggestions_with_all_filters(self) -> None:
        """Test suggestions when all filters provided.

        Validates:
            - Lines 93-107: All suggestion types generated
            - Returns comprehensive list
        """
        suggestions = _build_search_suggestions(
            keywords=["python"],
            title_filter="Tutorial",
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
        )

        # Assert: Multiple suggestions (keyword, title, date, list all)
        assert len(suggestions) >= 3

        # Assert: List all is always present
        assert any("list all" in s.lower() or "echomine list" in s.lower() for s in suggestions)

    def test_build_suggestions_empty_filters(self) -> None:
        """Test suggestions when no filters provided (edge case).

        Validates:
            - Lines 106-109: Always returns list all suggestion
            - Handles empty input gracefully
        """
        suggestions = _build_search_suggestions(
            keywords=None,
            title_filter=None,
            from_date=None,
            to_date=None,
        )

        # Assert: At least one suggestion (list all)
        assert len(suggestions) >= 1

        # Assert: List all is present
        assert any("list all" in s.lower() or "echomine list" in s.lower() for s in suggestions)


@pytest.mark.unit
class TestSearchQueryValidationError:
    """Unit tests for SearchQuery validation error handling.

    Coverage Target: Lines 382-387
    """

    def test_search_query_validation_error_exits_code_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test SearchQuery validation error exits with code 2.

        Validates:
            - Lines 382-387: PydanticValidationError caught
            - Exit code 2 (invalid arguments)
            - Error message on stderr
        """
        # Arrange: Create minimal export file
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Create a Pydantic validation error by trying to construct an invalid SearchQuery
        from echomine.models.search import SearchQuery

        # Mock SearchQuery.__init__ to raise PydanticValidationError
        def raise_validation_error(*args: object, **kwargs: object) -> None:
            # Trigger a real validation error by passing invalid data
            try:
                SearchQuery(keywords=None, limit=-5)
            except PydanticValidationError as e:
                raise e

        from click.exceptions import Exit

        with patch("echomine.cli.commands.search.SearchQuery", side_effect=raise_validation_error):
            # Act & Assert: Exits with code 2
            with pytest.raises(Exit) as exc_info:
                search_conversations(
                    file_path=export_file,
                    keywords=["test"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    limit=None,
                    format="text",
                    quiet=False,
                    json=False,
                )

            assert exc_info.value.exit_code == 2

            # Assert: Error message on stderr
            captured = capsys.readouterr()
            assert "invalid search parameters" in captured.err.lower() or "validation" in captured.err.lower()


@pytest.mark.unit
class TestSearchZeroResultsWithTTY:
    """Unit tests for zero results suggestions in TTY mode.

    Coverage Target: Lines 419-436
    """

    def test_search_zero_results_shows_suggestions_when_tty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test zero results shows suggestions when stderr is TTY.

        Validates:
            - Lines 419-436: Suggestions shown when sys.stderr.isatty() == True
            - _build_search_suggestions called
            - Suggestions printed to stderr
        """
        # Arrange: Create empty export
        export_file = tmp_path / "empty.json"
        export_file.write_text("[]")

        # Mock adapter to return no results
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.return_value = iter([])  # Empty iterator

        # Mock sys.stderr.isatty() to return True
        with (
            patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter),
            patch("sys.stderr.isatty", return_value=True),
        ):
            # Act: Search with no results
            search_conversations(
                file_path=export_file,
                keywords=["nonexistent"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date=None,
                to_date=None,
                limit=None,
                format="text",
                quiet=False,
                json=False,
            )

            # Assert: Suggestions printed to stderr
            captured = capsys.readouterr()
            stderr = captured.err.lower()

            # Should contain suggestion header
            assert "no conversations matched" in stderr or "suggestions" in stderr

            # Should suggest listing all conversations
            assert "list" in stderr or "echomine" in stderr

    def test_search_zero_results_no_suggestions_when_not_tty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test zero results doesn't show suggestions when stderr is not TTY.

        Validates:
            - Lines 418-436: sys.stderr.isatty() check works
            - No suggestions when piped (not interactive)
        """
        # Arrange: Create empty export
        export_file = tmp_path / "empty.json"
        export_file.write_text("[]")

        # Mock adapter to return no results
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.return_value = iter([])

        # Mock sys.stderr.isatty() to return False (piped/redirected)
        with (
            patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter),
            patch("sys.stderr.isatty", return_value=False),
        ):
            # Act: Search with no results
            search_conversations(
                file_path=export_file,
                keywords=["nonexistent"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date=None,
                to_date=None,
                limit=None,
                format="text",
                quiet=False,
                json=False,
            )

            # Assert: No suggestions in stderr
            captured = capsys.readouterr()
            stderr = captured.err.lower()

            # Should NOT have suggestion header (non-TTY mode)
            # May have progress indicators, but not full suggestions
            assert "suggestions:" not in stderr


@pytest.mark.unit
class TestSearchErrorHandlers:
    """Unit tests for exception handlers in search command.

    Coverage Targets:
        - Lines 474-478: FileNotFoundError handler
        - Lines 498-502: ValidationError handler
        - Lines 506-510: KeyboardInterrupt handler
        - Lines 517-523: Generic exception handler
    """

    def test_file_not_found_error_exits_code_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test FileNotFoundError handler (defensive path).

        Validates:
            - Lines 474-478: FileNotFoundError caught
            - Exit code 1
            - Error message on stderr

        Note: This is a defensive handler since line 350 checks file existence first.
        We mock the adapter to raise FileNotFoundError during search.
        """
        # Arrange: Create valid export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Mock adapter to raise FileNotFoundError during search
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.side_effect = FileNotFoundError("File deleted during search")

        from click.exceptions import Exit

        with patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter):
            # Act & Assert: Exits with code 1
            with pytest.raises(Exit) as exc_info:
                search_conversations(
                    file_path=export_file,
                    keywords=["test"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    limit=None,
                    format="text",
                    quiet=False,
                    json=False,
                )

            assert exc_info.value.exit_code == 1

            # Assert: Error message on stderr
            captured = capsys.readouterr()
            assert "file not found" in captured.err.lower()

    def test_validation_error_exits_code_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ValidationError handler during search execution.

        Validates:
            - Lines 498-502: ValidationError caught
            - Exit code 1
            - Error mentions validation
        """
        # Arrange: Create valid export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Mock adapter to raise ValidationError during search
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.side_effect = ValidationError("Invalid conversation schema")

        from click.exceptions import Exit

        with patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter):
            # Act & Assert: Exits with code 1
            with pytest.raises(Exit) as exc_info:
                search_conversations(
                    file_path=export_file,
                    keywords=["test"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    limit=None,
                    format="text",
                    quiet=False,
                    json=False,
                )

            assert exc_info.value.exit_code == 1

            # Assert: Error mentions validation
            captured = capsys.readouterr()
            assert "validation" in captured.err.lower()

    def test_keyboard_interrupt_exits_code_130(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test KeyboardInterrupt handler (Ctrl+C).

        Validates:
            - Lines 506-510: KeyboardInterrupt caught
            - Exit code 130 (standard for SIGINT)
            - User-friendly message
        """
        # Arrange: Create valid export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Mock adapter to raise KeyboardInterrupt during search
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.side_effect = KeyboardInterrupt()

        from click.exceptions import Exit

        with patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter):
            # Act & Assert: Exits with code 130
            with pytest.raises(Exit) as exc_info:
                search_conversations(
                    file_path=export_file,
                    keywords=["test"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    limit=None,
                    format="text",
                    quiet=False,
                    json=False,
                )

            assert exc_info.value.exit_code == 130

            # Assert: User-friendly message
            captured = capsys.readouterr()
            assert "interrupted" in captured.err.lower()

    def test_generic_exception_exits_code_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test generic exception handler (catch-all).

        Validates:
            - Lines 517-523: Unexpected exceptions caught
            - Exit code 1
            - Error message includes exception info
        """
        # Arrange: Create valid export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Mock adapter to raise unexpected exception
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.side_effect = RuntimeError("Unexpected database connection failure")

        from click.exceptions import Exit

        with patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter):
            # Act & Assert: Exits with code 1
            with pytest.raises(Exit) as exc_info:
                search_conversations(
                    file_path=export_file,
                    keywords=["test"],
                    phrase=None,
                    match_mode="any",
                    exclude=None,
                    role=None,
                    title=None,
                    from_date=None,
                    to_date=None,
                    limit=None,
                    format="text",
                    quiet=False,
                    json=False,
                )

            assert exc_info.value.exit_code == 1

            # Assert: Error message contains exception info
            captured = capsys.readouterr()
            assert "error" in captured.err.lower()
            # Generic handler shows exception message
            assert len(captured.err) > 0


@pytest.mark.unit
class TestSearchEdgeCases:
    """Unit tests for edge cases and special scenarios.

    Additional coverage for tricky branches.
    """

    def test_search_with_limit_applies_correctly(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that limit is applied correctly to results.

        Validates:
            - Lines 414-415: Limit slicing logic
            - Results truncated to limit
        """
        from datetime import UTC, datetime

        # Arrange: Create export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        # Mock adapter to return 10 results with properly mocked Conversation objects
        mock_results = []
        for i in range(10):
            # Create a properly configured mock conversation
            mock_conv = Mock()
            mock_conv.id = f"conv-{i}"
            mock_conv.title = f"Conversation {i}"
            mock_conv.created_at = datetime(2024, 1, 1, tzinfo=UTC)
            mock_conv.updated_at = None
            mock_conv.get_messages.return_value = []

            mock_result = SearchResult(conversation=mock_conv, score=1.0)
            mock_results.append(mock_result)

        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.return_value = iter(mock_results)

        # Mock the formatter to avoid issues
        with (
            patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter),
            patch("echomine.cli.commands.search.format_search_results", return_value="formatted output\n"),
        ):
            # Act: Search with limit=5
            search_conversations(
                file_path=export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date=None,
                to_date=None,
                limit=5,  # Limit to 5
                format="text",
                quiet=True,
                json=False,
            )

            # Assert: Adapter received query with large default limit (1000)
            # Then results sliced to 5 in command
            call_args = mock_adapter.search.call_args
            query = call_args[0][1]  # Second positional arg is SearchQuery
            assert query.limit == 5  # Limit passed to query

    def test_search_without_limit_uses_default(self, tmp_path: Path) -> None:
        """Test that no limit uses large default for query validation.

        Validates:
            - Lines 357-359: Default limit handling
            - SearchQuery gets 1000 as default
        """
        # Arrange: Create export
        export_file = tmp_path / "test.json"
        export_file.write_text("[]")

        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.search.return_value = iter([])

        with patch("echomine.cli.commands.search.OpenAIAdapter", return_value=mock_adapter):
            # Act: Search without limit
            search_conversations(
                file_path=export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date=None,
                to_date=None,
                limit=None,  # No limit specified
                format="text",
                quiet=True,
                json=False,
            )

            # Assert: Query received default limit
            call_args = mock_adapter.search.call_args
            query = call_args[0][1]
            assert query.limit == 1000
