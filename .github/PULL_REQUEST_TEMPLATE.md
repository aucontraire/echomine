## Summary

<!-- Brief description of what this PR does -->

## Changes

<!-- List the main changes in this PR -->
-
-
-

## Related Issues

<!-- Link related issues using "Closes #123" or "Relates to #456" -->
- Closes #
- Implements FR-

## Type of Change

<!-- Mark the relevant option(s) with an 'x' -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring (no functional changes)
- [ ] Test addition/improvement
- [ ] Dependency update

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Contract tests added/updated (if protocol changes)
- [ ] Performance tests added/updated (if performance-related)
- [ ] Manual testing performed
- [ ] Test coverage maintained/improved (>80% overall)

### Test Commands Run

```bash
# Add the commands you ran to test your changes
pytest tests/unit/test_xxx.py -v
pytest --cov=echomine --cov-report=term-missing
```

## Code Quality Checklist

<!-- Verify all quality checks pass -->

- [ ] Tests pass: `pytest`
- [ ] Type checking passes: `mypy --strict src/echomine/`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] Formatting applied: `ruff format src/ tests/`
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`
- [ ] Code follows TDD (tests written first)
- [ ] Docstrings added/updated (Google style)
- [ ] Type hints present on all functions
- [ ] No `Any` types in public API
- [ ] CHANGELOG.md updated (if user-facing change)

## Documentation

<!-- Check all that apply -->

- [ ] Public API documented (docstrings with examples)
- [ ] README updated (if needed)
- [ ] User guide updated (if needed)
- [ ] API reference updated (auto-generated from docstrings)
- [ ] Migration guide added (if breaking change)
- [ ] Code examples tested and working

## Constitution Compliance

<!-- Verify adherence to project principles -->

- [ ] Library-first: Core logic in library, CLI wraps it (Principle I)
- [ ] CLI contract: stdout for results, stderr for progress/errors (Principle II)
- [ ] TDD followed: RED-GREEN-REFACTOR cycle (Principle III)
- [ ] Logging: JSON structured logs with context (Principle IV)
- [ ] YAGNI: Only implements spec requirements (Principle V)
- [ ] Strict typing: mypy --strict passes with zero errors (Principle VI)
- [ ] Stateless adapters: No __init__ params if adapter (Principle VII)
- [ ] Memory efficient: Streaming/generators, O(1) memory (Principle VIII)

## Performance Impact

<!-- Complete if this PR affects performance -->

- [ ] No performance impact
- [ ] Performance improved (include benchmark results)
- [ ] Performance regression (justified and documented)

**Benchmark Results** (if applicable):
```
# Paste pytest-benchmark results here
```

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

**Does this PR introduce breaking changes?** No / Yes

**If yes, describe:**
- What breaks:
- Migration path:
- Deprecation warnings added: [ ]

## Screenshots/Examples

<!-- Add screenshots, code examples, or output samples if relevant -->

```python
# Example usage of new feature
```

## Deployment Notes

<!-- Any special notes for deploying this change -->

- [ ] No special deployment steps required
- [ ] Requires dependency updates:
- [ ] Requires data migration:
- [ ] Requires configuration changes:

## Reviewer Checklist

<!-- For maintainers reviewing this PR -->

- [ ] Code quality meets project standards
- [ ] Tests are comprehensive and pass
- [ ] Type hints are correct and mypy passes
- [ ] Documentation is clear and accurate
- [ ] Constitution principles followed
- [ ] Performance acceptable
- [ ] CHANGELOG.md updated appropriately
- [ ] Conventional commit message format used

---

**Additional Context**

<!-- Add any other context, design decisions, or tradeoffs made -->
