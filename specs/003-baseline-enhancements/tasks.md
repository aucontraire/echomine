# Tasks: Baseline Enhancement Package v1.2.0

**Input**: Design documents from `/specs/003-baseline-enhancements/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, qa-review.md
**Branch**: `003-baseline-enhancements`

**Tests**: TDD is MANDATORY per constitution - tests MUST be written first and verified to fail before implementation begins. TDD edge cases from qa-review.md are integrated as explicit test scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US10)
- **[GATE]**: Verification task from qa-review.md VERIFY items
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Statistics and CSV export infrastructure that all stories depend on

- [x] T001 Create src/echomine/models/statistics.py module structure
- [x] T002 [P] Create src/echomine/export/csv.py module structure
- [x] T003 [P] Create src/echomine/cli/commands/stats.py module structure
- [x] T004 [P] Create src/echomine/cli/commands/get.py module structure (for get messages subcommand)
- [x] T005 [P] Create tests/unit/test_statistics.py test file
- [x] T006 [P] Create tests/unit/test_csv_exporter.py test file
- [x] T007 [P] Create tests/integration/test_cli_stats.py test file
- [x] T008 [P] Create tests/contract/test_fr_baseline.py for FR contract tests

**Checkpoint**: Module structure ready, test files created

---

## Phase 2: Foundational (Shared Models & Types)

**Purpose**: Core models that multiple user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Foundational Models

- [x] T009 [P] Implement ConversationSummary model in src/echomine/models/statistics.py (FR-011)
- [x] T010 [P] Implement RoleCount model in src/echomine/models/statistics.py (FR-020)
- [x] T011 [P] Implement ExportMetadata model in src/echomine/models/statistics.py (FR-031)
- [x] T012 Add SortField and SortOrder type aliases to src/echomine/models/search.py (FR-043)

### Foundational Tests (TDD - write first, verify fail)

- [x] T013 [P] Unit tests for ConversationSummary validation in tests/unit/test_statistics.py
- [x] T014 [P] Unit tests for RoleCount.total property in tests/unit/test_statistics.py
- [x] T015 [P] Unit tests for ExportMetadata immutability in tests/unit/test_statistics.py

**Checkpoint**: Foundation models ready - user story implementation can now begin

---

## Phase 3: User Story 9 - Library-First Message Count Filtering (Priority: P1) 🎯 MVP

**Goal**: Enable programmatic filtering of conversations by message count via SearchQuery model

**Independent Test**: Create SearchQuery with min_messages/max_messages and verify adapter.search() respects filters

**FR Reference**: FR-001-008

### Tests for US9 (TDD - write first, verify fail) ⚠️

- [x] T016 [P] [US9] Unit test: SearchQuery accepts min_messages field in tests/unit/test_search_filters.py
- [x] T017 [P] [US9] Unit test: SearchQuery accepts max_messages field in tests/unit/test_search_filters.py
- [x] T018 [P] [US9] Unit test: Validation rejects min_messages > max_messages (FR-005) in tests/unit/test_search_filters.py
- [x] T019 [P] [US9] Unit test: Validation rejects min_messages < 1 (FR-005) in tests/unit/test_search_filters.py
- [x] T020 [P] [US9] TDD Edge Case (CHK002): Test boundary min=1, max=1 returns conversations with exactly 1 message
- [x] T021 [P] [US9] TDD Edge Case (CHK003): Test min_messages == max_messages returns exact count match
- [x] T022 [P] [US9] Integration test: adapter.search() filters by message count in tests/integration/test_search_message_count.py
- [x] T023 [P] [US9] Contract test: FR-004 message count fields in tests/contract/test_fr_baseline.py

### Implementation for US9

- [x] T024 [US9] Add min_messages field to SearchQuery model in src/echomine/models/search.py (FR-004)
- [x] T025 [US9] Add max_messages field to SearchQuery model in src/echomine/models/search.py (FR-004)
- [x] T026 [US9] Add model_validator for min <= max constraint in src/echomine/models/search.py (FR-005)
- [x] T027 [US9] Implement message count filtering in OpenAIAdapter.search() in src/echomine/adapters/openai.py (FR-006)
- [x] T028 [US9] Add has_message_count_filter() helper method to SearchQuery

**Checkpoint**: Library-first message count filtering complete - CLI can wrap this

---

## Phase 4: User Story 1 - Filter Conversations by Message Count CLI (Priority: P1)

**Goal**: CLI users can filter search results using --min-messages and --max-messages flags

**Independent Test**: Run `echomine search export.json --min-messages 10` and verify all results have 10+ messages

**FR Reference**: FR-001-003, FR-007-008

### Tests for US1 (TDD - write first, verify fail) ⚠️

- [x] T029 [P] [US1] CLI integration test: --min-messages flag accepted in tests/integration/test_cli_search.py
- [x] T030 [P] [US1] CLI integration test: --max-messages flag accepted in tests/integration/test_cli_search.py
- [x] T031 [P] [US1] CLI integration test: Invalid bounds (min > max) exits with code 2 (FR-008)
- [x] T032 [P] [US1] Contract test: JSON output includes message_count field (FR-007)

### Implementation for US1

- [x] T033 [US1] Add --min-messages option to search command in src/echomine/cli/commands/search.py (FR-001)
- [x] T034 [US1] Add --max-messages option to search command in src/echomine/cli/commands/search.py (FR-002)
- [x] T035 [US1] Handle validation errors with exit code 2 in src/echomine/cli/commands/search.py (FR-008)
- [x] T036 [US1] Ensure message_count included in JSON output in src/echomine/cli/formatters.py (FR-007)

**Checkpoint**: Message count filtering available via CLI

---

## Phase 5: User Story 10 - Library-First Statistics API (Priority: P1)

**Goal**: Provide calculate_statistics() and calculate_conversation_statistics() library functions

**Independent Test**: Call calculate_statistics(path) and verify ExportStatistics contains all required fields

**FR Reference**: FR-016-017, FR-022-023

### Tests for US10 (TDD - write first, verify fail) ⚠️

- [x] T037 [P] [US10] Unit test: ExportStatistics model validates all required fields in tests/unit/test_statistics.py
- [x] T038 [P] [US10] Unit test: ConversationStatistics model validates all required fields in tests/unit/test_statistics.py
- [x] T039 [P] [US10] Unit test: calculate_statistics() returns ExportStatistics in tests/unit/test_statistics.py
- [x] T040 [P] [US10] Unit test: calculate_conversation_statistics() returns ConversationStatistics in tests/unit/test_statistics.py
- [x] T041 [P] [US10] TDD Edge Case (CHK007): Empty export file returns zeros in ExportStatistics
- [x] T042 [P] [US10] TDD Edge Case (CHK010): Export with ALL malformed conversations returns zeros with skipped_count
- [x] T043 [P] [US10] TDD Edge Case (CHK015): Conversation with 1 message has average_gap_seconds = None
- [x] T044 [P] [US10] TDD Edge Case (CHK016): Conversation with 0 messages handled gracefully
- [x] T045 [P] [US10] Integration test: calculate_statistics() streams O(1) memory in tests/integration/test_statistics_streaming.py
- [x] T046 [P] [US10] Contract test: FR-016 calculate_statistics signature in tests/contract/test_fr_baseline.py
- [x] T047 [P] [US10] Contract test: FR-022 calculate_conversation_statistics signature in tests/contract/test_fr_baseline.py

### Implementation for US10

- [x] T048 [US10] Implement ExportStatistics Pydantic model in src/echomine/models/statistics.py (FR-017)
- [x] T049 [US10] Implement ConversationStatistics Pydantic model in src/echomine/models/statistics.py (FR-023)
- [x] T050 [US10] Implement calculate_statistics() function in src/echomine/statistics.py (FR-016)
- [x] T051 [US10] Implement calculate_conversation_statistics() function in src/echomine/statistics.py (FR-022)
- [x] T052 [US10] Add progress_callback parameter to calculate_statistics() (FR-016)
- [x] T053 [US10] Add on_skip callback for malformed entries (FR-015)
- [x] T054 [US10] Add structured logging for statistics operations (FR-060a)

**Checkpoint**: Statistics library API complete - CLI can wrap this

---

## Phase 6: User Story 2 - View Export Statistics CLI (Priority: P1)

**Goal**: CLI users can run `echomine stats export.json` to see export-level statistics

**Independent Test**: Run `echomine stats export.json` and verify output shows totals, date range, largest/smallest

**FR Reference**: FR-009-015

### Tests for US2 (TDD - write first, verify fail) ⚠️

- [x] T055 [P] [US2] CLI integration test: stats command executes in tests/integration/test_cli_stats.py
- [x] T056 [P] [US2] CLI integration test: --json flag outputs valid JSON (FR-012)
- [x] T057 [P] [US2] CLI integration test: Progress reported to stderr (FR-014)
- [x] T058 [P] [US2] Contract test: FR-009 stats command exists
- [x] T059 [P] [US2] Contract test: FR-010 stats output fields

### Implementation for US2

- [x] T060 [US2] Implement stats command in src/echomine/cli/commands/stats.py (FR-009)
- [x] T061 [US2] Format human-readable output with Rich in src/echomine/cli/commands/stats.py (FR-010)
- [x] T062 [US2] Add --json flag support in src/echomine/cli/commands/stats.py (FR-012)
- [x] T063 [US2] Add progress bar to stderr during calculation (FR-014)
- [x] T064 [US2] Register stats command in src/echomine/cli/app.py

**Checkpoint**: Export statistics command available

---

## Phase 7: User Story 3 - View Per-Conversation Statistics (Priority: P2)

**Goal**: CLI users can run `echomine stats export.json --conversation <id>` for detailed conversation stats

**Independent Test**: Run `echomine stats export.json --conversation abc-123` and verify role breakdown and temporal patterns

**FR Reference**: FR-018-024

### Tests for US3 (TDD - write first, verify fail) ⚠️

- [x] T065 [P] [US3] CLI integration test: --conversation option shows per-conversation stats
- [x] T066 [P] [US3] CLI integration test: Invalid conversation ID exits with code 1 (FR-018)
- [x] T067 [P] [US3] CLI integration test: --json flag with --conversation outputs JSON (FR-024)
- [x] T068 [P] [US3] Contract test: FR-019 per-conversation stats fields
- [x] T069 [P] [US3] Contract test: FR-020 message count by role

### Implementation for US3

- [x] T070 [US3] Add --conversation option to stats command in src/echomine/cli/commands/stats.py (FR-018)
- [x] T071 [US3] Format per-conversation output with Rich tables in src/echomine/cli/commands/stats.py (FR-019)
- [x] T072 [US3] Add color-coded role display (user=green, assistant=blue, system=yellow) (FR-020)
- [x] T073 [US3] Display temporal patterns: first/last message, duration, average gap (FR-021)

**Checkpoint**: Per-conversation statistics available

---

## Phase 8: User Story 4 - List All Messages for a Conversation (Priority: P2)

**Goal**: CLI users can run `echomine get messages export.json <id>` to list all messages

**Independent Test**: Run `echomine get messages export.json abc-123` and verify all messages listed with IDs, roles, timestamps

**FR Reference**: FR-025-029

### Tests for US4 (TDD - write first, verify fail) ⚠️

- [x] T074 [P] [US4] CLI integration test: get messages command executes
- [x] T075 [P] [US4] CLI integration test: Messages shown in chronological order (FR-026)
- [x] T076 [P] [US4] CLI integration test: --json flag outputs full message objects (FR-027)
- [x] T077 [P] [US4] CLI integration test: Invalid conversation ID exits with code 1 (FR-028)
- [x] T078 [P] [US4] TDD Edge Case (CHK019): Messages with empty content display gracefully
- [x] T079 [P] [US4] TDD Edge Case (CHK020): Messages with content < 100 chars not truncated
- [x] T080 [P] [US4] Contract test: FR-025 get messages command

### Implementation for US4

- [x] T081 [US4] Implement get messages subcommand in src/echomine/cli/commands/get.py (FR-025)
- [x] T082 [US4] Format message list with content preview (first 100 chars) in src/echomine/cli/commands/get.py (FR-026)
- [x] T083 [US4] Add --json flag support for full message objects (FR-027)
- [x] T084 [US4] Use streaming to find conversation (FR-029)
- [x] T085 [US4] Register get command group in src/echomine/cli/app.py

**Checkpoint**: Message listing available

---

## Phase 9: User Story 5 - Export Conversations with Rich Metadata (Priority: P2)

**Goal**: Markdown exports include YAML frontmatter and message IDs in headers

**Independent Test**: Export a conversation and verify YAML frontmatter at start and message IDs in headers

**FR Reference**: FR-030-035

### Tests for US5 (TDD - write first, verify fail) ⚠️

- [x] T086 [P] [US5] Unit test: export_conversation() includes YAML frontmatter by default in tests/unit/test_markdown_export.py
- [x] T087 [P] [US5] Unit test: Frontmatter contains all required fields (FR-031) in tests/unit/test_markdown_export.py
- [x] T088 [P] [US5] Unit test: Datetime fields use ISO 8601 with Z suffix (FR-031b)
- [x] T089 [P] [US5] Unit test: Message headers include message ID in backticks (FR-032)
- [x] T090 [P] [US5] Unit test: Generated message IDs follow msg-{conv_id}-{index} format (FR-032a)
- [x] T091 [P] [US5] Unit test: Generated IDs are deterministic/reproducible (FR-032b)
- [x] T092 [P] [US5] Unit test: --no-metadata flag disables frontmatter (FR-033)
- [x] T093 [P] [US5] Contract test: FR-030 frontmatter default behavior

### Implementation for US5

- [x] T094 [US5] Add include_metadata parameter to MarkdownExporter.export_conversation() (FR-035)
- [x] T095 [US5] Add include_message_ids parameter to MarkdownExporter.export_conversation() (FR-035)
- [x] T096 [US5] Implement YAML frontmatter generation in src/echomine/export/markdown.py (FR-030, FR-031)
- [x] T097 [US5] Implement message ID generation for missing source IDs (FR-032a, FR-032b)
- [x] T098 [US5] Add --no-metadata flag to export command in src/echomine/cli/commands/export.py (FR-033)

**Checkpoint**: Rich markdown export available

---

## Phase 10: User Story 7 - Sort Search Results (Priority: P3)

**Goal**: CLI users can control result ordering with --sort and --order flags

**Independent Test**: Search with `--sort date --order desc` and verify results ordered by updated_at

**FR Reference**: FR-043-048

### Tests for US7 (TDD - write first, verify fail) ⚠️

- [x] T099 [P] [US7] Unit test: SearchQuery accepts sort_by field in tests/unit/test_search_filters.py
- [x] T100 [P] [US7] Unit test: SearchQuery accepts sort_order field in tests/unit/test_search_filters.py
- [x] T101 [P] [US7] Unit test: Default sort is by score descending (FR-045)
- [x] T102 [P] [US7] Unit test: Title sort is case-insensitive (FR-047)
- [x] T103 [P] [US7] Unit test: Stable sort preserves relative order (FR-043b)
- [x] T104 [P] [US7] Unit test: NULL updated_at falls back to created_at (FR-046a)
- [x] T105 [P] [US7] Unit test: Tie-breaking by conversation_id (FR-043a)
- [x] T106 [P] [US7] CLI integration test: --sort flag accepted in search command
- [x] T107 [P] [US7] CLI integration test: --order flag accepted in search command
- [x] T108 [P] [US7] Contract test: FR-043 sort options

### Implementation for US7

- [x] T109 [US7] Add sort_by field to SearchQuery in src/echomine/models/search.py (FR-048)
- [x] T110 [US7] Add sort_order field to SearchQuery in src/echomine/models/search.py (FR-048)
- [x] T111 [US7] Implement sorting logic in OpenAIAdapter.search() in src/echomine/adapters/openai.py
- [x] T112 [US7] Implement date fallback for NULL updated_at (FR-046a)
- [x] T113 [US7] Add --sort flag to search command in src/echomine/cli/commands/search.py (FR-043)
- [x] T114 [US7] Add --order flag to search command in src/echomine/cli/commands/search.py (FR-044)
- [x] T115 [US7] Add --sort flag to list command in src/echomine/cli/commands/list.py (FR-048a)

**Checkpoint**: Sort options available for search and list

---

## Phase 11: User Story 6 - View Rich Formatted CLI Output (Priority: P3)

**Goal**: Terminal output uses Rich tables, colors, and progress bars

**Independent Test**: Run list/search commands and verify table format with color-coded elements

**FR Reference**: FR-036-042

### Tests for US6 (TDD - write first, verify fail) ⚠️

- [x] T116 [P] [US6] Unit test: Table formatter produces Rich table output in tests/unit/test_formatters.py
- [x] T117 [P] [US6] Unit test: Score colors (>0.7 green, 0.4-0.7 yellow, <0.4 red) (FR-037)
- [x] T118 [P] [US6] Unit test: Role colors (user=green, assistant=blue, system=yellow) (FR-038)
- [x] T119 [P] [US6] Unit test: Rich disabled when stdout not TTY (FR-040)
- [x] T120 [P] [US6] Unit test: Rich disabled with --json flag (FR-041)
- [x] T121 [P] [US6] Unit test: Conflicting format flags last-wins with warning (FR-041a)
- [x] T122 [P] [US6] Contract test: FR-036 table format

### Implementation for US6

- [x] T123 [US6] Implement Rich table formatting in src/echomine/cli/formatters.py (FR-036)
- [x] T124 [US6] Implement score color coding in src/echomine/cli/formatters.py (FR-037)
- [x] T125 [US6] Implement role color coding in src/echomine/cli/formatters.py (FR-038)
- [x] T126 [US6] Implement progress bar for long operations in src/echomine/cli/formatters.py (FR-039)
- [x] T127 [US6] Add TTY detection for Rich formatting in src/echomine/cli/formatters.py (FR-040)
- [x] T128 [US6] Implement format flag conflict handling (FR-041a)
- [x] T129 [US6] Apply Rich formatting to list command in src/echomine/cli/commands/list.py
- [x] T130 [US6] Apply Rich formatting to search command in src/echomine/cli/commands/search.py

**Checkpoint**: Rich CLI formatting available

---

## Phase 12: User Story 8 - Export Results to CSV Format (Priority: P3)

**Goal**: Export conversation data to RFC 4180 compliant CSV format

**Independent Test**: Run search with `--format csv` and verify valid CSV with proper headers and escaping

**FR Reference**: FR-049-055

### Tests for US8 (TDD - write first, verify fail) ⚠️

- [x] T131 [P] [US8] Unit test: CSVExporter.export_conversations() returns valid CSV in tests/unit/test_csv_exporter.py
- [x] T132 [P] [US8] Unit test: CSVExporter.export_search_results() includes score column
- [x] T133 [P] [US8] Unit test: CSVExporter.export_messages() returns valid CSV (FR-052)
- [x] T134 [P] [US8] Unit test: CSV properly escapes commas and quotes (FR-053)
- [x] T135 [P] [US8] Unit test: NULL values are empty fields (FR-053a)
- [x] T136 [P] [US8] Unit test: Newlines preserved in quoted fields (FR-053b)
- [x] T137 [P] [US8] Unit test: CSV parseable by Python csv module (FR-053c)
- [x] T138 [P] [US8] Unit test: --format csv and --csv-messages mutually exclusive (FR-051a)
- [x] T139 [P] [US8] TDD Edge Case (CHK054): Corrupted JSON during streaming handled gracefully
- [x] T140 [P] [US8] CLI integration test: --format csv outputs CSV
- [x] T141 [P] [US8] Contract test: FR-050 CSV schema

### Implementation for US8

- [x] T142 [US8] Implement CSVExporter class in src/echomine/export/csv.py (FR-055)
- [x] T143 [US8] Implement export_conversations() method (FR-050)
- [x] T144 [US8] Implement export_search_results() method (FR-050)
- [x] T145 [US8] Implement export_messages() method (FR-052)
- [x] T146 [US8] Implement export_messages_from_results() method
- [x] T147 [US8] Ensure RFC 4180 compliance with proper escaping (FR-053)
- [x] T148 [US8] Add --format csv flag to search command (FR-049)
- [x] T149 [US8] Add --format csv flag to list command (FR-049)
- [x] T150 [US8] Add --csv-messages flag to search command (FR-051)
- [x] T151 [US8] Implement mutual exclusion for CSV flags (FR-051a)
- [x] T152 [US8] Add structured logging for CSV export (FR-060a)

**Checkpoint**: CSV export available

---

## Phase 13: Error Handling & Interruption

**Purpose**: Implement error handling requirements from FR-061, FR-062

### Tests (TDD - write first, verify fail) ⚠️

- [x] T153 [P] Unit test: PermissionError raised on protected file access (FR-061b)
- [x] T154 [P] CLI integration test: Permission denied exits with code 1 (FR-061)
- [x] T155 [P] CLI integration test: Ctrl+C exits with code 130 (FR-062)
- [x] T156 [P] Unit test: Context managers close file handles on interrupt (FR-062a)

### Implementation

- [x] T157 Handle PermissionError in CLI with exit code 1 in src/echomine/cli/commands/stats.py (FR-061)
- [x] T158 Handle PermissionError in CLI with exit code 1 in src/echomine/cli/commands/search.py (FR-061)
- [x] T159 Implement KeyboardInterrupt handling with exit code 130 in src/echomine/cli/app.py (FR-062)
- [x] T160 Verify all file operations use context managers (FR-062a)

**Checkpoint**: Error handling complete

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Verification gates, documentation, and final polish

### VERIFY Gate Tasks (from qa-review.md)

- [x] T161 [GATE] (CHK043) Verify backward compatibility with ALL v1.1.0 command variations
- [x] T162 [GATE] (CHK047) Verify 100% library-first compliance - all CLI features have library API
- [x] T163 [GATE] (CHK061) Verify progress callback signature consistent between calculate_statistics() and search()
- [x] T164 [GATE] (CHK062) Verify exit code 1 consistent across all "not found" error scenarios
- [x] T165 [GATE] (CHK063) Verify --json flag behavior consistent across stats, search, list, get commands
- [x] T166 [GATE] (CHK064) Verify streaming O(1) memory for ALL new operations
- [x] T167 [GATE] (CHK065) Verify role values normalized to user/assistant/system
- [x] T168 [GATE] (CHK067) Verify ijson 3.2+ version requirement for streaming features

### Documentation Tasks (from qa-review.md DOC items)

- [x] T169 [P] (CHK069) Verify every FR has at least one acceptance scenario
- [x] T170 [P] (CHK070) Verify all edge cases traced to specific FRs
- [x] T171 [P] (CHK071) Verify library API functions documented in library_api.md
- [x] T172 [P] (CHK072) Verify CLI commands documented in cli_spec.md

### Performance Benchmark

- [x] T173 Create performance benchmark for stats <5s on 10K conversations in tests/performance/test_stats_performance.py (SC-002)
- [x] T174 Run quickstart.md validation
- [x] T175 Final mypy --strict verification
- [x] T176 Final ruff check and format

**Checkpoint**: All verification gates passed, ready for release

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────────────────────────┐
                                                     │
Phase 2: Foundational (blocks all stories) ──────────┤
                                                     │
         ┌───────────────────────────────────────────┴──────────────────────────────────────┐
         │                                                                                  │
         ▼                                                                                  ▼
Phase 3: US9 Library Message Count (P1)           Phase 5: US10 Library Statistics (P1)
         │                                                  │
         ▼                                                  ▼
Phase 4: US1 CLI Message Count (P1)               Phase 6: US2 CLI Stats (P1)
                                                           │
                                                           ├─────────────────────────────┐
                                                           ▼                             ▼
                                                  Phase 7: US3 Per-Conv Stats     Phase 8: US4 List Messages
                                                                                         │
                                                                                         ▼
                                                                                  Phase 9: US5 Rich Markdown
         ┌─────────────────────────────────────────────────────────────────────────────────┘
         │
         ├─────────────────┬─────────────────┬─────────────────┐
         ▼                 ▼                 ▼                 ▼
Phase 10: US7 Sort   Phase 11: US6 Rich   Phase 12: US8 CSV  Phase 13: Error Handling
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                   │
                                   ▼
                          Phase 14: Polish & Verify Gates
```

