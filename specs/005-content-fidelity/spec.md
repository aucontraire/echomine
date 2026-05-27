# Feature Specification: Content Fidelity & Asset Recovery

**Feature Branch**: `005-content-fidelity`
**Created**: 2026-05-26
**Status**: Draft

## Overview

echomine is silently losing or corrupting valuable conversation data in three systematic areas: non-conversational content handling, text-fidelity bugs, and asset/file recovery. These are not crashes — they are silent fidelity problems discovered by downstream consumers (InsightMesh) comparing echomine output against source conversations. This feature introduces a provider-agnostic content classification contract, fixes data-loss bugs, and surfaces previously-dropped content (attachments, reasoning, voice notes, asset references).

## Clarifications

### Session 2026-05-26

- Q: Should existing performance contracts hold unchanged with new metadata fields (especially `extracted_content` text blobs), or should large payloads be capped/lazy-loaded? → A: Existing performance contracts hold unchanged; `extracted_content` is included inline in metadata. Real-world attachment counts are low (15 out of hundreds of messages) and text sizes are modest (largest observed: 19KB).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Content Type Transparency (Priority: P1)

As a downstream consumer, I want each message to carry both its raw provider content type and a standardized content category so I can filter messages by semantic role (conversational, reasoning, tool I/O) without maintaining per-provider allowlists.

**Why this priority**: This is the highest-leverage change. It introduces the provider-agnostic content contract that all other stories build on. Alone, it gets consumers ~80% of the fidelity fix via existing empty-skip logic — placeholder messages like `[user_editable_context]` disappear without any consumer-side code changes.

**Independent Test**: Can be fully tested by parsing an export file and verifying that every message carries `content_type` and `content_type_category` metadata fields with values from the pinned vocabulary. Delivers immediate value: consumers can filter to `conversational` messages with a single provider-agnostic check.

**Acceptance Scenarios**:

1. **Given** an OpenAI export with `text`, `multimodal_text`, `thoughts`, and `user_editable_context` content types, **When** the export is parsed, **Then** each message carries `metadata["content_type"]` with the raw type and `metadata["content_type_category"]` with the correct category from the vocabulary (`conversational`, `reasoning`, `system`, respectively).
2. **Given** an OpenAI export with an unknown content type not in the mapping, **When** the export is parsed, **Then** the message has `content=""`, `metadata["content_type"]` with the raw type, and `metadata["content_type_category"] = "unknown"`.
3. **Given** a Claude export with `text` and `thinking` blocks, **When** the export is parsed, **Then** each message carries the correct category (`conversational` for text, `reasoning` for thinking).
4. **Given** an OpenAI `multimodal_text` message with both text and image pointers, **When** parsed, **Then** the category is `conversational` (reflecting text payload) AND `Message.images` is populated (reflecting image pointers) — category and media refs are orthogonal.
5. **Given** an export where `metadata["recipient"]` is present, **When** parsed, **Then** `metadata["recipient"]` is preserved on the message.

**Content Type Category Vocabulary**:

| Category       | OpenAI content_types                                          | Claude block types                 |
|----------------|---------------------------------------------------------------|------------------------------------|
| conversational | text, multimodal_text                                         | text, voice_note                   |
| reasoning      | thoughts, reasoning_recap                                     | thinking                           |
| tool_io        | code, execution_output, tether_quote, tether_browsing_display | tool_use, tool_result              |
| system         | user_editable_context, app_pairing_content, system_error      | token_budget                       |
| media          | image_asset_pointer, image                                    | —                                  |
| attachment     | —                                                             | attachments with extracted_content |
| unknown        | (any unmapped type)                                           | (any unmapped block type)          |

**Key Distinctions**:

