"""Example demonstrating timestamp handling in Conversation model.

This example shows how the Conversation model handles optional updated_at
timestamps with semantic correctness.

Design Decisions:
- created_at: REQUIRED (every conversation must have creation time)
- updated_at: OPTIONAL (None means "never modified")
- updated_at_or_created: Computed property for guaranteed non-null access

Key Principles:
1. Never invent false data (no Unix epoch for missing timestamps)
2. Semantic accuracy (None = never updated, not unknown)
3. Type safety (mypy --strict compliant)
4. Backward compatibility (JSON output always includes both timestamps)
"""

from datetime import UTC, datetime, timedelta

from echomine.models.conversation import Conversation
from echomine.models.message import Message


def example_conversation_never_updated() -> None:
    """Example: Conversation created but never updated."""
    print("\n=== Example 1: Conversation Never Updated ===")

    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)

    msg = Message(
        id="msg-1",
        content="Hello world",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    # updated_at is None (never updated)
    conv = Conversation(
        id="conv-001",
        title="Test Conversation",
        created_at=created,
        updated_at=None,  # Explicitly None
        messages=[msg],
    )

    print(f"Created: {conv.created_at}")
    print(f"Updated: {conv.updated_at}")  # None
    print(f"Updated (with fallback): {conv.updated_at_or_created}")  # Falls back to created_at

    # For JSON output, use updated_at_or_created
    assert conv.updated_at_or_created == created
    print("✓ Fallback works correctly")


def example_conversation_with_updates() -> None:
    """Example: Conversation updated after creation."""
    print("\n=== Example 2: Conversation With Updates ===")

    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)
    updated = created + timedelta(hours=2)

    msg = Message(
        id="msg-1",
        content="Hello world",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    # updated_at is set (conversation was modified)
    conv = Conversation(
        id="conv-002",
        title="Updated Conversation",
        created_at=created,
        updated_at=updated,
        messages=[msg],
    )

    print(f"Created: {conv.created_at}")
    print(f"Updated: {conv.updated_at}")
    print(f"Updated (with fallback): {conv.updated_at_or_created}")

    assert conv.updated_at == updated
    assert conv.updated_at_or_created == updated
    print("✓ Updated timestamp preserved correctly")


def example_validation_failure() -> None:
    """Example: Validation fails for invalid timestamps."""
    print("\n=== Example 3: Validation Errors ===")

    from pydantic import ValidationError

    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    # Test 1: Timezone-naive timestamp fails
    try:
        Conversation(
            id="conv-003",
            title="Invalid Conversation",
            created_at=datetime(2024, 3, 15, 14, 30, 0),  # No timezone!
            updated_at=None,
            messages=[msg],
        )
        print("✗ Should have raised ValidationError for naive datetime")
    except ValidationError as e:
        print(f"✓ Correctly rejected naive created_at: {e.error_count()} error(s)")

    # Test 2: updated_at < created_at fails
    try:
        Conversation(
            id="conv-004",
            title="Invalid Conversation",
            created_at=datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC),
            updated_at=datetime(2024, 3, 14, 10, 0, 0, tzinfo=UTC),  # Before creation!
            messages=[msg],
        )
        print("✗ Should have raised ValidationError for updated_at < created_at")
    except ValidationError as e:
        print(f"✓ Correctly rejected updated_at < created_at: {e.error_count()} error(s)")


def example_json_serialization() -> None:
    """Example: JSON output always has both timestamps."""
    print("\n=== Example 4: JSON Serialization ===")

    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)

    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    # Conversation with no updates
    conv = Conversation(
        id="conv-005",
        title="JSON Test",
        created_at=created,
        updated_at=None,
        messages=[msg],
    )

    # Simulate JSON serialization (as done in formatters.py)
    json_output = {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "updated_at": conv.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%S"),
        "message_count": conv.message_count,
    }

    print(f"JSON output: {json_output}")
    print("✓ Both timestamps present in JSON (created_at == updated_at)")
    assert json_output["created_at"] == json_output["updated_at"]


def example_date_filtering() -> None:
    """Example: Date filtering for search (uses created_at)."""
    print("\n=== Example 5: Date Filtering ===")

    from datetime import date

    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)

    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    conv = Conversation(
        id="conv-006",
        title="Date Filter Test",
        created_at=created,
        updated_at=None,
        messages=[msg],
    )

    # Date filtering uses created_at (as per search implementation)
    target_date = date(2024, 3, 15)
    conv_date = conv.created_at.date()

    print(f"Conversation date: {conv_date}")
    print(f"Target date: {target_date}")
    print(f"Match: {conv_date == target_date}")

    assert conv_date == target_date
    print("✓ Date filtering works with created_at")


if __name__ == "__main__":
    print("Timestamp Handling Examples")
    print("=" * 60)

    example_conversation_never_updated()
    example_conversation_with_updates()
    example_validation_failure()
    example_json_serialization()
    example_date_filtering()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
