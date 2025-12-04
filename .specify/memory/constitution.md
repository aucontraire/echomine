<!--
SYNC IMPACT REPORT
==================
Version: 1.1.0 → 1.1.1
Change Type: PATCH (Enhanced existing principle with clarification)

Modified Principles:
- VI. Strict Typing Mandatory - Added "Data Integrity" bullet point and enhanced rationale

Added Sections: None

Removed Sections: None

Templates Requiring Updates:
- .specify/templates/plan-template.md - No changes needed (type safety already covered)
- .specify/templates/spec-template.md - No changes needed
- .specify/templates/tasks-template.md - No changes needed

Follow-up TODOs: None (documentation already updated in CLAUDE.md and agent files)

Previous Changes (1.0.0 → 1.1.0):
- Added VI. Strict Typing Mandatory
- Added VII. Multi-Provider Adapter Pattern
- Added VIII. Memory Efficiency & Streaming
- Added Technology Standards section
-->

# Echomine Constitution

## Core Principles

### I. Library-First Architecture

Every feature in Echomine MUST start as a standalone library. Libraries SHALL be:

- **Self-contained**: Minimal external dependencies, clear bounded context
- **Independently testable**: Can be tested without the full application
- **Well-documented**: Clear purpose, API contracts, usage examples
- **Single-purpose**: Each library solves one problem well

**Rationale**: Library-first design enforces modularity, enables reuse, and prevents tight coupling. A feature that cannot stand alone as a library is likely insufficiently decomposed.

### II. CLI Interface Contract

Every library MUST expose its core functionality through a command-line interface following this protocol:

- **Input**: Accept data via stdin or command-line arguments
- **Output**: Results to stdout, errors to stderr (exit code non-zero on failure)
- **Formats**: Support both JSON (machine-readable) and human-readable output
- **Composability**: Designed for Unix pipeline integration

**Rationale**: CLI interfaces provide universal access, enable automation, facilitate testing, and ensure debuggability without requiring GUI or complex setup.

### III. Test-Driven Development (NON-NEGOTIABLE)

Test-Driven Development is MANDATORY for all code in Echomine. The workflow is:

1. **Write tests first**: Define expected behavior through tests
2. **Get user approval**: Review tests with stakeholders before implementation
3. **Verify tests fail**: Confirm tests fail for the right reason (red phase)
4. **Implement**: Write minimum code to make tests pass (green phase)
5. **Refactor**: Improve code while keeping tests green

**Rationale**: TDD ensures requirements are testable, prevents scope creep, provides immediate regression protection, and serves as living documentation. This is non-negotiable because it fundamentally changes how we think about and build software.

### IV. Observability & Debuggability

All components MUST be observable and debuggable in production:

- **Structured logging**: Use structured logs (JSON format) with consistent field names
- **Text-based I/O**: Prefer human-inspectable formats over binary when practical
- **Operation tracing**: Log key decision points, inputs, and outputs
- **Error context**: Errors MUST include actionable context (what failed, why, how to fix)

**Rationale**: Text-based protocols and structured logging make systems transparent. When issues arise, we can diagnose them through log analysis rather than requiring debugger attachment or code inspection.

### V. Simplicity & YAGNI

Start simple and resist premature complexity:

- **You Aren't Gonna Need It**: Don't build features for hypothetical future needs
- **Minimum viable complexity**: Choose the simplest solution that works
- **No premature abstraction**: Three uses before extracting a pattern
- **Question complexity**: Any abstraction beyond direct implementation MUST be justified

**Rationale**: Complexity is a liability. Every abstraction layer, design pattern, or framework adds cognitive load and maintenance burden. Optimize for clarity and simplicity over cleverness.

### VI. Strict Typing Mandatory

All Python code MUST use strict type checking without exception:

- **mypy --strict compliance**: Required for ALL code (application code AND tests)
- **Type hints mandatory**: All functions, methods, parameters, and return values
- **NO `Any` types**: Prohibited without explicit justification documented in code comments
- **Pydantic models mandatory**: ALL structured data uses Pydantic models (no raw dicts/lists)
- **Data Integrity**: Model data as it exists in source (nullable fields stay Optional, not hidden with defaults)
- **CI pipeline enforcement**: Type checking blocks merges on failures

**Rationale**: Strict typing catches bugs at development time, serves as inline documentation, and enables confident refactoring. For a data parsing tool handling complex JSON structures from multiple AI platforms, type safety is non-negotiable. Dynamic typing's flexibility becomes a liability when processing untrusted external data. Data integrity ensures type safety reflects reality—using Optional[T] for nullable fields enforces null safety and exposes data quality issues rather than papering over them with defaults.

### VII. Multi-Provider Adapter Pattern

Echomine parses conversation exports from multiple AI platforms using a shared abstraction:

- **Core parser abstraction**: Unified `ConversationProvider` protocol for all adapters
- **OpenAI adapter first**: ChatGPT export format is the initial implementation
- **Future adapters**: Anthropic, Google, and other providers MUST conform to the protocol
- **Shared Pydantic models**: Common data structures (`Message`, `Conversation`, `Thread`) across all providers
- **Isolated quirks**: Provider-specific format handling stays within adapter implementations

