# Echomine Documentation

This directory contains the MkDocs documentation for Echomine.

## Building Documentation

### Install Dependencies

```bash
pip install -e ".[docs]"
```

### Build Static HTML

```bash
mkdocs build
```

Generated HTML will be in `site/` directory.

### Serve Locally

```bash
mkdocs serve
```

Documentation will be available at http://127.0.0.1:8000

### Deploy to GitHub Pages

```bash
mkdocs gh-deploy
```

## Documentation Structure

```
docs/
├── index.md                    # Home page
├── installation.md             # Installation guide
├── quickstart.md               # Quick start guide
├── library-usage.md            # Library API usage
├── cli-usage.md                # CLI reference
├── architecture.md             # Design principles
├── contributing.md             # Development guidelines
└── api/                        # API reference
    ├── index.md                # API overview
    ├── models/                 # Data models
    │   ├── conversation.md     # Conversation model
    │   ├── message.md          # Message model
    │   └── search.md           # Search models
    ├── adapters/               # Provider adapters
    │   ├── openai.md           # OpenAI adapter
    │   └── protocols.md        # Protocol definition
    ├── search/                 # Search algorithms
    │   └── ranking.md          # BM25 ranking
    └── cli/                    # CLI reference
        └── commands.md         # Command documentation
```

## Writing Documentation

### Markdown Files

Documentation is written in Markdown with these extensions:

- **Admonitions**: `!!! note`, `!!! warning`, etc.
- **Code blocks**: Syntax highlighting with language identifiers
- **Tables**: GitHub-flavored markdown tables
- **Links**: Internal links with `[text](path.md)`

### API Documentation

API documentation is auto-generated from docstrings using mkdocstrings:

```markdown
::: echomine.models.Conversation
    options:
      show_source: true
      heading_level: 3
```

This extracts documentation from the Python source code.

### Google-Style Docstrings

All docstrings follow Google style:

```python
def search(file_path: Path, query: SearchQuery) -> Iterator[SearchResult]:
    """Search conversations with BM25 ranking.

    Args:
        file_path: Path to export JSON file
        query: Search parameters

    Returns:
        Iterator yielding SearchResult objects

    Raises:
        FileNotFoundError: If file does not exist
        ParseError: If export format is invalid

    Example:
        ```python
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])
        for result in adapter.search(file_path, query):
            print(result.conversation.title)
        ```
    """
```

## Configuration

Documentation configuration is in `mkdocs.yml` at the project root.

Key settings:

- **theme**: Material theme with dark mode support
- **plugins**: mkdocstrings for API docs, search
- **markdown_extensions**: Code highlighting, tables, admonitions
- **nav**: Navigation structure

## Quality Checks

Before committing documentation changes:

1. **Build without errors**: `mkdocs build`
2. **Check links**: Verify all internal links work
3. **Preview locally**: `mkdocs serve` and review in browser
4. **Spell check**: Review for typos and grammar
5. **Code examples**: Ensure all examples are valid and tested

## Style Guide

- **Clear, concise language**: Avoid jargon unless necessary
- **Code examples**: Include practical, runnable examples
- **Progressive disclosure**: Start simple, add complexity gradually
- **Active voice**: "Use this function" not "This function is used"
- **Type hints**: Always include type hints in examples

## Troubleshooting

### mkdocstrings Can't Find Module

Ensure package is installed in development mode:

```bash
pip install -e .
```

### Broken Links

Check navigation structure in `mkdocs.yml` matches file paths in `docs/`.

### Build Errors

Check MkDocs output for specific errors:

```bash
mkdocs build --verbose
```

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)
