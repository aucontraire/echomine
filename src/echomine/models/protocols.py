"""Protocol definitions for multi-provider adapter pattern.

This module defines the ConversationProvider protocol that all AI provider
adapters (OpenAI, Anthropic, Google, etc.) MUST implement. This ensures a
unified interface regardless of export format.

Constitution Compliance:
- Principle VII: Multi-Provider Adapter Pattern (shared abstraction)
- Principle VIII: Memory Efficiency (streaming via Iterator, not List)
- Principle I: Library-First (protocol defines library API contract)
- Principle VI: Strict typing with mypy --strict compliance

Contract per FR-215 through FR-221: All adapters must implement complete
protocol method signatures with proper types, exceptions, and guarantees.
"""

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Protocol, TypeVar, runtime_checkable

from echomine.models.conversation import Conversation
from echomine.models.search import SearchQuery, SearchResult


# ============================================================================
# Callback Type Aliases (per FR-076, FR-106, FR-219)
# ============================================================================

ProgressCallback = Callable[[int], None]
"""Progress callback type for reporting items processed.

Called periodically during streaming operations to report progress.

Args:
    count: Number of items processed so far

Example:
    ```python
    def progress(count: int) -> None:
        print(f"Processed {count} conversations")

    adapter.stream_conversations(
        Path("export.json"),
        progress_callback=progress
    )
    ```

Requirements:
    - FR-076: Optional progress callbacks for all streaming operations
    - FR-077: Callbacks invoked for CLI progress indicators
    - FR-069: Callbacks invoked at least every 100 items
"""

OnSkipCallback = Callable[[str, str], None]
"""Skip callback type for reporting malformed entries.

Called when a conversation entry is skipped due to malformed data.

Args:
    conversation_id: ID of skipped conversation (if available)
    reason: Human-readable reason for skip (e.g., "Missing required field: title")

Example:
    ```python
    def handle_skip(conv_id: str, reason: str) -> None:
        print(f"Skipped {conv_id}: {reason}")

    adapter.stream_conversations(
        Path("export.json"),
        on_skip=handle_skip
    )
    ```

Requirements:
    - FR-106: Optional on_skip callbacks for all streaming operations
    - FR-107: Callbacks invoked when malformed entries encountered
    - FR-281: Graceful degradation - processing continues after skip
"""


# ============================================================================
# Base Protocol Interfaces
# ============================================================================


@runtime_checkable
class BaseConversation(Protocol):
    """Minimum interface required for conversation types (per FR-154).

    All provider-specific conversation types must implement these attributes
    to be compatible with the ConversationProvider protocol. This enables
    type-safe multi-provider support via TypeVar bound constraint.

    This is the minimal contract - providers MAY include additional fields
    in their conversation types (e.g., moderation_results, plugin_ids) as
    long as the core attributes are present.

    Example:
        ```python
        # OpenAI Conversation implements BaseConversation
        assert isinstance(openai_conversation, BaseConversation)

        # Future Anthropic Conversation would also implement BaseConversation
        assert isinstance(anthropic_conversation, BaseConversation)
        ```

    Requirements:
        - FR-154: Protocol enables generic typing for multi-provider support
        - FR-169: Core fields (id, title, created_at) mandatory across all providers
        - FR-170: Provider-specific fields allowed via metadata
    """

    id: str
    title: str
    created_at: datetime


# Generic Type Variable bound to BaseConversation (per FR-151, FR-152, FR-154)
ConversationT = TypeVar("ConversationT", bound=BaseConversation)
"""Type variable for provider-specific conversation types.

Bound to BaseConversation protocol to ensure all conversation types have
minimum required attributes (id, title, created_at).

Example:
    ```python
    # OpenAIAdapter uses Conversation type
    class OpenAIAdapter(ConversationProvider[Conversation]):
        ...

    # Future Anthropic adapter would use ClaudeConversation type
    class AnthropicAdapter(ConversationProvider[ClaudeConversation]):
        ...
    ```

Requirements:
    - FR-151: Generic type parameters for protocol flexibility
    - FR-152: TypeVar enables type-safe multi-provider support
"""


