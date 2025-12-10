# ClaudeAdapter

Streaming adapter for Anthropic Claude conversation export files.

## Overview

The `ClaudeAdapter` class provides O(1) memory streaming for Claude conversation exports using ijson. It implements the same interface as `OpenAIAdapter`, enabling seamless multi-provider support through a unified API.

**Module:** `echomine.adapters.claude`

**Import:**
```python
from echomine import ClaudeAdapter
```

## Memory Characteristics

- **O(1) memory consumption**: File size independent (streaming parser)
- **O(N) per conversation**: Where N = message count in single conversation
- **Parser buffer**: ~50MB max (ijson state + current conversation)
- **No unbounded structures**: Conversations yielded immediately

## Claude Export Schema

Claude exports use a different JSON structure than OpenAI:

### Root Structure
```json
[
  {
    "uuid": "conversation-id",
    "name": "Conversation Title",
    "created_at": "2025-10-01T18:42:27.303515Z",
    "updated_at": "2025-10-01T18:45:30.123456Z",
    "chat_messages": [...]
  }
]
```

### Message Structure
```json
{
  "uuid": "message-id",
  "text": "Fallback message content",
  "content": [
    {
      "type": "text",
      "text": "Primary message content"
    }
  ],
  "sender": "human",
  "created_at": "2025-10-01T18:42:30.123456Z",
  "updated_at": "2025-10-01T18:42:30.123456Z"
}
```

### Field Mappings

Claude export fields are normalized to echomine's unified `Conversation` and `Message` models:

| Claude Field | Echomine Field | Notes |
|-------------|----------------|-------|
| `uuid` (conversation) | `id` | Conversation identifier |
| `name` | `title` | Empty string → "(No title)" |
| `created_at` | `created_at` | Parsed to timezone-aware datetime |
| `updated_at` | `updated_at` | Parsed to timezone-aware datetime |
| `chat_messages` | `messages` | Flat message array |
| `uuid` (message) | `id` | Message identifier |
| `content[type=text].text` | `content` | Extracted from content blocks |
| `text` | `content` | Fallback if content blocks empty |
| `sender` ("human") | `role` ("user") | Normalized role names |
| `sender` ("assistant") | `role` ("assistant") | Normalized role names |

### Content Block Handling

Claude messages use a content block structure:

```json
"content": [
  {"type": "text", "text": "Hello"},
  {"type": "tool_use", "id": "toolu_123", "name": "calc", "input": {}},
  {"type": "text", "text": "World"}
]
```

**Extraction Strategy:**
1. Extract text from all `type="text"` blocks
2. Skip `type="tool_use"` and `type="tool_result"` blocks (tool invocations ignored)
3. Concatenate text blocks with newline separator
4. Fallback to `text` field if content extraction yields empty string

## Class Definition

```python
class ClaudeAdapter:
    """Adapter for streaming Anthropic Claude conversation exports."""
```

The adapter is **stateless** - no instance variables or configuration. All methods accept file paths as arguments, enabling reuse across multiple export files.

## Methods

### stream_conversations

Stream all conversations from a Claude export file.

**Signature:**
```python
def stream_conversations(
    self,
    file_path: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> Iterator[Conversation]:
```

**Parameters:**
- `file_path` (Path): Path to Claude export JSON file
- `progress_callback` (Optional[ProgressCallback]): Callback invoked every 100 conversations for progress reporting
- `on_skip` (Optional[OnSkipCallback]): Callback invoked when malformed entries are skipped

**Returns:**
- Iterator[Conversation]: Lazy stream of parsed conversations

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ParseError`: If JSON syntax is invalid
- `ValidationError`: If conversation data violates Pydantic schema

**Example:**
```python
from pathlib import Path
from echomine import ClaudeAdapter

adapter = ClaudeAdapter()

# Basic streaming
for conv in adapter.stream_conversations(Path("claude_export.json")):
    print(f"{conv.title}: {len(conv.messages)} messages")

# With progress callback
def show_progress(count: int) -> None:
    print(f"Processed {count} conversations")

