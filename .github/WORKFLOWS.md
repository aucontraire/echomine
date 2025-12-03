# GitHub Actions CI/CD Pipeline

This directory contains the automated workflows for the echomine project.

## Workflows

### 🧪 Test Suite (`test.yml`)

**Triggers**: Every push and pull request

**Jobs**:
1. **Test Matrix** - Runs on 3 OS × 2 Python versions = 6 combinations
   - **Operating Systems**: Ubuntu, macOS, Windows
   - **Python Versions**: 3.12, 3.13
   - **Quality Gates**:
     - ✅ Ruff linting (`ruff check`)
     - ✅ Ruff formatting (`ruff format --check`)
     - ✅ Type checking (`mypy --strict`)
     - ✅ Test suite (`pytest` with coverage)
   - **Artifacts**:
     - Coverage HTML report (Ubuntu + Python 3.12 only)
     - Codecov upload (requires `CODECOV_TOKEN` secret)

2. **Acceptance Validation** - Validates all user story scenarios
   - Runs `validate_acceptance.py`
   - Uploads `ACCEPTANCE_VALIDATION_REPORT.md` as artifact
   - Current target: ≥93.3% pass rate (28/30 scenarios)

3. **Performance Benchmarks** - Ensures performance requirements
   - Runs `pytest tests/performance/ --benchmark-only`
   - Uploads benchmark results as JSON
   - Tracks performance regression on main/master branch (requires `benchmark-action`)

**Status Badge**:
```markdown
![Test Suite](https://github.com/YOUR_USERNAME/echomine/actions/workflows/test.yml/badge.svg)
```

---

### 📚 Documentation (`docs.yml`)

**Triggers**: Push to main/master, pull requests, manual dispatch

**Jobs**:
1. **Build** - Builds documentation with MkDocs
   - Validates with `mkdocs build --strict`
   - Uploads documentation artifact for preview

2. **Deploy** - Deploys to GitHub Pages (main/master only)
   - Runs `mkdocs gh-deploy`
   - Automatically updates https://YOUR_USERNAME.github.io/echomine/

**Setup Required**:
1. Enable GitHub Pages in repository settings
2. Set source to "gh-pages" branch
3. Documentation will be available at: `https://YOUR_USERNAME.github.io/echomine/`

**Status Badge**:
```markdown
![Documentation](https://github.com/YOUR_USERNAME/echomine/actions/workflows/docs.yml/badge.svg)
```

---

### 🚀 Release (`release.yml`)

**Triggers**:
- **Automatic**: Push tags matching `v*.*.*` (e.g., `v1.0.0`)
- **Manual**: Workflow dispatch with version input (for testing)

**Jobs**:
1. **Build** - Creates distribution packages
   - Builds wheel (`.whl`) and source distribution (`.tar.gz`)
   - Validates with `twine check`
   - Uploads packages as artifacts

2. **Test Install** - Tests installation in clean environments
   - Tests on Ubuntu, macOS, Windows × Python 3.12, 3.13
   - Verifies CLI is available (`echomine --version`)
   - Verifies library import (`from echomine import OpenAIAdapter`)

3. **Publish to TestPyPI** - Test publication (manual dispatch only)
   - Uploads to https://test.pypi.org
   - Requires `testpypi` environment in GitHub settings

4. **Publish to PyPI** - Production publication (tag push only)
   - Uploads to https://pypi.org
   - **Requires**:
     - `pypi` environment in GitHub settings
     - PyPI trusted publishing configured (see setup below)

5. **Create GitHub Release** - Creates release with changelog
   - Generates release notes from commits
   - Attaches distribution packages
   - Links to PyPI package

**PyPI Trusted Publishing Setup**:
1. Go to https://pypi.org/manage/account/publishing/
2. Add new publisher:
   - **PyPI Project Name**: `echomine`
   - **Owner**: `YOUR_USERNAME`
   - **Repository**: `echomine`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`
3. Repeat for TestPyPI: https://test.pypi.org/manage/account/publishing/

**GitHub Environment Setup**:
1. Go to repository Settings → Environments
2. Create `pypi` environment:
   - Add deployment protection rules (require approvals if desired)
   - No secrets needed (using trusted publishing)
3. Create `testpypi` environment (same as above)

**Creating a Release**:
```bash
# 1. Update version in pyproject.toml
VERSION=1.0.0

# 2. Commit and tag
git add pyproject.toml
git commit -m "chore: bump version to $VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"

