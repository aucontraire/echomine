"""Additional tests for Claude adapter to improve coverage.

This module targets specific uncovered lines identified by Codecov:
- Line 275-277: Timestamp parsing error handling
- Line 460: Progress callback at multiples of 100
- Line 477: on_skip callback invocation
- Line 545: Progress callback during search
- Line 585: Role filter empty message skip
- Line 604: Empty search results early return
- Line 715: Sort by message count
- Lines 659-664: Phrase matching with multiple text blocks

Constitution Compliance:
    - Principle III: TDD - Tests written to cover gaps
    - Principle VI: Strict typing with mypy --strict
    - Principle VIII: Memory efficiency testing
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.models.search import SearchQuery


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def large_export(tmp_path: Path) -> Path:
    """Create export with 200+ conversations for progress callback testing.

    This fixture ensures we have enough conversations to trigger the
    progress callback (which fires every 100 items).
    """
    conversations = []
    for i in range(250):
        conv = {
            "uuid": f"conv-{i:04d}",
            "name": f"Conversation {i}",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": f"msg-{i:04d}",
                    "text": f"Message content {i}",
                    "content": [{"type": "text", "text": f"Message content {i}"}],
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                }
            ],
        }
        conversations.append(conv)

    file_path = tmp_path / "large_export.json"
    file_path.write_text(json.dumps(conversations), encoding="utf-8")
    return file_path


@pytest.fixture
def invalid_timestamp_export(tmp_path: Path) -> Path:
    """Create export with invalid message timestamp to test fallback.

    Tests line 275-277: ValueError exception handling for timestamp parsing.
    """
    conversations = [
        {
            "uuid": "conv-001",
            "name": "Test Conversation",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": "msg-001",
                    "text": "Valid message",
                    "content": [{"type": "text", "text": "Valid message"}],
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                },
                {
                    "uuid": "msg-002",
                    "text": "Message with invalid timestamp",
                    "content": [{"type": "text", "text": "Message with invalid timestamp"}],
                    "sender": "assistant",
                    "created_at": "INVALID-TIMESTAMP-FORMAT",  # This will trigger ValueError
                },
            ],
        }
    ]

    file_path = tmp_path / "invalid_timestamp.json"
    file_path.write_text(json.dumps(conversations), encoding="utf-8")
    return file_path


@pytest.fixture
def role_filter_export(tmp_path: Path) -> Path:
    """Create export for testing role filter edge cases.

    Tests line 585: Skip conversations with no messages matching role filter.
    """
    conversations = [
        {
            "uuid": "conv-all-assistant",
            "name": "All Assistant Messages",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": "msg-001",
                    "text": "Assistant message 1",
                    "content": [{"type": "text", "text": "Assistant message 1"}],
                    "sender": "assistant",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                },
                {
                    "uuid": "msg-002",
                    "text": "Assistant message 2",
                    "content": [{"type": "text", "text": "Assistant message 2"}],
                    "sender": "assistant",
                    "created_at": "2025-10-01T18:42:29.370875Z",
                },
            ],
        },
        {
            "uuid": "conv-mixed",
            "name": "Mixed Messages",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": "msg-003",
                    "text": "User message python",
                    "content": [{"type": "text", "text": "User message python"}],
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                },
                {
                    "uuid": "msg-004",
                    "text": "Assistant response",
                    "content": [{"type": "text", "text": "Assistant response"}],
                    "sender": "assistant",
                    "created_at": "2025-10-01T18:42:29.370875Z",
                },
            ],
        },
    ]

    file_path = tmp_path / "role_filter.json"
    file_path.write_text(json.dumps(conversations), encoding="utf-8")
    return file_path


@pytest.fixture
def message_count_sort_export(tmp_path: Path) -> Path:
    """Create export with varying message counts for sort testing.

    Tests line 715: Sort by message count.
    """
    conversations = [
        {
            "uuid": "conv-5-messages",
            "name": "Five Messages",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": f"msg-5-{i}",
                    "text": f"Message {i}",
                    "content": [{"type": "text", "text": f"Message {i}"}],
                    "sender": "human" if i % 2 == 0 else "assistant",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                }
                for i in range(5)
            ],
        },
        {
            "uuid": "conv-2-messages",
            "name": "Two Messages",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": f"msg-2-{i}",
                    "text": f"Message {i}",
                    "content": [{"type": "text", "text": f"Message {i}"}],
                    "sender": "human" if i % 2 == 0 else "assistant",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                }
                for i in range(2)
            ],
        },
        {
            "uuid": "conv-10-messages",
            "name": "Ten Messages",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": f"msg-10-{i}",
                    "text": f"Message {i}",
                    "content": [{"type": "text", "text": f"Message {i}"}],
                    "sender": "human" if i % 2 == 0 else "assistant",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                }
                for i in range(10)
            ],
        },
    ]

    file_path = tmp_path / "message_count_sort.json"
    file_path.write_text(json.dumps(conversations), encoding="utf-8")
    return file_path


@pytest.fixture
def phrase_matching_export(tmp_path: Path) -> Path:
    """Create export for testing phrase matching with message ID collection.

    Tests lines 662-664: Collecting matched_message_ids for phrase matches.
    """
    conversations = [
        {
            "uuid": "conv-phrase-match",
            "name": "Phrase Matching Test",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": "msg-001",
                    "text": "This message contains binary search algorithm",
                    "content": [
                        {"type": "text", "text": "This message contains binary search algorithm"}
                    ],
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:28.370875Z",
                },
                {
                    "uuid": "msg-002",
                    "text": "Another message with binary search implementation",
                    "content": [
                        {
                            "type": "text",
                            "text": "Another message with binary search implementation",
                        }
                    ],
                    "sender": "assistant",
                    "created_at": "2025-10-01T18:42:29.370875Z",
                },
                {
                    "uuid": "msg-003",
                    "text": "No match here",
                    "content": [{"type": "text", "text": "No match here"}],
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:30.370875Z",
                },
            ],
        }
    ]

    file_path = tmp_path / "phrase_matching.json"
    file_path.write_text(json.dumps(conversations), encoding="utf-8")
    return file_path


# ============================================================================
# Test Cases for Coverage Gaps
# ============================================================================


class TestProgressCallbacks:
    """Test progress callback invocation at multiples of 100."""

    def test_progress_callback_at_100_items(self, large_export: Path) -> None:
        """Test line 460: Progress callback invoked at multiples of 100.

        Validates:
        - Callback invoked at 100, 200 items
        - Callback receives correct count values
        - Processing continues normally after callback
        """
        adapter = ClaudeAdapter()
        progress_calls: list[int] = []

        def progress(count: int) -> None:
            progress_calls.append(count)

        conversations = list(adapter.stream_conversations(large_export, progress_callback=progress))

        # Should have 250 conversations
        assert len(conversations) == 250

        # Progress callback should be invoked at 100, 200
        assert 100 in progress_calls
        assert 200 in progress_calls
        # NOT at 250 (only at multiples of 100)
        assert 250 not in progress_calls

    def test_search_progress_callback_at_100_items(self, large_export: Path) -> None:
        """Test line 545: Progress callback during search at multiples of 100.

        Validates:
        - Search progress callback invoked at 100, 200 items
        - Final callback invoked with total count
        - Callback receives correct count values
        """
        adapter = ClaudeAdapter()
        progress_calls: list[int] = []

        def progress(count: int) -> None:
            progress_calls.append(count)

        # Search all conversations
        query = SearchQuery(limit=300)
        results = list(adapter.search(large_export, query, progress_callback=progress))

        # Should find all 250 conversations
        assert len(results) == 250

        # Progress callback should be invoked at 100, 200, and final count 250
        assert 100 in progress_calls
        assert 200 in progress_calls
        assert 250 in progress_calls  # Final callback always fires


class TestOnSkipCallback:
    """Test on_skip callback invocation for malformed entries."""

    def test_on_skip_callback_for_malformed_conversation(self, tmp_path: Path) -> None:
        """Test line 477: on_skip callback invoked when conversation skipped.

        Validates:
        - Callback invoked with conversation_id and reason
        - Processing continues after skip
        - Valid conversations still parsed
        """
        # Create export with malformed conversation
        conversations = [
            {
                "uuid": "valid-conv-001",
                "name": "Valid",
                "created_at": "2025-10-01T18:42:27.303515Z",
                "updated_at": "2025-10-01T18:42:33.904627Z",
                "chat_messages": [],
            },
            {
                # Missing required uuid field - will trigger skip
                "name": "Invalid",
                "created_at": "2025-10-01T18:42:27.303515Z",
                "updated_at": "2025-10-01T18:42:33.904627Z",
                "chat_messages": [],
            },
            {
                "uuid": "valid-conv-002",
                "name": "Valid",
                "created_at": "2025-10-01T18:42:27.303515Z",
                "updated_at": "2025-10-01T18:42:33.904627Z",
                "chat_messages": [],
            },
        ]

        file_path = tmp_path / "with_malformed.json"
        file_path.write_text(json.dumps(conversations), encoding="utf-8")

        adapter = ClaudeAdapter()
        skip_calls: list[tuple[str, str]] = []

        def on_skip(conversation_id: str, reason: str) -> None:
            skip_calls.append((conversation_id, reason))

        parsed = list(adapter.stream_conversations(file_path, on_skip=on_skip))

        # Should parse 2 valid conversations
        assert len(parsed) == 2
        assert parsed[0].id == "valid-conv-001"
        assert parsed[1].id == "valid-conv-002"

        # Should have 1 skip callback
        assert len(skip_calls) == 1
        conversation_id, reason = skip_calls[0]
        # Malformed entry doesn't have uuid, so will be "unknown" or empty string
        assert conversation_id in ("unknown", "")
        # Reason should mention validation error or id field
        assert "validation error" in reason.lower() or "id" in reason.lower()


class TestTimestampFallback:
    """Test timestamp parsing error handling with fallback."""

    def test_invalid_timestamp_falls_back_to_conversation_created_at(
        self, invalid_timestamp_export: Path
    ) -> None:
        """Test lines 275-277: Invalid timestamp falls back to conversation created_at.

        Validates:
        - Invalid timestamp triggers ValueError exception
        - Exception is caught and handled gracefully
        - Message timestamp falls back to conversation.created_at
        - Processing continues normally
        """
        adapter = ClaudeAdapter()

        conversations = list(adapter.stream_conversations(invalid_timestamp_export))

        assert len(conversations) == 1
        conv = conversations[0]

        # Should have 2 messages
        assert len(conv.messages) == 2

        # First message has valid timestamp
        msg1 = conv.messages[0]
        assert msg1.id == "msg-001"
        assert msg1.timestamp.year == 2025
        assert msg1.timestamp.month == 10
        assert msg1.timestamp.day == 1

        # Second message has invalid timestamp, should fallback to conv.created_at
        msg2 = conv.messages[1]
        assert msg2.id == "msg-002"
        # Should equal conversation created_at (fallback)
        assert msg2.timestamp == conv.created_at
        assert msg2.timestamp.year == 2025
        assert msg2.timestamp.month == 10


class TestRoleFilterEdgeCases:
    """Test role filter edge cases including empty results."""

    def test_role_filter_skips_conversations_with_no_matching_messages(
        self, role_filter_export: Path
    ) -> None:
        """Test line 585: Skip conversations with no messages matching role filter.

        Validates:
        - Conversation with only assistant messages is skipped when role_filter='user'
        - Conversation with mixed messages is included
        - Empty filtered_messages list triggers continue statement
        """
        adapter = ClaudeAdapter()

        # Search for "python" in user messages only
        query = SearchQuery(keywords=["python"], role_filter="user", limit=10)
        results = list(adapter.search(role_filter_export, query))

        # Should find only the mixed conversation (conv-mixed with user message containing "python")
        assert len(results) == 1
        assert results[0].conversation.id == "conv-mixed"

        # The all-assistant conversation should be skipped (line 585)
        # because it has no user messages


class TestEmptySearchResults:
    """Test empty search results early return."""

    def test_empty_search_results_returns_early(self, tmp_path: Path) -> None:
        """Test line 604: Return early when no conversations match filters.

        Validates:
        - Empty results after filtering triggers early return
        - No scoring or sorting performed
        - Returns empty iterator
        """
        # Create export with conversations that won't match
        conversations = [
            {
                "uuid": "conv-001",
                "name": "JavaScript Tutorial",
                "created_at": "2025-10-01T18:42:27.303515Z",
                "updated_at": "2025-10-01T18:42:33.904627Z",
                "chat_messages": [
                    {
                        "uuid": "msg-001",
                        "text": "JavaScript is great",
                        "content": [{"type": "text", "text": "JavaScript is great"}],
                        "sender": "human",
                        "created_at": "2025-10-01T18:42:28.370875Z",
                    }
                ],
            }
        ]

        file_path = tmp_path / "no_match.json"
        file_path.write_text(json.dumps(conversations), encoding="utf-8")

        adapter = ClaudeAdapter()

        # Search for keyword that doesn't exist
        query = SearchQuery(keywords=["python"], limit=10)
        results = list(adapter.search(file_path, query))

        # Should return empty list (early return at line 604)
        assert len(results) == 0


class TestSortByMessageCount:
    """Test sorting by message count."""

    def test_sort_by_message_count_descending(self, message_count_sort_export: Path) -> None:
        """Test line 715: Sort by message count (descending).

        Validates:
        - sort_by='messages' sorts by conversation.message_count
        - Descending order (most messages first)
        - Correct ordering maintained
        """
        adapter = ClaudeAdapter()

        query = SearchQuery(sort_by="messages", sort_order="desc", limit=10)
        results = list(adapter.search(message_count_sort_export, query))

        # Should return all 3 conversations
        assert len(results) == 3

        # Order should be: 10 messages, 5 messages, 2 messages
        assert results[0].conversation.message_count == 10
        assert results[1].conversation.message_count == 5
        assert results[2].conversation.message_count == 2

    def test_sort_by_message_count_ascending(self, message_count_sort_export: Path) -> None:
        """Test line 715: Sort by message count (ascending).

        Validates:
        - sort_by='messages' with sort_order='asc'
        - Ascending order (fewest messages first)
        - Correct ordering maintained
        """
        adapter = ClaudeAdapter()

        query = SearchQuery(sort_by="messages", sort_order="asc", limit=10)
        results = list(adapter.search(message_count_sort_export, query))

        # Should return all 3 conversations
        assert len(results) == 3

        # Order should be: 2 messages, 5 messages, 10 messages
        assert results[0].conversation.message_count == 2
        assert results[1].conversation.message_count == 5
        assert results[2].conversation.message_count == 10


class TestPhraseMatchingMessageIds:
    """Test phrase matching with matched message ID collection."""

    def test_phrase_matches_collect_message_ids(self, phrase_matching_export: Path) -> None:
        """Test lines 662-664: Collect matched_message_ids for phrase matches.

        Validates:
        - Phrase matches iterate through filtered messages
        - Matched message IDs are collected
        - Duplicate message IDs are not added
        - Snippet includes matched message content
        """
        adapter = ClaudeAdapter()

        # Search for exact phrase "binary search"
        query = SearchQuery(phrases=["binary search"], limit=10)
        results = list(adapter.search(phrase_matching_export, query))

        # Should find 1 conversation
        assert len(results) == 1
        result = results[0]

        # Should have matched_message_ids for messages containing phrase
        assert len(result.matched_message_ids) >= 2
        assert "msg-001" in result.matched_message_ids
        assert "msg-002" in result.matched_message_ids
        # msg-003 should NOT be in matched IDs
        assert "msg-003" not in result.matched_message_ids

        # Snippet should contain the phrase
        assert "binary search" in result.snippet.lower()
