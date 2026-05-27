# Content Contract Quality Checklist: Content Fidelity & Asset Recovery

**Purpose**: Validate that the content type category vocabulary, provider mappings, and cross-provider symmetry requirements are complete, clear, and consistent — suitable for cross-project review (InsightMesh alignment)
**Created**: 2026-05-26
**Feature**: [spec.md](../spec.md) | [content_contract.md](../contracts/content_contract.md) | [data-model.md](../data-model.md)
**Focus**: Content contract quality (vocabulary, mappings, cross-provider symmetry)
**Depth**: Standard (~30 items)
**Audience**: Cross-project reviewer (InsightMesh consumer alignment)

## Vocabulary Completeness

- [x] CHK001 - Are all OpenAI content types observed in the real 280-conversation export (29K nodes) accounted for in the category mapping? [Completeness, Spec §US-1]
- [x] CHK002 - Are all Claude block types observed in the real Anthropic export (338 text, 110 thinking, 50 tool_use, 50 tool_result, 1 token_budget) accounted for in the category mapping? [Completeness, Spec §US-1]
- [x] CHK003 - Is the `unknown` category explicitly defined as distinct from `system`, with clear rationale for why the distinction matters? [Clarity, Spec §US-1 Key Distinctions]
- [x] CHK004 - Are all 7 vocabulary values (`conversational`, `reasoning`, `tool_io`, `system`, `media`, `attachment`, `unknown`) defined with consumer-facing descriptions of what "typically" to do with each? [Completeness, Data Model §ContentTypeCategory]
- [x] CHK005 - Is the vocabulary explicitly described as extensible (new categories may be added) and are consumers advised to treat unrecognized values as `unknown`? [Completeness, Contract §Extensibility]

## Mapping Clarity & Precision

- [x] CHK006 - Is the `code` → `tool_io` mapping accompanied by the Code Interpreter vs inline code distinction, making clear that markdown fences in `text` responses are `conversational`? [Clarity, Spec §US-1 Key Distinctions]
- [x] CHK007 - Is the multimodal orthogonality principle (category reflects text, images are separate) stated explicitly enough that a reader won't assume `multimodal_text` → `media`? [Clarity, Spec §US-1 Key Distinctions]
- [x] CHK008 - Is the `tether_quote`/`tether_browsing_display` → `tool_io` classification documented as a conscious deferral with a note about future `citation` category potential? [Clarity, Spec §US-1 Key Distinctions]
- [x] CHK009 - For `media` category messages (`image_asset_pointer`, `image`), is the content behavior specified — does `content` stay as `"[Image]"` or become `""`? [Ambiguity, Contract §OpenAI Content Types] — **Resolved**: FR-003 updated to specify `content="[Image]"` for media; contract already aligned
- [x] CHK010 - Is the `attachment` category (Claude-only) clearly distinguished from `media` (OpenAI-only), and is it stated that attachment has `extracted_content` text while media has binary pointers? [Clarity, Data Model §New Entity: ContentTypeCategory] — **Resolved**: Added distinction paragraph to data-model.md after vocabulary table

## Cross-Provider Symmetry

- [x] CHK011 - Is the `metadata["thinking"]` key explicitly specified as the same key name for both OpenAI (`thoughts`/`reasoning_recap`) and Claude (`thinking` blocks)? [Consistency, Spec §AC-3]
- [x] CHK012 - Are the structural differences in `metadata["thinking"]` between providers documented — Claude includes `summaries`, `cut_off`, `truncated` while OpenAI includes only `content`? [Clarity, Data Model §Claude-specific]
- [x] CHK013 - Is it specified that both providers set `content=""` for `reasoning`-category messages, preventing reasoning from leaking into prose? [Consistency, Spec §AC-3]
- [x] CHK014 - Are `content_type` and `content_type_category` specified as mandatory on every message from every adapter, not just when "interesting" types are present? [Completeness, Spec §FR-001, FR-002]
- [x] CHK015 - Is the handling of `voice_note` (Claude) and audio transcription (OpenAI multimodal parts) specified symmetrically — both as `conversational` with transcript text in `Message.content`? [Consistency, Spec §AC-3]

