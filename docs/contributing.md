# Contributing

Thank you for your interest in contributing to Echomine!

For comprehensive development guidelines, please see:

**[CONTRIBUTING.md](https://github.com/echomine/echomine/blob/main/CONTRIBUTING.md)**

## Quick Links

### Development Setup

1. Clone repository: `git clone https://github.com/echomine/echomine.git`
2. Install dependencies: `pip install -e ".[dev]"`
3. Install hooks: `pre-commit install`
4. Run tests: `pytest`

### Key Guidelines

- **TDD**: Write tests first (RED-GREEN-REFACTOR)
- **Type Safety**: mypy --strict must pass
- **Code Quality**: ruff for linting/formatting
- **Test Coverage**: 80% minimum, 95% for public API

### Common Tasks

```bash
# Run tests with coverage
pytest --cov=echomine --cov-report=term-missing

# Type checking
mypy --strict src/echomine/

# Linting and formatting
ruff check --fix src/ tests/
ruff format src/ tests/

# Pre-commit hooks
pre-commit run --all-files
```

### Pull Request Process

1. Create feature branch
2. Write failing tests (RED)
3. Implement feature (GREEN)
4. Refactor (REFACTOR)
5. Ensure all quality checks pass
6. Submit PR with conventional commit message

### Architecture Principles

1. **Library-First**: Core in library, CLI wraps it
2. **Type Safety**: mypy --strict, no `Any` types
3. **Memory Efficiency**: Streaming, O(1) memory
4. **YAGNI**: Implement only spec requirements

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/echomine/echomine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/echomine/echomine/discussions)
- **Docs**: [Full Documentation](index.md)

---

For complete details, see **[CONTRIBUTING.md](https://github.com/echomine/echomine/blob/main/CONTRIBUTING.md)**.
