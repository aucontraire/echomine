# Data Model: Baseline Enhancement Package v1.2.0

**Feature**: 003-baseline-enhancements
**Date**: 2025-12-05
**Status**: Complete

## Entity Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Search & Statistics Models                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐        ┌──────────────────────────────┐
│ SearchQuery (MODIFY)         │        │ ExportStatistics (NEW)       │
│──────────────────────────────│        │──────────────────────────────│
│ + keywords: list[str] | None │        │ + total_conversations: int   │
│ + title_filter: str | None   │        │ + total_messages: int        │
│ + from_date: date | None     │        │ + earliest_date: datetime    │
│ + to_date: date | None       │        │ + latest_date: datetime      │
│ + limit: int = 10            │        │ + average_messages: float    │
│ + phrases: list[str] | None  │        │ + largest_conversation:      │
│ + match_mode: Literal        │        │   ConversationSummary        │
│ + exclude_keywords: list     │        │ + smallest_conversation:     │
│ + role_filter: Literal       │        │   ConversationSummary        │
│──────────────────────────────│        │ + skipped_count: int         │
│ NEW FIELDS (v1.2.0):         │        └──────────────────────────────┘
│ + min_messages: int | None   │                    ▲
│ + max_messages: int | None   │                    │
│ + sort_by: SortField | None  │                    │ uses
│ + sort_order: SortOrder      │                    │
└──────────────────────────────┘        ┌──────────────────────────────┐
                                        │ ConversationSummary (NEW)    │
                                        │──────────────────────────────│
                                        │ + id: str                    │
                                        │ + title: str                 │
                                        │ + message_count: int         │
                                        └──────────────────────────────┘

┌──────────────────────────────┐        ┌──────────────────────────────┐
│ ConversationStatistics (NEW) │        │ RoleCount (NEW)              │
│──────────────────────────────│        │──────────────────────────────│
│ + conversation_id: str       │◄───────│ + user: int                  │
│ + title: str                 │ uses   │ + assistant: int             │
│ + created_at: datetime       │        │ + system: int                │
│ + updated_at: datetime | None│        └──────────────────────────────┘
│ + message_count: int         │
│ + message_count_by_role:     │
│   RoleCount                  │
│ + first_message: datetime    │
│ + last_message: datetime     │
│ + duration_seconds: float    │
│ + average_gap_seconds: float │
└──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Export Models                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐
│ ExportMetadata (NEW)         │
│──────────────────────────────│
│ + id: str                    │
│ + title: str                 │
│ + created_at: datetime       │
│ + updated_at: datetime | None│
│ + message_count: int         │
│ + export_date: datetime      │
│ + exported_by: str           │
└──────────────────────────────┘

┌──────────────────────────────┐
│ CSVExporter (NEW)            │
│──────────────────────────────│
│ + export_conversations()     │
│ + export_messages()          │
│ + export_search_results()    │
└──────────────────────────────┘

┌──────────────────────────────┐
│ MarkdownExporter (MODIFY)    │
│──────────────────────────────│
│ + export_conversation()      │
│ NEW PARAMETERS (v1.2.0):     │
│ + include_metadata: bool     │
│ + include_message_ids: bool  │
└──────────────────────────────┘
```

---

## Type Aliases

```python
# Sort options (FR-043-048)
SortField = Literal["score", "date", "title", "messages"]
SortOrder = Literal["asc", "desc"]

