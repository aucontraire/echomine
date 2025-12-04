# Implementation Plan: Advanced Search Enhancement Package

**Branch**: `002-advanced-search` | **Date**: 2025-12-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-advanced-search/spec.md`

## Summary

Enhance echomine's search functionality with five features: exact phrase matching (bypass tokenizer), boolean AND/OR match mode, exclude keywords filtering, message role filtering, and search result snippets. All features extend existing `SearchQuery` and `SearchResult` Pydantic models with optional fields, maintaining 100% backward compatibility. Implementation follows library-first pattern with CLI wrapping library functionality.

## Technical Context

**Language/Version**: Python 3.12+ (existing stack, mypy --strict compliant)
**Primary Dependencies**:
- Pydantic v2 (model extensions)
- BM25Scorer (existing, `src/echomine/search/ranking.py`)
- Typer (CLI framework)
- Rich (terminal output formatting)
- ijson (streaming JSON parser - must preserve O(1) memory)

**Storage**: File system only (JSON exports, no database)
**Testing**: pytest, pytest-cov, pytest-mock, pytest-benchmark
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single project (library + CLI)

**Performance Goals**:
- SC-003: Search 1.6GB file in <30 seconds (existing performance maintained)
- SC-006: Memory usage remains constant regardless of file size
- Estimated overhead: <5% increase in search time

**Constraints**:
- All new fields optional with sensible defaults (FR-027)
- Backward compatibility: existing queries work unchanged (FR-028)
- Streaming architecture must be preserved (Constitution Principle VIII)

**Scale/Scope**:
- 10K conversations, 50K messages per export file
- 8GB RAM limit for processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Library-First Architecture ✅ PASS
- All 5 features implemented in library layer first (`src/echomine/models/`, `src/echomine/adapters/`)
- CLI (`src/echomine/cli/`) wraps library with new flags
- Library API usable independently of CLI

### II. CLI Interface Contract ✅ PASS
- New flags: `--phrase`, `--match-mode`, `--exclude`, `--role`
- Results to stdout (JSON or human-readable), errors to stderr
- Exit codes: 0 (success), 1 (error), 2 (usage error)
- Composable with Unix pipelines

### III. Test-Driven Development ✅ PASS
- Tests written first for each feature (unit, integration, contract)
- TDD cycle: RED → GREEN → REFACTOR
- Coverage required before implementation proceeds

### IV. Observability & Debuggability ✅ PASS
- Structured logging for search operations
- Snippet extraction logs malformed content fallbacks
- Error context includes query parameters

### V. Simplicity & YAGNI ✅ PASS
- Simple substring matching for phrases (no regex, no fuzzy)
- No new dependencies required
- Reuse existing BM25Scorer tokenization for exclusion

### VI. Strict Typing Mandatory ✅ PASS
- All new fields strictly typed with Pydantic Field constraints
- `match_mode: Literal["all", "any"]`
- `role_filter: Literal["user", "assistant", "system"] | None`
- mypy --strict must pass before commit

### VII. Multi-Provider Adapter Pattern ✅ PASS
- Changes to `SearchQuery` and `SearchResult` apply to all providers
- `ConversationProvider` protocol unchanged
- OpenAI adapter modified, pattern replicable for future adapters

### VIII. Memory Efficiency & Streaming ✅ PASS
- No additional memory for phrase/role/exclude filtering
- Snippets extracted from already-loaded conversations (post-scoring)
- O(N) memory where N = matching conversations (existing behavior)

**GATE RESULT**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/002-advanced-search/
├── plan.md              # This file
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (technical decisions)
├── data-model.md        # Phase 1 output (Pydantic model changes)
├── quickstart.md        # Phase 1 output (usage examples)
├── contracts/           # Phase 1 output (CLI contract tests)
│   └── cli_search.md    # CLI interface contract for new flags
├── checklists/
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/echomine/
├── models/
│   └── search.py           # SearchQuery + SearchResult extensions
├── adapters/
│   └── openai.py           # search() method modifications
├── search/
│   └── ranking.py          # BM25Scorer (existing, may add phrase scoring)
└── cli/
    ├── commands/
    │   └── search.py       # New CLI flags
    └── formatters.py       # Snippet column display

tests/
├── unit/
│   ├── models/
│   │   └── test_search.py  # SearchQuery/SearchResult field tests
│   └── adapters/
│       └── test_openai_search.py  # Feature-specific unit tests
├── integration/
│   └── test_search_end_to_end.py  # Combined feature tests
├── contract/
│   └── test_cli_search.py  # CLI flag contract tests
└── performance/
    └── test_search_performance.py  # SC-003, SC-006 benchmarks
```

