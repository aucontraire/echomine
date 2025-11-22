# Quickstart: Echomine Library Usage

**Feature**: 001-ai-chat-parser
**Date**: 2025-11-21
**Audience**: Python developers integrating Echomine as a library

## Overview

This guide shows how to use Echomine programmatically in your Python applications. Perfect for tools like cognivault that need to ingest AI conversation data.

## Installation

```bash
# Install via pip (when published)
pip install echomine

# Or install from source
git clone https://github.com/yourorg/echomine.git
cd echomine
poetry install
```

**Requirements**:
- Python 3.12+
- 8GB RAM (for processing large exports)

---

## Basic Usage

### Import and Setup

```python
from echomine import OpenAIAdapter
from echomine.models import SearchQuery
from pathlib import Path

# Create adapter for ChatGPT exports
adapter = OpenAIAdapter()
export_file = Path("path/to/conversations.json")
```

---

## Common Workflows

### 1. List All Conversations (Discovery)

Browse what's in your export file before searching or exporting.

```python
# List all conversations with metadata
for conversation in adapter.stream_conversations(export_file):
    print(f"[{conversation.created_at.date()}] {conversation.title}")
    print(f"  Messages: {len(conversation.messages)}")
    print(f"  ID: {conversation.id}")
    print()
```

**Use case**: Discover what conversations exist in an export file (like `ls` for files).

**CLI equivalent**:
```bash
# Human-readable list
echomine list conversations.json

# JSON output for processing
echomine list conversations.json --json

# Limit to 10 most recent
echomine list conversations.json --limit 10
```

---

### 2. Stream All Conversations

