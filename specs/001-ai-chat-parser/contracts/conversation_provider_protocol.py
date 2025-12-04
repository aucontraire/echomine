"""
ConversationProvider Protocol

This file defines the contract that all AI provider adapters MUST implement.
This is a design artifact (not executable code) that will be implemented in src/echomine/models/protocols.py.

Contract per Constitution Principle VII: Multi-Provider Adapter Pattern

Complete Protocol Method Signatures (per FR-215, FR-216, FR-217, FR-218, FR-220, FR-221):
======================================================================================

1. stream_conversations(
       file_path: Path,
       *,
       progress_callback: Optional[ProgressCallback] = None,
       on_skip: Optional[OnSkipCallback] = None
   ) -> Iterator[Conversation]

   Raises: FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError

   Memory Guarantee: O(1) - constant memory regardless of file size
   Thread Safety: Adapter thread-safe, iterator NOT thread-safe (one per thread)
   Determinism: Same file -> same conversation order (chronological)


2. search(
       file_path: Path,
       query: SearchQuery,
       *,
       progress_callback: Optional[ProgressCallback] = None,
       on_skip: Optional[OnSkipCallback] = None
   ) -> Iterator[SearchResult]

   Raises: FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError

   Memory Guarantee: O(matching_results) - only matching conversations buffered
   Thread Safety: Adapter thread-safe, iterator NOT thread-safe (one per thread)
   Determinism: Same file + query -> same results in same relevance order


3. get_conversation_by_id(
       file_path: Path,
       conversation_id: str
   ) -> Optional[Conversation]

   Raises: FileNotFoundError, PermissionError, ParseError, SchemaVersionError

   Memory Guarantee: O(1) - streams until ID found, does not load full file
   Thread Safety: Adapter thread-safe, safe for concurrent calls
   Determinism: Same file + ID -> same conversation (or None if not found)
"""

from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Generic, Protocol, TypeVar


# Forward references to models defined in data-model.md
# Actual implementation will import from src/echomine/models/


# Generic Type Variable (per FR-151, FR-152, FR-154)
ConversationT = TypeVar("ConversationT", bound="BaseConversation")


class BaseConversation(Protocol):
    """Minimum interface required for conversation types (per FR-154).

    All provider-specific conversation types must implement these attributes.
    This enables type-safe multi-provider support via TypeVar bound constraint.
    """

    id: str
    title: str
    created_at: datetime


class Conversation:
    """Placeholder for OpenAI Conversation model (see data-model.md).

    Implements BaseConversation protocol.
    """

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SearchResult(Generic[ConversationT]):
    """Generic search result wrapping any conversation type (per FR-152).

    Type parameter allows adapters to return provider-specific conversation types
    while maintaining type safety. Example: SearchResult[Conversation] for OpenAI.
    """

    conversation: ConversationT  # Generic conversation type
    relevance_score: float


class SearchQuery:
    """Placeholder for SearchQuery model (see data-model.md)."""

    keywords: list[str] | None
    title_filter: str | None


# Callback Type Aliases (per FR-076, FR-106, FR-219)
ProgressCallback = Callable[[int], None]
"""Called with count of items processed. Used for progress indicators."""

OnSkipCallback = Callable[[str, str], None]
"""Called when entry is skipped. Args: (conversation_id, reason)."""