### User Story Dependencies

| Story | Priority | Depends On | Can Start After |
|-------|----------|------------|-----------------|
| US9 | P1 | Phase 2 | Foundational complete |
| US10 | P1 | Phase 2 | Foundational complete |
| US1 | P1 | US9 | US9 library API complete |
| US2 | P1 | US10 | US10 library API complete |
| US3 | P2 | US2, US10 | Stats command and library API |
| US4 | P2 | Phase 2 | Foundational complete |
| US5 | P2 | Phase 2 | Foundational complete |
| US6 | P3 | Phase 2 | Foundational complete |
| US7 | P3 | Phase 2 | Foundational complete |
| US8 | P3 | Phase 2 | Foundational complete |

### Parallel Opportunities

**After Foundational (Phase 2) completes:**
- US9 and US10 can run in parallel (library APIs)
- US4, US5, US6, US7, US8 can start in parallel (no inter-story dependencies)

**Within each story:**
- All tests marked [P] can run in parallel
- Models can be implemented in parallel

---

## Parallel Examples

### Example 1: Library Layer (US9 + US10 in parallel)

```bash
# Developer A: US9 - Message Count Filtering
Task: T016-T023 (tests first)
Task: T024-T028 (implementation)

# Developer B: US10 - Statistics API
Task: T037-T047 (tests first)
Task: T048-T054 (implementation)
```

