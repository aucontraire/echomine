# Gap Resolution: Priority 1 Critical Gaps

**Feature**: 001-ai-chat-parser
**Date**: 2025-11-22
**Status**: In Progress
**Total Gaps Addressed**: 17 items (Priority 1 - Pre-Implementation Blockers)

---

## 1. Type Safety & API Contract (5 items)

### CHK002, CHK019, CHK142: Complete Protocol Method Signatures

**Gap**: Are ConversationProvider protocol method signatures completely specified with all parameters, return types, and exceptions?

**Decision**:
Define complete method signatures for ALL ConversationProvider protocol methods with explicit types, no `Any` usage, and documented exception contracts.

**Complete Protocol Specification**:
```python
from typing import Protocol, Iterator, Optional, Callable
from pathlib import Path
from datetime import datetime

# Callback type aliases
ProgressCallback = Callable[[int], None]
"""Called with count of items processed. Used for progress indicators."""

OnSkipCallback = Callable[[str, str], None]
"""Called when entry is skipped. Args: (conversation_id, reason)."""


class ConversationProvider(Protocol):
    """Protocol for parsing AI conversation exports.

    All implementations MUST:
    - Stream conversations without loading entire file into memory
    - Be stateless (no instance variables modified after __init__)
    - Support context manager protocol for resource cleanup
    - Raise only public exceptions (EchomineError subclasses)
    - Be thread-safe for concurrent reads (but not concurrent iterator consumption)
    """

    def __init__(self) -> None:
        """Initialize adapter with no required parameters.

        Adapters MUST be stateless - all state passed via method parameters.
        Constructor MUST NOT raise exceptions.
        """
        ...

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[Conversation]:
        """Stream conversations from export file without loading entire file.

        Args:
            file_path: Absolute path to export file (must exist, must be readable)
            progress_callback: Optional callback invoked periodically with count of
                processed conversations. Called every 100 items OR every 100ms,
                whichever comes first. If None, no progress updates.
            on_skip: Optional callback invoked when malformed entry is skipped.
                Receives (conversation_id, reason). If None, skips are silent
                (only logged to library logger at WARNING level).

        Returns:
            Iterator yielding Conversation objects. Iterator guarantees:
            - Memory usage bounded (does not grow with file size)
            - Conversations yielded in file order (deterministic)
            - File handle closed when iteration completes OR when exception raised

        Raises:
            FileNotFoundError: Export file does not exist at file_path
            PermissionError: No read permission for export file
            ParseError: JSON syntax error, unable to parse file structure
            ValidationError: Conversation data fails Pydantic validation
            SchemaVersionError: Export schema version not supported by this adapter

        Notes:
            - Malformed entries are SKIPPED (not raised as exceptions)
            - Skipped entries trigger on_skip callback if provided
            - Iterator uses context manager internally for file cleanup
            - Safe for concurrent reads from multiple processes
            - NOT safe for concurrent consumption of same iterator
        """
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        *,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[SearchResult]:
        """Search conversations by keywords, title, date range, or limit.

        Args:
            file_path: Absolute path to export file
            query: Search criteria (keywords, title, date_from, date_to, limit)
            progress_callback: Optional progress updates (same semantics as stream_conversations)
            on_skip: Optional skip notification callback

        Returns:
            Iterator yielding SearchResult objects with:
            - conversation: Matched Conversation object
            - score: Relevance score (float, 0.0-1.0) if keywords specified, else 1.0
            - matched_message_ids: List of message IDs matching keywords (if applicable)

            Results are:
            - Ordered by relevance score DESC (if keywords specified)
            - Ordered by created_at DESC (if no keywords, title-only or date filtering)
            - Limited to query.limit items (if specified)

        Raises:
            Same exceptions as stream_conversations
            ValidationError: Invalid SearchQuery (e.g., date_from > date_to)

        Notes:
            - Empty keyword list returns ALL conversations (filtered by other criteria)
            - Limit applied AFTER scoring/sorting (top N results)
            - Memory usage bounded even with large result sets (streaming)
        """
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """Retrieve single conversation by ID.

        Args:
            file_path: Absolute path to export file
            conversation_id: Unique conversation identifier

        Returns:
            Conversation object if found, None if not found

        Raises:
            Same exceptions as stream_conversations (except ValidationError)

        Notes:
            - Streams through file until ID found (does not load entire file)
            - Returns first match (if duplicate IDs exist, undefined which returned)
            - Memory efficient (O(1) memory regardless of file size)
        """
        ...

    def __enter__(self) -> "ConversationProvider":
        """Context manager entry. Returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit. No resources to clean up (stateless adapter)."""
        pass
```

**Rationale**: Complete signatures eliminate ambiguity. Every parameter, return type, exception, and callback is explicitly documented. No room for misinterpretation.

**New Requirements**:
- **FR-215**: ConversationProvider protocol MUST define `stream_conversations` method with signature: `(file_path: Path, *, progress_callback: Optional[ProgressCallback] = None, on_skip: Optional[OnSkipCallback] = None) -> Iterator[Conversation]`
- **FR-216**: ConversationProvider protocol MUST define `search` method with signature: `(file_path: Path, query: SearchQuery, *, progress_callback: Optional[ProgressCallback] = None, on_skip: Optional[OnSkipCallback] = None) -> Iterator[SearchResult]`
- **FR-217**: ConversationProvider protocol MUST define `get_conversation_by_id` method with signature: `(file_path: Path, conversation_id: str) -> Optional[Conversation]`
- **FR-218**: All protocol methods MUST document ALL raised exceptions (FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError) in docstrings
- **FR-219**: Protocol MUST define type aliases for callbacks: `ProgressCallback = Callable[[int], None]` and `OnSkipCallback = Callable[[str, str], None]`
- **FR-220**: All protocol methods MUST use keyword-only arguments (after `*`) for optional parameters to prevent positional argument brittleness
- **FR-221**: Protocol documentation MUST specify memory guarantees, thread safety, and determinism for each method

---

### CHK013: Pydantic Model Configuration Requirements

**Gap**: Are Pydantic model configuration requirements complete (frozen=True, strict=True enforcement)?

**Decision**:
ALL Pydantic models representing conversation data MUST be frozen (immutable) and use strict validation. This is enforced via `model_config`.

