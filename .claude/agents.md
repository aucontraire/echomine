# Agent Directory

Detailed documentation for all Echomine sub-agents and their coordination patterns.

---

## streaming-parser-specialist

**Primary Responsibility**: ijson streaming patterns, memory-efficient parsing, and large file handling

**Mandatory for**:
- ALL ijson implementation code
- Memory profiling and optimization for large files
- Iterator/generator pattern design
- Backpressure and resource management strategies
- File handle cleanup with context managers
- OpenAI export format parsing logic
- Handling malformed JSON entries with graceful degradation

**Key Principles**:
- ✅ O(1) memory usage regardless of file size (FR-003, Constitution Principle VIII)
- ✅ Generator patterns for all streaming operations (FR-026)
- ✅ Context managers for file handle cleanup (FR-130-133)
- ✅ Graceful degradation for malformed entries (FR-281-285)
- ✅ Progress reporting at 100-item intervals (FR-069)
- ✅ Fail-fast on unrecoverable errors (FR-042)

**Invocation Patterns**:
- User says "stream", "parse", "ijson", "memory efficient"
- Implementing ConversationProvider methods (stream_conversations, search)
- Performance issues with large files (1GB+)
- File parsing errors or malformed data handling
- Memory profiling and optimization

**Example Tasks**:
- Design ijson event parsing for OpenAI export schema
- Optimize memory usage for 10K+ conversation exports
- Implement progress callbacks during streaming operations
- Handle malformed JSON entries with skip logging
- Design context manager for file handle cleanup
- Profile memory usage for 1.6GB file parsing

**Performance Contracts**:
- Memory: O(1) constant memory regardless of file size
- Progress: Callback invoked every 100 items or 100ms (FR-068, FR-069)
- Cleanup: File handles closed even on early iteration termination

---

## multi-provider-adapter-architect

**Primary Responsibility**: Adapter pattern implementation and provider abstraction design

**Mandatory for**:
- ALL ConversationProvider protocol implementations
- Protocol design and validation (runtime_checkable)
- Provider-specific schema mapping and transformation
- New provider adapter implementations (Claude, Gemini, future providers)
- Type variance and generic type design (TypeVar bounds)
- Schema versioning and migration strategies

**Key Principles**:
- ✅ Protocol-based design with runtime_checkable (FR-027, Constitution Principle VII)
- ✅ Stateless adapters: no configuration in __init__ (FR-113-115)
- ✅ Provider-specific models implement shared BaseConversation protocol (FR-154)
- ✅ Schema versioning for backwards compatibility (FR-085)
- ✅ Generic type safety via ConversationT TypeVar (FR-151-152)
- ✅ Thread-safe adapter instances (FR-098-101)

**Invocation Patterns**:
- User says "adapter", "provider", "protocol"
- Adding support for new AI provider exports (Claude, Gemini)
- Refactoring existing adapter implementations
- Type system issues with generic types or protocols
- Protocol method signature changes

**Example Tasks**:
- Design ClaudeAdapter for Anthropic conversation exports
- Review OpenAIAdapter for protocol compliance
- Design schema version detection and validation logic
- Implement provider-agnostic search ranking interface
- Resolve TypeVar bound constraints for multi-provider support
- Validate thread safety of adapter implementations

**Architecture Checklist**:
- [ ] Adapter is stateless (no __init__ parameters)
- [ ] Implements complete ConversationProvider protocol
- [ ] Provider-specific model inherits from BaseConversation
- [ ] Uses context managers for resource cleanup
- [ ] Thread-safe (safe to share across threads)
- [ ] Schema version validated at parse time

---

## pydantic-data-modeling-expert

**Primary Responsibility**: Pydantic v2 model design, validation logic, and strict typing

**Mandatory for**:
- ALL Pydantic model creation and modification
- Field validators and root validators implementation
- Immutability enforcement (frozen=True, extra="forbid")
- Type hint correctness for mypy --strict compliance
- Model serialization/deserialization logic
- Timezone-aware datetime handling (UTC normalization)