# 3. Push tag (triggers release workflow)
git push origin "v$VERSION"
```

**Status Badge**:
```markdown
![Release](https://github.com/YOUR_USERNAME/echomine/actions/workflows/release.yml/badge.svg)
```

---

### 🔒 Security (`security.yml`)

**Triggers**:
- Push to main/master/develop
- Pull requests
- Weekly schedule (Mondays at 00:00 UTC)

**Jobs**:
1. **Dependency Scan** - Checks for vulnerable dependencies
   - Runs `safety check` (checks against safety-db)
   - Runs `pip-audit` (checks against PyPI advisory database)

2. **CodeQL Analysis** - Static code analysis
   - Scans for security vulnerabilities
   - Checks code quality issues
   - Results appear in Security tab → Code scanning alerts

**Status Badge**:
```markdown
![Security](https://github.com/YOUR_USERNAME/echomine/actions/workflows/security.yml/badge.svg)
```

---

### 🤖 Dependabot (`dependabot.yml`)

**Purpose**: Automated dependency updates

**Configuration**:
- **Python dependencies**: Weekly updates (Mondays)
  - Groups pytest-related packages
  - Groups type checking packages (mypy, types-*)
  - Groups linting packages (ruff, pre-commit)
- **GitHub Actions**: Weekly updates (Mondays)

**Limits**:
- Python: Max 10 open PRs
- GitHub Actions: Max 5 open PRs

**Auto-assigned Reviewers**: `@omarcontreras` (update with your username)

---

## Local Testing

### Test workflows locally with act

Install [act](https://github.com/nektos/act):
```bash
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

Run workflows locally:
```bash
# Test suite
act push -W .github/workflows/test.yml

# Documentation build
act push -W .github/workflows/docs.yml --job build

# Security scan
act push -W .github/workflows/security.yml
```

---

## Secrets Configuration

### Required Secrets

Add these in repository Settings → Secrets and variables → Actions:

| Secret | Required For | How to Get |
|--------|-------------|------------|
| `CODECOV_TOKEN` | Coverage reporting (test.yml) | https://codecov.io (optional) |

### Optional Integrations

- **Codecov**: Code coverage visualization and PR comments
- **CodeQL**: Enabled by default for public repos, no configuration needed

---

## Badges for README

Add to your main/master README.md:

```markdown
[![Test Suite](https://github.com/YOUR_USERNAME/echomine/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/echomine/actions/workflows/test.yml)
[![Documentation](https://github.com/YOUR_USERNAME/echomine/actions/workflows/docs.yml/badge.svg)](https://github.com/YOUR_USERNAME/echomine/actions/workflows/docs.yml)
[![Security](https://github.com/YOUR_USERNAME/echomine/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_USERNAME/echomine/actions/workflows/security.yml)
[![PyPI Version](https://img.shields.io/pypi/v/echomine)](https://pypi.org/project/echomine/)
[![Python Version](https://img.shields.io/pypi/pyversions/echomine)](https://pypi.org/project/echomine/)
[![License](https://img.shields.io/github/license/YOUR_USERNAME/echomine)](LICENSE)
```

---

## Workflow Best Practices

### Performance Optimization
- ✅ Uses `cache: 'pip'` in setup-python action
- ✅ Matrix jobs run in parallel
- ✅ Artifacts retain for 30-90 days (not forever)

### Security
- ✅ Uses pinned major versions for actions (`@v4`, `@v5`)
- ✅ Minimal permissions (write only where needed)
- ✅ Dependabot keeps actions up to date
- ✅ CodeQL scanning enabled

### Cost Efficiency
- ✅ `fail-fast: false` allows all matrix combinations to complete (better visibility)
- ✅ Conditional jobs (e.g., only upload coverage from one OS/Python combo)
- ✅ Artifact retention limits (30-90 days, not forever)

---

## Troubleshooting

### Test failures on Windows
- Check for path separator issues (`/` vs `\`)
- Ensure `shell: bash` is used for cross-platform scripts

### Documentation deployment fails
- Verify GitHub Pages is enabled
- Check branch is `gh-pages`
- Ensure permissions include `contents: write`

### PyPI publish fails
- Verify trusted publishing is configured on PyPI
- Check environment name matches (`pypi` exactly)
- Ensure tag format matches `v*.*.*`

### Codecov upload fails
- Verify `CODECOV_TOKEN` secret is set
- Check repository is public or has Codecov plan
- Upload failure is non-blocking (`fail_ci_if_error: false`)

---

## Maintenance

### Updating Workflows
1. Edit workflow files in `.github/workflows/`
2. Test locally with `act` if possible
3. Commit and push - workflows run automatically
4. Monitor Actions tab for results

### Updating Dependencies
- Dependabot creates PRs automatically every Monday
- Review and merge PRs to keep dependencies current
- Grouped updates reduce PR noise

### Adding New Workflows
1. Create new `.yml` file in `.github/workflows/`
2. Follow naming convention: `kebab-case.yml`
3. Add documentation to this README
4. Update status badges in main/master README.md
