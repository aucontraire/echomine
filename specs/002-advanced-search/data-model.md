# Data Model: Advanced Search Enhancement Package

**Branch**: `002-advanced-search` | **Date**: 2025-12-03
**Purpose**: Define Pydantic model extensions for advanced search features

## Model Changes Overview

| Model | Change Type | New Fields |
|-------|-------------|------------|
| `SearchQuery` | Extension | `phrases`, `match_mode`, `exclude_keywords`, `role_filter` |
| `SearchResult` | Extension | `snippet` |
| `Message` | Unchanged | (existing `role` field used) |
| `Conversation` | Unchanged | (existing structure) |

## SearchQuery Model Extension

**Location**: `src/echomine/models/search.py`

### Current State

```python
class SearchQuery(BaseModel):
    """Query parameters for conversation search."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    keywords: list[str] | None = Field(default=None, description="Keywords to search")
    title: str | None = Field(default=None, description="Title filter")
    from_date: date | None = Field(default=None, description="Start date filter")
    to_date: date | None = Field(default=None, description="End date filter")
    limit: int = Field(default=10, gt=0, le=1000, description="Max results")
```

### Extended State

```python
from typing import Literal

class SearchQuery(BaseModel):
    """Query parameters for conversation search."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    # Existing fields (unchanged)
    keywords: list[str] | None = Field(default=None, description="Keywords to search")
    title: str | None = Field(default=None, description="Title filter")
    from_date: date | None = Field(default=None, description="Start date filter")
    to_date: date | None = Field(default=None, description="End date filter")
    limit: int = Field(default=10, gt=0, le=1000, description="Max results")

    # NEW: Phrase matching (FR-001-006)
    phrases: list[str] | None = Field(
        default=None,
        description="Exact phrases to match (no tokenization, case-insensitive)",
    )

    # NEW: Boolean match mode (FR-007-011)
    match_mode: Literal["all", "any"] = Field(
        default="any",
        description="'all' requires ALL keywords/phrases; 'any' matches ANY (default)",
    )

    # NEW: Exclude keywords (FR-012-016)
    exclude_keywords: list[str] | None = Field(
        default=None,
        description="Keywords to exclude from results (uses same tokenization as keywords)",
    )

    # NEW: Role filter (FR-017-020)
    role_filter: Literal["user", "assistant", "system"] | None = Field(
        default=None,
        description="Filter to messages from specific role only",
    )
```

### Field Specifications

#### `phrases`

| Attribute | Value |
|-----------|-------|
| Type | `list[str] | None` |
| Default | `None` |
| FR Reference | FR-001, FR-002, FR-005 |
| Validation | None (empty list treated as None) |
| Behavior | Case-insensitive substring matching |

#### `match_mode`

| Attribute | Value |
|-----------|-------|
| Type | `Literal["all", "any"]` |
| Default | `"any"` |
| FR Reference | FR-007, FR-008, FR-011 |
| Validation | Must be "all" or "any" (Pydantic Literal enforces) |
| Behavior | "all" = AND logic, "any" = OR logic (default) |

#### `exclude_keywords`

| Attribute | Value |
|-----------|-------|
| Type | `list[str] | None` |
| Default | `None` |
| FR Reference | FR-012, FR-013, FR-016 |
| Validation | None (empty list treated as None) |
| Behavior | Tokenized same as keywords, NOR logic for multiple |

#### `role_filter`

| Attribute | Value |
|-----------|-------|
| Type | `Literal["user", "assistant", "system"] | None` |
| Default | `None` |
| FR Reference | FR-017, FR-019, FR-020 |
| Validation | Must be valid role or None (Pydantic Literal enforces) |
| Behavior | `None` = search all roles (current behavior) |

---

## SearchResult Model Extension

**Location**: `src/echomine/models/search.py`

### Current State

```python
class SearchResult(BaseModel, Generic[ConversationT]):
    """Search result with relevance score."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    conversation: ConversationT
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    matched_message_ids: list[str] = Field(default_factory=list)
```

### Extended State

```python
class SearchResult(BaseModel, Generic[ConversationT]):
    """Search result with relevance score and snippet."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    # Existing fields (unchanged)
    conversation: ConversationT
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    matched_message_ids: list[str] = Field(default_factory=list)

    # NEW: Message snippet (FR-021-025)
    snippet: str | None = Field(
        default=None,
        description="First ~100 chars of first matched message",
    )
```

