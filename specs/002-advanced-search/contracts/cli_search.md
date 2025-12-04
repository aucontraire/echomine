# CLI Contract: Search Command Extensions

**Branch**: `002-advanced-search` | **Date**: 2025-12-03
**Purpose**: Define CLI interface contract for new search flags

## Command Signature

```bash
echomine search <EXPORT_FILE> [OPTIONS]
```

## New Options

### `--phrase` (FR-001, FR-002)

| Attribute | Value |
|-----------|-------|
| Flag | `--phrase` |
| Short | None |
| Type | `str` |
| Multiple | Yes (can be specified multiple times) |
| Required | No |
| Default | None |

**Usage**:
```bash
# Single phrase
echomine search export.json --phrase "algo-insights"

# Multiple phrases (OR logic by default)
echomine search export.json --phrase "algo-insights" --phrase "data pipeline"

# Combined with keywords
echomine search export.json -k "python" --phrase "algo-insights"
```

**Behavior**:
- Case-insensitive exact substring matching
- No tokenization (hyphens, dots, spaces preserved)
- Multiple phrases use OR logic (any match returns result)
- Phrases can be combined with `-k` keywords

---

### `--match-mode` (FR-007, FR-008)

| Attribute | Value |
|-----------|-------|
| Flag | `--match-mode` |
| Short | None |
| Type | `Literal["all", "any"]` |
| Multiple | No |
| Required | No |
| Default | `any` |

**Usage**:
```bash
# Require ALL keywords/phrases present
echomine search export.json -k "python" -k "async" --match-mode all

# Explicit ANY mode (same as default)
echomine search export.json -k "python" -k "async" --match-mode any
```

**Behavior**:
- `any`: Return conversations matching ANY keyword OR phrase (default, backward compatible)
- `all`: Return only conversations matching ALL keywords AND phrases
- Invalid value → exit code 2 (usage error)

---

### `--exclude` (FR-012, FR-013)

| Attribute | Value |
|-----------|-------|
| Flag | `--exclude` |
| Short | None |
| Type | `str` |
| Multiple | Yes (can be specified multiple times) |
| Required | No |
| Default | None |

**Usage**:
```bash
# Exclude single term
echomine search export.json -k "python" --exclude "django"

# Exclude multiple terms (NOR logic - neither present)
echomine search export.json -k "python" --exclude "django" --exclude "flask"
```

**Behavior**:
- Exclude conversations containing ANY excluded term
- Uses same tokenization as keywords
- Applied after matching, before ranking (FR-014)

---

### `--role` (FR-017)

| Attribute | Value |
|-----------|-------|
| Flag | `--role` |
| Short | None |
| Type | `Literal["user", "assistant", "system"]` |
| Multiple | No |
| Required | No |
| Default | None (all roles) |

**Usage**:
```bash
# Search only user messages
echomine search export.json -k "refactor" --role user

# Search only assistant messages
echomine search export.json -k "recommend" --role assistant

# Search only system messages
echomine search export.json -k "instruction" --role system
```

**Behavior**:
- Filters messages by role before keyword/phrase matching (FR-018)
- `None` (omitted) → search all roles (current behavior, FR-019)
- Invalid value → exit code 2 (usage error)

---

## Output Changes

### Human-Readable Format

**Before (v1.0.x)**:
```
Score  ID                                    Title                         Created     Messages
─────────────────────────────────────────────────────────────────────────────────────────────────
0.85   abc-123                               Python async patterns          2024-01-15  47
0.72   def-456                               Database optimization          2024-01-10  23
```

**After (v1.1.0)**:
```
Score  ID         Title                    Created     Snippet                                            Messages
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
0.85   abc-123    Python async patterns     2024-01-15  We use asyncio.gather() for concurrent... (+3)    47
0.72   def-456    Database optimization     2024-01-10  Consider adding an index on the user_id...        23
```

**New Column**: `Snippet` (~50-60 chars visible, truncated)

---

### JSON Format

**Before (v1.0.x)**:
```json
{
  "query": {
    "keywords": ["python"],
    "limit": 10
  },
  "results": [
    {
      "conversation": {...},
      "score": 0.85,
      "matched_message_ids": ["msg-001", "msg-005"]
    }
  ],
  "total_count": 2,
  "returned_count": 2
}
```

