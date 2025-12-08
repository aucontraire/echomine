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
    print(f"  Preview: {result.snippet}")  # v1.1.0: automatic snippets
    print(f"  Matches: {len(result.matched_message_ids)} messages")
```

#### Understanding Filter Combinations

Search filters use a two-stage process:

**Stage 1: Content Matching (OR relationship)**
- Phrases: ANY phrase matches (exact, case-insensitive)
- Keywords: Match according to `match_mode`
  - `match_mode="any"` (default): ANY keyword matches
  - `match_mode="all"`: ALL keywords must be present

If you specify both phrases and keywords, a conversation matches if EITHER a phrase matches OR keywords match (they are alternatives, not cumulative).

**Stage 2: Post-Match Filters (AND relationship)**
- `exclude_keywords`: Removes results containing ANY excluded term
- `role_filter`: Only searches messages from specified role
- `title_filter`: Only includes conversations with matching title
- `from_date` / `to_date`: Only includes conversations in date range

**Examples:**

```python
# Phrase OR keyword (matches conversations with "api" phrase OR "python" keyword)
query = SearchQuery(phrases=["api"], keywords=["python"])

# Multiple keywords with ALL mode (requires both "python" AND "async")
query = SearchQuery(keywords=["python", "async"], match_mode="all")

# Content matching + exclusion (phrase OR keyword, then exclude "java")
query = SearchQuery(
    phrases=["api"],
    keywords=["python"],
    exclude_keywords=["java"]
)

# Role-specific search (only search user messages)
query = SearchQuery(keywords=["python"], role_filter="user")

# Complex combination
query = SearchQuery(
    phrases=["algo-insights"],
    keywords=["refactor"],
    exclude_keywords=["test", "documentation"],
    role_filter="user",
    title_filter="Project",
    match_mode="any"  # Only affects keywords when multiple specified
)
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

### Calculate Statistics (v1.2.0+)

Get comprehensive statistics about your export:

```python
from echomine import calculate_statistics, calculate_conversation_statistics

# Export-level statistics (streaming, O(1) memory)
stats = calculate_statistics(export_file)

print(f"Total conversations: {stats.total_conversations}")
print(f"Total messages: {stats.total_messages}")
print(f"Date range: {stats.date_range.earliest} to {stats.date_range.latest}")
print(f"Average messages: {stats.average_messages:.1f}")

# Largest and smallest conversations
if stats.largest_conversation:
    largest = stats.largest_conversation
    print(f"Largest: {largest.title} ({largest.message_count} messages)")

if stats.smallest_conversation:
    smallest = stats.smallest_conversation
    print(f"Smallest: {smallest.title} ({smallest.message_count} messages)")

# Per-conversation statistics
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")
if conversation:
    conv_stats = calculate_conversation_statistics(conversation)

    # Message counts by role
    print(f"User messages: {conv_stats.message_count_by_role.user}")
    print(f"Assistant messages: {conv_stats.message_count_by_role.assistant}")
    print(f"System messages: {conv_stats.message_count_by_role.system}")

    # Temporal patterns
    print(f"Duration: {conv_stats.duration_seconds:.0f} seconds")
    if conv_stats.average_gap_seconds:
        print(f"Average gap: {conv_stats.average_gap_seconds:.1f} seconds")
```

## Advanced Search Features (v1.1.0+)

Version 1.1.0 introduces five powerful search enhancements for the library API:

### 1. Exact Phrase Matching

Search for exact multi-word phrases while preserving special characters:

```python
from echomine.models import SearchQuery

# Single phrase
query = SearchQuery(phrases=["algo-insights"])
for result in adapter.search(export_file, query):
    print(f"{result.conversation.title}: {result.snippet}")

# Multiple phrases (OR logic - matches any)
query = SearchQuery(phrases=["algo-insights", "data pipeline", "api design"])
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")

# Combine phrases and keywords
query = SearchQuery(
    phrases=["algo-insights"],
    keywords=["optimization", "performance"]
)
results = list(adapter.search(export_file, query))
```

**Use Cases:**
- Project-specific terminology with special characters
- Code patterns like "async/await", "error-handling"
- Multi-word concepts that must appear together

### 2. Boolean Match Mode

Control keyword matching logic with AND or OR:

```python
# Require ALL keywords (AND logic)
query = SearchQuery(
    keywords=["python", "async", "testing"],
    match_mode="all"  # All three keywords must be present
)
for result in adapter.search(export_file, query):
    print(f"Contains ALL keywords: {result.conversation.title}")

# Default: ANY keyword matches (OR logic)
query = SearchQuery(
    keywords=["python", "javascript", "rust"],
    match_mode="any"  # At least one keyword present (default)
)
for result in adapter.search(export_file, query):
    print(f"Contains ANY keyword: {result.conversation.title}")

# Compare results
query_all = SearchQuery(keywords=["python", "async"], match_mode="all")
query_any = SearchQuery(keywords=["python", "async"], match_mode="any")

results_all = list(adapter.search(export_file, query_all))
results_any = list(adapter.search(export_file, query_any))

print(f"AND mode: {len(results_all)} results")
print(f"OR mode: {len(results_any)} results")
```

