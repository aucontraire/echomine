# Implementation Plan: Baseline Enhancement Package v1.2.0

**Branch**: `003-baseline-enhancements` | **Date**: 2025-12-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-baseline-enhancements/spec.md`

## Summary

Baseline Enhancement Package v1.2.0 adds message count filtering, export/conversation statistics, message listing, rich markdown export (YAML frontmatter + message IDs), Rich CLI formatting (tables, colors, progress bars), sort options, and CSV export. All features follow library-first architecture with O(1) streaming and mypy --strict compliance.

## Technical Context

**Language/Version**: Python 3.12+ (existing stack, mypy --strict compliant)
**Primary Dependencies**: Pydantic v2.6+, ijson 3.2+, typer 0.9+, rich 13.0+, structlog 23.0+
**Storage**: File system only (JSON exports, no database)
**Testing**: pytest 7.4+ with pytest-cov, pytest-mock, pytest-benchmark
**Target Platform**: Linux/macOS/Windows (cross-platform CLI)
**Project Type**: Single project (library + CLI wrapper)
**Performance Goals**:
- Statistics: <5s for 10K conversations
- Search with message count filter: O(N) streaming
- CSV export: streaming writer (constant memory)
**Constraints**:
- O(1) memory usage for all operations (streaming architecture)
- <1GB memory for 10K conversations on 8GB RAM
**Scale/Scope**: 10K conversations, 50K messages, 1GB+ export files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Library-First Architecture
- **Status**: PASS
- **Compliance**: All features have corresponding library APIs (US9, US10)
  - `SearchQuery.min_messages`, `SearchQuery.max_messages` (US9, FR-004)
  - `calculate_statistics(file_path) -> ExportStatistics` (US10, FR-016)
  - `calculate_conversation_statistics(conversation) -> ConversationStatistics` (US10, FR-022)
  - `CSVExporter.export_conversations()`, `CSVExporter.export_messages()` (FR-055)
- CLI wraps library (never the reverse)

### Principle II: CLI Interface Contract
- **Status**: PASS
- **Compliance**:
  - Results to stdout (JSON via --json, human-readable by default)
  - Progress and errors to stderr
  - Exit codes: 0 (success), 1 (operational error), 2 (usage error)
  - Pipeline-friendly with --format csv

### Principle III: Test-Driven Development
- **Status**: PASS (enforced during implementation)
- **Compliance**: TDD workflow will be followed - tests before implementation

### Principle IV: Observability & Debuggability
- **Status**: PASS
- **Compliance**: structlog for JSON structured logging, progress callbacks

### Principle V: Simplicity & YAGNI
- **Status**: PASS
- **Compliance**: Features limited to spec requirements, no speculative abstractions

### Principle VI: Strict Typing Mandatory
- **Status**: PASS
- **Compliance**: All new models use Pydantic v2 with frozen=True, mypy --strict

### Principle VII: Multi-Provider Adapter Pattern
- **Status**: PASS
- **Compliance**: Statistics and filtering work via adapter pattern (OpenAIAdapter)

### Principle VIII: Memory Efficiency & Streaming
- **Status**: PASS
- **Compliance**:
  - Statistics calculated via streaming (O(1) memory)
  - Message count filtering in streaming loop
  - CSV export uses streaming writer

**Gate Result**: PASS - All constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/003-baseline-enhancements/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli_spec.md      # CLI command contracts
│   └── library_api.md   # Library API contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/echomine/
├── models/
│   ├── search.py        # MODIFY: Add min_messages, max_messages, sort_by, sort_order
│   └── statistics.py    # NEW: ExportStatistics, ConversationStatistics, RoleCount models
├── statistics.py        # NEW: calculate_statistics(), calculate_conversation_statistics() functions
├── adapters/
│   └── openai.py        # MODIFY: Add calculate_statistics(), filter by message count
├── export/
│   ├── markdown.py      # MODIFY: Add YAML frontmatter, message IDs
│   └── csv.py           # NEW: CSVExporter class
├── cli/
│   ├── app.py           # MODIFY: Register stats command
│   ├── formatters.py    # MODIFY: Rich table formatting, color-coded scores
│   └── commands/
│       ├── search.py    # MODIFY: Add --min-messages, --max-messages, --sort, --order, --format csv
│       ├── list.py      # MODIFY: Rich table formatting, --format csv
│       ├── stats.py     # NEW: stats command with --conversation option
│       └── get.py       # MODIFY: Add `get messages` subcommand

tests/
├── unit/
│   ├── test_statistics.py      # NEW: ExportStatistics, ConversationStatistics
│   ├── test_search_filters.py  # MODIFY: message count filter tests
│   ├── test_csv_exporter.py    # NEW: CSV export tests
│   └── test_markdown_export.py # MODIFY: frontmatter tests
├── integration/
│   └── test_cli_stats.py       # NEW: stats command integration
├── contract/
│   └── test_fr_baseline.py     # NEW: FR-001 to FR-060 contract tests
└── performance/
    └── test_stats_performance.py  # NEW: SC-002 benchmark
```

**Structure Decision**: Single project structure maintained. New files for statistics and CSV export, modifications to existing search and CLI modules.

## Complexity Tracking

> No violations identified - design follows simplicity principles

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | - | - |

---

## Post-Design Constitution Re-evaluation

*Completed after Phase 1 design artifacts generated.*

### Design Artifacts Generated

| Artifact | Location | Status |
|----------|----------|--------|
| research.md | [research.md](./research.md) | Complete |
| data-model.md | [data-model.md](./data-model.md) | Complete |
| cli_spec.md | [contracts/cli_spec.md](./contracts/cli_spec.md) | Complete |
| library_api.md | [contracts/library_api.md](./contracts/library_api.md) | Complete |
| quickstart.md | [quickstart.md](./quickstart.md) | Complete |

### Constitution Re-check Results

| Principle | Pre-Design | Post-Design | Notes |
|-----------|------------|-------------|-------|
| I. Library-First | PASS | PASS | Library APIs defined in library_api.md |
| II. CLI Contract | PASS | PASS | CLI contract defined in cli_spec.md |
| III. TDD | PASS | PASS | Test structure defined in data-model.md |
| IV. Observability | PASS | PASS | structlog, progress callbacks designed |
| V. Simplicity | PASS | PASS | No complexity violations |
| VI. Strict Typing | PASS | PASS | All models in data-model.md use frozen=True |
| VII. Multi-Provider | PASS | PASS | Adapter pattern maintained |
| VIII. Memory Efficiency | PASS | PASS | Streaming patterns in research.md |

**Final Gate Result**: PASS - Ready for `/speckit.tasks`

---

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Follow TDD workflow for each task
3. Run pre-commit checks before commits
