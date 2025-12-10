# Implementation Plan: Claude Export Adapter

**Branch**: `004-claude-adapter` | **Date**: 2025-12-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-claude-adapter/spec.md`

## Summary

Implement a stateless `ClaudeAdapter` for parsing Anthropic Claude conversation exports with feature parity to the existing `OpenAIAdapter`. The adapter will use ijson streaming for O(1) memory efficiency, share existing Pydantic models (`Conversation`, `Message`, `SearchResult`), and implement the `ConversationProvider` protocol. CLI will support provider auto-detection based on export schema structure.

## Technical Context

**Language/Version**: Python 3.12+ (existing stack, mypy --strict compliant)
**Primary Dependencies**: Pydantic v2.6+, ijson 3.2+, typer 0.9+, rich 13.0+, structlog 23.0+
**Storage**: File system only (JSON exports, no database)
**Testing**: pytest with pytest-cov, pytest-mock, pytest-benchmark
**Target Platform**: Cross-platform (macOS, Linux, Windows)
**Project Type**: Single project - library + CLI
**Performance Goals**: Search <30s for 10K conversations, O(1) memory streaming
**Benchmark Hardware**: Apple M1 (or equivalent), 8GB RAM, SSD storage
**CI Benchmark Environment**: GitHub Actions ubuntu-latest runner (2-core, 7GB RAM)
**Constraints**: <8GB RAM for 10K conversations, <100MB working set per conversation
**Scale/Scope**: Support Claude exports up to 1GB+ with thousands of conversations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First | PASS | `ClaudeAdapter` in `src/echomine/adapters/claude.py`, CLI wraps library |
| II. CLI Interface Contract | PASS | Auto-detection via `--provider` flag, stdout/stderr separation |
| III. TDD | PASS | Implementation phases restructured: tests FIRST, then implementation (RED-GREEN-REFACTOR) |
| IV. Observability | PASS | structlog for WARNING on malformed entries |
| V. Simplicity/YAGNI | PASS | Reuse existing models, stdlib over dependencies (datetime.fromisoformat) |
| VI. Strict Typing | PASS | mypy --strict, Pydantic v2, no `Any` in public API |
| VII. Multi-Provider Pattern | PASS | Implements `ConversationProvider` protocol |
| VIII. Memory Efficiency | PASS | ijson streaming, O(1) memory, context managers for resource cleanup (R-007) |

**Gate Status**: PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/004-claude-adapter/
├── plan.md              # This file
├── research.md          # Phase 0 output (Claude export schema analysis)
├── data-model.md        # Phase 1 output (field mappings)
├── quickstart.md        # Phase 1 output (usage examples)
├── contracts/           # Phase 1 output (CLI and library contracts)
│   ├── library_api.md   # Library API contract
│   └── cli_spec.md      # CLI contract with auto-detection
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/echomine/
├── adapters/
│   ├── __init__.py      # Export ClaudeAdapter
│   ├── openai.py        # Existing OpenAI adapter (no changes)
│   └── claude.py        # NEW: Claude adapter implementation
├── models/              # No changes - reuse existing models
│   ├── conversation.py  # Shared Conversation model
│   ├── message.py       # Shared Message model
│   └── protocols.py     # ConversationProvider protocol
├── cli/
│   └── app.py           # Add provider auto-detection logic
└── __init__.py          # Export ClaudeAdapter

tests/
├── unit/
│   └── adapters/
│       └── test_claude.py       # NEW: ClaudeAdapter unit tests
├── integration/
│   └── test_claude_integration.py  # NEW: End-to-end Claude tests
├── contract/
│   └── test_claude_contract.py  # NEW: FR validation tests
├── performance/
│   └── test_claude_performance.py  # NEW: Benchmarks
└── fixtures/
    └── claude/
        ├── sample_export.json   # NEW: Claude export fixture
        └── malformed_export.json # NEW: Graceful degradation tests
```

**Structure Decision**: Single project - new adapter file added to existing `adapters/` directory following established pattern.

## Complexity Tracking

> No violations - using existing patterns and shared models.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

# Phase 0: Research

## Claude Export Schema Analysis

Based on analysis of actual Claude export (`data/anthropic/conversations.json`):

### Conversation Schema

