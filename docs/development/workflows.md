# Development Workflows

This guide covers common development workflows for echomine contributors.

## Table of Contents

- [Adding a New Feature](#adding-a-new-feature)
- [Fixing a Bug](#fixing-a-bug)
- [Updating Dependencies](#updating-dependencies)
- [Updating Documentation](#updating-documentation)
- [Performance Optimization](#performance-optimization)

---

## Adding a New Feature

### Workflow Overview

1. **Understand the Requirement**
2. **Write Failing Tests (RED)**
3. **Implement Feature (GREEN)**
4. **Refactor (REFACTOR)**
5. **Update Documentation**
6. **Submit Pull Request**

### Detailed Steps

#### 1. Understand the Requirement

```bash
# Read the feature specification
cat specs/001-ai-chat-parser/spec.md | grep "FR-XXX"

# Check related issues
gh issue view <issue-number>

# Create feature branch
git checkout -b feature/descriptive-name
```

#### 2. Write Failing Tests (RED)

**Always write tests FIRST.** This is non-negotiable.

```python
# tests/unit/test_new_feature.py
import pytest
from echomine.models import NewModel


def test_new_feature_basic_functionality() -> None:
    """NewModel should validate required fields."""
    from pydantic import ValidationError

    # This test should FAIL initially (RED phase)
    with pytest.raises(ValidationError):
        NewModel()  # Missing required fields


def test_new_feature_with_valid_data() -> None:
    """NewModel should accept valid data."""
    # This test should also FAIL (feature doesn't exist yet)
    model = NewModel(field1="value1", field2="value2")
    assert model.field1 == "value1"
    assert model.field2 == "value2"
```

**Verify tests fail:**
```bash
pytest tests/unit/test_new_feature.py -v
# EXPECTED: FAILED (tests are RED)
```

#### 3. Implement Feature (GREEN)

Write minimal code to make tests pass:

```python
# src/echomine/models/new_model.py
from pydantic import BaseModel, ConfigDict, Field


class NewModel(BaseModel):
    """New feature model."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    field1: str = Field(..., description="First field")
    field2: str = Field(..., description="Second field")
```

**Verify tests pass:**
```bash
pytest tests/unit/test_new_feature.py -v
# EXPECTED: PASSED (tests are GREEN)
```

#### 4. Refactor (REFACTOR)

Improve code quality while keeping tests green:

```python
# Add validation, better error messages, helper methods
from pydantic import field_validator


class NewModel(BaseModel):
    """New feature model with enhanced validation."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
    )

    field1: str = Field(..., min_length=1, description="First field")
    field2: str = Field(..., min_length=1, description="Second field")

    @field_validator("field1")
    @classmethod
    def validate_field1(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field1 cannot be empty or whitespace")
        return v.strip()

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return f"{self.field1} - {self.field2}"
```

**Verify tests still pass:**
```bash
pytest tests/unit/test_new_feature.py -v
# EXPECTED: Still PASSED
```

#### 5. Run Quality Checks

```bash
# Type checking (must pass)
mypy --strict src/echomine/

# Linting and formatting
ruff check --fix src/ tests/
ruff format src/ tests/

# Full test suite with coverage
pytest --cov=echomine --cov-report=term-missing

# Pre-commit hooks
pre-commit run --all-files
```

#### 6. Update Documentation

```python
# Add comprehensive docstrings (Google style)
class NewModel(BaseModel):
    """New feature model with validation.

    This model provides [description of what it does and why it's useful].

    Attributes:
        field1: Description of field1
        field2: Description of field2

    Example:
        ```python
        from echomine.models import NewModel

        model = NewModel(field1="value1", field2="value2")
        print(model.display_name)  # "value1 - value2"
        ```

    Raises:
        ValidationError: If fields are invalid
    """
```

Update user-facing docs:
```bash
# If public API changed, update library-usage.md
vim docs/library-usage.md

# If CLI changed, update cli-usage.md
vim docs/cli-usage.md

# Update CHANGELOG.md
vim CHANGELOG.md
```

#### 7. Commit and Push

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(models): add NewModel with validation

Implements FR-XXX for [feature description].

- Validates field1 and field2 with Pydantic
- Provides display_name property
- Includes comprehensive unit tests (100% coverage)
- Adds docstrings with examples"

# Push to remote
git push origin feature/descriptive-name
```

#### 8. Create Pull Request

```bash
# Using GitHub CLI
gh pr create --title "feat(models): add NewModel with validation" \
  --body "## Summary
Implements FR-XXX for [feature description].

## Changes
- Added NewModel to src/echomine/models/
- Added unit tests with 100% coverage
- Updated documentation

## Related Issues
- Closes #123
- Implements FR-XXX

## Testing
- [x] Unit tests added
- [x] Type checking passes
- [x] Documentation updated"
```

---

## Fixing a Bug

### Workflow Overview

1. **Reproduce the Bug**
2. **Write Failing Test (RED)**
3. **Fix the Bug (GREEN)**
4. **Verify Fix**
5. **Submit Pull Request**

### Detailed Steps

#### 1. Reproduce the Bug

```bash
# Create bug fix branch
git checkout -b fix/issue-123-description

# Try to reproduce bug
python -c "from echomine import ...; # trigger bug"
```

Document reproduction steps in issue or comments.

#### 2. Write Failing Test (RED)

**CRITICAL**: Write a test that reproduces the bug FIRST.

```python
# tests/unit/test_bug_fix.py
def test_bug_123_conversation_with_null_timestamp() -> None:
    """Bug: Parser crashes on null timestamp (issue #123)."""
    from echomine.adapters.openai import OpenAIAdapter
    from pathlib import Path

    # Create fixture with null timestamp
    fixture = Path("tests/fixtures/null_timestamp.json")

    adapter = OpenAIAdapter()
    conversations = list(adapter.stream_conversations(fixture))

    # This should NOT raise an error
    # Currently fails with: AttributeError: 'NoneType' object has no attribute 'isoformat'
    assert len(conversations) > 0
```

**Verify test fails:**
```bash
pytest tests/unit/test_bug_fix.py::test_bug_123_conversation_with_null_timestamp -v
# EXPECTED: FAILED (reproduces bug)
```

#### 3. Fix the Bug (GREEN)

```python
# src/echomine/models/conversation.py
from datetime import datetime
from typing import Optional

class Conversation(BaseModel):
    # Before (buggy):
    # updated_at: datetime  # Crashes if null

    # After (fixed):
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update time, null if never updated"
    )

    @property
    def updated_at_or_created(self) -> datetime:
        """Fallback to created_at if updated_at is null."""
        return self.updated_at if self.updated_at is not None else self.created_at
```

**Verify test passes:**
```bash
pytest tests/unit/test_bug_fix.py::test_bug_123_conversation_with_null_timestamp -v
# EXPECTED: PASSED (bug fixed)
```

#### 4. Run Full Test Suite

```bash
# Ensure fix doesn't break existing tests
pytest --cov=echomine

# Type checking
mypy --strict src/echomine/

# Pre-commit
pre-commit run --all-files
```

#### 5. Update CHANGELOG

```bash
vim CHANGELOG.md
```

```markdown
## [Unreleased]

### Fixed
- Fixed crash when parsing conversations with null updated_at timestamp (#123)
```

#### 6. Commit and Create PR

```bash
git add .
git commit -m "fix(parser): handle null timestamp in conversations

Fixes #123 where parser crashed on conversations with null updated_at.

- Made updated_at Optional[datetime] instead of datetime
- Added updated_at_or_created property for fallback
- Added regression test with null timestamp fixture"

gh pr create --title "fix(parser): handle null timestamp in conversations"
```

---

## Updating Dependencies

### Workflow

#### Security Updates (Immediate)

```bash
# Check for security vulnerabilities
pip-audit

# If vulnerability found:
# 1. Update pyproject.toml
vim pyproject.toml
# Change: pydantic>=2.6.0,<3.0.0
# To: pydantic>=2.6.1,<3.0.0  (patched version)

# 2. Install updated version
pip install --upgrade pydantic

# 3. Run full test suite
pytest --cov=echomine
mypy --strict src/echomine/

# 4. Commit and release patch version
git add pyproject.toml
git commit -m "chore(deps): update pydantic to 2.6.1 (security fix)"
```

#### Minor Updates (Monthly)

```bash
# Check outdated packages
pip list --outdated

# Update in isolated environment
python -m venv test-env
source test-env/bin/activate
pip install -e ".[dev]"
pip install --upgrade <package>

# Run tests
pytest --cov=echomine
mypy --strict src/echomine/

# If all pass, update pyproject.toml
deactivate
```

#### Major Updates (Evaluate Breaking Changes)

```bash
# Example: Pydantic v2 → v3 (hypothetical)

# 1. Read migration guide
open https://docs.pydantic.dev/latest/migration/

# 2. Create branch
git checkout -b chore/upgrade-pydantic-v3

# 3. Update in isolated env, fix breaking changes
# 4. Run full test suite
# 5. Update docs if API changed
# 6. Bump MAJOR version of echomine (1.x → 2.x)
```

---

## Updating Documentation

### When to Update Docs

- Public API changes (new classes, functions, parameters)
- CLI command changes
- Breaking changes (migration guides)
- Bug fixes affecting documented behavior
- Performance improvements

### Workflow

#### 1. Update Docstrings (Code)

```python
# src/echomine/adapters/openai.py
def new_method(self, param: str) -> Iterator[Result]:
    """New method description.

    Args:
        param: Description of parameter

    Yields:
        Result objects with [description]

    Raises:
        ValueError: If param is invalid

    Example:
        ```python
        adapter = OpenAIAdapter()
        for result in adapter.new_method("value"):
            print(result)
        ```
    """
```

#### 2. Update User Guides (Markdown)

```bash
# Library API changes
vim docs/library-usage.md

# CLI changes
vim docs/cli-usage.md

# New features
vim docs/quickstart.md
```

#### 3. Build and Preview Docs

```bash
# Build locally
mkdocs build

# Serve with live reload
mkdocs serve
# Visit http://127.0.0.1:8000

# Check for broken links, formatting issues
```

#### 4. Update CHANGELOG

```bash
vim CHANGELOG.md
```

```markdown
## [Unreleased]

### Added
- New `new_method` in OpenAIAdapter for [purpose]

### Documentation
- Updated library-usage.md with new_method examples
- Added migration guide for breaking changes
```

#### 5. Deploy (Maintainers Only)

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

## Performance Optimization

### Workflow

#### 1. Identify Performance Issue

```bash
# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Profile code
python -m cProfile -o profile.stats -m echomine.cli search large_export.json
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

#### 2. Write Performance Test (RED)

```python
# tests/performance/test_optimization.py
def test_search_performance_under_30s(benchmark, large_export):
    """Search must complete in <30s for 1.6GB file."""
    from echomine.adapters.openai import OpenAIAdapter
    from echomine.models.search import SearchQuery

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["python"], limit=10)

    def search():
        return list(adapter.search(large_export, query))

    result = benchmark(search)
    assert benchmark.stats["mean"] < 30.0  # Currently FAILS at 45s
```

#### 3. Optimize (GREEN)

```python
# Before (slow):
def search(self, file_path: Path, query: SearchQuery):
    conversations = list(self.stream_conversations(file_path))  # Loads all into memory!
    for conv in conversations:
        # Score and rank

# After (fast):
def search(self, file_path: Path, query: SearchQuery):
    for conv in self.stream_conversations(file_path):  # Streaming!
        score = self._calculate_score(conv, query)
        if score > 0:
            yield SearchResult(conversation=conv, score=score)
```

#### 4. Verify Performance Improvement

```bash
pytest tests/performance/test_optimization.py --benchmark-only
# EXPECTED: Now passes (<30s)

# Compare before/after
pytest tests/performance/ --benchmark-compare=baseline
```

#### 5. Document Performance Change

```bash
vim CHANGELOG.md
```

```markdown
## [Unreleased]

### Performance
- Improved search performance by 50% (45s → 22s for 1.6GB files) via streaming optimization
```

---

## Common Pitfalls

### ❌ Writing Code Before Tests

```python
# WRONG: Implementation first
def new_feature():
    return "implementation"

# Then later...
def test_new_feature():
    assert new_feature() == "implementation"
```

**Why wrong?** You don't know if test actually validates behavior.

### ✅ Tests First (TDD)

```python
# CORRECT: Test first (RED)
def test_new_feature():
    result = new_feature()  # Doesn't exist yet - test FAILS
    assert result == "expected"

# Then implement (GREEN)
def new_feature():
    return "expected"  # Minimal code to pass
```

### ❌ Skipping mypy --strict

```bash
# WRONG: Ignoring type errors
mypy src/echomine/  # Has errors
# "I'll fix them later" ← Never happens
```

### ✅ Fix Type Errors Immediately

```bash
# CORRECT: Fix before committing
mypy --strict src/echomine/  # Must be zero errors
```

---

## Quick Reference

### Feature Development
```bash
git checkout -b feature/name
# Write failing test → Implement → Refactor → Quality checks → Commit
```

### Bug Fix
```bash
git checkout -b fix/issue-123
# Reproduce → Write failing test → Fix → Verify → Commit
```

### Dependency Update
```bash
pip list --outdated
# Update pyproject.toml → Test → Commit
```

### Documentation Update
```bash
# Update docstrings and markdown
mkdocs serve  # Preview
git commit -m "docs: update ..."
```

---

**Last Updated**: 2025-11-28
