# Library Usage Guide

This guide covers comprehensive usage of Echomine as a Python library. Perfect for integrating with tools like cognivault or building custom analysis workflows.

## Installation

```bash
pip install echomine
```

See [Installation](installation.md) for details.

## Core Concepts

### Library-First Architecture

Echomine is designed as a library first, with the CLI built on top. All functionality is available programmatically:

```python
from echomine import OpenAIAdapter
from echomine.models import SearchQuery

# Core library components
adapter = OpenAIAdapter()          # Stateless adapter
query = SearchQuery(keywords=["python"])  # Type-safe query model

# Use in your application
for result in adapter.search(file_path, query):
    process(result.conversation)
```

### Stateless Adapters

Adapters have no `__init__` parameters and maintain no internal state:

```python
# Reusable across different files
adapter = OpenAIAdapter()

for file in export_files:
    for conv in adapter.stream_conversations(file):
        process(conv)
```

### Streaming Operations

All operations use generators for O(1) memory usage:

```python
# Handles 1GB+ files with constant memory
for conversation in adapter.stream_conversations(large_file):
    # Process one at a time
    analyze(conversation)
```

## Basic Operations

### Stream All Conversations

Memory-efficient iteration over all conversations:

```python
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")

for conversation in adapter.stream_conversations(export_file):
    print(f"{conversation.title} ({conversation.created_at})")
    print(f"  Messages: {len(conversation.messages)}")
```

### Search with Keywords

Find conversations matching specific keywords with BM25 ranking:

```python
from echomine.models import SearchQuery

query = SearchQuery(
    keywords=["algorithm", "leetcode"],
    limit=10
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

### Filter by Title

Fast metadata-only search:

```python
query = SearchQuery(
    title_filter="Project",  # Partial match, case-insensitive
    limit=10
)

for result in adapter.search(export_file, query):
    print(result.conversation.title)
```

### Filter by Date Range

Narrow down conversations by creation date:

```python
from datetime import date

query = SearchQuery(
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    keywords=["refactor"],
    limit=5
)

for result in adapter.search(export_file, query):
    print(f"{result.conversation.title} - {result.conversation.created_at}")
```

### Get Conversation by ID

Retrieve a specific conversation:

```python
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")

if conversation:
    print(f"Found: {conversation.title}")
else:
    print("Conversation not found")
```

### Get Message by ID

Retrieve a specific message with its parent conversation context:

```python
# Search all conversations for the message
result = adapter.get_message_by_id(export_file, "msg-def456")

if result:
    message, conversation = result
    print(f"Message: {message.content}")
    print(f"From conversation: {conversation.title}")
    print(f"Role: {message.role}")
    print(f"Timestamp: {message.timestamp}")
else:
    print("Message not found")
```

For better performance with large files, provide a conversation ID hint:

```python
# Faster: search only within specified conversation
result = adapter.get_message_by_id(
    export_file,
    "msg-def456",
    conversation_id="conv-abc123"
)

if result:
    message, conversation = result
    print(f"Found message in {conversation.title}")
```

**Performance Note:**

- Without `conversation_id`: O(N*M) - searches all conversations and their messages
- With `conversation_id`: O(N) - searches only until the specified conversation is found

## Advanced Usage

### Message Tree Navigation

Conversations can have branching message trees (e.g., regenerated AI responses). Helper methods to navigate:

```python
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")

# Get all threads (root-to-leaf paths)
threads = conversation.get_all_threads()

print(f"Conversation has {len(threads)} branches:")
for i, thread in enumerate(threads, 1):
    print(f"\nThread {i} ({len(thread)} messages):")
    for msg in thread:
        print(f"  {msg.role}: {msg.content[:50]}...")

# Get specific thread by leaf message ID
thread = conversation.get_thread("msg-xyz-789")

# Get root messages
roots = conversation.get_root_messages()

# Get children of a message
children = conversation.get_children("msg-abc-123")

# Check if message has children
has_branches = conversation.has_children("msg-abc-123")
```

### Data Validation and Immutability

All models use Pydantic with strict validation and immutability:

```python
from pydantic import ValidationError

