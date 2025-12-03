# Documentation Guide

This guide covers writing documentation for Echomine, including docstrings, user guides, and API reference.

## Documentation Types

### 1. API Reference (Auto-Generated)

Generated automatically from Python docstrings using mkdocstrings:

- **Source**: Docstrings in `src/echomine/`
- **Output**: `docs/api/` pages
- **Updates**: Automatic when code changes

### 2. User Guides (Manual)

Written manually in Markdown:

- **Source**: `docs/*.md` files
- **Examples**: quickstart.md, cli-usage.md, library-usage.md
- **Updates**: Manual when features change

### 3. Developer Docs (Manual)

This section and related guides:

- **Source**: `docs/development/`, `docs/maintaining/`
- **Updates**: Manual when processes change

## Docstring Format (Google Style)

Echomine uses Google-style docstrings for consistency with mkdocstrings.

### Function Docstring

```python
def search(
    self,
    file_path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations matching query criteria with BM25 ranking.

    Streams through the export file and returns matching conversations
    ranked by relevance score. Uses O(1) memory regardless of file size.

    Args:
        file_path: Path to OpenAI export JSON file.
        query: Search parameters including keywords, date filters, and limit.
        progress_callback: Optional callback invoked with count of processed
            conversations. Called every 100 items or 100ms.

    Yields:
        SearchResult containing matched conversation and relevance score (0.0-1.0).
        Results are yielded in descending order by score.

    Raises:
        FileNotFoundError: If file_path does not exist.
        PermissionError: If file is not readable.
        ParseError: If export format is invalid or unsupported.

    Example:
        ```python
        from echomine import OpenAIAdapter, SearchQuery
        from pathlib import Path

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python", "algorithm"], limit=10)

        for result in adapter.search(Path("export.json"), query):
            print(f"{result.score:.2f}: {result.conversation.title}")
        ```

    Note:
        The search uses BM25 ranking algorithm. Title-only searches
        (no keywords) skip full-text ranking for better performance.

    See Also:
        - `stream_conversations`: For unfiltered iteration
        - `get_conversation_by_id`: For direct ID lookup
    """
```

### Class Docstring

```python
class OpenAIAdapter:
    """Adapter for parsing and searching OpenAI ChatGPT exports.

    Implements the ConversationProvider protocol for ChatGPT export files.
    Stateless design allows reuse across multiple files.

    The adapter handles:
        - Streaming conversations with O(1) memory usage
        - BM25-ranked keyword search
        - Date range and title filtering
        - Graceful handling of malformed entries

    Attributes:
        None. This adapter is stateless by design.

    Example:
        ```python
        from echomine import OpenAIAdapter
        from pathlib import Path

        adapter = OpenAIAdapter()

        # List all conversations
        for conv in adapter.stream_conversations(Path("export.json")):
            print(conv.title)

        # Search with keywords
        from echomine import SearchQuery
        query = SearchQuery(keywords=["python"])
        for result in adapter.search(Path("export.json"), query):
            print(f"{result.score:.2f}: {result.conversation.title}")
        ```

    Note:
        OpenAI exports use a specific JSON schema. This adapter supports
        the current export format as of 2024. Future format changes may
        require adapter updates.

    See Also:
        - `ConversationProvider`: The protocol this adapter implements
        - `Conversation`: The data model returned by this adapter
    """
```

### Property Docstring

```python
@property
def message_count(self) -> int:
    """Total number of messages across all branches.

    Counts all messages in the conversation tree, including
    messages in alternate branches.

    Returns:
        Non-negative integer count of messages.

    Example:
        ```python
        conv = adapter.get_conversation_by_id(path, conv_id)
        print(f"Conversation has {conv.message_count} messages")
        ```
    """
    return len(self.messages)
```

### Module Docstring

```python
"""OpenAI ChatGPT export adapter.

This module provides the OpenAIAdapter class for parsing and searching
ChatGPT conversation exports.

Example:
    ```python
    from echomine.adapters.openai import OpenAIAdapter

    adapter = OpenAIAdapter()
    for conv in adapter.stream_conversations(Path("export.json")):
        print(conv.title)
    ```

Typical usage:
    1. Create adapter instance (stateless, reusable)
    2. Call stream_conversations() for listing
    3. Call search() for filtered/ranked results
    4. Call get_conversation_by_id() for specific lookup

See Also:
    - `echomine.protocols.ConversationProvider`: Protocol definition
    - `echomine.models.Conversation`: Data model
"""
```

