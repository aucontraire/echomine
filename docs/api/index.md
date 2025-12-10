# API Reference

Complete API documentation for Echomine library.

## Overview

Echomine provides a clean, type-safe API for parsing and searching AI conversation exports. All public APIs are fully typed and validated.

## Main Components

### Models

Data models built with Pydantic v2 for strict validation and type safety:

- **[Conversation](models/conversation.md)**: Represents a complete conversation with messages
- **[Message](models/message.md)**: Individual message in a conversation
- **[Search](models/search.md)**: Search query and result models

### Adapters

Provider-specific implementations for parsing conversation exports:

- **[OpenAI Adapter](adapters/openai.md)**: ChatGPT conversation export parser
- **[Claude Adapter](adapters/claude.md)**: Anthropic Claude conversation export parser
- **[Protocols](adapters/protocols.md)**: ConversationProvider protocol definition

### Search

Search and ranking algorithms:

- **[Ranking](search/ranking.md)**: BM25 relevance ranking implementation

### CLI

Command-line interface (built on library):

- **[Commands](cli/commands.md)**: CLI command reference

## Quick Example

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

# Initialize adapter
adapter = OpenAIAdapter()

# Stream conversations
for conversation in adapter.stream_conversations(Path("export.json")):
    print(f"{conversation.title}: {len(conversation.messages)} messages")

# Search with keywords
query = SearchQuery(keywords=["python"], limit=10)
for result in adapter.search(Path("export.json"), query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

## Type Safety

All public APIs provide complete type hints for IDE support:

```python
from typing import Iterator
from echomine import OpenAIAdapter
from echomine.models import Conversation, SearchQuery, SearchResult

adapter: OpenAIAdapter = OpenAIAdapter()
conversations: Iterator[Conversation] = adapter.stream_conversations(file_path)
results: Iterator[SearchResult[Conversation]] = adapter.search(file_path, query)
```

## Import Paths

### Top-Level Imports (Recommended)

```python
from echomine import OpenAIAdapter
from echomine.models import Conversation, Message, SearchQuery, SearchResult
```

### Full Module Paths

```python
from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.search import SearchQuery, SearchResult
```

## Navigation

- **[Models](models/conversation.md)**: Data models and schemas
- **[Adapters](adapters/openai.md)**: Provider implementations
- **[Search](search/ranking.md)**: Ranking algorithms
- **[CLI](cli/commands.md)**: Command-line interface
