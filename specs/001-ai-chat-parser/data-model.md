# Data Model: Echomine AI Chat Parser

**Feature**: 001-ai-chat-parser
**Date**: 2025-11-21
**Status**: ✅ Complete

## Overview

This document defines the Pydantic v2 data models for Echomine. All models are:
- **Immutable**: `frozen=True` (constitution requirement)
- **Strictly typed**: mypy --strict compliant
- **Validated**: Pydantic validation catches malformed data at parse time

## Core Entities

### Message

Represents a single message in a conversation with threading support.

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
from typing import Optional, List, Literal, Any

class Message(BaseModel):
    """Immutable message structure from conversation export (per FR-223, FR-227).

    This model is FROZEN - attempting to modify fields will raise ValidationError.
    Use .model_copy(update={...}) to create modified instances.
    """
    # Pydantic Configuration (per FR-223, FR-226, FR-227)
    model_config = ConfigDict(
        frozen=True,              # Immutability: prevents accidental modification
        strict=True,              # Strict validation: no type coercion
        extra="forbid",           # Reject unknown fields
        validate_assignment=True, # Validate on field assignment
        arbitrary_types_allowed=False,  # Only Pydantic-compatible types
    )

    # Required Fields (per FR-239, FR-244, FR-276)
    id: str = Field(..., description="Unique message identifier within conversation")
    content: str = Field(..., description="Message text content")
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Normalized message role (per FR-239): user, assistant, or system"
    )
    timestamp: datetime = Field(
        ...,
        description="Message creation time (timezone-aware UTC, per FR-244)"
    )
    parent_id: Optional[str] = Field(
        None,
        description="Parent message ID for threading (None for root, per FR-276)"
    )

    # Optional Provider-Specific Metadata (per FR-236)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific fields (e.g., original_role, token_count)"
    )

    # Timestamp Validator (per FR-246)
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware and normalized to UTC (per FR-244, FR-245, FR-246)."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError(f"Timestamp must be timezone-aware: {v}")
        return v.astimezone(timezone.utc)  # Normalize to UTC

    def is_root(self) -> bool:
        """Check if message is conversation root (no parent)."""
        return self.parent_id is None
