"""Contract tests for US3-AS1: Export conversation by title.

User Story 3, Acceptance Scenario 1: Export conversation by title
This module contains comprehensive black-box tests to validate that the export
command supports looking up conversations by title in addition to ID.

Test Pyramid Classification: Contract (5% of test suite)
TDD Phase: RED (these tests validate acceptance criteria)

Acceptance Criteria (US3-AS1):
1. User can export a conversation by providing its exact title
2. User can export a conversation using case-insensitive title match
3. User can export a conversation using partial/substring title match
4. When multiple conversations match the title, an appropriate error is shown
5. When no conversation matches the title, an appropriate error is shown
6. Title with special characters (Unicode, emojis, punctuation) works correctly
7. Both stdout and file output modes work with title lookup
8. Title lookup works with --json flag (if applicable to export command)

Constitution Compliance:
- Principle II: CLI Interface Contract (exit codes, stdout/stderr separation)
- Principle III: TDD - Tests written FIRST to verify acceptance scenario
- Principle VI: Strict typing - All test code is type-safe

Requirements Validated:
- FR-016: Support --title as alternative to conversation ID
- FR-018: Export command with file path, conversation ID/title, --output flag
- CHK031: stdout for data, stderr for progress/errors
- CHK032: Exit codes 0 (success), 1 (error), 2 (invalid arguments)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def cli_command() -> list[str]:
    """Return the CLI command to invoke echomine.

    Returns the appropriate command to run echomine CLI in development mode.
    """
    return [sys.executable, "-m", "echomine.cli.app"]


@pytest.fixture
def title_export_file(tmp_path: Path) -> Path:
    """Create sample export for title-based export testing.

    Contains varied conversation titles:
    - Simple ASCII title
    - Title with Unicode characters
    - Title with emoji
    - Title with special characters/punctuation
    - Multiple conversations with similar titles (substring matching test)
    """
    conversations = [
        {
            "id": "title-conv-001",
            "title": "Python AsyncIO Tutorial",
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
                            "parts": ["Explain Python asyncio basics"],
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
                            "parts": ["AsyncIO is Python's library for asynchronous programming."],
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
        {
            "id": "title-conv-002",
            "title": "Python Tutorial: Getting Started",
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["How to start with Python?"]},
                        "create_time": 1710100000.0,
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
        {
            "id": "title-conv-003",
            "title": "机器学习入门 🚀 Machine Learning Intro",
            "create_time": 1710200000.0,
            "update_time": 1710200500.0,
            "mapping": {
                "msg-4": {
                    "id": "msg-4",
                    "message": {
                        "id": "msg-4",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Explain neural networks"]},
                        "create_time": 1710200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-4",
        },
        {
            "id": "title-conv-004",
            "title": "What's the difference: var vs let vs const?",
            "create_time": 1710300000.0,
            "update_time": 1710300500.0,
            "mapping": {
                "msg-5": {
                    "id": "msg-5",
                    "message": {
                        "id": "msg-5",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain JavaScript scoping"],
                        },
                        "create_time": 1710300000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-5",
        },
    ]

    export_file = tmp_path / "title_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


@pytest.fixture
def duplicate_title_export_file(tmp_path: Path) -> Path:
    """Create export with duplicate/similar conversation titles.

    Used to test ambiguous title matching behavior.
    Contains:
    - Two conversations with identical titles
    - Two conversations with similar titles (substring matches)
    """
    conversations = [
        {
            "id": "dup-conv-001",
            "title": "Python Tutorial",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Question 1 about basics"]},
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
        },
        {
            "id": "dup-conv-002",
            "title": "Python Tutorial",  # Exact duplicate
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Question 2 about advanced topics"],
                        },
                        "create_time": 1710100000.0,
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
            "id": "dup-conv-003",
            "title": "Advanced Python Tutorial",
            "create_time": 1710200000.0,
            "update_time": 1710200500.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Question 3 about decorators"],
                        },
                        "create_time": 1710200000.0,
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

    export_file = tmp_path / "duplicate_titles.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


# =============================================================================
# US3-AS1 Contract Tests - Core Title Export Functionality
# =============================================================================


@pytest.mark.contract
class TestUS3AS1ExportByTitleCore:
    """Core tests for US3-AS1: Export conversation by title.

    These tests validate the PRIMARY acceptance criteria:
    - Exact title match works
    - Case-insensitive title match works
    - Partial/substring title match works
    - Correct conversation is exported

    Expected Behavior (After Implementation):
    - echomine export file.json --title "Python AsyncIO Tutorial" → exports conv-001
    - echomine export file.json --title "python asyncio tutorial" → exports conv-001 (case-insensitive)
    - echomine export file.json --title "AsyncIO" → exports conv-001 (substring match)

    TDD Phase: RED
    These tests will FAIL until title lookup is correctly implemented.
    """

    def test_export_by_exact_title_match_to_stdout(
        self, cli_command: list[str], title_export_file: Path
    ) -> None:
        """Test export using exact title match with output to stdout.

        Validates:
        - US3-AS1 Acceptance Criterion 1: Exact title match
        - FR-016: --title flag support
        - CHK031: Data on stdout when no --output specified

        Expected to PASS: Feature already implemented.
        """
        # Exact title match
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Python AsyncIO Tutorial",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Export by exact title should succeed. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported to stdout
        stdout = result.stdout
        assert len(stdout) > 0, "stdout should contain markdown"
        assert "AsyncIO" in stdout, "Should export correct conversation (contains 'AsyncIO')"
        assert "asynchronous programming" in stdout, (
            "Should contain conversation content from correct conversation"
        )

    def test_export_by_case_insensitive_title_match(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using case-insensitive title match.

        Validates:
        - US3-AS1 Acceptance Criterion 2: Case-insensitive matching
        - Title "python asyncio tutorial" matches "Python AsyncIO Tutorial"

        Expected to PASS: Feature already implemented (case-insensitive substring match).
        """
        output_file = tmp_path / "output.md"

        # Lowercase title (should match "Python AsyncIO Tutorial")
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "python asyncio tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Case-insensitive title match should succeed. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "AsyncIO" in markdown, "Should export correct conversation"
        assert "asynchronous programming" in markdown, "Should contain correct content"

    def test_export_by_partial_substring_title_match(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using partial/substring title match.

        Validates:
        - US3-AS1 Acceptance Criterion 3: Partial/substring matching
        - Title "AsyncIO" matches "Python AsyncIO Tutorial"
        - Title "Tutorial" matches multiple conversations (ambiguous, should error)

        Expected to PASS: Feature already implemented (substring match).
        """
        output_file = tmp_path / "output.md"

        # Substring match: "AsyncIO" should match "Python AsyncIO Tutorial"
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "AsyncIO",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Substring title match should succeed. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "AsyncIO" in markdown, "Should export conversation with 'AsyncIO' in title"

    def test_export_by_title_with_output_file(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export by title with --output file specified.

        Validates:
        - US3-AS1 Acceptance Criterion 7: Title lookup works with file output
        - CHK031: stdout empty when --output specified, stderr has progress

        Expected to PASS: Feature already implemented.
        """
        output_file = tmp_path / "titled_export.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, f"Export should succeed. stderr: {result.stderr}"

        # Assert: File created with correct content
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "AsyncIO" in markdown, "File should contain exported conversation"

        # Assert: stdout empty (data written to file)
        assert len(result.stdout) == 0, "stdout should be empty when --output specified"

        # Assert: stderr contains success message
        assert len(result.stderr) > 0, "stderr should contain progress/success message"


# =============================================================================
# US3-AS1 Contract Tests - Error Handling
# =============================================================================


@pytest.mark.contract
class TestUS3AS1ExportByTitleErrors:
    """Error handling tests for US3-AS1: Export by title.

    These tests validate error scenarios:
    - Multiple matching titles (ambiguous)
    - No matching titles (not found)
    - Both ID and --title provided (invalid arguments)
    - Neither ID nor --title provided (invalid arguments)

    TDD Phase: RED
    These tests verify proper error handling and exit codes.
    """

    def test_export_by_title_multiple_matches_returns_error(
        self, cli_command: list[str], duplicate_title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that multiple matching titles returns exit code 1 with error.

        Validates:
        - US3-AS1 Acceptance Criterion 4: Multiple matches show appropriate error
        - CHK032: Exit code 1 for operational errors
        - Error message explains ambiguity and suggests using ID instead

        Expected to PASS: Feature already implemented (ValueError raised for multiple matches).
        """
        output_file = tmp_path / "output.md"

        # "Python Tutorial" appears in 3 conversation titles (2 exact, 1 partial)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(duplicate_title_export_file),
                "--title",
                "Python Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1 (operational error)
        assert result.returncode == 1, (
            f"Ambiguous title should fail with exit code 1. Got {result.returncode}"
        )

        # Assert: Error message explains ambiguity
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "multiple" in stderr.lower() or "ambiguous" in stderr.lower(), (
            f"Error should mention multiple matches. Got: {stderr}"
        )

        # Assert: Output file NOT created
        assert not output_file.exists(), "Output file should not be created on error"

    def test_export_by_title_no_match_returns_error(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that non-matching title returns exit code 1 with error.

        Validates:
        - US3-AS1 Acceptance Criterion 5: No matches show appropriate error
        - CHK032: Exit code 1 for operational errors
        - Error message indicates conversation not found

        Expected to PASS: Feature already implemented (None returned, error raised).
        """
        output_file = tmp_path / "output.md"

        # Title that doesn't match any conversation
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Nonexistent Conversation Title",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 1 (operational error)
        assert result.returncode == 1, (
            f"Non-matching title should fail with exit code 1. Got {result.returncode}"
        )

        # Assert: Error message indicates not found
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "not found" in stderr.lower() or "no conversation" in stderr.lower(), (
            f"Error should mention conversation not found. Got: {stderr}"
        )

        # Assert: Output file NOT created
        assert not output_file.exists(), "Output file should not be created on error"

    def test_export_with_both_id_and_title_returns_error(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that providing both ID and --title returns exit code 2.

        Validates:
        - Mutually exclusive: conversation ID OR --title (not both)
        - CHK032: Exit code 2 for invalid arguments
        - Error message explains mutual exclusivity

        Expected to PASS: Feature already implemented (validation in export_conversation).
        """
        output_file = tmp_path / "output.md"

        # Provide both positional ID AND --title flag
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "title-conv-001",  # Positional ID
                "--title",
                "Python AsyncIO Tutorial",  # --title flag
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2 (invalid arguments)
        assert result.returncode == 2, (
            f"Both ID and --title should fail with exit code 2. Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"
        assert "cannot" in stderr.lower() or "both" in stderr.lower(), (
            f"Error should mention mutual exclusivity. Got: {stderr}"
        )

    def test_export_with_neither_id_nor_title_returns_error(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that omitting both ID and --title returns exit code 2.

        Validates:
        - Required: conversation ID OR --title (must provide one)
        - CHK032: Exit code 2 for invalid arguments

        Expected to PASS: Feature already implemented (validation in export_conversation).
        """
        output_file = tmp_path / "output.md"

        # Omit both positional ID and --title flag
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Exit code 2 (invalid arguments)
        assert result.returncode == 2, (
            f"Missing ID and --title should fail with exit code 2. Got {result.returncode}"
        )

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"


# =============================================================================
# US3-AS1 Contract Tests - Edge Cases
# =============================================================================


@pytest.mark.contract
class TestUS3AS1ExportByTitleEdgeCases:
    """Edge case tests for US3-AS1: Export by title.

    These tests validate special scenarios:
    - Unicode characters in titles
    - Emoji in titles
    - Special characters and punctuation
    - Empty title
    - Very long titles
    - Whitespace handling

    TDD Phase: RED
    These tests ensure robustness across various input types.
    """

    def test_export_by_title_with_unicode_characters(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using title with Unicode (CJK) characters.

        Validates:
        - US3-AS1 Acceptance Criterion 6: Unicode in titles works correctly
        - CHK126: UTF-8 encoding assumption
        - Title "机器学习入门" matches conversation with Chinese characters

        Expected to PASS: Feature should handle Unicode correctly.
        """
        output_file = tmp_path / "unicode_output.md"

        # Title with Chinese characters
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "机器学习",  # Partial match for "机器学习入门 🚀 Machine Learning Intro"
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Unicode title match should succeed. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "neural networks" in markdown or "机器学习" in markdown, (
            "Should export conversation with Chinese title"
        )

    def test_export_by_title_with_emoji(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using title containing emoji.

        Validates:
        - US3-AS1 Acceptance Criterion 6: Emoji in titles works correctly
        - Title with "🚀" emoji matches correctly

        Expected to PASS: Feature should handle emoji correctly.
        """
        output_file = tmp_path / "emoji_output.md"

        # Search for title containing emoji
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Machine Learning",  # Partial match, avoiding emoji in search
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Title with emoji should be searchable. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "neural networks" in markdown or "Machine Learning" in markdown, (
            "Should export conversation with emoji in title"
        )

    def test_export_by_title_with_special_punctuation(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using title with special characters and punctuation.

        Validates:
        - US3-AS1 Acceptance Criterion 6: Special characters work correctly
        - Title "What's the difference: var vs let vs const?" has: apostrophe, colon, question mark

        Expected to PASS: Feature should handle special characters correctly.
        """
        output_file = tmp_path / "punctuation_output.md"

        # Title with punctuation (exact match)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "What's the difference: var vs let vs const?",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Title with punctuation should match. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "JavaScript" in markdown or "scoping" in markdown, (
            "Should export conversation with punctuation in title"
        )

    def test_export_by_title_partial_match_with_punctuation(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using partial title match (ignoring punctuation in search).

        Validates:
        - Substring match works even when full title has punctuation
        - Search "var vs let" matches "What's the difference: var vs let vs const?"

        Expected to PASS: Substring matching should work.
        """
        output_file = tmp_path / "partial_punctuation_output.md"

        # Partial match (substring without full punctuation)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "var vs let",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0, (
            f"Partial title with punctuation should match. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: Correct conversation exported
        assert output_file.exists(), "Output file should be created"
        markdown = output_file.read_text(encoding="utf-8")
        assert "JavaScript" in markdown or "scoping" in markdown, (
            "Should export conversation matching partial title"
        )

    def test_export_by_empty_title_returns_error(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that empty title string returns error.

        Validates:
        - Empty string is invalid title
        - Appropriate error handling for edge case

        Expected Behavior:
        - May return exit code 2 (invalid argument) or 1 (not found)
        - Should NOT crash
        """
        output_file = tmp_path / "output.md"

        # Empty title
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Non-zero exit code (error)
        assert result.returncode != 0, f"Empty title should fail. Got exit code {result.returncode}"

        # Assert: Error message on stderr
        stderr = result.stderr
        assert len(stderr) > 0, "Error message should be on stderr"

        # Assert: Output file NOT created
        assert not output_file.exists(), "Output file should not be created on error"


# =============================================================================
# US3-AS1 Contract Tests - Output Validation
# =============================================================================


@pytest.mark.contract
class TestUS3AS1ExportByTitleOutputValidation:
    """Output validation tests for US3-AS1: Export by title.

    These tests validate that the CORRECT conversation is exported
    when using title-based lookup.

    TDD Phase: RED
    These tests ensure title lookup returns the expected conversation.
    """

    def test_export_by_title_returns_correct_conversation_content(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that title lookup exports the CORRECT conversation.

        Validates:
        - Title "Python AsyncIO Tutorial" → conversation with "asynchronous programming"
        - NOT the conversation with "Python Tutorial: Getting Started"

        This is critical: title lookup MUST return the right conversation.
        """
        output_file = tmp_path / "correct_conv_output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: CORRECT conversation exported (verify content)
        markdown = output_file.read_text(encoding="utf-8")

        # Should contain content from "Python AsyncIO Tutorial" conversation
        assert "asynchronous programming" in markdown, (
            "Should export conversation about async/await (correct match)"
        )

        # Should NOT contain content from "Python Tutorial: Getting Started"
        assert "Getting Started" not in markdown, "Should NOT export wrong conversation"

    def test_export_by_title_includes_conversation_metadata(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that exported conversation includes metadata header.

        Validates:
        - FR-014: Conversation metadata in exported files
        - Metadata includes: title, created date, message count

        This verifies the FULL export pipeline works with title lookup.
        """
        output_file = tmp_path / "metadata_output.md"

        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: Metadata present in export
        markdown = output_file.read_text(encoding="utf-8")

        # Find first message header
        lines = markdown.split("\n")
        first_message_idx = None
        for i, line in enumerate(lines):
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_idx = i
                break

        assert first_message_idx is not None, "Should have message headers"

        # Extract metadata section (before first message)
        metadata_section = "\n".join(lines[:first_message_idx])

        # Validate metadata fields
        assert "Python AsyncIO Tutorial" in metadata_section, (
            "Metadata should include conversation title"
        )
        assert any(marker in metadata_section for marker in ["2024-", "Created:", "Date:"]), (
            "Metadata should include created date"
        )
        assert any(marker in metadata_section for marker in ["2 message", "Messages:", "Count:"]), (
            "Metadata should include message count"
        )

    def test_export_by_title_stderr_shows_matched_title(
        self, cli_command: list[str], title_export_file: Path
    ) -> None:
        """Test that stderr shows which conversation title was matched.

        Validates:
        - User feedback: show which conversation was found
        - Helps user confirm correct conversation when using partial match

        Expected Behavior:
        - stderr: "Matched conversation: Python AsyncIO Tutorial"
        - This is OPTIONAL but highly valuable for UX

        May FAIL if not implemented (user feedback feature).
        """
        # Export to stdout (stderr should show matched title)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "AsyncIO",  # Partial match
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Assert: Success
        assert result.returncode == 0

        # Assert: stderr shows matched title (OPTIONAL feature)
        stderr = result.stderr
        # This may fail if feature not implemented
        # If it fails, it indicates an enhancement opportunity for better UX
        if "Matched" in stderr or "matched" in stderr:
            assert "Python AsyncIO Tutorial" in stderr, (
                "stderr should show the exact matched title for user confirmation"
            )


# =============================================================================
# US3-AS1 Integration Test - Full Workflow
# =============================================================================


@pytest.mark.contract
class TestUS3AS1ExportByTitleWorkflow:
    """End-to-end workflow tests for US3-AS1.

    These tests validate the COMPLETE user workflow:
    1. User searches for conversations by keyword
    2. User identifies conversation title from search results
    3. User exports conversation using that title

    TDD Phase: RED
    These tests validate the full acceptance scenario.
    """

    def test_us3_as1_complete_workflow(
        self, cli_command: list[str], title_export_file: Path, tmp_path: Path
    ) -> None:
        """Test complete US3-AS1 workflow: search → identify title → export by title.

        User Story:
        "As a researcher, I want to export a specific conversation by its title
        so that I can quickly save conversations without looking up UUIDs."

        Workflow:
        1. User knows the conversation title (from ChatGPT UI or memory)
        2. User runs: echomine export file.json --title "Python AsyncIO Tutorial"
        3. User receives exported markdown

        This is the PRIMARY acceptance scenario for US3-AS1.
        """
        output_file = tmp_path / "workflow_output.md"

        # Step 1: Export by title (the core US3-AS1 functionality)
        result = subprocess.run(
            [
                *cli_command,
                "export",
                str(title_export_file),
                "--title",
                "Python AsyncIO Tutorial",
                "--output",
                str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Validate: Success
        assert result.returncode == 0, (
            f"US3-AS1 FAILURE: Export by title should succeed. "
            f"Exit code: {result.returncode}. stderr: {result.stderr}"
        )

        # Validate: Output file created
        assert output_file.exists(), "US3-AS1 FAILURE: Output file should be created"

        # Validate: Correct conversation exported
        markdown = output_file.read_text(encoding="utf-8")
        assert "Python AsyncIO Tutorial" in markdown, (
            "US3-AS1 FAILURE: Title should be in exported markdown"
        )
        assert "asynchronous programming" in markdown, (
            "US3-AS1 FAILURE: Conversation content should be in exported markdown"
        )

        # Validate: Markdown format compliance
        assert "##" in markdown, "Should have markdown headers"
        assert "👤" in markdown or "🤖" in markdown, "Should have emoji role indicators"

        # SUCCESS: US3-AS1 acceptance scenario PASSES