# Role types (existing)
Role = Literal["user", "assistant", "system"]
```

---

## Entity Definitions

### 1. SearchQuery (MODIFY)

**File**: `src/echomine/models/search.py`
**FR Reference**: FR-001-008, FR-043-048

Extend existing SearchQuery model with message count and sort fields.

```python
class SearchQuery(BaseModel):
    """Search query parameters with filters.

    v1.2.0 additions:
    - min_messages: Filter conversations by minimum message count
    - max_messages: Filter conversations by maximum message count
    - sort_by: Sort results by field (score, date, title, messages)
    - sort_order: Sort direction (asc, desc)
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    # Existing fields (v1.1.0)
    keywords: list[str] | None = Field(default=None)
    title_filter: str | None = Field(default=None)
    from_date: date | None = Field(default=None)
    to_date: date | None = Field(default=None)
    limit: int = Field(default=10, gt=0, le=1000)
    phrases: list[str] | None = Field(default=None)
    match_mode: Literal["all", "any"] = Field(default="any")
    exclude_keywords: list[str] | None = Field(default=None)
    role_filter: Literal["user", "assistant", "system"] | None = Field(default=None)

    # NEW v1.2.0: Message count filtering (FR-001-008)
    min_messages: int | None = Field(
        default=None,
        ge=1,
        description="Minimum message count (inclusive, >= 1)",
    )
    max_messages: int | None = Field(
        default=None,
        ge=1,
        description="Maximum message count (inclusive, >= 1)",
    )

    # NEW v1.2.0: Sort options (FR-043-048)
    sort_by: Literal["score", "date", "title", "messages"] | None = Field(
        default=None,
        description="Sort field (default: score for search, date for list)",
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort direction (default: desc for score/date, asc for title)",
    )

    @model_validator(mode="after")
    def validate_message_count_bounds(self) -> "SearchQuery":
        """Validate min_messages <= max_messages when both provided (FR-005)."""
        if self.min_messages is not None and self.max_messages is not None:
            if self.min_messages > self.max_messages:
                raise ValueError(
                    f"min_messages ({self.min_messages}) must be <= "
                    f"max_messages ({self.max_messages})"
                )
        return self
```

### 2. ExportStatistics (NEW)

**File**: `src/echomine/models/statistics.py`
**FR Reference**: FR-010-011, FR-016-017

```python
class ConversationSummary(BaseModel):
    """Minimal conversation info for statistics (largest/smallest)."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    message_count: int = Field(..., ge=0)


class ExportStatistics(BaseModel):
    """Export-level statistics (FR-010, FR-011, FR-017).

    Immutable model representing statistics for an entire export file.
    Calculated via streaming (O(1) memory) by calculate_statistics().
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    total_conversations: int = Field(
        ...,
        ge=0,
        description="Total conversations in export",
    )
    total_messages: int = Field(
        ...,
        ge=0,
        description="Total messages across all conversations",
    )
    earliest_date: datetime | None = Field(
        default=None,
        description="Earliest conversation created_at (None if empty)",
    )
    latest_date: datetime | None = Field(
        default=None,
        description="Latest conversation updated_at (None if empty)",
    )
    average_messages: float = Field(
        ...,
        ge=0.0,
        description="Average messages per conversation",
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
```

### 3. ConversationStatistics (NEW)

**File**: `src/echomine/models/statistics.py`
**FR Reference**: FR-019-023

```python
class RoleCount(BaseModel):
    """Message count breakdown by role."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    user: int = Field(default=0, ge=0)
    assistant: int = Field(default=0, ge=0)
    system: int = Field(default=0, ge=0)

    @property
    def total(self) -> int:
        """Total messages across all roles."""
        return self.user + self.assistant + self.system


class ConversationStatistics(BaseModel):
    """Per-conversation statistics (FR-019-023).

    Immutable model representing detailed statistics for a single conversation.
    Calculated by calculate_conversation_statistics().
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    conversation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    created_at: datetime = Field(...)
    updated_at: datetime | None = Field(default=None)
    message_count: int = Field(..., ge=0)
    message_count_by_role: RoleCount = Field(...)

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
        description="Time between first and last message",
    )
    average_gap_seconds: float | None = Field(
        default=None,
        description="Average time between consecutive messages (None if <2 messages)",
    )
```

### 4. ExportMetadata (NEW)

**File**: `src/echomine/models/statistics.py`
**FR Reference**: FR-030-031

```python
class ExportMetadata(BaseModel):
    """Metadata for markdown frontmatter (FR-030-031).

    Used to generate YAML frontmatter in exported markdown files.
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    message_count: int = Field(..., ge=0, description="Number of messages")
    export_date: datetime = Field(..., description="When this export was created")
    exported_by: str = Field(default="echomine", description="Export tool identifier")