**Key Principles**:
- ✅ **STRICT TYPING REQUIRED**: All code must pass mypy --strict
- ✅ Immutable models via frozen=True, extra="forbid" (FR-222-227)
- ✅ Timezone-aware datetime with UTC normalization (FR-244-246)
- ✅ Comprehensive field validation (min_length, ge, le constraints)
- ✅ Clear docstrings with usage examples
- ✅ Pydantic v2 patterns (ConfigDict, Field, field_validator)

**Invocation Patterns**:
- User says "model", "Pydantic", "validation", "schema"
- Creating or modifying Message, Conversation, SearchQuery, SearchResult models
- Type errors in model code (mypy failures)
- Adding new provider-specific models (ClaudeMessage, GeminiConversation)
- Field validation logic implementation

**Example Tasks**:
- Design SearchQuery model with date range filters and validation
- Implement timezone validation for Message timestamps
- Review Conversation tree navigation method type annotations
- Create ClaudeMessage model for Anthropic export format
- Add field validators for business logic constraints
- Ensure model serialization handles all edge cases

**Model Design Checklist**:
- [ ] frozen=True for immutability
- [ ] extra="forbid" to reject unknown fields
- [ ] All datetimes are timezone-aware and normalized to UTC
- [ ] Field constraints documented and validated
- [ ] Docstrings include usage examples
- [ ] mypy --strict passes with no errors
- [ ] Custom validators use @field_validator decorator

---

## search-ranking-engineer

**Primary Responsibility**: BM25 implementation, relevance scoring, and search optimization

**Mandatory for**:
- ALL search and ranking logic implementation
- BM25 algorithm implementation and tuning
- Keyword matching and scoring strategies
- Search result filtering and sorting
- Query optimization for large datasets (10K+ conversations)
- Combined filter execution (title + keywords + date range)

**Key Principles**:
- ✅ BM25 ranking algorithm for keyword search (FR-317-326)
- ✅ Case-insensitive keyword matching (FR-318)
- ✅ Score normalization to 0.0-1.0 range (FR-324)
- ✅ Title metadata filtering fast path: <5s for 10K conversations (FR-444)
- ✅ Combined filter optimization strategy (FR-319)
- ✅ OR logic for multiple keywords (FR-320)

**Invocation Patterns**:
- User says "search", "ranking", "BM25", "relevance"
- Implementing search() method in adapters
- Performance issues with keyword searches (>30s for 1.6GB)
- Relevance scoring inaccuracies or unexpected ordering
- Search query optimization

**Example Tasks**:
- Implement BM25 scoring for message content
- Optimize title filtering for metadata-only queries
- Design combined filter execution strategy (title first, then keywords)
- Validate relevance scores against test fixtures
- Profile search performance on 10K conversation dataset
- Tune BM25 parameters (k1, b) for conversation search

**Performance Contracts**:
- Title-only search: <5s for 10K conversations (FR-444)
- Full keyword search: <30s for 1.6GB file (SC-001)
- Score normalization: 0.0 (no match) to 1.0 (perfect match)
- Results: Always sorted by relevance (descending)

---

## tdd-test-strategy-engineer

**Primary Responsibility**: TDD workflow enforcement, test design, and coverage analysis

**Mandatory for**:
- ALL test writing (unit, integration, contract, performance)
- Test-first workflow validation (RED-GREEN-REFACTOR cycle)
- Test fixture design and generation
- Contract test validation against FR specifications
- Performance benchmark design with pytest-benchmark
- Test coverage analysis and gap identification

**Key Principles**:
- ✅ **WRITE TESTS FIRST**: Implementation MUST NOT start before failing test (Constitution Principle III)
- ✅ Test pyramid distribution: 70% unit, 20% integration, 5% contract, 5% e2e
- ✅ Contract tests validate FR requirements exactly (FR-215-221)
- ✅ Performance tests with memory/time constraints (SC-001, SC-005)
- ✅ Fixture reusability (sample_export.json, generate_large_export.py)
- ✅ Graceful degradation tests (malformed_*.json fixtures)

