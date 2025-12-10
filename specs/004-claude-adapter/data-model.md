# Data Model: Claude Export Adapter

**Feature**: 004-claude-adapter
**Date**: 2025-12-08
**Status**: Complete

## Overview

This document defines field mappings from Claude export schema to Echomine's shared Pydantic models. The ClaudeAdapter reuses existing `Conversation`, `Message`, and `SearchResult` models - no new models required.

## Conversation Mapping

### Source: Claude Export

```json
{
  "uuid": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
  "name": "Freedom fighter portrait",
  "summary": "Conversation overview...",
  "created_at": "2025-10-01T18:42:27.303515Z",
  "updated_at": "2025-10-01T18:42:33.904627Z",
  "account": {"uuid": "2dd9aadf-..."},
  "chat_messages": [...]
}
```

### Target: Echomine Conversation Model

```python
Conversation(
    id: str,                    # Required
    title: str,                 # Required (min_length=1)
    created_at: datetime,       # Required (timezone-aware UTC)
    updated_at: datetime | None,# Optional
    messages: list[Message],    # Required (min_length=1)
    metadata: dict[str, Any]    # Optional
)
```

### Field Mapping Table

| Claude Field | Conversation Field | Transform | FR Reference |
|--------------|-------------------|-----------|--------------|
| `uuid` | `id` | Direct copy | FR-002 |
| `name` | `title` | Direct copy (preserve empty*) | FR-003 |
| `created_at` | `created_at` | `datetime.fromisoformat()` | FR-004 |
| `updated_at` | `updated_at` | `datetime.fromisoformat()` or None | FR-005 |
| `chat_messages` | `messages` | Parse each message | FR-006 |
| `summary` | `metadata["summary"]` | Optional, store in metadata | FR-007 |
| `account` | `metadata["account"]` | Optional, store in metadata | FR-008 |

*Note: Empty `name` requires special handling since Conversation.title has min_length=1. Use fallback placeholder "(No title)" at parse time.

### Transformation Logic

```python
def _parse_conversation(self, raw: dict[str, Any]) -> Conversation:
    """Transform Claude conversation to Echomine Conversation."""

    # Parse timestamps (ISO 8601 → datetime)
    created_at = datetime.fromisoformat(raw["created_at"])
    updated_at = (
        datetime.fromisoformat(raw["updated_at"])
        if raw.get("updated_at") else None
    )

    # Parse messages
    messages = [
        self._parse_message(msg)
        for msg in raw.get("chat_messages", [])
    ]

    # Handle empty title (model requires min_length=1)
    title = raw.get("name", "") or "(No title)"

    return Conversation(
        id=raw["uuid"],
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        messages=messages,
        metadata={
            "summary": raw.get("summary"),
            "account": raw.get("account"),
            "provider": "claude",
        }
    )
```

## Message Mapping

### Source: Claude Message

```json
{
  "uuid": "caaac42b-b9a2-4555-96fb-4d15537abc8b",
  "text": "Generate a picture of a freedom fighter",
  "content": [
    {
      "type": "text",
      "text": "Generate a picture of a freedom fighter",
      "citations": []
    }
  ],
  "sender": "human",
  "created_at": "2025-10-01T18:42:28.370875Z",
  "updated_at": "2025-10-01T18:42:28.370875Z",
  "attachments": [],
  "files": []
}
```

### Target: Echomine Message Model

```python
Message(
    id: str,                               # Required
    content: str,                          # Required
    role: Literal["user", "assistant", "system"],  # Required
    timestamp: datetime,                   # Required (timezone-aware UTC)
    parent_id: str | None,                 # Optional (always None for Claude)
    images: list[ImageRef],                # Optional
    metadata: dict[str, Any]               # Optional
)
```

### Field Mapping Table

| Claude Field | Message Field | Transform | FR Reference |
|--------------|---------------|-----------|--------------|
| `uuid` | `id` | Direct copy | FR-011 |
| `content[*].text` | `content` | Concatenate text blocks | FR-012, FR-015 |
| `text` | `content` | Fallback if content empty | FR-015b |
| `sender` | `role` | "human"→"user", "assistant"→"assistant" | FR-013 |
| `created_at` | `timestamp` | `datetime.fromisoformat()` | FR-014 |
| N/A | `parent_id` | Always `None` | FR-020 |
| `attachments` | `images` | Map to ImageRef | FR-016 |
| `files` | `images` | Map to ImageRef | FR-016 |
| `updated_at` | `metadata["updated_at"]` | Store in metadata | - |