**Required Pydantic Configuration**:
```python
from pydantic import BaseModel, ConfigDict

class Conversation(BaseModel):
    """Immutable conversation data."""
    model_config = ConfigDict(
        frozen=True,           # Immutability: prevents accidental modification
        strict=True,           # Strict validation: no type coercion
        extra="forbid",        # Reject unknown fields
        validate_assignment=True,  # Validate on field assignment (for non-frozen)
        arbitrary_types_allowed=False,  # Only Pydantic-compatible types
    )

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
    metadata: dict[str, Any] = {}


class Message(BaseModel):
    """Immutable message data."""
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = {}


class SearchQuery(BaseModel):
    """Mutable search query (not frozen - used for construction)."""
    model_config = ConfigDict(
        frozen=False,          # Mutable: users can modify queries
        strict=True,           # But still strict validation
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    keywords: list[str] = []
    title: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: Optional[int] = None
```

**Immutability Rules**:
- **Conversation, Message, SearchResult**: MUST be `frozen=True` (immutable after creation)
- **SearchQuery**: MAY be `frozen=False` (mutable for user convenience during query construction)
- **All models**: MUST use `strict=True` (no silent type coercion)
- **All models**: MUST use `extra="forbid"` (reject unknown fields, catch typos)

**Rationale**: Immutability prevents accidental data corruption. Strict validation catches type errors early. Forbidding extra fields prevents silent failures from typos.

**New Requirements**:
- **FR-222**: Conversation model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-223**: Message model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-224**: SearchResult model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-225**: SearchQuery model MAY use `frozen=False` for user convenience but MUST use `strict=True, extra="forbid"`
- **FR-226**: All Pydantic models MUST set `arbitrary_types_allowed=False` to prevent non-serializable types
- **FR-227**: Library MUST document immutability contract in all model docstrings

---

### CHK014: Type Annotation Requirements for ALL Public APIs

**Gap**: Are type annotation requirements specified for ALL library public APIs (no Any types, Protocol usage)?

**Decision**:
**Zero tolerance for `Any` in public API**. All public functions, methods, and classes MUST have complete type annotations. Use Union, Optional, Protocol, TypeVar, or Generic instead of Any.

**Type Annotation Policy**:
```python
# ✅ ALLOWED - Explicit types
def stream_conversations(
    file_path: Path,
    *,
    progress_callback: Optional[ProgressCallback] = None,
) -> Iterator[Conversation]:
    ...

# ✅ ALLOWED - Generic with constraints
T = TypeVar('T', Conversation, SearchResult)
def process_items(items: Iterator[T]) -> list[T]:
    ...

# ✅ ALLOWED - Protocol for callbacks
class ProgressCallback(Protocol):
    def __call__(self, count: int) -> None: ...

# ✅ ALLOWED - Union for multiple types
def parse_date(value: str | datetime) -> datetime:
    ...

# ✅ ALLOWED - Metadata dict (internal flexibility)
metadata: dict[str, Any] = {}  # OK for internal data bags

# ❌ FORBIDDEN - Any in function signatures
def parse_conversation(data: Any) -> Conversation:  # WRONG
    ...

# ❌ FORBIDDEN - Untyped parameters
def search(file_path, query):  # WRONG - missing types
    ...

# ❌ FORBIDDEN - Untyped returns
def get_conversation_by_id(file_path: Path, id: str):  # WRONG - no return type
    ...
```

**Exceptions** (where `Any` is permitted):
1. **Internal implementation details** (private functions starting with `_`)
2. **Metadata dictionaries** (`dict[str, Any]`) for provider-specific extensibility
3. **JSON parsing intermediate results** (before Pydantic validation)

**Enforcement**:
- CI MUST run `mypy --strict` on all public API modules
- Type coverage MUST be 100% for public API (measured by mypy)
- Pull requests with type errors MUST be rejected

**Rationale**: Type annotations are documentation, IDE autocomplete, and static analysis. Any defeats all these benefits. Explicit types catch bugs at development time.

**New Requirements**:
- **FR-228**: ALL public functions and methods MUST have complete type annotations for parameters and return types
- **FR-229**: Public API MUST NOT use `Any` type in function signatures (parameters or returns)
- **FR-230**: Public API MAY use `Any` only in: (1) metadata dictionaries (`dict[str, Any]`), (2) private implementation functions, (3) JSON parsing intermediate results
- **FR-231**: Library MUST enforce `mypy --strict` in CI pipeline for all public API modules
- **FR-232**: Library MUST achieve 100% type coverage for public API (measured by mypy)
- **FR-233**: Library MUST use Protocol for callback types instead of `Callable[..., Any]`

---

## 2. Multi-Provider Consistency (3 items)

### CHK057: Conversation Model Must Be Provider-Agnostic

**Gap**: Are Conversation model requirements provider-agnostic (no OpenAI-specific fields in shared models)?

**Decision**:
**Zero OpenAI-specific fields in shared models**. All provider-specific data goes in `metadata` dict. Shared models represent the **common subset** across all providers.

**Provider-Agnostic Data Model**:
```python
class Conversation(BaseModel):
    """Provider-agnostic conversation representation.

    This model represents the COMMON SUBSET of conversation data
    across all AI providers (OpenAI, Anthropic, Google, etc.).

    Provider-specific fields MUST be stored in metadata dict.
    """
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    # REQUIRED FIELDS (common across ALL providers)
    id: str
    """Unique conversation identifier. Format varies by provider but must be unique."""

    title: str
    """Conversation title. May be user-provided or AI-generated."""

    created_at: datetime
    """Conversation creation timestamp (ISO 8601, timezone-aware)."""

    updated_at: datetime
    """Last modification timestamp (ISO 8601, timezone-aware)."""

    messages: list[Message]
    """Chronologically ordered messages. Tree structure preserved via parent_id."""

    # OPTIONAL FIELD (provider-specific data)
    metadata: dict[str, Any] = {}
    """Provider-specific fields that don't map to common schema.

    Examples:
    - OpenAI: {"moderation_results": [...], "plugin_ids": [...]}
    - Anthropic: {"model_version": "claude-3", "token_count": 1234}
    - Google: {"safety_ratings": [...], "grounding_sources": [...]}

    Library consumers MUST NOT rely on specific metadata fields.
    Metadata is for informational/debugging purposes only.
    """


# ❌ ANTI-PATTERN - OpenAI-specific field in shared model
class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
    moderation_results: list[dict] = []  # ❌ OpenAI-specific!
    plugin_ids: list[str] = []  # ❌ OpenAI-specific!


# ✅ CORRECT - OpenAI-specific data in metadata
conversation = Conversation(
    id="...",
    title="...",
    created_at=...,
    updated_at=...,
    messages=[...],
    metadata={
        "moderation_results": [...],  # OpenAI-specific
        "plugin_ids": [...],  # OpenAI-specific
    }
)
```