**Use Cases:**
- Narrow results: Find conversations covering multiple topics
- Broad discovery: Cast wide net across related keywords
- Topic intersection: Require specific keyword combinations

**Note:** `match_mode` only affects keywords. Phrases always use OR logic.

### 3. Exclude Keywords

Filter out unwanted results containing specific terms:

```python
# Exclude single term
query = SearchQuery(
    keywords=["python"],
    exclude_keywords=["django"]
)
for result in adapter.search(export_file, query):
    print(result.conversation.title)
    # Guaranteed: no results contain "django"

# Exclude multiple terms (OR logic - excludes if ANY present)
query = SearchQuery(
    keywords=["python"],
    exclude_keywords=["django", "flask", "pyramid"]
)
for result in adapter.search(export_file, query):
    print(result.conversation.title)
    # None of these contain django, flask, or pyramid

# Combine with other filters
query = SearchQuery(
    keywords=["refactor", "optimization"],
    exclude_keywords=["test", "example", "tutorial"],
    match_mode="all"
)
results = list(adapter.search(export_file, query))
```

**Use Cases:**
- Remove noise: Exclude "test", "example", "deprecated"
- Filter frameworks: Search Python without specific frameworks
- Avoid unrelated topics: Exclude terms that pollute results

**Note:** Excluded terms use OR logic - a result is removed if it contains ANY excluded term.

### 4. Role Filtering

Search only messages from specific author roles:

```python
# Search only YOUR questions
query = SearchQuery(
    keywords=["how do I", "refactor", "optimize"],
    role_filter="user"
)
for result in adapter.search(export_file, query):
    print(f"You asked: {result.snippet}")

# Search only AI responses
query = SearchQuery(
    keywords=["recommend", "suggest", "best practice"],
    role_filter="assistant"
)
for result in adapter.search(export_file, query):
    print(f"AI suggested: {result.snippet}")

# Search system messages
query = SearchQuery(
    keywords=["context", "instructions"],
    role_filter="system"
)
for result in adapter.search(export_file, query):
    print(f"System: {result.snippet}")

# Compare user vs assistant content
user_query = SearchQuery(keywords=["algorithm"], role_filter="user")
assistant_query = SearchQuery(keywords=["algorithm"], role_filter="assistant")

user_results = list(adapter.search(export_file, user_query))
assistant_results = list(adapter.search(export_file, assistant_query))

print(f"You mentioned 'algorithm' in {len(user_results)} conversations")
print(f"AI mentioned 'algorithm' in {len(assistant_results)} conversations")
```

**Use Cases:**
- Find your questions: `role_filter="user"`
- Find AI recommendations: `role_filter="assistant"`
- Analyze system prompts: `role_filter="system"`
- Compare user vs AI language patterns

**Valid Roles:** `"user"`, `"assistant"`, `"system"` (case-insensitive)

### 5. Message Snippets (Automatic)

All search results automatically include message previews:

```python
query = SearchQuery(keywords=["algorithm"])

for result in adapter.search(export_file, query):
    # v1.1.0: snippet field always present
    print(f"Title: {result.conversation.title}")
    print(f"Score: {result.score:.2f}")
    print(f"Preview: {result.snippet}")
    print(f"Matched messages: {len(result.matched_message_ids)}")
    print(f"Message IDs: {result.matched_message_ids[:3]}")  # First 3
    print("---")
```

**Snippet Features:**
- ~100 character preview from first matching message
- Truncated with "..." for long content
- Multiple matches indicated in `matched_message_ids`
- Fallback text for empty/malformed content
- Always present (never None)

**Working with Matched Messages:**

```python
from echomine import OpenAIAdapter, SearchQuery

adapter = OpenAIAdapter()
query = SearchQuery(keywords=["refactor"])

for result in adapter.search(export_file, query):
    conversation = result.conversation
    matched_ids = result.matched_message_ids

    # Find the actual matched messages
    matched_messages = [
        msg for msg in conversation.messages
        if msg.id in matched_ids
    ]

    print(f"Conversation: {conversation.title}")
    print(f"Matched {len(matched_messages)} messages:")
    for msg in matched_messages:
        print(f"  [{msg.role}] {msg.content[:80]}...")
```

### Combining Advanced Features

All features work together for powerful precision searches:

```python
from datetime import date

# Complex query combining all v1.1.0 features
query = SearchQuery(
    # Content matching (Stage 1: OR relationship)
    keywords=["python", "optimization"],
    phrases=["algo-insights"],
    match_mode="all",  # Only affects keywords

    # Post-match filters (Stage 2: AND relationship)
    exclude_keywords=["test", "documentation"],
    role_filter="user",
    title_filter="Project",
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),

    # Output control
    limit=10
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Created: {result.conversation.created_at.date()}")
    print(f"  Snippet: {result.snippet}")
    print(f"  Matches: {len(result.matched_message_ids)} messages")
```

### Filter Combination Logic

