# Implementation Plan: Content Fidelity & Asset Recovery

**Branch**: `005-content-fidelity` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-content-fidelity/spec.md`

## Summary

echomine silently drops or corrupts conversation data across both OpenAI and Claude adapters. This plan introduces a provider-agnostic content classification contract (`content_type` + `content_type_category`), fixes multi-part text truncation, surfaces Claude attachments/thinking/voice blocks, adds hidden message flags, and provides an OpenAI asset resolver. All changes are additive and non-breaking.

## Technical Context

**Language/Version**: Python 3.12+ (existing stack)
**Primary Dependencies**: Pydantic v2.6+, ijson 3.2+, typer 0.9+, rich 13.0+, structlog 23.0+
**Storage**: File system only (JSON exports, no database)
**Testing**: pytest with pytest-cov, pytest-mock, pytest-benchmark
**Target Platform**: Linux/macOS (CLI + library)
**Project Type**: Library + CLI
**Performance Goals**: 1.6GB search <30s, 10K conversations on 8GB RAM, O(1) memory
**Constraints**: O(1) memory usage, mypy --strict zero errors, existing performance contracts unchanged
**Scale/Scope**: Real exports tested: 280 conversations / 29K nodes (OpenAI), 338+ blocks (Claude)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First Architecture | PASS | All new logic in `src/echomine/` library; CLI unchanged |
| II. CLI Interface Contract | PASS | No CLI changes; new metadata is library-level. Existing `--json` output gains new fields additively |
| III. Test-Driven Development | PASS | TDD enforced: failing tests before implementation for each AC |
| IV. Observability & Debuggability | PASS | FR-017: unknown block types logged at DEBUG. `unknown` category is the schema-drift canary |
| V. Simplicity & YAGNI | PASS | Category vocabulary is a dict lookup, not a class hierarchy. Asset resolver is a single function. No premature abstractions |
| VI. Strict Typing Mandatory | PASS | `ContentTypeCategory` will be a `Literal` type. All new metadata fields typed. mypy --strict enforced |
| VII. Multi-Provider Adapter Pattern | PASS | Symmetric handling: both adapters populate `content_type`, `content_type_category`, `thinking` using same metadata keys. Category vocabulary is provider-agnostic |
| VIII. Memory Efficiency & Streaming | PASS | No new memory allocations beyond per-message metadata dict entries. `extracted_content` included inline (clarification: accepted, real-world sizes modest). O(1) streaming unchanged |

No violations. No complexity justifications needed.

## Project Structure

### Documentation (this feature)

```text
specs/005-content-fidelity/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: data model changes
├── quickstart.md        # Phase 1: usage examples
├── contracts/           # Phase 1: API contracts
│   └── content_contract.md  # Content type category vocabulary contract
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (changes to existing structure)

```text
src/echomine/
├── models/
│   ├── message.py          # MODIFY: metadata type guidance (no structural changes)
│   ├── image.py            # MODIFY: add DALL-E metadata fields to ImageRef
│   └── content_types.py    # NEW: ContentTypeCategory literal, category mapping dicts
├── adapters/
│   ├── openai.py           # MODIFY: _parse_message, _parse_multimodal_parts
│   └── claude.py           # MODIFY: _extract_content_from_blocks, _parse_message
└── utils/
    └── asset_resolver.py   # NEW: asset pointer → file path resolver

tests/
├── unit/
│   ├── models/
│   │   └── test_content_types.py   # NEW: category mapping tests
│   ├── test_openai_adapter.py      # MODIFY: add content fidelity tests
│   ├── test_claude_adapter.py      # MODIFY: add content fidelity tests
│   └── test_asset_resolver.py      # NEW: resolver unit tests
├── integration/
│   └── test_content_fidelity.py    # NEW: cross-provider fidelity tests
├── contract/
│   └── test_content_contract.py    # NEW: category vocabulary contract tests
└── fixtures/
    ├── content_fidelity/           # NEW: test fixtures directory
    │   ├── openai_multipart.json   # Multi-part text messages
    │   ├── openai_content_types.json # All content types
    │   ├── openai_hidden.json      # Hidden messages
    │   ├── claude_thinking.json    # Thinking blocks
    │   ├── claude_attachments.json # Attachments + file refs
    │   └── claude_voice_note.json  # Voice note blocks
    └── asset_resolver/             # NEW: resolver test fixtures
        ├── file_abc123-test.png    # Sample image (tiny)
        ├── file_def456-test.wav    # Sample audio (tiny)
        └── file_ghi789-test.dat   # Mismatched extension (actually PNG)
```

**Structure Decision**: Single project structure (existing). No new top-level directories. New module `content_types.py` for the category vocabulary. New module `asset_resolver.py` for the resolver. All other changes modify existing files.

## Implementation Phases

### Phase 1: Content Type Contract + Multi-Part Fix (AC-1, AC-2)

**Scope**: Highest leverage — introduces the category vocabulary, stops placeholder leak, fixes multi-part truncation.

**Changes**:
1. `src/echomine/models/content_types.py` (NEW):
   - `ContentTypeCategory` Literal type with 7 values
   - `OPENAI_CATEGORY_MAP: dict[str, ContentTypeCategory]` mapping raw types → categories
   - `CLAUDE_CATEGORY_MAP: dict[str, ContentTypeCategory]` mapping block types → categories
   - `classify_content_type(raw_type, provider)` helper function

