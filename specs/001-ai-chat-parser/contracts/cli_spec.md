# CLI Interface Contract

**Feature**: Echomine AI Chat Parser
**Date**: 2025-11-21
**Contract Version**: 1.0.0

## Overview

This document specifies the command-line interface contract per Constitution Principle II (CLI Interface Contract). All commands MUST follow these conventions.

## General Conventions

### Input/Output Protocol
- **Input**: Command-line arguments (file paths, flags)
- **Output**: Results to stdout (human-readable by default, JSON with --json flag)
- **Errors**: Error messages to stderr
- **Exit Codes**: 0 for success, non-zero for failure

### Common Flags
- `--json`: Output JSON format instead of human-readable
- `--help`: Display command usage and examples
- `--version`: Display echomine version

### Error Handling (per FR-033)
- File not found → stderr message, exit code 1
- Permission denied → stderr message, exit code 1
- Invalid arguments → stderr message with usage hint, exit code 1
- Disk full during export → stderr message, exit code 1

---

## Commands

### `echomine search`

Search conversations by keywords, title, or date range.

#### Synopsis
```bash
echomine search <file> [OPTIONS]
```

#### Arguments
- `file`: Path to export file (required, positional)

#### Options
- `--keywords TEXT`: Comma-separated keywords for full-text search (OR logic)
- `--title TEXT`: Filter by conversation title (partial match, case-insensitive)
- `--from DATE`: Start date for range filter (ISO 8601: YYYY-MM-DD)
- `--to DATE`: End date for range filter (ISO 8601: YYYY-MM-DD)
- `--limit INTEGER`: Maximum results to return (default: 10, max: 1000)
- `--json`: Output results as JSON array

#### Output Format (Human-Readable)
```
Found 3 conversations matching "algorithm":

[1] Algo Insights Project (2024-03-15)
    Relevance: 0.85
    Excerpt: "We discussed several algorithm design patterns including..."

[2] LeetCode Solutions (2024-02-10)
    Relevance: 0.72
    Excerpt: "Dynamic programming is a key algorithm technique for..."

[3] Data Structures Review (2024-01-05)
    Relevance: 0.58
    Excerpt: "Binary search trees are efficient algorithms for..."
```

#### Output Format (JSON)
```json
{
  "query": {
    "keywords": ["algorithm"],
    "title_filter": null,
    "from_date": null,
    "to_date": null,
    "limit": 10
  },
  "results": [
    {
      "conversation_id": "conv-uuid-1",
      "title": "Algo Insights Project",
      "created_at": "2024-03-15T10:30:00Z",
      "relevance_score": 0.85,
      "excerpt": "We discussed several algorithm design patterns including...",
      "matched_keywords": ["algorithm"]
    },
    {
      "conversation_id": "conv-uuid-2",
      "title": "LeetCode Solutions",
      "created_at": "2024-02-10T14:20:00Z",
      "relevance_score": 0.72,
      "excerpt": "Dynamic programming is a key algorithm technique for...",
      "matched_keywords": ["algorithm"]
    }
  ],
  "total_results": 2
}
```

#### Examples
```bash
# Search by keywords
echomine search conversations.json --keywords "algorithm,leetcode"

# Search by title only (fast, metadata-only)
echomine search conversations.json --title "Project"

# Combined filters
echomine search conversations.json --title "Project" --keywords "refactor" --limit 5

# Date range filter
echomine search conversations.json --from "2024-01-01" --to "2024-03-31"

# JSON output for piping
echomine search conversations.json --keywords "algorithm" --json | jq '.results[0].title'
```

#### Exit Codes
- `0`: Search completed successfully (even if 0 results)
- `1`: File not found, permission denied, or invalid arguments
- `2`: Invalid date format or other validation error

#### Progress Indicators
- For files >100MB: Display progress bar with rich (per FR-021)
- For operations >2 seconds: Show "Searching..." indicator

---

### `echomine export`

Export conversation to markdown or JSON format.

#### Synopsis
```bash
echomine export <file> [OPTIONS]
```

#### Arguments
- `file`: Path to export file (required, positional)

#### Options
- `--id UUID`: Export conversation by ID (mutually exclusive with --title)
- `--title TEXT`: Export conversation by title (partial match, mutually exclusive with --id)
- `--format FORMAT`: Output format: `markdown` (default) or `json`
- `--output PATH`: Output file path (default: current directory with auto-generated filename)

