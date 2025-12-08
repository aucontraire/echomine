# Quickstart: Baseline Enhancement Package v1.2.0

**Feature**: 003-baseline-enhancements
**Date**: 2025-12-05

## What's New in v1.2.0

- **Message Count Filtering** - Filter conversations by number of messages
- **Statistics Command** - View export and per-conversation statistics
- **List Messages** - View all messages in a conversation
- **Rich Markdown Export** - YAML frontmatter + message IDs
- **Rich CLI Output** - Tables, colors, progress bars
- **Sort Options** - Sort results by date, title, or message count
- **CSV Export** - Export to CSV for data analysis

---

## CLI Usage

### Message Count Filtering

Filter conversations by message count to focus on substantial discussions:

```bash
# Find conversations with at least 10 messages
echomine search export.json --keywords "python" --min-messages 10

# Find short conversations (5 or fewer messages)
echomine search export.json --max-messages 5

# Find medium-length conversations (5-20 messages)
echomine search export.json --min-messages 5 --max-messages 20
```

### Statistics Command

Get an overview of your conversation export:

```bash
# Export-level statistics
echomine stats export.json

# Output:
# Export Statistics
# ─────────────────────────────────────
# Total conversations:  1,234
# Total messages:       45,678
# Date range:           2024-01-01 to 2024-12-05
# Average messages:     37.0
#
# Largest conversation:
#   "Deep Python Discussion" (id: abc-123, 245 messages)

# JSON output for scripting
echomine stats export.json --json | jq '.total_conversations'

# Per-conversation statistics
echomine stats export.json --conversation abc-123

# Output:
# Conversation Statistics: "Deep Python Discussion"
# ─────────────────────────────────────
# Message Breakdown:
#   user:       82 messages
#   assistant:  155 messages
#   system:     8 messages
#
# Temporal Patterns:
#   Duration:           4h 14m 27s
#   Average gap:        62.3 seconds
```

### List Messages

View all messages in a specific conversation:

```bash
# Human-readable list
echomine get messages export.json abc-123

# Output:
# Messages in "Deep Python Discussion" (245 messages)
# ─────────────────────────────────────
# msg-001  user       2024-01-15 10:30:05  I need help with Python generators...
# msg-002  assistant  2024-01-15 10:30:47  Python generators are a powerful fe...

# JSON output with full content
echomine get messages export.json abc-123 --json
```

### Sort Options

Control result ordering:

```bash
# Sort by date (most recent first)
echomine search export.json -k "python" --sort date

# Sort by title (alphabetical)
echomine search export.json -k "python" --sort title --order asc

# Sort by message count (shortest first)
echomine search export.json -k "python" --sort messages --order asc
```

### CSV Export

Export for data analysis:

```bash
# Search results to CSV
echomine search export.json -k "python" --format csv > results.csv

# List all conversations to CSV
echomine list export.json --format csv > conversations.csv

# Open in Excel or analyze with pandas
python -c "import pandas as pd; print(pd.read_csv('results.csv'))"
```

### Rich Markdown Export

Export with YAML frontmatter for static site generators:

```bash
# Export with metadata (default in v1.2.0)
echomine export export.json abc-123 --output chat.md

# Export without metadata (v1.1.0 behavior)
echomine export export.json abc-123 --output chat.md --no-metadata
```

Output with metadata:

```markdown
---
id: abc-123
title: Deep Python Discussion
created_at: 2024-01-15T10:30:00+00:00
message_count: 245
export_date: 2025-12-05T15:30:00+00:00
exported_by: echomine
---

# Deep Python Discussion

## User (`msg-001`) - 2024-01-15 10:30:05 UTC

I need help with Python generators...
```

---

## Library Usage

### Message Count Filtering

```python
from pathlib import Path
from echomine import OpenAIAdapter, SearchQuery

adapter = OpenAIAdapter()

# Filter by message count
query = SearchQuery(
    keywords=["python"],
    min_messages=10,
    max_messages=100,
)

for result in adapter.search(Path("export.json"), query):
    conv = result.conversation
    print(f"{conv.title}: {conv.message_count} messages")
```

### Statistics Functions

