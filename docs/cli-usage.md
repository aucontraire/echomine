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

Content Matching (v1.1.0+):
- `--keywords, -k TEXT`: Keywords to search for (can specify multiple, OR logic by default)
- `--phrase TEXT`: Exact phrase to match (can specify multiple, preserves hyphens/special chars)
- `--match-mode TEXT`: Keyword matching mode: 'any' (OR, default) or 'all' (AND)
- `--exclude TEXT`: Keywords to exclude from results (can specify multiple, OR logic)
- `--role TEXT`: Filter to messages from specific role: 'user', 'assistant', or 'system'

Legacy Filters:
- `--title, -t TEXT`: Filter by conversation title (partial match, case-insensitive)
- `--from-date DATE`: Filter conversations created on or after date (YYYY-MM-DD)
- `--to-date DATE`: Filter conversations created on or before date (YYYY-MM-DD)

Output Control:
- `--limit, -n INTEGER`: Maximum number of results to return (default: 10)
- `--format, -f TEXT`: Output format ('text' or 'json')
- `--quiet, -q`: Suppress progress indicators
- `--json`: Output as JSON (alias for --format json)
- `--help`: Show help message

#### How Search Filters Combine

Search filters follow a two-stage matching process:

**Stage 1: Content Matching (OR relationship)**

Conversations are included if ANY of these match:
- **Phrases**: ANY phrase is found (exact match, case-insensitive)
- **Keywords**: Keywords match according to `--match-mode`
  - `--match-mode any` (default): ANY keyword matches
  - `--match-mode all`: ALL keywords must be present

Phrases and keywords are alternatives: `--phrase "api" -k "python"` matches conversations containing EITHER "api" phrase OR "python" keyword.

**Stage 2: Post-Match Filters (AND relationship)**

After content matching, results are filtered by ALL of these conditions:
- `--exclude`: Removes results containing ANY excluded term
- `--role`: Only includes messages from the specified role
- `--title`: Only includes conversations with matching title
- `--from-date` / `--to-date`: Only includes conversations in date range

**Example Scenarios:**

```bash
# Matches if "api" phrase found OR "python" keyword found
echomine search export.json --phrase "api" -k "python"

# Matches if "python" AND "async" keywords both present
echomine search export.json -k "python" -k "async" --match-mode all

# Matches if ("api" phrase OR "python" keyword) AND NOT contains "java"
echomine search export.json --phrase "api" -k "python" --exclude "java"

# Matches if "python" keyword found in user messages only
echomine search export.json -k "python" --role user

# Matches if ("tutorial" phrase OR "python" keyword) AND title contains "Guide"
echomine search export.json --phrase "tutorial" -k "python" --title "Guide"
```

**Examples:**

```bash
# Basic keyword search
echomine search export.json --keywords "algorithm,design"

# Search with limit
echomine search export.json --keywords "python" --limit 5

# NEW v1.1.0: Exact phrase matching
echomine search export.json --phrase "algo-insights"
echomine search export.json --phrase "data pipeline" --phrase "api design"  # Multiple phrases (OR)

# NEW v1.1.0: Boolean match mode (require ALL keywords)
echomine search export.json -k "python" -k "async" --match-mode all
echomine search export.json -k "python" -k "async" --match-mode any  # Default: OR logic

# NEW v1.1.0: Exclude keywords
echomine search export.json -k "python" --exclude "django"
echomine search export.json -k "python" --exclude "django" --exclude "flask"  # Multiple exclusions

# NEW v1.1.0: Role filtering
echomine search export.json -k "refactor" --role user       # Your questions
echomine search export.json -k "recommend" --role assistant # AI responses
echomine search export.json -k "system" --role system       # System messages

# NEW v1.1.0: Combined advanced search
echomine search export.json \
  --phrase "algo-insights" \
  -k "python" \
  --exclude "test" \
  --role user \
  --match-mode all \
  --limit 5

# Search by title (fast, metadata-only)
echomine search export.json --title "Project"

# Filter by date range
echomine search export.json --from-date "2024-01-01" --to-date "2024-03-31"

# Combine all filters
echomine search export.json \
  --phrase "api design" \
  --keywords "python,async" \
  --exclude "test" \
  --role user \
  --title "Tutorial" \
  --from-date "2024-01-01" \
  --match-mode all \
  --limit 10

# JSON output for processing (includes snippets in v1.1.0+)
echomine search export.json --keywords "machine learning" --json | \
  jq '.results[] | select(.score > 0.8) | {title: .conversation.title, snippet: .snippet}'
```

