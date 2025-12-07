"""Integration tests for CSV export CLI functionality.

This module tests the CSV export features in the list and search commands,
verifying end-to-end integration with the OpenAIAdapter and CSVExporter.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle II: CLI interface contract (stdout/stderr/exit codes)
    - CHK031: Results to stdout, progress/errors to stderr

Test Coverage:
    - T138: --format csv and --csv-messages are mutually exclusive (FR-051a)
    - T140: --format csv outputs CSV (FR-049)
    - T141: FR-050 CSV schema validation (conversation-level)

Requirements:
    - FR-049: CSV output format (--format csv)
    - FR-050: Conversation-level CSV schema
    - FR-051: Message-level CSV with --csv-messages flag
    - FR-051a: --format csv and --csv-messages are mutually exclusive (exit 2)
    - FR-051b: Error message explains mutual exclusion
    - FR-052: Message-level CSV schema
"""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

import pytest
from typer.testing import CliRunner

from echomine.cli.app import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def csv_test_export(tmp_path: Path) -> Path:
    """Create test export for CSV testing.

    Creates an export with 2 conversations with known data for CSV validation.
    """
    export_data = [
        {
            "id": "abc-123",
            "title": "Deep Python Discussion",
            "create_time": 1705320600.0,  # 2024-01-15 10:30:00 UTC
            "update_time": 1705336500.0,  # 2024-01-15 14:45:00 UTC
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Hello, I need help with Python generators"],
                        },
                        "create_time": 1705320605.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-002"],
                },
                "msg-002": {
                    "id": "msg-002",
                    "message": {
                        "id": "msg-002",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Python generators are a powerful feature..."],
                        },
                        "create_time": 1705320647.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001",
                    "children": [],
                },
            },
        },
        {
            "id": "def-456",
            "title": 'Quick Question, with "comma" and quotes',
            "create_time": 1705234500.0,  # 2024-01-14 09:15:00 UTC
            "update_time": 1705234800.0,  # 2024-01-14 09:20:00 UTC
            "mapping": {
                "msg-003": {
                    "id": "msg-003",
                    "message": {
                        "id": "msg-003",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["What is Python?"]},
                        "create_time": 1705234500.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
    ]

    export_file = tmp_path / "csv_test_export.json"
    export_file.write_text(json.dumps(export_data))
    return export_file


# T140: Test --format csv outputs CSV (FR-049)
class TestListCommandCSV:
    """Test list command CSV output (FR-049, FR-050)."""

    def test_list_with_format_csv(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test list command with --format csv outputs CSV format."""
        result = cli_runner.invoke(app, ["list", str(csv_test_export), "--format", "csv"])

        # Verify exit code 0 (success)
        assert result.exit_code == 0

        # Verify output is CSV format
        output = result.stdout
        lines = output.splitlines()

        # Verify CSV header (FR-050)
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count"

        # Verify at least one data row
        assert len(lines) >= 2

    def test_list_csv_parseable(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test that list CSV output is parseable by Python csv module."""
        result = cli_runner.invoke(app, ["list", str(csv_test_export), "--format", "csv"])

        assert result.exit_code == 0

        # Parse CSV output
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify we got 2 conversations
        assert len(rows) == 2

        # Verify CSV schema (FR-050)
        assert "conversation_id" in rows[0]
        assert "title" in rows[0]
        assert "created_at" in rows[0]
        assert "updated_at" in rows[0]
        assert "message_count" in rows[0]

        # Verify special character handling
        # One of the conversations has commas and quotes in title
        titles = [row["title"] for row in rows]
        assert 'Quick Question, with "comma" and quotes' in titles

    def test_list_csv_with_limit(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test list CSV with --limit flag."""
        result = cli_runner.invoke(
            app, ["list", str(csv_test_export), "--format", "csv", "--limit", "1"]
        )

        assert result.exit_code == 0

        lines = result.stdout.splitlines()
        # Header + 1 data row (due to limit)
        assert len(lines) == 2


class TestSearchCommandCSV:
    """Test search command CSV output (FR-049, FR-050)."""

    def test_search_with_format_csv(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test search command with --format csv outputs CSV format."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--format", "csv"],
        )

        # Verify exit code 0 (success)
        assert result.exit_code == 0

        # Verify output is CSV format
        output = result.stdout
        lines = output.splitlines()

        # Verify CSV header includes score column (FR-050)
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count,score"

    def test_search_csv_includes_scores(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test that search CSV output includes relevance scores."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--format", "csv"],
        )

        assert result.exit_code == 0

        # Parse CSV output
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify score column exists
        assert "score" in rows[0]

        # Verify score is a valid float between 0 and 1
        for row in rows:
            score = float(row["score"])
            assert 0.0 <= score <= 1.0


# T138: Test --format csv and --csv-messages are mutually exclusive (FR-051a)
class TestCSVMutualExclusion:
    """Test mutual exclusion of CSV flags (FR-051a, FR-051b)."""

    def test_format_csv_and_csv_messages_mutually_exclusive(
        self, cli_runner: CliRunner, csv_test_export: Path
    ) -> None:
        """Test that --format csv and --csv-messages cannot be used together."""
        result = cli_runner.invoke(
            app,
            [
                "search",
                str(csv_test_export),
                "-k",
                "python",
                "--format",
                "csv",
                "--csv-messages",
            ],
        )

        # Verify exit code 2 (usage error) per FR-051a
        assert result.exit_code == 2

        # Verify error message explains mutual exclusion (FR-051b)
        assert "mutually exclusive" in result.stderr.lower()
        assert "--format csv" in result.stderr
        assert "--csv-messages" in result.stderr

    def test_csv_messages_works_alone(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test that --csv-messages works without --format csv."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--csv-messages"],
        )

        # Should succeed (exit code 0)
        assert result.exit_code == 0

        # Verify message-level CSV header (FR-052)
        lines = result.stdout.splitlines()
        assert lines[0] == "conversation_id,message_id,role,timestamp,content"

    def test_csv_messages_schema(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test message-level CSV schema (FR-052)."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--csv-messages"],
        )

        assert result.exit_code == 0

        # Parse CSV output
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify message-level schema (FR-052)
        assert "conversation_id" in rows[0]
        assert "message_id" in rows[0]
        assert "role" in rows[0]
        assert "timestamp" in rows[0]
        assert "content" in rows[0]

        # Verify message content
        for row in rows:
            assert row["role"] in ["user", "assistant", "system"]
            assert len(row["content"]) > 0


# T141: Contract test - FR-050 CSV schema validation
class TestCSVSchemaContract:
    """Contract tests for CSV schema (FR-050, FR-052)."""

    def test_conversation_csv_schema_complete(
        self, cli_runner: CliRunner, csv_test_export: Path
    ) -> None:
        """Test that conversation-level CSV contains all required fields."""
        result = cli_runner.invoke(app, ["list", str(csv_test_export), "--format", "csv"])

        assert result.exit_code == 0

        # Parse CSV
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify required fields exist for each row
        for row in rows:
            # FR-050: conversation_id, title, created_at, updated_at, message_count
            assert "conversation_id" in row
            assert "title" in row
            assert "created_at" in row
            assert "updated_at" in row
            assert "message_count" in row

            # Verify non-empty values
            assert len(row["conversation_id"]) > 0
            assert len(row["title"]) > 0
            assert len(row["created_at"]) > 0
            # updated_at can be empty (NULL)
            assert len(row["message_count"]) > 0

            # Verify message_count is valid integer
            assert int(row["message_count"]) > 0

    def test_search_csv_schema_includes_score(
        self, cli_runner: CliRunner, csv_test_export: Path
    ) -> None:
        """Test that search CSV includes score column (FR-050)."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--format", "csv"],
        )

        assert result.exit_code == 0

        # Parse CSV
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify score column exists
        for row in rows:
            assert "score" in row
            # Verify score is valid float
            score = float(row["score"])
            assert 0.0 <= score <= 1.0

    def test_message_csv_schema_complete(
        self, cli_runner: CliRunner, csv_test_export: Path
    ) -> None:
        """Test that message-level CSV contains all required fields (FR-052)."""
        result = cli_runner.invoke(
            app,
            ["search", str(csv_test_export), "-k", "python", "--csv-messages"],
        )

        assert result.exit_code == 0

        # Parse CSV
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify required fields exist for each row
        for row in rows:
            # FR-052: conversation_id, message_id, role, timestamp, content
            assert "conversation_id" in row
            assert "message_id" in row
            assert "role" in row
            assert "timestamp" in row
            assert "content" in row

            # Verify non-empty values
            assert len(row["conversation_id"]) > 0
            assert len(row["message_id"]) > 0
            assert len(row["role"]) > 0
            assert len(row["timestamp"]) > 0
            # content can be empty for some messages

            # Verify role is valid
            assert row["role"] in ["user", "assistant", "system"]

    def test_csv_datetime_format(self, cli_runner: CliRunner, csv_test_export: Path) -> None:
        """Test that CSV datetimes are in ISO 8601 format with Z suffix."""
        result = cli_runner.invoke(app, ["list", str(csv_test_export), "--format", "csv"])

        assert result.exit_code == 0

        # Parse CSV
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        # Verify datetime format (ISO 8601 with Z suffix)
        for row in rows:
            # created_at is always present
            assert row["created_at"].endswith("Z")
            assert "T" in row["created_at"]  # ISO 8601 separator

            # updated_at may be empty (NULL)
            if row["updated_at"]:
                assert row["updated_at"].endswith("Z")
                assert "T" in row["updated_at"]
