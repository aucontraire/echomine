"""Test SearchQuery model date filtering fields and validation.

This module tests the date range filtering capabilities of the SearchQuery
Pydantic model, including field validation and helper methods.

Constitution Compliance:
    - Principle III: TDD (tests for existing implementation)
    - Principle VI: Strict typing with mypy --strict compliance
"""

from __future__ import annotations

from datetime import date

import pytest

from echomine.models.search import SearchQuery


class TestSearchQueryDateFields:
    """Test date range filtering fields in SearchQuery model."""

    def test_from_date_only(self) -> None:
        """Test SearchQuery with only from_date specified."""
        query = SearchQuery(from_date=date(2024, 1, 1))
        
        assert query.from_date == date(2024, 1, 1)
        assert query.to_date is None
        assert query.has_date_filter() is True

    def test_to_date_only(self) -> None:
        """Test SearchQuery with only to_date specified."""
        query = SearchQuery(to_date=date(2024, 12, 31))
        
        assert query.from_date is None
        assert query.to_date == date(2024, 12, 31)
        assert query.has_date_filter() is True

    def test_both_dates_valid_range(self) -> None:
        """Test SearchQuery with valid date range (from <= to)."""
        query = SearchQuery(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31)
        )
        
        assert query.from_date == date(2024, 1, 1)
        assert query.to_date == date(2024, 12, 31)
        assert query.has_date_filter() is True

    def test_same_from_and_to_date(self) -> None:
        """Test SearchQuery with same from_date and to_date (single day)."""
        query = SearchQuery(
            from_date=date(2024, 6, 15),
            to_date=date(2024, 6, 15)
        )
        
        assert query.from_date == query.to_date
        assert query.has_date_filter() is True

    def test_no_date_filter(self) -> None:
        """Test SearchQuery with no date filters."""
        query = SearchQuery()
        
        assert query.from_date is None
        assert query.to_date is None
        assert query.has_date_filter() is False

    def test_leap_year_date(self) -> None:
        """Test SearchQuery with leap year date (Feb 29)."""
        query = SearchQuery(from_date=date(2024, 2, 29))
        
        assert query.from_date == date(2024, 2, 29)
        assert query.has_date_filter() is True

    def test_inverted_date_range_allowed_in_model(self) -> None:
        """Test SearchQuery allows from_date > to_date (CLI validates).
        
        The library-first design means the model doesn't enforce CLI semantics.
        Validation of from_date <= to_date happens in the CLI layer.
        """
        query = SearchQuery(
            from_date=date(2024, 12, 31),
            to_date=date(2024, 1, 1)
        )
        
        # Model accepts invalid range (no validation here)
        assert query.from_date > query.to_date
        assert query.has_date_filter() is True