# Models are frozen (immutable)
try:
    conversation.title = "New Title"  # Raises ValidationError
except ValidationError as e:
    print(f"Error: {e}")

# Create modified copy instead
updated = conversation.model_copy(update={"title": "New Title"})
print(f"Original: {conversation.title}")
print(f"Updated: {updated.title}")
```

### Timezone-Aware Timestamps

All timestamps are timezone-aware UTC datetimes:

```python
from datetime import timezone

for message in conversation.messages:
    # All timestamps guaranteed to be UTC
    assert message.timestamp.tzinfo == timezone.utc

    # Safe to compare and serialize
    print(f"{message.timestamp.isoformat()}: {message.content[:30]}...")

# Convert to local timezone for display
import datetime
local_tz = datetime.datetime.now().astimezone().tzinfo
for msg in conversation.messages:
    local_time = msg.timestamp.astimezone(local_tz)
    print(f"[{local_time}] {msg.role}: {msg.content[:30]}...")
```

### Role Normalization

Message roles are normalized to standard values:

```python
# Message.role is Literal["user", "assistant", "system"]
for message in conversation.messages:
    if message.role == "user":
        print(f"User: {message.content}")
    elif message.role == "assistant":
        print(f"AI: {message.content}")
    elif message.role == "system":
        print(f"System: {message.content}")
    # No other values possible - type safety guaranteed!
```

## Error Handling

### Exception Hierarchy

All library operational errors inherit from `EchomineError`:

```python
from echomine import (
    OpenAIAdapter,
    EchomineError,      # Base exception
    ParseError,         # Malformed JSON/structure
    ValidationError,    # Pydantic validation failures
    SchemaVersionError  # Unsupported schema version
)
```

### Recommended Error Handling Pattern

For library consumers (e.g., cognivault integration):

```python
from echomine import OpenAIAdapter, EchomineError
import structlog

logger = structlog.get_logger()

try:
    adapter = OpenAIAdapter()
    for conversation in adapter.stream_conversations(export_file):
        knowledge_base.ingest(conversation)

except EchomineError as e:
    # All library operational errors
    logger.error("echomine_parsing_failed", error=str(e))
    # Handle gracefully: notify user, log error, skip file

except (FileNotFoundError, PermissionError) as e:
    # Filesystem errors (not wrapped by library)
    logger.error("file_access_failed", error=str(e))
    # Handle: check permissions, verify path

except Exception as e:
    # Unexpected errors (library bugs or system issues)
    logger.exception("unexpected_error", error=str(e))
    raise  # Re-raise to surface bugs
```

### Specific Exception Types

```python
# ParseError (malformed export)
from echomine import ParseError

try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
except ParseError as e:
    print(f"Export file corrupted: {e}")

# ValidationError (invalid data)
from echomine import ValidationError

try:
    results = adapter.search(export_file, query)
except ValidationError as e:
    print(f"Invalid query or data: {e}")

# SchemaVersionError (unsupported version)
from echomine import SchemaVersionError

try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
except SchemaVersionError as e:
    print(f"Unsupported export version: {e}")
```

## Progress Reporting

### Custom Progress Callback

Implement custom progress handlers:

```python
def my_progress_handler(count: int) -> None:
    """Custom progress callback for UI or logging."""
    if count % 100 == 0:
        print(f"Processed {count:,} conversations...")

adapter = OpenAIAdapter()
for conversation in adapter.stream_conversations(
    Path("large_export.json"),
    progress_callback=my_progress_handler
):
    knowledge_base.ingest(conversation)

print("Ingestion complete!")
```

### Graceful Degradation

Track malformed entries that were skipped:

```python
skipped_entries = []

def handle_skipped(conversation_id: str, reason: str) -> None:
    """Called when malformed entry is skipped."""
    skipped_entries.append({
        "id": conversation_id,
        "reason": reason,
    })
    logger.warning("conversation_skipped", conv_id=conversation_id, reason=reason)