for conv in adapter.stream_conversations(
    Path("claude_export.json"),
    progress_callback=show_progress
):
    process(conv)

# Early termination (memory efficient)
conversations = []
for i, conv in enumerate(adapter.stream_conversations(Path("claude_export.json"))):
    conversations.append(conv)
    if i >= 9:  # First 10 only
        break
```

**Performance:**
- Memory: O(1) for file size, O(N) for single conversation
- Time: O(M) where M = total conversations in file
- Lazy: Conversations yielded as parsed (no upfront loading)

---

### search

Search conversations with BM25 relevance ranking.

**Signature:**
```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> Iterator[SearchResult[Conversation]]:
```

**Parameters:**
- `file_path` (Path): Path to Claude export file
- `query` (SearchQuery): Search query with keywords, filters, and limits
- `progress_callback` (Optional[ProgressCallback]): Progress reporting callback
- `on_skip` (Optional[OnSkipCallback]): Malformed entry callback

**Returns:**
- Iterator[SearchResult[Conversation]]: Ranked search results with scores

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ParseError`: If JSON syntax is invalid

**Example:**
```python
from pathlib import Path
from echomine import ClaudeAdapter, SearchQuery

adapter = ClaudeAdapter()
export_file = Path("claude_export.json")

# Keyword search
query = SearchQuery(keywords=["python", "algorithm"], limit=10)
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Snippet: {result.snippet}")

# Advanced search with filters
from datetime import date

query = SearchQuery(
    keywords=["refactor"],
    phrases=["code review"],
    match_mode="all",
    exclude_keywords=["test"],
    role_filter="user",
    from_date=date(2025, 1, 1),
    limit=5
)

for result in adapter.search(export_file, query):
    print(f"{result.conversation.title}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Matched messages: {len(result.matched_message_ids)}")
```

**Search Features:**
- BM25 relevance ranking
- Exact phrase matching
- Boolean keyword logic (AND/OR)
- Keyword exclusion
- Role filtering (user/assistant)
- Date range filtering
- Message count filtering
- Automatic snippet extraction

**Performance:**
- Memory: O(N) where N = matching conversations (must score all for ranking)
- Time: O(M) where M = total conversations in file

---

### get_conversation_by_id

Retrieve a specific conversation by UUID.

**Signature:**
```python
def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str,
) -> Conversation | None:
```

**Parameters:**
- `file_path` (Path): Path to Claude export file
- `conversation_id` (str): Full or partial UUID (minimum 4 characters)

**Returns:**
- Conversation | None: Conversation if found, None otherwise

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ParseError`: If JSON syntax is invalid

**Example:**
```python
from pathlib import Path
from echomine import ClaudeAdapter

adapter = ClaudeAdapter()
export_file = Path("claude_export.json")

# Full UUID match
conv = adapter.get_conversation_by_id(
    export_file,
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
)

# Partial UUID match (minimum 4 characters)
conv = adapter.get_conversation_by_id(export_file, "a1b2")

if conv:
    print(f"Found: {conv.title}")
    print(f"Messages: {len(conv.messages)}")
else:
    print("Conversation not found")
```

**Matching Rules:**
- Case-insensitive
- Exact match takes precedence
- Prefix match requires minimum 4 characters
- Returns first match found (early termination)

**Performance:**
- Memory: O(1) for file size, O(M) for single conversation
- Time: O(N) where N = conversations until match (early termination)

---

### get_message_by_id

Retrieve a specific message by UUID with conversation context.

**Signature:**
```python
def get_message_by_id(
    self,
    file_path: Path,
    message_id: str,
    *,
    conversation_id: str | None = None,
) -> tuple[Message, Conversation] | None:
```

**Parameters:**
- `file_path` (Path): Path to Claude export file
- `message_id` (str): UUID of message to retrieve
- `conversation_id` (Optional[str]): Conversation hint for faster lookup

**Returns:**
- tuple[Message, Conversation] | None: Message and parent conversation if found, None otherwise

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ParseError`: If JSON syntax is invalid