### Field Specifications

#### `snippet`

| Attribute | Value |
|-----------|-------|
| Type | `str | None` |
| Default | `None` |
| FR Reference | FR-021, FR-024 |
| Max Length | ~100 characters + indicator |
| Fallback | "[Content unavailable]" for malformed content (FR-025) |
| Format | `"Text..."` or `"Text... (+N more matches)"` |

---

## Message Model (Unchanged)

**Location**: `src/echomine/models/conversation.py`

The existing `Message` model already has the `role` field used for role filtering:

```python
class Message(BaseModel):
    """Immutable message in a conversation."""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    id: str
    role: str  # "user", "assistant", "system"
    content: str
    created_at: datetime
    # ... other fields
```

**Note**: The `role` field is a string (not Literal) because external exports may contain non-standard roles. The role filter only matches on known values.

---

## Validation Rules

### SearchQuery Validation

1. **At least one search criterion required**:
   - `keywords` OR `phrases` OR `title` must be provided
   - Empty lists (`[]`) treated as `None`

2. **Match mode only applies when terms exist**:
   - If no keywords/phrases, match_mode is ignored

3. **Exclusion requires search terms**:
   - `exclude_keywords` without `keywords`/`phrases` is a warning (no-op)

### SearchResult Validation

1. **Snippet consistency**:
   - If `matched_message_ids` is empty, `snippet` should be `None` or fallback text
   - Snippet length should be ≤ 150 chars (100 + "..." + " (+N more matches)")

---

## Backward Compatibility

All new fields have default values that preserve existing behavior:

| Field | Default | Existing Behavior |
|-------|---------|-------------------|
| `phrases` | `None` | No phrase matching |
| `match_mode` | `"any"` | OR logic (current) |
| `exclude_keywords` | `None` | No exclusion |
| `role_filter` | `None` | All roles searched |
| `snippet` | `None` | No snippet in results |

**FR-028 Compliance**: Existing code using `SearchQuery(keywords=["python"])` continues to work unchanged.

---

## JSON Schema Examples

### SearchQuery with New Fields

```json
{
  "keywords": ["python", "async"],
  "phrases": ["algo-insights", "data pipeline"],
  "match_mode": "all",
  "exclude_keywords": ["django"],
  "role_filter": "user",
  "limit": 10
}
```

### SearchResult with Snippet

```json
{
  "conversation": {
    "id": "abc-123",
    "title": "Python async patterns",
    "messages": [...]
  },
  "score": 0.85,
  "matched_message_ids": ["msg-001", "msg-005", "msg-012"],
  "snippet": "We use asyncio.gather() for concurrent requests... (+2 more matches)"
}
```

---

## Test Requirements

### Model Unit Tests

```python
# tests/unit/models/test_search.py

def test_search_query_phrases_optional():
    """SearchQuery works without phrases (backward compat)."""
    query = SearchQuery(keywords=["python"])
    assert query.phrases is None

def test_search_query_match_mode_default():
    """Match mode defaults to 'any' for backward compat."""
    query = SearchQuery(keywords=["python"])
    assert query.match_mode == "any"

def test_search_query_match_mode_all():
    """Match mode accepts 'all' value."""
    query = SearchQuery(keywords=["python"], match_mode="all")
    assert query.match_mode == "all"

def test_search_query_role_filter_literal():
    """Role filter only accepts valid literals."""
    query = SearchQuery(keywords=["python"], role_filter="user")
    assert query.role_filter == "user"

def test_search_result_snippet_optional():
    """SearchResult works without snippet (backward compat)."""
    result = SearchResult(conversation=conv, score=0.5, matched_message_ids=[])
    assert result.snippet is None

def test_search_result_with_snippet():
    """SearchResult accepts snippet field."""
    result = SearchResult(
        conversation=conv,
        score=0.5,
        matched_message_ids=["msg-1"],
        snippet="Hello world..."
    )
    assert result.snippet == "Hello world..."
```

---

## Migration Notes

No data migration required. All changes are additive with optional fields.

Clients upgrading from v1.0.x to v1.1.x:
- Existing `SearchQuery` instances work unchanged
- New `SearchResult.snippet` field may be `None` (clients should handle)
- Library API is fully backward compatible
