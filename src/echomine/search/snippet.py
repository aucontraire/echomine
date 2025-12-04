"""Snippet extraction for search results (FR-021-025).

This module provides functions for extracting context snippets from
matched messages for display in search results.

Constitution Compliance:
- Principle I: Library-first (pure functions, no side effects)
- Principle VI: Strict typing (mypy --strict compliant)
- FR-022: Snippets ~100 characters with "..." suffix
- FR-023: Multiple matches show "+N more" indicator
- FR-025: Graceful handling of malformed content with fallback

Example:
    ```python
    from echomine.search.snippet import extract_snippet, extract_snippet_from_messages

    # Simple extraction
    snippet = extract_snippet(
        "This is a message about Python programming.",
        ["python"],
    )
    # Returns: "This is a message about Python programming."

    # With match count indicator
    snippet = extract_snippet(
        "Python is great. Python again.",
        ["python"],
        match_count=2,
    )
    # Returns: "Python is great. Python again. (+1 more)"
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from echomine.models.message import Message


# Constants
SNIPPET_MAX_LENGTH = 100
FALLBACK_EMPTY = "[Content unavailable]"
FALLBACK_NO_MATCH = "[No content matched]"


def extract_snippet(
    content: str,
    keywords: list[str],
    match_count: int | None = None,
) -> str:
    """Extract a ~100 character snippet from content.

    Finds the first occurrence of a matched keyword and extracts surrounding
    context. If no keyword is found, returns the beginning of the content.

    Args:
        content: Message content to extract snippet from
        keywords: Keywords that were matched (for context positioning)
        match_count: Optional count of total matches for "+N more" indicator

    Returns:
        Snippet string (~100 chars) with optional ellipsis and match indicator

    Requirements:
        - FR-022: Snippets ~100 characters with "..." suffix
        - FR-023: Multiple matches show "+N more" indicator
        - FR-025: Graceful handling with fallback text

    Example:
        >>> extract_snippet("Python is a great language.", ["python"])
        'Python is a great language.'

        >>> long_text = "Python is " + "great " * 50 + "language."
        >>> snippet = extract_snippet(long_text, ["python"])
        >>> len(snippet) <= 110
        True
    """
    # Handle empty or whitespace-only content (FR-025)
    if not content or not content.strip():
        return FALLBACK_EMPTY

    content = content.strip()

    # Find first keyword match position (case-insensitive)
    match_pos = -1
    content_lower = content.lower()

    for keyword in keywords:
        if keyword:
            pos = content_lower.find(keyword.lower())
            if pos != -1:
                if match_pos == -1 or pos < match_pos:
                    match_pos = pos
                break  # Use first keyword's first match

    # Extract snippet around the match position
    if match_pos >= 0:
        # Center snippet around keyword
        start = max(0, match_pos - 20)  # Some leading context
        end = start + SNIPPET_MAX_LENGTH
    else:
        # No keyword match - return beginning of content
        start = 0
        end = SNIPPET_MAX_LENGTH

    # Extract the snippet
    snippet = content[start:end]

    # Add ellipsis if truncated
    if end < len(content):
        snippet = snippet.rstrip() + "..."

    # Add leading ellipsis if we started mid-content
    if start > 0:
        # Find first word boundary
        space_pos = snippet.find(" ")
        if space_pos > 0 and space_pos < 20:
            snippet = "..." + snippet[space_pos + 1 :]
        else:
            snippet = "..." + snippet

    # Add "+N more" indicator for multiple matches (FR-023)
    if match_count is not None and match_count > 1:
        more_count = match_count - 1
        indicator = f" (+{more_count} more)"
        snippet = snippet + indicator

    return snippet


def extract_snippet_from_messages(
    messages: list[Message],
    keywords: list[str],
    matched_message_ids: list[str],
) -> tuple[str, int]:
    """Extract snippet from the first matched message.

    Finds the first message in matched_message_ids and extracts a snippet
    from its content.

    Args:
        messages: All messages in the conversation
        keywords: Keywords that were matched
        matched_message_ids: IDs of messages containing matches

    Returns:
        Tuple of (snippet, match_count) where:
        - snippet: Extracted text snippet
        - match_count: Number of messages that matched

    Requirements:
        - FR-022: Snippets ~100 characters
        - FR-023: Multiple matches tracked for indicator
        - FR-025: Fallback for empty/missing content

    Example:
        >>> from echomine.models.message import Message
        >>> from datetime import datetime, timezone
        >>> msgs = [Message(id="m1", role="user", content="Hello", timestamp=datetime.now(timezone.utc))]
        >>> snippet, count = extract_snippet_from_messages(msgs, ["hello"], ["m1"])
        >>> snippet
        'Hello'
        >>> count
        1
    """
    # Handle empty message list (FR-025)
    if not messages:
        return FALLBACK_EMPTY, 0

    # No matched messages - return fallback
    if not matched_message_ids:
        return FALLBACK_NO_MATCH, 0

    # Build message lookup
    msg_map = {m.id: m for m in messages}

    # Find first matched message
    first_matched_content: str | None = None
    for msg_id in matched_message_ids:
        if msg_id in msg_map:
            first_matched_content = msg_map[msg_id].content
            break

    if first_matched_content is None:
        return FALLBACK_NO_MATCH, 0

    # Extract snippet with match count
    match_count = len(matched_message_ids)
    snippet = extract_snippet(
        first_matched_content,
        keywords,
        match_count=match_count if match_count > 1 else None,
    )

    return snippet, match_count
