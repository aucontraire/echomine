# Installation

## Requirements

- Python 3.12 or higher
- 8GB RAM (for processing large exports)

## Install from PyPI

When published, install using pip:

```bash
pip install echomine
```

## Install from Source

### Clone Repository

```bash
git clone https://github.com/echomine/echomine.git
cd echomine
```

### Basic Installation

For library use only:

```bash
pip install -e .
```

### Development Installation

With all development dependencies (testing, linting, type checking):

```bash
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check CLI works
echomine --version

# Run tests
pytest

# Check type checking
mypy --strict src/echomine/
```

## Pre-commit Hooks (Optional)

Install pre-commit hooks for automatic code quality checks:

```bash
pre-commit install
```

This will run:
- Type checking (mypy --strict)
- Linting and formatting (ruff)
- Tests (pytest)

On every commit.

## Dependencies

### Core Dependencies

- **pydantic** (>=2.6.0): Data validation and type safety
- **ijson** (>=3.2.0): Streaming JSON parser
- **typer** (>=0.9.0): CLI framework
- **rich** (>=13.0.0): Terminal formatting
- **structlog** (>=23.0.0): Structured logging
- **python-slugify** (>=8.0.0): Text slugification
- **python-dateutil** (>=2.8.0): Date parsing utilities

### Development Dependencies

- **pytest** (>=7.4.0): Testing framework
- **pytest-cov** (>=4.1.0): Coverage reporting
- **pytest-mock** (>=3.11.0): Mocking utilities
- **pytest-benchmark** (>=4.0.0): Performance benchmarks
- **psutil** (>=5.9.0): Resource monitoring
- **mypy** (>=1.5.0): Static type checker
- **ruff** (>=0.1.0): Linter and formatter
- **pre-commit** (>=3.4.0): Git hooks

## Troubleshooting

### Python Version Issues

Echomine requires Python 3.12+ for modern type hints. Check your version:

```bash
python --version  # Should show 3.12 or higher
```

### Import Errors

If you see import errors after installation:

```bash
# Reinstall in development mode
pip install -e .

# Or with full dependencies
pip install -e ".[dev]"
```

### Type Checking Errors

Ensure mypy is installed and configured:

```bash
pip install mypy
mypy --strict src/echomine/
```

## Upgrading

### From PyPI

```bash
pip install --upgrade echomine
```

### From Source

```bash
cd echomine
git pull origin master
pip install -e ".[dev]"
```

## Uninstalling

```bash
pip uninstall echomine
```
