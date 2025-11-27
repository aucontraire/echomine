# Architecture

This document describes the design principles, patterns, and architectural decisions that guide Echomine development.

## Design Principles

Echomine follows 8 core Constitution Principles that guide all architectural and implementation decisions:

### I. Library-First Architecture

Core functionality is built as an importable library, with CLI as a thin wrapper on top.

**Rationale**: Primary use case is cognivault integration. CLI is a convenience layer, not the core product.

**Implementation**:

```python
# ✅ CORRECT: CLI wraps library
from echomine import OpenAIAdapter, SearchQuery

def search_command(file: Path, keywords: list[str]):
    adapter = OpenAIAdapter()  # Library component
    query = SearchQuery(keywords=keywords)
    for result in adapter.search(file, query):
        print_result(result)  # CLI formatting

# ❌ WRONG: Library calls CLI
def search(file: Path, query: SearchQuery):
    subprocess.run(["echomine", "search", ...])  # NO!
```

### II. CLI Interface Contract

Results go to stdout, progress and errors go to stderr, with standard exit codes.

**Contract**:

- **stdout**: Results only (JSON or human-readable)
- **stderr**: Progress, warnings, errors
- **Exit codes**: 0 (success), 1 (operational error), 2 (usage error)

**Benefits**:

- Pipeline-friendly (compose with jq, grep, xargs)
- Separates data from metadata
- Standard UNIX conventions

### III. Test-Driven Development (TDD)

All features follow the RED-GREEN-REFACTOR cycle with no exceptions.

**Workflow**:

1. **RED**: Write failing test first (verify it fails)
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Improve code while keeping tests green

**Enforcement**: Pre-commit hooks reject commits without test coverage.

### IV. Observability & Debuggability

JSON structured logs via structlog with contextual fields.

**Logging Pattern**:

```python
from echomine.utils.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Processing conversation",
    operation="stream_conversations",
    file_name=str(file_path),
    conversation_id=conversation.id,
    count=count,
)
```

**Graceful Degradation**:

- Malformed entries logged and skipped (WARNING level)
- Processing continues for valid entries
- Summary reports include skip counts

### V. Simplicity & YAGNI

Implement ONLY what the spec requires. No speculative features.

**Examples**:

- No database layer (just file parsing)
- No caching (streaming is sufficient)
- No async (sync generators are simpler and adequate)

**When Complexity is Justified**:

- ijson: Required for O(1) memory usage on 1GB+ files
- BM25 ranking: Spec requirement for search quality

### VI. Strict Typing Mandatory

mypy --strict with ZERO TOLERANCE for errors.

**Requirements**:

- Type hints on ALL functions, methods, variables
- No `Any` types in public API
- Use Protocol for abstractions
- Pydantic models for all structured data

**Example**:

```python
from typing import Iterator, Optional
from pathlib import Path
from echomine.models import Conversation, SearchQuery, SearchResult

def search(
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Iterator[SearchResult[Conversation]]:
    """Full type safety."""
    pass
```

### VII. Multi-Provider Adapter Pattern

Stateless adapters implement ConversationProvider protocol.

**Design**:

- OpenAIAdapter for ChatGPT (v1.0)
- Future: ClaudeAdapter, GeminiAdapter (v2.0+)
- Shared models (Message, Conversation) across providers
- Provider-specific data in `metadata` dict

**Stateless Pattern**:

```python
# ✅ CORRECT: Stateless adapter
class OpenAIAdapter:
    def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
        # file_path passed as argument
        pass

# ❌ WRONG: Stateful adapter
class OpenAIAdapter:
    def __init__(self, file_path: Path):  # NO!
        self.file_path = file_path
```

### VIII. Memory Efficiency & Streaming

O(1) memory usage regardless of file size via ijson streaming.

**Pattern**:

```python
# ✅ CORRECT: Streaming with ijson
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")
        for item in parser:
            yield Conversation.model_validate(item)

# ❌ WRONG: Load entire file
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path) as f:
        data = json.load(f)  # Loads entire file into memory!
        for item in data:
            yield Conversation.model_validate(item)
```