**Invocation Patterns**:
- **BEFORE implementing any feature** (TDD enforcement)
- User says "test", "TDD", "coverage", "benchmark"
- After feature completion (coverage gap analysis)
- Performance regression detection
- Contract test validation

**Example Tasks**:
- Design contract tests for search FR-317-332 requirements
- Create performance benchmarks for 10K conversation parsing
- Review test coverage for OpenAIAdapter implementation
- Design malformed data test fixtures for graceful degradation
- Validate RED-GREEN-REFACTOR cycle adherence
- Create integration tests for CLI commands

**TDD Cycle Enforcement**:
1. **RED**: Write failing test that defines desired behavior
2. **GREEN**: Write minimal code to make test pass
3. **REFACTOR**: Improve code quality while keeping tests green
4. Reject any implementation-before-tests approach

**Test Design Checklist**:
- [ ] Tests written BEFORE implementation
- [ ] Tests verify acceptance criteria from spec
- [ ] Test names clearly describe behavior (Given-When-Then)
- [ ] Fixtures are documented and reusable
- [ ] Contract tests match FR specifications exactly
- [ ] Performance tests have memory/time thresholds
- [ ] Coverage >80% for critical paths

---

## python-strict-typing-enforcer

**Primary Responsibility**: mypy --strict compliance, type hint correctness, and type system design

**Mandatory for**:
- ALL Python code changes (no exceptions)
- Type hint validation and correction
- Generic type parameter design (TypeVar, Protocol)
- Forward reference resolution (from __future__ import annotations)
- Return type annotations and variable type declarations
- Resolving mypy errors in CI/CD pipeline

**Key Principles**:
- ✅ **ZERO MYPY ERRORS**: mypy --strict must pass with no issues (Constitution Principle VI)
- ✅ Explicit type annotations for all variables and function signatures
- ✅ No Any types except when unavoidable (use protocols or generics instead)
- ✅ Proper use of Optional, Union, Literal for type precision
- ✅ Collection type annotations (list[Message], dict[str, Any])
- ✅ Forward references via `from __future__ import annotations`

**Invocation Patterns**:
- **ANY Python code change** (automatic enforcement)
- mypy errors in pre-commit checks or CI
- Type system design decisions (Protocol vs ABC)
- Generic/protocol implementation
- Circular import resolution with type hints

**Example Tasks**:
- Fix mypy --strict errors in conversation.py
- Design TypeVar bounds for ConversationProvider protocol
- Review function signatures for type completeness
- Resolve circular import issues with forward references
- Add explicit type annotations to iterator/generator patterns
- Validate protocol compliance with runtime_checkable

**Type Safety Checklist**:
- [ ] mypy --strict passes with zero errors
- [ ] All function signatures have type hints
- [ ] All variable assignments have type annotations
- [ ] No bare `Any` types (use Protocol/TypeVar instead)
- [ ] Collections specify contained types (list[T], dict[K, V])
- [ ] Optional/Union used correctly for nullable types
- [ ] Forward references resolved via __future__ import

---

## cli-ux-designer

**Primary Responsibility**: Typer CLI design, Rich output formatting, and terminal UX

**Mandatory for**:
- ALL CLI command structure and naming
- Rich console output (tables, progress bars, syntax highlighting)
- Help text and command documentation
- stdout/stderr separation (FR-428)
- Exit code design (FR-429: 0=success, 1=error, 2=usage)
- Progress indicator implementation (FR-021)

**Key Principles**:
- ✅ CLI wraps library, never contains business logic (Constitution Principle I)
- ✅ stdout for results, stderr for progress/errors (FR-291-293)
- ✅ JSON output via --json flag for machine-readability (FR-301-303)
- ✅ Human-readable default output with Rich tables (FR-304-306)
- ✅ Pipeline-friendly: composable with jq, xargs (FR-307-309)
- ✅ Consistent exit codes (FR-296-300)

