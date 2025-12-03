# Type Checking Guide

Echomine enforces **mypy --strict** with zero tolerance for errors. This guide covers type hint patterns and common issues.

## Core Principle

> **ZERO TOLERANCE**: mypy --strict MUST pass with no errors before any commit.

This is a non-negotiable Constitution Principle (VI). Type safety catches bugs at development time, not runtime.

## Running mypy

```bash
# Check all source code (required before commit)
mypy --strict src/echomine/

# Check tests too
mypy --strict src/echomine/ tests/

# Quick incremental check
mypy src/echomine/

# Verbose output for debugging
mypy --strict --show-error-codes --show-error-context src/echomine/
```

## Type Hint Basics

### Function Signatures

```python
# All parameters and return types must be annotated
def search(
    file_path: Path,
    query: SearchQuery,
    *,
    limit: int = 10,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations."""
    pass

# Use Optional for nullable parameters
def get_conversation(
    file_path: Path,
    conversation_id: str,
) -> Optional[Conversation]:
    """Returns None if not found."""
    pass
```

### Variables

```python
# Explicit annotation when type isn't obvious
results: list[SearchResult[Conversation]] = []
count: int = 0
found: bool = False

# Not needed when type is obvious from assignment
name = "test"  # str is inferred
adapter = OpenAIAdapter()  # Type is inferred
```

### Collections

```python
from typing import Dict, List, Set, Tuple  # Deprecated in 3.9+

# Use built-in generics (Python 3.9+)
names: list[str] = []
scores: dict[str, float] = {}
unique_ids: set[str] = set()
pair: tuple[str, int] = ("id", 42)

# For variable-length tuples
args: tuple[str, ...] = ("a", "b", "c")
```

## Advanced Patterns

### Generics with TypeVar

```python
from typing import TypeVar, Generic, Iterator

ConversationT = TypeVar("ConversationT", bound="Conversation")

class SearchResult(Generic[ConversationT]):
    """Generic search result."""
    conversation: ConversationT
    score: float

def search(query: SearchQuery) -> Iterator[SearchResult[Conversation]]:
    pass
```

### Protocol Classes

Use Protocol instead of ABC for duck typing:

```python
from typing import Protocol, Iterator, runtime_checkable

@runtime_checkable
class ConversationProvider(Protocol[ConversationT]):
    """Protocol for conversation providers."""

    def stream_conversations(
        self,
        file_path: Path,
    ) -> Iterator[ConversationT]:
        """Stream conversations from file."""
        ...

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
    ) -> Iterator[SearchResult[ConversationT]]:
        """Search with ranking."""
        ...

# Implementation doesn't need to inherit
class OpenAIAdapter:
    """Implements ConversationProvider implicitly."""

    def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
        pass

    def search(self, file_path: Path, query: SearchQuery) -> Iterator[SearchResult[Conversation]]:
        pass
```

### Callable Types

```python
from typing import Callable, Optional

# Function that takes int, returns None
ProgressCallback = Callable[[int], None]

def search(
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[ProgressCallback] = None,
) -> Iterator[SearchResult[Conversation]]:
    if progress_callback:
        progress_callback(count)
```

### Union Types

```python
from typing import Union

# Python 3.10+ syntax
def process(value: str | int) -> str:
    return str(value)

# Pre-3.10 syntax
def process(value: Union[str, int]) -> str:
    return str(value)
```

### Literal Types

```python
from typing import Literal

Role = Literal["user", "assistant", "system"]

def create_message(role: Role, content: str) -> Message:
    pass

# Only these values are allowed
create_message("user", "Hello")      # OK
create_message("admin", "Hello")     # mypy error!
```

## Pydantic Model Patterns

### Basic Model

```python
from pydantic import BaseModel, ConfigDict, Field

class Message(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    id: str = Field(..., min_length=1)
    content: str
    role: Literal["user", "assistant", "system"]
    timestamp: datetime
```

### Optional Fields (CRITICAL)

```python
from typing import Optional
from pydantic import Field

# CORRECT: Use Optional when data can be null
class Conversation(BaseModel):
    title: str
    updated_at: Optional[datetime] = Field(default=None)

# WRONG: Don't hide nullable with defaults (violates Data Integrity)
class Conversation(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.now)  # NO!
```

