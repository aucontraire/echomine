"""Integration tests for Claude adapter end-to-end functionality.

This test suite validates complete workflows from file parsing through search
and retrieval operations, ensuring all components work together correctly.

Test Coverage:
    - T097: End-to-end Claude export parsing
    - T098: Search with all filter types
    - T099: CLI auto-detection of Claude format

Constitution Compliance:
    - Principle III: Test-Driven Development
    - Principle VIII: Memory efficiency (O(1) streaming)
    - Principle I: Library-first architecture

Requirements:
    - FR-001 to FR-020: Conversation and message parsing
    - FR-021 to FR-035: Search support
    - FR-036 to FR-040: Conversation retrieval
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.models.search import SearchQuery


# ============================================================================
# T097: End-to-End Parsing Tests
# ============================================================================


def test_end_to_end_claude_parsing(claude_sample_export: Path) -> None:
    """Integration: Parse Claude export and verify complete data model.

    Validates the entire parsing pipeline from file reading through model
    instantiation, ensuring all required fields are present and valid.
    """
    adapter = ClaudeAdapter()
    conversations = list(adapter.stream_conversations(claude_sample_export))

    assert len(conversations) >= 1, "Test requires at least one conversation"

    for conv in conversations:
        # Verify conversation has required fields (BaseConversation protocol)
        assert conv.id, f"Conversation {conv} missing id"
        assert conv.title, f"Conversation {conv.id} missing title"
        assert conv.created_at, f"Conversation {conv.id} missing created_at"

        # Verify created_at is timezone-aware (FR-004, FR-005)
        assert conv.created_at.tzinfo is not None, (
            f"Conversation {conv.id} created_at must be timezone-aware"
        )
        # updated_at is Optional but should be timezone-aware if present
        if conv.updated_at is not None:
            assert conv.updated_at.tzinfo is not None, (
                f"Conversation {conv.id} updated_at must be timezone-aware"
            )

        # Verify messages exist (may be placeholder for empty conversations)
        assert conv.messages is not None, f"Conversation {conv.id} missing messages"
        assert len(conv.messages) >= 1, (
            f"Conversation {conv.id} has no messages (should have placeholder)"
        )

        # Verify messages have required fields
        for msg in conv.messages:
            assert msg.id, f"Message in {conv.id} missing id"
            assert msg.content is not None, f"Message {msg.id} missing content"
            assert msg.role in ("user", "assistant", "system"), (
                f"Message {msg.id} has invalid role: {msg.role}"
            )
            assert msg.timestamp, f"Message {msg.id} missing timestamp"
            assert msg.timestamp.tzinfo is not None, (
                f"Message {msg.id} timestamp must be timezone-aware"
            )

        # Verify message_count property matches
        expected_count = len(conv.messages)
        assert conv.message_count == expected_count, (
            f"Conversation {conv.id} message_count mismatch: "
            f"property={conv.message_count}, actual={expected_count}"
        )


def test_empty_conversation_handling(claude_empty_conversations: Path) -> None:
    """Integration: Parse export with empty conversations (FR-010).

    Empty conversations should parse successfully with placeholder messages
    to satisfy the Conversation model's min_length=1 requirement.
    """
    adapter = ClaudeAdapter()
    conversations = list(adapter.stream_conversations(claude_empty_conversations))

    assert len(conversations) >= 1, "Test requires at least one conversation"

    # Find conversations with placeholder messages
    empty_convs = [
        conv
        for conv in conversations
        if len(conv.messages) == 1 and conv.messages[0].metadata.get("is_placeholder") is True
    ]

    assert len(empty_convs) >= 1, (
        "Test fixture should contain at least one empty conversation with placeholder"
    )

    # Verify placeholder message structure
    for conv in empty_convs:
        placeholder = conv.messages[0]
        assert placeholder.role == "system"
        assert "(Empty conversation)" in placeholder.content
        assert placeholder.metadata.get("is_placeholder") is True


def test_role_normalization(claude_sample_export: Path) -> None:
    """Integration: Verify role normalization from sender field (FR-013).

    Claude exports use "human" and "assistant" as sender values,
    which must be normalized to "user" and "assistant" roles.
    """
    adapter = ClaudeAdapter()
    conversations = list(adapter.stream_conversations(claude_sample_export))

    assert len(conversations) >= 1

    # Find conversations with actual messages (not placeholders)
    real_messages = [
        msg
        for conv in conversations
        for msg in conv.messages
        if not msg.metadata.get("is_placeholder")
    ]

    assert len(real_messages) >= 2, "Test requires multiple real messages"

    # Verify all roles are normalized
    for msg in real_messages:
        assert msg.role in ("user", "assistant", "system"), (
            f"Message {msg.id} has invalid role: {msg.role}"
        )

    # Verify we have both user and assistant messages
    roles = {msg.role for msg in real_messages}
    assert "user" in roles, "Should have at least one user message"
    assert "assistant" in roles, "Should have at least one assistant message"


# ============================================================================
# T098: Search with All Filters Tests
# ============================================================================


def test_search_with_keywords(claude_sample_export: Path) -> None:
    """Integration: Search with keyword filtering.

    Validates BM25 keyword search produces relevant results with scores.
    """
    adapter = ClaudeAdapter()

    # Search with keywords likely to match
    query = SearchQuery(keywords=["python"])
    results = list(adapter.search(claude_sample_export, query))

    # Should have at least some results (fixture contains "python" keyword)
    assert len(results) >= 1, "Should find conversations matching 'python'"

    # Verify result structure
    for result in results:
        assert result.conversation, "Result missing conversation"
        assert 0.0 <= result.score <= 1.0, f"Score {result.score} outside [0, 1]"
        assert result.matched_message_ids is not None
        assert result.snippet is not None


def test_search_with_title_filter(claude_sample_export: Path) -> None:
    """Integration: Search with title filtering.

    Title filter performs case-insensitive substring matching on conversation titles.
    """
    adapter = ClaudeAdapter()

    # Search with title filter (case-insensitive)
    query = SearchQuery(title_filter="Code")
    results = list(adapter.search(claude_sample_export, query))

    # Verify all results match title filter
    for result in results:
        assert "code" in result.conversation.title.lower(), (
            f"Conversation title '{result.conversation.title}' does not contain 'code'"
        )


def test_search_with_date_range(claude_sample_export: Path) -> None:
    """Integration: Search with date range filtering.

    Date filters are inclusive on both ends (from_date <= date <= to_date).
    """
    adapter = ClaudeAdapter()

    # Search with date range
    from_date = date(2025, 10, 1)
    to_date = date(2025, 11, 30)

    query = SearchQuery(from_date=from_date, to_date=to_date)
    results = list(adapter.search(claude_sample_export, query))

    # Verify all results fall within date range
    for result in results:
        conv_date = result.conversation.created_at.date()
        assert from_date <= conv_date <= to_date, (
            f"Conversation {result.conversation.id} date {conv_date} "
            f"outside range [{from_date}, {to_date}]"
        )


def test_search_with_message_count_filter(claude_sample_export: Path) -> None:
    """Integration: Search with message count filtering.

    Message count filters are inclusive (min_messages <= count <= max_messages).
    """
    adapter = ClaudeAdapter()

    # Search for conversations with 2-5 messages
    query = SearchQuery(min_messages=2, max_messages=5)
    results = list(adapter.search(claude_sample_export, query))

    # Verify all results have message counts in range
    for result in results:
        msg_count = result.conversation.message_count
        # Exclude placeholder messages from count
        real_msg_count = len(
            [m for m in result.conversation.messages if not m.metadata.get("is_placeholder")]
        )

        assert 2 <= real_msg_count <= 5, (
            f"Conversation {result.conversation.id} has {real_msg_count} messages, expected 2-5"
        )


def test_search_with_role_filter(claude_sample_export: Path) -> None:
    """Integration: Search with role filtering.

    Role filter restricts search to messages from specific role only.
    """
    adapter = ClaudeAdapter()

    # Search only in user messages
    query = SearchQuery(keywords=["binary"], role_filter="user")
    results = list(adapter.search(claude_sample_export, query))

    # Verify matched messages are from user role
    for result in results:
        assert len(result.matched_message_ids) > 0, "Should have at least one matched message"

        # Find matched messages and verify roles
        matched_messages = [
            msg for msg in result.conversation.messages if msg.id in result.matched_message_ids
        ]

        for msg in matched_messages:
            assert msg.role == "user", (
                f"Matched message {msg.id} has role '{msg.role}', expected 'user'"
            )


def test_search_with_combined_filters(claude_sample_export: Path) -> None:
    """Integration: Search with multiple filters combined.

    All filters should work together with AND logic.
    """
    adapter = ClaudeAdapter()

    # Combine keyword, title, and date filters
    query = SearchQuery(
        keywords=["python"],
        title_filter="Code",
        from_date=date(2025, 10, 1),
    )
    results = list(adapter.search(claude_sample_export, query))

    # Verify all results match ALL filters
    for result in results:
        # Title filter
        assert "code" in result.conversation.title.lower()

        # Date filter
        assert result.conversation.created_at.date() >= date(2025, 10, 1)

        # Keyword filter (score > 0 indicates match)
        assert result.score > 0.0


def test_search_with_limit(claude_sample_export: Path) -> None:
    """Integration: Search with result limit.

    Limit parameter caps the number of results returned.
    """
    adapter = ClaudeAdapter()

    # Search with limit
    query = SearchQuery(limit=2)
    results = list(adapter.search(claude_sample_export, query))

    # Verify result count respects limit
    assert len(results) <= 2, f"Expected max 2 results, got {len(results)}"


# ============================================================================
# T099: CLI Auto-Detection Tests
# ============================================================================


def test_cli_auto_detection(claude_sample_export: Path) -> None:
    """Integration: CLI auto-detects Claude format.

    The detect_provider function should identify Claude exports by their
    schema structure (root array with uuid, name, chat_messages fields).
    """
    from echomine.cli.provider import detect_provider

    provider = detect_provider(claude_sample_export)
    assert provider == "claude", (
        f"Expected provider 'claude', got '{provider}'. "
        f"Auto-detection should identify Claude export format."
    )


def test_cli_openai_detection_contrast(openai_sample_export: Path) -> None:
    """Integration: Verify OpenAI exports are not detected as Claude.

    Ensures provider detection distinguishes between formats correctly.
    """
    from echomine.cli.provider import detect_provider

    provider = detect_provider(openai_sample_export)
    assert provider == "openai", (
        f"Expected provider 'openai', got '{provider}'. "
        f"Auto-detection should not confuse OpenAI with Claude format."
    )


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def claude_sample_export() -> Path:
    """Path to Claude sample export fixture."""
    return Path("tests/fixtures/claude/sample_export.json")


@pytest.fixture
def claude_empty_conversations() -> Path:
    """Path to Claude export with empty conversations."""
    return Path("tests/fixtures/claude/empty_conversations.json")


@pytest.fixture
def openai_sample_export() -> Path:
    """Path to OpenAI sample export fixture for comparison."""
    return Path("tests/fixtures/sample_export.json")
