# Echomine

**Library-first tool for parsing AI conversation exports with search, filtering, and markdown export**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy.readthedocs.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Overview

Echomine is a Python library and CLI tool for parsing, searching, and exporting AI conversation exports. Initially designed for ChatGPT exports, it uses a multi-provider adapter pattern to support future AI platforms (Claude, Gemini, etc.).

## Key Features

- **Memory Efficient**: Stream-based parsing handles 1GB+ files with constant memory usage
- **Full-Text Search**: BM25 relevance ranking for keyword searches across conversations
- **Type Safe**: Strict typing with Pydantic v2 and mypy --strict compliance
- **Library First**: All CLI capabilities available as importable Python library
- **Multi-Provider Ready**: Adapter pattern supports multiple AI export formats

## Design Principles

1. **Library-First Architecture**: CLI built on top of library, not vice versa
2. **Strict Type Safety**: mypy --strict, no `Any` types in public API
3. **Memory Efficiency**: Stream-based parsing, never load entire file into memory
4. **Test-Driven Development**: All features test-first validated
5. **YAGNI**: Simple solutions, no speculative features

## Quick Example

### Library API (Primary Interface)

```python
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

# Initialize adapter (stateless, reusable)
adapter = OpenAIAdapter()
export_file = Path("conversations.json")

# 1. List all conversations (discovery)
for conversation in adapter.stream_conversations(export_file):
    print(f"[{conversation.created_at.date()}] {conversation.title}")
    print(f"  Messages: {len(conversation.messages)}")

# 2. Search with keywords (BM25 ranking)
query = SearchQuery(keywords=["algorithm", "design"], limit=10)
for result in adapter.search(export_file, query):
    print(f"{result.conversation.title} (score: {result.score:.2f})")

# 3. Filter by date range
from datetime import date
query = SearchQuery(
    keywords=["refactor"],
    from_date=date(2024, 1, 1),
    to_date=date(2024, 3, 31),
    limit=5
)
results = list(adapter.search(export_file, query))

# 4. Get specific conversation by ID
conversation = adapter.get_conversation_by_id(export_file, "conv-abc123")
if conversation:
    print(f"Found: {conversation.title}")
```

### CLI Usage (Built on Library)

```bash
# List all conversations
echomine list export.json

# Search by keywords
echomine search export.json --keywords "algorithm,design" --limit 10

# Search by title (fast, metadata-only)
echomine search export.json --title "Project"

# Filter by date range
echomine search export.json --from-date "2024-01-01" --to-date "2024-03-31"

# Export conversation to markdown
echomine export export.json conv-abc123 --output algo.md

# JSON output for piping
echomine search export.json --keywords "python" --json | jq '.results[].title'
```

## Performance

Echomine is designed for memory efficiency and speed:

- **Memory**: O(1) memory usage regardless of file size (streaming-based)
- **Search**: <30 seconds for 1.6GB files (10K conversations, 50K messages)
- **Listing**: <5 seconds for 10K conversations

## Installation

### From PyPI (when published)

```bash
pip install echomine
```

### From Source

```bash
# Clone repository
git clone https://github.com/echomine/echomine.git
cd echomine

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## Next Steps

- [Quick Start Guide](quickstart.md): Get started with library and CLI usage
- [Library Usage](library-usage.md): Comprehensive library API guide
- [CLI Usage](cli-usage.md): Command-line interface reference
- [API Reference](api/index.md): Detailed API documentation
- [Architecture](architecture.md): Design principles and patterns
- [Contributing](contributing.md): Development setup and guidelines

## License

MIT License - See [LICENSE](https://github.com/echomine/echomine/blob/master/LICENSE) file for details

## Acknowledgments

Built with:
- [Pydantic](https://docs.pydantic.dev/) - Data validation and type safety
- [ijson](https://github.com/ICRAR/ijson) - Streaming JSON parser
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [structlog](https://www.structlog.org/) - Structured logging
