"""Statistics calculation functions for conversation exports.

This module provides functions for calculating aggregate statistics across entire
export files (calculate_statistics) and detailed statistics for individual
conversations (calculate_conversation_statistics).

Memory Characteristics:
    - calculate_statistics(): O(1) memory usage via streaming (ijson)
    - calculate_conversation_statistics(): O(N) where N = messages in conversation

Constitution Compliance:
    - Principle VIII: Memory-efficient streaming (FR-003, SC-001)
    - Principle VI: Strict typing with mypy --strict compliance
    - Principle IV: Observability (structured logging, progress callbacks)
    - FR-016, FR-022: Library-first statistics API

Baseline Enhancement Package (v1.2.0):
    - FR-016: calculate_statistics() with streaming parser
    - FR-022: calculate_conversation_statistics() as pure function
    - FR-060a: Structured logging via structlog
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.protocols import OnSkipCallback, ProgressCallback
from echomine.models.statistics import (
    ConversationStatistics,
    ConversationSummary,
    ExportStatistics,
    RoleCount,
)


# Module logger for operational visibility
logger = logging.getLogger(__name__)


def calculate_statistics(
    file_path: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> ExportStatistics:
    """Calculate statistics for entire export file (FR-016).

    Uses streaming (O(1) memory) to process arbitrarily large export files.
    Invokes progress_callback every 100 conversations and on_skip callback
    for malformed entries that are skipped during processing.

    Memory Characteristics:
        - O(1) memory usage regardless of file size
        - Streaming parser (ijson) with bounded buffer (~50MB)
        - No accumulation of conversation objects
        - Tracks only aggregate statistics (counts, min/max, dates)

    Args:
        file_path: Path to OpenAI export JSON file
        progress_callback: Optional callback invoked every 100 conversations (FR-069)
        on_skip: Optional callback for malformed entries (conversation_id, reason)

    Returns:
        ExportStatistics with aggregated statistics

    Raises:
        FileNotFoundError: If file doesn't exist
        ParseError: If JSON is malformed (syntax errors)

    Example:
        ```python
        from pathlib import Path
        from echomine.statistics import calculate_statistics

        # Basic usage
        stats = calculate_statistics(Path("export.json"))
        print(f"Total: {stats.total_conversations} conversations")
        print(f"Messages: {stats.total_messages}")
        print(f"Average: {stats.average_messages:.1f} per conversation")

        # With progress tracking
        def on_progress(count: int) -> None:
            print(f"Processed {count} conversations...")

        stats = calculate_statistics(
            Path("export.json"),
            progress_callback=on_progress
        )

        # With skip tracking
        skipped: list[str] = []

        def on_skip_entry(conv_id: str, reason: str) -> None:
            skipped.append(conv_id)

        stats = calculate_statistics(
            Path("export.json"),
            on_skip=on_skip_entry
        )
        print(f"Skipped {len(skipped)} malformed entries")
        ```

    Requirements:
        - FR-016: Function signature with file_path, progress_callback, on_skip
        - FR-003: O(1) memory usage via streaming
        - FR-060a: Structured logging
        - SC-001: Memory usage <1GB for large exports
    """
    logger.info("calculate_statistics", extra={"file_name": str(file_path)})

    # Initialize aggregation variables
    total_conversations = 0
    total_messages = 0
    earliest_date: datetime | None = None
    latest_date: datetime | None = None
    largest_conversation: ConversationSummary | None = None
    smallest_conversation: ConversationSummary | None = None
    skipped_count = 0

    # Use OpenAIAdapter for streaming (O(1) memory)
    adapter = OpenAIAdapter()

    # Wrap on_skip to track skipped_count
    def on_skip_wrapper(conversation_id: str, reason: str) -> None:
        nonlocal skipped_count
        skipped_count += 1
        if on_skip:
            on_skip(conversation_id, reason)

    # Stream conversations one at a time
    # Memory: O(1) - each conversation processed and discarded
    for conversation in adapter.stream_conversations(
        file_path,
        progress_callback=progress_callback,
        on_skip=on_skip_wrapper,
    ):
        # Track total conversations
        total_conversations += 1

        # Track total messages
        message_count = conversation.message_count
        total_messages += message_count

        # Track earliest created_at
        if earliest_date is None or conversation.created_at < earliest_date:
            earliest_date = conversation.created_at

        # Track latest updated_at (fallback to created_at)
        conv_latest = conversation.updated_at or conversation.created_at
        if latest_date is None or conv_latest > latest_date:
            latest_date = conv_latest

        # Track largest conversation
        if largest_conversation is None or message_count > largest_conversation.message_count:
            largest_conversation = ConversationSummary(
                id=conversation.id,
                title=conversation.title,
                message_count=message_count,
            )

        # Track smallest conversation
        if smallest_conversation is None or message_count < smallest_conversation.message_count:
            smallest_conversation = ConversationSummary(
                id=conversation.id,
                title=conversation.title,
                message_count=message_count,
            )

    # Calculate average messages per conversation
    average_messages = total_messages / total_conversations if total_conversations > 0 else 0.0

    # Build ExportStatistics
    stats = ExportStatistics(
        total_conversations=total_conversations,
        total_messages=total_messages,
        earliest_date=earliest_date,
        latest_date=latest_date,
        average_messages=average_messages,
        largest_conversation=largest_conversation,
        smallest_conversation=smallest_conversation,
        skipped_count=skipped_count,
    )

    logger.info(
        "calculate_statistics complete",
        extra={
            "file_name": str(file_path),
            "total_conversations": total_conversations,
            "total_messages": total_messages,
        },
    )

    return stats


def calculate_conversation_statistics(
    conversation: Conversation,
) -> ConversationStatistics:
    """Calculate detailed statistics for single conversation (FR-022).

    Pure function - no I/O, no side effects. Deterministic: same input produces
    same output. Calculates message counts, role distribution, temporal patterns
    (duration, average gap between messages), and first/last message timestamps.

    Memory Characteristics:
        - O(N) where N = messages in conversation
        - No file I/O or external state access
        - Deterministic (same input -> same output)

    Args:
        conversation: Conversation to analyze

    Returns:
        ConversationStatistics with message breakdown and temporal patterns

    Example:
        ```python
        from echomine.adapters import OpenAIAdapter
        from echomine.statistics import calculate_conversation_statistics

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

    Requirements:
        - FR-022: Function signature with conversation parameter
        - FR-019: Message count by role
        - FR-021: First/last message timestamps and duration
        - Pure function (no I/O, no side effects, deterministic)
    """
    logger.info(
        "calculate_conversation_statistics",
        extra={
            "conversation_id": conversation.id,
            "message_count": conversation.message_count,
        },
    )

    # Calculate message count by role
    user_count = 0
    assistant_count = 0
    system_count = 0

    for message in conversation.messages:
        if message.role == "user":
            user_count += 1
        elif message.role == "assistant":
            assistant_count += 1
        elif message.role == "system":
            system_count += 1

    role_count = RoleCount(user=user_count, assistant=assistant_count, system=system_count)

    # Calculate temporal patterns
    first_message = None
    last_message = None
    duration_seconds = 0.0
    average_gap_seconds = None

    if conversation.messages:
        # Messages are already sorted chronologically by OpenAIAdapter
        first_message = conversation.messages[0].timestamp
        last_message = conversation.messages[-1].timestamp

        # Calculate duration (first to last message)
        duration_seconds = (last_message - first_message).total_seconds()

        # Calculate average gap between consecutive messages (only if 2+ messages)
        if len(conversation.messages) >= 2:
            gaps = []
            for i in range(1, len(conversation.messages)):
                gap = (
                    conversation.messages[i].timestamp - conversation.messages[i - 1].timestamp
                ).total_seconds()
                gaps.append(gap)

            average_gap_seconds = sum(gaps) / len(gaps)

    # Build ConversationStatistics
    stats = ConversationStatistics(
        conversation_id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=conversation.message_count,
        message_count_by_role=role_count,
        first_message=first_message,
        last_message=last_message,
        duration_seconds=duration_seconds,
        average_gap_seconds=average_gap_seconds,
    )

    logger.info(
        "calculate_conversation_statistics complete",
        extra={
            "conversation_id": conversation.id,
            "message_count": conversation.message_count,
            "duration_seconds": duration_seconds,
        },
    )

    return stats