Memory-efficient iteration over all conversations (doesn't load entire file).

```python
# Stream conversations one at a time
for conversation in adapter.stream_conversations(export_file):
    print(f"{conversation.title} ({conversation.created_at})")
    print(f"  Messages: {len(conversation.messages)}")
```

**Use case**: Process all conversations without memory constraints (1GB+ files).

---

### 3. Search by Keywords

Find conversations matching specific topics with relevance ranking.

```python
# Create search query
query = SearchQuery(
    keywords=["algorithm", "leetcode"],
    limit=5
)

# Execute search (returns iterator)
for result in adapter.search(export_file, query):
    print(f"[{result.relevance_score:.2f}] {result.conversation.title}")
    print(f"  Excerpt: {result.excerpt}")
    print(f"  Matched: {', '.join(result.matched_keywords)}")
```

**Use case**: Keyword-based discovery of relevant conversations.

---

### 4. Filter by Title (Fast Metadata Search)

Search conversation titles without scanning message content.

```python
# Title-based filtering (fast, metadata-only)
query = SearchQuery(
    title_filter="Project",  # Partial match, case-insensitive
    limit=10
)

for result in adapter.search(export_file, query):
    print(result.conversation.title)
```

**Use case**: When you remember the conversation title from ChatGPT app.

---

### 5. Combined Filtering

Combine multiple filters for precision.

```python
from datetime import date

query = SearchQuery(
    keywords=["refactor"],
    title_filter="Project",
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    limit=5
)

for result in adapter.search(export_file, query):
    print(f"{result.conversation.title} - {result.conversation.created_at}")
```

**Use case**: Narrow down results with multiple criteria.

---

### 6. Export Conversation to Markdown

Retrieve conversation by ID and export to markdown.

```python
# Get conversation by ID
conversation = adapter.get_conversation_by_id(export_file, "conv-uuid-123")

if conversation:
    # Export to markdown
    from echomine.exporters import MarkdownExporter

    exporter = MarkdownExporter()
    markdown_content = exporter.export(conversation)

    # Save to file
    output_path = Path("output/conversation.md")
    output_path.write_text(markdown_content, encoding="utf-8")
    print(f"Exported to {output_path}")
else:
    print("Conversation not found")
```

**Use case**: Extract specific conversation for documentation.

---

## Advanced: cognivault Integration Pattern

Example of using Echomine in a knowledge management system (primary use case).

```python
from echomine import OpenAIAdapter
from echomine.models import SearchQuery
from pathlib import Path
from typing import Iterator

class CognivaultIngestionPipeline:
    """
    Ingest AI conversation data into cognivault knowledge graph.

    This demonstrates the library-first architecture (Constitution Principle I):
    - Echomine provides typed, validated conversation data
    - cognivault focuses on knowledge graph operations
    - Clean separation of concerns
    """

    def __init__(self, cognivault_client):
        self.adapter = OpenAIAdapter()
        self.cognivault = cognivault_client

    def ingest_export_file(self, export_file: Path) -> int:
        """
        Ingest all conversations from export file into cognivault.

        Returns:
            Number of conversations ingested
        """
        count = 0
        for conversation in self.adapter.stream_conversations(export_file):
            # Transform echomine data to cognivault format
            knowledge_node = {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "content": conversation.flatten_messages(),
                "tags": self._extract_tags(conversation),
            }

            # Ingest into knowledge graph
            self.cognivault.ingest_node(knowledge_node)
            count += 1

        return count

    def ingest_filtered_conversations(
        self,
        export_file: Path,
        project_tag: str
    ) -> int:
        """
        Ingest only conversations matching a project tag.

        Example: Ingest all conversations related to "project-x"
        """
        query = SearchQuery(
            keywords=[project_tag],
            limit=1000  # Process up to 1000 matches
        )

        count = 0
        for result in self.adapter.search(export_file, query):
            knowledge_node = {
                "id": result.conversation.id,
                "title": result.conversation.title,
                "relevance": result.relevance_score,
                "content": result.conversation.flatten_messages(),
                "project": project_tag,
            }

            self.cognivault.ingest_node(knowledge_node)
            count += 1

        return count

    def _extract_tags(self, conversation) -> list[str]:
        """Extract tags from conversation content (simple keyword extraction)."""
        # Implement your tag extraction logic
        return []


# Usage
pipeline = CognivaultIngestionPipeline(cognivault_client)
count = pipeline.ingest_export_file(Path("conversations.json"))
print(f"Ingested {count} conversations into cognivault")
```

**Key benefits**:
1. Type safety: Pydantic models provide IDE autocomplete and type checking
2. Memory efficiency: Streaming prevents OOM errors on large files
3. Clean API: Simple, predictable methods (stream, search, get_by_id)
4. Extensibility: Easy to add custom processing logic

---

## Type Safety Example

Echomine provides full type hints for IDE support:

```python
from echomine import OpenAIAdapter
from echomine.models import Conversation, SearchResult

adapter: OpenAIAdapter = OpenAIAdapter()

# IDE autocomplete works!
conversations: Iterator[Conversation] = adapter.stream_conversations(export_file)

for conv in conversations:
    # Type checker knows these fields exist
    title: str = conv.title
    message_count: int = len(conv.messages)

    # mypy catches this error!
    # invalid_field = conv.nonexistent_field  # AttributeError caught at type-check time
```

---

## Message Tree Navigation

Conversations can have branching message trees (e.g., regenerated AI responses). Echomine provides helper methods to navigate these structures (per FR-276, FR-277, FR-278, FR-280).

### Extracting All Conversation Threads

```python
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()
conversation = adapter.get_conversation_by_id(
    Path("conversations.json"),
    "conv-uuid-123"
)

if conversation:
    # Get all threads (root-to-leaf paths)
    threads = conversation.get_all_threads()

    print(f"Conversation has {len(threads)} branches:")
    for i, thread in enumerate(threads, 1):
        print(f"\n📍 Thread {i} ({len(thread)} messages):")
        for msg in thread:
            role_icon = "👤" if msg.role == "user" else "🤖"
            preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"  {role_icon} {msg.role}: {preview}")
```

**Use case**: Extract all conversation branches for comparison or display.

### Navigating Specific Thread

```python
# Get a specific thread by leaf message ID
leaf_message_id = "msg-xyz-789"
thread = conversation.get_thread(leaf_message_id)

if thread:
    print(f"Thread to message {leaf_message_id}:")
    for msg in thread:
        print(f"  [{msg.timestamp}] {msg.role}: {msg.content[:30]}...")
```

**Use case**: Reconstruct conversation path to a specific message.

### Tree Structure Helpers

```python
# Get root messages (conversation starters)
roots = conversation.get_root_messages()
print(f"Conversation has {len(roots)} root message(s)")

# Get children of a specific message
message = conversation.messages[0]
children = conversation.get_children(message.id)

if children:
    print(f"Message '{message.id}' has {len(children)} branches:")
    for child in children:
        print(f"  → {child.role}: {child.content[:40]}...")
else:
    print(f"Message '{message.id}' is a leaf (no children)")

# Check if message has children
has_branches = conversation.has_children(message.id)
print(f"Has branches: {has_branches}")
```

**Use case**: Custom tree traversal algorithms.

---

## Data Immutability & Validation

All Echomine models use Pydantic with strict validation and immutability guarantees (per FR-223, FR-227, FR-239, FR-244).

### Immutable Models (Frozen)

```python
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()
conversation = adapter.get_conversation_by_id(
    Path("conversations.json"),
    "conv-uuid-123"
)

# ❌ This will raise ValidationError (models are frozen)
try:
    conversation.title = "New Title"
except ValidationError as e:
    print(f"Error: {e}")  # "Instance is frozen"

# ✅ Create modified copy instead
updated_conversation = conversation.model_copy(update={"title": "New Title"})
print(f"Original: {conversation.title}")
print(f"Updated: {updated_conversation.title}")
```

**Rationale**: Immutability prevents accidental data corruption during processing.

### Role Normalization

Message roles are normalized to standard values using `Literal` type (per FR-239, FR-240):

```python
# Message.role is Literal["user", "assistant", "system"]
for message in conversation.messages:
    # Role is guaranteed to be one of three values
    if message.role == "user":
        print(f"User: {message.content}")
    elif message.role == "assistant":
        print(f"AI: {message.content}")
    elif message.role == "system":
        print(f"System: {message.content}")
    # No other values possible - type safety guaranteed!
```

**Benefits**:
- Type-safe role checking (IDE autocomplete)
- No need for defensive validation
- Provider-specific roles automatically normalized

### Timezone-Aware Timestamps

All timestamps are timezone-aware UTC datetimes (per FR-244, FR-245, FR-246):

```python
from datetime import timezone

for message in conversation.messages:
    # All timestamps guaranteed to be UTC and timezone-aware
    assert message.timestamp.tzinfo is not None
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

**Guarantees**:
- No naive datetimes (always timezone-aware)
- Normalized to UTC for consistency
- Safe cross-timezone comparisons

### Strict Validation

Pydantic validation prevents invalid data (per FR-226, FR-227):

```python
from echomine.models import Message
from datetime import datetime, timezone

# ❌ This will raise ValidationError (missing required fields)
try:
    invalid_msg = Message(
        id="msg-1",
        content="Hello"
        # Missing: role, timestamp, parent_id
    )
except ValidationError as e:
    print(f"Validation failed: {e}")

# ❌ This will raise ValidationError (naive timestamp)
try:
    invalid_msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=datetime.now(),  # ❌ Not timezone-aware!
        parent_id=None
    )