```

**Fields**:
- `id`: UUID from OpenAI export (unique per conversation)
- `content`: Full message text (may be empty for deleted messages)
- `role`: Enum ensures only valid roles (type safety)
- `timestamp`: Parsed from ISO 8601 string in export
- `parent_id`: Enables tree reconstruction (None = root message)
- `child_ids`: List of message IDs that reply to this message (branching)

**Validation Rules**:
- `content` must be string (empty string allowed for deleted messages)
- `timestamp` must be valid datetime (Pydantic parses ISO 8601 automatically)
- `child_ids` cannot contain duplicates (enforced by set conversion if needed)

**State Transitions**: Messages are immutable (no state changes after creation)

---

### Conversation

Represents a complete conversation thread with metadata and message tree.

```python
class Conversation(BaseModel):
    """Immutable conversation structure with tree navigation (per FR-222, FR-227, FR-278).

    This model is FROZEN - attempting to modify fields will raise ValidationError.
    Use .model_copy(update={...}) to create modified instances.
    """
    # Pydantic Configuration (per FR-222, FR-226, FR-227)
    model_config = ConfigDict(
        frozen=True,              # Immutability: prevents accidental modification
        strict=True,              # Strict validation: no type coercion
        extra="forbid",           # Reject unknown fields
        validate_assignment=True, # Validate on field assignment
        arbitrary_types_allowed=False,  # Only Pydantic-compatible types
    )

    # Required Fields (per FR-269, FR-270, FR-271, FR-272, FR-274)
    id: str = Field(..., description="Unique conversation identifier (non-empty)")
    title: str = Field(..., description="Conversation title (non-empty, any UTF-8)")
    created_at: datetime = Field(..., description="Conversation creation timestamp (timezone-aware UTC)")
    updated_at: datetime = Field(..., description="Last modification timestamp (timezone-aware UTC)")
    messages: List[Message] = Field(..., description="All messages in conversation (non-empty)")

    # Optional Provider-Specific Metadata (per FR-236, FR-237, FR-275)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific fields NOT part of stable API (e.g., moderation_results, plugin_ids)"
    )

    # Timestamp Validators (per FR-246, FR-273)
    @field_validator('created_at', 'updated_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamps are timezone-aware and normalized to UTC (per FR-244, FR-245, FR-246)."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError(f"Timestamp must be timezone-aware: {v}")
        return v.astimezone(timezone.utc)  # Normalize to UTC

    @field_validator('updated_at')
    @classmethod
    def validate_updated_after_created(cls, v: datetime, info) -> datetime:
        """Ensure updated_at >= created_at (per FR-273)."""
        created_at = info.data.get('created_at')
        if created_at and v < created_at:
            raise ValueError(f"updated_at ({v}) must be >= created_at ({created_at})")
        return v

    @field_validator('messages')
    @classmethod
    def validate_non_empty_messages(cls, v: List[Message]) -> List[Message]:
        """Ensure conversations have at least one message (per FR-274)."""
        if not v:
            raise ValueError("Conversation must have at least one message")
        return v

    @field_validator('id', 'title')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure id and title are non-empty (per FR-270, FR-271)."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty string")
        return v

    # Tree Navigation Methods (per FR-278, FR-280)

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Find message by ID (per FR-278)."""
        return next((m for m in self.messages if m.id == message_id), None)

    def get_root_messages(self) -> List[Message]:
        """Get all root messages (parent_id is None) (per FR-278)."""
        return [m for m in self.messages if m.parent_id is None]

    def get_children(self, message_id: str) -> List[Message]:
        """Get all direct children of a message (per FR-278)."""
        return [m for m in self.messages if m.parent_id == message_id]

    def get_thread(self, message_id: str) -> List[Message]:
        """Get message and all ancestors up to root (per FR-278).

        Returns messages in chronological order (oldest first).
        """
        thread = []
        current = self.get_message_by_id(message_id)

        while current:
            thread.insert(0, current)  # Prepend (oldest first)
            current = self.get_message_by_id(current.parent_id) if current.parent_id else None

        return thread

    def get_all_threads(self) -> List[List[Message]]:
        """Get all conversation threads (root-to-leaf paths) (per FR-278, FR-280).

        Returns list of threads, where each thread is a list of messages
        from root to leaf in chronological order.

        Example:
            msg-1 (user: "Hello")
            ├── msg-2 (assistant: "Hi! How can I help?")
            └── msg-3 (assistant: "Alternative response")

            Returns: [[msg-1, msg-2], [msg-1, msg-3]]
        """
        threads = []

        def build_threads(msg: Message, path: List[Message]):
            path = path + [msg]
            children = self.get_children(msg.id)

            if not children:
                # Leaf node: complete thread
                threads.append(path)
            else:
                # Branch node: recurse into children
                for child in children:
                    build_threads(child, path)

        for root in self.get_root_messages():
            build_threads(root, [])

        return threads

    def flatten_messages(self) -> str:
        """Flatten all message content to single string for search."""
        return " ".join(msg.content for msg in self.messages)
```

**Fields**:
- `id`: Conversation UUID from export
- `title`: User-provided or auto-generated from first message
- `created_at`: Timestamp of first message
- `updated_at`: Timestamp of most recent message
- `messages`: Flat list for iteration (preserves parse order)
- `message_tree`: Dict for O(1) lookup by message ID

**Relationships**:
- One Conversation has many Messages (1:N)
- Messages form a tree via `parent_id` / `child_ids` (self-referential)

**Helper Methods**:
- `get_root_messages()`: Entry points for conversation tree traversal
- `get_message_by_id()`: Fast lookup for threading operations
- `get_children()`: Navigate message tree (breadth-first or depth-first)
- `flatten_messages()`: Prepare text for full-text keyword search

---

### SearchResult

Represents a conversation match from a search query with relevance metadata.

```python
class SearchResult(BaseModel):
    """Search result with relevance scoring (per FR-224, FR-227)."""
    # Pydantic Configuration (per FR-224, FR-226, FR-227)
    model_config = ConfigDict(
        frozen=True,              # Immutability
        strict=True,              # Strict validation
        extra="forbid",           # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    conversation: Conversation = Field(..., description="Matched conversation object")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0-1.0, higher = better)")
    matched_message_ids: List[str] = Field(
        default_factory=list,
        description="Message IDs containing keyword matches"
    )

    def __lt__(self, other: "SearchResult") -> bool:
        """Enable sorting by relevance (descending)."""
        return self.score > other.score  # Reverse for descending
```

**Fields**:
- `conversation`: Full Conversation object (not just ID - enables immediate access)
- `relevance_score`: TF-IDF score (0.0 to unbounded, higher = better match)
- `matched_keywords`: List of keywords found in conversation (subset of query keywords)
- `excerpt`: 200-character snippet with keyword context (FR-034)

**Validation Rules**:
- `relevance_score` must be >= 0.0 (Pydantic `ge` validator)
- `excerpt` max 200 characters (Pydantic `max_length` validator)
- `matched_keywords` must not be empty (at least one keyword matched)

**Sorting**: Implements `__lt__` for sorting results by relevance (highest first)

---

### SearchQuery

Encapsulates search parameters and filters.

```python
from typing import Optional
from datetime import date

class SearchQuery(BaseModel):
    """Search query parameters with filters."""
    model_config = {"frozen": True, "strict": True}

    keywords: Optional[List[str]] = Field(None, description="Keywords for full-text search (OR logic)")
    title_filter: Optional[str] = Field(None, description="Partial match on conversation title (metadata-only)")
    from_date: Optional[date] = Field(None, description="Start date for date range filter (inclusive)")
    to_date: Optional[date] = Field(None, description="End date for date range filter (inclusive)")
    limit: int = Field(10, gt=0, le=1000, description="Maximum results to return (1-1000)")

    def has_keyword_search(self) -> bool:
        """Check if keyword search is requested."""
        return self.keywords is not None and len(self.keywords) > 0

    def has_title_filter(self) -> bool:
        """Check if title filtering is requested."""
        return self.title_filter is not None and len(self.title_filter) > 0

    def has_date_filter(self) -> bool:
        """Check if date range filtering is requested."""
        return self.from_date is not None or self.to_date is not None
```

**Fields**:
- `keywords`: List of search terms (OR logic per FR-007)
- `title_filter`: Substring match on conversation title (faster than full-text)
- `from_date` / `to_date`: Date range filter (ISO 8601 format per FR-009)
- `limit`: Max results (default 10, capped at 1000 for performance)

**Validation Rules**:
- `limit` must be 1-1000 (prevents excessive result sets)
- `from_date` <= `to_date` if both provided (date range sanity check)
- At least one filter must be non-empty (keywords, title, or date)

---

## Message Tree Structure Examples

**Per FR-276, FR-279, FR-280**: Tree structure represented using parent_id references (adjacency list pattern).

### JSON Serialization Format

Conversations use **flat message lists** with parent_id references (not nested objects):

```json
{
  "id": "conv-123",
  "title": "Multi-branch conversation",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg-1",
      "parent_id": null,
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-15T10:00:00Z",
      "metadata": {}
    },
    {
      "id": "msg-2",
      "parent_id": "msg-1",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2024-01-15T10:01:00Z",
      "metadata": {}
    },
    {
      "id": "msg-3",
      "parent_id": "msg-1",
      "role": "assistant",
      "content": "Alternative response",
      "timestamp": "2024-01-15T10:01:30Z",
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

### Tree Visualization

The above conversation has this tree structure:

```
msg-1 (user: "Hello")
├── msg-2 (assistant: "Hi! How can I help?")
└── msg-3 (assistant: "Alternative response")
```

### Tree Navigation Examples

```python
# Get all root messages
roots = conversation.get_root_messages()
# Returns: [msg-1]

# Get children of a message
children = conversation.get_children("msg-1")
# Returns: [msg-2, msg-3]

# Get thread (message + all ancestors)
thread = conversation.get_thread("msg-2")
# Returns: [msg-1, msg-2]

# Get all threads (root-to-leaf paths)
all_threads = conversation.get_all_threads()
# Returns: [[msg-1, msg-2], [msg-1, msg-3]]
```

### cognivault Integration Pattern

```python
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()
conversation = adapter.get_conversation_by_id(file_path, "conv-123")

# Ingest all conversation threads into cognivault
for thread in conversation.get_all_threads():
    # Each thread is a root-to-leaf path
    cognivault.knowledge_graph.add_thread(
        conversation_id=conversation.id,
        messages=[{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
        } for msg in thread]
    )
```

### Complex Tree Example

More complex conversation with multiple branches:

```
msg-1 (user: "Explain algorithms")
├── msg-2 (assistant: "Sure! What type?")
│   ├── msg-4 (user: "Sorting")
│   │   └── msg-6 (assistant: "Bubble sort...")
│   └── msg-5 (user: "Search")
│       └── msg-7 (assistant: "Binary search...")
└── msg-3 (assistant: "Alternative intro")
    └── msg-8 (user: "Thanks!")
```

**Threads** (root-to-leaf paths):
1. `[msg-1, msg-2, msg-4, msg-6]` - Sorting algorithm thread
2. `[msg-1, msg-2, msg-5, msg-7]` - Search algorithm thread
3. `[msg-1, msg-3, msg-8]` - Alternative conversation thread

---

## Exception Classes

Exception hierarchy for library error contract (per FR-035 through FR-063).

### EchomineError

Base exception class for all library operational errors.

```python
class EchomineError(Exception):
    """Base exception for all Echomine library errors.

    Library consumers should catch this exception to handle all operational failures.
    Exceptions NOT inheriting from this class indicate bugs (TypeError, AssertionError, etc.)
    and should propagate to help identify defects.
    """
    pass
```

**Usage**: Library consumers catch `EchomineError` to handle all library failures.

---

### ParseError

Raised when export file contains malformed JSON or invalid structure.

```python
class ParseError(EchomineError):
    """Raised when parsing export file fails due to malformed data.

    Examples:
    - Invalid JSON syntax
    - Missing required fields in export structure
    - Corrupt conversation data
    - Unexpected export format

    Message format: "{operation} failed: {reason}. {guidance}"
    """
    pass
```

**When raised**:
- JSON syntax errors (invalid characters, unclosed brackets)
- Missing required top-level fields
- Conversation structure violations
- ijson parsing failures

**Example**:
```python
raise ParseError(
    f"Failed to parse conversation at index {idx}: missing required field 'id'. "
    f"Export file may be corrupted or use unsupported schema version."
)
```

---

### ValidationError

Raised when conversation data fails Pydantic validation or custom validation rules.

```python
class ValidationError(ValueError, EchomineError):
    """Raised when conversation data fails validation.

    Subclasses ValueError for compatibility with existing code catching ValueError.

    Examples:
    - Pydantic model validation failures (wrong types, missing fields)
    - Invalid date formats (not ISO 8601)
    - Empty or malformed conversation/message IDs
    - Out-of-range values

    Message format: "Invalid {entity} in '{id}': {reason}. {expected_format}"
    """
    pass
```

**When raised**:
- Pydantic validation failures (wrong types, missing required fields)
- Invalid ISO 8601 dates
- Malformed UUIDs
- Empty required strings

**Example**:
```python
raise ValidationError(
    f"Invalid date format in conversation '{conv_id}': expected ISO 8601 (YYYY-MM-DD), got '{date_str}'. "
    f"Use --from '2024-01-01' format."
)
```

---

### SchemaVersionError

Raised when export file uses unsupported schema version.

```python
class SchemaVersionError(EchomineError):
    """Raised when export schema version is unsupported.

    Examples:
    - Detected schema version not in supported list
    - Unknown export format (not recognizable as any known schema)
    - Future OpenAI export format changes

    Message format: "Unsupported export schema version: {version}. {supported_versions}. {remediation}"
    """
    pass
```

**When raised**:
- Schema version detection identifies unsupported version
- Export format doesn't match any known heuristics
- Explicit version field contains unknown value

**Example**:
```python
raise SchemaVersionError(
    f"Unsupported export schema version: {detected_version}. "
    f"Echomine v1.0 supports only OpenAI export format v1.0 (current as of 2024). "
    f"To fix: (1) Re-export from ChatGPT, or (2) Upgrade echomine if newer version available."
)
```

---

### Standard Python Exceptions (Re-raised)

Library re-raises standard Python exceptions as-is (not wrapped) per FR-038, FR-049, FR-051.

**FileNotFoundError**:
```python
if not file_path.exists():
    raise FileNotFoundError(
        f"Export file not found: {file_path}. "
        f"Verify the file exists and the path is correct."
    )
```

**PermissionError**:
```python
try:
    with open(file_path, 'rb') as f:
        ...
except PermissionError:
    raise PermissionError(
        f"Cannot read export file: {file_path}. "
        f"Check file permissions (requires read access)."
    )
```

**Rationale**: Standard exceptions maintain compatibility with existing error handling patterns.

---

### Exception Chaining

All exceptions use chaining (`raise ... from ...`) to preserve debug context per FR-058, FR-059, FR-060.

**Pattern**:
```python
try:
    data = json.loads(content)
except JSONDecodeError as e:
    raise ParseError(
        f"Failed to parse JSON at line {e.lineno}: {e.msg}. "
        f"Export file may be corrupted."
    ) from e  # ← Preserves original exception in __cause__
```

**Benefits**:
- User sees friendly message (ParseError)
- Developer sees technical details (JSONDecodeError in `__cause__`)
- Full stack trace preserved for debugging

---

## Callback Type Signatures

Type signatures for optional callback parameters (per FR-076, FR-077, FR-106, FR-107).

### ProgressCallback

Optional callback for reporting parsing progress.

```python
from typing import Callable

ProgressCallback = Callable[[int], None]
```

**Signature**: `callback(count: int) -> None`

**Parameters**:
- `count`: Current number of items processed (conversations or search results)

**When called**: Periodically during long-running operations (every 100 items or 100ms per FR-068, FR-069)

**Usage**:
```python
def my_progress_handler(count: int) -> None:
    print(f"Processed {count} conversations...")

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(file_path, progress_callback=my_progress_handler):
    process(conv)
```

---

### OnSkipCallback

Optional callback for notification when malformed entries are skipped.

```python
from typing import Callable

OnSkipCallback = Callable[[str, str], None]
```

**Signature**: `callback(conversation_id: str, reason: str) -> None`

**Parameters**:
- `conversation_id`: ID of skipped conversation (or index as string if ID unavailable)
- `reason`: Human-readable explanation of why entry was skipped

**When called**: When FR-004 skips malformed JSON entry during parsing

**Usage**:
```python
skipped_entries = []

def handle_skip(conv_id: str, reason: str) -> None:
    skipped_entries.append((conv_id, reason))
    print(f"Warning: Skipped conversation {conv_id}: {reason}")

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(file_path, on_skip=handle_skip):
    process(conv)

print(f"Total skipped: {len(skipped_entries)}")
```

---

## Protocol Definitions

### ConversationProvider

Protocol for AI provider export parsers (multi-provider adapter pattern per Principle VII).

```python
from typing import Protocol, Iterator, Optional
from pathlib import Path

class ConversationProvider(Protocol):
    """Protocol for AI provider export parsers.

    Thread Safety (per FR-098, FR-099, FR-100, FR-101):
    - Adapter instances MUST be thread-safe (safe to share across threads)
    - Iterators returned by methods MUST NOT be shared across threads
    - Each thread MUST create its own iterator by calling methods separately
    """

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None
    ) -> Iterator[Conversation]:
        """
        Stream conversations one at a time from export file.

        Args:
            file_path: Path to export file (e.g., conversations.json)
            progress_callback: Optional callback(count) for progress reporting (per FR-076, FR-077)
            on_skip: Optional callback(conversation_id, reason) when entries skipped (per FR-106, FR-107)

        Yields:
            Conversation objects parsed from export

        Raises:
            FileNotFoundError: If file_path does not exist (per FR-049)
            PermissionError: If file_path is not readable (per FR-051)
            ParseError: If export format is invalid or corrupted (per FR-036)
            SchemaVersionError: If export schema version is unsupported (per FR-036)
            ValidationError: If conversation data fails validation (per FR-036)

        Thread Safety:
            This iterator MUST NOT be shared across threads (per FR-099).
            Each thread must call this method to get its own iterator.

        Progress Reporting:
            progress_callback called every 100 items or 100ms (per FR-068, FR-069)

        Graceful Degradation:
            Malformed entries skipped with WARNING log and on_skip callback (per FR-004, FR-105, FR-107)
        """
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None
    ) -> Iterator[SearchResult]:
        """
        Search conversations matching query criteria.

        Args:
            file_path: Path to export file
            query: Search parameters (keywords, filters, limit)
            progress_callback: Optional callback(count) for progress reporting (per FR-076, FR-077)
            on_skip: Optional callback(conversation_id, reason) when entries skipped (per FR-106, FR-107)

        Yields:
            SearchResult objects sorted by relevance (descending per FR-008)

        Raises:
            FileNotFoundError: If file_path does not exist
            ParseError: If export format is invalid
            SchemaVersionError: If schema version unsupported
            ValidationError: If query or conversation data invalid

        Thread Safety:
            This iterator MUST NOT be shared across threads (per FR-099).
        """
        ...

    def get_conversation_by_id(self, file_path: Path, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve specific conversation by ID.

        Args:
            file_path: Path to export file
            conversation_id: Conversation UUID

        Returns:
            Conversation object or None if not found

        Raises:
            FileNotFoundError: If file_path does not exist
        """
        ...
