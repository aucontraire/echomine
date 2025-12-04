# Development Setup Guide

This guide walks you through setting up a development environment for Echomine.

## Prerequisites

- **Python 3.12+**: Required for modern type hints (PEP 695)
- **Git**: For version control
- **pyenv** (recommended): For managing Python versions

### Verify Python Version

```bash
python --version
# Should output: Python 3.12.x or higher
```

If you need to install Python 3.12+:

```bash
# Using pyenv (recommended)
pyenv install 3.12.2
pyenv local 3.12.2

# Or using homebrew (macOS)
brew install python@3.12
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/aucontraire/echomine.git
cd echomine
```

### 2. Create Virtual Environment

```bash
# Using venv (standard library)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Or using pyenv-virtualenv
pyenv virtualenv 3.12.2 echomine
pyenv activate echomine
```

### 3. Install Dependencies

```bash
# Install in development mode with all dev dependencies
pip install -e ".[dev]"
```

This installs:
- Core dependencies (pydantic, ijson, typer, rich, structlog)
- Development tools (pytest, mypy, ruff, pre-commit)
- Documentation tools (mkdocs, mkdocstrings)

### 4. Install Pre-Commit Hooks

```bash
pre-commit install
```

This enables automatic quality checks on every commit:
- mypy --strict type checking
- ruff linting and formatting
- pytest test execution

### 5. Verify Installation

```bash
# Run tests
pytest --cov=echomine

# Check type safety
mypy --strict src/echomine/

# Check linting
ruff check src/ tests/

# Run CLI
echomine --help
```

All commands should complete without errors.

## IDE Setup

### VS Code (Recommended)

Install these extensions:
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Ruff** (charliermarsh.ruff)

Add to `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "strict",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "ruff.lint.args": ["--config=pyproject.toml"]
}
```

### PyCharm

1. **Set Python Interpreter**: File → Settings → Project → Python Interpreter → Select `.venv`
2. **Enable Type Checking**: File → Settings → Editor → Inspections → Python → Type checker compatibility
3. **Configure Ruff**: File → Settings → Tools → External Tools → Add ruff

## Project Structure

```
echomine/
├── src/echomine/           # Library source code
│   ├── models/             # Pydantic data models
│   ├── protocols/          # Protocol definitions
│   ├── adapters/           # Provider implementations
│   ├── search/             # Search and ranking
│   ├── utils/              # Utilities
│   └── cli/                # CLI commands
├── tests/
│   ├── unit/               # Fast, isolated tests (70%)
│   ├── integration/        # Component interaction (20%)
│   ├── contract/           # Protocol compliance (5%)
│   ├── performance/        # Benchmarks (5%)
│   └── fixtures/           # Test data
├── docs/                   # Documentation (MkDocs)
├── specs/                  # Feature specifications
└── pyproject.toml          # Project configuration
```

## Common Issues

### "Module not found" errors

Ensure you're in the virtual environment:
```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### mypy errors after installation

Clear the mypy cache:
```bash
rm -rf .mypy_cache
mypy --strict src/echomine/
```

### Pre-commit hook failures

Run hooks manually to see detailed output:
```bash
pre-commit run --all-files
```

### Tests failing with fixture errors

Ensure test fixtures exist:
```bash
ls tests/fixtures/sample_export.json
```

If missing, the fixture is generated automatically by pytest.

## Next Steps

- [Development Workflows](workflows.md): Common development patterns
- [Testing Guide](testing.md): Writing and running tests
- [Type Checking](type-checking.md): mypy --strict patterns
- [Contributing](../contributing.md): Contribution guidelines

---

**Last Updated**: 2025-11-30
