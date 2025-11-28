# Maintaining Echomine

This guide is for maintainers of the Echomine project. For contributor guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Table of Contents

- [Release Process](#release-process)
- [Versioning Policy](#versioning-policy)
- [PyPI Publishing](#pypi-publishing)
- [Documentation Maintenance](#documentation-maintenance)
- [Dependency Management](#dependency-management)
- [Issue and PR Triage](#issue-and-pr-triage)
- [Security](#security)

## Release Process

Echomine follows a structured release process to ensure quality and consistency.

### Pre-Release Checklist

Before starting a release, ensure:

- [ ] All planned features/fixes are merged to `master`
- [ ] CI/CD passes on `master` branch
- [ ] All tests pass locally: `pytest --cov=echomine`
- [ ] Type checking passes: `mypy --strict src/echomine/`
- [ ] Performance benchmarks pass: `pytest tests/performance/ --benchmark-only`
- [ ] Documentation is up to date
- [ ] No open blockers for the release

### Release Steps

1. **Update Version Number**

   Edit `pyproject.toml`:
   ```toml
   [project]
   version = "1.1.0"  # Increment according to semver
   ```

2. **Update CHANGELOG.md**

   Add release notes following [Keep a Changelog](https://keepachangelog.com/) format:

   ```markdown
   ## [1.1.0] - 2025-11-28

   ### Added
   - New feature X (#123)
   - Support for Y (#124)

   ### Changed
   - Improved performance of Z (#125)

   ### Fixed
   - Bug fix for A (#126)
   ```

3. **Commit Version Bump**

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 1.1.0"
   git push origin master
   ```

4. **Run Full Test Suite**

   ```bash
   # All tests with coverage
   pytest --cov=echomine --cov-report=term-missing

   # Type checking
   mypy --strict src/echomine/

   # Linting
   ruff check src/ tests/

   # Performance benchmarks
   pytest tests/performance/ --benchmark-only
   ```

5. **Build Distribution**

   ```bash
   # Clean old builds
   rm -rf dist/ build/ *.egg-info

   # Build wheel and source distribution
   python -m build

   # Verify build
   ls -lh dist/
   # Should see: echomine-1.1.0-py3-none-any.whl and echomine-1.1.0.tar.gz
   ```

6. **Test on TestPyPI** (Recommended)

   ```bash
   # Upload to TestPyPI
   python -m twine upload --repository testpypi dist/*

   # Test installation in clean environment
   python -m venv test-env
   source test-env/bin/activate
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ echomine

   # Verify it works
   python -c "from echomine import OpenAIAdapter; print('Success!')"
   echomine --version

   # Clean up
   deactivate
   rm -rf test-env
   ```

7. **Publish to PyPI**

   ```bash
   # Upload to production PyPI
   python -m twine upload dist/*

   # Verify on PyPI
   # Visit: https://pypi.org/project/echomine/
   ```

8. **Create Git Tag**

   ```bash
   # Create annotated tag
   git tag -a v1.1.0 -m "Release v1.1.0

   ### Added
   - Feature X

   ### Fixed
   - Bug Y
   "

   # Push tag to GitHub
   git push origin v1.1.0
   ```

9. **Create GitHub Release**

   Go to [GitHub Releases](https://github.com/echomine/echomine/releases/new):

   - Select tag: `v1.1.0`
   - Release title: `v1.1.0`
   - Description: Copy relevant section from CHANGELOG.md
   - Attach dist files (optional): `echomine-1.1.0.tar.gz`, `echomine-1.1.0-py3-none-any.whl`
   - Click "Publish release"

10. **Announce Release** (Optional)

    - Post to GitHub Discussions
    - Update project README if needed
    - Tweet/social media (if applicable)

### Post-Release

- Verify installation: `pip install --upgrade echomine`
- Monitor GitHub issues for release-related problems
- Update project roadmap/milestones

## Versioning Policy

Echomine follows [Semantic Versioning 2.0.0](https://semver.org/).

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR** (1.x.x): Breaking changes to public API
  - Removed public functions/classes
  - Changed function signatures
  - Changed behavior of existing features
  - Example: `1.0.0` → `2.0.0`

- **MINOR** (x.1.x): New features, backward compatible
  - New public functions/classes
  - New optional parameters
  - Performance improvements
  - Deprecation warnings (not removals)
  - Example: `1.0.0` → `1.1.0`

- **PATCH** (x.x.1): Bug fixes, backward compatible
  - Bug fixes
  - Documentation updates
  - Internal refactoring (no API changes)
  - Dependency updates (no breaking changes)
  - Example: `1.0.0` → `1.0.1`

### Pre-Release Versions

For alpha/beta releases:

- **Alpha**: `1.1.0-alpha.1` (early testing, unstable)
- **Beta**: `1.1.0-beta.1` (feature complete, testing)
- **Release Candidate**: `1.1.0-rc.1` (final testing)

### Breaking Changes

When making breaking changes:

1. **Deprecate first** (minor version):
   ```python
   import warnings

   def old_function():
       warnings.warn(
           "old_function is deprecated, use new_function instead",
           DeprecationWarning,
           stacklevel=2
       )
       return new_function()
   ```

2. **Document migration path** in CHANGELOG and docs

3. **Remove in next major version**

4. **Provide migration guide** in release notes

## PyPI Publishing

### Initial Setup (One-Time)

1. **Create PyPI Account**
   - Production: https://pypi.org/account/register/
   - Test: https://test.pypi.org/account/register/

2. **Configure API Token**

   ```bash
   # Create ~/.pypirc
   cat > ~/.pypirc << EOF
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-YOUR-API-TOKEN-HERE

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-YOUR-TESTPYPI-TOKEN-HERE
   EOF

   # Secure permissions
   chmod 600 ~/.pypirc
   ```

3. **Install Publishing Tools**

   ```bash
   pip install --upgrade build twine
   ```

### Publishing Checklist

Before publishing:

- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Documentation built successfully
- [ ] Tested on TestPyPI
- [ ] Git tag created
- [ ] README.md accurate (shown on PyPI)

### Troubleshooting

**Issue: Upload fails with "File already exists"**
- Solution: Cannot re-upload same version. Increment patch version.

**Issue: Package not installable after upload**
- Solution: Check dependencies in `pyproject.toml`, test with TestPyPI first

**Issue: Metadata not displaying correctly**
- Solution: Verify README.md format, check `pyproject.toml` metadata fields

## Documentation Maintenance

### When to Update Docs

Update documentation when:

- **Public API changes**: New classes, functions, parameters
- **Breaking changes**: Migration guides required
- **New features**: Usage examples, tutorials
- **Bug fixes affecting behavior**: Update expected behavior docs
- **Performance improvements**: Update performance claims

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build locally
mkdocs build

# Serve locally for preview
mkdocs serve
# Visit: http://127.0.0.1:8000

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Documentation Checklist

Before deploying docs:

- [ ] All code examples tested and working
- [ ] API reference up to date (mkdocstrings auto-generates)
- [ ] Links work (no 404s)
- [ ] Screenshots/diagrams current (if any)
- [ ] Navigation structure logical
- [ ] Search index rebuilt

### Versioned Documentation (Future)

For version-specific docs using `mike`:

```bash
# Deploy docs for version 1.1
mike deploy 1.1 latest --update-aliases

# Set default version
mike set-default latest

# Deploy to GitHub Pages
mike deploy --push 1.1 latest
```

### API Reference Generation

API docs are auto-generated from docstrings using mkdocstrings.

**To update API docs:**

1. Update docstrings in source code (Google style)
2. Run `mkdocs build` (auto-generates from docstrings)
3. Review at `docs/api/` pages

**Example docstring:**

```python
def search(
    file_path: Path,
    query: SearchQuery,
) -> Iterator[SearchResult[Conversation]]:
    """Search conversations matching query criteria.

    Args:
        file_path: Path to OpenAI export JSON file
        query: Search parameters

    Yields:
        SearchResult with conversation and relevance score

    Raises:
        FileNotFoundError: If file_path does not exist

    Example:
        ```python
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])
        for result in adapter.search(Path("export.json"), query):
            print(result.score, result.conversation.title)
        ```
    """
```

## Dependency Management

### Dependency Categories

1. **Core Dependencies** (required for library)
   - Listed in `dependencies` in `pyproject.toml`
   - Conservative version constraints
   - Example: `pydantic>=2.6.0,<3.0.0`

2. **Development Dependencies** (dev, testing, linting)
   - Listed in `[project.optional-dependencies]` → `dev`
   - Can be more permissive

3. **Documentation Dependencies**
   - Listed in `[project.optional-dependencies]` → `docs`

### Update Strategy

**Security Updates**: Immediate
```bash
# Check for security vulnerabilities
pip-audit

# Update specific package
pip install --upgrade pydantic
# Update pyproject.toml, test, release patch version
```

**Minor Updates**: Monthly review
```bash
# Check outdated packages
pip list --outdated

# Update in isolated environment, test thoroughly
# If breaking changes: evaluate impact before updating
```

**Major Updates**: Evaluate breaking changes
```bash
# Example: Pydantic v2 → v3 (hypothetical)
# 1. Read migration guide
# 2. Test in separate branch
# 3. Update code for breaking changes
# 4. Run full test suite
# 5. Update docs
# 6. Release as MAJOR version bump (echomine 1.x → 2.x)
```

### Dependency Update Checklist

Before updating dependencies:

- [ ] Read changelog/release notes
- [ ] Check for breaking changes
- [ ] Test in isolated environment
- [ ] Run full test suite
- [ ] Update type hints if needed (mypy)
- [ ] Update docs if behavior changed
- [ ] Update pyproject.toml version constraints
- [ ] Note in CHANGELOG.md

### Pinning Strategy

**Library (`dependencies`):**
- Use `>=X.Y.Z,<MAJOR+1` (e.g., `>=2.6.0,<3.0.0`)
- Allows minor/patch updates, prevents breaking changes

**Development (`dev`):**
- Use `>=X.Y` (e.g., `>=1.5.0`)
- More permissive, faster access to tooling improvements

## Issue and PR Triage

### Issue Labels

Use GitHub labels for organization:

- **Type**: `bug`, `feature`, `documentation`, `question`
- **Priority**: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Status**: `needs-triage`, `blocked`, `ready`, `in-progress`
- **Area**: `cli`, `library`, `search`, `adapters`, `tests`
- **Meta**: `good-first-issue`, `help-wanted`, `duplicate`, `wontfix`

### Triage Process

**Daily:**
- Review new issues/PRs
- Apply labels
- Ask for clarification if needed
- Close duplicates/off-topic

**Weekly:**
- Review `needs-triage` label
- Prioritize for milestone
- Assign to contributors (if applicable)

### PR Review Checklist

Before merging PR:

- [ ] CI/CD passes (tests, type checking, linting)
- [ ] Code follows TDD (tests included)
- [ ] Type hints present and mypy passes
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated (if user-facing)
- [ ] No merge conflicts
- [ ] Conventional commit message format
- [ ] Reviewer approval

### Merge Strategy

- **Squash and merge**: Combine commits with clean message
- **Message format**: Conventional Commits
- **Delete branch**: After merge

## Security

### Reporting Security Issues

Security issues should NOT be reported via public GitHub issues.

**To report a security vulnerability:**
1. Email maintainers directly (list in SECURITY.md if created)
2. Include: description, impact, reproduction steps
3. Wait for acknowledgment before public disclosure

### Security Update Process

1. **Assess severity**: Critical, High, Medium, Low
2. **Patch privately**: Fix in private branch
3. **Test thoroughly**: Verify fix, no regressions
4. **Release patch version**: Expedited release process
5. **Announce**: CHANGELOG, GitHub Security Advisory
6. **Credit reporter**: With permission

### Dependency Security

```bash
# Check for known vulnerabilities (run monthly)
pip-audit

# Update vulnerable dependencies immediately
pip install --upgrade <package>

# Test and release patch version
```

## Governance

### Maintainer Responsibilities

- Review PRs within 1 week
- Triage issues within 2 business days
- Release patches for critical bugs within 24 hours
- Release minor versions quarterly (or as needed)
- Keep documentation up to date
- Respond to security issues immediately

### Decision Making

- **Minor changes**: Single maintainer approval
- **Major changes**: Consensus among maintainers
- **Breaking changes**: RFC process + consensus

### Maintainer Onboarding

When adding new maintainer:

1. Add to GitHub team with write access
2. Share this MAINTAINING.md guide
3. Add to PyPI project collaborators
4. Grant access to relevant infrastructure
5. Announce in project README/docs

---

## Quick Reference

### Common Commands

```bash
# Release workflow
python -m build && python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
git tag -a v1.1.0 -m "Release v1.1.0" && git push origin v1.1.0

# Docs deployment
mkdocs gh-deploy

# Security audit
pip-audit

# Full quality check
pytest --cov=echomine && mypy --strict src/echomine/ && ruff check src/ tests/
```

### Support Contacts

- **GitHub Issues**: https://github.com/echomine/echomine/issues
- **GitHub Discussions**: https://github.com/echomine/echomine/discussions
- **PyPI**: https://pypi.org/project/echomine/

---

**Last Updated**: 2025-11-28