- **Code Interpreter vs inline code**: `code`/`execution_output` under `tool_io` refers to ChatGPT Code Interpreter sandbox I/O (the assistant executing Python in a sandboxed environment). Inline code blocks (markdown fences in a regular `text` response) are part of `content_type: text` → `conversational` and are always preserved in message content. The category classification does not affect code within prose answers.
- **Category-artifact orthogonality**: A message's category reflects its conversational role. Any artifact carried alongside conversational text (images, attachments, reasoning, or future types) is orthogonal metadata, present regardless of category. A message whose only content is an artifact takes that artifact's category (`media`, `attachment`, `reasoning`). This principle is general — new artifact types inherit it automatically without re-litigating the rule.
- **Browsing citations (conscious deferral)**: `tether_quote`/`tether_browsing_display` carry source URLs from web browsing and are classified as `tool_io` for now. These URLs are valuable for future source-attribution features; the raw type is preserved in `metadata["content_type"]` so a future `citation`/`source` category can surface them without losing data in the interim.
- **`unknown` as schema-drift canary**: Unmapped content types get category `unknown` (not `system`). Both result in `content=""` and are dropped by prose consumers, but `unknown` signals "echomine doesn't recognize this type yet" vs `system` which means "known to be system-level." Consumers can log/count `unknown`-category messages to detect when providers ship new types that need mapping, rather than discovering silent degradation months later.

---

### User Story 2 - Accurate Text Extraction (Priority: P1)

As a researcher exporting conversations, I want all text parts of a message preserved so that multi-part messages are not silently truncated.

**Why this priority**: This is a silent data-loss bug with a trivial fix. Currently only the first element of multi-part text messages is kept; the rest is silently dropped. Co-prioritized with US-1 because it's a one-line fix that stops real content loss.

**Independent Test**: Can be tested by parsing an export containing a message with multiple text parts and verifying the output content contains all parts joined together.

**Acceptance Scenarios**:

1. **Given** an OpenAI message with `content.parts = ["Part one", "Part two", "Part three"]`, **When** parsed, **Then** `Message.content` contains all three parts joined (e.g., `"Part one\nPart two\nPart three"`).
2. **Given** an OpenAI message with `content.parts = ["Only part"]`, **When** parsed, **Then** `Message.content = "Only part"` (single-part behavior unchanged).
3. **Given** an OpenAI message with `content.parts = ["text", 42, "more text"]` (mixed types), **When** parsed, **Then** only string elements are joined; non-string elements are skipped.

---

### User Story 3 - Claude Attachments & File References (Priority: P2)

As a consumer processing Anthropic exports, I want uploaded file content (text extracts of PDFs, documents) and file references surfaced so that recoverable source material is not silently dropped.

**Why this priority**: Claude exports contain already-parsed text from uploaded files (PDF extracts, document text) that is currently being dropped. This is ready-to-use source material for downstream synthesis — low effort to surface, high consumer value.

**Independent Test**: Can be tested by parsing a Claude export containing messages with `attachments` (carrying `extracted_content`) and `files` (UUID-only references) and verifying both are surfaced in message metadata.

**Acceptance Scenarios**:

1. **Given** a Claude message with `attachments` containing `extracted_content`, `file_name`, `file_type`, and `file_size`, **When** parsed, **Then** `metadata["attachments"]` contains a list with each attachment's `file_name`, `file_type`, `file_size`, and `extracted_content`.
2. **Given** a Claude message with `files` containing `file_uuid` and `file_name`, **When** parsed, **Then** `metadata["file_refs"]` contains a list with each file's `file_uuid` and `file_name` so consumers know a file was attached even without the binary.
3. **Given** a Claude message with both `attachments` and `files`, **When** parsed, **Then** both `metadata["attachments"]` and `metadata["file_refs"]` are populated independently.
4. **Given** a Claude message with `files` where `file_name` is empty, **When** parsed, **Then** `metadata["file_refs"]` still includes the entry with the `file_uuid` (the tombstone is preserved even without a filename).

---

### User Story 4 - Reasoning & Voice Block Recovery (Priority: P2)

As a consumer processing AI exports, I want thinking/reasoning blocks accessible via metadata and voice note transcriptions included as message content, so that real content is not silently dropped. This handling should be symmetric across providers.

**Why this priority**: 110 thinking blocks and voice note transcriptions are currently silently dropped in Claude exports. OpenAI reasoning types (`thoughts`, `reasoning_recap`) also need symmetric treatment to avoid provider divergence.

**Independent Test**: Can be tested by parsing exports containing thinking blocks (Claude) or thoughts/reasoning_recap content types (OpenAI) and verifying reasoning content appears in `metadata["thinking"]` for both providers, and voice note text appears in `Message.content`.

**Acceptance Scenarios**:

