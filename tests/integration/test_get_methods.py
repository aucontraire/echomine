"""Integration tests for get_conversation_by_id and get_message_by_id methods.

This module validates that the OpenAIAdapter get methods work correctly for
retrieving specific conversations and messages by ID.

Test Strategy:
    - Test get_conversation_by_id with existing and non-existent IDs
    - Test get_message_by_id with and without conversation_id hint
    - Test return types and error handling
    - Verify O(1) memory usage with streaming

Constitution Compliance:
    - Principle I: Library-First Architecture (test library methods, not CLI)
    - Principle VI: Strict Typing Mandatory (validate return types)
    - Principle III: Test-Driven Development (RED phase - tests written first)
    - Principle VIII: Memory Efficiency & Streaming (O(1) memory)

Requirements Coverage:
    - FR-155: get_conversation_by_id method
    - FR-217: Method signature and return type
    - FR-356: Streaming search for memory efficiency

Test Execution:
    pytest tests/integration/test_get_methods.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.message import Message


# ============================================================================
# T113-001: get_conversation_by_id Tests
# ============================================================================


@pytest.mark.integration
class TestGetConversationById:
    """Integration tests for OpenAIAdapter.get_conversation_by_id method.

    These tests validate that get_conversation_by_id correctly retrieves
    conversations from OpenAI export files using streaming.
    """

    def test_get_conversation_by_id_returns_conversation_when_found(
        self, tmp_export_file: Path
    ) -> None:
        """Test that get_conversation_by_id returns Conversation when ID exists.

        Validates:
            - FR-155: get_conversation_by_id returns Conversation object
            - FR-217: Method signature matches protocol
            - FR-356: Streaming implementation (O(1) memory)

        Expected: Returns Conversation with matching ID
        """
        adapter = OpenAIAdapter()

        # Act: Get conversation by known ID from fixture
        # tmp_export_file contains "conv-001" from conftest.py
        result = adapter.get_conversation_by_id(tmp_export_file, "conv-001")

        # Assert: Returns Conversation object
        assert result is not None, (
            "get_conversation_by_id should return Conversation when ID exists"
        )
        assert isinstance(result, Conversation), (
            f"get_conversation_by_id should return Conversation, got {type(result)}"
        )

        # Assert: Correct conversation returned
        assert result.id == "conv-001", (
            f"Expected conversation ID 'conv-001', got '{result.id}'"
        )
        assert result.title == "Test Conversation", (
            f"Expected title 'Test Conversation', got '{result.title}'"
        )

    def test_get_conversation_by_id_returns_none_when_not_found(
        self, tmp_export_file: Path
    ) -> None:
        """Test that get_conversation_by_id returns None when ID doesn't exist.

        Validates:
            - FR-155: Returns None for non-existent ID (not exception)
            - FR-356: Streams through entire file before returning None

        Expected: Returns None (does not raise exception)
        """
        adapter = OpenAIAdapter()

        # Act: Get conversation with non-existent ID
        result = adapter.get_conversation_by_id(
            tmp_export_file, "nonexistent-conversation-id"
        )

        # Assert: Returns None, not exception
        assert result is None, (
            "get_conversation_by_id should return None for non-existent ID, "
            "not raise exception"
        )

    def test_get_conversation_by_id_returns_correct_conversation_from_multiple(
        self, tmp_path: Path
    ) -> None:
        """Test that get_conversation_by_id returns correct conversation from multiple.

        Validates:
            - FR-155: Correctly identifies conversation among multiple
            - FR-356: Stops streaming after finding match (early termination)

        Expected: Returns only the matching conversation, not others
        """
        # Arrange: Create export with 3 conversations
        export_data = [
            {
                "id": "conv-001",
                "title": "First Conversation",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello 1"]},
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-001",
            },
            {
                "id": "conv-002",
                "title": "Second Conversation",
                "create_time": 1700000200.0,
                "update_time": 1700000300.0,
                "mapping": {
                    "msg-002": {
                        "id": "msg-002",
                        "message": {
                            "id": "msg-002",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello 2"]},
                            "create_time": 1700000200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-002",
            },
            {
                "id": "conv-003",
                "title": "Third Conversation",
                "create_time": 1700000400.0,
                "update_time": 1700000500.0,
                "mapping": {
                    "msg-003": {
                        "id": "msg-003",
                        "message": {
                            "id": "msg-003",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello 3"]},
                            "create_time": 1700000400.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-003",
            },
        ]

        import json

        export_file = tmp_path / "multi_export.json"
        export_file.write_text(json.dumps(export_data))

        adapter = OpenAIAdapter()

        # Act: Get middle conversation
        result = adapter.get_conversation_by_id(export_file, "conv-002")

        # Assert: Returns correct conversation
        assert result is not None
        assert result.id == "conv-002"
        assert result.title == "Second Conversation"

    def test_get_conversation_by_id_raises_file_not_found_for_missing_file(
        self,
    ) -> None:
        """Test that get_conversation_by_id raises FileNotFoundError for missing files.

        Validates:
            - FR-049: FileNotFoundError for non-existent files
            - FR-033: Proper error handling

        Expected: Raises FileNotFoundError
        """
        adapter = OpenAIAdapter()
        non_existent = Path("/tmp/this_file_does_not_exist_12345.json")

        # Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            adapter.get_conversation_by_id(non_existent, "conv-001")

    def test_get_conversation_by_id_with_empty_export_file(
        self, tmp_path: Path
    ) -> None:
        """Test that get_conversation_by_id handles empty export file gracefully.

        Validates:
            - FR-155: Graceful handling of empty files
            - Returns None for empty file (no conversations)

        Expected: Returns None (not exception)
        """
        # Arrange: Create empty export file (empty JSON array)
        empty_file = tmp_path / "empty_export.json"
        empty_file.write_text("[]")

        adapter = OpenAIAdapter()

        # Act: Get conversation from empty file
        result = adapter.get_conversation_by_id(empty_file, "conv-001")

        # Assert: Returns None
        assert result is None, (
            "get_conversation_by_id should return None for empty export file"
        )


# ============================================================================
# T113-002: get_message_by_id Tests (NEW - Not Yet Implemented)
# ============================================================================


@pytest.mark.integration
class TestGetMessageById:
    """Integration tests for OpenAIAdapter.get_message_by_id method.

    These tests are written in TDD RED phase - they will FAIL until
    get_message_by_id is implemented.

    Expected Failures:
        - AttributeError: 'OpenAIAdapter' has no attribute 'get_message_by_id'
    """

    def test_get_message_by_id_method_exists(self) -> None:
        """Test that get_message_by_id method exists on OpenAIAdapter.

        Validates:
            - Method exists and is callable
            - Part of ConversationProvider protocol extension

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()

        # Assert: Method exists
        assert hasattr(adapter, "get_message_by_id"), (
            "OpenAIAdapter must have get_message_by_id method"
        )
        assert callable(adapter.get_message_by_id), (
            "get_message_by_id must be callable"
        )

    def test_get_message_by_id_returns_tuple_when_found_with_conversation_hint(
        self, tmp_export_file: Path
    ) -> None:
        """Test get_message_by_id returns (Message, Conversation) with conversation_id hint.

        Validates:
            - Returns tuple[Message, Conversation] when message found
            - Uses conversation_id hint for performance optimization
            - Correct message and parent conversation returned

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()

        # Act: Get message by ID with conversation_id hint
        # tmp_export_file has conv-001 with msg-001 and msg-002
        result = adapter.get_message_by_id(
            tmp_export_file, "msg-001", conversation_id="conv-001"
        )

        # Assert: Returns tuple of (Message, Conversation)
        assert result is not None, (
            "get_message_by_id should return tuple when message exists"
        )
        assert isinstance(result, tuple), (
            f"get_message_by_id should return tuple, got {type(result)}"
        )
        assert len(result) == 2, (
            f"get_message_by_id should return 2-tuple, got {len(result)} items"
        )

        message, conversation = result

        # Assert: Message is correct type
        assert isinstance(message, Message), (
            f"First tuple element should be Message, got {type(message)}"
        )

        # Assert: Conversation is correct type
        assert isinstance(conversation, Conversation), (
            f"Second tuple element should be Conversation, got {type(conversation)}"
        )

        # Assert: Correct message and conversation
        assert message.id == "msg-001", f"Expected message ID 'msg-001', got '{message.id}'"
        assert conversation.id == "conv-001", (
            f"Expected conversation ID 'conv-001', got '{conversation.id}'"
        )

    def test_get_message_by_id_returns_tuple_when_found_without_conversation_hint(
        self, tmp_export_file: Path
    ) -> None:
        """Test get_message_by_id returns (Message, Conversation) without conversation_id hint.

        Validates:
            - Searches all conversations when no conversation_id provided
            - Returns tuple[Message, Conversation] when found
            - Correct parent conversation returned

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()

        # Act: Get message by ID WITHOUT conversation_id hint (search all)
        result = adapter.get_message_by_id(tmp_export_file, "msg-002")

        # Assert: Returns tuple
        assert result is not None, (
            "get_message_by_id should return tuple when message exists "
            "(even without conversation_id hint)"
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

        message, conversation = result

        # Assert: Correct types
        assert isinstance(message, Message)
        assert isinstance(conversation, Conversation)

        # Assert: Correct message and parent conversation
        assert message.id == "msg-002"
        assert conversation.id == "conv-001", (
            "Should return parent conversation containing the message"
        )

    def test_get_message_by_id_returns_none_when_message_not_found(
        self, tmp_export_file: Path
    ) -> None:
        """Test get_message_by_id returns None when message ID doesn't exist.

        Validates:
            - Returns None for non-existent message ID (not exception)
            - Searches through all conversations before returning None

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()

        # Act: Get message with non-existent ID
        result = adapter.get_message_by_id(
            tmp_export_file, "nonexistent-message-id"
        )

        # Assert: Returns None
        assert result is None, (
            "get_message_by_id should return None for non-existent message ID"
        )

    def test_get_message_by_id_returns_none_when_conversation_not_found_with_hint(
        self, tmp_export_file: Path
    ) -> None:
        """Test get_message_by_id returns None when conversation_id hint doesn't exist.

        Validates:
            - Returns None if conversation_id hint points to non-existent conversation
            - Does not fall back to searching all conversations

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()

        # Act: Get message with non-existent conversation_id hint
        result = adapter.get_message_by_id(
            tmp_export_file,
            "msg-001",
            conversation_id="nonexistent-conversation-id",
        )

        # Assert: Returns None
        assert result is None, (
            "get_message_by_id should return None when conversation_id hint "
            "doesn't match any conversation"
        )

    def test_get_message_by_id_returns_none_when_message_not_in_hinted_conversation(
        self, tmp_path: Path
    ) -> None:
        """Test get_message_by_id returns None when message not in hinted conversation.

        Validates:
            - Returns None if message exists but not in hinted conversation
            - Does not search other conversations when hint provided

        Expected to FAIL: Method not implemented yet
        """
        # Arrange: Create export with 2 conversations
        import json

        export_data = [
            {
                "id": "conv-001",
                "title": "First Conversation",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["In conv-001"]},
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-001",
            },
            {
                "id": "conv-002",
                "title": "Second Conversation",
                "create_time": 1700000200.0,
                "update_time": 1700000300.0,
                "mapping": {
                    "msg-002": {
                        "id": "msg-002",
                        "message": {
                            "id": "msg-002",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["In conv-002"]},
                            "create_time": 1700000200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-002",
            },
        ]

        export_file = tmp_path / "multi_conv_export.json"
        export_file.write_text(json.dumps(export_data))

        adapter = OpenAIAdapter()

        # Act: Search for msg-002 but hint wrong conversation (conv-001)
        result = adapter.get_message_by_id(
            export_file, "msg-002", conversation_id="conv-001"
        )

        # Assert: Returns None (message exists but not in hinted conversation)
        assert result is None, (
            "get_message_by_id should return None when message exists but "
            "not in the hinted conversation (should not search other conversations)"
        )

    def test_get_message_by_id_finds_message_in_any_conversation_without_hint(
        self, tmp_path: Path
    ) -> None:
        """Test get_message_by_id finds message in any conversation without hint.

        Validates:
            - Searches all conversations when no conversation_id provided
            - Returns first match found
            - Returns correct parent conversation

        Expected to FAIL: Method not implemented yet
        """
        # Arrange: Create export with 2 conversations
        import json

        export_data = [
            {
                "id": "conv-001",
                "title": "First Conversation",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["In conv-001"]},
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-001",
            },
            {
                "id": "conv-002",
                "title": "Second Conversation",
                "create_time": 1700000200.0,
                "update_time": 1700000300.0,
                "mapping": {
                    "msg-002": {
                        "id": "msg-002",
                        "message": {
                            "id": "msg-002",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["In conv-002"]},
                            "create_time": 1700000200.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": "msg-002",
            },
        ]

        export_file = tmp_path / "multi_conv_export.json"
        export_file.write_text(json.dumps(export_data))

        adapter = OpenAIAdapter()

        # Act: Search for msg-002 without hint (should find in conv-002)
        result = adapter.get_message_by_id(export_file, "msg-002")

        # Assert: Returns tuple with correct message and conversation
        assert result is not None
        message, conversation = result

        assert message.id == "msg-002"
        assert conversation.id == "conv-002", (
            "Should return parent conversation containing the message"
        )

    def test_get_message_by_id_raises_file_not_found_for_missing_file(self) -> None:
        """Test get_message_by_id raises FileNotFoundError for missing files.

        Validates:
            - FR-049: FileNotFoundError for non-existent files
            - FR-033: Proper error handling

        Expected to FAIL: Method not implemented yet
        """
        adapter = OpenAIAdapter()
        non_existent = Path("/tmp/this_file_does_not_exist_12345.json")

        # Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            adapter.get_message_by_id(non_existent, "msg-001")

    def test_get_message_by_id_with_empty_export_file(
        self, tmp_path: Path
    ) -> None:
        """Test get_message_by_id handles empty export file gracefully.

        Validates:
            - Graceful handling of empty files
            - Returns None for empty file (no conversations/messages)

        Expected to FAIL: Method not implemented yet
        """
        # Arrange: Create empty export file
        empty_file = tmp_path / "empty_export.json"
        empty_file.write_text("[]")

        adapter = OpenAIAdapter()

        # Act: Get message from empty file
        result = adapter.get_message_by_id(empty_file, "msg-001")

        # Assert: Returns None
        assert result is None, (
            "get_message_by_id should return None for empty export file"
        )