Understanding how filters interact is crucial:

**Stage 1: Content Matching (OR relationship)**
- **Phrases**: Match if ANY phrase is found (exact, case-insensitive)
- **Keywords**: Match according to `match_mode`
  - `match_mode="any"` (default): Match if ANY keyword present
  - `match_mode="all"`: Match if ALL keywords present
- **Key insight**: Phrases OR keywords (not both required)

**Stage 2: Post-Match Filters (AND relationship)**
- `exclude_keywords`: Remove if ANY excluded term found
- `role_filter`: Only messages from specified role
- `title_filter`: Only conversations with matching title
- `from_date` / `to_date`: Only in date range
- **All must be satisfied**

**Examples:**

```python
# Phrase OR keyword (matches either)
query = SearchQuery(phrases=["api"], keywords=["python"])
# Matches: conversations with "api" phrase OR "python" keyword

# Multiple keywords with ALL mode
query = SearchQuery(keywords=["python", "async"], match_mode="all")
# Matches: conversations with BOTH "python" AND "async"

# Content + exclusion
query = SearchQuery(
    phrases=["api"],
    keywords=["python"],
    exclude_keywords=["java"]
)
# Matches: ("api" phrase OR "python" keyword) AND NOT "java"

# Role-specific search
query = SearchQuery(keywords=["python"], role_filter="user")
# Matches: "python" in user messages only

# Complex combination
query = SearchQuery(
    phrases=["algo-insights"],
    keywords=["refactor"],
    exclude_keywords=["test", "docs"],
    role_filter="user",
    title_filter="Project",
    match_mode="any"
)
# Matches: ("algo-insights" phrase OR "refactor" keyword) in user messages
#          in conversations titled "Project" WITHOUT "test" or "docs"
```

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

### Fail-Fast vs Skip-Malformed Strategy

Echomine distinguishes between **operational errors** (fail-fast) and **data quality issues** (skip-malformed):

**Fail-Fast: Operational Errors** (raises exceptions)
- **JSON syntax errors**: Completely malformed file structure
- **File access errors**: Missing files, permission denied, disk errors
- **Unsupported schema version**: Export format version mismatch

These errors indicate problems with the export file itself or the environment. Processing cannot continue safely, so exceptions are raised immediately.

**Skip-Malformed: Data Quality Issues** (log warning, continue processing)

The library categorizes malformed entries into three types (per FR-264):

1. **JSON Syntax Errors (Structural)**
   - Completely malformed conversation objects within valid array
   - Example: Truncated objects, unescaped quotes, invalid nesting
   - Handling: Skip conversation, log JSON parse error

2. **Schema Violations (Missing Required Fields)**
   - Conversations missing required fields: `id`, `title`, `create_time`
   - Messages missing required fields: `id`, `author.role`, `content`
   - Example: `{"title": "Test"}` (missing id, create_time)
   - Handling: Skip conversation, log "missing field: {field_name}"

3. **Validation Failures (Invalid Field Values)**
   - Fields present but values violate type/format constraints
   - Examples: Non-UTC timestamps, invalid role values, negative timestamps
   - Handling: Skip conversation, log "invalid {field}: {reason}"

For all three categories, the library:
1. Logs WARNING with conversation ID and category-specific error message
2. Invokes `on_skip` callback if provided (with conversation ID and reason)
3. Continues processing remaining conversations
4. Returns partial results (graceful degradation)

This strategy ensures maximum data recovery while maintaining safety for operational errors.

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

## Export Formats (v1.2.0+)

### Markdown Export with YAML Frontmatter

```python
from echomine import OpenAIAdapter
from echomine.exporters import MarkdownExporter
from pathlib import Path

adapter = OpenAIAdapter()
exporter = MarkdownExporter()

conversation = adapter.get_conversation_by_id(Path("export.json"), "conv-abc123")

if conversation:
    # Export with YAML frontmatter (default in v1.2.0)
    markdown = exporter.export_conversation(conversation)
    Path("chat.md").write_text(markdown)

    # Export without frontmatter (v1.1.0 style)
    markdown_plain = exporter.export_conversation(
        conversation,
        include_metadata=False,
        include_message_ids=False
    )
    Path("chat_plain.md").write_text(markdown_plain)
```

### CSV Export

```python
from echomine import OpenAIAdapter, SearchQuery
from echomine.exporters import CSVExporter
from pathlib import Path

adapter = OpenAIAdapter()
exporter = CSVExporter()

# Export search results to CSV
query = SearchQuery(keywords=["python"], limit=100)
results = list(adapter.search(Path("export.json"), query))

# Conversation-level CSV
csv_content = exporter.export_search_results(results)
Path("results.csv").write_text(csv_content)

# Message-level CSV
csv_messages = exporter.export_messages_from_results(results)
Path("messages.csv").write_text(csv_messages)

# Export single conversation
conversation = adapter.get_conversation_by_id(Path("export.json"), "conv-abc123")
if conversation:
    csv_single = exporter.export_conversation(conversation)
    Path("conversation.csv").write_text(csv_single)
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
