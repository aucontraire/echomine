# Quickstart: Advanced Search Features

**Branch**: `002-advanced-search` | **Version**: 1.1.0
**Purpose**: Usage examples for new search capabilities

## Overview

Version 1.1.0 adds five advanced search features:

| Feature | CLI Flag | Library Field |
|---------|----------|---------------|
| Exact phrase matching | `--phrase` | `phrases` |
| Boolean match mode | `--match-mode` | `match_mode` |
| Exclude keywords | `--exclude` | `exclude_keywords` |
| Role filtering | `--role` | `role_filter` |
| Message snippets | (automatic) | `snippet` |

---

## How Search Filters Combine

Understanding how filters interact is crucial for effective searches:

### Two-Stage Matching Process

**Stage 1: Content Matching (OR relationship)**

Conversations match if **ANY** of these are true:
- **Phrases**: ANY phrase is found (exact match, case-insensitive)
- **Keywords**: Match according to `match_mode`
  - `match_mode="any"` (default): ANY keyword matches
  - `match_mode="all"`: ALL keywords must be present

**Key insight**: Phrases and keywords are alternatives, not cumulative. If you specify both, a conversation matches if EITHER a phrase matches OR keywords match.

```python
# This matches conversations containing EITHER "api" phrase OR "python" keyword
query = SearchQuery(phrases=["api"], keywords=["python"])

# This is NOT the same as requiring both!
```

**Stage 2: Post-Match Filters (AND relationship)**

After Stage 1 matching, results are filtered by **ALL** of these:
- `exclude_keywords`: Remove if ANY excluded term is found
- `role_filter`: Only search messages from specified role
- `title_filter`: Only include conversations with matching title
- `from_date` / `to_date`: Only include conversations in date range

### Filter Combination Examples

```python
from echomine import OpenAIAdapter, SearchQuery

adapter = OpenAIAdapter()

# Example 1: Phrase OR Keyword
# Matches: conversations with "api" phrase OR "python" keyword
query = SearchQuery(phrases=["api"], keywords=["python"])

# Example 2: Multiple keywords with match_mode
# Matches: conversations with "python" AND "async" (both required)
query = SearchQuery(keywords=["python", "async"], match_mode="all")

# Example 3: Content matching + exclusion
# Matches: ("api" phrase OR "python" keyword) AND NOT contains "java"
query = SearchQuery(
    phrases=["api"],
    keywords=["python"],
    exclude_keywords=["java"]
)

# Example 4: Content matching + role filter
# Matches: "python" keyword in user messages only
query = SearchQuery(keywords=["python"], role_filter="user")

# Example 5: Complex combination
# Matches: (phrase OR keyword) AND role AND title AND NOT excluded
query = SearchQuery(
    phrases=["algo-insights"],
    keywords=["refactor"],
    exclude_keywords=["test", "documentation"],
    role_filter="user",
    title_filter="Project",
    match_mode="any"  # Only affects keywords if multiple specified
)
```

### Important Notes

1. **match_mode only affects keywords**: When you have multiple keywords, `match_mode` determines if you need ANY or ALL. It does NOT affect the relationship between phrases and keywords.

2. **Phrases are always OR**: Multiple phrases use OR logic - match any one of them.

3. **Exclusion is always AND**: All `exclude_keywords` are applied as AND NOT conditions.

4. **Post-match filters are always AND**: All post-match filters must be satisfied simultaneously.

---

## Library API Examples

### Basic Usage with New Features

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")

# 1. Exact phrase matching (finds "algo-insights" exactly)
query = SearchQuery(phrases=["algo-insights"])
for result in adapter.search(export_file, query):
    print(f"{result.conversation.title}: {result.snippet}")

# 2. Multiple phrases (OR logic)
query = SearchQuery(phrases=["algo-insights", "data pipeline"])
for result in adapter.search(export_file, query):
    print(f"{result.score:.2f}: {result.conversation.title}")

# 3. Combine keywords and phrases
query = SearchQuery(
    keywords=["python", "refactor"],
    phrases=["algo-insights"],
)
results = list(adapter.search(export_file, query))
```

### Boolean Match Mode

```python
# Require ALL keywords present (AND logic)
query = SearchQuery(
    keywords=["python", "async", "await"],
    match_mode="all",  # Only return if ALL three keywords present
)
results = list(adapter.search(export_file, query))
print(f"Found {len(results)} conversations with ALL keywords")

# Compare with default ANY mode
query_any = SearchQuery(
    keywords=["python", "async", "await"],
    match_mode="any",  # Default: return if ANY keyword present
)
results_any = list(adapter.search(export_file, query_any))
print(f"Found {len(results_any)} conversations with ANY keyword")
```

### Exclude Keywords

```python
# Find Python conversations but exclude Django and Flask
query = SearchQuery(
    keywords=["python"],
    exclude_keywords=["django", "flask"],
)
for result in adapter.search(export_file, query):
    print(f"{result.conversation.title}")
    # Guaranteed: no results contain "django" or "flask"
