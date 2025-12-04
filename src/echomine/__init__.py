"""Echomine: Library-first tool for parsing AI conversation exports.

This package provides tools for parsing, searching, and exporting AI chat conversation
exports (initially ChatGPT) with memory-efficient streaming, strict type safety, and
both programmatic (library) and command-line (CLI) interfaces.

Core Features:
- Stream-based parsing for memory efficiency (handles 1GB+ files)
- Full-text search with BM25 relevance ranking
- Date range filtering
- Markdown export with preserved conversation threading
- Multi-provider adapter pattern (OpenAI ChatGPT initially)

Library-First Architecture:
The CLI is built on top of the library. All capabilities available via command-line
are also available programmatically.

Example Usage (Library):
    ```python
    from echomine import OpenAIAdapter
    from pathlib import Path

    # List conversations
    adapter = OpenAIAdapter()
    for conversation in adapter.stream_conversations(Path("export.json")):
        print(f"{conversation.title}: {len(conversation.messages)} messages")

    # Search conversations
    results = adapter.search(
        Path("export.json"),
        keywords=["algorithm", "design"],
        limit=10
    )
    for result in results:
        print(f"{result.conversation.title} (score: {result.relevance_score})")
    ```

Example Usage (CLI):
    ```bash
    # List all conversations
    echomine list export.json

    # Search with keywords
    echomine search export.json --keywords "algorithm,design" --limit 10

    # Export to markdown
    echomine export export.json --title "Project" --output project.md
    ```

Type Safety:
All public APIs are strictly typed with Pydantic models and mypy --strict compliance.

License:
    AGPL-3.0 License - See LICENSE file for details
"""

__version__ = "1.1.0"
__author__ = "Echomine Contributors"

# Public API imports (T061-T062)
from echomine.adapters.openai import OpenAIAdapter
from echomine.exceptions import (
    EchomineError,
    ParseError,
    SchemaVersionError,
    ValidationError,
)
from echomine.export.markdown import MarkdownExporter
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.protocols import ConversationProvider
from echomine.models.search import SearchQuery, SearchResult


# T063: __all__ defines public API surface for library consumers
__all__: list[str] = [
    # Version metadata
    "__version__",
    # Data models
    "Conversation",
    "Message",
    "SearchQuery",
    "SearchResult",
    # Adapters
    "OpenAIAdapter",
    # Exporters
    "MarkdownExporter",
    # Protocols
    "ConversationProvider",
    # Exceptions
    "EchomineError",
    "ParseError",
    "ValidationError",
    "SchemaVersionError",
]