for conv in adapter.stream_conversations(export_file, on_skip=handle_skipped):
    process(conv)

if skipped_entries:
    print(f"Skipped {len(skipped_entries)} conversations")
```

## Concurrency

### Multi-Process Concurrent Reads (Safe)

Multiple processes can read the same file:

```python
from multiprocessing import Process
from echomine import OpenAIAdapter
from pathlib import Path

def worker_process(export_file, process_id):
    """Each process creates its own adapter instance."""
    adapter = OpenAIAdapter()
    for conv in adapter.stream_conversations(export_file):
        print(f"[Process {process_id}] Processing: {conv.title}")

# Safe: Multiple processes, same file
export_file = Path("conversations.json")
processes = [
    Process(target=worker_process, args=(export_file, i))
    for i in range(4)
]

for p in processes:
    p.start()
for p in processes:
    p.join()
```

### Multi-Threading (Safe Pattern)

Adapter instances are thread-safe, but iterators are NOT:

```python
from threading import Thread
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()  # SAFE: Share adapter across threads

def worker_thread(thread_id):
    """Each thread creates its own iterator."""
    # SAFE: Each thread calls stream_conversations separately
    for conv in adapter.stream_conversations(export_file):
        process(conv, thread_id)

threads = [Thread(target=worker_thread, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Integration Examples

### cognivault Integration

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path
from typing import Iterator

class CognivaultIngestionPipeline:
    """Ingest AI conversation data into cognivault knowledge graph."""

    def __init__(self, cognivault_client):
        self.adapter = OpenAIAdapter()
        self.cognivault = cognivault_client

    def ingest_export_file(self, export_file: Path) -> int:
        """Ingest all conversations from export file."""
        count = 0
        for conversation in self.adapter.stream_conversations(export_file):
            knowledge_node = {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "content": self._flatten_messages(conversation),
                "tags": self._extract_tags(conversation),
            }

            self.cognivault.ingest_node(knowledge_node)
            count += 1

        return count

    def ingest_filtered_conversations(
        self,
        export_file: Path,
        project_tag: str
    ) -> int:
        """Ingest only conversations matching a project tag."""
        query = SearchQuery(keywords=[project_tag], limit=1000)

        count = 0
        for result in self.adapter.search(export_file, query):
            knowledge_node = {
                "id": result.conversation.id,
                "title": result.conversation.title,
                "relevance": result.score,
                "content": self._flatten_messages(result.conversation),
                "project": project_tag,
            }

            self.cognivault.ingest_node(knowledge_node)
            count += 1

        return count

    def _flatten_messages(self, conversation) -> str:
        """Flatten conversation messages to text."""
        return "\\n\\n".join(
            f"{msg.role}: {msg.content}"
            for msg in conversation.messages
        )

    def _extract_tags(self, conversation) -> list[str]:
        """Extract tags from conversation content."""
        # Implement your tag extraction logic
        return []


# Usage
pipeline = CognivaultIngestionPipeline(cognivault_client)
count = pipeline.ingest_export_file(Path("conversations.json"))
print(f"Ingested {count} conversations into cognivault")
```

## Performance Tips

1. **Use streaming for large files**: Don't convert iterators to lists
2. **Limit search results**: Use `limit` parameter
3. **Use title filtering when possible**: Faster than full-text search
4. **Monitor memory**: Streaming uses O(1) memory

## Type Safety

Echomine provides full type hints for IDE support:

```python
from echomine import OpenAIAdapter
from echomine.models import Conversation, SearchResult
from typing import Iterator

adapter: OpenAIAdapter = OpenAIAdapter()

# IDE autocomplete works!
conversations: Iterator[Conversation] = adapter.stream_conversations(export_file)

for conv in conversations:
    # Type checker knows these fields exist
    title: str = conv.title
    message_count: int = len(conv.messages)
```

## Next Steps

- [API Reference](api/index.md): Detailed API documentation
- [CLI Usage](cli-usage.md): Command-line interface reference
- [Architecture](architecture.md): Design principles and patterns
- [Contributing](contributing.md): Development guidelines
