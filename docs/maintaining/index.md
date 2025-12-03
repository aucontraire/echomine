# Maintaining Echomine

This section contains guides for project maintainers. For contributor guidelines, see [Contributing](../contributing.md).

## Quick Navigation

- **[Release Process](release-process.md)**: Step-by-step release workflow
- **[Versioning](versioning.md)**: Semantic versioning policy
- **[PyPI Publishing](pypi-publishing.md)**: Publishing to PyPI workflow

For the complete maintainer guide, see **[MAINTAINING.md](https://github.com/echomine/echomine/blob/master/MAINTAINING.md)** in the repository root.

## Overview

Maintainers are responsible for:

- **Releases**: Planning, executing, and documenting releases
- **Quality**: Ensuring code quality standards are met
- **Community**: Reviewing PRs, triaging issues, supporting contributors
- **Security**: Responding to security issues, updating dependencies
- **Documentation**: Keeping docs accurate and up to date

## Maintainer Quick Reference

### Release Workflow

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Run quality checks
pytest --cov=echomine && mypy --strict src/echomine/

# 4. Build distribution
python -m build

# 5. Test on TestPyPI
python -m twine upload --repository testpypi dist/*

# 6. Publish to PyPI
python -m twine upload dist/*

# 7. Tag release
git tag -a v1.1.0 -m "Release v1.1.0" && git push origin v1.1.0

# 8. Create GitHub release
gh release create v1.1.0 --title "v1.1.0" --notes-file RELEASE_NOTES.md
```

### Issue Triage

**Labels:**
- Type: `bug`, `feature`, `documentation`, `question`
- Priority: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- Status: `needs-triage`, `blocked`, `ready`, `in-progress`
- Area: `cli`, `library`, `search`, `adapters`, `tests`
- Meta: `good-first-issue`, `help-wanted`, `duplicate`, `wontfix`

**Triage Process:**
1. Review new issues/PRs daily
2. Apply appropriate labels
3. Ask for clarification if needed
4. Close duplicates
5. Assign to milestone

### PR Review Checklist

Before merging:

- [ ] CI/CD passes (tests, mypy, ruff)
- [ ] TDD followed (tests included)
- [ ] Type hints present, mypy --strict passes
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated (if user-facing)
- [ ] No merge conflicts
- [ ] Conventional commit format
- [ ] Reviewer approval

### Security

**Reporting:** Security issues via private email, NOT public issues

**Update Process:**
1. Assess severity
2. Patch privately
3. Test thoroughly
4. Release patch version
5. Announce (CHANGELOG, GitHub Security Advisory)

## Versioning Policy

Echomine follows [Semantic Versioning 2.0.0](https://semver.org/).

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes (remove functions, change signatures)
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Examples

- `1.0.0` → `2.0.0`: Breaking change (removed old API)
- `1.0.0` → `1.1.0`: New feature (added search filtering)
- `1.0.0` → `1.0.1`: Bug fix (fixed null timestamp crash)

See [Versioning Guide](versioning.md) for details.

## Release Cadence

- **Patch**: As needed (bug fixes, security updates)
- **Minor**: Quarterly or when features ready
- **Major**: Annually or when breaking changes justified

## Documentation Maintenance

### When to Update

- Public API changes
- CLI command changes
- Breaking changes (migration guides)
- Bug fixes affecting behavior
- Performance improvements

### Deployment

```bash
# Build and serve locally
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

API reference is auto-generated from docstrings (mkdocstrings).

## Dependency Management

### Update Strategy

- **Security**: Immediate
- **Minor**: Monthly review
- **Major**: Evaluate breaking changes

### Commands

```bash
# Check for security issues
pip-audit

# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade <package>
# Update pyproject.toml, test, commit
```

## Governance

### Decision Making

- **Minor changes**: Single maintainer approval
- **Major changes**: Consensus
- **Breaking changes**: RFC + consensus

### Maintainer Responsibilities

- Review PRs within 1 week
- Triage issues within 2 business days
- Release patches for critical bugs within 24 hours
- Release minor versions quarterly
- Respond to security issues immediately

## Support Channels

- **GitHub Issues**: https://github.com/echomine/echomine/issues
- **GitHub Discussions**: https://github.com/echomine/echomine/discussions
- **PyPI**: https://pypi.org/project/echomine/

---

For complete details, see **[MAINTAINING.md](https://github.com/echomine/echomine/blob/master/MAINTAINING.md)**.

**Last Updated**: 2025-11-28
