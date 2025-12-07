# Research: Baseline Enhancement Package v1.2.0

**Feature**: 003-baseline-enhancements
**Date**: 2025-12-05
**Status**: Complete

## Research Tasks

No "NEEDS CLARIFICATION" items in Technical Context - all technologies are established.
Research focuses on best practices for new feature implementations.

---

## 1. YAML Frontmatter Format (FR-030-035)

### Decision
Use Jekyll/Hugo-compatible YAML frontmatter with triple-dash delimiters.

### Rationale
- Jekyll/Hugo conventions are the de facto standard for static site generators
- Triple-dash delimiters (`---`) are universally recognized
- Compatible with Obsidian, MkDocs, and other knowledge management tools
- PyYAML is already a transitive dependency via Pydantic

### Alternatives Considered
1. **TOML frontmatter**: Less widely supported; requires new dependency
2. **JSON frontmatter**: Valid but less human-readable
3. **Custom format**: Non-standard; incompatible with existing tooling

### Implementation Notes
```python
# Use safe_dump for security (no arbitrary Python objects)
import yaml

def generate_frontmatter(metadata: dict[str, Any]) -> str:
    """Generate YAML frontmatter from metadata dict."""
    yaml_content = yaml.safe_dump(metadata, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n\n"
```

---

## 2. CSV Export Format (FR-049-055)

### Decision
RFC 4180 compliant CSV with Python's csv module and streaming writer.

### Rationale
- RFC 4180 is the formal standard for CSV
- Python's csv module handles proper escaping automatically
- Streaming writer pattern ensures O(1) memory for large exports
- Excel, pandas, R all support RFC 4180

### Alternatives Considered
1. **TSV format**: Less widely supported than CSV
2. **Excel format (xlsx)**: Requires openpyxl dependency; binary format
3. **Custom delimiters**: Non-standard; compatibility issues

### Implementation Notes
```python
import csv
from io import StringIO

def write_csv_row(writer: csv.writer, row: list[str]) -> None:
    """Write single row (streaming pattern)."""
    writer.writerow(row)

# CSV schema for conversations:
# conversation_id, title, created_at, updated_at, message_count, score

# CSV schema for messages:
# conversation_id, message_id, role, timestamp, content
```

### Escaping Rules (RFC 4180)
- Fields containing commas, quotes, or newlines must be quoted
- Double quotes inside quoted fields escaped as `""`
- Python's csv module handles this automatically

---

## 3. Statistics Calculation Algorithm (FR-009-017, FR-018-024)

### Decision
Single-pass streaming algorithm with O(1) memory accumulator pattern.

### Rationale
- Single pass ensures O(N) time complexity
- Accumulator pattern keeps memory at O(1)
- Compatible with existing ijson streaming architecture

### Alternatives Considered
1. **Multi-pass (count, then aggregate)**: O(2N) time; unnecessary
2. **Load all into memory**: Violates Constitution Principle VIII
3. **Database indexing**: Overkill; violates simplicity principle

### Implementation Notes
```python
@dataclass
class StatsAccumulator:
    """O(1) memory accumulator for streaming statistics."""
    total_conversations: int = 0
    total_messages: int = 0
    earliest_date: datetime | None = None
    latest_date: datetime | None = None
    largest_conv: tuple[str, str, int] | None = None  # (id, title, count)
    smallest_conv: tuple[str, str, int] | None = None

    def update(self, conv: Conversation) -> None:
        """Update accumulator with single conversation (O(1))."""
        self.total_conversations += 1
        self.total_messages += conv.message_count
        # Update min/max tracking...
```

---

## 4. Rich CLI Formatting (FR-036-042)

### Decision
Use Rich library's Console, Table, and Progress classes with TTY detection.

### Rationale
- Rich is already a project dependency (v13.0+)
- Built-in TTY detection via `console.is_terminal`
- Table class provides consistent column alignment
- Progress class integrates with iterators

### Alternatives Considered
1. **Manual ANSI codes**: Error-prone; incompatible with Windows
2. **Texttable library**: Less feature-rich; new dependency
3. **Click's echo**: Limited formatting; less flexible

