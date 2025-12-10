"""Integration tests for message count filtering in search.

Task: T022 - Integration Test - Message Count Search Filtering
Phase: RED (tests designed to FAIL initially)
Feature: 003-baseline-enhancements (US9 Library-First Message Count Filtering)

This module tests the complete end-to-end workflow for message count filtering:
1. Read OpenAI export JSON file from disk
2. Stream parse conversations using ijson
3. Apply message count filters (min_messages, max_messages)
4. Filter out conversations outside the range
5. Return matching results

Test Pyramid Classification: Integration (20% of test suite)
These tests validate component integration but NOT CLI interface.

Architectural Coverage:
- StreamingParser → SearchEngine → MessageCountFilter → OpenAIAdapter
- File I/O → JSON streaming → Filtering → Results

Requirements Validated:
- FR-004: SearchQuery min_messages/max_messages fields
- FR-005: Validation (min >= 1, max >= min)
- FR-006: Streaming approach (O(1) memory)
- FR-007: JSON output includes message_count field
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def message_count_test_export(tmp_path: Path) -> Path:
    """Create test fixture with conversations of varying message counts.

    This fixture is specifically designed to test message count filtering:
    - Conv 1: 1 message (edge case: minimum)
    - Conv 2: 5 messages
    - Conv 3: 10 messages
    - Conv 4: 15 messages
    - Conv 5: 20 messages
    - Conv 6: 50 messages
    - Conv 7: 100 messages (edge case: large)

    Returns:
        Path to test export file
    """
    import json

    def create_conversation(conv_id: str, message_count: int) -> dict[str, Any]:
        """Helper to create conversation with specific message count."""
        mapping = {}
        for i in range(message_count):
            msg_id = f"msg-{conv_id}-{i:03d}"
            parent_id = f"msg-{conv_id}-{i - 1:03d}" if i > 0 else None

            mapping[msg_id] = {
                "id": msg_id,
                "message": {
                    "id": msg_id,
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": [f"Message {i} content for conversation {conv_id}"],
                    },
                    "create_time": 1710000000.0 + (i * 10),
                    "update_time": None,
                    "metadata": {},
                },
                "parent": parent_id,
                "children": [f"msg-{conv_id}-{i + 1:03d}"] if i < message_count - 1 else [],
            }

        return {
            "id": conv_id,
            "title": f"Conversation with {message_count} messages",
            "create_time": 1710000000.0,
            "update_time": 1710000000.0 + (message_count * 10),
            "mapping": mapping,
            "moderation_results": [],
            "current_node": f"msg-{conv_id}-{message_count - 1:03d}",
        }

    conversations = [
        create_conversation("conv-001", 1),
        create_conversation("conv-002", 5),
        create_conversation("conv-003", 10),
        create_conversation("conv-004", 15),
        create_conversation("conv-005", 20),
        create_conversation("conv-006", 50),
        create_conversation("conv-007", 100),
    ]

    export_file = tmp_path / "message_count_test_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2)

    return export_file


@pytest.mark.integration
class TestMessageCountFiltering:
    """Integration tests for message count filtering in adapter.search().

    Tests the complete chain: File → Parser → MessageCountFilter → Results
    Expected Failure Reasons (RED phase):
    - Message count filtering not implemented in adapter.search()
    - SearchQuery missing min_messages/max_messages fields
    """

    def test_filter_by_min_messages_only(self, message_count_test_export: Path) -> None:
        """Test filtering with only min_messages specified (FR-001, FR-004).

        Expected to FAIL: min_messages filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with min_messages=10
        query = SearchQuery(min_messages=10)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Only conversations with >= 10 messages
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-003", "conv-004", "conv-005", "conv-006", "conv-007"}

        assert result_ids == expected_ids, (
            f"min_messages=10 should filter conversations with <10 messages. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        # Verify message counts
        for result in results:
            assert result.conversation.message_count >= 10, (
                f"Conversation {result.conversation.id} has "
                f"{result.conversation.message_count} messages, expected >= 10"
            )

    def test_filter_by_max_messages_only(self, message_count_test_export: Path) -> None:
        """Test filtering with only max_messages specified (FR-002, FR-004).

        Expected to FAIL: max_messages filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with max_messages=20
        query = SearchQuery(max_messages=20)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Only conversations with <= 20 messages
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-001", "conv-002", "conv-003", "conv-004", "conv-005"}

        assert result_ids == expected_ids, (
            f"max_messages=20 should filter conversations with >20 messages. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        # Verify message counts
        for result in results:
            assert result.conversation.message_count <= 20, (
                f"Conversation {result.conversation.id} has "
                f"{result.conversation.message_count} messages, expected <= 20"
            )

    def test_filter_by_min_and_max_messages_range(self, message_count_test_export: Path) -> None:
        """Test filtering with both min and max (range filter) (FR-003, FR-004).

        Expected to FAIL: Range filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with min=10, max=50
        query = SearchQuery(min_messages=10, max_messages=50)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Only conversations in [10, 50] range
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-003", "conv-004", "conv-005", "conv-006"}

        assert result_ids == expected_ids, (
            f"min=10, max=50 should filter conversations outside [10, 50]. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        # Verify message counts are in range
        for result in results:
            msg_count = result.conversation.message_count
            assert 10 <= msg_count <= 50, (
                f"Conversation {result.conversation.id} has {msg_count} messages, expected [10, 50]"
            )

    def test_edge_case_exact_count_min_equals_max(self, message_count_test_export: Path) -> None:
        """Test exact count matching when min == max (FR-004, Edge Case).

        Expected to FAIL: Exact count filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for conversations with exactly 10 messages
        query = SearchQuery(min_messages=10, max_messages=10)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Only conv-003 has exactly 10 messages
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-003"}

        assert result_ids == expected_ids, (
            f"min=10, max=10 should return only conversations with exactly 10 messages. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        # Verify exact count
        assert len(results) == 1
        assert results[0].conversation.message_count == 10

    def test_edge_case_min_1_max_1_single_message(self, message_count_test_export: Path) -> None:
        """Test filtering for conversations with exactly 1 message (FR-004, T020).

        Expected to FAIL: Single message filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for conversations with exactly 1 message
        query = SearchQuery(min_messages=1, max_messages=1)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Only conv-001 has exactly 1 message
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-001"}

        assert result_ids == expected_ids, (
            f"min=1, max=1 should return conversations with exactly 1 message. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        assert results[0].conversation.message_count == 1

    def test_message_count_filter_combines_with_keywords(
        self, message_count_test_export: Path
    ) -> None:
        """Test message count filters combine with keyword search (FR-003).

        Expected to FAIL: Combined filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with keywords AND message count filter
        query = SearchQuery(keywords=["conversation"], min_messages=20)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: All results have "conversation" keyword AND >= 20 messages
        # All our test conversations have "conversation" in message content
        result_ids = {r.conversation.id for r in results}
        expected_ids = {"conv-005", "conv-006", "conv-007"}

        assert result_ids == expected_ids, (
            f"Keywords + min_messages should apply both filters. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

        # Verify all results meet both conditions
        for result in results:
            assert result.conversation.message_count >= 20
            # Keyword match verified by presence in results

    def test_message_count_filter_with_limit(self, message_count_test_export: Path) -> None:
        """Test message count filter respects limit parameter.

        Expected to FAIL: Message count + limit not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with min_messages and limit
        query = SearchQuery(min_messages=10, limit=3)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: No more than 3 results
        assert len(results) <= 3, f"Limit=3 should return max 3 results, got {len(results)}"

        # All results should have >= 10 messages
        for result in results:
            assert result.conversation.message_count >= 10

    def test_no_results_when_no_conversations_match_count(
        self, message_count_test_export: Path
    ) -> None:
        """Test empty results when no conversations match message count filter.

        Expected to FAIL: Empty result handling not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for conversations with >200 messages (none exist)
        query = SearchQuery(min_messages=200)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: Empty results
        assert len(results) == 0, "Should return empty when no conversations match count filter"

    def test_streaming_applies_message_count_filter_efficiently(
        self, message_count_test_export: Path
    ) -> None:
        """Test that message count filtering happens during streaming (FR-006).

        This test verifies O(1) memory usage by checking that filtering
        happens during iteration, not post-processing.

        Expected to FAIL: Streaming filter not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Use generator without consuming all results
        query = SearchQuery(min_messages=50)
        results_generator = adapter.search(message_count_test_export, query)

        # Take first result only (should not load entire export)
        first_result = next(results_generator, None)

        assert first_result is not None
        assert first_result.conversation.message_count >= 50

        # Verify it's a generator (not list)
        from collections.abc import Iterator

        assert isinstance(adapter.search(message_count_test_export, query), Iterator)

    def test_message_count_in_search_result_json_output(
        self, message_count_test_export: Path
    ) -> None:
        """Test that SearchResult includes message_count field (FR-007).

        Expected to FAIL: message_count not exposed in result.
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(min_messages=10)
        results = list(adapter.search(message_count_test_export, query))

        # Assert: All results have message_count accessible
        for result in results:
            # Verify conversation has message_count attribute
            assert hasattr(result.conversation, "message_count")
            assert isinstance(result.conversation.message_count, int)
            assert result.conversation.message_count >= 10
