# Tasks: Advanced Search Enhancement Package

**Input**: Design documents from `/specs/002-advanced-search/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD is MANDATORY - tests MUST be written first and verified to fail before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/echomine/`, `tests/` at repository root
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend existing Pydantic models with new optional fields

- [X] T001 [P] Add `phrases` field to SearchQuery model in src/echomine/models/search.py
- [X] T002 [P] Add `match_mode` field to SearchQuery model in src/echomine/models/search.py
- [X] T003 [P] Add `exclude_keywords` field to SearchQuery model in src/echomine/models/search.py
- [X] T004 [P] Add `role_filter` field to SearchQuery model in src/echomine/models/search.py
- [X] T005 Add `snippet` field to SearchResult model in src/echomine/models/search.py
- [X] T006 Run mypy --strict on src/echomine/models/search.py and fix any type errors

**Checkpoint**: All model extensions complete, types validated

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T007 [P] Add phrase_matches() function signature with NotImplementedError to src/echomine/search/ranking.py
- [X] T008 [P] Add exclude_filter() function signature with NotImplementedError to src/echomine/search/ranking.py
- [X] T009 Update OpenAIAdapter.search() signature to use extended SearchQuery in src/echomine/adapters/openai.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Notes**:
- Functions raise NotImplementedError until implemented in their respective user story phases
- snippet.py creation moved to Phase 7 (US5-specific, not foundational)

---

## Phase 3: User Story 1 - Exact Phrase Matching (Priority: P1)

**Goal**: Enable searching for exact phrases like "algo-insights" without tokenization splitting

**Independent Test**: Search for "algo-insights" returns only conversations with that exact string

### Tests for User Story 1 (MANDATORY per TDD principle)

- [X] T011 [P] [US1] Unit test for phrase_matches() in tests/unit/search/test_phrase_matching.py
- [X] T012 [P] [US1] Unit test for SearchQuery.phrases field in tests/unit/models/test_search.py
- [X] T013 [P] [US1] Contract test for --phrase CLI flag in tests/contract/test_cli_search_phrase.py
- [X] T014 [US1] Integration test for phrase search end-to-end in tests/integration/test_search_phrase.py

### Implementation for User Story 1

- [X] T015 [US1] Implement phrase_matches() case-insensitive substring matching in src/echomine/search/ranking.py
- [X] T016 [US1] Integrate phrase matching into BM25Scorer.score() in src/echomine/search/ranking.py
- [X] T017 [US1] Update search() to check phrases before scoring in src/echomine/adapters/openai.py
- [X] T018 [US1] Add --phrase CLI flag to search command in src/echomine/cli/commands/search.py
- [X] T019 [US1] Add phrase to JSON output format in src/echomine/cli/formatters.py
- [X] T020 [US1] Verify all US1 tests pass with pytest tests/ -k phrase

**Checkpoint**: Phrase matching fully functional - can search for "algo-insights" exactly

---

## Phase 4: User Story 2 - Boolean Match Mode (Priority: P1)

**Goal**: Allow requiring ALL keywords present (AND logic) instead of ANY (OR)

**Independent Test**: Search with --match-mode all returns only conversations with ALL terms

### Tests for User Story 2 (MANDATORY per TDD principle)

- [X] T021 [P] [US2] Unit test for match_mode=all logic in tests/unit/search/test_match_mode.py
- [X] T022 [P] [US2] Unit test for SearchQuery.match_mode field in tests/unit/models/test_search.py
- [X] T023 [P] [US2] Contract test for --match-mode CLI flag in tests/contract/test_cli_search_match_mode.py
- [X] T024 [US2] Integration test for match mode search with SC-002 observation in tests/integration/test_search_match_mode.py

### Implementation for User Story 2

- [X] T025 [US2] Implement all_terms_present() check with early exit in src/echomine/search/ranking.py
- [X] T026 [US2] Integrate match_mode logic before BM25 scoring in src/echomine/adapters/openai.py
- [X] T027 [US2] Add --match-mode CLI flag with Literal validation in src/echomine/cli/commands/search.py
- [X] T028 [US2] Add match_mode to JSON output query section in src/echomine/cli/formatters.py
- [X] T029 [US2] Verify all US2 tests pass with pytest tests/ -k match_mode

**Checkpoint**: Boolean match mode functional - can require ALL or ANY terms

---

## Phase 5: User Story 3 - Exclude Keywords (Priority: P2)

**Goal**: Filter out conversations containing excluded terms

**Independent Test**: Search with --exclude "django" returns no conversations mentioning django

### Tests for User Story 3 (MANDATORY per TDD principle)

- [X] T030 [P] [US3] Unit test for exclude_filter() in tests/unit/search/test_exclude.py
- [X] T031 [P] [US3] Unit test for SearchQuery.exclude_keywords field in tests/unit/models/test_search.py
- [X] T032 [P] [US3] Contract test for --exclude CLI flag in tests/contract/test_cli_search_exclude.py
- [X] T033 [US3] Integration test for exclusion search in tests/integration/test_search_exclude.py

### Implementation for User Story 3

- [X] T034 [US3] Implement exclude_filter() using BM25Scorer._tokenize() in src/echomine/search/ranking.py
- [X] T035 [US3] Integrate exclusion post-filter after scoring in src/echomine/adapters/openai.py
- [X] T036 [US3] Add --exclude CLI flag (multiple values) in src/echomine/cli/commands/search.py
- [X] T037 [US3] Add exclude_keywords to JSON output query section in src/echomine/cli/formatters.py
- [X] T038 [US3] Verify all US3 tests pass with pytest tests/ -k exclude

**Checkpoint**: Exclusion filtering functional - can exclude unwanted terms