**Invocation Patterns**:
- User says "CLI", "command", "terminal output"
- Implementing new CLI commands (list, search, export)
- Rich formatting issues or table display
- Help text design and discoverability
- Progress indicator design for long operations

**Example Tasks**:
- Design `search` command interface with filters
- Implement Rich table formatter for search results
- Design progress bar for large file parsing (>2 seconds)
- Validate stdout/stderr separation for pipeline composition
- Create help text with usage examples
- Design --json output schema for machine consumption

**CLI Design Checklist**:
- [ ] Command name is intuitive and follows conventions
- [ ] Help text includes description and examples
- [ ] Results to stdout, progress/errors to stderr
- [ ] --json flag provides complete, structured output
- [ ] Exit codes follow contract (0/1/2)
- [ ] Progress indicators for operations >2 seconds
- [ ] Pipeline-friendly (supports jq, grep, xargs)

---

## performance-profiling-specialist

**Primary Responsibility**: Performance optimization, profiling, and benchmark validation

**Mandatory for**:
- Performance bottleneck identification and resolution
- Memory profiling (memory_profiler, tracemalloc)
- Time profiling (cProfile, pytest-benchmark)
- Algorithm complexity analysis
- Scalability validation (10K conversations, 50K messages)
- Performance regression detection in CI

**Key Principles**:
- ✅ Performance contract: 1.6GB search in <30s (SC-001)
- ✅ Memory constraint: 8GB RAM for 10K conversations (SC-005)
- ✅ Streaming efficiency validation (O(1) memory)
- ✅ pytest-benchmark for regression detection
- ✅ Data-driven optimization: profile before optimizing
- ✅ Performance tests in CI/CD pipeline

**Invocation Patterns**:
- User says "optimize", "performance", "slow", "bottleneck"
- Performance test failures or regressions
- Memory usage concerns or OOM errors
- Benchmark design for new features
- Scalability validation

**Example Tasks**:
- Profile ijson parsing for 1.6GB file
- Optimize BM25 scoring for 10K conversations
- Design memory benchmarks for streaming operations
- Identify search query bottlenecks with cProfile
- Validate memory usage stays <8GB for 10K conversations
- Create pytest-benchmark tests for critical paths

**Performance Contracts**:
- Search: <30s for 1.6GB file (SC-001)
- Memory: <8GB for 10K conversations (SC-005)
- Title search: <5s for 10K conversations (FR-444)
- Progress updates: Every 100 items or 100ms (FR-068-069)

---

## git-version-control

**Primary Responsibility**: All version control operations and commit crafting

**Mandatory for**:
- ALL commits (reviews changes, crafts messages)
- Branch creation and management
- Release preparation and tagging
- Conventional commit enforcement
- Changelog generation from commit history
- Pull request creation and description

**Key Rules**:
- ✅ Conventional commits enforced (feat:, fix:, docs:, refactor:, test:, perf:)
- ✅ Linear history required (no merge commits on main)
- ✅ Semantic versioning for releases (MAJOR.MINOR.PATCH)
- ✅ Meaningful commit messages focusing on "why" not "what"
- ✅ Never skip hooks (--no-verify) unless explicitly requested

**Invocation Patterns**:
- User says "commit", "ready to commit", "create PR"
- User says "create branch", "new feature branch"
- User says "prepare release", "version bump"
- After completing feature implementation (proactive)

**Example Tasks**:
- Review staged changes and craft conventional commit message
- Create feature branch for Claude adapter implementation
- Generate changelog from commit history since last release
- Prepare v0.1.0 release with semantic versioning
- Validate commit message follows conventional commits
- Create pull request with comprehensive description

**Commit Message Format**:
```
<type>: <subject>

<body>

```

**Types**: feat, fix, docs, style, refactor, test, perf, chore, ci, build

