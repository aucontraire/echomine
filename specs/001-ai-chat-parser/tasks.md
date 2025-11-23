# Tasks: Echomine AI Chat Parser

**Input**: Design documents from `/specs/001-ai-chat-parser/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Per the constitution, TDD is MANDATORY - tests MUST be written first and verified to fail before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project structure:
- Source: `src/echomine/`
- Tests: `tests/`
- Specs: `specs/001-ai-chat-parser/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [X] T001 Create project structure with src/echomine/ and tests/ directories
- [X] T002 Initialize Python 3.12+ project with pyproject.toml (poetry/setuptools)
- [X] T003 [P] Add core dependencies: pydantic v2, ijson, typer, rich, structlog, python-slugify, python-dateutil
- [X] T004 [P] Add development dependencies: pytest, pytest-cov, pytest-mock, pytest-benchmark, mypy, ruff
- [X] T005 [P] Configure mypy for strict type checking in pyproject.toml
- [X] T006 [P] Configure ruff for linting and formatting in pyproject.toml
- [X] T007 [P] Setup pre-commit hooks for mypy --strict and ruff
- [X] T008 Create src/echomine/__init__.py with public API exports
- [X] T009 Create tests/conftest.py with shared pytest fixtures

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Pydantic models, protocols, and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Pydantic Models (from data-model.md)

- [X] T010 [P] Create Message model in src/echomine/models/message.py with frozen=True, strict=True, Literal role, timezone validators
- [X] T011 [P] Create Conversation model in src/echomine/models/conversation.py with tree navigation methods (get_all_threads, get_thread, get_children)
- [X] T012 [P] Create SearchQuery model in src/echomine/models/search.py with keywords, title_filter, date_from, date_to, limit fields
- [X] T013 [P] Create SearchResult model in src/echomine/models/search.py with conversation, relevance_score fields
- [X] T014 Create src/echomine/models/__init__.py exporting all models

### Protocol Definitions (from contracts/)

- [X] T015 Create ConversationProvider protocol in src/echomine/models/protocols.py with stream_conversations, search, get_conversation_by_id signatures
- [X] T016 Define ProgressCallback and OnSkipCallback type aliases in src/echomine/models/protocols.py
- [X] T017 Define BaseConversation protocol interface in src/echomine/models/protocols.py

### Exception Hierarchy (per FR-286 to FR-290)

- [X] T018 [P] Create EchomineError base exception in src/echomine/exceptions.py
- [X] T019 [P] Create ParseError, ValidationError, SchemaVersionError in src/echomine/exceptions.py
- [X] T020 Create src/echomine/exceptions.py __all__ export

### Logging Infrastructure (per FR-028 to FR-032)

- [X] T021 Configure structlog for JSON logging in src/echomine/utils/logging.py with required fields (operation, file_name, conversation_id, timestamp, level)
- [X] T022 Create logging helpers for progress callbacks in src/echomine/utils/logging.py

### Test Fixtures

- [X] T023 [P] Create sample OpenAI export fixture (10 conversations, 50 messages) in tests/fixtures/sample_export.json
- [X] T024 [P] Create large OpenAI export fixture generator (1000+ conversations) in tests/fixtures/generate_large_export.py
- [X] T025 [P] Create malformed export fixtures (missing fields, invalid JSON) in tests/fixtures/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - List All Conversations (Priority: P0) 🎯 FOUNDATION

**Goal**: Enable basic discovery and browsing of conversations in export files

**Independent Test**: Load export file, run list command, verify all conversations displayed with metadata in chronological order

### Tests for [US0] (TDD - Write First!) ⚠️

> **CRITICAL: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US0] Integration test for list workflow in tests/integration/test_list_flow.py (end-to-end: file → parse → list → verify output)
- [X] T027 [P] [US0] CLI contract test for list command in tests/contract/test_cli_contract.py (verify stdout format, exit codes)
- [X] T028 [P] [US0] Performance test for listing 10K conversations in tests/performance/test_list_benchmark.py (verify <5s per FR-444, callback frequency ≥100 items per FR-069)

### Implementation for [US0]

#### Streaming Parser (Foundation for all commands)

