# Quick Start: Claude Export Adapter

**Feature**: 004-claude-adapter
**Date**: 2025-12-08

## Overview

This guide shows how to use the ClaudeAdapter to parse, search, and export Claude AI conversation exports. The API is identical to OpenAIAdapter for consistent multi-provider usage.

## Installation

```bash
pip install echomine
```

## Getting Your Claude Export

1. Log in to Claude at https://claude.ai
2. Go to Settings > Export Data
3. Download your data export ZIP
4. Extract to find `conversations.json`

## Library Usage (Primary Interface)

### Basic Setup

```python
from echomine import ClaudeAdapter, SearchQuery
from pathlib import Path

# Create adapter (stateless, reusable)
adapter = ClaudeAdapter()
export_file = Path("path/to/conversations.json")
```

### 1. List All Conversations

```python
# Stream all conversations (O(1) memory)
for conversation in adapter.stream_conversations(export_file):
    print(f"[{conversation.created_at.date()}] {conversation.title}")
    print(f"  Messages: {conversation.message_count}")
    print(f"  ID: {conversation.id}")
```

### 2. Search by Keywords

```python
# Create search query with BM25 ranking
query = SearchQuery(
    keywords=["algorithm", "python"],
    limit=5
)

# Execute search
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Preview: {result.snippet}")
```

### 3. Advanced Search

```python
from datetime import date

# Combine multiple filters
query = SearchQuery(
    keywords=["refactor", "optimization"],
    phrases=["code review"],       # Exact phrase matching
    match_mode="all",              # Require ALL keywords
    exclude_keywords=["test"],     # Filter out unwanted results
    role_filter="user",            # Search only your messages
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),
    limit=10
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Snippet: {result.snippet}")
    print(f"  Matched: {len(result.matched_message_ids)} messages")
```

### 4. Get Specific Conversation

```python
# Retrieve by UUID
conversation = adapter.get_conversation_by_id(
    export_file,
    "5551eb71-ada2-45bd-8f91-0c4945a1e5a6"
)

if conversation:
    print(f"Found: {conversation.title}")
    print(f"Messages: {conversation.message_count}")

    # Access messages
    for msg in conversation.messages:
        print(f"  [{msg.role}] {msg.content[:100]}...")
else:
    print("Conversation not found")
```

### 5. Get Specific Message

```python
# Retrieve message with conversation context
result = adapter.get_message_by_id(
    export_file,
    "caaac42b-b9a2-4555-96fb-4d15537abc8b"
)

if result:
    message, conversation = result
    print(f"Message: {message.content}")
    print(f"From conversation: {conversation.title}")
    print(f"Role: {message.role}")
else:
    print("Message not found")
```

## CLI Usage

### Provider Auto-Detection

The CLI automatically detects whether an export is from Claude or OpenAI:

```bash
# Claude export - auto-detected
echomine list conversations.json

# Explicit provider (optional)
echomine list conversations.json --provider claude
```

### List Conversations

```bash
# Human-readable list
echomine list conversations.json

# JSON output for processing
echomine list conversations.json --json

# Limit to recent conversations
echomine list conversations.json --limit 10
```

### Search

```bash
# Search by keywords
echomine search conversations.json --keywords "algorithm,design" --limit 10

# Exact phrase matching
echomine search conversations.json --phrase "code review"

# Require all keywords
echomine search conversations.json -k "python" -k "async" --match-mode all

# Exclude unwanted results
echomine search conversations.json -k "python" --exclude "test"

# Filter by role
echomine search conversations.json -k "refactor" --role user

# Filter by date range
echomine search conversations.json --from-date "2024-01-01" --to-date "2024-03-31"

# JSON output
echomine search conversations.json --keywords "python" --json
```

### Get Conversation

```bash
# Display full conversation
echomine get conversations.json 5551eb71-ada2-45bd-8f91-0c4945a1e5a6

# Summary only
echomine get conversations.json <uuid> --display summary

# JSON output
echomine get conversations.json <uuid> --json
```

### Export to Markdown

```bash
# Export as markdown with YAML frontmatter
echomine export conversations.json <uuid> --output chat.md

# Export as JSON
echomine export conversations.json <uuid> --format json --output chat.json

# Export as CSV
echomine export conversations.json <uuid> --format csv --output messages.csv
```

### View Statistics

```bash
# View export statistics
echomine stats conversations.json

# JSON output
echomine stats conversations.json --json
```

## Multi-Provider Usage

Use the same code for both Claude and OpenAI exports:

```python
from echomine import ClaudeAdapter, OpenAIAdapter, SearchQuery
from pathlib import Path

def search_conversations(adapter, file_path: Path, query: SearchQuery):
    """Generic search function works with any adapter."""
    for result in adapter.search(file_path, query):
        print(f"[{result.score:.2f}] {result.conversation.title}")

# Claude export
claude_adapter = ClaudeAdapter()
search_conversations(
    claude_adapter,
    Path("claude_conversations.json"),
    SearchQuery(keywords=["python"])
)

# OpenAI export
openai_adapter = OpenAIAdapter()
search_conversations(
    openai_adapter,
    Path("openai_conversations.json"),
    SearchQuery(keywords=["python"])
)
```

## Performance Tips

1. **Use streaming**: Don't convert iterators to lists unless necessary
2. **Limit results**: Use `limit` parameter to avoid processing everything
3. **Title filter first**: Title filtering is faster than full-text search
4. **Monitor memory**: Streaming uses O(1) memory regardless of file size

## Error Handling

```python
from echomine.exceptions import ParseError

try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
except FileNotFoundError:
    print("Export file not found")
except ParseError as e:
    print(f"Invalid export format: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Type Safety

Full type hints for IDE support:

```python
from echomine import ClaudeAdapter, SearchQuery
from echomine.models import Conversation, SearchResult
from collections.abc import Iterator

adapter = ClaudeAdapter()

# IDE knows these types
conversations: Iterator[Conversation] = adapter.stream_conversations(export_file)
results: Iterator[SearchResult[Conversation]] = adapter.search(export_file, query)
```

## Common Workflows

### Export All Conversations to Markdown

```python
from echomine import ClaudeAdapter
from echomine.export import MarkdownExporter
from pathlib import Path
from slugify import slugify

adapter = ClaudeAdapter()
exporter = MarkdownExporter()
output_dir = Path("exported")
output_dir.mkdir(exist_ok=True)

for conv in adapter.stream_conversations(Path("conversations.json")):
    markdown = exporter.export(conv)
    filename = f"{slugify(conv.title or 'untitled')}.md"
    (output_dir / filename).write_text(markdown, encoding="utf-8")
    print(f"Exported: {filename}")
```

### Search Across Multiple Exports

```python
from echomine import ClaudeAdapter, OpenAIAdapter, SearchQuery
from pathlib import Path

adapters = [
    (ClaudeAdapter(), Path("claude_export.json")),
    (OpenAIAdapter(), Path("openai_export.json")),
]

query = SearchQuery(keywords=["machine learning"], limit=5)

for adapter, file_path in adapters:
    print(f"\n=== {file_path.name} ===")
    for result in adapter.search(file_path, query):
        print(f"[{result.score:.2f}] {result.conversation.title}")
```
