# Library API Contract: Baseline Enhancement Package v1.2.0

**Feature**: 003-baseline-enhancements
**Date**: 2025-12-05
**Status**: Complete

## Public API Surface

### 1. SearchQuery Model (MODIFY)

**Module**: `echomine.models.search`
**FR Reference**: FR-004-008, FR-048

```python
from echomine import SearchQuery

# New fields in v1.2.0
query = SearchQuery(
    keywords=["python"],
    min_messages=10,           # NEW: Filter min (FR-004)
    max_messages=50,           # NEW: Filter max (FR-004)
    sort_by="date",            # NEW: Sort field (FR-048)
    sort_order="desc",         # NEW: Sort direction (FR-048)
)

# Validation: min <= max (FR-005)
try:
    SearchQuery(min_messages=20, max_messages=5)  # Raises ValueError
except ValueError as e:
    print(e)  # "min_messages (20) must be <= max_messages (5)"

# Helper methods
query.has_message_count_filter()  # True if min or max set
```

---

### 2. Statistics Functions (NEW)

**Module**: `echomine.statistics`
**FR Reference**: FR-016, FR-022

#### calculate_statistics()

```python
from pathlib import Path
from echomine import calculate_statistics
from echomine.models import ExportStatistics

def calculate_statistics(
    file_path: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> ExportStatistics:
    """Calculate statistics for entire export file.

    Uses streaming (O(1) memory) regardless of file size.

    Args:
        file_path: Path to OpenAI export JSON file
        progress_callback: Optional callback invoked every 100 conversations
        on_skip: Optional callback for malformed entries

    Returns:
        ExportStatistics with aggregated statistics

    Raises:
        FileNotFoundError: If file doesn't exist
        ParseError: If JSON is malformed

    Example:
        stats = calculate_statistics(Path("export.json"))
        print(f"Total: {stats.total_conversations} conversations")
        print(f"Messages: {stats.total_messages}")
        print(f"Average: {stats.average_messages:.1f} per conversation")
    """
```

#### calculate_conversation_statistics()

```python
from echomine import calculate_conversation_statistics
from echomine.models import Conversation, ConversationStatistics

def calculate_conversation_statistics(
    conversation: Conversation,
) -> ConversationStatistics:
    """Calculate detailed statistics for single conversation.

    Pure function - no I/O, no side effects.

    Args:
        conversation: Conversation to analyze

    Returns:
        ConversationStatistics with message breakdown and temporal patterns

    Example:
        # Get conversation first
        adapter = OpenAIAdapter()
        conv = adapter.get_conversation_by_id(path, "abc-123")

        # Calculate stats
        stats = calculate_conversation_statistics(conv)
        print(f"User messages: {stats.message_count_by_role.user}")
        print(f"Duration: {stats.duration_seconds:.0f} seconds")
    """
```

---

### 3. OpenAIAdapter.search() (MODIFY)

**Module**: `echomine.adapters.openai`
**FR Reference**: FR-006

#### Enhanced Search with Message Count Filtering

```python
from pathlib import Path
from echomine import OpenAIAdapter, SearchQuery

adapter = OpenAIAdapter()

# Message count filtering (FR-001-003)
query = SearchQuery(
    keywords=["python"],
    min_messages=10,
    max_messages=100,
)

for result in adapter.search(Path("export.json"), query):
    # Guaranteed: 10 <= result.conversation.message_count <= 100
    print(f"{result.conversation.title}: {result.conversation.message_count} messages")
```

#### Sort Options

```python
# Sort by date (most recent first)
query = SearchQuery(keywords=["python"], sort_by="date", sort_order="desc")

# Sort by title (alphabetical)
query = SearchQuery(keywords=["python"], sort_by="title", sort_order="asc")

# Sort by message count (smallest first)
query = SearchQuery(keywords=["python"], sort_by="messages", sort_order="asc")

# Default: sort by score (highest first)
query = SearchQuery(keywords=["python"])  # sort_by="score", sort_order="desc"
```

---

### 4. CSVExporter (NEW)

**Module**: `echomine.export.csv`
**FR Reference**: FR-055

```python
from pathlib import Path
from echomine import OpenAIAdapter, CSVExporter, SearchQuery

adapter = OpenAIAdapter()
exporter = CSVExporter()

# Export search results to CSV
query = SearchQuery(keywords=["python"], limit=100)
results = list(adapter.search(Path("export.json"), query))

# Conversation-level CSV (FR-050)
csv_content = exporter.export_search_results(results)
Path("results.csv").write_text(csv_content)

# Message-level CSV (FR-052)
csv_messages = exporter.export_messages_from_results(results)
Path("messages.csv").write_text(csv_messages)

# Export all conversations (list command)
conversations = list(adapter.stream_conversations(Path("export.json")))
csv_all = exporter.export_conversations(conversations)
```