### Implementation Notes
```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

def format_score_color(score: float) -> str:
    """Color-code score: >0.7 green, 0.4-0.7 yellow, <0.4 red."""
    if score > 0.7:
        return f"[green]{score:.3f}[/green]"
    elif score >= 0.4:
        return f"[yellow]{score:.3f}[/yellow]"
    else:
        return f"[red]{score:.3f}[/red]"

# Disable rich when not TTY or --json/--format csv
if not console.is_terminal or output_format in ("json", "csv"):
    console = Console(force_terminal=False, no_color=True)
```

---

## 5. Message Count Filtering Strategy (FR-001-008)

### Decision
Filter during streaming loop, before BM25 scoring.

### Rationale
- Early filtering reduces corpus size for BM25
- No need to score conversations that will be filtered out
- Maintains O(N) time complexity
- No additional memory overhead

### Alternatives Considered
1. **Post-scoring filter**: Wasteful; scores filtered conversations
2. **Pre-index with message counts**: Overkill; violates simplicity
3. **Separate pass for count**: O(2N) time; unnecessary

### Implementation Notes
```python
# In OpenAIAdapter.search():
for conv in self.stream_conversations(file_path):
    # Apply message count filter early
    if query.min_messages is not None and conv.message_count < query.min_messages:
        continue
    if query.max_messages is not None and conv.message_count > query.max_messages:
        continue

    # Only add matching conversations to corpus
    conversations.append(conv)
```

---

## 6. Sort Implementation (FR-043-048)

### Decision
In-memory sort after filtering, before limit application.

### Rationale
- Sorting requires comparing all results (O(N log N))
- Apply after filtering to minimize sort set
- Apply before limit to ensure correct top-K results
- Python's sorted() is efficient for in-memory collections

### Alternatives Considered
1. **Database with ORDER BY**: Overkill; no database
2. **Heap-based top-K**: Only beneficial for very large N with small K
3. **External sort**: Unnecessary; results fit in memory

### Implementation Notes
```python
from typing import Literal

SortField = Literal["score", "date", "title", "messages"]
SortOrder = Literal["asc", "desc"]

def sort_results(
    results: list[SearchResult[Conversation]],
    sort_by: SortField,
    order: SortOrder,
) -> list[SearchResult[Conversation]]:
    """Sort results by specified field and order."""
    key_funcs = {
        "score": lambda r: r.score,
        "date": lambda r: r.conversation.updated_at_or_created,
        "title": lambda r: r.conversation.title.lower(),
        "messages": lambda r: r.conversation.message_count,
    }
    reverse = order == "desc"
    return sorted(results, key=key_funcs[sort_by], reverse=reverse)
```

---

## 7. Per-Conversation Statistics (FR-018-024)

### Decision
Pure function taking Conversation, returns ConversationStatistics model.

### Rationale
- Library-first: function works on in-memory model
- No file I/O needed (CLI finds conversation via adapter)
- Pure function enables easy testing
- Separation of concerns: adapter finds, function analyzes

### Alternatives Considered
1. **Adapter method**: Mixes concerns; less reusable
2. **Method on Conversation**: Pollutes model with business logic
3. **Streaming from file**: Unnecessary; single conversation fits in memory

### Implementation Notes
```python
def calculate_conversation_statistics(
    conversation: Conversation,
) -> ConversationStatistics:
    """Calculate statistics for single conversation.

    Pure function - no I/O, no side effects.

    Args:
        conversation: Conversation to analyze

    Returns:
        ConversationStatistics with role breakdown, duration, etc.
    """
    message_count_by_role = {"user": 0, "assistant": 0, "system": 0}
    for msg in conversation.messages:
        message_count_by_role[msg.role] += 1

    # Calculate duration and average gap...
    return ConversationStatistics(...)
```

---

## Summary

All research complete. No blockers identified.

| Topic | Decision | Confidence |
|-------|----------|------------|
| YAML frontmatter | Jekyll/Hugo triple-dash | High |
| CSV export | RFC 4180 with csv module | High |
| Statistics algorithm | Single-pass streaming | High |
| Rich CLI formatting | Rich library with TTY detection | High |
| Message count filtering | Filter during streaming | High |
| Sort implementation | In-memory sort post-filter | High |
| Per-conversation stats | Pure function on Conversation | High |

**Ready for Phase 1: Design & Contracts**