**Rationale**: Echomine will parse exports from multiple AI platforms. A shared abstraction prevents coupling to any single vendor's format while allowing provider-specific handling. Users should interact with a unified conversation model regardless of source.

### VIII. Memory Efficiency & Streaming

Support for large conversation exports (1GB+ files) is mandatory:

- **No full-file loading**: Never load entire exports into memory at once
- **Streaming JSON parsing**: Parse conversation trees incrementally
- **Lazy loading**: Use generator patterns for large datasets
- **Performance contracts**: Tests MUST verify max memory usage and processing time
- **Progress indicators**: Long-running operations show progress to users

**Rationale**: ChatGPT exports can be gigabytes for power users with extensive conversation history. Users expect responsive tools that don't crash their machines or require closing other applications. Memory efficiency isn't optional—it's a core requirement.

## Development Workflow

### Code Review Requirements

All changes MUST be reviewed for:

1. **Constitution compliance**: Does this change violate any core principles?
2. **Test coverage**: Are tests written first? Do they cover edge cases?
3. **Type safety**: Does mypy --strict pass? Are all types properly annotated?
4. **Library boundaries**: Is this properly isolated? Could it be more modular?
5. **CLI contract**: Does the interface follow our protocol?
6. **Provider abstraction**: Does code respect the ConversationProvider protocol?
7. **Memory efficiency**: Are streaming patterns used for large data?
8. **Observability**: Can we debug this in production through logs?

### Complexity Justification

Any violation of Simplicity & YAGNI principles MUST be documented in plan.md:

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [Pattern/Tool] | [Specific problem] | [Why direct approach insufficient] |

This table forces explicit cost-benefit analysis before adding complexity.

### Quality Gates

Before merging to master:

- ✅ All tests pass (and were written first)
- ✅ mypy --strict passes with zero errors (code + tests)
- ✅ No raw dicts/lists for structured data (Pydantic models only)
- ✅ Memory/performance tests pass (if applicable to changes)
- ✅ CLI interface follows protocol (if applicable)
- ✅ Constitution check completed in plan.md
- ✅ Code review completed
- ✅ Documentation updated

## Governance

### Authority

This constitution supersedes all other development practices, guides, or conventions. When conflicts arise between this constitution and other documents, the constitution takes precedence.

### Amendment Process

Constitutional changes require:

1. **Proposal**: Document the change, rationale, and impact analysis
2. **Review**: Stakeholder review and approval
3. **Version bump**: Update CONSTITUTION_VERSION according to semantic versioning
4. **Propagation**: Update all dependent templates and documentation
5. **Migration plan**: If existing code violates new principles, document remediation

### Versioning Policy

- **MAJOR**: Backward incompatible changes (removing/redefining principles)
- **MINOR**: Adding new principles or materially expanding guidance
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance Review

All pull requests MUST include a constitution compliance check. Reviewers SHALL verify:

- Core principles are followed (all eight principles)
- Complexity is justified if Simplicity principle violated
- TDD workflow was followed (tests written first)
- Type safety enforced (mypy --strict passes)
- Pydantic models used for all structured data
- Provider protocol respected (for parser code)
- Memory efficiency patterns applied (for large data operations)
- CLI contract followed where applicable

## Technology Standards

### Python Type Safety Requirements

- **Python 3.12+**: Minimum version required for all development
- **mypy --strict**: Must pass with zero errors in pre-commit hooks
- **Pydantic v2**: ALL data models use Pydantic with `strict=True` mode enabled
- **No raw dict/list**: Structured data MUST use Pydantic models, not primitive types
- **Protocol classes**: Use `typing.Protocol` for interfaces (`ConversationProvider`, `ExportAdapter`)
- **Type annotations**: Mandatory for all function signatures, parameters, return values, and class attributes

Example of proper typing:

```python
from typing import Protocol
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Immutable message structure."""
    model_config = {"frozen": True, "strict": True}

    id: str
    content: str
    timestamp: datetime
    parent_id: str | None = None

class ConversationProvider(Protocol):
    """Protocol for AI provider export parsers."""
    def parse_export(self, file_path: Path) -> Iterator[Conversation]:
        """Stream conversations from export file."""
        ...
```

### Data Model Conventions

- **Immutability**: All conversation structures use Pydantic models with `frozen=True`
- **Tree relationships**: Parent/child message chains preserved through `parent_id` references
- **Export format versioning**: Models support schema evolution (handle v1, v2, etc. formats)
- **JSON schema generation**: Pydantic models auto-generate schemas for external tooling
- **Validation**: Pydantic validation catches malformed exports at parse time

### Testing Requirements

- **Type checking in tests**: Test code MUST also pass mypy --strict
- **Memory profiling**: Performance tests MUST measure memory usage for large files
- **Fixture typing**: Test fixtures properly typed (no `Any` in conftest.py)
- **Provider contract tests**: Shared test suite verifying all providers implement protocol correctly

**Version**: 1.1.1 | **Ratified**: 2025-11-21 | **Last Amended**: 2025-11-22
