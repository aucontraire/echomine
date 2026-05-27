# Content Type Category Contract

**Feature**: 005-content-fidelity | **Version**: 1.0

## Contract Summary

Every `Message` produced by any echomine adapter MUST carry two metadata fields that together form a provider-agnostic content classification contract:

1. `metadata["content_type"]` — the raw provider-specific content type string
2. `metadata["content_type_category"]` — a standardized category from the vocabulary below

## Vocabulary (Pinned)

The following 7 category values are the complete, pinned vocabulary. Any value not in this set is a contract violation.

```
conversational | reasoning | tool_io | system | media | attachment | unknown
```

## Provider Mappings

### OpenAI Content Types

| Raw content_type | Category | content behavior |
|------------------|----------|-----------------|
| `text` | `conversational` | All string parts joined with `\n` |
| `multimodal_text` | `conversational` | Text parts joined; images → `Message.images` (orthogonal) |
| `thoughts` | `reasoning` | `content=""`, reasoning → `metadata["thinking"]` |
| `reasoning_recap` | `reasoning` | `content=""`, reasoning → `metadata["thinking"]` |
| `code` | `tool_io` | `content=""` (Code Interpreter sandbox, NOT inline fences) |
| `execution_output` | `tool_io` | `content=""` |
| `tether_quote` | `tool_io` | `content=""` (browsing citation — future `citation` category) |
| `tether_browsing_display` | `tool_io` | `content=""` |
| `user_editable_context` | `system` | `content=""` |
| `app_pairing_content` | `system` | `content=""` |
| `system_error` | `system` | `content=""` |
| `image_asset_pointer` | `media` | `content="[Image]"`, asset pointer → `Message.images` |
| `image` | `media` | `content="[Image]"`, asset pointer → `Message.images` |
| _(any other)_ | `unknown` | `content=""`, raw type preserved for drift detection |

### Claude Block Types

| Raw block type | Category | content behavior |
|----------------|----------|-----------------|
| `text` | `conversational` | Text included in `Message.content` |
| `voice_note` | `conversational` | Transcribed text included in `Message.content` |
| `thinking` | `reasoning` | `content=""`, reasoning → `metadata["thinking"]` |
| `tool_use` | `tool_io` | Skipped (tool I/O plumbing, not prose) |
| `tool_result` | `tool_io` | Skipped (tool I/O plumbing, not prose) |
| `token_budget` | `system` | Skipped, logged at DEBUG |
| _(any other)_ | `unknown` | Skipped, logged at DEBUG, raw type preserved |

**Message-Level Override (Claude)**: When a message has `attachments` with `extracted_content` but no conversational text blocks, the category is overridden to `attachment` (`content=""`). When text co-exists with attachments, category stays `conversational` and attachments populate `metadata["attachments"]` orthogonally. This follows the category-artifact orthogonality principle: any artifact alongside text is orthogonal metadata; a pure-artifact message takes the artifact's category.

## Cross-Provider Metadata Contract

### Symmetric Keys

These metadata keys use the same name and structure regardless of provider:

| Key | Structure | Set when |
|-----|-----------|----------|
| `content_type` | `str` | Always |
| `content_type_category` | `str` (vocabulary value) | Always |
| `thinking` | `{"content": str, ...}` | Category is `reasoning` |

### Provider-Specific Keys

| Key | Provider | Structure |
|-----|----------|-----------|
| `recipient` | OpenAI | `str` |
| `is_visually_hidden` | OpenAI | `bool` |
| `original_role` | OpenAI | `str` |
| `update_time` | OpenAI | `float \| None` |
| `attachments` | Claude | `list[{"file_name", "file_type", "file_size", "extracted_content"}]` |
| `file_refs` | Claude | `list[{"file_uuid", "file_name"}]` |

## Backward Compatibility

- All new keys are **additive** — they appear in the existing `metadata: dict[str, Any]` field
- No existing keys are removed, renamed, or re-typed
- Existing consumers that do not read these keys see no behavior change
- `content=""` for non-conversational types works with existing empty-skip patterns

## Extensibility

- New categories MAY be added to the vocabulary in future versions (e.g., `citation`)
- New provider mappings MAY be added as new content types appear
- The `unknown` category provides forward-compatible handling for unmapped types
- Consumers SHOULD treat unrecognized category values the same as `unknown`