```python
from pathlib import Path
from echomine import (
    OpenAIAdapter,
    calculate_statistics,
    calculate_conversation_statistics,
)

# Export-level statistics (streaming, O(1) memory)
stats = calculate_statistics(Path("export.json"))
print(f"Total: {stats.total_conversations} conversations")
print(f"Messages: {stats.total_messages}")
print(f"Average: {stats.average_messages:.1f} per conversation")

if stats.largest_conversation:
    largest = stats.largest_conversation
    print(f"Largest: {largest.title} ({largest.message_count} messages)")

# Per-conversation statistics
adapter = OpenAIAdapter()
conv = adapter.get_conversation_by_id(Path("export.json"), "abc-123")

if conv:
    conv_stats = calculate_conversation_statistics(conv)
    print(f"User messages: {conv_stats.message_count_by_role.user}")
    print(f"Assistant messages: {conv_stats.message_count_by_role.assistant}")
    print(f"Duration: {conv_stats.duration_seconds:.0f} seconds")
```

### CSV Export

```python
from pathlib import Path
from echomine import OpenAIAdapter, CSVExporter, SearchQuery

adapter = OpenAIAdapter()
exporter = CSVExporter()

# Export search results
query = SearchQuery(keywords=["python"], limit=100)
results = list(adapter.search(Path("export.json"), query))

# Conversation-level CSV
csv_content = exporter.export_search_results(results)
Path("results.csv").write_text(csv_content)

# Message-level CSV
csv_messages = exporter.export_messages_from_results(results)
Path("messages.csv").write_text(csv_messages)
```

### Rich Markdown Export

```python
from pathlib import Path
from echomine import OpenAIAdapter, MarkdownExporter

adapter = OpenAIAdapter()
exporter = MarkdownExporter()

conv = adapter.get_conversation_by_id(Path("export.json"), "abc-123")

# With YAML frontmatter (default)
markdown = exporter.export_conversation(conv)
Path("chat.md").write_text(markdown)

# Without frontmatter
markdown_plain = exporter.export_conversation(
    conv,
    include_metadata=False,
    include_message_ids=False,
)
```

### Sort Options

```python
from echomine import SearchQuery

# Sort by date
query = SearchQuery(
    keywords=["python"],
    sort_by="date",
    sort_order="desc",  # Most recent first
)

# Sort by title
query = SearchQuery(
    keywords=["python"],
    sort_by="title",
    sort_order="asc",  # Alphabetical
)

# Sort by message count
query = SearchQuery(
    keywords=["python"],
    sort_by="messages",
    sort_order="asc",  # Shortest first
)
```

---

## Common Workflows

### Analyze Conversation Patterns

```bash
# Get export overview
echomine stats export.json

# Find substantial technical discussions
echomine search export.json -k "algorithm,architecture" --min-messages 20

# Export for deeper analysis
echomine search export.json -k "algorithm" --format csv > algorithms.csv
```

### Build Knowledge Base

```bash
# Export all substantial conversations with metadata
for id in $(echomine search export.json --min-messages 10 --json | jq -r '.[].conversation.id'); do
  echomine export export.json "$id" --output "docs/${id}.md"
done
```

### Data Analysis Pipeline

```python
import pandas as pd
from pathlib import Path
from echomine import OpenAIAdapter, CSVExporter, SearchQuery

# Search and export
adapter = OpenAIAdapter()
exporter = CSVExporter()

query = SearchQuery(keywords=["python"], limit=1000)
results = list(adapter.search(Path("export.json"), query))
csv_content = exporter.export_search_results(results)

# Analyze with pandas
df = pd.read_csv(pd.io.common.StringIO(csv_content))
print(f"Average score: {df['score'].mean():.3f}")
print(f"Average messages: {df['message_count'].mean():.1f}")
print(df.groupby('message_count').size().describe())
```

---

## Migration from v1.1.0

### Breaking Changes

None - all v1.1.0 code continues to work.

### Behavior Changes

| Feature | v1.1.0 | v1.2.0 |
|---------|--------|--------|
| Markdown export | No frontmatter | Frontmatter by default |
| CLI tables | Plain text | Rich tables (TTY only) |

### Opt-out of New Defaults

```bash
# Use v1.1.0 markdown format
echomine export export.json abc-123 --output chat.md --no-metadata
```

```python
# Use v1.1.0 markdown format in library
markdown = exporter.export_conversation(conv, include_metadata=False)
```
