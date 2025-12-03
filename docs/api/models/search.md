# Search Models

Models for search queries and results.

## Overview

Search models provide type-safe interfaces for searching conversations with BM25 ranking, date filtering, and title matching.

## SearchQuery

::: echomine.models.search.SearchQuery
    options:
      show_source: true
      heading_level: 3

## SearchResult

::: echomine.models.search.SearchResult
    options:
      show_source: true
      heading_level: 3

## Usage Examples

### Basic Keyword Search

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")

# Create search query
query = SearchQuery(
    keywords=["algorithm", "leetcode"],
    limit=10
)

# Execute search
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

### Title Filtering (Fast)

Title filtering is metadata-only, much faster than full-text search:

```python
# Search by title (partial match, case-insensitive)
query = SearchQuery(
    title_filter="Project Alpha",
    limit=10
)

for result in adapter.search(export_file, query):
    print(result.conversation.title)
```

### Date Range Filtering

```python
from datetime import date

# Filter by creation date
query = SearchQuery(
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    limit=20
)

for result in adapter.search(export_file, query):
    print(f"{result.conversation.title} - {result.conversation.created_at.date()}")
```

### Combined Filtering

Combine multiple filters for precision:

```python
query = SearchQuery(
    keywords=["python", "async"],
    title_filter="Tutorial",
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),
    limit=5
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Created: {result.conversation.created_at.date()}")
    print(f"  Messages: {len(result.conversation.messages)}")
```

### Working with Results

```python
# Collect results
results = list(adapter.search(export_file, query))

# Results are sorted by relevance (descending)
assert results[0].score >= results[1].score

# Access conversation data
for result in results:
    conv = result.conversation
    print(f"Title: {conv.title}")
    print(f"Score: {result.score:.2f}")
    print(f"Messages: {len(conv.messages)}")
```

### Validation

SearchQuery validates constraints automatically:

```python
from pydantic import ValidationError

# ❌ Invalid: from_date > to_date
try:
    invalid = SearchQuery(
        from_date=date(2024, 12, 31),
        to_date=date(2024, 1, 1),
        keywords=["test"]
    )
except ValidationError as e:
    print(f"Error: {e}")

# ❌ Invalid: limit < 1
try:
    invalid = SearchQuery(
        keywords=["test"],
        limit=0
    )
except ValidationError as e:
    print(f"Error: limit must be >= 1")

# ✅ Valid: all constraints met
valid = SearchQuery(
    keywords=["test"],
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),
    limit=10
)
```

## SearchQuery Fields

### Optional Fields

All fields are optional, but at least one filter must be specified:

- **keywords** (`list[str] | None`): Keywords for BM25 full-text search
- **title_filter** (`str | None`): Partial title match (case-insensitive)
- **from_date** (`date | None`): Minimum creation date (inclusive)
- **to_date** (`date | None`): Maximum creation date (inclusive)
- **limit** (`int`): Maximum results to return (default: 10, min: 1)

### Validation Rules

1. **At least one filter**: Must specify keywords or title_filter
2. **Date range**: If both dates specified, `from_date <= to_date`
3. **Limit**: Must be >= 1

## SearchResult Fields

### Fields

- **conversation** (`Conversation`): The matched conversation
- **score** (`float`): Relevance score (0.0 to 1.0, higher is better)

### Score Interpretation

- **1.0**: Perfect match (all keywords present, high frequency)
- **0.8-0.9**: Excellent match (most keywords, good frequency)
- **0.6-0.7**: Good match (some keywords, moderate frequency)
- **0.4-0.5**: Fair match (few keywords, low frequency)
- **<0.4**: Weak match

**Note**: Title filtering and date filtering do not affect score. Score is based on BM25 ranking when keywords are specified.

## Search Behavior

### Keyword Search (BM25)

When keywords are specified:

1. Full-text search across all message content
2. BM25 relevance ranking
3. Results sorted by score (descending)

**Performance**: Scans all conversation content. Slower but comprehensive.

### Title Filtering

When only title_filter is specified:

1. Metadata-only search (no message content scan)
2. Partial match, case-insensitive
3. Results returned in file order

**Performance**: Fast (metadata-only). Use when you remember the title.

### Date Filtering

When date range is specified:

1. Filters by `conversation.created_at`
2. Inclusive range (from_date <= created_at <= to_date)
3. Can be combined with keyword or title search

### Combined Filters

Multiple filters are applied sequentially:

1. Date range filter (if specified)
2. Title filter (if specified) - metadata-only
3. Keyword search (if specified) - full-text with BM25
4. Limit results

## Performance Tips

1. **Use title filtering when possible**: 10-100x faster than keyword search
2. **Limit results**: Use `limit` to avoid processing thousands of matches
3. **Narrow date ranges**: Reduces conversations to search
4. **Specific keywords**: More specific keywords = better ranking

## Related Models

- **[Conversation](conversation.md)**: Result conversation model
- **[Message](message.md)**: Message model within conversations

## See Also

- [Library Usage Guide](../../library-usage.md#search-with-keywords)
- [BM25 Ranking](../search/ranking.md)
- [OpenAI Adapter](../adapters/openai.md)