## Consumer Contract Clarity

- [x] CHK016 - Is the additive/non-breaking guarantee stated clearly enough for a consumer to confidently bump echomine without code changes? [Clarity, Spec §Non-Goals]
- [x] CHK017 - Is it specified that no existing metadata keys (`original_role`, `update_time`, `original_sender`) are removed, renamed, or re-typed? [Completeness, Contract §Backward Compatibility]
- [x] CHK018 - Is the `content=""` behavior for non-conversational types documented as intentionally compatible with existing empty-skip consumer logic? [Clarity, Spec §AC-1]
- [x] CHK019 - Is the consumer filtering pattern (`content_type_category == "conversational"`) documented as the primary provider-agnostic API, with `content_type` as the drill-down? [Clarity, Quickstart]
- [x] CHK020 - Are the provider-specific metadata keys (`is_visually_hidden`, `attachments`, `file_refs`, `recipient`) clearly marked as provider-specific so consumers don't expect them from all adapters? [Clarity, Contract §Provider-Specific Keys]

## Edge Case & Boundary Coverage

- [x] CHK021 - Is behavior specified for a Claude message containing only `thinking` blocks and no `text` blocks? [Coverage, Spec §Edge Cases]
- [x] CHK022 - Is behavior specified for OpenAI messages with empty `content.parts` array? [Coverage, Spec §Edge Cases]
- [x] CHK023 - Is behavior specified for Claude `file_refs` where `file_name` is an empty string? [Coverage, Spec §US-3 AC scenario 4]
- [x] CHK024 - Is behavior specified for a `multimodal_text` message with text + images + audio transcript simultaneously? [Coverage, Spec §Edge Cases]
- [x] CHK025 - Is behavior specified for OpenAI asset pointers with no matching file in the export directory? [Coverage, Spec §US-6 AC scenario 6]
- [x] CHK026 - Is behavior specified for when a provider ships a new, previously-unseen content type? [Coverage, Spec §Edge Cases]

## Acceptance Criteria Measurability

- [x] CHK027 - Is SC-002 ("message counts match human-visible turn count") measurable without subjective judgment — are the counting rules defined (count where `category == conversational`)? [Measurability, Spec §SC-002] — **Resolved**: SC-002 updated with explicit counting rule
- [x] CHK028 - Is SC-004 ("unknown-category counts are observable") specific about how observability is achieved — logging level, metadata accessibility, or consumer-side counting? [Measurability, Spec §SC-004] — **Resolved**: SC-004 updated with metadata inspection + DEBUG logging mechanism
- [x] CHK029 - Are the acceptance scenarios in US-1 through US-6 written with concrete Given/When/Then that reference specific field values, not vague outcomes? [Measurability, Spec §User Scenarios]

## Dependencies & Assumptions

- [x] CHK030 - Is the assumption that Claude exports don't include binaries documented with evidence (confirmed via real export testing, dated)? [Assumption, Spec §Assumptions]
- [x] CHK031 - Is the assumption that existing performance contracts hold unchanged with new metadata explicitly tied to the clarification decision and real-world evidence (15 attachments, 19KB max)? [Assumption, Spec §Clarifications]
- [x] CHK032 - Is the OpenAI asset resolver's dependency on file-ID-based naming documented as an assumption, with a note about what happens if naming conventions change? [Assumption, Spec §Assumptions] — **Resolved**: Added graceful degradation fallback to assumption text

## Notes

- This checklist validates the **requirements as written**, not the implementation
- Focus is on content contract quality for cross-project (InsightMesh) reviewer alignment
- Items reference spec sections, contract document, and data model for traceability
- Check items off as reviewed: `[x]` — add inline comments for findings
