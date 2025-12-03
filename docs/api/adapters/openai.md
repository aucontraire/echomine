# OpenAI Adapter

Adapter for parsing ChatGPT conversation exports.

## Overview

The `OpenAIAdapter` implements the `ConversationProvider` protocol for OpenAI (ChatGPT) conversation exports. It provides stateless, streaming-based parsing with O(1) memory usage.

## API Reference

::: echomine.adapters.openai.OpenAIAdapter
    options:
      show_source: true
      heading_level: 3

## Usage Examples

### Basic Setup

```python
from echomine import OpenAIAdapter
from pathlib import Path

# Create adapter (stateless, reusable)
adapter = OpenAIAdapter()
export_file = Path("conversations.json")
```

### Stream All Conversations

Memory-efficient iteration over all conversations:

```python
# Stream conversations (O(1) memory usage)
for conversation in adapter.stream_conversations(export_file):
    print(f"[{conversation.created_at.date()}] {conversation.title}")
    print(f"  Messages: {len(conversation.messages)}")
    print(f"  ID: {conversation.id}")
```

### Search with Keywords

Full-text search with BM25 ranking:

```python
from echomine.models import SearchQuery

# Create search query
query = SearchQuery(
    keywords=["algorithm", "leetcode"],
    limit=10
)

# Execute search
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

### Get Conversation by ID

Retrieve a specific conversation:

```python
# Get specific conversation
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")

if conversation:
    print(f"Found: {conversation.title}")
    print(f"Messages: {len(conversation.messages)}")
else:
    print("Conversation not found")
```

### Progress Reporting

Track progress for long-running operations:

```python
def progress_callback(count: int) -> None:
    """Called periodically during processing."""
    if count % 100 == 0:
        print(f"Processed {count:,} conversations...")

# Stream with progress reporting
for conversation in adapter.stream_conversations(
    export_file,
    progress_callback=progress_callback
):
    process(conversation)
```

### Graceful Degradation

Handle malformed entries gracefully:

```python
skipped_entries = []

def handle_skipped(conversation_id: str, reason: str) -> None:
    """Called when malformed entry is skipped."""
    skipped_entries.append({
        "id": conversation_id,
        "reason": reason,
    })

# Stream with skip handler
for conversation in adapter.stream_conversations(
    export_file,
    on_skip=handle_skipped
):
    process(conversation)

if skipped_entries:
    print(f"Skipped {len(skipped_entries)} malformed conversations")
```

## Methods

### stream_conversations()

Stream all conversations from export file.

**Signature:**

```python
def stream_conversations(
    self,
    file_path: Path,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
    on_skip: Optional[Callable[[str, str], None]] = None,
) -> Iterator[Conversation]:
    ...
```

**Parameters:**

- `file_path`: Path to OpenAI export JSON file
- `progress_callback`: Optional callback invoked periodically with conversation count
- `on_skip`: Optional callback invoked when malformed entry is skipped

**Returns:**

Iterator yielding `Conversation` objects.

**Raises:**

- `FileNotFoundError`: If file does not exist
- `PermissionError`: If file cannot be read
- `ParseError`: If export format is invalid
- `SchemaVersionError`: If export schema version is unsupported

**Memory Usage:** O(1) - constant memory regardless of file size.

### search()

Search conversations with BM25 ranking and filtering.

**Signature:**

```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
    on_skip: Optional[Callable[[str, str], None]] = None,
) -> Iterator[SearchResult[Conversation]]:
    ...
```

**Parameters:**

- `file_path`: Path to OpenAI export JSON file
- `query`: Search parameters (keywords, filters, limit)
- `progress_callback`: Optional callback for progress reporting
- `on_skip`: Optional callback for skipped entries

**Returns:**

Iterator yielding `SearchResult[Conversation]` objects, sorted by relevance score (descending).

**Raises:**

Same as `stream_conversations()`.

**Performance:**

- Title-only search: <5 seconds for 10K conversations (metadata-only)
- Keyword search: <30 seconds for 1.6GB files (full-text with BM25)

### get_conversation_by_id()

Retrieve a specific conversation by ID.

**Signature:**

```python
def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str,
) -> Optional[Conversation]:
    ...
```

**Parameters:**

- `file_path`: Path to OpenAI export JSON file
- `conversation_id`: ID of conversation to retrieve

**Returns:**

`Conversation` if found, `None` otherwise.

**Raises:**

Same as `stream_conversations()`.

**Performance:** Early termination - stops searching after finding conversation.

## Adapter Pattern

### Stateless Design

`OpenAIAdapter` has no `__init__` parameters and maintains no internal state:

```python
# ✅ CORRECT: Reusable adapter
adapter = OpenAIAdapter()