- [X] T029 [P] [US0] Implement ijson streaming parser in src/echomine/parsers/streaming.py (parse conversations one-at-a-time, O(1) memory)
- [X] T030 [P] [US0] Add schema version detection in src/echomine/parsers/streaming.py (detect OpenAI export format per FR-080 to FR-084)
- [X] T031 [US0] Add graceful degradation for malformed entries in src/echomine/parsers/streaming.py (skip with WARNING, invoke on_skip callback per FR-281 to FR-285)

#### OpenAI Adapter - Stream Method

- [X] T032 [US0] Implement OpenAIAdapter.stream_conversations in src/echomine/adapters/openai.py (use streaming parser, yield Conversation objects)
- [X] T033 [US0] Add progress_callback support in OpenAIAdapter.stream_conversations per FR-076, FR-077
- [X] T034 [US0] Add on_skip callback support in OpenAIAdapter.stream_conversations per FR-106, FR-107

#### List Command Implementation

- [X] T035 [US0] Create typer CLI app in src/echomine/cli/app.py with --help, --version outputs per FR-294, FR-432
- [X] T036 [US0] Implement `list` command in src/echomine/cli/list_cmd.py with --limit, --json flags per FR-438, FR-443
- [X] T037 [US0] Add conversation sorting by created_at descending in list_cmd.py per FR-440
- [X] T038 [US0] Implement human-readable formatter in src/echomine/cli/formatters.py (date, title, message count per FR-441)
- [X] T039 [US0] Implement JSON formatter for list in list_cmd.py (array of conversation metadata per FR-442)
- [X] T040 [US0] Add stdout routing for list results in list_cmd.py per FR-446
- [X] T041 [US0] Add "No conversations found" handling in list_cmd.py per FR-445

#### CLI Entry Point

- [X] T042 [US0] Create CLI entry point script in src/echomine/__main__.py
- [X] T043 [US0] Configure setuptools/poetry console_scripts entry point: `echomine = echomine.cli.app:main`

**Checkpoint**: US0 complete - basic list functionality enables discovery workflow

**Parallel Opportunities**: T026-T028 (tests), T029-T031 (parser), T035-T041 (CLI components) can run in parallel after foundation

---

## Phase 4: User Story 1 - Search Conversations by Keyword (Priority: P1) 🎯 MVP

**Goal**: Enable keyword search across AI conversation exports with relevance ranking

**Independent Test**: Provide sample export file, run keyword search via CLI, verify matching conversations returned with BM25 scores

### Tests for [US1] (TDD - Write First!) ⚠️

> **CRITICAL: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T044 [P] [US1] Contract test for ConversationProvider.search in tests/contract/test_provider_protocol.py (verify signature, relevance ranking, limit semantics)
- [X] T045 [P] [US1] Integration test for keyword search workflow in tests/integration/test_search_flow.py (end-to-end: file → parse → search → results)
- [X] T046 [P] [US1] CLI contract test for search stdout/stderr separation in tests/contract/test_cli_contract.py (verify results to stdout, progress to stderr per FR-291, FR-292)
- [X] T047 [P] [US1] Performance test for 1GB file search in tests/performance/test_search_benchmark.py (verify <30s per SC-001, callback frequency ≥100 items per FR-069)

### Implementation for [US1]

#### BM25 Search Engine (per FR-317 to FR-326)

- [X] T048 [P] [US1] Implement BM25Scorer in src/echomine/search/ranking.py with k1=1.5, b=0.75 parameters
- [X] T049 [P] [US1] Implement keyword search in src/echomine/search/keyword.py (case-insensitive matching, multi-keyword OR logic)
- [X] T050 [P] [US1] Implement title filtering in src/echomine/search/title.py (case-insensitive substring matching per FR-327 to FR-331)
- [X] T051 [US1] Implement OpenAIAdapter.search in src/echomine/adapters/openai.py (stream, score, rank, apply limit per FR-332 to FR-336)

#### CLI Search Command

- [X] T052 [US1] Implement `search` command in src/echomine/cli/search_cmd.py with --keywords, --title, --limit, --json, --quiet flags
- [X] T053 [US1] Add stdout/stderr routing in search_cmd.py (results to stdout, progress/errors to stderr per FR-291, FR-292, FR-293)
- [X] T054 [US1] Add JSON output format in search_cmd.py with schema {results, metadata} per FR-301 to FR-306
- [X] T055 [US1] Add exit code handling in search_cmd.py (0, 1, 2, 130 per FR-296 to FR-299)
- [X] T056 [US1] Add rich progress indicators in search_cmd.py (suppress with --quiet per FR-310)

