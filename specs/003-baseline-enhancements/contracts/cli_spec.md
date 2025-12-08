# CLI Contract: Baseline Enhancement Package v1.2.0

**Feature**: 003-baseline-enhancements
**Date**: 2025-12-05
**Status**: Complete

## Command Reference

### 1. Search Command Enhancements

**Command**: `echomine search <export.json> [OPTIONS]`

#### New Options (v1.2.0)

| Option | Type | Default | Description | FR |
|--------|------|---------|-------------|-----|
| `--min-messages` | int | None | Filter: minimum message count | FR-001 |
| `--max-messages` | int | None | Filter: maximum message count | FR-002 |
| `--sort` | choice | "score" | Sort by: score, date, title, messages | FR-043 |
| `--order` | choice | "desc" | Sort direction: asc, desc | FR-044 |
| `--format` | choice | None | Output format: csv | FR-049 |

#### Contract Examples

```bash
# Message count filtering (FR-001, FR-002)
echomine search export.json --keywords "python" --min-messages 10
echomine search export.json --keywords "python" --max-messages 5
echomine search export.json --keywords "python" --min-messages 5 --max-messages 20

# Invalid bounds (FR-008) - exits with code 2
echomine search export.json --min-messages 20 --max-messages 5
# stderr: Error: min_messages (20) must be <= max_messages (5)
# exit code: 2

# Sort options (FR-043, FR-044)
echomine search export.json -k "python" --sort date --order desc
echomine search export.json -k "python" --sort title --order asc
echomine search export.json -k "python" --sort messages --order asc

# CSV output (FR-049)
echomine search export.json -k "python" --format csv
# stdout: conversation_id,title,created_at,updated_at,message_count,score
#         abc-123,"Chat about Python",2024-01-15T10:30:00Z,2024-01-15T11:45:00Z,15,0.875
```

#### Exit Codes

| Code | Condition | Example |
|------|-----------|---------|
| 0 | Success (including empty results) | Search completed |
| 1 | Operational error | File not found |
| 2 | Usage error | Invalid --min-messages > --max-messages |

---

### 2. Stats Command (NEW)

**Command**: `echomine stats <export.json> [OPTIONS]`

#### Options

| Option | Type | Default | Description | FR |
|--------|------|---------|-------------|-----|
| `--json` | flag | False | Output as JSON | FR-012 |
| `--conversation` | string | None | Show stats for specific conversation ID | FR-018 |

#### Contract Examples

```bash
# Export-level statistics (FR-009, FR-010, FR-011)
echomine stats export.json
# stdout:
# Export Statistics
# ─────────────────────────────────────
# Total conversations:  1,234
# Total messages:       45,678
# Date range:           2024-01-01 to 2024-12-05
# Average messages:     37.0
#
# Largest conversation:
#   "Deep Python Discussion" (id: abc-123, 245 messages)
#
# Smallest conversation:
#   "Quick Question" (id: xyz-789, 2 messages)

# JSON output (FR-012)
echomine stats export.json --json
# stdout: {"total_conversations": 1234, "total_messages": 45678, ...}

# Per-conversation statistics (FR-018, FR-019, FR-020, FR-021)
echomine stats export.json --conversation abc-123
# stdout:
# Conversation Statistics: "Deep Python Discussion"
# ─────────────────────────────────────
# ID:                   abc-123
# Created:              2024-01-15 10:30:00 UTC
# Updated:              2024-01-15 14:45:00 UTC
#
# Message Breakdown:
#   user:       82 messages
#   assistant:  155 messages
#   system:     8 messages
#   Total:      245 messages
#
# Temporal Patterns:
#   First message:      2024-01-15 10:30:05 UTC
#   Last message:       2024-01-15 14:44:32 UTC
#   Duration:           4h 14m 27s
#   Average gap:        62.3 seconds

# Per-conversation JSON (FR-024)
echomine stats export.json --conversation abc-123 --json
# stdout: {"conversation_id": "abc-123", "title": "...", ...}

# Invalid conversation ID (FR-018)
echomine stats export.json --conversation invalid-id
# stderr: Error: Conversation not found: invalid-id
# exit code: 1
```

#### Exit Codes

| Code | Condition | Example |
|------|-----------|---------|
| 0 | Success | Stats calculated |
| 1 | Operational error | Conversation not found |
| 2 | Usage error | Missing required argument |

---

### 3. Get Messages Command (NEW)

**Command**: `echomine get messages <export.json> <conversation-id> [OPTIONS]`

#### Options

| Option | Type | Default | Description | FR |
|--------|------|---------|-------------|-----|
| `--json` | flag | False | Output full message objects | FR-027 |

#### Contract Examples

