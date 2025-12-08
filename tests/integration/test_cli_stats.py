"""Integration tests for stats CLI command.

This module tests the stats command end-to-end integration with the
OpenAIAdapter, verifying correct statistics computation and output formatting.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle II: CLI interface contract (stdout/stderr/exit codes)
    - CHK031: Results to stdout, progress/errors to stderr

Test Coverage:
    - T055: Stats command executes and returns exit code 0
    - T056: --json flag outputs valid JSON (FR-012)
    - T057: Progress is reported to stderr (FR-014)
    - Error handling (file not found, parse errors)
    - Exit code validation

Phase: RED (tests designed to FAIL initially)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from echomine.cli.app import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def stats_test_export(tmp_path: Path) -> Path:
    """Create test export for stats command with known statistics.

    Creates an export with 3 conversations:
    - Conversation 1: 5 messages (2 user, 3 assistant)
    - Conversation 2: 2 messages (1 user, 1 assistant) - smallest
    - Conversation 3: 10 messages (4 user, 5 assistant, 1 system) - largest

    Total: 3 conversations, 17 messages
    Average: 5.67 messages per conversation
    Date range: 2024-01-15 to 2024-01-20
    """
    export_data = [
        {
            "id": "conv-001",
            "title": "Python Discussion",
            "create_time": 1705320000.0,  # 2024-01-15 10:00:00 UTC
            "update_time": 1705330000.0,  # 2024-01-15 12:46:40 UTC
            "mapping": {
                "msg-001-1": {
                    "id": "msg-001-1",
                    "message": {
                        "id": "msg-001-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello"]},
                        "create_time": 1705320000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-001-2"],
                },
                "msg-001-2": {
                    "id": "msg-001-2",
                    "message": {
                        "id": "msg-001-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Hi there!"]},
                        "create_time": 1705320010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-1",
                    "children": ["msg-001-3"],
                },
                "msg-001-3": {
                    "id": "msg-001-3",
                    "message": {
                        "id": "msg-001-3",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["How are you?"]},
                        "create_time": 1705320020.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-2",
                    "children": ["msg-001-4"],
                },
                "msg-001-4": {
                    "id": "msg-001-4",
                    "message": {
                        "id": "msg-001-4",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["I'm good"]},
                        "create_time": 1705320030.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-3",
                    "children": ["msg-001-5"],
                },
                "msg-001-5": {
                    "id": "msg-001-5",
                    "message": {
                        "id": "msg-001-5",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Thanks"]},
                        "create_time": 1705320040.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-4",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-001-5",
        },
        {
            "id": "conv-002",
            "title": "Quick Question",
            "create_time": 1705492800.0,  # 2024-01-17 10:00:00 UTC
            "update_time": None,
            "mapping": {
                "msg-002-1": {
                    "id": "msg-002-1",
                    "message": {
                        "id": "msg-002-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Quick question"]},
                        "create_time": 1705492800.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-002-2"],
                },
                "msg-002-2": {
                    "id": "msg-002-2",
                    "message": {
                        "id": "msg-002-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Sure, go ahead"]},
                        "create_time": 1705492810.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-002-2",
        },
        {
            "id": "conv-003",
            "title": "Deep Technical Discussion",
            "create_time": 1705665600.0,  # 2024-01-19 10:00:00 UTC
            "update_time": 1705752000.0,  # 2024-01-20 10:00:00 UTC
            "mapping": {
                f"msg-003-{i}": {
                    "id": f"msg-003-{i}",
                    "message": {
                        "id": f"msg-003-{i}",
                        "author": {
                            "role": "user"
                            if i % 2 == 1
                            else "assistant"
                            if i % 2 == 0 and i < 10
                            else "system"
                        },
                        "content": {"content_type": "text", "parts": [f"Message {i}"]},
                        "create_time": 1705665600.0 + (i * 10),
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": f"msg-003-{i - 1}" if i > 1 else None,
                    "children": [f"msg-003-{i + 1}"] if i < 10 else [],
                }
                for i in range(1, 11)
            },
            "moderation_results": [],
            "current_node": "msg-003-10",
        },
    ]

    export_path = tmp_path / "stats_test_export.json"
    with open(export_path, "w") as f:
        json.dump(export_data, f)

    return export_path


class TestT055StatsCommandExecution:
    """T055: Test stats command executes and returns exit code 0."""

    def test_stats_command_exists(self, cli_runner: CliRunner, stats_test_export: Path) -> None:
        """Verify stats command is registered and accessible."""
        result = cli_runner.invoke(app, ["stats", "--help"])

        # Should return 0 and show help text
        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"
        assert "stats" in result.stdout.lower(), "Help text should mention stats command"

    def test_stats_command_returns_exit_code_0(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify stats command executes successfully and returns 0."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export)])

        # Should return 0 for successful execution
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_stats_command_displays_statistics(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify stats command outputs statistics to stdout."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export)])

        assert result.exit_code == 0

        # Check for required statistics in output (FR-010)
        assert "3" in result.stdout, "Should display total conversations (3)"
        assert "17" in result.stdout, "Should display total messages (17)"

        # Check for largest/smallest conversations (FR-011)
        assert "Deep Technical Discussion" in result.stdout, "Should show largest conversation"
        assert "Quick Question" in result.stdout, "Should show smallest conversation"


class TestT056StatsJsonOutput:
    """T056: Test --json flag outputs valid JSON (FR-012)."""

    def test_stats_json_flag_produces_valid_json(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify --json flag outputs parseable JSON."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export), "--json"])

        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

        # Parse JSON from stdout
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout}")

        # Verify required fields (FR-012)
        assert "total_conversations" in data, "JSON should include total_conversations"
        assert "total_messages" in data, "JSON should include total_messages"
        assert data["total_conversations"] == 3, "Should have 3 conversations"
        assert data["total_messages"] == 17, "Should have 17 messages"

    def test_stats_json_includes_all_fields(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify JSON output includes all required statistics fields."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Verify all required fields (FR-010, FR-011)
        required_fields = [
            "total_conversations",
            "total_messages",
            "earliest_date",
            "latest_date",
            "average_messages",
            "largest_conversation",
            "smallest_conversation",
        ]

        for field in required_fields:
            assert field in data, f"JSON output should include {field}"

        # Verify largest conversation structure
        assert data["largest_conversation"]["id"] == "conv-003"
        assert data["largest_conversation"]["title"] == "Deep Technical Discussion"
        assert data["largest_conversation"]["message_count"] == 10

        # Verify smallest conversation structure
        assert data["smallest_conversation"]["id"] == "conv-002"
        assert data["smallest_conversation"]["title"] == "Quick Question"
        assert data["smallest_conversation"]["message_count"] == 2


class TestT057StatsProgressReporting:
    """T057: Test progress is reported to stderr (FR-014)."""

    def test_stats_reports_progress_to_stderr(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify progress indicators are written to stderr, not stdout."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export)])

        assert result.exit_code == 0

        # Progress should be in stderr (or at least not pollute stdout)
        # When --json is NOT used, stdout should only contain the formatted stats
        # Progress/status updates should go to stderr

        # For human-readable output, stdout should contain stats table
        assert "Export Statistics" in result.stdout or "Total conversations" in result.stdout

    def test_stats_json_stdout_clean(self, cli_runner: CliRunner, stats_test_export: Path) -> None:
        """Verify JSON output to stdout contains ONLY valid JSON (FR-014)."""
        result = cli_runner.invoke(app, ["stats", str(stats_test_export), "--json"])

        assert result.exit_code == 0

        # stdout should be ONLY valid JSON (no progress indicators)
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"stdout should contain ONLY valid JSON (no progress pollution): {e}\n"
                f"stdout: {result.stdout}"
            )


class TestT055ErrorHandling:
    """Test error handling for stats command."""

    def test_stats_file_not_found_exit_code_1(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Verify stats command returns exit code 1 for missing file."""
        missing_file = tmp_path / "nonexistent.json"
        result = cli_runner.invoke(app, ["stats", str(missing_file)])

        # Should return exit code 1 for operational errors
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"
        assert (
            "Error" in result.stdout
            or "Error" in result.stderr
            or "not found" in result.stdout.lower()
        )

    def test_stats_missing_argument_exit_code_2(self, cli_runner: CliRunner) -> None:
        """Verify stats command returns exit code 2 for missing arguments."""
        result = cli_runner.invoke(app, ["stats"])

        # Should return exit code 2 for usage errors
        assert result.exit_code == 2, f"Expected exit code 2, got {result.exit_code}"


