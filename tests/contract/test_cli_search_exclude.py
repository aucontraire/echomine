"""Contract tests for --exclude CLI flag.

Tests for FR-012-016: Exclude keywords via CLI.

TDD: These tests are written FIRST and should FAIL until T036 implements
the --exclude CLI flag.

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2
    - FR-012: --exclude flag accepts multiple values
    - FR-015: Uses same tokenization as keywords
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
def exclude_export(tmp_path: Path) -> Path:
    """Create export with exclude testable content."""
    conversations = [
        {
            "id": "conv-python-django",
            "title": "Python Django Tutorial",
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
                            "parts": ["How to use Django with Python"],
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
            "id": "conv-python-flask",
            "title": "Python Flask Tutorial",
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
                            "parts": ["How to use Flask with Python"],
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
            "id": "conv-python-fastapi",
            "title": "Python FastAPI Tutorial",
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
                            "parts": ["How to use FastAPI with Python"],
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

    export_file = tmp_path / "exclude_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.contract
class TestExcludeFlagAccepted:
    """Contract tests for --exclude flag acceptance (FR-012)."""

    def test_exclude_single_term_accepted(
        self, cli_command: list[str], exclude_export: Path
    ) -> None:
        """--exclude with single term is accepted."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should not fail with "unknown option" error
        assert "Error: Unknown option" not in result.stderr
        assert result.returncode in (0, 1)

    def test_exclude_multiple_terms_accepted(
        self, cli_command: list[str], exclude_export: Path
    ) -> None:
        """--exclude with multiple terms is accepted."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
                "--exclude",
                "flask",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert "Error: Unknown option" not in result.stderr
        assert result.returncode in (0, 1)


@pytest.mark.contract
class TestExcludeBehavior:
    """Contract tests for --exclude behavior (FR-013-015)."""

    def test_exclude_filters_out_matching_conversations(
        self, cli_command: list[str], exclude_export: Path
    ) -> None:
        """--exclude filters out conversations containing excluded terms."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)

        # Should find flask and fastapi, but NOT django
        result_ids = [r["conversation_id"] for r in data["results"]]

        assert "conv-python-flask" in result_ids
        assert "conv-python-fastapi" in result_ids
        assert "conv-python-django" not in result_ids
        assert data["metadata"]["total_results"] == 2

    def test_exclude_multiple_filters_all(
        self, cli_command: list[str], exclude_export: Path
    ) -> None:
        """Multiple --exclude filters out all matching terms."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
                "--exclude",
                "flask",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)

        # Should only find fastapi
        result_ids = [r["conversation_id"] for r in data["results"]]

        assert "conv-python-fastapi" in result_ids
        assert "conv-python-django" not in result_ids
        assert "conv-python-flask" not in result_ids
        assert data["metadata"]["total_results"] == 1


@pytest.mark.contract
class TestExcludeJsonOutput:
    """Contract tests for exclude_keywords in JSON output."""

    def test_exclude_in_json_query(self, cli_command: list[str], exclude_export: Path) -> None:
        """JSON output includes exclude_keywords in query section."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "exclude_keywords" in data["metadata"]["query"]
        assert data["metadata"]["query"]["exclude_keywords"] == ["django"]

    def test_exclude_multiple_in_json_query(
        self, cli_command: list[str], exclude_export: Path
    ) -> None:
        """JSON output includes all exclude_keywords."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(exclude_export),
                "-k",
                "python",
                "--exclude",
                "django",
                "--exclude",
                "flask",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        exclude_kw = data["metadata"]["query"]["exclude_keywords"]
        assert "django" in exclude_kw
        assert "flask" in exclude_kw
