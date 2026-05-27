# Quickstart: Content Fidelity & Asset Recovery

**Feature**: 005-content-fidelity

## Filtering by Content Category (Library)

```python
from pathlib import Path
from echomine import OpenAIAdapter, ClaudeAdapter

# Parse and filter to conversational messages only
adapter = OpenAIAdapter()
for conversation in adapter.stream_conversations(Path("export/conversations.json")):
    for message in conversation.messages:
        category = message.metadata.get("content_type_category")
        if category == "conversational":
            print(f"[{message.role}]: {message.content[:100]}")
```

```python
# Same code works for Claude — provider-agnostic filtering
adapter = ClaudeAdapter()
for conversation in adapter.stream_conversations(Path("export/conversations.json")):
    for message in conversation.messages:
        if message.metadata.get("content_type_category") == "conversational":
            print(f"[{message.role}]: {message.content[:100]}")
```

## Accessing Reasoning/Thinking Metadata

```python
# Works identically for both OpenAI and Claude
for message in conversation.messages:
    if message.metadata.get("content_type_category") == "reasoning":
        thinking = message.metadata.get("thinking", {})
        print(f"Reasoning: {thinking.get('content', '')[:200]}")
        # Claude-specific fields (absent for OpenAI)
        if "cut_off" in thinking:
            print(f"  Truncated: {thinking['cut_off']}")
```

## Accessing Claude Attachments

```python
for message in conversation.messages:
    # Uploaded file text extracts
    for attachment in message.metadata.get("attachments", []):
        print(f"Attached: {attachment['file_name']} ({attachment['file_type']})")
        print(f"Content: {attachment['extracted_content'][:200]}...")

    # File reference tombstones (no binary available)
    for ref in message.metadata.get("file_refs", []):
        print(f"File referenced: {ref['file_name']} (uuid: {ref['file_uuid']})")
```

## Detecting Hidden Messages (OpenAI)

```python
for message in conversation.messages:
    if message.metadata.get("is_visually_hidden"):
        print(f"Hidden: {message.metadata.get('content_type')} (skipping)")
        continue
    # Process visible messages...
```

## Resolving Asset Pointers to Files (OpenAI)

```python
from echomine.utils.asset_resolver import resolve_asset

export_dir = Path("export/")
for message in conversation.messages:
    for image in message.images:
        resolved = resolve_asset(export_dir, image.asset_pointer)
        if resolved:
            print(f"Image: {resolved.path} (type: {resolved.detected_type})")
        else:
            print(f"Image not found: {image.asset_pointer}")
```

## Monitoring Schema Drift

```python
from collections import Counter

unknown_types: Counter[str] = Counter()
for conversation in adapter.stream_conversations(path):
    for message in conversation.messages:
        if message.metadata.get("content_type_category") == "unknown":
            raw_type = message.metadata.get("content_type", "")
            unknown_types[raw_type] += 1

if unknown_types:
    print(f"Unknown content types detected: {dict(unknown_types)}")
    print("Consider updating echomine's category mapping.")
```
