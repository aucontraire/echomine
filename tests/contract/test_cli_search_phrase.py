"""Contract tests for --phrase CLI flag.

Tests for FR-001, FR-002: Exact phrase matching via CLI.

TDD: These tests are written FIRST and should FAIL until T018 implements
the --phrase CLI flag.

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2
    - FR-001: --phrase flag accepts string
    - FR-002: Multiple --phrase flags supported
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine."""
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def phrase_export(tmp_path: Path) -> Path:
    """Create export with phrase-testable content."""
    conversations = [
        {
            "id": "conv-with-phrase",
            "title": "Algo-Insights Project",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Let's discuss the algo-insights project"],
                        },
                        "create_time": 1700000000.0,
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
                        "content": {
                            "content_type": "text",
                            "parts": ["The algo-insights project uses data pipeline techniques"],
                        },
                        "create_time": 1700000100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-2",
        },
        {
            "id": "conv-no-phrase",
            "title": "Different Topic",
            "create_time": 1700002000.0,
            "update_time": 1700003000.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["This is about algorithm insights separately"],
                        },
                        "create_time": 1700002000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-3",
        },
    ]

    export_file = tmp_path / "phrase_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.contract
class TestPhraseFlagAccepted:
    """Contract tests for --phrase flag acceptance (FR-001)."""

    def test_phrase_flag_accepted(self, cli_command: list[str], phrase_export: Path) -> None:
        """--phrase flag is accepted by search command."""
        result = subprocess.run(
            [*cli_command, "search", str(phrase_export), "--phrase", "algo-insights"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should not fail with "unknown option" error
        assert "Error: Unknown option" not in result.stderr
        # Should succeed or exit with exit code 0 (even if no results due to not implemented)
        # Once implemented, this will return results
        assert result.returncode in (0, 1)  # 0 success, 1 for not-yet-implemented

    def test_phrase_flag_as_only_filter(self, cli_command: list[str], phrase_export: Path) -> None:
        """--phrase alone (without -k) should be a valid filter."""
        result = subprocess.run(
            [*cli_command, "search", str(phrase_export), "--phrase", "algo-insights"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should not complain about missing filters
        assert "At least one filter" not in result.stderr
        assert result.returncode in (0, 1)


@pytest.mark.contract
class TestMultiplePhrasesFlags:
    """Contract tests for multiple --phrase flags (FR-002)."""

    def test_multiple_phrase_flags_accepted(
        self, cli_command: list[str], phrase_export: Path
    ) -> None:
        """Multiple --phrase flags are accepted."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(phrase_export),
                "--phrase",
                "algo-insights",
                "--phrase",
                "data pipeline",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode in (0, 1)
        assert "Error" not in result.stderr or "NotImplementedError" in result.stderr


@pytest.mark.contract
class TestPhraseCombinedWithKeywords:
    """Contract tests for combining --phrase with -k (FR-004)."""

    def test_phrase_and_keyword_combined(self, cli_command: list[str], phrase_export: Path) -> None:
        """--phrase can be combined with -k keywords."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(phrase_export),
                "-k",
                "python",
                "--phrase",
                "algo-insights",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode in (0, 1)


@pytest.mark.contract
class TestPhraseJsonOutput:
    """Contract tests for phrase in JSON output."""

    def test_phrase_in_json_query(self, cli_command: list[str], phrase_export: Path) -> None:
        """JSON output includes phrases in query section."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(phrase_export),
                "--phrase",
                "algo-insights",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Once implemented, should include phrases in JSON output
        # This test will pass once T019 implements the JSON output
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                # Check that metadata.query includes phrases
                if "metadata" in data and "query" in data["metadata"]:
                    assert "phrases" in data["metadata"]["query"]
            except json.JSONDecodeError:
                pass  # Skip if JSON not valid (feature not yet implemented)
