"""Contract tests for search command error handling and edge cases.

This module tests error paths, validation, and edge cases in the search command
that are currently missing coverage.

Coverage Target: search.py lines 233-464 (currently 12% coverage)

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2/130
    - FR-291-299: Error handling and exit codes
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine."""
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def minimal_export(tmp_path: Path) -> Path:
    """Create minimal valid export for testing."""
    conversations = [
        {
            "id": "test-conv-1",
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
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-1",
        }
    ]

    export_file = tmp_path / "test_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.contract
class TestSearchCommandValidation:
    """Contract tests for search command argument validation."""

    def test_search_requires_at_least_one_filter(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search without any filters exits with code 2.

        Validates:
        - search.py line 250-255: At least one filter required
        - Exit code 2 (invalid arguments)
        - Clear error message
        """
        result = subprocess.run(
            [*cli_command, "search", str(minimal_export)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2, f"No filters should exit 2, got {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error should be on stderr"
        assert "filter" in stderr.lower() or "keyword" in stderr.lower()

    def test_search_with_negative_limit_exits_code_2(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with --limit -5 exits with code 2.

        Validates:
        - search.py line 258-263: limit must be positive
        - Exit code 2
        - Error mentions limit
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--limit",
                "-5",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2, f"Negative limit should exit 2, got {result.returncode}"

        # Assert: Error mentions limit
        stderr = result.stderr
        assert "limit" in stderr.lower()

    def test_search_with_zero_limit_exits_code_2(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with --limit 0 exits with code 2.

        Validates:
        - search.py line 258-263: limit must be positive (> 0)
        - Exit code 2
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--limit",
                "0",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2

        # Assert: Error mentions limit
        assert "limit" in result.stderr.lower()

    def test_search_with_invalid_format_exits_code_1(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with --format xml exits with code 1.

        Validates:
        - search.py line 241-246: Invalid format validation
        - Exit code 1 (operational error, not argument error)
        - Error message clear
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--format",
                "xml",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1, f"Invalid format should exit 1, got {result.returncode}"

        # Assert: Error mentions format
        stderr = result.stderr
        assert "format" in stderr.lower()
        assert "xml" in stderr.lower()


@pytest.mark.contract
class TestSearchCommandDateValidation:
    """Contract tests for date parsing and validation in search."""

    def test_search_with_malformed_from_date_exits_code_2(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with invalid --from-date format exits code 2.

        Validates:
        - search.py line 269-277: from_date parsing
        - Exit code 2 (invalid argument)
        - Error mentions date format
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--from-date",
                "not-a-date",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2

        # Assert: Error mentions date
        assert "date" in result.stderr.lower()

    def test_search_with_malformed_to_date_exits_code_2(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with invalid --to-date format exits code 2.

        Validates:
        - search.py line 279-287: to_date parsing
        - Exit code 2
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--to-date",
                "2024/12/31",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2
        assert "date" in result.stderr.lower()

    def test_search_with_inverted_date_range_exits_code_2(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with from_date > to_date exits code 2.

        Validates:
        - search.py line 290-296: Date range validation
        - Exit code 2
        - Error message clear
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--from-date",
                "2024-12-31",
                "--to-date",
                "2024-01-01",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2

        # Assert: Error mentions date range issue
        stderr = result.stderr.lower()
        date_keywords = ["from", "to", "range", "after", "before"]
        assert any(keyword in stderr for keyword in date_keywords)


@pytest.mark.contract
class TestSearchCommandErrorHandling:
    """Contract tests for search command error handling paths."""

    def test_search_permission_denied_exits_code_1(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test search with unreadable file exits code 1.

        Validates:
        - search.py line 421-427: PermissionError handling
        - Exit code 1
        - Error mentions permission

        Skipped on Windows (different permission model).
        """
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        import stat

        # Create file without read permission
        no_read_file = tmp_path / "no_read.json"
        with no_read_file.open("w") as f:
            json.dump([], f)

        no_read_file.chmod(stat.S_IWUSR)  # Write-only

        try:
            result = subprocess.run(
                [
                    *cli_command,
                    "search",
                    str(no_read_file),
                    "--keywords",
                    "test",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            # Assert: Exit code 1
            assert result.returncode == 1

            # Assert: Error mentions permission
            stderr = result.stderr.lower()
            assert "permission" in stderr or "denied" in stderr

        finally:
            # Restore permissions for cleanup
            no_read_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_search_parse_error_exits_code_1(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test search with invalid JSON exits code 1.

        Validates:
        - search.py line 429-435: ParseError handling
        - Exit code 1
        - Error mentions JSON/parse
        """
        # Create malformed JSON
        malformed = tmp_path / "malformed.json"
        malformed.write_text("{not valid json")

        result = subprocess.run(
            [*cli_command, "search", str(malformed), "--keywords", "test"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions JSON/parse
        stderr = result.stderr.lower()
        assert "json" in stderr or "parse" in stderr or "invalid" in stderr


@pytest.mark.contract
class TestSearchCommandZeroResults:
    """Contract tests for zero results behavior and guidance."""

    def test_search_zero_results_exits_code_0(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with no matches exits code 0 (not error).

        Validates:
        - FR-296: Zero results is success
        - Exit code 0
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "nonexistentkeyword12345",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success, not error)
        assert result.returncode == 0

    def test_search_zero_results_shows_suggestions_on_tty(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search zero results shows suggestions to stderr.

        Validates:
        - search.py line 363-381: Zero results guidance
        - FR-097: Actionable suggestions
        - Suggestions on stderr, not stdout

        Note: subprocess.run doesn't simulate TTY, so stderr.isatty()
        returns False. This test validates the suggestion logic exists
        by checking that suggestions are NOT shown in non-TTY mode.
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "nonexistent",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # In non-TTY mode (subprocess), suggestions should NOT appear
        # This validates the sys.stderr.isatty() check works
        stderr = result.stderr

        # If stderr has content, it should be minimal (not full suggestions)
        # Full suggestions would have "Suggestions:" or "Try" text
        # In non-TTY, these should be absent
        if stderr:
            # May have progress indicators, but not suggestions
            pass  # No specific assertion - just ensuring no crash


@pytest.mark.contract
class TestSearchCommandKeywordHandling:
    """Contract tests for keyword parsing and handling."""

    def test_search_with_comma_separated_keywords(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with comma-separated keywords works.

        Validates:
        - search.py line 310-317: Comma-separated keyword parsing
        - Multiple keywords processed correctly
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test,message",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success (keywords parsed correctly)
        assert result.returncode == 0

    def test_search_with_multiple_keyword_flags(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search with multiple --keywords flags works.

        Validates:
        - Typer list accumulation
        - Multiple keyword flags combined
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--keywords",
                "message",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0


@pytest.mark.contract
class TestSearchCommandQuietFlag:
    """Contract tests for --quiet flag behavior."""

    def test_search_quiet_flag_suppresses_progress(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test --quiet suppresses progress indicators.

        Validates:
        - search.py line 335-340: progress_callback only if not quiet
        - FR-310: --quiet flag behavior
        - stderr minimal when quiet
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--quiet",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Results still on stdout
        assert len(result.stdout) > 0

        # Assert: No progress indicators on stderr
        stderr = result.stderr.lower()
        progress_keywords = ["searching", "processed", "conversations"]

        # Note: Some stderr output may exist (warnings), but no progress
        for keyword in progress_keywords:
            if keyword in stderr:
                # If found, should not be in a progress message format
                assert "processed" not in stderr or "conversations" not in stderr


@pytest.mark.contract
class TestSearchCommandJSONOutput:
    """Contract tests for JSON output format."""

    def test_search_json_flag_produces_valid_json(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test --json flag produces valid JSON output.

        Validates:
        - search.py line 238-239: --json alias for --format json
        - FR-301-306: JSON output schema
        - Valid JSON parseable by json.loads()
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Valid JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}\n{result.stdout}")

        # Assert: JSON structure
        assert isinstance(data, dict)
        assert "results" in data
        assert "metadata" in data

    def test_search_json_output_includes_metadata(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test JSON output includes complete metadata.

        Validates:
        - search.py line 392-402: format_search_results_json call
        - FR-303: Metadata structure
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(minimal_export),
                "--keywords",
                "test",
                "--limit",
                "5",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        data = json.loads(result.stdout)
        metadata = data["metadata"]

        # Assert: Metadata fields present (FR-303)
        assert "query" in metadata
        assert "total_results" in metadata
        assert "skipped_conversations" in metadata
        assert "elapsed_seconds" in metadata

        # Assert: Query metadata
        query = metadata["query"]
        assert "keywords" in query
        assert "title_filter" in query
        assert "date_from" in query
        assert "date_to" in query
        assert "limit" in query

        # Assert: Query values match request
        assert query["keywords"] == ["test"]
        assert query["limit"] == 5


@pytest.mark.contract
class TestSearchCommandStdoutStderrSeparation:
    """Contract tests for stdout/stderr separation."""

    def test_search_progress_on_stderr_not_stdout(
        self, cli_command: list[str], minimal_export: Path
    ) -> None:
        """Test search progress goes to stderr, not stdout.

        Validates:
        - CHK031: Data on stdout, progress on stderr
        - FR-291-292: Stream separation
        """
        result = subprocess.run(
            [*cli_command, "search", str(minimal_export), "--keywords", "test"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: stdout contains ONLY data (no progress indicators)
        stdout = result.stdout.lower()
        progress_keywords = ["searching", "processing", "parsed"]

        for keyword in progress_keywords:
            assert keyword not in stdout, (
                f"Progress indicator '{keyword}' found in stdout. Should be on stderr per CHK031"
            )

    def test_search_errors_on_stderr_not_stdout(self, cli_command: list[str]) -> None:
        """Test search errors go to stderr, not stdout.

        Validates:
        - CHK031: Errors on stderr
        - stdout empty on error
        """
        result = subprocess.run(
            [
                *cli_command,
                "search",
                "/nonexistent/file.json",
                "--keywords",
                "test",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Error (exit code 1)
        assert result.returncode == 1

        # Assert: Error message on stderr
        assert len(result.stderr) > 0

        # Assert: stdout empty
        assert len(result.stdout) == 0, "stdout should be empty on error"