---

## Phase 6: User Story 4 - Filter by Message Role (Priority: P2)

**Goal**: Search only in user messages or only in assistant messages

**Independent Test**: Search with --role user returns matches only from user messages

### Tests for User Story 4 (MANDATORY per TDD principle)

- [X] T039 [P] [US4] Unit test for role filtering in tests/unit/search/test_role_filter.py
- [X] T040 [P] [US4] Unit test for SearchQuery.role_filter field in tests/unit/models/test_search.py
- [X] T041 [P] [US4] Contract test for --role CLI flag in tests/contract/test_cli_search_role.py
- [X] T042 [US4] Integration test for role-filtered search in tests/integration/test_search_role.py

### Implementation for User Story 4

- [X] T043 [US4] Implement message role filter before corpus building in src/echomine/adapters/openai.py
- [X] T044 [US4] Add --role CLI flag with Literal validation in src/echomine/cli/commands/search.py
- [X] T045 [US4] Add role_filter to JSON output query section in src/echomine/cli/formatters.py
- [X] T046 [US4] Verify all US4 tests pass with pytest tests/ -k role

**Checkpoint**: Role filtering functional - can search user or assistant messages only

---

## Phase 7: User Story 5 - Message Context Snippets (Priority: P3)

**Goal**: Show matched text snippet in search results for quick relevance assessment

**Independent Test**: Search results include ~100 char snippet from matched message

### Tests for User Story 5 (MANDATORY per TDD principle)

- [X] T047 [P] [US5] Unit test for extract_snippet() in tests/unit/search/test_snippet.py
- [X] T048 [P] [US5] Unit test for SearchResult.snippet field in tests/unit/models/test_search.py
- [X] T049 [P] [US5] Contract test for snippet in JSON output in tests/contract/test_cli_search_snippet.py
- [X] T050 [US5] Integration test for snippet extraction in tests/integration/test_search_snippet.py

### Implementation for User Story 5

- [X] T051 [US5] Create src/echomine/search/snippet.py with extract_snippet() function (100 char truncation)
- [X] T052 [US5] Add "+N more matches" indicator logic in src/echomine/search/snippet.py
- [X] T053 [US5] Add "[Content unavailable]" fallback handling in src/echomine/search/snippet.py
- [X] T054 [US5] Integrate snippet extraction into search results in src/echomine/adapters/openai.py
- [X] T055 [US5] Add snippet column to human-readable output in src/echomine/cli/formatters.py
- [X] T056 [US5] Verify all US5 tests pass with pytest tests/ -k snippet

**Checkpoint**: Snippet extraction functional - results show matched text preview

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T057 [P] Add combined feature integration test in tests/integration/test_search_combined.py
- [X] T058 [P] Add performance benchmark for new features in tests/performance/test_advanced_search_benchmark.py
- [X] T058b [P] Add memory profiling tests for SC-006 validation in tests/performance/test_advanced_search_benchmark.py
- [X] T059 [P] Update CLI help text with new flag examples in src/echomine/cli/commands/search.py
- [X] T060 Run full test suite: pytest tests/ --cov=echomine --cov-report=term-missing
- [X] T061 Run mypy --strict src/echomine/ and fix any type errors
- [X] T062 Run ruff check src/ tests/ and fix any linting issues
- [X] T063 Validate quickstart.md examples work correctly
- [X] T064 Update CHANGELOG.md with v1.1.0 features

**Checkpoint**: All quality gates passed, ready for release

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Phase 2 completion
  - User stories can proceed in parallel (if staffed) or sequentially (P1 → P2 → P3)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 5 (P3)**: Can start after Phase 2 - Depends on matched_message_ids from existing search

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (TDD is mandatory)
- Unit tests before integration tests
- Implementation follows test specification
- Story complete before moving to next priority

### Parallel Opportunities

- T001-T004: All SearchQuery field additions can run in parallel (different fields)
- T007-T009: All foundational helpers can run in parallel (different files)
- T011-T014: All US1 tests can run in parallel (different test files)
- T021-T024: All US2 tests can run in parallel
- T030-T033: All US3 tests can run in parallel
- T039-T042: All US4 tests can run in parallel
- T047-T050: All US5 tests can run in parallel
- T057-T058b, T059: All polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD mandatory):
Task: "Unit test for phrase_matches() in tests/unit/search/test_phrase_matching.py"
Task: "Unit test for SearchQuery.phrases field in tests/unit/models/test_search.py"
Task: "Contract test for --phrase CLI flag in tests/contract/test_cli_search_phrase.py"

# After tests fail, launch implementation:
Task: "Implement phrase_matches() case-insensitive substring matching in src/echomine/search/ranking.py"
Task: "Integrate phrase matching into BM25Scorer.score() in src/echomine/search/ranking.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (model extensions)
2. Complete Phase 2: Foundational (helper functions)
3. Complete Phase 3: User Story 1 (Phrase Matching)
4. Complete Phase 4: User Story 2 (Boolean Match Mode)
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy v1.1.0-alpha if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Phrase matching works
3. Add User Story 2 → Test independently → Boolean mode works
4. Add User Story 3 → Test independently → Exclusion works
5. Add User Story 4 → Test independently → Role filter works
6. Add User Story 5 → Test independently → Snippets work
7. Polish → Full validation → Release v1.1.0

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Phrase) + User Story 2 (Match Mode)
   - Developer B: User Story 3 (Exclude) + User Story 4 (Role)
   - Developer C: User Story 5 (Snippets) + Polish
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 and US2 are both P1 priority (core search improvements)
- US3 and US4 are P2 priority (refinement features)
- US5 is P3 priority (UX enhancement)
