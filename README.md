# Echomine

**Library-first tool for parsing AI conversation exports with search, filtering, and markdown export**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy.readthedocs.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/aucontraire/echomine/graph/badge.svg)](https://codecov.io/gh/aucontraire/echomine)

## Overview

Echomine is a Python library and CLI tool for parsing, searching, and exporting AI conversation exports. Initially designed for ChatGPT exports, it uses a multi-provider adapter pattern to support future AI platforms (Claude, Gemini, etc.).

### Key Features

- **Memory Efficient**: Stream-based parsing handles 1GB+ files with constant memory usage
- **Full-Text Search**: BM25 relevance ranking for keyword searches across conversations
- **Type Safe**: Strict typing with Pydantic v2 and mypy --strict compliance
- **Library First**: All CLI capabilities available as importable Python library
- **Multi-Provider Ready**: Adapter pattern supports multiple AI export formats

### Design Principles

1. **Library-First Architecture**: CLI built on top of library, not vice versa
2. **Strict Type Safety**: mypy --strict, no `Any` types in public API
3. **Memory Efficiency**: Stream-based parsing, never load entire file into memory
4. **Test-Driven Development**: All features test-first validated
5. **YAGNI**: Simple solutions, no speculative features

See [Constitution](specs/001-ai-chat-parser/constitution.md) for complete design principles.

## Installation

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

### From PyPI (when published)

```bash
pip install echomine
```

## Quick Start

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

# Get conversation by ID
echomine get conversation export.json conv-abc123

# Get message by ID (with conversation hint for performance)
echomine get message export.json msg-def456 -c conv-abc123

# Export conversation to markdown
echomine export export.json conv-abc123 --output algo.md

# JSON output for piping
echomine search export.json --keywords "python" --json | jq '.results[].title'

# Version info
echomine --version
```

See [Quickstart Guide](specs/001-ai-chat-parser/quickstart.md) for detailed examples.

## Development

### Prerequisites

- Python 3.12 or higher
- Git

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/echomine/echomine.git
cd echomine

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=echomine --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m contract       # Contract tests only
pytest -m performance    # Performance benchmarks
```

### Code Quality

```bash
# Type checking (strict mode)
mypy src/

# Linting and formatting
ruff check .
ruff format .

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Project Structure

```
echomine/
├── src/echomine/           # Library source code
│   ├── models/             # Pydantic data models
│   ├── adapters/           # Provider adapters (OpenAI, etc.)
│   ├── parsers/            # Streaming JSON parsers
│   ├── search/             # Search and ranking logic
│   ├── exporters/          # Export formatters (markdown, JSON)
│   └── cli/                # CLI commands
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── contract/           # Protocol contract tests
│   └── performance/        # Performance benchmarks
└── specs/                  # Design documents
    └── 001-ai-chat-parser/ # Feature specification
```

## Documentation

- [Feature Specification](specs/001-ai-chat-parser/spec.md)
- [Implementation Plan](specs/001-ai-chat-parser/plan.md)
- [Quickstart Guide](specs/001-ai-chat-parser/quickstart.md)
- [CLI Interface Contract](specs/001-ai-chat-parser/contracts/cli_spec.md)
- [Data Model](specs/001-ai-chat-parser/data-model.md)
- [Architecture Decisions](specs/001-ai-chat-parser/research.md)

## Performance

Echomine is designed for memory efficiency and speed:

- **Memory**: O(1) memory usage regardless of file size (streaming-based)
- **Search**: <30 seconds for 1.6GB files (10K conversations, 50K messages)
- **Listing**: <5 seconds for 10K conversations

See [Performance Requirements](specs/001-ai-chat-parser/spec.md#performance-requirements) for benchmarks.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup and prerequisites
- TDD workflow (RED-GREEN-REFACTOR cycle mandatory)
- Testing guidelines (pytest, mypy --strict, ruff)
- Code quality standards and conventions
- Commit message format (conventional commits)
- Pull request process

## License

AGPL-3.0 License - See [LICENSE](LICENSE) file for details

## Acknowledgments

Built with:
- [Pydantic](https://docs.pydantic.dev/) - Data validation and type safety
- [ijson](https://github.com/ICRAR/ijson) - Streaming JSON parser
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [structlog](https://www.structlog.org/) - Structured logging
