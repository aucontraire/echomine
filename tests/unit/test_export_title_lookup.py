"""Unit tests for export command title lookup functionality.

Task: US3-AS1 - Export conversation by title (Unit Test Coverage)
Phase: RED (tests designed to validate implementation)

This module provides unit-level tests for the _find_conversation_by_title
helper function in the export command. These tests are WHITE BOX tests that
directly test the function implementation.

Test Pyramid Classification: Unit (70% of test suite)
These tests validate the title lookup logic in isolation.

Test Strategy:
- Test _find_conversation_by_title() function directly
- Validate exact match behavior
- Validate case-insensitive substring matching
- Validate multiple match error handling
- Validate no match handling
- Validate edge cases (empty title, Unicode, special characters)

Constitution Compliance:
- Principle III: TDD - Unit tests provide fast feedback
- Principle VI: Strict typing - All tests are type-safe
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.cli.commands.export import _find_conversation_by_title


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_export_file(tmp_path: Path) -> Path:
    """Create sample export with varied conversation titles for testing.

    Contains:
    - Simple ASCII titles
    - Similar titles (for substring matching tests)
    - Unicode titles
    - Titles with special characters
    """
    conversations = [
        {
            "id": "conv-001",
            "title": "Python AsyncIO Tutorial",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
        {
            "id": "conv-002",
            "title": "Python Tutorial: Getting Started",
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
        {
            "id": "conv-003",
            "title": "机器学习入门 🚀",
            "create_time": 1710200000.0,
            "update_time": 1710200500.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
        {
            "id": "conv-004",
            "title": "What's the difference: var vs let?",
            "create_time": 1710300000.0,
            "update_time": 1710300500.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
    ]

    export_file = tmp_path / "sample_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


@pytest.fixture
def duplicate_title_file(tmp_path: Path) -> Path:
    """Create export with duplicate titles for multiple match testing."""
    conversations = [
        {
            "id": "dup-001",
            "title": "Python Tutorial",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
        {
            "id": "dup-002",
            "title": "Python Tutorial",  # Exact duplicate
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
        {
            "id": "dup-003",
            "title": "Advanced Python Tutorial",  # Contains "Python Tutorial"
            "create_time": 1710200000.0,
            "update_time": 1710200500.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        },
    ]

    export_file = tmp_path / "duplicate_titles.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


# =============================================================================
# Unit Tests - _find_conversation_by_title Function
# =============================================================================


class TestFindConversationByTitleExactMatch:
    """Unit tests for exact title matching."""

    def test_exact_title_match_returns_id_and_title(
        self, sample_export_file: Path
    ) -> None:
        """Test exact title match returns tuple of (id, exact_title).

        Validates:
        - Exact match: "Python AsyncIO Tutorial" → ("conv-001", "Python AsyncIO Tutorial")
        - Return type is tuple[str, str]
        - ID and title are both returned
        """
        result = _find_conversation_by_title(sample_export_file, "Python AsyncIO Tutorial")

        # Assert: Returns tuple
        assert result is not None, "Exact match should return result"
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should return (id, title) tuple"

        # Assert: Correct conversation found
        conversation_id, exact_title = result
        assert conversation_id == "conv-001", "Should return correct conversation ID"
        assert exact_title == "Python AsyncIO Tutorial", "Should return exact title"

    def test_exact_match_case_sensitive_title(
        self, sample_export_file: Path
    ) -> None:
        """Test that exact title is returned with original casing.

        Validates:
        - Search is case-insensitive
        - Returned title preserves original casing from file
        """
        # Search with lowercase (case-insensitive match)
        result = _find_conversation_by_title(sample_export_file, "python asyncio tutorial")

        assert result is not None
        conversation_id, exact_title = result

        # Assert: Correct conversation found
        assert conversation_id == "conv-001"

        # Assert: Exact title preserves original casing
        assert exact_title == "Python AsyncIO Tutorial", (
            "Returned title should preserve original casing"
        )


class TestFindConversationByTitleCaseInsensitive:
    """Unit tests for case-insensitive matching."""

    def test_case_insensitive_lowercase_search(
        self, sample_export_file: Path
    ) -> None:
        """Test lowercase search matches title with mixed case."""
        result = _find_conversation_by_title(sample_export_file, "python asyncio tutorial")

        assert result is not None
        conversation_id, _ = result
        assert conversation_id == "conv-001", "Lowercase search should match"

    def test_case_insensitive_uppercase_search(
        self, sample_export_file: Path
    ) -> None:
        """Test uppercase search matches title with mixed case."""
        result = _find_conversation_by_title(sample_export_file, "PYTHON ASYNCIO TUTORIAL")

        assert result is not None
        conversation_id, _ = result
        assert conversation_id == "conv-001", "Uppercase search should match"

    def test_case_insensitive_mixed_case_search(
        self, sample_export_file: Path
    ) -> None:
        """Test mixed case search matches title."""
        result = _find_conversation_by_title(sample_export_file, "PyThOn AsynCIO tUtOrIaL")

        assert result is not None
        conversation_id, _ = result
        assert conversation_id == "conv-001", "Mixed case search should match"


class TestFindConversationByTitleSubstringMatch:
    """Unit tests for substring/partial matching."""

    def test_substring_match_returns_conversation(
        self, sample_export_file: Path
    ) -> None:
        """Test substring match returns conversation containing the substring.

        Validates:
        - "AsyncIO" matches "Python AsyncIO Tutorial"
        - Substring can appear anywhere in title
        """
        result = _find_conversation_by_title(sample_export_file, "AsyncIO")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-001"
        assert "AsyncIO" in exact_title

    def test_substring_at_beginning(
        self, sample_export_file: Path
    ) -> None:
        """Test substring at beginning of title matches.

        Note: "Python" matches MULTIPLE conversations:
        - "Python AsyncIO Tutorial"
        - "Python Tutorial: Getting Started"
        This should raise ValueError for ambiguity.
        """
        # This test documents current behavior: multiple matches raise ValueError
        with pytest.raises(ValueError, match="Multiple conversations"):
            _find_conversation_by_title(sample_export_file, "Python")

    def test_substring_at_end(
        self, sample_export_file: Path
    ) -> None:
        """Test substring at end of title matches.

        Note: "Tutorial" appears in multiple titles:
        - "Python AsyncIO Tutorial"
        - "Python Tutorial: Getting Started"
        This should raise ValueError for ambiguity.
        """
        # This test documents current behavior: multiple matches raise ValueError
        with pytest.raises(ValueError, match="Multiple conversations"):
            _find_conversation_by_title(sample_export_file, "Tutorial")

    def test_substring_in_middle(
        self, sample_export_file: Path
    ) -> None:
        """Test substring in middle of title matches."""
        result = _find_conversation_by_title(sample_export_file, "Getting Started")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-002"
        assert "Getting Started" in exact_title

    def test_unique_substring_returns_single_match(
        self, sample_export_file: Path
    ) -> None:
        """Test unique substring returns single match (no ambiguity)."""
        # "AsyncIO" only appears in one conversation
        result = _find_conversation_by_title(sample_export_file, "AsyncIO")

        assert result is not None
        conversation_id, _ = result
        assert conversation_id == "conv-001"


class TestFindConversationByTitleNoMatch:
    """Unit tests for no match scenarios."""

    def test_nonexistent_title_returns_none(
        self, sample_export_file: Path
    ) -> None:
        """Test that non-matching title returns None.

        Validates:
        - Return value is None (not exception)
        - Function handles no match gracefully
        """
        result = _find_conversation_by_title(sample_export_file, "Nonexistent Title")

        assert result is None, "Non-matching title should return None"

    def test_empty_export_file_returns_none(self, tmp_path: Path) -> None:
        """Test empty export file (no conversations) returns None."""
        empty_file = tmp_path / "empty.json"
        with empty_file.open("w") as f:
            json.dump([], f)

        result = _find_conversation_by_title(empty_file, "Any Title")

        assert result is None, "Empty export should return None"

    def test_partial_match_not_found_returns_none(
        self, sample_export_file: Path
    ) -> None:
        """Test substring that doesn't match any title returns None."""
        result = _find_conversation_by_title(sample_export_file, "Nonexistent Substring")

        assert result is None


