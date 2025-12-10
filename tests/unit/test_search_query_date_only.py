"""Unit tests for SearchQuery with date-only filtering (FR-009).

Task: US4-AS1/AS4/AS5 - SearchQuery Model Date-Only Support
Phase: RED (tests designed to FAIL or PASS depending on model state)

This module validates that the SearchQuery Pydantic model supports
date-only queries without requiring keywords or title_filter.

Current State:
    SearchQuery already has Optional[list[str]] keywords and Optional[str] title_filter,
    so these tests should PASS. The issue is in CLI validation (search.py lines 248-254),
    not the model.

Test Purpose:
    - Verify SearchQuery model supports date-only queries (SHOULD PASS)
    - Document expected model behavior for date-only filtering
    - Provide unit-level validation before fixing CLI layer

Constitution Compliance:
    - Principle III: TDD - Test model behavior
    - Principle VI: Strict typing - mypy --strict compliant tests
    - Principle I: Library-first - Model is library layer, testable independently
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from echomine.models.search import SearchQuery


class TestSearchQueryDateOnlySupport:
    """Test SearchQuery model supports date-only queries.

    These tests validate the Pydantic model layer, NOT the CLI layer.
    The model should allow date-only queries (no keywords or title).
    """

    def test_search_query_date_range_only_is_valid(self) -> None:
        """Test SearchQuery with only from_date and to_date (no keywords/title).

        Validates:
        - FR-009: Model supports date-only queries
        - keywords and title_filter are Optional
        - Model validation succeeds

        Expected: SHOULD PASS (model already supports this)
        """
        # Act: Create query with date range only
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
        )

        # Assert: Model accepts date-only query
        assert query.keywords is None, "keywords should be None when not specified"
        assert query.title_filter is None, "title_filter should be None when not specified"
        assert query.from_date == date(2024, 1, 1)
        assert query.to_date == date(2024, 12, 31)

        # Assert: Helper methods work correctly
        assert query.has_keyword_search() is False, "No keyword search"
        assert query.has_title_filter() is False, "No title filter"
        assert query.has_date_filter() is True, "Has date filter"

    def test_search_query_from_date_only_is_valid(self) -> None:
        """Test SearchQuery with only from_date (no keywords/title/to_date).

        Validates:
        - FR-009: Model supports from_date-only queries
        - US4-AS4: from_date alone is valid

        Expected: SHOULD PASS
        """
        # Act: Create query with from_date only
        query = SearchQuery(from_date=date(2024, 6, 1))

        # Assert: Model accepts from_date-only query
        assert query.keywords is None
        assert query.title_filter is None
        assert query.from_date == date(2024, 6, 1)
        assert query.to_date is None

        # Assert: Helper methods
        assert query.has_keyword_search() is False
        assert query.has_title_filter() is False
        assert query.has_date_filter() is True

    def test_search_query_to_date_only_is_valid(self) -> None:
        """Test SearchQuery with only to_date (no keywords/title/from_date).

        Validates:
        - FR-009: Model supports to_date-only queries
        - US4-AS5: to_date alone is valid

        Expected: SHOULD PASS
        """
        # Act: Create query with to_date only
        query = SearchQuery(to_date=date(2024, 6, 30))

        # Assert: Model accepts to_date-only query
        assert query.keywords is None
        assert query.title_filter is None
        assert query.from_date is None
        assert query.to_date == date(2024, 6, 30)

        # Assert: Helper methods
        assert query.has_keyword_search() is False
        assert query.has_title_filter() is False
        assert query.has_date_filter() is True

    def test_search_query_empty_valid_but_useless(self) -> None:
        """Test SearchQuery with no filters at all is valid (model layer).

        Note:
        - Model layer: Allows empty query (valid Pydantic model)
        - CLI layer: Should reject empty query (exit code 2)

        Validates:
        - Library-first design: Model doesn't enforce CLI semantics
        - CLI validation is separate concern

        Expected: SHOULD PASS (model allows it, CLI validates it)
        """
        # Act: Create completely empty query
        query = SearchQuery()

        # Assert: Model accepts empty query
        assert query.keywords is None
        assert query.title_filter is None
        assert query.from_date is None
        assert query.to_date is None

        # Assert: All helper methods return False
        assert query.has_keyword_search() is False
        assert query.has_title_filter() is False
        assert query.has_date_filter() is False

        # Note: This is valid at model layer, but CLI should reject with exit code 2

    def test_search_query_immutability_preserved_with_date_only(self) -> None:
        """Test SearchQuery immutability works with date-only queries.

        Validates:
        - FR-224, FR-227: Immutability via frozen=True
        - Date-only queries are immutable

        Expected: SHOULD PASS
        """
        # Arrange
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
        )

        # Act & Assert: Attempt to modify frozen field
        with pytest.raises(ValidationError, match="Instance is frozen"):
            query.from_date = date(2025, 1, 1)

    def test_search_query_model_copy_with_date_only(self) -> None:
        """Test model_copy works with date-only queries.

        Validates:
        - Immutable model can be copied with modifications
        - Date-only queries support model_copy

        Expected: SHOULD PASS
        """
        # Arrange
        original = SearchQuery(from_date=date(2024, 1, 1))

        # Act: Copy with modification
        modified = original.model_copy(update={"to_date": date(2024, 12, 31)})

        # Assert: Original unchanged
        assert original.from_date == date(2024, 1, 1)
        assert original.to_date is None

        # Assert: Modified has new values
        assert modified.from_date == date(2024, 1, 1)
        assert modified.to_date == date(2024, 12, 31)

    def test_search_query_date_only_with_limit(self) -> None:
        """Test date-only query with custom limit.

        Validates:
        - FR-009: Date-only queries work with limit
        - FR-336: Limit parameter works independently

        Expected: SHOULD PASS
        """
        # Act: Create date-only query with limit
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            limit=50,
        )

        # Assert: All fields correct
        assert query.from_date == date(2024, 1, 1)
        assert query.to_date is None
        assert query.keywords is None
        assert query.title_filter is None
        assert query.limit == 50

    def test_search_query_date_only_with_default_limit(self) -> None:
        """Test date-only query uses default limit when not specified.

        Validates:
        - FR-332: Default limit is 10
        - Date-only queries get default limit

        Expected: SHOULD PASS
        """
        # Act: Create date-only query without specifying limit
        query = SearchQuery(from_date=date(2024, 1, 1))

        # Assert: Default limit applied
        assert query.limit == 10, "Default limit should be 10 (FR-332)"


class TestSearchQueryValidationEdgeCases:
    """Test SearchQuery validation edge cases with date-only queries."""

    def test_search_query_date_only_with_empty_keywords_list(self) -> None:
        """Test date-only query with empty keywords list (not None).

        Validates:
        - Empty list is different from None
        - has_keyword_search() returns False for empty list

        Expected: SHOULD PASS (existing behavior)
        """
        # Act: Create query with empty keywords list
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            keywords=[],  # Empty list (not None)
        )

        # Assert: keywords is empty list (not None)
        assert query.keywords == []
        assert query.keywords is not None

        # Assert: Helper method treats empty list as "no search"
        assert query.has_keyword_search() is False, "Empty keywords list = no search"

    def test_search_query_date_only_with_empty_title_string(self) -> None:
        """Test date-only query with empty title string.

        Validates:
        - Empty string is different from None
        - has_title_filter() returns False for empty/whitespace string

        Expected: SHOULD PASS (existing behavior)
        """
        # Act: Create query with empty title string
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            title_filter="   ",  # Whitespace only
        )

        # Assert: title_filter is whitespace string (not None)
        assert query.title_filter == "   "
        assert query.title_filter is not None

        # Assert: Helper method treats whitespace as "no filter"
        assert query.has_title_filter() is False, "Whitespace title_filter = no filter"

    def test_search_query_date_only_with_invalid_limit(self) -> None:
        """Test date-only query with invalid limit raises ValidationError.

        Validates:
        - FR-332: Limit must be 1-1000
        - Date-only queries don't bypass limit validation

        Expected: SHOULD PASS (existing validation)
        """
        # Act & Assert: Limit too low
        with pytest.raises(ValidationError, match="greater than 0"):
            SearchQuery(
                from_date=date(2024, 1, 1),
                limit=0,  # Invalid: must be > 0
            )

        # Act & Assert: Limit too high
        with pytest.raises(ValidationError, match="less than or equal to 1000"):
            SearchQuery(
                from_date=date(2024, 1, 1),
                limit=1001,  # Invalid: must be <= 1000
            )


class TestSearchQueryHelperMethodsWithDateOnly:
    """Test SearchQuery helper methods work correctly with date-only queries."""

    def test_has_date_filter_true_with_from_date_only(self) -> None:
        """Test has_date_filter() returns True when only from_date set."""
        query = SearchQuery(from_date=date(2024, 1, 1))
        assert query.has_date_filter() is True

    def test_has_date_filter_true_with_to_date_only(self) -> None:
        """Test has_date_filter() returns True when only to_date set."""
        query = SearchQuery(to_date=date(2024, 12, 31))
        assert query.has_date_filter() is True

    def test_has_date_filter_true_with_both_dates(self) -> None:
        """Test has_date_filter() returns True when both dates set."""
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31),
        )
        assert query.has_date_filter() is True

    def test_has_date_filter_false_when_no_dates(self) -> None:
        """Test has_date_filter() returns False when no dates set."""
        query = SearchQuery()
        assert query.has_date_filter() is False

    def test_has_keyword_search_false_with_date_only(self) -> None:
        """Test has_keyword_search() returns False for date-only queries."""
        query = SearchQuery(from_date=date(2024, 1, 1))
        assert query.has_keyword_search() is False

    def test_has_title_filter_false_with_date_only(self) -> None:
        """Test has_title_filter() returns False for date-only queries."""
        query = SearchQuery(from_date=date(2024, 1, 1))
        assert query.has_title_filter() is False