# ============================================================================
# ConversationProvider Protocol
# ============================================================================


@runtime_checkable
class ConversationProvider(Protocol[ConversationT]):
    """Generic protocol for AI provider export parsers (per FR-151).

    All adapters (OpenAI, Anthropic, Google, etc.) MUST implement this protocol.
    This ensures a unified interface regardless of export format, enabling
    library consumers to write provider-agnostic code.

    Type Parameter:
        ConversationT: Provider-specific conversation type (must implement BaseConversation)
                      Examples: Conversation (OpenAI), ClaudeConversation (Anthropic)

    Adapter Design Principles (per FR-113, FR-114, FR-115, FR-120):
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

    Example:
        ```python
        from pathlib import Path
        from echomine import OpenAIAdapter, SearchQuery

        adapter = OpenAIAdapter()

        # List all conversations
        for conversation in adapter.stream_conversations(Path("export.json")):
            print(conversation.title)

        # Search with filters
        query = SearchQuery(keywords=["algorithm"], limit=10)
        for result in adapter.search(Path("export.json"), query):
            print(f"{result.score:.2f}: {result.conversation.title}")

        # Get specific conversation
        conv = adapter.get_conversation_by_id(Path("export.json"), "conv-uuid-123")
        if conv:
            print(conv.title)
        ```

    Requirements:
        - FR-151: Generic protocol with ConversationT type parameter
        - FR-215-221: Complete method signatures with proper types
        - FR-027: All adapters must implement this protocol
    """

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[ConversationT]:
        """Stream conversations one at a time from export file (per FR-151, FR-153).

        Memory Contract: MUST use streaming (ijson or equivalent) to avoid loading
        entire file into memory. Memory usage MUST be constant regardless of file size.

        Args:
            file_path: Absolute path to export file (e.g., /path/to/conversations.json)
            progress_callback: Optional callback(count) called periodically with item count
            on_skip: Optional callback(conversation_id, reason) when malformed entries skipped

        Yields:
            ConversationT: Provider-specific conversation objects one at a time

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

        Requirements:
            - FR-151: Generic return type (Iterator[ConversationT])
            - FR-153: Streaming memory contract
            - FR-076, FR-077: Progress callback support
            - FR-106, FR-107: Skip callback support
        """
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        *,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[SearchResult[ConversationT]]:
        """Search conversations matching query criteria with relevance ranking.

        Ranking Contract: Results MUST be sorted by relevance_score (descending).
        BM25 or equivalent algorithm MUST be used for keyword ranking (FR-317).

        Args:
            file_path: Path to export file
            query: Search parameters (keywords, title filter, date range, limit)
            progress_callback: Optional callback(count) for progress reporting
            on_skip: Optional callback(conversation_id, reason) when entries skipped

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

        Requirements:
            - FR-152: Generic return type (Iterator[SearchResult[ConversationT]])
            - FR-153: Memory-efficient streaming
            - FR-317-326: BM25 relevance ranking
        """
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[ConversationT]:
        """Retrieve specific conversation by UUID (per FR-151, FR-153, FR-155).

        Performance Contract: MAY use streaming or index lookup. For large files,
        consider building an in-memory index (conversation_id -> file offset) on first call.

        Args:
            file_path: Path to export file
            conversation_id: Conversation UUID from export

        Returns:
            ConversationT: Provider-specific conversation object if found
            None: If conversation_id not found in export (per FR-155)

        Raises:
            FileNotFoundError: If file_path does not exist (per FR-049)
            PermissionError: If file_path is not readable (per FR-051)
            ParseError: If export format is invalid (per FR-036)
            SchemaVersionError: If schema version unsupported (per FR-036, FR-085)

        Requirements:
            - FR-151: Generic return type (Optional[ConversationT])
            - FR-153: Memory-efficient (O(1) or streaming until found)
            - FR-155: Returns None if not found (not exception)
        """
        ...