class TestFindConversationByTitleMultipleMatches:
    """Unit tests for multiple match scenarios (ambiguous titles)."""

    def test_duplicate_exact_titles_raises_error(
        self, duplicate_title_file: Path
    ) -> None:
        """Test that duplicate exact titles raise ValueError.

        Validates:
        - Multiple exact matches → ValueError
        - Error message mentions "Multiple conversations"
        - Error message includes match count
        """
        with pytest.raises(ValueError, match="Multiple conversations"):
            _find_conversation_by_title(duplicate_title_file, "Python Tutorial")

    def test_multiple_substring_matches_raises_error(
        self, duplicate_title_file: Path
    ) -> None:
        """Test that substring matching multiple titles raises ValueError.

        "Python Tutorial" appears in:
        - "Python Tutorial" (exact, 2 times)
        - "Advanced Python Tutorial" (substring)
        Total: 3 matches → ambiguous
        """
        with pytest.raises(ValueError, match="Multiple conversations"):
            _find_conversation_by_title(duplicate_title_file, "Python Tutorial")

    def test_error_message_includes_match_count(
        self, duplicate_title_file: Path
    ) -> None:
        """Test that error message includes number of matches."""
        try:
            _find_conversation_by_title(duplicate_title_file, "Python Tutorial")
            pytest.fail("Should raise ValueError")
        except ValueError as e:
            error_message = str(e)
            # Should mention multiple matches
            assert "Multiple conversations" in error_message or "multiple" in error_message
            # Should include count (3 matches in this case)
            assert "3" in error_message, "Error should mention match count"

    def test_error_suggests_using_id(
        self, duplicate_title_file: Path
    ) -> None:
        """Test that error message suggests using conversation ID instead."""
        try:
            _find_conversation_by_title(duplicate_title_file, "Python Tutorial")
            pytest.fail("Should raise ValueError")
        except ValueError as e:
            error_message = str(e)
            # Should suggest using ID
            assert "ID" in error_message or "id" in error_message, (
                "Error should suggest using conversation ID instead"
            )


