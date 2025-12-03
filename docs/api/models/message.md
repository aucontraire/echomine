# Message Model

Represents an individual message within a conversation.

## Overview

The `Message` model represents a single message in a conversation, including the role (user/assistant/system), content, timestamp, and parent relationship for tree navigation.

## API Reference

::: echomine.models.message.Message
    options:
      show_source: true
      heading_level: 3

## Usage Examples

### Basic Access

```python
from echomine import OpenAIAdapter
from pathlib import Path

adapter = OpenAIAdapter()
conversation = adapter.get_conversation_by_id(Path("export.json"), "conv-abc123")

# Access messages
for message in conversation.messages:
    print(f"[{message.timestamp}] {message.role}: {message.content[:50]}...")
```

### Role Types

Messages have normalized roles:

```python
from typing import Literal

# Message.role is Literal["user", "assistant", "system"]
for message in conversation.messages:
    if message.role == "user":
        print(f"User: {message.content}")
    elif message.role == "assistant":
        print(f"AI: {message.content}")
    elif message.role == "system":
        print(f"System: {message.content}")
    # No other values possible - type safety guaranteed!
```

### Timestamp Handling

All timestamps are timezone-aware UTC datetimes:

```python
from datetime import timezone

for message in conversation.messages:
    # Guaranteed to be UTC and timezone-aware
    assert message.timestamp.tzinfo == timezone.utc

    # Safe to compare and serialize
    print(f"{message.timestamp.isoformat()}: {message.content}")

# Convert to local timezone for display
import datetime
local_tz = datetime.datetime.now().astimezone().tzinfo
for msg in conversation.messages:
    local_time = msg.timestamp.astimezone(local_tz)
    print(f"[{local_time}] {msg.role}: {msg.content[:30]}...")
```

### Parent-Child Relationships

Messages are organized in a tree structure:

```python
# Check if message is root (conversation starter)
is_root = message.parent_id is None

# Find message's parent
parent_id = message.parent_id
if parent_id:
    parent = next((m for m in conversation.messages if m.id == parent_id), None)
    if parent:
        print(f"Parent: {parent.content[:50]}...")

# Find message's children
children = [m for m in conversation.messages if m.parent_id == message.id]
print(f"Message has {len(children)} children")
```

### Immutability

Messages are frozen (immutable):

```python
from pydantic import ValidationError

# ❌ This raises ValidationError
try:
    message.content = "New content"
except ValidationError:
    print("Error: Cannot modify frozen model")

# ✅ Create modified copy instead
updated = message.model_copy(update={"content": "New content"})
```

### Validation

All fields are strictly validated:

```python
from echomine.models import Message
from datetime import datetime, timezone
from pydantic import ValidationError

# ❌ Invalid: naive timestamp (no timezone)
try:
    invalid = Message(
        id="msg-123",
        content="Hello",
        role="user",
        timestamp=datetime.now(),  # ❌ Not timezone-aware!
        parent_id=None
    )
except ValidationError as e:
    print(f"Error: {e}")

# ✅ Valid: timezone-aware UTC timestamp
valid = Message(
    id="msg-123",
    content="Hello",
    role="user",
    timestamp=datetime.now(timezone.utc),
    parent_id=None
)
```

## Model Fields

### Required Fields

- **id** (`str`): Unique message identifier (non-empty)
- **content** (`str`): Message text content
- **role** (`Literal["user", "assistant", "system"]`): Message role (normalized)
- **timestamp** (`datetime`): Message timestamp (UTC, timezone-aware)

### Optional Fields

- **parent_id** (`str | None`): ID of parent message, `None` for root messages
- **metadata** (`dict[str, Any]`): Message-specific metadata (default: empty dict)

## Role Normalization

All provider-specific roles are normalized to three standard values:

| Provider | Source Role | Normalized Role |
|----------|-------------|----------------|
| OpenAI | "user" | "user" |
| OpenAI | "assistant" | "assistant" |
| OpenAI | "system" | "system" |
| Anthropic (future) | "human" | "user" |
| Anthropic (future) | "assistant" | "assistant" |
| Google (future) | "user" | "user" |
| Google (future) | "model" | "assistant" |

## Timestamp Format

All timestamps follow these rules:

1. **Timezone-aware**: Must have `tzinfo` set
2. **UTC**: Normalized to UTC timezone
3. **ISO 8601**: Serialized as ISO 8601 strings

**Example:**

```python
from datetime import datetime, timezone

# Create message with current UTC time
message = Message(
    id="msg-123",
    content="Hello",
    role="user",
    timestamp=datetime.now(timezone.utc),
    parent_id=None
)

# Serialize to ISO 8601
iso_timestamp = message.timestamp.isoformat()
# Output: "2024-01-15T10:30:00+00:00"
```

## Metadata

Message-specific metadata (e.g., image attachments, code blocks):

```python
# Access metadata
image_urls = message.metadata.get("image_urls", [])
code_blocks = message.metadata.get("code_blocks", [])

# Check if metadata exists
if "image_urls" in message.metadata:
    print(f"Message has {len(message.metadata['image_urls'])} images")
```

## Related Models

- **[Conversation](conversation.md)**: Container for messages
- **[Image](../../library-usage.md)**: Image attachment model (if present in metadata)

## See Also

- [Library Usage Guide](../../library-usage.md#message-tree-navigation)
- [Data Validation](../../library-usage.md#data-validation-and-immutability)