except ValidationError as e:
    print(f"Timestamp must be timezone-aware: {e}")

# ✅ Correct usage
valid_msg = Message(
    id="msg-1",
    content="Hello",
    role="user",
    timestamp=datetime.now(timezone.utc),  # ✅ UTC timezone-aware
    parent_id=None
)
```

**Protection**:
- Required fields enforced
- Type coercion disabled (`strict=True`)
- Unknown fields rejected (`extra="forbid"`)
- Custom validators ensure data quality

---

## Error Handling

Echomine follows fail-fast error handling with a clear exception contract (per FR-035 through FR-063).

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
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")
```

### Comprehensive Error Handling (cognivault Pattern)

**Recommended pattern for library consumers** (per FR-061, FR-062):

```python
from echomine import OpenAIAdapter, EchomineError
import structlog

logger = structlog.get_logger()

try:
    adapter = OpenAIAdapter()
    for conversation in adapter.stream_conversations(export_file):
        cognivault.knowledge_graph.ingest(conversation)

except EchomineError as e:
    # All library operational errors
    logger.error("echomine_parsing_failed", error=str(e), export_file=str(export_file))
    # Handle gracefully: notify user, log error, skip file, etc.

except (FileNotFoundError, PermissionError) as e:
    # Filesystem errors (not wrapped by library)
    logger.error("file_access_failed", error=str(e), file_path=str(export_file))
    # Handle: check permissions, verify path, prompt user

except Exception as e:
    # Unexpected errors (library bugs or system issues)
    logger.exception("unexpected_error", error=str(e))
    raise  # Re-raise to surface bugs

# NEVER catch these (per FR-063):
# - KeyboardInterrupt (user cancellation)
# - SystemExit (shutdown signals)
# - MemoryError (system-level, can't recover)
```

### Specific Exception Types

**ParseError** (malformed export):
```python
from echomine import ParseError

try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
except ParseError as e:
    print(f"Export file corrupted: {e}")
    print("Try re-exporting from ChatGPT")
```

