# Tasks: Claude Export Adapter

**Input**: Design documents from `/specs/004-claude-adapter/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Per Constitution Principle III (TDD), all tests are MANDATORY and MUST be written FIRST and verified to FAIL before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

## User Stories Summary

| Story | Title | Priority | FR Range |
|-------|-------|----------|----------|
| US1 | Claude Export Parsing | P1 | FR-001 to FR-010 |
| US2 | Claude Message Parsing | P1 | FR-011 to FR-020 |
| US3 | Claude Search Support | P1 | FR-021 to FR-035 |
| US4 | Conversation Retrieval | P2 | FR-036 to FR-040 |
| US5 | Message Retrieval | P2 | FR-041 to FR-045 |
| US6 | Provider Auto-Detection | P2 | FR-046 to FR-055 |

---

## Phase 1: Setup (Test Infrastructure)

**Purpose**: Create test fixtures and directory structure before any implementation

- [x] T001 Create test fixtures directory at tests/fixtures/claude/
- [x] T002 [P] Create sample_export.json fixture with 3-5 conversations in tests/fixtures/claude/sample_export.json
- [x] T003 [P] Create malformed_export.json fixture with missing fields and invalid timestamps in tests/fixtures/claude/malformed_export.json
- [x] T004 [P] Create tool_messages.json fixture with tool_use/tool_result blocks in tests/fixtures/claude/tool_messages.json
- [x] T005 [P] Create empty_conversations.json fixture with zero messages in tests/fixtures/claude/empty_conversations.json

---

## Phase 2: Foundational (Adapter Skeleton)

**Purpose**: Core infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create ClaudeAdapter class skeleton in src/echomine/adapters/claude.py with ConversationProvider protocol stub
- [x] T007 Add ClaudeAdapter export to src/echomine/adapters/__init__.py
- [x] T008 Add ClaudeAdapter export to src/echomine/__init__.py
- [x] T009 Create test file structure at tests/unit/adapters/test_claude.py with test class skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Claude Export Parsing (Priority: P1) 🎯 MVP

**Goal**: Parse Claude export JSON files with O(1) memory streaming via ijson

**Independent Test**: Call `ClaudeAdapter.stream_conversations(file_path)` on Claude export and verify Conversation objects with correct field mappings

**FR Coverage**: FR-001 to FR-010

### Tests for User Story 1 (RED - Write First, Verify Fails) ⚠️

- [x] T010 [P] [US1] Write failing test for parsing root array structure (FR-001) in tests/unit/adapters/test_claude.py::test_parse_root_array_structure
- [x] T011 [P] [US1] Write failing test for uuid→id mapping (FR-002) in tests/unit/adapters/test_claude.py::test_uuid_maps_to_id
- [x] T012 [P] [US1] Write failing test for name→title mapping with empty string preservation (FR-003) in tests/unit/adapters/test_claude.py::test_name_maps_to_title
- [x] T013 [P] [US1] Write failing test for ISO 8601 timestamp parsing (FR-004, FR-005) in tests/unit/adapters/test_claude.py::test_iso_timestamp_parsing
- [x] T014 [P] [US1] Write failing test for chat_messages→messages mapping (FR-006) in tests/unit/adapters/test_claude.py::test_chat_messages_mapping
- [x] T015 [P] [US1] Write failing test for summary/account stored in metadata (FR-007, FR-008) in tests/unit/adapters/test_claude.py::test_metadata_storage
- [x] T016 [P] [US1] Write failing test for ijson streaming (FR-009) in tests/unit/adapters/test_claude.py::test_streaming_memory_efficiency
- [x] T017 [P] [US1] Write failing test for empty conversation handling (FR-010) in tests/unit/adapters/test_claude.py::test_empty_conversation_handling
- [x] T018 [US1] Verify all US1 tests fail (RED phase complete)

### Implementation for User Story 1 (GREEN)

- [x] T019 [US1] Implement `_parse_conversation()` method in src/echomine/adapters/claude.py per data-model.md
- [x] T020 [US1] Implement `stream_conversations()` with ijson streaming in src/echomine/adapters/claude.py
- [x] T021 [US1] Add context manager for file handle cleanup per R-007 in src/echomine/adapters/claude.py
- [x] T022 [US1] Add progress callback support (every 100 items OR 100ms) per R-008 in src/echomine/adapters/claude.py
- [x] T023 [US1] Verify all US1 tests pass (GREEN phase complete)

**Checkpoint**: User Story 1 complete - can stream Claude conversations with O(1) memory

---

## Phase 4: User Story 2 - Claude Message Parsing (Priority: P1)

**Goal**: Parse Claude messages with role normalization and content block extraction

**Independent Test**: Parse Claude export and verify each message has correct field mappings and role normalization

**FR Coverage**: FR-011 to FR-020

### Tests for User Story 2 (RED - Write First, Verify Fails) ⚠️

- [x] T024 [P] [US2] Write failing test for message uuid→id mapping (FR-011) in tests/unit/adapters/test_claude.py::test_message_uuid_mapping
- [x] T025 [P] [US2] Write failing test for content block extraction (FR-012, FR-015) in tests/unit/adapters/test_claude.py::test_content_block_extraction
- [x] T026 [P] [US2] Write failing test for role normalization human→user (FR-013) in tests/unit/adapters/test_claude.py::test_role_normalization
- [x] T027 [P] [US2] Write failing test for message timestamp parsing (FR-014) in tests/unit/adapters/test_claude.py::test_message_timestamp_parsing
- [x] T028 [P] [US2] Write failing test for tool_use/tool_result block skipping (FR-015a) in tests/unit/adapters/test_claude.py::test_tool_block_skipping
- [x] T029 [P] [US2] Write failing test for text field fallback (FR-015b) in tests/unit/adapters/test_claude.py::test_text_field_fallback
- [x] T030 [P] [US2] Write failing test for message timestamp fallback to conversation created_at (FR-019) in tests/unit/adapters/test_claude.py::test_message_timestamp_fallback
- [x] T031 [P] [US2] Write failing test for malformed entry skipping with WARNING (FR-017, FR-018) in tests/unit/adapters/test_claude.py::test_malformed_entry_skipping
- [x] T032 [P] [US2] Write failing test for parent_id=None (FR-020) in tests/unit/adapters/test_claude.py::test_parent_id_none
- [x] T033 [US2] Verify all US2 tests fail (RED phase complete)

### Implementation for User Story 2 (GREEN)

- [x] T034 [US2] Implement `_parse_message()` method in src/echomine/adapters/claude.py per data-model.md
- [x] T035 [US2] Implement `_extract_content_from_blocks()` helper in src/echomine/adapters/claude.py
- [x] T036 [US2] Implement `_normalize_role()` helper in src/echomine/adapters/claude.py
- [x] T037 [US2] Implement `_parse_attachments()` helper for ImageRef mapping (FR-016) in src/echomine/adapters/claude.py
- [x] T038 [US2] Add structlog WARNING for skipped malformed entries in src/echomine/adapters/claude.py
- [x] T039 [US2] Verify all US2 tests pass (GREEN phase complete)

**Checkpoint**: User Stories 1 AND 2 complete - full conversation and message parsing works

---

## Phase 5: User Story 3 - Claude Search Support (Priority: P1)

**Goal**: Search Claude conversations using SearchQuery with BM25 ranking

**Independent Test**: Create SearchQuery with various filters and verify results match expected conversations with correct relevance ranking

**FR Coverage**: FR-021 to FR-035

### Tests for User Story 3 (RED - Write First, Verify Fails) ⚠️

- [x] T040 [P] [US3] Write failing test for search() returning Iterator[SearchResult] (FR-021) in tests/unit/adapters/test_claude.py::test_search_returns_iterator
- [x] T041 [P] [US3] Write failing test for BM25 keyword ranking and SearchResult structure (FR-022, FR-033) in tests/unit/adapters/test_claude.py::test_bm25_keyword_ranking
- [x] T042 [P] [US3] Write failing test for phrase matching (FR-023) in tests/unit/adapters/test_claude.py::test_phrase_matching
- [x] T043 [P] [US3] Write failing test for title_filter (FR-024) in tests/unit/adapters/test_claude.py::test_title_filter
- [x] T044 [P] [US3] Write failing test for date range filtering (FR-025) in tests/unit/adapters/test_claude.py::test_date_range_filtering
- [x] T045 [P] [US3] Write failing test for message count filtering (FR-026) in tests/unit/adapters/test_claude.py::test_message_count_filtering
- [x] T046 [P] [US3] Write failing test for role_filter (FR-027) in tests/unit/adapters/test_claude.py::test_role_filter
- [x] T047 [P] [US3] Write failing test for exclude_keywords (FR-028) in tests/unit/adapters/test_claude.py::test_exclude_keywords
- [x] T048 [P] [US3] Write failing test for match_mode all/any (FR-029) in tests/unit/adapters/test_claude.py::test_match_mode
- [x] T049 [P] [US3] Write failing test for sort_by and sort_order (FR-030) in tests/unit/adapters/test_claude.py::test_sort_options
- [x] T050 [P] [US3] Write failing test for snippet generation (FR-031) in tests/unit/adapters/test_claude.py::test_snippet_generation
- [x] T051 [P] [US3] Write failing test for limit parameter (FR-035) in tests/unit/adapters/test_claude.py::test_limit_parameter
- [x] T052 [US3] Verify all US3 tests fail (RED phase complete)

### Implementation for User Story 3 (GREEN)

- [x] T053 [US3] Implement `search()` method in src/echomine/adapters/claude.py using existing BM25Scorer
- [x] T054 [US3] Add all SearchQuery filter support (title, date, message count, role, exclude) in src/echomine/adapters/claude.py
- [x] T055 [US3] Add match_mode handling (all/any) in src/echomine/adapters/claude.py
- [x] T056 [US3] Add sort_by and sort_order support in src/echomine/adapters/claude.py
- [x] T057 [US3] Add snippet generation using existing extract_snippet_from_messages() in src/echomine/adapters/claude.py
- [x] T058 [US3] Verify all US3 tests pass (GREEN phase complete)

**Checkpoint**: All P1 stories complete - core Claude adapter functionality ready

---

## Phase 6: User Story 4 - Conversation Retrieval (Priority: P2)

**Goal**: Retrieve specific Claude conversations by UUID

**Independent Test**: Call `get_conversation_by_id()` with known UUID and verify correct conversation returned

**FR Coverage**: FR-036 to FR-040

### Tests for User Story 4 (RED - Write First, Verify Fails) ⚠️

- [x] T059 [P] [US4] Write failing test for get_conversation_by_id() signature (FR-036) in tests/unit/adapters/test_claude.py::test_get_conversation_by_id_signature
- [x] T060 [P] [US4] Write failing test for uuid field search (FR-037) in tests/unit/adapters/test_claude.py::test_search_by_uuid
- [x] T061 [P] [US4] Write failing test for None on non-existent ID (FR-038) in tests/unit/adapters/test_claude.py::test_returns_none_not_found
- [x] T062 [P] [US4] Write failing test for O(1) memory usage (FR-039) in tests/unit/adapters/test_claude.py::test_retrieval_memory_efficiency
- [x] T063 [P] [US4] Write failing test for partial ID matching (FR-040) in tests/unit/adapters/test_claude.py::test_partial_id_matching
- [x] T064 [US4] Verify all US4 tests fail (RED phase complete)

### Implementation for User Story 4 (GREEN)

- [x] T065 [US4] Implement `get_conversation_by_id()` method in src/echomine/adapters/claude.py
- [x] T066 [US4] Add partial ID matching support in src/echomine/adapters/claude.py
- [x] T067 [US4] Verify all US4 tests pass (GREEN phase complete)

**Checkpoint**: User Story 4 complete - can retrieve conversations by ID

---

## Phase 7: User Story 5 - Message Retrieval (Priority: P2)

**Goal**: Retrieve specific messages by UUID with conversation context

**Independent Test**: Call `get_message_by_id()` with known UUID and verify message and parent conversation returned

**FR Coverage**: FR-041 to FR-045

### Tests for User Story 5 (RED - Write First, Verify Fails) ⚠️

- [x] T068 [P] [US5] Write failing test for get_message_by_id() signature (FR-041) in tests/unit/adapters/test_claude.py::test_get_message_by_id_signature
- [x] T069 [P] [US5] Write failing test for message uuid search (FR-042) in tests/unit/adapters/test_claude.py::test_search_message_by_uuid
- [x] T070 [P] [US5] Write failing test for conversation_id hint performance (FR-043) in tests/unit/adapters/test_claude.py::test_conversation_id_hint
- [x] T071 [P] [US5] Write failing test for returning tuple (Message, Conversation) (FR-044) in tests/unit/adapters/test_claude.py::test_returns_message_with_context
- [x] T072 [P] [US5] Write failing test for None on non-existent message (FR-045) in tests/unit/adapters/test_claude.py::test_message_not_found_returns_none
- [x] T073 [US5] Verify all US5 tests fail (RED phase complete)

### Implementation for User Story 5 (GREEN)

- [x] T074 [US5] Implement `get_message_by_id()` method in src/echomine/adapters/claude.py
- [x] T075 [US5] Add conversation_id hint optimization in src/echomine/adapters/claude.py
- [x] T076 [US5] Verify all US5 tests pass (GREEN phase complete)

**Checkpoint**: User Story 5 complete - can retrieve messages with context

---

## Phase 8: User Story 6 - Provider Auto-Detection (Priority: P2)

**Goal**: CLI auto-detects Claude vs OpenAI exports and supports --provider flag

**Independent Test**: Provide different export files to CLI and verify correct adapter selected automatically

**FR Coverage**: FR-046 to FR-055

### Tests for User Story 6 (RED - Write First, Verify Fails) ⚠️

- [x] T077 [P] [US6] Write failing test for auto-detection based on schema (FR-046) in tests/unit/cli/test_provider_detection.py::test_auto_detect_provider
- [x] T078 [P] [US6] Write failing test for Claude detection via chat_messages key (FR-047) in tests/unit/cli/test_provider_detection.py::test_detect_claude_format
- [x] T079 [P] [US6] Write failing test for OpenAI detection via mapping key (FR-048) in tests/unit/cli/test_provider_detection.py::test_detect_openai_format
- [x] T080 [P] [US6] Write failing test for --provider flag (FR-049) in tests/unit/cli/test_provider_detection.py::test_provider_flag
- [x] T081 [P] [US6] Write failing test for unrecognized format error (FR-050) in tests/unit/cli/test_provider_detection.py::test_unrecognized_format_error
- [x] T082 [US6] Verify all US6 tests fail (RED phase complete)

### Implementation for User Story 6 (GREEN)

- [x] T083 [US6] Implement `detect_provider()` function in src/echomine/cli/provider.py per cli_spec.md
- [x] T084 [US6] Implement `get_adapter()` function in src/echomine/cli/provider.py per cli_spec.md
- [x] T085 [US6] Add `--provider` flag to list command in src/echomine/cli/commands/list.py
- [x] T086 [US6] Add `--provider` flag to search command in src/echomine/cli/commands/search.py
- [x] T087 [US6] Add `--provider` flag to get command in src/echomine/cli/commands/get.py
- [x] T088 [US6] Add `--provider` flag to export command in src/echomine/cli/commands/export.py
- [x] T089 [US6] Add `--provider` flag to stats command in src/echomine/cli/commands/stats.py
- [x] T090 [US6] Add error message for unrecognized formats in src/echomine/cli/provider.py
- [x] T091 [US6] Verify all US6 tests pass (GREEN phase complete)

**Checkpoint**: All user stories complete - full Claude adapter with CLI integration

---

## Phase 9: Integration, Contract & Protocol Compliance Tests

**Purpose**: End-to-end validation, FR contract verification, and protocol compliance

### Protocol Compliance Tests (Moved from US6)

- [ ] T092 [P] Write test for ConversationProvider protocol compliance (FR-051) in tests/contract/test_protocol_compliance.py::test_protocol_compliance
- [ ] T093 [P] Write test for stateless adapter (FR-052) in tests/contract/test_protocol_compliance.py::test_stateless_adapter
- [ ] T094 [P] Write test for shared model usage - no provider-specific subclasses (FR-053) in tests/contract/test_protocol_compliance.py::test_uses_shared_models
- [ ] T095 [P] Write test for error handling parity with OpenAI adapter (FR-054) in tests/contract/test_protocol_compliance.py::test_error_handling_parity

### Cross-Adapter Parity Tests

- [ ] T096 [P] Write contract test for BM25 score parity between adapters (FR-032) in tests/contract/test_bm25_parity.py::test_bm25_scores_match

### Integration Tests

- [ ] T097 [P] Write integration test for end-to-end Claude parsing in tests/integration/test_claude_integration.py
- [ ] T098 [P] Write integration test for search with all filters in tests/integration/test_claude_integration.py
- [ ] T099 [P] Write integration test for CLI auto-detection in tests/integration/test_claude_integration.py

### FR Contract Tests

- [ ] T100 [P] Write contract tests for FR-001 to FR-010 in tests/contract/test_claude_contract.py
- [ ] T101 [P] Write contract tests for FR-011 to FR-020 in tests/contract/test_claude_contract.py
- [ ] T102 [P] Write contract tests for FR-021 to FR-035 in tests/contract/test_claude_contract.py
- [ ] T103 [P] Write contract tests for FR-036 to FR-055 in tests/contract/test_claude_contract.py
- [ ] T104 Verify all integration and contract tests pass

---

## Phase 10: Performance & Polish

**Purpose**: Performance validation and final quality checks

- [ ] T105 Create large_export.json generator script at tests/fixtures/claude/generate_large_export.py
- [ ] T106 [P] Write performance benchmark for 1000+ conversations in tests/performance/test_claude_performance.py
- [ ] T107 [P] Write memory efficiency benchmark in tests/performance/test_claude_performance.py
- [ ] T108 Run performance benchmarks and verify <30s search for 10K conversations (SC-002)
- [ ] T109 Run mypy --strict and verify zero errors on src/echomine/adapters/claude.py
- [ ] T110 Run ruff check and format on all new files
- [ ] T111 Run full test suite and verify >80% coverage
- [ ] T112 Validate quickstart.md examples work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phases 3-8 (User Stories)**: All depend on Phase 2 completion
  - US1/US2/US3 (P1) should complete before US4/US5/US6 (P2)
  - US2 depends on US1 (uses _parse_conversation)
  - US3 depends on US1+US2 (uses stream_conversations)
  - US4/US5 depend on US1+US2 (uses parsing methods)
  - US6 depends on all adapter methods being implemented
- **Phase 9 (Integration)**: Depends on all user stories complete
- **Phase 10 (Polish)**: Depends on Phase 9 complete

### User Story Dependencies

```
Phase 2 (Foundation)
    ↓