1. **Given** a Claude message with a `thinking` block containing `thinking` text, `summaries`, `cut_off`, and `truncated` fields, **When** parsed, **Then** `metadata["thinking"]` contains the thinking text and associated fields, and `Message.content` does not include the reasoning text.
2. **Given** an OpenAI message with `content_type: thoughts` or `reasoning_recap`, **When** parsed, **Then** `metadata["thinking"]` contains the reasoning content (same key as Claude), `content=""`, and `metadata["content_type_category"] = "reasoning"`.
3. **Given** a Claude message with a `voice_note` block, **When** parsed, **Then** the transcribed text is included in `Message.content` and `metadata["content_type_category"] = "conversational"`.
4. **Given** an OpenAI `multimodal_text` message containing an audio transcription part-object, **When** parsed, **Then** the transcript text is included in `Message.content` as `conversational` via the multimodal-parts handling path.
5. **Given** a Claude message with a `token_budget` block (or other unknown block type), **When** parsed, **Then** the block is skipped gracefully and logged at DEBUG level.

---

### User Story 5 - Hidden Message Filtering (Priority: P3)

As a consumer building a UI or document from exported conversations, I want to know which messages were hidden in the original interface (custom instructions, memory, internal prompts) so I can choose whether to include or exclude them.

**Why this priority**: Small, additive metadata flag. Useful for consumers but not blocking — hidden messages were always present in output; this just makes them identifiable.

**Independent Test**: Can be tested by parsing an OpenAI export containing messages with `is_visually_hidden_from_conversation: true` and verifying the flag appears in message metadata.

**Acceptance Scenarios**:

1. **Given** an OpenAI message with `metadata.is_visually_hidden_from_conversation: true`, **When** parsed, **Then** `metadata["is_visually_hidden"] = True`.
2. **Given** an OpenAI message without the hidden flag (or with it set to false), **When** parsed, **Then** `metadata["is_visually_hidden"]` is not set or is `False`.
3. **Given** the hidden flag is surfaced, **When** a consumer processes messages, **Then** hidden messages are still included in output by default — the consumer decides whether to filter.

---

### User Story 6 - OpenAI Asset Resolution (Priority: P3)

As a researcher or knowledge-base builder, I want to resolve image and audio asset pointers to actual files in the OpenAI export bundle, so I can recover the binary media that the export already contains.

**Why this priority**: Highest long-term value but also the biggest implementation effort. The export bundles contain hundreds of binary files (PNG, JPEG, WebP, WAV) that are currently unreachable through echomine. Deferred to P3 because the other stories deliver quicker wins.

**Independent Test**: Can be tested by providing a sample export directory with binary files and verifying the resolver matches asset pointers to actual file paths, with correct file type detection.

**Acceptance Scenarios**:

1. **Given** an `ImageRef` with `asset_pointer = "sediment://file_00000000752c61fba7625d0cee8b8c65"` and a file `file_00000000752c61fba7625d0cee8b8c65-sanitized.png` in the export directory, **When** the resolver is called, **Then** it returns the full path to that file.
2. **Given** an asset pointer with `file-service://file-XXXX` scheme (older format), **When** the resolver is called, **Then** it strips the scheme and matches the file ID prefix correctly.
3. **Given** a file with mismatched extension (e.g., a WebP file saved as `.dat`), **When** the resolver is called, **Then** it sniffs magic bytes to determine the true file type.
4. **Given** a WAV audio file in the export bundle, **When** the resolver is called with the corresponding pointer, **Then** the audio file is discoverable (not just images).
5. **Given** DALL-E metadata (`gen_id`, `prompt`, `seed`) present on an image, **When** parsed, **Then** `ImageRef` preserves these fields in its metadata.
6. **Given** an asset pointer with no matching file in the export directory, **When** the resolver is called, **Then** it returns a clear "not found" result rather than failing silently.

---

### Edge Cases