**Example:**
```python
from pathlib import Path
from echomine import ClaudeAdapter

adapter = ClaudeAdapter()
export_file = Path("claude_export.json")

# Search with conversation hint (faster)
result = adapter.get_message_by_id(
    export_file,
    "msg-123",
    conversation_id="conv-456"
)

# Search all conversations (slower)
result = adapter.get_message_by_id(export_file, "msg-123")

if result:
    message, conversation = result
    print(f"Message: {message.content}")
    print(f"From conversation: {conversation.title}")
else:
    print("Message not found")
```

**Performance:**
- With `conversation_id` hint:
  - Time: O(N) where N = conversations until match
  - Memory: O(1) for file size
- Without hint:
  - Time: O(N*M) where N = conversations, M = messages per conversation
  - Memory: O(1) for file size
- Early termination: Returns immediately when match found

---

## Error Handling

The adapter follows a **fail-fast** strategy for unrecoverable errors and **graceful degradation** for malformed entries:

### Fail-Fast Errors

Raised immediately, processing stops:

```python
from echomine.exceptions import ParseError
from pydantic import ValidationError

try:
    conversations = list(adapter.stream_conversations(path))
except FileNotFoundError:
    print("Export file not found")
except ParseError:
    print("Invalid JSON syntax")
except ValidationError:
    print("Export schema violation")
```

### Graceful Degradation

Malformed conversations/messages are logged and skipped, processing continues:

```python
import logging

# Enable logging to see skipped entries
logging.basicConfig(level=logging.WARNING)

skipped_ids = []

def on_skip(item_id: str, reason: str) -> None:
    skipped_ids.append(item_id)

# Processing continues despite malformed entries
conversations = list(adapter.stream_conversations(
    path,
    on_skip=on_skip
))

print(f"Parsed {len(conversations)} conversations")
print(f"Skipped {len(skipped_ids)} malformed entries")
```

---

## Empty Conversation Handling

Claude exports may contain conversations with zero messages. The adapter handles this gracefully:

```python
# Empty conversation in export
{
  "uuid": "conv-123",
  "name": "Empty Chat",
  "created_at": "2025-10-01T18:42:27.303515Z",
  "updated_at": "2025-10-01T18:42:27.303515Z",
  "chat_messages": []
}

# Adapter inserts placeholder message
conversation = adapter.get_conversation_by_id(path, "conv-123")
print(len(conversation.messages))  # 1 (placeholder)
print(conversation.messages[0].content)  # "(Empty conversation)"
print(conversation.messages[0].metadata)  # {"is_placeholder": True}
```

This satisfies the `Conversation` model's requirement for at least one message while preserving data integrity.

---

## Type Safety

The adapter is fully type-checked with mypy --strict:

```python
from pathlib import Path
from echomine import ClaudeAdapter
from echomine.models import Conversation, Message, SearchResult
from typing import Iterator

adapter = ClaudeAdapter()

# Type inference works
conversations: Iterator[Conversation] = adapter.stream_conversations(Path("export.json"))

for conv in conversations:
    # IDE autocomplete and type checking
    title: str = conv.title
    message_count: int = len(conv.messages)

    # mypy catches errors at type-check time
    # invalid = conv.nonexistent_field  # AttributeError caught by mypy
```

---

## Constitution Compliance

The `ClaudeAdapter` adheres to all project constitution principles:

- **Principle I (Library-First)**: Importable adapter, no CLI dependencies
- **Principle VI (Strict Typing)**: mypy --strict, no `Any` types in public API
- **Principle VII (Multi-Provider)**: Stateless adapter implements ConversationProvider protocol
- **Principle VIII (Memory Efficiency)**: O(1) memory via ijson streaming

---

## See Also

- [OpenAIAdapter](openai.md) - Adapter for ChatGPT exports
- [ConversationProvider Protocol](protocols.md) - Adapter interface contract
- [Search Ranking](../search/ranking.md) - BM25 ranking and relevance scoring
- [SearchQuery Model](../models/search.md) - Search query parameters and filters
- [Conversation Model](../models/conversation.md) - Unified conversation schema