---

## technical-documentation-specialist

**Primary Responsibility**: API documentation, user guides, and inline documentation

**Mandatory for**:
- Docstring creation and updates (all public APIs)
- README and user guide updates
- API reference documentation
- Quickstart tutorial creation
- Release notes and changelog
- Library integration examples (cognivault use case)

**Key Principles**:
- ✅ Clear, concise language (avoid jargon)
- ✅ Code examples for all features
- ✅ Progressive disclosure (basics first, advanced later)
- ✅ Scannable structure (headers, bullets, code blocks)
- ✅ Keep docs in sync with code changes
- ✅ Library-first examples (show programmatic API)

**Invocation Patterns**:
- User says "docs", "README", "documentation"
- After feature completion (proactive documentation)
- API changes requiring documentation updates
- User guide creation or refinement

**Example Tasks**:
- Write user guide for search command
- Update README with library usage examples
- Add docstrings to ConversationProvider protocol
- Create quickstart tutorial for cognivault integration
- Document CLI commands with examples
- Write API reference for OpenAIAdapter

**Documentation Checklist**:
- [ ] Language is clear and jargon-free
- [ ] Examples provided for key concepts
- [ ] Structure is scannable (headers, bullets)
- [ ] Code examples are tested and accurate
- [ ] Library API documented before CLI
- [ ] Links to related docs included

---

## software-architect

**Primary Responsibility**: System design, architectural decisions, and constitution compliance

**Mandatory for**:
- New feature architecture planning (before Phase 1 design)
- Major refactoring decisions
- Protocol/interface design changes
- Dependency introduction or removal decisions
- Module structure and organization changes
- Performance vs complexity trade-off analysis

**Key Principles**:
- ✅ Enforce library-first: CLI is thin wrapper over library API (Principle I)
- ✅ Single Responsibility Principle per module
- ✅ Protocol stability: changes must be backwards-compatible
- ✅ Prevent circular dependencies (models ← protocols ← adapters)
- ✅ Design for extensibility WITHOUT over-engineering (Principle V)
- ✅ Constitution compliance on all architectural decisions

**Invocation Patterns**:
- User says "design", "architecture", "how should we structure"
- Before implementing major features (User Stories)
- When adding new provider adapters
- When considering caching, indexing, or database introduction
- Module structure or boundary changes

**Example Tasks**:
- Design search ranking pluggability strategy
- Review module organization for Claude adapter addition
- Decide: in-memory index vs streaming for get_conversation_by_id()
- Plan schema versioning strategy for multi-provider compatibility
- Design export functionality architecture (markdown, future PDF/CSV)
- Review protocol changes for backwards compatibility

**Architecture Review Checklist**:
- [ ] Respects all 8 constitution principles
- [ ] Module has single, clear responsibility
- [ ] No circular dependencies introduced
- [ ] Public API is minimal and well-defined
- [ ] Design allows for testing and mocking
- [ ] Extensible for future providers without breaking changes
- [ ] Memory efficiency maintained (streaming, not loading)
- [ ] Library API remains usable for external integrations

---

## Agent Coordination

**Primary Coordinator**: Claude Code (main assistant)

### Coordination Rules

1. **Parse User Request**: Identify all relevant domains and required agents
2. **Invoke Agents IN PARALLEL**: When domains are independent and no sequential dependencies exist
3. **Invoke Sequentially**: When one agent's output informs another's work
4. **Synthesize Recommendations**: Resolve conflicts, create unified implementation plan
5. **Implement with Guidance**: Follow agent recommendations during implementation
6. **Final Review by Agents**: Quality gates before commit (tests, types, performance)

### Multi-Agent Workflow Examples

#### Example 1: "Implement OpenAI search functionality"