```bash
# List messages (FR-025, FR-026) - chronological order (oldest first)
echomine get messages export.json abc-123
# stdout:
# Messages in "Deep Python Discussion" (245 messages)
# ─────────────────────────────────────
# msg-001  user       2024-01-15 10:30:05  I need help with Python generators...
# msg-002  assistant  2024-01-15 10:30:47  Python generators are a powerful fe...
# msg-003  user       2024-01-15 10:32:15  Can you show me an example with yie...
# ...

# JSON output (FR-027)
echomine get messages export.json abc-123 --json
# stdout: [{"id": "msg-001", "role": "user", "timestamp": "...", "content": "..."}, ...]

# Invalid conversation ID (FR-028)
echomine get messages export.json invalid-id
# stderr: Error: Conversation not found: invalid-id
# exit code: 1
```

#### Exit Codes

| Code | Condition | Example |
|------|-----------|---------|
| 0 | Success | Messages listed |
| 1 | Operational error | Conversation not found |
| 2 | Usage error | Missing conversation ID |

---

### 4. List Command Enhancements

**Command**: `echomine list <export.json> [OPTIONS]`

#### New Options (v1.2.0)

| Option | Type | Default | Description | FR |
|--------|------|---------|-------------|-----|
| `--format` | choice | None | Output format: csv | FR-049 |
| `--sort` | choice | "date" | Sort by: date, title, messages | FR-048a |
| `--order` | choice | varies | Sort direction: asc, desc (default varies by field) | FR-048c |

#### Contract Examples

```bash
# CSV output (FR-049)
echomine list export.json --format csv
# stdout: conversation_id,title,created_at,updated_at,message_count
#         abc-123,"Chat about Python",2024-01-15T10:30:00Z,2024-01-15T11:45:00Z,15

# Sort by date (default, newest first) (FR-048a)
echomine list export.json --sort date
# Results sorted by updated_at (falls back to created_at if NULL) descending

# Sort by title (alphabetical) (FR-048a)
echomine list export.json --sort title --order asc
# Results sorted alphabetically by title (case-insensitive)

# Sort by message count (highest first) (FR-048c)
echomine list export.json --sort messages
# Results sorted by message_count descending
```

**Note**: List command with `--sort` buffers all conversations in memory (breaks O(1) streaming). This is acceptable for explicit user request.

---

### 5. Export Command Enhancements

**Command**: `echomine export <export.json> <conversation-id> [OPTIONS]`

#### New Options (v1.2.0)

| Option | Type | Default | Description | FR |
|--------|------|---------|-------------|-----|
| `--no-metadata` | flag | False | Disable YAML frontmatter | FR-033 |

#### Contract Examples

```bash
# Export with metadata (default, FR-030, FR-031, FR-031b, FR-032)
echomine export export.json abc-123 --output chat.md
# Output file contains:
# ---
# id: abc-123
# title: Deep Python Discussion
# created_at: 2024-01-15T10:30:00Z      # ISO 8601 with Z suffix (FR-031b)
# updated_at: 2024-01-15T14:45:00Z      # ISO 8601 with Z suffix (FR-031b)
# message_count: 245
# export_date: 2025-12-05T15:30:00Z     # ISO 8601 with Z suffix (FR-031b)
# exported_by: echomine
# ---
#
# # Deep Python Discussion
#
# ## User (`msg-001`) - 2024-01-15 10:30:05 UTC
#
# I need help with Python generators...

# Message without source ID (FR-032a)
# If source message lacks ID, generated as: msg-{conversation_id}-{index}
# Example: ## User (`msg-abc123-001`) - 2024-01-15 10:30:05 UTC

# Export without metadata (FR-033)
echomine export export.json abc-123 --output chat.md --no-metadata
# Output file contains (no frontmatter):
# # Deep Python Discussion
#
# ## User - 2024-01-15 10:30:05 UTC
#
# I need help with Python generators...
```

---

## Output Contracts

### Rich CLI Formatting (FR-036-042)

#### Table Format (FR-036)

```
┌──────────────┬────────────────────────────────┬──────────┬────────────────────┬───────┐
│ ID           │ Title                          │ Messages │ Created            │ Score │
├──────────────┼────────────────────────────────┼──────────┼────────────────────┼───────┤
│ abc-123      │ Deep Python Discussion         │ 245      │ 2024-01-15 10:30   │ 0.875 │
│ def-456      │ Quick Question about Lists     │ 8        │ 2024-01-14 09:15   │ 0.654 │
│ ghi-789      │ Debugging Session              │ 42       │ 2024-01-13 14:20   │ 0.421 │
└──────────────┴────────────────────────────────┴──────────┴────────────────────┴───────┘
```

#### Score Colors (FR-037)

