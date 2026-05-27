# Tasks: Content Fidelity & Asset Recovery

**Input**: Design documents from `/specs/005-content-fidelity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/content_contract.md, quickstart.md

**Tests**: Included per Constitution Principle III (TDD mandatory). Write failing tests FIRST, verify they fail, then implement.

**Organization**: Tasks grouped by user story. US-1 and US-2 are combined (same code area, same priority, plan Phase 1 bundles them).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create directory structure for new test fixtures

- [x] T001 Create test fixture directories `tests/fixtures/content_fidelity/` and `tests/fixtures/asset_resolver/`

---

## Phase 2: Foundational — Content Type Classification Module

**Purpose**: ContentTypeCategory Literal type and mapping dictionaries used by ALL user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Write failing unit tests for ContentTypeCategory mappings (every raw type to expected category, unknown fallback) and classify_content_type() helper in `tests/unit/models/test_content_types.py`
- [x] T003 [P] Write failing content contract vocabulary tests (all 7 values present, all provider mappings complete, no overlap) in `tests/contract/test_content_contract.py`
- [x] T004 Implement ContentTypeCategory Literal type with 7 values, OPENAI_CATEGORY_MAP dict (13 entries), CLAUDE_CATEGORY_MAP dict (6 entries), and classify_content_type(raw_type, provider) helper in `src/echomine/models/content_types.py`

**Checkpoint**: Category vocabulary module complete. T002 and T003 tests should now pass.

---

## Phase 3: US-1 + US-2 — Content Type Transparency + Accurate Text Extraction (P1) MVP

**Goal**: Every message carries content_type + content_type_category metadata. Placeholder leak eliminated. Multi-part text truncation fixed.

**Independent Test**: Parse an export file and verify every message has content_type and content_type_category metadata with values from the pinned vocabulary. Verify multi-part messages contain all string parts.

### Test Fixtures

- [x] T005 [P] [US1] Create OpenAI content type test fixtures covering all 13 content types (text, multimodal_text, thoughts, reasoning_recap, code, execution_output, tether_quote, tether_browsing_display, user_editable_context, app_pairing_content, system_error, image_asset_pointer, image) plus one unknown type in `tests/fixtures/content_fidelity/openai_content_types.json`
- [x] T006 [P] [US2] Create OpenAI multi-part text test fixtures (1-part, 3-part, mixed string/non-string types, empty parts array) in `tests/fixtures/content_fidelity/openai_multipart.json`

### Tests (Write FIRST, verify they FAIL)

- [x] T007 [P] [US1] Write failing tests for OpenAI content type classification (each type maps to correct category), placeholder elimination (no more `[user_editable_context]` in content), recipient preservation, and content behavior per FR-003 in `tests/unit/test_openai_adapter.py`
- [x] T008 [P] [US2] Write failing tests for multi-part text joining: 3-part message contains all parts with `\n` separator, single-part unchanged, mixed types skip non-strings in `tests/unit/test_openai_adapter.py`
- [x] T009 [P] [US1] Write failing tests for Claude block type classification (text->conversational, thinking->reasoning, tool_use->tool_io, tool_result->tool_io, token_budget->system, unknown_type->unknown) in `tests/unit/test_claude_adapter.py`

### Implementation

- [x] T010 [US1] Modify `_parse_message` and `_parse_multimodal_parts` in OpenAI adapter: persist metadata["content_type"] and metadata["content_type_category"] via OPENAI_CATEGORY_MAP lookup; persist metadata["recipient"] when present; set content="" for reasoning/tool_io/system/unknown, content="[Image]" for media (FR-003); fix multi-part text from parts[0] to "\n".join() of all string parts; log unknown types at DEBUG (FR-017) in `src/echomine/adapters/openai.py`
- [x] T011 [US1] Modify `_extract_content_from_blocks` in Claude adapter: track primary block type for category assignment; persist metadata["content_type"] and metadata["content_type_category"] via CLAUDE_CATEGORY_MAP lookup; set content behavior per FR-003 in `src/echomine/adapters/claude.py`
- [x] T012 [US1] Write cross-provider content fidelity integration tests verifying symmetric content_type_category values across both OpenAI and Claude adapters for equivalent semantic roles in `tests/integration/test_content_fidelity.py`

**Checkpoint**: US-1 + US-2 complete. Every message from both adapters now carries content_type and content_type_category. Multi-part text preserved. Placeholder leak eliminated. Consumers can filter with `content_type_category == "conversational"`.

---

## Phase 4: US-3 — Claude Attachments & File References (P2)

**Goal**: Surface uploaded file text extracts and UUID-only file tombstones from Claude exports.

**Independent Test**: Parse a Claude export with attachments and files, verify metadata["attachments"] and metadata["file_refs"] are populated with correct structure.

### Test Fixtures & Tests

- [x] T013 [P] [US3] Create Claude attachment test fixtures: message with attachments (extracted_content, file_name, file_type, file_size), message with files only (file_uuid, file_name), message with both, message with empty file_name in `tests/fixtures/content_fidelity/claude_attachments.json`
- [x] T014 [P] [US3] Write failing tests for Claude attachment extraction: attachments -> metadata["attachments"], files -> metadata["file_refs"], both populated independently, empty file_name preserved in tombstone, attachment-only message (no text blocks) -> content_type_category="attachment", text+attachment message -> content_type_category="conversational" with attachments in metadata (category-artifact orthogonality) in `tests/unit/test_claude_adapter.py`

### Implementation

- [x] T015 [US3] Modify `_parse_message` in Claude adapter: extract attachments field -> metadata["attachments"] list of {file_name, file_type, file_size, extracted_content}; extract files field -> metadata["file_refs"] list of {file_uuid, file_name}; apply message-level post-classification — if attachments present with no conversational text blocks, override content_type_category to "attachment" (category-artifact orthogonality) in `src/echomine/adapters/claude.py`

**Checkpoint**: US-3 complete. Claude attachments with extracted text and file tombstones are accessible via metadata.

---

## Phase 5: US-4 — Reasoning & Voice Block Recovery (P2)

**Goal**: Symmetric thinking/reasoning metadata across providers. Voice note transcriptions included as content. Unknown block types logged, not silently dropped.

**Independent Test**: Parse exports containing thinking blocks (Claude), thoughts/reasoning_recap (OpenAI), and voice notes. Verify metadata["thinking"] populated for both providers with same key. Verify voice note text in Message.content.

### Test Fixtures

- [x] T016 [P] [US4] Create Claude thinking block test fixtures: message with thinking block (thinking text, summaries, cut_off, truncated), message with only thinking blocks (no text), message with token_budget block in `tests/fixtures/content_fidelity/claude_thinking.json`
- [x] T017 [P] [US4] Create Claude voice note test fixtures: message with voice_note block containing transcribed text in `tests/fixtures/content_fidelity/claude_voice_note.json`

### Tests (Write FIRST)

- [x] T018 [P] [US4] Write failing tests for Claude: thinking block -> metadata["thinking"] with content/summaries/cut_off/truncated, mixed text+thinking -> content_type_category="conversational" with metadata["thinking"] populated (category-artifact orthogonality), voice_note -> text in Message.content as conversational, token_budget -> skipped + DEBUG log, unknown block -> skipped + DEBUG log in `tests/unit/test_claude_adapter.py`
- [x] T019 [P] [US4] Write failing tests for OpenAI: thoughts -> metadata["thinking"]["content"] + content="" + category=reasoning, reasoning_recap -> same handling, audio transcription parts in multimodal_text -> text in Message.content in `tests/unit/test_openai_adapter.py`

### Implementation

- [x] T020 [US4] Modify `_extract_content_from_blocks` in Claude adapter: thinking blocks -> metadata["thinking"] dict with content, summaries, cut_off, truncated fields; mixed text+thinking -> content_type_category stays "conversational", thinking orthogonal in metadata (category-artifact orthogonality); voice_note blocks -> include transcribed text in content; unknown/token_budget blocks -> structlog DEBUG log + skip in `src/echomine/adapters/claude.py`
- [x] T021 [US4] Modify `_parse_message` in OpenAI adapter: thoughts/reasoning_recap content types -> metadata["thinking"] = {"content": reasoning_text}, content="", category=reasoning; audio transcription part-objects in multimodal_text -> include transcript in Message.content in `src/echomine/adapters/openai.py`

**Checkpoint**: US-4 complete. Reasoning content accessible via metadata["thinking"] from both providers (symmetric key). Voice notes in content. Unknown blocks logged, not dropped.

---

## Phase 6: US-5 — Hidden Message Filtering (P3)

**Goal**: Surface OpenAI's is_visually_hidden_from_conversation flag so consumers can filter.

**Independent Test**: Parse an OpenAI export with hidden messages. Verify metadata["is_visually_hidden"] is True on hidden messages and absent/False on others.

### Test Fixtures & Tests

- [x] T022 [P] [US5] Create OpenAI hidden message test fixtures: message with is_visually_hidden_from_conversation=true, message without flag, message with flag=false in `tests/fixtures/content_fidelity/openai_hidden.json`
- [x] T023 [P] [US5] Write failing tests for hidden message flag: hidden -> metadata["is_visually_hidden"]=True, non-hidden -> key absent, hidden messages still in output (additive only) in `tests/unit/test_openai_adapter.py`

### Implementation

- [x] T024 [US5] Modify `_parse_message` in OpenAI adapter: check message_data.get("metadata", {}).get("is_visually_hidden_from_conversation"); set metadata["is_visually_hidden"]=True when present and true in `src/echomine/adapters/openai.py`

**Checkpoint**: US-5 complete. Hidden messages identifiable via metadata flag. Still included in output by default.

---

## Phase 7: US-6 — OpenAI Asset Resolution (P3)

**Goal**: Resolve image/audio asset pointers to actual files in the export bundle. Detect true file types via magic bytes.

**Independent Test**: Given a sample export directory with binary files, verify the resolver maps asset pointers to file paths with correct type detection, including mismatched extensions.

### Test Fixtures & Tests

- [x] T025 [P] [US6] Create asset resolver test fixtures: tiny valid PNG file as `file_abc123-test.png`, tiny valid WAV as `file_def456-test.wav`, tiny valid PNG saved as `file_ghi789-test.dat` (mismatched extension) in `tests/fixtures/asset_resolver/`
- [x] T026 [P] [US6] Write failing unit tests for resolve_asset(): sediment:// scheme -> correct file, file-service:// scheme -> correct file, mismatched extension -> detected via magic bytes, WAV audio -> discoverable, missing file -> returns None, ResolvedAsset fields populated in `tests/unit/test_asset_resolver.py`
- [x] T027 [P] [US6] Write failing tests for ImageRef content_type Literal expansion to accept "image" in addition to "image_asset_pointer" in `tests/unit/test_openai_adapter.py`

### Implementation

- [x] T028 [P] [US6] Expand ImageRef content_type Literal from Literal["image_asset_pointer"] to Literal["image_asset_pointer", "image"] in `src/echomine/models/image.py`
- [x] T029 [US6] Create ResolvedAsset Pydantic model (path, detected_type, original_extension, file_id) and resolve_asset(export_dir, asset_pointer) function: strip URI schemes (sediment://, file-service://), match file ID prefix in directory, sniff magic bytes (PNG/JPEG/WebP/GIF/WAV signatures) for true type in `src/echomine/utils/asset_resolver.py`
- [x] T030 [P] [US6] Write failing test for DALL-E metadata (gen_id, prompt, seed) preservation on ImageRef in `tests/unit/test_openai_adapter.py`
- [x] T031 [US6] Verify and fix DALL-E metadata preservation in _parse_multimodal_parts in `src/echomine/adapters/openai.py`

**Checkpoint**: US-6 complete. Asset pointers resolvable to files. True file types detected. Non-image binaries (WAV) discoverable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and validation across all stories

- [x] T032 [P] Run mypy --strict on all new and modified source files (`src/echomine/models/content_types.py`, `src/echomine/utils/asset_resolver.py`, `src/echomine/adapters/openai.py`, `src/echomine/adapters/claude.py`, `src/echomine/models/image.py`), fix any type errors
- [x] T033 [P] Run ruff check and ruff format on all new and modified files in `src/` and `tests/`
- [x] T034 Validate quickstart.md code examples compile and run against test fixtures
- [x] T035 [P] Verify backward compatibility: all pre-existing tests pass unchanged with no modifications
- [x] T036 Run full test suite with coverage report (`pytest --cov=echomine --cov-report=term-missing`), verify >80% coverage on new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **US-1 + US-2 (Phase 3)**: Depends on Foundational (T004) — MVP delivery
- **US-3 (Phase 4)**: Depends on Phase 3 (Claude adapter has content_type from T011)
- **US-4 (Phase 5)**: Depends on Phase 3 (both adapters have content_type infrastructure from T010, T011)
- **US-5 (Phase 6)**: Depends on Phase 3 (OpenAI adapter has content_type from T010)
- **US-6 (Phase 7)**: Depends on Phase 3 (OpenAI adapter baseline from T010); T028 can start after Phase 2
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US-1 + US-2 (P1)**: Start after Foundational — no cross-story dependencies
- **US-3 (P2)**: Start after US-1+US-2 — needs Claude adapter content_type infrastructure
- **US-4 (P2)**: Start after US-1+US-2 — needs both adapters' content_type infrastructure; can run in parallel with US-3 (different functions: US-3 modifies `_parse_message`, US-4 modifies `_extract_content_from_blocks`)
- **US-5 (P3)**: Start after US-4 — both modify `_parse_message` in openai.py
- **US-6 (P3)**: Start after US-1+US-2 — T028 (ImageRef Literal expansion) is a safe one-line change that can be pulled into Phase 2 if `image` content type triggers ImageRef creation before Phase 7; T029 (resolver) is independent; T030-T031 depend on T010. Can run in parallel with US-3/US-4/US-5

### Within Each User Story

1. Create test fixtures (parallel, different files)
2. Write failing tests (parallel, verify they FAIL)
3. Implement production code (sequential within same file)
4. Verify tests pass (GREEN)
5. Story complete before moving to next priority

### Parallel Opportunities

**Within Phase 3 (US-1 + US-2)**:
- T005, T006 in parallel (different fixture files)
- T007, T008, T009 in parallel (different test focus, same files but additive)
- T010, T011 in parallel (different adapter files)

**Within Phase 5 (US-4)**:
- T016, T017 in parallel (different fixture files)
- T018, T019 in parallel (different adapter test files)
- T020, T021 in parallel (different adapter files: claude.py vs openai.py)

**Within Phase 7 (US-6)**:
- T025, T026, T027 all parallel (different files)
- T028, T029 in parallel (different files: image.py vs asset_resolver.py)

**Cross-Story**:
- US-3 and US-4 can run in parallel (different functions in claude.py)
- US-6 can run in parallel with US-3/US-4/US-5 (different files entirely)

---

## Parallel Example: US-1 + US-2

```
# Launch all fixture creation together:
Task T005: "Create OpenAI content type fixtures in tests/fixtures/content_fidelity/openai_content_types.json"
Task T006: "Create OpenAI multi-part text fixtures in tests/fixtures/content_fidelity/openai_multipart.json"

