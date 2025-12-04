"""Contract tests for --role CLI flag (FR-017-020).

Tests the search command's --role flag for filtering by message author role.

Requirements:
    - FR-017: --role accepts 'user', 'assistant', 'system'
    - FR-018: Filter applied to messages before text aggregation
    - FR-019: No --role flag means all roles included
    - FR-020: Case-insensitive role value handling
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def sample_export_path() -> Path:
    """Path to sample export file for testing."""
    return Path(__file__).parent.parent / "fixtures" / "sample_export.json"


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine."""
    return [sys.executable, "-m", "echomine.cli.app"]


class TestRoleFlagBasic:
    """Test basic --role flag functionality."""

    def test_role_flag_user_accepted(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """--role user is accepted without error."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--role",
                "user",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should succeed (exit code 0)
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_role_flag_assistant_accepted(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """--role assistant is accepted without error."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--role",
                "assistant",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_role_flag_system_accepted(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """--role system is accepted without error."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--role",
                "system",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_role_flag_invalid_value_rejected(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """--role with invalid value is rejected with exit code 2."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--role",
                "invalid_role",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should fail with exit code 2 (invalid arguments)
        assert result.returncode == 2, f"stdout: {result.stdout}, stderr: {result.stderr}"
        assert "invalid" in result.stderr.lower() or "role" in result.stderr.lower()


class TestRoleFlagJsonOutput:
    """Test --role flag in JSON output metadata."""

    def test_role_filter_in_json_metadata(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """--role value appears in JSON output metadata."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--role",
                "user",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Parse JSON output
        output = json.loads(result.stdout)
        assert "metadata" in output
        assert "query" in output["metadata"]
        assert "role_filter" in output["metadata"]["query"]
        assert output["metadata"]["query"]["role_filter"] == "user"

    def test_no_role_filter_null_in_json(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """When --role not specified, role_filter is null in JSON."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["metadata"]["query"]["role_filter"] is None
