# Conversation Provider Protocol

Protocol definition for conversation export adapters.

## Overview

`ConversationProvider` is a Protocol (PEP 544) that defines the interface all conversation adapters must implement. This enables type-safe, provider-agnostic code.

## API Reference

::: echomine.models.protocols.ConversationProvider
    options:
      show_source: true
      heading_level: 3

## Usage Examples

### Type-Safe Adapter Usage

Write code that works with any adapter:

```python
from echomine.protocols import ConversationProvider
from echomine.models import Conversation
from pathlib import Path

def process_export(
    adapter: ConversationProvider,  # Works with ANY adapter
    file_path: Path
) -> int:
    """Process export file using any provider adapter."""
    count = 0
    for conv in adapter.stream_conversations(file_path):
        print(f"{conv.title}: {len(conv.messages)} messages")
        count += 1
    return count


# Works with OpenAI
from echomine import OpenAIAdapter
count = process_export(OpenAIAdapter(), Path("chatgpt.json"))

# Works with future providers
# from echomine import ClaudeAdapter
# count = process_export(ClaudeAdapter(), Path("claude.jsonl"))
```

### Adapter Registry Pattern

Build multi-provider systems:

```python
from echomine import OpenAIAdapter
from echomine.protocols import ConversationProvider

# Adapter registry
ADAPTERS: dict[str, type[ConversationProvider]] = {
    "openai": OpenAIAdapter,
    # Future providers:
    # "anthropic": ClaudeAdapter,
    # "google": GeminiAdapter,
}

def ingest_ai_export(provider: str, export_file: Path):
    """Ingest any AI provider export."""
    adapter_class = ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown provider: {provider}")

    adapter = adapter_class()

    # Same logic works for all providers!
    count = 0
    for conv in adapter.stream_conversations(export_file):
        knowledge_base.add(conv)
        count += 1

    return count


# Usage
ingest_ai_export("openai", Path("chatgpt_export.json"))
# Future: ingest_ai_export("anthropic", Path("claude_export.jsonl"))
```

## Protocol Methods

### stream_conversations()

Stream all conversations from export file.

**Signature:**

```python
def stream_conversations(
    self,
    file_path: Path,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
    on_skip: Optional[Callable[[str, str], None]] = None,
) -> Iterator[ConversationT]:
    ...
```

**Required for all adapters.**

### search()

Search conversations with filtering and ranking.

**Signature:**

```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
    on_skip: Optional[Callable[[str, str], None]] = None,
) -> Iterator[SearchResult[ConversationT]]:
    ...
```

**Required for all adapters.**

### get_conversation_by_id()

Retrieve specific conversation by ID.

**Signature:**

```python
def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str,
) -> Optional[ConversationT]:
    ...
```

**Required for all adapters.**

## Implementing Custom Adapters

### Step 1: Define Adapter Class

```python
from typing import Iterator, Optional
from pathlib import Path
from echomine.models import Conversation, SearchQuery, SearchResult

class ClaudeAdapter:
    """Adapter for Anthropic Claude exports."""

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: Optional[Callable[[int], None]] = None,
        on_skip: Optional[Callable[[str, str], None]] = None,
    ) -> Iterator[Conversation]:
        """Stream conversations from Claude export."""
        # Implementation here
        pass

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        *,
        progress_callback: Optional[Callable[[int], None]] = None,
        on_skip: Optional[Callable[[str, str], None]] = None,
    ) -> Iterator[SearchResult[Conversation]]:
        """Search Claude conversations."""
        # Implementation here
        pass

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """Get Claude conversation by ID."""
        # Implementation here
        pass
```

### Step 2: Normalize Provider-Specific Data

Map provider-specific fields to standard `Conversation` model:

```python
# Claude-specific parsing
def _parse_claude_conversation(self, raw_data: dict) -> Conversation:
    """Parse Claude export format."""
    return Conversation(
        id=raw_data["conversation_id"],
        title=raw_data["name"],
        created_at=self._parse_timestamp(raw_data["created_at"]),
        messages=self._parse_messages(raw_data["messages"]),
        metadata={
            "claude_model": raw_data.get("model", "unknown"),
            "claude_workspace_id": raw_data.get("workspace_id"),
        }
    )
```

### Step 3: Normalize Roles

Map provider-specific roles to standard roles:

```python
def _normalize_role(self, claude_role: str) -> Literal["user", "assistant", "system"]:
    """Normalize Claude roles to standard roles."""
    role_mapping = {
        "human": "user",
        "assistant": "assistant",
        # Claude doesn't have system role
    }
    return role_mapping.get(claude_role, "user")
```

### Step 4: Implement Streaming

Use generators for memory efficiency:

```python
import ijson

def stream_conversations(
    self,
    file_path: Path,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
    on_skip: Optional[Callable[[str, str], None]] = None,
) -> Iterator[Conversation]:
    """Stream conversations with O(1) memory."""
    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")  # Streaming parser
        count = 0

        for item in parser:
            try:
                conversation = self._parse_claude_conversation(item)
                yield conversation
                count += 1

                # Progress reporting
                if progress_callback and count % 100 == 0:
                    progress_callback(count)

            except ValidationError as e:
                # Graceful degradation
                if on_skip:
                    on_skip(item.get("conversation_id", "unknown"), str(e))
                continue
```

### Step 5: Type Checking

Verify protocol compliance with mypy:

```python
from echomine.protocols import ConversationProvider

# This line verifies ClaudeAdapter implements the protocol
adapter: ConversationProvider = ClaudeAdapter()  # Type-checks!
```

## Design Guidelines

### Stateless Design

Adapters should have no `__init__` parameters:

```python
# ✅ CORRECT: Stateless
class ClaudeAdapter:
    def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
        pass

# ❌ WRONG: Stateful
class ClaudeAdapter:
    def __init__(self, file_path: Path):  # NO!
        self.file_path = file_path
```

### Memory Efficiency

Always use streaming (generators, not lists):

```python
# ✅ CORRECT: Generator
def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
    for item in parser:
        yield conversation

# ❌ WRONG: List (loads entire file)
def stream_conversations(self, file_path: Path) -> list[Conversation]:
    return [conversation for item in parser]
```

### Error Handling

- Fail fast on unrecoverable errors (file not found, unsupported version)
- Graceful degradation on data errors (skip malformed entries)

### Progress Reporting

Invoke callbacks every 100 items OR 100ms (whichever comes first):

```python
import time

last_progress_time = time.monotonic()
count = 0

for item in parser:
    count += 1
    current_time = time.monotonic()

    if progress_callback and (count % 100 == 0 or current_time - last_progress_time >= 0.1):
        progress_callback(count)
        last_progress_time = current_time
```

## Protocol Benefits

1. **Type Safety**: mypy validates adapter implementations
2. **Interchangeability**: Swap providers without code changes
3. **Testability**: Mock adapters for testing
4. **Documentation**: Self-documenting interface

## Related

- **[OpenAI Adapter](openai.md)**: Reference implementation
- **[Conversation Model](../models/conversation.md)**: Standard conversation model
- **[SearchQuery](../models/search.md)**: Search parameters

## See Also

- [Architecture](../../architecture.md#adapter-pattern)
- [Library Usage](../../library-usage.md)
