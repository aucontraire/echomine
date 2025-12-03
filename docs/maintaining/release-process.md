# Release Process

This guide covers the step-by-step process for releasing new versions of Echomine.

## Release Types

| Type | Version Change | When to Use |
|------|----------------|-------------|
| **Patch** | 1.0.0 → 1.0.1 | Bug fixes, security patches |
| **Minor** | 1.0.0 → 1.1.0 | New features, backward compatible |
| **Major** | 1.0.0 → 2.0.0 | Breaking changes |

See [Versioning](versioning.md) for detailed version policy.

## Pre-Release Checklist

Before starting a release:

- [ ] All tests pass: `pytest --cov=echomine`
- [ ] Type checking passes: `mypy --strict src/echomine/`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] Documentation builds: `mkdocs build --strict`
- [ ] No blocking issues in GitHub Issues
- [ ] CHANGELOG.md is up to date

## Release Workflow

### Step 1: Create Release Branch

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create release branch
git checkout -b release/v1.2.0
```

### Step 2: Update Version

Update version in `pyproject.toml`:

```toml
[project]
name = "echomine"
version = "1.2.0"  # Update this
```

### Step 3: Update CHANGELOG.md

Add release notes following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.2.0] - 2024-01-15

### Added
- New `--title` flag for search command (#123)
- Support for date-only filtering (#125)

### Changed
- Improved BM25 ranking performance by 30%

### Fixed
- Fixed crash when export contains null timestamps (#127)

### Deprecated
- `--keywords-only` flag (use `--title` instead)
```

### Step 4: Run Final Quality Checks

```bash
# All tests
pytest --cov=echomine --cov-report=term-missing

# Type checking
mypy --strict src/echomine/

# Linting
ruff check src/ tests/
ruff format --check src/ tests/

# Documentation
mkdocs build --strict

# Build packages
python -m build
```

### Step 5: Commit and Tag

```bash
# Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v1.2.0"

# Push release branch
git push origin release/v1.2.0

# Create and push tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### Step 6: Create Pull Request

Create PR from `release/v1.2.0` to `main`:

```bash
gh pr create \
  --title "Release v1.2.0" \
  --body "## Release v1.2.0

See CHANGELOG.md for details.

## Checklist
- [x] Version updated in pyproject.toml
- [x] CHANGELOG.md updated
- [x] All tests pass
- [x] Documentation builds"
```

### Step 7: Merge and Publish

After PR approval:

1. **Merge PR** to main
2. **GitHub Actions** automatically:
   - Runs all tests
   - Builds packages
   - Publishes to PyPI (via trusted publishing)
   - Creates GitHub Release

### Step 8: Verify Release

```bash
# Check PyPI
pip install echomine==1.2.0

# Verify version
echomine --version
# echomine 1.2.0

# Check GitHub Release
gh release view v1.2.0
```

## Automated Release (GitHub Actions)

The release workflow (`.github/workflows/release.yml`) handles:

1. **Build**: Creates wheel and sdist packages
2. **Test**: Installs on all platforms (Ubuntu, macOS, Windows)
3. **Publish**: Uploads to PyPI via trusted publishing
4. **Release**: Creates GitHub Release with changelog

### Triggering a Release

Releases are triggered by version tags:

```bash
git tag v1.2.0
git push origin v1.2.0
# GitHub Actions takes over
```

### Manual Trigger

For testing or re-runs:

```bash
gh workflow run release.yml \
  --field version=1.2.0
```

## Hotfix Process

For urgent bug fixes:

```bash
# Branch from latest release tag
git checkout -b hotfix/v1.2.1 v1.2.0

# Fix the bug
# ... make changes ...

# Update version to patch
# pyproject.toml: version = "1.2.1"

# Update CHANGELOG
# Add entry under [1.2.1]

# Commit, tag, push
git add -A
git commit -m "fix: critical bug in search (#999)"
git tag v1.2.1
git push origin hotfix/v1.2.1 v1.2.1

# Create PR to main
gh pr create --title "Hotfix v1.2.1"
```

## Release Notes Template

```markdown
## What's New in v1.2.0

### Highlights

Brief summary of the most important changes.

### New Features

- **Feature Name**: Description of what it does and why it's useful.
  ```python
  # Example usage
  ```

### Improvements

- Performance: 30% faster search on large files
- Memory: Reduced memory usage for streaming

### Bug Fixes

- Fixed crash when... (#123)
- Fixed incorrect results when... (#125)

### Breaking Changes

(Only for major releases)

- Removed deprecated `old_function()`. Use `new_function()` instead.
- Changed return type of `search()` from `List` to `Iterator`.

### Migration Guide

(Only for breaking changes)

```python
# Before (v1.x)
results = adapter.search(path, query)
for r in results:
    print(r)

# After (v2.x)
results = list(adapter.search(path, query))
for r in results:
    print(r)
```

### Contributors

Thanks to everyone who contributed:
- @username1
- @username2

### Full Changelog

See [CHANGELOG.md](https://github.com/aucontraire/echomine/blob/main/CHANGELOG.md) for complete details.
```

## Rollback Process

If a release has critical issues:

### 1. Yank from PyPI

```bash
# Yank specific version (makes it uninstallable for new users)
pip index yank echomine==1.2.0
```

### 2. Create Hotfix

Follow the hotfix process above.

### 3. Communicate

- Update GitHub Release notes with warning
- Post in Discussions if applicable
- Update CHANGELOG with note about yanked version

## Release Schedule

- **Patch releases**: As needed for bug fixes
- **Minor releases**: When features are ready (no fixed schedule)
- **Major releases**: Planned, with advance notice

## Next Steps

- [Versioning](versioning.md): Version numbering policy
- [PyPI Publishing](pypi-publishing.md): Publishing setup

---

**Last Updated**: 2025-11-30
