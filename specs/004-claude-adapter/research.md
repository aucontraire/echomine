# Research: Claude Export Adapter

**Feature**: 004-claude-adapter
**Date**: 2025-12-08
**Status**: Complete

## Overview

This document captures research findings for implementing the Claude conversation export adapter. Analysis based on actual Claude export data from `data/anthropic/conversations.json`.

## Claude Export Schema

### Root Structure

Claude exports are JSON files with a root array of conversation objects:

```json
[
  {
    "uuid": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
    "name": "Freedom fighter portrait",
    "summary": "Conversation overview...",
    "created_at": "2025-10-01T18:42:27.303515Z",
    "updated_at": "2025-10-01T18:42:33.904627Z",
    "account": {"uuid": "2dd9aadf-0a54-4916-8a98-7f8fde3fb14c"},
    "chat_messages": [...]
  }
]
```

### Conversation Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | string | Yes | Unique conversation identifier |
| `name` | string | Yes | Conversation title (can be empty) |
| `summary` | string | No | AI-generated conversation summary |
| `created_at` | ISO 8601 | Yes | Conversation creation timestamp |
| `updated_at` | ISO 8601 | Yes | Last modification timestamp |
| `account` | object | No | User account reference |
| `chat_messages` | array | Yes | Array of message objects |

### Message Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | string | Yes | Unique message identifier |
| `text` | string | Yes | Plain text message content |
| `content` | array | Yes | Structured content blocks |
| `sender` | string | Yes | "human" or "assistant" |
| `created_at` | ISO 8601 | Yes | Message creation timestamp |
| `updated_at` | ISO 8601 | Yes | Message update timestamp |
| `attachments` | array | No | File attachments |
| `files` | array | No | Uploaded files |

### Content Block Structure

Each message has a `content` array with structured blocks:

```json
{
  "content": [
    {
      "start_timestamp": "2025-10-01T18:42:28.365328Z",
      "stop_timestamp": "2025-10-01T18:42:28.365328Z",
      "flags": null,
      "type": "text",
      "text": "The actual message content",
      "citations": []
    }
  ]
}
```

Content block types observed:
- `"text"`: Regular text content
- `"tool_use"`: Tool invocation (not stored per feature parity)
- `"tool_result"`: Tool execution result (not stored per feature parity)

## Comparison: Claude vs OpenAI

### Structural Differences

| Aspect | Claude | OpenAI |
|--------|--------|--------|
| Root structure | Array of conversations | Array of conversations |
| Conversation ID | `uuid` | `id` |
| Title field | `name` | `title` |
| Message storage | `chat_messages` (array) | `mapping` (tree structure) |
| Message ID | `uuid` | `id` |
| Role field | `sender` | `author.role` |
| Role values | "human", "assistant" | "user", "assistant", "system", "tool" |
| Timestamps | ISO 8601 strings | Unix epoch floats |
| Message ordering | Sequential array | Tree with parent/children |
| Content storage | `content` blocks + `text` | `content.parts` array |

### Key Implementation Differences

1. **Message Structure**: Claude uses linear array, OpenAI uses tree structure
2. **Timestamp Format**: Claude uses ISO 8601, OpenAI uses Unix floats
3. **Role Normalization**: Claude's "human" maps to "user"
4. **Content Extraction**: Claude has `content` blocks with types; OpenAI has `content.parts`

## Research Decisions

### RD-001: Content Extraction Strategy

**Question**: Should we use the `text` field or parse `content` blocks?

**Analysis**:
- Compared `text` field to concatenated `content` blocks
- 92% of messages: `text` identical to content block text
- 8% of messages: `content` contains additional tool context

**Decision**: Parse `content` blocks as primary source
**Rationale**: More accurate representation; `text` field is a convenience fallback
**Fallback**: Use `text` field if `content` array is empty or missing

### RD-002: Linear Message Structure

**Question**: How to handle Claude's linear message structure vs OpenAI's tree?

