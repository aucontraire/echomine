# Content Types

Provider-agnostic content type classification for conversation messages.

## Overview

The content types module provides a standardized 7-value vocabulary for classifying message content across all providers. Each message carries both a raw provider-specific `content_type` and a normalized `content_type_category` in its metadata.

## ContentTypeCategory

```python
from echomine.models.content_types import ContentTypeCategory

# Literal type with 7 values:
# "conversational" | "reasoning" | "tool_io" | "system" | "media" | "attachment" | "unknown"
```

| Category | Description |
|---|---|
| `conversational` | Regular chat messages (text, multimodal text, voice notes) |
| `reasoning` | Model thinking and chain-of-thought (thoughts, reasoning recap) |
| `tool_io` | Tool calls, code execution, and results (also any message with `author.role == "tool"`) |
| `system` | System-level messages (context, errors, token budgets) |
| `media` | Standalone media content (images without accompanying text) |
| `attachment` | Standalone file attachments (no accompanying text) |
| `unknown` | Unmapped or unrecognized content types |

## classify_content_type

::: echomine.models.content_types.classify_content_type
    options:
      show_source: true
      heading_level: 3

## Category Maps

### OPENAI_CATEGORY_MAP

Maps 13 OpenAI raw content types to categories:

| Raw Type | Category |
|---|---|
| `text` | conversational |
| `multimodal_text` | conversational |
| `thoughts` | reasoning |
| `reasoning_recap` | reasoning |
| `code` | tool_io |
| `execution_output` | tool_io |
| `tether_quote` | tool_io |
| `tether_browsing_display` | tool_io |
| `user_editable_context` | system |
| `app_pairing_content` | system |
| `system_error` | system |
| `image_asset_pointer` | media |
| `image` | media |

### CLAUDE_CATEGORY_MAP

Maps 6 Claude block types to categories:

| Block Type | Category |
|---|---|
| `text` | conversational |
| `voice_note` | conversational |
| `thinking` | reasoning |
| `tool_use` | tool_io |
| `tool_result` | tool_io |
| `token_budget` | system |

## Usage Examples

### Classify Content Types

```python
from echomine.models.content_types import classify_content_type

# OpenAI
classify_content_type("text", "openai")           # "conversational"
classify_content_type("thoughts", "openai")        # "reasoning"
classify_content_type("code", "openai")            # "tool_io"

# Claude
classify_content_type("thinking", "claude")        # "reasoning"
classify_content_type("tool_use", "claude")        # "tool_io"

# Unknown returns "unknown"
classify_content_type("new_type", "openai")        # "unknown"
```

### Access Category from Messages

```python
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(Path("export.json")):
    for msg in conv.messages:
        category = msg.metadata.get("content_type_category", "unknown")
        if category == "reasoning":
            print(f"Thinking: {msg.metadata.get('reasoning', '')[:80]}")
```