class TestFindConversationByTitleEdgeCases:
    """Unit tests for edge cases."""

    def test_unicode_title_matching(
        self, sample_export_file: Path
    ) -> None:
        """Test matching titles with Unicode (CJK) characters."""
        result = _find_conversation_by_title(sample_export_file, "机器学习")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-003"
        assert "机器学习" in exact_title

    def test_emoji_in_title_matching(
        self, sample_export_file: Path
    ) -> None:
        """Test matching titles containing emoji."""
        result = _find_conversation_by_title(sample_export_file, "🚀")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-003"
        assert "🚀" in exact_title

    def test_special_characters_in_title(
        self, sample_export_file: Path
    ) -> None:
        """Test matching titles with special characters and punctuation."""
        result = _find_conversation_by_title(sample_export_file, "What's the difference")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-004"
        assert "What's the difference" in exact_title

    def test_colon_in_title_matching(
        self, sample_export_file: Path
    ) -> None:
        """Test matching titles with colon character."""
        result = _find_conversation_by_title(sample_export_file, "var vs let")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-004"

    def test_whitespace_in_search_query(
        self, sample_export_file: Path
    ) -> None:
        """Test search query with extra whitespace."""
        # Extra spaces should still match
        result = _find_conversation_by_title(sample_export_file, "Python  AsyncIO  Tutorial")

        # Current implementation: exact substring match
        # Extra spaces won't match (no normalization)
        # This documents current behavior
        assert result is None, "Extra whitespace should not match (no normalization)"

    def test_leading_trailing_whitespace(
        self, sample_export_file: Path
    ) -> None:
        """Test search query with leading/trailing whitespace."""
        # Leading/trailing whitespace
        result = _find_conversation_by_title(sample_export_file, "  AsyncIO  ")

        # Current implementation: no whitespace stripping
        # This will not match because of leading/trailing spaces
        assert result is None, "Leading/trailing whitespace should not match (no stripping)"

    def test_empty_title_search(
        self, sample_export_file: Path
    ) -> None:
        """Test empty string title search."""
        # Empty string should match all titles (substring of everything)
        # OR could return None as invalid input
        # This documents current behavior
        with pytest.raises(ValueError, match="Multiple conversations"):
            _find_conversation_by_title(sample_export_file, "")


