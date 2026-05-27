# Research: Content Fidelity & Asset Recovery

**Feature**: 005-content-fidelity | **Date**: 2026-05-26

## R1: Content Type Category Vocabulary Design

**Decision**: Hybrid approach — raw provider type passthrough (`content_type`) + standardized semantic category (`content_type_category`) with 7-value pinned vocabulary.

**Rationale**: Consumers need provider-agnostic filtering (one-line check: `category == "conversational"`) without maintaining per-provider allowlists. The raw type is preserved for drill-down when consumers need provider-specific logic.

**Alternatives considered**:
- **Standardized-only**: Clean for consumers but lossy — editorial decisions about cross-provider mapping can't be overridden
- **Provider-prefixed keys** (e.g., `openai.content_type`): No ambiguity but forces provider-specific consumer logic, defeating the adapter pattern
- **Hybrid (chosen)**: Best of both — semantic layer for filtering, raw layer for drill-down

**Key design decisions from cross-project review (InsightMesh)**:
- `unknown` as distinct category (not collapsed into `system`) — serves as schema-drift canary
- `code`/`execution_output` → `tool_io` (Code Interpreter sandbox, not inline markdown fences)
- `multimodal_text` → `conversational` (category reflects text payload; images are orthogonal via `Message.images`)
- `tether_quote`/`tether_browsing_display` → `tool_io` for now (browsing citations deferred to future `citation` category)

## R2: OpenAI Multi-Part Text Handling

**Decision**: Join all string parts with `"\n".join(...)` instead of keeping only `parts[0]`.

**Rationale**: Silent data loss — current code drops `parts[1:]`. OpenAI text content is occasionally split across multiple parts. The fix is a one-liner that matches Claude adapter behavior (which already joins with `"\n".join(text_parts)`).

**Alternatives considered**:
- `" ".join(...)` (space separator): Less faithful to original structure
- `"".join(...)` (no separator): Could merge words across part boundaries
- `"\n".join(...)` (chosen): Matches Claude adapter convention, preserves part boundaries

## R3: Claude Export Format — Attachments & File References

**Decision**: Surface both `attachments` (with `extracted_content`) and `files` (UUID-only tombstones) in message metadata.

**Rationale**: Confirmed via real export analysis (2026-05-25):
- `attachments[]` contains `{file_name, file_size, file_type, extracted_content}` — already-parsed text ready for synthesis
- `files[]` contains `{file_uuid, file_name}` — tombstone references (no binary in export)
- Claude official exports (Settings > Privacy > Export Data) do NOT include binary files

**Key finding**: Some `file_name` values are empty strings. The `file_uuid` is always present and is the reliable identifier.

## R4: Claude Block Types — Thinking, Voice, Unknown

**Decision**: Handle `thinking` → `metadata["thinking"]`, `voice_note` → `Message.content`, unknown → DEBUG log + skip.

**Rationale**: Confirmed via real export analysis:
- 110 `thinking` blocks found with structure: `{thinking, summaries, cut_off, truncated, signature, alternative_display_type}`
- 0 `voice_note` blocks in test export (handle based on documented format)
- 1 `token_budget` block (unknown type, should be logged not dropped silently)

**Cross-provider symmetry**: OpenAI `thoughts`/`reasoning_recap` → same `metadata["thinking"]` key as Claude. Both get `content=""` and `category: reasoning`.

## R5: OpenAI Asset Resolution

**Decision**: Resolver function that strips URI scheme, matches file ID prefix, sniffs magic bytes.

**Rationale**: Real export evidence:
- 456 PNG + 130 JPEG + 21 JPG + 19 WebP + 12 WAV files in export bundle
- Two URI schemes: `sediment://file_xxx` (newer) and `file-service://file-XXX` (older)
- Some files have mismatched extensions (WebP saved as `.dat`)

**Magic byte signatures** (well-known, no external dependency needed):
- PNG: `\x89PNG\r\n\x1a\n`
- JPEG: `\xff\xd8\xff`
- WebP: `RIFF....WEBP`
- GIF: `GIF87a` or `GIF89a`
- WAV: `RIFF....WAVE`

## R6: Performance Impact Assessment

**Decision**: Existing performance contracts hold unchanged. No size caps or lazy loading for `extracted_content`.

**Rationale**: Per clarification session (2026-05-26):
- Attachment counts are low (15 out of hundreds of messages in real Claude export)
- Largest `extracted_content` observed: 19KB (resume text)
- Per-message metadata overhead is a dict entry — negligible vs conversation text
- O(1) streaming pattern unchanged; metadata is per-yield, not accumulated

## R7: Backward Compatibility Contract

**Decision**: All changes are additive. Existing output unchanged without explicit consumer opt-in.

**Rationale**: Critical for downstream consumers (InsightMesh):
- Consumers can bump echomine dependency without breaking
- New metadata fields appear only in `metadata` dict (already typed as `dict[str, Any]`)
- `content=""` for non-conversational types works with existing empty-skip logic
- No existing fields removed or renamed