# Launch all test writing together (after fixtures):
Task T007: "Write failing OpenAI content type tests in tests/unit/test_openai_adapter.py"
Task T008: "Write failing multi-part text tests in tests/unit/test_openai_adapter.py"
Task T009: "Write failing Claude block classification tests in tests/unit/test_claude_adapter.py"

# Launch adapter implementations together (after tests):
Task T010: "Implement OpenAI adapter content type + multi-part fix in src/echomine/adapters/openai.py"
Task T011: "Implement Claude adapter content type classification in src/echomine/adapters/claude.py"
```

---

## Implementation Strategy

### MVP First (US-1 + US-2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (content_types.py module)
3. Complete Phase 3: US-1 + US-2
4. **STOP and VALIDATE**: Every message has content_type + content_type_category. Multi-part text preserved. Placeholder leak eliminated.
5. Consumers can already filter to `conversational` messages with one check

### Incremental Delivery

1. Setup + Foundational -> Classification infrastructure ready
2. US-1 + US-2 -> MVP! Consumer-facing filtering works (T001-T012)
3. US-3 -> Claude attachments accessible (T013-T015)
4. US-4 -> Reasoning/voice surfaced, symmetric across providers (T016-T021)
5. US-5 -> Hidden messages identifiable (T022-T024)
6. US-6 -> Asset pointers resolvable to files (T025-T030)
7. Polish -> Quality gates validated (T031-T035)

Each story adds value without breaking previous stories (FR-018: additive contract).

### Parallel Team Strategy

With multiple developers after Foundational completes:

- Developer A: US-1 + US-2 (MVP, must complete first)
- Then after MVP:
  - Developer A: US-3 (Claude adapter: _parse_message)
  - Developer B: US-4 (Claude adapter: _extract_content_from_blocks + OpenAI adapter: _parse_message)
  - Developer C: US-6 (new files: image.py, asset_resolver.py)
- After US-4 completes:
  - Developer B: US-5 (OpenAI adapter: _parse_message)

---

## FR Traceability

| FR | Description | Task(s) |
|----|-------------|---------|
| FR-001 | content_type on every message | T010, T011 |
| FR-002 | content_type_category from vocabulary | T004, T010, T011 |
| FR-003 | Content behavior per category | T010, T011 |
| FR-004 | Preserve recipient | T010 |
| FR-005 | Join all multi-part text | T010 |
| FR-006 | Claude thinking metadata | T020 |
| FR-007 | OpenAI reasoning metadata (symmetric) | T021 |
| FR-008 | Claude voice_note text | T020 |
| FR-009 | OpenAI audio transcription text | T021 |
| FR-010 | Claude attachments | T015 |
| FR-011 | Claude file_refs | T015 |
| FR-012 | is_visually_hidden flag | T024 |
| FR-013 | DALL-E metadata on ImageRef | T030, T031 |
| FR-014 | Asset resolver | T029 |
| FR-015 | Magic byte sniffing | T029 |
| FR-016 | Non-image binary support | T029 |
| FR-017 | DEBUG logging for unknown types | T010, T020 |
| FR-018 | Additive/non-breaking | T035 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- US-2 is absorbed into US-1 phase (one-line fix in same function)
- TDD mandatory per Constitution Principle III: tests FAIL before implementation
- All metadata changes are additive — existing tests must pass unchanged (T034)
- Commit after each task or logical group per Constitution