**Provider-Specific Adapter Handling**:
```python
class OpenAIAdapter:
    def _convert_to_conversation(self, openai_data: dict) -> Conversation:
        """Convert OpenAI export to provider-agnostic Conversation."""
        return Conversation(
            id=openai_data["id"],
            title=openai_data["title"],
            created_at=datetime.fromisoformat(openai_data["create_time"]),
            updated_at=datetime.fromisoformat(openai_data["update_time"]),
            messages=self._convert_messages(openai_data["mapping"]),
            metadata={
                # Preserve OpenAI-specific fields
                "moderation_results": openai_data.get("moderation_results", []),
                "plugin_ids": openai_data.get("plugin_ids", []),
                "is_archived": openai_data.get("is_archived", False),
                "workspace_id": openai_data.get("workspace_id"),
            }
        )
```

**Rationale**: Provider-agnostic models enable adapter interchangeability. cognivault can ingest conversations from any provider without code changes. Metadata preserves provider-specific data for debugging.

**New Requirements**:
- **FR-234**: Conversation model MUST contain ONLY fields common to all AI providers (id, title, created_at, updated_at, messages)
- **FR-235**: Conversation model MUST NOT include provider-specific fields (moderation_results, plugin_ids, workspace_id, etc.)
- **FR-236**: Conversation model MUST provide `metadata: dict[str, Any]` field for provider-specific data
- **FR-237**: Adapter implementations MUST store provider-specific fields in metadata dict, NOT as top-level Conversation fields
- **FR-238**: Library documentation MUST warn consumers NOT to rely on specific metadata fields (not part of stable API)

---

### CHK058: Message Role Requirements Consistent with Multi-Provider Support

**Gap**: Are Message role requirements consistent with multi-provider support (OpenAI roles vs Claude/Gemini roles)?

**Decision**:
Use **normalized role names** in shared Message model. Adapters MUST map provider-specific roles to standard roles: `"user"`, `"assistant"`, `"system"`.

**Normalized Role Mapping**:
```python
from typing import Literal

MessageRole = Literal["user", "assistant", "system"]
"""Normalized message roles across all providers."""

class Message(BaseModel):
    """Provider-agnostic message representation."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    id: str
    role: MessageRole  # ONLY "user", "assistant", "system"
    content: str
    timestamp: datetime
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = {}


# Provider-specific role mappings
OPENAI_ROLE_MAP = {
    "user": "user",
    "assistant": "assistant",
    "system": "system",
}

ANTHROPIC_ROLE_MAP = {
    "human": "user",      # Claude uses "human" instead of "user"
    "assistant": "assistant",
    # Claude v1 has no system role - handle via metadata
}

GOOGLE_ROLE_MAP = {
    "user": "user",
    "model": "assistant",  # Gemini uses "model" instead of "assistant"
    "system": "system",
}


class AnthropicAdapter:
    def _convert_message(self, claude_msg: dict) -> Message:
        """Convert Claude message to normalized Message."""
        role = claude_msg["role"]  # "human" or "assistant"

        return Message(
            id=claude_msg["id"],
            role=ANTHROPIC_ROLE_MAP[role],  # Maps "human" -> "user"
            content=claude_msg["content"],
            timestamp=datetime.fromisoformat(claude_msg["timestamp"]),
            metadata={
                "original_role": role,  # Preserve original for debugging
            }
        )
```

**Role Normalization Rules**:
1. **Adapters MUST map provider roles to normalized roles**:
   - User messages: `"user"` (OpenAI: "user", Claude: "human", Gemini: "user")
   - Assistant messages: `"assistant"` (OpenAI: "assistant", Claude: "assistant", Gemini: "model")
   - System messages: `"system"` (OpenAI: "system", Claude: N/A, Gemini: "system")

2. **Adapters MUST preserve original role in metadata** (for debugging):
   ```python
   metadata={"original_role": "human"}
   ```

3. **Adapters MUST handle missing role types gracefully**:
   - Claude v1 has no "system" role → System instructions go in first message metadata
   - Some providers may add new roles → Store unknown roles in metadata, map to "user"

**Rationale**: Normalized roles enable provider-agnostic processing. cognivault can filter by role without knowing the source provider. Original roles preserved in metadata for debugging.

**New Requirements**:
- **FR-239**: Message model MUST use normalized role type: `Literal["user", "assistant", "system"]`
- **FR-240**: Adapters MUST map provider-specific roles to normalized roles: "human" → "user", "model" → "assistant"
- **FR-241**: Adapters MUST preserve original provider role in `metadata["original_role"]` field
- **FR-242**: Adapters MUST handle providers lacking certain role types (e.g., Claude lacking "system") by storing instructions in metadata
- **FR-243**: Library documentation MUST define role normalization mapping for each supported provider

---

### CHK059: Timestamp Format Requirements Consistent Across Providers

**Gap**: Are timestamp format requirements consistent across providers (all ISO 8601, timezone handling)?

**Decision**:
**All timestamps MUST be timezone-aware datetimes in UTC**. Adapters convert provider-specific formats to ISO 8601 UTC datetime objects.

**Timestamp Normalization**:
```python
from datetime import datetime, timezone

class Conversation(BaseModel):
    created_at: datetime
    """Conversation creation timestamp.

    MUST be timezone-aware datetime in UTC.
    Stored as ISO 8601 string when serialized.
    """

    updated_at: datetime
    """Last modification timestamp.

    MUST be timezone-aware datetime in UTC.
    Stored as ISO 8601 string when serialized.
    """


class Message(BaseModel):
    timestamp: datetime
    """Message creation timestamp.

    MUST be timezone-aware datetime in UTC.
    Stored as ISO 8601 string when serialized.
    """


# Provider-specific timestamp parsing
class OpenAIAdapter:
    def _parse_timestamp(self, unix_timestamp: float) -> datetime:
        """Convert OpenAI Unix timestamp to UTC datetime.

        OpenAI uses Unix timestamps (seconds since epoch).
        """
        return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


class AnthropicAdapter:
    def _parse_timestamp(self, iso_string: str) -> datetime:
        """Convert Claude ISO 8601 string to UTC datetime.

        Claude uses ISO 8601 strings with timezone.
        """
        dt = datetime.fromisoformat(iso_string)

        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to UTC
        return dt.astimezone(timezone.utc)
```