```

### Role Filtering

```python
# Search only in YOUR messages (what you asked)
query = SearchQuery(
    keywords=["refactor", "optimize"],
    role_filter="user",
)
for result in adapter.search(export_file, query):
    print(f"You asked about: {result.snippet}")

# Search only in AI responses (what it recommended)
query = SearchQuery(
    keywords=["recommend", "suggest"],
    role_filter="assistant",
)
for result in adapter.search(export_file, query):
    print(f"AI suggested: {result.snippet}")
```

### Working with Snippets

```python
# Snippets are automatically extracted
query = SearchQuery(keywords=["algorithm"])
for result in adapter.search(export_file, query):
    print(f"Title: {result.conversation.title}")
    print(f"Score: {result.score:.2f}")
    print(f"Preview: {result.snippet}")
    print(f"Match count: {len(result.matched_message_ids)}")
    print("---")
```

### Combined Example (Power User)

```python
# Find conversations where:
# - You asked about refactoring (role=user)
# - That mention "algo-insights" exactly (phrase)
# - And discuss "python" (keyword)
# - But NOT testing or docs (exclude)
# - ALL terms must be present (match_mode=all)

query = SearchQuery(
    keywords=["python"],
    phrases=["algo-insights"],
    match_mode="all",
    exclude_keywords=["testing", "documentation"],
    role_filter="user",
    limit=5,
)

for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
    print(f"  Preview: {result.snippet}")
```

---

## CLI Examples

### Phrase Matching

```bash
# Find exact phrase (hyphen preserved)
echomine search export.json --phrase "algo-insights"

# Multiple phrases (OR logic)
echomine search export.json --phrase "algo-insights" --phrase "data pipeline"

# Combine with keywords
echomine search export.json -k "python" --phrase "algo-insights"
```

### Boolean Match Mode

```bash
# Require ALL keywords (AND logic)
echomine search export.json -k "python" -k "async" --match-mode all

# Explicit ANY mode (default behavior)
echomine search export.json -k "python" -k "async" --match-mode any
```

### Exclude Keywords

```bash
# Exclude single term
echomine search export.json -k "python" --exclude "django"

# Exclude multiple terms
echomine search export.json -k "python" --exclude "django" --exclude "flask"
```

### Role Filtering

```bash
# Search only your messages
echomine search export.json -k "refactor" --role user

# Search only AI responses
echomine search export.json -k "recommend" --role assistant
```

### Combined Example

```bash
# Full power query
echomine search export.json \
  -k "python" \
  --phrase "algo-insights" \
  --exclude "testing" \
  --role user \
  --match-mode all \
  --limit 5
```

### JSON Output with New Fields

```bash
# Get structured output for scripting
echomine search export.json -k "python" --json | jq '.results[].snippet'

# Filter results by role in jq
echomine search export.json -k "refactor" --role user --json | \
  jq '.results[] | {title: .conversation.title, preview: .snippet}'
```

---

## Output Examples

### Human-Readable Output

```
$ echomine search export.json --phrase "algo-insights" --role user

Score  ID         Title                    Created     Snippet                                         Messages
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
0.95   abc-123    Algo-insights project    2024-01-15  How should I structure the algo-insights...     47
0.82   def-456    Python optimization      2024-01-10  I'm using algo-insights for the base... (+2)    23

Showing 2 of 2 results
```

### JSON Output

```json
{
  "query": {
    "keywords": null,
    "phrases": ["algo-insights"],
    "match_mode": "any",
    "exclude_keywords": null,
    "role_filter": "user",
    "limit": 10
  },
  "results": [
    {
      "conversation": {
        "id": "abc-123",
        "title": "Algo-insights project"
      },
      "score": 0.95,
      "matched_message_ids": ["msg-001"],
      "snippet": "How should I structure the algo-insights..."
    }
  ],
  "total_count": 2,
  "returned_count": 2
}
```

---

## Migration from v1.0.x

### No Breaking Changes

All existing code continues to work unchanged:

```python
# v1.0.x code (still works in v1.1.0)
query = SearchQuery(keywords=["python"], limit=10)
for result in adapter.search(export_file, query):
    print(result.conversation.title)
```

### Optional Upgrades

```python
# v1.1.0 enhancement: add snippet handling
for result in adapter.search(export_file, query):
    print(result.conversation.title)
    if result.snippet:  # NEW: show preview
        print(f"  → {result.snippet}")
```

---

## Tips

1. **Use `--match-mode all` to narrow results** - Especially useful with multiple keywords

2. **Role filtering finds what YOU asked** - `--role user` shows your questions, `--role assistant` shows AI answers

3. **Phrases preserve special characters** - `--phrase "algo-insights"` matches exactly, not "algo" OR "insights"

4. **Exclude common noise terms** - `--exclude "test" --exclude "example"` cleans up results

5. **Combine for precision** - All flags work together for complex queries
