"""Test statistics calculation functions.

This module tests the calculate_statistics() and calculate_conversation_statistics()
functions from echomine.statistics.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle VI: Strict typing with mypy --strict compliance
    - Principle VIII: O(1) memory usage via streaming

Test Coverage:
    - T039: calculate_statistics() returns ExportStatistics
    - T040: calculate_conversation_statistics() returns ConversationStatistics
    - T041: Edge case - empty export file returns zeros
    - T042: Edge case - all malformed entries returns zeros with skipped_count
    - T043: Edge case - conversation with 1 message has average_gap_seconds = None
    - T044: Edge case - conversation with 0 messages handled gracefully
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.statistics import RoleCount


class TestCalculateStatistics:
    """Test calculate_statistics() function (T039, T041, T042)."""

    def test_calculate_statistics_returns_export_statistics(self, tmp_path: Path) -> None:
        """Test calculate_statistics() returns ExportStatistics (T039)."""
        from echomine.statistics import calculate_statistics

        # Create test export file
        export_data = [
            {
                "id": "conv-1",
                "title": "First Conversation",
                "create_time": 1704110400.0,  # 2024-01-01 12:00:00 UTC
                "update_time": 1704197000.0,  # 2024-01-02 12:03:20 UTC
                "mapping": {
                    "node-1": {
                        "id": "node-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                            "create_time": 1704110410.0,
                        },
                        "parent": None,
                        "children": [],
                    },
                    "node-2": {
                        "id": "node-2",
                        "message": {
                            "id": "msg-2",
                            "author": {"role": "assistant"},
                            "content": {"content_type": "text", "parts": ["Hi there!"]},
                            "create_time": 1704110420.0,
                        },
                        "parent": "node-1",
                        "children": [],
                    },
                },
            },
            {
                "id": "conv-2",
                "title": "Second Conversation",
                "create_time": 1704283200.0,  # 2024-01-03 12:00:00 UTC
                "update_time": 1704283300.0,
                "mapping": {
                    "node-3": {
                        "id": "node-3",
                        "message": {
                            "id": "msg-3",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Question"]},
                            "create_time": 1704283210.0,
                        },
                        "parent": None,
                        "children": [],
                    },
                },
            },
        ]

        export_file = tmp_path / "export.json"
        export_file.write_text(json.dumps(export_data))

        # Calculate statistics
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter)

        # Verify ExportStatistics returned
        assert stats.total_conversations == 2
        assert stats.total_messages == 3
        assert stats.earliest_date == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert stats.latest_date == datetime(2024, 1, 3, 12, 1, 40, tzinfo=UTC)
        assert stats.average_messages == 1.5
        assert stats.largest_conversation is not None
        assert stats.largest_conversation.id == "conv-1"
        assert stats.largest_conversation.message_count == 2
        assert stats.smallest_conversation is not None
        assert stats.smallest_conversation.id == "conv-2"
        assert stats.smallest_conversation.message_count == 1
        assert stats.skipped_count == 0

    def test_calculate_statistics_empty_export(self, tmp_path: Path) -> None:
        """Test calculate_statistics() with empty export returns zeros (T041)."""
        from echomine.statistics import calculate_statistics

        # Create empty export file
        export_file = tmp_path / "empty_export.json"
        export_file.write_text("[]")

        # Calculate statistics
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter)

        # Verify zeros for empty export
        assert stats.total_conversations == 0
        assert stats.total_messages == 0
        assert stats.earliest_date is None
        assert stats.latest_date is None
        assert stats.average_messages == 0.0
        assert stats.largest_conversation is None
        assert stats.smallest_conversation is None
        assert stats.skipped_count == 0

    def test_calculate_statistics_all_malformed(self, tmp_path: Path) -> None:
        """Test calculate_statistics() with all malformed entries (T042)."""
        from echomine.statistics import calculate_statistics

        # Create export with all malformed conversations
        export_data = [
            {"id": "conv-1"},  # Missing required fields
            {"title": "No ID"},  # Missing id field
            {},  # Empty object
        ]

        export_file = tmp_path / "malformed_export.json"
        export_file.write_text(json.dumps(export_data))

        # Calculate statistics (should skip all entries)
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter)

        # Verify zeros with skipped_count
        assert stats.total_conversations == 0
        assert stats.total_messages == 0
        assert stats.earliest_date is None
        assert stats.latest_date is None
        assert stats.average_messages == 0.0
        assert stats.largest_conversation is None
        assert stats.smallest_conversation is None
        assert stats.skipped_count == 3

    def test_calculate_statistics_with_progress_callback(self, tmp_path: Path) -> None:
        """Test calculate_statistics() invokes progress_callback."""
        from echomine.statistics import calculate_statistics

        # Create export with 250 conversations (to trigger callback at 100, 200)
        export_data = []
        for i in range(250):
            export_data.append(
                {
                    "id": f"conv-{i}",
                    "title": f"Conversation {i}",
                    "create_time": 1704110400.0 + i * 100,
                    "update_time": 1704110400.0 + i * 100,
                    "mapping": {
                        f"node-{i}": {
                            "id": f"node-{i}",
                            "message": {
                                "id": f"msg-{i}",
                                "author": {"role": "user"},
                                "content": {"content_type": "text", "parts": [f"Message {i}"]},
                                "create_time": 1704110400.0 + i * 100,
                            },
                            "parent": None,
                            "children": [],
                        },
                    },
                }
            )

        export_file = tmp_path / "large_export.json"
        export_file.write_text(json.dumps(export_data))

        # Track progress callbacks
        progress_calls: list[int] = []

        def progress_callback(count: int) -> None:
            progress_calls.append(count)

        # Calculate statistics with progress callback
        adapter = OpenAIAdapter()
        stats = calculate_statistics(
            export_file, adapter=adapter, progress_callback=progress_callback
        )

        # Verify progress callback invoked at 100, 200
        assert 100 in progress_calls
        assert 200 in progress_calls
        assert stats.total_conversations == 250

    def test_calculate_statistics_with_on_skip_callback(self, tmp_path: Path) -> None:
        """Test calculate_statistics() invokes on_skip callback for malformed entries."""
        from echomine.statistics import calculate_statistics

        # Create export with mix of valid and malformed conversations
        export_data = [
            {
                "id": "conv-1",
                "title": "Valid",
                "create_time": 1704110400.0,
                "update_time": 1704110400.0,
                "mapping": {
                    "node-1": {
                        "id": "node-1",
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                            "create_time": 1704110400.0,
                        },
                        "parent": None,
                        "children": [],
                    },
                },
            },
            {"id": "conv-2"},  # Missing required fields
            {
                "id": "conv-3",
                "title": "Also Valid",
                "create_time": 1704110500.0,
                "update_time": 1704110500.0,
                "mapping": {
                    "node-3": {
                        "id": "node-3",
                        "message": {
                            "id": "msg-3",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["World"]},
                            "create_time": 1704110500.0,
                        },
                        "parent": None,
                        "children": [],
                    },
                },
            },
        ]

        export_file = tmp_path / "mixed_export.json"
        export_file.write_text(json.dumps(export_data))

        # Track on_skip callbacks
        skip_calls: list[tuple[str, str]] = []

        def on_skip_callback(conversation_id: str, reason: str) -> None:
            skip_calls.append((conversation_id, reason))

        # Calculate statistics with on_skip callback
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter, on_skip=on_skip_callback)

        # Verify on_skip invoked for conv-2
        assert len(skip_calls) == 1
        assert skip_calls[0][0] == "conv-2"
        assert "validation error" in skip_calls[0][1].lower()
        assert stats.total_conversations == 2
        assert stats.skipped_count == 1


class TestCalculateConversationStatistics:
    """Test calculate_conversation_statistics() function (T040, T043, T044)."""

    def test_calculate_conversation_statistics_returns_stats(self) -> None:
        """Test calculate_conversation_statistics() returns ConversationStatistics (T040)."""
        from echomine.statistics import calculate_conversation_statistics

        # Create conversation with multiple messages
        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        updated = datetime(2024, 1, 15, 14, 45, 0, tzinfo=UTC)

        messages = [
            Message(
                id="msg-1",
                content="Hello",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                parent_id=None,
            ),
            Message(
                id="msg-2",
                content="Hi there!",
                role="assistant",
                timestamp=datetime(2024, 1, 15, 10, 30, 47, tzinfo=UTC),
                parent_id="msg-1",
            ),
            Message(
                id="msg-3",
                content="How are you?",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 31, 10, tzinfo=UTC),
                parent_id="msg-2",
            ),
        ]

        conversation = Conversation(
            id="conv-123",
            title="Test Conversation",
            created_at=created,
            updated_at=updated,
            messages=messages,
        )

        # Calculate statistics
        stats = calculate_conversation_statistics(conversation)

        # Verify ConversationStatistics returned
        assert stats.conversation_id == "conv-123"
        assert stats.title == "Test Conversation"
        assert stats.created_at == created
        assert stats.updated_at == updated
        assert stats.message_count == 3
        assert stats.message_count_by_role == RoleCount(user=2, assistant=1, system=0)
        assert stats.first_message == datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC)
        assert stats.last_message == datetime(2024, 1, 15, 10, 31, 10, tzinfo=UTC)
        assert stats.duration_seconds == 65.0
        # Average gap: (42 + 23) / 2 = 32.5 seconds
        assert stats.average_gap_seconds == 32.5

    def test_calculate_conversation_statistics_single_message(self) -> None:
        """Test calculate_conversation_statistics() with 1 message has average_gap_seconds = None (T043)."""
        from echomine.statistics import calculate_conversation_statistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        messages = [
            Message(
                id="msg-1",
                content="Hello",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                parent_id=None,
            ),
        ]

        conversation = Conversation(
            id="conv-123",
            title="Single Message",
            created_at=created,
            messages=messages,
        )

        # Calculate statistics
        stats = calculate_conversation_statistics(conversation)

        # Verify average_gap_seconds is None for single message
        assert stats.message_count == 1
        assert stats.first_message == datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC)
        assert stats.last_message == datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC)
        assert stats.duration_seconds == 0.0
        assert stats.average_gap_seconds is None

    # NOTE: Test for 0-message conversation (T044) is not needed because:
    # Conversation model enforces min_length=1 on messages field (FR-108).
    # Empty conversations cannot exist in the data model, so calculate_conversation_statistics()
    # will never receive a conversation with 0 messages. This is correct behavior.

    def test_calculate_conversation_statistics_role_counts(self) -> None:
        """Test calculate_conversation_statistics() calculates role counts correctly."""
        from echomine.statistics import calculate_conversation_statistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        messages = [
            Message(
                id="msg-1",
                content="User 1",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
                parent_id=None,
            ),
            Message(
                id="msg-2",
                content="Assistant 1",
                role="assistant",
                timestamp=datetime(2024, 1, 15, 10, 30, 10, tzinfo=UTC),
                parent_id="msg-1",
            ),
            Message(
                id="msg-3",
                content="User 2",
                role="user",
                timestamp=datetime(2024, 1, 15, 10, 30, 15, tzinfo=UTC),
                parent_id="msg-2",
            ),
            Message(
                id="msg-4",
                content="System message",
                role="system",
                timestamp=datetime(2024, 1, 15, 10, 30, 20, tzinfo=UTC),
                parent_id=None,
            ),
        ]

        conversation = Conversation(
            id="conv-123",
            title="Mixed Roles",
            created_at=created,
            messages=messages,
        )

        # Calculate statistics
        stats = calculate_conversation_statistics(conversation)

        # Verify role counts
        assert stats.message_count_by_role.user == 2
        assert stats.message_count_by_role.assistant == 1
        assert stats.message_count_by_role.system == 1
        assert stats.message_count_by_role.total == 4