**Timestamp Handling Rules**:
1. **ALL datetime fields MUST be timezone-aware** (never naive datetimes)
2. **ALL datetime fields MUST be normalized to UTC** before creating Conversation/Message
3. **Adapters MUST convert provider formats to UTC**:
   - Unix timestamps (OpenAI) → `datetime.fromtimestamp(ts, tz=timezone.utc)`
   - ISO 8601 strings (Claude) → `datetime.fromisoformat(s).astimezone(timezone.utc)`
   - RFC 3339 strings (Google) → Parse and convert to UTC

4. **Pydantic serialization uses ISO 8601**:
   ```python
   conversation.model_dump_json()
   # {"created_at": "2024-01-15T10:30:00Z", ...}
   ```

5. **Library MUST reject naive datetimes** via Pydantic validator:
   ```python
   from pydantic import field_validator

   class Conversation(BaseModel):
       created_at: datetime

       @field_validator('created_at', 'updated_at')
       @classmethod
       def validate_timezone_aware(cls, v: datetime) -> datetime:
           if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
               raise ValueError(f"Timestamp must be timezone-aware: {v}")
           return v.astimezone(timezone.utc)  # Normalize to UTC
   ```

**Rationale**: Timezone-aware UTC timestamps eliminate ambiguity. cognivault can compare timestamps across providers without worrying about timezone conversions. ISO 8601 is the standard for API serialization.

**New Requirements**:
- **FR-244**: ALL datetime fields (created_at, updated_at, timestamp) MUST be timezone-aware Python datetime objects
- **FR-245**: ALL datetime fields MUST be normalized to UTC timezone before creating Conversation/Message objects
- **FR-246**: Pydantic models MUST include field validators rejecting naive datetimes (no timezone)
- **FR-247**: Adapters MUST convert provider-specific timestamp formats (Unix, ISO 8601, RFC 3339) to UTC datetime objects
- **FR-248**: Pydantic JSON serialization MUST output timestamps as ISO 8601 strings with 'Z' suffix (UTC indicator)

---

## 3. Critical Ambiguities & Conflicts (3 items)

### CHK133: FR-004 (Skip Malformed) vs FR-033 (Fail Fast) Conflict

**Gap**: Is the relationship between FR-004 (skip malformed entries) and FR-033 (fail fast, no retries) clarified?

**Decision**:
**"Fail fast" applies to operational errors. "Skip malformed" applies to data quality issues.**

**Clear Distinction**:

| Error Type | Behavior | Exception | Retry? | Example |
|------------|----------|-----------|--------|---------|
| **Operational Error** | Fail fast | Raise exception immediately | No | File not found, permission denied, disk full |
| **Data Quality Issue** | Skip & continue | Log warning, invoke on_skip callback | N/A | Missing field, invalid date, malformed JSON entry |

**Implementation Pattern**:
```python
def stream_conversations(
    file_path: Path,
    *,
    on_skip: Optional[OnSkipCallback] = None,
) -> Iterator[Conversation]:
    # Operational errors: FAIL FAST
    if not file_path.exists():
        raise FileNotFoundError(f"Export file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            # Data quality issues: SKIP & CONTINUE
            for idx, line in enumerate(f):
                try:
                    data = json.loads(line)
                    conversation = Conversation.model_validate(data)
                    yield conversation
                except (json.JSONDecodeError, ValidationError) as e:
                    # Data quality issue: Skip this entry
                    conv_id = data.get("id", f"line-{idx}") if data else f"line-{idx}"
                    logger.warning(f"Skipped malformed entry {conv_id}: {e}")
                    if on_skip:
                        on_skip(conv_id, str(e))
                    # Continue to next entry (don't raise)
                    continue

    except PermissionError:
        # Operational error: Fail fast
        raise PermissionError(f"Cannot read {file_path}: permission denied")
```

**Fail Fast Scenarios** (raise immediately):
- File does not exist
- No read permission
- Entire file is corrupt (not valid JSON/JSONL)
- Unsupported schema version
- Out of disk space (when writing exports)

**Skip & Continue Scenarios** (log warning, continue):
- Single conversation entry has malformed JSON
- Single conversation missing required field
- Single conversation has invalid date format
- Single message has unsupported role

**Rationale**: Operational errors are unrecoverable (user must fix). Data quality issues are recoverable (skip bad entries, process good ones). This maximizes successful data ingestion while failing fast on real problems.

**New Requirements**:
- **FR-249**: Library MUST fail fast (raise exception immediately) for operational errors: file access, permissions, disk space, schema version
- **FR-250**: Library MUST skip & continue for data quality issues: malformed entries, missing fields, invalid formats within individual conversations
- **FR-251**: Library MUST distinguish "fail fast" (operational) from "skip malformed" (data quality) in documentation
- **FR-252**: Skipped entries MUST trigger on_skip callback (if provided) and MUST be logged at WARNING level
- **FR-253**: Library MUST NOT retry any operation (operational or data quality) - fail fast means single attempt

---

### CHK137: FR-003 (Streaming) vs FR-008 (Relevance Ranking) Conflict

**Gap**: Do FR-003 (stream without loading full file) and FR-008 (rank by relevance) conflict? Ranking requires seeing all results.

**Decision**:
**Use streaming relevance scoring with bounded memory**. Rank results using TF-IDF computed during streaming pass, then yield top N results.

