# BM25 Ranking

BM25 relevance ranking algorithm for full-text search.

## Overview

Echomine uses BM25 (Best Matching 25) algorithm for relevance ranking when searching conversations by keywords. BM25 is a probabilistic ranking function used by search engines to estimate the relevance of documents to a given query.

## API Reference

::: echomine.search.ranking
    options:
      show_source: true
      heading_level: 3

## How BM25 Works

### Algorithm

BM25 calculates a relevance score based on:

1. **Term Frequency (TF)**: How often keywords appear in the conversation
2. **Inverse Document Frequency (IDF)**: How rare keywords are across all conversations
3. **Document Length Normalization**: Adjusts for conversation length

**Formula:**

```
score(D, Q) = Σ IDF(qi) · (f(qi, D) · (k1 + 1)) / (f(qi, D) + k1 · (1 - b + b · |D| / avgdl))
```

Where:
- `D` = Conversation (document)
- `Q` = Search query keywords
- `f(qi, D)` = Frequency of keyword qi in conversation D
- `|D|` = Length of conversation (number of words)
- `avgdl` = Average conversation length across all conversations
- `k1` = Term saturation parameter (default: 1.5)
- `b` = Length normalization parameter (default: 0.75)

### Parameters

Echomine uses standard BM25 parameters:

- **k1 = 1.5**: Controls term saturation (higher = more weight to term frequency)
- **b = 0.75**: Controls length normalization (higher = more penalty for long documents)

## Usage Examples

### Basic Search with Ranking

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("conversations.json")

# Search with keywords
query = SearchQuery(keywords=["python", "async"], limit=10)

# Results are ranked by BM25 score
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

### Score Interpretation

```python
for result in adapter.search(export_file, query):
    score = result.score

    if score >= 0.8:
        quality = "Excellent match"
    elif score >= 0.6:
        quality = "Good match"
    elif score >= 0.4:
        quality = "Fair match"
    else:
        quality = "Weak match"

    print(f"[{score:.2f}] {quality}: {result.conversation.title}")
```

### Filtering by Score Threshold

```python
# Only show high-quality matches
min_score = 0.6

for result in adapter.search(export_file, query):
    if result.score >= min_score:
        print(f"[{result.score:.2f}] {result.conversation.title}")
```

## Score Normalization

Scores are normalized to 0.0-1.0 range:

- **1.0**: Perfect match (all keywords present, high frequency)
- **0.8-0.9**: Excellent match (most keywords, good frequency)
- **0.6-0.7**: Good match (some keywords, moderate frequency)
- **0.4-0.5**: Fair match (few keywords, low frequency)
- **<0.4**: Weak match

**Note**: Scores are relative. A score of 0.8 doesn't mean "80% match" - it means the conversation is in the top tier of matches for the query.

## Search Behavior

### Keyword Processing

Keywords are processed as follows:

1. **Case-insensitive**: "Python" matches "python", "PYTHON"
2. **Whole words**: "python" doesn't match "pythonic" (unless stemming is enabled)
3. **Multiple keywords**: All keywords contribute to score (OR logic)

### Content Searched

BM25 searches across:

- Message content (all messages in conversation)
- Conversation title (weighted higher)

### Ranking Order

Results are sorted by score in descending order:

```python
results = list(adapter.search(export_file, query))

# Results are pre-sorted by score
assert results[0].score >= results[1].score >= results[2].score
```

## Performance

### Time Complexity

- **O(n · m)**: Where n = number of conversations, m = average messages per conversation
- **Early termination**: Stops after finding `limit` top matches

### Memory Complexity

- **O(1)**: Constant memory (streaming-based)
- No full conversation buffering

### Speed

- **1.6GB file**: <30 seconds for keyword search
- **10K conversations**: <10 seconds

## Comparison with Other Ranking Methods

### BM25 vs TF-IDF

| Feature | BM25 | TF-IDF |
|---------|------|--------|
| **Saturation** | Yes (k1 parameter) | No |
| **Length normalization** | Yes (b parameter) | Limited |
| **Performance** | Better for varied-length documents | Better for uniform documents |
| **Echomine choice** | ✅ Used | ❌ Not used |

**Why BM25?** Conversations vary widely in length. BM25's length normalization prevents long conversations from dominating results.

### BM25 vs Semantic Search

| Feature | BM25 | Semantic Search |
|---------|------|----------------|
| **Query type** | Keywords | Natural language |
| **Speed** | Fast (no ML) | Slower (embedding models) |
| **Setup** | No dependencies | Requires embedding models |
| **Accuracy** | Good for exact terms | Better for synonyms/concepts |
| **Echomine v1.0** | ✅ Used | ❌ Not used |

**Future**: Semantic search may be added in v2.0 as an optional feature.

## Limitations

1. **No fuzzy matching**: "python" doesn't match "pythonic"
2. **No synonym matching**: "car" doesn't match "automobile"
3. **Keyword-only**: Doesn't understand semantic meaning
4. **No phrase matching**: "machine learning" treated as two separate keywords

## Advanced Usage

### Multi-Keyword Queries

```python
# All keywords contribute to score (OR logic)
query = SearchQuery(
    keywords=["python", "async", "asyncio", "coroutine"],
    limit=10
)

# Conversations with more keyword matches rank higher
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

### Combining with Filters

```python
from datetime import date

# BM25 ranking + date filtering
query = SearchQuery(
    keywords=["algorithm", "design"],
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    limit=10
)

# Date filter reduces search space, then BM25 ranks
for result in adapter.search(export_file, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

## Implementation Details

### Tokenization

Messages are tokenized by:

1. Lowercase conversion
2. Split on whitespace and punctuation
3. Filter stop words (optional, not implemented in v1.0)

### IDF Calculation

```python
import math

def calculate_idf(term: str, total_docs: int, docs_with_term: int) -> float:
    """Calculate inverse document frequency."""
    return math.log((total_docs - docs_with_term + 0.5) / (docs_with_term + 0.5) + 1.0)
```

### Score Calculation

```python
def calculate_bm25_score(
    term_freq: int,
    doc_length: int,
    avg_doc_length: float,
    idf: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calculate BM25 score for a single term."""
    numerator = term_freq * (k1 + 1)
    denominator = term_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
    return idf * (numerator / denominator)
```

## Related

- **[SearchQuery](../models/search.md)**: Search parameters
- **[SearchResult](../models/search.md#searchresult)**: Result model with score
- **[OpenAI Adapter](../adapters/openai.md)**: Adapter using BM25

## See Also

- [Library Usage](../../library-usage.md#search-with-keywords)
- [Architecture](../../architecture.md#search-operation-flow)

## References

- [BM25 on Wikipedia](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Elasticsearch BM25](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-similarity.html#bm25)