#### CSVExporter API

```python
class CSVExporter:
    """RFC 4180 compliant CSV exporter.

    Uses streaming writer pattern for O(1) memory with large result sets.
    """

    def export_conversations(
        self,
        conversations: Iterable[Conversation],
    ) -> str:
        """Export conversations to CSV string.

        Schema: conversation_id, title, created_at, updated_at, message_count

        Args:
            conversations: Conversations to export

        Returns:
            RFC 4180 compliant CSV string with headers
        """

    def export_search_results(
        self,
        results: Iterable[SearchResult[Conversation]],
    ) -> str:
        """Export search results to CSV string.

        Schema: conversation_id, title, created_at, updated_at, message_count, score

        Args:
            results: Search results to export

        Returns:
            RFC 4180 compliant CSV string with headers
        """

    def export_messages(
        self,
        conversation: Conversation,
    ) -> str:
        """Export conversation messages to CSV string.

        Schema: conversation_id, message_id, role, timestamp, content

        Args:
            conversation: Conversation with messages

        Returns:
            RFC 4180 compliant CSV string with headers
        """

    def export_messages_from_results(
        self,
        results: Iterable[SearchResult[Conversation]],
    ) -> str:
        """Export all messages from search results to CSV.

        Args:
            results: Search results containing conversations

        Returns:
            RFC 4180 compliant CSV string with all messages
        """
```

---

### 5. MarkdownExporter (MODIFY)

**Module**: `echomine.export.markdown`
**FR Reference**: FR-035

#### Enhanced Export with Metadata

```python
from pathlib import Path
from echomine import OpenAIAdapter, MarkdownExporter

adapter = OpenAIAdapter()
exporter = MarkdownExporter()

conv = adapter.get_conversation_by_id(Path("export.json"), "abc-123")

# Default: include metadata (FR-030)
markdown = exporter.export_conversation(
    conv,
    include_metadata=True,      # NEW v1.2.0 (default: True)
    include_message_ids=True,   # NEW v1.2.0 (default: True)
)

# Without metadata (FR-033)
markdown_plain = exporter.export_conversation(
    conv,
    include_metadata=False,
    include_message_ids=False,
)
```

#### Output Format

**With metadata (default)**:
```markdown
---
id: abc-123
title: Deep Python Discussion
created_at: 2024-01-15T10:30:00+00:00
updated_at: 2024-01-15T14:45:00+00:00
message_count: 245
export_date: 2025-12-05T15:30:00+00:00
exported_by: echomine
---

# Deep Python Discussion

## User (`msg-001`) - 2024-01-15 10:30:05 UTC

I need help with Python generators...

---

## Assistant (`msg-002`) - 2024-01-15 10:30:47 UTC

Python generators are a powerful feature...
```

**Without metadata**:
```markdown
# Deep Python Discussion

## User - 2024-01-15 10:30:05 UTC

I need help with Python generators...
```

---

### 6. Models (NEW)

**Module**: `echomine.models.statistics`

#### ExportStatistics

```python
from echomine.models import ExportStatistics, ConversationSummary

stats = ExportStatistics(
    total_conversations=1234,
    total_messages=45678,
    earliest_date=datetime(2024, 1, 1, tzinfo=UTC),
    latest_date=datetime(2024, 12, 5, tzinfo=UTC),
    average_messages=37.0,
    largest_conversation=ConversationSummary(
        id="abc-123",
        title="Deep Discussion",
        message_count=245,
    ),
    smallest_conversation=ConversationSummary(
        id="xyz-789",
        title="Quick Q",
        message_count=2,
    ),
    skipped_count=3,
)

# Immutable (frozen=True)
stats.total_conversations = 999  # Raises ValidationError
```

#### ConversationStatistics

```python
from echomine.models import ConversationStatistics, RoleCount

stats = ConversationStatistics(
    conversation_id="abc-123",
    title="Deep Python Discussion",
    created_at=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
    updated_at=datetime(2024, 1, 15, 14, 45, tzinfo=UTC),
    message_count=245,
    message_count_by_role=RoleCount(user=82, assistant=155, system=8),
    first_message=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
    last_message=datetime(2024, 1, 15, 14, 44, 32, tzinfo=UTC),
    duration_seconds=15267.0,
    average_gap_seconds=62.3,
)

# Computed property
assert stats.message_count_by_role.total == 245
```

---

## Type Signatures

### Function Signatures

```python
# Statistics functions
def calculate_statistics(
    file_path: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    on_skip: OnSkipCallback | None = None,
) -> ExportStatistics: ...

def calculate_conversation_statistics(
    conversation: Conversation,
) -> ConversationStatistics: ...

# Callback types (existing)
ProgressCallback = Callable[[int], None]
OnSkipCallback = Callable[[str, str], None]  # (conversation_id, reason)
```

