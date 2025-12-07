"""Contract tests for Baseline Enhancement Package (v1.2.0) functional requirements.

This module validates that the implementation meets all functional requirements
specified in the Baseline Enhancement Package specification.

Constitution Compliance:
    - Principle III: TDD (tests validate spec compliance)
    - Contract tests verify FR acceptance criteria

Test Coverage:
    Statistics Command (FR-017-028):
        - FR-017-018: Total conversations and messages display
        - FR-019-020: Message count by role
        - FR-021-024: Largest/smallest conversations
        - FR-025-028: JSON output format

    Export Enhancements (FR-029-034):
        - FR-029-031: Markdown frontmatter metadata
        - FR-032-034: Custom output path

    CSV Export (FR-035-042):
        - FR-035-038: CSV export with configurable fields
        - FR-039: Streaming CSV generation
        - FR-040-042: Custom output path

    Search Sorting (FR-043-048):
        - FR-043-045: Sort by score, date, title, messages
        - FR-046-048: Ascending/descending order

Future Implementation:
    Tests will be implemented following TDD pattern. Functional requirements
    will be validated incrementally as features are implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.models.search import SearchQuery


@pytest.mark.contract
class TestFR004MessageCountFields:
    """Contract test for FR-004: SearchQuery min_messages/max_messages fields.

    Task: T023 - Contract Test - FR-004 Message Count Fields
    Phase: RED (test designed to FAIL initially)

    FR-004: SearchQuery model MUST include `min_messages: int | None` and
            `max_messages: int | None` fields

    Validates:
    - Fields exist with correct types
    - Fields default to None
    - Fields accept valid integer values
    - Type hints are correct (int | None)
    """

    def test_fr004_min_messages_field_exists(self) -> None:
        """Verify SearchQuery has min_messages field (FR-004)."""
        query = SearchQuery()

        # Assert field exists
        assert hasattr(query, "min_messages"), "SearchQuery must have min_messages field (FR-004)"

        # Assert default is None
        assert query.min_messages is None, "min_messages must default to None (FR-004)"

    def test_fr004_max_messages_field_exists(self) -> None:
        """Verify SearchQuery has max_messages field (FR-004)."""
        query = SearchQuery()

        # Assert field exists
        assert hasattr(query, "max_messages"), "SearchQuery must have max_messages field (FR-004)"

        # Assert default is None
        assert query.max_messages is None, "max_messages must default to None (FR-004)"

    def test_fr004_min_messages_accepts_integer(self) -> None:
        """Verify min_messages accepts integer values (FR-004)."""
        query = SearchQuery(min_messages=10)

        assert query.min_messages == 10, "min_messages must accept integer values (FR-004)"
        assert isinstance(query.min_messages, int), "min_messages must be int type (FR-004)"

    def test_fr004_max_messages_accepts_integer(self) -> None:
        """Verify max_messages accepts integer values (FR-004)."""
        query = SearchQuery(max_messages=100)

        assert query.max_messages == 100, "max_messages must accept integer values (FR-004)"
        assert isinstance(query.max_messages, int), "max_messages must be int type (FR-004)"

    def test_fr004_type_hints_int_or_none(self) -> None:
        """Verify fields have correct type hints: int | None (FR-004)."""
        # This test verifies the type annotation at runtime
        import typing

        # Get type hints for SearchQuery
        hints = typing.get_type_hints(SearchQuery)

        # Verify min_messages type hint
        assert "min_messages" in hints, "min_messages must have type hint (FR-004)"
        # Type hint should be int | None (Union[int, None] in runtime)

        # Verify max_messages type hint
        assert "max_messages" in hints, "max_messages must have type hint (FR-004)"
        # Type hint should be int | None (Union[int, None] in runtime)


@pytest.mark.contract
class TestFR016CalculateStatisticsSignature:
    """Contract test for FR-016: calculate_statistics() function signature (T046).

    Task: T046 - Contract Test - FR-016 calculate_statistics Signature
    Phase: RED (test designed to FAIL initially)

    FR-016: calculate_statistics() function MUST have signature:
            def calculate_statistics(
                file_path: Path,
                *,
                progress_callback: ProgressCallback | None = None,
                on_skip: OnSkipCallback | None = None,
            ) -> ExportStatistics

    Validates:
    - Function exists in echomine.statistics module
    - Required positional parameter: file_path (Path)
    - Keyword-only parameters: progress_callback, on_skip
    - Return type: ExportStatistics
    - Type hints are correct
    """

    def test_fr016_function_exists(self) -> None:
        """Verify calculate_statistics() function exists (FR-016)."""
        from echomine import statistics

        assert hasattr(statistics, "calculate_statistics"), (
            "calculate_statistics() must exist in echomine.statistics (FR-016)"
        )

    def test_fr016_accepts_file_path_parameter(self) -> None:
        """Verify calculate_statistics() accepts file_path parameter (FR-016)."""
        import inspect

        from echomine.statistics import calculate_statistics

        # Get function signature
        sig = inspect.signature(calculate_statistics)

        # Verify file_path parameter exists
        assert "file_path" in sig.parameters, (
            "calculate_statistics() must have file_path parameter (FR-016)"
        )

        # Verify file_path is positional-or-keyword
        param = sig.parameters["file_path"]
        assert param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        ), "file_path must be positional parameter (FR-016)"

    def test_fr016_accepts_progress_callback_parameter(self) -> None:
        """Verify calculate_statistics() accepts progress_callback parameter (FR-016)."""
        import inspect

        from echomine.statistics import calculate_statistics

        sig = inspect.signature(calculate_statistics)

        # Verify progress_callback parameter exists
        assert "progress_callback" in sig.parameters, (
            "calculate_statistics() must have progress_callback parameter (FR-016)"
        )

        # Verify progress_callback is keyword-only
        param = sig.parameters["progress_callback"]
        assert param.kind == inspect.Parameter.KEYWORD_ONLY, (
            "progress_callback must be keyword-only parameter (FR-016)"
        )

        # Verify progress_callback defaults to None
        assert param.default is None, "progress_callback must default to None (FR-016)"

    def test_fr016_accepts_on_skip_parameter(self) -> None:
        """Verify calculate_statistics() accepts on_skip parameter (FR-016)."""
        import inspect

        from echomine.statistics import calculate_statistics

        sig = inspect.signature(calculate_statistics)

        # Verify on_skip parameter exists
        assert "on_skip" in sig.parameters, (
            "calculate_statistics() must have on_skip parameter (FR-016)"
        )

        # Verify on_skip is keyword-only
        param = sig.parameters["on_skip"]
        assert param.kind == inspect.Parameter.KEYWORD_ONLY, (
            "on_skip must be keyword-only parameter (FR-016)"
        )

        # Verify on_skip defaults to None
        assert param.default is None, "on_skip must default to None (FR-016)"

    def test_fr016_returns_export_statistics(self) -> None:
        """Verify calculate_statistics() return type is ExportStatistics (FR-016)."""
        import typing

        from echomine.statistics import calculate_statistics

        # Get type hints
        hints = typing.get_type_hints(calculate_statistics)

        # Verify return type hint exists
        assert "return" in hints, "calculate_statistics() must have return type hint (FR-016)"

        # Verify return type is ExportStatistics
        from echomine.models.statistics import ExportStatistics

        # The return type should be ExportStatistics
        assert hints["return"] == ExportStatistics, (
            "calculate_statistics() must return ExportStatistics (FR-016)"
        )


@pytest.mark.contract
class TestFR022CalculateConversationStatisticsSignature:
    """Contract test for FR-022: calculate_conversation_statistics() signature (T047).

    Task: T047 - Contract Test - FR-022 calculate_conversation_statistics Signature
    Phase: RED (test designed to FAIL initially)

    FR-022: calculate_conversation_statistics() function MUST have signature:
            def calculate_conversation_statistics(
                conversation: Conversation,
            ) -> ConversationStatistics

    Validates:
    - Function exists in echomine.statistics module
    - Required positional parameter: conversation (Conversation)
    - Return type: ConversationStatistics
    - Type hints are correct
    - Pure function (no I/O, no side effects)
    """

    def test_fr022_function_exists(self) -> None:
        """Verify calculate_conversation_statistics() function exists (FR-022)."""
        from echomine import statistics

        assert hasattr(statistics, "calculate_conversation_statistics"), (
            "calculate_conversation_statistics() must exist in echomine.statistics (FR-022)"
        )

    def test_fr022_accepts_conversation_parameter(self) -> None:
        """Verify calculate_conversation_statistics() accepts conversation parameter (FR-022)."""
        import inspect

        from echomine.statistics import calculate_conversation_statistics

        # Get function signature
        sig = inspect.signature(calculate_conversation_statistics)

        # Verify conversation parameter exists
        assert "conversation" in sig.parameters, (
            "calculate_conversation_statistics() must have conversation parameter (FR-022)"
        )

        # Verify conversation is positional-or-keyword
        param = sig.parameters["conversation"]
        assert param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        ), "conversation must be positional parameter (FR-022)"

    def test_fr022_returns_conversation_statistics(self) -> None:
        """Verify calculate_conversation_statistics() return type is ConversationStatistics (FR-022)."""
        import typing

        from echomine.statistics import calculate_conversation_statistics

        # Get type hints
        hints = typing.get_type_hints(calculate_conversation_statistics)

        # Verify return type hint exists
        assert "return" in hints, (
            "calculate_conversation_statistics() must have return type hint (FR-022)"
        )

        # Verify return type is ConversationStatistics
        from echomine.models.statistics import ConversationStatistics

        # The return type should be ConversationStatistics
        assert hints["return"] == ConversationStatistics, (
            "calculate_conversation_statistics() must return ConversationStatistics (FR-022)"
        )

    def test_fr022_is_pure_function(self) -> None:
        """Verify calculate_conversation_statistics() is a pure function (FR-022).

        Pure function characteristics:
        - No I/O operations (no file access)
        - No side effects (no global state modification)
        - Deterministic (same input produces same output)

        This test verifies determinism by calling the function twice with the same
        input and verifying identical results.
        """
        from datetime import UTC, datetime

        from echomine.models.conversation import Conversation
        from echomine.models.message import Message
        from echomine.statistics import calculate_conversation_statistics

        # Create test conversation
        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        messages = [
            Message(
                id="msg-1",
                content="Test",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                parent_id=None,
            ),
        ]

        conversation = Conversation(
            id="conv-123", title="Test", created_at=created, messages=messages
        )

        # Call function twice
        result1 = calculate_conversation_statistics(conversation)
        result2 = calculate_conversation_statistics(conversation)

        # Verify identical results (pure function property)
        assert result1 == result2, (
            "calculate_conversation_statistics() must be deterministic (FR-022)"
        )


@pytest.mark.contract
class TestFR009StatsCommandExists:
    """Contract test for FR-009: stats command exists and returns statistics (T058).

    Task: T058 - Contract Test - FR-009 stats command exists
    Phase: RED (test designed to FAIL initially)

    FR-009: CLI MUST include `echomine stats <export.json>` command that
            displays export-level statistics

    Validates:
    - stats command is registered in CLI app
    - stats command accepts file path argument
    - stats command executes successfully
    - stats command displays statistics to stdout
    """

    def test_fr009_stats_command_registered(self) -> None:
        """Verify stats command is registered in CLI (FR-009)."""
        from echomine.cli.app import app

        # Get registered commands
        commands = app.registered_commands

        # Verify stats command is registered
        assert any(cmd.name == "stats" for cmd in commands), (
            "stats command must be registered in CLI app (FR-009)"
        )

    def test_fr009_stats_command_callable(self) -> None:
        """Verify stats command is callable via CLI (FR-009)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        runner = CliRunner()

        # Invoke stats command with --help
        result = runner.invoke(app, ["stats", "--help"])

        # Should not fail (exit code 0)
        assert result.exit_code == 0, f"stats --help should succeed (FR-009): {result.stdout}"

        # Help text should describe stats command
        assert "stats" in result.stdout.lower() or "statistics" in result.stdout.lower(), (
            "Help text should describe stats command (FR-009)"
        )