#### Human-Readable Output (per FR-019)

- [X] T057 [P] [US1] Implement human-readable search results formatter in src/echomine/cli/formatters.py (table layout with title, date, score, excerpt)

**Checkpoint**: US1 complete - keyword search functional via CLI and library API

**Parallel Opportunities**: T044-T047 (tests), T048-T050 (search algorithms), T052-T057 (CLI components) can run in parallel

---

## Phase 5: User Story 2 - Programmatic Library Access (Priority: P2)

**Goal**: Ensure echomine is consumable as a Python library with full type safety and IDE support

**Independent Test**: Import library, create adapter, call search/list/export methods, verify type hints work in IDE

### Tests for [US2] (TDD - Write First!) ✅

- [x] T058 [P] [US2] Library API test in tests/integration/test_library_api.py (verify import, adapter creation, method calls) - 18 tests created, 70/75 passing
- [x] T059 [P] [US2] Type safety test in tests/unit/test_type_contracts.py (verify mypy --strict passes, no Any types in public API) - 13 tests created
- [x] T060 [P] [US2] Immutability test in tests/unit/models/test_conversation.py (verify frozen=True, model_copy works) - 18 tests created

### Implementation for [US2]

#### Library API Exports

- [x] T061 [US2] Update src/echomine/__init__.py to export OpenAIAdapter, Conversation, Message, SearchQuery, SearchResult
- [x] T062 [US2] Update src/echomine/__init__.py to export EchomineError, ParseError, ValidationError, SchemaVersionError
- [x] T063 [US2] Add __all__ and type stubs for public API in src/echomine/__init__.py

#### Documentation for Library Users

- [x] T064 [P] [US2] Create cognivault integration example in examples/cognivault_integration.py (demonstrate streaming ingestion per FR-337 to FR-341) - Also addresses CHK077 P1 gap
- [x] T065 [P] [US2] Create batch processing example in examples/batch_processing.py (demonstrate concurrent file processing per FR-361 to FR-365) - 656 lines: ThreadPoolExecutor, Rich multi-progress, thread-safe statistics, JSON output mode
- [x] T066 [P] [US2] Create rate limiting example in examples/rate_limiting.py (demonstrate consumer-side throttling per FR-342 to FR-345) - 612 lines: Token bucket algorithm, rate limiter with burst support, Rich progress with rate tracking

#### Library-Specific Tests

- [x] T067 [P] [US2] Add thread safety test in tests/unit/test_concurrency.py (verify adapter thread-safe, iterators not shared per FR-098 to FR-101) - 10 tests created
- [x] T068 [P] [US2] Add resource cleanup test in tests/unit/test_cleanup.py (verify file handles closed on early break, exceptions per FR-394 to FR-398) - 15 tests created

**Checkpoint**: US2 complete - library API fully documented and tested

**Parallel Opportunities**: T058-T060 (tests), T064-T066 (examples), T067-T068 (additional tests) can all run in parallel

---

## Phase 6: User Story 3 - Export Conversation to Markdown (Priority: P3)

**Goal**: Export specific conversations to markdown format for documentation

**Independent Test**: Select conversation by ID/title, export to markdown, verify file contains all messages with proper formatting

### Tests for [US3] (TDD - Write First!) ⚠️

- [ ] T069 [P] [US3] Integration test for export workflow in tests/integration/test_export_flow.py (end-to-end: file → search by ID → export → verify markdown)
- [ ] T070 [P] [US3] Unit test for markdown formatting in tests/unit/exporters/test_markdown.py (verify tree structure, code blocks, metadata)

### Implementation for [US3]

#### ID-Based Retrieval

- [ ] T071 [US3] Implement OpenAIAdapter.get_conversation_by_id in src/echomine/adapters/openai.py (stream until ID found, O(1) memory per FR-048)

#### Markdown Exporter

- [ ] T072 [P] [US3] Implement MarkdownExporter in src/echomine/exporters/markdown.py (render conversation metadata, messages, preserve tree structure)
- [ ] T073 [P] [US3] Add code block preservation in MarkdownExporter (preserve fencing and formatting)
- [ ] T074 [P] [US3] Add tree structure visualization in MarkdownExporter (indentation or markers for branches)

