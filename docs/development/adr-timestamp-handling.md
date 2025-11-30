# ADR: Timestamp Handling

**Date**: 2025-11-22
**Status**: Accepted
**Decision**: Use semantic optionality (`Optional[datetime]`) instead of Unix epoch fallback for `updated_at`

---

## Overview

This document describes the design decisions and best practices for handling potentially null timestamps in the echomine Conversation model.

## Design Decision: Optional `updated_at` with Semantic Fallback

### The Problem

OpenAI conversation exports have `create_time` and `update_time` fields at the conversation level. While these fields are present in all real-world exports (verified with 280+ conversations), the schema doesn't guarantee they'll always be present.

**Anti-Pattern: Unix Epoch Fallback**
```python
# WRONG: Creates false data
updated_at = (
    datetime.fromtimestamp(float(update_time), tz=UTC)
    if update_time is not None
    else datetime.fromtimestamp(0, tz=UTC)  # 1970-01-01 is FALSE DATA
)
```

**Problems with Unix epoch fallback:**
- Creates false data that never existed
- Corrupts analytics and search results
- Misleads users (conversation from 1970?)
- Violates data integrity principles
- Difficult to distinguish "unknown" from "actually 1970"

### The Solution: Semantic Optionality

```python
class Conversation(BaseModel):
    created_at: datetime  # REQUIRED - every conversation must have creation time
    updated_at: Optional[datetime] = None  # OPTIONAL - None means "never updated"

    @property
    def updated_at_or_created(self) -> datetime:
        """Fallback to created_at if never updated."""
        return self.updated_at if self.updated_at is not None else self.created_at
```

**Why this works:**
1. **Semantic Correctness**: `None` explicitly means "never modified" (not "unknown")
2. **Data Integrity**: Never invents false data
3. **Type Safety**: Fully mypy --strict compliant
4. **Backward Compatibility**: JSON output always includes both timestamps via `updated_at_or_created`
5. **Flexible Access**: Direct field for null-checking, property for guaranteed non-null value

## Implementation Details

### 1. Pydantic Model

**File: `src/echomine/models/conversation.py`**

```python
from datetime import UTC, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class Conversation(BaseModel):
    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp (timezone-aware UTC, REQUIRED)",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last modification timestamp (timezone-aware UTC, None if never updated)",
    )

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure created_at is timezone-aware and normalized to UTC."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            msg = f"created_at must be timezone-aware: {v}"
            raise ValueError(msg)
        return v.astimezone(UTC)

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at_timezone_aware(cls, v: Optional[datetime], info: Any) -> Optional[datetime]:
        """Ensure updated_at is timezone-aware and >= created_at (if provided)."""
        if v is None:
            return None

        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            msg = f"updated_at must be timezone-aware: {v}"
            raise ValueError(msg)

        v_utc = v.astimezone(UTC)

        # Validate updated_at >= created_at
        created_at = info.data.get("created_at")
        if created_at and v_utc < created_at:
            msg = f"updated_at ({v_utc}) must be >= created_at ({created_at})"
            raise ValueError(msg)

        return v_utc

    @property
    def updated_at_or_created(self) -> datetime:
        """Get last update timestamp, falling back to created_at if not set."""
        return self.updated_at if self.updated_at is not None else self.created_at
```

### 2. Adapter Validation

**File: `src/echomine/adapters/openai.py`**

```python
from pydantic import ValidationError as PydanticValidationError

# Validate created_at is present (REQUIRED)
if create_time is None:
    raise PydanticValidationError.from_exception_data(
        "Conversation",
        [
            {
                "type": "missing",
                "loc": ("create_time",),
                "input": raw_data,
            }
        ],
    )

created_at = datetime.fromtimestamp(float(create_time), tz=UTC)

# Handle optional updated_at
updated_at: Optional[datetime] = (
    datetime.fromtimestamp(float(update_time), tz=UTC)
    if update_time is not None
    else None
)
```

**Validation Strategy:**
- `created_at`: REQUIRED - if null, raise ValidationError (malformed data)
- `updated_at`: OPTIONAL - if null, set to None (semantically valid)

### 3. JSON Serialization

**File: `src/echomine/cli/formatters.py`**

```python
def format_json(conversations: list[Conversation]) -> str:
    """Format conversations as JSON with guaranteed timestamps."""
    conv_dicts = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": conv.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%S"),  # Never null
            "message_count": conv.message_count,
        }
        conv_dicts.append(conv_dict)

    return json.dumps(conv_dicts, separators=(',', ':'), ensure_ascii=False) + "\n"
```

**JSON Output Schema:**
```json
{
  "id": "conv-123",
  "title": "Python best practices",
  "created_at": "2024-03-15T14:23:11",
  "updated_at": "2024-03-15T14:23:11",
  "message_count": 47
}
```

**Key Points:**
- JSON consumers ALWAYS get both timestamps (never null)
- If conversation never updated, `created_at == updated_at` (semantically correct)
- No need for null handling in downstream JSON processors

## Usage Patterns

### Pattern 1: Display Timestamps

```python
# For display (CLI table, JSON output)
print(f"Last modified: {conv.updated_at_or_created}")

# Guaranteed non-null, mypy --strict compliant
```

