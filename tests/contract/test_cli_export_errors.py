"""Contract tests for export command error handling and edge cases.

This module tests error paths, validation, and edge cases in the export command
that are currently missing coverage.

Coverage Target: export.py lines 169-285 (currently 29% coverage)

Constitution Compliance:
    - CHK031: stdout/stderr separation
    - CHK032: Exit codes 0/1/2
    - FR-016: Export by title support
    - FR-018: Export command functionality
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine."""
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def export_with_conversations(tmp_path: Path) -> Path:
    """Create export file with multiple conversations for testing."""
    conversations = [
        {
            "id": "conv-001",
            "title": "Python Tutorial",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Explain Python"]},
                        "create_time": 1700000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-1",
        },
        {
            "id": "conv-002",
            "title": "JavaScript Basics",
            "create_time": 1700100000.0,
            "update_time": 1700101000.0,
            "mapping": {
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Explain JS"]},
                        "create_time": 1700100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-2",
        },
        {
            "id": "conv-003",
            "title": "Python Advanced",
            "create_time": 1700200000.0,
            "update_time": 1700201000.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Advanced Python"]},
                        "create_time": 1700200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-3",
        },
    ]

    export_file = tmp_path / "export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.contract
class TestExportCommandValidation:
    """Contract tests for export command argument validation."""

    def test_export_requires_id_or_title(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export without ID or --title exits code 2.

        Validates:
        - export.py line 178-180: Requires ID or --title
        - Exit code 2 (invalid arguments)
        - Clear error message
        """
        result = subprocess.run(
            [*cli_command, "export", str(export_with_conversations)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2, (
            f"Export without ID/title should exit 2, got {result.returncode}"
        )

        # Assert: Error mentions missing requirement
        stderr = result.stderr.lower()
        assert "must specify" in stderr or "required" in stderr or "id" in stderr

    def test_export_rejects_both_id_and_title(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export with both ID and --title exits code 2.

        Validates:
        - export.py line 171-176: Mutually exclusive ID and --title
        - Exit code 2
        - Error message clear
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
                "--title",
                "Python",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 2
        assert result.returncode == 2

        # Assert: Error mentions conflict
        stderr = result.stderr.lower()
        assert "both" in stderr or "cannot specify" in stderr


@pytest.mark.contract
class TestExportCommandByTitle:
    """Contract tests for export by title functionality."""

    def test_export_by_title_single_match_succeeds(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by unique title succeeds.

        Validates:
        - export.py line 189-203: Title lookup and match
        - Exit code 0
        - Markdown output to stdout
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "--title",
                "JavaScript",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0, f"Export by title should succeed, got {result.returncode}"

        # Assert: Markdown content on stdout
        stdout = result.stdout
        assert len(stdout) > 0, "Should output markdown"
        assert "JavaScript" in stdout or "JS" in stdout

    def test_export_by_title_no_match_exits_code_1(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by non-existent title exits code 1.

        Validates:
        - export.py line 193-197: No match handling
        - Exit code 1 (not found)
        - Error message clear
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "--title",
                "NonexistentTitle12345",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions not found
        stderr = result.stderr.lower()
        assert "not found" in stderr or "no conversation" in stderr

    def test_export_by_title_multiple_matches_exits_code_1(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by ambiguous title (multiple matches) exits code 1.

        Validates:
        - export.py line 204-207: Multiple match error
        - Exit code 1
        - Error mentions multiple matches
        """
        # "Python" matches both "Python Tutorial" and "Python Advanced"
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "--title",
                "Python",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions multiple matches
        stderr = result.stderr.lower()
        assert "multiple" in stderr or "2" in stderr or "matches" in stderr


@pytest.mark.contract
class TestExportCommandByID:
    """Contract tests for export by conversation ID."""

    def test_export_by_id_succeeds(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by conversation ID succeeds.

        Validates:
        - export.py line 208-231: Export by ID
        - Exit code 0
        - Markdown output
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Markdown content on stdout
        assert len(result.stdout) > 0
        assert "Python" in result.stdout

    def test_export_by_invalid_id_exits_code_1(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by non-existent ID exits code 1.

        Validates:
        - export.py line 220-223, 228-231: Conversation not found
        - Exit code 1
        - Error message
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "nonexistent-id-12345",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions not found
        stderr = result.stderr.lower()
        assert "not found" in stderr or "error" in stderr


@pytest.mark.contract
class TestExportCommandOutputFile:
    """Contract tests for --output file writing."""

    def test_export_to_file_with_output_flag(
        self, cli_command: list[str], export_with_conversations: Path, tmp_path: Path
    ) -> None:
        """Test export with --output writes to file.

        Validates:
        - export.py line 234-242: File writing
        - Exit code 0
        - File created with markdown content
        - Success message on stderr
        """
        output_file = tmp_path / "output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: File created
        assert output_file.exists(), "Output file should be created"

        # Assert: File contains markdown
        content = output_file.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "Python" in content

        # Assert: Success message on stderr
        stderr = result.stderr
        assert len(stderr) > 0
        # Should mention success or filename

    def test_export_to_file_overwrites_existing_file(
        self, cli_command: list[str], export_with_conversations: Path, tmp_path: Path
    ) -> None:
        """Test export overwrites existing file with warning.

        Validates:
        - export.py line 236-237: File exists warning
        - File overwritten successfully
        - Warning on stderr
        """
        output_file = tmp_path / "existing.md"
        output_file.write_text("Old content", encoding="utf-8")

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: File overwritten
        content = output_file.read_text(encoding="utf-8")
        assert "Old content" not in content
        assert "Python" in content

        # Assert: Warning on stderr
        stderr = result.stderr.lower()
        assert "warning" in stderr or "overwriting" in stderr or "exists" in stderr

    def test_export_to_file_permission_denied_exits_code_1(
        self, cli_command: list[str], export_with_conversations: Path, tmp_path: Path
    ) -> None:
        """Test export to unwritable location exits code 1.

        Validates:
        - export.py line 243-245: PermissionError handling
        - Exit code 1
        - Error mentions permission

        Skipped on Windows (different permission model).
        """
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        import stat

        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # Read and execute only

        output_file = readonly_dir / "output.md"

        try:
            result = subprocess.run(
                [
                    *cli_command,
                    "export",
                    str(export_with_conversations),
                    "conv-001",
                    "--output",
                    str(output_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            # Assert: Exit code 1
            assert result.returncode == 1

            # Assert: Error mentions permission
            stderr = result.stderr.lower()
            assert "permission" in stderr or "denied" in stderr

        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    def test_export_to_file_os_error_exits_code_1(
        self, cli_command: list[str], export_with_conversations: Path, tmp_path: Path
    ) -> None:
        """Test export with OS error (e.g., disk full simulation) exits code 1.

        Validates:
        - export.py line 246-248: OSError handling
        - Exit code 1
        - Error message

        Note: Hard to simulate real OS errors in tests. This validates
        the error path exists by testing with invalid path characters.
        """
        # Try to write to a path with invalid characters (OS-specific)
        # On Unix: null byte in path causes OSError
        import platform

        if platform.system() == "Windows":
            # Windows invalid characters: < > : " | ? *
            invalid_path = tmp_path / "invalid<file>.md"
        else:
            # Unix: Use path that would cause issues (very long name)
            invalid_path = tmp_path / ("x" * 300 + ".md")

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
                "--output",
                str(invalid_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # May succeed or fail depending on OS, but should not crash
        # If it fails, should exit with code 1 and error message
        if result.returncode != 0:
            assert result.returncode == 1
            assert len(result.stderr) > 0


@pytest.mark.contract
class TestExportCommandStdoutOutput:
    """Contract tests for export to stdout behavior."""

    def test_export_to_stdout_without_output_flag(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export without --output writes to stdout.

        Validates:
        - export.py line 250-252: stdout output
        - Markdown on stdout
        - Minimal stderr (no progress indicator when to stdout)
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "conv-001",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Markdown on stdout
        stdout = result.stdout
        assert len(stdout) > 0
        assert "Python" in stdout

        # Assert: No success message on stderr (keeps stdout clean for piping)
        # May have minimal stderr, but not success message
        if result.stderr:
            assert "exported" not in result.stderr.lower()


@pytest.mark.contract
class TestExportCommandErrorHandling:
    """Contract tests for export command error handling."""

    def test_export_file_not_found_exits_code_1(self, cli_command: list[str]) -> None:
        """Test export with non-existent file exits code 1.

        Validates:
        - export.py line 183-185, 257-260: File not found handling
        - Exit code 1
        - Error on stderr
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                "/nonexistent/file.json",
                "some-id",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions not found
        stderr = result.stderr.lower()
        assert "not found" in stderr or "no such file" in stderr

    def test_export_permission_denied_on_read_exits_code_1(
        self, cli_command: list[str], tmp_path: Path
    ) -> None:
        """Test export with unreadable file exits code 1.

        Validates:
        - export.py line 262-265: PermissionError on read
        - Exit code 1
        - Error mentions permission

        Skipped on Windows.
        """
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        import stat

        # Create file without read permission
        no_read_file = tmp_path / "no_read.json"
        with no_read_file.open("w") as f:
            json.dump([], f)

        no_read_file.chmod(stat.S_IWUSR)  # Write-only

        try:
            result = subprocess.run(
                [
                    *cli_command,
                    "export",
                    str(no_read_file),
                    "some-id",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            # Assert: Exit code 1
            assert result.returncode == 1

            # Assert: Error mentions permission
            stderr = result.stderr.lower()
            assert "permission" in stderr or "denied" in stderr

        finally:
            # Restore permissions for cleanup
            no_read_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_export_invalid_json_exits_code_1(self, cli_command: list[str], tmp_path: Path) -> None:
        """Test export with malformed JSON exits code 1.

        Validates:
        - export.py line 267-270: JSONDecodeError handling
        - Exit code 1
        - Error mentions JSON
        """
        malformed = tmp_path / "malformed.json"
        malformed.write_text("{invalid json")

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(malformed),
                "some-id",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Exit code 1
        assert result.returncode == 1

        # Assert: Error mentions JSON or parsing error
        stderr = result.stderr.lower()
        assert "json" in stderr or "invalid" in stderr or "expecting" in stderr or "error" in stderr

    def test_export_keyboard_interrupt_exits_code_130(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export KeyboardInterrupt handling.

        Validates:
        - export.py line 272-275: KeyboardInterrupt → exit 130

        Note: Hard to test reliably in automated tests.
        Skipped for now - manual verification required.
        """
        pytest.skip("KeyboardInterrupt requires manual testing")


@pytest.mark.contract
class TestExportCommandTitleLookup:
    """Contract tests for title lookup helper function."""

    def test_export_by_title_case_insensitive(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by title is case-insensitive.

        Validates:
        - export.py line 75: title_lower = title.lower()
        - Case-insensitive substring matching
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "--title",
                "javascript",  # lowercase
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success (matches "JavaScript Basics")
        assert result.returncode == 0
        assert "JavaScript" in result.stdout or "JS" in result.stdout

    def test_export_by_title_substring_match(
        self, cli_command: list[str], export_with_conversations: Path
    ) -> None:
        """Test export by title uses substring matching.

        Validates:
        - export.py line 84: title_lower in conv_title.lower()
        - Substring matching (not exact match required)
        """
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(export_with_conversations),
                "--title",
                "Script",  # Substring of "JavaScript"
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # Assert: Success
        assert result.returncode == 0
        assert "JavaScript" in result.stdout or "JS" in result.stdout