**Output (Human-Readable):**

```
Search Results

Score  ID         Title                         Created     Snippet                                          Messages
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
0.92   abc-123    Python Async Best Practices   2024-01-15  How do I use async/await with Python...          42
0.85   xyz-789    Algorithm Design Patterns     2024-01-14  I need to refactor my algorithm using... (+2)    28

Showing 2 of 5 results
```

Note: v1.1.0+ automatically includes message snippets (~100 characters) with match preview. The "(+N)" indicator shows when multiple messages matched.

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
      "score": 0.92,
      "matched_message_ids": ["msg-001", "msg-015"],
      "snippet": "How do I use async/await with Python..."
    }
  ],
  "total": 5,
  "query": {
    "keywords": ["algorithm", "design"],
    "phrases": null,
    "match_mode": "any",
    "exclude_keywords": null,
    "role_filter": null,
    "limit": 10
  }
}
```

Note: v1.1.0+ adds `matched_message_ids` (list of matching message IDs) and `snippet` (preview text) to each result.

---

### Advanced Search Features (v1.1.0+)

Version 1.1.0 introduces five powerful search enhancements:

#### 1. Exact Phrase Matching

Search for exact multi-word phrases while preserving special characters like hyphens and underscores.

**Use Cases:**
- Find project-specific terminology: `"algo-insights"`, `"data-pipeline"`
- Match code patterns: `"async/await"`, `"error-handling"`
- Locate specific concepts: `"machine learning"`, `"database migration"`

**Examples:**
```bash
# Find exact phrase (hyphen preserved)
echomine search export.json --phrase "algo-insights"

# Multiple phrases (OR logic - matches any)
echomine search export.json --phrase "api design" --phrase "system architecture"

# Combine with keywords
echomine search export.json --phrase "algo-insights" -k "optimization"
```

#### 2. Boolean Match Mode

Control whether keywords use AND logic (all required) or OR logic (any match).

**Use Cases:**
- Narrow results: Require ALL keywords present (`--match-mode all`)
- Broad discovery: Match ANY keyword (`--match-mode any`, default)
- Topic intersection: Find conversations covering multiple topics

**Examples:**
```bash
# Require ALL keywords (AND logic)
echomine search export.json -k "python" -k "async" -k "testing" --match-mode all

# Default: ANY keyword matches (OR logic)
echomine search export.json -k "python" -k "javascript" --match-mode any
```

**Important:** `--match-mode` only affects keywords. Phrases always use OR logic.

#### 3. Exclude Keywords

Filter out unwanted results containing specific terms.

**Use Cases:**
- Remove noise: Exclude "test", "example", "tutorial"
- Filter frameworks: Exclude "django" when searching Python
- Avoid topics: Exclude "deprecated", "legacy"

**Examples:**
```bash
# Exclude single term
echomine search export.json -k "python" --exclude "django"

# Exclude multiple terms (OR logic - excludes if ANY present)
echomine search export.json -k "python" --exclude "django" --exclude "flask" --exclude "pyramid"

# Combine with other filters
echomine search export.json -k "refactor" --exclude "test" --role user
```

**Important:** Excluded terms use OR logic - a result is removed if it contains ANY excluded term.

#### 4. Role Filtering

Search only messages from a specific author role.

**Use Cases:**
- Find your questions: `--role user`
- Find AI recommendations: `--role assistant`
- Find system prompts: `--role system`

**Examples:**
```bash
# Search only your messages
echomine search export.json -k "how do I" --role user

# Search only AI responses
echomine search export.json -k "recommend" --role assistant