- What happens when a provider ships a new, previously-unseen content type? → Categorized as `unknown`, `content=""`, raw type preserved. The `unknown` count serves as a schema-drift canary.
- What happens when a Claude message has only `thinking` blocks and no `text` blocks? → `Message.content = ""`, reasoning is in `metadata["thinking"]`, category is `reasoning`.
- What happens when a Claude message has both `text` and `thinking` blocks? → `content_type` is `text`, `content_type_category` is `conversational`. Text takes priority for classification; thinking content goes to `metadata["thinking"]` regardless (category-artifact orthogonality).
- What happens when a Claude message has `attachments` with `extracted_content` but no text blocks? → `content_type_category` is `attachment`, `content` is `""` (value is in `metadata["attachments"]`). Mirrors image-only → `media`.
- What happens when a Claude message has both text blocks and attachments? → `content_type_category` is `conversational`, and `metadata["attachments"]` is populated regardless (category-artifact orthogonality).
- What happens when an OpenAI message has `content.parts = []` (empty parts array)? → `Message.content = ""`, same as current behavior.
- What happens when a Claude attachment has `extracted_content` but empty `file_name`? → Attachment is still surfaced with empty filename; the `extracted_content` is the valuable data.
- What happens when an asset pointer references a file that has been deleted from the export bundle? → Resolver returns "not found"; the `ImageRef` still preserves the pointer for reference.
- What happens when a `multimodal_text` message has text parts AND image pointers AND an audio transcription? → All three are handled: text joined into content, images into `Message.images`, audio transcript into content. Category is `conversational`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist the raw provider content type on every message as `metadata["content_type"]`
- **FR-002**: System MUST classify every message into a standardized `metadata["content_type_category"]` from the pinned vocabulary: `conversational`, `reasoning`, `tool_io`, `system`, `media`, `attachment`, `unknown`
- **FR-003**: System MUST set `content=""` for messages with content types categorized as `reasoning`, `tool_io`, `system`, or `unknown`. Messages categorized as `media` retain `content="[Image]"` as a consumer-visible placeholder. Messages categorized as `attachment` retain `content=""` (the value is in `metadata["attachments"]`)
- **FR-004**: System MUST preserve `metadata["recipient"]` when present in the source data
- **FR-005**: System MUST join all string elements in OpenAI multi-part text messages rather than keeping only the first part
- **FR-006**: System MUST surface Claude `thinking` block content in `metadata["thinking"]` with associated fields (`summaries`, `cut_off`, `truncated`)
- **FR-007**: System MUST surface OpenAI `thoughts`/`reasoning_recap` content in `metadata["thinking"]` (same key as Claude) for symmetric cross-provider handling
- **FR-008**: System MUST include Claude `voice_note` block transcribed text in `Message.content` as `conversational`
- **FR-009**: System MUST include OpenAI audio transcription text (part-objects inside `multimodal_text`) in `Message.content` as `conversational`
- **FR-010**: System MUST surface Claude `attachments` with `extracted_content` as `metadata["attachments"]` including `file_name`, `file_type`, `file_size`, and `extracted_content`
- **FR-011**: System MUST surface Claude file references (UUID-only tombstones) as `metadata["file_refs"]` with `file_uuid` and `file_name`
- **FR-012**: System MUST surface OpenAI `is_visually_hidden_from_conversation` flag as `metadata["is_visually_hidden"]`
- **FR-013**: System MUST preserve full `asset_pointer` values and DALL-E metadata (`gen_id`, `prompt`, `seed`) on `ImageRef`
- **FR-014**: System MUST provide an asset resolver that maps asset pointers to file paths in the export bundle by stripping URI schemes and matching file ID prefixes
- **FR-015**: Asset resolver MUST sniff file magic bytes to determine true file type when extensions are mismatched
- **FR-016**: Asset resolver MUST support non-image binaries (e.g., WAV audio files)
- **FR-017**: System MUST log unknown/unmapped block types at DEBUG level rather than dropping them silently
- **FR-018**: All new metadata fields MUST be additive — existing output and behavior unchanged without explicit consumer opt-in

### Key Entities

- **Content Type Category**: A standardized semantic classification applied to every message, drawn from a pinned vocabulary of 7 values. Maps provider-specific content types to provider-agnostic categories.
- **Thinking/Reasoning Metadata**: Cross-provider representation of model reasoning content, stored in message metadata rather than message content to prevent reasoning from leaking into prose output.
- **Attachment**: A file uploaded by a user to a conversation, represented either as extracted text content (Claude) or a resolvable binary reference (OpenAI).
- **File Reference (Tombstone)**: A minimal record indicating a file was attached to a message, preserving UUID and filename even when the binary is unavailable.
- **Asset Pointer**: A URI reference to a binary file in an OpenAI export bundle, using `sediment://` or `file-service://` schemes, resolvable to an on-disk file path.

## Non-Goals

