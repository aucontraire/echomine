"""Message model for AI conversation exports.

This module defines the Message Pydantic model representing a single message
in a conversation with threading support via parent_id references.

Constitution Compliance:
- Principle VI: Strict typing with mypy --strict compliance
- Principle I: Library-first (importable, reusable model)
- FR-223, FR-227: Immutability via frozen=True
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from echomine.models.image import ImageRef


class Message(BaseModel):
    """Immutable message structure from conversation export (per FR-223, FR-227).

    This model represents a single message in an AI conversation, supporting
    message threading via parent_id references. Messages form a tree structure
    within conversations, enabling branching dialogue paths.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        from datetime import datetime, UTC

        message = Message(
            id="msg-001",
            content="Hello, world!",
            role="user",
            timestamp=datetime.now(UTC),
            parent_id=None  # Root message
        )

        # Create a reply
        reply = Message(
            id="msg-002",
            content="Hi! How can I help?",
            role="assistant",
            timestamp=datetime.now(UTC),
            parent_id="msg-001"  # References parent
        )
        ```

    Role Normalization:
        The `role` field is normalized to one of three standard values for
        multi-provider consistency. Provider-specific roles are mapped as follows:

        OpenAI role mappings:
            - "user" → "user" (human input)
            - "assistant" → "assistant" (AI response)
            - "system" → "system" (system messages)
            - "tool" → "assistant" (tool execution is assistant action)
            - unknown roles → "assistant" (safe fallback)

        The original provider-specific role is preserved in metadata["original_role"]
        for debugging and provider-specific workflows.

    Attributes:
        id: Unique message identifier within conversation (non-empty string)
        content: Message text content (may be empty for deleted messages)
        role: Normalized message role (user, assistant, or system)
        timestamp: Message creation time (timezone-aware UTC)
        parent_id: Parent message ID for threading (None for root messages)
        images: Image attachments extracted from multimodal content (empty for text-only)
        metadata: Provider-specific fields (e.g., original_role, token_count)
    """

    # Pydantic Configuration (per FR-222, FR-223, FR-226, FR-227)
    model_config = ConfigDict(
        frozen=True,  # Immutability: prevents accidental modification
        strict=True,  # Strict validation: no type coercion
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,  # Validate on field assignment
        arbitrary_types_allowed=False,  # Only Pydantic-compatible types
    )

    # Required Fields (per FR-239, FR-244, FR-276)
    id: str = Field(
        ...,
        min_length=1,
        description="Unique message identifier within conversation (non-empty)",
    )
    content: str = Field(
        ..., description="Message text content (may be empty for deleted messages)"
    )
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Normalized message role: user, assistant, or system (per FR-239)",
    )
    timestamp: datetime = Field(
        ...,
        description="Message creation time (timezone-aware UTC, per FR-244)",
    )
    parent_id: str | None = Field(
        None,
        description="Parent message ID for threading (None for root, per FR-276)",
    )

    # Image Attachments (Phase 6: Export with Images, FR-XXX)
    images: list[ImageRef] = Field(
        default_factory=list,
        description="Image attachments extracted from multimodal content (empty for text-only)",
    )

    # Optional Provider-Specific Metadata (per FR-236)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific fields (e.g., original_role, token_count)",
    )

    # Timestamp Validator (per FR-244, FR-245, FR-246)
    @field_validator("timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware and normalized to UTC.

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

    def is_root(self) -> bool:
        """Check if message is conversation root (no parent).

        Returns:
            True if parent_id is None, False otherwise

        Example:
            ```python
            root_msg = Message(id="1", content="Hello", role="user", timestamp=now, parent_id=None)
            reply_msg = Message(id="2", content="Hi", role="assistant", timestamp=now, parent_id="1")

            assert root_msg.is_root() is True
            assert reply_msg.is_root() is False
            ```
        """
        return self.parent_id is None
