# Library API Contract: Claude Export Adapter

**Feature**: 004-claude-adapter
**Date**: 2025-12-08
**Version**: 1.0.0

## Overview

This contract defines the public API for the `ClaudeAdapter` class. The API is identical to `OpenAIAdapter` to ensure multi-provider consistency.

## ClaudeAdapter Class

### Module

```python
from echomine import ClaudeAdapter
# or
from echomine.adapters.claude import ClaudeAdapter
```

### Class Signature

```python
class ClaudeAdapter:
    """Adapter for streaming Anthropic Claude conversation exports.

    This adapter uses ijson to stream-parse Claude export files with
    O(1) memory complexity. Conversations are yielded one at a time,
    enabling processing of arbitrarily large export files.

    Constitution Compliance:
        - Principle VII: Implements ConversationProvider protocol
        - Principle VIII: Memory-efficient streaming (ijson)
        - Principle VI: Strict typing with mypy --strict

    Example:
        ```python
        from echomine import ClaudeAdapter, SearchQuery
        from pathlib import Path

        adapter = ClaudeAdapter()

        # Stream all conversations
        for conv in adapter.stream_conversations(Path("conversations.json")):
            print(f"{conv.title}: {conv.message_count} messages")

        # Search with BM25 ranking
        query = SearchQuery(keywords=["python"], limit=10)
        for result in adapter.search(Path("conversations.json"), query):
            print(f"{result.score:.2f}: {result.conversation.title}")
        ```
    """
    pass
```

## Method Contracts

### stream_conversations()

```python
def stream_conversations(
    self,
    file_path: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> Iterator[Conversation]:
    """Stream conversations from Claude export file with O(1) memory.

    Args:
        file_path: Path to Claude conversations.json export file
        progress_callback: Optional callback(count) called every 100 items OR 100ms (whichever comes first)
        on_skip: Optional callback(conversation_id, reason) when entries skipped

    Yields:
        Conversation objects parsed from export, one at a time

    Raises:
        FileNotFoundError: If file_path does not exist
        ParseError: If JSON is malformed (syntax errors)
        ValidationError: If conversation data violates schema

    Memory Complexity: O(1) for file size, O(N) for single conversation
    Time Complexity: O(M) where M = total conversations in file

    Resource Management:
        - File handles MUST be closed even on exceptions or early termination
        - Uses context managers (with statements) for automatic cleanup
        - Follows FR-130-133 resource cleanup pattern

    FR Coverage: FR-001 through FR-010, FR-051 through FR-054
    """
```

### search()

```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations with BM25 relevance ranking.

    All SearchQuery filters are supported:
    - keywords: BM25 keyword matching
    - phrases: Exact phrase matching
    - title_filter: Partial title matching (case-insensitive)
    - from_date/to_date: Date range filtering
    - min_messages/max_messages: Message count filtering
    - role_filter: Filter by message author role
    - exclude_keywords: Exclude conversations containing terms
    - match_mode: "any" (default) or "all" keywords required
    - sort_by: "score", "date", "title", "messages"
    - sort_order: "asc" or "desc"
    - limit: Maximum results to return

    Args:
        file_path: Path to Claude export file
        query: SearchQuery with filters and ranking parameters
        progress_callback: Optional callback for progress reporting
        on_skip: Optional callback for skipped entries

    Yields:
        SearchResult[Conversation] with ranked results and scores

    Raises:
        FileNotFoundError: If file_path does not exist
        ParseError: If JSON is malformed

    FR Coverage: FR-021 through FR-035
    """
```

### get_conversation_by_id()

```python
def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str,
) -> Conversation | None:
    """Retrieve specific conversation by UUID.

    Uses streaming search for memory efficiency.

    Args:
        file_path: Path to Claude export file
        conversation_id: UUID of conversation to retrieve

    Returns:
        Conversation object if found, None otherwise

    Raises:
        FileNotFoundError: If file_path does not exist
        ParseError: If JSON is malformed

    FR Coverage: FR-036 through FR-040
    """
```

### get_message_by_id()

```python
def get_message_by_id(
    self,
    file_path: Path,
    message_id: str,
    *,
    conversation_id: str | None = None,
) -> tuple[Message, Conversation] | None:
    """Retrieve specific message by UUID with parent conversation context.

    Args:
        file_path: Path to Claude export file
        message_id: UUID of message to retrieve
        conversation_id: Optional conversation UUID for faster lookup

    Returns:
        Tuple of (Message, Conversation) if found, None otherwise

    Raises:
        FileNotFoundError: If file_path does not exist
        ParseError: If JSON is malformed

    FR Coverage: FR-041 through FR-045
    """
```

## Type Definitions

### Callback Types

```python
# Progress callback - receives count of items processed
ProgressCallback = Callable[[int], None]

# Skip callback - receives (conversation_id, reason) for skipped entries
OnSkipCallback = Callable[[str, str], None]
```

### Return Types

All methods return the same types as OpenAIAdapter:

```python
# stream_conversations
Iterator[Conversation]

# search
Iterator[SearchResult[Conversation]]

# get_conversation_by_id
Conversation | None

# get_message_by_id
tuple[Message, Conversation] | None
```

## Protocol Compliance

ClaudeAdapter implements the `ConversationProvider` protocol:

```python
from echomine.models.protocols import ConversationProvider

# Runtime check
assert isinstance(ClaudeAdapter(), ConversationProvider)

# Type check (mypy)
adapter: ConversationProvider[Conversation] = ClaudeAdapter()
```

## Error Handling Contract

### Exception Hierarchy

```python
# File not found
FileNotFoundError: "If file_path does not exist"

# Invalid JSON syntax
ParseError: "JSON parsing failed: {details}"

# Schema violation
ValidationError: "Validation error for {model}: {details}"
```

### Graceful Degradation

Malformed entries are skipped with WARNING log:
- Missing required fields
- Invalid timestamps
- Invalid sender values

Processing continues after skip per FR-017, FR-018.

## Testing Contract

### Unit Test Requirements

```python
def test_stream_conversations_returns_iterator():
    """stream_conversations returns Iterator[Conversation]"""

def test_stream_conversations_parses_uuid_to_id():
    """Maps uuid field to conversation.id (FR-002)"""

def test_stream_conversations_parses_name_to_title():
    """Maps name field to conversation.title (FR-003)"""

def test_stream_conversations_parses_iso_timestamps():
    """Parses ISO 8601 timestamps to datetime (FR-004, FR-005)"""

def test_stream_conversations_normalizes_sender_to_role():
    """Maps 'human' to 'user', 'assistant' to 'assistant' (FR-013)"""

def test_search_returns_ranked_results():
    """Search returns BM25-ranked results (FR-022)"""

def test_get_conversation_by_id_returns_none_if_not_found():
    """Returns None for non-existent ID (FR-038)"""
```

### Integration Test Requirements

```python
def test_end_to_end_parse_real_export():
    """Parse actual Claude export file"""

def test_search_with_all_filters():
    """Search with keywords, phrases, date range, role filter"""

def test_memory_constant_for_large_file():
    """O(1) memory usage regardless of file size"""
```

## Versioning

- API version: 1.0.0
- Compatible with: echomine >= 1.3.0
- Breaking changes: None (new adapter)
