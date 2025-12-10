# CLI Contract: Claude Export Adapter

**Feature**: 004-claude-adapter
**Date**: 2025-12-08
**Version**: 1.0.0

## Overview

This contract defines CLI behavior changes for Claude adapter support. The primary addition is provider auto-detection and explicit `--provider` flag.

## Provider Auto-Detection

### Detection Algorithm (FR-046, FR-047, FR-048)

```python
def detect_provider(file_path: Path) -> Literal["openai", "claude"]:
    """Auto-detect export provider from file structure.

    Detection rules:
    1. Read first conversation object from JSON array
    2. If "chat_messages" key present → Claude (FR-047)
    3. If "mapping" key present → OpenAI (FR-048)
    4. Otherwise → raise error with clear message (FR-050)

    Returns:
        "openai" or "claude"

    Raises:
        ValueError: "Unsupported export format. Expected OpenAI or Claude export JSON."
    """
```

### Implementation Notes

- Detection reads only first array item (O(1) memory)
- Use ijson prefix scan for efficiency
- Cache detection result for multi-command sessions

## Command Changes

### All Commands: Add --provider Flag (FR-049)

```bash
# New optional flag for all commands
--provider [openai|claude]  # Optional, auto-detected if omitted
```

### list Command

```bash
# Auto-detect provider
echomine list conversations.json

# Explicit provider
echomine list conversations.json --provider claude
echomine list conversations.json --provider openai

# All existing flags work identically
echomine list conversations.json --limit 10 --json
```

### search Command

```bash
# Auto-detect provider
echomine search conversations.json --keywords "python"

# Explicit provider
echomine search conversations.json --provider claude --keywords "python"

# All search flags work identically for both providers
echomine search conversations.json \
  --keywords "algorithm" \
  --phrase "code review" \
  --match-mode all \
  --exclude "test" \
  --role user \
  --from-date "2024-01-01" \
  --to-date "2024-12-31" \
  --title "Tutorial" \
  --limit 10 \
  --json
```

### get Command

```bash
# Auto-detect provider
echomine get conversations.json <uuid>

# Explicit provider
echomine get conversations.json <uuid> --provider claude

# All display options work identically
echomine get conversations.json <uuid> --display summary
echomine get conversations.json <uuid> --json
```

### export Command

```bash
# Auto-detect provider
echomine export conversations.json <uuid> --output chat.md

# Explicit provider
echomine export conversations.json <uuid> --provider claude --output chat.md

# All export formats work identically
echomine export conversations.json <uuid> --format json --output chat.json
echomine export conversations.json <uuid> --format csv --output messages.csv
```

### stats Command

```bash
# Auto-detect provider
echomine stats conversations.json

# Explicit provider
echomine stats conversations.json --provider claude

# JSON output
echomine stats conversations.json --json
```

## Error Messages (FR-050)

### Unrecognized Format

```
Error: Unsupported export format.

Expected OpenAI export (with 'mapping' key) or Claude export (with 'chat_messages' key).

Please verify your export file is from ChatGPT or Claude.
```

### Invalid Provider Flag

```
Error: Invalid value for '--provider': 'invalid' is not one of 'openai', 'claude'.
```

### Provider Mismatch (Explicit vs Detected)

When `--provider` is specified but doesn't match file content:

```
Warning: File appears to be Claude export but --provider openai specified.
Proceeding with OpenAI adapter as requested.
```

## Exit Codes

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Command completed normally |
| 1 | Operational error | File not found, parse error |
| 2 | Usage error | Invalid arguments, unrecognized format |

## Output Format

### Human-Readable Output

No changes to output format. Conversations from both providers display identically:

```
┌──────────────────────────────────────────────────────────────┐
│ Freedom fighter portrait                                      │
│ ID: 5551eb71-ada2-45bd-8f91-0c4945a1e5a6                      │
│ Created: 2025-10-01 18:42:27 UTC                             │
│ Messages: 2                                                   │
└──────────────────────────────────────────────────────────────┘
```

### JSON Output

JSON output includes provider in metadata:

```json
{
  "conversations": [
    {
      "id": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
      "title": "Freedom fighter portrait",
      "created_at": "2025-10-01T18:42:27.303515Z",
      "message_count": 2,
      "metadata": {
        "provider": "claude"
      }
    }
  ]
}
```

## Implementation Notes

### Adapter Selection Logic

```python
def get_adapter(provider: str | None, file_path: Path) -> ConversationProvider:
    """Get appropriate adapter based on provider flag or auto-detection.

    Args:
        provider: Explicit provider ("openai", "claude") or None for auto-detect
        file_path: Path to export file

    Returns:
        OpenAIAdapter or ClaudeAdapter instance

    Raises:
        ValueError: If format unrecognized and provider not specified
    """
    if provider == "openai":
        return OpenAIAdapter()
    elif provider == "claude":
        return ClaudeAdapter()
    else:
        # Auto-detect
        detected = detect_provider(file_path)
        if detected == "claude":
            return ClaudeAdapter()
        else:
            return OpenAIAdapter()
```

### Typer Integration

```python
from typing import Annotated
import typer

ProviderOption = Annotated[
    str | None,
    typer.Option(
        "--provider",
        help="Export provider (openai or claude). Auto-detected if omitted.",
        case_sensitive=False,
    ),
]

@app.command()
def list_cmd(
    file_path: Path,
    provider: ProviderOption = None,
    limit: int = 100,
    json_output: bool = False,
):
    adapter = get_adapter(provider, file_path)
    # ... rest of command
```

## Testing Contract

### CLI Test Requirements

```python
def test_auto_detect_claude_format():
    """CLI auto-detects Claude export (FR-046, FR-047)"""

def test_auto_detect_openai_format():
    """CLI auto-detects OpenAI export (FR-046, FR-048)"""

def test_explicit_provider_flag():
    """--provider flag overrides auto-detection (FR-049)"""

def test_unrecognized_format_error():
    """Clear error for unrecognized format (FR-050)"""

def test_all_commands_support_provider_flag():
    """list, search, get, export, stats accept --provider"""

def test_output_identical_between_providers():
    """Same output format for Claude and OpenAI"""
```

## Backward Compatibility

- All existing commands work unchanged
- Auto-detection is default (no required changes)
- `--provider` flag is optional
- No changes to existing OpenAI behavior