for file in export_files:
    for conv in adapter.stream_conversations(file):
        process(conv)
```

**Benefits:**

- Thread-safe (no shared state)
- Reusable across multiple files
- Simple, predictable behavior

### Protocol Implementation

Implements `ConversationProvider` protocol:

```python
from echomine.protocols import ConversationProvider

# Type-safe adapter usage
def process_export(
    adapter: ConversationProvider,  # Works with ANY adapter
    file_path: Path
) -> None:
    for conv in adapter.stream_conversations(file_path):
        print(conv.title)

# OpenAIAdapter implements protocol
process_export(OpenAIAdapter(), Path("export.json"))
```

## OpenAI-Specific Behavior

### Export Format

Expects OpenAI ChatGPT export JSON format:

```json
[
  {
    "id": "conv-uuid",
    "title": "Conversation Title",
    "create_time": 1704974400.0,
    "update_time": 1704974500.0,
    "mapping": {
      "msg-uuid-1": {
        "id": "msg-uuid-1",
        "message": {
          "id": "msg-uuid-1",
          "author": {"role": "user"},
          "content": {"content_type": "text", "parts": ["Hello"]},
          "create_time": 1704974410.0
        },
        "parent": null,
        "children": ["msg-uuid-2"]
      }
    }
  }
]
```

### Metadata Mapping

Provider-specific fields stored in `conversation.metadata`:

- `openai_model`: Model used (e.g., "gpt-4")
- `openai_conversation_template_id`: Template ID
- `openai_plugin_ids`: List of plugin IDs used
- `openai_moderation_results`: Moderation results (if any)

**Example:**

```python
conversation = adapter.get_conversation_by_id(file_path, "conv-123")
model = conversation.metadata.get("openai_model", "unknown")
print(f"Model: {model}")
```

### Role Normalization

OpenAI roles are already normalized (no mapping needed):

- "user" → "user"
- "assistant" → "assistant"
- "system" → "system"

## Error Handling

### Exceptions

```python
from echomine import (
    ParseError,          # Malformed JSON/structure
    ValidationError,     # Invalid data
    SchemaVersionError,  # Unsupported version
)

try:
    for conv in adapter.stream_conversations(file_path):
        process(conv)
except ParseError as e:
    print(f"Export file corrupted: {e}")
except SchemaVersionError as e:
    print(f"Unsupported export version: {e}")
except FileNotFoundError:
    print(f"File not found: {file_path}")
```

### Graceful Degradation

Malformed conversations are skipped with warnings logged:

```python
# Skipped entries logged as WARNING
# Processing continues for valid entries
for conv in adapter.stream_conversations(file_path):
    # Only valid conversations yielded
    process(conv)
```

## Concurrency

### Thread Safety

- **Adapter instances**: Thread-safe (stateless)
- **Iterators**: NOT thread-safe (each thread needs its own)

```python
from threading import Thread

adapter = OpenAIAdapter()  # SAFE: Share adapter

def worker(thread_id):
    # SAFE: Each thread creates its own iterator
    for conv in adapter.stream_conversations(file_path):
        process(conv, thread_id)

threads = [Thread(target=worker, args=(i,)) for i in range(4)]
```

### Multi-Process Safety

Multiple processes can read the same file concurrently:

```python
from multiprocessing import Process

def worker(process_id):
    adapter = OpenAIAdapter()  # Each process has its own adapter
    for conv in adapter.stream_conversations(file_path):
        process(conv, process_id)

processes = [Process(target=worker, args=(i,)) for i in range(4)]
```

## Performance

### Memory Efficiency

- **O(1) memory usage**: Constant memory regardless of file size
- **Streaming**: Uses ijson for incremental parsing
- **No buffering**: Yields conversations as they're parsed

### Speed

- **10K conversations**: <5 seconds for listing (metadata-only)
- **1.6GB file**: <30 seconds for keyword search
- **Early termination**: `get_conversation_by_id` stops after finding match

## Related

- **[ConversationProvider Protocol](protocols.md)**: Protocol definition
- **[Conversation Model](../models/conversation.md)**: Result type
- **[SearchQuery](../models/search.md)**: Search parameters

## See Also

- [Library Usage Guide](../../library-usage.md)
- [Architecture](../../architecture.md#adapter-pattern)