```

**Methods**:
- `stream_conversations()`: Generator for memory-efficient iteration (Principle VIII)
- `search()`: Filtered search with relevance ranking
- `get_conversation_by_id()`: Direct lookup by UUID (for export commands)

**Implementations**:
- `OpenAIAdapter`: Parses ChatGPT conversations.json format (MVP)
- Future: `AnthropicAdapter`, `GoogleAdapter` (conform to same protocol)

---

## Validation Rules Summary

| Field | Constraint | Enforcement |
|-------|-----------|-------------|
| Message.id | Non-empty string | Pydantic `...` (required) |
| Message.content | String (empty allowed) | Pydantic type check |
| Message.timestamp | Valid datetime | Pydantic datetime parser |
| Conversation.messages | Non-empty list | Pydantic `...` (required) |
| SearchResult.relevance_score | >= 0.0 | Pydantic `ge=0.0` |
| SearchResult.excerpt | <= 200 chars | Pydantic `max_length=200` |
| SearchQuery.limit | 1-1000 | Pydantic `gt=0, le=1000` |

---

## Data Flow

```
Export File (JSON)
        ↓
OpenAIAdapter.stream_conversations()
        ↓
Iterator[Conversation]  ← Memory-efficient streaming
        ↓
SearchEngine.rank_results(query)
        ↓
