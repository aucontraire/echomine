# Research: Advanced Search Enhancement Package

**Branch**: `002-advanced-search` | **Date**: 2025-12-03
**Purpose**: Resolve technical decisions and document rationale before implementation

## Technical Decisions

### TD-1: Phrase Matching Strategy

**Decision**: Case-insensitive substring matching (no word boundaries)

**Rationale**:
- Simple implementation: `phrase.lower() in text.lower()`
- Fast: O(n) substring search, no regex overhead
- Handles all special characters naturally (hyphens, dots, underscores)
- FR-006 requires literal matching of special characters

**Alternatives Considered**:

| Alternative | Why Rejected |
|-------------|--------------|
| Regex word boundaries (`\b`) | Complex escaping, slower, breaks on hyphens |
| Token-based matching | Inconsistent with "exact phrase" requirement |
| Fuzzy matching | Out of scope (spec says exact only) |

**Trade-off**: "log" matches in "catalog"
**Mitigation**: Document in user guide; add `--exact-word-boundaries` flag in future if requested

---

### TD-2: Phrase Score Contribution

**Decision**: Binary scoring (1.0 if any phrase matches, 0.0 otherwise)

**Rationale**:
- Simple and predictable ranking behavior
- Combined with BM25: `total = bm25_score + phrase_score`
- Phrases boost relevance without complex TF-IDF calculations

**Alternatives Considered**:

| Alternative | Why Rejected |
|-------------|--------------|
| Phrase TF-IDF | Complex, marginal benefit for exact matching |
| Phrase count boost | Multiple matches inflate score unpredictably |
| No score contribution | Phrases wouldn't affect ranking order |

---

### TD-3: Boolean Match Mode Implementation

**Decision**: Apply during scoring phase with early exit for "all" mode

**Rationale**:
- Early exit saves computation (skip BM25 if not all terms present)
- Applies to both keywords AND phrases uniformly
- Default "any" preserves backward compatibility (FR-008)

**Algorithm**:
```python
if query.match_mode == "all":
    # Check keywords
    for kw in query.keywords or []:
        if kw.lower() not in conv_text.lower():
            continue  # Skip this conversation
    # Check phrases
    for phrase in query.phrases or []:
        if phrase.lower() not in conv_text.lower():
            continue  # Skip this conversation
# Proceed with BM25 scoring
```

---

### TD-4: Exclusion Filter Timing

**Decision**: Post-filter after scoring, before sorting (per FR-014)

**Rationale**:
- FR-014 explicitly requires "after matching but before ranking"
- Clear separation of concerns: scoring logic stays pure
- Excluded conversations don't affect BM25 IDF (corpus already built)

**Tokenization**: Use same `BM25Scorer._tokenize()` method (FR-015)

**Algorithm**:
```python
# After scoring, before sort
if query.exclude_keywords:
    exclude_tokens = set()
    for kw in query.exclude_keywords:
        exclude_tokens.update(scorer._tokenize(kw))

    scored = [
        (conv, score, ids) for conv, score, ids in scored
        if not any(t in scorer._tokenize(conv_text) for t in exclude_tokens)
    ]
```

---

### TD-5: Role Filter Application Point

**Decision**: Pre-corpus construction (filter messages before building text)

**Rationale**:
- FR-018 requires "applied before keyword/phrase matching"
- Correctly affects BM25 IDF (only filtered messages count)
- User expectation: "search in user messages" means only user messages searchable

**Edge Case**: Conversation with no messages of specified role
- Corpus text = title only
- Can still match on title keywords

**Algorithm**:
```python
if query.role_filter:
    messages = [m for m in conv.messages if m.role == query.role_filter]
else:
    messages = conv.messages

conv_text = f"{conv.title} " + " ".join(m.content for m in messages)
```

---

### TD-6: Snippet Extraction Strategy

**Decision**: Extract from first matched message, truncate to 100 chars

**Rationale**:
- FR-021-025 define requirements clearly
- First match is most relevant for user assessment
- 100 chars sufficient for relevance preview (assumption validated)

**Fallback Text**: "[Content unavailable]" for malformed content (FR-025)

**Algorithm**:
```python
def extract_snippet(conv: Conversation, matched_ids: list[str]) -> str:
    if not matched_ids:
        return "[No matches]"

    first_id = matched_ids[0]
    msg = next((m for m in conv.messages if m.id == first_id), None)

    if not msg or not msg.content:
        return "[Content unavailable]"

    content = msg.content
    if len(content) > 100:
        snippet = content[:97] + "..."
    else:
        snippet = content

    if len(matched_ids) > 1:
        snippet += f" (+{len(matched_ids) - 1} more matches)"

    return snippet
```

---

### TD-7: Memory Impact Assessment

**Decision**: Minimal memory overhead, no architecture changes needed

**Analysis**:

| Component | Memory Impact | Justification |
|-----------|---------------|---------------|
| `SearchQuery` new fields | ~200 bytes/query | 4 optional fields, primitives only |
| `SearchResult.snippet` | ~100 bytes/result | String truncated to 100 chars |
| Phrase matching | 0 | Operates on existing conv_text string |
| Role filtering | 0 | Filters during iteration, no extra storage |
| Exclusion filtering | O(k) | k = exclude token count, typically <10 |

**Total**: <10KB additional memory for 100 search results

**Conclusion**: SC-006 (constant memory) maintained. No streaming changes needed.

---

### TD-8: CLI Flag Design

**Decision**: Follow existing patterns from `search.py`

**New Flags**:

| Flag | Type | Default | Multiple | Description |
|------|------|---------|----------|-------------|
| `--phrase` | `str` | None | Yes | Exact phrase to match |
| `--match-mode` | `Literal["all", "any"]` | "any" | No | Require all or any terms |
| `--exclude` | `str` | None | Yes | Exclude conversations with term |
| `--role` | `Literal["user", "assistant", "system"]` | None | No | Filter by message role |

**Validation**: At least one search term required (`-k` or `--phrase` or `--title`)

---

## Best Practices Applied

### From Existing Codebase

1. **Pydantic Field Pattern**:
   ```python
   field: Optional[type] = Field(default=None, description="...")
   ```

2. **CLI Multiple Values**:
   ```python
   phrase: Annotated[Optional[list[str]], Option("--phrase")] = None
   ```

3. **Streaming Preservation**:
   - Generator yields (no list accumulation)
   - Context managers for file handles

4. **Error Handling**:
   - ValidationError for model issues
   - Graceful degradation with logging

### Testing Patterns

1. **Unit Tests**: One test file per feature, parametrized tests
2. **Integration Tests**: End-to-end with fixture files
3. **Contract Tests**: CLI flag validation, exit codes
4. **Performance Tests**: Benchmarks with `pytest-benchmark`

---

## Unresolved Items

None. All technical decisions resolved.

---

## References

- [spec.md](./spec.md): Feature specification (28 FRs, 6 SCs)
- [constitution.md](../../.specify/memory/constitution.md): 8 principles
- [BM25Scorer](../../src/echomine/search/ranking.py): Existing scoring implementation
- [OpenAIAdapter.search()](../../src/echomine/adapters/openai.py): Current search logic
