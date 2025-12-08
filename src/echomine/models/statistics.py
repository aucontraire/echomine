"""Statistics models for conversation metadata and aggregations.

This module defines Pydantic models for conversation statistics, including
minimal conversation summaries, role-based message counts, and export metadata
for markdown frontmatter.

Constitution Compliance:
- Principle VI: Strict typing with mypy --strict compliance
- Principle I: Library-first (importable, reusable models)
- Immutability via frozen=True, extra="forbid"

Baseline Enhancement Package (v1.2.0):
- FR-030-031: ExportMetadata for markdown frontmatter
- FR-018: ConversationSummary for largest/smallest conversation tracking
- FR-019-020: RoleCount for message distribution analysis
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationSummary(BaseModel):
    """Minimal conversation info for statistics (largest/smallest).

    This model provides a lightweight representation of conversation metadata
    for statistical analysis without loading full message content. Used for
    identifying largest/smallest conversations in export summaries.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        summary = ConversationSummary(
            id="conv-001",
            title="Project Planning",
            message_count=42
        )

        assert summary.message_count == 42
        assert summary.title == "Project Planning"
        ```

    Attributes:
        id: Unique conversation identifier (non-empty string)
        title: Conversation title (non-empty, any UTF-8)
        message_count: Number of messages in conversation (non-negative)

    Requirements:
        - FR-018: Metadata includes conversation ID, title, and message count
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

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
    message_count: int = Field(
        ...,
        ge=0,
        description="Number of messages in conversation (non-negative)",
    )


class RoleCount(BaseModel):
    """Message count breakdown by role.

    This model aggregates message counts by role (user, assistant, system)
    for conversation statistics. Provides a .total property for convenient
    access to total message count across all roles.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        role_count = RoleCount(user=10, assistant=8, system=2)

        assert role_count.user == 10
        assert role_count.assistant == 8
        assert role_count.system == 2
        assert role_count.total == 20

        # Default values for optional fields
        role_count2 = RoleCount()
        assert role_count2.total == 0
        ```

    Attributes:
        user: Number of user messages (defaults to 0)
        assistant: Number of assistant messages (defaults to 0)
        system: Number of system messages (defaults to 0)

    Computed Properties:
        total: Sum of user + assistant + system (read-only)

    Requirements:
        - FR-019: Message count breakdown by role
        - FR-020: Total message count computed property
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    user: int = Field(
        default=0,
        ge=0,
        description="Number of user messages (non-negative)",
    )
    assistant: int = Field(
        default=0,
        ge=0,
        description="Number of assistant messages (non-negative)",
    )
    system: int = Field(
        default=0,
        ge=0,
        description="Number of system messages (non-negative)",
    )

    @property
    def total(self) -> int:
        """Total messages across all roles.

        Returns:
            Sum of user + assistant + system messages

        Example:
            ```python
            role_count = RoleCount(user=5, assistant=3, system=1)
            assert role_count.total == 9
            ```

        Requirements:
            - FR-020: Computed total property for convenience
        """
        return self.user + self.assistant + self.system


