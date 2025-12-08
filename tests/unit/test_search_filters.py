"""Test SearchQuery model message count filtering fields and validation.

This module tests the message count filtering capabilities of the SearchQuery
Pydantic model, including field validation and helper methods.

Tasks: T016-T021 (TDD RED phase - tests DESIGNED TO FAIL)
Feature: 003-baseline-enhancements (US9 Library-First Message Count Filtering)

Constitution Compliance:
    - Principle III: TDD (tests for existing implementation)
    - Principle VI: Strict typing with mypy --strict compliance
    - FR-004-008: Message count filtering requirements
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from echomine.models.search import SearchQuery


class TestSearchQueryMessageCountFields:
    """Test message count filtering fields in SearchQuery model (FR-004)."""

    def test_min_messages_field_exists_and_accepts_valid_value(self) -> None:
        """T016: Test SearchQuery accepts min_messages field with valid value."""
        query = SearchQuery(min_messages=10)

        assert query.min_messages == 10
        assert query.has_message_count_filter() is True

    def test_min_messages_default_is_none(self) -> None:
        """T016: Test SearchQuery min_messages defaults to None."""
        query = SearchQuery()

        assert query.min_messages is None
        assert query.has_message_count_filter() is False

    def test_max_messages_field_exists_and_accepts_valid_value(self) -> None:
        """T017: Test SearchQuery accepts max_messages field with valid value."""
        query = SearchQuery(max_messages=100)

        assert query.max_messages == 100
        assert query.has_message_count_filter() is True

    def test_max_messages_default_is_none(self) -> None:
        """T017: Test SearchQuery max_messages defaults to None."""
        query = SearchQuery()

        assert query.max_messages is None
        assert query.has_message_count_filter() is False

    def test_both_min_and_max_messages_valid_range(self) -> None:
        """Test SearchQuery with valid message count range (min <= max)."""
        query = SearchQuery(min_messages=5, max_messages=20)

        assert query.min_messages == 5
        assert query.max_messages == 20
        assert query.has_message_count_filter() is True

    def test_validation_rejects_min_greater_than_max(self) -> None:
        """T018: Test validation rejects min_messages > max_messages (FR-005)."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(min_messages=20, max_messages=5)

        # Verify error message mentions the constraint
        error_message = str(exc_info.value)
        assert "min_messages" in error_message.lower()
        assert "max_messages" in error_message.lower()

    def test_validation_rejects_min_messages_less_than_1(self) -> None:
        """T019: Test validation rejects min_messages < 1 (FR-005)."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(min_messages=0)

        # Verify error includes constraint (ge=1)
        error_message = str(exc_info.value)
        assert (
            "greater than or equal to 1" in error_message.lower() or "ge=1" in error_message.lower()
        )

    def test_validation_rejects_max_messages_less_than_1(self) -> None:
        """T019: Test validation rejects max_messages < 1 (FR-005)."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(max_messages=0)

        # Verify error includes constraint (ge=1)
        error_message = str(exc_info.value)
        assert (
            "greater than or equal to 1" in error_message.lower() or "ge=1" in error_message.lower()
        )

    def test_validation_rejects_negative_min_messages(self) -> None:
        """T019: Test validation rejects negative min_messages."""
        with pytest.raises(ValidationError):
            SearchQuery(min_messages=-5)

    def test_validation_rejects_negative_max_messages(self) -> None:
        """T019: Test validation rejects negative max_messages."""
        with pytest.raises(ValidationError):
            SearchQuery(max_messages=-10)

    def test_edge_case_min_1_max_1_returns_exact_match(self) -> None:
        """T020: TDD Edge Case - min=1, max=1 should return conversations with exactly 1 message."""
        query = SearchQuery(min_messages=1, max_messages=1)

        assert query.min_messages == 1
        assert query.max_messages == 1
        assert query.has_message_count_filter() is True

    def test_edge_case_min_equals_max_valid(self) -> None:
        """T021: TDD Edge Case - min_messages == max_messages is valid (exact count)."""
        query = SearchQuery(min_messages=10, max_messages=10)

        assert query.min_messages == 10
        assert query.max_messages == 10
        assert query.has_message_count_filter() is True

    def test_has_message_count_filter_true_when_min_set(self) -> None:
        """Test has_message_count_filter() returns True when only min_messages set."""
        query = SearchQuery(min_messages=5)

        assert query.has_message_count_filter() is True

    def test_has_message_count_filter_true_when_max_set(self) -> None:
        """Test has_message_count_filter() returns True when only max_messages set."""
        query = SearchQuery(max_messages=50)

        assert query.has_message_count_filter() is True

    def test_has_message_count_filter_false_when_neither_set(self) -> None:
        """Test has_message_count_filter() returns False when no message count filters."""
        query = SearchQuery()

        assert query.has_message_count_filter() is False

    def test_min_messages_only_allows_open_ended_upper_bound(self) -> None:
        """Test min_messages without max_messages creates open-ended filter."""
        query = SearchQuery(min_messages=10)

        assert query.min_messages == 10
        assert query.max_messages is None
        assert query.has_message_count_filter() is True

    def test_max_messages_only_allows_open_ended_lower_bound(self) -> None:
        """Test max_messages without min_messages creates open-ended filter."""
        query = SearchQuery(max_messages=5)

        assert query.min_messages is None
        assert query.max_messages == 5
        assert query.has_message_count_filter() is True

    def test_message_count_filters_combine_with_keywords(self) -> None:
        """Test message count filters can be combined with keyword search."""
        query = SearchQuery(keywords=["python"], min_messages=10, max_messages=50)

        assert query.keywords == ["python"]
        assert query.min_messages == 10
        assert query.max_messages == 50
        assert query.has_keyword_search() is True
        assert query.has_message_count_filter() is True

    def test_message_count_filters_combine_with_title_filter(self) -> None:
        """Test message count filters can be combined with title filter."""
        query = SearchQuery(title_filter="Project", min_messages=5)

        assert query.title_filter == "Project"
        assert query.min_messages == 5
        assert query.has_title_filter() is True
        assert query.has_message_count_filter() is True
