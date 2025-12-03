"""T092-T094: Validation Edge Cases for Error Handling.

This test module validates graceful degradation for malformed data:
- T092: Empty conversations (zero messages)
- T093: Missing required fields (id, title, created_at)
- T094: Deleted messages (empty content)

Test Strategy:
    - Verify Pydantic validation enforces constraints
    - Verify adapter skips malformed entries with WARNING log
    - Verify proper error context in logs
    - Verify graceful degradation continues processing

Constitution Compliance:
    - Principle IV: Observability (WARNING logs with context)
    - Principle VI: Strict Typing (Pydantic validation)
    - FR-281-285: Graceful degradation for malformed entries

Requirements Coverage:
    - FR-379: Skip conversations missing required fields
    - FR-380: Skip conversations with empty id or title
    - FR-381: Skip conversations with zero messages
    - FR-384-388: Handle empty content messages (deleted messages)

Test Execution:
    pytest tests/unit/test_validation_edge_cases.py -v
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from echomine import Conversation, Message
from echomine.adapters.openai import OpenAIAdapter


# ============================================================================
# T092: Empty Conversations (Zero Messages)
# ============================================================================


def test_conversation_model_rejects_empty_messages_list() -> None:
    """Verify Conversation model enforces min_length=1 for messages field.

    Requirements:
        - FR-381: Library MUST skip conversations with zero messages
        - Pydantic Field validation with min_length=1

    Expected Behavior:
        - ValidationError raised when messages list is empty
        - Error message indicates constraint violation
    """
    # Attempt to create conversation with empty messages list
    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            id="conv-001",
            title="Empty Conversation",
            created_at=datetime.now(UTC),
            updated_at=None,
            messages=[],  # Empty list - should fail validation
        )

    # Verify error message indicates min_length constraint
    error_str = str(exc_info.value)
    assert "min_length" in error_str.lower() or "at least 1" in error_str.lower()


def test_adapter_skips_conversation_with_zero_messages(caplog: pytest.LogCaptureFixture) -> None:
    """Verify adapter skips conversations with zero messages and logs WARNING.

    Requirements:
        - FR-381: Skip conversations with zero messages
        - FR-281: Graceful degradation with warning logs

    Expected Behavior:
        - Conversation with zero messages is skipped
        - WARNING log emitted with conversation_id and reason
        - Processing continues (no exception raised)
    """
    # Create export with one valid conversation and one with zero messages
    export_data = [
        {
            "id": "conv-valid",
            "title": "Valid Conversation",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello"]},
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
        {
            "id": "conv-empty-messages",
            "title": "Empty Conversation",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {},  # No messages - should be skipped
        },
    ]

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(temp_path))

        # Should yield only the valid conversation
        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"

        # Verify WARNING log emitted for skipped conversation
        assert any(
            "Skipped malformed" in record.message
            and hasattr(record, "conversation_id")
            and record.conversation_id == "conv-empty-messages"
            for record in caplog.records
        ), "Expected WARNING log with conversation_id context"

    finally:
        temp_path.unlink()


# ============================================================================
# T093: Missing Required Fields
# ============================================================================


def test_conversation_model_requires_id_field() -> None:
    """Verify Conversation model enforces required id field.

    Requirements:
        - FR-379: Skip conversations missing required fields
        - Pydantic required field validation
    """
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            # id missing - should fail
            title="Test",
            created_at=datetime.now(UTC),
            updated_at=None,
            messages=messages,
        )  # type: ignore[call-arg]

    error_str = str(exc_info.value)
    assert "id" in error_str.lower()


def test_conversation_model_requires_title_field() -> None:
    """Verify Conversation model enforces required title field.

    Requirements:
        - FR-379: Skip conversations missing required fields
    """
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            id="conv-001",
            # title missing - should fail
            created_at=datetime.now(UTC),
            updated_at=None,
            messages=messages,
        )  # type: ignore[call-arg]

    error_str = str(exc_info.value)
    assert "title" in error_str.lower()


def test_conversation_model_requires_created_at_field() -> None:
    """Verify Conversation model enforces required created_at field.

    Requirements:
        - FR-379: Skip conversations missing required fields
    """
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            id="conv-001",
            title="Test",
            # created_at missing - should fail
            updated_at=None,
            messages=messages,
        )  # type: ignore[call-arg]

    error_str = str(exc_info.value)
    assert "created_at" in error_str.lower()


def test_conversation_model_rejects_empty_id() -> None:
    """Verify Conversation model enforces min_length=1 for id field.

    Requirements:
        - FR-380: Skip conversations with empty id (empty string)
        - Pydantic min_length validation
    """
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            id="",  # Empty string - should fail min_length=1
            title="Test",
            created_at=datetime.now(UTC),
            updated_at=None,
            messages=messages,
        )

    error_str = str(exc_info.value)
    assert "min_length" in error_str.lower() or "at least 1" in error_str.lower()


def test_conversation_model_rejects_empty_title() -> None:
    """Verify Conversation model enforces min_length=1 for title field.

    Requirements:
        - FR-380: Skip conversations with empty title (empty string)
    """
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        Conversation(
            id="conv-001",
            title="",  # Empty string - should fail min_length=1
            created_at=datetime.now(UTC),
            updated_at=None,
            messages=messages,
        )

    error_str = str(exc_info.value)
    assert "min_length" in error_str.lower() or "at least 1" in error_str.lower()


def test_adapter_skips_conversation_missing_id(caplog: pytest.LogCaptureFixture) -> None:
    """Verify adapter skips conversations with missing id field.

    Requirements:
        - FR-379: Skip conversations missing required fields (id)
        - FR-281: Graceful degradation with warning logs
    """
    export_data = [
        {
            "id": "conv-valid",
            "title": "Valid Conversation",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello"]},
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
        {
            # Missing "id" field
            "title": "Missing ID",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Test"]},
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(temp_path))

        # Should yield only the valid conversation
        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"

        # Verify WARNING log emitted
        assert any("Skipped malformed" in record.message for record in caplog.records), (
            "Expected WARNING log for skipped conversation"
        )

    finally:
        temp_path.unlink()


def test_adapter_skips_conversation_missing_title(caplog: pytest.LogCaptureFixture) -> None:
    """Verify adapter skips conversations with missing title field.

    Requirements:
        - FR-379: Skip conversations missing required fields (title)
    """
    export_data = [
        {
            "id": "conv-no-title",
            # Missing "title" field
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Test"]},
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(temp_path))

        # Should yield zero conversations
        assert len(conversations) == 0

        # Verify WARNING log emitted
        assert any("Skipped malformed" in record.message for record in caplog.records)

    finally:
        temp_path.unlink()


# ============================================================================
# T094: Deleted Messages (Empty Content)
# ============================================================================


def test_message_model_accepts_empty_content() -> None:
    """Verify Message model accepts empty string for content field.

    Requirements:
        - FR-384: Message content field MUST accept empty strings
        - FR-388: Empty content messages preserved for tree structure

    Expected Behavior:
        - Empty string content is valid (represents deleted message)
        - No validation error raised
    """
    # Create message with empty content - should succeed
    message = Message(
        id="msg-deleted",
        content="",  # Empty string - represents deleted message
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    assert message.content == ""
    assert message.id == "msg-deleted"


def test_message_model_preserves_whitespace_in_content() -> None:
    """Verify Message model does NOT trim or normalize content.

    Requirements:
        - FR-385: Library MUST NOT trim or normalize message content
    """
    # Create message with whitespace content
    whitespace_content = "  \n\t  Hello  \n  "
    message = Message(
        id="msg-whitespace",
        content=whitespace_content,
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    # Content should be preserved exactly as-is
    assert message.content == whitespace_content


def test_adapter_parses_deleted_messages_with_empty_content() -> None:
    """Verify adapter successfully parses messages with empty content.

    Requirements:
        - FR-384: Accept empty content strings
        - FR-388: Include empty content messages in conversation
    """
    export_data = [
        {
            "id": "conv-001",
            "title": "Conversation with Deleted Message",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [""]},  # Empty content
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": ["msg-002"],
                },
                "msg-002": {
                    "id": "msg-002",
                    "message": {
                        "id": "msg-002",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Response"]},
                        "create_time": 1700000010.0,
                    },
                    "parent": "msg-001",
                    "children": [],
                },
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(temp_path))

        assert len(conversations) == 1
        conversation = conversations[0]

        # Should have 2 messages (including empty content one)
        assert conversation.message_count == 2

        # First message should have empty content
        assert conversation.messages[0].content == ""
        assert conversation.messages[0].id == "msg-001"

        # Second message should have normal content
        assert conversation.messages[1].content == "Response"
        assert conversation.messages[1].id == "msg-002"

    finally:
        temp_path.unlink()


def test_adapter_handles_deleted_messages_with_empty_parts_array() -> None:
    """Verify adapter handles OpenAI export with empty parts array.

    Requirements:
        - FR-384: Handle deleted messages (empty parts array)
    """
    export_data = [
        {
            "id": "conv-001",
            "title": "Conversation",
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": []},  # Empty array
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(temp_path))

        assert len(conversations) == 1
        # Message should have empty content string
        assert conversations[0].messages[0].content == ""

    finally:
        temp_path.unlink()


def test_search_skips_empty_content_messages() -> None:
    """Verify empty content messages don't match keyword searches.

    Requirements:
        - FR-387: Empty content messages MUST NOT match keyword searches
        - FR-388: But are still included in conversation
    """
    from echomine.models.search import SearchQuery

    export_data = [
        {
            "id": "conv-001",
            "title": "Empty Message Conversation",  # Non-matching title (keyword is "test")
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [""]},  # Empty
                        "create_time": 1700000000.0,
                    },
                    "parent": None,
                    "children": [],
                },
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"])

        results = list(adapter.search(temp_path, query))

        # Should find no matches (empty content cannot match keywords)
        assert len(results) == 0

    finally:
        temp_path.unlink()


# ============================================================================
# Logging Context Validation
# ============================================================================


def test_warning_logs_include_conversation_id_context(caplog: pytest.LogCaptureFixture) -> None:
    """Verify WARNING logs include conversation_id for traceability.

    Requirements:
        - FR-281: Graceful degradation with contextual logging
        - Principle IV: Observability and debuggability
    """
    export_data = [
        {
            "id": "conv-malformed-123",
            "title": "",  # Empty title - will be skipped
            "create_time": 1700000000.0,
            "update_time": 1700000100.0,
            "mapping": {},
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(export_data, f)
        temp_path = Path(f.name)

    try:
        adapter = OpenAIAdapter()
        list(adapter.stream_conversations(temp_path))

        # Find warning log record
        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_logs) > 0, "Expected at least one WARNING log"

        # Verify conversation_id in log context (stored in extra dict)
        assert hasattr(warning_logs[0], "conversation_id"), (
            "Log should have conversation_id in extra"
        )
        assert warning_logs[0].conversation_id == "conv-malformed-123", (
            "conversation_id should match skipped conversation"
        )

    finally:
        temp_path.unlink()