**Two-Pass Streaming Solution**:
```python
def search(
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[ProgressCallback] = None,
) -> Iterator[SearchResult]:
    """Search with streaming relevance ranking.

    Memory usage: O(result_count) not O(file_size)
    """

    if not query.keywords:
        # No keywords: Simple filtering, stream directly
        yield from _stream_filter(file_path, query, progress_callback)
        return

    # Keywords specified: Need relevance ranking
    # Pass 1: Build TF-IDF index (memory-efficient streaming)
    tfidf = TFIDFScorer()
    conversations = []

    for conv in _stream_filter(file_path, query, progress_callback):
        score = tfidf.score(conv, query.keywords)
        if score > 0:  # Only keep matching conversations
            conversations.append(SearchResult(
                conversation=conv,
                score=score,
                matched_message_ids=tfidf.get_matched_message_ids(conv, query.keywords),
            ))

    # Pass 2: Sort by score and yield (memory bounded to matching results)
    conversations.sort(key=lambda r: r.score, reverse=True)

    limit = query.limit or len(conversations)
    for result in conversations[:limit]:
        yield result


def _stream_filter(
    file_path: Path,
    query: SearchQuery,
    progress_callback: Optional[ProgressCallback],
) -> Iterator[Conversation]:
    """Stream conversations applying date/title filters.

    Memory usage: O(1) - true streaming
    """
    adapter = OpenAIAdapter()

    for conv in adapter.stream_conversations(file_path, progress_callback=progress_callback):
        # Apply filters
        if query.title and query.title.lower() not in conv.title.lower():
            continue
        if query.date_from and conv.created_at < query.date_from:
            continue
        if query.date_to and conv.created_at > query.date_to:
            continue

        yield conv
```

**Memory Analysis**:
- **Without keywords**: O(1) memory (true streaming, no buffering)
- **With keywords**: O(matching_results) memory (buffer only matching conversations)
- **Not O(file_size)**: Rejected conversations are not buffered

**Trade-offs**:
- **Pro**: Memory bounded (only matching results buffered, not entire file)
- **Pro**: Still faster than loading full file (rejected conversations never buffered)
- **Con**: Keyword search requires buffering matching results for sorting
- **Con**: Two passes through file (filtering + scoring)

**Alternative Considered**: Approximate top-K ranking (streaming algorithms). **Rejected** because complexity outweighs benefit for v1.0. Current solution is simple and handles realistic file sizes (10K conversations = ~10MB memory for matching results).

**Rationale**: This resolves the conflict. Streaming is preserved (no full file load). Relevance ranking is preserved (TF-IDF scoring). Memory bounded to matching results (typically much smaller than full file).

**New Requirements**:
- **FR-254**: Search with keywords MUST use two-pass streaming: (1) filter and score, (2) sort and yield
- **FR-255**: Search with keywords MUST buffer only matching conversations in memory (not entire file)
- **FR-256**: Search without keywords MUST use single-pass streaming (true O(1) memory)
- **FR-257**: Search memory usage MUST be O(matching_result_count), NOT O(file_size)
- **FR-258**: Library documentation MUST document memory trade-offs for keyword vs non-keyword search

---

### CHK138: Constitution Principle V (YAGNI) vs Principle VII (Multi-Provider) Conflict