class ConversationProvider(Protocol[ConversationT]):
    """
    Generic protocol for AI provider export parsers (per FR-151).

    All adapters (OpenAI, Anthropic, Google, etc.) MUST implement this protocol.
    This ensures a unified interface regardless of export format.

    Type Parameter:
        ConversationT: Provider-specific conversation type (must implement BaseConversation)
                      Examples: Conversation (OpenAI), ClaudeConversation (Anthropic)

    Principles Enforced:
    - Principle VII: Multi-Provider Adapter Pattern (shared abstraction)
    - Principle VIII: Memory Efficiency (streaming via Iterator, not List)
    - Principle I: Library-First (protocol defines library API contract)

    Adapter Design (per FR-113, FR-114, FR-115, FR-120):
    - Stateless: No configuration parameters in __init__
    - Reusable: Same adapter instance can process different files
    - Lightweight: Instantiation should be instant (no I/O)
    - NOT context managers: Adapters don't implement __enter__/__exit__

    Thread Safety (per FR-098, FR-099, FR-100, FR-101):
    - Adapter instances MUST be thread-safe (safe to share across threads)
    - Iterators returned by methods MUST NOT be shared across threads
    - Each thread MUST create its own iterator by calling methods separately

    Iterator Lifecycle (per FR-116, FR-117, FR-118, FR-119):
    - Iterators are single-use (exhausted after completion)
    - Multiple calls return independent iterators (not resume)
    - File handles closed even if iteration stops early
    - Context managers guarantee cleanup in ALL scenarios

    Resource Management (per FR-130, FR-131, FR-132, FR-133):
    - Methods use try/finally for cleanup guarantees
    - File handles managed via context managers
    - Cleanup occurs: normal completion, early break, exceptions, GC
    - NO __del__ methods for cleanup

    Backpressure (per FR-134, FR-135, FR-136, FR-137):
    - NO explicit backpressure mechanisms
    - Generators yield one item at a time
    - Memory usage constant regardless of consumer speed
    - Consumer controls parsing pace (pull-based)
    """

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: ProgressCallback | None = None,
        on_skip: OnSkipCallback | None = None,
    ) -> Iterator[ConversationT]:
        """
        Stream conversations one at a time from export file (per FR-151, FR-153).

        Memory Contract: MUST use streaming (ijson or equivalent) to avoid loading
        entire file into memory. Memory usage MUST be constant regardless of file size.

        Args:
            file_path: Absolute path to export file (e.g., /path/to/conversations.json)
            progress_callback: Optional callback(count) called periodically with item count (per FR-076, FR-077)
            on_skip: Optional callback(conversation_id, reason) when malformed entries skipped (per FR-106, FR-107)

        Yields:
            ConversationT: Provider-specific conversation objects one at a time
                          (Conversation for OpenAI, ClaudeConversation for Anthropic, etc.)

        Raises:
            FileNotFoundError: If file_path does not exist (per FR-049, FR-033)
            PermissionError: If file_path is not readable (per FR-051, FR-033)
            ParseError: If export format is invalid or corrupted (per FR-036)
            SchemaVersionError: If export schema version is unsupported (per FR-036, FR-085)
            ValidationError: If conversation data fails Pydantic validation (per FR-036, FR-054)

        Exception Handling (per FR-042, FR-045, FR-046, FR-047, FR-048):
            - MUST fail fast, no retries
            - MUST use context managers for file handle cleanup
            - MUST include conversation index in exception messages
            - MUST NOT raise StopIteration explicitly (use return)

        Progress Reporting (per FR-068, FR-069):
            - progress_callback called every 100 items OR 100ms, whichever comes first
            - Callback receives current item count (not percentage)

        Graceful Degradation (per FR-004, FR-105):
            - Malformed entries skipped with WARNING log
            - on_skip callback invoked with conversation_id and reason
            - Processing continues after skip

        Thread Safety:
            This iterator MUST NOT be shared across threads (per FR-099).
            Each thread must call this method to get its own iterator.

        Example:
            >>> adapter = OpenAIAdapter()
            >>> def progress(count):
            ...     print(f"Processed {count} conversations")
            >>> def handle_skip(conv_id, reason):
            ...     print(f"Skipped {conv_id}: {reason}")
            >>> for conversation in adapter.stream_conversations(
            ...     Path("export.json"),
            ...     progress_callback=progress,
            ...     on_skip=handle_skip
            ... ):
            ...     print(conversation.title)
        """
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        *,
        progress_callback: ProgressCallback | None = None,
        on_skip: OnSkipCallback | None = None,
    ) -> Iterator[SearchResult[ConversationT]]:
        """
        Search conversations matching query criteria with relevance ranking (per FR-152, FR-153).

        Ranking Contract: Results MUST be sorted by relevance_score (descending).
        TF-IDF or equivalent algorithm MUST be used for keyword ranking (FR-008).

        Args:
            file_path: Path to export file
            query: Search parameters (keywords, title filter, date range, limit)
            progress_callback: Optional callback(count) for progress reporting (per FR-076, FR-077)
            on_skip: Optional callback(conversation_id, reason) when entries skipped (per FR-106, FR-107)

        Yields:
            SearchResult[ConversationT]: Matched conversations with provider-specific type,
                                         sorted by relevance (highest first)

        Raises:
            FileNotFoundError: If file_path does not exist (per FR-049)
            PermissionError: If file_path is not readable (per FR-051)
            ParseError: If export format is invalid (per FR-036)
            SchemaVersionError: If schema version unsupported (per FR-036, FR-085)
            ValidationError: If query or conversation data invalid (per FR-036, FR-054, FR-055)

        Thread Safety:
            This iterator MUST NOT be shared across threads (per FR-099).

        Example:
            >>> query = SearchQuery(keywords=["algorithm"], limit=5)
            >>> for result in adapter.search(Path("export.json"), query):
            ...     print(f"{result.relevance_score:.2f}: {result.conversation.title}")
        """
        ...

    def get_conversation_by_id(self, file_path: Path, conversation_id: str) -> ConversationT | None:
        """
        Retrieve specific conversation by UUID (per FR-151, FR-153, FR-155).

        Performance Contract: MAY use streaming or index lookup. For large files,
        consider building an in-memory index (conversation_id -> file offset) on first call.

        Args:
            file_path: Path to export file
            conversation_id: Conversation UUID from export

        Returns:
            ConversationT: Provider-specific conversation object if found
            None: If conversation_id not found in export (per FR-155)

        Raises:
            FileNotFoundError: If file_path does not exist

        Example:
            >>> conv = adapter.get_conversation_by_id(Path("export.json"), "conv-uuid-123")
            >>> if conv:
            ...     print(conv.title)
        """
        ...


# Contract Tests (shared across all adapter implementations)
# ============================================================
# All ConversationProvider implementations MUST pass these tests:
#
# 1. test_stream_conversations_memory_bounded()
#    - Process 1GB file with memory usage < 100MB
#
# 2. test_stream_conversations_fail_fast()
#    - FileNotFoundError raised immediately for missing file
#    - PermissionError raised immediately for unreadable file
#
# 3. test_search_results_sorted_by_relevance()
#    - Results returned in descending relevance order
#    - TF-IDF scoring used for keyword queries
#
# 4. test_search_respects_limit()
#    - No more than query.limit results returned
#
# 5. test_get_conversation_by_id_returns_none_if_not_found()
#    - None returned (not exception) for missing conversation_id
#
# See tests/contract/test_provider_protocol.py for full test suite.
