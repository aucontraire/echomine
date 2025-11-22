# Gap Resolution: Priority 2 High-Priority Gaps

**Feature**: 001-ai-chat-parser
**Date**: 2025-11-22
**Status**: In Progress
**Total Gaps Addressed**: 28 items (Priority 2 - Early Implementation)

---

## 1. CLI Interface Contract (5 items)

### CHK031: stdout/stderr Separation Requirements

**Gap**: Are stdout/stderr separation requirements unambiguous for all output types (results, progress, errors)?

**Decision**:
**Strict separation**: Results to stdout, everything else to stderr. This enables Unix pipeline composability.

**Output Routing Rules**:

| Output Type | Stream | Rationale |
|------------|--------|-----------|
| **Search results** (default format) | stdout | Primary output, pipeable |
| **Search results** (--json format) | stdout | Primary output, pipeable |
| **Export file content** | File (not stdout) | Too large for pipes, written to disk |
| **Progress indicators** | stderr | Metadata, shouldn't pollute results |
| **Warnings** (skipped entries) | stderr | Metadata, shouldn't pollute results |
| **Error messages** | stderr | Diagnostic, shouldn't pollute results |
| **Help text** (--help) | stdout | Informational output |
| **Version info** (--version) | stdout | Informational output |

**CLI Output Examples**:

```bash
# Results go to stdout (pipeable)
echomine search conversations.json --keywords "algorithm" | jq '.[] | .title'

# Progress goes to stderr (doesn't pollute pipe)
echomine search conversations.json --keywords "algorithm" 2>/dev/null

# Errors go to stderr
echomine search missing.json --keywords "test" 2>errors.log

# Compose with other tools
echomine search export.json --keywords "python" --json | \
  jq '.[] | select(.score > 0.8)' | \
  wc -l
```

**Rationale**: Unix philosophy - stdout for data, stderr for metadata/diagnostics. This enables: piping results to other tools, redirecting errors separately, combining multiple commands.

**New Requirements**:
- **FR-291**: CLI MUST write search results (default and --json format) to stdout
- **FR-292**: CLI MUST write progress indicators, warnings, and diagnostic messages to stderr
- **FR-293**: CLI MUST write error messages to stderr
- **FR-294**: CLI MUST write help text (--help) and version info (--version) to stdout
- **FR-295**: CLI MUST NOT mix result data and metadata in same stream (strict separation)

---

### CHK032: Exit Code Requirements for All Failure Modes

**Gap**: Are exit code requirements enumerated for all failure modes?

**Decision**:
Use **standard Unix exit codes** with specific mappings for common failures.

**Exit Code Specification**:

| Exit Code | Meaning | Triggered By | Example |
|-----------|---------|--------------|---------|
| **0** | Success | Normal completion, even with skipped entries | `echomine search export.json --keywords "test"` |
| **1** | General error | File not found, permission denied, parse error, validation error | `echomine search missing.json` |
| **2** | Usage error | Invalid CLI arguments, missing required args | `echomine search` (no file path) |
| **130** | Interrupted | User pressed Ctrl+C (SIGINT) | User cancels long operation |

**Detailed Exit Code Logic**:

```python
# Exit code 0: Success (even with skipped entries)
if operation_completed:
    sys.exit(0)  # Partial success is success

# Exit code 1: Operational errors
if file_not_found or permission_denied or parse_error or validation_error:
    sys.exit(1)

# Exit code 2: Usage errors
if invalid_arguments or missing_required_args:
    sys.exit(2)

# Exit code 130: Interrupted (Ctrl+C)
if keyboard_interrupt:
    sys.exit(130)  # Standard SIGINT exit code
```

**Examples**:

```bash
# Success (exit 0)
$ echomine search export.json --keywords "python"
$ echo $?
0

# File not found (exit 1)
$ echomine search missing.json --keywords "test"
Error: Export file not found: missing.json
$ echo $?
1

# Usage error (exit 2)
$ echomine search
Error: Missing required argument: FILE_PATH
$ echo $?
2

# Interrupted (exit 130)
$ echomine search huge-export.json --keywords "test"
^C
$ echo $?
130
```

**Rationale**: Standard Unix exit codes for shell script compatibility. Exit 0 even with skipped entries (partial success is success). Exit 2 for usage errors (user fix required). Exit 130 for interrupts (standard SIGINT code).

**New Requirements**:
- **FR-296**: CLI MUST exit with code 0 for successful operations (even if some entries were skipped)
- **FR-297**: CLI MUST exit with code 1 for operational errors (file not found, permission denied, parse errors, validation errors)
- **FR-298**: CLI MUST exit with code 2 for usage errors (invalid arguments, missing required parameters)
- **FR-299**: CLI MUST exit with code 130 when interrupted by user (Ctrl+C / SIGINT)
- **FR-300**: CLI MUST document exit codes in --help text and documentation

---

### CHK033: JSON Output Schema Requirements

**Gap**: Are JSON output schema requirements specified (--json flag output structure)?

**Decision**:
Define **strict JSON schema** for --json output with consistent field names and structure.

**Search Results JSON Schema**:

```json
{
  "results": [
    {
      "conversation_id": "string (UUID)",
      "title": "string",
      "created_at": "string (ISO 8601 UTC)",
      "updated_at": "string (ISO 8601 UTC)",
      "score": 0.85,
      "matched_message_ids": ["msg-1", "msg-2"],
      "message_count": 42
    }
  ],
  "metadata": {
    "query": {
      "keywords": ["algorithm", "python"],
      "title_filter": null,
      "date_from": null,
      "date_to": null,
      "limit": 10
    },
    "total_results": 5,
    "skipped_conversations": 2,
    "elapsed_seconds": 1.234
  }
}
```

**Field Specifications**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `results` | Array | Yes | List of matching conversations |
| `results[].conversation_id` | String | Yes | UUID from export |
| `results[].title` | String | Yes | Conversation title |
| `results[].created_at` | String | Yes | ISO 8601 UTC timestamp |
| `results[].updated_at` | String | Yes | ISO 8601 UTC timestamp |
| `results[].score` | Number | Yes | Relevance score (0.0-1.0) |
| `results[].matched_message_ids` | Array | Yes | Message IDs with keyword matches |
| `results[].message_count` | Number | Yes | Total messages in conversation |
| `metadata` | Object | Yes | Query and execution metadata |
| `metadata.query` | Object | Yes | Original query parameters |
| `metadata.total_results` | Number | Yes | Count of returned results |
| `metadata.skipped_conversations` | Number | Yes | Count of malformed entries |
| `metadata.elapsed_seconds` | Number | Yes | Query execution time |

**CLI Usage**:

```bash
# JSON output
echomine search export.json --keywords "python" --json

# Pipe to jq for filtering
echomine search export.json --keywords "algorithm" --json | \
  jq '.results[] | select(.score > 0.8)'

# Extract specific fields
echomine search export.json --keywords "test" --json | \
  jq -r '.results[] | "\(.conversation_id): \(.title)"'
```

**Rationale**: Consistent JSON schema enables programmatic parsing. ISO 8601 timestamps for unambiguous dates. Metadata separate from results for clarity. jq-friendly structure (flat objects, consistent field names).

**New Requirements**:
- **FR-301**: CLI --json flag MUST output valid JSON with schema: `{"results": [...], "metadata": {...}}`
- **FR-302**: JSON results array MUST include fields: conversation_id, title, created_at, updated_at, score, matched_message_ids, message_count
- **FR-303**: JSON metadata object MUST include fields: query, total_results, skipped_conversations, elapsed_seconds
- **FR-304**: JSON timestamps MUST use ISO 8601 format with UTC timezone (YYYY-MM-DDTHH:MM:SSZ)
- **FR-305**: JSON output MUST be valid (parseable by standard JSON libraries) and pretty-printed with 2-space indentation
- **FR-306**: CLI documentation MUST include JSON schema specification and jq usage examples

---

### CHK036: CLI Composability Requirements

**Gap**: Are CLI composability requirements documented (pipeline examples, jq integration)?

**Decision**:
Design CLI for **Unix pipeline composability** with explicit examples and patterns.

