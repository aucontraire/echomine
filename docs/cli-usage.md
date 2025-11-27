# CLI Usage Guide

Complete reference for using Echomine from the command line.

## Installation

```bash
pip install echomine
```

Verify installation:

```bash
echomine --version
```

## Global Options

Available for all commands:

```bash
echomine [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version and exit
  --help     Show help message and exit
```

## Commands

### list

List all conversations in an export file.

**Usage:**

```bash
echomine list [OPTIONS] FILE_PATH
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)

**Options:**

- `--limit INTEGER`: Maximum number of conversations to list
- `--json`: Output as JSON (for programmatic use)
- `--help`: Show help message

**Examples:**

```bash
# List all conversations (human-readable)
echomine list conversations.json

# List with limit
echomine list conversations.json --limit 10

# JSON output for piping
echomine list conversations.json --json | jq '.conversations[].title'

# Count conversations
echomine list conversations.json --json | jq '.conversations | length'
```

**Output (Human-Readable):**

```
Conversations in conversations.json

[2024-01-15] Python Async Best Practices
  Messages: 42
  ID: conv-abc123

[2024-01-14] Algorithm Design Patterns
  Messages: 28
  ID: conv-xyz789

...

Total: 145 conversations
```

**Output (JSON):**

```json
{
  "conversations": [
    {
      "id": "conv-abc123",
      "title": "Python Async Best Practices",
      "created_at": "2024-01-15T10:30:00Z",
      "message_count": 42
    }
  ],
  "total": 145
}
```

---

### search

Search conversations with keyword matching and relevance ranking.

**Usage:**

```bash
echomine search [OPTIONS] FILE_PATH
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)

**Options:**

- `--keywords TEXT`: Comma-separated keywords to search for
- `--title TEXT`: Filter by conversation title (partial match, case-insensitive)
- `--from-date DATE`: Filter conversations created on or after date (YYYY-MM-DD)
- `--to-date DATE`: Filter conversations created on or before date (YYYY-MM-DD)
- `--limit INTEGER`: Maximum number of results to return (default: 10)
- `--json`: Output as JSON
- `--help`: Show help message

**Examples:**

```bash
# Search by keywords
echomine search export.json --keywords "algorithm,design"

# Search with limit
echomine search export.json --keywords "python" --limit 5

# Search by title (fast, metadata-only)
echomine search export.json --title "Project"

# Filter by date range
echomine search export.json --from-date "2024-01-01" --to-date "2024-03-31"

# Combine filters
echomine search export.json \
  --keywords "python,async" \
  --title "Tutorial" \
  --from-date "2024-01-01" \
  --limit 10

# JSON output for processing
echomine search export.json --keywords "machine learning" --json | \
  jq '.results[] | select(.score > 0.8)'
```

**Output (Human-Readable):**

```
Search Results

[0.92] Python Async Best Practices
  Created: 2024-01-15
  Messages: 42
  ID: conv-abc123

[0.85] Algorithm Design Patterns
  Created: 2024-01-14
  Messages: 28
  ID: conv-xyz789

...

Found 5 conversations (showing top 5)
```

**Output (JSON):**

```json
{
  "results": [
    {
      "conversation": {
        "id": "conv-abc123",
        "title": "Python Async Best Practices",
        "created_at": "2024-01-15T10:30:00Z",
        "message_count": 42
      },
      "score": 0.92
    }
  ],
  "total": 5,
  "query": {
    "keywords": ["algorithm", "design"],
    "limit": 10
  }
}
```

---

### export

Export a specific conversation to markdown format.

**Usage:**

```bash
echomine export [OPTIONS] FILE_PATH CONVERSATION_ID
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)
- `CONVERSATION_ID`: ID of conversation to export (required)

**Options:**

- `--output PATH`: Output file path (if not specified, prints to stdout)
- `--json`: Output conversation as JSON instead of markdown
- `--help`: Show help message

**Examples:**

```bash
# Export to stdout (markdown)
echomine export export.json conv-abc123

# Export to file
echomine export export.json conv-abc123 --output algorithm.md

# Export as JSON
echomine export export.json conv-abc123 --json

# Pipe to file
echomine export export.json conv-abc123 > conversation.md

# Export multiple conversations with bash loop
for id in conv-abc123 conv-xyz789; do
  echomine export export.json "$id" --output "${id}.md"
done
```

**Output (Markdown):**

```markdown
# Python Async Best Practices

**Created:** 2024-01-15 10:30:00 UTC
**Messages:** 42

---

## Message 1

**User** - 2024-01-15 10:30:15 UTC

How do I properly use async/await in Python?

---

## Message 2

**Assistant** - 2024-01-15 10:30:45 UTC

