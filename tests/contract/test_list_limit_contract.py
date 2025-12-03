"""Contract tests for list command --limit flag (US0-AS2).

Task: Design failing tests for US0-AS2 acceptance scenario fix
Phase: RED (tests designed to FAIL initially)

This module validates the --limit flag functionality for the list command
per FR-443 and acceptance scenario US0-AS2.

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the CLI --limit flag adheres to its specification.

Functional Requirements Validated:
- FR-443: List --limit flag MUST restrict output to top N conversations (after sorting)
- FR-440: List output MUST sort conversations by created_at descending (newest first)
- FR-442: List --json format MUST output array of objects

Acceptance Scenario:
- US0-AS2: "Given a large export file, When I run `echomine list conversations.json --limit 20`,
           Then I see only the 20 most recent conversations (sorted by created_at descending)"

Constitution Requirements:
- Principle II: CLI Interface Contract - Exit codes (0 for success, 2 for usage error)
- Principle III: TDD - Write failing tests FIRST
- Principle VI: Strict typing - All tests must be type-safe

Expected Failure Reason:
- --limit flag not implemented in list command
- typer.Option for limit not added to list_conversations function
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# Fixtures
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
def large_export_file(tmp_path: Path) -> Path:
    """Create export file with 50 conversations for limit testing.

    Conversations have incrementing timestamps to test sort order.
    The newest conversation should have id "conv-050" and oldest "conv-001".
    """
    conversations = []

    # Create 50 conversations with incrementing timestamps
    # conv-001 is oldest (1710000000), conv-050 is newest (1710049000)
    for i in range(1, 51):
        conv_id = f"conv-{i:03d}"
        title = f"Test Conversation {i:03d}"
        # Increment by 1000 seconds per conversation
        timestamp = 1710000000.0 + (i - 1) * 1000.0

        conversation = {
            "id": conv_id,
            "title": title,
            "create_time": timestamp,
            "update_time": timestamp + 100.0,
            "mapping": {
                f"msg-{i}-1": {
                    "id": f"msg-{i}-1",
                    "message": {
                        "id": f"msg-{i}-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": [f"Question {i}"],
                        },
                        "create_time": timestamp,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": f"msg-{i}-1",
        }
        conversations.append(conversation)

    export_file = tmp_path / "large_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


# =============================================================================
# Contract Tests - FR-443: --limit flag functionality
# =============================================================================


@pytest.mark.contract
class TestListLimitFlagContract:
    """Contract tests for 'echomine list --limit' flag.

    These tests validate FR-443 and US0-AS2 acceptance scenario.
    All tests should FAIL initially because --limit flag is not implemented.

    Expected Failure Mode:
    - CLI will show "no such option: --limit" error
    - Exit code 2 (usage error) instead of 0 (success)
    """

    def test_limit_flag_restricts_output_to_n_conversations_text_format(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit flag restricts output to N conversations in text format.

        Validates:
        - FR-443: --limit flag restricts output to top N conversations
        - FR-440: Output sorted by created_at descending (newest first)
        - US0-AS2: Primary acceptance scenario

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit 5'
        result = subprocess.run(
            [*cli_command, "list", str(large_export_file), "--limit", "5"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 for success
        assert result.returncode == 0, (
            f"Expected exit code 0 with --limit flag. Got {result.returncode}. "
            f"stderr: {result.stderr}"
        )

        # Assert: stdout contains exactly 5 conversations (plus header)
        stdout = result.stdout
        lines = stdout.strip().split("\n")

        # The 5 newest conversations should be: conv-050, conv-049, conv-048, conv-047, conv-046
        assert "conv-050" in stdout, "Newest conversation (conv-050) should be included"
        assert "conv-049" in stdout, "2nd newest conversation should be included"
        assert "conv-048" in stdout, "3rd newest conversation should be included"
        assert "conv-047" in stdout, "4th newest conversation should be included"
        assert "conv-046" in stdout, "5th newest conversation should be included"

        # Assert: Older conversations NOT included
        assert "conv-045" not in stdout, "6th conversation should be excluded by --limit 5"
        assert "conv-001" not in stdout, "Oldest conversation should be excluded"

    def test_limit_flag_restricts_output_to_n_conversations_json_format(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit flag restricts output to N conversations in JSON format.

        Validates:
        - FR-443: --limit flag works with --format json
        - FR-442: JSON output structure
        - FR-440: Sort order (newest first)

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit 10 --format json'
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(large_export_file),
                "--limit",
                "10",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Valid JSON output
        stdout = result.stdout
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\n{stdout}")

        # Assert: Exactly 10 conversations in array
        assert isinstance(data, list), "JSON output should be array of conversations"
        assert len(data) == 10, (
            f"Expected exactly 10 conversations with --limit 10. Got {len(data)}"
        )

        # Assert: Conversations sorted by created_at descending (newest first)
        # First conversation should be conv-050 (newest)
        assert data[0]["id"] == "conv-050", (
            f"First conversation should be newest (conv-050). Got {data[0]['id']}"
        )
        # Last should be conv-041 (10th from top)
        assert data[9]["id"] == "conv-041", (
            f"10th conversation should be conv-041. Got {data[9]['id']}"
        )

        # Verify all 10 are in descending order
        expected_ids = [f"conv-{i:03d}" for i in range(50, 40, -1)]  # 50 down to 41
        actual_ids = [conv["id"] for conv in data]
        assert actual_ids == expected_ids, (
            f"Conversations not in correct order. Expected {expected_ids}, got {actual_ids}"
        )

    def test_limit_flag_accepts_value_1_returns_single_conversation(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit 1 returns only the newest conversation.

        Validates:
        - FR-443: --limit 1 edge case (single conversation)
        - FR-440: Newest conversation first

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit 1 --format json'
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(large_export_file),
                "--limit",
                "1",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Exactly 1 conversation
        data = json.loads(result.stdout)
        assert len(data) == 1, f"Expected exactly 1 conversation. Got {len(data)}"

        # Assert: It's the newest conversation (conv-050)
        assert data[0]["id"] == "conv-050", (
            f"--limit 1 should return newest conversation (conv-050). Got {data[0]['id']}"
        )

    def test_limit_flag_greater_than_total_returns_all_conversations(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit greater than total count returns all conversations.

        Validates:
        - FR-443: --limit N where N > total doesn't error, just returns all
        - Graceful handling of limit > available

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit 1000 --format json'
        # File only has 50 conversations, so should return all 50
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(large_export_file),
                "--limit",
                "1000",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: All 50 conversations returned
        data = json.loads(result.stdout)
        assert len(data) == 50, (
            f"Expected all 50 conversations when --limit > total. Got {len(data)}"
        )

    def test_limit_flag_value_0_shows_usage_error_exit_code_2(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit 0 shows error with exit code 2.

        Validates:
        - FR-443: --limit must be positive integer (> 0)
        - Principle II: Exit code 2 for usage errors
        - Clear error message

        Expected to FAIL: --limit flag not implemented (will fail with "no such option").
        Once implemented, should validate --limit > 0.
        """
        # Act: Run 'echomine list <file> --limit 0'
        result = subprocess.run(
            [*cli_command, "list", str(large_export_file), "--limit", "0"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (usage error)
        assert result.returncode == 2, (
            f"--limit 0 should exit with code 2 (usage error). Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        # Error should mention limit or positive or valid value
        assert any(
            keyword in stderr.lower() for keyword in ["limit", "positive", "greater", "invalid"]
        ), f"Error should mention invalid limit value. Got: {stderr}"

    def test_limit_flag_negative_value_shows_usage_error_exit_code_2(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit with negative value shows error with exit code 2.

        Validates:
        - FR-443: --limit must be positive integer
        - Principle II: Exit code 2 for usage errors
        - Input validation

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit -5'
        result = subprocess.run(
            [*cli_command, "list", str(large_export_file), "--limit", "-5"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (usage error)
        assert result.returncode == 2, (
            f"Negative --limit should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert any(
            keyword in stderr.lower() for keyword in ["limit", "positive", "greater", "invalid"]
        ), f"Error should mention invalid limit value. Got: {stderr}"

    def test_limit_flag_non_integer_value_shows_usage_error_exit_code_2(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit with non-integer value shows error with exit code 2.

        Validates:
        - FR-443: --limit must be integer
        - Typer argument validation
        - Clear error message

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit abc'
        result = subprocess.run(
            [*cli_command, "list", str(large_export_file), "--limit", "abc"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2 (usage error)
        assert result.returncode == 2, (
            f"Non-integer --limit should exit with code 2. Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

    def test_limit_flag_mentioned_in_help_text(self, cli_command: list[str]) -> None:
        """Test that --limit flag is documented in help text.

        Validates:
        - FR-443: --limit flag is discoverable
        - CLI documentation completeness

        Expected to FAIL: --limit flag not in help text.
        """
        # Act: Run 'echomine list --help'
        result = subprocess.run(
            [*cli_command, "list", "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0
        assert result.returncode == 0, "Help should exit with code 0"

        # Assert: Help text contains --limit flag
        stdout = result.stdout
        assert "--limit" in stdout, "Help text should mention --limit flag"

        # Assert: Help describes what --limit does
        # Should mention "limit" or "restrict" or "top N" or similar
        assert any(
            keyword in stdout.lower() for keyword in ["restrict", "top", "maximum", "first"]
        ), "Help should describe what --limit does"

    def test_limit_flag_respects_sort_order_newest_first(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit returns newest N conversations (per FR-440 sort order).

        Validates:
        - FR-443: --limit applies AFTER sorting
        - FR-440: Sort by created_at descending (newest first)
        - US0-AS2: "20 most recent conversations"

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Run 'echomine list <file> --limit 20 --format json'
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(large_export_file),
                "--limit",
                "20",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Assert: Exactly 20 conversations
        data = json.loads(result.stdout)
        assert len(data) == 20, f"Expected 20 conversations. Got {len(data)}"

        # Assert: First is newest (conv-050), last is 20th from top (conv-031)
        assert data[0]["id"] == "conv-050", "First should be newest"
        assert data[19]["id"] == "conv-031", "20th should be conv-031"

        # Assert: All conversations in descending order by created_at
        expected_ids = [f"conv-{i:03d}" for i in range(50, 30, -1)]  # 50 down to 31
        actual_ids = [conv["id"] for conv in data]
        assert actual_ids == expected_ids, "Conversations not sorted correctly"

        # Assert: No older conversations included
        for conv in data:
            conv_num = int(conv["id"].split("-")[1])
            assert conv_num >= 31, (
                f"Conversation {conv['id']} should be excluded (older than top 20)"
            )


# =============================================================================
# Edge Cases and Integration
# =============================================================================


@pytest.mark.contract
class TestListLimitEdgeCases:
    """Edge case tests for --limit flag."""

    def test_limit_flag_with_empty_export_file(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test --limit with empty export file succeeds (not error).

        Validates:
        - FR-445: Empty file is success (exit code 0)
        - FR-443: --limit N with 0 results returns empty

        Expected to FAIL: --limit flag not implemented.
        """
        # Create empty export
        empty_file = tmp_path / "empty.json"
        with empty_file.open("w") as f:
            json.dump([], f)

        # Act: Run with --limit on empty file
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(empty_file),
                "--limit",
                "10",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 0 (success, not error)
        assert result.returncode == 0, (
            f"Empty file with --limit should succeed. Got exit code {result.returncode}"
        )

        # Assert: Empty array in JSON output
        data = json.loads(result.stdout)
        assert data == [], "Empty file should return empty array"

    def test_limit_flag_works_with_single_conversation_file(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test --limit 5 with file containing only 1 conversation.

        Validates:
        - FR-443: --limit N where N > total returns all available
        - Graceful handling of small files

        Expected to FAIL: --limit flag not implemented.
        """
        # Create file with 1 conversation
        conversations = [
            {
                "id": "single-conv",
                "title": "Only Conversation",
                "create_time": 1710000000.0,
                "update_time": 1710000100.0,
                "mapping": {
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1710000000.0,
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

        single_file = tmp_path / "single.json"
        with single_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Request --limit 5 from file with only 1 conversation
        result = subprocess.run(
            [
                *cli_command,
                "list",
                str(single_file),
                "--limit",
                "5",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Returns the 1 conversation available
        data = json.loads(result.stdout)
        assert len(data) == 1, "Should return the 1 available conversation"
        assert data[0]["id"] == "single-conv"

    def test_limit_flag_output_pipelineable_with_jq(
        self, cli_command: list[str], large_export_file: Path
    ) -> None:
        """Test --limit JSON output is pipeline-friendly with jq.

        Validates:
        - FR-019: Pipeline-friendly output
        - FR-442: JSON output structure
        - Real-world usage pattern

        Expected to FAIL: --limit flag not implemented.
        """
        # Act: Pipe output to jq to extract titles
        import shlex

        cmd_str = " ".join(shlex.quote(arg) for arg in cli_command)
        pipeline = f"{cmd_str} list {large_export_file} --limit 3 --format json | jq -r '.[].title'"

        result = subprocess.run(
            pipeline,
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Pipeline succeeds
        assert result.returncode == 0, f"Pipeline should succeed. stderr: {result.stderr}"

        # Assert: Output contains exactly 3 titles
        titles = result.stdout.strip().split("\n")
        assert len(titles) == 3, f"Expected 3 titles. Got {len(titles)}: {titles}"

        # Assert: Titles are for newest 3 conversations
        assert titles[0] == "Test Conversation 050"
        assert titles[1] == "Test Conversation 049"
        assert titles[2] == "Test Conversation 048"
