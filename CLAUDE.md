# echomine Development Guidelines

**Project**: Library-first AI conversation export parser with multi-provider support
**Primary Use Case**: cognivault integration + standalone CLI for researchers
**Last Updated**: 2025-11-22

---

## Active Technologies

### Core Stack
- **Python 3.12+**: Required for modern type hints (PEP 695, improved generics)
- **Pydantic v2**: Immutable data models with strict validation
- **ijson**: Streaming JSON parser for O(1) memory usage (1GB+ files)
- **typer**: CLI framework with type hints
- **rich**: Terminal output formatting (tables, progress bars, syntax highlighting)
- **structlog**: JSON structured logging with contextual fields

### Development Tools
- **pytest**: Test framework with pytest-cov, pytest-mock, pytest-benchmark
- **mypy**: Static type checker (--strict mode enforced)
- **ruff**: Fast linter and formatter (replaces black, isort, flake8)
- **pre-commit**: Git hooks for quality gates

### Why These Choices
- **ijson over json.load()**: Prevents loading entire 1GB+ file into memory (Constitution Principle VIII)
- **Pydantic over dataclasses**: Comprehensive validation, immutability, JSON schema export
- **typer over click**: Native type hint support, automatic help generation
- **structlog over logging**: JSON output for observability, contextual fields

---

## Project Structure

```
echomine/
├── .claude/
│   ├── agents/              # 11 specialized sub-agents
│   ├── agents.md            # Agent coordination guide (READ THIS)
│   └── commands/            # Spec-kit commands (/speckit.*)
├── specs/
│   └── 001-ai-chat-parser/
│       ├── spec.md          # Feature specification with FRs
│       ├── plan.md          # Implementation plan
│       ├── tasks.md         # Task breakdown
│       └── contracts/       # CLI contract tests
├── src/echomine/
│   ├── models/              # Pydantic models (Message, Conversation, SearchQuery)
│   ├── protocols/           # ConversationProvider protocol
│   ├── adapters/            # Provider implementations (openai/, future: claude/, gemini/)
│   ├── search/              # BM25 ranking algorithms (future)
│   ├── utils/               # Logging, exceptions (NO business logic)
│   └── cli/                 # CLI commands (wraps library, no business logic)
├── tests/
│   ├── unit/                # Fast, isolated tests (70% of test pyramid)
│   ├── integration/         # Component interaction tests (20%)
│   ├── contract/            # FR validation tests (5%)
│   ├── performance/         # pytest-benchmark tests (5%)
│   └── fixtures/            # Test data (sample_export.json, generate_large_export.py)
└── pyproject.toml           # Dependencies, tool configs (mypy, ruff, pytest)
```

**Key Principles**:
- `src/echomine/` = library (importable, reusable)
- `src/echomine/cli/` = thin wrapper over library
- `tests/` mirrors `src/` structure
- `fixtures/` contains reusable test data

---

## Constitution Principles (Non-Negotiable)

All code, architecture, and design decisions MUST comply with these 8 principles:

### I. Library-First Architecture
- ✅ Core functionality in `src/echomine/` as importable library
- ✅ CLI in `src/echomine/cli/` wraps library (NEVER the reverse)
- ✅ All features available programmatically (cognivault integration use case)
- ❌ NEVER put business logic in CLI commands

### II. CLI Interface Contract
- ✅ Results to **stdout** (JSON via --json, human-readable by default)
- ✅ Progress and errors to **stderr**
- ✅ Exit codes: 0 (success), 1 (operational error), 2 (usage error)
- ✅ Pipeline-friendly (composable with jq, xargs, grep)

### III. Test-Driven Development (TDD)
- ✅ **RED**: Write failing test FIRST (verify it fails)
- ✅ **GREEN**: Write minimal code to pass test
- ✅ **REFACTOR**: Improve code while keeping tests green
- ❌ NEVER write implementation before tests
- ❌ NEVER commit without test coverage