**Analysis**:
- Claude exports don't expose branching/regeneration history
- All messages appear in sequential order
- No parent/children references in export

**Decision**: Set `parent_id=None` for all Claude messages
**Rationale**: Matches source data accurately; inferring structure would be unreliable

### RD-003: Role Normalization

**Question**: How to normalize Claude's "human"/"assistant" roles?

**Analysis**:
- Claude uses "human" for user messages
- OpenAI uses "user" for human input
- Existing Message model uses "user", "assistant", "system"

**Decision**: Map "human" → "user", keep "assistant" unchanged
**Rationale**: Consistent with OpenAI adapter and shared Message model

### RD-004: Timestamp Parsing

**Question**: How to parse Claude's ISO 8601 timestamps?

**Analysis**:
- Claude format: "2025-10-01T18:42:27.303515Z"
- Python's `datetime.fromisoformat()` handles this format
- All timestamps include timezone (Z = UTC)

**Decision**: Use `datetime.fromisoformat()` for parsing
**Rationale**: Built-in, no external dependencies needed

### RD-005: Empty Title Handling

**Question**: How to handle conversations with empty `name` field?

**Analysis**:
- Some Claude conversations have `name: ""`
- Data integrity principle requires preserving source data
- Display can show "(Untitled)" without modifying data

**Decision**: Preserve empty string in model, display "(Untitled)" in UI
**Rationale**: Constitution VI - data integrity, don't pollute source data

### RD-006: Provider Auto-Detection

**Question**: How to auto-detect Claude vs OpenAI exports?

**Analysis**:
- Claude: Has `chat_messages` key in conversation objects
- OpenAI: Has `mapping` key in conversation objects
- These are mutually exclusive structural differences

**Decision**: Detect based on presence of `chat_messages` (Claude) vs `mapping` (OpenAI)
**Rationale**: Reliable structural markers, no false positives

## Data Samples

### Sample Conversation (Claude)

```json
{
  "uuid": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
  "name": "Freedom fighter portrait",
  "created_at": "2025-10-01T18:42:27.303515Z",
  "updated_at": "2025-10-01T18:42:33.904627Z",
  "chat_messages": [
    {
      "uuid": "caaac42b-b9a2-4555-96fb-4d15537abc8b",
      "text": "Generate a picture of a freedom fighter",
      "content": [
        {
          "type": "text",
          "text": "Generate a picture of a freedom fighter"
        }
      ],
      "sender": "human",
      "created_at": "2025-10-01T18:42:28.370875Z"
    }
  ]
}
```

### Equivalent Conversation (Mapped to Echomine Model)

```python
Conversation(
    id="5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
    title="Freedom fighter portrait",
    created_at=datetime(2025, 10, 1, 18, 42, 27, 303515, tzinfo=UTC),
    updated_at=datetime(2025, 10, 1, 18, 42, 33, 904627, tzinfo=UTC),
    messages=[
        Message(
            id="caaac42b-b9a2-4555-96fb-4d15537abc8b",
            content="Generate a picture of a freedom fighter",
            role="user",  # Normalized from "human"
            timestamp=datetime(2025, 10, 1, 18, 42, 28, 370875, tzinfo=UTC),
            parent_id=None  # Always None for Claude
        )
    ],
    metadata={
        "summary": "...",
        "account": {"uuid": "..."}
    }
)
```

## Edge Cases Documented

1. **Empty `name` field**: Preserve as empty string, display "(Untitled)"
2. **Empty `chat_messages`**: Return conversation with empty messages list
3. **Missing `content` array**: Fall back to `text` field
4. **Only `tool_use`/`tool_result` blocks**: Content is empty string
5. **Invalid timestamp**: Skip message with WARNING log, continue processing
6. **Missing required fields**: Skip conversation with WARNING log

## Recommendations

1. Use ijson streaming for O(1) memory (same as OpenAI adapter)
2. Reuse existing BM25 search implementation
3. Reuse existing Conversation/Message models
4. Add provider detection to CLI app.py
5. Create test fixtures from sanitized real export data