## MkDocs Configuration

### mkdocs.yml Structure

```yaml
site_name: Echomine
nav:
  - Home: index.md
  - Getting Started:
    - Installation: installation.md
    - Quickstart: quickstart.md
  - User Guide:
    - CLI Usage: cli-usage.md
    - Library Usage: library-usage.md
  - API Reference:
    - api/index.md
    - Models:
      - Conversation: api/models/conversation.md
      - Message: api/models/message.md
    - Adapters:
      - OpenAI: api/adapters/openai.md
  - Development:
    - development/index.md
    - Setup: development/setup.md
    - Testing: development/testing.md

theme:
  name: material
  features:
    - content.code.copy
    - navigation.sections

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
```

### API Reference Pages

Create stub pages that pull from docstrings:

```markdown
<!-- docs/api/adapters/openai.md -->
# OpenAI Adapter

::: echomine.adapters.openai.OpenAIAdapter
    options:
      show_root_heading: true
      show_source: true
      members:
        - stream_conversations
        - search
        - get_conversation_by_id
```

## Writing User Guides

### Structure

1. **Start with "why"**: What problem does this solve?
2. **Quick example**: Working code immediately
3. **Detailed explanation**: Step-by-step guide
4. **Advanced usage**: Edge cases, options
5. **Troubleshooting**: Common issues

### Example Page Structure

```markdown
# Feature Name

Brief description of what this feature does and why you'd use it.

## Quick Start

\`\`\`python
# Minimal working example
from echomine import OpenAIAdapter
adapter = OpenAIAdapter()
\`\`\`

## Basic Usage

### Step 1: Setup

Explanation...

### Step 2: Execute

Explanation...

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| limit | int | 10 | Maximum results |

## Examples

### Example: Search by Keywords

\`\`\`python
# Full example with context
\`\`\`

### Example: Filter by Date

\`\`\`python
# Another example
\`\`\`

## Troubleshooting

### Error: FileNotFoundError

**Cause**: File path doesn't exist.

**Solution**: Verify the path...

## See Also

- [Related Feature](other-page.md)
- [API Reference](api/module.md)
```

## Building Documentation

### Local Development

```bash
# Install docs dependencies
pip install -e ".[dev]"

# Serve with live reload
mkdocs serve
# View at http://127.0.0.1:8000

# Build static site
mkdocs build
# Output in site/ directory
```

### Checking for Issues

```bash
# Build with strict mode (fails on warnings)
mkdocs build --strict

# Common warnings:
# - Broken links
# - Missing pages in nav
# - Invalid markdown
```

### Deployment

Documentation deploys automatically via GitHub Actions when pushed to main:

```bash
git add docs/
git commit -m "docs: update user guide"
git push origin main
# GitHub Actions runs mkdocs gh-deploy
```

## Style Guidelines

### Do

- Use active voice ("Returns the count" not "The count is returned")
- Include working code examples
- Document all public APIs
- Keep examples minimal but complete
- Link to related documentation

### Don't

- Document private methods (prefix with `_`)
- Repeat type information in description
- Use jargon without explanation
- Leave placeholder TODOs in docs

### Code Examples

```python
# Good: Complete, runnable example
from echomine import OpenAIAdapter, SearchQuery
from pathlib import Path

adapter = OpenAIAdapter()
query = SearchQuery(keywords=["python"], limit=5)
results = list(adapter.search(Path("export.json"), query))
print(f"Found {len(results)} results")

# Bad: Incomplete, won't run
results = adapter.search(path, query)  # What's adapter? path? query?
```

## Updating Documentation

### When to Update

- New features: Add to user guide + API reference
- Changed behavior: Update affected pages
- Bug fixes: Update if behavior was documented incorrectly
- Breaking changes: Add migration guide

### Checklist

- [ ] Docstrings updated for changed functions
- [ ] User guide reflects new behavior
- [ ] Examples still work
- [ ] Links not broken
- [ ] `mkdocs build --strict` passes

## Next Steps

- [Testing Guide](testing.md): Writing tests
- [Type Checking](type-checking.md): Type hints
- [Contributing](../contributing.md): Full contribution guide

---

**Last Updated**: 2025-11-30
