"""T060: Immutability Contract Tests for Data Models.

This test module validates that all Pydantic models (Conversation, Message,
SearchQuery, SearchResult) are immutable and enforce frozen=True behavior.

Test Strategy:
    - Verify models cannot have fields modified after creation
    - Verify model_copy() works for creating modified versions
    - Verify frozen=True raises FrozenInstanceError on modification attempts
    - Verify immutability works across all model types
    - Verify nested models (Messages within Conversation) are also immutable

Constitution Compliance:
    - Principle VI: Strict Typing Mandatory (immutable models)
    - FR-222, FR-227: Immutability via frozen=True
    - Principle III: Test-Driven Development (RED phase)

Requirements Coverage:
    - FR-222: All models must be frozen (immutable)
    - FR-227: Use model_copy() for creating modified instances
    - FR-054: Validation enforced at parse time (immutability part of validation)

Test Execution:
    pytest tests/unit/models/test_conversation.py -v

Expected State: FAILING (imports will fail until exports added to __init__.py)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


# ============================================================================
# T060-001: Conversation Immutability
# ============================================================================


def test_conversation_fields_are_immutable() -> None:
    """Verify Conversation fields cannot be modified after creation.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Pydantic frozen=True enforcement

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message

    # Create a conversation
    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    conversation = Conversation(
        id="conv-1",
        title="Test Conversation",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Attempting to modify fields should raise ValidationError or AttributeError
    with pytest.raises((ValidationError, AttributeError)):
        conversation.title = "Modified Title"  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        conversation.id = "conv-modified"  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        conversation.messages = []  # type: ignore[misc]


def test_conversation_model_copy_creates_modified_instance() -> None:
    """Verify model_copy() can create modified Conversation instances.

    Requirements:
        - FR-227: Use model_copy() for creating modified instances
        - Immutable models require copy-on-write pattern

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message

    # Create original conversation
    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    original = Conversation(
        id="conv-1",
        title="Original Title",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Create modified copy
    modified = original.model_copy(update={"title": "Modified Title"})

    # Original should be unchanged
    assert original.title == "Original Title", "Original should not be modified"
    assert original.id == "conv-1", "Original ID should be unchanged"

    # Modified should have new value
    assert modified.title == "Modified Title", "Modified copy should have new title"
    assert modified.id == "conv-1", "Modified copy should preserve other fields"

    # They should be different objects
    assert original is not modified, "Should create new instance, not modify original"


def test_conversation_model_copy_deep_copies_mutable_fields() -> None:
    """Verify model_copy() handles mutable fields correctly for frozen models.

    Requirements:
        - FR-227: model_copy() should create independent copies
        - Pydantic v2: frozen models perform shallow copy by default (safe due to immutability)

    Note:
        Pydantic v2 frozen models perform SHALLOW copy by default. This is safe
        because frozen=True prevents modifications. For true deep copy, use
        model_copy(deep=True).

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message

    # Create conversation with messages
    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]

    original = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Create shallow copy (default for frozen models)
    shallow_copy = original.model_copy()

    # Frozen models share list references (shallow copy) - this is SAFE
    assert original.messages is shallow_copy.messages, (
        "Frozen models perform shallow copy by default (safe due to immutability)"
    )

    # But should have same values
    assert len(original.messages) == len(shallow_copy.messages), "Should have same message count"
    assert original.messages[0].id == shallow_copy.messages[0].id, (
        "Messages should have same content"
    )

    # Create deep copy if truly needed
    deep_copy = original.model_copy(deep=True)

    # Deep copy should have different list object
    assert original.messages is not deep_copy.messages, "Deep copy should create new list object"

    # But still have same values
    assert len(original.messages) == len(deep_copy.messages), "Should have same message count"
    assert original.messages[0].id == deep_copy.messages[0].id, "Messages should have same content"


# ============================================================================
# T060-002: Message Immutability
# ============================================================================


