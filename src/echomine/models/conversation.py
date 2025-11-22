"""Conversation model for AI conversation exports.

This module defines the Conversation Pydantic model representing a complete
conversation thread with metadata and message tree navigation.

Constitution Compliance:
- Principle VI: Strict typing with mypy --strict compliance
- Principle I: Library-first (importable, reusable model)
- FR-222, FR-227: Immutability via frozen=True
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from echomine.models.message import Message


class Conversation(BaseModel):
    """Immutable conversation structure with tree navigation (per FR-222, FR-227, FR-278).

    This model represents a complete AI conversation with metadata and all messages.
    Messages form a tree structure via parent_id references, enabling branching
    dialogue paths and multi-turn interactions.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Tree Navigation:
        Conversations support tree navigation via helper methods:
        - get_root_messages(): Entry points for conversation traversal
        - get_message_by_id(): Fast lookup for specific messages
        - get_children(): Get direct replies to a message
        - get_thread(): Get message and all ancestors up to root
        - get_all_threads(): Get all root-to-leaf paths

    Example:
        ```python
        from datetime import datetime, UTC

        messages = [
            Message(id="1", content="Hello", role="user", timestamp=datetime.now(UTC), parent_id=None),
            Message(id="2", content="Hi!", role="assistant", timestamp=datetime.now(UTC), parent_id="1"),
            Message(id="3", content="Alt response", role="assistant", timestamp=datetime.now(UTC), parent_id="1"),
        ]

        conversation = Conversation(
            id="conv-001",
            title="Greeting",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            messages=messages
        )

        # Tree navigation
        roots = conversation.get_root_messages()  # [msg-1]
        children = conversation.get_children("1")  # [msg-2, msg-3]
        threads = conversation.get_all_threads()  # [[msg-1, msg-2], [msg-1, msg-3]]
        ```

    Attributes:
        id: Unique conversation identifier (non-empty string)
        title: Conversation title (non-empty, any UTF-8)
        created_at: Conversation creation timestamp (timezone-aware UTC)
        updated_at: Last modification timestamp (timezone-aware UTC)
        messages: All messages in conversation (non-empty list)
        metadata: Provider-specific fields (e.g., moderation_results, plugin_ids)
    """

    # Pydantic Configuration (per FR-222, FR-226, FR-227)
    model_config = ConfigDict(
        frozen=True,  # Immutability: prevents accidental modification
        strict=True,  # Strict validation: no type coercion
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,  # Validate on field assignment
        arbitrary_types_allowed=False,  # Only Pydantic-compatible types
    )

    # Required Fields (per FR-269, FR-270, FR-271, FR-272, FR-274)
    id: str = Field(
        ...,
        min_length=1,
        description="Unique conversation identifier (non-empty)",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Conversation title (non-empty, any UTF-8)",
    )
    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp (timezone-aware UTC)",
    )
    updated_at: datetime = Field(
        ...,
        description="Last modification timestamp (timezone-aware UTC)",
    )
    messages: list[Message] = Field(
        ...,
        min_length=1,
        description="All messages in conversation (non-empty)",
    )

    # Optional Provider-Specific Metadata (per FR-236, FR-237, FR-275)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific fields NOT part of stable API (e.g., moderation_results, plugin_ids)",
    )

    # Timestamp Validators (per FR-244, FR-245, FR-246, FR-273)
    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamps are timezone-aware and normalized to UTC.

        Args:
            v: Timestamp value to validate

        Returns:
            Timezone-aware datetime normalized to UTC

        Raises:
            ValueError: If timestamp is timezone-naive

        Requirements:
            - FR-244: Timestamps must be timezone-aware
            - FR-245: Timestamps normalized to UTC
            - FR-246: Validation enforced at parse time
        """
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            msg = f"Timestamp must be timezone-aware: {v}"
            raise ValueError(msg)
        return v.astimezone(UTC)  # Normalize to UTC

    @field_validator("updated_at")
    @classmethod
    def validate_updated_after_created(cls, v: datetime, info: Any) -> datetime:
        """Ensure updated_at >= created_at.

        Args:
            v: updated_at value to validate
            info: Field validation info containing created_at

        Returns:
            Validated updated_at timestamp

        Raises:
            ValueError: If updated_at < created_at

        Requirements:
            - FR-273: updated_at must be >= created_at
        """
        created_at = info.data.get("created_at")
        if created_at and v < created_at:
            msg = f"updated_at ({v}) must be >= created_at ({created_at})"
            raise ValueError(msg)
        return v

    # Tree Navigation Methods (per FR-278, FR-280)

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Find message by ID.

        Args:
            message_id: Message identifier to find

        Returns:
            Message if found, None otherwise

        Example:
            ```python
            msg = conversation.get_message_by_id("msg-001")
            if msg:
                print(msg.content)
            ```

        Requirements:
            - FR-278: Support message lookup by ID
        """
        return next((m for m in self.messages if m.id == message_id), None)

    def get_root_messages(self) -> list[Message]:
        """Get all root messages (parent_id is None).

        Root messages are entry points for conversation tree traversal.

        Returns:
            List of root messages (may be empty if malformed data)

        Example:
            ```python
            roots = conversation.get_root_messages()
            for root in roots:
                print(f"Thread starting with: {root.content}")
            ```

        Requirements:
            - FR-278: Support identifying conversation entry points
        """
        return [m for m in self.messages if m.parent_id is None]

    def get_children(self, message_id: str) -> list[Message]:
        """Get all direct children of a message.

        Args:
            message_id: Parent message identifier

        Returns:
            List of messages with parent_id == message_id (may be empty)

        Example:
            ```python
            children = conversation.get_children("msg-001")
            if children:
                print(f"Found {len(children)} replies")
            ```

        Requirements:
            - FR-278: Support tree navigation via parent-child relationships
        """
        return [m for m in self.messages if m.parent_id == message_id]

    def get_thread(self, message_id: str) -> list[Message]:
        """Get message and all ancestors up to root.

        Returns messages in chronological order (oldest first), representing
        the conversation path from root to the specified message.

        Args:
            message_id: Target message identifier

        Returns:
            List of messages from root to target (empty if message_id not found)

        Example:
            ```python
            thread = conversation.get_thread("msg-005")
            for msg in thread:
                print(f"{msg.role}: {msg.content}")
            ```

        Requirements:
            - FR-278: Support retrieving conversation context for a message
        """
        thread: list[Message] = []
        current = self.get_message_by_id(message_id)

        while current:
            thread.insert(0, current)  # Prepend (oldest first)
            current = (
                self.get_message_by_id(current.parent_id) if current.parent_id else None
            )

        return thread

    def get_all_threads(self) -> list[list[Message]]:
        """Get all conversation threads (root-to-leaf paths).

        Returns list of threads, where each thread is a list of messages
        from root to leaf in chronological order. Useful for understanding
        all conversation branches.

        Returns:
            List of message threads (each thread is a list of messages)

        Example:
            ```python
            # Conversation structure:
            #   msg-1 (user: "Hello")
            #   ├── msg-2 (assistant: "Hi! How can I help?")
            #   └── msg-3 (assistant: "Alternative response")
            #
            # Result: [[msg-1, msg-2], [msg-1, msg-3]]

            threads = conversation.get_all_threads()
            for i, thread in enumerate(threads):
                print(f"Thread {i+1}: {len(thread)} messages")
            ```

        Requirements:
            - FR-278: Support comprehensive tree traversal
            - FR-280: Enable analysis of all conversation branches
        """
        threads: list[list[Message]] = []

        def build_threads(msg: Message, path: list[Message]) -> None:
            """Recursive helper to build all threads from a message.

            Args:
                msg: Current message in traversal
                path: Accumulated messages from root to current
            """
            path = [*path, msg]  # Extend path with current message
            children = self.get_children(msg.id)

            if not children:
                # Leaf node: complete thread
                threads.append(path)
            else:
                # Branch node: recurse into children
                for child in children:
                    build_threads(child, path)

        # Start traversal from each root
        for root in self.get_root_messages():
            build_threads(root, [])

        return threads

    def flatten_messages(self) -> str:
        """Flatten all message content to single string for search.

        Concatenates all message content with space separation, useful for
        full-text search operations.

        Returns:
            Single string containing all message content

        Example:
            ```python
            text = conversation.flatten_messages()
            if "algorithm" in text.lower():
                print("Conversation mentions algorithms")
            ```

        Requirements:
            - FR-322: Enable full-text search across conversation content
        """
        return " ".join(msg.content for msg in self.messages)