```json
{
  "uuid": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
  "name": "Freedom fighter portrait",
  "summary": "...",
  "created_at": "2025-10-01T18:42:27.303515Z",
  "updated_at": "2025-10-01T18:42:33.904627Z",
  "account": {"uuid": "..."},
  "chat_messages": [...]
}
```

### Message Schema

```json
{
  "uuid": "caaac42b-b9a2-4555-96fb-4d15537abc8b",
  "text": "Generate a picture of a freedom fighter",
  "content": [
    {
      "start_timestamp": "2025-10-01T18:42:28.365328Z",
      "stop_timestamp": "2025-10-01T18:42:28.365328Z",
      "flags": null,
      "type": "text",
      "text": "Generate a picture of a freedom fighter",
      "citations": []
    }
  ],
  "sender": "human",
  "created_at": "2025-10-01T18:42:28.370875Z",
  "updated_at": "2025-10-01T18:42:28.370875Z",
  "attachments": [],
  "files": []
}
```

### Key Differences from OpenAI

| Field | Claude | OpenAI | Mapping |
|-------|--------|--------|---------|
| Conversation ID | `uuid` | `id` | Direct map |
| Title | `name` | `title` | Direct map (empty string preserved) |
| Messages | `chat_messages` | `mapping` (tree) | Array vs tree structure |
| Message ID | `uuid` | `id` | Direct map |
| Content | `content` blocks or `text` | `content.parts` | Parse content blocks first, fallback to text |
| Role | `sender` ("human"/"assistant") | `author.role` | Normalize human→user |
| Timestamps | ISO 8601 string | Unix float | Parse ISO 8601 |
| Structure | Linear array | Tree (parent/child) | Linear (parent_id=None) |

### Content Block Strategy (per spec clarifications)

1. **Primary**: Extract text from `content` array blocks where `type="text"`
2. **Skip**: `tool_use` and `tool_result` blocks (feature parity with OpenAI)
3. **Fallback**: Use `text` field if `content` array is empty/missing
4. **Concatenate**: Multiple text blocks joined with newline

## Research Decisions

### R-001: Content Extraction Strategy

**Decision**: Parse `content` blocks, not `text` field
**Rationale**: 92% of messages have identical content, but 8% have richer tool context in `content` blocks. Using `content` is more accurate and future-proof.
**Alternatives Rejected**: Using `text` field only would lose tool context for 8% of messages.

### R-002: Linear Message Structure

**Decision**: Set `parent_id=None` for all Claude messages
**Rationale**: Claude exports are linear (no branching/regeneration visible in export). OpenAI has tree structure via `mapping` with parent/children.
**Alternatives Rejected**: Attempting to infer parent/child from timestamps would be unreliable and not match source data.

### R-003: Role Normalization

**Decision**: Map `sender: "human"` → `role: "user"`, keep `"assistant"` unchanged
**Rationale**: Aligns with OpenAI normalization pattern. Consistent with existing Message model.
**Alternatives Rejected**: Custom Claude roles would break shared model constraint.

### R-004: Timestamp Parsing

**Decision**: Use `datetime.fromisoformat()` for ISO 8601 timestamps
**Rationale**: Claude uses ISO 8601 strings (e.g., "2025-10-01T18:42:27.303515Z"), unlike OpenAI's Unix floats. Python's `datetime.fromisoformat()` handles this well and is available in stdlib (no external dependencies).
**Alternatives Rejected**: `dateutil.parser.isoparse()` would require python-dateutil dependency (violates YAGNI - stdlib is sufficient for standard ISO 8601 formats). Manual parsing would be error-prone for edge cases.

### R-005: Empty Title Handling