# Search system messages
echomine search export.json -k "context" --role system
```

**Note:** Role filtering is case-insensitive (`user`, `User`, `USER` all work).

#### 5. Message Snippets (Automatic)

All search results automatically include ~100 character previews of matched content.

**Features:**
- Shows first matching message content
- Truncated with "..." for long messages
- Multiple matches indicated with "+N more"
- Fallback text for empty/malformed content

**Example Output:**
```
Score  Title                    Snippet
0.92   Python Async Tutorial    How do I use async/await with Python...
0.85   Refactoring Guide        I need to refactor my algorithm... (+2 more)
```

**JSON Output:**
```json
{
  "snippet": "How do I use async/await with Python...",
  "matched_message_ids": ["msg-001", "msg-015", "msg-023"]
}
```

#### Combining Advanced Features

All features work together for powerful precision searches:

```bash
# Find conversations where:
# - You asked about refactoring (role=user)
# - Mentioning "algo-insights" exactly (phrase)
# - Discussing Python (keyword)
# - NOT about testing (exclude)
# - All conditions must match (match-mode=all)
echomine search export.json \
  --phrase "algo-insights" \
  -k "python" \
  --exclude "test" \
  --role user \
  --match-mode all \
  --limit 10
```

#### Filter Combination Logic

**Stage 1: Content Matching (OR relationship)**
- Phrases: Match if ANY phrase is found (exact, case-insensitive)
- Keywords: Match according to `--match-mode` (any OR all)
- Phrase OR keyword match (not both required)

**Stage 2: Post-Match Filters (AND relationship)**
- `--exclude`: Remove if ANY excluded term found
- `--role`: Only messages from specified role
- `--title`: Only conversations with matching title
- `--from-date` / `--to-date`: Only in date range

All post-match filters must be satisfied.

---

### stats

Generate comprehensive statistics for your conversation export.

**Usage:**

```bash
echomine stats [OPTIONS] FILE_PATH
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)

**Options:**

- `--json`: Output as JSON (for programmatic use)
- `--help`: Show help message

**Examples:**

```bash
# View export statistics (human-readable)
echomine stats export.json

# JSON output for scripting
echomine stats export.json --json | jq '.total_conversations'

# Analyze message distribution
echomine stats export.json --json | jq '.average_messages'
```

**Output (Human-Readable):**

```
Export Statistics
═══════════════════════════════════════════════

Total Conversations:  1,234
Total Messages:       45,678
Date Range:           2024-01-01 to 2024-12-07
Average Messages:     37.0 per conversation

Largest Conversation:
  Title:     "Deep Python Discussion"
  ID:        abc-123
  Messages:  245

Smallest Conversation:
  Title:     "Quick Question"
  ID:        xyz-789
  Messages:  2
```

**Output (JSON):**

```json
{
  "total_conversations": 1234,
  "total_messages": 45678,
  "date_range": {
    "earliest": "2024-01-01T10:00:00Z",
    "latest": "2024-12-07T15:30:00Z"
  },
  "average_messages": 37.0,
  "largest_conversation": {
    "id": "abc-123",
    "title": "Deep Python Discussion",
    "message_count": 245
  },
  "smallest_conversation": {
    "id": "xyz-789",
    "title": "Quick Question",
    "message_count": 2
  }
}
```

---

### get

Retrieve and display a specific conversation by ID with Rich terminal formatting.

**Usage:**

```bash
echomine get [OPTIONS] FILE_PATH CONVERSATION_ID
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)
- `CONVERSATION_ID`: Conversation ID to retrieve (required)

**Options:**

- `--display TEXT`: Display mode: `full` (default, shows all messages), `summary` (metadata only), or `messages-only`
- `--json`: Output as JSON (for programmatic use)
- `--help`: Show help message

**Examples:**

```bash
# Get conversation with full display (default)
echomine get export.json conv-abc123

# Show summary only (metadata, no messages)
echomine get export.json conv-abc123 --display summary

# Show messages only (no metadata header)
echomine get export.json conv-abc123 --display messages-only

# Get conversation as JSON
echomine get export.json conv-abc123 --json

# Pipe JSON to jq for processing
echomine get export.json conv-abc123 --json | \
  jq '.messages[] | select(.role == "user") | .content'
```

**Output (Full Display - Default):**

```
Conversation: Python AsyncIO Tutorial
═══════════════════════════════════════════════