#### Output File Naming
**Default behavior** (no --output flag):
- Markdown: `conversation-{slugified-title}.md`
- JSON: `conversation-{slugified-title}.json`

**Custom output** (with --output flag):
- Use exact path provided by user

**Slugification rules**:
- Lowercase, replace spaces with hyphens, remove special chars
- Example: "Algo Insights Project" → "algo-insights-project"

#### Output Format (Markdown)
```markdown
# Algo Insights Project

**Created**: 2024-03-15T10:30:00Z
**Last Updated**: 2024-03-20T16:45:00Z
**Participants**: User, Assistant

---

## Message 1 (User, 2024-03-15T10:30:00Z)

Can you explain common algorithm design patterns?

## Message 2 (Assistant, 2024-03-15T10:31:15Z)

Sure! Here are key algorithm design patterns:

1. **Divide and Conquer**: Split problem into subproblems
2. **Dynamic Programming**: Solve overlapping subproblems once
3. **Greedy Algorithms**: Make locally optimal choices

### Message 2.1 (User, 2024-03-15T10:32:00Z)

Can you give an example of dynamic programming?

### Message 2.1.1 (Assistant, 2024-03-15T10:33:00Z)

Classic example: Fibonacci sequence...
```

**Threading notation**:
- Root messages: `## Message N`
- Replies: `### Message N.M` (one level deeper)
- Nested replies: `#### Message N.M.K` (two levels deeper)

#### Output Format (JSON)
```json
{
  "id": "conv-uuid-1",
  "title": "Algo Insights Project",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-20T16:45:00Z",
  "messages": [
    {
      "id": "msg-uuid-1",
      "content": "Can you explain common algorithm design patterns?",
      "role": "user",
      "timestamp": "2024-03-15T10:30:00Z",
      "parent_id": null,
      "child_ids": ["msg-uuid-2"]
    },
    {
      "id": "msg-uuid-2",
      "content": "Sure! Here are key algorithm design patterns:\n\n1. **Divide and Conquer**...",
      "role": "assistant",
      "timestamp": "2024-03-15T10:31:15Z",
      "parent_id": "msg-uuid-1",
      "child_ids": ["msg-uuid-3"]
    }
  ]
}
```

#### Examples
```bash
# Export by title (markdown, default format)
echomine export conversations.json --title "Algo Insights Project"

# Export by ID (JSON format)
echomine export conversations.json --id "conv-uuid-123" --format json

# Export to specific path
echomine export conversations.json --title "Project" --output /path/to/output.md
```

#### Exit Codes
- `0`: Export completed successfully
- `1`: File not found, permission denied, invalid arguments
- `2`: Conversation not found (ID or title doesn't match)
- `3`: Disk full during export (fail fast per FR-033)

#### Error Messages (stderr)
```
Error: File not found: conversations.json
Error: No conversation found matching title "NonexistentTitle"
Error: Disk full: cannot write to output.md
Error: Permission denied: cannot write to /protected/path.md
```

---

## Unix Pipeline Integration

### Composability Examples

```bash
# Search and count results
echomine search conversations.json --keywords "algorithm" --json | jq '.results | length'

# Export multiple conversations
echomine search conversations.json --keywords "project" --json \
  | jq -r '.results[].conversation_id' \
  | xargs -I {} echomine export conversations.json --id {} --format markdown

# Filter by date and export
echomine search conversations.json --from "2024-01-01" --to "2024-03-31" --json \
  | jq -r '.results[0].conversation_id' \
  | xargs echomine export conversations.json --id

# Grep through exported markdown
echomine export conversations.json --title "Algorithm" --output /tmp/algo.md \
  && grep -i "dynamic programming" /tmp/algo.md
```

---

## Contract Tests

All CLI commands MUST pass these contract tests (see `tests/contract/test_cli_contract.py`):

1. **test_stdout_for_success**: Successful output goes to stdout
2. **test_stderr_for_errors**: Error messages go to stderr
3. **test_nonzero_exit_on_failure**: Exit code 1 on file not found
4. **test_json_output_parseable**: --json flag produces valid JSON
5. **test_help_flag_works**: --help displays usage and exits 0
6. **test_progress_indicator_for_large_files**: Progress bar shown for files >100MB

---

## Version Compatibility

CLI interface follows semantic versioning:
- **MAJOR**: Breaking changes to command syntax or output format
- **MINOR**: New commands or optional flags
- **PATCH**: Bug fixes, no interface changes

Current version: 1.0.0 (initial release)