### IV. Observability & Debuggability
- ✅ JSON structured logs via structlog (timestamp, level, operation, message)
- ✅ Contextual fields: file_name, conversation_id, message_id, count
- ✅ Text-based I/O (human-inspectable JSON exports)
- ✅ WARNING logs for skipped malformed entries (graceful degradation)

### V. Simplicity & YAGNI
- ✅ Implement ONLY what spec requires (no speculative features)
- ✅ Simplest solution that meets requirements
- ⚠️ Justify ANY complexity (e.g., ijson required for memory efficiency)
- ❌ No premature abstractions or over-engineering

### VI. Strict Typing Mandatory
- ✅ **ZERO TOLERANCE**: mypy --strict MUST pass (no exceptions)
- ✅ Type hints on ALL functions, methods, variables
- ✅ No `Any` types (use Protocol or TypeVar instead)
- ✅ Pydantic models for ALL structured data
- ✅ Protocol classes for abstractions (runtime_checkable)
- ✅ **Data Integrity**: Model data as it exists in source (nullable fields stay Optional, not hidden with defaults)

### VII. Multi-Provider Adapter Pattern
- ✅ OpenAIAdapter implements ConversationProvider protocol
- ✅ Stateless adapters: NO __init__ parameters, NO instance state
- ✅ Shared models (Message, Conversation) across providers
- ✅ Provider-specific models inherit from BaseConversation protocol
- ✅ Future: Claude, Gemini adapters without changing core library

### VIII. Memory Efficiency & Streaming
- ✅ **O(1) memory usage** regardless of file size (ijson streaming)
- ✅ Generator patterns for all streaming operations (Iterator, not List)
- ✅ Context managers for file handle cleanup (try/finally)
- ✅ Performance contract: 1.6GB search in <30s, 10K conversations on 8GB RAM
- ❌ NEVER load entire file into memory (no json.load())

---

## Architecture Patterns (Quick Reference)

### Library-First Pattern
```python
# ✅ CORRECT: CLI wraps library
from echomine import OpenAIAdapter, SearchQuery

def search_command(file: Path, keywords: list[str]):
    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=keywords)
    for result in adapter.search(file, query):
        print_result(result)

# ❌ WRONG: Library calls CLI
def search(file: Path, query: SearchQuery):
    subprocess.run(["echomine", "search", ...])  # NO!
```

### Stateless Adapter Pattern
```python
# ✅ CORRECT: Stateless, reusable adapter
class OpenAIAdapter:
    def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
        # No instance state, file_path passed as argument
        pass

# ❌ WRONG: Stateful adapter with __init__ config
class OpenAIAdapter:
    def __init__(self, file_path: Path):  # NO!
        self.file_path = file_path
```

### Streaming Pattern (O(1) Memory)
```python
# ✅ CORRECT: Generator with ijson
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")
        for item in parser:
            yield Conversation.model_validate(item)

# ❌ WRONG: Load entire file
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path) as f:
        data = json.load(f)  # Loads entire file!
        for item in data:
            yield Conversation.model_validate(item)
```

### Immutable Model Pattern
```python
# ✅ CORRECT: Frozen Pydantic model
class Message(BaseModel):
    model_config = ConfigDict(
        frozen=True,        # Immutability
        strict=True,        # No type coercion
        extra="forbid",     # Reject unknown fields
    )
    id: str
    content: str
    timestamp: datetime
```

### Graceful Degradation Pattern
```python
# ✅ CORRECT: Skip malformed, log, continue
for item in parser:
    try:
        conversation = Conversation.model_validate(item)
        yield conversation
    except ValidationError as e:
        logger.warning(
            "Skipped malformed entry",
            conversation_id=item.get("id", "unknown"),
            reason=str(e),
        )
        continue  # Keep processing
```

---

## Sub-Agents & Coordination

**Complete Documentation**: See `.claude/agents.md` for full details

