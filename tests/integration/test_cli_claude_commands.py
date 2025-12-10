"""Integration tests for CLI commands with Claude provider.

This module tests all CLI commands with the --provider claude flag to ensure
proper integration with the ClaudeAdapter. These tests validate end-to-end
functionality using the actual Claude export fixture.

Constitution Compliance:
    - Principle III: TDD (tests written to validate implementation)
    - Principle II: CLI interface contract (stdout/stderr/exit codes)
    - CHK031: Results to stdout, progress/errors to stderr
    - FR-049: --provider flag support for explicit provider selection

Test Coverage:
    - list command with --provider claude
    - search command with --provider claude
    - export command with --provider claude
    - get conversation command with --provider claude
    - get message command with --provider claude
    - stats command with --provider claude

All tests use the sample Claude export at tests/fixtures/claude/sample_export.json

Phase: GREEN (tests validate existing implementation)
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
def claude_export_path() -> Path:
    """Return path to Claude sample export fixture."""
    return Path(__file__).parent.parent / "fixtures" / "claude" / "sample_export.json"


class TestListCommandWithClaudeProvider:
    """Integration tests for 'echomine list' command with --provider claude."""

    def test_list_command_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test list command with --provider claude returns exit code 0.

        Validates:
        - FR-049: --provider claude flag accepted
        - Exit code 0 on success
        - stdout contains conversation data
        - ClaudeAdapter integration works end-to-end
        """
        result = cli_runner.invoke(
            app,
            ["list", str(claude_export_path), "--provider", "claude"],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert stdout contains conversation titles from fixture (may be truncated)
        assert "Python Code Review" in result.stdout or "Binary" in result.stdout
        assert "Multi-turn Technical" in result.stdout or "Quick Question" in result.stdout

    def test_list_command_with_provider_claude_json_output(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test list command with --provider claude and --format json.

        Validates:
        - JSON output format works with Claude provider
        - Valid JSON structure
        - Conversation data includes expected fields
        """
        result = cli_runner.invoke(
            app,
            ["list", str(claude_export_path), "--provider", "claude", "--format", "json"],
        )

        assert result.exit_code == 0

        # Parse JSON output
        conversations = json.loads(result.stdout)

        # Validate structure
        assert isinstance(conversations, list), "JSON output should be array"
        assert len(conversations) == 5, f"Expected 5 conversations, got {len(conversations)}"

        # Validate first conversation structure (most recent first by default)
        first_conv = conversations[0]
        assert "id" in first_conv
        assert "title" in first_conv
        assert "created_at" in first_conv
        assert "message_count" in first_conv

        # Validate specific data from fixture (find the binary search conversation)
        binary_search_conv = next(
            (c for c in conversations if c["id"] == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"), None
        )
        assert binary_search_conv is not None
        assert binary_search_conv["title"] == "Python Code Review - Binary Search Implementation"
        assert binary_search_conv["message_count"] == 2

    def test_list_command_with_provider_claude_and_limit(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test list command with --provider claude and --limit flag.

        Validates:
        - --limit flag works with Claude provider
        - Limits number of results correctly
        """
        result = cli_runner.invoke(
            app,
            ["list", str(claude_export_path), "--provider", "claude", "--limit", "2"],
        )

        assert result.exit_code == 0

        # With limit=2, we should only see 2 most recent conversations
        # Count title occurrences in output
        output_lower = result.stdout.lower()
        title_count = sum(
            1
            for title in [
                "python code review",
                "multi-turn technical",
                "quick question",
                "very long title",
            ]
            if title in output_lower
        )

        # Should have at most 2 conversations shown
        assert title_count <= 2, f"Expected max 2 conversations with --limit 2, got {title_count}"


class TestSearchCommandWithClaudeProvider:
    """Integration tests for 'echomine search' command with --provider claude."""

    def test_search_command_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test search command with --provider claude and keyword search.

        Validates:
        - FR-049: --provider claude flag accepted
        - Search functionality works with ClaudeAdapter
        - Exit code 0 on success
        - Results contain matched conversations
        """
        result = cli_runner.invoke(
            app,
            ["search", str(claude_export_path), "--provider", "claude", "-k", "binary search"],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert results contain matched conversation
        assert "binary" in result.stdout.lower() or "search" in result.stdout.lower()

    def test_search_command_with_provider_claude_json_output(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test search command with --provider claude and --json flag.

        Validates:
        - JSON output format works with Claude provider
        - Valid JSON structure with results and metadata
        - Search results include expected fields
        """
        result = cli_runner.invoke(
            app,
            [
                "search",
                str(claude_export_path),
                "--provider",
                "claude",
                "-k",
                "database",
                "--json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.stdout)

        # Validate structure per FR-301
        assert isinstance(data, dict), "JSON output should be object"
        assert "results" in data, "JSON should have 'results' field"
        assert "metadata" in data, "JSON should have 'metadata' field"

        # Validate results array
        assert isinstance(data["results"], list), "results should be array"

        # If results exist, validate structure
        if len(data["results"]) > 0:
            first_result = data["results"][0]
            assert "conversation_id" in first_result
            assert "title" in first_result
            assert "score" in first_result
            assert "matched_message_ids" in first_result

    def test_search_command_with_provider_claude_multiple_keywords(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test search command with --provider claude and multiple keywords.

        Validates:
        - Multi-keyword OR logic works with Claude provider
        - Keywords flag accepts comma-separated values
        """
        result = cli_runner.invoke(
            app,
            [
                "search",
                str(claude_export_path),
                "--provider",
                "claude",
                "-k",
                "python,database,async",
            ],
        )

        assert result.exit_code == 0
        # Should match conversations containing any of the keywords
        assert len(result.stdout) > 0, "Should have search results"


class TestExportCommandWithClaudeProvider:
    """Integration tests for 'echomine export' command with --provider claude."""

    def test_export_command_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test export command with --provider claude exports conversation to markdown.

        Validates:
        - FR-049: --provider claude flag accepted
        - Export functionality works with ClaudeAdapter
        - Exit code 0 on success
        - Markdown file created with expected content

        NOTE: This test is currently skipped due to a bug in the export command
        when using the Claude adapter. The conversation lookup mechanism appears
        to fail even though the conversation exists and can be listed/searched.
        """
        output_file = tmp_path / "exported_conversation.md"

        result = cli_runner.invoke(
            app,
            [
                "export",
                str(claude_export_path),
                "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",  # Binary search conversation
                "--provider",
                "claude",
                "--output",
                str(output_file),
            ],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert output file created
        assert output_file.exists(), "Output file should be created"

        # Validate markdown content
        content = output_file.read_text()
        assert "Python Code Review - Binary Search Implementation" in content
        assert "binary_search" in content  # Code block should be present

    def test_export_command_with_provider_claude_invalid_id_exits_with_code_1(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test export command with --provider claude and invalid conversation ID.

        Validates:
        - Exit code 1 for conversation not found
        - Error message to stderr/output
        """
        output_file = tmp_path / "nonexistent.md"

        result = cli_runner.invoke(
            app,
            [
                "export",
                str(claude_export_path),
                "nonexistent-conversation-id",
                "--provider",
                "claude",
                "--output",
                str(output_file),
            ],
        )

        # Assert exit code 1
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Assert error message mentions not found
        output = result.output
        assert "not found" in output.lower() or "error" in output.lower()


class TestGetConversationWithClaudeProvider:
    """Integration tests for 'echomine get conversation' command with --provider claude."""

    def test_get_conversation_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get conversation command with --provider claude.

        Validates:
        - FR-049: --provider claude flag accepted
        - Get conversation functionality works with ClaudeAdapter
        - Exit code 0 on success
        - Output contains conversation details
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "conversation",
                str(claude_export_path),
                "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
                "--provider",
                "claude",
            ],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert output contains conversation title
        assert "Python Code Review - Binary Search Implementation" in result.stdout

        # Assert output contains message count
        assert "2 messages" in result.stdout or "messages" in result.stdout.lower()

    def test_get_conversation_with_provider_claude_json_output(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get conversation command with --provider claude and --format json.

        Validates:
        - JSON output format works with Claude provider
        - Valid JSON structure
        - Conversation data includes all expected fields
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "conversation",
                str(claude_export_path),
                "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
                "--provider",
                "claude",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        conversation = json.loads(result.stdout)

        # Validate structure
        assert isinstance(conversation, dict), "JSON output should be object"
        assert "id" in conversation
        assert "title" in conversation
        assert "created_at" in conversation
        assert "messages" in conversation

        # Validate specific data
        assert conversation["id"] == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
        assert conversation["title"] == "Python Code Review - Binary Search Implementation"
        assert isinstance(conversation["messages"], list)
        assert len(conversation["messages"]) == 2

    def test_get_conversation_with_provider_claude_invalid_id_exits_with_code_1(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get conversation with --provider claude and invalid ID.

        Validates:
        - Exit code 1 for conversation not found
        - Error message in output
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "conversation",
                str(claude_export_path),
                "invalid-conversation-id",
                "--provider",
                "claude",
            ],
        )

        # Assert exit code 1
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Assert error message
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestGetMessageWithClaudeProvider:
    """Integration tests for 'echomine get message' command with --provider claude."""

    def test_get_message_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get message command with --provider claude.

        Validates:
        - FR-049: --provider claude flag accepted
        - Get message functionality works with ClaudeAdapter
        - Exit code 0 on success
        - Output contains message content
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "message",
                str(claude_export_path),
                "msg-001-uuid",  # First message in binary search conversation
                "--provider",
                "claude",
            ],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert output contains message content
        assert "binary search" in result.stdout.lower()

    def test_get_message_with_provider_claude_json_output(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get message command with --provider claude and --format json.

        Validates:
        - JSON output format works with Claude provider
        - Valid JSON structure
        - Message data includes all expected fields
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "message",
                str(claude_export_path),
                "msg-001-uuid",
                "--provider",
                "claude",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.stdout)

        # Validate structure (get message returns conversation context + message)
        assert isinstance(data, dict), "JSON output should be object"
        assert "message" in data or "id" in data

        # If it has a message field, validate that
        if "message" in data:
            message = data["message"]
            assert "id" in message
            assert "role" in message
            assert "content" in message
        else:
            # Validate direct message structure
            assert "id" in data
            assert "role" in data
            assert "content" in data

    def test_get_message_with_provider_claude_invalid_id_exits_with_code_1(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test get message with --provider claude and invalid message ID.

        Validates:
        - Exit code 1 for message not found
        - Error message in output
        """
        result = cli_runner.invoke(
            app,
            [
                "get",
                "message",
                str(claude_export_path),
                "invalid-message-id",
                "--provider",
                "claude",
            ],
        )

        # Assert exit code 1
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Assert error message
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestStatsCommandWithClaudeProvider:
    """Integration tests for 'echomine stats' command with --provider claude."""

    def test_stats_command_with_provider_claude_succeeds(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test stats command with --provider claude.

        Validates:
        - FR-049: --provider claude flag accepted
        - Stats functionality works with ClaudeAdapter
        - Exit code 0 on success
        - Output contains statistics summary
        """
        result = cli_runner.invoke(
            app,
            ["stats", str(claude_export_path), "--provider", "claude"],
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert output contains statistics
        output_lower = result.stdout.lower()
        assert "total conversations" in output_lower or "conversations:" in output_lower
        assert "total messages" in output_lower or "messages:" in output_lower

    def test_stats_command_with_provider_claude_json_output(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test stats command with --provider claude and --json flag.

        Validates:
        - JSON output format works with Claude provider
        - Valid JSON structure
        - Stats data includes all expected fields

        NOTE: This test is skipped due to a bug in the stats command where
        the --provider flag is not properly respected, causing it to use
        the OpenAI adapter even when --provider claude is specified.
        """
        result = cli_runner.invoke(
            app,
            ["stats", str(claude_export_path), "--provider", "claude", "--json"],
        )

        assert result.exit_code == 0

        # Parse JSON output
        stats = json.loads(result.stdout)

        # Validate structure
        assert isinstance(stats, dict), "JSON output should be object"
        assert "total_conversations" in stats
        assert "total_messages" in stats

        # Validate values from fixture (5 conversations)
        assert stats["total_conversations"] == 5
        # Binary search: 2, Multi-turn: 4, Quick: 2, Untitled: 2, Long title: 2 = 12 messages
        assert stats["total_messages"] == 12

    def test_stats_command_with_provider_claude_specific_conversation(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test stats command with --provider claude and --conversation flag.

        Validates:
        - Conversation-specific stats work with Claude provider
        - Statistics for specific conversation displayed

        NOTE: This test is skipped due to same bug as JSON stats test.
        """
        result = cli_runner.invoke(
            app,
            [
                "stats",
                str(claude_export_path),
                "--provider",
                "claude",
                "--conversation",
                "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
            ],
        )

        assert result.exit_code == 0

        # Output should contain conversation-specific stats
        output_lower = result.stdout.lower()
        assert "messages" in output_lower or "conversation" in output_lower


class TestProviderAutoDetectionWithClaudeExport:
    """Integration tests for provider auto-detection with Claude export files."""

    def test_list_command_auto_detects_claude_provider(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test list command auto-detects Claude provider without explicit flag.

        Validates:
        - FR-048: Auto-detection works for Claude exports
        - Exit code 0 on success
        - Same results as explicit --provider claude
        """
        result = cli_runner.invoke(
            app,
            ["list", str(claude_export_path)],  # No --provider flag
        )

        # Assert exit code 0
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )

        # Assert stdout contains conversation titles (same as explicit provider, may be truncated)
        assert "Python Code Review" in result.stdout or "Binary" in result.stdout

    def test_search_command_auto_detects_claude_provider(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test search command auto-detects Claude provider without explicit flag.

        Validates:
        - Auto-detection works for search command
        - Search results match explicit --provider claude
        """
        result = cli_runner.invoke(
            app,
            ["search", str(claude_export_path), "-k", "python"],  # No --provider flag
        )

        assert result.exit_code == 0
        assert len(result.stdout) > 0, "Should have search results"


class TestStdoutStderrSeparationWithClaudeProvider:
    """Tests validating stdout/stderr separation with Claude provider (CHK031)."""

    def test_list_command_progress_to_stderr_data_to_stdout(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test list command with --provider claude separates stdout/stderr correctly.

        Validates:
        - CHK031: Data on stdout, progress/errors on stderr
        - stdout contains ONLY conversation data
        - No progress indicators in stdout
        """
        result = cli_runner.invoke(
            app,
            ["list", str(claude_export_path), "--provider", "claude"],
        )

        # Assert stdout does not contain progress keywords
        stdout = result.stdout
        progress_keywords = ["parsing", "processing", "loading", "reading"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stdout.lower(), (
                f"Progress indicator '{keyword}' found in stdout. "
                "Progress MUST go to stderr per CHK031"
            )

    def test_search_command_progress_to_stderr_data_to_stdout(
        self,
        cli_runner: CliRunner,
        claude_export_path: Path,
    ) -> None:
        """Test search command with --provider claude separates stdout/stderr correctly.

        Validates:
        - CHK031: Search results on stdout, progress on stderr
        - stdout contains ONLY search results
        """
        result = cli_runner.invoke(
            app,
            ["search", str(claude_export_path), "--provider", "claude", "-k", "python"],
        )

        # Assert stdout does not contain progress keywords
        stdout = result.stdout
        progress_keywords = ["parsing", "searching", "processing"]
        for keyword in progress_keywords:
            assert keyword.lower() not in stdout.lower(), (
                f"Progress indicator '{keyword}' found in stdout. "
                "Progress MUST go to stderr per CHK031"
            )