**ValidationError** (invalid data):
```python
from echomine import ValidationError

try:
    results = adapter.search(export_file, query)
except ValidationError as e:
    print(f"Invalid query or data: {e}")
    # Check date formats, keyword syntax, etc.
```

**SchemaVersionError** (unsupported version):
```python
from echomine import SchemaVersionError

try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
except SchemaVersionError as e:
    print(f"Unsupported export version: {e}")
    print("Upgrade echomine or re-export from ChatGPT")
```

**No retries**: All errors are permanent (per FR-042, FR-043). Users must fix the issue and retry manually.

---

## Progress Indicators & Callbacks

### Custom Progress Reporting

Library consumers can implement custom progress handlers (per FR-076, FR-077):

```python
from echomine import OpenAIAdapter
from pathlib import Path

def my_progress_handler(count: int) -> None:
    """Custom progress callback for UI or logging."""
    if count % 100 == 0:  # Log every 100 conversations
        print(f"📊 Processed {count:,} conversations...")

adapter = OpenAIAdapter()
for conversation in adapter.stream_conversations(
    Path("large_export.json"),
    progress_callback=my_progress_handler
):
    cognivault.ingest(conversation)

print("✅ Ingestion complete!")
```

### Graceful Degradation: Handling Skipped Entries

Track malformed entries that were skipped (per FR-106, FR-107):

```python
skipped_entries = []

def handle_skipped(conversation_id: str, reason: str) -> None:
    """Called when malformed entry is skipped."""
    skipped_entries.append({
        "id": conversation_id,
        "reason": reason,
        "timestamp": datetime.utcnow()
    })
    logger.warning("conversation_skipped", conv_id=conversation_id, reason=reason)

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(
    export_file,
    on_skip=handle_skipped
):
    process(conv)

# Summary reporting (per FR-110, FR-112)
if skipped_entries:
    print(f"⚠️  Skipped {len(skipped_entries)} conversations (see logs for details)")
    # Optionally save skip report
    with open("skipped_report.json", "w") as f:
        json.dump(skipped_entries, f, indent=2)
```

### Combined: Progress + Skip Handling

```python
processed_count = 0
skipped_count = 0

def progress(count):
    global processed_count
    processed_count = count
    print(f"⏳ Progress: {count:,} conversations processed...", end="\r")

def on_skip(conv_id, reason):
    global skipped_count
    skipped_count += 1

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(
    export_file,
    progress_callback=progress,
    on_skip=on_skip
):
    cognivault.ingest(conv)

print(f"\n✅ Completed: {processed_count:,} processed, {skipped_count} skipped")
```

---

## Concurrency & Thread Safety

### Multi-Process Concurrent Reads (Safe)

Multiple processes can read the same file concurrently (per FR-094, FR-095):

```python
from multiprocessing import Process
from echomine import OpenAIAdapter
from pathlib import Path

def worker_process(export_file, process_id):
    """Each process creates its own adapter instance."""
    adapter = OpenAIAdapter()  # Independent file handle
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

Adapter instances are thread-safe, but iterators are NOT (per FR-098, FR-099, FR-100):

```python
from threading import Thread
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()  # ✅ SAFE: Share adapter across threads

def worker_thread(thread_id):
    """Each thread creates its own iterator."""
    # ✅ SAFE: Each thread calls stream_conversations separately
    for conv in adapter.stream_conversations(export_file):
        process(conv, thread_id)

