"""Comprehensive unit tests for CLI commands using CliRunner.

This module provides complete test coverage for all CLI commands using
Typer's CliRunner, which runs commands in-process and counts for coverage.

CRITICAL: DO NOT use subprocess.run() - it runs in a separate process and
does not count for pytest-cov coverage.

Coverage Targets:
    - src/echomine/cli/app.py: 0% → 80%+ (lines 28-137)
    - src/echomine/cli/commands/list.py: 59% → 80%+ (lines 118-203)
    - src/echomine/cli/commands/search.py: 12% → 80%+ (lines 91-464)
    - src/echomine/cli/commands/export.py: 29% → 80%+ (lines 79-285)
    - src/echomine/cli/commands/get.py: 49% → 80%+ (lines 332-574)

Test Strategy:
    - AAA pattern (Arrange, Act, Assert)
    - Test both success and error paths
    - Validate exit codes (0=success, 1=error, 2=invalid args)
    - Validate stdout/stderr separation (CHK031)
    - Test all format options (text/json)
    - Parameterized tests for multiple scenarios

Constitution Compliance:
    - Principle III: Test-driven development
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2/130
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from echomine import __version__
from echomine.cli.app import app

# Create CliRunner instance for all tests
runner = CliRunner()


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_export(tmp_path: Path) -> Path:
    """Create a sample OpenAI export JSON file for testing.

    Returns:
        Path to temporary export file with 3 conversations
    """
    data = [
        {
            "id": "conv-001",
            "title": "Python AsyncIO Tutorial",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-001-1": {
                    "id": "msg-001-1",
                    "message": {
                        "id": "msg-001-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Explain Python asyncio"]},
                        "create_time": 1700000000.0,
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
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "AsyncIO is Python's library for asynchronous programming."
                            ],
                        },
                        "create_time": 1700000010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-001-2",
        },
        {
            "id": "conv-002",
            "title": "Algorithm Design Patterns",
            "create_time": 1700100000.0,
            "update_time": 1700101000.0,
            "mapping": {
                "msg-002-1": {
                    "id": "msg-002-1",
                    "message": {
                        "id": "msg-002-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["What are common algorithm design patterns?"],
                        },
                        "create_time": 1700100000.0,
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
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Common patterns include divide-and-conquer, dynamic programming."
                            ],
                        },
                        "create_time": 1700100010.0,
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
            "title": "Debug Session",
            "create_time": 1700200000.0,
            "update_time": 1700201000.0,
            "mapping": {
                "msg-003-1": {
                    "id": "msg-003-1",
                    "message": {
                        "id": "msg-003-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Help debug my code"]},
                        "create_time": 1700200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-003-2"],
                },
                "msg-003-2": {
                    "id": "msg-003-2",
                    "message": {
                        "id": "msg-003-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["I can help with that."]},
                        "create_time": 1700200010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-003-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-003-2",
        },
    ]

    file = tmp_path / "export.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    return file


@pytest.fixture
def malformed_export(tmp_path: Path) -> Path:
    """Create a malformed JSON file for error testing.

    Returns:
        Path to temporary file with invalid JSON syntax
    """
    file = tmp_path / "malformed.json"
    file.write_text("{invalid json syntax", encoding="utf-8")
    return file


@pytest.fixture
def empty_export(tmp_path: Path) -> Path:
    """Create an empty export (empty array) for edge case testing.

    Returns:
        Path to temporary file with empty conversation array
    """
    file = tmp_path / "empty.json"
    file.write_text("[]", encoding="utf-8")
    return file


# ============================================================================
# Test App Entry Point (app.py)
# ============================================================================


class TestAppEntryPoint:
    """Test main application entry point, version, and help flags.

    Coverage Target: src/echomine/cli/app.py lines 28-137
    """

    def test_version_flag_displays_version(self) -> None:
        """Test --version flag displays version and exits with code 0.

        Validates:
        - app.py line 89-91: version callback
        - Exit code 0
        - Version string format
        """
        # Act
        result = runner.invoke(app, ["--version"])

        # Assert: Exit code 0
        assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}"

        # Assert: Version string in output
        assert "echomine" in result.stdout.lower()
        assert "version" in result.stdout.lower()
        assert __version__ in result.stdout

    def test_version_short_flag_works(self) -> None:
        """Test -v short flag also displays version.

        Validates:
        - app.py line 82: -v short flag alias
        """
        # Act
        result = runner.invoke(app, ["-v"])

        # Assert: Same as --version
        assert result.exit_code == 0
        assert "echomine" in result.stdout.lower()
        assert __version__ in result.stdout

    def test_help_flag_displays_usage(self) -> None:
        """Test --help flag displays usage information.

        Validates:
        - app.py line 94-96: callback shows help
        - Exit code 0
        - Help text contains command list
        """
        # Act
        result = runner.invoke(app, ["--help"])

        # Assert: Exit code 0
        assert result.exit_code == 0

        # Assert: Help text mentions commands
        assert len(result.stdout) > 100
        assert "list" in result.stdout.lower()
        assert "search" in result.stdout.lower()
        assert "export" in result.stdout.lower()
        assert "get" in result.stdout.lower()

    def test_no_command_displays_help(self) -> None:
        """Test running with no command shows help.

        Validates:
        - app.py line 94-96: no subcommand shows help
        - Exit code 0 (help, not error)
        """
        # Act
        result = runner.invoke(app, [])

        # Assert: Exit code 0 (help is not an error)
        assert result.exit_code == 0
        assert "echomine" in result.stdout.lower()

    def test_invalid_command_exits_with_error(self) -> None:
        """Test invalid command name exits with error code 2.

        Validates:
        - Typer handles invalid commands
        - Exit code 2 (invalid argument)
        """
        # Act
        result = runner.invoke(app, ["invalid-command-name"])

        # Assert: Exit code 2
        assert result.exit_code == 2

    def test_version_takes_precedence_over_commands(self) -> None:
        """Test --version works even with command specified.

        Validates:
        - app.py line 84: is_eager=True on version flag
        """
        # Act
        result = runner.invoke(app, ["--version", "list"])

        # Assert: Version shown, command not executed
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()


# ============================================================================
# Test List Command
# ============================================================================


class TestListCommand:
    """Test list command functionality.

    Coverage Target: src/echomine/cli/commands/list.py lines 118-203
    """

    def test_list_success_text_format(self, sample_export: Path) -> None:
        """Test listing conversations in default text format.

        Validates:
        - list.py: stream_conversations, format_text_table
        - Exit code 0
        - Text output contains conversation titles
        """
        # Act
        result = runner.invoke(app, ["list", str(sample_export)])

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Output contains conversation data
        assert "Python AsyncIO Tutorial" in result.stdout
        assert "Algorithm Design Patterns" in result.stdout
        assert "Debug Session" in result.stdout

    def test_list_success_json_format(self, sample_export: Path) -> None:
        """Test listing conversations in JSON format.

        Validates:
        - list.py: format_json
        - Valid JSON output
        """
        # Act
        result = runner.invoke(app, ["list", str(sample_export), "--format", "json"])

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["title"] == "Debug Session"  # Newest first (FR-440)

    def test_list_with_limit(self, sample_export: Path) -> None:
        """Test list command with --limit option (FR-443).

        Validates:
        - list.py lines 140-141: limit application
        """
        # Act
        result = runner.invoke(app, ["list", str(sample_export), "--limit", "2"])

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Only 2 conversations in output
        data = json.loads(
            runner.invoke(
                app, ["list", str(sample_export), "--limit", "2", "--format", "json"]
            ).stdout
        )
        assert len(data) == 2

    def test_list_file_not_found(self) -> None:
        """Test list with non-existent file exits with code 1.

        Validates:
        - list.py lines 125-130: file existence check
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["list", "/nonexistent/file.json"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_list_invalid_format(self, sample_export: Path) -> None:
        """Test list with invalid format option.

        Validates:
        - list.py lines 117-122: format validation
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["list", str(sample_export), "--format", "xml"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "invalid format" in result.output.lower()

    def test_list_invalid_limit_negative(self, sample_export: Path) -> None:
        """Test list with negative limit value.

        Validates:
        - list.py lines 107-112: limit validation
        - Exit code 2 (invalid argument)
        """
        # Act
        result = runner.invoke(app, ["list", str(sample_export), "--limit", "0"])

        # Assert: Exit code 2
        assert result.exit_code == 2

    def test_list_malformed_json(self, malformed_export: Path) -> None:
        """Test list with malformed JSON file.

        Validates:
        - list.py lines 173-179: ParseError handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["list", str(malformed_export)])

        # Assert: Exit code 1
        assert result.exit_code == 1

    def test_list_empty_export(self, empty_export: Path) -> None:
        """Test list with empty export file (no conversations).

        Validates:
        - Graceful handling of empty results
        - Exit code 0 (not an error)
        """
        # Act
        result = runner.invoke(app, ["list", str(empty_export)])

        # Assert: Success (empty result is not an error)
        assert result.exit_code == 0


