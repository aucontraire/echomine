"""Contract tests for --match-mode CLI flag.

Tests for FR-007-011: Boolean match mode via CLI.

TDD: These tests are written FIRST and should FAIL until T027 implements
the --match-mode CLI flag.

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2
    - FR-007: --match-mode flag accepts 'all' or 'any'
    - FR-008: Default is 'any' (OR logic)
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
def match_mode_export(tmp_path: Path) -> Path:
    """Create export with match mode testable content."""
    conversations = [
        {
            "id": "conv-both-terms",
            "title": "Python and Java Discussion",
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
                            "parts": ["I use both Python and Java in my projects"],
                        },
                        "create_time": 1700000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-1",
        },
        {
            "id": "conv-python-only",
            "title": "Python Only Project",
            "create_time": 1700002000.0,
            "update_time": 1700003000.0,
            "mapping": {
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Python is my favorite programming language"],
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
            "current_node": "msg-2",
        },
        {
            "id": "conv-java-only",
            "title": "Java Enterprise Project",
            "create_time": 1700004000.0,
            "update_time": 1700005000.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Java is great for enterprise applications"],
                        },
                        "create_time": 1700004000.0,
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

    export_file = tmp_path / "match_mode_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.contract
class TestMatchModeFlagAccepted:
    """Contract tests for --match-mode flag acceptance (FR-007)."""

    def test_match_mode_all_accepted(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """--match-mode all is accepted by search command."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "--match-mode",
                "all",
            ],
            check=False, capture_output=True,
            text=True,
        )

        # Should not fail with "unknown option" error
        assert "Error: Unknown option" not in result.stderr
        assert result.returncode in (0, 1)

    def test_match_mode_any_accepted(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """--match-mode any is accepted by search command."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "--match-mode",
                "any",
            ],
            check=False, capture_output=True,
            text=True,
        )

        assert "Error: Unknown option" not in result.stderr
        assert result.returncode in (0, 1)

    def test_match_mode_invalid_rejected(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """--match-mode invalid is rejected with exit code 2."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "--match-mode",
                "invalid",
            ],
            check=False, capture_output=True,
            text=True,
        )

        # Should fail with exit code 2 (invalid argument)
        assert result.returncode == 2


@pytest.mark.contract
class TestMatchModeDefault:
    """Contract tests for default match mode (FR-008)."""

    def test_default_match_mode_is_any(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """Default match mode (no flag) uses 'any' (OR logic)."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "-k",
                "java",
                "--json",
            ],
            check=False, capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        # With 'any' mode, should find all 3 conversations (each has python OR java)
        assert data["metadata"]["total_results"] == 3


@pytest.mark.contract
class TestMatchModeAllBehavior:
    """Contract tests for match_mode='all' behavior (FR-009)."""

    def test_match_mode_all_requires_all_keywords(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """--match-mode all returns only conversations with ALL keywords."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "-k",
                "java",
                "--match-mode",
                "all",
                "--json",
            ],
            check=False, capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        # With 'all' mode, should only find conv-both-terms (has both python AND java)
        assert data["metadata"]["total_results"] == 1
        assert data["results"][0]["conversation_id"] == "conv-both-terms"


@pytest.mark.contract
class TestMatchModeJsonOutput:
    """Contract tests for match_mode in JSON output."""

    def test_match_mode_in_json_query(
        self, cli_command: list[str], match_mode_export: Path
    ) -> None:
        """JSON output includes match_mode in query section."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(match_mode_export),
                "-k",
                "python",
                "--match-mode",
                "all",
                "--json",
            ],
            check=False, capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "match_mode" in data["metadata"]["query"]
        assert data["metadata"]["query"]["match_mode"] == "all"