### Content Extraction Logic

```python
def _extract_content_from_blocks(
    self,
    content_blocks: list[dict[str, Any]],
    fallback_text: str
) -> str:
    """Extract text content from Claude content blocks.

    Strategy (per FR-015, FR-015a, FR-015b):
    1. Filter blocks where type="text"
    2. Skip tool_use and tool_result blocks
    3. Concatenate text from matching blocks
    4. Fall back to text field if empty
    """
    text_parts: list[str] = []

    for block in content_blocks:
        block_type = block.get("type", "")

        # FR-015a: Skip tool blocks
        if block_type in ("tool_use", "tool_result"):
            continue

        # FR-015: Extract text from text blocks
        if block_type == "text":
            text = block.get("text", "")
            if text:
                text_parts.append(text)

    # FR-015b: Fallback to text field
    if not text_parts:
        return fallback_text

    return "\n".join(text_parts)
```

### Role Normalization Logic

```python
def _normalize_role(self, sender: str) -> Literal["user", "assistant", "system"]:
    """Normalize Claude sender to Echomine role.

    Mapping (per FR-013):
    - "human" → "user"
    - "assistant" → "assistant"
    - Unknown → "assistant" (safe default)
    """
    role_map: dict[str, Literal["user", "assistant", "system"]] = {
        "human": "user",
        "assistant": "assistant",
    }
    return role_map.get(sender, "assistant")
```

### Message Transformation Logic

```python
def _parse_message(self, raw: dict[str, Any]) -> Message:
    """Transform Claude message to Echomine Message."""

    # Extract content from blocks with fallback
    content = self._extract_content_from_blocks(
        raw.get("content", []),
        raw.get("text", "")
    )

    # Parse timestamp
    timestamp = datetime.fromisoformat(raw["created_at"])

    # Map attachments to ImageRef (if applicable)
    images = self._parse_attachments(
        raw.get("attachments", []),
        raw.get("files", [])
    )

    return Message(
        id=raw["uuid"],
        content=content,
        role=self._normalize_role(raw["sender"]),
        timestamp=timestamp,
        parent_id=None,  # FR-020: Claude is linear
        images=images,
        metadata={
            "updated_at": raw.get("updated_at"),
            "original_sender": raw.get("sender"),
            "provider": "claude",
        }
    )
```

## SearchResult Mapping

No mapping required - reuse existing `SearchResult[Conversation]` generic type.

The search implementation will:
1. Stream conversations via `stream_conversations()`
2. Apply filters (title, date, message count)
3. Calculate BM25 scores using existing `BM25Scorer`
4. Generate snippets using existing `extract_snippet_from_messages()`
5. Return `SearchResult[Conversation]` objects

## Validation Rules

### Conversation Validation

| Field | Rule | Error Handling |
|-------|------|----------------|
| `uuid` | Must be non-empty | Skip with WARNING |
| `name` | Can be empty (use placeholder) | Use "(No title)" |
| `created_at` | Must be valid ISO 8601 | Skip with WARNING |
| `chat_messages` | Must be array | Skip with WARNING |

### Message Validation

| Field | Rule | Error Handling |
|-------|------|----------------|
| `uuid` | Must be non-empty | Skip message with WARNING |
| `sender` | Must be "human" or "assistant" | Default to "assistant" |
| `created_at` | Must be valid ISO 8601 | Use conversation created_at |
| `content` | Array of blocks | Fall back to text field |

## Provider Metadata

Each conversation and message includes `metadata["provider"] = "claude"` to enable:
- Provider-specific display logic
- Debugging and traceability
- Future provider-specific features

## No New Models Required

The ClaudeAdapter reuses all existing models:
- `Conversation` (from `echomine.models.conversation`)
- `Message` (from `echomine.models.message`)
- `SearchResult` (from `echomine.models.search`)
- `SearchQuery` (from `echomine.models.search`)
- `ImageRef` (from `echomine.models.image`)

This maintains feature parity and ensures existing consumers work with both providers.
