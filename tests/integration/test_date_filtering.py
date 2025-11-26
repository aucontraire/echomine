"""Integration tests for date range filtering in OpenAIAdapter.search().

This module tests end-to-end date filtering with real fixtures to ensure
the date range logic works correctly across the full stack.

Constitution Compliance:
    - Principle III: TDD (tests for existing implementation)
    - Principle VIII: Memory efficiency (streaming with O(1) memory)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def date_test_fixture() -> Path:
    """Path to date test fixture with strategic dates."""
    return Path(__file__).parent.parent / "fixtures" / "date_test_conversations.json"


class TestDateFilteringIntegration:
    """Test date range filtering end-to-end with OpenAIAdapter."""

    def test_from_date_only_filters_correctly(self, date_test_fixture: Path) -> None:
        """Test from_date filters conversations >= from_date (inclusive)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(from_date=date(2024, 2, 1))
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Should include: 2024-02-29, 2024-03-01, 2024-12-31
        # Should exclude: 2024-01-15, 2023-06-15
        assert len(results) == 3
        
        for result in results:
            conv_date = result.conversation.created_at.date()
            assert conv_date >= date(2024, 2, 1)

    def test_to_date_only_filters_correctly(self, date_test_fixture: Path) -> None:
        """Test to_date filters conversations <= to_date (inclusive)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(to_date=date(2024, 3, 1))
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Should include: 2024-01-15, 2024-02-29, 2024-03-01, 2023-06-15
        # Should exclude: 2024-12-31
        assert len(results) == 4
        
        for result in results:
            conv_date = result.conversation.created_at.date()
            assert conv_date <= date(2024, 3, 1)

    def test_date_range_both_filters(self, date_test_fixture: Path) -> None:
        """Test from_date and to_date together (range filter)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            from_date=date(2024, 2, 1),
            to_date=date(2024, 3, 31)
        )
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Should include: 2024-02-29, 2024-03-01
        # Should exclude: 2024-01-15, 2024-12-31, 2023-06-15
        assert len(results) == 2
        
        for result in results:
            conv_date = result.conversation.created_at.date()
            assert date(2024, 2, 1) <= conv_date <= date(2024, 3, 31)

    def test_single_day_filter(self, date_test_fixture: Path) -> None:
        """Test same from_date and to_date returns conversations on that day."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            from_date=date(2024, 2, 29),
            to_date=date(2024, 2, 29)
        )
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Should include only: 2024-02-29 (leap day)
        assert len(results) == 1
        assert results[0].conversation.created_at.date() == date(2024, 2, 29)

    def test_no_matches_in_date_range(self, date_test_fixture: Path) -> None:
        """Test date range with no matching conversations returns empty."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            from_date=date(2025, 1, 1),
            to_date=date(2025, 12, 31)
        )
        
        results = list(adapter.search(date_test_fixture, query))
        
        assert len(results) == 0

    def test_boundary_inclusive_from_date(self, date_test_fixture: Path) -> None:
        """Test from_date boundary is inclusive (conversations ON from_date included)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(from_date=date(2024, 2, 29))
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Leap day conversation should be included (boundary is inclusive)
        conv_dates = [r.conversation.created_at.date() for r in results]
        assert date(2024, 2, 29) in conv_dates

    def test_boundary_inclusive_to_date(self, date_test_fixture: Path) -> None:
        """Test to_date boundary is inclusive (conversations ON to_date included)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(to_date=date(2024, 3, 1))
        
        results = list(adapter.search(date_test_fixture, query))
        
        # Post-leap-day conversation should be included (boundary is inclusive)
        conv_dates = [r.conversation.created_at.date() for r in results]
        assert date(2024, 3, 1) in conv_dates
