# Release Template

Use this template when creating GitHub releases.

---

## Release Title Format

```
v{VERSION} - {SHORT_DESCRIPTION}
```

Examples:
- `v1.0.0 - Initial Release`
- `v1.0.2 - JSON Export & License Fix`
- `v1.1.0 - Claude Adapter Support`

---

## Release Notes Template

```markdown
## What's New

### Features
- {Feature 1 description}
- {Feature 2 description}

### Improvements
- {Improvement 1}
- {Improvement 2}

### Bug Fixes
- {Fix 1}
- {Fix 2}

## Installation

```bash
pip install echomine=={VERSION}
```

Or upgrade:

```bash
pip install --upgrade echomine
```

## Quick Start

```python
from echomine import OpenAIAdapter

adapter = OpenAIAdapter()
for conversation in adapter.stream_conversations(Path("export.json")):
    print(conversation.title)
```

## Documentation

- [Full Documentation](https://aucontraire.github.io/echomine/)
- [API Reference](https://aucontraire.github.io/echomine/api/)
- [CLI Usage](https://aucontraire.github.io/echomine/cli-usage/)

## Breaking Changes

{List any breaking changes, or "None" if backwards compatible}

## Contributors

Thanks to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/aucontraire/echomine/compare/v{PREV_VERSION}...v{VERSION}
```

---

## Checklist Before Release

- [ ] All CI checks pass (Ubuntu, macOS, Windows × Python 3.12/3.13)
- [ ] CHANGELOG.md updated with release notes
- [ ] Version bumped in `pyproject.toml` and `src/echomine/__init__.py`
- [ ] Documentation updated if needed
- [ ] TestPyPI validation complete (optional but recommended)
- [ ] Git tag created: `git tag -a v{VERSION} -m "Release v{VERSION}"`
- [ ] Tag pushed: `git push origin v{VERSION}`

---

## Release Workflow

### 1. Prepare Release

```bash
# Ensure clean working directory
git status

# Run full test suite
pytest --cov=echomine

# Verify type checking
mypy --strict src/echomine/

# Check linting
ruff check src/ tests/
```

### 2. Build & Upload to PyPI

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Check package
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

### 3. Create GitHub Release

```bash
# Create annotated tag
git tag -a v{VERSION} -m "Release v{VERSION}"

# Push tag
git push origin v{VERSION}

# Create release via CLI (or use GitHub web UI)
gh release create v{VERSION} \
  --title "v{VERSION} - {SHORT_DESCRIPTION}" \
  --notes-file RELEASE_NOTES.md
```

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New backwards-compatible features
- **PATCH** (0.0.X): Backwards-compatible bug fixes

---

**Last Updated**: 2025-12-03
