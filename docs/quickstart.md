# Quick Start Guide

Get up and running with Echomine in minutes. This guide covers both library and CLI usage.

## Installation

```bash
pip install echomine
```

Or from source:

```bash
git clone https://github.com/echomine/echomine.git
cd echomine
pip install -e ".[dev]"
```

## Library Usage (Recommended)

### Basic Setup

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

# Create adapter for ChatGPT exports
adapter = OpenAIAdapter()
export_file = Path("path/to/conversations.json")
```

### 1. List All Conversations

Browse what's in your export file:

```python
# List all conversations with metadata
for conversation in adapter.stream_conversations(export_file):
    print(f"[{conversation.created_at.date()}] {conversation.title}")
    print(f"  Messages: {len(conversation.messages)}")
    print(f"  ID: {conversation.id}")
```

### 2. Search by Keywords

Find conversations matching specific topics:

```python
# Create search query
query = SearchQuery(
    keywords=["algorithm", "leetcode"],
    limit=5
)

# Execute search (returns ranked results)
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Preview: {result.snippet}")  # v1.1.0: automatic snippets
```

### 3. Advanced Search (v1.1.0+)

Use powerful new search features:

```python
from datetime import date

# Exact phrase matching + boolean logic + exclusions + role filtering
query = SearchQuery(
    keywords=["refactor", "optimization"],
    phrases=["algo-insights"],  # Exact phrase (preserves hyphens)
    match_mode="all",  # Require ALL keywords (AND logic)
    exclude_keywords=["test"],  # Filter out unwanted results
    role_filter="user",  # Search only your messages
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    limit=5
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Snippet: {result.snippet}")
    print(f"  Matched: {len(result.matched_message_ids)} messages")
```

### 4. Calculate Statistics (v1.2.0+)

Get comprehensive export statistics:

```python
from echomine import calculate_statistics

# Export-level statistics
stats = calculate_statistics(export_file)
print(f"Total conversations: {stats.total_conversations}")
print(f"Total messages: {stats.total_messages}")
print(f"Average messages: {stats.average_messages:.1f}")

if stats.largest_conversation:
    print(f"Largest: {stats.largest_conversation.title} "
          f"({stats.largest_conversation.message_count} messages)")
```

### 5. Get Specific Conversation

Retrieve a conversation by ID:

```python
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")

if conversation:
    print(f"Found: {conversation.title}")
    print(f"Messages: {len(conversation.messages)}")
```

## CLI Usage

### List Conversations

```bash
# Human-readable list
echomine list conversations.json

# JSON output for processing
echomine list conversations.json --json

# Limit to 10 most recent
echomine list conversations.json --limit 10
```

### Search

```bash
# Search by keywords
echomine search export.json --keywords "algorithm,design" --limit 10

# v1.1.0: Exact phrase matching
echomine search export.json --phrase "algo-insights"

# v1.1.0: Boolean match mode (require ALL keywords)
echomine search export.json -k "python" -k "async" --match-mode all

# v1.1.0: Exclude unwanted results
echomine search export.json -k "python" --exclude "django" --exclude "flask"

# v1.1.0: Role filtering (search only user/assistant messages)
echomine search export.json -k "refactor" --role user

# Search by title (fast, metadata-only)
echomine search export.json --title "Project"

# Filter by date range
echomine search export.json --from-date "2024-01-01" --to-date "2024-03-31"

# v1.1.0: Combine all advanced features
echomine search export.json \
  --phrase "api design" \
  --keywords "python" \
  --exclude "test" \
  --role user \
  --match-mode all \
  --title "Tutorial" \
  --from-date "2024-01-01" \
  --limit 5
```

**How filters combine:**
- **Content matching** (Stage 1): Phrases OR Keywords (use --match-mode for keyword logic)
- **Post-filtering** (Stage 2): --exclude, --role, --title, date range (all must match)

See [CLI Usage](cli-usage.md#how-search-filters-combine) for detailed filter logic.

### View Statistics (v1.2.0+)

```bash
# View export statistics
echomine stats export.json

# JSON output for scripting
echomine stats export.json --json
```

### Get Conversation by ID (v1.2.0+)

```bash
# Display full conversation
echomine get export.json conv-abc123

# Summary only
echomine get export.json conv-abc123 --display summary

# JSON output
echomine get export.json conv-abc123 --json
```

### Export to Markdown, JSON, or CSV (v1.2.0+)

```bash
# Export as markdown with YAML frontmatter (default in v1.2.0)
echomine export export.json conv-abc123 --output algo.md

# Export without frontmatter (v1.1.0 style)
echomine export export.json conv-abc123 --output algo.md --no-metadata

# Export as JSON (for programmatic use)
echomine export export.json conv-abc123 --format json --output conversation.json

# Export as CSV (v1.2.0+)
echomine export export.json conv-abc123 --format csv --output messages.csv

# Export JSON to stdout for piping
echomine export export.json conv-abc123 -f json | jq '.messages[0].content'
```

### JSON Output for Piping

All commands support `--json` flag for pipeline integration:

```bash
# Extract titles with jq
echomine search export.json --keywords "python" --json | jq '.results[].title'

# Count results
echomine search export.json --keywords "algorithm" --json | jq '.results | length'

# Filter results
echomine list export.json --json | jq '.conversations[] | select(.message_count > 10)'
```

## Common Workflows

### Workflow 1: Discovery

Find conversations about a specific topic:

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
query = SearchQuery(keywords=["machine learning"], limit=10)

for result in adapter.search(Path("export.json"), query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Created: {result.conversation.created_at.date()}")
    print(f"  Messages: {len(result.conversation.messages)}")
    print()
```

### Workflow 2: Batch Export

Export multiple conversations to markdown:

```python
from echomine import OpenAIAdapter, SearchQuery
from echomine.exporters import MarkdownExporter
from pathlib import Path

adapter = OpenAIAdapter()
exporter = MarkdownExporter()
export_file = Path("conversations.json")
output_dir = Path("exported")
output_dir.mkdir(exist_ok=True)

# Search for project-related conversations
query = SearchQuery(keywords=["project"], limit=20)

for result in adapter.search(export_file, query):
    conv = result.conversation

    # Export to markdown
    markdown = exporter.export(conv)

    # Save with slugified title
    from slugify import slugify
    filename = f"{slugify(conv.title)}.md"
    output_path = output_dir / filename

    output_path.write_text(markdown, encoding="utf-8")
    print(f"Exported: {output_path}")
```

### Workflow 3: Knowledge Base Ingestion

Integrate with a knowledge management system:

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")

# Stream all conversations for ingestion
count = 0
for conversation in adapter.stream_conversations(export_file):
    # Transform to your knowledge base format
    knowledge_node = {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "content": " ".join(msg.content for msg in conversation.messages),
        "tags": extract_tags(conversation),  # Your custom logic
    }

    # Ingest into knowledge base
    knowledge_base.add_node(knowledge_node)
    count += 1

print(f"Ingested {count} conversations")
```

## Type Safety Example

Echomine provides full type hints for IDE support:

```python
from echomine import OpenAIAdapter
from echomine.models import Conversation, SearchResult
from typing import Iterator

adapter = OpenAIAdapter()

# IDE autocomplete works!
conversations: Iterator[Conversation] = adapter.stream_conversations(export_file)

for conv in conversations:
    # Type checker knows these fields exist
    title: str = conv.title
    message_count: int = len(conv.messages)

    # mypy catches this error at type-check time!
    # invalid_field = conv.nonexistent_field  # AttributeError
```

## Next Steps

- **[Library Usage](library-usage.md)**: Comprehensive library API guide with advanced patterns
- **[CLI Usage](cli-usage.md)**: Complete CLI reference
- **[API Reference](api/index.md)**: Detailed API documentation
- **[Architecture](architecture.md)**: Design principles and patterns

## Troubleshooting

### Import Errors

```python
# If you see import errors, ensure package is installed
pip install -e .
```

### File Not Found

```python
from pathlib import Path

export_file = Path("conversations.json")
if not export_file.exists():
    print(f"Export file not found: {export_file}")
```

### Empty Results

```python
# Check if file contains conversations
conversations = list(adapter.stream_conversations(export_file))
print(f"Found {len(conversations)} conversations")
```

## Performance Tips

1. **Use streaming for large files**: Don't convert iterators to lists unless necessary
2. **Limit search results**: Use `limit` parameter to avoid processing thousands of results
3. **Use title filtering when possible**: Title search is faster than full-text search
4. **Monitor memory**: Streaming uses O(1) memory regardless of file size
