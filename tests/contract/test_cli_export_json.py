"""Contract tests for CLI export command JSON format support.

Task: JSON Export Format Implementation
Phase: RED (tests designed to FAIL initially)

This module validates the JSON export format functionality in the CLI export command.
These are BLACK BOX tests - we invoke the CLI as subprocess and validate
external behavior (stdout, stderr, exit codes, output format).

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure the export command supports JSON format output.

Contract Requirements Validated:
- FR-018: Export command with format option
- CHK031: stdout/stderr separation (JSON data vs progress messages)
- CHK032: Exit codes (0=success, 1=error, 2=invalid input)
- Pydantic model serialization via .model_dump_json()

Architectural Coverage:
- CLI entry point → format validation → JSON serialization → file I/O
- Pydantic Conversation.model_dump_json() for JSON output
- Error handling for invalid format values
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# CLI Export JSON Contract Test Fixtures
# =============================================================================


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI in development mode.
    """
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def export_sample_file(tmp_path: Path) -> Path:
    """Create sample export for JSON export testing (1 conversation).

    Returns a minimal valid OpenAI export with:
    - One conversation with 2 messages (user + assistant)
    - All required fields for Conversation model validation
    """
    conversations = [
        {
            "id": "json-export-001",
            "title": "Python JSON Export Test",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["What is JSON?"],
                        },
                        "create_time": 1710000000.0,
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
                            "parts": ["JSON is JavaScript Object Notation."],
                        },
                        "create_time": 1710000010.0,
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
    ]

    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(conversations), encoding="utf-8")
    return export_file


# =============================================================================
# Test: JSON Format Output to stdout
# =============================================================================


def test_export_json_format_to_stdout(cli_command: list[str], export_sample_file: Path) -> None:
    """Test that --format json outputs valid JSON to stdout.

    RED Phase: This test SHOULD FAIL initially because:
    - The --format flag does not exist yet
    - JSON export functionality not implemented

    Expected behavior after GREEN:
    - Exit code 0 (success)
    - stdout contains valid JSON parseable by json.loads()
    - stderr contains progress/success messages (empty for stdout output)
    - JSON includes conversation metadata (id, title, created_at, updated_at)
    - JSON includes messages array with role, content, timestamp

    Requirements:
        - FR-018: Export command with format options
        - CHK031: JSON data on stdout, progress on stderr
    """
    # Arrange: Prepare command
    cmd = [
        *cli_command,
        "export",
        str(export_sample_file),
        "json-export-001",
        "--format",
        "json",
    ]

    # Act: Execute command
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    # Assert: Validate exit code and output
    assert result.returncode == 0, (
        f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"
    )

    # Assert: stdout contains valid JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"stdout is not valid JSON: {e}\nstdout: {result.stdout}")

    # Assert: JSON structure includes expected fields
    assert "id" in data, "JSON missing 'id' field"
    assert "title" in data, "JSON missing 'title' field"
    assert "created_at" in data, "JSON missing 'created_at' field"
    assert "updated_at" in data, "JSON missing 'updated_at' field (nullable OK)"
    assert "messages" in data, "JSON missing 'messages' field"

    # Assert: Validate conversation data
    assert data["id"] == "json-export-001"
    assert data["title"] == "Python JSON Export Test"
    assert isinstance(data["messages"], list)
    assert len(data["messages"]) == 2

    # Assert: Validate message structure
    first_msg = data["messages"][0]
    assert "id" in first_msg
    assert "role" in first_msg
    assert "content" in first_msg
    assert "timestamp" in first_msg
    assert first_msg["role"] == "user"
    assert first_msg["content"] == "What is JSON?"


# =============================================================================
# Test: JSON Format Output to File
# =============================================================================


