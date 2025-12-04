"""Integration tests for role-filtered search (FR-017-020).

Tests the end-to-end role filtering functionality through the OpenAIAdapter.

Requirements:
    - FR-017: role_filter accepts 'user', 'assistant', 'system'
    - FR-018: Filter applied to messages before text aggregation
    - FR-019: No role_filter means all roles included
    - FR-020: Case-insensitive role matching
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


def create_test_export(conversations: list[dict[str, object]]) -> Path:
    """Create a temporary export file with the given conversations."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(conversations, tmp)
    tmp.close()
    return Path(tmp.name)


def make_conversation(
    id: str,
    title: str,
    messages: list[dict[str, str]],
) -> dict[str, object]:
    """Create a conversation dict with the given messages."""
    now = datetime.now(UTC).timestamp()
    mapping: dict[str, dict[str, object]] = {}

    for i, msg in enumerate(messages):
        msg_id = f"{id}-msg-{i}"
        mapping[msg_id] = {
            "id": msg_id,
            "message": {
                "id": msg_id,
                "author": {"role": msg["role"]},
                "content": {"parts": [msg["content"]]},
                "create_time": now + i,
            },
        }

    return {
        "id": id,
        "title": title,
        "create_time": now,
        "update_time": now,
        "mapping": mapping,
    }


class TestRoleFilterAcceptance:
    """Acceptance tests for role filtering feature."""

    def test_us4_as1_filter_to_user_messages(self) -> None:
        """US4-AS1: Search finds keywords only in user messages."""
        # Conversation with keyword "algorithm" in both user and assistant
        conversations = [
            make_conversation(
                id="conv-1",
                title="Algorithm Discussion",
                messages=[
                    {"role": "user", "content": "Tell me about sorting algorithms"},
                    {"role": "assistant", "content": "Sorting algorithms are fundamental..."},
                ],
            ),
            make_conversation(
                id="conv-2",
                title="General Chat",
                messages=[
                    {"role": "user", "content": "How are you today?"},
                    {"role": "assistant", "content": "I'll explain some algorithms to help"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search for "algorithms" in USER messages only
        query = SearchQuery(
            keywords=["algorithms"],
            role_filter="user",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # Only conv-1 should match (user said "algorithms")
        # conv-2 assistant mentioned "algorithms" but user didn't
        assert len(results) == 1
        assert results[0].conversation.id == "conv-1"

        export_path.unlink()

    def test_us4_as2_filter_to_assistant_messages(self) -> None:
        """US4-AS2: Search finds keywords only in assistant messages."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="Python Help",
                messages=[
                    {"role": "user", "content": "What is Python?"},
                    {"role": "assistant", "content": "Python is a programming language"},
                ],
            ),
            make_conversation(
                id="conv-2",
                title="User Mentions Python",
                messages=[
                    {"role": "user", "content": "I love using Python for data science"},
                    {"role": "assistant", "content": "That's great! It's very popular."},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search for "Python" in ASSISTANT messages only
        query = SearchQuery(
            keywords=["python"],
            role_filter="assistant",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # Only conv-1 should match (assistant said "Python")
        # conv-2 user mentioned "Python" but assistant didn't
        assert len(results) == 1
        assert results[0].conversation.id == "conv-1"

        export_path.unlink()

    def test_us4_as3_no_role_filter_includes_all(self) -> None:
        """US4-AS3: Without role filter, all messages are searched."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="Machine Learning",
                messages=[
                    {"role": "user", "content": "Explain neural networks"},
                    {"role": "assistant", "content": "Neural networks are..."},
                ],
            ),
            make_conversation(
                id="conv-2",
                title="Also ML",
                messages=[
                    {"role": "user", "content": "What is deep learning?"},
                    {"role": "assistant", "content": "Deep learning uses neural networks"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search for "neural networks" without role filter
        query = SearchQuery(
            keywords=["neural", "networks"],
            # role_filter is None (default)
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # Both conversations should match
        assert len(results) == 2

        export_path.unlink()


class TestRoleFilterEdgeCases:
    """Edge case tests for role filtering."""

    def test_role_filter_no_matching_messages(self) -> None:
        """When role has no matching messages, conversation is excluded."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="No System Messages",
                messages=[
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search in system messages only (none exist)
        query = SearchQuery(
            keywords=["hello"],
            role_filter="system",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # No results since no system messages exist
        assert len(results) == 0

        export_path.unlink()

    def test_role_filter_with_phrases(self) -> None:
        """Role filter works with phrase search."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="Test",
                messages=[
                    {"role": "user", "content": "What about machine learning?"},
                    {"role": "assistant", "content": "machine learning is a branch of AI"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search phrase "machine learning" in user messages only
        query = SearchQuery(
            phrases=["machine learning"],
            role_filter="user",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # Should match (user said "machine learning")
        assert len(results) == 1

        export_path.unlink()

    def test_role_filter_with_exclude(self) -> None:
        """Role filter works with exclude keywords."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="Python Discussion",
                messages=[
                    {"role": "user", "content": "Tell me about Python and Django"},
                    {"role": "assistant", "content": "Python is great"},
                ],
            ),
            make_conversation(
                id="conv-2",
                title="Just Python",
                messages=[
                    {"role": "user", "content": "I love Python programming"},
                    {"role": "assistant", "content": "Python with Django is powerful"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search "python" in user messages, excluding "django"
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["django"],
            role_filter="user",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # conv-1 user said "Django" so excluded
        # conv-2 user didn't say "Django" (assistant did) so included
        assert len(results) == 1
        assert results[0].conversation.id == "conv-2"

        export_path.unlink()

    def test_role_filter_with_match_mode_all(self) -> None:
        """Role filter works with match_mode='all'."""
        conversations = [
            make_conversation(
                id="conv-1",
                title="Full Match",
                messages=[
                    {"role": "user", "content": "I use Python and JavaScript daily"},
                    {"role": "assistant", "content": "Both are great languages"},
                ],
            ),
            make_conversation(
                id="conv-2",
                title="Partial Match",
                messages=[
                    {"role": "user", "content": "I love Python"},
                    {"role": "assistant", "content": "JavaScript is also popular"},
                ],
            ),
        ]
        export_path = create_test_export(conversations)

        adapter = OpenAIAdapter()

        # Search for both "python" AND "javascript" in user messages only
        query = SearchQuery(
            keywords=["python", "javascript"],
            match_mode="all",
            role_filter="user",
            limit=10,
        )
        results = list(adapter.search(export_path, query))

        # Only conv-1 should match (user mentioned both)
        # conv-2 user only mentioned "Python" (assistant mentioned JavaScript)
        assert len(results) == 1
        assert results[0].conversation.id == "conv-1"

        export_path.unlink()