| Score Range | Color | Example |
|-------------|-------|---------|
| > 0.7 | Green | `[green]0.875[/green]` |
| 0.4 - 0.7 | Yellow | `[yellow]0.654[/yellow]` |
| < 0.4 | Red | `[red]0.321[/red]` |

#### Role Colors (FR-038)

| Role | Color | Example |
|------|-------|---------|
| user | Green | `[green]user[/green]` |
| assistant | Blue | `[blue]assistant[/blue]` |
| system | Yellow | `[yellow]system[/yellow]` |

#### Progress Bar (FR-039)

```
Analyzing conversations... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05
```

Format: `{operation}... {bar} {percentage}% {elapsed}`

#### TTY Detection (FR-040)

When stdout is not a TTY (piped or redirected):
- Rich formatting disabled
- Plain text output
- No colors or progress bars

```bash
# TTY: Rich table output
echomine list export.json

# Piped: Plain text
echomine list export.json | grep "Python"
```

### CSV Format (FR-049-054)

#### Conversation-Level CSV (FR-050)

```csv
conversation_id,title,created_at,updated_at,message_count,score
abc-123,"Deep Python Discussion",2024-01-15T10:30:00Z,2024-01-15T14:45:00Z,245,0.875
def-456,"Quick Question, with comma",2024-01-14T09:15:00Z,2024-01-14T09:20:00Z,8,0.654
```

#### Message-Level CSV (FR-051, FR-052)

```csv
conversation_id,message_id,role,timestamp,content
abc-123,msg-001,user,2024-01-15T10:30:05Z,"I need help with Python generators..."
abc-123,msg-002,assistant,2024-01-15T10:30:47Z,"Python generators are a powerful feature..."
```

#### Escaping Rules (FR-053, FR-053b)

- Fields containing `,`, `"`, or newlines are quoted
- Quotes inside quoted fields escaped as `""`
- Example: `"He said ""Hello"""`
- **Newlines**: Preserved as literal line breaks inside quoted fields (NOT escaped as `\n`)

```csv
conversation_id,message_id,role,timestamp,content
abc-123,msg-001,user,2024-01-15T10:30:05Z,"Hello,
This message has
multiple lines"
```

#### NULL Value Handling (FR-053a)

- NULL values (e.g., `updated_at` when None) are empty fields (zero-length, no quotes)
- Example: `abc-123,"Chat Title",2024-01-15T10:30:00Z,,15,0.875` (empty updated_at)
- Compatible with pandas `read_csv()` and Excel import

#### Sort Tie-Breaking (FR-043a)

- When primary sort values are equal, secondary sort is by `conversation_id` (ascending, lexicographic)
- Ensures deterministic ordering for reproducible results
- Example: Two conversations with same title sorted by ID

---

## Error Messages

### Validation Errors (Exit Code 2)

```bash
# Invalid message count bounds
echomine search export.json --min-messages 20 --max-messages 5
# stderr: Error: min_messages (20) must be <= max_messages (5)

# Negative message count
echomine search export.json --min-messages -5
# stderr: Error: --min-messages must be >= 1

# Unknown sort field
echomine search export.json --sort invalid
# stderr: Error: Invalid value for '--sort': 'invalid' is not one of 'score', 'date', 'title', 'messages'

# Conflicting output format flags (FR-041a) - last flag wins with WARNING
echomine search export.json -k "python" --format csv --json
# stderr: WARNING: Conflicting output formats: using JSON (last flag wins)
# stdout: [{"id": "abc-123", ...}]
# exit code: 0
```

### Operational Errors (Exit Code 1)

```bash
# File not found
echomine stats missing.json
# stderr: Error: File not found: missing.json

# Conversation not found
echomine stats export.json --conversation invalid-id
# stderr: Error: Conversation not found: invalid-id

# Parse error
echomine stats corrupt.json
# stderr: Error: Failed to parse export: Invalid JSON at line 42

# Permission denied (FR-061)
echomine stats /protected/export.json
# stderr: Error: Permission denied: /protected/export.json. Check file read permissions.
# exit code: 1
```

### Interruption (Exit Code 130)

```bash
# User presses Ctrl+C (FR-062)
echomine search export.json -k "python"
# ^C
# [partial output may be present]
# exit code: 130

# Notes:
# - Exit is immediate (no graceful shutdown delay)
# - Partial output is acceptable for streaming operations
# - File handles are closed automatically via context managers
```

### CSV Flag Conflicts (Exit Code 2)

```bash
# --format csv and --csv-messages are mutually exclusive (FR-051a)
echomine search export.json -k "python" --format csv --csv-messages
# stderr: Error: --format csv and --csv-messages are mutually exclusive. Use --format csv for conversation-level or --csv-messages for message-level export.
# exit code: 2
```
