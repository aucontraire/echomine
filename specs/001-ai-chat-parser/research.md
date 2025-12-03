# Phase 0: Research & Technology Validation

**Feature**: Echomine AI Chat Parser
**Date**: 2025-11-21
**Status**: ✅ Complete

## Research Topics

### 1. ijson Streaming Patterns for Nested JSON

**Decision**: Use `ijson.items()` with path-based extraction for OpenAI's nested conversation structure

**Rationale**:
- OpenAI export format has deeply nested JSON: `conversations[].mapping[message_id].message`
- ijson provides constant memory usage regardless of file size (critical for 1GB+ files)
- `items()` method yields Python objects incrementally without loading full file

**Implementation Pattern**:
```python
import ijson
from pathlib import Path
from typing import Iterator

def stream_conversations(file_path: Path) -> Iterator[dict]:
    """Stream conversations one at a time from export file."""
    with open(file_path, 'rb') as f:
        # Extract each conversation from the array
        for conversation in ijson.items(f, 'item'):
            yield conversation
```

**Alternatives Considered**:
- `json.load()`: Rejected - loads entire file into memory (violates FR-003, Principle VIII)
- `json.JSONDecoder().raw_decode()`: Rejected - still requires reading full file, complex error handling
- `orjson`: Rejected - faster but no streaming support, same memory issues as stdlib json

**Reference**: ijson documentation on path-based extraction patterns

---

### 2. TF-IDF Implementation for Keyword Ranking

**Decision**: Lightweight in-memory TF-IDF using Python Counter + math.log for relevance scoring

**Rationale**:
- TF-IDF is industry standard for text relevance (term frequency * inverse document frequency)
- Conversation-level scoring (not message-level) keeps implementation simple
- No external NLP library needed - Python stdlib sufficient for basic TF-IDF

**Implementation Pattern**:
```python
from collections import Counter
import math
from typing import List

def calculate_relevance(keywords: List[str], conversation_text: str, total_conversations: int, keyword_doc_counts: dict) -> float:
    """Calculate TF-IDF relevance score for conversation."""
    text_lower = conversation_text.lower()
    words = text_lower.split()
    word_counts = Counter(words)

    score = 0.0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        # Term Frequency: how often keyword appears in this conversation
        tf = word_counts[keyword_lower] / len(words) if words else 0

        # Inverse Document Frequency: log(total docs / docs containing keyword)
        idf = math.log(total_conversations / (keyword_doc_counts.get(keyword_lower, 1) + 1))

        score += tf * idf

    return score
```

**Alternatives Considered**:
- `scikit-learn TfidfVectorizer`: Rejected - heavyweight dependency for simple use case (violates Principle V: YAGNI)
- BM25 algorithm: Rejected - more complex, marginal improvement for conversation search (not web search)
- Simple keyword frequency: Rejected - doesn't account for common vs rare terms (poor ranking quality)

**Trade-off**: TF-IDF requires two passes (one to count docs per keyword, one to score). Acceptable because:
1. First pass can stream (constant memory)
2. Second pass only processes search results (subset of data)
3. Meets <30 second requirement for 1.6GB file (SC-001)

---

### 3. Pydantic v2 Frozen Models for Immutability

**Decision**: Use `model_config = {"frozen": True, "strict": True}` on all conversation data models

**Rationale**:
- Immutability prevents accidental mutation of parsed data (data integrity)
- Aligns with constitution Data Model Conventions (frozen=True required)
- `strict=True` enforces type coercion rules (e.g., no auto str->int conversion)

**Implementation Pattern**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    """Immutable message structure from conversation export."""
    model_config = {"frozen": True, "strict": True}

    id: str = Field(..., description="Unique message identifier")
    content: str = Field(..., description="Message text content")
    role: str = Field(..., description="Author role: user, assistant, system")
    timestamp: datetime = Field(..., description="Message creation time")
    parent_id: Optional[str] = Field(None, description="Parent message ID for threading")

class Conversation(BaseModel):
    """Immutable conversation structure."""
    model_config = {"frozen": True, "strict": True}

    id: str
    title: str
    created_at: datetime
    messages: List[Message]
