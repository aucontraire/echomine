# Asset Resolver

Resolve OpenAI asset pointers to actual files in export bundles.

## Overview

OpenAI exports reference images and other assets via URI pointers (e.g., `sediment://file_abc123`). The asset resolver maps these pointers to actual files on disk using file ID matching and magic-byte MIME type detection.

## ResolvedAsset

::: echomine.utils.asset_resolver.ResolvedAsset
    options:
      show_source: true
      heading_level: 3

## resolve_asset

::: echomine.utils.asset_resolver.resolve_asset
    options:
      show_source: true
      heading_level: 3

## Supported Formats

Magic-byte detection supports the following formats:

| Format | MIME Type | Signature |
|---|---|---|
| PNG | `image/png` | `\x89PNG\r\n\x1a\n` |
| JPEG | `image/jpeg` | `\xff\xd8\xff` |
| WebP | `image/webp` | `RIFF....WEBP` |
| GIF | `image/gif` | `GIF87a` or `GIF89a` |
| WAV | `audio/wav` | `RIFF....WAVE` |

Unrecognized formats return `application/octet-stream`.

## Usage Examples

### Resolve Image Assets

```python
from echomine.utils.asset_resolver import resolve_asset
from pathlib import Path

export_dir = Path("chatgpt_export/")

# Resolve a single asset pointer
asset = resolve_asset(export_dir, "sediment://file-abc123")
if asset:
    print(f"Path: {asset.path}")
    print(f"Type: {asset.detected_type}")       # e.g., "image/png"
    print(f"Extension: {asset.original_extension}")  # e.g., ".png"
    print(f"File ID: {asset.file_id}")           # e.g., "file-abc123"
```

### Resolve All Images in a Conversation

```python
from echomine import OpenAIAdapter
from echomine.utils.asset_resolver import resolve_asset
from pathlib import Path

adapter = OpenAIAdapter()
export_file = Path("chatgpt_export/conversations.json")
export_dir = export_file.parent

for conv in adapter.stream_conversations(export_file):
    for msg in conv.messages:
        for img in msg.images:
            asset = resolve_asset(export_dir, img.asset_pointer)
            if asset:
                print(f"[{conv.title}] {asset.detected_type}: {asset.path.name}")
```