**Gap**: Do Constitution Principle V (YAGNI - don't build features before needed) and Principle VII (Multi-Provider Pattern - design for multiple providers) conflict?

**Decision**:
**Implement Protocol abstraction NOW (not YAGNI). Implement only OpenAI adapter NOW (YAGNI). Add future adapters when needed.**

**Resolution**:
- **Build abstraction**: ConversationProvider Protocol ✅ (do now)
- **Build test suite**: Protocol compliance tests ✅ (do now)
- **Build one adapter**: OpenAIAdapter ✅ (do now)
- **Don't build adapters**: AnthropicAdapter, GoogleAdapter ❌ (wait until needed)

**Why This Resolves Conflict**:
1. **Abstraction is cheap**: Protocol is just a type definition, no runtime cost
2. **Abstraction prevents rework**: Designing protocol now avoids refactoring OpenAIAdapter later
3. **Adapters are expensive**: Implementing Anthropic/Google adapters requires export format research, testing, maintenance
4. **Adapters wait until needed**: YAGNI applies to concrete implementations, not abstractions

**Implementation Strategy**:
```python
# ✅ DO NOW: Define protocol (cheap abstraction)
class ConversationProvider(Protocol):
    def stream_conversations(...) -> Iterator[Conversation]: ...
    def search(...) -> Iterator[SearchResult]: ...
    def get_conversation_by_id(...) -> Optional[Conversation]: ...

# ✅ DO NOW: Implement OpenAI adapter (needed immediately)
class OpenAIAdapter:
    """Adapter for OpenAI ChatGPT export format (JSON)."""
    def stream_conversations(...) -> Iterator[Conversation]:
        # Implementation for OpenAI format
        ...

# ✅ DO NOW: Protocol compliance tests (cheap, validates abstraction)
@pytest.fixture(params=[OpenAIAdapter])
def adapter(request):
    return request.param()

def test_stream_conversations_contract(adapter):
    """All adapters must pass this test."""
    ...

# ❌ DON'T DO NOW: Future adapters (expensive, not needed yet)
# class AnthropicAdapter:  # Wait until user requests Claude support
#     ...
# class GoogleAdapter:  # Wait until user requests Gemini support
#     ...
```

**When to Add Future Adapters**:
- **Trigger**: User/cognivault explicitly requests Claude or Gemini support
- **Not before**: Don't implement speculatively

**Rationale**: Protocol abstraction has near-zero cost and prevents expensive refactoring. Concrete adapter implementations are expensive (research, testing, maintenance) and should wait until needed. This satisfies both YAGNI (no unused code) and Multi-Provider Pattern (correct abstraction).

**New Requirements**:
- **FR-259**: Library MUST define ConversationProvider Protocol in v1.0 even with only one adapter
- **FR-260**: Library MUST implement only OpenAI adapter in v1.0 (no Anthropic/Google adapters until explicitly requested)
- **FR-261**: Library MUST include protocol compliance test suite that all current and future adapters must pass
- **FR-262**: Library documentation MUST explain multi-provider architecture and how to add future adapters
- **FR-263**: Future adapter implementations MUST be added only when users explicitly request support for that provider

---

## 4. Core Data Model Clarifications (3 items)

### CHK038: "Malformed JSON Entry" Precisely Defined

**Gap**: Is "malformed JSON entry" precisely defined (syntax errors, missing required fields, schema violations)?

**Decision**:
Define **three categories of malformed entries** with specific handling for each.

**Malformed Entry Categories**:

| Category | Definition | Examples | Handling |
|----------|------------|----------|----------|
| **1. JSON Syntax Error** | Invalid JSON syntax | Missing quote, trailing comma, invalid escape | Skip entry, log warning, continue |
| **2. Schema Violation** | Valid JSON but missing required fields | No "id" field, no "title" field | Skip entry, log warning, continue |
| **3. Validation Failure** | Has required fields but invalid values | Invalid date format, empty ID, invalid role | Skip entry, log warning, continue |

**Implementation**:
```python
def stream_conversations(
    file_path: Path,
    *,
    on_skip: Optional[OnSkipCallback] = None,
) -> Iterator[Conversation]:
    with open(file_path, 'r') as f:
        for idx, line in enumerate(f):
            try:
                # Category 1: JSON syntax error
                data = json.loads(line)
            except json.JSONDecodeError as e:
                error_msg = f"JSON syntax error at line {e.lineno}: {e.msg}"
                logger.warning(f"Skipped entry at line {idx}: {error_msg}")
                if on_skip:
                    on_skip(f"line-{idx}", error_msg)
                continue

            try:
                # Category 2 & 3: Schema violation or validation failure
                conversation = Conversation.model_validate(data)
                yield conversation

            except ValidationError as e:
                conv_id = data.get("id", f"line-{idx}")

                # Categorize validation failure
                missing_fields = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
                invalid_values = [err["loc"][0] for err in e.errors() if err["type"] != "missing"]

                if missing_fields:
                    # Category 2: Schema violation
                    error_msg = f"Missing required fields: {missing_fields}"
                else:
                    # Category 3: Validation failure
                    error_msg = f"Invalid values in fields: {invalid_values}"

                logger.warning(f"Skipped conversation '{conv_id}': {error_msg}")
                if on_skip:
                    on_skip(conv_id, error_msg)
                continue
```

**Specific Examples**:

**Category 1: JSON Syntax Error**
```json
{"id": "123", "title": "Test",  // Missing closing brace - SYNTAX ERROR
```
→ Skip, log: "JSON syntax error at line 1: Expecting '}'"

**Category 2: Schema Violation**
```json
{"id": "123", "created_at": "2024-01-15T10:00:00Z"}
```
→ Skip, log: "Missing required fields: ['title', 'updated_at', 'messages']"

**Category 3: Validation Failure**
```json
{
  "id": "",
  "title": "Test",
  "created_at": "invalid-date",
  "updated_at": "2024-01-15T10:00:00Z",
  "messages": []
}
```
→ Skip, log: "Invalid values in fields: ['id', 'created_at']"

**Rationale**: Precise categorization helps users understand what's wrong. Different categories may require different fixes (syntax errors = file corruption, schema violations = wrong export version, validation failures = data quality issues).

**New Requirements**:
- **FR-264**: Library MUST categorize malformed entries as: (1) JSON syntax errors, (2) schema violations (missing required fields), (3) validation failures (invalid field values)
- **FR-265**: Library MUST skip all three categories of malformed entries and continue processing (not raise exceptions)
- **FR-266**: Library MUST log warnings for each skipped entry with category-specific error messages
- **FR-267**: on_skip callback MUST receive conversation ID (or "line-N" if ID unavailable) and category-specific error message
- **FR-268**: Library documentation MUST provide examples of each malformed entry category and expected handling

---

### CHK041: "Conversation Metadata" Enumerated

**Gap**: Is "conversation metadata" enumerated (which fields exactly: title, ID, timestamps - anything else)?

**Decision**:
Define **required conversation metadata fields** (common across providers) and **optional metadata dict** (provider-specific).

**Complete Conversation Metadata Specification**:
```python
class Conversation(BaseModel):
    """Complete conversation metadata and message content."""

    # === REQUIRED METADATA (common across all providers) ===

    id: str
    """Unique conversation identifier.

    - MUST be unique within export file
    - Format varies by provider (UUID, sequential ID, etc.)
    - MUST be non-empty string
    """

    title: str
    """Conversation title.

    - MAY be user-provided or AI-generated
    - MUST be non-empty string
    - MAY contain any UTF-8 characters
    - No maximum length enforced (but UI may truncate display)
    """

    created_at: datetime
    """Conversation creation timestamp.

    - MUST be timezone-aware datetime in UTC
    - Represents when conversation was first created
    - Immutable (does not change with edits)
    """

    updated_at: datetime
    """Last modification timestamp.

    - MUST be timezone-aware datetime in UTC
    - Represents last message addition, edit, or metadata change
    - MUST be >= created_at
    """

    messages: list[Message]
    """All messages in conversation, chronologically ordered.

    - MUST be non-empty (conversations with zero messages are invalid)
    - Ordered by timestamp (earliest first)
    - Tree structure preserved via Message.parent_id
    """

    # === OPTIONAL METADATA (provider-specific, not in stable API) ===

    metadata: dict[str, Any] = {}
    """Provider-specific metadata not common across all providers.

    Common examples:
    - OpenAI: moderation_results, plugin_ids, is_archived, workspace_id
    - Anthropic: model_version, token_count
    - Google: safety_ratings, grounding_sources

    ⚠️ WARNING: Library consumers MUST NOT rely on specific metadata fields.
    Metadata structure is provider-specific and not part of stable API.
    Use for debugging/informational purposes only.
    """
```

**What is NOT Included**:
- **Message content**: Not metadata (in `messages` field)
- **Search ranking scores**: Not metadata (in `SearchResult.score`)
- **File-level information**: Not conversation metadata (file size, export date)

**Rationale**: Explicit enumeration eliminates ambiguity. "Metadata" term is overloaded - this clarifies exactly what's included in Conversation object.

**New Requirements**:
- **FR-269**: Conversation metadata MUST include exactly five required fields: id, title, created_at, updated_at, messages
- **FR-270**: Conversation id MUST be non-empty string, unique within export file
- **FR-271**: Conversation title MUST be non-empty string, MAY contain any UTF-8 characters
- **FR-272**: Conversation created_at and updated_at MUST be timezone-aware datetime in UTC
- **FR-273**: Conversation updated_at MUST be >= created_at (Pydantic validator enforced)
- **FR-274**: Conversation messages MUST be non-empty list (conversations with zero messages are invalid)
- **FR-275**: Conversation metadata dict is for provider-specific fields only, NOT part of stable API

---

### CHK042: "Preserve Message Tree Structures" Clarified

**Gap**: Is "preserve message tree structures" clarified (in-memory representation, serialization format, API access patterns)?

**Decision**:
Represent tree structure using **parent_id references** (adjacency list). Provide **tree navigation utilities** for library consumers.

**Tree Structure Representation**:
```python
class Message(BaseModel):
    """Message with tree structure via parent_id."""

    id: str
    """Unique message identifier within conversation."""

    parent_id: Optional[str] = None
    """ID of parent message in conversation tree.

    - None for root messages (conversation starters)
    - References another message's ID for branched messages
    - MUST reference valid message ID within same conversation (validated)
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = {}


class Conversation(BaseModel):
    """Conversation with tree-structured messages."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    messages: list[Message]
    """Messages in chronological order (tree structure via parent_id)."""

    # Tree navigation helpers
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Find message by ID."""
        return next((m for m in self.messages if m.id == message_id), None)

    def get_root_messages(self) -> list[Message]:
        """Get all root messages (parent_id is None)."""
        return [m for m in self.messages if m.parent_id is None]

    def get_children(self, message_id: str) -> list[Message]:
        """Get all direct children of a message."""
        return [m for m in self.messages if m.parent_id == message_id]

    def get_thread(self, message_id: str) -> list[Message]:
        """Get message and all ancestors up to root."""
        thread = []
        current = self.get_message_by_id(message_id)

        while current:
            thread.insert(0, current)  # Prepend (oldest first)
            current = self.get_message_by_id(current.parent_id) if current.parent_id else None

        return thread

    def get_all_threads(self) -> list[list[Message]]:
        """Get all conversation threads (root-to-leaf paths)."""
        threads = []

        def build_threads(msg: Message, path: list[Message]):
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
```

**Tree Serialization (JSON)**:
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
      "timestamp": "2024-01-15T10:00:00Z"
    },
    {
      "id": "msg-2",
      "parent_id": "msg-1",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2024-01-15T10:01:00Z"
    },
    {
      "id": "msg-3",
      "parent_id": "msg-1",
      "role": "assistant",
      "content": "Alternative response",
      "timestamp": "2024-01-15T10:01:30Z"
    }
  ]
}
```

**Tree Visualization Example**:
```
msg-1 (user: "Hello")
├── msg-2 (assistant: "Hi! How can I help?")
└── msg-3 (assistant: "Alternative response")
```

**cognivault Integration Pattern**:
```python
# Ingest conversation preserving tree structure
conversation = adapter.get_conversation_by_id(file_path, "conv-123")