#### CLI Export Command

- [ ] T075 [US3] Implement `export` command in src/echomine/cli/export_cmd.py with --id, --title, --output flags
- [ ] T076 [US3] Add filename slugification in export_cmd.py using python-slugify
- [ ] T077 [US3] Add default output directory handling in export_cmd.py (current dir per FR-399, --output flag per FR-400)

#### Search-Then-Export Workflow (per FR-356 to FR-360)

- [ ] T078 [US3] Add conversation_id to JSON search results in search_cmd.py for piping to export command
- [ ] T079 [P] [US3] Create search-then-export example in examples/search_then_export.sh (demonstrate pipeline workflow)

**Checkpoint**: US3 complete - markdown export functional

**Parallel Opportunities**: T069-T070 (tests), T072-T074 (exporter components), T079 (example) can run in parallel

---

## Phase 7: User Story 4 - Filter Conversations by Date Range (Priority: P4)

**Goal**: Add temporal filtering to search functionality

**Independent Test**: Specify date range, run search, verify only conversations within range returned

### Tests for [US4] (TDD - Write First!) ⚠️

- [ ] T080 [P] [US4] Integration test for date filtering in tests/integration/test_date_filtering.py (verify date range logic)
- [ ] T081 [P] [US4] Unit test for date parsing in tests/unit/test_date_utils.py (verify ISO 8601 parsing per FR-404 to FR-408)

### Implementation for [US4]

#### Date Filtering Logic

- [ ] T082 [US4] Add date_from/date_to filtering in src/echomine/search/filters.py (support datetime, date, ISO 8601 strings per FR-404)
- [ ] T083 [US4] Add Pydantic validator for date parsing in SearchQuery model (auto-parse ISO 8601 strings per FR-405)
- [ ] T084 [US4] Update OpenAIAdapter.search to apply date filters in src/echomine/adapters/openai.py

#### CLI Date Flags

- [ ] T085 [US4] Add --from and --to flags to search command in src/echomine/cli/search_cmd.py
- [ ] T086 [US4] Add date format validation and error messages in search_cmd.py (clear error for invalid formats per acceptance scenario 3)

**Checkpoint**: US4 complete - date range filtering functional

**Parallel Opportunities**: T080-T081 (tests), T082-T083 (filtering logic) can run in parallel

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and quality assurance

### Documentation

- [ ] T087 [P] Create README.md with installation, quick start, CLI examples
- [ ] T088 [P] Create CONTRIBUTING.md with development setup, testing guidelines
- [ ] T089 [P] Create API documentation from docstrings using sphinx/mkdocs
- [ ] T090 [P] Add docstrings to all public classes and methods (sphinx format)

### Error Handling & Edge Cases

- [ ] T091 [P] Add comprehensive error messages for all exception types (actionable context per FR-039 to FR-041)
- [ ] T092 [P] Add validation for empty conversations (zero messages per FR-381)
- [ ] T093 [P] Add validation for missing required fields (id, title per FR-379, FR-380)
- [ ] T094 [P] Add handling for empty content messages (deleted messages per FR-384 to FR-388)

### CLI UX Enhancements

- [ ] T095 [P] Add --version output with library version in cli/app.py
- [ ] T096 [P] Add comprehensive --help documentation with examples per FR-432
- [ ] T097 [P] Add suggested next steps when search returns 0 results (user story 1, acceptance scenario 4)

### Performance Validation

- [ ] T098 Verify all performance tests pass (1.6GB in <30s, 10K conversations on 8GB RAM, list in <5s)
- [ ] T099 Run pytest-benchmark suite and document baseline metrics
- [ ] T100 Profile memory usage with tracemalloc during 1GB file processing

### Final Integration Testing

- [ ] T101 Run full test suite with pytest-cov (ensure >90% coverage per SC-002)
- [ ] T102 Run mypy --strict and ensure 0 errors
- [ ] T103 Run ruff check and format
- [ ] T104 Test CLI on sample ChatGPT export files (manual validation)
- [ ] T105 Verify all acceptance scenarios from spec.md pass

### Packaging

- [ ] T106 Configure pyproject.toml metadata (name, version, description, authors, license)
- [ ] T107 Add Python version constraint (>=3.12) in pyproject.toml
- [ ] T108 Test installation in clean virtual environment
- [ ] T109 Build distribution packages (wheel, sdist)

