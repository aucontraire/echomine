# Implementation Plan: Echomine AI Chat Parser

**Branch**: `001-ai-chat-parser` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-chat-parser/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Echomine is a library-first tool for parsing AI conversation exports (initially ChatGPT) with search, filtering, and markdown export capabilities. Built to handle 1GB+ files via streaming JSON parsing, it provides both a programmatic Python API (primary use case for cognivault integration) and a CLI interface. Key technical approach: ijson for incremental parsing, Pydantic v2 for strict typing, typer+rich for CLI, and structlog for JSON-formatted observability.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- CLI: typer (framework), rich (output/progress)
- Data: pydantic v2 (models), ijson (streaming JSON parser)
- Utilities: python-slugify (filenames), python-dateutil (ISO 8601 dates)
- Logging: structlog (JSON structured logs)

**Storage**: File system only (local export files, no database)
**Testing**: pytest, pytest-cov, pytest-mock, pytest-benchmark (performance validation)
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single project (library + CLI)
**Performance Goals**:
- Search 1.6GB file in <30 seconds (SC-001)
- Process 10,000 conversations / 50,000 messages without crash on 8GB RAM (SC-005)
- Progress indicators for operations >2 seconds (FR-021)

**Constraints**:
- Memory: Never load entire file into memory (FR-003, Principle VIII)
- Type safety: mypy --strict compliance (Principle VI)
- TDD: Tests written first, must fail before implementation (Principle III)

**Scale/Scope**:
- MVP: OpenAI ChatGPT exports only
- Future: Multi-provider (Claude, Gemini via Principle VII adapter pattern)
- Test baseline: 10K conversations, 50K messages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Library-First Architecture ✅ PASS
- ✅ **Compliance**: Core parsing/search logic in `src/echomine/` as importable library
- ✅ **Compliance**: CLI in `src/echomine/cli/` consumes library (not vice versa)
- ✅ **Verification**: User Story 2 (P2) validates library API independently of CLI

### Principle II: CLI Interface Contract ✅ PASS
- ✅ **Compliance**: `search` command outputs to stdout (JSON via --json, human-readable by default)
- ✅ **Compliance**: Errors to stderr with non-zero exit codes (FR-022, FR-033)
- ✅ **Verification**: FR-017 through FR-022 specify CLI contract adherence

### Principle III: Test-Driven Development ✅ PASS
- ✅ **Compliance**: TDD workflow mandatory per constitution
- ✅ **Compliance**: Tasks template updated to enforce "write tests first, verify fail" (constitution amendment)
- ✅ **Verification**: All acceptance scenarios in spec are testable before implementation

### Principle IV: Observability & Debuggability ✅ PASS
- ✅ **Compliance**: structlog emits JSON logs with contextual fields (FR-028 through FR-032)
- ✅ **Compliance**: Text-based I/O (JSON exports human-inspectable)
- ✅ **Verification**: FR-029 specifies required log fields (operation, file_name, conversation_id, timestamp, level)

### Principle V: Simplicity & YAGNI ✅ PASS (with justification required)
- ⚠️ **Potential violation**: Using ijson instead of built-in json module
- ✅ **Justification**: Built-in json.load() would violate FR-003 (no full-file load) and Principle VIII (memory efficiency)
- ✅ **Decision**: ijson is the simplest solution meeting the memory constraint; no simpler alternative exists

### Principle VI: Strict Typing Mandatory ✅ PASS
- ✅ **Compliance**: mypy --strict in pre-commit hooks (tech stack)
- ✅ **Compliance**: Pydantic v2 for all structured data (Message, Conversation, SearchResult models per spec)
- ✅ **Compliance**: Protocol classes for ConversationProvider (tech standards)
- ✅ **Verification**: FR-023 through FR-027 mandate type hints and Pydantic models

### Principle VII: Multi-Provider Adapter Pattern ✅ PASS
- ✅ **Compliance**: OpenAIAdapter implements ConversationProvider protocol (FR-027)
- ✅ **Compliance**: Shared Pydantic models (Message, Conversation) across providers
- ✅ **Verification**: Architecture supports future Claude/Gemini adapters without changing core library

### Principle VIII: Memory Efficiency & Streaming ✅ PASS
- ✅ **Compliance**: ijson for streaming JSON parsing (FR-003)
- ✅ **Compliance**: Generator patterns (FR-026: iterator for large datasets)
- ✅ **Compliance**: Performance tests with memory/time contracts (pytest-benchmark)
- ✅ **Verification**: SC-005 validates 10K conversations on 8GB RAM; ijson ensures constant memory usage

**GATE RESULT**: ✅ ALL GATES PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-chat-parser/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
└── implementation/      # Detailed implementation plans per phase
    ├── README.md        # Index of implementation docs
    └── phase-6-export.md # Phase 6 detailed plan (export to markdown)
