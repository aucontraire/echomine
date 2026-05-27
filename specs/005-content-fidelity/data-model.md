# Data Model: Content Fidelity & Asset Recovery

**Feature**: 005-content-fidelity | **Date**: 2026-05-26

## Model Changes Summary

This feature makes **no structural changes** to the core `Message` or `Conversation` models. All new data flows through the existing `metadata: dict[str, Any]` field and the existing `images: list[ImageRef]` field. One new module (`content_types.py`) and one new module (`asset_resolver.py`) are added.

## New Entity: ContentTypeCategory

A `Literal` type defining the 7-value pinned vocabulary for provider-agnostic content classification.

### Values

| Category       | Meaning                                          | Consumers typically... |
|----------------|--------------------------------------------------|----------------------|
| `conversational` | Real user/assistant dialogue                    | Keep (prose, synthesis) |
| `reasoning`      | Model thinking/chain-of-thought                 | Drop from prose, surface in analysis tools |
| `tool_io`        | Code Interpreter I/O, browsing, tool calls      | Drop (plumbing) |
| `system`         | Custom instructions, memory, system errors      | Drop (internal) |
| `media`          | Image-only messages (no text payload)            | Handle via `Message.images` |
| `attachment`     | Uploaded file with extracted text content        | Synthesize from `metadata["attachments"]` |
| `unknown`        | Unmapped type (schema-drift canary)              | Drop, monitor count |

**attachment vs media**: `attachment` (Claude-only) carries already-extracted text content in `metadata["attachments"]` — the binary is absent from Claude exports, but the parsed text (PDF extracts, document text) is inline and ready for synthesis. `media` (OpenAI-only) carries binary asset pointers resolvable via `Message.images` and the asset resolver; the message retains `content="[Image]"` as a consumer-visible placeholder.

### Category Mapping Dictionaries

**OpenAI** (`OPENAI_CATEGORY_MAP`):
```
text               → conversational
multimodal_text    → conversational
thoughts           → reasoning
reasoning_recap    → reasoning
code               → tool_io
execution_output   → tool_io
tether_quote       → tool_io
tether_browsing_display → tool_io
user_editable_context   → system
app_pairing_content     → system
system_error            → system
image_asset_pointer     → media
image                   → media
(unmapped)              → unknown
```

**Claude** (`CLAUDE_CATEGORY_MAP`):
```
text          → conversational
voice_note    → conversational
thinking      → reasoning
tool_use      → tool_io
tool_result   → tool_io
token_budget  → system
(unmapped)    → unknown
```

### Message-Level Post-Classification (Claude)

After block-level classification via `CLAUDE_CATEGORY_MAP`, the Claude adapter applies a message-level override following the category-artifact orthogonality rule:

- If the message has `attachments` with `extracted_content` AND no conversational text blocks → override `content_type_category` to `attachment`, set `content = ""`
- If the message has both text blocks and attachments → keep `conversational`, populate `metadata["attachments"]` orthogonally

This mirrors how OpenAI handles pure-image messages: `image_asset_pointer`/`image` → `media` only when there are no text parts. When text co-exists, the category stays `conversational`. The principle is general — any future artifact type inherits the same rule without re-litigating it.

## Modified Entity: Message.metadata

The existing `metadata: dict[str, Any]` field gains new keys. No schema change — all keys are optional and additive.

### New Metadata Keys (all providers)

| Key | Type | When Set | Description |
|-----|------|----------|-------------|
| `content_type` | `str` | Always | Raw provider content type (e.g., `"text"`, `"multimodal_text"`, `"thinking"`) |
| `content_type_category` | `str` | Always | Standardized category from vocabulary (e.g., `"conversational"`, `"reasoning"`) |

### New Metadata Keys (OpenAI-specific)

| Key | Type | When Set | Description |
|-----|------|----------|-------------|
| `recipient` | `str` | When present in source | Message recipient (e.g., `"all"`, tool name) |
| `is_visually_hidden` | `bool` | When `true` in source | OpenAI's `is_visually_hidden_from_conversation` flag |
| `thinking` | `dict` | For `thoughts`/`reasoning_recap` types | Reasoning content: `{"content": str}` |

### New Metadata Keys (Claude-specific)

| Key | Type | When Set | Description |
|-----|------|----------|-------------|
| `thinking` | `dict` | For `thinking` blocks | Reasoning content: `{"content": str, "summaries": list, "cut_off": bool, "truncated": bool}` |
| `attachments` | `list[dict]` | When attachments present | `[{"file_name": str, "file_type": str, "file_size": int, "extracted_content": str}]` |
| `file_refs` | `list[dict]` | When files present | `[{"file_uuid": str, "file_name": str}]` |

### Existing Metadata Keys (unchanged)

| Key | Provider | Description |
|-----|----------|-------------|
| `original_role` | OpenAI | Raw author role before normalization |
| `update_time` | OpenAI | Message update timestamp |
| `original_sender` | Claude | Raw sender when not in standard role_mapping |

## Modified Entity: ImageRef

No structural changes needed. The existing `metadata: dict[str, Any]` field on `ImageRef` already captures DALL-E metadata (`gen_id`, `prompt`, `seed`) via the dict comprehension in `_parse_multimodal_parts`.

The `content_type` Literal field should be widened from `Literal["image_asset_pointer"]` to `Literal["image_asset_pointer", "image"]` to handle the alternate OpenAI content type.

## New Entity: ResolvedAsset

A Pydantic model returned by the asset resolver.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `path` | `Path` | Absolute path to the resolved file on disk |
| `detected_type` | `str` | MIME type detected via magic bytes (e.g., `"image/png"`, `"audio/wav"`) |
| `original_extension` | `str` | Original file extension from disk (e.g., `".png"`, `".dat"`) |
| `file_id` | `str` | Extracted file ID from the asset pointer |

## Relationships

```
Message
├── metadata["content_type"]           → str (raw provider type)
├── metadata["content_type_category"]  → ContentTypeCategory (standardized)
├── metadata["thinking"]               → dict (reasoning content, cross-provider)
├── metadata["attachments"]            → list[dict] (Claude extracted text)
├── metadata["file_refs"]              → list[dict] (Claude file tombstones)
├── metadata["is_visually_hidden"]     → bool (OpenAI hidden flag)
├── metadata["recipient"]              → str (OpenAI recipient)
└── images: list[ImageRef]
    └── ImageRef.asset_pointer         → resolve_asset() → ResolvedAsset | None
```

## Validation Rules

- `content_type_category` MUST be one of the 7 vocabulary values
- `content_type` MUST be a non-empty string
- When `content_type_category` is `reasoning`, `content` MUST be `""` (reasoning in metadata only)
- When `content_type_category` is `tool_io`, `content` MUST be `""` (plumbing, not prose)
- When `content_type_category` is `system`, `content` MUST be `""` (internal)
- When `content_type_category` is `media`, `content` MUST be `"[Image]"` (consumer-visible placeholder; binary via `Message.images`)
- When `content_type_category` is `attachment`, `content` MUST be `""` (value is in `metadata["attachments"]`)
- When `content_type_category` is `unknown`, `content` MUST be `""` (safe drop)
- `attachments[].extracted_content` has no size cap (per clarification: inline, no lazy loading)
- `file_refs[].file_uuid` MUST be non-empty; `file_name` may be empty string
- `ResolvedAsset.path` MUST point to an existing file
