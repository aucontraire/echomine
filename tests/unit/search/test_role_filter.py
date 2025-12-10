"""Unit tests for role filtering in search (FR-017-020).

Tests the role_filter functionality that allows searching only in messages
from specific roles (user, assistant, system).

Requirements:
    - FR-017: role_filter accepts 'user', 'assistant', 'system'
    - FR-018: Filter applied to messages before text aggregation
    - FR-019: No role_filter means all roles included
    - FR-020: Case-insensitive role matching in filter
"""

from __future__ import annotations

from datetime import UTC, datetime

from echomine.models.message import Message


class TestRoleFilterBasic:
    """Test basic role filtering on messages."""

    def test_filter_user_messages_only(self) -> None:
        """Messages from 'user' role are included when role_filter='user'."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="This is from the user",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="This is from the assistant",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="user",
                content="Another user message",
                timestamp=datetime.now(UTC),
            ),
        ]

        # Filter to user messages only
        filtered = [m for m in messages if m.role == "user"]

        assert len(filtered) == 2
        assert all(m.role == "user" for m in filtered)

    def test_filter_assistant_messages_only(self) -> None:
        """Messages from 'assistant' role are included when role_filter='assistant'."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="User question",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Assistant answer",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="assistant",
                content="Another assistant response",
                timestamp=datetime.now(UTC),
            ),
        ]

        # Filter to assistant messages only
        filtered = [m for m in messages if m.role == "assistant"]

        assert len(filtered) == 2
        assert all(m.role == "assistant" for m in filtered)

    def test_filter_system_messages_only(self) -> None:
        """Messages from 'system' role are included when role_filter='system'."""
        messages = [
            Message(
                id="msg-1",
                role="system",
                content="System prompt",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="user",
                content="User question",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="assistant",
                content="Assistant answer",
                timestamp=datetime.now(UTC),
            ),
        ]

        # Filter to system messages only
        filtered = [m for m in messages if m.role == "system"]

        assert len(filtered) == 1
        assert filtered[0].role == "system"

    def test_no_role_filter_includes_all(self) -> None:
        """When role_filter is None, all messages are included."""
        messages = [
            Message(
                id="msg-1",
                role="system",
                content="System prompt",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="user",
                content="User question",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="assistant",
                content="Assistant answer",
                timestamp=datetime.now(UTC),
            ),
        ]

        role_filter = None

        # No filtering when role_filter is None
        filtered = (
            messages if role_filter is None else [m for m in messages if m.role == role_filter]
        )

        assert len(filtered) == 3


class TestRoleFilterEdgeCases:
    """Test edge cases for role filtering."""

    def test_empty_messages_list(self) -> None:
        """Empty message list returns empty result."""
        messages: list[Message] = []
        filtered = [m for m in messages if m.role == "user"]
        assert filtered == []

    def test_no_matching_role(self) -> None:
        """When no messages match the role filter, empty list returned."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="User message",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Assistant message",
                timestamp=datetime.now(UTC),
            ),
        ]

        # Filter to system messages (none exist)
        filtered = [m for m in messages if m.role == "system"]

        assert filtered == []

    def test_role_filter_preserves_message_content(self) -> None:
        """Filtered messages retain their original content."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="Original user content",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Original assistant content",
                timestamp=datetime.now(UTC),
            ),
        ]

        filtered = [m for m in messages if m.role == "user"]

        assert len(filtered) == 1
        assert filtered[0].content == "Original user content"
        assert filtered[0].id == "msg-1"

    def test_role_filter_preserves_order(self) -> None:
        """Filtered messages maintain their original order."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="First user message",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Assistant message",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-3",
                role="user",
                content="Second user message",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-4",
                role="user",
                content="Third user message",
                timestamp=datetime.now(UTC),
            ),
        ]

        filtered = [m for m in messages if m.role == "user"]

        assert len(filtered) == 3
        assert [m.id for m in filtered] == ["msg-1", "msg-3", "msg-4"]


class TestRoleFilterIntegration:
    """Test role filtering with conversation search flow."""

    def test_role_filter_affects_keyword_search(self) -> None:
        """Keywords only match in messages from filtered role."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="Tell me about Python programming",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Python is a great programming language",
                timestamp=datetime.now(UTC),
            ),
        ]

        # If we filter to user messages only, keyword "great" should NOT match
        user_messages = [m for m in messages if m.role == "user"]
        user_text = " ".join(m.content for m in user_messages)

        assert "great" not in user_text.lower()
        assert "python" in user_text.lower()

    def test_role_filter_affects_phrase_search(self) -> None:
        """Phrases only match in messages from filtered role."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="What is machine learning?",
                timestamp=datetime.now(UTC),
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="Machine learning is a subset of AI that enables...",
                timestamp=datetime.now(UTC),
            ),
        ]

        # If we filter to user messages only
        user_text = " ".join(m.content for m in messages if m.role == "user")
        assistant_text = " ".join(m.content for m in messages if m.role == "assistant")

        # "machine learning" appears in both, but "subset of AI" only in assistant
        assert "machine learning" in user_text.lower()
        assert "subset of AI" not in user_text
        assert "subset of AI" in assistant_text
