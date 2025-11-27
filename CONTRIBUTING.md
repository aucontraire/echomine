# Contributing to Echomine

Thank you for your interest in contributing to Echomine! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Test-Driven Development (TDD)](#test-driven-development-tdd)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Architecture](#project-architecture)

## Development Setup

### Prerequisites

- **Python 3.12 or higher** (required for modern type hints)
- **Git** for version control
- Basic understanding of async/await patterns and type hints

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/echomine/echomine.git
cd echomine

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install
```

### Verify Installation

```bash
# Run tests to verify setup
pytest

# Check type checking works
mypy --strict src/echomine/

# Verify CLI works
python -m echomine.cli --version
```

## Development Workflow

Echomine follows a strict **Test-Driven Development (TDD)** workflow. All code changes must follow the RED-GREEN-REFACTOR cycle.

### Basic Workflow

1. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write failing tests first** (RED phase)
   - Write tests that define the expected behavior
   - Verify tests fail (proving they test something)

3. **Implement minimal code** to pass tests (GREEN phase)
   - Write the simplest code that makes tests pass
   - No premature optimization

4. **Refactor** while keeping tests green (REFACTOR phase)
   - Improve code structure, readability, performance
   - Tests must remain green throughout

5. **Run quality checks**
   ```bash
   # Type checking (must pass)
   mypy --strict src/echomine/

   # Linting and formatting
   ruff check --fix src/ tests/
   ruff format src/ tests/

   # Full test suite with coverage
   pytest --cov=echomine --cov-report=term-missing
   ```

6. **Commit with conventional commit message**
   ```bash
   git add .
   git commit -m "feat: add search filtering by date range"
   ```

7. **Push and create pull request**

## Test-Driven Development (TDD)

### The RED-GREEN-REFACTOR Cycle

Echomine enforces strict TDD. **No exceptions.**

#### RED Phase: Write Failing Test

```python
# tests/unit/test_search_query.py
import pytest
from echomine.models.search import SearchQuery

def test_search_query_requires_at_least_keywords_or_title() -> None:
    """SearchQuery must have either keywords or title_filter."""
    from pydantic import ValidationError

    # This test should FAIL initially (RED)
    with pytest.raises(ValidationError, match="at least one"):
        SearchQuery()  # No keywords or title_filter
```

**Verify the test fails:**
```bash
pytest tests/unit/test_search_query.py::test_search_query_requires_at_least_keywords_or_title -v
# EXPECTED: FAILED (test is RED)
```

#### GREEN Phase: Make Test Pass

```python
# src/echomine/models/search.py
from pydantic import BaseModel, Field, model_validator

class SearchQuery(BaseModel):
    keywords: Optional[list[str]] = Field(default=None)
    title_filter: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_at_least_one_filter(self) -> "SearchQuery":
        if not self.keywords and not self.title_filter:
            raise ValueError("At least one of keywords or title_filter required")
        return self
```

**Verify the test passes:**
```bash
pytest tests/unit/test_search_query.py::test_search_query_requires_at_least_keywords_or_title -v
# EXPECTED: PASSED (test is GREEN)
```

#### REFACTOR Phase: Improve Code

Now that tests are green, improve the implementation:
- Better error messages
- Extract validation logic
- Improve type safety
- Add docstrings

**Tests must remain GREEN throughout refactoring.**

### TDD Best Practices

1. **Write the smallest test possible** - One assertion per test when practical
2. **Test behavior, not implementation** - Focus on what, not how
3. **Keep tests independent** - No shared state between tests
4. **Use descriptive test names** - Name explains what is being tested
5. **Verify tests fail before implementing** - Proves tests are actually testing something

## Code Quality Standards

### Type Checking (Mandatory)

Echomine requires **mypy --strict** compliance with **zero errors**.

```bash
# Check type compliance (must pass)
mypy --strict src/echomine/

# Check tests too (optional but recommended)
mypy --strict src/echomine/ tests/
```

**Type Checking Rules:**
- ✅ All functions must have type hints
- ✅ All variables must have type annotations when ambiguous
- ✅ Use `Protocol` for abstract types, not `Any`
- ✅ Use `Optional[T]` for nullable values
- ❌ No `Any` types in public API
- ❌ No `# type: ignore` without justification

**Example:**
```python
from pathlib import Path
from typing import Iterator, Optional

from echomine.models.conversation import Conversation
from echomine.models.search import SearchQuery, SearchResult

def search(
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations with proper type hints."""
    # Implementation with full type safety
    pass
```

### Linting and Formatting

Echomine uses **Ruff** for linting and formatting.

```bash
# Check for linting issues
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Check formatting without changes
ruff format --check src/ tests/
```

### Docstrings (Google Style)

All public functions, classes, and modules must have docstrings.

```python
def search(
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

### Pre-Commit Hooks

Run all quality checks before committing:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or let git run them automatically on commit
git commit -m "feat: add new feature"  # Hooks run automatically
```

## Testing Guidelines

### Test Pyramid Structure

Echomine follows the testing pyramid:
- **70% Unit Tests**: Fast, isolated tests of individual components
- **20% Integration Tests**: Component interaction tests
- **5% Contract Tests**: Protocol compliance and FR validation
- **5% Performance Tests**: Benchmarks and memory profiling

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=echomine --cov-report=term-missing

# Run only unit tests (fast)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run contract tests (FR validation)
pytest tests/contract/ -v

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Run specific test file
pytest tests/unit/test_conversation.py -v

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m unit        # Only unit tests
```

### Test Coverage Requirements

- **Minimum coverage**: 80% overall
- **Critical paths**: 90% coverage
- **Public API**: 95% coverage

Check coverage:
```bash
# Generate coverage report
pytest --cov=echomine --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Writing Good Tests

**Unit Test Example:**
```python
# tests/unit/test_search_query.py
import pytest
from datetime import date
from echomine.models.search import SearchQuery

@pytest.mark.unit
def test_search_query_date_range_validation() -> None:
    """SearchQuery validates from_date <= to_date."""
    from pydantic import ValidationError

    # Valid date range
    query = SearchQuery(
        keywords=["test"],
        from_date=date(2024, 1, 1),
        to_date=date(2024, 12, 31),
    )
    assert query.from_date < query.to_date

    # Invalid date range (from_date > to_date)
    with pytest.raises(ValidationError, match="from_date"):
        SearchQuery(
            keywords=["test"],
            from_date=date(2024, 12, 31),
            to_date=date(2024, 1, 1),
        )
```

**Integration Test Example:**
```python
# tests/integration/test_search_flow.py
import pytest
from pathlib import Path
from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery

@pytest.mark.integration
def test_search_with_keywords_returns_ranked_results(tmp_export_file: Path) -> None:
    """End-to-end search workflow with BM25 ranking."""
    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["python", "async"], limit=5)

    results = list(adapter.search(tmp_export_file, query))

    # Verify results structure
    assert len(results) <= 5
    assert all(0.0 <= r.score <= 1.0 for r in results)

    # Verify ranking (descending scores)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
```

### Test Fixtures

Use pytest fixtures for reusable test data:

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_export_file() -> Path:
    """Path to sample export fixture."""
    return Path(__file__).parent / "fixtures" / "sample_export.json"

@pytest.fixture
def tmp_export_file(tmp_path: Path) -> Path:
    """Create temporary export file for testing."""
    export_file = tmp_path / "test_export.json"
    # Generate test data
    return export_file
```

## Commit Guidelines

### Conventional Commits

Echomine uses [Conventional Commits](https://www.conventionalcommits.org/) for semantic versioning.

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring (no behavior change)
- `perf`: Performance improvements
- `chore`: Build process, dependencies, tooling

**Examples:**
```bash
# Feature with body
git commit -m "feat(search): add date range filtering

Implements FR-334 date range filtering for SearchQuery.
Supports from_date and to_date parameters with inclusive ranges."

# Bug fix
git commit -m "fix(parser): handle missing timestamp field gracefully

Fixes issue where conversations without updated_at caused parser to fail.
Now falls back to created_at when updated_at is null."

# Documentation
git commit -m "docs: add TDD workflow examples to CONTRIBUTING.md"

# Test addition
git commit -m "test(search): add contract tests for BM25 ranking"
```

### Commit Message Guidelines

- ✅ Use imperative mood ("add feature" not "added feature")
- ✅ Keep subject line under 72 characters
- ✅ Reference issue/FR numbers in body when applicable
- ✅ Explain *why* not just *what* in the body
- ❌ No "Co-Authored-By" or AI attribution lines (removed by pre-commit hook)

## Pull Request Process

### Before Submitting PR

1. **Ensure all tests pass**
   ```bash
   pytest
   ```

2. **Verify type checking**
   ```bash
   mypy --strict src/echomine/
   ```

3. **Check coverage** (target: 80% minimum)
   ```bash
   pytest --cov=echomine --cov-report=term-missing
   ```

4. **Run linting and formatting**
   ```bash
   ruff check --fix src/ tests/
   ruff format src/ tests/
   ```

5. **Run pre-commit hooks**
   ```bash
   pre-commit run --all-files
   ```

### PR Template

When creating a PR, include:

**Title:** Use conventional commit format
```
feat(search): add date range filtering
```

**Description:**
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Added date range filtering to SearchQuery
- Updated search adapter to respect from_date/to_date
- Added 8 unit tests, 2 integration tests
- Updated documentation

## Related Issues
- Closes #123
- Implements FR-334, FR-335

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Coverage maintained >80%

## Checklist
- [ ] Tests pass (`pytest`)
- [ ] Type checking passes (`mypy --strict`)
- [ ] Linting passes (`ruff check`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
```

### PR Review Process

1. **Automated Checks**: CI/CD runs tests, type checking, linting
2. **Code Review**: Maintainer reviews for:
   - Constitution compliance
   - Test coverage
   - Type safety
   - Documentation quality
3. **Approval**: At least one maintainer approval required
4. **Merge**: Squash and merge with conventional commit message

## Project Architecture

### Design Principles

Echomine follows 8 Constitution Principles (see `specs/001-ai-chat-parser/constitution.md`):

1. **Library-First Architecture**: Core functionality is importable library, CLI wraps it
2. **CLI Interface Contract**: Results to stdout, progress/errors to stderr
3. **Test-Driven Development**: RED-GREEN-REFACTOR cycle mandatory
4. **Observability**: JSON structured logging, contextual fields
5. **Simplicity & YAGNI**: Implement only what spec requires
6. **Strict Typing**: mypy --strict with zero tolerance for errors
7. **Multi-Provider Pattern**: Stateless adapters implementing ConversationProvider protocol
8. **Memory Efficiency**: O(1) memory via streaming (ijson), never load entire file

### Library-First Pattern

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

### Adapter Pattern

All provider adapters implement the `ConversationProvider` protocol:

```python
from typing import Protocol, Iterator, TypeVar
from echomine.models.conversation import Conversation
from echomine.models.search import SearchQuery, SearchResult

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
```

Adapters are **stateless** (no `__init__` parameters):

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

### Streaming Pattern (O(1) Memory)

Always use generators and ijson for memory efficiency:

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

## Getting Help

- **Documentation**: See `specs/001-ai-chat-parser/` for detailed specifications
- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

## License

By contributing to Echomine, you agree that your contributions will be licensed under the MIT License.
