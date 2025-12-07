"""Unit tests for search command validation error paths.

Task: Coverage improvement for validation errors in search.py
Phase: TDD RED-GREEN-REFACTOR

This module tests the validation error handling in the search command:
- Invalid --sort values (lines 368-373)
- Invalid --order values (lines 376-382)
- Invalid date range (from_date > to_date) (lines 409-415)

Test Pyramid Classification: Unit (70% of test suite)
These tests validate error handling and exit codes.

Coverage Target:
- Lines 368-373 in search.py (invalid --sort validation)
- Lines 376-382 in search.py (invalid --order validation)
- Lines 409-415 in search.py (invalid date range validation)
- Exit code 2 for invalid arguments
"""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from echomine.cli.commands.search import search_conversations


@pytest.fixture
def sample_export_file(tmp_path: Path) -> Path:
    """Create a minimal valid export file for testing."""
    export_file = tmp_path / "export.json"
    export_file.write_text(
        """[
  {
    "id": "conv-001",
    "title": "Test Conversation",
    "create_time": 1700000000.0,
    "update_time": 1700001000.0,
    "mapping": {
      "msg-1": {
        "id": "msg-1",
        "message": {
          "id": "msg-1",
          "author": {"role": "user"},
          "content": {"content_type": "text", "parts": ["Test message"]},
          "create_time": 1700000000.0,
          "update_time": null,
          "metadata": {}
        },
        "parent": null,
        "children": []
      }
    },
    "moderation_results": [],
    "current_node": "msg-1"
  }
]"""
    )
    return export_file