### 11 Specialized Agents
1. **streaming-parser-specialist**: ijson, memory efficiency, large files
2. **multi-provider-adapter-architect**: Protocol design, multi-provider pattern
3. **pydantic-data-modeling-expert**: Models, validation, strict typing
4. **search-ranking-engineer**: BM25, relevance scoring, search optimization
5. **tdd-test-strategy-engineer**: TDD enforcement, test design, coverage
6. **python-strict-typing-enforcer**: mypy --strict compliance (ZERO ERRORS)
7. **cli-ux-designer**: Typer, Rich, terminal UX, stdout/stderr
8. **performance-profiling-specialist**: Profiling, benchmarks, optimization
9. **git-version-control**: Commits, branches, releases, conventional commits
10. **technical-documentation-specialist**: Docstrings, README, API docs
11. **software-architect**: Architecture, constitution compliance, design decisions

### Coordination Rules (READ agents.md for details)

**Before ANY Feature Implementation**:
1. ✅ Invoke `tdd-test-strategy-engineer` to design failing tests FIRST
2. ✅ Invoke `software-architect` if architecture is affected
3. ✅ Invoke domain experts in parallel (streaming, modeling, search, etc.)
4. ✅ Implement following TDD cycle (RED-GREEN-REFACTOR)

**Before EVERY Commit** (Quality Gates):
1. ✅ `tdd-test-strategy-engineer`: Validate test coverage >80% critical paths
2. ✅ `python-strict-typing-enforcer`: Validate mypy --strict passes (zero errors)
3. ✅ `performance-profiling-specialist`: Validate benchmarks pass
4. ✅ `git-version-control`: Review changes, craft conventional commit

**Quick Reference**:
| Task | Agents |
|------|--------|
| New provider adapter | software-architect, multi-provider-adapter-architect, pydantic-data-modeling-expert, streaming-parser-specialist, tdd-test-strategy-engineer |
| Search implementation | tdd-test-strategy-engineer, search-ranking-engineer, streaming-parser-specialist, python-strict-typing-enforcer |
| CLI command | software-architect, cli-ux-designer, tdd-test-strategy-engineer |
| Pydantic models | pydantic-data-modeling-expert, python-strict-typing-enforcer |
| Performance optimization | performance-profiling-specialist, software-architect, streaming-parser-specialist |
| Commit/PR | tdd-test-strategy-engineer → python-strict-typing-enforcer → performance-profiling-specialist → git-version-control |

---

## Development Commands

### Setup
```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=echomine --cov-report=term-missing

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run contract tests (FR validation)
pytest tests/contract/

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Run specific test file
pytest tests/unit/test_conversation.py -v

# Run with specific marker
pytest -m "not slow"
```

### Type Checking (MUST PASS)
```bash
# Check all source files (strict mode)
mypy --strict src/echomine/

# Check tests too
mypy --strict src/echomine/ tests/

# Quick check (incremental)
mypy src/echomine/
```

### Linting & Formatting
```bash
# Check linting issues
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Check formatting without changes
ruff format --check src/ tests/
```

### Running CLI (Development)
```bash
# List conversations
python -m echomine.cli list tests/fixtures/sample_export.json

# Search with keywords
python -m echomine.cli search tests/fixtures/sample_export.json \
  --keywords "algorithm,leetcode" --limit 5

# Search with JSON output
python -m echomine.cli search tests/fixtures/sample_export.json \
  --keywords "python" --json

# Get specific conversation
python -m echomine.cli export tests/fixtures/sample_export.json \
  <conversation-id> --output ./output.md
```

### Pre-Commit Checks (Run Before Commit)
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run mypy --all-files
pre-commit run ruff --all-files
```

### Generate Test Fixtures
```bash
# Generate large export for performance testing
python tests/fixtures/generate_large_export.py \
  --conversations 10000 \
  --output tests/fixtures/large_export.json
```

---

## Code Style & Standards

### Mypy Strict Mode (MANDATORY)
```python
# ✅ All functions must have type hints
def search(file_path: Path, query: SearchQuery) -> Iterator[SearchResult[Conversation]]:
    pass

# ✅ All variables must have type annotations when ambiguous
results: list[SearchResult[Conversation]] = []