**Agents Required** (invoke in parallel):
- `tdd-test-strategy-engineer`: Design contract tests for FR-317-332 FIRST
- `software-architect`: Review search architecture against constitution principles
- `streaming-parser-specialist`: Design ijson event parsing for search iteration
- `search-ranking-engineer`: Implement BM25 algorithm and relevance scoring
- `pydantic-data-modeling-expert`: Design SearchQuery and SearchResult models
- `python-strict-typing-enforcer`: Ensure mypy --strict compliance throughout

**Workflow**:
1. TDD agent designs failing tests based on FR-317-332
2. All other agents work in parallel on their domains
3. Implementation follows test-driven approach
4. Final review: types, performance, test coverage

---

#### Example 2: "Add support for Claude conversation exports"

**Agents Required** (sequential then parallel):

**Phase 1 - Architecture** (sequential):
1. `software-architect`: Design overall Claude adapter strategy
2. `multi-provider-adapter-architect`: Design protocol compliance and schema mapping

**Phase 2 - Implementation** (parallel):
- `pydantic-data-modeling-expert`: Create ClaudeMessage and ClaudeConversation models
- `streaming-parser-specialist`: Implement Claude JSON format parsing with ijson
- `tdd-test-strategy-engineer`: Design adapter contract tests
- `python-strict-typing-enforcer`: Ensure type safety throughout

**Phase 3 - Integration** (sequential):
- `performance-profiling-specialist`: Validate memory/time contracts
- `technical-documentation-specialist`: Document Claude adapter usage

---

#### Example 3: "Ready to commit search feature"

**Agents Required** (sequential quality gates):

1. `tdd-test-strategy-engineer`: Validate test coverage meets thresholds
   - Contract tests pass and validate all FRs
   - Unit test coverage >80% for critical paths
   - Performance benchmarks pass

2. `python-strict-typing-enforcer`: Validate mypy --strict compliance
   - Zero type errors
   - All public APIs have type hints
   - Generic types properly bounded

3. `performance-profiling-specialist`: Validate performance contracts
   - 1.6GB search completes in <30s
   - Memory usage <8GB for 10K conversations
   - No performance regressions detected

4. `git-version-control`: Craft commit message and commit
   - Review all staged changes
   - Create conventional commit message

---

#### Example 4: "Implement CLI search command"

**Agents Required** (parallel then sequential):

**Phase 1 - Design** (parallel):
- `software-architect`: Ensure CLI wraps library (not vice versa)
- `cli-ux-designer`: Design command interface, flags, help text
- `tdd-test-strategy-engineer`: Design CLI contract tests

**Phase 2 - Implementation** (parallel):
- `cli-ux-designer`: Implement Rich output formatting
- `python-strict-typing-enforcer`: Ensure type safety
- `technical-documentation-specialist`: Write help text and examples

**Phase 3 - Validation** (sequential):
- Validate stdout/stderr separation
- Validate exit codes (0/1/2)
- Validate --json output schema
- Test pipeline composition (jq, xargs)

---

#### Example 5: "Optimize search performance for large files"

**Agents Required** (sequential):

1. `performance-profiling-specialist`: Profile current implementation
   - Identify bottlenecks with cProfile
   - Measure memory usage with tracemalloc
   - Establish baseline metrics

2. `software-architect`: Review optimization strategy
   - Evaluate indexing vs streaming trade-offs
   - Assess impact on constitution principles
   - Design optimization approach

3. **Then in parallel**:
   - `streaming-parser-specialist`: Optimize ijson parsing patterns
   - `search-ranking-engineer`: Optimize BM25 scoring algorithm
   - `tdd-test-strategy-engineer`: Add performance regression tests

4. `performance-profiling-specialist`: Validate improvements
   - Measure new performance metrics
   - Ensure memory contracts maintained
   - Confirm no regressions

---

### Coordination Patterns

#### Pattern 1: Architecture-First

Used for: Major features, new provider adapters, significant refactoring

```
software-architect
    ↓
multi-provider-adapter-architect OR other domain architect
    ↓
[parallel domain experts]
```

#### Pattern 2: TDD-First

Used for: All feature implementation

