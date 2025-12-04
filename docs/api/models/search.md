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
    print(f"  Snippet: {result.snippet}")  # v1.1.0: automatic preview
    print(f"  Matches: {len(result.matched_message_ids)} messages")
```

### Advanced Search Features (v1.1.0+)

```python
# Exact phrase matching
query = SearchQuery(phrases=["algo-insights", "data pipeline"])
for result in adapter.search(export_file, query):
    print(f"{result.conversation.title}: {result.snippet}")

# Boolean match mode (require ALL keywords)
query = SearchQuery(
    keywords=["python", "async", "testing"],
    match_mode="all"  # AND logic
)

# Exclude unwanted results
query = SearchQuery(
    keywords=["python"],
    exclude_keywords=["django", "flask"]
)

# Role filtering
query = SearchQuery(
    keywords=["refactor"],
    role_filter="user"  # Search only your messages
)

# Combine all features
query = SearchQuery(
    keywords=["optimization"],
    phrases=["algo-insights"],
    match_mode="all",
    exclude_keywords=["test"],
    role_filter="user",
    limit=10
)
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

### Content Matching Fields (v1.1.0+)

- **keywords** (`list[str] | None`): Keywords for BM25 full-text search
- **phrases** (`list[str] | None`): Exact phrases to match (preserves special characters)
- **match_mode** (`Literal["any", "all"]`): Keyword matching logic (default: "any")
  - `"any"`: OR logic - match if ANY keyword present
  - `"all"`: AND logic - match if ALL keywords present
- **exclude_keywords** (`list[str] | None`): Terms to exclude (OR logic - excludes if ANY present)
- **role_filter** (`Literal["user", "assistant", "system"] | None`): Filter by message author role

### Legacy Filter Fields

- **title_filter** (`str | None`): Partial title match (case-insensitive)
- **from_date** (`date | None`): Minimum creation date (inclusive)
- **to_date** (`date | None`): Maximum creation date (inclusive)

### Output Control

- **limit** (`int`): Maximum results to return (default: 10, min: 1)

### Validation Rules

1. **At least one filter**: Must specify keywords, phrases, or title_filter
2. **Date range**: If both dates specified, `from_date <= to_date`
3. **Limit**: Must be >= 1
4. **Match mode**: Only affects keywords (phrases always use OR logic)
5. **Role filter**: Must be one of: "user", "assistant", "system" (case-insensitive)

## SearchResult Fields

### Fields

- **conversation** (`Conversation`): The matched conversation
- **score** (`float`): Relevance score (0.0 to 1.0, higher is better)
- **matched_message_ids** (`list[str]`): IDs of messages that matched the search query (v1.1.0+)
- **snippet** (`str`): Preview text from first matching message, ~100 characters (v1.1.0+)

### Score Interpretation

- **1.0**: Perfect match (all keywords present, high frequency)
- **0.8-0.9**: Excellent match (most keywords, good frequency)
- **0.6-0.7**: Good match (some keywords, moderate frequency)
- **0.4-0.5**: Fair match (few keywords, low frequency)
- **<0.4**: Weak match

**Note**: Title filtering and date filtering do not affect score. Score is based on BM25 ranking when keywords or phrases are specified.

### Snippet Features (v1.1.0+)

- Extracted from first matching message
- Truncated to ~100 characters with "..." suffix
- Multiple matches indicated by "(+N more)" in CLI output
- Fallback text for empty/malformed content
- Always present (never None)

### Working with Matched Messages

```python
for result in adapter.search(export_file, query):
    conversation = result.conversation
    matched_ids = result.matched_message_ids

    # Find actual matched messages
    matched_messages = [
        msg for msg in conversation.messages
        if msg.id in matched_ids
    ]

    print(f"Found {len(matched_messages)} matching messages")
    for msg in matched_messages:
        print(f"  [{msg.role}] {msg.content[:50]}...")
```

## Search Behavior

### Two-Stage Matching Process (v1.1.0+)

**Stage 1: Content Matching (OR relationship)**

Conversations match if ANY of these are true:
- **Phrases**: ANY phrase is found (exact match, case-insensitive)
- **Keywords**: Match according to `match_mode`
  - `match_mode="any"` (default): ANY keyword present
  - `match_mode="all"`: ALL keywords present

**Key insight**: Phrases and keywords are alternatives, not cumulative. If both specified, matches if EITHER phrases match OR keywords match.

**Stage 2: Post-Match Filters (AND relationship)**

After Stage 1, results are filtered by ALL of these:
- `exclude_keywords`: Remove if ANY excluded term found
- `role_filter`: Only messages from specified role
- `title_filter`: Only conversations with matching title
- `from_date` / `to_date`: Only in date range

### Filter Combination Examples

```python
# Phrase OR keyword (matches either)
SearchQuery(phrases=["api"], keywords=["python"])

# Multiple keywords with ALL mode (requires both)
SearchQuery(keywords=["python", "async"], match_mode="all")

# Content + exclusion
SearchQuery(phrases=["api"], keywords=["python"], exclude_keywords=["java"])

# Role-specific search
SearchQuery(keywords=["python"], role_filter="user")
```

### Legacy Behavior (v1.0.x)

For backward compatibility, v1.0.x behavior is preserved:

1. Date range filter (if specified)
2. Title filter (if specified) - metadata-only
3. Keyword search (if specified) - full-text with BM25
4. Limit results

### Keyword Search (BM25)

When keywords or phrases are specified:

1. Full-text search across message content
2. BM25 relevance ranking
3. Results sorted by score (descending)
4. Snippet extraction from first match

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
3. Can be combined with keyword, phrase, or title search

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