Here's a comprehensive guide to async/await in Python...

---

...
```

**Output (JSON):**

```json
{
  "id": "conv-abc123",
  "title": "Python Async Best Practices",
  "created_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "How do I properly use async/await in Python?",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ]
}
```

---

## Output Formats

### Human-Readable Output

Default format with rich terminal formatting:

- Progress indicators
- Color-coded output
- Tables for structured data
- Formatted timestamps

### JSON Output

All commands support `--json` flag for machine-readable output:

- Structured JSON on stdout
- Progress and errors to stderr
- Exit codes: 0 (success), 1 (error), 2 (usage error)

## Exit Codes

Echomine follows standard UNIX exit code conventions:

- **0**: Success
- **1**: Operational error (file not found, parsing error, etc.)
- **2**: Usage error (invalid arguments, missing required options)

**Examples:**

```bash
# Success (exit code 0)
echomine list export.json && echo "Success"

# File not found (exit code 1)
echomine list nonexistent.json || echo "Error: $?"

# Invalid arguments (exit code 2)
echomine search --invalid-option || echo "Usage error: $?"
```

## Pipeline Integration

Echomine is designed for UNIX pipeline composition:

### With jq

```bash
# Extract conversation titles
echomine list export.json --json | jq '.conversations[].title'

# Filter by message count
echomine list export.json --json | \
  jq '.conversations[] | select(.message_count > 20)'

# Get conversation IDs
echomine search export.json --keywords "python" --json | \
  jq -r '.results[].conversation.id'
```

### With grep

```bash
# Search titles
echomine list export.json | grep -i "python"

# Filter results
echomine search export.json --keywords "algorithm" | grep "Messages:"
```

### With awk

```bash
# Extract specific fields
echomine list export.json | awk '/Messages:/ {print $2}'
```

### Batch Processing

```bash
# Export all search results
echomine search export.json --keywords "python" --json | \
  jq -r '.results[].conversation.id' | \
  while read -r id; do
    echomine export export.json "$id" --output "${id}.md"
  done

# Count conversations by date
echomine list export.json --json | \
  jq -r '.conversations[].created_at' | \
  cut -d'T' -f1 | \
  sort | uniq -c
```

## Progress and Error Reporting

### Progress Indicators

Long-running operations show progress to stderr:

```bash
echomine search large_export.json --keywords "python"
# stderr: Processing conversations... 1000/10000 (10%)
# stdout: [results]
```

### Error Messages

Errors are printed to stderr with context:

```bash
echomine list nonexistent.json
# stderr: Error: File not found: nonexistent.json
# exit code: 1
```

### Graceful Degradation

Malformed entries are skipped with warnings:

```bash
echomine list export.json
# stderr: Warning: Skipped malformed conversation: conv-broken-123 (invalid timestamp)
# stdout: [remaining valid conversations]
```

## Environment Variables

None currently. All configuration is via command-line flags.

## Configuration Files

None currently. All options are passed as command-line arguments.

## Tips and Tricks

### 1. Save Search Results

```bash
# Save high-relevance results
echomine search export.json --keywords "machine learning" --json > ml_convs.json
```

### 2. Quick Title Search

```bash
# Faster than full-text search
echomine search export.json --title "Project Alpha"
```

### 3. Date Range Filtering

```bash
# Q1 2024 conversations
echomine search export.json \
  --from-date "2024-01-01" \
  --to-date "2024-03-31" \
  --json > q1_2024.json
```

### 4. Batch Export with Filtering

```bash
# Export all Python-related conversations
echomine search export.json --keywords "python" --limit 100 --json | \
  jq -r '.results[].conversation.id' | \
  while read id; do
    echomine export export.json "$id" --output "exports/${id}.md"
  done
```

### 5. Statistics

```bash
# Count conversations
echomine list export.json --json | jq '.total'

# Average messages per conversation
echomine list export.json --json | \
  jq '[.conversations[].message_count] | add / length'
```

## Troubleshooting

### Command Not Found

```bash
# Ensure installed
pip install echomine

# Check PATH
which echomine
```

### File Not Found

```bash
# Use absolute path
echomine list /path/to/export.json

# Or check file exists
ls -la export.json
```

### No Results

```bash
# Check if file has conversations
echomine list export.json --json | jq '.total'

# Try broader keywords
echomine search export.json --keywords "python"
```

### Invalid JSON

```bash
# Validate JSON file
jq empty export.json

# Check for corruption
echomine list export.json  # Will report parsing errors
```

## Next Steps

- [Library Usage](library-usage.md): Use Echomine programmatically
- [API Reference](api/index.md): Detailed API documentation
- [Architecture](architecture.md): Design principles
- [Contributing](contributing.md): Development guidelines