```

**Implementation Documentation**: For phases requiring detailed architecture decisions, testing strategies, or complex coordination, see `implementation/*.md` for phase-specific implementation guides.

### Source Code (repository root)

```text
# Single project structure (library + CLI)
src/echomine/
├── __init__.py              # Public API exports
├── models/                  # Pydantic data models
│   ├── __init__.py
│   ├── conversation.py      # Conversation, Message, Thread
│   ├── search.py            # SearchResult, SearchQuery
│   └── protocols.py         # ConversationProvider protocol
├── adapters/                # Provider-specific parsers
│   ├── __init__.py
│   ├── base.py              # Shared adapter utilities
│   └── openai.py            # OpenAIAdapter (ChatGPT format)
├── parsers/                 # Streaming JSON parsing logic
│   ├── __init__.py
│   └── streaming.py         # ijson-based incremental parser
├── search/                  # Search & filtering engine
│   ├── __init__.py
│   ├── keyword.py           # Full-text keyword search
│   ├── title.py             # Title-based filtering (metadata-only)
│   └── ranking.py           # TF-IDF relevance scoring
├── exporters/               # Markdown/JSON exporters
│   ├── __init__.py
│   ├── markdown.py          # Conversation -> markdown
│   └── json_export.py       # Conversation -> JSON
├── cli/                     # Typer CLI application
│   ├── __init__.py
│   ├── app.py               # Main typer app
│   ├── search_cmd.py        # `echomine search` command
│   └── export_cmd.py        # `echomine export` command
└── utils/                   # Shared utilities
    ├── __init__.py
    ├── logging.py           # structlog configuration
    ├── slugify.py           # Filename sanitization
    └── progress.py          # rich progress bars

tests/
├── conftest.py              # Shared pytest fixtures
├── contract/                # Interface contract tests
│   ├── test_provider_protocol.py    # ConversationProvider conformance
│   └── test_cli_contract.py         # CLI stdin/stdout/stderr
├── integration/             # End-to-end workflows
│   ├── test_search_flow.py          # Search 1GB file scenario
│   └── test_export_flow.py          # Export markdown scenario
├── unit/                    # Isolated component tests
│   ├── models/
│   ├── adapters/
│   ├── parsers/
│   ├── search/
│   └── exporters/
└── performance/             # pytest-benchmark tests
    ├── test_memory_usage.py         # SC-005 validation (10K convos)
    └── test_search_speed.py         # SC-001 validation (1.6GB <30s)

pyproject.toml               # Poetry dependencies
.pre-commit-config.yaml      # mypy --strict, ruff, black
README.md                    # Installation & quick start
```

**Structure Decision**: Single project structure selected because:
1. Library and CLI are tightly coupled (CLI is thin wrapper over library)
2. No frontend/backend separation needed (CLI only)
3. Simplifies dependency management and testing
4. Aligns with Principle I (library-first: CLI imports from `src/echomine/`)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ijson dependency (vs built-in json) | Memory constraint: Must handle 1GB+ files without full load (FR-003, Principle VIII) | json.load() loads entire file into memory, violating memory efficiency requirement and crashing on large files |

**Note**: This is the **only** complexity addition. All other dependencies (typer, pydantic, rich) are industry-standard tools that reduce complexity by providing battle-tested abstractions.

---

## Phase 0: Research & Technology Validation

**Status**: ⏳ Pending (generated after this plan is saved)

**Research Topics Identified**:
1. ijson streaming patterns for nested JSON (OpenAI export structure)
2. TF-IDF implementation for keyword ranking (FR-008)
3. Pydantic v2 frozen models for immutability (constitution requirement)
4. structlog best practices for CLI applications
5. pytest-benchmark memory profiling techniques

**Output**: `research.md` with decisions, rationales, and code examples

---

## Phase 1: Design & Contracts

**Status**: ⏳ Pending (generated after Phase 0 completes)

**Deliverables**:
1. **data-model.md**: Pydantic models for Conversation, Message, SearchResult, protocols
2. **contracts/**:
   - `conversation_provider_protocol.py` (ConversationProvider interface)
   - `cli_spec.md` (stdin/stdout contract for `search` and `export` commands)
3. **quickstart.md**: Library usage examples (cognivault integration pattern)

**Agent Context Update**: Run `.specify/scripts/bash/update-agent-context.sh claude` to add technology stack to agent context file

---

## Phase 2: Task Decomposition

**Status**: ⏳ Pending (run `/speckit.tasks` after Phase 1)

**Not included in this plan** - generated by separate `/speckit.tasks` command after design artifacts are complete.

---

## Next Steps

1. ✅ Save this plan
2. ⏳ Run Phase 0 research (auto-generated by this command)
3. ⏳ Run Phase 1 design (auto-generated by this command)
4. ⏳ Run `/speckit.tasks` to generate task breakdown

**Command**: This plan was generated by `/speckit.plan`. Phase 0 and Phase 1 artifacts will be generated automatically after this file is saved.