**Performance Contracts**:

- 1.6GB file search in <30 seconds
- 10K conversations + 50K messages on 8GB RAM
- O(1) memory (constant, not proportional to file size)

## Architectural Patterns

### Adapter Pattern

All provider-specific logic is encapsulated in adapters that implement the `ConversationProvider` protocol:

```python
from typing import Protocol, Iterator, TypeVar
from echomine.models import Conversation, SearchQuery, SearchResult

ConversationT = TypeVar("ConversationT", bound="Conversation")

class ConversationProvider(Protocol[ConversationT]):
    """Protocol for conversation export adapters."""

    def stream_conversations(
        self,
        file_path: Path,
    ) -> Iterator[ConversationT]:
        """Stream conversations from export file."""
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
    ) -> Iterator[SearchResult[ConversationT]]:
        """Search conversations with BM25 ranking."""
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[ConversationT]:
        """Retrieve specific conversation by ID."""
        ...
```

### Immutable Data Models

All data models use Pydantic with strict validation and immutability:

```python
from pydantic import BaseModel, ConfigDict, Field

class Message(BaseModel):
    model_config = ConfigDict(
        frozen=True,           # Immutability
        strict=True,           # No type coercion
        extra="forbid",        # Reject unknown fields
        validate_assignment=True,
    )

    id: str = Field(..., min_length=1)
    content: str
    role: Literal["user", "assistant", "system"]
    timestamp: datetime  # UTC, timezone-aware
    parent_id: Optional[str] = None
```

### Streaming Pattern

All operations use generators for memory efficiency:

```python
# Returns Iterator, not List
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")
        for item in parser:
            try:
                yield Conversation.model_validate(item)
            except ValidationError as e:
                logger.warning("Skipped malformed entry", reason=str(e))
                continue
```

### Error Handling Strategy

**Fail-Fast on Unrecoverable Errors**:

- FileNotFoundError: File doesn't exist
- PermissionError: No read access
- SchemaVersionError: Unsupported export version

**Graceful Degradation on Data Errors**:

- ValidationError: Skip malformed conversation, log warning, continue
- ParseError: Skip malformed JSON entry, log warning, continue

**No Retries**: All errors are permanent. Users must fix the issue manually.

## Project Structure

```
echomine/
├── src/echomine/           # Library source code
│   ├── models/             # Pydantic data models
│   │   ├── conversation.py # Conversation, Message
│   │   ├── search.py       # SearchQuery, SearchResult
│   │   └── protocols.py    # ConversationProvider protocol
│   ├── adapters/           # Provider adapters
│   │   └── openai/         # OpenAI (ChatGPT) adapter
│   ├── search/             # Search and ranking logic
│   │   └── ranking.py      # BM25 algorithm
│   ├── exporters/          # Export formatters
│   │   └── markdown.py     # Markdown exporter
│   ├── utils/              # Utilities
│   │   └── logging.py      # Structured logging setup
│   └── cli/                # CLI commands (thin wrapper)
│       ├── app.py          # Typer app
│       └── commands/       # Individual commands
├── tests/                  # Test suite
│   ├── unit/               # Unit tests (70%)
│   ├── integration/        # Integration tests (20%)
│   ├── contract/           # Protocol contract tests (5%)
│   └── performance/        # Performance benchmarks (5%)
└── specs/                  # Design documents
    └── 001-ai-chat-parser/ # Feature specification
```

## Data Flow

### Streaming Operation Flow

```
Export File (JSON)
    ↓
ijson.items() [Streaming Parser]
    ↓
dict (raw JSON object)
    ↓
Conversation.model_validate() [Pydantic Validation]
    ↓
Conversation (Immutable Model)
    ↓
Generator Yield
    ↓
Consumer (CLI, Library User)
```

### Search Operation Flow

```
Export File
    ↓
stream_conversations() [Stream All]
    ↓
Filter by Date Range (if specified)
    ↓
Filter by Title (if specified) [Metadata-only]
    ↓
BM25 Ranking (if keywords specified) [Full-text]
    ↓
Sort by Relevance Score (descending)
    ↓
Limit Results
    ↓
SearchResult[Conversation] Generator
    ↓
Consumer
```