@pytest.mark.unit
class TestSearchSortValidation:
    """Unit tests for --sort validation in search command."""

    def test_invalid_sort_value_returns_exit_code_2(self, sample_export_file: Path) -> None:
        """Test invalid --sort value returns exit code 2.

        Validates:
        - Lines 368-373 in search.py executed
        - Exit code 2 for invalid arguments
        - Error message mentions valid options
        """
        # Act: Call search_conversations with invalid --sort
        with pytest.raises(typer.Exit) as exc_info:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                sort="invalid_sort",  # Invalid value
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Assert: Exit code 2
        assert exc_info.value.exit_code == 2

    def test_invalid_sort_error_message_lists_valid_options(
        self, sample_export_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test invalid --sort shows valid options in error message.

        Validates:
        - Error message helpful and clear
        - Line 370 executed (error message)
        """
        # Act: Call search_conversations with invalid --sort
        with pytest.raises(typer.Exit):
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                sort="bad_sort",
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Capture stderr
        captured = capsys.readouterr()

        # Assert: Error message mentions valid options
        assert "Invalid --sort" in captured.err or "bad_sort" in captured.err
        assert (
            "score" in captured.err
            or "date" in captured.err
            or "title" in captured.err
            or "messages" in captured.err
        )

    def test_valid_sort_values_accepted(self, sample_export_file: Path) -> None:
        """Test valid --sort values are accepted without error.

        Validates:
        - "score", "date", "title", "messages" are valid
        - No exit code 2 for valid values
        """
        valid_sorts = ["score", "date", "title", "messages"]

        for sort_value in valid_sorts:
            # Act: Should not raise typer.Exit with code 2
            try:
                search_conversations(
                    file_path=sample_export_file,
                    keywords=["test"],
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
                    sort=sort_value,
                    order="desc",
                    format="text",
                    quiet=False,
                    json=False,
                    csv_messages=False,
                )
            except typer.Exit as e:
                # Exit code 0 is OK (success), only fail on code 2
                if e.exit_code == 2:
                    pytest.fail(f"Valid sort value '{sort_value}' was rejected")


@pytest.mark.unit
class TestSearchOrderValidation:
    """Unit tests for --order validation in search command."""

    def test_invalid_order_value_returns_exit_code_2(self, sample_export_file: Path) -> None:
        """Test invalid --order value returns exit code 2.

        Validates:
        - Lines 376-382 in search.py executed
        - Exit code 2 for invalid arguments
        - Error message mentions valid options
        """
        # Act: Call search_conversations with invalid --order
        with pytest.raises(typer.Exit) as exc_info:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                order="invalid_order",  # Invalid value
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Assert: Exit code 2
        assert exc_info.value.exit_code == 2

    def test_invalid_order_error_message_lists_valid_options(
        self, sample_export_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test invalid --order shows valid options in error message.

        Validates:
        - Error message helpful and clear
        - Line 378 executed (error message)
        """
        # Act: Call search_conversations with invalid --order
        with pytest.raises(typer.Exit):
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                order="bad_order",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Capture stderr
        captured = capsys.readouterr()

        # Assert: Error message mentions valid options
        assert "Invalid --order" in captured.err or "bad_order" in captured.err
        assert "asc" in captured.err or "desc" in captured.err

    def test_valid_order_values_accepted(self, sample_export_file: Path) -> None:
        """Test valid --order values are accepted without error.

        Validates:
        - "asc", "desc" are valid
        - No exit code 2 for valid values
        """
        valid_orders = ["asc", "desc"]

        for order_value in valid_orders:
            # Act: Should not raise typer.Exit with code 2
            try:
                search_conversations(
                    file_path=sample_export_file,
                    keywords=["test"],
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
                    order=order_value,
                    format="text",
                    quiet=False,
                    json=False,
                    csv_messages=False,
                )
            except typer.Exit as e:
                # Exit code 0 is OK (success), only fail on code 2
                if e.exit_code == 2:
                    pytest.fail(f"Valid order value '{order_value}' was rejected")


@pytest.mark.unit
class TestSearchDateRangeValidation:
    """Unit tests for date range validation in search command."""

    def test_from_date_after_to_date_returns_exit_code_2(self, sample_export_file: Path) -> None:
        """Test from_date > to_date returns exit code 2.

        Validates:
        - Lines 409-415 in search.py executed
        - Exit code 2 for invalid date range
        - Error message mentions the constraint
        """
        # Act: Call search_conversations with invalid date range
        with pytest.raises(typer.Exit) as exc_info:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date="2024-12-31",  # After to_date
                to_date="2024-01-01",  # Before from_date
                min_messages=None,
                max_messages=None,
                limit=None,
                sort="score",
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Assert: Exit code 2
        assert exc_info.value.exit_code == 2

    def test_invalid_date_range_error_message(
        self, sample_export_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test invalid date range shows helpful error message.

        Validates:
        - Error message explains the constraint
        - Line 412 executed (error message)
        """
        # Act: Call search_conversations with invalid date range
        with pytest.raises(typer.Exit):
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date="2024-12-31",
                to_date="2024-01-01",
                min_messages=None,
                max_messages=None,
                limit=None,
                sort="score",
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Capture stderr
        captured = capsys.readouterr()

        # Assert: Error message explains constraint
        assert "--from-date" in captured.err
        assert "--to-date" in captured.err
        assert "<=" in captured.err or "must be" in captured.err.lower()

    def test_valid_date_range_accepted(self, sample_export_file: Path) -> None:
        """Test valid date range (from <= to) is accepted.

        Validates:
        - from_date <= to_date passes validation
        - No exit code 2
        """
        # Act: Valid date range should not raise exit code 2
        try:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date="2024-01-01",  # Before to_date
                to_date="2024-12-31",  # After from_date
                min_messages=None,
                max_messages=None,
                limit=None,
                sort="score",
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )
        except typer.Exit as e:
            if e.exit_code == 2:
                pytest.fail("Valid date range was rejected")

    def test_equal_from_and_to_date_accepted(self, sample_export_file: Path) -> None:
        """Test from_date == to_date is valid (same day filtering).

        Validates:
        - Equal dates allowed (single day filter)
        - Line 410 executed (comparison allows equality)
        """
        # Act: Equal dates should be accepted
        try:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
                phrase=None,
                match_mode="any",
                exclude=None,
                role=None,
                title=None,
                from_date="2024-06-15",
                to_date="2024-06-15",  # Same date
                min_messages=None,
                max_messages=None,
                limit=None,
                sort="score",
                order="desc",
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )
        except typer.Exit as e:
            if e.exit_code == 2:
                pytest.fail("Equal from_date and to_date should be valid")


@pytest.mark.unit
class TestSearchCombinedValidation:
    """Unit tests for combined validation scenarios."""

    def test_case_insensitive_validation(self, sample_export_file: Path) -> None:
        """Test --sort and --order are case-insensitive.

        Validates:
        - Upper/mixed case values accepted
        - Lines 367, 376 executed (lowercase conversion)
        """
        # Act: Upper case should be accepted
        try:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                sort="SCORE",  # Upper case
                order="DESC",  # Upper case
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )
        except typer.Exit as e:
            if e.exit_code == 2:
                pytest.fail("Case-insensitive validation failed")

    def test_multiple_validation_errors_fails_on_first(self, sample_export_file: Path) -> None:
        """Test multiple validation errors fail on first encountered.

        Validates:
        - Validation order matters
        - Exit code 2 on first failure
        """
        # Act: Multiple errors, but --sort checked first (before --order)
        with pytest.raises(typer.Exit) as exc_info:
            search_conversations(
                file_path=sample_export_file,
                keywords=["test"],
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
                sort="invalid_sort",  # Checked first
                order="invalid_order",  # Not reached
                format="text",
                quiet=False,
                json=False,
                csv_messages=False,
            )

        # Assert: Exit code 2
        assert exc_info.value.exit_code == 2