def test_export_json_format_to_file(
    cli_command: list[str], export_sample_file: Path, tmp_path: Path
) -> None:
    """Test that --format json --output writes valid JSON to file.

    RED Phase: This test SHOULD FAIL initially because:
    - The --format flag does not exist yet
    - JSON export functionality not implemented

    Expected behavior after GREEN:
    - Exit code 0 (success)
    - Output file exists and contains valid JSON
    - stderr contains success message (e.g., "✓ Exported to...")
    - stdout is empty (data written to file)
    - JSON structure matches Pydantic Conversation model

    Requirements:
        - FR-018: Export command with --output flag
        - CHK031: Empty stdout when writing to file
    """
    # Arrange: Prepare command and output path
    output_file = tmp_path / "conversation.json"
    cmd = [
        *cli_command,
        "export",
        str(export_sample_file),
        "json-export-001",
        "--format",
        "json",
        "--output",
        str(output_file),
    ]

    # Act: Execute command
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    # Assert: Validate exit code
    assert result.returncode == 0, (
        f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"
    )

    # Assert: stdout is empty (data written to file)
    assert result.stdout.strip() == "", f"Expected empty stdout, got: {result.stdout}"

    # Assert: stderr contains success message
    assert "Exported to" in result.stderr or "✓" in result.stderr

    # Assert: Output file exists
    assert output_file.exists(), f"Output file not created: {output_file}"

    # Assert: File contains valid JSON
    try:
        data = json.loads(output_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        pytest.fail(f"Output file is not valid JSON: {e}")

    # Assert: JSON structure matches expected conversation
    assert data["id"] == "json-export-001"
    assert data["title"] == "Python JSON Export Test"
    assert len(data["messages"]) == 2


# =============================================================================
# Test: Default Format is Markdown (Backwards Compatibility)
# =============================================================================


def test_export_default_format_is_markdown(
    cli_command: list[str], export_sample_file: Path
) -> None:
    """Test that export command defaults to markdown format (backwards compatibility).

    RED Phase: This test SHOULD PASS even before implementation to ensure
    we don't break existing functionality.

    Expected behavior:
    - No --format flag: defaults to markdown
    - stdout contains markdown (starts with "# " header)
    - No JSON output

    Requirements:
        - FR-018: Default format is markdown
        - Backwards compatibility with existing behavior
    """
    # Arrange: Prepare command WITHOUT --format flag
    cmd = [
        *cli_command,
        "export",
        str(export_sample_file),
        "json-export-001",
    ]

    # Act: Execute command
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    # Assert: Exit code 0
    assert result.returncode == 0

    # Assert: stdout contains markdown (starts with heading)
    assert result.stdout.startswith("# "), f"Expected markdown output, got: {result.stdout[:100]}"

    # Assert: NOT JSON (would fail json.loads)
    with pytest.raises(json.JSONDecodeError):
        json.loads(result.stdout)


# =============================================================================
# Test: Invalid Format Value Shows Error
# =============================================================================


def test_export_invalid_format_shows_error(
    cli_command: list[str], export_sample_file: Path
) -> None:
    """Test that invalid --format value shows error message and exits with code 2.

    RED Phase: This test SHOULD FAIL initially because:
    - The --format flag does not exist yet
    - Format validation not implemented

    Expected behavior after GREEN:
    - Exit code 2 (invalid arguments)
    - stderr contains error message mentioning invalid format
    - stdout is empty

    Requirements:
        - CHK032: Exit code 2 for invalid arguments
        - User-friendly error messages
    """
    # Arrange: Prepare command with invalid format
    cmd = [
        *cli_command,
        "export",
        str(export_sample_file),
        "json-export-001",
        "--format",
        "xml",  # Invalid format
    ]

    # Act: Execute command
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    # Assert: Exit code 2 (invalid arguments)
    assert result.returncode == 2, (
        f"Expected exit code 2, got {result.returncode}. stderr: {result.stderr}"
    )

    # Assert: stderr contains error about invalid format
    assert "format" in result.stderr.lower() or "invalid" in result.stderr.lower()

    # Assert: stdout is empty
    assert result.stdout.strip() == ""


# =============================================================================
# Test: JSON Format Preserves All Data
# =============================================================================


def test_export_json_preserves_all_data(cli_command: list[str], export_sample_file: Path) -> None:
    """Test that JSON export includes all conversation fields from Pydantic model.

    RED Phase: This test SHOULD FAIL initially because JSON export not implemented.

    Expected behavior after GREEN:
    - JSON includes all Conversation model fields
    - Timestamps in ISO 8601 format
    - Messages include parent_id, images (if present)
    - Metadata preserved

    Requirements:
        - Pydantic Conversation.model_dump_json() serialization
        - Complete data preservation for programmatic consumption
    """
    # Arrange: Prepare command
    cmd = [
        *cli_command,
        "export",
        str(export_sample_file),
        "json-export-001",
        "--format",
        "json",
    ]

    # Act: Execute command
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    # Assert: Valid JSON output
    assert result.returncode == 0
    data = json.loads(result.stdout)

    # Assert: All Conversation model fields present
    required_fields = ["id", "title", "created_at", "updated_at", "messages", "metadata"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Assert: Timestamps are strings (ISO 8601 from Pydantic)
    assert isinstance(data["created_at"], str)
    # updated_at can be null or string
    assert data["updated_at"] is None or isinstance(data["updated_at"], str)

    # Assert: Messages have Message model fields
    first_msg = data["messages"][0]
    required_msg_fields = ["id", "role", "content", "timestamp", "parent_id", "images"]
    for field in required_msg_fields:
        assert field in first_msg, f"Missing required message field: {field}"

    # Assert: parent_id can be None
    assert first_msg["parent_id"] is None  # Root message

    # Assert: images is a list (empty or with items)
    assert isinstance(first_msg["images"], list)
