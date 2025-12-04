# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- N/A

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

## [1.1.0] - 2025-12-04

### Added

#### Advanced Search Features (5 User Stories)

- **Exact Phrase Matching (US1, FR-001-006)**: Search for exact phrases like "algo-insights"
  - CLI: `--phrase "algo-insights"`
  - Library: `SearchQuery(phrases=["algo-insights"])`
  - Preserves hyphens, underscores, and special characters
  - Multiple phrases use OR logic

- **Boolean Match Mode (US2, FR-007-011)**: Control keyword matching logic
  - CLI: `--match-mode all` or `--match-mode any`
  - Library: `SearchQuery(keywords=["python", "async"], match_mode="all")`
  - "all" = AND logic (all keywords must be present)
  - "any" = OR logic (default, at least one keyword)

- **Exclude Keywords (US3, FR-012-016)**: Filter out unwanted results
  - CLI: `--exclude "django" --exclude "flask"`
  - Library: `SearchQuery(keywords=["python"], exclude_keywords=["django"])`
  - Excluded terms use OR logic (any excluded term removes result)

- **Role Filtering (US4, FR-017-020)**: Search by message author role
  - CLI: `--role user` or `--role assistant`
  - Library: `SearchQuery(keywords=["refactor"], role_filter="user")`
  - Supports: "user", "assistant", "system"
  - Case-insensitive role matching

- **Message Snippets (US5, FR-021-025)**: Preview matched content
  - Automatically included in all search results
  - `SearchResult.snippet` field shows ~100 character preview
  - Truncated with "..." suffix for long content
  - Multiple matches show "+N more" indicator
  - Fallback text for empty/malformed content

#### New Tests
- Combined feature integration tests (10 tests)
- Advanced search performance benchmarks (7 tests)
- Snippet extraction unit tests (18 tests)
- Role filtering contract tests (6 tests)

### Changed
- SearchQuery model extended with new optional fields
- SearchResult model includes snippet field
- CLI search output includes Snippet column
- JSON output includes snippet field in results

### Documentation
- Quickstart guide for advanced search features
- Library API examples for all new features
- CLI usage examples with all new flags

## [1.0.2] - 2025-12-03

### Added
- JSON export format via `--format json` flag in CLI export command
- Contract tests for JSON export functionality (5 new tests)
- GitHub release template for consistent release notes

### Changed
- Documentation updated with JSON export examples (README, CLI usage, quickstart)

### Fixed
- Windows CI timing-sensitive performance tests (added platform-specific skips)
- License consistency across all project files (corrected to AGPL-3.0)

## [1.0.1] - 2025-12-02

### Fixed
- License declaration corrected from MIT to AGPL-3.0 across all files
- Removed obsolete REMAINING_WORK.md documentation

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

[Unreleased]: https://github.com/aucontraire/echomine/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/aucontraire/echomine/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/aucontraire/echomine/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/aucontraire/echomine/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/aucontraire/echomine/releases/tag/v1.0.0