**Decision**: Preserve empty string titles (don't default to "Untitled")
**Rationale**: Data integrity per Constitution VI. Display logic can show "(Untitled)" placeholder per FR-034.
**Alternatives Rejected**: Replacing empty with placeholder at parse time pollutes data.

### R-006: Provider Auto-Detection

**Decision**: Detect based on `chat_messages` key (Claude) vs `mapping` key (OpenAI)
**Rationale**: These are mutually exclusive structural differences, reliable for detection.
**Alternatives Rejected**: Checking `uuid` vs `id` is less reliable (both could have UUIDs).

### R-007: Resource Cleanup Strategy

**Decision**: Use context managers (`with` statements) for all file operations, ensure cleanup on exceptions
**Rationale**: Constitution Principle VIII requires proper resource cleanup. File handles must be closed even on early termination or exceptions.
**Implementation**: Follow existing OpenAI adapter pattern using `try/finally` blocks within context managers.
**Pattern Reference**: Follows resource cleanup pattern established in 003-baseline-enhancements (FR-130-133 in that feature's spec)

### R-008: Progress Callback Frequency

**Decision**: Invoke progress_callback every 100 items OR every 100ms (whichever comes first)
**Rationale**: Matches existing OpenAI adapter pattern from FR-068, FR-069. Provides responsive progress reporting for both small and large files without performance overhead.
**Implementation**: Track item count and elapsed time, call callback when either threshold is met.
**Alternatives Rejected**: Fixed-count-only callbacks would be unresponsive for large files with slow parsing.

---

# Phase 1: Design & Contracts

## Data Model Mappings

See `data-model.md` for complete field mapping specification.

### Claude → Conversation Mapping

| Claude Field | Conversation Field | Transform |
|--------------|-------------------|-----------|
| `uuid` | `id` | Direct copy |
| `name` | `title` | Direct copy (preserve empty) |
| `created_at` | `created_at` | `datetime.fromisoformat()` |
| `updated_at` | `updated_at` | `datetime.fromisoformat()` or None |
| `chat_messages` | `messages` | Parse each, see Message mapping |
| `summary` | `metadata["summary"]` | Optional, store in metadata |
| `account` | `metadata["account"]` | Optional, store in metadata |

### Claude → Message Mapping

| Claude Field | Message Field | Transform |
|--------------|---------------|-----------|
| `uuid` | `id` | Direct copy |
| `content[*].text` | `content` | Concatenate text blocks, fallback to `text` |
| `sender` | `role` | `"human"→"user"`, `"assistant"→"assistant"` |
| `created_at` | `timestamp` | `datetime.fromisoformat()` |
| `attachments`, `files` | `images` | Map to ImageRef if applicable |
| N/A | `parent_id` | Always `None` (linear structure) |
| `updated_at` | `metadata["updated_at"]` | Store in metadata |

## API Contracts

See `contracts/library_api.md` for complete library API contract.
See `contracts/cli_spec.md` for CLI contract with auto-detection.

### Library API Summary

```python
from echomine import ClaudeAdapter, SearchQuery
from pathlib import Path

adapter = ClaudeAdapter()

# Stream conversations (O(1) memory)
for conv in adapter.stream_conversations(Path("conversations.json")):
    print(f"{conv.title}: {conv.message_count} messages")

# Search with BM25 ranking
query = SearchQuery(keywords=["algorithm"], limit=10)
for result in adapter.search(Path("conversations.json"), query):
    print(f"{result.score:.2f}: {result.conversation.title}")

# Get by ID
conv = adapter.get_conversation_by_id(Path("conversations.json"), "uuid-here")

# Get message with context
result = adapter.get_message_by_id(Path("conversations.json"), "msg-uuid")
```

### CLI Contract Summary

```bash
# Auto-detection (default)
echomine list conversations.json  # Detects Claude format

# Explicit provider
echomine list conversations.json --provider claude

# Search with all existing flags
echomine search conversations.json --keywords "python" --limit 10

# Export works identically
echomine export conversations.json <uuid> --output chat.md
```

## Implementation Phases

**TDD Workflow Note**: Following Constitution Principle III, ALL implementation tasks follow RED-GREEN-REFACTOR cycle:
1. **RED**: Write failing test FIRST (verify it fails)
2. **GREEN**: Write minimal implementation to pass test
3. **REFACTOR**: Improve code while keeping tests green

Each phase below integrates test creation BEFORE implementation tasks.

### Phase 0: Test Infrastructure Setup

1. **T-001**: Create test fixtures directory structure (`tests/fixtures/claude/`)
2. **T-002**: Create `sample_export.json` fixture (3-5 conversations with varied content)
3. **T-003**: Create `malformed_export.json` fixture (missing fields, invalid timestamps)
4. **T-004**: Create `tool_messages.json` fixture (tool_use/tool_result blocks)

### Phase 1: Core Parsing (P1 - TDD Cycle)

**Tests First (RED)**:
5. **T-005**: Write failing tests for conversation parsing (FR-001 to FR-010)
6. **T-006**: Write failing tests for message parsing (FR-011 to FR-020)
7. **T-007**: Write failing tests for content block extraction (FR-015, FR-015a, FR-015b)

**Implementation (GREEN)**:
8. **T-008**: Create `src/echomine/adapters/claude.py` with class skeleton
9. **T-009**: Implement `_parse_conversation()` method (pass T-005 tests)
10. **T-010**: Implement `_parse_message()` method (pass T-006 tests)
11. **T-011**: Implement `_extract_content_from_blocks()` helper (pass T-007 tests)
12. **T-012**: Implement `_normalize_role()` helper
13. **T-013**: Implement `stream_conversations()` with ijson streaming

**Verification (GREEN)**:
14. **T-014**: Verify all Phase 1 tests pass, code coverage >80%

### Phase 2: Search & Retrieval (P1/P2 - TDD Cycle)

**Tests First (RED)**:
15. **T-015**: Write failing tests for search() with BM25 ranking (FR-021 to FR-035)
16. **T-016**: Write failing tests for get_conversation_by_id() (FR-036 to FR-040)
17. **T-017**: Write failing tests for get_message_by_id() (FR-041 to FR-045)

**Implementation (GREEN)**:
18. **T-018**: Implement `search()` with BM25 ranking (pass T-015 tests)
19. **T-019**: Implement `get_conversation_by_id()` (pass T-016 tests)
20. **T-020**: Implement `get_message_by_id()` (pass T-017 tests)
21. **T-021**: Add ClaudeAdapter export to `__init__.py`

**Verification (GREEN)**:
22. **T-022**: Verify all Phase 2 tests pass, integration tests green

### Phase 3: CLI Integration (P2 - TDD Cycle)

**Tests First (RED)**:
23. **T-023**: Write failing tests for provider auto-detection (FR-046 to FR-050)
24. **T-024**: Write failing tests for --provider flag behavior

**Implementation (GREEN)**:
25. **T-025**: Implement provider auto-detection in `cli/app.py` (pass T-023 tests)
26. **T-026**: Add `--provider` flag to relevant commands (pass T-024 tests)
27. **T-027**: Update error messages for unrecognized formats

**Verification (GREEN)**:
28. **T-028**: Verify all CLI tests pass, end-to-end contract tests green

### Phase 4: Performance & Contract Validation

29. **T-029**: Write performance benchmarks for 1000+ conversation files
30. **T-030**: Write contract tests validating all FRs (FR-001 to FR-055)
31. **T-031**: Run performance benchmarks (verify <30s search, O(1) memory)
32. **T-032**: Verify mypy --strict passes (zero errors)
33. **T-033**: Update documentation (README, API docs, quickstart.md)

## Test Strategy

### Test Fixtures Required

1. **sample_export.json**: 3-5 conversations with varied content (text, empty, long)
2. **malformed_export.json**: Missing fields, invalid timestamps, empty arrays
3. **large_export.json**: 1000+ conversations for performance testing (generated)
4. **tool_messages.json**: Messages with tool_use/tool_result blocks

### Contract Tests (per FR)

| FR Range | Test File | Coverage |
|----------|-----------|----------|
| FR-001-010 | test_claude_parsing.py | Conversation parsing |
| FR-011-020 | test_claude_messages.py | Message parsing |
| FR-021-035 | test_claude_search.py | Search functionality |
| FR-036-040 | test_claude_retrieval.py | get_conversation_by_id |
| FR-041-045 | test_claude_message_retrieval.py | get_message_by_id |
| FR-046-050 | test_provider_detection.py | CLI auto-detection |
| FR-051-055 | test_protocol_compliance.py | ConversationProvider protocol |

---

# Post-Planning Checklist

- [x] Technical Context fully specified
- [x] Constitution Check passes (no violations)
- [x] Research decisions documented (R-001 through R-006)
- [x] Data model mappings defined
- [x] API contracts specified
- [x] Test strategy outlined
- [ ] Tasks to be generated via `/speckit.tasks`

**Recommended Next Step**: `/speckit.tasks` to generate task breakdown