### Field with Default (mypy --strict requirement)

```python
# CORRECT: Explicit default= keyword
class SearchQuery(BaseModel):
    keywords: Optional[list[str]] = Field(default=None)
    limit: int = Field(default=10, gt=0)

# WRONG: Positional defaults (fails mypy --strict)
class SearchQuery(BaseModel):
    keywords: Optional[list[str]] = Field(None)  # Ambiguous!
    limit: int = Field(10, gt=0)  # Ambiguous!
```

## Common Errors and Fixes

### Error: Missing return type

```python
# Error: Function is missing a return type annotation
def get_count():
    return 42

# Fix: Add return type
def get_count() -> int:
    return 42
```

### Error: Incompatible return type

```python
# Error: Incompatible return value type (got "None", expected "str")
def get_name() -> str:
    if condition:
        return "name"
    # Missing return!

# Fix: Return in all branches or use Optional
def get_name() -> Optional[str]:
    if condition:
        return "name"
    return None
```

### Error: No return statement

```python
# Error: Missing return statement
def process(items: list[str]) -> list[str]:
    for item in items:
        pass  # Forgot to return!

# Fix: Add return
def process(items: list[str]) -> list[str]:
    result = []
    for item in items:
        result.append(item.upper())
    return result
```

### Error: Cannot infer type

```python
# Error: Need type annotation for "items"
items = []
items.append("test")

# Fix: Explicit annotation
items: list[str] = []
items.append("test")
```

### Error: Incompatible types in assignment

```python
# Error: Incompatible types in assignment
count: int = "10"  # str != int

# Fix: Use correct type
count: int = 10
```

### Error: "X" has no attribute "Y"

```python
# Error: "Optional[str]" has no attribute "upper"
def process(name: Optional[str]) -> str:
    return name.upper()  # name might be None!

# Fix: Handle None case
def process(name: Optional[str]) -> str:
    if name is None:
        return ""
    return name.upper()

# Or use assert for guaranteed non-None
def process(name: Optional[str]) -> str:
    assert name is not None
    return name.upper()
```

### Error: Iterator vs List

```python
# Error: Incompatible return value type (got "list", expected "Iterator")
def stream() -> Iterator[int]:
    return [1, 2, 3]  # list != Iterator

# Fix: Use yield (generator)
def stream() -> Iterator[int]:
    yield 1
    yield 2
    yield 3

# Or convert with iter()
def stream() -> Iterator[int]:
    return iter([1, 2, 3])
```

## Type Narrowing

```python
from typing import Optional, Union

def process(value: Optional[str]) -> str:
    # Type narrowing with if
    if value is None:
        return "default"
    # mypy knows value is str here
    return value.upper()

def handle(item: Union[str, int]) -> str:
    # Type narrowing with isinstance
    if isinstance(item, str):
        return item.upper()
    # mypy knows item is int here
    return str(item)
```

## Ignoring Errors (Last Resort)

Only use when absolutely necessary and document why:

```python
# type: ignore[error-code] - Use specific error code
result = external_lib.call()  # type: ignore[no-untyped-call]

# Document the reason
# mypy doesn't understand this third-party library's types
result = weird_api.fetch()  # type: ignore[arg-type]
```

**Rules for ignoring**:
1. Only for third-party libraries with bad type stubs
2. Always use specific error code
3. Add comment explaining why
4. Never ignore errors in your own code

## Configuration

pyproject.toml settings:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # Less strict for tests
```

## Pre-Commit Integration

mypy runs automatically on commit:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.8.0
  hooks:
    - id: mypy
      args: [--strict, --config-file=pyproject.toml]
      additional_dependencies:
        - pydantic>=2.0
        - types-all
```

## Debugging Type Issues

```bash
# Show what mypy infers
mypy --strict --show-error-codes src/echomine/

# Reveal inferred types
from typing import reveal_type
reveal_type(variable)  # mypy will print the inferred type

# Check specific file
mypy --strict src/echomine/adapters/openai/adapter.py
```

## Next Steps

- [Testing Guide](testing.md): TDD practices
- [Documentation](documentation.md): Writing docstrings
- [Architecture](../architecture.md): Design patterns

---

**Last Updated**: 2025-11-30
