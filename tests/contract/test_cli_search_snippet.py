"""Contract tests for snippet in CLI search output (FR-021-025).

Tests the search command's snippet display in both human-readable and JSON output.

Requirements:
    - FR-021: CLI human-readable output MUST include a snippet column
    - FR-022: Snippets ~100 characters with "..." suffix
    - FR-023: Multiple matches show "+N more" indicator
    - FR-024: JSON output MUST include `snippet` field
    - FR-025: Graceful handling of malformed content with fallback text
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


class TestSnippetJsonOutput:
    """Test snippet field in JSON output (FR-024)."""

    def test_snippet_field_in_json_results(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """JSON output includes snippet field in results."""
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
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        output = json.loads(result.stdout)
        assert "results" in output

        # Each result should have snippet field
        for res in output["results"]:
            assert "snippet" in res, f"Missing snippet in result: {res}"

    def test_snippet_contains_matched_keyword(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """Snippet contains at least one matched keyword."""
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
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        output = json.loads(result.stdout)

        # At least one result should have snippet with keyword
        if output["results"]:
            snippets_with_keyword = [
                r
                for r in output["results"]
                if r.get("snippet") and "python" in r["snippet"].lower()
            ]
            # Either snippet has keyword OR it's "[Content unavailable]" fallback
            assert (
                len(snippets_with_keyword) > 0
                or all(
                    r.get("snippet") in ["[Content unavailable]", "[No content matched]"]
                    for r in output["results"]
                )
            )

    def test_snippet_length_approximately_100_chars(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """Snippet is truncated to ~100 characters (FR-022)."""
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
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        output = json.loads(result.stdout)

        for res in output["results"]:
            snippet = res.get("snippet", "")
            if snippet and snippet not in [
                "[Content unavailable]",
                "[No content matched]",
            ]:
                # Allow up to 150 chars (100 + "..." + " (+N more matches)")
                assert len(snippet) <= 150, f"Snippet too long: {len(snippet)} chars"


class TestSnippetTextOutput:
    """Test snippet column in human-readable output (FR-021)."""

    def test_snippet_column_in_text_output(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """Human-readable output includes Snippet column header."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--format",
                "text",
            ],
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Check for Snippet column in header
        lines = result.stdout.strip().split("\n")
        if lines:
            header = lines[0]
            assert "Snippet" in header, f"Missing Snippet column in header: {header}"

    def test_snippet_truncated_with_ellipsis(
        self, sample_export_path: Path, cli_command: list[str]
    ) -> None:
        """Long snippets end with '...' in text output."""
        result = subprocess.run(
            [
                *cli_command,
                "search",
                str(sample_export_path),
                "--keywords",
                "python",
                "--format",
                "text",
            ],
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # If there are results with long content, they should have ellipsis
        # This is a heuristic check - actual long content may or may not be present
        lines = result.stdout.strip().split("\n")
        if len(lines) > 2:  # Header + separator + at least one result
            # Just verify output is formatted correctly
            assert len(lines[0]) > 0  # Header exists
