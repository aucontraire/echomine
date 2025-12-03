"""Contract tests for date-only filtering (FR-009).

Task: US4-AS1/AS4/AS5 - Date-Only Filtering Contract Tests
Phase: RED (tests designed to FAIL initially)

This module validates that the search command supports date-only filtering
without requiring --keywords or --title filters.

Current Issue:
    Lines 248-254 in search.py reject searches without --keywords or --title,
    returning exit code 2. This violates FR-009 which requires date-only filtering.

Expected Behavior:
    - echomine search export.json --from-date 2024-01-01 → Exit code 0
    - echomine search export.json --to-date 2024-12-31 → Exit code 0
    - echomine search export.json --from-date X --to-date Y → Exit code 0

Failing Acceptance Scenarios:
    - US4-AS1: Filter by date range (--from-date/--to-date)
    - US4-AS4: Filter with only --from-date
    - US4-AS5: Filter with only --to-date

Contract Requirements Validated:
    - FR-009: Date-only filtering without keywords/title
    - FR-442: --from-date filters conversations >= from_date
    - FR-443: --to-date filters conversations <= to_date
    - CHK032: Exit code 0 for success (not 2)
    - FR-301-306: JSON output works with date-only filtering

Constitution Compliance:
    - Principle III: TDD - Write failing tests FIRST
    - Principle II: CLI Interface Contract - Proper exit codes
    - Principle VI: Strict typing - All tests type-safe
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI:
    - In development: python -m echomine.cli.app
    - After install: echomine
    """
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def date_range_export(tmp_path: Path) -> Path:
    """Create export with conversations spanning different date ranges.

    Conversations:
    - conv-2024-01 (Jan 1, 2024): "January conversation"
    - conv-2024-06 (Jun 15, 2024): "June conversation"
    - conv-2024-12 (Dec 31, 2024): "December conversation"

    This allows testing date range filtering with predictable boundaries.
    """
    conversations = [
        {
            "id": "conv-2024-01",
            "title": "January conversation",
            "create_time": 1704067200.0,  # 2024-01-01 00:00:00 UTC
            "update_time": 1704067200.0,
            "mapping": {
                "msg-jan": {
                    "id": "msg-jan",
                    "message": {
                        "id": "msg-jan",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["January content"]},
                        "create_time": 1704067200.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-jan",
        },
        {
            "id": "conv-2024-06",
            "title": "June conversation",
            "create_time": 1718409600.0,  # 2024-06-15 00:00:00 UTC
            "update_time": 1718409600.0,
            "mapping": {
                "msg-jun": {
                    "id": "msg-jun",
                    "message": {
                        "id": "msg-jun",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["June content"]},
                        "create_time": 1718409600.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-jun",
        },
        {
            "id": "conv-2024-12",
            "title": "December conversation",
            "create_time": 1735689600.0,  # 2024-12-31 00:00:00 UTC
            "update_time": 1735689600.0,
            "mapping": {
                "msg-dec": {
                    "id": "msg-dec",
                    "message": {
                        "id": "msg-dec",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["December content"]},
                        "create_time": 1735689600.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-dec",
        },
    ]

    export_file = tmp_path / "date_range_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


# =============================================================================
# US4-AS1: Date Range Filtering (--from-date and --to-date)
# =============================================================================


@pytest.mark.contract
class TestDateRangeFilteringContract:
    """Contract tests for US4-AS1 - Filter by date range.

    Validates:
    - FR-009: Date-only filtering works without keywords/title
    - FR-442-443: Date range filters work correctly
    - Exit code 0 (success), not 2 (invalid args)

    Expected to FAIL:
    - Current implementation (lines 248-254 in search.py) requires
      at least one of --keywords or --title
    - These tests use ONLY --from-date and --to-date
    - Exit code 2 expected initially, should be 0 after fix
    """

    def test_us4_as1_date_range_without_keywords_succeeds(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS1: Search with --from-date and --to-date only (no keywords).

        Validates:
        - FR-009: Date-only filtering allowed
        - FR-442-443: Results filtered to date range
        - Exit code 0 (success)

        Expected to FAIL (RED phase):
        - Current: Exit code 2 "At least one of --keywords or --title must be specified"
        - After fix: Exit code 0 with results in date range
        """
        # Act: Search with date range ONLY (no keywords or title)
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-06-01",
                "--to-date",
                "2024-12-01",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success, not invalid args)
        assert result.returncode == 0, (
            f"Date-only filtering should succeed (FR-009). "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: stdout contains filtered results
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain search results"

        # Assert: Results include conversations in date range
        # June (2024-06-15) and potentially others between June 1 - Dec 1
        assert "June" in stdout, "June conversation should be in range [2024-06-01, 2024-12-01]"

        # Assert: Results exclude conversations outside date range
        assert "January" not in stdout, "January conversation before range (2024-01-01)"
        # December (2024-12-31) is after --to-date (2024-12-01)
        assert "December" not in stdout, "December conversation after range (2024-12-31)"

    def test_us4_as1_date_range_json_output_without_keywords(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS1: Date-only filtering with --json output.

        Validates:
        - FR-009: Date-only filtering works with JSON output
        - FR-301-306: JSON schema correct for date-only queries
        - Exit code 0

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before JSON processing
        - After fix: Valid JSON with date-filtered results
        """
        # Act: Search with date range and --json flag
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-06-01",
                "--to-date",
                "2024-12-01",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, (
            f"Date-only filtering with --json should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Valid JSON output
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{stdout}")

        # Assert: JSON structure (FR-301)
        assert isinstance(data, dict), "JSON output should be object"
        assert "results" in data, "JSON should have 'results' field"
        assert "metadata" in data, "JSON should have 'metadata' field"

        # Assert: Metadata includes date filters
        metadata = data["metadata"]
        assert "query" in metadata
        query_meta = metadata["query"]
        assert query_meta["date_from"] == "2024-06-01", "Metadata should include from_date"
        assert query_meta["date_to"] == "2024-12-01", "Metadata should include to_date"
        assert query_meta["keywords"] is None, "Metadata should show no keywords"
        assert query_meta["title_filter"] is None, "Metadata should show no title filter"

        # Assert: Results filtered correctly
        results = data["results"]
        assert isinstance(results, list)
        # At least June conversation should be present
        conv_titles = [r["title"] for r in results]
        assert "June conversation" in conv_titles


# =============================================================================
# US4-AS4: From-Date Only Filtering (--from-date without --to-date)
# =============================================================================


@pytest.mark.contract
class TestFromDateOnlyFilteringContract:
    """Contract tests for US4-AS4 - Filter with only --from-date.

    Validates:
    - FR-009: Date-only filtering works
    - FR-442: --from-date filters conversations >= from_date
    - Exit code 0 (success)

    Expected to FAIL:
    - Current implementation requires --keywords or --title
    - Exit code 2 expected initially
    """

    def test_us4_as4_from_date_only_without_keywords_succeeds(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS4: Search with --from-date only (no keywords, no --to-date).

        Validates:
        - FR-009: Date-only filtering allowed
        - FR-442: Results include all conversations >= from_date
        - Exit code 0 (success)

        Expected to FAIL (RED phase):
        - Current: Exit code 2 "At least one of --keywords or --title must be specified"
        - After fix: Exit code 0 with all conversations after from_date
        """
        # Act: Search with --from-date ONLY
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-06-01",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success)
        assert result.returncode == 0, (
            f"--from-date only should succeed (FR-009, FR-442). "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: stdout contains results
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain search results"

        # Assert: Results include conversations >= 2024-06-01
        assert "June" in stdout, "June conversation (2024-06-15) should be included"
        assert "December" in stdout, "December conversation (2024-12-31) should be included"

        # Assert: Results exclude conversations < 2024-06-01
        assert "January" not in stdout, "January conversation (2024-01-01) should be excluded"

    def test_us4_as4_from_date_only_with_quiet_flag(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS4: --from-date only with --quiet flag.

        Validates:
        - FR-009: Date-only filtering works
        - FR-310: --quiet suppresses progress indicators
        - Exit code 0

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before reaching quiet logic
        """
        # Act: Search with --from-date and --quiet
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-06-01",
                "--quiet",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, (
            f"--from-date with --quiet should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Results on stdout
        assert len(result.stdout) > 0, "Results should be on stdout"

        # Assert: No progress indicators on stderr
        stderr = result.stderr
        progress_keywords = ["parsing", "searching", "processing"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stderr.lower(), (
                f"--quiet should suppress '{keyword}' progress indicator"
            )

    def test_us4_as4_from_date_only_with_limit(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS4: --from-date only with --limit flag.

        Validates:
        - FR-009: Date-only filtering works
        - FR-336: --limit works with date-only queries
        - Exit code 0

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before limit processing
        """
        # Act: Search with --from-date and --limit
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-01-01",
                "--limit",
                "2",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, (
            f"--from-date with --limit should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Results returned (up to limit)
        stdout = result.stdout
        assert len(stdout) > 0, "Results should be on stdout"


# =============================================================================
# US4-AS5: To-Date Only Filtering (--to-date without --from-date)
# =============================================================================


@pytest.mark.contract
class TestToDateOnlyFilteringContract:
    """Contract tests for US4-AS5 - Filter with only --to-date.

    Validates:
    - FR-009: Date-only filtering works
    - FR-443: --to-date filters conversations <= to_date
    - Exit code 0 (success)

    Expected to FAIL:
    - Current implementation requires --keywords or --title
    - Exit code 2 expected initially
    """

    def test_us4_as5_to_date_only_without_keywords_succeeds(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS5: Search with --to-date only (no keywords, no --from-date).

        Validates:
        - FR-009: Date-only filtering allowed
        - FR-443: Results include all conversations <= to_date
        - Exit code 0 (success)

        Expected to FAIL (RED phase):
        - Current: Exit code 2 "At least one of --keywords or --title must be specified"
        - After fix: Exit code 0 with all conversations before to_date
        """
        # Act: Search with --to-date ONLY
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--to-date",
                "2024-06-30",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success)
        assert result.returncode == 0, (
            f"--to-date only should succeed (FR-009, FR-443). "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: stdout contains results
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain search results"

        # Assert: Results include conversations <= 2024-06-30
        assert "January" in stdout, "January conversation (2024-01-01) should be included"
        assert "June" in stdout, "June conversation (2024-06-15) should be included"

        # Assert: Results exclude conversations > 2024-06-30
        assert "December" not in stdout, "December conversation (2024-12-31) should be excluded"

    def test_us4_as5_to_date_only_json_output(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS5: --to-date only with --json output.

        Validates:
        - FR-009: Date-only filtering works with JSON
        - FR-301-306: JSON metadata includes to_date
        - Exit code 0

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before JSON processing
        """
        # Act: Search with --to-date and --json
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--to-date",
                "2024-06-30",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, (
            f"--to-date with --json should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Valid JSON
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{stdout}")

        # Assert: Metadata includes to_date
        metadata = data["metadata"]
        query_meta = metadata["query"]
        assert query_meta["date_to"] == "2024-06-30", "Metadata should include to_date"
        assert query_meta["date_from"] is None, "Metadata should show no from_date"
        assert query_meta["keywords"] is None, "Metadata should show no keywords"
        assert query_meta["title_filter"] is None, "Metadata should show no title filter"

    def test_us4_as5_to_date_only_with_format_text(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test US4-AS5: --to-date only with --format text.

        Validates:
        - FR-009: Date-only filtering works
        - FR-018: Human-readable text output
        - Exit code 0

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before format processing
        """
        # Act: Search with --to-date and --format text
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--to-date",
                "2024-06-30",
                "--format",
                "text",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, (
            f"--to-date with --format text should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Human-readable output
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain formatted results"
        # Table headers expected in text format
        assert "id" in stdout.lower() or "title" in stdout.lower()


# =============================================================================
# Edge Cases for Date-Only Filtering
# =============================================================================


@pytest.mark.contract
class TestDateOnlyFilteringEdgeCases:
    """Edge case tests for date-only filtering.

    Validates:
    - FR-009: Date-only filtering edge cases
    - Exit code 0 for zero results (not error)
    - Invalid date formats still exit code 2
    """

    def test_date_only_filtering_with_zero_results(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test date-only filtering with no matching conversations returns exit code 0.

        Validates:
        - FR-009: Date-only filtering works
        - FR-296: Zero results is success (exit code 0)
        - No error when date range has no matches

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before search execution
        - After fix: Exit code 0 with zero results
        """
        # Act: Search with date range that has no conversations
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2025-01-01",  # Future date - no conversations
                "--to-date",
                "2025-12-31",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success, not error)
        assert result.returncode == 0, (
            f"Zero results should be success (exit code 0). "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Output indicates zero results
        stdout = result.stdout
        # Either shows "0" results or very minimal output
        assert "0" in stdout or len(stdout) < 200, "Should indicate zero results"

    def test_date_only_filtering_invalid_date_format_still_exits_2(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test invalid date format with date-only filtering returns exit code 2.

        Validates:
        - FR-086: Invalid date format validation still works
        - Exit code 2 for invalid arguments
        - Date-only filtering doesn't bypass date validation

        Expected to FAIL initially (RED phase):
        - Current: keywords/title validation happens BEFORE date parsing
        - After fix: Date validation should happen BEFORE keywords/title validation
        - This ensures proper error messages (date error, not "missing keywords")
        """
        # Act: Search with invalid date format
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "01/01/2024",  # Invalid format (MM/DD/YYYY)
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (invalid argument)
        assert result.returncode == 2, (
            f"Invalid date format should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message mentions date format (not "keywords required")
        # After fix, date parsing should happen BEFORE keywords validation
        stderr = result.stderr
        assert "date" in stderr.lower(), (
            f"Error should mention date format, not missing keywords. Got: {stderr}"
        )

    def test_date_only_filtering_inverted_range_still_exits_2(
        self, cli_command: list[str], date_range_export: Path
    ) -> None:
        """Test inverted date range with date-only filtering returns exit code 2.

        Validates:
        - Date range validation (from <= to) still enforced
        - Exit code 2 for inverted range
        - Date-only filtering doesn't bypass range validation

        Expected to FAIL initially (RED phase):
        - Current: keywords/title validation happens BEFORE date range validation
        - After fix: Date range validation should happen BEFORE keywords/title validation
        - This ensures proper error messages (date range error, not "missing keywords")
        """
        # Act: Search with inverted date range
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(date_range_export),
                "--from-date",
                "2024-12-31",
                "--to-date",
                "2024-01-01",  # Before from_date!
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (invalid argument)
        assert result.returncode == 2, (
            f"Inverted date range should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message mentions date range
        stderr = result.stderr
        date_keywords = ["from", "to", "range", "after", "before"]
        assert any(keyword in stderr.lower() for keyword in date_keywords), (
            f"Error should mention date range issue. Got: {stderr}"
        )

    def test_date_only_filtering_works_with_empty_export(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test date-only filtering on empty export returns exit code 0.

        Validates:
        - FR-009: Date-only filtering works on empty files
        - Exit code 0 for empty results (not error)

        Expected to FAIL (RED phase):
        - Current: Exit code 2 before file processing
        - After fix: Exit code 0 with zero results
        """
        # Create empty export
        empty_file = tmp_path / "empty.json"
        with empty_file.open("w") as f:
            json.dump([], f)

        # Act: Search empty file with date-only filter
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(empty_file),
                "--from-date",
                "2024-01-01",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success)
        assert result.returncode == 0, (
            f"Date-only filtering on empty export should succeed. "
            f"Got exit code {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Zero results indicated
        stdout = result.stdout
        assert "0" in stdout or len(stdout) < 200, "Should indicate zero results"