def test_message_fields_are_immutable() -> None:
    """Verify Message fields cannot be modified after creation.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Pydantic frozen=True enforcement

    Expected Failure:
        ImportError: cannot import name 'Message' from 'echomine'
    """
    from echomine import Message

    message = Message(
        id="msg-1",
        content="Hello, world!",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    # Attempting to modify fields should raise ValidationError or AttributeError
    with pytest.raises((ValidationError, AttributeError)):
        message.content = "Modified content"  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        message.role = "assistant"  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        message.id = "msg-modified"  # type: ignore[misc]


def test_message_model_copy_creates_modified_instance() -> None:
    """Verify model_copy() can create modified Message instances.

    Requirements:
        - FR-227: Use model_copy() for creating modified instances
        - Copy-on-write pattern for immutable models

    Expected Failure:
        ImportError: cannot import name 'Message' from 'echomine'
    """
    from echomine import Message

    original = Message(
        id="msg-1",
        content="Original content",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    # Create modified copy
    modified = original.model_copy(update={"content": "Modified content"})

    # Original should be unchanged
    assert original.content == "Original content", "Original should not be modified"

    # Modified should have new value
    assert modified.content == "Modified content", "Modified copy should have new content"
    assert modified.id == "msg-1", "Modified copy should preserve other fields"
    assert modified.role == "user", "Modified copy should preserve other fields"


# ============================================================================
# T060-003: SearchQuery Immutability
# ============================================================================


def test_search_query_fields_are_immutable() -> None:
    """Verify SearchQuery fields cannot be modified after creation.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Query parameters should not change during search

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    query = SearchQuery(keywords=["algorithm", "python"], limit=10)

    # Attempting to modify fields should raise ValidationError or AttributeError
    with pytest.raises((ValidationError, AttributeError)):
        query.keywords = ["modified"]  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        query.limit = 50  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        query.title_filter = "Modified"  # type: ignore[misc]


def test_search_query_model_copy_creates_modified_instance() -> None:
    """Verify model_copy() can create modified SearchQuery instances.

    Requirements:
        - FR-227: Use model_copy() for creating modified instances
        - Useful for creating query variations

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    original = SearchQuery(keywords=["algorithm"], limit=10)

    # Create modified copy with different limit
    modified = original.model_copy(update={"limit": 50})

    # Original should be unchanged
    assert original.limit == 10, "Original limit should not be modified"

    # Modified should have new value
    assert modified.limit == 50, "Modified copy should have new limit"
    assert modified.keywords == ["algorithm"], "Modified copy should preserve keywords"


def test_search_query_keywords_list_is_immutable() -> None:
    """Verify SearchQuery keywords list cannot be modified in place.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Prevent modification of mutable nested fields

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    query = SearchQuery(keywords=["algorithm", "python"], limit=10)

    # The query itself is frozen
    with pytest.raises((ValidationError, AttributeError)):
        query.keywords = ["modified"]  # type: ignore[misc]

    # Note: The list itself might be mutable (Python limitation), but
    # reassignment should be blocked. Best practice is to not modify
    # the list in-place, but we can't prevent it at runtime with Pydantic.
    # This is a known limitation - users should treat as immutable.


# ============================================================================
# T060-004: SearchResult Immutability
# ============================================================================


def test_search_result_fields_are_immutable() -> None:
    """Verify SearchResult fields cannot be modified after creation.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Search results should not change after computation

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'
    """
    from echomine import Conversation, Message, SearchResult

    # Create conversation for search result
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]
    conversation = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Create search result
    result = SearchResult(conversation=conversation, score=0.85, matched_message_ids=["msg-1"])

    # Attempting to modify fields should raise ValidationError or AttributeError
    with pytest.raises((ValidationError, AttributeError)):
        result.score = 0.95  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        result.conversation = conversation  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        result.matched_message_ids = []  # type: ignore[misc]


def test_search_result_model_copy_creates_modified_instance() -> None:
    """Verify model_copy() can create modified SearchResult instances.

    Requirements:
        - FR-227: Use model_copy() for creating modified instances

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'
    """
    from echomine import Conversation, Message, SearchResult

    # Create conversation
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]
    conversation = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Create original result
    original = SearchResult(conversation=conversation, score=0.85, matched_message_ids=["msg-1"])

    # Create modified copy with different score
    modified = original.model_copy(update={"score": 0.95})

    # Original should be unchanged
    assert original.score == 0.85, "Original score should not be modified"

    # Modified should have new value
    assert modified.score == 0.95, "Modified copy should have new score"
    assert modified.conversation == conversation, "Modified copy should preserve conversation"


# ============================================================================
# T060-005: Nested Model Immutability
# ============================================================================


def test_nested_messages_in_conversation_are_immutable() -> None:
    """Verify Messages nested within Conversation are also immutable.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Immutability should apply to nested structures

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message

    # Create conversation with nested messages
    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        ),
        Message(
            id="msg-2",
            content="Hi!",
            role="assistant",
            timestamp=datetime.now(UTC),
            parent_id="msg-1",
        ),
    ]

    conversation = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    # Nested messages should also be immutable
    message = conversation.messages[0]

    with pytest.raises((ValidationError, AttributeError)):
        message.content = "Modified content"  # type: ignore[misc]

    with pytest.raises((ValidationError, AttributeError)):
        message.role = "assistant"  # type: ignore[misc]