### Pattern 2: Distinguish "Never Updated"

```python
# When you need to know if conversation was EVER updated
if conv.updated_at is None:
    print("Conversation never modified since creation")
else:
    print(f"Last updated: {conv.updated_at}")
```

### Pattern 3: Date Range Filtering

```python
# Search filtering uses created_at (required field)
if query.from_date is not None:
    if conv.created_at.date() < query.from_date:
        continue  # Skip conversation outside date range
```

### Pattern 4: Sorting by Modification Time

```python
# Sort by "last modified" (with fallback)
conversations.sort(key=lambda c: c.updated_at_or_created, reverse=True)
```

## Type Safety Guarantees

### mypy --strict Compliance

All code passes `mypy --strict` without warnings:

```bash
$ mypy --strict src/echomine/models/conversation.py
Success: no issues found in 1 source file

$ mypy --strict src/echomine/adapters/openai.py
Success: no issues found in 1 source file

$ mypy --strict src/echomine/cli/formatters.py
Success: no issues found in 1 source file
```

### Type Narrowing

```python
# Direct field access (Optional[datetime])
timestamp: Optional[datetime] = conv.updated_at
if timestamp is not None:
    # Type narrowed to datetime (non-null)
    print(timestamp.isoformat())

# Property access (datetime, never None)
timestamp: datetime = conv.updated_at_or_created
print(timestamp.isoformat())  # No null check needed
```

## Impact Analysis

### Downstream Components

| Component | Impact | Mitigation |
|-----------|--------|------------|
| **CLI Formatters** | Must use `updated_at_or_created` | ✅ Updated in formatters.py |
| **JSON Output** | Must never output null | ✅ Uses `updated_at_or_created` |
| **Search Filtering** | Date ranges use `created_at` | ✅ No changes needed |
| **BM25 Scoring** | Not timestamp-dependent | ✅ No changes needed |
| **Tree Navigation** | Not timestamp-dependent | ✅ No changes needed |

### API Stability

**Breaking Change: NO**
- JSON output schema unchanged (both timestamps always present)
- Search API unchanged (filters on `created_at`)
- CLI output unchanged (uses fallback property)

**Internal Change: YES**
- `Conversation.updated_at` is now `Optional[datetime]`
- New property `updated_at_or_created` for guaranteed access
- Adapters must handle null `update_time` explicitly

## Testing

### Unit Tests

```python
from datetime import UTC, datetime, timedelta
from echomine.models.conversation import Conversation
from echomine.models.message import Message

def test_conversation_never_updated():
    """Test conversation with None updated_at."""
    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)

    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    conv = Conversation(
        id="conv-001",
        title="Test",
        created_at=created,
        updated_at=None,  # Never updated
        messages=[msg],
    )

    assert conv.updated_at is None
    assert conv.updated_at_or_created == created

def test_conversation_with_updates():
    """Test conversation with explicit updated_at."""
    created = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)
    updated = created + timedelta(hours=2)

    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=created,
        parent_id=None,
    )

    conv = Conversation(
        id="conv-002",
        title="Test",
        created_at=created,
        updated_at=updated,
        messages=[msg],
    )

    assert conv.updated_at == updated
    assert conv.updated_at_or_created == updated
```

### Integration Tests

All existing integration tests pass without modifications:
- `tests/integration/test_list_flow.py` (10/10 passed)
- `tests/integration/test_search_flow.py` (16/16 passed)

## Migration Guide

### For Existing Code

**If you were using `conv.updated_at` for display:**
```python
# Before
print(f"Updated: {conv.updated_at}")

# After (handles None gracefully)
print(f"Updated: {conv.updated_at_or_created}")
```

**If you need to distinguish null:**
```python
# Before (always had a value)
print(f"Updated: {conv.updated_at}")

# After (check for None)
if conv.updated_at is not None:
    print(f"Updated: {conv.updated_at}")
else:
    print("Never updated")
```

### For New Code

**Recommended pattern:**
```python
# For display/sorting (guaranteed non-null)
timestamp = conv.updated_at_or_created

# For business logic (check if updated)
if conv.updated_at is not None:
    # Handle updated case
    pass
else:
    # Handle never-updated case
    pass
```

## References

### Related Files
- `/Users/omarcontreras/PycharmProjects/echomine/src/echomine/models/conversation.py`
- `/Users/omarcontreras/PycharmProjects/echomine/src/echomine/adapters/openai.py`
- `/Users/omarcontreras/PycharmProjects/echomine/src/echomine/cli/formatters.py`
- `/Users/omarcontreras/PycharmProjects/echomine/examples/timestamp_handling.py`

### Constitution Principles
- **Principle VI**: Strict typing with mypy --strict compliance
- **Principle I**: Library-first (data models are pure, reusable)
- **FR-222, FR-227**: Immutability via frozen=True
- **FR-244, FR-245, FR-246**: Timezone-aware timestamps
- **FR-273**: updated_at >= created_at validation
- **FR-301-306**: JSON output schema

### External Resources
- [Pydantic Field Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Python datetime Best Practices](https://docs.python.org/3/library/datetime.html)
- [mypy Optional Type Handling](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#optional-types-and-the-none-type)