- **Merging continuation turns (B2)**: Consecutive assistant messages from "Continue generating" remain as separate messages. This is faithful to the source tree structure; merging is a consumer-side concern.
- **Canvas document recovery (C3)**: ChatGPT Canvas documents are largely absent from export bundles (the `textdocs/` folder frequently doesn't appear). This is an OpenAI export limitation, not an echomine problem. Document the limitation but don't attempt recovery.
- **Binary file extraction/copying**: The asset resolver returns file paths; it does not copy, convert, or re-encode files. Consumers handle what to do with resolved paths.
- **Changing default output**: All new metadata fields are additive. Existing CLI output and message counts remain unchanged unless consumers explicitly filter on the new fields. Consumers can bump the echomine dependency without breaking, then adopt new fields deliberately.
- **Real-time API integration**: This feature works exclusively with static export files, not live API calls to OpenAI or Anthropic.
- **Browsing citation extraction**: `tether_quote`/`tether_browsing_display` source URLs are preserved in raw metadata but not surfaced as a dedicated category. Deferred to a future source-attribution feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Downstream consumers can filter to conversational content with a single provider-agnostic check (`content_type_category == "conversational"`) instead of maintaining per-provider type allowlists
- **SC-002**: Message counts for conversational turns (counted as messages where `content_type_category == "conversational"`) match the human-visible turn count in the source application — no more inflated counts from placeholder messages (e.g., `[user_editable_context]`, `[thoughts]`)
- **SC-003**: Zero silent data loss — multi-part text messages contain all string parts; Claude voice notes appear in message content; uploaded file text extracts are accessible via metadata
- **SC-004**: `unknown`-category message counts are observable via `metadata["content_type_category"]` field inspection (consumers can count/filter) and DEBUG-level adapter logging (FR-017), enabling detection of provider schema changes within one release cycle
- **SC-005**: All changes are additive and non-breaking — existing consumers see no behavior change without opting in to new metadata fields; bumping the echomine dependency does not require consumer code changes

## Assumptions

- The `content_type_category` vocabulary is stable but extensible — new categories (e.g., `citation`) may be added in future versions without breaking existing consumers
- OpenAI and Anthropic export formats will continue to evolve; the `unknown` category provides forward-compatible handling for new types
- Voice note transcription text in Claude exports is accurate enough to include as conversational content (echomine does not re-transcribe)
- OpenAI export bundles consistently place binary files alongside `conversations.json` with file-ID-based naming conventions. If naming conventions change in future exports, the resolver returns "not found" for unresolvable pointers (graceful degradation, not failure) and the `unknown` category canary pattern applies — consumers detecting unresolved pointers signals a format change
- Claude official data exports (Settings > Privacy > Export Data) do not include binary file attachments — only JSON with text extracts and UUID references (confirmed via real export testing, 2026-05-25)
- OpenAI audio transcription part-objects within `multimodal_text` messages have not been observed in available export data (2026-05-26). FR-009 handles them by including transcript text in `Message.content` if encountered; if the part format cannot be parsed, the part is logged at DEBUG and skipped (graceful degradation). The exact JSON structure will be documented in research.md upon first observation in real data
- Existing performance contracts (1.6GB search <30s, 10K conversations on 8GB RAM, O(1) memory) hold unchanged with new metadata fields; `extracted_content` is included inline in metadata without size caps or lazy loading

## Priority / Sequencing

1. **US-1 / AC-1** (content_type + content_type_category + stop placeholder leak) — highest leverage; gets consumers ~80% of the fix via existing empty-skip logic
2. **US-2 / AC-2** (multi-part text fix) — trivial fix, stops silent text loss
3. **US-3 / AC-6** (Claude attachments/extracted_content) — low effort, high consumer value; already-parsed text ready for synthesis
4. **US-4 / AC-3** (thinking/voice_note + symmetric OpenAI reasoning) — surfaces dropped content
5. **US-5 / AC-4** (is_visually_hidden flag) — small, additive
6. **US-6 / AC-5** (OpenAI asset resolver) — biggest effort, highest long-term value

## Evidence Base

All findings grounded in real export data:
- **OpenAI**: 280-conversation export (29,022 mapping nodes, 456 PNG, 130 JPEG, 21 JPG, 19 WebP, 12 WAV files)
- **Anthropic**: Official account export containing 338 text blocks, 110 thinking blocks, 50 tool_use blocks, 50 tool_result blocks, 1 token_budget block, 16 messages with file references, 15 messages with attachments carrying extracted_content