**After (v1.1.0)**:
```json
{
  "query": {
    "keywords": ["python"],
    "phrases": ["algo-insights"],
    "match_mode": "all",
    "exclude_keywords": ["django"],
    "role_filter": "user",
    "limit": 10
  },
  "results": [
    {
      "conversation": {...},
      "score": 0.85,
      "matched_message_ids": ["msg-001", "msg-005"],
      "snippet": "We use asyncio.gather() for concurrent requests... (+1 more matches)"
    }
  ],
  "total_count": 2,
  "returned_count": 2
}
```

**New Fields**:
- `query.phrases`: List of exact phrases searched
- `query.match_mode`: "all" or "any"
- `query.exclude_keywords`: List of excluded terms
- `query.role_filter`: Role filter applied
- `results[].snippet`: Matched text excerpt

---

## Exit Codes

| Code | Meaning | Trigger |
|------|---------|---------|
| 0 | Success | Search completed (even with 0 results) |
| 1 | Operational error | File not found, parse error |
| 2 | Usage error | Invalid `--match-mode`, invalid `--role` |

---

## Validation Rules

1. **At least one search criterion required**:
   - Must provide `-k`, `--phrase`, or `--title`
   - Error: "At least one search criterion required"

2. **Invalid match-mode**:
   - Must be "all" or "any"
   - Error: "Invalid value for --match-mode: 'foo'. Must be 'all' or 'any'"

3. **Invalid role**:
   - Must be "user", "assistant", or "system"
   - Error: "Invalid value for --role: 'bot'. Must be 'user', 'assistant', or 'system'"

---

## Help Text

```
$ echomine search --help

Usage: echomine search [OPTIONS] EXPORT_FILE

  Search conversations by keywords, phrases, and filters.

Arguments:
  EXPORT_FILE  Path to the AI conversation export file  [required]

Options:
  -k, --keywords TEXT        Keywords to search (can be repeated)
  --phrase TEXT              Exact phrase to match (can be repeated)
  --match-mode [all|any]     Require all or any keywords/phrases [default: any]
  --exclude TEXT             Exclude conversations with term (can be repeated)
  --role [user|assistant|system]
                             Filter by message role
  --title TEXT               Filter by conversation title
  --from-date DATE           Filter from date (YYYY-MM-DD)
  --to-date DATE             Filter to date (YYYY-MM-DD)
  --limit INTEGER            Maximum results [default: 10]
  --json                     Output as JSON
  -q, --quiet                Suppress progress output
  --help                     Show this message and exit

Examples:
  # Search for exact phrase
  echomine search export.json --phrase "algo-insights"

  # Require ALL keywords present
  echomine search export.json -k "python" -k "async" --match-mode all

  # Search user messages only, exclude django
  echomine search export.json -k "python" --role user --exclude "django"
```

---

## Contract Tests

```python
# tests/contract/test_cli_search_advanced.py

def test_phrase_flag_accepted():
    """--phrase flag is accepted."""
    result = runner.invoke(app, ["search", "export.json", "--phrase", "algo-insights"])
    assert result.exit_code == 0

def test_multiple_phrase_flags():
    """Multiple --phrase flags accepted."""
    result = runner.invoke(app, [
        "search", "export.json",
        "--phrase", "algo-insights",
        "--phrase", "data pipeline"
    ])
    assert result.exit_code == 0

def test_match_mode_all():
    """--match-mode all is accepted."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "python", "--match-mode", "all"
    ])
    assert result.exit_code == 0

def test_match_mode_invalid():
    """Invalid --match-mode returns exit code 2."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "python", "--match-mode", "xor"
    ])
    assert result.exit_code == 2

def test_exclude_flag_accepted():
    """--exclude flag is accepted."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "python", "--exclude", "django"
    ])
    assert result.exit_code == 0

def test_role_filter_user():
    """--role user is accepted."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "refactor", "--role", "user"
    ])
    assert result.exit_code == 0

def test_role_filter_invalid():
    """Invalid --role returns exit code 2."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "python", "--role", "bot"
    ])
    assert result.exit_code == 2

def test_json_output_includes_snippet():
    """JSON output includes snippet field."""
    result = runner.invoke(app, [
        "search", "export.json", "-k", "python", "--json"
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "snippet" in data["results"][0]

def test_json_output_includes_new_query_fields():
    """JSON output includes new query fields."""
    result = runner.invoke(app, [
        "search", "export.json",
        "--phrase", "test",
        "--match-mode", "all",
        "--exclude", "foo",
        "--role", "user",
        "--json"
    ])
    data = json.loads(result.stdout)
    assert data["query"]["phrases"] == ["test"]
    assert data["query"]["match_mode"] == "all"
    assert data["query"]["exclude_keywords"] == ["foo"]
    assert data["query"]["role_filter"] == "user"
```