```

**Pydantic v2 Features Leveraged**:
- `Field(..., description)`: Auto-generates JSON schema for external tools
- `frozen=True`: Raises error on mutation attempts (immutability enforcement)
- `strict=True`: Type validation without coercion (safer than v1 behavior)

**Alternatives Considered**:
- Python `dataclasses` with `frozen=True`: Rejected - no validation, no JSON schema generation
- `attrs` library: Rejected - less ecosystem support than Pydantic, no native JSON handling
- Mutable Pydantic models: Rejected - violates constitution requirement for immutability

---

### 4. structlog Best Practices for CLI Applications

**Decision**: Configure structlog with JSON processor for machine-readable logs, optional dev-friendly console renderer

**Rationale**:
- JSON logs enable log aggregation tools (CloudWatch, Splunk, ELK)
- Contextual fields (operation, file_name, conversation_id) propagate automatically
- Console renderer during development provides human-readable output

**Implementation Pattern**:
```python
import structlog
import sys

def configure_logging(json_logs: bool = True):
    """Configure structlog for CLI application."""
    processors = [
        structlog.contextvars.merge_contextvars,  # Add bound context
        structlog.processors.add_log_level,       # Add 'level' field
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 timestamp
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development mode: colorized console output
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),  # Logs to stderr
        cache_logger_on_first_use=True,
    )

# Usage in code
logger = structlog.get_logger()
logger.info("parsing_started", file_name="conversations.json", operation="search")
```

**Log Levels Mapping** (per FR-028 through FR-032):
- **INFO**: Operation start/completion (parsing started, search completed)
- **WARNING**: Recoverable issues (malformed JSON entries skipped)
- **ERROR**: Unrecoverable failures (file not found, permission denied)

**Alternatives Considered**:
- Python stdlib `logging`: Rejected - requires manual JSON formatting, no automatic context propagation
- `loguru`: Rejected - less flexible for structured logging patterns
- Custom JSON logger: Rejected - reinventing wheel, structlog is battle-tested

---

### 5. pytest-benchmark Memory Profiling Techniques

**Decision**: Use `pytest-benchmark` + `memory_profiler` decorator for performance contract validation

**Rationale**:
- pytest-benchmark provides statistical analysis (mean, stddev, outliers)
- memory_profiler measures peak memory usage (validates SC-005: <8GB for 10K conversations)
- Integrated with pytest (no separate tooling needed)

**Implementation Pattern**:
```python
import pytest
from memory_profiler import memory_usage

@pytest.mark.benchmark(group="search")
def test_search_performance_1gb_file(benchmark, sample_export_1gb):
    """Validate SC-001: Search 1.6GB file in <30 seconds."""
    def search_operation():
        adapter = OpenAIAdapter(sample_export_1gb)
        results = list(adapter.search(keywords=["algorithm"]))
        return results

    # Benchmark execution time
    result = benchmark(search_operation)

    # Assert performance contract
    assert benchmark.stats['mean'] < 30.0, "Search exceeded 30 second target"
    assert len(result) > 0, "Search should return results"

@pytest.mark.benchmark(group="memory")
def test_memory_usage_10k_conversations(sample_export_10k_conversations):
    """Validate SC-005: Process 10K conversations under 8GB RAM."""
    def process_all():
        adapter = OpenAIAdapter(sample_export_10k_conversations)
        count = sum(1 for _ in adapter.stream_conversations())
        return count

    # Measure peak memory (returns in MiB)
    mem_usage = memory_usage(process_all, max_usage=True)

    # Assert memory constraint (8GB = 8192 MiB)
    assert mem_usage < 8192, f"Memory usage {mem_usage}MiB exceeds 8GB limit"
```

**Test Data Generation**:
- Use `faker` library to generate synthetic conversation exports
- Scale: 10K conversations, 50K messages (matches SC-005 baseline)
- Store in `tests/fixtures/` with gitignored large files

**Alternatives Considered**:
- `pytest-monitor`: Rejected - less granular control over memory measurement
- Manual `time.time()` + `resource.getrusage()`: Rejected - reinventing benchmark tooling
- `scalene` profiler: Rejected - overkill for simple performance contracts

---

## Summary

All technology choices validated and implementation patterns documented. No unresolved clarifications remaining.

**Key Decisions**:
1. ✅ ijson for streaming (constant memory, handles 1GB+ files)
2. ✅ Lightweight TF-IDF (stdlib-based, no heavy NLP dependencies)
3. ✅ Pydantic v2 frozen models (immutability + validation)
4. ✅ structlog JSON logs (machine-readable, contextual fields)
5. ✅ pytest-benchmark + memory_profiler (performance contract validation)

**Next Phase**: Phase 1 - Design data models and contracts