# ============================================================================
# Test Search Command
# ============================================================================


class TestSearchCommand:
    """Test search command functionality.

    Coverage Target: src/echomine/cli/commands/search.py lines 91-464
    """

    def test_search_by_keywords_success(self, sample_export: Path) -> None:
        """Test search with keywords in text format.

        Validates:
        - search.py: keyword search execution
        - Exit code 0
        - Results contain matching conversations
        """
        # Act
        result = runner.invoke(app, ["search", str(sample_export), "-k", "python"])

        # Assert: Success
        assert result.exit_code == 0
        assert "Python AsyncIO Tutorial" in result.stdout

    def test_search_by_keywords_json_format(self, sample_export: Path) -> None:
        """Test search with JSON output format.

        Validates:
        - search.py lines 384-402: JSON formatting with metadata
        - FR-301-306: JSON output schema
        """
        # Act
        result = runner.invoke(
            app, ["search", str(sample_export), "-k", "python", "--format", "json"]
        )

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Valid JSON with metadata
        data = json.loads(result.stdout)
        assert "results" in data
        assert "metadata" in data
        assert data["metadata"]["total_results"] >= 0

    def test_search_with_json_flag_alias(self, sample_export: Path) -> None:
        """Test search with --json flag (alias for --format json).

        Validates:
        - search.py lines 237-239: --json flag handling
        """
        # Act
        result = runner.invoke(app, ["search", str(sample_export), "-k", "python", "--json"])

        # Assert: JSON output
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "results" in data

    def test_search_by_title_filter(self, sample_export: Path) -> None:
        """Test search with title filter only.

        Validates:
        - search.py: title-only filtering (FR-444)
        """
        # Act
        result = runner.invoke(app, ["search", str(sample_export), "--title", "Debug"])

        # Assert: Success
        assert result.exit_code == 0
        assert "Debug Session" in result.stdout

    def test_search_with_limit(self, sample_export: Path) -> None:
        """Test search with --limit option.

        Validates:
        - search.py lines 359-360: limit application
        """
        # Act
        result = runner.invoke(
            app, ["search", str(sample_export), "-k", "python", "--limit", "1"]
        )

        # Assert: Success
        assert result.exit_code == 0

    def test_search_no_filters_exits_error(self, sample_export: Path) -> None:
        """Test search without any filters exits with code 2.

        Validates:
        - search.py lines 250-255: require at least one filter
        - Exit code 2 (invalid argument)
        """
        # Act
        result = runner.invoke(app, ["search", str(sample_export)])

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "at least one filter" in result.output.lower()

    def test_search_invalid_limit(self, sample_export: Path) -> None:
        """Test search with invalid limit value.

        Validates:
        - search.py lines 258-263: limit validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app, ["search", str(sample_export), "-k", "python", "--limit", "0"]
        )

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "limit must be positive" in result.output.lower()

    def test_search_invalid_date_format(self, sample_export: Path) -> None:
        """Test search with invalid date format.

        Validates:
        - search.py lines 269-277: date parsing and validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app, ["search", str(sample_export), "-k", "python", "--from-date", "invalid-date"]
        )

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "invalid" in result.output.lower()

    def test_search_invalid_date_range(self, sample_export: Path) -> None:
        """Test search with from_date > to_date.

        Validates:
        - search.py lines 290-296: date range validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app,
            [
                "search",
                str(sample_export),
                "-k",
                "python",
                "--from-date",
                "2024-12-31",
                "--to-date",
                "2024-01-01",
            ],
        )

        # Assert: Exit code 2
        assert result.exit_code == 2

    def test_search_file_not_found(self) -> None:
        """Test search with non-existent file.

        Validates:
        - search.py lines 299-304: file existence check
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["search", "/nonexistent.json", "-k", "test"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_search_malformed_json(self, malformed_export: Path) -> None:
        """Test search with malformed JSON file.

        Validates:
        - search.py lines 429-435: ParseError handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["search", str(malformed_export), "-k", "test"])

        # Assert: Exit code 1
        assert result.exit_code == 1

    def test_search_zero_results(self, sample_export: Path) -> None:
        """Test search with no matching results.

        Validates:
        - search.py lines 363-381: zero results handling with suggestions
        - Exit code 0 (zero results is not an error)
        """
        # Act
        result = runner.invoke(app, ["search", str(sample_export), "-k", "nonexistent-keyword"])

        # Assert: Success (zero results is not an error)
        assert result.exit_code == 0

    def test_search_with_quiet_flag(self, sample_export: Path) -> None:
        """Test search with --quiet flag suppresses progress.

        Validates:
        - search.py lines 335-340: progress_callback conditional
        - FR-310: --quiet flag
        """
        # Act
        result = runner.invoke(
            app, ["search", str(sample_export), "-k", "python", "--quiet"]
        )

        # Assert: Success
        assert result.exit_code == 0


# ============================================================================
# Test Export Command
# ============================================================================


class TestExportCommand:
    """Test export command functionality.

    Coverage Target: src/echomine/cli/commands/export.py lines 79-285
    """

    def test_export_by_id_to_stdout(self, sample_export: Path) -> None:
        """Test exporting conversation by ID to stdout.

        Validates:
        - export.py lines 212-231: export by ID
        - Exit code 0
        - Markdown output on stdout
        """
        # Act
        result = runner.invoke(app, ["export", str(sample_export), "conv-001"])

        # Assert: Success
        assert result.exit_code == 0
        assert "# Python AsyncIO Tutorial" in result.stdout
        assert "Explain Python asyncio" in result.stdout

    def test_export_by_id_to_file(self, sample_export: Path, tmp_path: Path) -> None:
        """Test exporting conversation by ID to file.

        Validates:
        - export.py lines 234-248: write to output file
        - File creation
        """
        # Arrange
        output_file = tmp_path / "output.md"

        # Act
        result = runner.invoke(
            app, ["export", str(sample_export), "conv-001", "--output", str(output_file)]
        )

        # Assert: Success
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "# Python AsyncIO Tutorial" in content

    def test_export_by_title(self, sample_export: Path) -> None:
        """Test exporting conversation by title substring.

        Validates:
        - export.py lines 189-207: title lookup
        - FR-016: --title as alternative to ID
        """
        # Act
        result = runner.invoke(
            app, ["export", str(sample_export), "--title", "Algorithm"]
        )

        # Assert: Success
        assert result.exit_code == 0
        assert "Algorithm Design Patterns" in result.stdout

    def test_export_both_id_and_title_error(self, sample_export: Path) -> None:
        """Test export with both ID and --title exits with error.

        Validates:
        - export.py lines 171-176: mutual exclusivity validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app, ["export", str(sample_export), "conv-001", "--title", "Test"]
        )

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "cannot specify both" in result.output.lower()

    def test_export_neither_id_nor_title_error(self, sample_export: Path) -> None:
        """Test export without ID or --title exits with error.

        Validates:
        - export.py lines 178-180: require one identifier
        - Exit code 2
        """
        # Act
        result = runner.invoke(app, ["export", str(sample_export)])

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "must specify" in result.output.lower()

    def test_export_conversation_not_found(self, sample_export: Path) -> None:
        """Test export with non-existent conversation ID.

        Validates:
        - export.py lines 220-223: conversation not found handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["export", str(sample_export), "nonexistent-id"])

        # Assert: Exit code 1
        assert result.exit_code == 1

    def test_export_title_not_found(self, sample_export: Path) -> None:
        """Test export with title that doesn't match any conversation.

        Validates:
        - export.py lines 193-197: no matches for title
        - Exit code 1
        """
        # Act
        result = runner.invoke(
            app, ["export", str(sample_export), "--title", "NonexistentTitle"]
        )

        # Assert: Exit code 1
        assert result.exit_code == 1

    def test_export_file_not_found(self) -> None:
        """Test export with non-existent export file.

        Validates:
        - export.py lines 183-185: file existence check
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["export", "/nonexistent.json", "conv-001"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_export_malformed_json(self, malformed_export: Path) -> None:
        """Test export with malformed JSON file.

        Validates:
        - export.py lines 267-270: JSONDecodeError handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["export", str(malformed_export), "conv-001"])

        # Assert: Exit code 1
        assert result.exit_code == 1


# ============================================================================
# Test Get Conversation Command
# ============================================================================


class TestGetConversationCommand:
    """Test 'get conversation' subcommand functionality.

    Coverage Target: src/echomine/cli/commands/get.py lines 332-403
    """

    def test_get_conversation_table_format(self, sample_export: Path) -> None:
        """Test getting conversation in table format.

        Validates:
        - get.py lines 347-369: get_conversation_by_id + table formatting
        - Exit code 0
        - Table output contains conversation details
        """
        # Act
        result = runner.invoke(
            app, ["get", "conversation", str(sample_export), "conv-001"]
        )

        # Assert: Success
        assert result.exit_code == 0
        assert "Conversation Details" in result.stdout
        assert "Python AsyncIO Tutorial" in result.stdout
        assert "conv-001" in result.stdout

    def test_get_conversation_json_format(self, sample_export: Path) -> None:
        """Test getting conversation in JSON format.

        Validates:
        - get.py lines 366-367: JSON formatting
        """
        # Act
        result = runner.invoke(
            app, ["get", "conversation", str(sample_export), "conv-001", "--format", "json"]
        )

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Valid JSON
        data = json.loads(result.stdout)
        assert data["id"] == "conv-001"
        assert data["title"] == "Python AsyncIO Tutorial"
        assert "messages" in data

    def test_get_conversation_verbose(self, sample_export: Path) -> None:
        """Test getting conversation with --verbose flag.

        Validates:
        - get.py line 369: verbose=True parameter
        - Full message content displayed
        """
        # Act
        result = runner.invoke(
            app, ["get", "conversation", str(sample_export), "conv-001", "--verbose"]
        )

        # Assert: Success
        assert result.exit_code == 0
        assert "Messages:" in result.stdout
        assert "Explain Python asyncio" in result.stdout

    def test_get_conversation_not_found(self, sample_export: Path) -> None:
        """Test getting non-existent conversation.

        Validates:
        - get.py lines 359-363: None result handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(
            app, ["get", "conversation", str(sample_export), "nonexistent-id"]
        )

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_get_conversation_invalid_format(self, sample_export: Path) -> None:
        """Test get conversation with invalid format option.

        Validates:
        - get.py lines 334-339: format validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app,
            ["get", "conversation", str(sample_export), "conv-001", "--format", "xml"],
        )

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "invalid format" in result.output.lower()

    def test_get_conversation_file_not_found(self) -> None:
        """Test get conversation with non-existent file.

        Validates:
        - get.py lines 342-344: file existence check
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["get", "conversation", "/nonexistent.json", "conv-001"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


# ============================================================================
# Test Get Message Command
# ============================================================================


class TestGetMessageCommand:
    """Test 'get message' subcommand functionality.

    Coverage Target: src/echomine/cli/commands/get.py lines 485-574
    """

    def test_get_message_table_format(self, sample_export: Path) -> None:
        """Test getting message in table format.

        Validates:
        - get.py lines 500-540: get_message_by_id + table formatting
        - Exit code 0
        - Table output contains message details
        """
        # Act
        result = runner.invoke(app, ["get", "message", str(sample_export), "msg-001-1"])

        # Assert: Success
        assert result.exit_code == 0
        assert "Message Details" in result.stdout
        assert "msg-001-1" in result.stdout
        assert "Explain Python asyncio" in result.stdout

    def test_get_message_json_format(self, sample_export: Path) -> None:
        """Test getting message in JSON format.

        Validates:
        - get.py lines 537-538: JSON formatting
        """
        # Act
        result = runner.invoke(
            app, ["get", "message", str(sample_export), "msg-001-1", "--format", "json"]
        )

        # Assert: Success
        assert result.exit_code == 0

        # Assert: Valid JSON with message and conversation context
        data = json.loads(result.stdout)
        assert "message" in data
        assert data["message"]["id"] == "msg-001-1"
        assert "conversation" in data
        assert data["conversation"]["id"] == "conv-001"

    def test_get_message_with_conversation_hint(self, sample_export: Path) -> None:
        """Test getting message with --conversation-id hint for faster lookup.

        Validates:
        - get.py lines 511-513: conversation_id parameter usage
        """
        # Act
        result = runner.invoke(
            app,
            [
                "get",
                "message",
                str(sample_export),
                "msg-001-1",
                "--conversation-id",
                "conv-001",
            ],
        )

        # Assert: Success
        assert result.exit_code == 0
        assert "msg-001-1" in result.stdout

    def test_get_message_verbose(self, sample_export: Path) -> None:
        """Test getting message with --verbose flag.

        Validates:
        - get.py line 540: verbose=True parameter
        - Full content and conversation messages displayed
        """
        # Act
        result = runner.invoke(
            app, ["get", "message", str(sample_export), "msg-001-1", "--verbose"]
        )

        # Assert: Success
        assert result.exit_code == 0
        assert "All Messages in Conversation:" in result.stdout

    def test_get_message_not_found(self, sample_export: Path) -> None:
        """Test getting non-existent message.

        Validates:
        - get.py lines 521-531: None result handling
        - Exit code 1
        """
        # Act
        result = runner.invoke(
            app, ["get", "message", str(sample_export), "nonexistent-msg-id"]
        )

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_get_message_not_found_with_hint(self, sample_export: Path) -> None:
        """Test message not found in specified conversation.

        Validates:
        - get.py lines 522-526: error message with conversation context
        - Exit code 1
        """
        # Act
        result = runner.invoke(
            app,
            [
                "get",
                "message",
                str(sample_export),
                "msg-999-999",
                "-c",
                "conv-001",
            ],
        )

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_get_message_invalid_format(self, sample_export: Path) -> None:
        """Test get message with invalid format option.

        Validates:
        - get.py lines 487-492: format validation
        - Exit code 2
        """
        # Act
        result = runner.invoke(
            app,
            ["get", "message", str(sample_export), "msg-001-1", "--format", "xml"],
        )

        # Assert: Exit code 2
        assert result.exit_code == 2
        assert "invalid format" in result.output.lower()

    def test_get_message_file_not_found(self) -> None:
        """Test get message with non-existent file.

        Validates:
        - get.py lines 495-497: file existence check
        - Exit code 1
        """
        # Act
        result = runner.invoke(app, ["get", "message", "/nonexistent.json", "msg-001-1"])

        # Assert: Exit code 1
        assert result.exit_code == 1
        assert "not found" in result.output.lower()