US1 (Conversation Parsing) → US2 (Message Parsing) → US3 (Search)
                                      ↓
                          US4 (Conv Retrieval) → US5 (Msg Retrieval)
                                      ↓
                              US6 (CLI Auto-Detection)
```

### Within Each User Story (TDD Cycle)

1. Write ALL tests first (RED) - verify they fail
2. Implement minimal code to pass tests (GREEN)
3. Verify all tests pass before moving to next story

### Parallel Opportunities

**Within Phases (same phase, different files):**
- T002-T005: All fixtures can be created in parallel
- T010-T017: All US1 tests can be written in parallel
- T024-T032: All US2 tests can be written in parallel
- T040-T051: All US3 tests can be written in parallel
- T059-T063: All US4 tests can be written in parallel
- T068-T072: All US5 tests can be written in parallel
- T077-T081: All US6 tests can be written in parallel
- T092-T103: All integration/contract tests can be written in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together (TDD mandatory - RED phase):
Task: "[US1] Write failing test for parsing root array structure"
Task: "[US1] Write failing test for uuid→id mapping"
Task: "[US1] Write failing test for name→title mapping"
Task: "[US1] Write failing test for ISO 8601 timestamp parsing"
Task: "[US1] Write failing test for chat_messages→messages mapping"
Task: "[US1] Write failing test for ijson streaming"
Task: "[US1] Write failing test for empty conversation handling"

# After RED phase verification, implementation is sequential
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup (fixtures)
2. Complete Phase 2: Foundational (skeleton)
3. Complete Phase 3: User Story 1 (Conversation Parsing)
4. Complete Phase 4: User Story 2 (Message Parsing)
5. Complete Phase 5: User Story 3 (Search Support)
6. **STOP and VALIDATE**: All P1 stories independently testable
7. Deploy/demo if ready - core Claude adapter works!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test parsing → Core MVP
3. Add US2 → Test messages → Enhanced MVP
4. Add US3 → Test search → Full P1 MVP!
5. Add US4+US5 → Test retrieval → P2 features
6. Add US6 → Test CLI → Complete feature

### Quality Gates (Per Phase)

- All tests pass (pytest)
- mypy --strict passes (zero errors)
- ruff check passes (zero errors)
- Coverage >80% for new code

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 112 |
| **Setup Tasks** | 5 |
| **Foundational Tasks** | 4 |
| **US1 Tasks** | 14 |
| **US2 Tasks** | 16 |
| **US3 Tasks** | 19 |
| **US4 Tasks** | 9 |
| **US5 Tasks** | 9 |
| **US6 Tasks** | 15 |
| **Integration/Contract Tasks** | 13 |
| **Polish Tasks** | 8 |
| **Parallel Opportunities** | 72 tasks marked [P] |
| **MVP Scope** | US1-US3 (53 tasks) |
| **Test-First Tasks** | 54 (RED phase) |

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- TDD is MANDATORY: verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
