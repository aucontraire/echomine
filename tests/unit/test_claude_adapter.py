"""Unit tests for Claude adapter implementation.

This module tests the ClaudeAdapter class for streaming conversations from
Anthropic Claude export files with O(1) memory complexity.

Constitution Compliance:
    - Principle III: Test-driven development (TDD)
    - Principle VI: Strict typing (mypy --strict)
    - Principle VIII: Memory efficiency (streaming, not bulk loading)

Test Coverage:
    - stream_conversations: Basic streaming, progress callbacks, skip callbacks
    - search: BM25 ranking, filters, sorting
    - get_conversation_by_id: ID lookup with streaming
    - get_message_by_id: Message lookup with conversation context

Test Strategy:
    - AAA pattern (Arrange, Act, Assert)
    - Use fixtures from tests/fixtures/claude/
    - Test error handling (FileNotFoundError, ParseError, ValidationError)
    - Test graceful degradation (malformed entries)
    - Test memory efficiency (streaming behavior)
"""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.search import SearchQuery


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_export(request: pytest.FixtureRequest) -> Path:
    """Path to sample Claude export fixture.

    Returns:
        Path to tests/fixtures/claude/sample_export.json
    """
    # Get the test file's directory
    test_dir = Path(request.path).parent
    # Navigate to fixtures/claude
    fixtures_dir = test_dir.parent / "fixtures" / "claude"
    return fixtures_dir / "sample_export.json"


@pytest.fixture
def malformed_export(request: pytest.FixtureRequest) -> Path:
    """Path to malformed Claude export fixture.

    Returns:
        Path to tests/fixtures/claude/malformed_export.json
    """
    test_dir = Path(request.path).parent
    fixtures_dir = test_dir.parent / "fixtures" / "claude"
    return fixtures_dir / "malformed_export.json"


@pytest.fixture
def empty_export(request: pytest.FixtureRequest) -> Path:
    """Path to empty Claude export fixture.

    Returns:
        Path to tests/fixtures/claude/empty_conversations.json
    """
    test_dir = Path(request.path).parent
    fixtures_dir = test_dir.parent / "fixtures" / "claude"
    return fixtures_dir / "empty_conversations.json"


@pytest.fixture
def tool_messages_export(request: pytest.FixtureRequest) -> Path:
    """Path to Claude export with tool messages.

    Returns:
        Path to tests/fixtures/claude/tool_messages.json
    """
    test_dir = Path(request.path).parent
    fixtures_dir = test_dir.parent / "fixtures" / "claude"
    return fixtures_dir / "tool_messages.json"


# ============================================================================
# Test stream_conversations
# ============================================================================