**Composability Principles**:
1. **Stdout for data**: Results go to stdout (pipeable)
2. **Stderr for metadata**: Progress/errors go to stderr (doesn't pollute pipes)
3. **Exit codes**: Follow Unix conventions (0=success, 1=error, 2=usage)
4. **JSON output**: Machine-readable format for processing
5. **Newline-delimited**: Each result on separate line (NDJSON for streaming)

**Pipeline Examples**:

```bash
# Example 1: Count conversations matching keyword
echomine search export.json --keywords "python" --json | \
  jq '.results | length'

# Example 2: Extract titles of high-relevance results
echomine search export.json --keywords "algorithm" --json | \
  jq -r '.results[] | select(.score > 0.8) | .title'

# Example 3: Get conversation IDs for further processing
echomine search export.json --keywords "refactor" --json | \
  jq -r '.results[].conversation_id' | \
  while read conv_id; do
    echomine export export.json "$conv_id" --format markdown
  done

# Example 4: Filter by date range, then by keyword
echomine search export.json \
  --from 2024-01-01 \
  --to 2024-03-31 \
  --keywords "project" \
  --json | \
  jq '.results[] | select(.message_count > 10)'

# Example 5: Suppress progress (stderr), keep results (stdout)
echomine search export.json --keywords "test" 2>/dev/null | \
  jq -r '.results[].title'

# Example 6: Log errors separately while processing results
echomine search export.json --keywords "debug" --json \
  2>search-errors.log | \
  jq '.results[]' > results.json

# Example 7: Combine multiple searches
(echomine search export1.json --keywords "python" --json;
 echomine search export2.json --keywords "python" --json) | \
  jq -s 'add | .results |= add' > combined-results.json
```

**Integration with Common Tools**:

| Tool | Purpose | Example |
|------|---------|---------|
| **jq** | JSON filtering | `... \| jq '.results[] \| select(.score > 0.8)'` |
| **grep** | Text filtering | `... \| jq -r '.results[].title' \| grep -i "python"` |
| **wc** | Counting | `... \| jq '.results[]' \| wc -l` |
| **xargs** | Batch processing | `... \| jq -r '.results[].conversation_id' \| xargs -I {} ...` |
| **sort** | Ordering | `... \| jq -r '.results[].title' \| sort` |
| **uniq** | Deduplication | `... \| jq -r '.results[].title' \| sort \| uniq` |

**Rationale**: Unix philosophy - small, focused tools that compose well. JSON output enables programmatic processing. Strict stdout/stderr separation enables flexible pipelines.

**New Requirements**:
- **FR-307**: CLI MUST be composable in Unix pipelines (results to stdout, metadata to stderr)
- **FR-308**: CLI --json output MUST be valid JSON parseable by jq and standard JSON libraries
- **FR-309**: CLI documentation MUST include at least 5 pipeline examples showing composition with jq, grep, xargs
- **FR-310**: CLI MUST support quiet mode (suppress progress to stderr) for cleaner pipeline integration
- **FR-311**: CLI error messages MUST be actionable and include exit codes in documentation

---

### CHK141: CLI Exit Codes Consistent with FR-022 and FR-033

**Gap**: Are CLI exit codes consistent with FR-022 and FR-033?

**Decision**:
**Consolidate exit code specification** across all requirements. This is consistent with CHK032 resolution.

**Consolidated Exit Code Mapping**:

| Scenario | Exit Code | FR Reference | Example |
|----------|-----------|--------------|---------|
| Successful search with results | 0 | FR-022 | `echomine search export.json --keywords "test"` |
| Successful search with 0 results | 0 | FR-022 | `echomine search export.json --keywords "nonexistent"` |
| File not found | 1 | FR-033 | `echomine search missing.json` |
| Permission denied | 1 | FR-033 | `echomine search /root/export.json` |
| Parse error (corrupt file) | 1 | FR-033 | `echomine search corrupt.json` |
| Validation error | 1 | - | `echomine search export.json --from invalid-date` |
| Usage error (missing args) | 2 | - | `echomine search` |
| Invalid flag combination | 2 | - | `echomine search export.json --json --format markdown` |
| User interrupt (Ctrl+C) | 130 | - | User presses Ctrl+C during long operation |

**Consistency Check**:
- ✅ FR-022: "write error messages to stderr and use non-zero exit codes on failure" → Exit 1 for operational errors
- ✅ FR-033: "fail immediately (no retries) on file system errors with exit code 1" → File access errors = Exit 1
- ✅ New: Usage errors = Exit 2 (standard Unix convention)
- ✅ New: Interrupted = Exit 130 (standard SIGINT code)

**No conflicts** - all specifications align with standard Unix exit code conventions.

**New Requirements**:
- **FR-312**: CLI exit codes MUST be consistent with FR-022 (non-zero on failure) and FR-033 (exit 1 for file system errors)
- **FR-313**: CLI MUST use exit code 0 for all successful operations (including 0 results)
- **FR-314**: CLI MUST use exit code 1 for all operational failures (file access, parsing, validation)
- **FR-315**: CLI MUST use exit code 2 for usage errors (invalid arguments, missing parameters)
- **FR-316**: CLI MUST use exit code 130 for user interrupts (SIGINT)

---

## 2. Search & Filtering Semantics (4 items)

### CHK037: Relevance Score Quantified with TF-IDF Algorithm

**Gap**: Is "relevance score" quantified with specific algorithm (TF-IDF formula)?

**Decision**:
Use **BM25 algorithm** (improved TF-IDF variant) with documented parameters.

**Why BM25 over classic TF-IDF**:
- BM25 has **term saturation** (diminishing returns for repeated keywords)
- BM25 has **document length normalization** (favors longer documents less)
- BM25 is **industry standard** (Elasticsearch, Lucene use BM25)
- BM25 is **empirically better** for short documents (like chat messages)

**BM25 Formula**:

```
score(Q, D) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

Where:
- Q = query keywords
- D = document (conversation)
- f(qi, D) = frequency of keyword qi in document D
- |D| = number of words in document D
- avgdl = average document length in corpus
- k1 = term saturation parameter (default: 1.5)
- b = length normalization parameter (default: 0.75)
- IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5))
  - N = total conversations in export
  - n(qi) = conversations containing keyword qi
```

**Implementation Parameters**:

```python
class BM25Scorer:
    """BM25 relevance scoring for keyword search (per FR-317)."""

    def __init__(
        self,
        k1: float = 1.5,  # Term saturation (higher = more weight to term frequency)
        b: float = 0.75,  # Length normalization (0 = no normalization, 1 = full)
    ):
        self.k1 = k1
        self.b = b

    def score(self, query_keywords: list[str], conversation: Conversation) -> float:
        """Calculate BM25 relevance score for conversation."""
        # Implementation details...
```

**Score Normalization**:
- Raw BM25 scores are **unbounded** (can be very large)
- Normalize to **0.0-1.0 range** using: `score_normalized = score_raw / (score_raw + 1)`
- This ensures consistent score interpretation across queries

**Examples**:

```python
# High relevance: keyword appears multiple times in short conversation
conversation1 = "python python python code"
query = ["python"]
# BM25 score: ~0.85 (high)

# Medium relevance: keyword appears once in longer conversation
conversation2 = "python is great for data science and machine learning..."
query = ["python"]
# BM25 score: ~0.45 (medium)

# Low relevance: keyword appears in very long conversation with many other words
conversation3 = "... (10,000 words about various topics) ... python ..."
query = ["python"]
# BM25 score: ~0.15 (low)
```

**Rationale**: BM25 is empirically superior to classic TF-IDF for short documents. Configurable parameters (k1, b) allow tuning. Normalization to 0-1 range makes scores interpretable.

**New Requirements**:
- **FR-317**: Library MUST use BM25 algorithm for keyword relevance scoring (not classic TF-IDF)
- **FR-318**: BM25 parameters MUST be: k1=1.5 (term saturation), b=0.75 (length normalization)
- **FR-319**: BM25 scores MUST be normalized to 0.0-1.0 range using: score_normalized = score_raw / (score_raw + 1)
- **FR-320**: Library documentation MUST explain BM25 formula, parameters, and score interpretation
- **FR-321**: SearchResult.score field MUST contain normalized BM25 score (0.0-1.0)

---

### CHK039: Keyword Frequency and Position Clarified

**Gap**: Is "keyword frequency and position" clarified (within message, conversation, or entire export)?

**Decision**:
**Keyword scoring operates at conversation level**. Frequency and position calculated across all messages in a conversation.

**Scoring Scope**:

```
Corpus (entire export file)
└── Conversation 1
    ├── Message 1: "python is great"
    ├── Message 2: "I love python"
    └── Message 3: "python python python"
└── Conversation 2
    └── ...

BM25 scoring:
- Document = Single conversation (all messages concatenated)
- Corpus = All conversations in export file
- Term frequency = Count across all messages in conversation
- IDF = Calculated across all conversations
```

**Position Weighting** (NOT implemented in v1.0):
- v1.0: Position does NOT affect score (only frequency matters)
- Future (v2.0+): MAY add position weighting (title match > early message > late message)

**Frequency Calculation**:

```python
def calculate_term_frequency(keyword: str, conversation: Conversation) -> int:
    """Count keyword occurrences across all messages in conversation."""
    total_count = 0
    for message in conversation.messages:
        # Case-insensitive matching
        total_count += message.content.lower().count(keyword.lower())
    return total_count
```

**Examples**:

```python
# Conversation with keyword in multiple messages
conv = Conversation(
    id="conv-1",
    title="Python Discussion",
    messages=[
        Message(content="I love python"),          # 1 occurrence
        Message(content="Python is great"),        # 1 occurrence
        Message(content="python python python"),   # 3 occurrences
    ]
)

term_frequency("python", conv)  # Returns: 5 (total across all messages)
```

**matched_message_ids Field**:

SearchResult includes `matched_message_ids` listing which specific messages contain keywords:

```python
class SearchResult(BaseModel):
    conversation: Conversation
    score: float
    matched_message_ids: list[str]  # IDs of messages containing any query keyword
```

**Rationale**: Conversation-level scoring treats entire conversation as single document (natural for chat history). Term frequency across all messages rewards comprehensive discussion of topic. Future position weighting can be added non-breakingly.

**New Requirements**:
- **FR-322**: Keyword frequency MUST be calculated across all messages in a conversation (conversation = document)
- **FR-323**: BM25 scoring MUST treat concatenated conversation messages as single document
- **FR-324**: Keyword position within messages MUST NOT affect relevance score in v1.0 (only frequency matters)
- **FR-325**: SearchResult.matched_message_ids MUST list IDs of messages containing any query keyword
- **FR-326**: Keyword matching MUST be case-insensitive ("Python" matches "python")

---

### CHK044: Partial Match Requirements for Title Filtering

**Gap**: Are "partial match" requirements for title filtering specified (substring, prefix, fuzzy)?

**Decision**:
Use **case-insensitive substring matching** for title filtering. No fuzzy matching in v1.0.

**Title Matching Rules**:

| Query | Title | Match? | Rationale |
|-------|-------|--------|-----------|
| "algo" | "Algorithm Design" | ✅ Yes | Case-insensitive substring |
| "Algo" | "algorithm design" | ✅ Yes | Case-insensitive |
| "design" | "Algorithm Design" | ✅ Yes | Substring match |
| "alg" | "Algorithm Design" | ✅ Yes | Prefix match (also substring) |
| "rithm" | "Algorithm Design" | ✅ Yes | Infix match |
| "algo design" | "Algorithm Design" | ❌ No | Space breaks match (literal) |
| "algor" | "Algorithm Design" | ✅ Yes | Partial word match |
| "algoritm" | "Algorithm Design" | ❌ No | No fuzzy matching (typo) |

**Implementation**:

```python
def title_matches(title_filter: str, conversation_title: str) -> bool:
    """Check if title filter matches conversation title (case-insensitive substring).

    Args:
        title_filter: User-provided title filter (e.g., "algo")
        conversation_title: Conversation title from export (e.g., "Algorithm Design")

    Returns:
        True if title_filter is substring of conversation_title (case-insensitive)
    """
    return title_filter.lower() in conversation_title.lower()
```

**CLI Examples**:

```bash
# Exact substring match
echomine search export.json --title "Algorithm"

# Case-insensitive match
echomine search export.json --title "python"  # Matches "Python Tips", "PYTHON", etc.

# Partial word match
echomine search export.json --title "algo"  # Matches "Algorithm Design", "Algorithms"

# Multiple words require literal match (no fuzzy)
echomine search export.json --title "algo design"  # Must contain exact phrase
```

**Future Enhancements** (v2.0+, not in v1.0):
- Fuzzy matching with edit distance (e.g., "algoritm" → "algorithm")
- Regex support (e.g., `--title-regex "algo.*design"`)
- Word boundary matching (e.g., `--title-words "algo"` only matches word boundaries)

**Rationale**: Substring matching is simple, predictable, fast. Case-insensitive for user convenience. No fuzzy matching avoids false positives. Literal spaces require exact phrase match.

**New Requirements**:
- **FR-327**: Title filtering MUST use case-insensitive substring matching
- **FR-328**: Title filter "algo" MUST match titles: "Algorithm", "Algorithms", "algorithm design"
- **FR-329**: Title filtering MUST NOT use fuzzy matching or edit distance in v1.0
- **FR-330**: Title filter with spaces MUST match literal substring (e.g., "algo design" requires exact phrase)
- **FR-331**: Library documentation MUST include title filtering examples showing substring matching behavior

---

### CHK136: Interaction Between --limit and Relevance Ranking

**Gap**: Is the interaction between --limit and relevance ranking specified (top N by score, or first N encountered)?

**Decision**:
**Top N by score** (after ranking). Limit applied AFTER sorting by relevance.

**Execution Order**:

```
1. Stream & filter conversations (keywords, title, date range)
2. Score matching conversations (BM25)
3. Sort by score descending (highest relevance first)
4. Apply limit (take top N)
5. Return results
```

**Implementation**:

```python
def search(
    file_path: Path,
    query: SearchQuery
) -> Iterator[SearchResult]:
    """Search with limit applied AFTER relevance ranking (per FR-332)."""

    # Step 1-2: Stream, filter, score
    matching_results = []
    for conv in stream_conversations(file_path):
        if matches_filters(conv, query):
            score = calculate_bm25_score(conv, query.keywords)
            matching_results.append(SearchResult(
                conversation=conv,
                score=score,
                matched_message_ids=get_matched_message_ids(conv, query.keywords)
            ))

    # Step 3: Sort by relevance (highest first)
    matching_results.sort(key=lambda r: r.score, reverse=True)

    # Step 4: Apply limit (top N)
    limit = query.limit or len(matching_results)
    top_results = matching_results[:limit]

    # Step 5: Yield results
    for result in top_results:
        yield result
```

**Examples**:

```python
# Scenario 1: 100 conversations match query, limit=5
# Returns: Top 5 highest-scored conversations (not first 5 encountered)

query = SearchQuery(keywords=["python"], limit=5)
results = list(search(export_file, query))

# Results are sorted by score descending:
# results[0].score = 0.95 (highest)
# results[1].score = 0.87
# results[2].score = 0.82
# results[3].score = 0.76
# results[4].score = 0.71 (5th highest, not 5th encountered)


# Scenario 2: No limit specified
query = SearchQuery(keywords=["algorithm"])  # limit=None
results = list(search(export_file, query))

# Returns: ALL matching conversations, sorted by score descending
```

**Memory Impact**:
- With keywords: Must buffer matching conversations for sorting (O(matching_results))
- Without keywords: Can stream directly (O(1)) but still applies limit

**CLI Behavior**:

```bash
# Get top 5 most relevant results
echomine search export.json --keywords "python" --limit 5

# Default limit (show all results, sorted by relevance)
echomine search export.json --keywords "algorithm"
```

**Rationale**: Users expect --limit to return "best N results", not "first N encountered". Ranking is useless if limit returns arbitrary subset. Memory usage acceptable (only matching results buffered, not entire file).

**New Requirements**:
- **FR-332**: Search limit MUST be applied AFTER relevance ranking (return top N by score, not first N encountered)
- **FR-333**: Search results MUST be sorted by relevance score descending before applying limit
- **FR-334**: Search with limit=5 MUST return the 5 highest-scored conversations (even if 1000+ match)
- **FR-335**: Search without limit MUST return ALL matching conversations sorted by relevance descending
- **FR-336**: Library documentation MUST clarify that limit returns "top N most relevant" not "first N found"

---

## 3. cognivault Integration (4 items)

### CHK071: Complete cognivault Integration Flow

**Gap**: Are requirements complete for the cognivault integration flow (adapter creation → streaming → knowledge graph ingestion)?

**Decision**:
Define **end-to-end integration workflow** with error handling, progress tracking, and data transformation.

**cognivault Integration Workflow**:

```python
from echomine import OpenAIAdapter, EchomineError
from pathlib import Path
import structlog

logger = structlog.get_logger()

def ingest_chat_export(export_file: Path) -> dict:
    """
    Complete cognivault integration flow (per FR-337).

    Returns:
        dict: Ingestion summary with counts and errors
    """
    # Step 1: Create adapter
    adapter = OpenAIAdapter()

    # Step 2: Track ingestion progress
    ingested_count = 0
    skipped_count = 0
    skipped_entries = []

    def track_skip(conversation_id: str, reason: str):
        """Track skipped entries for reporting."""
        nonlocal skipped_count
        skipped_count += 1
        skipped_entries.append({"id": conversation_id, "reason": reason})
        logger.warning("conversation_skipped", conversation_id=conversation_id, reason=reason)

    def track_progress(count: int):
        """Log progress every 100 items."""
        logger.info("ingestion_progress", conversations_processed=count)

    # Step 3: Stream and ingest conversations
    try:
        for conversation in adapter.stream_conversations(
            export_file,
            progress_callback=track_progress,
            on_skip=track_skip
        ):
            # Step 4: Transform to cognivault format
            cognivault_data = transform_conversation(conversation)

            # Step 5: Ingest into knowledge graph
            cognivault.knowledge_graph.add_conversation(cognivault_data)

            ingested_count += 1

    except EchomineError as e:
        logger.error("ingestion_failed", error=str(e), file=str(export_file))
        raise

    except (FileNotFoundError, PermissionError) as e:
        logger.error("file_access_failed", error=str(e), file=str(export_file))
        raise

    # Step 6: Return summary
    return {
        "ingested": ingested_count,
        "skipped": skipped_count,
        "skipped_entries": skipped_entries,
        "export_file": str(export_file)
    }


def transform_conversation(conversation: Conversation) -> dict:
    """Transform echomine Conversation to cognivault format (per FR-340)."""
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,  # Already normalized by adapter
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "parent_id": msg.parent_id,
            }
            for msg in conversation.messages
        ],
        "threads": [
            [msg.id for msg in thread]
            for thread in conversation.get_all_threads()
        ],
        "metadata": conversation.metadata,  # Provider-specific fields
    }
```

**Integration Checkpoints**:

1. ✅ **Adapter Creation**: Stateless, no configuration needed
2. ✅ **Streaming**: Memory-efficient iteration over large files
3. ✅ **Progress Tracking**: Callbacks for UI updates
4. ✅ **Skip Handling**: Track malformed entries without failing
5. ✅ **Error Handling**: Catch EchomineError, filesystem errors
6. ✅ **Data Transformation**: Convert to cognivault schema
7. ✅ **Ingestion**: Add to knowledge graph
8. ✅ **Summary Reporting**: Return counts and errors

**Rationale**: Complete end-to-end workflow with all edge cases handled. Progress tracking for long operations. Error handling for robustness. Data transformation layer for schema flexibility.

**New Requirements**:
- **FR-337**: cognivault integration MUST follow workflow: adapter creation → streaming → transformation → ingestion → summary
- **FR-338**: cognivault MUST use progress_callback to track ingestion progress (log every 100 conversations)
- **FR-339**: cognivault MUST use on_skip callback to track skipped entries and include in summary report
- **FR-340**: cognivault MUST transform Conversation objects to cognivault schema before ingestion
- **FR-341**: cognivault integration MUST return summary with: ingested_count, skipped_count, skipped_entries list

---

### CHK155: cognivault Ingestion Rate Limiting

**Gap**: Are requirements defined for cognivault ingestion rate limiting (can library signal backpressure)?

**Decision**:
**Library does NOT implement rate limiting**. cognivault controls pace via pull-based iteration.

**Backpressure Mechanism**:

The library uses **pull-based generators** (not push-based callbacks). This gives cognivault **natural flow control**:

```python
# cognivault controls ingestion rate
adapter = OpenAIAdapter()

for conversation in adapter.stream_conversations(export_file):
    # cognivault can slow down here (generator pauses)
    if cognivault.queue_full():
        time.sleep(0.1)  # Wait before requesting next conversation

    # cognivault can add rate limiting
    rate_limiter.wait_if_needed()

    # cognivault ingests when ready
    cognivault.ingest(conversation)
    # Only after ingest completes does generator resume and yield next item
```

**No Explicit Rate Limiting**:
- Library does NOT have rate limit configuration (FR-134: no backpressure mechanisms)
- Library does NOT throttle/delay yielding (generator yields immediately when requested)
- Library does NOT buffer items (memory-efficient streaming)

**cognivault Rate Limiting Patterns**:

```python
# Pattern 1: Simple delay between conversations
for conv in adapter.stream_conversations(export_file):
    cognivault.ingest(conv)
    time.sleep(0.01)  # 10ms delay = max 100 conversations/sec

# Pattern 2: Token bucket rate limiter
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=1)  # 100 conversations per second
def ingest_with_rate_limit(conversation):
    cognivault.ingest(conversation)

for conv in adapter.stream_conversations(export_file):
    ingest_with_rate_limit(conv)

# Pattern 3: Adaptive rate limiting based on queue depth
for conv in adapter.stream_conversations(export_file):
    while cognivault.queue_depth() > 1000:
        time.sleep(0.1)  # Wait until queue drains
    cognivault.ingest(conv)
```

**Rationale**: Pull-based iteration gives consumer full control. Library stays simple (no rate limiting complexity). cognivault can implement any rate limiting strategy without library changes.

**New Requirements**:
- **FR-342**: Library MUST NOT implement rate limiting or throttling (consumers control pace via pull-based iteration)
- **FR-343**: Library generators MUST yield next item immediately when consumer requests it (no delays)
- **FR-344**: cognivault MAY implement rate limiting by adding delays between iterations
- **FR-345**: Library documentation MUST include rate limiting examples showing consumer-side patterns

---

### CHK156: cognivault Data Transformation

**Gap**: Are requirements specified for cognivault data transformation (which Conversation fields map to knowledge graph)?

**Decision**:
Define **explicit field mapping** from echomine Conversation to cognivault knowledge graph schema.

**Field Mapping Specification**:

| echomine Field | cognivault Field | Transformation | Notes |
|----------------|------------------|----------------|-------|
| `conversation.id` | `conversation_id` | Direct copy | UUID string |
| `conversation.title` | `title` | Direct copy | String |
| `conversation.created_at` | `created_at` | `.isoformat()` | ISO 8601 string |
| `conversation.updated_at` | `updated_at` | `.isoformat()` | ISO 8601 string |
| `conversation.messages` | `messages` | Transform each | List of message dicts |
| `message.id` | `message_id` | Direct copy | UUID string |
| `message.role` | `role` | Direct copy | "user" \| "assistant" \| "system" |
| `message.content` | `content` | Direct copy | String |
| `message.timestamp` | `timestamp` | `.isoformat()` | ISO 8601 string |
| `message.parent_id` | `parent_id` | Direct copy | UUID string \| null |
| `message.metadata` | `message_metadata` | Direct copy | Dict (provider-specific) |
| `conversation.metadata` | `conversation_metadata` | Direct copy | Dict (provider-specific) |
| `conversation.get_all_threads()` | `threads` | Extract thread paths | List of message ID lists |

**Transformation Function**:

```python
def transform_to_cognivault(conversation: Conversation) -> dict:
    """Transform echomine Conversation to cognivault schema (per FR-346)."""
    return {
        # Required fields
        "conversation_id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),

        # Messages array
        "messages": [
            {
                "message_id": msg.id,
                "role": msg.role,  # Already normalized
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "parent_id": msg.parent_id,
                "message_metadata": msg.metadata,
            }
            for msg in conversation.messages
        ],

        # Thread structure
        "threads": [
            [msg.id for msg in thread]
            for thread in conversation.get_all_threads()
        ],

        # Provider-specific metadata
        "conversation_metadata": conversation.metadata,

        # Derived fields
        "message_count": len(conversation.messages),
        "thread_count": len(conversation.get_all_threads()),
        "provider": "openai",  # Or determined from adapter type
    }
```

**Data Type Conversions**:
- **datetime → ISO 8601 string**: For JSON serialization and database storage
- **Pydantic models → dicts**: Using `.model_dump()` or manual construction
- **Tree structure → thread paths**: Using `.get_all_threads()` helper

**Rationale**: Explicit mapping prevents ambiguity. ISO 8601 strings for timestamps (universal format). Thread paths extracted for graph navigation. Provider metadata preserved for debugging.

**New Requirements**:
- **FR-346**: cognivault transformation MUST convert datetime fields to ISO 8601 strings using `.isoformat()`
- **FR-347**: cognivault transformation MUST include all required fields: conversation_id, title, created_at, updated_at, messages
- **FR-348**: cognivault transformation MUST include thread structure using `conversation.get_all_threads()`
- **FR-349**: cognivault transformation MUST preserve provider-specific metadata in separate fields
- **FR-350**: Library documentation MUST include complete transformation function example

---

### CHK157: cognivault Streaming Patterns

**Gap**: Are requirements defined for cognivault streaming patterns (batch vs one-at-a-time)?

**Decision**:
Support **both one-at-a-time and batched ingestion** patterns. Library provides flexible iterator.

**Pattern 1: One-at-a-Time Ingestion** (Simple, memory-efficient):

```python
def ingest_one_at_a_time(export_file: Path):
    """Ingest conversations individually (per FR-351)."""
    adapter = OpenAIAdapter()

    for conversation in adapter.stream_conversations(export_file):
        # Transform
        data = transform_to_cognivault(conversation)

        # Ingest immediately
        cognivault.knowledge_graph.add_conversation(data)

        # Commit after each (durable but slower)
        cognivault.commit()
```

**Pattern 2: Batched Ingestion** (Faster, trades memory for throughput):

```python
def ingest_in_batches(export_file: Path, batch_size: int = 100):
    """Ingest conversations in batches (per FR-352)."""
    adapter = OpenAIAdapter()
    batch = []

    for conversation in adapter.stream_conversations(export_file):
        # Transform
        data = transform_to_cognivault(conversation)

        # Add to batch
        batch.append(data)

        # Flush batch when full
        if len(batch) >= batch_size:
            cognivault.knowledge_graph.add_conversations_batch(batch)
            cognivault.commit()
            batch = []

    # Flush remaining items
    if batch:
        cognivault.knowledge_graph.add_conversations_batch(batch)
        cognivault.commit()
```

**Pattern 3: Async/Concurrent Ingestion** (Advanced, maximum throughput):

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def ingest_concurrent(export_file: Path, max_workers: int = 4):
    """Ingest conversations concurrently (per FR-353)."""
    adapter = OpenAIAdapter()

    async def ingest_one(conversation):
        data = transform_to_cognivault(conversation)
        await cognivault.async_add_conversation(data)

    # Create tasks
    tasks = []
    for conversation in adapter.stream_conversations(export_file):
        task = asyncio.create_task(ingest_one(conversation))
        tasks.append(task)

        # Limit concurrent tasks
        if len(tasks) >= max_workers:
            await asyncio.gather(*tasks)
            tasks = []

    # Wait for remaining
    if tasks:
        await asyncio.gather(*tasks)
```

**Performance Characteristics**:

| Pattern | Throughput | Memory | Latency | Use Case |
|---------|-----------|--------|---------|----------|
| One-at-a-time | Low | O(1) | High (per-item commit) | Small exports, real-time |
| Batched | High | O(batch_size) | Medium | Large exports, offline |
| Concurrent | Highest | O(max_workers) | Lowest | Bulk ingestion |

**Rationale**: Flexible patterns for different use cases. One-at-a-time for simplicity. Batched for performance. Concurrent for maximum throughput. Library doesn't dictate strategy.

**New Requirements**:
- **FR-351**: cognivault MAY use one-at-a-time ingestion pattern for simplicity and low memory usage
- **FR-352**: cognivault MAY use batched ingestion pattern for higher throughput (recommended batch size: 100-1000)
- **FR-353**: cognivault MAY use concurrent ingestion with multiple threads/tasks for maximum throughput
- **FR-354**: Library documentation MUST include examples of all three ingestion patterns
- **FR-355**: Library iterators MUST be safe for concurrent consumption by multiple threads (each thread gets own iterator)

---

## 4. Core Workflow Coverage (5 items)

### CHK072: Search-Then-Export Workflow

**Gap**: Are requirements specified for the search-then-export workflow (find by keyword, export by ID)?

**Decision**:
Define **two-step workflow** with search returning IDs, then export by ID.

**Workflow Implementation**:

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

def search_then_export_workflow(
    export_file: Path,
    keywords: list[str],
    output_dir: Path
):
    """
    Two-step workflow: search by keyword, then export matches (per FR-356).

    Args:
        export_file: Source ChatGPT export
        keywords: Search keywords
        output_dir: Directory to write exported conversations

    Returns:
        list[Path]: Paths to exported markdown files
    """
    adapter = OpenAIAdapter()

    # Step 1: Search by keywords
    query = SearchQuery(keywords=keywords, limit=10)
    search_results = list(adapter.search(export_file, query))

    print(f"Found {len(search_results)} matching conversations")

    # Step 2: Export each match
    exported_files = []
    for result in search_results:
        conv_id = result.conversation.id
        title_slug = slugify(result.conversation.title)

        # Get full conversation by ID
        conversation = adapter.get_conversation_by_id(export_file, conv_id)

        if conversation:
            # Export to markdown
            output_file = output_dir / f"{title_slug}.md"
            export_to_markdown(conversation, output_file)
            exported_files.append(output_file)

    return exported_files
```

**CLI Workflow**:

```bash
# Step 1: Search and view results
echomine search export.json --keywords "python,algorithm" --json > results.json

# Step 2: Extract conversation IDs
cat results.json | jq -r '.results[].conversation_id' > conv_ids.txt

# Step 3: Export each conversation
while read conv_id; do
  echomine export export.json "$conv_id" --format markdown --output exports/
done < conv_ids.txt

# One-liner version
echomine search export.json --keywords "python" --json | \
  jq -r '.results[].conversation_id' | \
  xargs -I {} echomine export export.json {} --format markdown
```

**Optimized Library Pattern** (single pass):

```python
def search_and_export_optimized(
    export_file: Path,
    keywords: list[str],
    output_dir: Path
):
    """Optimized: export during search (single file pass) (per FR-357)."""
    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=keywords)

    exported_count = 0
    for result in adapter.search(export_file, query):
        # Export directly from search results (conversation already loaded)
        conversation = result.conversation
        title_slug = slugify(conversation.title)
        output_file = output_dir / f"{title_slug}.md"

        export_to_markdown(conversation, output_file)
        exported_count += 1

    return exported_count
```

**Rationale**: Two-step workflow mirrors user mental model (search → select → export). CLI composability via JSON output and jq. Optimized pattern for programmatic use (avoids re-parsing).

**New Requirements**:
- **FR-356**: Library MUST support search-then-export workflow: search() returns results with IDs, get_conversation_by_id() retrieves full conversation
- **FR-357**: SearchResult MUST include full Conversation object to enable single-pass export (no re-parsing needed)
- **FR-358**: CLI MUST support exporting conversation by ID: `echomine export FILE CONVERSATION_ID`
- **FR-359**: CLI search --json output MUST include conversation_id field for easy extraction and piping to export command
- **FR-360**: Library documentation MUST include complete search-then-export workflow examples (both two-step and optimized patterns)

---

### CHK073: Batch Processing Scenarios

**Gap**: Are requirements defined for batch processing scenarios (processing multiple export files)?

**Decision**:
Support **sequential and concurrent batch processing** of multiple export files.

**Sequential Batch Processing**:

```python
def process_multiple_exports_sequential(export_files: list[Path]):
    """Process multiple exports sequentially (per FR-361)."""
    adapter = OpenAIAdapter()  # Reuse same adapter instance
    results = []

    for export_file in export_files:
        try:
            file_results = {
                "file": str(export_file),
                "conversations": 0,
                "skipped": 0,
                "errors": []
            }

            skipped_count = 0

            def track_skip(conv_id: str, reason: str):
                nonlocal skipped_count
                skipped_count += 1

            # Process this export
            for conversation in adapter.stream_conversations(
                export_file,
                on_skip=track_skip
            ):
                cognivault.ingest(conversation)
                file_results["conversations"] += 1

            file_results["skipped"] = skipped_count
            results.append(file_results)

        except Exception as e:
            results.append({
                "file": str(export_file),
                "error": str(e)
            })

    return results
```

**Concurrent Batch Processing**:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_multiple_exports_concurrent(
    export_files: list[Path],
    max_workers: int = 4
):
    """Process multiple exports concurrently (per FR-362)."""

    def process_one_export(export_file: Path) -> dict:
        """Process single export in separate thread."""
        # Each thread needs its own adapter instance (per FR-099)
        adapter = OpenAIAdapter()

        conversations_count = 0
        skipped_count = 0

        def track_skip(conv_id: str, reason: str):
            nonlocal skipped_count
            skipped_count += 1

        try:
            for conversation in adapter.stream_conversations(
                export_file,
                on_skip=track_skip
            ):
                cognivault.ingest(conversation)
                conversations_count += 1

            return {
                "file": str(export_file),
                "conversations": conversations_count,
                "skipped": skipped_count,
                "status": "success"
            }

        except Exception as e:
            return {
                "file": str(export_file),
                "error": str(e),
                "status": "failed"
            }

    # Process concurrently
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_one_export, f): f
            for f in export_files
        }

        for future in as_completed(futures):
            export_file = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "file": str(export_file),
                    "error": str(e),
                    "status": "failed"
                })

    return results