Iterator[SearchResult]  ← Sorted by relevance
        ↓
CLI / Library Consumer
```

**Key Properties**:
1. **Streaming**: No full-file load (ijson + generators)
2. **Immutability**: All models frozen (prevents accidental mutation)
3. **Type Safety**: mypy --strict compliant (no `Any` types)
4. **Validation**: Pydantic catches malformed data at parse time

---

## Next Steps

Phase 1 continues with:
1. ✅ Create `contracts/` directory with protocol files
2. ✅ Generate `quickstart.md` with library usage examples
3. ✅ Update agent context with technology stack

## Adapter Lifecycle & Initialization

### OpenAIAdapter Design

Stateless adapter design for thread safety (per FR-113, FR-114, FR-115, FR-120).

```python
class OpenAIAdapter:
    """Stateless adapter for OpenAI ChatGPT export format.

    Thread Safety:
    - Instance can be shared across threads (per FR-098)
    - No mutable state, no configuration
    - Each method call creates independent iterator

    Lifecycle:
    - Instantiation is lightweight (no I/O)
    - No context manager needed (stateless)
    - Reusable across different export files
    """

    def __init__(self) -> None:
        """Initialize adapter with no configuration.

        Per FR-113: No configuration parameters (stateless design).
        Per FR-115: Lightweight - no I/O, validation, or setup.

        Example:
            >>> adapter = OpenAIAdapter()  # Instant, no side effects
            >>> # Reuse across files
            >>> for conv in adapter.stream_conversations(file1):
            ...     process(conv)
            >>> for conv in adapter.stream_conversations(file2):
            ...     process(conv)
        """
        pass  # Stateless - no initialization needed
```

**Not a Context Manager** (per FR-120):
```python
# ✅ CORRECT: Direct instantiation
adapter = OpenAIAdapter()

# ❌ WRONG: Adapters are NOT context managers
# with OpenAIAdapter() as adapter:  # Not supported
#     ...
```

**Rationale**: Stateless design enables thread safety, adapter reuse, and simple API.

---

## Iterator Lifecycle & Cleanup

### Single-Use Iterators

Iterators are single-use and create independent streams (per FR-116, FR-117).

```python
adapter = OpenAIAdapter()

# First iteration - consumes iterator
for conv in adapter.stream_conversations(file_path):
    process(conv)
# Iterator is now exhausted

# Second call - NEW iterator (not resume)
for conv in adapter.stream_conversations(file_path):
    process(conv)  # Works - starts from beginning
```

### Guaranteed Cleanup

File handles closed in ALL scenarios (per FR-118, FR-119, FR-130, FR-131, FR-132):

```python
def stream_conversations(
    self,
    file_path: Path,
    progress_callback: Optional[ProgressCallback] = None,
    on_skip: Optional[OnSkipCallback] = None
) -> Iterator[Conversation]:
    """Stream conversations with guaranteed cleanup."""
    with open(file_path, 'rb') as f:  # Context manager
        try:
            for idx, conv_data in enumerate(ijson.items(f, 'item')):
                if progress_callback and idx % 100 == 0:
                    progress_callback(idx + 1)

                try:
                    yield parse_conversation(conv_data)
                except ValidationError as e:
                    if on_skip:
                        on_skip(conv_data.get('id', str(idx)), str(e))
        finally:
            # Cleanup guaranteed even if:
            # - Consumer breaks early
            # - Exception raised
            # - Generator garbage collected
            pass
    # File handle closed when exiting 'with' block
```

**Cleanup Scenarios Covered**:
- ✅ Normal completion (iterator exhausted)
- ✅ Early `break` by consumer
- ✅ Exception during iteration
- ✅ Generator garbage collected without being consumed

---

## Backpressure & Memory Management

### Natural Backpressure Handling

No explicit backpressure mechanism needed (per FR-134, FR-135, FR-136, FR-137).

**How It Works**:
```python
# Generator pauses when consumer is processing
for conv in adapter.stream_conversations(large_file):
    # If this takes 1 second, parser waits 1 second before next item
    time.sleep(1)
    cognivault.ingest(conv)  # Slow consumer

# No memory buildup:
# - ijson reads incrementally
# - Generator yields one item at a time
# - Parser pauses when consumer not ready
```

**Memory Characteristics**:
- **Slow consumer** → Parser pauses, no buffering, constant memory
- **Fast consumer** → Parser runs at max speed, still constant memory
- **Memory usage independent of consumer speed** (per FR-136)

**Pull-Based Model**:
```python
# Consumer controls flow (pull-based)
iterator = adapter.stream_conversations(file_path)

# Consumer requests next item when ready
conv1 = next(iterator)  # Parser delivers, then pauses
# ... consumer processes ...
conv2 = next(iterator)  # Parser delivers next, then pauses again
```

---

## Versioning Policy

### Semantic Versioning

Library follows strict semantic versioning (per FR-123, FR-124, FR-125, FR-126).

**Version Format**: `MAJOR.MINOR.PATCH`

**MAJOR** (Breaking changes):
- Method signature changes (removing parameters, changing types)
- Removed public classes/functions
- Changed exception hierarchy
- Example: `stream_conversations(file_path)` → `stream_conversations(file_path, required_param)`

**MINOR** (Backward-compatible additions):
- New optional parameters with defaults
- New methods on existing classes
- New exception types (additions)
- Example: Adding `progress_callback` parameter (optional, defaults to None)

**PATCH** (No API changes):
- Bug fixes
- Performance improvements
- Documentation updates
- Example: Fixing TF-IDF scoring bug

### Deprecation Process

2-release warning period before removal (per FR-127, FR-128):

```python
import warnings

