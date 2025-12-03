# PyPI Publishing Guide

This guide covers publishing Echomine to the Python Package Index (PyPI).

## Overview

Echomine uses **Trusted Publishing** (OIDC) for secure, tokenless publishing from GitHub Actions.

### Benefits of Trusted Publishing

- No API tokens to manage or rotate
- No secrets to configure in GitHub
- Audit trail of which workflow published each release
- More secure than long-lived API tokens

## Prerequisites

### 1. PyPI Account

Create accounts on:
- [PyPI](https://pypi.org/account/register/) (production)
- [TestPyPI](https://test.pypi.org/account/register/) (testing)

### 2. Public Repository

Trusted Publishing requires a **public** GitHub repository. PyPI verifies the GitHub Actions workflow is running from your registered repository.

### 3. Package Name

Ensure `echomine` is available on PyPI or you own it.

## Setup Trusted Publishing

### Step 1: Configure on PyPI

1. Go to [PyPI Publishing Settings](https://pypi.org/manage/account/publishing/)

2. Click **Add a new pending publisher**

3. Fill in the form:
   - **PyPI Project Name**: `echomine`
   - **Owner**: `aucontraire` (your GitHub username)
   - **Repository name**: `echomine`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi` (optional but recommended)

4. Click **Add**

### Step 2: Configure on TestPyPI (Optional)

Repeat for TestPyPI at [TestPyPI Publishing Settings](https://test.pypi.org/manage/account/publishing/):
- **Environment name**: `testpypi`

### Step 3: Verify GitHub Workflow

The workflow (`.github/workflows/release.yml`) should include:

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi  # Must match PyPI config
    permissions:
      id-token: write  # Required for OIDC
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No credentials needed - uses OIDC
```

## Publishing Workflow

### Automatic Publishing (Recommended)

Releases are published automatically when you push a version tag:

```bash
# Create and push tag
git tag v1.2.0
git push origin v1.2.0

# GitHub Actions will:
# 1. Run tests
# 2. Build packages
# 3. Publish to PyPI
# 4. Create GitHub Release
```

### Manual Publishing (Emergency)

If automated publishing fails:

```bash
# Build packages locally
python -m build

# Check packages
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ echomine

# Upload to PyPI
twine upload dist/*
```

**Note**: Manual upload requires API token. Generate at PyPI → Account Settings → API tokens.

## Package Configuration

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "echomine"
version = "1.0.0"
description = "Library-first AI conversation export parser"
readme = "README.md"
license = {text = "AGPL-3.0-or-later"}
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "you@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Text Processing",
    "Typing :: Typed",
]
keywords = ["chatgpt", "openai", "conversation", "export", "parser"]

dependencies = [
    "pydantic>=2.0",
    "ijson>=3.0",
    "typer>=0.9",
    "rich>=13.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "mypy>=1.8",
    "ruff>=0.3",
]

[project.urls]
Homepage = "https://github.com/aucontraire/echomine"
Documentation = "https://aucontraire.github.io/echomine/"
Repository = "https://github.com/aucontraire/echomine"
Changelog = "https://github.com/aucontraire/echomine/blob/main/CHANGELOG.md"

[project.scripts]
echomine = "echomine.cli:app"
```

### Files to Include

Ensure these are included in the package:

```toml
# pyproject.toml
[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/LICENSE",
    "/README.md",
    "/CHANGELOG.md",
]

[tool.hatch.build.targets.wheel]
packages = ["src/echomine"]
```

### Files to Exclude

Automatically excluded:
- `__pycache__/`
- `*.pyc`
- `.git/`
- `tests/`
- `docs/`

## Testing Before Release

### 1. Build Locally

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Check contents
tar -tzf dist/echomine-1.0.0.tar.gz | head -20
unzip -l dist/echomine-1.0.0-py3-none-any.whl | head -20
```

### 2. Validate Package

```bash
# Check package metadata
twine check dist/*

# Should output:
# Checking dist/echomine-1.0.0-py3-none-any.whl: PASSED
# Checking dist/echomine-1.0.0.tar.gz: PASSED
```

### 3. Test on TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    echomine

# Verify
echomine --version
python -c "from echomine import OpenAIAdapter; print('OK')"
```

### 4. Test in Clean Environment

```bash
# Create fresh environment
python -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    echomine

# Run quick test
echomine --help
python -c "from echomine import OpenAIAdapter, SearchQuery; print('All imports OK')"

# Clean up
deactivate
rm -rf test-env
```

## Troubleshooting

### "Project not found" Error

**Cause**: Trusted publisher not configured or repository not public.

**Solution**:
1. Verify PyPI publishing settings
2. Ensure repository is public
3. Check workflow name matches exactly

### "Invalid token" Error

**Cause**: OIDC token generation failed.

**Solution**:
1. Ensure `permissions.id-token: write` in workflow
2. Check environment name matches PyPI config
3. Verify repository owner/name match

### "File already exists" Error

**Cause**: Trying to upload same version again.

**Solution**: PyPI doesn't allow overwriting. Increment version number.

### Package Installs But Import Fails

**Cause**: Package structure issues.

**Solution**:
1. Check `[tool.hatch.build.targets.wheel].packages`
2. Verify `__init__.py` files exist
3. Test with `pip install -e .` first

## Version Yanking

If you need to remove a bad release:

```bash
# Yank (hide from default installs, still downloadable by version)
# Must be done via PyPI web interface:
# 1. Go to https://pypi.org/manage/project/echomine/releases/
# 2. Click on the version
# 3. Click "Options" → "Yank"

# Or via API (requires token)
pip index yank echomine==1.2.0
```

**Note**: Yanking is reversible. For permanent removal, contact PyPI support.

## Security Best Practices

### Do

- Use Trusted Publishing (OIDC) instead of API tokens
- Use environment protection rules in GitHub
- Review workflow changes carefully
- Test on TestPyPI before production

### Don't

- Commit API tokens to repository
- Share API tokens
- Use long-lived tokens when OIDC is available
- Skip TestPyPI testing

## Environment Protection (Optional)

Add protection rules in GitHub:

1. Go to Settings → Environments
2. Create `pypi` environment
3. Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (only `main`)

## Next Steps

- [Release Process](release-process.md): Full release workflow
- [Versioning](versioning.md): Version numbering

---

**Last Updated**: 2025-11-30