### Example 2: CLI Layer (after library APIs)

```bash
# Developer A: US1 - Message Count CLI
Task: T029-T032 (tests first)
Task: T033-T036 (implementation)

# Developer B: US2 - Stats CLI
Task: T055-T059 (tests first)
Task: T060-T064 (implementation)
```

### Example 3: P3 Features (fully parallel)

```bash
# Developer A: US7 - Sort
Task: T099-T108 (tests), T109-T115 (implementation)

# Developer B: US6 - Rich Formatting
Task: T116-T122 (tests), T123-T130 (implementation)

# Developer C: US8 - CSV Export
Task: T131-T141 (tests), T142-T152 (implementation)
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US9 (Library Message Count)
4. Complete Phase 4: US1 (CLI Message Count)
5. **STOP and VALIDATE**: Message count filtering works end-to-end
6. Complete Phase 5: US10 (Library Statistics)
7. Complete Phase 6: US2 (CLI Statistics)
8. **STOP and VALIDATE**: Statistics command works end-to-end

### Incremental Delivery

| Increment | Stories | Value Delivered |
|-----------|---------|-----------------|
| MVP | US9, US1 | Message count filtering via CLI |
| Stats | US10, US2 | Export statistics command |
| Deep Stats | US3 | Per-conversation statistics |
| Messages | US4 | Message listing command |
| Rich Export | US5 | Markdown with frontmatter |
| UX Polish | US6 | Rich terminal formatting |
| Sort | US7 | Result sorting options |
| CSV | US8 | CSV export format |

---

## Summary

| Category | Count |
|----------|-------|
| Total Tasks | 176 |
| Setup Phase | 8 |
| Foundational Phase | 7 |
| US1-US10 Tasks | 144 |
| Error Handling | 8 |
| Polish/Gates | 16 |
| TDD Edge Cases (from qa-review.md) | 10 |
| VERIFY Gate Tasks (from qa-review.md) | 8 |

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story
- [GATE] = verification task from qa-review.md VERIFY items
- TDD Edge Cases from CHK items marked → TDD are included as explicit test tasks
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