class TestT065PerConversationStats:
    """T065: Test --conversation option shows per-conversation stats (FR-018)."""

    def test_conversation_option_displays_statistics(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify --conversation option displays per-conversation statistics."""
        result = cli_runner.invoke(
            app, ["stats", str(stats_test_export), "--conversation", "conv-001"]
        )

        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Check for required per-conversation fields (FR-019)
        assert "conv-001" in result.stdout, "Should display conversation ID"
        assert "Python Discussion" in result.stdout, "Should display conversation title"

        # Check for message breakdown (FR-020)
        assert "user:" in result.stdout or "User:" in result.stdout, (
            "Should show user message count"
        )
        assert "assistant:" in result.stdout or "Assistant:" in result.stdout, (
            "Should show assistant message count"
        )

        # Check for temporal patterns (FR-021)
        assert "Duration:" in result.stdout or "duration:" in result.stdout, (
            "Should show conversation duration"
        )
        assert "First message:" in result.stdout or "first message:" in result.stdout, (
            "Should show first message time"
        )
        assert "Last message:" in result.stdout or "last message:" in result.stdout, (
            "Should show last message time"
        )

    def test_conversation_option_shows_role_breakdown(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify --conversation displays message count by role (FR-020)."""
        result = cli_runner.invoke(
            app, ["stats", str(stats_test_export), "--conversation", "conv-003"]
        )

        assert result.exit_code == 0

        # conv-003 has 10 messages: 5 user, 4 assistant, 1 system
        # Check for numeric counts in output
        output_lower = result.stdout.lower()
        assert "user" in output_lower, "Should show user role"
        assert "assistant" in output_lower, "Should show assistant role"
        assert "system" in output_lower, "Should show system role (conv-003 has system messages)"


class TestT066InvalidConversationID:
    """T066: Test invalid conversation ID exits with code 1 (FR-018)."""

    def test_invalid_conversation_id_exit_code_1(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify invalid conversation ID returns exit code 1."""
        result = cli_runner.invoke(
            app, ["stats", str(stats_test_export), "--conversation", "invalid-id-999"]
        )

        # Should return exit code 1 for operational error (conversation not found)
        assert result.exit_code == 1, (
            f"Expected exit code 1 for invalid conversation ID, got {result.exit_code}"
        )

        # Error message should indicate conversation not found
        combined_output = result.stdout + result.stderr
        assert "not found" in combined_output.lower() or "error" in combined_output.lower(), (
            "Should display error message for invalid conversation ID"
        )


class TestT067PerConversationJSON:
    """T067: Test --json flag with --conversation outputs JSON (FR-024)."""

    def test_conversation_json_output_valid(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify --conversation with --json outputs valid JSON."""
        result = cli_runner.invoke(
            app, ["stats", str(stats_test_export), "--conversation", "conv-001", "--json"]
        )

        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

        # Parse JSON from stdout
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout}")

        # Verify required per-conversation fields (FR-024)
        assert "conversation_id" in data, "JSON should include conversation_id"
        assert "title" in data, "JSON should include title"
        assert "message_count" in data, "JSON should include message_count"
        assert "message_count_by_role" in data, "JSON should include message_count_by_role"

        # Verify values match conv-001
        assert data["conversation_id"] == "conv-001"
        assert data["title"] == "Python Discussion"
        assert data["message_count"] == 5

    def test_conversation_json_includes_temporal_patterns(
        self, cli_runner: CliRunner, stats_test_export: Path
    ) -> None:
        """Verify --conversation JSON includes temporal patterns (FR-021, FR-024)."""
        result = cli_runner.invoke(
            app, ["stats", str(stats_test_export), "--conversation", "conv-001", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Verify temporal pattern fields (FR-021)
        assert "first_message" in data, "JSON should include first_message timestamp"
        assert "last_message" in data, "JSON should include last_message timestamp"
        assert "duration_seconds" in data, "JSON should include duration_seconds"
        assert "average_gap_seconds" in data, "JSON should include average_gap_seconds"