# Get all conversation threads
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

**Rationale**: Parent_id adjacency list is simple and standard. Helper methods make tree navigation easy for library consumers. JSON serialization is flat (no nested objects) for easier parsing.

**New Requirements**:
- **FR-276**: Message tree structure MUST be represented using parent_id references (adjacency list pattern)
- **FR-277**: Message parent_id MUST reference valid message ID within same conversation (Pydantic validator enforced)
- **FR-278**: Conversation MUST provide tree navigation helper methods: get_root_messages(), get_children(), get_thread(), get_all_threads()
- **FR-279**: JSON serialization MUST use flat message list (not nested objects) with parent_id references
- **FR-280**: Library documentation MUST include tree structure examples and navigation patterns

---

## 5. Exception Handling Clarity (2 items)

### CHK077: Handling Malformed Entries Mid-Stream

**Gap**: Are requirements defined for handling malformed entries mid-stream (log warning, skip, continue - documented in library API)?

**Decision**:
**Skip malformed entries, invoke on_skip callback, log warning, continue streaming**. This is the documented behavior in library API.

**Complete Malformed Entry Handling**:
```python
def stream_conversations(
    file_path: Path,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    on_skip: Optional[OnSkipCallback] = None,
) -> Iterator[Conversation]:
    """Stream conversations, skipping malformed entries.

    Malformed Entry Handling:
    1. Skip entry (do not yield, do not raise exception)
    2. Log warning with conversation ID and error reason
    3. Invoke on_skip callback if provided
    4. Continue to next entry

    This ensures maximum data recovery from partially corrupt files.
    """
    logger = logging.getLogger(__name__)

    with open(file_path, 'r') as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
                conversation = Conversation.model_validate(data)

                # Success: yield conversation
                yield conversation

                # Update progress
                if progress_callback and (idx + 1) % 100 == 0:
                    progress_callback(idx + 1)

            except (json.JSONDecodeError, ValidationError) as e:
                # Malformed entry: skip and continue
                conv_id = data.get("id", f"line-{idx}") if isinstance(data, dict) else f"line-{idx}"
                error_reason = str(e)

                # 1. Log warning
                logger.warning(
                    f"Skipped malformed conversation '{conv_id}' at line {idx}: {error_reason}",
                    extra={
                        "conversation_id": conv_id,
                        "line_number": idx,
                        "error_type": type(e).__name__,
                        "error_reason": error_reason,
                    }
                )

                # 2. Invoke callback
                if on_skip:
                    on_skip(conv_id, error_reason)

                # 3. Continue (don't raise, don't stop iteration)
                continue
```

**Library Consumer Pattern**:
```python
# cognivault tracking skipped entries
skipped_entries = []

def track_skips(conversation_id: str, reason: str):
    skipped_entries.append({"id": conversation_id, "reason": reason})
    print(f"⚠️  Skipped {conversation_id}: {reason}")

adapter = OpenAIAdapter()
successful = 0

for conversation in adapter.stream_conversations(
    file_path,
    on_skip=track_skips,
):
    cognivault.ingest(conversation)
    successful += 1

# Summary
print(f"✅ Successfully ingested: {successful}")
print(f"⚠️  Skipped entries: {len(skipped_entries)}")
for entry in skipped_entries:
    print(f"   - {entry['id']}: {entry['reason']}")
```

**Rationale**: Skipping malformed entries maximizes data recovery. cognivault can ingest 9,990 good conversations even if 10 are corrupt. on_skip callback gives visibility into what was skipped.

**New Requirements**:
- **FR-281**: stream_conversations MUST skip malformed entries (JSON syntax errors, validation failures) without raising exceptions
- **FR-282**: Skipped entries MUST be logged at WARNING level with conversation ID, line number, error type, and reason
- **FR-283**: Skipped entries MUST invoke on_skip callback (if provided) with conversation ID and error reason
- **FR-284**: Skipped entries MUST NOT stop iteration (continue processing remaining conversations)
- **FR-285**: Library documentation MUST include example of tracking skipped entries via on_skip callback

