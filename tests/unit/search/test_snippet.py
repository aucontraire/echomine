"""Unit tests for snippet extraction (FR-021-025).

Tests the extract_snippet() function that extracts context snippets
from matched messages for search results.

Requirements:
    - FR-021: CLI human-readable output MUST include a snippet column
    - FR-022: Snippets MUST be truncated to ~100 characters with "..." suffix
    - FR-023: Multiple matches show first match with "+N more" indicator
    - FR-024: JSON output MUST include snippet field
    - FR-025: Graceful handling of malformed content with fallback text
"""

from __future__ import annotations

from datetime import UTC


# Import will fail until implementation is created - TDD red phase
# from echomine.search.snippet import extract_snippet


class TestSnippetExtraction:
    """Test basic snippet extraction functionality."""

    def test_extract_snippet_returns_first_100_chars(self) -> None:
        """Snippet is truncated to ~100 characters (FR-022)."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python is a " + "great " * 50 + "language."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        # Should be ~100 chars + "..."
        assert len(snippet) <= 110  # Allow some flexibility
        assert snippet.endswith("...")

    def test_extract_snippet_short_content_no_ellipsis(self) -> None:
        """Short content (≤100 chars) does not get ellipsis."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python is a great language."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        assert snippet == "Python is a great language."
        assert not snippet.endswith("...")

    def test_extract_snippet_contains_keyword(self) -> None:
        """Snippet contains at least one matched keyword."""
        from echomine.search.snippet import extract_snippet

        message_content = "I really enjoy learning about algorithms and data structures."
        keywords = ["algorithm"]

        snippet = extract_snippet(message_content, keywords)

        assert "algorithm" in snippet.lower()

    def test_extract_snippet_multiple_keywords_first_match(self) -> None:
        """Snippet centers around first matched keyword."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python is great. Later we discuss algorithms. Finally async."
        keywords = ["python", "algorithm", "async"]

        snippet = extract_snippet(message_content, keywords)

        # First keyword should be in snippet
        assert "python" in snippet.lower()

    def test_extract_snippet_case_insensitive(self) -> None:
        """Keyword matching is case-insensitive."""
        from echomine.search.snippet import extract_snippet

        message_content = "PYTHON is a great LANGUAGE for learning."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        assert "PYTHON" in snippet or "Python" in snippet or "python" in snippet

    def test_extract_snippet_empty_content(self) -> None:
        """Empty content returns fallback text (FR-025)."""
        from echomine.search.snippet import extract_snippet

        snippet = extract_snippet("", ["python"])

        assert snippet == "[Content unavailable]"

    def test_extract_snippet_no_keywords(self) -> None:
        """No keywords returns beginning of content."""
        from echomine.search.snippet import extract_snippet

        message_content = "This is a long message " + "content " * 20 + "end."

        snippet = extract_snippet(message_content, [])

        assert snippet.startswith("This is a long message")
        assert len(snippet) <= 110


class TestSnippetMultipleMatches:
    """Test "+N more matches" indicator (FR-023)."""

    def test_extract_snippet_with_match_count_multiple(self) -> None:
        """Multiple matches show count indicator."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python is great. Python again. Python everywhere."
        keywords = ["python"]

        # With match_count parameter
        snippet = extract_snippet(message_content, keywords, match_count=3)

        assert "+2 more" in snippet

    def test_extract_snippet_with_match_count_single(self) -> None:
        """Single match does not show count indicator."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python is great."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords, match_count=1)

        assert "+0 more" not in snippet
        assert "more" not in snippet.lower()

    def test_extract_snippet_match_count_zero(self) -> None:
        """Zero match count (title-only match) returns beginning of content."""
        from echomine.search.snippet import extract_snippet

        message_content = "This message has no matching keywords at all."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords, match_count=0)

        # Should return beginning of content
        assert snippet.startswith("This message")


class TestSnippetEdgeCases:
    """Test edge cases for snippet extraction."""

    def test_extract_snippet_whitespace_content(self) -> None:
        """Whitespace-only content returns fallback (FR-025)."""
        from echomine.search.snippet import extract_snippet

        snippet = extract_snippet("   \n\t   ", ["python"])

        assert snippet == "[Content unavailable]"

    def test_extract_snippet_special_characters(self) -> None:
        """Content with special characters handled correctly."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python uses `print()` and **bold** and <html>."
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        assert "Python" in snippet
        assert len(snippet) <= 110

    def test_extract_snippet_unicode_content(self) -> None:
        """Unicode content handled correctly."""
        from echomine.search.snippet import extract_snippet

        message_content = "Python支持Unicode。Python真棒！"
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        assert "Python" in snippet

    def test_extract_snippet_very_long_word(self) -> None:
        """Very long word (e.g., URL) handled correctly."""
        from echomine.search.snippet import extract_snippet

        long_url = "https://example.com/" + "a" * 150
        message_content = f"Python tutorial at {long_url}"
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        assert "Python" in snippet
        assert len(snippet) <= 150  # May include partial URL

    def test_extract_snippet_keyword_at_end(self) -> None:
        """Keyword at end of content included in snippet."""
        from echomine.search.snippet import extract_snippet

        message_content = "I " + "really " * 20 + "love Python"
        keywords = ["python"]

        snippet = extract_snippet(message_content, keywords)

        # Should center around keyword if possible
        assert "Python" in snippet or snippet.endswith("...")


class TestSnippetFromMessages:
    """Test snippet extraction from message lists."""

    def test_extract_snippet_from_messages_first_match(self) -> None:
        """Snippet comes from first message with match."""
        from datetime import datetime

        from echomine.models.message import Message
        from echomine.search.snippet import extract_snippet_from_messages

        messages = [
            Message(
                id="msg-1",
                role="user",
                content="Hello, how are you?",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Python is great for programming.",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="user",
                content="Tell me more about Python.",
                timestamp=datetime.now(UTC),
            ),
        ]
        keywords = ["python"]
        matched_message_ids = ["msg-2", "msg-3"]

        snippet, count = extract_snippet_from_messages(messages, keywords, matched_message_ids)

        assert "Python" in snippet
        assert count == 2  # Two messages matched

    def test_extract_snippet_from_messages_no_matches(self) -> None:
        """No matched messages returns fallback."""
        from datetime import datetime

        from echomine.models.message import Message
        from echomine.search.snippet import extract_snippet_from_messages

        messages = [
            Message(
                id="msg-1",
                role="user",
                content="Hello, how are you?",
                timestamp=datetime.now(UTC),
            ),
        ]
        keywords = ["python"]
        matched_message_ids: list[str] = []

        snippet, count = extract_snippet_from_messages(messages, keywords, matched_message_ids)

        assert snippet == "[No content matched]"
        assert count == 0

    def test_extract_snippet_from_messages_empty_list(self) -> None:
        """Empty message list returns fallback."""
        from echomine.models.message import Message
        from echomine.search.snippet import extract_snippet_from_messages

        messages: list[Message] = []
        keywords = ["python"]
        matched_message_ids: list[str] = []

        snippet, count = extract_snippet_from_messages(messages, keywords, matched_message_ids)

        assert snippet == "[Content unavailable]"
        assert count == 0