# ✅ Use Protocol for abstract types
from typing import Protocol

class ConversationProvider(Protocol[ConversationT]):
    def search(self, file_path: Path, query: SearchQuery) -> Iterator[SearchResult[ConversationT]]:
        ...

# ❌ No Any types
def process(data: Any) -> Any:  # NO!
    pass
```

### Pydantic Models (v2 Patterns)
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Message(BaseModel):
    # Always use ConfigDict for v2
    model_config = ConfigDict(
        frozen=True,           # Immutability
        strict=True,           # No type coercion
        extra="forbid",        # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    # Use Field for constraints and descriptions
    id: str = Field(..., min_length=1, description="Message ID")
    content: str = Field(..., description="Message text")

    # Use field_validator for custom validation (v2 pattern)
    @field_validator("timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v.astimezone(UTC)
```

**CRITICAL v2 Patterns (Phase 5 Discoveries)**:

```python
# 1. ALWAYS use explicit default= keyword (mypy --strict requirement)
from typing import Optional
from pydantic import BaseModel, Field

# ❌ AVOID: Positional defaults (fails mypy --strict)
class SearchQuery(BaseModel):
    keywords: Optional[list[str]] = Field(None, description="...")
    limit: int = Field(10, gt=0, description="...")

# ✅ REQUIRED: Explicit keyword arguments (mypy --strict compliant)
class SearchQuery(BaseModel):
    keywords: Optional[list[str]] = Field(default=None, description="...")
    limit: int = Field(default=10, gt=0, description="...")

# 2. Use Optional[T] when source data can be null (Constitution Principle VI: Data Integrity)
class Conversation(BaseModel):
    created_at: datetime = Field(...)  # Always present
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Null if never updated (OpenAI export reality)"
    )

    # Provide helper properties for convenience without sacrificing accuracy
    @property
    def updated_at_or_created(self) -> datetime:
        """Non-null fallback for consumers who don't need null handling."""
        return self.updated_at if self.updated_at is not None else self.created_at

# ❌ AVOID: Hiding nullable data with defaults (violates Data Integrity principle)
class Conversation(BaseModel):
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),  # Pollutes data!
        description="Defaults to now if missing"
    )

# 3. model_copy() does shallow copy by default (Pydantic v2 frozen models)
original = conversation.model_copy()           # Shallow (fast, safe for frozen models)
deep_copy = conversation.model_copy(deep=True)  # Deep (explicit when needed)
```

**Why These Matter**:
- **Explicit default=**: Pydantic v2 + mypy --strict requires keyword arguments for type safety
- **Optional design**: Accurately represents source data, enables data quality monitoring, prevents default pollution
- **Shallow copy**: Performance optimization for frozen models (immutability makes it safe)

### Import Conventions
```python
# ✅ Use future annotations for forward references
from __future__ import annotations

# ✅ Standard library first, then third-party, then local
import logging
from pathlib import Path
from typing import Iterator, Optional

import ijson
from pydantic import BaseModel

from echomine.models import Conversation
from echomine.protocols import ConversationProvider

# ❌ Avoid TYPE_CHECKING unless absolutely necessary
# We prefer from __future__ import annotations instead
```

### Docstring Style (Google Style)
```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[ProgressCallback] = None,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations matching query criteria with BM25 ranking.

    Args:
        file_path: Path to OpenAI export JSON file
        query: Search parameters (keywords, filters, limit)
        progress_callback: Optional callback for progress reporting

    Yields:
        SearchResult with conversation and relevance score (0.0-1.0)

    Raises:
        FileNotFoundError: If file_path does not exist
        ParseError: If export format is invalid
        ValidationError: If conversation data is malformed

    Example:
        ```python
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["algorithm"], limit=10)
        for result in adapter.search(Path("export.json"), query):
            print(f"{result.score:.2f}: {result.conversation.title}")
        ```
    """
```