def old_method(self) -> None:
    """Deprecated method with warning."""
    warnings.warn(
        "old_method() is deprecated and will be removed in v2.0.0. "
        "Use new_method() instead. "
        "Migration guide: https://echomine.readthedocs.io/migration/v2.html",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method()
```

**Timeline**:
1. **v1.5.0**: Introduce `new_method()`, deprecate `old_method()` with warning
2. **v1.6.0**: Warning remains, document migration path
3. **v2.0.0**: Remove `old_method()` (MAJOR version bump)

### Version Access

Library version available at runtime (per FR-129):

```python
import echomine

print(echomine.__version__)  # "1.0.0"
```

---

## Type Safety & Validation

### Pydantic Validation Error Handling

Library catches Pydantic errors and re-raises as echomine.ValidationError (per FR-138, FR-139, FR-140, FR-141).

**Error Handling Pattern**:
```python
from pydantic import ValidationError as PydanticValidationError
from echomine.exceptions import ValidationError

def parse_conversation(conv_data: dict, index: int) -> Conversation:
    """Parse conversation data with detailed error handling."""
    try:
        return Conversation.model_validate(conv_data)
    except PydanticValidationError as e:
        # Re-raise with context (per FR-138, FR-140)
        raise ValidationError(
            f"Conversation validation failed at index {index}: {e}. "
            f"Missing required field: 'title'. "
            f"Export file may be corrupted or from unsupported schema version."
        ) from e  # Exception chaining preserves stack trace
```

**Error Message Format** (per FR-139, FR-141):
```
{operation} failed at index {idx}: {pydantic_error}.
{field_details}
{remediation_guidance}
```

**Field-Level Details from Pydantic**:
- `Field required: title` (missing required field)
- `Input should be a valid string: received int` (type mismatch)
- `String should have at most 500 characters: received 1024` (constraint violation)

**Remediation Guidance Examples**:
- "Check export schema version with adapter.detect_schema_version()"
- "Re-export conversations from ChatGPT"
- "Verify file is not corrupted (check file size, validate JSON)"

---

### Immutability Contract

ALL data models are frozen (per FR-142, FR-143, FR-144, FR-145).

**Frozen Model Configuration**:
```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Conversation(BaseModel):
    """Immutable conversation model."""

    model_config = ConfigDict(
        frozen=True,  # Prevents in-place modifications (FR-142)
        strict=True,  # Strict type validation
    )

    id: str
    title: str
    created_at: datetime
    messages: list[Message]

class Message(BaseModel):
    """Immutable message model."""

    model_config = ConfigDict(frozen=True)  # All models frozen

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime

class SearchResult(BaseModel):
    """Immutable search result model."""

    model_config = ConfigDict(frozen=True)

    conversation: Conversation
    relevance_score: float
    matched_keywords: list[str]
    excerpt: str

class SearchQuery(BaseModel):
    """Immutable search query model."""

    model_config = ConfigDict(frozen=True)

    keywords: Optional[list[str]] = None
    title_filter: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    limit: int = 10
```

**Attempting Modifications** (per FR-143):
```python
conv = Conversation(
    id="conv-123",
    title="Original Title",
    created_at=datetime.now(),
    messages=[]
)

# ❌ In-place modification raises ValidationError
try:
    conv.title = "Updated Title"
except ValidationError as e:
    print(e)  # "Instance is frozen"
```

**Copy-on-Write Pattern** (per FR-144):
```python
# ✅ Correct: Create new instance with modifications
updated_conv = conv.model_copy(update={"title": "Updated Title"})

# Original unchanged
assert conv.title == "Original Title"
assert updated_conv.title == "Updated Title"

# Deep copy for nested structures
conv_with_new_message = conv.model_copy(
    update={"messages": conv.messages + [new_message]}
)
```

**Why Immutability**:
1. **Thread safety**: Safe to share across threads without locks
2. **Predictability**: No hidden state mutations
3. **Hash stability**: Can use as dict keys (if `__hash__` implemented)
4. **Library contract clarity**: Library returns read-only data

---

### Static Type Checking with mypy

Library enforces mypy --strict compliance (per FR-146, FR-147, FR-148, FR-149, FR-150).

**pyproject.toml Configuration**:
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "ijson.*"
ignore_missing_imports = true  # Third-party library without stubs
```

**Type Annotation Coverage** (per FR-148):
```python
from typing import Iterator, Optional
from pathlib import Path

class OpenAIAdapter:
    """All methods fully type-annotated (no Any types)."""

    def stream_conversations(
        self,
        file_path: Path,  # Explicit type (not Any)
        progress_callback: Optional[ProgressCallback] = None,  # Optional with default
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[Conversation]:  # Concrete return type (not Iterator[Any])
        """Fully type-annotated method signature."""
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[Conversation]:  # Explicit Optional (not Conversation | None in 3.12)
        """Returns None if not found."""
        ...
```

**Type Ignore Comments** (per FR-149):
```python
# ❌ BAD: No justification
result = unsafe_operation()  # type: ignore

# ✅ GOOD: Documented justification with issue link
result = unsafe_operation()  # type: ignore  # TODO(#123): Remove when upstream adds type stubs
```

**py.typed Marker** (per FR-150):
```python
# src/echomine/py.typed (empty file)
# Signals to mypy that this package has type annotations
```

**CI Integration** (per FR-147):
```yaml
# .github/workflows/ci.yml
- name: Type Check
  run: |
    poetry run mypy --strict src/ tests/
    if [ $? -ne 0 ]; then
      echo "mypy found type errors"
      exit 1
    fi
```

---

### Generic Types & Protocols

Protocol uses TypeVar for multi-provider support (per FR-151, FR-152, FR-153, FR-154).

**TypeVar Definitions**:
```python
from typing import TypeVar, Protocol, Iterator, Optional, Generic
from pathlib import Path

# TypeVar for conversation types (bound to ensure minimum interface)
ConversationT = TypeVar('ConversationT', bound='BaseConversation')

class BaseConversation(Protocol):
    """Minimum interface required for conversation types."""
    id: str
    title: str
    created_at: datetime
```

**Generic Protocol** (per FR-151):
```python
class ConversationProvider(Protocol[ConversationT]):
    """Generic protocol supporting different conversation types.

    OpenAI returns Conversation, Anthropic might return ClaudeConversation, etc.
    """

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[ConversationT]:  # Generic return type
        """Stream conversations of provider-specific type."""
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[ConversationT]:  # Generic return type
        """Get conversation by ID."""
        ...
```

**Generic SearchResult** (per FR-152):
```python
class SearchResult(Generic[ConversationT], BaseModel):
    """Search result wrapping any conversation type."""

    model_config = ConfigDict(frozen=True)

    conversation: ConversationT  # Generic type
    relevance_score: float
    matched_keywords: list[str]
    excerpt: str
```

**Concrete Adapter Implementation** (per FR-153):
```python
class OpenAIAdapter:
    """Concrete adapter returns specific Conversation type."""

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[Conversation]:  # Concrete type (not ConversationT)
        """Stream OpenAI conversations."""
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[SearchResult[Conversation]]:  # Concrete: SearchResult[Conversation]
        """Search returns results with concrete conversation type."""
        ...
```

**Type Safety Benefits**:
```python
# mypy infers concrete types
adapter: OpenAIAdapter = OpenAIAdapter()
convs: Iterator[Conversation] = adapter.stream_conversations(file_path)

for conv in convs:
    # IDE autocomplete knows conv.title, conv.messages, etc.
    print(conv.title)  # Type: str (not Any)

# Search results are also type-safe
results: Iterator[SearchResult[Conversation]] = adapter.search(file_path, query)

for result in results:
    # result.conversation is Conversation (not ConversationT)
    title: str = result.conversation.title  # ✅ Type-safe
```

---

### Type Narrowing & Optional Handling

Explicit None checks for type narrowing (per FR-155, FR-156, FR-157, FR-158).

**Optional Unwrapping** (per FR-155, FR-156):
```python
from typing import Optional

def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str,
) -> Optional[Conversation]:
    """Get conversation by ID.

    Returns:
        Conversation if found, None if not found (per FR-155)
    """
    ...

# Consumer code - explicit None check
conv: Optional[Conversation] = adapter.get_conversation_by_id(file_path, "conv-123")

if conv is not None:
    # mypy narrows type from Optional[Conversation] to Conversation
    print(conv.title)  # ✅ Type-safe
    print(conv.created_at.isoformat())  # ✅ Type-safe
else:
    print("Conversation not found")

# ❌ BAD: No None check
# print(conv.title)  # mypy error: Item "None" has no attribute "title"
```

**Union Types with Literals** (per FR-157):
```python
from typing import Literal

# ✅ GOOD: Use Literal for enums
MessageRole = Literal["user", "assistant", "system"]

class Message(BaseModel):
    role: MessageRole  # Union of literal strings
    content: str
    timestamp: datetime

# ❌ BAD: Plain str (loses type safety)
# role: str  # mypy can't validate role values
```

**Exhaustive Pattern Matching** (per FR-158):
```python
from typing import assert_never

def process_message(msg: Message) -> None:
    """Process message based on role (exhaustive matching)."""
    match msg.role:
        case "user":
            # mypy knows role is "user" here
            handle_user_message(msg)
        case "assistant":
            handle_assistant_message(msg)
        case "system":
            handle_system_message(msg)
        case _:
            # Exhaustiveness check: mypy warns if missing case
            assert_never(msg.role)  # Type error if new role added without handler

# If we add "tool" to MessageRole, mypy will catch missing case
```

**Type Narrowing with isinstance** (when needed):
```python
from typing import Union

def handle_error(error: Union[ParseError, ValidationError, SchemaVersionError]) -> None:
    """Handle different error types."""
    if isinstance(error, ParseError):
        # mypy narrows error to ParseError
        print(f"Parse error: {error.file_path}")
    elif isinstance(error, ValidationError):
        # mypy narrows error to ValidationError
        print(f"Validation error: {error.field_name}")
    elif isinstance(error, SchemaVersionError):
        # mypy narrows error to SchemaVersionError
        print(f"Schema error: {error.detected_version}")
    else:
        # Exhaustiveness check
        assert_never(error)
```

---

### Runtime vs Static Validation

Pydantic (runtime) and mypy (static) are complementary (per FR-159, FR-160, FR-161, FR-162, FR-163).

**Division of Responsibilities**:

**Pydantic** (Runtime Validation):
- Validates external data (JSON from export files)
- Enforces constraints (string length, date formats, required fields)
- Coerces types (string → datetime, int → float)
- Runs at parse time (every file load)

**mypy** (Static Type Checking):
- Validates internal code (function calls, variable assignments)
- Catches type errors before runtime (at development time)
- No runtime overhead (pure static analysis)
- Runs in CI/IDE (not in production)

**Example - Both Systems Together** (per FR-161):
```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal

MessageRole = Literal["user", "assistant", "system"]

class Message(BaseModel):
    """Message with both runtime (Pydantic) and static (mypy) validation."""

    model_config = ConfigDict(frozen=True)

    # mypy: Enforces role is MessageRole (compile-time)
    # Pydantic: Validates role is one of the literals (runtime)
    role: MessageRole

    # mypy: Enforces content is str (compile-time)
    # Pydantic: Validates content is non-empty (runtime)
    content: str = Field(min_length=1, max_length=100000)

    # mypy: Enforces timestamp is datetime (compile-time)
    # Pydantic: Coerces ISO 8601 string → datetime (runtime)
    timestamp: datetime

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Additional runtime validation beyond types."""
        if v not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {v}")
        return v

# Pydantic: Runtime validation (parses JSON, validates constraints)
msg_data = {"role": "user", "content": "Hello", "timestamp": "2024-01-15T10:30:00Z"}
msg = Message.model_validate(msg_data)

# mypy: Static validation (checks function call is type-safe)
def process_user_message(msg: Message) -> None:
    # mypy knows msg.role is MessageRole (not just str)
    # mypy knows msg.content is str
    # mypy knows msg.timestamp is datetime (not str)
    print(f"{msg.role}: {msg.content} at {msg.timestamp}")
```

**When to Use Each** (per FR-162):

| Scenario | Use Pydantic | Use mypy |
|----------|--------------|----------|
| Validating export file JSON | ✅ Required | ❌ N/A (external data) |
| Checking function parameter types | ❌ Not needed | ✅ Required |
| Enforcing string length limits | ✅ Required | ❌ Can't express |
| Catching typos in variable names | ❌ Not detected | ✅ Detected |
| Runtime type coercion (str → datetime) | ✅ Required | ❌ N/A (static) |
| IDE autocomplete | ❌ Indirect (via types) | ✅ Direct |
| Validate nested dict structure | ✅ Required | ❌ Limited |
| Detect unreachable code | ❌ Not detected | ✅ Detected |

**Avoid Redundant Runtime Checks** (per FR-163):
```python
# ❌ BAD: Redundant isinstance check (mypy already verifies this)
def handle_conversation(conv: Conversation) -> None:
    if not isinstance(conv, Conversation):  # Unnecessary!
        raise TypeError("Expected Conversation")
    print(conv.title)

# ✅ GOOD: Trust mypy's static verification
def handle_conversation(conv: Conversation) -> None:
    # mypy guarantees conv is Conversation
    print(conv.title)  # No runtime check needed

# ✅ GOOD: Use isinstance only for Union types (where mypy can't narrow)
def handle_result(result: Union[Conversation, ParseError]) -> None:
    if isinstance(result, Conversation):  # Necessary for type narrowing
        print(result.title)
    else:
        print(result.error_message)
```

---

## Multi-Provider Adapter Pattern

### Adapter Implementation Guidelines

Future adapters must implement ConversationProvider protocol while adapting provider-specific formats (per FR-164, FR-165, FR-166, FR-167).

**What MUST Be Preserved** (immutable across all adapters):
- Method signatures (all protocol methods)
- Exception contract (same exception types)
- Memory efficiency (streaming with Iterator)
- Thread safety (adapter instances thread-safe)
- Return types (must match protocol exactly)

**What CAN Vary** (adapter-specific):
- Parsing logic (ijson, xml.etree, csv.reader, etc.)
- Internal data structures
- Performance characteristics
- File format quirks handling
- Metadata extraction strategies

**Example - Future Anthropic Adapter**:
```python
class AnthropicAdapter:
    """Adapter for Claude export format (JSONL).

    Format differences from OpenAI:
    - JSONL (one JSON per line) instead of single JSON array
    - Different field names: 'claude_message' vs 'message'
    - Different role names: 'human'/'assistant' vs 'user'/'assistant'
    - No 'system' role in Claude v1

    But protocol contract is identical!
    """

    def __init__(self) -> None:
        """Stateless constructor (per FR-113, FR-164)."""
        pass

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[Conversation]:
        """Stream Claude conversations (JSONL format).

        Implementation differs from OpenAI:
        - Line-by-line parsing (JSONL)
        - Role mapping: 'human' → 'user'
        - Different JSON structure

        But returns same Iterator[Conversation] as OpenAI adapter!
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                try:
                    # Parse JSONL (one JSON object per line)
                    claude_data = json.loads(line)

                    # Convert Claude format → shared Conversation model
                    conv = self._convert_claude_to_conversation(claude_data)

                    if progress_callback and idx % 100 == 0:
                        progress_callback(idx + 1)

                    yield conv
                except (json.JSONDecodeError, ValidationError) as e:
                    if on_skip:
                        on_skip(claude_data.get('id', str(idx)), str(e))

    def _convert_claude_to_conversation(self, claude_data: dict) -> Conversation:
        """Convert Claude-specific format to shared Conversation model.

        Provider-specific quirks isolated here (per FR-174, FR-175).
        """
        # Map Claude roles to shared model
        messages = []
        for msg_data in claude_data.get('messages', []):
            role = self._normalize_role(msg_data['role'])  # 'human' → 'user'
            messages.append(Message(
                id=msg_data['id'],
                role=role,
                content=msg_data['content'],
                timestamp=datetime.fromisoformat(msg_data['timestamp'])
            ))

        return Conversation(
            id=claude_data['id'],
            title=claude_data.get('title', messages[0].content[:50] if messages else "Untitled"),
            created_at=datetime.fromisoformat(claude_data['created_at']),
            updated_at=datetime.fromisoformat(claude_data['updated_at']),
            messages=messages,
            metadata={
                "claude_model": claude_data.get('model', 'unknown'),
                "claude_workspace_id": claude_data.get('workspace_id'),
            }
        )

    def _normalize_role(self, claude_role: str) -> Literal["user", "assistant", "system"]:
        """Normalize Claude role names to shared model (per FR-171)."""
        mapping = {
            "human": "user",
            "assistant": "assistant",
            # Claude v1 has no 'system' role
        }
        return mapping.get(claude_role, "user")
```

---

### Shared Data Model Requirements

All adapters must populate required fields from provider-specific formats (per FR-169, FR-170, FR-171, FR-172, FR-173).

**Required Fields** (ALL providers):

**Conversation Model**:
```python
class Conversation(BaseModel):
    """Provider-agnostic conversation model.

    All adapters MUST populate these fields.
    """

    model_config = ConfigDict(frozen=True)

    # REQUIRED (per FR-169)
    id: str  # UUID or provider-specific ID
    title: str  # Conversation title (or generated default)
    created_at: datetime  # ISO 8601 timestamp
    updated_at: datetime  # ISO 8601 timestamp
    messages: list[Message]  # At least one message

    # OPTIONAL (per FR-172)
    metadata: dict[str, Any] = {}  # Provider-specific fields
```

**Message Model**:
```python
class Message(BaseModel):
    """Provider-agnostic message model."""

    model_config = ConfigDict(frozen=True)

    # REQUIRED (per FR-170)
    id: str  # UUID or provider-specific ID
    role: Literal["user", "assistant", "system"]  # Normalized (per FR-171)
    content: str  # Message text content
    timestamp: datetime  # ISO 8601 timestamp

    # OPTIONAL
    parent_id: Optional[str] = None  # For threading
    child_ids: list[str] = []  # For branching
    metadata: dict[str, Any] = {}  # Provider-specific fields
```

**Role Normalization** (per FR-171):
```python
# Provider-specific roles → Shared model
ROLE_MAPPINGS = {
    "OpenAI": {
        "user": "user",
        "assistant": "assistant",
        "system": "system",
    },
    "Anthropic Claude": {
        "human": "user",
        "assistant": "assistant",
        # No 'system' role in Claude v1
    },
    "Google Gemini": {
        "user": "user",
        "model": "assistant",
        # System instructions in separate field
    },
}
```

**Provider-Specific Metadata** (per FR-172):
```python
# OpenAI metadata
conv = Conversation(
    id="conv-123",
    title="Debugging Python",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    messages=[...],
    metadata={
        "openai_model": "gpt-4",
        "openai_conversation_template_id": "template-456",
        "openai_plugin_ids": ["plugin-789"],
    }
)

# Anthropic metadata
conv = Conversation(
    id="conv-abc",
    title="Writing Code",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    messages=[...],
    metadata={
        "claude_model": "claude-3-sonnet",
        "claude_workspace_id": "ws-xyz",
    }
)

# Google metadata
conv = Conversation(
    id="conv-def",
    title="Data Analysis",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    messages=[...],
    metadata={
        "gemini_model": "gemini-pro",
        "gemini_system_instruction": "You are a data analyst.",
    }
)
```

**Generating Defaults** (per FR-173):
```python
def _generate_default_title(messages: list[Message]) -> str:
    """Generate title when provider doesn't provide one (per FR-173)."""
    if not messages:
        return "Untitled Conversation"

    # Use first 50 characters of first user message
    first_user_msg = next((m for m in messages if m.role == "user"), None)
    if first_user_msg:
        return first_user_msg.content[:50].strip() + ("..." if len(first_user_msg.content) > 50 else "")

    # Fallback: first message content
    return messages[0].content[:50].strip() + ("..." if len(messages[0].content) > 50 else "")
```

---

### Provider-Specific Quirks Isolation

Adapters must isolate quirks in private methods, never exposing them to protocol (per FR-174, FR-175, FR-176, FR-177, FR-178).

**Quirk Isolation Strategy**:

**Layer 1: Private Quirk Handling** (adapter internals):
```python
class OpenAIAdapter:
    """OpenAI adapter isolating format quirks."""

    def stream_conversations(self, file_path: Path, ...) -> Iterator[Conversation]:
        """Public protocol method (quirk-free interface)."""
        with open(file_path, 'rb') as f:
            for conv_data in ijson.items(f, 'item'):
                # Delegate to quirk-handling method (per FR-174)
                yield self._parse_openai_conversation(conv_data)

    def _parse_openai_conversation(self, raw_data: dict) -> Conversation:
        """Private method isolating OpenAI quirks (per FR-177).

        OpenAI Format Quirks:
        1. Null 'title' field → Generate from messages
        2. Nested 'mapping' dict instead of 'messages' list
        3. Float timestamps (seconds since epoch) instead of ISO 8601
        4. Branching message tree (complex parent/child relationships)
        """

        # QUIRK 1: Handle null titles
        title = raw_data.get('title') or self._generate_title_from_messages(
            raw_data.get('mapping', {})
        )

        # QUIRK 2: Flatten message tree
        messages = self._flatten_openai_message_tree(raw_data.get('mapping', {}))

        # QUIRK 3: Convert float timestamps to datetime
        created_at = datetime.fromtimestamp(raw_data['create_time'], tz=timezone.utc)
        updated_at = datetime.fromtimestamp(raw_data['update_time'], tz=timezone.utc)

        # Return normalized Conversation model (per FR-175)
        return Conversation(
            id=raw_data['id'],
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata={
                "openai_model": raw_data.get('model', 'unknown'),
                "openai_moderation_results": raw_data.get('moderation_results', []),
            }
        )

    def _flatten_openai_message_tree(self, mapping: dict) -> list[Message]:
        """Flatten OpenAI's nested message tree structure (QUIRK 2).

        OpenAI stores messages in a dict keyed by message ID, with parent/child
        relationships. This flattens to a simple list in chronological order.
        """
        messages = []
        for msg_id, msg_node in mapping.items():
            msg_data = msg_node.get('message')
            if not msg_data or msg_data.get('author', {}).get('role') is None:
                continue  # Skip empty nodes

            messages.append(Message(
                id=msg_id,
                role=msg_data['author']['role'],
                content=self._extract_content(msg_data),
                timestamp=datetime.fromtimestamp(msg_data['create_time'], tz=timezone.utc),
                parent_id=msg_node.get('parent'),
                child_ids=msg_node.get('children', []),
            ))

        # Sort by timestamp (chronological order)
        messages.sort(key=lambda m: m.timestamp)
        return messages

    def _extract_content(self, msg_data: dict) -> str:
        """Extract text content from OpenAI message structure (QUIRK handling)."""
        content_parts = msg_data.get('content', {}).get('parts', [])
        return '\n'.join(str(part) for part in content_parts if part)
```

**Layer 2: Clean Protocol Interface** (no quirks visible):
```python
# Consumer (cognivault) sees normalized interface
adapter = OpenAIAdapter()  # Could swap with AnthropicAdapter seamlessly
for conv in adapter.stream_conversations(file_path):
    # conv is normalized Conversation model
    # No OpenAI-specific quirks visible (per FR-176)
    print(f"{conv.title}: {len(conv.messages)} messages")
    print(f"Created: {conv.created_at.isoformat()}")
```

**Format Change Absorption** (per FR-178):
```python
# If OpenAI changes export format (e.g., v2.0 schema):
class OpenAIAdapter:
    def _parse_openai_conversation(self, raw_data: dict) -> Conversation:
        """Adapt to format changes internally."""

        # Detect schema version (heuristic)
        if 'mapping' in raw_data:
            # Old format (v1.0)
            return self._parse_v1_format(raw_data)
        elif 'messages' in raw_data:
            # New format (v2.0) - absorbed internally
            return self._parse_v2_format(raw_data)
        else:
            raise ParseError("Unknown OpenAI export format")

    def _parse_v1_format(self, raw_data: dict) -> Conversation:
        """Parse OpenAI v1.0 format (nested mapping)."""
        ...

    def _parse_v2_format(self, raw_data: dict) -> Conversation:
        """Parse OpenAI v2.0 format (flat messages list)."""
        ...

# Protocol interface unchanged - consumers unaffected!
```

---

### Protocol Compliance Testing

All adapters must pass shared contract test suite (per FR-188, FR-189, FR-190, FR-191, FR-192).

**Contract Test Suite Structure**:
```python
# tests/contract/test_provider_protocol.py
import pytest
from echomine import OpenAIAdapter  # Future: AnthropicAdapter, GoogleAdapter

# All adapter implementations (per FR-192)
ADAPTERS = [
    OpenAIAdapter,
    # Future adapters automatically inherit tests by adding here
]

@pytest.fixture(params=ADAPTERS)
def adapter(request):
    """Fixture providing each adapter implementation."""
    return request.param()


# CONTRACT TEST 1: Memory Efficiency (per FR-190)
def test_memory_bounded(adapter, large_export_file):
    """Memory usage constant regardless of file size."""
    import tracemalloc

    tracemalloc.start()
    peak_before = tracemalloc.get_traced_memory()[1]

    count = 0
    for conv in adapter.stream_conversations(large_export_file):
        count += 1
        if count >= 1000:
            break

    peak_after = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    memory_delta_mb = (peak_after - peak_before) / (1024 * 1024)
    assert memory_delta_mb < 100, f"Memory grew by {memory_delta_mb}MB (should be constant)"


# CONTRACT TEST 2: Fail-Fast Errors (per FR-190)
def test_fail_fast(adapter, tmp_path):
    """FileNotFoundError raised immediately."""
    missing_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        iterator = adapter.stream_conversations(missing_file)
        next(iterator)


# CONTRACT TEST 3: Search Result Ordering (per FR-190)
def test_search_sorted_by_relevance(adapter, sample_export):
    """Results sorted by relevance_score descending."""
    query = SearchQuery(keywords=["test"], limit=10)
    results = list(adapter.search(sample_export, query))

    scores = [r.relevance_score for r in results]
    assert scores == sorted(scores, reverse=True)


# CONTRACT TEST 4: Thread Safety (per FR-190)
def test_thread_safe(adapter, sample_export):
    """Adapter instance safe to share across threads."""
    from threading import Thread

    results = []

    def worker():
        convs = list(adapter.stream_conversations(sample_export))
        results.append(len(convs))

    threads = [Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get same count
    assert len(set(results)) == 1


# CONTRACT TEST 5: Type Correctness (per FR-190)
def test_type_correctness(adapter):
    """Method signatures match protocol."""
    import inspect
    from echomine.protocols import ConversationProvider

    # Verify adapter implements protocol
    assert isinstance(adapter, ConversationProvider)

    # Check return type annotations
    sig = inspect.signature(adapter.stream_conversations)
    assert "Iterator" in str(sig.return_annotation)
```

**CI Integration** (per FR-191):
```yaml
# .github/workflows/contract-tests.yml
name: Contract Tests

on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: poetry install
      - name: Run Contract Tests
        run: |
          pytest tests/contract/ -v --tb=short
          # Fail build if ANY adapter fails ANY contract test (per FR-191)
```

**Adding New Adapters** (per FR-192):
```python
# When adding AnthropicAdapter, just add to list:
ADAPTERS = [
    OpenAIAdapter,
    AnthropicAdapter,  # ← Automatically runs all contract tests!
]

# Zero additional test code needed - adapter inherits full suite
```

---