```
tdd-test-strategy-engineer (design failing tests)
    ↓
[parallel implementation by domain experts]
    ↓
[sequential quality gates before commit]
```

#### Pattern 3: Quality Gates

Used for: Before every commit

```
tdd-test-strategy-engineer (coverage)
    ↓
python-strict-typing-enforcer (mypy --strict)
    ↓
performance-profiling-specialist (benchmarks)
    ↓
git-version-control (commit)
```

---

## Quick Reference Table

| Task Type | Required Agents | Invocation Order |
|-----------|----------------|------------------|
| **New provider adapter** | software-architect, multi-provider-adapter-architect, pydantic-data-modeling-expert, streaming-parser-specialist, tdd-test-strategy-engineer, python-strict-typing-enforcer | Sequential: architect → parallel: others |
| **Search implementation** | tdd-test-strategy-engineer, search-ranking-engineer, streaming-parser-specialist, pydantic-data-modeling-expert, python-strict-typing-enforcer | TDD first → parallel: others |
| **CLI command** | software-architect, cli-ux-designer, tdd-test-strategy-engineer, python-strict-typing-enforcer | Architect first → parallel: others |
| **Pydantic models** | pydantic-data-modeling-expert, python-strict-typing-enforcer, tdd-test-strategy-engineer | Parallel: modeling + typing, TDD validates |
| **Performance optimization** | performance-profiling-specialist, software-architect, streaming-parser-specialist, tdd-test-strategy-engineer | Sequential: profile → architect → optimize → validate |
| **Commit/PR** | tdd-test-strategy-engineer, python-strict-typing-enforcer, performance-profiling-specialist, git-version-control | Sequential quality gates |
| **Documentation** | technical-documentation-specialist, software-architect (for API design) | Parallel, architect reviews API docs |
| **Type errors** | python-strict-typing-enforcer | Standalone |
| **Architecture decisions** | software-architect, [relevant domain experts] | Architect first, then domain experts |

---

## Agent Hierarchy & Decision Authority

### Strategic Layer (Constitution & Architecture)
- **software-architect**: Final authority on architecture decisions, constitution compliance
  - Delegates implementation details to domain architects
  - Resolves conflicts between domain experts
  - Ensures multi-agent coordination aligns with principles

### Domain Layer (Specialized Expertise)
- **multi-provider-adapter-architect**: Protocol design authority
- **search-ranking-engineer**: Search algorithm authority
- **streaming-parser-specialist**: Parsing and memory efficiency authority
- **pydantic-data-modeling-expert**: Data model design authority
- **cli-ux-designer**: Terminal UX authority

### Quality Layer (Enforcement & Validation)
- **tdd-test-strategy-engineer**: Test strategy and TDD enforcement
- **python-strict-typing-enforcer**: Type safety enforcement (no exceptions)
- **performance-profiling-specialist**: Performance contract validation

### Operations Layer (Process & Documentation)
- **git-version-control**: Version control operations
- **technical-documentation-specialist**: Documentation

### Conflict Resolution

When agents disagree:
1. **software-architect** reviews constitution principles
2. Architect makes final decision based on:
   - Constitution compliance
   - Long-term maintainability
   - Library-first principle
   - Simplicity vs performance trade-offs

---

## Constitution Principles Reference

All agents must respect these principles:

1. **Library-First Architecture**: CLI wraps library, not vice versa
2. **CLI Interface Contract**: stdout for results, stderr for errors
3. **Test-Driven Development**: Tests written first, must fail before implementation
4. **Observability & Debuggability**: JSON structured logs, contextual fields
5. **Simplicity & YAGNI**: Simplest solution that meets requirements
6. **Strict Typing Mandatory**: mypy --strict compliance, no exceptions
7. **Multi-Provider Adapter Pattern**: Protocol-based, stateless adapters
8. **Memory Efficiency & Streaming**: O(1) memory, streaming for large files

When in doubt, consult `software-architect` for constitution interpretation.