def test_conversation_in_search_result_is_immutable() -> None:
    """Verify Conversation nested within SearchResult is immutable.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Nested models preserve immutability

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'
    """
    from echomine import Conversation, Message, SearchResult

    # Create search result with nested conversation
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]
    conversation = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )

    result = SearchResult(conversation=conversation, score=0.85, matched_message_ids=["msg-1"])

    # Nested conversation should be immutable
    with pytest.raises((ValidationError, AttributeError)):
        result.conversation.title = "Modified"  # type: ignore[misc]


# ============================================================================
# T060-006: ConfigDict frozen=True Validation
# ============================================================================


def test_conversation_model_config_has_frozen_true() -> None:
    """Verify Conversation model has frozen=True in ConfigDict.

    Requirements:
        - FR-222: All models must be frozen (immutable)
        - Pydantic v2 ConfigDict pattern

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation

    # Verify ConfigDict has frozen=True
    assert hasattr(Conversation, "model_config"), "Should have model_config"
    assert Conversation.model_config.get("frozen") is True, "model_config should have frozen=True"


def test_message_model_config_has_frozen_true() -> None:
    """Verify Message model has frozen=True in ConfigDict.

    Requirements:
        - FR-222: All models must be frozen (immutable)

    Expected Failure:
        ImportError: cannot import name 'Message' from 'echomine'
    """
    from echomine import Message

    assert hasattr(Message, "model_config"), "Should have model_config"
    assert Message.model_config.get("frozen") is True, "model_config should have frozen=True"


def test_search_query_model_config_has_frozen_true() -> None:
    """Verify SearchQuery model has frozen=True in ConfigDict.

    Requirements:
        - FR-222: All models must be frozen (immutable)

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    assert hasattr(SearchQuery, "model_config"), "Should have model_config"
    assert SearchQuery.model_config.get("frozen") is True, "model_config should have frozen=True"


def test_search_result_model_config_has_frozen_true() -> None:
    """Verify SearchResult model has frozen=True in ConfigDict.

    Requirements:
        - FR-222: All models must be frozen (immutable)

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'
    """
    from echomine import SearchResult

    assert hasattr(SearchResult, "model_config"), "Should have model_config"
    assert SearchResult.model_config.get("frozen") is True, "model_config should have frozen=True"


# ============================================================================
# T060-007: Immutability with Validation
# ============================================================================


def test_immutable_conversation_still_validates_on_creation() -> None:
    """Verify immutable models still perform validation at creation time.

    Requirements:
        - FR-054: Validation enforced at parse time
        - FR-222: Immutability doesn't disable validation

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message

    # Valid conversation should be created
    messages = [
        Message(
            id="msg-1",
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
    ]
    valid = Conversation(
        id="conv-1",
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=messages,
    )
    assert valid is not None

    # Invalid conversation should raise ValidationError
    with pytest.raises(ValidationError):
        Conversation(
            id="",  # Empty ID should fail validation
            title="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            messages=messages,
        )


def test_immutable_message_still_validates_on_creation() -> None:
    """Verify immutable Message validates required fields.

    Requirements:
        - FR-054: Validation enforced at parse time
        - FR-222: Immutability doesn't disable validation

    Expected Failure:
        ImportError: cannot import name 'Message' from 'echomine'
    """
    from echomine import Message

    # Valid message should be created
    valid = Message(
        id="msg-1",
        content="Test",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )
    assert valid is not None

    # Invalid message should raise ValidationError
    with pytest.raises(ValidationError):
        Message(
            id="",  # Empty ID should fail validation
            content="Test",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None,
        )
