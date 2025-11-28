# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial CHANGELOG.md for tracking releases

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [1.0.0] - 2025-11-28

### Added
- Core library with streaming conversation parser using ijson
- OpenAI ChatGPT export adapter with O(1) memory usage
- BM25-based search with keyword relevance ranking
- Conversation filtering by date, title, and custom criteria
- Markdown export functionality for conversations
- CLI with commands: `list`, `search`, `export`, `validate`
- Pydantic v2 models with strict validation and immutability
- Type-safe API with mypy --strict compliance
- Comprehensive test suite (unit, integration, contract, performance)
- Documentation with mkdocs, API reference, usage guides
- Progress reporting via callbacks for long-running operations
- Graceful degradation for malformed conversation entries
- JSON structured logging with contextlog for debugging
- Library-first architecture (CLI wraps library)
- Multi-provider adapter pattern (protocol-based)
- Performance contracts: 1.6GB search <30s, 10K conversations on 8GB RAM

### Documentation
- README with installation, quick start, usage examples
- CONTRIBUTING.md with TDD workflow, type checking, testing guidelines
- MAINTAINING.md with release process, PyPI publishing, dependency management
- API reference auto-generated from docstrings
- Architecture documentation with design patterns
- Library usage guide with code examples
- CLI usage guide with all command options

### Performance
- Streaming parser handles 1GB+ files without memory issues
- Search performance: <30s for 1.6GB export
- Title-only search: <5s for 10K conversations
- Memory usage: O(1) constant regardless of file size

### Quality Assurance
- Test coverage: >80% overall, >90% critical paths
- mypy --strict: Zero type errors
- ruff: Linting and formatting
- pre-commit hooks: Automated quality checks
- pytest-benchmark: Performance regression testing

---

## Release Types

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: Backward-compatible new features
- **PATCH** version: Backward-compatible bug fixes

## Release Notes Format

Each release includes:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes

---

[Unreleased]: https://github.com/echomine/echomine/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/echomine/echomine/releases/tag/v1.0.0