## Technology Choices

### Core Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.12+** | Language | Modern type hints (PEP 695, improved generics) |
| **Pydantic v2** | Data validation | Comprehensive validation, immutability, JSON schema |
| **ijson** | JSON parsing | Streaming for O(1) memory (handles 1GB+ files) |
| **typer** | CLI framework | Native type hint support, automatic help |
| **rich** | Terminal output | Tables, progress bars, syntax highlighting |
| **structlog** | Logging | JSON output for observability, contextual fields |

### Development Tools

| Tool | Purpose | Why Chosen |
|------|---------|------------|
| **pytest** | Testing | De facto standard, excellent fixtures/plugins |
| **mypy** | Type checking | Strict mode for zero-tolerance type safety |
| **ruff** | Linting/Formatting | Fast (10-100x faster than alternatives) |
| **pre-commit** | Git hooks | Automated quality gates |

### Alternative Considerations

**Why not async?**

- Sync generators are simpler
- No I/O-bound operations (just CPU + disk reads)
- ijson streaming is adequate for performance

**Why not database?**

- YAGNI: Not required by spec
- Export files are read-only
- Streaming handles large files efficiently

**Why not caching?**

- Export files don't change during read
- Memory efficiency is more important
- Adds complexity without clear benefit

## Extension Points

### Adding New Providers

1. Implement `ConversationProvider` protocol
2. Map provider-specific roles to standard roles
3. Store provider-specific data in `metadata` dict
4. Add provider-specific tests

Example:

```python
class ClaudeAdapter:
    """Adapter for Anthropic Claude exports."""

    def stream_conversations(
        self,
        file_path: Path,
    ) -> Iterator[Conversation]:
        # Parse Claude-specific format
        # Map "human" → "user", "assistant" → "assistant"
        # Store Claude-specific fields in metadata
        pass
```

### Adding New Search Filters

1. Add optional field to `SearchQuery` model
2. Update search logic in adapters
3. Add tests for new filter
4. Update CLI to accept new filter

**Backward compatibility**: New filters must be optional with sensible defaults.

## Performance Optimization

### Memory Efficiency

- **Streaming**: Never load entire file into memory
- **Generators**: Use `Iterator` return types, not `List`
- **Context Managers**: Ensure file handles are closed

### Search Performance

- **Title Filtering**: Metadata-only (no message content scan)
- **BM25 Ranking**: Only when keywords specified
- **Early Termination**: Stop after `limit` results

### Profiling

Use pytest-benchmark for performance regression testing:

```python
def test_search_performance(benchmark):
    """Search 1.6GB file completes in <30 seconds."""
    result = benchmark(adapter.search, large_file, query)
    assert benchmark.stats.stats.mean < 30.0
```

## Security Considerations

### Input Validation

- All file paths validated (Path objects, existence checks)
- All search queries validated (Pydantic models)
- No shell execution or eval()

### Resource Limits

- Streaming prevents OOM attacks
- File handle cleanup ensures no resource leaks

### Data Privacy

- No network calls (offline library)
- No telemetry or tracking
- All processing local

## Concurrency Model

### Thread Safety

- **Adapter instances**: Thread-safe (stateless)
- **Iterators**: NOT thread-safe (each thread needs its own)

### Multi-Process Safety

- Multiple processes can read same file concurrently
- File system provides read isolation

## Future Considerations

### Multi-Provider Support (v2.0)

- Add ClaudeAdapter, GeminiAdapter
- Auto-detection helper (optional)
- Provider registry pattern

### Advanced Search (v1.1)

- Semantic search (embeddings)
- Regex pattern matching
- Boolean query syntax

### Export Formats (v1.1)

- HTML export
- PDF export
- CSV export (metadata)

## Next Steps

- [Library Usage](library-usage.md): Comprehensive API guide
- [CLI Usage](cli-usage.md): Command-line reference
- [API Reference](api/index.md): Detailed API documentation
- [Contributing](contributing.md): Development guidelines