2. `src/echomine/adapters/openai.py` (MODIFY `_parse_message`):
   - Persist `metadata["content_type"]` = raw `content_type`
   - Persist `metadata["content_type_category"]` via lookup
   - Persist `metadata["recipient"]` when present
   - Set `content=""` for non-conversational types (instead of `f"[{content_type}]"`)
   - Fix multi-part: `"\n".join(p for p in content_parts if isinstance(p, str))` instead of `content_parts[0]`

3. `src/echomine/adapters/claude.py` (MODIFY `_extract_content_from_blocks`):
   - Track primary block type for category assignment
   - Persist `metadata["content_type"]` and `metadata["content_type_category"]`

**Tests** (TDD — write first):
- Category mapping: every raw type maps to expected category
- Unknown types → `unknown` category, `content=""`
- Multi-part text: 1-part, 3-part, mixed-type parts
- OpenAI placeholder elimination: `[user_editable_context]` no longer appears
- Claude block categories: text→conversational, thinking→reasoning, etc.

### Phase 2: Claude Attachments & File References (AC-6)

**Scope**: Surface `extracted_content` and file tombstones from Claude exports.

**Changes**:
1. `src/echomine/adapters/claude.py` (MODIFY `_parse_message`):
   - Extract `attachments` field → `metadata["attachments"]` list
   - Extract `files` field → `metadata["file_refs"]` list
   - Each attachment: `{file_name, file_type, file_size, extracted_content}`
   - Each file_ref: `{file_uuid, file_name}`
   - Message-level post-classification: if attachments present with no conversational text blocks → override `content_type_category` to `attachment` (category-artifact orthogonality)

**Tests**:
- Message with attachments → metadata populated
- Message with files only → file_refs populated
- Message with both → both populated independently
- Empty file_name preserved in tombstone
- Attachment-only message (no text blocks) → `content_type_category = "attachment"`
- Text + attachment message → `content_type_category = "conversational"`, attachments in metadata

### Phase 3: Reasoning & Voice Blocks (AC-3)

**Scope**: Symmetric thinking/reasoning metadata across providers + voice note content.

**Changes**:
1. `src/echomine/adapters/claude.py` (MODIFY `_extract_content_from_blocks`):
   - `thinking` blocks → `metadata["thinking"]` with `summaries`, `cut_off`, `truncated`
   - `voice_note` blocks → include transcribed text in content
   - Unknown blocks → log at DEBUG, skip

2. `src/echomine/adapters/openai.py` (MODIFY `_parse_message`):
   - `thoughts`/`reasoning_recap` → `metadata["thinking"]`, `content=""`
   - Audio transcription parts in multimodal → include in content

**Tests**:
- Claude thinking block → metadata["thinking"] populated, content excluded
- OpenAI thoughts → same metadata key, content=""
- Claude voice_note → content includes transcript
- Unknown block types → logged at DEBUG
- Symmetric: same metadata key name across providers

### Phase 4: Hidden Message Flag (AC-4)

**Scope**: Small, additive metadata flag for OpenAI hidden messages.

**Changes**:
1. `src/echomine/adapters/openai.py` (MODIFY `_parse_message`):
   - Check `message_data.get("metadata", {}).get("is_visually_hidden_from_conversation")`
   - Set `metadata["is_visually_hidden"] = True` when flag is present and true

**Tests**:
- Hidden message → flag set
- Non-hidden message → flag absent
- Hidden messages still in output (additive only)

### Phase 5: OpenAI Asset Resolution (AC-5)

**Scope**: Biggest effort — resolver function + enhanced ImageRef.

**Changes**:
1. `src/echomine/models/image.py` (MODIFY):
   - Expand `content_type` Literal to include `"image"` (not just `"image_asset_pointer"`)
   - DALL-E metadata fields preserved in existing `metadata` dict (no schema change needed — `gen_id`, `prompt`, `seed` already land there via the dict comprehension in `_parse_multimodal_parts`)

2. `src/echomine/utils/asset_resolver.py` (NEW):
   - `resolve_asset(export_dir: Path, asset_pointer: str) -> ResolvedAsset | None`
   - Strip URI scheme (`sediment://`, `file-service://`)
   - Match file ID as filename prefix in export directory
   - Sniff magic bytes for true file type (PNG, JPEG, WebP, GIF, WAV signatures)
   - `ResolvedAsset` model: `path`, `detected_type`, `original_extension`

3. `src/echomine/adapters/openai.py` (MODIFY `_parse_multimodal_parts`):
   - Ensure DALL-E metadata (`gen_id`, `prompt`, `seed`) included in ImageRef.metadata
   - Already mostly working via dict comprehension; verify coverage

**Tests**:
- Resolve `sediment://file_xxx` → correct file path
- Resolve `file-service://file-XXX` → correct file path
- Mismatched extension → detected via magic bytes
- WAV audio → discoverable
- Missing file → returns None
- DALL-E metadata preserved on ImageRef

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Raw dicts for metadata values (`thinking`, `attachments`, `file_refs`) instead of Pydantic models (Constitution VI tension) | Maintains `metadata: dict[str, Any]` backward compatibility (FR-018). Consumers access these keys via `metadata.get()` today. | Creating typed Pydantic sub-models would require a breaking schema change to the `metadata` field type, violating the additive/non-breaking contract. Typed helpers may be added in a future version as opt-in convenience. |