```

**CLI Batch Processing**:

```bash
# Sequential processing
for file in exports/*.json; do
  echomine search "$file" --keywords "python" --json >> all-results.json
done

# Parallel processing (GNU parallel)
parallel echomine search {} --keywords "python" --json ::: exports/*.json > all-results.json

# Parallel with xargs
ls exports/*.json | xargs -P 4 -I {} echomine search {} --keywords "test" --json
```

**Rationale**: Sequential for simplicity and resource constraints. Concurrent for throughput on multi-core systems. Each file independently processable (no cross-file dependencies).

**New Requirements**:
- **FR-361**: Library MUST support sequential batch processing (same adapter instance for multiple files)
- **FR-362**: Library MUST support concurrent batch processing (separate adapter instances per thread, per FR-099)
- **FR-363**: Adapter instances MUST be reusable across different files (stateless design per FR-114)
- **FR-364**: CLI MUST be composable for batch processing via shell loops and parallel utilities
- **FR-365**: Library documentation MUST include batch processing examples (sequential and concurrent patterns)

---

### CHK074: Title-Based Search Fallback

**Gap**: Are requirements specified for title-based search fallback when keywords return zero results?

**Decision**:
**NO automatic fallback**. Library does NOT implement fallback logic. Users control fallback via explicit second query.

**Fallback Pattern** (user-controlled):

```python
def search_with_fallback(
    export_file: Path,
    keywords: list[str],
    title_filter: Optional[str] = None
):
    """User-controlled fallback: try keywords, then title (per FR-366)."""
    adapter = OpenAIAdapter()

    # Try keyword search first
    query = SearchQuery(keywords=keywords)
    results = list(adapter.search(export_file, query))

    if results:
        return results  # Success, return keyword results

    # No results from keywords, try title-based search
    if title_filter:
        print(f"No keyword results, trying title filter: {title_filter}")
        query = SearchQuery(title=title_filter)
        results = list(adapter.search(export_file, query))

    return results
```

**Why NO automatic fallback**:
1. **Explicit over implicit**: Users should control fallback logic
2. **Different semantics**: Keywords = content search, title = metadata search
3. **Performance**: Title fallback requires second file pass (expensive)
4. **Predictability**: Automatic fallback would surprise users

**CLI Pattern** (user-controlled):

```bash
#!/bin/bash
# User script with explicit fallback logic

# Try keyword search
results=$(echomine search export.json --keywords "python" --json)

# Check if results are empty
if [ $(echo "$results" | jq '.results | length') -eq 0 ]; then
  echo "No keyword results, trying title search..."
  results=$(echomine search export.json --title "Python" --json)
fi

echo "$results" | jq '.results[]'
```

**Alternative: Combined Query** (single pass):

```python
# Users can combine keywords AND title in single query
query = SearchQuery(
    keywords=["python"],
    title="Algorithm"  # Both must match
)

# This is AND logic, not fallback
# Returns conversations with "python" in content AND "Algorithm" in title
```

**Rationale**: Library stays simple (no magic fallback). Users have full control over fallback strategy. Fallback can be implemented in one line of user code. Performance transparent (user decides if second pass acceptable).

**New Requirements**:
- **FR-366**: Library MUST NOT implement automatic title fallback when keyword search returns zero results
- **FR-367**: Users MAY implement fallback logic by making sequential search calls with different query parameters
- **FR-368**: Library documentation MUST include fallback pattern example showing user-controlled retry
- **FR-369**: SearchQuery MUST support combined filters (keywords + title) with AND logic (not OR/fallback)

---

### CHK075: Pagination or Result Streaming for Large Result Sets

**Gap**: Are requirements defined for pagination or result streaming (what if 10K conversations match query)?

**Decision**:
Use **iterator-based streaming** (no pagination). Results yielded one at a time, consumer controls consumption.

**No Pagination** (streaming instead):

Pagination is BATCH-oriented (page 1, page 2, etc.). Streaming is ITEM-oriented (one at a time).

**Why streaming over pagination**:
1. **Memory efficient**: O(1) memory (consumer processes one at a time)
2. **Simpler API**: No page size, page number, total pages complexity
3. **More flexible**: Consumer can stop early (no wasted computation)
4. **Consistent**: Matches library architecture (stream_conversations also streaming)

**Streaming Implementation**:

```python
def search(
    file_path: Path,
    query: SearchQuery
) -> Iterator[SearchResult]:
    """
    Search returns iterator (streaming, not paginated) (per FR-370).

    Consumer controls consumption:
    - Process all: list(search(...))
    - Process first N: itertools.islice(search(...), N)
    - Process until condition: takewhile(lambda r: r.score > 0.5, search(...))
    """
    # Implementation yields one result at a time
    for result in matching_results:
        yield result  # Consumer controls when next item is requested
```

**Handling Large Result Sets**:

```python
# Scenario: 10K conversations match query

# Option 1: Limit results (recommended)
query = SearchQuery(keywords=["python"], limit=100)
results = list(adapter.search(export_file, query))  # Only top 100

# Option 2: Process lazily (iterator)
for result in adapter.search(export_file, query):
    # Process one at a time (memory-efficient)
    cognivault.ingest(result.conversation)
    # Only loads 1 conversation in memory at a time

# Option 3: Take first N (itertools)
import itertools
query = SearchQuery(keywords=["python"])  # No limit
first_10 = list(itertools.islice(adapter.search(export_file, query), 10))

# Option 4: Filter by score threshold
results_above_threshold = [
    r for r in adapter.search(export_file, query)
    if r.score > 0.7
]
```

**CLI Behavior** (streaming-friendly):

```bash
# Limit results (recommended for large result sets)
echomine search export.json --keywords "test" --limit 100

# Stream to file (handle large result sets)
echomine search export.json --keywords "algorithm" --json > results.json

# Pipe to head (take first 10)
echomine search export.json --keywords "python" --json | \
  jq '.results[]' | \
  head -10
```

**Memory Analysis**:

| Approach | Memory Usage | Performance |
|----------|--------------|-------------|
| Streaming with limit | O(limit) | Optimal |
| Streaming all results | O(matching_results) for ranking | Good |
| Pagination | O(page_size) | Complex API |

**Rationale**: Streaming is simpler and more flexible than pagination. Iterator-based API is Pythonic. Consumer controls consumption rate. Limit parameter provides bounded memory usage.

**New Requirements**:
- **FR-370**: Library search() MUST return iterator (not paginated results)
- **FR-371**: Library MUST NOT implement pagination API (no page_size, page_number parameters)
- **FR-372**: Consumers MUST use SearchQuery.limit to bound result set size (recommended for large result sets)
- **FR-373**: Consumers MAY use itertools.islice() to consume first N results from unlimited search
- **FR-374**: Library documentation MUST explain handling large result sets via limit, itertools, and lazy iteration

---

### CHK076: Partial Result Delivery

**Gap**: Are requirements specified for partial result delivery (showing first N results while still processing)?

**Decision**:
**Partial delivery NOT SUPPORTED** in v1.0 due to ranking requirement. All results must be scored before returning top N.

**Why NO partial delivery**:

Relevance ranking requires seeing ALL results before returning top N:

```
Step 1: Stream & score ALL matching conversations
Step 2: Sort by score
Step 3: Return top N

Cannot return partial results during Step 1 because:
- Don't know if early result is in top N until all scored
- Ranking requires global view of all matches
```

**Example**:

```python
# 1000 conversations match keyword "python"

# Conversation 1: score = 0.3
# Conversation 2: score = 0.5
# ...
# Conversation 999: score = 0.95  # Highest score!
# Conversation 1000: score = 0.2

# If we returned Conversation 1 immediately (partial delivery):
# - Wrong! It's not in top 10 (score too low)
# - Must wait until all 1000 scored to know top 10
```

**Workaround: Disable Ranking** (future enhancement, v2.0+):

```python
# Not implemented in v1.0
query = SearchQuery(
    keywords=["python"],
    order_by="chronological",  # No ranking
    disable_scoring=True  # Partial delivery possible
)

# With chronological order, can stream partial results:
for result in adapter.search(export_file, query):
    # Yield immediately (no scoring delay)
    yield result
```

**Progress During Search**:

While partial delivery is not supported, progress indicators ARE supported:

```python
def search_with_progress(export_file: Path, keywords: list[str]):
    """Show progress while scoring (no partial results yet) (per FR-375)."""

    def progress_callback(count: int):
        print(f"Scored {count} conversations...", file=sys.stderr)

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=keywords)

    # Progress updates during scoring (stderr)
    # Results returned after ranking (stdout)
    results = adapter.search(
        export_file,
        query,
        progress_callback=progress_callback
    )

    return list(results)  # Blocks until all scored, sorted
```

**Rationale**: Relevance ranking requires global view (can't return partial). Progress indicators provide feedback during scoring. Future enhancement could add chronological order for partial delivery.

**New Requirements**:
- **FR-375**: Library MUST NOT support partial result delivery in v1.0 (ranking requires scoring all matches before returning top N)
- **FR-376**: Library MAY provide progress_callback to indicate scoring progress while results are being computed
- **FR-377**: Future versions MAY add chronological ordering to enable partial result delivery (non-ranked search)
- **FR-378**: Library documentation MUST explain that ranking requires buffering all matching results before yielding any

---

## 5. Error Handling & Recovery (4 items)

### CHK081: Handling Conversations with Missing Required Fields

**Gap**: Are requirements defined for handling conversations with missing required fields (title, ID, created_at)?

**Decision**:
**Validate and skip** conversations with missing required fields. Log warning, invoke on_skip callback.

**Required Field Validation**:

```python
# Required fields (per FR-269)
REQUIRED_FIELDS = ["id", "title", "created_at", "updated_at", "messages"]

def validate_conversation(data: dict) -> Optional[ValidationError]:
    """Validate conversation has required fields (per FR-379)."""

    # Check missing fields
    missing_fields = [
        field for field in REQUIRED_FIELDS
        if field not in data or data[field] is None
    ]

    if missing_fields:
        return ValidationError(
            f"Missing required fields: {missing_fields}. "
            f"Conversation may be corrupted or from unsupported schema version."
        )

    # Check empty strings
    for field in ["id", "title"]:
        if isinstance(data.get(field), str) and not data[field].strip():
            return ValidationError(
                f"Field '{field}' cannot be empty string. "
                f"Check export integrity."
            )

    # Check empty message list
    if isinstance(data.get("messages"), list) and len(data["messages"]) == 0:
        return ValidationError(
            f"Conversation must have at least one message. "
            f"Empty conversations are invalid."
        )

    return None  # Valid
```

**Handling Strategy**:

```python
def stream_conversations(
    file_path: Path,
    *,
    on_skip: Optional[OnSkipCallback] = None
) -> Iterator[Conversation]:
    """Stream with required field validation (per FR-379)."""

    for idx, data in enumerate(parse_export(file_path)):
        # Validate required fields
        validation_error = validate_conversation(data)

        if validation_error:
            conv_id = data.get("id", f"line-{idx}")

            # Log warning
            logger.warning(
                "skipped_conversation_missing_fields",
                conversation_id=conv_id,
                line=idx,
                error=str(validation_error)
            )

            # Invoke callback
            if on_skip:
                on_skip(conv_id, str(validation_error))

            # Skip (don't raise exception)
            continue

        # Pydantic validation (will also catch missing fields)
        try:
            conversation = Conversation.model_validate(data)
            yield conversation
        except PydanticValidationError as e:
            # Handle Pydantic validation failures separately
            ...
```

**Examples**:

```python
# Missing 'id' field
{
  "title": "Test",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "messages": [...]
}
# → Skipped: "Missing required fields: ['id']"

# Empty 'title' field
{
  "id": "conv-123",
  "title": "",  # Empty string
  "created_at": "2024-01-15T10:00:00Z",
  ...
}
# → Skipped: "Field 'title' cannot be empty string"

# No messages
{
  "id": "conv-456",
  "title": "Test",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "messages": []  # Empty array
}
# → Skipped: "Conversation must have at least one message"
```

**Rationale**: Missing required fields = data corruption or schema mismatch. Skipping (not raising) maximizes data recovery. Detailed error messages help users identify root cause.

**New Requirements**:
- **FR-379**: Library MUST skip conversations missing required fields (id, title, created_at, updated_at, messages)
- **FR-380**: Library MUST skip conversations with empty id or title (empty string after trimming whitespace)
- **FR-381**: Library MUST skip conversations with zero messages (empty messages array)
- **FR-382**: Skipped conversations MUST trigger on_skip callback with descriptive reason including which fields are missing
- **FR-383**: Skipped conversations MUST be logged at WARNING level with fields: conversation_id, line_number, missing_fields

---

### CHK082: Handling Messages with No Content

**Gap**: Are requirements specified for handling messages with no content (deleted messages, system metadata)?

**Decision**:
**Allow empty content** but require all other message fields. Empty content represents deleted/redacted messages.

**Message Content Validation**:

```python
class Message(BaseModel):
    """Message with optional empty content (per FR-384)."""

    id: str
    role: Literal["user", "assistant", "system"]
    timestamp: datetime
    parent_id: Optional[str] = None
    content: str  # CAN be empty string (deleted messages)
    metadata: dict[str, Any] = {}

    # No validator rejecting empty content
    # Empty string is valid (represents deleted/redacted message)
```

**Handling Examples**:

```python
# Valid: Empty content (deleted message)
msg = Message(
    id="msg-123",
    role="user",
    content="",  # Empty OK
    timestamp=datetime.now(timezone.utc)
)
# ✅ Accepted

# Valid: Whitespace-only content
msg = Message(
    id="msg-456",
    role="assistant",
    content="   ",  # Whitespace OK
    timestamp=datetime.now(timezone.utc)
)
# ✅ Accepted (not trimmed, preserved as-is)

# Invalid: Missing content field entirely
data = {
    "id": "msg-789",
    "role": "user",
    # "content": missing!
    "timestamp": "2024-01-15T10:00:00Z"
}
# ❌ ValidationError: Missing required field 'content'
```

**Use Cases for Empty Content**:

1. **Deleted messages**: User deleted message after sending
2. **Redacted content**: Privacy/security redaction
3. **System messages**: Metadata-only (e.g., "User joined channel")
4. **Placeholder nodes**: Tree structure maintenance

**Search Behavior**:

```python
# Empty content messages don't match keyword searches
msg = Message(id="msg-1", role="user", content="", ...)

matches_keyword(msg, "python")  # → False (no content to search)

# But conversation is still searchable if OTHER messages have content
conversation = Conversation(
    messages=[
        Message(content=""),  # Deleted
        Message(content="python is great"),  # Matches!
        Message(content=""),  # Deleted
    ]
)

search(conversation, ["python"])  # → Matches (second message has keyword)
```

**Rationale**: Empty content is semantically valid (deleted/redacted messages). Rejecting empty content would lose message tree structure. Missing content field (validation error) vs empty string (valid) distinction.

**New Requirements**:
- **FR-384**: Message content field MUST accept empty strings (represents deleted/redacted messages)
- **FR-385**: Library MUST NOT trim or normalize message content (preserve whitespace, empty strings as-is)
- **FR-386**: Missing content field MUST raise ValidationError (content field required, but can be empty string)
- **FR-387**: Empty content messages MUST NOT match keyword searches (no content to search)
- **FR-388**: Empty content messages MUST be included in conversation (preserved for tree structure integrity)

---

### CHK084: Retry Behavior Clarification

**Gap**: Are requirements specified for retry behavior in library API (FR-033 says no retries - is this absolute)?

**Decision**:
**Absolutely NO retries**. Library never retries any operation. This is a hard requirement.

**No Retry Scenarios**:

| Operation | Transient Error Example | Library Behavior | Rationale |
|-----------|------------------------|------------------|-----------|
| File access | Network drive timeout | Raise immediately, no retry | User must fix |
| Parse JSON | Temporary memory pressure | Raise immediately, no retry | Retrying won't help |
| Validation | Rate limit (hypothetical) | Raise immediately, no retry | Not applicable |
| Network (future) | API timeout | Raise immediately, no retry | Consumer controls retry |

**Implementation**:

```python
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    """Stream conversations with NO retry logic (per FR-389)."""

    # Open file - no retry on failure
    try:
        with open(file_path, 'r') as f:
            ...
    except OSError as e:
        # Raise immediately (no retry)
        raise  # Per FR-042: fail immediately

    # Parse JSON - no retry on failure
    try:
        data = json.loads(content)
    except JSONDecodeError as e:
        # Raise immediately (no retry)
        raise ParseError(f"Invalid JSON: {e}") from e

    # No retry logic anywhere in library
```

**Why NO Retries**:

1. **Simple & predictable**: No retry delay surprises
2. **Consumer control**: Library consumers implement retry strategy
3. **Fail fast**: Errors surface immediately (per FR-033, FR-042)
4. **Stateless**: Retries require state tracking (violates adapter design)
5. **Local files**: Retry doesn't help (file missing = need user intervention)

**Consumer Retry Pattern** (if needed):

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def ingest_with_retry(export_file: Path):
    """Consumer implements retry logic (per FR-390)."""
    adapter = OpenAIAdapter()

    for conversation in adapter.stream_conversations(export_file):
        cognivault.ingest(conversation)

# Library raises immediately, tenacity retries entire operation
```

**Rationale**: Library stays simple. Consumer knows best when/how to retry (backoff strategy, max attempts, which errors). Local file access rarely benefits from retry (file missing needs user fix).

**New Requirements**:
- **FR-389**: Library MUST NOT implement retry logic for any operation (file access, parsing, validation, network)
- **FR-390**: Library consumers MAY implement retry logic using decorator libraries (tenacity, backoff)
- **FR-391**: Library MUST fail immediately on all errors (no delays, no retry hints in exceptions)
- **FR-392**: Library documentation MUST state that NO retries are performed and consumers must implement retry if needed
- **FR-393**: All exceptions MUST be raised immediately (no internal retry attempts before raising)

---

### CHK085: Resource Cleanup After Exceptions

**Gap**: Are requirements defined for cleaning up resources after exceptions (file handles, memory, temp files)?

**Decision**:
**Guaranteed cleanup via context managers**. All resources cleaned up even on exceptions.

**Resource Cleanup Guarantees**:

```python
def stream_conversations(
    file_path: Path,
    *,
    on_skip: Optional[OnSkipCallback] = None
) -> Iterator[Conversation]:
    """
    Stream with guaranteed cleanup (per FR-394, FR-395).

    Resources cleaned up even if:
    - Exception raised during iteration
    - Consumer breaks early
    - Generator garbage collected
    """

    # Context manager guarantees file handle cleanup
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            for idx, line in enumerate(f):
                try:
                    data = json.loads(line)
                    conversation = Conversation.model_validate(data)
                    yield conversation

                except (json.JSONDecodeError, ValidationError) as e:
                    # Skip malformed entry (file still open)
                    if on_skip:
                        on_skip(data.get("id", f"line-{idx}"), str(e))
                    continue

        finally:
            # Cleanup runs even on exception or early break
            # (but context manager already handles file cleanup)
            pass

    # File handle closed here (context manager __exit__)
    # Even if exception raised or iteration breaks early
```

**Cleanup Scenarios**:

```python
# Scenario 1: Exception during iteration
adapter = OpenAIAdapter()
try:
    for conv in adapter.stream_conversations(export_file):
        process(conv)
        raise RuntimeError("Unexpected error!")
except RuntimeError:
    pass
# ✅ File handle closed (context manager)

# Scenario 2: Early break
for conv in adapter.stream_conversations(export_file):
    if conv.title == "Found it!":
        break  # Stop iteration early
# ✅ File handle closed (context manager)

# Scenario 3: Generator garbage collected
gen = adapter.stream_conversations(export_file)
next(gen)  # Get first item
del gen  # GC without exhausting
# ✅ File handle closed (context manager __exit__ on GC)
```

**No Temp Files**:

Library does NOT create temporary files (per FR-396):
- No temp file for parsing (streaming, no buffering)
- No temp file for search results (in-memory sorting)
- No temp file for exports (write directly to user-specified path)

**Memory Cleanup**:

Python GC handles memory automatically. Library follows best practices:
- No circular references (Pydantic models are simple)
- No caching (stateless adapters)
- Generators release memory after yielding (not held)

**Rationale**: Context managers are Python best practice for cleanup. Guaranteed cleanup even in edge cases (early break, exception, GC). No manual close() calls needed. No temp files (simpler, no cleanup needed).

**New Requirements**:
- **FR-394**: Library MUST use context managers (with statements) for all file I/O operations
- **FR-395**: File handles MUST be closed even when: exceptions raised, iteration breaks early, generators garbage collected
- **FR-396**: Library MUST NOT create temporary files (no temp file cleanup needed)
- **FR-397**: Library MUST use try/finally blocks to guarantee cleanup code execution
- **FR-398**: Library documentation MUST document cleanup guarantees (resources always released)

---

## 6. Consistency Checks (5 items)

### CHK052: Export Default Output Location Consistency

**Gap**: Do FR-018 (export to current directory) and library API requirements align?

**Decision**:
**CLI defaults to current directory**. **Library requires explicit path**. This is consistent and intentional.

**CLI Behavior** (FR-018):

```bash
# Default: export to current working directory
echomine export conversations.json conv-123 --format markdown
# Creates: ./conv-123-title.md (current directory)

# Explicit path: --output flag
echomine export conversations.json conv-123 --format markdown --output /path/to/output/
# Creates: /path/to/output/conv-123-title.md
```

**Library API Behavior**:

```python
# Library: explicit output_path required (no default)
def export_conversation(
    conversation: Conversation,
    output_path: Path,  # Required
    format: Literal["markdown", "json"] = "markdown"
) -> None:
    """Export conversation to file (per FR-399).

    Args:
        conversation: Conversation to export
        output_path: Full path to output file (required, no default)
        format: Export format

    Note: No default output path. Caller must specify explicitly.
    """
    with open(output_path, 'w') as f:
        if format == "markdown":
            f.write(conversation.to_markdown())
        else:
            f.write(conversation.model_dump_json())
```

**Why Different**:

| Aspect | CLI | Library | Rationale |
|--------|-----|---------|-----------|
| Default path | ✅ Current dir | ❌ Required param | CLI convenience vs library explicitness |
| Context | Shell session (current dir obvious) | Python code (current dir ambiguous) | Different execution contexts |
| User expectation | "Save here" (implicit) | "Save where?" (explicit) | UX conventions |

**Consistency**: Both behaviors are consistent with their contexts:
- CLI: Interactive tool, reasonable default (current directory)
- Library: Programmatic API, explicit better than implicit (Zen of Python)

**Rationale**: CLI convenience (reasonable default). Library explicitness (no surprises). Different UX expectations for CLI vs library.

**New Requirements**:
- **FR-399**: CLI MUST default to current working directory for export output (per FR-018)
- **FR-400**: CLI MUST support --output flag to specify custom export directory
- **FR-401**: Library export functions MUST require explicit output_path parameter (no default)
- **FR-402**: Library MUST NOT use current working directory as default (explicit over implicit)
- **FR-403**: Documentation MUST explain CLI vs library export path behavior differences

---

### CHK053: Date Filtering Consistency (CLI vs Library)

**Gap**: Are date filtering requirements consistent between CLI (ISO 8601 strings) and library (date objects vs strings)?

**Decision**:
**CLI accepts ISO 8601 strings**. **Library accepts datetime objects OR ISO 8601 strings**. Automatic parsing.

**CLI Interface**:

```bash
# CLI: ISO 8601 strings
echomine search export.json \
  --from 2024-01-01 \
  --to 2024-03-31 \
  --keywords "project"
```

**Library Interface** (flexible):

```python
from datetime import datetime, date

# Option 1: datetime objects (preferred)
query = SearchQuery(
    keywords=["project"],
    date_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
    date_to=datetime(2024, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
)

# Option 2: date objects (convenience)
query = SearchQuery(
    keywords=["project"],
    date_from=date(2024, 1, 1),
    date_to=date(2024, 3, 31)
)

# Option 3: ISO 8601 strings (automatic parsing)
query = SearchQuery(
    keywords=["project"],
    date_from="2024-01-01",
    date_to="2024-03-31"
)

# All three work! Pydantic handles conversion
```

**Pydantic Auto-Parsing**:

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Union

class SearchQuery(BaseModel):
    """Search query with flexible date parsing (per FR-404)."""

    date_from: Optional[Union[datetime, date, str]] = None
    date_to: Optional[Union[datetime, date, str]] = None

    @field_validator('date_from', 'date_to', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse string dates to datetime (per FR-405)."""
        if v is None:
            return None

        if isinstance(v, datetime):
            return v

        if isinstance(v, date):
            # Convert date to datetime (start of day UTC)
            return datetime.combine(v, datetime.min.time(), tzinfo=timezone.utc)

        if isinstance(v, str):
            # Parse ISO 8601 string
            try:
                return datetime.fromisoformat(v)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format: {v}. Expected ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                ) from e

        raise ValueError(f"Invalid date type: {type(v)}")
```

**Consistency Check**:
- ✅ CLI: ISO 8601 strings → Parsed to datetime
- ✅ Library: ISO 8601 strings, date, or datetime → All accepted
- ✅ Internal: All converted to datetime for comparison
- ✅ Behavior: Same date filtering logic regardless of input format

**Rationale**: CLI limited to strings (command-line interface). Library flexible (Pydantic auto-parsing). Both consistent internally (datetime comparison). User convenience (multiple input formats).

**New Requirements**:
- **FR-404**: Library SearchQuery MUST accept date_from/date_to as: datetime objects, date objects, OR ISO 8601 strings
- **FR-405**: Library MUST automatically parse ISO 8601 date strings to datetime objects (Pydantic validator)
- **FR-406**: CLI MUST parse --from/--to flags as ISO 8601 strings and convert to datetime for SearchQuery
- **FR-407**: Date filtering MUST use datetime comparison internally (consistent behavior across input formats)
- **FR-408**: Library documentation MUST show all three date input formats with examples

---

### CHK054: Limit Requirements Consistency

**Gap**: Are limit requirements consistent (CLI --limit flag vs SearchQuery.limit field)?

**Decision**:
**Perfectly consistent**. CLI --limit maps directly to SearchQuery.limit with same defaults and bounds.

**Consistency Specification**:

| Aspect | CLI | Library | Consistent? |
|--------|-----|---------|-------------|
| Parameter name | `--limit` | `SearchQuery.limit` | ✅ Yes (both "limit") |
| Default value | None (no limit) | None (no limit) | ✅ Yes |
| Data type | Integer | Optional[int] | ✅ Yes |
| Minimum value | 1 | 1 (ge=1 validator) | ✅ Yes |
| Maximum value | None (unbounded) | None (unbounded) | ✅ Yes |
| Behavior when None | Return all results | Return all results | ✅ Yes |
| Behavior when set | Return top N by score | Return top N by score | ✅ Yes |

**CLI Implementation**:

```python
# CLI argument parser
parser.add_argument(
    '--limit',
    type=int,
    default=None,
    help='Maximum results to return (default: no limit)'
)

# CLI → Library mapping
query = SearchQuery(
    keywords=args.keywords,
    limit=args.limit  # Direct mapping
)
```

**Library Implementation**:

```python
from pydantic import Field

class SearchQuery(BaseModel):
    """Search query with consistent limit semantics (per FR-409)."""

    limit: Optional[int] = Field(
        None,
        ge=1,  # Minimum 1 (if specified)
        description="Maximum results to return (None = no limit)"
    )
```

**Examples**:

```bash
# CLI: No limit (return all)
echomine search export.json --keywords "python"

# CLI: Limit to 10
echomine search export.json --keywords "python" --limit 10
```

```python
# Library: No limit (return all)
query = SearchQuery(keywords=["python"])  # limit=None

# Library: Limit to 10
query = SearchQuery(keywords=["python"], limit=10)
```

**Validation**:

```bash
# CLI: Invalid limit (< 1)
echomine search export.json --keywords "test" --limit 0
# Error: --limit must be >= 1
```

```python
# Library: Invalid limit (< 1)
query = SearchQuery(keywords=["test"], limit=0)
# ValidationError: limit must be >= 1
```

**Rationale**: Perfect 1:1 mapping between CLI and library. No surprises. Same validation rules. Same semantics (top N by score).

**New Requirements**:
- **FR-409**: CLI --limit flag MUST map directly to SearchQuery.limit field (no transformation)
- **FR-410**: Both CLI and library MUST default to None (no limit, return all results)
- **FR-411**: Both CLI and library MUST validate limit >= 1 (if specified)
- **FR-412**: Both CLI and library MUST interpret limit as "top N by relevance score" (not "first N encountered")
- **FR-413**: Documentation MUST show CLI and library limit usage with identical semantics

---

### CHK055: Error Handling Consistency (CLI vs Library)

**Gap**: Are error handling requirements consistent between CLI (exit codes) and library (exceptions)?

**Decision**:
**Consistent mapping**: CLI catches library exceptions and maps to exit codes.

**Exception → Exit Code Mapping**:

| Library Exception | CLI Exit Code | CLI Behavior |
|------------------|---------------|--------------|
| `FileNotFoundError` | 1 | Print error to stderr, exit 1 |
| `PermissionError` | 1 | Print error to stderr, exit 1 |
| `ParseError` | 1 | Print error to stderr, exit 1 |
| `ValidationError` | 1 | Print error to stderr, exit 1 |
| `SchemaVersionError` | 1 | Print error to stderr, exit 1 |
| Invalid CLI args | 2 | Print usage to stderr, exit 2 |
| `KeyboardInterrupt` | 130 | Print "Interrupted", exit 130 |
| Unexpected exception | 1 | Print error + stack trace, exit 1 |

**CLI Error Handler**:

```python
def cli_main():
    """CLI entry point with exception → exit code mapping (per FR-414)."""
    try:
        # Parse arguments
        args = parse_args()

        # Call library
        adapter = OpenAIAdapter()
        results = adapter.search(
            Path(args.file),
            SearchQuery(keywords=args.keywords)
        )

        # Output results
        for result in results:
            print(result.conversation.title)

        sys.exit(0)  # Success

    except (FileNotFoundError, PermissionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except (ParseError, ValidationError, SchemaVersionError, EchomineError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
```

**Consistency Check**:
- ✅ Library raises specific exceptions
- ✅ CLI catches and maps to exit codes
- ✅ Error messages written to stderr (both CLI and library log to stderr)
- ✅ No retry logic (both library and CLI fail fast)

**Rationale**: Clean separation of concerns. Library focuses on exceptions (Pythonic). CLI focuses on exit codes (Unix convention). Mapping layer in CLI entry point.

**New Requirements**:
- **FR-414**: CLI MUST catch all library exceptions and map to appropriate exit codes (FileNotFoundError → 1, etc.)
- **FR-415**: CLI MUST write all error messages to stderr (never stdout)
- **FR-416**: CLI MUST preserve exception messages from library (don't obscure root cause)
- **FR-417**: CLI MUST handle KeyboardInterrupt separately (exit 130, not 1)
- **FR-418**: Library exceptions and CLI exit codes MUST be documented together (mapping table)

---

### CHK056: Keyword Search Consistency

**Gap**: Are keyword search requirements consistent between FR-006 (all messages) and FR-017 (full-text search)?

**Decision**:
**Perfectly consistent**. FR-006 and FR-017 describe the same feature (full-text keyword search across all messages).

**Feature Analysis**:

| Requirement | Description | Scope |
|-------------|-------------|-------|
| **FR-006** | "System MUST support keyword search across all conversation messages, not just titles" | Library feature |
| **FR-017** | "System MUST provide a `search` command that accepts file path and supports --keywords (full-text search across messages)" | CLI feature |

**Consistency**:
- ✅ Both search "all conversation messages" (not just titles)
- ✅ Both use "keywords" terminology
- ✅ Both are "full-text search" (content, not metadata)
- ✅ FR-017 is CLI wrapper around FR-006 (same underlying implementation)

**Implementation**:

```python
# FR-006: Library implementation
def search(
    file_path: Path,
    query: SearchQuery
) -> Iterator[SearchResult]:
    """Search across all conversation messages (per FR-006)."""

    for conversation in stream_conversations(file_path):
        # Search ALL messages (not just title)
        text = " ".join(msg.content for msg in conversation.messages)

        if any(keyword.lower() in text.lower() for keyword in query.keywords):
            score = calculate_bm25_score(conversation, query.keywords)
            yield SearchResult(conversation=conversation, score=score)
```

```bash
# FR-017: CLI implementation (calls FR-006)
echomine search export.json --keywords "algorithm,python"
# Internally: adapter.search(file_path, SearchQuery(keywords=["algorithm", "python"]))
```

**No Conflict**: FR-006 and FR-017 are complementary (library + CLI), not conflicting.

**Rationale**: FR-006 defines library behavior. FR-017 defines CLI interface. Both describe same underlying feature. No inconsistency.

**New Requirements**:
- **FR-419**: Keyword search (FR-006, FR-017) MUST search across ALL messages in conversation (not just title or first message)
- **FR-420**: CLI --keywords flag MUST map to SearchQuery.keywords field (consistent naming)
- **FR-421**: Both library and CLI MUST use same search algorithm (BM25 relevance scoring)
- **FR-422**: Documentation MUST clarify FR-006 (library) and FR-017 (CLI) describe same feature

---

## 7. Documentation Alignment (3 items)

### CHK060: quickstart.md Examples Consistent with Spec

**Gap**: Are quickstart.md examples consistent with spec requirements (API signatures, method names, return types)?

**Decision**:
**Audit and update quickstart.md** to match current spec. Examples must use exact signatures from P1/P2 resolutions.

**Consistency Checklist**:

| Spec Element | quickstart.md MUST Show | Current Status |
|--------------|------------------------|----------------|
| Method signatures | Keyword-only args (`*`) | ✅ Update needed |
| Callback types | ProgressCallback, OnSkipCallback | ✅ Update needed |
| Pydantic config | ConfigDict(frozen=True, strict=True, extra="forbid") | ✅ Update needed |
| Exception handling | Catch EchomineError, not Exception | ✅ Already correct |
| Tree navigation | get_all_threads(), get_thread() | ❌ Missing |
| Role normalization | Literal["user", "assistant", "system"] | ❌ Missing |
| Timestamp normalization | Timezone-aware UTC | ❌ Missing |

**Required Updates**:

1. **Method Signatures**: Update to use keyword-only args
   ```python
   # ❌ OLD
   adapter.stream_conversations(file_path, progress, on_skip)

   # ✅ NEW
   adapter.stream_conversations(file_path, progress_callback=progress, on_skip=on_skip)
   ```

2. **Tree Navigation**: Add examples
   ```python
   # NEW: Tree navigation examples
   threads = conversation.get_all_threads()
   for thread in threads:
       print([msg.content for msg in thread])
   ```

3. **Pydantic Config**: Show ConfigDict
   ```python
   # NEW: Pydantic configuration example
   class Message(BaseModel):
       model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
       ...
   ```

**Rationale**: quickstart.md is first-impression documentation. Must match latest spec exactly. Outdated examples cause confusion and integration errors.

**New Requirements**:
- **FR-423**: quickstart.md examples MUST use keyword-only arguments for all protocol methods
- **FR-424**: quickstart.md MUST include tree navigation examples (get_all_threads, get_thread)
- **FR-425**: quickstart.md MUST show Pydantic ConfigDict configuration
- **FR-426**: quickstart.md MUST show role normalization and timestamp handling
- **FR-427**: quickstart.md MUST be reviewed for consistency after every spec update

---

### CHK061: CLI Spec Examples Consistent

**Gap**: Are CLI spec examples consistent with FR-017/FR-018 command definitions?

**Decision**:
**Audit CLI examples** in spec.md to match CLI contract from P2 resolutions.

**Consistency Checklist**:

| CLI Feature | Spec Example MUST Show | Current Status |
|-------------|----------------------|----------------|
| stdout/stderr | Results to stdout, progress to stderr | ❌ Needs clarification |
| Exit codes | Exit 0 (success), 1 (error), 2 (usage), 130 (interrupt) | ❌ Not documented |
| --json schema | Complete JSON schema with results + metadata | ❌ Incomplete |
| Pipeline examples | jq, grep, xargs composition | ❌ Missing |
| --limit flag | Maps to SearchQuery.limit | ✅ Correct |
| --from/--to dates | ISO 8601 format | ✅ Correct |

**Required Updates**:

1. **stdout/stderr Examples**:
   ```bash
   # NEW: Show stderr redirection
   echomine search export.json --keywords "test" 2>/dev/null
   ```

2. **Exit Code Documentation**:
   ```markdown
   ## Exit Codes
   - 0: Success
   - 1: Operational error (file not found, parse error, etc.)
   - 2: Usage error (invalid arguments)
   - 130: Interrupted (Ctrl+C)
   ```

3. **Pipeline Examples**:
   ```bash
   # NEW: Pipeline composition examples
   echomine search export.json --keywords "python" --json | \
     jq '.results[] | select(.score > 0.8)' | \
     ...
   ```

**Rationale**: Spec is authoritative reference. CLI examples must demonstrate full capabilities (stdout/stderr, exit codes, pipelines). Users copy-paste examples.

**New Requirements**:
- **FR-428**: spec.md CLI examples MUST demonstrate stdout/stderr separation
- **FR-429**: spec.md MUST document all CLI exit codes (0, 1, 2, 130) with examples
- **FR-430**: spec.md MUST include at least 3 pipeline composition examples
- **FR-431**: spec.md CLI examples MUST use complete --json schema (results + metadata)
- **FR-432**: spec.md MUST show --help and --version output examples

---

### CHK062: Data Model Documentation Consistency

**Gap**: Are data model documentation requirements consistent with Pydantic model specifications?

**Decision**:
**data-model.md already updated** in P1 resolutions. Verify consistency.

**Consistency Verification**:

| Pydantic Spec | data-model.md | Status |
|---------------|---------------|--------|
| ConfigDict(frozen=True, ...) | ✅ Documented | ✅ Consistent |
| Literal["user", "assistant", "system"] | ✅ Documented | ✅ Consistent |
| Timezone-aware validators | ✅ Documented | ✅ Consistent |
| Tree navigation methods | ✅ Documented | ✅ Consistent |
| metadata dict | ✅ Documented | ✅ Consistent |
| Field descriptions | ✅ Documented | ✅ Consistent |

**Already Consistent** (from P1 work):
- Message model: Complete ConfigDict, validators, role Literal
- Conversation model: Complete ConfigDict, validators, tree methods
- SearchResult model: Complete ConfigDict
- Tree structure examples: JSON serialization, visualization

**No Updates Needed**: data-model.md was comprehensively updated in P1 resolution (Step 3).

**Rationale**: data-model.md is single source of truth for Pydantic models. Must match implementation exactly. P1 updates already achieved consistency.

**New Requirements**:
- **FR-433**: data-model.md MUST document all Pydantic model_config settings (frozen, strict, extra)
- **FR-434**: data-model.md MUST document all field validators with examples
- **FR-435**: data-model.md MUST show complete field type specifications (Literal, Optional, etc.)
- **FR-436**: data-model.md MUST include JSON serialization examples for all models
- **FR-437**: data-model.md MUST be kept in sync with src/ Pydantic model implementations

---

## Summary: Priority 2 Gap Resolution

**Total Gaps Resolved**: 28
**New Functional Requirements**: FR-291 through FR-437 (147 requirements)

**Breakdown by Category**:
1. **CLI Interface Contract** (5 gaps): FR-291 to FR-316 (26 requirements)
2. **Search & Filtering Semantics** (4 gaps): FR-317 to FR-336 (20 requirements)
3. **cognivault Integration** (4 gaps): FR-337 to FR-355 (19 requirements)
4. **Core Workflow Coverage** (5 gaps): FR-356 to FR-378 (23 requirements)
5. **Error Handling & Recovery** (4 gaps): FR-379 to FR-398 (20 requirements)
6. **Consistency Checks** (5 gaps): FR-399 to FR-422 (24 requirements)
7. **Documentation Alignment** (3 gaps): FR-423 to FR-437 (15 requirements)

**Artifacts to Update**:
- ✅ spec.md (add FR-291 to FR-437)
- ✅ quickstart.md (update examples per CHK060)
- ✅ CLI implementation guide (new section for exit codes, pipelines)
- ✅ checklists/library-api.md (mark 28 P2 gaps as resolved)

---

## Next Steps

1. **Update spec.md** with FR-291 to FR-437
2. **Update quickstart.md** with corrected examples (keyword-only args, tree navigation)
3. **Update library-api.md checklist** marking 28 P2 gaps as resolved
4. **Add CLI composability section** to documentation (pipeline examples)