```

---

## Relationships

| Entity | Relates To | Cardinality | Description |
|--------|------------|-------------|-------------|
| ExportStatistics | ConversationSummary | 1:2 | largest/smallest conversation |
| ConversationStatistics | RoleCount | 1:1 | message breakdown |
| SearchQuery | SearchResult | 1:N | query produces results |
| CSVExporter | Conversation | 1:N | exports conversations |
| MarkdownExporter | ExportMetadata | 1:1 | includes frontmatter |

---

## Validation Rules

### SearchQuery Validation

| Rule | Field(s) | Constraint | FR |
|------|----------|------------|-----|
| Message count bounds | min_messages, max_messages | min <= max when both set | FR-005 |
| Min messages range | min_messages | >= 1 (no zero or negative) | FR-005 |
| Max messages range | max_messages | >= 1 (no zero or negative) | FR-005 |

### ExportStatistics Validation

| Rule | Field(s) | Constraint | FR |
|------|----------|------------|-----|
| Non-negative counts | total_*, skipped_count | >= 0 | FR-010 |
| Average consistency | average_messages | total_messages / total_conversations | FR-010 |

### ConversationStatistics Validation

| Rule | Field(s) | Constraint | FR |
|------|----------|------------|-----|
| Duration non-negative | duration_seconds | >= 0.0 | FR-021 |
| Gap requires 2+ messages | average_gap_seconds | None if message_count < 2 | FR-021 |

---

## State Transitions

No state machines - all models are immutable snapshots.

---

## JSON Schemas

### ExportStatistics JSON Schema (FR-012)

```json
{
  "type": "object",
  "required": ["total_conversations", "total_messages", "average_messages"],
  "properties": {
    "total_conversations": {"type": "integer", "minimum": 0},
    "total_messages": {"type": "integer", "minimum": 0},
    "earliest_date": {"type": ["string", "null"], "format": "date-time"},
    "latest_date": {"type": ["string", "null"], "format": "date-time"},
    "average_messages": {"type": "number", "minimum": 0},
    "largest_conversation": {
      "type": ["object", "null"],
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "message_count": {"type": "integer"}
      }
    },
    "smallest_conversation": {"$ref": "#/properties/largest_conversation"},
    "skipped_count": {"type": "integer", "minimum": 0}
  }
}
```

### ConversationStatistics JSON Schema (FR-024)

```json
{
  "type": "object",
  "required": ["conversation_id", "title", "created_at", "message_count", "message_count_by_role"],
  "properties": {
    "conversation_id": {"type": "string"},
    "title": {"type": "string"},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": ["string", "null"], "format": "date-time"},
    "message_count": {"type": "integer", "minimum": 0},
    "message_count_by_role": {
      "type": "object",
      "properties": {
        "user": {"type": "integer", "minimum": 0},
        "assistant": {"type": "integer", "minimum": 0},
        "system": {"type": "integer", "minimum": 0}
      }
    },
    "first_message": {"type": ["string", "null"], "format": "date-time"},
    "last_message": {"type": ["string", "null"], "format": "date-time"},
    "duration_seconds": {"type": "number", "minimum": 0},
    "average_gap_seconds": {"type": ["number", "null"]}
  }
}
```

---

## CSV Schemas

### Conversation-Level CSV (FR-050)

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| conversation_id | string | Unique identifier | Yes |
| title | string | Conversation title | Yes |
| created_at | ISO 8601 | Creation timestamp | Yes |
| updated_at | ISO 8601 | Update timestamp (empty if null) | No |
| message_count | integer | Number of messages | Yes |
| score | float | Search relevance (empty if not search) | No |

### Message-Level CSV (FR-052)

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| conversation_id | string | Parent conversation ID | Yes |
| message_id | string | Message identifier | Yes |
| role | string | user/assistant/system | Yes |
| timestamp | ISO 8601 | Message timestamp | Yes |
| content | string | Message text | Yes |

---

## YAML Frontmatter Schema (FR-031)

```yaml
---
id: <conversation_id>
title: <conversation_title>
created_at: <ISO 8601 timestamp>
updated_at: <ISO 8601 timestamp or null>
message_count: <integer>
export_date: <ISO 8601 timestamp>
exported_by: echomine
---
```