class TestFindConversationByTitleFileHandling:
    """Unit tests for file handling edge cases."""

    def test_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        """Test that missing file raises FileNotFoundError."""
        nonexistent_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            _find_conversation_by_title(nonexistent_file, "Any Title")

    def test_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """Test that malformed JSON raises json.JSONDecodeError."""
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            _find_conversation_by_title(malformed_file, "Any Title")

    def test_single_conversation_export_works(self, tmp_path: Path) -> None:
        """Test that single conversation (not array) is handled correctly.

        Some exports may be a single conversation object instead of an array.
        The function should handle both formats.
        """
        single_conv = {
            "id": "single-conv",
            "title": "Single Conversation",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        }

        single_file = tmp_path / "single.json"
        with single_file.open("w") as f:
            json.dump(single_conv, f)

        result = _find_conversation_by_title(single_file, "Single Conversation")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "single-conv"
        assert exact_title == "Single Conversation"

    def test_conversation_missing_title_field_skipped(self, tmp_path: Path) -> None:
        """Test that conversations without title field are skipped gracefully."""
        conversations = [
            {
                "id": "conv-001",
                # Missing title field
                "create_time": 1710000000.0,
                "update_time": 1710001000.0,
                "mapping": {},
            },
            {
                "id": "conv-002",
                "title": "Valid Conversation",
                "create_time": 1710100000.0,
                "update_time": 1710100500.0,
                "mapping": {},
            },
        ]

        export_file = tmp_path / "missing_title.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Should find conv-002, skip conv-001
        result = _find_conversation_by_title(export_file, "Valid Conversation")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "conv-002"

    def test_conversation_missing_id_field_skipped(self, tmp_path: Path) -> None:
        """Test that conversations without id/conversation_id are skipped gracefully."""
        conversations = [
            {
                # Missing id field
                "title": "Missing ID",
                "create_time": 1710000000.0,
                "update_time": 1710001000.0,
                "mapping": {},
            },
            {
                "id": "conv-002",
                "title": "Valid Conversation",
                "create_time": 1710100000.0,
                "update_time": 1710100500.0,
                "mapping": {},
            },
        ]

        export_file = tmp_path / "missing_id.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        # Should find conv-002, skip conversation without ID
        result = _find_conversation_by_title(export_file, "Valid Conversation")

        assert result is not None
        conversation_id, _ = result
        assert conversation_id == "conv-002"

    def test_conversation_id_field_alternative(self, tmp_path: Path) -> None:
        """Test that 'conversation_id' field is accepted in addition to 'id'."""
        conversations = [
            {
                "conversation_id": "alt-conv-001",  # Alternative field name
                "title": "Alternative ID Field",
                "create_time": 1710000000.0,
                "update_time": 1710001000.0,
                "mapping": {},
            }
        ]

        export_file = tmp_path / "alt_id.json"
        with export_file.open("w") as f:
            json.dump(conversations, f)

        result = _find_conversation_by_title(export_file, "Alternative ID Field")

        assert result is not None
        conversation_id, exact_title = result
        assert conversation_id == "alt-conv-001"