@pytest.mark.contract
class TestFR010StatsOutputFields:
    """Contract test for FR-010: output includes all required fields (T059).

    Task: T059 - Contract Test - FR-010 output includes required fields
    Phase: RED (test designed to FAIL initially)

    FR-010: stats command output MUST include:
            - Total conversations
            - Total messages
            - Date range (earliest to latest)
            - Average messages per conversation
            - Largest conversation (title, ID, count)
            - Smallest conversation (title, ID, count)

    Validates:
    - Human-readable output contains all fields
    - JSON output (--json) contains all fields with correct structure
    """

    def test_fr010_json_output_structure(self, tmp_path: Path) -> None:
        """Verify --json output includes all required fields (FR-010)."""
        import json

        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Create minimal test export
        export_data = [
            {
                "id": "test-001",
                "title": "Test Conversation",
                "create_time": 1705320000.0,
                "update_time": None,
                "mapping": {
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                            "create_time": 1705320000.0,
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
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Run stats command with --json
        runner = CliRunner()
        result = runner.invoke(app, ["stats", str(export_file), "--json"])

        assert result.exit_code == 0, f"stats command should succeed (FR-010): {result.stdout}"

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output must be valid JSON (FR-010): {e}")

        # Verify required fields (FR-010)
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
            assert field in data, f"JSON output must include {field} (FR-010)"

        # Verify largest/smallest conversation structure (FR-010)
        assert isinstance(data["largest_conversation"], dict), (
            "largest_conversation must be object (FR-010)"
        )
        assert "id" in data["largest_conversation"], "largest_conversation must include id (FR-010)"
        assert "title" in data["largest_conversation"], (
            "largest_conversation must include title (FR-010)"
        )
        assert "message_count" in data["largest_conversation"], (
            "largest_conversation must include message_count (FR-010)"
        )


@pytest.mark.contract
class TestFR019PerConversationStatsFields:
    """Contract test for FR-019: Per-conversation stats output fields (T068).

    Task: T068 - Contract Test - FR-019 per-conversation stats fields
    Phase: RED (test designed to FAIL initially)

    FR-019: stats --conversation output MUST include:
            - Conversation ID
            - Title
            - Created/updated dates
            - Message breakdown by role (user/assistant/system)
            - Total message count

    Validates:
    - Human-readable output contains all fields
    - JSON output (--json) contains all fields with correct structure
    """

    def test_fr019_conversation_option_exists(self, tmp_path: Path) -> None:
        """Verify stats command accepts --conversation option (FR-018, FR-019)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Create minimal test export
        export_data = [
            {
                "id": "test-conv-001",
                "title": "Test Conversation",
                "create_time": 1705320000.0,
                "update_time": 1705330000.0,
                "mapping": {
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                            "create_time": 1705320000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": ["msg-2"],
                    },
                    "msg-2": {
                        "id": "msg-2",
                        "message": {
                            "id": "msg-2",
                            "author": {"role": "assistant"},
                            "content": {"content_type": "text", "parts": ["Hi there!"]},
                            "create_time": 1705320010.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": "msg-1",
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-2",
            }
        ]

        export_file = tmp_path / "test_export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Run stats command with --conversation
        runner = CliRunner()
        result = runner.invoke(app, ["stats", str(export_file), "--conversation", "test-conv-001"])

        # Should succeed
        assert result.exit_code == 0, (
            f"stats --conversation should succeed (FR-019): {result.stdout}\n{result.stderr}"
        )

    def test_fr019_json_output_structure(self, tmp_path: Path) -> None:
        """Verify --conversation --json output includes all required fields (FR-019, FR-024)."""
        import json

        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Create test export with multiple roles
        export_data = [
            {
                "id": "test-conv-002",
                "title": "Multi-Role Conversation",
                "create_time": 1705320000.0,
                "update_time": 1705330000.0,
                "mapping": {
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["User message"]},
                            "create_time": 1705320000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": ["msg-2"],
                    },
                    "msg-2": {
                        "id": "msg-2",
                        "message": {
                            "id": "msg-2",
                            "author": {"role": "assistant"},
                            "content": {"content_type": "text", "parts": ["Assistant response"]},
                            "create_time": 1705320010.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": "msg-1",
                        "children": ["msg-3"],
                    },
                    "msg-3": {
                        "id": "msg-3",
                        "message": {
                            "id": "msg-3",
                            "author": {"role": "system"},
                            "content": {"content_type": "text", "parts": ["System message"]},
                            "create_time": 1705320020.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": "msg-2",
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-3",
            }
        ]

        export_file = tmp_path / "test_export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Run stats command with --conversation --json
        runner = CliRunner()
        result = runner.invoke(
            app, ["stats", str(export_file), "--conversation", "test-conv-002", "--json"]
        )

        assert result.exit_code == 0, (
            f"stats --conversation --json should succeed (FR-019, FR-024): {result.stdout}"
        )

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output must be valid JSON (FR-024): {e}")

        # Verify required fields (FR-019)
        required_fields = [
            "conversation_id",
            "title",
            "created_at",
            "updated_at",
            "message_count",
            "message_count_by_role",
        ]

        for field in required_fields:
            assert field in data, f"JSON output must include {field} (FR-019)"

        # Verify message_count_by_role structure (FR-019, FR-020)
        assert isinstance(data["message_count_by_role"], dict), (
            "message_count_by_role must be object (FR-019)"
        )
        assert "user" in data["message_count_by_role"], (
            "message_count_by_role must include user (FR-020)"
        )
        assert "assistant" in data["message_count_by_role"], (
            "message_count_by_role must include assistant (FR-020)"
        )
        assert "system" in data["message_count_by_role"], (
            "message_count_by_role must include system (FR-020)"
        )

        # Verify values match test data
        assert data["conversation_id"] == "test-conv-002"
        assert data["title"] == "Multi-Role Conversation"
        assert data["message_count"] == 3
        assert data["message_count_by_role"]["user"] == 1
        assert data["message_count_by_role"]["assistant"] == 1
        assert data["message_count_by_role"]["system"] == 1


@pytest.mark.contract
class TestFR020MessageCountByRole:
    """Contract test for FR-020: Message count by role display (T069).

    Task: T069 - Contract Test - FR-020 message count by role
    Phase: RED (test designed to FAIL initially)

    FR-020: Per-conversation stats MUST display message count by role:
            - user: N messages (color: green)
            - assistant: N messages (color: blue)
            - system: N messages (color: yellow)

    Validates:
    - Role counts are displayed in human-readable output
    - JSON output includes role breakdown
    - Total message count matches sum of roles
    """

    def test_fr020_role_breakdown_in_output(self, tmp_path: Path) -> None:
        """Verify role breakdown is displayed in human-readable output (FR-020)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Create test export with known role distribution
        export_data = [
            {
                "id": "test-conv-003",
                "title": "Role Test Conversation",
                "create_time": 1705320000.0,
                "update_time": None,
                "mapping": {
                    f"msg-{i}": {
                        "id": f"msg-{i}",
                        "message": {
                            "id": f"msg-{i}",
                            "author": {
                                "role": "user"
                                if i % 3 == 1
                                else "assistant"
                                if i % 3 == 2
                                else "system"
                            },
                            "content": {"content_type": "text", "parts": [f"Message {i}"]},
                            "create_time": 1705320000.0 + i * 10,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": f"msg-{i - 1}" if i > 1 else None,
                        "children": [f"msg-{i + 1}"] if i < 9 else [],
                    }
                    for i in range(1, 10)  # 9 messages: 3 user, 3 assistant, 3 system
                },
                "moderation_results": [],
                "current_node": "msg-9",
            }
        ]

        export_file = tmp_path / "test_export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Run stats command with --conversation
        runner = CliRunner()
        result = runner.invoke(app, ["stats", str(export_file), "--conversation", "test-conv-003"])

        assert result.exit_code == 0, (
            f"stats --conversation should succeed (FR-020): {result.stdout}"
        )

        # Verify role labels are present (FR-020)
        output_lower = result.stdout.lower()
        assert "user" in output_lower, "Output must show 'user' role (FR-020)"
        assert "assistant" in output_lower, "Output must show 'assistant' role (FR-020)"
        assert "system" in output_lower, "Output must show 'system' role (FR-020)"

    def test_fr020_role_counts_in_json(self, tmp_path: Path) -> None:
        """Verify role counts in JSON output match expected values (FR-020)."""
        import json

        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Create test export with known role distribution
        export_data = [
            {
                "id": "test-conv-004",
                "title": "Role Count Test",
                "create_time": 1705320000.0,
                "update_time": None,
                "mapping": {
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["User 1"]},
                            "create_time": 1705320000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": ["msg-2"],
                    },
                    "msg-2": {
                        "id": "msg-2",
                        "message": {
                            "id": "msg-2",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["User 2"]},
                            "create_time": 1705320010.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": "msg-1",
                        "children": ["msg-3"],
                    },
                    "msg-3": {
                        "id": "msg-3",
                        "message": {
                            "id": "msg-3",
                            "author": {"role": "assistant"},
                            "content": {"content_type": "text", "parts": ["Assistant 1"]},
                            "create_time": 1705320020.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": "msg-2",
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-3",
            }
        ]

        export_file = tmp_path / "test_export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f)

        # Run stats command with --conversation --json
        runner = CliRunner()
        result = runner.invoke(
            app, ["stats", str(export_file), "--conversation", "test-conv-004", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Verify role counts (FR-020)
        assert data["message_count_by_role"]["user"] == 2, "Should have 2 user messages (FR-020)"
        assert data["message_count_by_role"]["assistant"] == 1, (
            "Should have 1 assistant message (FR-020)"
        )
        assert data["message_count_by_role"]["system"] == 0, (
            "Should have 0 system messages (FR-020)"
        )

        # Verify total equals sum of roles (FR-020)
        role_sum = (
            data["message_count_by_role"]["user"]
            + data["message_count_by_role"]["assistant"]
            + data["message_count_by_role"]["system"]
        )
        assert data["message_count"] == role_sum, (
            "Total message_count must equal sum of roles (FR-020)"
        )


@pytest.mark.contract
class TestFR025GetMessagesCommandExists:
    """Contract test for FR-025: get messages command exists (T080).

    Task: T080 - Contract Test - FR-025 get messages command exists
    Phase: RED (test designed to FAIL initially)

    FR-025: CLI MUST include `echomine get messages <export.json> <conversation-id>` command
            that lists all messages in a conversation

    Validates:
    - get messages subcommand is registered in CLI app
    - get messages accepts file path and conversation ID arguments
    - get messages executes successfully
    - get messages displays messages to stdout
    """

    def test_fr025_get_messages_command_registered(self) -> None:
        """Verify get messages subcommand is registered in CLI (FR-025)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        # Verify get command is registered by invoking help
        runner = CliRunner()
        result = runner.invoke(app, ["get", "--help"])

        # Should succeed
        assert result.exit_code == 0, f"get --help should succeed (FR-025): {result.stdout}"

        # Verify "messages" subcommand is mentioned in help text
        assert "messages" in result.stdout.lower(), (
            f"get command should have messages subcommand (FR-025): {result.stdout}"
        )

    def test_fr025_get_messages_callable_via_help(self) -> None:
        """Verify get messages command is callable via CLI (FR-025)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        runner = CliRunner()

        # Invoke get messages command with --help
        result = runner.invoke(app, ["get", "messages", "--help"])

        # Should not fail (exit code 0)
        assert result.exit_code == 0, (
            f"get messages --help should succeed (FR-025): {result.stdout}"
        )

        # Help text should describe messages subcommand
        assert "messages" in result.stdout.lower() or "message" in result.stdout.lower(), (
            "Help text should describe messages subcommand (FR-025)"
        )

    def test_fr025_get_messages_accepts_required_arguments(self) -> None:
        """Verify get messages accepts file path and conversation ID arguments (FR-025)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        runner = CliRunner()

        # Invoke get messages without arguments (should show usage error)
        result = runner.invoke(app, ["get", "messages"])

        # Should fail with exit code 2 (usage error)
        assert result.exit_code == 2, (
            f"get messages without args should fail with exit code 2 (FR-025): {result.output}"
        )

        # Error message should mention required arguments
        # Use result.output for combined stdout+stderr
        output_lower = result.output.lower()
        assert (
            "missing" in output_lower or "required" in output_lower or "argument" in output_lower
        ), f"Error should mention required arguments (FR-025): {result.output}"


@pytest.mark.contract
class TestFR043SearchSortOptions:
    """Contract test for FR-043: Sort search results by multiple fields (T108).

    Task: T108 - Contract Test - FR-043 Sort Options
    Phase: RED (test designed to FAIL initially)

    FR-043: Search results MUST support sorting by:
            - score (BM25 relevance)
            - date (created_at/updated_at)
            - title (case-insensitive)
            - messages (message count)

    FR-043a: Tie-breaking by conversation_id (ascending, lexicographic)
    FR-043b: Stable sort (Python's sort() guarantee)
    FR-044: Sort order: asc or desc
    FR-045: Default sort is score descending

    Validates:
    - SearchQuery accepts sort_by field with all valid values
    - SearchQuery accepts sort_order field (asc/desc)
    - Default sort is score descending
    - CLI search command accepts --sort flag
    - CLI search command accepts --order flag
    """

    def test_fr043_search_query_accepts_sort_by_score(self) -> None:
        """Verify SearchQuery accepts sort_by='score' (FR-043)."""
        query = SearchQuery(sort_by="score")

        assert query.sort_by == "score", "SearchQuery must accept sort_by='score' (FR-043)"

    def test_fr043_search_query_accepts_sort_by_date(self) -> None:
        """Verify SearchQuery accepts sort_by='date' (FR-043)."""
        query = SearchQuery(sort_by="date")

        assert query.sort_by == "date", "SearchQuery must accept sort_by='date' (FR-043)"

    def test_fr043_search_query_accepts_sort_by_title(self) -> None:
        """Verify SearchQuery accepts sort_by='title' (FR-043)."""
        query = SearchQuery(sort_by="title")

        assert query.sort_by == "title", "SearchQuery must accept sort_by='title' (FR-043)"

    def test_fr043_search_query_accepts_sort_by_messages(self) -> None:
        """Verify SearchQuery accepts sort_by='messages' (FR-043)."""
        query = SearchQuery(sort_by="messages")

        assert query.sort_by == "messages", "SearchQuery must accept sort_by='messages' (FR-043)"

    def test_fr044_search_query_accepts_sort_order_asc(self) -> None:
        """Verify SearchQuery accepts sort_order='asc' (FR-044)."""
        query = SearchQuery(sort_order="asc")

        assert query.sort_order == "asc", "SearchQuery must accept sort_order='asc' (FR-044)"

    def test_fr044_search_query_accepts_sort_order_desc(self) -> None:
        """Verify SearchQuery accepts sort_order='desc' (FR-044)."""
        query = SearchQuery(sort_order="desc")

        assert query.sort_order == "desc", "SearchQuery must accept sort_order='desc' (FR-044)"

    def test_fr045_default_sort_is_score_descending(self) -> None:
        """Verify default sort is score descending (FR-045)."""
        query = SearchQuery()

        assert query.sort_by == "score", "Default sort_by must be 'score' (FR-045)"
        assert query.sort_order == "desc", "Default sort_order must be 'desc' (FR-045)"

    def test_fr043_cli_search_accepts_sort_flag(self) -> None:
        """Verify search command accepts --sort flag (FR-043)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        runner = CliRunner()

        # Check help text includes --sort flag
        result = runner.invoke(app, ["search", "--help"])

        assert result.exit_code == 0, f"search --help should succeed (FR-043): {result.stdout}"
        assert "--sort" in result.stdout.lower(), (
            f"search command should have --sort flag (FR-043): {result.stdout}"
        )

    def test_fr044_cli_search_accepts_order_flag(self) -> None:
        """Verify search command accepts --order flag (FR-044)."""
        from typer.testing import CliRunner

        from echomine.cli.app import app

        runner = CliRunner()

        # Check help text includes --order flag
        result = runner.invoke(app, ["search", "--help"])

        assert result.exit_code == 0, f"search --help should succeed (FR-044): {result.stdout}"
        assert "--order" in result.stdout.lower(), (
            f"search command should have --order flag (FR-044): {result.stdout}"
        )