**Structure Decision**: Single project structure (existing). No new directories required - all changes extend existing modules.

## Complexity Tracking

> No violations - all gates passed. Simple solutions selected for all features.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Phrase matching | Substring (not regex) | Simpler, faster, covers 95% use cases |
| Phrase scoring | Binary (1.0 or 0.0) | Avoids complex relevance calculations |
| Exclusion timing | Post-filter | Clear separation from scoring logic |
| Role filtering | Pre-corpus | FR-018 requirement, affects BM25 IDF correctly |

## Implementation Phases

### Phase 0: Research (resolve unknowns)
- Confirm phrase matching strategy (substring vs word boundaries)
- Confirm exclusion filter uses BM25 tokenization
- Validate memory impact of snippet extraction

### Phase 1: Design & Contracts
- Extend `SearchQuery` model with new optional fields
- Extend `SearchResult` model with `snippet` field
- Define CLI flag contract for new parameters
- Create usage examples in quickstart.md

### Phase 2: Task Generation (/speckit.tasks)
- Break down into ordered implementation tasks
- Define test-first approach for each task
- Identify dependencies between tasks

### Phase 3-8: Implementation (via /speckit.implement)
- Phase 3: Models (SearchQuery, SearchResult)
- Phase 4: Phrase Matching
- Phase 5: Boolean Match Mode
- Phase 6: Exclude Keywords
- Phase 7: Role Filtering
- Phase 8: Snippet Extraction
- Phase 9: CLI Integration
- Phase 10: Performance Validation

## Search Pipeline Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                      Search Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. STREAM CONVERSATIONS (existing)                              │
│     └─→ ijson streaming parser                                   │
│                                                                  │
│  2. ROLE FILTER (NEW - FR-018)                    ◄── PRE-CORPUS │
│     └─→ Filter messages by role before corpus text               │
│                                                                  │
│  3. BUILD CORPUS TEXT (existing)                                 │
│     └─→ title + filtered messages                                │
│                                                                  │
│  4. BM25 SCORING (existing)                                      │
│     └─→ Score keywords against corpus                            │
│                                                                  │
│  5. PHRASE SCORING (NEW - FR-001-006)          ◄── DURING SCORE  │
│     └─→ Binary score: 1.0 if phrase in text, else 0.0            │
│                                                                  │
│  6. BOOLEAN MATCH MODE (NEW - FR-007-011)      ◄── DURING SCORE  │
│     └─→ If "all": require ALL keywords+phrases present           │
│     └─→ If "any": require ANY keyword/phrase match (default)     │
│                                                                  │
│  7. EXCLUSION FILTER (NEW - FR-012-016)        ◄── POST-FILTER   │
│     └─→ Remove conversations containing excluded terms           │
│                                                                  │
│  8. SORT BY SCORE (existing)                                     │
│     └─→ Descending relevance order                               │
│                                                                  │
│  9. APPLY LIMIT (existing)                                       │
│     └─→ Return top N results                                     │
│                                                                  │
│ 10. SNIPPET EXTRACTION (NEW - FR-021-025)      ◄── POST-LIMIT    │
│     └─→ Extract 100-char snippet from first matched message      │
│                                                                  │
│ 11. YIELD SEARCH RESULTS (existing)                              │
│     └─→ Return SearchResult with snippet                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance regression | SC-003 failure | Benchmark before merge, <5% overhead target |
| Memory increase | SC-006 failure | Profile with 1GB+ files, snippet ~100 bytes/result |
| Backward compat break | FR-028 failure | All fields optional, contract tests verify |
| Phrase false positives | User confusion | Document substring behavior, add word-boundary later if needed |
| Empty role filter results | User frustration | Zero-results guidance in CLI, document edge case |

## Next Steps

1. Generate `research.md` with technical decisions
2. Generate `data-model.md` with Pydantic model changes
3. Generate `contracts/cli_search.md` with CLI flag contract
4. Generate `quickstart.md` with usage examples
5. Run `/speckit.tasks` to create task breakdown