### Error Handling Patterns
```python
# ✅ Specific exceptions, context managers, fail-fast
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    try:
        with open(file_path, "rb") as f:  # Context manager
            parser = ijson.items(f, "item")
            for item in parser:
                try:
                    yield Conversation.model_validate(item)
                except ValidationError as e:
                    # Graceful degradation: log and skip
                    logger.warning("Skipped malformed entry", reason=str(e))
                    continue
    except FileNotFoundError:
        # Fail fast on unrecoverable errors
        raise
    except PermissionError:
        raise

# ❌ Bare except clauses
try:
    do_something()
except:  # NO! Too broad
    pass
```

### Logging Patterns (structlog)
```python
from echomine.utils.logging import get_logger

logger = get_logger(__name__)

# ✅ JSON logs with contextual fields
logger.info(
    "Processing conversation",
    operation="stream_conversations",
    file_name=str(file_path),
    conversation_id=conversation.id,
    count=count,
)

# ✅ WARNING for skipped entries (graceful degradation)
logger.warning(
    "Skipped malformed entry",
    operation="stream_conversations",
    conversation_id=item.get("id", "unknown"),
    reason=str(e),
)

# ✅ ERROR for failures
logger.error(
    "Failed to parse export",
    operation="stream_conversations",
    file_name=str(file_path),
    error=str(e),
    exc_info=True,  # Include stack trace
)
```

---

## Key Documentation Links

### Specification & Planning
- **Feature Spec**: `specs/001-ai-chat-parser/spec.md` (FRs, user scenarios, acceptance criteria)
- **Implementation Plan**: `specs/001-ai-chat-parser/plan.md` (architecture, constitution, phases)
- **Tasks**: `specs/001-ai-chat-parser/tasks.md` (task breakdown with dependencies)
- **Data Model**: `specs/001-ai-chat-parser/data-model.md` (Pydantic model design)
- **Quickstart**: `specs/001-ai-chat-parser/quickstart.md` (library + CLI examples)

### Agent Coordination
- **Agent Directory**: `.claude/agents.md` (11 agents, coordination patterns, workflows)

### Contracts & Checklists
- **CLI Contract**: `specs/001-ai-chat-parser/contracts/cli_spec.md`
- **Requirements Checklist**: `specs/001-ai-chat-parser/checklists/requirements.md`
- **Library API Checklist**: `specs/001-ai-chat-parser/checklists/library-api.md`

### Test Fixtures
- **Sample Export**: `tests/fixtures/sample_export.json` (10 conversations for unit tests)
- **Large Export Generator**: `tests/fixtures/generate_large_export.py` (10K+ conversations)
- **Malformed Fixtures**: `tests/fixtures/malformed_*.json` (graceful degradation tests)

---

## Performance Contracts (MUST VALIDATE)

### Search Performance (SC-001)
- ✅ 1.6GB file search completes in <30 seconds
- ✅ Title-only search: <5 seconds for 10K conversations (FR-444)
- 🧪 Test: `pytest tests/performance/test_search_performance.py --benchmark-only`

### Memory Efficiency (SC-005)
- ✅ 10,000 conversations + 50,000 messages on 8GB RAM
- ✅ O(1) memory usage (constant, not proportional to file size)
- 🧪 Test: `pytest tests/performance/test_memory_usage.py`

### Progress Reporting (FR-068, FR-069)
- ✅ Callback invoked every 100 items OR 100ms (whichever comes first)
- ✅ Graceful degradation: processing continues after skip

### Resource Cleanup (FR-130-133)
- ✅ File handles closed even on early termination or exception
- ✅ Context managers for all file operations
- 🧪 Test: `pytest tests/unit/test_resource_cleanup.py`

---

## Recent Changes

- 2025-11-22: Added comprehensive development guidelines, agent coordination, constitution principles
- 2025-11-21: Initial project setup from Specify template (001-ai-chat-parser)

<!-- MANUAL ADDITIONS START -->
<!-- Add project-specific notes, tips, or warnings here -->
<!-- MANUAL ADDITIONS END -->