### Model Type Hints

```python
# Sort types
SortField = Literal["score", "date", "title", "messages"]
SortOrder = Literal["asc", "desc"]

# SearchQuery additions
class SearchQuery(BaseModel):
    # ... existing fields ...
    min_messages: int | None = None
    max_messages: int | None = None
    sort_by: SortField | None = None
    sort_order: SortOrder = "desc"
```

---

## Backward Compatibility

### Preserved Behaviors

| Feature | v1.1.0 | v1.2.0 | Compatible |
|---------|--------|--------|------------|
| `SearchQuery()` default | Works | Works | Yes |
| `adapter.search()` | Works | Works | Yes |
| `exporter.export_conversation()` | No frontmatter | Frontmatter by default | Yes* |

*Note: `export_conversation()` now includes frontmatter by default. Use `include_metadata=False` for v1.1.0 behavior.

### Migration Guide

```python
# v1.1.0 behavior (no frontmatter)
markdown = exporter.export_conversation(conv)

# v1.2.0 equivalent (explicit no metadata)
markdown = exporter.export_conversation(conv, include_metadata=False)
```

---

## Logging Contracts (FR-060a)

All new operations emit structured JSON logs via structlog:

### calculate_statistics()
```python
# INFO (start)
{"event": "calculate_statistics", "file_name": "export.json", "level": "info"}

# INFO (complete)
{"event": "calculate_statistics", "file_name": "export.json", "total_conversations": 1234,
 "total_messages": 45678, "elapsed_seconds": 2.5, "level": "info"}

# WARNING (skip malformed)
{"event": "calculate_statistics", "conversation_id": "abc-123",
 "reason": "malformed entry", "level": "warning"}
```

### calculate_conversation_statistics()
```python
# INFO
{"event": "calculate_conversation_statistics", "conversation_id": "abc-123",
 "message_count": 245, "duration_seconds": 15267.0, "level": "info"}
```

### CSVExporter
```python
# INFO (start)
{"event": "csv_export", "format": "conversation", "item_count": 100, "level": "info"}

# INFO (complete)
{"event": "csv_export", "rows_written": 100, "elapsed_seconds": 0.5, "level": "info"}
```

---

## Error Handling

### Validation Errors

```python
from pydantic import ValidationError

# Invalid message count bounds
try:
    query = SearchQuery(min_messages=20, max_messages=5)
except ValidationError as e:
    # "min_messages (20) must be <= max_messages (5)"
    pass

# Negative message count
try:
    query = SearchQuery(min_messages=-1)
except ValidationError as e:
    # "ensure this value is >= 1"
    pass
```

### Operational Errors

```python
from echomine.exceptions import ParseError

# File not found
try:
    stats = calculate_statistics(Path("missing.json"))
except FileNotFoundError:
    pass

# Permission denied (FR-061b) - library raises standard PermissionError
try:
    stats = calculate_statistics(Path("/protected/export.json"))
except PermissionError:
    # CLI catches and converts to exit code 1
    pass

# Invalid JSON
try:
    stats = calculate_statistics(Path("corrupt.json"))
except ParseError as e:
    # "JSON parsing failed: ..."
    pass
```

---

## Sorting Behavior (FR-043b, FR-046a)

### Stable Sort Guarantee

```python
# Python's sorted() is stable - equal-scored results maintain relative order
results = adapter.search(path, query)
sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
# Equal scores preserve original file order
```

### NULL updated_at Fallback

```python
# When sorting by date, updated_at is used; falls back to created_at if NULL
# This is handled internally by the adapter's sorting logic
query = SearchQuery(keywords=["python"], sort_by="date", sort_order="desc")

# Conversations with NULL updated_at use created_at for comparison
for result in adapter.search(path, query):
    # result.conversation.updated_at may be None
    # Sorting used updated_at or created_at as fallback
    pass
```

---

## Message ID Generation (FR-032a, FR-032b)

### Deterministic ID for Missing Source IDs

```python
# When source message lacks ID, adapter generates deterministic ID:
# Format: "msg-{conversation_id}-{zero_padded_index}"

conv = adapter.get_conversation_by_id(path, "abc-123")

for i, msg in enumerate(conv.messages):
    if msg.id.startswith("msg-abc-123-"):
        # This message had no source ID; was generated
        # msg.id == "msg-abc-123-001", "msg-abc-123-002", etc.
        pass

# Same source file always produces same generated IDs (reproducible)
```

---

## CSV Export Behavior (FR-053b, FR-053c)

### Newline Handling

```python
from echomine import CSVExporter

exporter = CSVExporter()

# Message content with newlines is preserved in quoted fields
# NOT escaped as \n - actual newlines inside quotes
csv_output = exporter.export_messages(conversation)

# CSV is compatible with:
# - Python csv.reader()
# - pandas.read_csv()
# - Excel import
```
