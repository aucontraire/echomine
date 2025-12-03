# CLI Commands

Command-line interface built on the Echomine library.

## Overview

The Echomine CLI provides a thin wrapper over the library API for terminal use. All CLI commands use the same library functions available programmatically.

See [CLI Usage Guide](../../cli-usage.md) for comprehensive command reference.

## Architecture

The CLI follows the library-first architecture principle:

```
User Input (CLI)
    ↓
Typer Command Handler
    ↓
Library Function (OpenAIAdapter)
    ↓
Rich Formatter (Terminal Output)
    ↓
stdout/stderr
```

**Key Points:**

- CLI contains NO business logic
- All operations delegated to library
- Rich formatting for human-readable output
- JSON mode for programmatic use

## Commands

### list

List all conversations in an export file.

**Usage:**

```bash
echomine list [OPTIONS] FILE_PATH
```

**Library Equivalent:**

```python
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()
for conversation in adapter.stream_conversations(file_path):
    print(f"{conversation.title}: {len(conversation.messages)} messages")
```

**See:** [CLI Usage - list](../../cli-usage.md#list)

### search

Search conversations with keyword matching and relevance ranking.

**Usage:**

```bash
echomine search [OPTIONS] FILE_PATH
```

**Library Equivalent:**

```python
from echomine import OpenAIAdapter, SearchQuery

adapter = OpenAIAdapter()
query = SearchQuery(keywords=["python"], limit=10)
for result in adapter.search(file_path, query):
    print(f"[{result.score:.2f}] {result.conversation.title}")
```

**See:** [CLI Usage - search](../../cli-usage.md#search)

### export

Export a specific conversation to markdown or JSON format.

**Usage:**

```bash
echomine export [OPTIONS] FILE_PATH CONVERSATION_ID
```

**Options:**

- `--output PATH`: Output file path (if not specified, prints to stdout)
- `--format TEXT`: Export format: `markdown` (default) or `json`

**Library Equivalent:**

```python
from echomine import OpenAIAdapter
from echomine.exporters import MarkdownExporter, JSONExporter

adapter = OpenAIAdapter()
conversation = adapter.get_conversation_by_id(file_path, conversation_id)

if conversation:
    # Markdown export (default)
    markdown_exporter = MarkdownExporter()
    markdown = markdown_exporter.export(conversation)
    print(markdown)

    # JSON export
    json_exporter = JSONExporter()
    json_output = json_exporter.export(conversation)
    print(json_output)
```

**See:** [CLI Usage - export](../../cli-usage.md#export)

## Output Formats

### Human-Readable (Default)

Uses Rich library for formatted terminal output:

```bash
echomine list export.json

# Output:
# Conversations in export.json
#
# [2024-01-15] Python Async Best Practices
#   Messages: 42
#   ID: conv-abc123
# ...
```

### JSON (--json flag)

Machine-readable JSON on stdout:

```bash
echomine list export.json --json

# Output:
# {"conversations": [...], "total": 145}
```

## Exit Codes

Standard UNIX exit codes:

- **0**: Success
- **1**: Operational error (file not found, parsing error)
- **2**: Usage error (invalid arguments)

## Implementation

### Typer Application

::: echomine.cli.app
    options:
      show_source: true
      heading_level: 4

### Command Handlers

Command handlers in `echomine/cli/commands/`:

- `list.py`: List command handler
- `search.py`: Search command handler
- `export.py`: Export command handler

### Formatters

Terminal formatters in `echomine/cli/formatters.py`:

- `format_conversation_list()`: Format list output
- `format_search_results()`: Format search output
- `format_conversation_export()`: Format export output

## Design Patterns

### Library-First Pattern

```python
# CLI command handler (thin wrapper)
def list_command(file_path: Path, limit: Optional[int] = None, json: bool = False):
    # Delegate to library
    adapter = OpenAIAdapter()
    conversations = adapter.stream_conversations(file_path)

    if limit:
        conversations = itertools.islice(conversations, limit)

    # Format output
    if json:
        print_json(conversations)  # JSON formatter
    else:
        print_table(conversations)  # Rich formatter
```

### Stdout/Stderr Contract

```python
import sys

# Results to stdout
print(json.dumps(results))  # stdout

# Progress to stderr
print("Processing...", file=sys.stderr)  # stderr

# Errors to stderr
print(f"Error: {error}", file=sys.stderr)  # stderr
sys.exit(1)  # Exit code 1
```

### Progress Reporting

```python
from rich.progress import track

def list_command(file_path: Path):
    adapter = OpenAIAdapter()

    # Show progress bar (stderr)
    conversations = list(adapter.stream_conversations(file_path))

    for conv in track(conversations, description="Listing..."):
        # Process
        pass
```

## Testing CLI

### Contract Tests

CLI contract tests verify stdout/stderr behavior:

```python
def test_list_command_json_output(tmp_export_file):
    """List command outputs valid JSON to stdout."""
    result = subprocess.run(
        ["echomine", "list", str(tmp_export_file), "--json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)  # Validates JSON
    assert "conversations" in data
```

### Exit Code Tests

```python
def test_list_command_file_not_found():
    """List command exits with code 1 on file not found."""
    result = subprocess.run(
        ["echomine", "list", "nonexistent.json"],
        capture_output=True
    )

    assert result.returncode == 1
    assert "not found" in result.stderr.lower()
```

## Related

- **[CLI Usage Guide](../../cli-usage.md)**: Complete CLI reference
- **[OpenAI Adapter](../adapters/openai.md)**: Library backend
- **[Library Usage](../../library-usage.md)**: Programmatic usage

## See Also

- [Architecture](../../architecture.md#cli-interface-contract)
- [Contributing](../../contributing.md)