threads = [Thread(target=worker_thread, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### ❌ UNSAFE Threading Pattern

**Do NOT share iterators across threads** (per FR-099):

```python
# ❌ WRONG: Sharing iterator across threads causes race conditions
adapter = OpenAIAdapter()
iterator = adapter.stream_conversations(export_file)  # Single iterator

def worker_thread():
    for conv in iterator:  # ❌ RACE CONDITION: Multiple threads consuming same iterator
        process(conv)

# This will corrupt iterator state and produce undefined behavior
threads = [Thread(target=worker_thread) for _ in range(4)]
```

### File Immutability Assumption

Library assumes export files are immutable during read (per FR-096, FR-102, FR-104):

```python
# ✅ SAFE: File not modified during read
for conv in adapter.stream_conversations(export_file):
    process(conv)

# ❌ UNSAFE: External process modifying file during read
# If another process writes to the file while library is reading,
# behavior is UNDEFINED (may see partial data, corruption, or errors)

# Best practice: Use temp copies if modification is possible
import shutil
temp_copy = Path("/tmp/conversations_copy.json")
shutil.copy(export_file, temp_copy)
for conv in adapter.stream_conversations(temp_copy):
    process(conv)
temp_copy.unlink()  # Clean up
```

---

## Performance Tips

### 1. Use Streaming for Large Files

```python
# ✅ Good: Memory-efficient streaming
for conversation in adapter.stream_conversations(large_file):
    process(conversation)

# ❌ Bad: Loads entire file into memory
all_conversations = list(adapter.stream_conversations(large_file))  # OOM risk!
```

### 2. Limit Search Results

```python
# ✅ Good: Limit results for responsiveness
query = SearchQuery(keywords=["term"], limit=10)

# ❌ Bad: Processing thousands of results
query = SearchQuery(keywords=["term"], limit=10000)  # Slow!
```

### 3. Use Title Filtering When Possible

```python
# ✅ Fast: Title filtering (metadata-only)
query = SearchQuery(title_filter="Project")

# ✅ Slower: Keyword search (full-text)
query = SearchQuery(keywords=["Project"])  # Scans all message content
```

---

## Testing Your Integration

```python
import pytest
from pathlib import Path
from echomine import OpenAIAdapter

def test_echomine_integration():
    """Test that echomine can parse your export file."""
    adapter = OpenAIAdapter()
    export_file = Path("tests/fixtures/sample_export.json")

    # Stream conversations
    conversations = list(adapter.stream_conversations(export_file))

    # Assert expected data
    assert len(conversations) > 0
    assert all(conv.title for conv in conversations)
    assert all(len(conv.messages) > 0 for conv in conversations)
```

---

## Multi-Provider Support (Future)

### Adapter Selection

Library v1.0 supports OpenAI (ChatGPT) exports only. Future versions will add adapters for other providers.

**Current (v1.0) - Explicit Selection**:
```python
from echomine import OpenAIAdapter

# User explicitly selects OpenAI adapter
adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(Path("chatgpt_export.json")):
    process(conv)
```

**Future (v2.0+) - Multiple Providers**:
```python
# Explicit selection (recommended)
from echomine import OpenAIAdapter, AnthropicAdapter, GoogleAdapter

# Choose based on export source
if export_source == "chatgpt":
    adapter = OpenAIAdapter()
elif export_source == "claude":
    adapter = AnthropicAdapter()
elif export_source == "gemini":
    adapter = GoogleAdapter()

for conv in adapter.stream_conversations(export_file):
    process(conv)
```

**Auto-Detection** (v2.0+, opt-in):
```python
from echomine import detect_adapter

# Optional helper for auto-detection (less reliable)
try:
    adapter_class = detect_adapter(export_file)
    adapter = adapter_class()
except UnknownFormatError:
    # Fallback: user selects manually
    print("Could not detect format. Please specify adapter.")
```

---

### Provider-Specific Metadata

All adapters return normalized `Conversation` models with provider-specific data in `metadata` dict.

**Accessing Provider-Specific Fields**:
```python
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(export_file):
    # Standard fields (all providers)
    print(f"Title: {conv.title}")
    print(f"Created: {conv.created_at}")
    print(f"Messages: {len(conv.messages)}")

    # OpenAI-specific metadata
    openai_model = conv.metadata.get("openai_model", "unknown")
    print(f"Model: {openai_model}")

    # Check if specific metadata exists
    if "openai_plugin_ids" in conv.metadata:
        plugins = conv.metadata["openai_plugin_ids"]
        print(f"Plugins used: {', '.join(plugins)}")
```

**Example Metadata by Provider**:
```python
# OpenAI metadata fields
{
    "openai_model": "gpt-4",
    "openai_conversation_template_id": "template-456",
    "openai_plugin_ids": ["plugin-789"],
    "openai_moderation_results": [],
}

# Anthropic metadata fields (future)
{
    "claude_model": "claude-3-sonnet",
    "claude_workspace_id": "ws-xyz",
}

# Google metadata fields (future)
{
    "gemini_model": "gemini-pro",
    "gemini_system_instruction": "You are a helpful assistant.",
}
```

---

### Adapter Interchangeability

All adapters implement the same protocol, enabling seamless provider switching.

**Provider-Agnostic Processing**:
```python
from typing import Iterator
from echomine.protocols import ConversationProvider
from echomine.models import Conversation

def process_export(
    adapter: ConversationProvider,  # Works with ANY adapter
    export_file: Path
) -> int:
    """Process export file using any provider adapter."""
    count = 0
    for conv in adapter.stream_conversations(export_file):
        # Process conversation (provider-agnostic)
        cognivault.ingest(conv)
        count += 1
    return count


# Works with OpenAI
from echomine import OpenAIAdapter
count = process_export(OpenAIAdapter(), Path("chatgpt.json"))

# Works with Anthropic (future)
from echomine import AnthropicAdapter
count = process_export(AnthropicAdapter(), Path("claude.jsonl"))

# Works with Google (future)
from echomine import GoogleAdapter
count = process_export(GoogleAdapter(), Path("gemini.json"))
```

**cognivault Multi-Provider Integration**:
```python
from echomine import OpenAIAdapter  # Future: add more adapters

# Adapter registry
ADAPTERS = {
    "openai": OpenAIAdapter,
    # Future providers:
    # "anthropic": AnthropicAdapter,
    # "google": GoogleAdapter,
}

def ingest_ai_export(provider: str, export_file: Path):
    """Ingest any AI provider export into cognivault."""
    adapter_class = ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown provider: {provider}. Supported: {list(ADAPTERS.keys())}")

    adapter = adapter_class()

    # Same ingestion logic for all providers!
    count = 0
    for conv in adapter.stream_conversations(export_file):
        cognivault.knowledge_graph.add_conversation(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            messages=[{
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
            } for msg in conv.messages],
            provider=provider,  # Track source
            provider_metadata=conv.metadata,  # Preserve provider-specific data
        )
        count += 1

    return count


# Usage
ingest_ai_export("openai", Path("chatgpt_export.json"))
# Future:
# ingest_ai_export("anthropic", Path("claude_export.jsonl"))
# ingest_ai_export("google", Path("gemini_export.json"))
```

---

### Role Normalization

All adapters normalize provider-specific role names to standard roles.

**Normalized Roles**:
```python
from typing import Literal

MessageRole = Literal["user", "assistant", "system"]

# All adapters map to these three roles
```

**Provider Role Mapping**:
```python
# OpenAI (no mapping needed)
"user" → "user"
"assistant" → "assistant"
"system" → "system"

# Anthropic Claude (future)
"human" → "user"
"assistant" → "assistant"
# (no 'system' role in Claude v1)

# Google Gemini (future)
"user" → "user"
"model" → "assistant"
# (system instructions stored in metadata)
```

**Working with Normalized Roles**:
```python
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(export_file):
    for msg in conv.messages:
        # Role is always one of: "user", "assistant", "system"
        if msg.role == "user":
            print(f"User asked: {msg.content}")
        elif msg.role == "assistant":
            print(f"AI responded: {msg.content}")
        elif msg.role == "system":
            print(f"System prompt: {msg.content}")
```

---

### SearchQuery Extensibility

SearchQuery model supports backward-compatible filter additions.

**Current Filters** (v1.0):
```python
from echomine.models import SearchQuery
from datetime import date

query = SearchQuery(
    keywords=["python", "django"],
    title_filter="Project",
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),
    limit=10
)
```

**Future Filters** (v1.1+, backward compatible):
```python
# New optional filters added without breaking v1.0 code
query = SearchQuery(
    keywords=["python"],
    title_filter="Project",
    from_date=date(2024, 1, 1),
    limit=10,

    # NEW in v1.1 (optional, defaults to None)
    author_filter="user@example.com",  # Filter by author
    min_message_count=5,  # Minimum messages in conversation
    tag_filter=["work", "python"],  # Filter by tags
)

# v1.0 code still works (ignores new filters)
old_query = SearchQuery(keywords=["python"], limit=10)
```

**Adapter Filter Support**:
```python
# Check which filters an adapter supports
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()

# All v1.0 adapters support all v1.0 filters
results = adapter.search(export_file, SearchQuery(
    keywords=["test"],
    title_filter="Debug",
    from_date=date(2024, 1, 1),
    limit=5
))

for result in results:
    print(f"[{result.relevance_score:.2f}] {result.conversation.title}")
```

---

## Testing Your Integration

- Read [data-model.md](./data-model.md) for detailed model documentation
- See [contracts/cli_spec.md](./contracts/cli_spec.md) for CLI usage
- Check [contracts/conversation_provider_protocol.py](./contracts/conversation_provider_protocol.py) for protocol details

---

## Support

- Issues: [GitHub Issues](https://github.com/yourorg/echomine/issues)
- Documentation: [Full docs](https://echomine.readthedocs.io)
- Community: [Discord](https://discord.gg/echomine)
