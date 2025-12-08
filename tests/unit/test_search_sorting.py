"""Test SearchQuery model sorting fields and validation.

This module tests the sorting capabilities of the SearchQuery Pydantic model,
including field validation and helper methods.

Tasks: T099-T105 (TDD RED phase - tests DESIGNED TO FAIL)
Feature: 003-baseline-enhancements (US7 Sort Search Results)

Constitution Compliance:
    - Principle III: TDD (tests written FIRST, will fail initially)
    - Principle VI: Strict typing with mypy --strict compliance
    - FR-043-048: Sort functionality requirements
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from echomine.models.search import SearchQuery


class TestSearchQuerySortFields:
    """Test sorting fields in SearchQuery model (FR-048)."""

    def test_sort_by_field_exists_and_accepts_score(self) -> None:
        """T099: Test SearchQuery accepts sort_by field with 'score' value."""
        query = SearchQuery(sort_by="score")

        assert query.sort_by == "score"

    def test_sort_by_field_exists_and_accepts_date(self) -> None:
        """T099: Test SearchQuery accepts sort_by field with 'date' value."""
        query = SearchQuery(sort_by="date")

        assert query.sort_by == "date"

    def test_sort_by_field_exists_and_accepts_title(self) -> None:
        """T099: Test SearchQuery accepts sort_by field with 'title' value."""
        query = SearchQuery(sort_by="title")

        assert query.sort_by == "title"

    def test_sort_by_field_exists_and_accepts_messages(self) -> None:
        """T099: Test SearchQuery accepts sort_by field with 'messages' value."""
        query = SearchQuery(sort_by="messages")

        assert query.sort_by == "messages"

    def test_sort_by_default_is_score(self) -> None:
        """T101: Test SearchQuery sort_by defaults to 'score' (FR-045)."""
        query = SearchQuery()

        assert query.sort_by == "score"

    def test_sort_by_rejects_invalid_value(self) -> None:
        """T099: Test SearchQuery rejects invalid sort_by values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(sort_by="invalid")  # type: ignore

        # Verify error message mentions the constraint
        error_message = str(exc_info.value)
        assert "sort_by" in error_message.lower() or "input" in error_message.lower()

    def test_sort_order_field_exists_and_accepts_asc(self) -> None:
        """T100: Test SearchQuery accepts sort_order field with 'asc' value."""
        query = SearchQuery(sort_order="asc")

        assert query.sort_order == "asc"

    def test_sort_order_field_exists_and_accepts_desc(self) -> None:
        """T100: Test SearchQuery accepts sort_order field with 'desc' value."""
        query = SearchQuery(sort_order="desc")

        assert query.sort_order == "desc"

    def test_sort_order_default_is_desc(self) -> None:
        """T101: Test SearchQuery sort_order defaults to 'desc' (FR-045)."""
        query = SearchQuery()

        assert query.sort_order == "desc"

    def test_sort_order_rejects_invalid_value(self) -> None:
        """T100: Test SearchQuery rejects invalid sort_order values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(sort_order="invalid")  # type: ignore

        # Verify error message mentions the constraint
        error_message = str(exc_info.value)
        assert "sort_order" in error_message.lower() or "input" in error_message.lower()

    def test_default_sort_is_score_descending(self) -> None:
        """T101: Test default sort is by score descending (FR-045)."""
        query = SearchQuery()

        assert query.sort_by == "score"
        assert query.sort_order == "desc"

    def test_sort_by_and_sort_order_combined(self) -> None:
        """Test sort_by and sort_order work together."""
        query = SearchQuery(sort_by="date", sort_order="asc")

        assert query.sort_by == "date"
        assert query.sort_order == "asc"

    def test_sort_fields_combine_with_keywords(self) -> None:
        """Test sort fields can be combined with keyword search."""
        query = SearchQuery(keywords=["python"], sort_by="title", sort_order="asc")

        assert query.keywords == ["python"]
        assert query.sort_by == "title"
        assert query.sort_order == "asc"

    def test_sort_fields_combine_with_filters(self) -> None:
        """Test sort fields can be combined with other filters."""
        query = SearchQuery(
            title_filter="Project",
            min_messages=5,
            sort_by="messages",
            sort_order="desc",
        )

        assert query.title_filter == "Project"
        assert query.min_messages == 5
        assert query.sort_by == "messages"
        assert query.sort_order == "desc"


class TestSearchResultSorting:
    """Test sorting behavior for search results (FR-043, FR-047, FR-043a, FR-043b).

    These tests validate sorting implementation in OpenAIAdapter.search().
    """

    def test_title_sort_is_case_insensitive(self) -> None:
        """T102: Test title sort is case-insensitive (FR-047).

        This test validates the sorting implementation, not the model.
        It will be implemented in integration tests with actual conversations.
        """
        # This will be tested in integration tests with actual conversation data
        # Placeholder test to document FR-047 requirement

    def test_stable_sort_preserves_relative_order(self) -> None:
        """T103: Test stable sort preserves relative order (FR-043b).

        When multiple conversations have the same sort key, their relative
        order should be preserved (stable sort). Python's sort is stable by default.
        """
        # This will be tested in integration tests with actual conversation data
        # Placeholder test to document FR-043b requirement

    def test_null_updated_at_falls_back_to_created_at(self) -> None:
        """T104: Test NULL updated_at falls back to created_at (FR-046a).

        When sorting by date, conversations with NULL updated_at should use
        created_at for sorting.
        """
        # This will be tested in integration tests with actual conversation data
        # Placeholder test to document FR-046a requirement

    def test_tie_breaking_by_conversation_id(self) -> None:
        """T105: Test tie-breaking by conversation_id (FR-043a).

        When conversations have the same sort value, they should be sorted
        by conversation_id in ascending lexicographic order.
        """
        # This will be tested in integration tests with actual conversation data
        # Placeholder test to document FR-043a requirement