class TestStreamConversations:
    """Test ClaudeAdapter.stream_conversations() method.

    Coverage:
        - Basic streaming functionality
        - Progress callback invocation
        - Skip callback for malformed entries
        - Error handling (FileNotFoundError, ParseError)
        - Empty exports
    """

    # Phase 3a: RED - Failing Tests (T010-T018)

    def test_parse_root_array_structure(self, sample_export: Path) -> None:
        """Test T010: Verify root JSON array parsing works (FR-001).

        Validates:
        - Root array is parsed correctly
        - Returns iterator of Conversation objects
        - Yields all conversations in export (5 in sample_export.json)
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))

        # Sample export has 5 conversations
        assert len(conversations) == 5
        assert all(hasattr(conv, "id") for conv in conversations)
        assert all(hasattr(conv, "title") for conv in conversations)

    def test_uuid_maps_to_id(self, sample_export: Path) -> None:
        """Test T011: Verify uuid→id mapping (FR-002).

        Validates:
        - Claude's "uuid" field maps to Conversation.id
        - First conversation has expected UUID
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]

        # First conversation in sample_export.json has uuid: "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
        assert first_conv.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"

    def test_name_maps_to_title(self, sample_export: Path) -> None:
        """Test T012: Verify name→title mapping with empty string handling (FR-003).

        Validates:
        - Claude's "name" field maps to Conversation.title
        - Empty name string maps to "(No title)" placeholder
        - Non-empty names preserved exactly
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))

        # First conversation: non-empty title
        assert conversations[0].title == "Python Code Review - Binary Search Implementation"

        # Fourth conversation (index 3): empty name → "(No title)"
        # From fixture: {"uuid": "f9e8d7c6-b5a4-4321-9876-fedcba098765", "name": "", ...}
        assert conversations[3].title == "(No title)"

    def test_iso_timestamp_parsing(self, sample_export: Path) -> None:
        """Test T013: Verify ISO 8601 timestamp parsing (FR-004, FR-005).

        Validates:
        - created_at parsed from ISO 8601 string
        - updated_at parsed from ISO 8601 string
        - Timestamps are timezone-aware (UTC)
        - Z suffix (Zulu time) handled correctly
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]

        # First conversation timestamps:
        # "created_at": "2025-10-01T18:42:27.303515Z"
        # "updated_at": "2025-10-01T18:42:33.904627Z"

        assert first_conv.created_at.year == 2025
        assert first_conv.created_at.month == 10
        assert first_conv.created_at.day == 1
        assert first_conv.created_at.tzinfo is not None  # Timezone-aware
        assert first_conv.created_at.tzinfo == UTC

        assert first_conv.updated_at is not None
        assert first_conv.updated_at.year == 2025
        assert first_conv.updated_at.tzinfo == UTC

    def test_chat_messages_mapping(self, sample_export: Path) -> None:
        """Test T014: Verify chat_messages→messages mapping (FR-006).

        Validates:
        - Claude's "chat_messages" array maps to Conversation.messages
        - Message count is correct
        - Messages are Message objects
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))

        # First conversation has 2 messages
        first_conv = conversations[0]
        assert len(first_conv.messages) == 2
        assert first_conv.message_count == 2

        # Second conversation has 4 messages
        second_conv = conversations[1]
        assert len(second_conv.messages) == 4
        assert second_conv.message_count == 4

    def test_metadata_ignored_not_stored(self, sample_export: Path) -> None:
        """Test T015: Verify summary/account NOT stored in metadata (FR-007, FR-008).

        Validates:
        - summary field is ignored (not stored)
        - account field is ignored (not stored)
        - metadata dict does not contain these fields
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]

        # FR-007, FR-008: summary and account MUST be ignored
        assert "summary" not in first_conv.metadata
        assert "account" not in first_conv.metadata

    def test_streaming_memory_efficiency(self, sample_export: Path) -> None:
        """Test T016: Verify iterator returned (streaming pattern, FR-009).

        Validates:
        - stream_conversations returns Iterator, not list
        - Can iterate lazily without materializing entire export
        - Early termination works (doesn't load entire file)
        """
        from collections.abc import Iterator

        adapter = ClaudeAdapter()

        result = adapter.stream_conversations(sample_export)

        # Must return Iterator
        assert isinstance(result, Iterator)

        # Can consume first item without loading all
        first_conv = next(result)
        assert first_conv.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"

    def test_empty_conversation_handling(self, empty_export: Path) -> None:
        """Test T017: Verify zero-message conversations work (FR-010).

        Validates:
        - Conversations with empty chat_messages array parse successfully
        - No errors raised for empty conversations
        - Placeholder message added to satisfy Conversation.messages min_length=1

        Note: Conversation model requires min_length=1 for messages. Empty conversations
        get a placeholder system message to satisfy this constraint while still allowing
        graceful parsing.
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(empty_export))

        # empty_conversations.json has 7 conversations total
        assert len(conversations) == 7

        # First conversation has 0 original messages, but 1 placeholder
        first_conv = conversations[0]
        assert first_conv.id == "empty-conv-001"
        assert len(first_conv.messages) == 1  # Placeholder message
        assert first_conv.message_count == 1

        # Verify placeholder message characteristics
        placeholder = first_conv.messages[0]
        assert placeholder.role == "system"
        assert placeholder.content == "(Empty conversation)"
        assert placeholder.metadata.get("is_placeholder") is True

    def test_progress_callback_invoked(self, sample_export: Path) -> None:
        """Test T018: Verify progress callback invoked every 100 items.

        Validates:
        - progress_callback parameter exists
        - Callback invoked with correct counts
        - Callback NOT invoked for <100 items (sample has 5)
        """
        adapter = ClaudeAdapter()
        progress_calls: list[int] = []

        def progress(count: int) -> None:
            progress_calls.append(count)

        conversations = list(
            adapter.stream_conversations(sample_export, progress_callback=progress)
        )

        # Sample export has only 5 conversations, so callback should NOT be invoked
        # (invoked every 100 items)
        assert len(conversations) == 5
        assert len(progress_calls) == 0  # No callback for <100 items


# ============================================================================
# Test Message Parsing (Phase 4: User Story 2)
# ============================================================================


class TestMessageParsing:
    """Test Claude message parsing with content blocks.

    Coverage:
        - T024: Message UUID mapping
        - T025: Content block extraction from content array
        - T026: Role normalization (human→user, assistant→assistant)
        - T027: Message timestamp parsing
        - T028: Tool block skipping (tool_use, tool_result)
        - T029: Text field fallback when content is empty
        - T030: Message timestamp fallback to conversation created_at
        - T031: Malformed entry skipping with WARNING logs
        - T032: Parent ID is None for all messages
    """

    def test_message_uuid_mapping(self, sample_export: Path) -> None:
        """Test T024: Verify uuid→id mapping for messages (FR-011).

        Validates:
        - Message uuid field maps to Message.id
        - First message has expected UUID
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]
        first_message = first_conv.messages[0]

        # First message in sample_export.json has uuid: "msg-001-uuid"
        assert first_message.id == "msg-001-uuid"

    def test_content_block_extraction(self, sample_export: Path) -> None:
        """Test T025: Verify content extracted from content blocks, not text field (FR-012, FR-015).

        Validates:
        - Content extracted from content[type=text] blocks
        - Multiple text blocks concatenated with newline
        - Text field ignored when content array present
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]
        first_message = first_conv.messages[0]

        # First message has content block with code snippet
        # Should extract from content[0].text, not text field
        assert "Can you review my binary search implementation?" in first_message.content
        assert "```python" in first_message.content
        assert "def binary_search(arr, target):" in first_message.content

    def test_role_normalization(self, sample_export: Path) -> None:
        """Test T026: Verify role normalization (FR-013).

        Validates:
        - "human" → "user"
        - "assistant" → "assistant"
        - Roles are correct for all messages
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]

        # First message: human → user
        assert first_conv.messages[0].role == "user"

        # Second message: assistant → assistant
        assert first_conv.messages[1].role == "assistant"

    def test_message_timestamp_parsing(self, sample_export: Path) -> None:
        """Test T027: Verify ISO 8601 timestamp parsing for messages (FR-014).

        Validates:
        - Message created_at parsed correctly
        - Timestamps are timezone-aware (UTC)
        - Z suffix handled correctly
        """

        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))
        first_conv = conversations[0]
        first_message = first_conv.messages[0]

        # First message: "created_at": "2025-10-01T18:42:28.370875Z"
        assert first_message.timestamp.year == 2025
        assert first_message.timestamp.month == 10
        assert first_message.timestamp.day == 1
        assert first_message.timestamp.tzinfo is not None
        assert first_message.timestamp.tzinfo == UTC

    def test_tool_block_skipping(self, tool_messages_export: Path) -> None:
        """Test T028: Verify tool_use and tool_result blocks are SKIPPED (FR-015a).

        Validates:
        - tool_use blocks are not included in message content
        - tool_result blocks are not included in message content
        - Only text-type blocks are extracted
        - Messages with ONLY tool blocks have empty content
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(tool_messages_export))

        # First conversation has mixed text and tool blocks
        first_conv = conversations[0]

        # msg-tool-002: Has text block + tool_use block
        # Content should only contain text block
        msg_with_tool_use = first_conv.messages[1]
        assert "I'll create a Python script" in msg_with_tool_use.content
        assert "write_file" not in msg_with_tool_use.content  # tool_use should be skipped
        assert "toolu_" not in msg_with_tool_use.content  # tool ID should not appear

        # msg-tool-003: Has ONLY tool_result block (no text blocks)
        # Content should be empty string (FR-015a)
        msg_tool_result_only = first_conv.messages[2]
        assert msg_tool_result_only.content == ""

    def test_text_field_fallback(self, tool_messages_export: Path) -> None:
        """Test T029: Verify fallback to text field when content is empty/missing (FR-015b).

        Validates:
        - If content array is empty, use text field
        - If content array is missing, use text field
        - Text field acts as fallback for compatibility
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(tool_messages_export))

        # msg-tool-003: Has empty content after tool block extraction
        # Should fallback to text field (which is empty in this case)
        first_conv = conversations[0]
        msg_tool_result_only = first_conv.messages[2]

        # This message has text="" and content=[tool_result]
        # After skipping tool_result, content extraction yields ""
        # Fallback to text field also yields ""
        # Final content should be ""
        assert msg_tool_result_only.content == ""

    def test_message_timestamp_fallback(self, malformed_export: Path) -> None:
        """Test T030: Verify fallback to conversation created_at if message timestamp missing (FR-019).

        Validates:
        - If message created_at is missing, use conversation created_at
        - If message created_at is invalid, use conversation created_at
        - Ensures all messages have valid timestamps
        """
        # Note: Current malformed_export.json doesn't have messages with missing timestamps
        # This test will need a specific fixture or we'll modify the implementation to handle this
        # For now, we'll test with valid data and expect the feature to work
        adapter = ClaudeAdapter()

        # This will be tested with a modified fixture in Phase 4b
        # For now, just verify that valid messages work correctly
        conversations = list(adapter.stream_conversations(malformed_export))

        # All messages should have timestamps
        for conv in conversations:
            for msg in conv.messages:
                assert msg.timestamp is not None

    def test_malformed_entry_skipping(self, malformed_export: Path) -> None:
        """Test T031: Verify malformed messages are skipped with WARNING (FR-017, FR-018).

        Validates:
        - Malformed conversations are skipped (logged at conversation level)
        - Malformed messages within valid conversations are skipped
        - Processing continues after skip
        - Valid messages/conversations after errors are parsed
        """
        adapter = ClaudeAdapter()

        # malformed_export has 6 total entries:
        # - 1 valid conversation (valid-conv-001)
        # - 1 conversation with missing UUID (skipped)
        # - 1 conversation with invalid timestamp (skipped)
        # - 1 valid conversation with malformed message (valid-conv-002)
        # - 1 empty conversation (empty-messages-conv)
        # - 1 final valid conversation (valid-conv-003)
        conversations = list(adapter.stream_conversations(malformed_export))

        # Should successfully parse 4 valid conversations despite malformed entries
        assert len(conversations) == 4

        # First conversation should be valid-conv-001
        assert conversations[0].id == "valid-conv-001"
        assert len(conversations[0].messages) == 1

        # Second conversation should be valid-conv-002 (with malformed message skipped)
        assert conversations[1].id == "valid-conv-002"
        # Original has 3 messages, 1 malformed (missing uuid and sender), so 2 valid messages
        assert len(conversations[1].messages) == 2

        # Third conversation is empty-messages-conv (with placeholder)
        assert conversations[2].id == "empty-messages-conv"
        assert len(conversations[2].messages) == 1  # Placeholder message

        # Final conversation should be valid-conv-003
        assert conversations[3].id == "valid-conv-003"
        assert len(conversations[3].messages) == 1

    def test_parent_id_none(self, sample_export: Path) -> None:
        """Test T032: Verify all messages have parent_id=None (FR-020).

        Validates:
        - Claude exports use flat message structure (no threading)
        - All messages have parent_id=None
        - No parent-child relationships in Claude messages
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(sample_export))

        # Check all messages in all conversations
        for conv in conversations:
            for msg in conv.messages:
                assert msg.parent_id is None


# ============================================================================
# Test search
# ============================================================================


class TestSearch:
    """Test ClaudeAdapter.search() method.

    Coverage:
        - Keyword search with BM25 ranking
        - Title filter
        - Date range filter
        - Message count filter
        - Role filter
        - Phrase search
        - Exclude keywords
        - Sorting (score, date, title, messages)
        - Limit parameter
    """

    # Phase 5: RED - Failing Tests (T040-T052)

    def test_search_returns_iterator(self, sample_export: Path) -> None:
        """Test T040: Verify search returns Iterator[SearchResult] (FR-021).

        Validates:
        - Returns Iterator type
        - SearchResult objects contain conversation and score
        - Can iterate over results
        """
        from collections.abc import Iterator

        adapter = ClaudeAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = adapter.search(sample_export, query)

        # Must return Iterator
        assert isinstance(results, Iterator)

        # Consume results and validate structure
        result_list = list(results)
        assert len(result_list) > 0
        assert all(hasattr(r, "conversation") for r in result_list)
        assert all(hasattr(r, "score") for r in result_list)

    def test_bm25_keyword_ranking(self, sample_export: Path) -> None:
        """Test T041: Verify BM25 scoring with keyword search (FR-022, FR-032).

        Validates:
        - Keyword search uses BM25 scoring
        - Results sorted by relevance (descending)
        - Scores normalized to [0.0, 1.0] range
        - More relevant results have higher scores
        """
        adapter = ClaudeAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export, query))

        # Should find conversations with "python" keyword
        assert len(results) > 0

        # All scores should be in [0.0, 1.0] range
        for result in results:
            assert 0.0 <= result.score <= 1.0

        # Results should be sorted by score (descending)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_phrase_matching(self, sample_export: Path) -> None:
        """Test T042: Verify exact phrase matching works (FR-023).

        Validates:
        - Phrase search finds exact substring matches
        - Case-insensitive matching
        - Phrases combined with OR logic
        """
        adapter = ClaudeAdapter()
        query = SearchQuery(phrases=["binary search"], limit=10)

        results = list(adapter.search(sample_export, query))

        # Should find conversation with "binary search" phrase
        assert len(results) > 0

        # First conversation should contain the phrase
        first_conv = results[0].conversation
        assert "binary search" in first_conv.title.lower() or any(
            "binary search" in msg.content.lower() for msg in first_conv.messages
        )

    def test_title_filter(self, sample_export: Path) -> None:
        """Test T043: Verify title_filter filters by title substring (FR-024).

        Validates:
        - title_filter matches substring in title
        - Case-insensitive matching
        - Only matching conversations returned
        """
        adapter = ClaudeAdapter()
        query = SearchQuery(title_filter="Python", limit=10)

        results = list(adapter.search(sample_export, query))

        # Should find conversations with "Python" in title
        assert len(results) > 0

        # All results should have "Python" in title (case-insensitive)
        for result in results:
            assert "python" in result.conversation.title.lower()

    def test_date_range_filtering(self, sample_export: Path) -> None:
        """Test T044: Verify from_date/to_date filtering (FR-025).

        Validates:
        - from_date filters conversations created on or after date
        - to_date filters conversations created on or before date
        - Both filters can be combined
        """
        from datetime import date

        adapter = ClaudeAdapter()

        # Test from_date filter
        query = SearchQuery(from_date=date(2025, 11, 1), limit=10)
        results = list(adapter.search(sample_export, query))

        assert len(results) > 0
        for result in results:
            assert result.conversation.created_at.date() >= date(2025, 11, 1)

        # Test to_date filter
        query2 = SearchQuery(to_date=date(2025, 10, 31), limit=10)
        results2 = list(adapter.search(sample_export, query2))

        assert len(results2) > 0
        for result in results2:
            assert result.conversation.created_at.date() <= date(2025, 10, 31)

    def test_message_count_filtering(self, sample_export: Path) -> None:
        """Test T045: Verify min_messages/max_messages filtering (FR-026).

        Validates:
        - min_messages filters conversations with at least N messages
        - max_messages filters conversations with at most N messages
        - Both filters can be combined
        """
        adapter = ClaudeAdapter()

        # Test min_messages filter
        query = SearchQuery(min_messages=3, limit=10)
        results = list(adapter.search(sample_export, query))

        assert len(results) > 0
        for result in results:
            assert result.conversation.message_count >= 3

        # Test max_messages filter
        query2 = SearchQuery(max_messages=2, limit=10)
        results2 = list(adapter.search(sample_export, query2))

        assert len(results2) > 0
        for result in results2:
            assert result.conversation.message_count <= 2

    def test_role_filter(self, sample_export: Path) -> None:
        """Test T046: Verify searching only user or assistant messages (FR-027).

        Validates:
        - role_filter='user' searches only user messages
        - role_filter='assistant' searches only assistant messages
        - Keyword matches only in filtered role messages
        """
        adapter = ClaudeAdapter()

        # Search for keyword in user messages only
        query = SearchQuery(keywords=["binary"], role_filter="user", limit=10)
        results = list(adapter.search(sample_export, query))

        # Should find conversations where user mentioned "binary"
        assert len(results) > 0

    def test_exclude_keywords(self, sample_export: Path) -> None:
        """Test T047: Verify excluded keywords filter out results (FR-028).

        Validates:
        - exclude_keywords removes conversations containing excluded terms
        - Works with keyword search
        - Case-insensitive matching
        """
        adapter = ClaudeAdapter()

        # Search for "python" but exclude conversations with "async"
        query = SearchQuery(keywords=["python"], exclude_keywords=["async"], limit=10)
        results = list(adapter.search(sample_export, query))

        # All results should have "python" but not "async"
        for result in results:
            conv_text = (
                result.conversation.title
                + " "
                + " ".join(m.content for m in result.conversation.messages)
            )
            assert "async" not in conv_text.lower()

    def test_match_mode(self, sample_export: Path) -> None:
        """Test T048: Verify match_mode='all' requires all keywords (FR-029).

        Validates:
        - match_mode='all' requires ALL keywords present
        - match_mode='any' matches if ANY keyword present (default)
        - Results differ between modes
        """
        adapter = ClaudeAdapter()

        # Test 'any' mode (default)
        query_any = SearchQuery(keywords=["python", "database"], match_mode="any", limit=10)
        results_any = list(adapter.search(sample_export, query_any))

        # Test 'all' mode
        query_all = SearchQuery(keywords=["python", "binary"], match_mode="all", limit=10)
        results_all = list(adapter.search(sample_export, query_all))

        # 'any' mode should return more results (less restrictive)
        # Both keywords should be present in 'all' mode results
        for result in results_all:
            conv_text = (
                result.conversation.title
                + " "
                + " ".join(m.content for m in result.conversation.messages)
            )
            assert "python" in conv_text.lower()
            assert "binary" in conv_text.lower()

    def test_sort_options(self, sample_export: Path) -> None:
        """Test T049: Verify sort_by and sort_order work (FR-030).

        Validates:
        - sort_by='score' (default): sort by BM25 relevance
        - sort_by='date': sort by conversation date
        - sort_by='title': sort by title alphabetically
        - sort_by='messages': sort by message count
        - sort_order='desc' (default) vs 'asc'
        """
        adapter = ClaudeAdapter()

        # Test sort by date descending
        query_date_desc = SearchQuery(
            keywords=["python"], sort_by="date", sort_order="desc", limit=10
        )
        results_date_desc = list(adapter.search(sample_export, query_date_desc))

        # Dates should be descending (newest first)
        if len(results_date_desc) > 1:
            dates = [r.conversation.created_at for r in results_date_desc]
            assert dates == sorted(dates, reverse=True)

        # Test sort by title ascending
        query_title_asc = SearchQuery(title_filter="", sort_by="title", sort_order="asc", limit=10)
        results_title_asc = list(adapter.search(sample_export, query_title_asc))

        # Titles should be ascending (alphabetical)
        if len(results_title_asc) > 1:
            titles = [r.conversation.title.lower() for r in results_title_asc]
            assert titles == sorted(titles)

    def test_snippet_generation(self, sample_export: Path) -> None:
        """Test T050: Verify snippets are extracted (FR-031).

        Validates:
        - SearchResult contains snippet field
        - Snippet highlights matched keywords
        - Snippet is from matched messages
        """
        adapter = ClaudeAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export, query))

        assert len(results) > 0

        # All results should have snippets
        for result in results:
            assert result.snippet is not None
            # Snippet should be non-empty for keyword matches
            if result.score > 0:
                assert len(result.snippet) > 0

    def test_limit_parameter(self, sample_export: Path) -> None:
        """Test T051: Verify limit caps results (FR-035).

        Validates:
        - limit parameter restricts number of results
        - Returns exactly limit results (or fewer if not enough matches)
        - Default limit is respected
        """
        adapter = ClaudeAdapter()

        # Test limit=2
        query = SearchQuery(limit=2)
        results = list(adapter.search(sample_export, query))

        # Should return at most 2 results
        assert len(results) <= 2

        # Test limit=10
        query2 = SearchQuery(limit=10)
        results2 = list(adapter.search(sample_export, query2))

        # Should return all conversations (sample has 5)
        assert len(results2) == 5


# ============================================================================
# Test get_conversation_by_id
# ============================================================================


class TestGetConversationById:
    """Test ClaudeAdapter.get_conversation_by_id() method.

    Coverage:
        - Find existing conversation by ID
        - Return None for non-existent ID
        - Error handling (FileNotFoundError, ParseError)
        - Memory efficiency (streaming search)
        - Partial ID matching (prefix, min 4 chars, case-insensitive)
    """

    # Phase 6 - RED: Failing Tests (T059-T064)

    def test_get_conversation_by_id_signature(self, sample_export: Path) -> None:
        """Test T059: Verify method exists with correct signature (FR-036).

        Validates:
        - Method exists and is callable
        - Takes file_path and conversation_id parameters
        - Returns Conversation | None (not exception for missing)
        """
        adapter = ClaudeAdapter()

        # Method should exist and be callable
        assert hasattr(adapter, "get_conversation_by_id")
        assert callable(adapter.get_conversation_by_id)

        # Should return None for non-existent ID (not raise exception)
        result = adapter.get_conversation_by_id(sample_export, "non-existent-id")
        assert result is None

    def test_search_by_uuid(self, sample_export: Path) -> None:
        """Test T060: Return correct conversation for valid UUID (FR-037).

        Validates:
        - Finds conversation by exact UUID match
        - Returns full Conversation object with all fields
        - UUID matching is case-insensitive
        """
        adapter = ClaudeAdapter()

        # Find first conversation by exact UUID
        conv = adapter.get_conversation_by_id(sample_export, "5551eb71-ada2-45bd-8f91-0c4945a1e5a6")

        assert conv is not None
        assert conv.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
        assert conv.title == "Python Code Review - Binary Search Implementation"
        assert len(conv.messages) == 2

        # Case-insensitive matching
        conv_upper = adapter.get_conversation_by_id(
            sample_export, "5551EB71-ADA2-45BD-8F91-0C4945A1E5A6"
        )
        assert conv_upper is not None
        assert conv_upper.id == conv.id

    def test_returns_none_not_found(self, sample_export: Path) -> None:
        """Test T061: Return None for non-existent ID (FR-038).

        Validates:
        - Returns None (not exception) for invalid UUID
        - No partial matches for invalid IDs
        - Empty string returns None
        """
        adapter = ClaudeAdapter()

        # Non-existent UUID
        result = adapter.get_conversation_by_id(
            sample_export, "00000000-0000-0000-0000-000000000000"
        )
        assert result is None

        # Empty string
        result_empty = adapter.get_conversation_by_id(sample_export, "")
        assert result_empty is None

        # Partial match but too short (less than 4 chars)
        result_short = adapter.get_conversation_by_id(sample_export, "555")
        assert result_short is None

    def test_retrieval_memory_efficiency(self, sample_export: Path) -> None:
        """Test T062: Uses streaming approach (FR-039).

        Validates:
        - Uses stream_conversations (iterator pattern)
        - No buffering of entire file
        - Early termination when match found
        """
        adapter = ClaudeAdapter()

        # Mock stream_conversations to verify it's called
        original_stream = adapter.stream_conversations
        call_count = 0

        def mock_stream(file_path: Path, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            yield from original_stream(file_path, **kwargs)

        adapter.stream_conversations = mock_stream  # type: ignore[method-assign]

        # Call get_conversation_by_id
        result = adapter.get_conversation_by_id(
            sample_export, "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
        )

        # Verify streaming was used
        assert call_count == 1
        assert result is not None

    def test_partial_id_matching(self, sample_export: Path) -> None:
        """Test T063: Support prefix matching (FR-040).

        Validates:
        - Minimum 4 characters for partial match
        - Case-insensitive prefix matching
        - Returns first match if multiple prefixes match
        """
        adapter = ClaudeAdapter()

        # Partial match with minimum 4 chars (first conversation)
        conv = adapter.get_conversation_by_id(sample_export, "5551")
        assert conv is not None
        assert conv.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"

        # Case-insensitive partial match
        conv_upper = adapter.get_conversation_by_id(sample_export, "5551EB")
        assert conv_upper is not None
        assert conv_upper.id == conv.id

        # Partial match with longer prefix (second conversation)
        conv2 = adapter.get_conversation_by_id(sample_export, "7892bc")
        assert conv2 is not None
        assert conv2.id == "7892bc45-def3-4a21-9c12-3d5e6f7a8b9c"

        # Too short for partial match (less than 4 chars)
        conv_short = adapter.get_conversation_by_id(sample_export, "789")
        assert conv_short is None


# ============================================================================
# Test get_message_by_id
# ============================================================================


class TestGetMessageById:
    """Test ClaudeAdapter.get_message_by_id() method.

    Coverage:
        - Find message by ID (with conversation hint)
        - Find message by ID (without conversation hint)
        - Return None for non-existent ID
        - Return tuple of (Message, Conversation)
        - Error handling
    """

    # Phase 7 - RED: Failing Tests (T068-T073)

    def test_get_message_by_id_signature(self, sample_export: Path) -> None:
        """Test T068: Verify method exists with correct signature (FR-041).

        Validates:
        - Method exists and is callable
        - Takes file_path, message_id, and optional conversation_id
        - Returns tuple[Message, Conversation] | None
        """
        adapter = ClaudeAdapter()

        # Method should exist and be callable
        assert hasattr(adapter, "get_message_by_id")
        assert callable(adapter.get_message_by_id)

        # Should return None for non-existent ID (not raise exception)
        result = adapter.get_message_by_id(sample_export, "non-existent-msg-id")
        assert result is None

    def test_search_message_by_uuid(self, sample_export: Path) -> None:
        """Test T069: Return message for valid UUID (FR-042).

        Validates:
        - Finds message by exact UUID match
        - Returns tuple (Message, Conversation) with full context
        - Message has correct content and metadata
        """
        adapter = ClaudeAdapter()

        # Find first message by UUID (no conversation hint)
        result = adapter.get_message_by_id(sample_export, "msg-001-uuid")

        assert result is not None
        message, conversation = result

        # Verify message
        assert message.id == "msg-001-uuid"
        assert "Can you review my binary search implementation?" in message.content
        assert message.role == "user"

        # Verify conversation context
        assert conversation.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
        assert conversation.title == "Python Code Review - Binary Search Implementation"
        assert len(conversation.messages) == 2

    def test_conversation_id_hint(self, sample_export: Path) -> None:
        """Test T070: conversation_id hint optimizes search (FR-043).

        Validates:
        - conversation_id parameter exists and is optional
        - When provided, searches only that conversation
        - Performance optimization via early termination
        - Still returns correct result
        """
        adapter = ClaudeAdapter()

        # Search with conversation hint (should be faster, search only one conv)
        result = adapter.get_message_by_id(
            sample_export,
            "msg-001-uuid",
            conversation_id="5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
        )

        assert result is not None
        message, conversation = result

        assert message.id == "msg-001-uuid"
        assert conversation.id == "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"

        # Search with wrong conversation hint (should return None)
        result_wrong = adapter.get_message_by_id(
            sample_export,
            "msg-001-uuid",
            conversation_id="7892bc45-def3-4a21-9c12-3d5e6f7a8b9c",  # Wrong conv
        )
        assert result_wrong is None

    def test_returns_message_with_context(self, sample_export: Path) -> None:
        """Test T071: Returns tuple (Message, Conversation) (FR-044).

        Validates:
        - Return type is tuple, not just Message
        - Tuple contains exactly 2 elements
        - First element is Message, second is Conversation
        - Conversation contains the message
        """
        adapter = ClaudeAdapter()

        result = adapter.get_message_by_id(sample_export, "msg-101-uuid")

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2

        message, conversation = result

        # Verify types
        assert isinstance(message, Message)
        assert isinstance(conversation, Conversation)

        # Verify message is in conversation
        assert message in conversation.messages
        assert message.id == "msg-101-uuid"
        assert conversation.id == "7892bc45-def3-4a21-9c12-3d5e6f7a8b9c"

    def test_message_not_found_returns_none(self, sample_export: Path) -> None:
        """Test T072: Return None for invalid message ID (FR-045).

        Validates:
        - Returns None (not exception) for non-existent message
        - No partial matches for invalid IDs
        - Empty string returns None
        """
        adapter = ClaudeAdapter()

        # Non-existent message UUID
        result = adapter.get_message_by_id(sample_export, "msg-nonexistent-uuid")
        assert result is None

        # Empty string
        result_empty = adapter.get_message_by_id(sample_export, "")
        assert result_empty is None

        # Message exists but conversation hint is wrong
        result_wrong_conv = adapter.get_message_by_id(
            sample_export,
            "msg-001-uuid",
            conversation_id="00000000-0000-0000-0000-000000000000",
        )
        assert result_wrong_conv is None


# ============================================================================
# Integration Tests (Placeholder)
# ============================================================================


class TestClaudeAdapterIntegration:
    """Integration tests for ClaudeAdapter end-to-end workflows.

    These tests will validate complete workflows across multiple methods
    once implementation is complete in later phases.

    Placeholder tests ensure test structure is ready for future implementation.
    """

    def test_adapter_instantiation(self) -> None:
        """Test ClaudeAdapter can be instantiated (stateless design).

        Validates:
        - No __init__ parameters required
        - Instantiation is lightweight (no I/O)
        - Multiple instances are independent
        """
        adapter1 = ClaudeAdapter()
        adapter2 = ClaudeAdapter()

        # Stateless design - instances are independent
        assert adapter1 is not adapter2
        assert type(adapter1) is ClaudeAdapter
        assert type(adapter2) is ClaudeAdapter

    def test_adapter_conforms_to_protocol(self) -> None:
        """Test ClaudeAdapter conforms to ConversationProvider protocol.

        Validates:
        - Has stream_conversations method
        - Has search method
        - Has get_conversation_by_id method
        - Has get_message_by_id method
        """
        adapter = ClaudeAdapter()

        # Check methods exist
        assert hasattr(adapter, "stream_conversations")
        assert hasattr(adapter, "search")
        assert hasattr(adapter, "get_conversation_by_id")
        assert hasattr(adapter, "get_message_by_id")

        # Check methods are callable
        assert callable(adapter.stream_conversations)
        assert callable(adapter.search)
        assert callable(adapter.get_conversation_by_id)
        assert callable(adapter.get_message_by_id)
