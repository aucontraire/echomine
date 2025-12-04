"""Unit tests for SearchQuery and SearchResult advanced search fields.

Tests for v1.1.0 advanced search features:
- FR-005: SearchQuery.phrases field
- FR-011: SearchQuery.match_mode field
- FR-016: SearchQuery.exclude_keywords field
- FR-020: SearchQuery.role_filter field
- FR-024: SearchResult.snippet field

TDD: These tests are written FIRST to validate model extensions.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from echomine.models.search import SearchQuery, SearchResult


class TestSearchQueryPhrases:
    """Tests for SearchQuery.phrases field (FR-005)."""

    def test_phrases_optional_default_none(self) -> None:
        """Phrases field defaults to None (backward compatibility)."""
        query = SearchQuery(keywords=["python"])
        assert query.phrases is None

    def test_phrases_accepts_list(self) -> None:
        """Phrases field accepts a list of strings."""
        query = SearchQuery(phrases=["algo-insights", "data pipeline"])
        assert query.phrases == ["algo-insights", "data pipeline"]

    def test_phrases_empty_list(self) -> None:
        """Phrases field accepts empty list."""
        query = SearchQuery(phrases=[])
        assert query.phrases == []

    def test_has_phrase_search_true(self) -> None:
        """has_phrase_search() returns True when phrases provided."""
        query = SearchQuery(phrases=["algo-insights"])
        assert query.has_phrase_search() is True

    def test_has_phrase_search_false_none(self) -> None:
        """has_phrase_search() returns False when phrases is None."""
        query = SearchQuery(keywords=["python"])
        assert query.has_phrase_search() is False

    def test_has_phrase_search_false_empty(self) -> None:
        """has_phrase_search() returns False when phrases is empty list."""
        query = SearchQuery(phrases=[])
        assert query.has_phrase_search() is False

    def test_phrases_with_special_characters(self) -> None:
        """Phrases can contain special characters."""
        query = SearchQuery(phrases=["algo-insights", "data_pipeline", "v1.0.0"])
        assert query.phrases == ["algo-insights", "data_pipeline", "v1.0.0"]

    def test_phrases_combined_with_keywords(self) -> None:
        """Phrases can be combined with keywords (FR-004)."""
        query = SearchQuery(keywords=["python"], phrases=["algo-insights"])
        assert query.keywords == ["python"]
        assert query.phrases == ["algo-insights"]
        assert query.has_keyword_search() is True
        assert query.has_phrase_search() is True


class TestSearchQueryMatchMode:
    """Tests for SearchQuery.match_mode field (FR-011)."""

    def test_match_mode_default_any(self) -> None:
        """Match mode defaults to 'any' (backward compatibility, FR-008)."""
        query = SearchQuery(keywords=["python"])
        assert query.match_mode == "any"

    def test_match_mode_accepts_all(self) -> None:
        """Match mode accepts 'all' value."""
        query = SearchQuery(keywords=["python"], match_mode="all")
        assert query.match_mode == "all"

    def test_match_mode_accepts_any(self) -> None:
        """Match mode accepts 'any' value explicitly."""
        query = SearchQuery(keywords=["python"], match_mode="any")
        assert query.match_mode == "any"

    def test_match_mode_invalid_raises(self) -> None:
        """Match mode rejects invalid values."""
        with pytest.raises(ValidationError):
            SearchQuery(keywords=["python"], match_mode="invalid")  # type: ignore[arg-type]

    def test_match_mode_literal_type(self) -> None:
        """Match mode is Literal['all', 'any']."""
        query = SearchQuery(keywords=["python"], match_mode="all")
        # This should type-check correctly
        mode: str = query.match_mode
        assert mode in ("all", "any")


class TestSearchQueryExcludeKeywords:
    """Tests for SearchQuery.exclude_keywords field (FR-016)."""

    def test_exclude_keywords_default_none(self) -> None:
        """Exclude keywords defaults to None."""
        query = SearchQuery(keywords=["python"])
        assert query.exclude_keywords is None

    def test_exclude_keywords_accepts_list(self) -> None:
        """Exclude keywords accepts a list of strings."""
        query = SearchQuery(keywords=["python"], exclude_keywords=["django", "flask"])
        assert query.exclude_keywords == ["django", "flask"]

    def test_exclude_keywords_empty_list(self) -> None:
        """Exclude keywords accepts empty list."""
        query = SearchQuery(keywords=["python"], exclude_keywords=[])
        assert query.exclude_keywords == []

    def test_exclude_keywords_single_item(self) -> None:
        """Exclude keywords works with single item."""
        query = SearchQuery(keywords=["python"], exclude_keywords=["django"])
        assert query.exclude_keywords == ["django"]


class TestSearchQueryRoleFilter:
    """Tests for SearchQuery.role_filter field (FR-020)."""

    def test_role_filter_default_none(self) -> None:
        """Role filter defaults to None (all roles, FR-019)."""
        query = SearchQuery(keywords=["python"])
        assert query.role_filter is None

    def test_role_filter_accepts_user(self) -> None:
        """Role filter accepts 'user' value."""
        query = SearchQuery(keywords=["python"], role_filter="user")
        assert query.role_filter == "user"

    def test_role_filter_accepts_assistant(self) -> None:
        """Role filter accepts 'assistant' value."""
        query = SearchQuery(keywords=["python"], role_filter="assistant")
        assert query.role_filter == "assistant"

    def test_role_filter_accepts_system(self) -> None:
        """Role filter accepts 'system' value."""
        query = SearchQuery(keywords=["python"], role_filter="system")
        assert query.role_filter == "system"

    def test_role_filter_invalid_raises(self) -> None:
        """Role filter rejects invalid values."""
        with pytest.raises(ValidationError):
            SearchQuery(keywords=["python"], role_filter="invalid")  # type: ignore[arg-type]

    def test_role_filter_literal_type(self) -> None:
        """Role filter is Literal['user', 'assistant', 'system'] | None."""
        query = SearchQuery(keywords=["python"], role_filter="user")
        # This should type-check correctly
        role: str | None = query.role_filter
        assert role in ("user", "assistant", "system", None)


class TestSearchResultSnippet:
    """Tests for SearchResult.snippet field (FR-024)."""

    def test_snippet_default_none(self) -> None:
        """Snippet defaults to None (backward compatibility)."""
        # Create a minimal conversation-like object for testing
        conv: dict[str, Any] = {"id": "test", "title": "Test"}
        result = SearchResult[dict[str, Any]](
            conversation=conv,
            score=0.5,
            matched_message_ids=[],
        )
        assert result.snippet is None

    def test_snippet_accepts_string(self) -> None:
        """Snippet accepts a string value."""
        conv: dict[str, Any] = {"id": "test", "title": "Test"}
        result = SearchResult[dict[str, Any]](
            conversation=conv,
            score=0.5,
            matched_message_ids=["msg-1"],
            snippet="This is a test snippet...",
        )
        assert result.snippet == "This is a test snippet..."

    def test_snippet_with_truncation_indicator(self) -> None:
        """Snippet can include truncation indicator."""
        conv: dict[str, Any] = {"id": "test", "title": "Test"}
        result = SearchResult[dict[str, Any]](
            conversation=conv,
            score=0.5,
            matched_message_ids=["msg-1", "msg-2", "msg-3"],
            snippet="First matched message content... (+2 more matches)",
        )
        assert "+2 more matches" in (result.snippet or "")

    def test_snippet_content_unavailable_fallback(self) -> None:
        """Snippet can use fallback text for malformed content."""
        conv: dict[str, Any] = {"id": "test", "title": "Test"}
        result = SearchResult[dict[str, Any]](
            conversation=conv,
            score=0.5,
            matched_message_ids=["msg-1"],
            snippet="[Content unavailable]",
        )
        assert result.snippet == "[Content unavailable]"


class TestSearchQueryBackwardCompatibility:
    """Test that existing SearchQuery usage continues to work (FR-028)."""

    def test_existing_query_unchanged(self) -> None:
        """Existing query patterns work without modification."""
        # v1.0.x style query
        query = SearchQuery(keywords=["python"], limit=10)

        assert query.keywords == ["python"]
        assert query.limit == 10
        # New fields have sensible defaults
        assert query.phrases is None
        assert query.match_mode == "any"
        assert query.exclude_keywords is None
        assert query.role_filter is None

    def test_query_with_all_filters(self) -> None:
        """Query with all new fields works correctly."""
        from datetime import date

        query = SearchQuery(
            keywords=["python", "async"],
            phrases=["algo-insights"],
            match_mode="all",
            exclude_keywords=["django"],
            role_filter="user",
            title_filter="Project",
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
            limit=5,
        )

        assert query.keywords == ["python", "async"]
        assert query.phrases == ["algo-insights"]
        assert query.match_mode == "all"
        assert query.exclude_keywords == ["django"]
        assert query.role_filter == "user"
        assert query.title_filter == "Project"
        assert query.from_date == date(2024, 1, 1)
        assert query.to_date == date(2024, 12, 31)
        assert query.limit == 5