**Checkpoint**: Project ready for v1.0 release

---

## Dependencies & Execution Strategy

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation) → All user stories can run in parallel
                                       ↓
                              ┌────────┴────┬───────┬───────┬───────┐
                              │             │       │       │       │
                             US0           US1     US2     US3     US4
                            (P0)          (P1)    (P2)    (P3)    (P4)
                         Foundation       MVP   Library  Export   Dates
                              │             │       │       │       │
                              └────────┬────┴───┬───┴───┬───┴───┬───┘
                                       ↓        ↓       ↓       ↓
                                    Phase 8 (Polish)
```

**Key Insight**: US0 (List) is the foundation that enables discovery. Users first list conversations, then search/export specific ones.

### MVP Scope (Recommended)

**Minimum Viable Product**: User Stories 0 + 1
- Phases 1, 2, 3, 4 (T001-T057)
- Delivers: List conversations + keyword search
- Validates: Core architecture, performance, memory efficiency
- ~57 tasks

**MVP+**: Add User Story 2 (library API)
- Phases 1, 2, 3, 4, 5 (T001-T068)
- Enables: cognivault integration
- ~68 tasks

### Parallel Execution Examples

**Phase 2 Parallelization** (Foundation):
```bash
# All model files can be created in parallel
T010, T011, T012, T013 (models)
T018, T019 (exceptions)
T023, T024, T025 (fixtures)
```

**Phase 3 Parallelization** (US0 - List):
```bash
# Tests, parser, CLI components can run in parallel
T026-T028 (tests)
T029-T031 (parser)
T035-T041 (CLI)

# Then sequential integration:
T032-T034 (adapter integration) → T042-T043 (entry point)
```

**Phase 4 Parallelization** (US1 - Search):
```bash
# Tests, search algorithms, formatters can run in parallel
T044-T047 (tests)
T048-T050 (search algorithms)
T052-T057 (CLI)

# Integration happens after foundation
T051 (adapter search method)
```

**Phase 5 Parallelization** (US2 - Library):
```bash
# All tasks can run in parallel (documentation and examples)
T058-T068 (all tasks parallelizable)
```

---

## Implementation Strategy

### Week 1: Foundation
- Complete Phase 1 (Setup): T001-T009
- Complete Phase 2 (Foundation): T010-T025
- **Deliverable**: Project structure, models, protocols ready

### Week 2: List & Discovery (US0)
- Complete US0 Tests: T026-T028
- Complete US0 Implementation: T029-T043
- **Deliverable**: `echomine list` command functional

### Week 3: Search MVP (US1)
- Complete US1 Tests: T044-T047
- Complete US1 Implementation: T048-T057
- **Deliverable**: `echomine search` command functional (MVP COMPLETE)

### Week 4: Library API (US2)
- Complete US2: T058-T068
- **Deliverable**: cognivault integration ready

### Week 5+: Additional Features
- Complete US3 (Export): T069-T079
- Complete US4 (Dates): T080-T086
- Complete Polish: T087-T109

---

## Task Summary

- **Total Tasks**: 109 tasks (was 102 before adding US0)
- **Setup**: 9 tasks (T001-T009)
- **Foundation**: 16 tasks (T010-T025)
- **User Story 0 (P0)**: 18 tasks (T026-T043) - **NEW**
- **User Story 1 (P1)**: 14 tasks (T044-T057)
- **User Story 2 (P2)**: 11 tasks (T058-T068)
- **User Story 3 (P3)**: 11 tasks (T069-T079)
- **User Story 4 (P4)**: 7 tasks (T080-T086)
- **Polish**: 23 tasks (T087-T109)

**Parallel Opportunities**: ~42% of tasks can run in parallel (marked with [P])

**Independent Test Criteria**:
- **US0**: Run `echomine list conversations.json` and verify all conversations listed with metadata
- **US1**: Run keyword search via CLI, verify results with BM25 scores
- **US2**: Import library, create adapter, verify type hints
- **US3**: Export conversation to markdown, verify formatting
- **US4**: Filter by date range, verify temporal filtering

**TDD Checkpoints**: Every user story has dedicated test tasks that MUST pass before implementation tasks

**Critical Change**: Added User Story 0 (List) as P0 priority - this is the foundational discovery operation that should be implemented FIRST, enabling all other workflows.