ID:          conv-abc123
Created:     2023-11-14 22:13:20 UTC
Updated:     2023-11-14 22:30:00 UTC
Messages:    2

Messages:
───────────────────────────────────────────────

User (2023-11-14 22:13:20 UTC)
Explain Python asyncio

Assistant (2023-11-14 22:13:45 UTC)
Python asyncio is a library to write concurrent code...
```

**Output (Summary Display):**

```
Conversation: Python AsyncIO Tutorial
═══════════════════════════════════════════════

ID:          conv-abc123
Created:     2023-11-14 22:13:20 UTC
Updated:     2023-11-14 22:30:00 UTC
Messages:    2

Role Breakdown:
  user:      1 message
  assistant: 1 message
```

**Output (JSON):**

```json
{
  "id": "conv-abc123",
  "title": "Python AsyncIO Tutorial",
  "created_at": "2023-11-14T22:13:20Z",
  "updated_at": "2023-11-14T22:30:00Z",
  "message_count": 2,
  "messages": [
    {
      "id": "msg-001-1",
      "role": "user",
      "content": "Explain Python asyncio",
      "timestamp": "2023-11-14T22:13:20Z",
      "parent_id": null
    }
  ]
}
```

---

### export

Export a specific conversation to markdown, JSON, or CSV format.

**Usage:**

```bash
echomine export [OPTIONS] FILE_PATH CONVERSATION_ID
```

**Arguments:**

- `FILE_PATH`: Path to OpenAI export JSON file (required)
- `CONVERSATION_ID`: ID of conversation to export (required)

**Options:**

- `--output PATH`: Output file path (if not specified, prints to stdout)
- `--format TEXT`: Export format: `markdown` (default), `json`, or `csv`
- `--fields TEXT`: CSV only - comma-separated field names (default: all fields)
- `--no-metadata`: Markdown only - exclude YAML frontmatter (v1.1.0 compatibility)
- `--help`: Show help message

**Examples:**

```bash
# Export to stdout (markdown with YAML frontmatter, default in v1.2.0)
echomine export export.json conv-abc123

# Export to markdown file
echomine export export.json conv-abc123 --output algorithm.md

# Export without YAML frontmatter (v1.1.0 style)
echomine export export.json conv-abc123 --output algo.md --no-metadata

# Export as JSON to file
echomine export export.json conv-abc123 --format json --output algo.json

# Export as CSV (v1.2.0+)
echomine export export.json conv-abc123 --format csv --output algo.csv

# CSV with specific fields only
echomine export export.json conv-abc123 --format csv \
  --fields "id,role,content,timestamp" --output messages.csv

# Export JSON to stdout for piping
echomine export export.json conv-abc123 -f json | jq '.messages | length'

# Count user messages in a conversation
echomine export export.json conv-abc123 -f json | jq '[.messages[] | select(.role == "user")] | length'

# Pipe markdown to file
echomine export export.json conv-abc123 > conversation.md

# Export multiple conversations with bash loop
for id in conv-abc123 conv-xyz789; do
  echomine export export.json "$id" --output "${id}.md"
done
```

**Output (Markdown with YAML Frontmatter - v1.2.0 Default):**

```markdown
---
id: conv-abc123
title: Python Async Best Practices
created_at: 2024-01-15T10:30:00+00:00
updated_at: 2024-01-15T12:45:00+00:00
message_count: 42
export_date: 2024-12-07T15:30:00+00:00
exported_by: echomine
---

# Python Async Best Practices

## User (`msg-001`) - 2024-01-15 10:30:15 UTC

How do I properly use async/await in Python?

## Assistant (`msg-002`) - 2024-01-15 10:30:45 UTC

Here's a comprehensive guide to async/await in Python...
```

**Output (Markdown without Metadata - v1.1.0 Style):**

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

**Output (CSV - v1.2.0+):**

```csv
id,role,content,timestamp,parent_id
msg-001,user,"How do I properly use async/await in Python?",2024-01-15T10:30:15Z,
msg-002,assistant,"Here's a comprehensive guide to async/await in Python...",2024-01-15T10:30:45Z,msg-001
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
