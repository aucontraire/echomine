# Observability Checklist: Advanced Search Enhancement Package

**Purpose**: Validate Constitution Principle IV compliance before commit
**Created**: 2025-12-03
**Gate**: Before merge to main

---

## Logging & Observability (Constitution Principle IV)

> "Log key decision points, inputs, and outputs"

### Query Parameter Logging

- [ ] LOG001 - Do new search features log query parameters? (phrases, match_mode, exclude_keywords, role_filter)
- [ ] LOG002 - Are query parameters logged with structured fields (not string interpolation)?
- [ ] LOG003 - Is sensitive content excluded from logs? (actual message content, user data)

### Decision Point Logging

- [ ] LOG004 - Is phrase matching logged with match count? (operation="phrase_match", matches=N)
- [ ] LOG005 - Is match mode filtering logged? (operation="match_mode_filter", mode=all/any, passed=N)
- [ ] LOG006 - Is exclusion filtering logged? (operation="exclude_filter", excluded_count=N)
- [ ] LOG007 - Is role filtering logged? (operation="role_filter", role=user/assistant/system, filtered_count=N)
- [ ] LOG008 - Is snippet extraction logged? (operation="snippet_extract", length=N, fallback=bool)

### Error & Warning Logging

- [ ] LOG009 - Are malformed entries logged with WARNING level? (graceful degradation)
- [ ] LOG010 - Do errors include exc_info=True for stack traces?
- [ ] LOG011 - Are errors logged with actionable context? (file_name, conversation_id, operation)

### Contextual Fields

- [ ] LOG012 - Do logs include operation field? (e.g., "search", "phrase_match", "snippet_extract")
- [ ] LOG013 - Do logs include file_name for file operations?
- [ ] LOG014 - Do logs include conversation_id where applicable?
- [ ] LOG015 - Do logs include count/result metrics where applicable?

---

## Example Logging Patterns

### Good: Structured Logging with Context

```python
logger.info(
    "Applying phrase filter",
    operation="phrase_match",
    phrase=query.phrases[0] if query.phrases else None,
    matches=match_count,
    conversation_id=conversation.id,
)
```

### Good: Warning for Graceful Degradation

```python
logger.warning(
    "Skipped malformed message for snippet extraction",
    operation="snippet_extract",
    conversation_id=conversation.id,
    message_id=message_id,
    reason="content field missing",
)
```

### Bad: String Interpolation

```python
# DON'T DO THIS
logger.info(f"Found {count} matches for phrase {phrase}")
```

---

## Validation Steps

1. **Run search with all new features enabled**
2. **Examine log output** (export LOG_LEVEL=DEBUG for verbose logs)
3. **Verify structured fields** are present (grep for "operation=")
4. **Check error scenarios** (malformed fixture, invalid role, etc.)

---

## Sign-off

| Task | Reviewer | Date | Status |
|------|----------|------|--------|
| T015 (phrase_matches) logging | | | |
| T025 (all_terms_present) logging | | | |
| T034 (exclude_filter) logging | | | |
| T043 (role filter) logging | | | |
| T051 (extract_snippet) logging | | | |