---

### CHK134: "Library Consumers MUST Catch Exceptions" Contract Clarity

**Gap**: Is the "library consumers MUST catch exceptions" contract ambiguous (which exceptions are guaranteed stable API)?

**Decision**:
Define **public exception API contract** explicitly. Library consumers MUST catch these exceptions and ONLY these exceptions.

**Public Exception API Contract**:
```python
# === PUBLIC EXCEPTIONS (stable API, library consumers MUST catch) ===

class EchomineError(Exception):
    """Base class for all Echomine library exceptions.

    Library consumers catching this exception will catch ALL operational
    errors from the library.

    DO NOT CATCH: KeyboardInterrupt, SystemExit, MemoryError, AssertionError
    """
    pass


class ParseError(EchomineError):
    """Export file parsing failed.

    Raised when:
    - JSON syntax error in file (not individual entry)
    - File structure does not match expected format (not JSONL, not JSON array)
    - File is corrupted and cannot be read

    NOT raised for: Individual malformed entries (those are skipped)
    """
    pass


class ValidationError(EchomineError, ValueError):
    """Conversation data validation failed.

    Raised when:
    - Pydantic model validation fails (wrong types, missing fields)
    - Invalid date format
    - Invalid conversation/message structure

    Subclasses ValueError for backward compatibility.
    """
    pass


class SchemaVersionError(EchomineError):
    """Export schema version not supported.

    Raised when:
    - Detected schema version is newer than library supports
    - Detected schema version is older and incompatible

    NOT raised for: Unknown schema (library attempts to parse anyway)
    """
    pass


# Standard Python exceptions (re-raised as-is, NOT wrapped)
# - FileNotFoundError: Export file does not exist
# - PermissionError: No read permission for export file
# - OSError: Disk errors, file system issues


# === LIBRARY CONSUMER EXCEPTION HANDLING PATTERN ===

from echomine import OpenAIAdapter, EchomineError

try:
    adapter = OpenAIAdapter()

    for conversation in adapter.stream_conversations(file_path):
        cognivault.ingest(conversation)

except EchomineError as e:
    # All library operational errors
    logger.error(f"Echomine error: {e}")
    # Handle: display error to user, retry with different file, etc.

except (FileNotFoundError, PermissionError) as e:
    # Filesystem errors (not wrapped)
    logger.error(f"File access error: {e}")
    # Handle: prompt user for correct file path, check permissions

except Exception as e:
    # Unexpected errors (library bugs, system issues)
    logger.exception(f"Unexpected error: {e}")
    # Handle: report bug, crash gracefully
    raise  # Re-raise unexpected errors


# === EXCEPTIONS LIBRARY CONSUMERS MUST NOT CATCH ===

# DON'T catch KeyboardInterrupt (user cancellation)
# DON'T catch SystemExit (shutdown signals)
# DON'T catch MemoryError (system-level, can't recover)
# DON'T catch AssertionError (library bugs, should crash)
# DON'T catch BaseException (too broad, catches system exceptions)
```

**Exception Stability Guarantee**:
| Exception | Stable API? | Can Appear in Future Versions? | Consumer Must Catch? |
|-----------|-------------|-------------------------------|----------------------|
| `EchomineError` | ✅ Yes | N/A (base class) | ✅ Yes |
| `ParseError` | ✅ Yes | New subclasses may be added | ✅ Yes (via EchomineError) |
| `ValidationError` | ✅ Yes | New validation rules may appear | ✅ Yes (via EchomineError) |
| `SchemaVersionError` | ✅ Yes | Unlikely to change | ✅ Yes (via EchomineError) |
| `FileNotFoundError` | ✅ Yes (Python stdlib) | No | ✅ Yes |
| `PermissionError` | ✅ Yes (Python stdlib) | No | ✅ Yes |
| Other exceptions | ❌ No (bugs) | Should not appear | ❌ No (let crash) |

**Rationale**: Explicit contract eliminates ambiguity. Library consumers know exactly what to catch. Catching EchomineError base class future-proofs code against new exception types.

**New Requirements**:
- **FR-286**: Library public exception API MUST consist of: EchomineError (base), ParseError, ValidationError, SchemaVersionError
- **FR-287**: Library MUST re-raise standard Python exceptions as-is (FileNotFoundError, PermissionError, OSError) without wrapping
- **FR-288**: Library documentation MUST include exception handling example showing correct pattern
- **FR-289**: Future library versions MAY add new EchomineError subclasses (consumers catching EchomineError are forward-compatible)
- **FR-290**: Library MUST guarantee exception API stability (listed exceptions will not be removed or renamed in MAJOR version)

---

## Summary: Priority 1 Gap Resolution

**Total Gaps Resolved**: 17
**New Functional Requirements**: FR-215 through FR-290 (76 requirements)

**Breakdown by Category**:
1. **Type Safety & API Contract** (5 gaps): FR-215 to FR-233 (19 requirements)
2. **Multi-Provider Consistency** (3 gaps): FR-234 to FR-248 (15 requirements)
3. **Critical Ambiguities & Conflicts** (3 gaps): FR-249 to FR-263 (15 requirements)
4. **Core Data Model Clarifications** (3 gaps): FR-264 to FR-280 (17 requirements)
5. **Exception Handling Clarity** (2 gaps): FR-281 to FR-290 (10 requirements)

**Artifacts to Update**:
- ✅ spec.md (add FR-215 to FR-290)
- ✅ contracts/conversation_provider_protocol.py (add complete method signatures)
- ✅ data-model.md (add Pydantic config, tree structure examples)
- ✅ quickstart.md (add exception handling examples, tree navigation patterns)
- ✅ checklists/library-api.md (mark CHK002, CHK013, CHK014, CHK019, CHK038, CHK041, CHK042, CHK057, CHK058, CHK059, CHK077, CHK133, CHK134, CHK137, CHK138, CHK142 as resolved)

---

## Next Steps

1. **Update spec.md** with FR-215 to FR-290
2. **Update conversation_provider_protocol.py** with complete signatures
3. **Update data-model.md** with Pydantic configurations and tree structure
4. **Update quickstart.md** with exception handling and tree navigation examples
5. **Update library-api.md checklist** marking 17 P1 gaps as resolved
