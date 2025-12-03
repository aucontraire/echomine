# Conversation Model

Represents a complete AI conversation with messages and metadata.

## Overview

The `Conversation` model is the primary data structure for representing AI conversations. It includes metadata (title, timestamps) and a collection of messages organized in a tree structure.

## API Reference

::: echomine.models.conversation.Conversation
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

# Access metadata
print(f"Title: {conversation.title}")
print(f"Created: {conversation.created_at}")
print(f"Messages: {len(conversation.messages)}")

# Access messages
for message in conversation.messages:
    print(f"{message.role}: {message.content[:50]}...")
```

### Message Tree Navigation

Conversations can have branching message trees (e.g., regenerated AI responses):

```python
# Get all threads (root-to-leaf paths)
threads = conversation.get_all_threads()
print(f"Conversation has {len(threads)} branches")

for i, thread in enumerate(threads, 1):
    print(f"\nThread {i} ({len(thread)} messages):")
    for msg in thread:
        print(f"  {msg.role}: {msg.content[:50]}...")

# Get specific thread by leaf message ID
thread = conversation.get_thread("msg-xyz-789")

# Get root messages (conversation starters)
roots = conversation.get_root_messages()

# Get children of a specific message
children = conversation.get_children("msg-abc-123")

# Check if message has children (branches)
has_branches = conversation.has_children("msg-abc-123")
```

### Immutability

Models are frozen (immutable) to prevent accidental data corruption:

```python
from pydantic import ValidationError

# ❌ This raises ValidationError (frozen model)
try:
    conversation.title = "New Title"
except ValidationError:
    print("Error: Cannot modify frozen model")

# ✅ Create modified copy instead
updated = conversation.model_copy(update={"title": "New Title"})
print(f"Original: {conversation.title}")
print(f"Updated: {updated.title}")
```

### Validation

All fields are strictly validated:

```python
from echomine.models import Conversation
from datetime import datetime, timezone
from pydantic import ValidationError

# ❌ Invalid: missing required fields
try:
    invalid = Conversation(
        id="conv-123",
        title="Test"
        # Missing: created_at, messages
    )
except ValidationError as e:
    print(f"Validation error: {e}")

# ✅ Valid: all required fields provided
valid = Conversation(
    id="conv-123",
    title="Test Conversation",
    created_at=datetime.now(timezone.utc),
    messages=[],
    metadata={}
)
```

## Model Fields

### Required Fields

- **id** (`str`): Unique conversation identifier
- **title** (`str`): Conversation title (1-2000 characters)
- **created_at** (`datetime`): Creation timestamp (UTC, timezone-aware)
- **messages** (`list[Message]`): List of conversation messages

### Optional Fields

- **updated_at** (`datetime | None`): Last update timestamp (UTC, timezone-aware), `None` if never updated
- **metadata** (`dict[str, Any]`): Provider-specific metadata (default: empty dict)

### Computed Properties

- **message_count** (`int`): Number of messages in conversation

## Message Tree Structure

Conversations are organized as trees, not linear sequences:

- Each message has an optional `parent_id` pointing to its predecessor
- Messages with `parent_id=None` are root messages (conversation starters)
- Messages can have multiple children (branches from regenerated responses)

**Example Tree:**

```
Root (parent_id=None)
├── Child 1 (parent_id=Root)
│   └── Child 1.1 (parent_id=Child 1)
└── Child 2 (parent_id=Root)  # Branch from regeneration
    └── Child 2.1 (parent_id=Child 2)
```

## Thread Extraction

**Thread**: A root-to-leaf path through the message tree.

```python
# Get all threads (all possible conversation paths)
threads = conversation.get_all_threads()

# Each thread is a list of messages in chronological order
for thread in threads:
    for msg in thread:
        print(f"{msg.role}: {msg.content}")
```

## Metadata

Provider-specific data is stored in the `metadata` dictionary:

```python
# OpenAI-specific metadata
conversation.metadata.get("openai_model", "unknown")
conversation.metadata.get("openai_conversation_template_id")
conversation.metadata.get("openai_plugin_ids", [])

# Check if metadata exists
if "openai_model" in conversation.metadata:
    print(f"Model: {conversation.metadata['openai_model']}")
```

## Related Models

- **[Message](message.md)**: Individual message model
- **[SearchResult](search.md#searchresult)**: Search result containing a conversation

## See Also

- [Library Usage Guide](../../library-usage.md#message-tree-navigation)
- [OpenAI Adapter](../adapters/openai.md)
