"""Test date parsing utilities for ISO 8601 format.

This module tests the parse_date() function used by the CLI to convert
YYYY-MM-DD strings to Python date objects.

Constitution Compliance:
    - Principle III: TDD (tests for existing implementation)
    - Principle VI: Strict typing with mypy --strict compliance
"""

from __future__ import annotations

from datetime import date

import pytest

from echomine.cli.commands.search import parse_date


class TestDateParsing:
    """Test ISO 8601 date parsing (YYYY-MM-DD)."""

    def test_parse_valid_date(self) -> None:
        """Test parsing valid ISO 8601 date string."""
        result = parse_date("2024-06-15")
        assert result == date(2024, 6, 15)

    def test_parse_leap_year_date(self) -> None:
        """Test parsing leap year date (Feb 29)."""
        result = parse_date("2024-02-29")
        assert result == date(2024, 2, 29)

    def test_parse_invalid_leap_year(self) -> None:
        """Test parsing Feb 29 in non-leap year raises error."""
        with pytest.raises(ValueError, match="day is out of range"):
            parse_date("2023-02-29")

    def test_parse_month_boundary(self) -> None:
        """Test parsing dates at month boundaries."""
        assert parse_date("2024-01-31") == date(2024, 1, 31)
        assert parse_date("2024-02-01") == date(2024, 2, 1)

    def test_parse_invalid_format_slash(self) -> None:
        """Test parsing MM/DD/YYYY format raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("06/15/2024")

    def test_parse_invalid_format_dmy(self) -> None:
        """Test parsing DD-MM-YYYY format raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("15-06-2024")

    def test_parse_invalid_string(self) -> None:
        """Test parsing non-date string raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("yesterday")

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("")

    def test_parse_invalid_month(self) -> None:
        """Test parsing invalid month (13) raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("2024-13-01")

    def test_parse_invalid_day(self) -> None:
        """Test parsing invalid day (32) raises error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("2024-01-32")
