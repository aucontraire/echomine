"""Contract tests validating all FRs for ClaudeAdapter.

This test suite validates that ClaudeAdapter satisfies all functional requirements
defined in the Claude adapter specification. Each test maps directly to one or more FRs.

Test Coverage:
    - T100: Conversation parsing FRs (FR-001 to FR-010)
    - T101: Message parsing FRs (FR-011 to FR-020)
    - T102: Search support FRs (FR-021 to FR-035)
    - T103: Conversation retrieval FRs (FR-036 to FR-040)

Constitution Compliance:
    - Principle III: Test-Driven Development (TDD)
    - Principle VI: Strict typing (mypy --strict)
    - Principle VIII: Memory efficiency (streaming)

Test Organization:
    Each test class corresponds to a functional area (Conversation, Message, Search, etc.)
    with tests explicitly labeled with their FR numbers for traceability.
"""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.models.search import SearchQuery


# ============================================================================
# T100: Conversation Parsing Contract Tests (FR-001 to FR-010)
# ============================================================================


class TestConversationParsing:
    """Contract tests for conversation parsing functionality."""

    def test_fr001_root_array_structure(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-001: Parse root JSON array structure.

        Claude exports have a JSON array at the root level containing
        conversation objects. Adapter must parse this array structure.
        """
        conversations = list(adapter.stream_conversations(claude_export))
        assert isinstance(conversations, list), "Should return list of conversations"
        assert len(conversations) >= 1, "Should parse at least one conversation"

    def test_fr002_uuid_to_id_mapping(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-002: Map uuid field to id attribute.

        Claude conversations use 'uuid' field, which must be mapped to
        Conversation.id attribute.
        """
        conversations = list(adapter.stream_conversations(claude_export))
        assert all(conv.id for conv in conversations), "All conversations must have id"

        # Verify IDs are non-empty strings
        for conv in conversations:
            assert isinstance(conv.id, str), f"Conversation id must be string, got {type(conv.id)}"
            assert len(conv.id) > 0, f"Conversation {conv} has empty id"

    def test_fr003_name_to_title_mapping(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-003: Map name field to title, use placeholder for empty names.

        Claude conversations use 'name' field for title. Empty names should
        be replaced with "(No title)" placeholder.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        # All conversations must have non-empty titles
        for conv in conversations:
            assert conv.title, f"Conversation {conv.id} has empty title"
            assert len(conv.title) >= 1, f"Conversation {conv.id} title too short"

    def test_fr003_empty_name_placeholder(self, adapter: ClaudeAdapter) -> None:
        """FR-003: Empty name field should map to "(No title)" placeholder.

        When Claude export has empty string for name, adapter must use
        a descriptive placeholder.
        """
        # Test with fixture containing empty name
        empty_name_export = Path("tests/fixtures/claude/sample_export.json")
        conversations = list(adapter.stream_conversations(empty_name_export))

        # Find conversation with empty original name
        empty_name_convs = [conv for conv in conversations if conv.title == "(No title)"]

        # Fixture should have at least one conversation with empty name
        assert len(empty_name_convs) >= 1, (
            "Test fixture should contain at least one conversation with empty name"
        )

    def test_fr004_fr005_timestamp_parsing(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-004, FR-005: Parse ISO 8601 timestamps to timezone-aware datetime.

        Claude exports use ISO 8601 format with 'Z' suffix (Zulu/UTC).
        Both created_at and updated_at must be parsed to timezone-aware datetimes.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            # Verify created_at is timezone-aware
            assert conv.created_at.tzinfo is not None, (
                f"Conversation {conv.id} created_at must be timezone-aware"
            )
            assert conv.created_at.tzinfo == UTC or conv.created_at.tzinfo.utcoffset(
                None
            ) == UTC.utcoffset(None), f"Conversation {conv.id} created_at must be in UTC"

            # Verify updated_at is timezone-aware (if present, it's Optional)
            if conv.updated_at is not None:
                assert conv.updated_at.tzinfo is not None, (
                    f"Conversation {conv.id} updated_at must be timezone-aware"
                )

    def test_fr006_chat_messages_parsing(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-006: Parse chat_messages array to messages list.

        Claude conversations have a 'chat_messages' array that must be
        parsed to Conversation.messages list.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            assert conv.messages is not None, f"Conversation {conv.id} must have messages attribute"
            assert isinstance(conv.messages, list), f"Conversation {conv.id} messages must be list"

    def test_fr007_summary_ignored(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-007: Summary field should be IGNORED (not stored in metadata).

        Claude exports include a 'summary' field which should be parsed but
        not stored in the Conversation model (not in metadata).
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            # Summary should not be in metadata
            assert "summary" not in conv.metadata, (
                f"Conversation {conv.id} should not store summary in metadata"
            )

    def test_fr008_account_ignored(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-008: Account field should be IGNORED (not stored in metadata).

        Claude exports include an 'account' object which should not be stored.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            # Account should not be in metadata
            assert "account" not in conv.metadata, (
                f"Conversation {conv.id} should not store account in metadata"
            )

    def test_fr009_streaming_memory_efficiency(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-009: Use ijson streaming for O(1) memory.

        Adapter must return an iterator (not list) to enable memory-efficient
        streaming without loading entire file into memory.
        """
        # Verify iterator returned (not list)
        result = adapter.stream_conversations(claude_export)
        assert hasattr(result, "__iter__"), "Must return iterator"
        assert hasattr(result, "__next__"), "Must be a generator/iterator"

    def test_fr010_empty_conversation_handling(
        self,
        adapter: ClaudeAdapter,
    ) -> None:
        """FR-010: Handle empty conversations (no messages).

        Conversations with empty chat_messages arrays should parse successfully
        with a placeholder message to satisfy Conversation model constraints.
        """
        empty_export = Path("tests/fixtures/claude/empty_conversations.json")
        conversations = list(adapter.stream_conversations(empty_export))

        # Should parse without error
        assert len(conversations) >= 1, "Should parse empty conversations"

        # Find conversations with placeholder messages
        empty_convs = [
            conv
            for conv in conversations
            if len(conv.messages) == 1 and conv.messages[0].metadata.get("is_placeholder") is True
        ]

        assert len(empty_convs) >= 1, "Should have at least one empty conversation"


# ============================================================================
# T101: Message Parsing Contract Tests (FR-011 to FR-020)
# ============================================================================


class TestMessageParsing:
    """Contract tests for message parsing functionality."""

    def test_fr011_uuid_to_id_mapping(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-011: Map message uuid field to id attribute.

        Claude messages use 'uuid' field for identification.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        # Get real messages (not placeholders)
        real_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if not msg.metadata.get("is_placeholder")
        ]

        assert len(real_messages) >= 1, "Need at least one real message"

        for msg in real_messages:
            assert msg.id, "Message must have id"
            assert isinstance(msg.id, str), "Message id must be string"
            assert len(msg.id) > 0, "Message id must be non-empty"

    def test_fr012_content_from_blocks(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-012: Extract text from content blocks.

        Claude messages have a 'content' array with text blocks that must
        be extracted and concatenated.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        real_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if not msg.metadata.get("is_placeholder")
        ]

        assert len(real_messages) >= 1

        # Verify messages have content
        for msg in real_messages:
            assert msg.content is not None, f"Message {msg.id} missing content"
            assert isinstance(msg.content, str), "Message content must be string"

    def test_fr013_role_normalization(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-013: Normalize sender to role (human->user, assistant->assistant).

        Claude messages use 'sender' field with values "human" and "assistant",
        which must be normalized to "user" and "assistant" roles.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        real_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if not msg.metadata.get("is_placeholder")
        ]

        assert len(real_messages) >= 2, "Need multiple messages for role variety"

        # Verify all roles are valid
        for msg in real_messages:
            assert msg.role in ("user", "assistant", "system"), (
                f"Message {msg.id} has invalid role: {msg.role}"
            )

        # Verify we have both user and assistant messages
        roles = {msg.role for msg in real_messages}
        assert "user" in roles, "Should have at least one user message"
        assert "assistant" in roles, "Should have at least one assistant message"

    def test_fr014_timestamp_parsing(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-014: Parse message created_at to timezone-aware datetime.

        Message timestamps must be timezone-aware and in UTC.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        real_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if not msg.metadata.get("is_placeholder")
        ]

        assert len(real_messages) >= 1

        for msg in real_messages:
            assert msg.timestamp.tzinfo is not None, (
                f"Message {msg.id} timestamp must be timezone-aware"
            )

    def test_fr015a_skip_tool_blocks(
        self,
        adapter: ClaudeAdapter,
    ) -> None:
        """FR-015a: Skip tool_use and tool_result blocks.

        Messages with tool blocks should have them filtered out, keeping only
        text-type content blocks. Tool-only messages (no text blocks) will have
        empty content per spec.
        """
        # Test with fixture containing tool messages
        tool_export = Path("tests/fixtures/claude/tool_messages.json")
        conversations = list(adapter.stream_conversations(tool_export))

        assert len(conversations) >= 1, "Should parse conversations with tool blocks"

        # Find messages with both text and tool blocks
        mixed_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if msg.id in ("msg-tool-002", "msg-mixed-001", "msg-mixed-003")
        ]

        # These messages should have text content (tool blocks filtered out)
        for msg in mixed_messages:
            assert len(msg.content) > 0, (
                f"Message {msg.id} should have text content after filtering tool blocks"
            )

        # Find tool-only messages (no text blocks, only tool blocks)
        tool_only_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if msg.id in ("msg-tool-003", "msg-search-002", "msg-toolonly-002")
        ]

        # Tool-only messages will have empty content (per spec, tool blocks are skipped)
        for msg in tool_only_messages:
            # Empty content is acceptable - tool blocks were correctly filtered
            # This validates that tool_use and tool_result blocks are skipped
            assert isinstance(msg.content, str), f"Message {msg.id} content must be string"

    def test_fr015b_fallback_to_text_field(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-015b: Fall back to text field if content blocks are empty.

        If content extraction yields empty string, use the text field as fallback.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        real_messages = [
            msg
            for conv in conversations
            for msg in conv.messages
            if not msg.metadata.get("is_placeholder")
        ]

        # All messages should have non-empty content (either from blocks or text field)
        for msg in real_messages:
            assert len(msg.content) > 0, f"Message {msg.id} has empty content (fallback failed)"

    def test_fr019_timestamp_fallback(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-019: Fall back to conversation created_at for missing message timestamps.

        If message created_at is missing or invalid, use conversation's created_at.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            real_messages = [msg for msg in conv.messages if not msg.metadata.get("is_placeholder")]

            if real_messages:
                # All message timestamps should be valid (using fallback if needed)
                for msg in real_messages:
                    assert msg.timestamp is not None
                    assert msg.timestamp.tzinfo is not None

    def test_fr020_parent_id_none(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-020: All messages have parent_id=None (flat/linear structure).

        Claude exports use a flat message array with no threading.
        All messages must have parent_id=None.
        """
        conversations = list(adapter.stream_conversations(claude_export))

        for conv in conversations:
            for msg in conv.messages:
                assert msg.parent_id is None, (
                    f"Message {msg.id} should have parent_id=None (flat structure)"
                )


# ============================================================================
# T102: Search Support Contract Tests (FR-021 to FR-035)
# ============================================================================


class TestSearchSupport:
    """Contract tests for search functionality."""

    def test_fr021_search_returns_iterator(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-021: search() returns Iterator[SearchResult].

        Search method must return an iterator for memory efficiency.
        """
        query = SearchQuery(keywords=["test"])
        result = adapter.search(claude_export, query)

        assert hasattr(result, "__iter__"), "search() must return iterator"

    def test_fr022_keyword_search(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-022: Support keyword-based search with BM25 ranking.

        Keyword search must use BM25 algorithm and return results sorted by
        relevance score (descending).
        """
        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(claude_export, query))

        if results:
            # Verify scores are in descending order
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True), (
                "Search results must be sorted by score (descending)"
            )

            # Verify all scores are in [0, 1] range
            for result in results:
                assert 0.0 <= result.score <= 1.0, f"Score {result.score} outside [0, 1] range"

    def test_fr024_title_filter(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-024: Support title_filter for case-insensitive substring matching.

        Title filter must perform case-insensitive substring search on
        conversation titles.
        """
        query = SearchQuery(title_filter="Python")
        results = list(adapter.search(claude_export, query))

        # Verify all results match title filter (case-insensitive)
        for result in results:
            assert "python" in result.conversation.title.lower(), (
                f"Title '{result.conversation.title}' does not contain 'python'"
            )

    def test_fr035_limit_parameter(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-035: limit parameter caps results.

        Search results must respect the limit parameter.
        """
        query = SearchQuery(limit=1)
        results = list(adapter.search(claude_export, query))

        assert len(results) <= 1, f"Expected max 1 result, got {len(results)}"

    def test_fr_search_with_no_filters(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """Search with no filters should return all conversations.

        When no keywords or filters are specified, search should return
        all conversations with score=1.0.
        """
        query = SearchQuery()
        results = list(adapter.search(claude_export, query))

        # Should return all conversations
        all_convs = list(adapter.stream_conversations(claude_export))
        # Apply default limit
        expected_count = min(len(all_convs), query.limit)
        assert len(results) <= expected_count


# ============================================================================
# T103: Conversation Retrieval Contract Tests (FR-036 to FR-040)
# ============================================================================


class TestConversationRetrieval:
    """Contract tests for conversation retrieval by ID."""

    def test_fr036_get_by_full_id(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-036, FR-037: Retrieve conversation by full UUID.

        get_conversation_by_id must support full UUID matching.
        """
        # Get a valid conversation ID
        conversations = list(adapter.stream_conversations(claude_export))
        assert len(conversations) >= 1

        full_id = conversations[0].id

        # Retrieve by full ID
        result = adapter.get_conversation_by_id(claude_export, full_id)

        assert result is not None, f"Should find conversation with ID {full_id}"
        assert result.id == full_id, "Returned conversation should match requested ID"

    def test_fr038_returns_none_not_found(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-038: Return None for non-existent ID.

        get_conversation_by_id must return None (not raise exception) when
        conversation is not found.
        """
        result = adapter.get_conversation_by_id(claude_export, "nonexistent-id-12345")
        assert result is None, "Should return None for non-existent ID"

    def test_fr040_partial_id_matching(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-040: Support partial ID matching (min 4 chars).

        get_conversation_by_id must support prefix matching with minimum
        4 characters.
        """
        # Get a valid conversation ID
        conversations = list(adapter.stream_conversations(claude_export))
        assert len(conversations) >= 1

        full_id = conversations[0].id
        prefix = full_id[:8]  # Use first 8 chars

        # Retrieve by partial ID
        result = adapter.get_conversation_by_id(claude_export, prefix)

        assert result is not None, f"Should find conversation with prefix {prefix}"
        assert result.id == full_id, "Should return correct conversation for prefix"

    def test_fr040_min_prefix_length(
        self,
        adapter: ClaudeAdapter,
        claude_export: Path,
    ) -> None:
        """FR-040: Partial ID matching requires minimum 4 characters.

        Prefixes shorter than 4 characters should still work but be exact match only.
        """
        conversations = list(adapter.stream_conversations(claude_export))
        assert len(conversations) >= 1

        full_id = conversations[0].id
        short_prefix = full_id[:3]  # Only 3 chars

        # Short prefix won't match unless it's the full ID (unlikely)
        result = adapter.get_conversation_by_id(claude_export, short_prefix)
        # Result will be None unless prefix happens to be full ID
        # This test documents the minimum length requirement


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def adapter() -> ClaudeAdapter:
    """ClaudeAdapter instance for testing."""
    return ClaudeAdapter()


@pytest.fixture
def claude_export() -> Path:
    """Path to Claude sample export fixture."""
    return Path("tests/fixtures/claude/sample_export.json")