class ExportStatistics(BaseModel):
    """Export-level statistics (FR-010, FR-011, FR-017).

    Immutable model representing statistics for an entire export file.
    Calculated via streaming (O(1) memory) by calculate_statistics().

    This model provides aggregated statistics across all conversations in an
    export file, including conversation counts, message counts, temporal range,
    averages, and identification of largest/smallest conversations.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        from datetime import datetime, UTC
        from echomine.statistics import calculate_statistics

        # Calculate statistics from export file
        stats = calculate_statistics(Path("export.json"))

        print(f"Total: {stats.total_conversations} conversations")
        print(f"Messages: {stats.total_messages}")
        print(f"Average: {stats.average_messages:.1f} per conversation")

        if stats.largest_conversation:
            print(f"Largest: {stats.largest_conversation.title}")
            print(f"  ({stats.largest_conversation.message_count} messages)")
        ```

    Attributes:
        total_conversations: Total number of conversations in export (non-negative)
        total_messages: Total number of messages across all conversations (non-negative)
        earliest_date: Earliest conversation created_at (None if empty export)
        latest_date: Latest conversation updated_at (None if empty export)
        average_messages: Average messages per conversation (non-negative float)
        largest_conversation: Conversation with most messages (None if empty)
        smallest_conversation: Conversation with fewest messages (None if empty)
        skipped_count: Number of malformed conversations skipped (defaults to 0)

    Requirements:
        - FR-010: Total conversations and total messages fields
        - FR-011: Earliest/latest date fields
        - FR-017: ExportStatistics model for aggregated statistics
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    total_conversations: int = Field(
        ...,
        ge=0,
        description="Total conversations in export (non-negative)",
    )
    total_messages: int = Field(
        ...,
        ge=0,
        description="Total messages across all conversations (non-negative)",
    )
    earliest_date: datetime | None = Field(
        default=None,
        description="Earliest conversation created_at (None if empty export)",
    )
    latest_date: datetime | None = Field(
        default=None,
        description="Latest conversation updated_at (None if empty export)",
    )
    average_messages: float = Field(
        ...,
        ge=0.0,
        description="Average messages per conversation (non-negative)",
    )
    largest_conversation: ConversationSummary | None = Field(
        default=None,
        description="Conversation with most messages (None if empty)",
    )
    smallest_conversation: ConversationSummary | None = Field(
        default=None,
        description="Conversation with fewest messages (None if empty)",
    )
    skipped_count: int = Field(
        default=0,
        ge=0,
        description="Number of malformed conversations skipped (FR-015)",
    )


class ConversationStatistics(BaseModel):
    """Per-conversation statistics (FR-019-023).

    Immutable model representing detailed statistics for a single conversation.
    Calculated by calculate_conversation_statistics() as a pure function.

    This model provides comprehensive analytics for individual conversations,
    including message counts, role distribution, temporal patterns (duration,
    average gap between messages), and first/last message timestamps.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        from echomine.statistics import calculate_conversation_statistics
        from echomine.adapters import OpenAIAdapter

        adapter = OpenAIAdapter()
        conv = adapter.get_conversation_by_id(Path("export.json"), "conv-123")

        stats = calculate_conversation_statistics(conv)

        print(f"Title: {stats.title}")
        print(f"Messages: {stats.message_count}")
        print(f"User: {stats.message_count_by_role.user}")
        print(f"Assistant: {stats.message_count_by_role.assistant}")
        print(f"Duration: {stats.duration_seconds:.0f} seconds")

        if stats.average_gap_seconds:
            print(f"Avg gap: {stats.average_gap_seconds:.1f} seconds")
        ```

    Attributes:
        conversation_id: Unique conversation identifier (non-empty)
        title: Conversation title (non-empty)
        created_at: Conversation creation timestamp (timezone-aware UTC)
        updated_at: Last modification timestamp (None if never updated)
        message_count: Total number of messages (non-negative)
        message_count_by_role: Message breakdown by role (user/assistant/system)
        first_message: Timestamp of first message (None if no messages)
        last_message: Timestamp of last message (None if no messages)
        duration_seconds: Time between first and last message (non-negative, 0.0 defaults)
        average_gap_seconds: Average time between consecutive messages (None if <2 messages)

    Requirements:
        - FR-019: Message count by role
        - FR-020: Total message count property
        - FR-021: First/last message timestamps and duration
        - FR-023: ConversationStatistics model
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    conversation_id: str = Field(
        ...,
        min_length=1,
        description="Unique conversation identifier (non-empty)",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Conversation title (non-empty)",
    )
    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp (timezone-aware UTC)",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last modification timestamp (None if never updated)",
    )
    message_count: int = Field(
        ...,
        ge=0,
        description="Total number of messages (non-negative)",
    )
    message_count_by_role: RoleCount = Field(
        ...,
        description="Message breakdown by role (user/assistant/system)",
    )

    # Temporal patterns (FR-021)
    first_message: datetime | None = Field(
        default=None,
        description="Timestamp of first message (None if no messages)",
    )
    last_message: datetime | None = Field(
        default=None,
        description="Timestamp of last message (None if no messages)",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Time between first and last message (non-negative)",
    )
    average_gap_seconds: float | None = Field(
        default=None,
        description="Average time between consecutive messages (None if <2 messages)",
    )


class ExportMetadata(BaseModel):
    """Metadata for markdown frontmatter (FR-030-031).

    This model encapsulates conversation metadata for inclusion in exported
    markdown files as YAML frontmatter. Provides structured metadata for
    downstream processing, archival, and search indexing.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        from datetime import datetime, UTC

        metadata = ExportMetadata(
            id="conv-001",
            title="Project Planning",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, 18, 30, 0, tzinfo=UTC),
            message_count=42,
            export_date=datetime.now(UTC),
            exported_by="echomine"
        )

        assert metadata.message_count == 42
        assert metadata.exported_by == "echomine"

        # Optional updated_at
        metadata2 = ExportMetadata(
            id="conv-002",
            title="Test",
            created_at=datetime.now(UTC),
            message_count=5,
            export_date=datetime.now(UTC)
        )
        assert metadata2.updated_at is None
        ```

    Attributes:
        id: Unique conversation identifier
        title: Conversation title
        created_at: Conversation creation timestamp (timezone-aware UTC)
        updated_at: Last modification timestamp (timezone-aware UTC, None if never updated)
        message_count: Number of messages in conversation (non-negative)
        export_date: Timestamp when export was generated (timezone-aware UTC)
        exported_by: Tool name that generated export (defaults to "echomine")

    Requirements:
        - FR-030: Export metadata includes all conversation fields
        - FR-031: Export timestamp and tool identification
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    id: str = Field(
        ...,
        description="Unique conversation identifier",
    )
    title: str = Field(
        ...,
        description="Conversation title",
    )
    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp (timezone-aware UTC)",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last modification timestamp (timezone-aware UTC, None if never updated)",
    )
    message_count: int = Field(
        ...,
        ge=0,
        description="Number of messages in conversation (non-negative)",
    )
    export_date: datetime = Field(
        ...,
        description="Timestamp when export was generated (timezone-aware UTC)",
    )
    exported_by: str = Field(
        default="echomine",
        description="Tool name that generated export",
    )
