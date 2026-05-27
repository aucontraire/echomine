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

## [1.4.0] - 2026-05-27

### Added

#### Content Fidelity & Asset Resolution

- **Content Type Classification**: Provider-agnostic message categorization across both adapters
  - 7-value vocabulary: `conversational`, `reasoning`, `tool_io`, `system`, `media`, `attachment`, `unknown`
  - OpenAI: 13 raw content types mapped (text, multimodal_text, thoughts, code, image_asset_pointer, etc.)
  - Claude: 6 block types mapped (text, thinking, tool_use, tool_result, voice_note, token_budget)
  - Every message now carries `content_type` and `content_type_category` in metadata
  - Library: `from echomine.models.content_types import classify_content_type, ContentTypeCategory`

- **Category-Artifact Orthogonality**: Consistent rule for mixed-content messages
  - Category reflects the message's conversational role, not what it carries
  - Text + artifact (image, attachment, thinking) → `conversational`
  - Pure artifact (image-only, attachment-only, thinking-only) → artifact's category (`media`, `attachment`, `reasoning`)
  - Symmetric behavior across OpenAI and Claude adapters

- **Asset Resolution**: Resolve OpenAI asset pointers to actual files in export bundles
  - Library: `from echomine.utils.asset_resolver import resolve_asset, ResolvedAsset`
  - Magic-byte detection for PNG, JPEG, WebP, GIF, WAV formats
  - Extracts file ID from `sediment://` and similar URI schemes
  - Returns typed `ResolvedAsset` with path, detected MIME type, and original extension

- **OpenAI Adapter Enhancements**:
  - Tool-authored message classification: messages with `author.role == "tool"` now classified as `tool_io` regardless of content_type (was incorrectly labeled `conversational` for text/multimodal_text tool results, affecting 2,097 of 3,018 tool messages in real-data testing)
  - Multi-part text joining: messages with multiple text parts are joined with newlines (was only using first part)
  - Reasoning metadata: `thoughts` and `reasoning_recap` content extracted into `metadata["thinking"]`
  - Hidden message detection: `metadata["is_hidden"]` flag for system-generated messages
  - Recipient tracking: `metadata["recipient"]` preserved from OpenAI export data
  - Placeholder leak elimination: all non-conversational content types get `content=""` instead of placeholders (`f"[{content_type}]"`, `"[Image]"`)

- **Claude Adapter Enhancements**:
  - Attachment extraction: file attachments parsed into `metadata["attachments"]` with name, type, and content
  - File reference extraction: `metadata["file_references"]` for attached files
  - Thinking block extraction: reasoning content stored in `metadata["thinking"]`
  - Voice note detection: voice_note blocks classified as `conversational`
  - Message-level post-classification: pure thinking/attachment messages get correct category

- **Test Factories**: Shared factory module for test data generation
  - `tests/factories.py` with 6 factory functions for OpenAI and Claude test data
  - Eliminates 200+ lines of repetitive JSON boilerplate across test files
  - `make_openai_message()`, `make_openai_conversation()`, `make_openai_export()`
  - `make_claude_message()`, `make_claude_export()`, `write_export()`

### Changed

- Messages from both adapters now include `content_type` and `content_type_category` in metadata (backward compatible — new keys added to existing metadata dict)
- OpenAI multimodal text messages now join all text parts with newlines instead of spaces
- Claude adapter returns 4-tuple from content block extraction (added thinking and voice_note outputs)

### Upgrade Guide

This release is **fully backward compatible**. No code changes required.

**New metadata fields** (additive, never break existing code):
- `msg.metadata["content_type"]` — raw provider-specific type (e.g., "text", "thinking", "code")
- `msg.metadata["content_type_category"]` — standardized category (e.g., "conversational", "reasoning")
- `msg.metadata["thinking"]` — extracted reasoning/thinking content dict (OpenAI thoughts, Claude thinking blocks)
- `msg.metadata["is_hidden"]` — boolean flag for system-generated hidden messages (OpenAI)
- `msg.metadata["attachments"]` — list of attachment dicts with name, type, content (Claude)
- `msg.metadata["file_references"]` — list of file reference dicts (Claude)

**Behavioral changes** (improved correctness, unlikely to affect consumers):
- OpenAI multi-part text messages now use `"\n"` join instead of only first part — more content, not less
- All non-conversational content types now have `content=""` instead of placeholders (`"[content_type]"`, `"[Image]"`) — cleaner data for downstream consumers

### Documentation

- Complete specification: `specs/005-content-fidelity/spec.md`
- Implementation plan: `specs/005-content-fidelity/plan.md`
- Task breakdown: `specs/005-content-fidelity/tasks.md`
- Content fidelity design: `CONTENT_FIDELITY_AND_ASSETS.md`

### Quality Metrics

- Test coverage: 95.85% line, 94.21% branch (1435 passed, 7 skipped)
- mypy --strict: 0 errors across 136 source and test files
- ruff check: All passed
- Cross-provider content fidelity integration tests validate symmetric behavior

## [1.3.0] - 2025-12-10

### Added

#### Multi-Provider Support: Anthropic Claude

- **ClaudeAdapter**: Full-featured adapter for Anthropic Claude conversation exports
  - Library: `from echomine import ClaudeAdapter`
  - Streaming parser with O(1) memory usage (same performance as OpenAI adapter)
  - Supports all core operations: stream_conversations, search, get_conversation_by_id, get_message_by_id
  - Handles Claude-specific export schema (chat_messages, content blocks, tool use)
  - Graceful handling of empty conversations and malformed entries

- **Auto-Detection**: Automatic provider detection from export file structure
  - Library: `from echomine.cli.provider import detect_provider, get_adapter`
  - Inspects JSON structure to identify provider (chat_messages → Claude, mapping → OpenAI)
  - Zero-configuration usage - works automatically in all CLI commands
  - O(1) memory usage (streams first conversation only)

- **Provider Selection Flag**: Explicit provider control across all CLI commands
  - CLI: `--provider {openai,claude}` flag on list, search, get, export, stats commands
  - Bypasses auto-detection for faster startup or ambiguous exports
  - Backwards compatible - auto-detection used when flag omitted

#### Claude Export Format Support

- **Field Mappings**: Claude export schema mapped to unified Conversation model
  - uuid → id (conversation and message identifiers)
  - name → title (with "(No title)" fallback for empty names)
  - chat_messages → messages (flat message array structure)
  - sender ("human"/"assistant") → role ("user"/"assistant")

- **Content Block Extraction**: Intelligent handling of Claude's multi-block content structure
  - Extracts text from content[type=text] blocks
  - Skips tool_use and tool_result blocks (tool invocations ignored)
  - Fallback to text field if content blocks empty
  - Multi-block concatenation with newline separator

- **Timestamp Handling**: Timezone-aware parsing with fallback strategy
  - Parses ISO 8601 timestamps with Z suffix (Zulu/UTC)
  - Message timestamps fall back to conversation created_at if missing
  - All timestamps normalized to UTC

- **Empty Conversation Support**: Graceful handling of zero-message conversations
  - Placeholder message inserted to satisfy Conversation model constraints
  - Marked with is_placeholder metadata flag
  - Prevents validation errors while maintaining data integrity

### Changed

- All CLI commands now support both OpenAI and Claude exports via auto-detection
- Library exports updated: `from echomine import ClaudeAdapter` now available
- Provider detection integrated into CLI command initialization

### Documentation

- Complete specification: `specs/004-claude-adapter/spec.md`
- Implementation plan: `specs/004-claude-adapter/plan.md`
- Task breakdown: `specs/004-claude-adapter/tasks.md`
- Library API contracts: `specs/004-claude-adapter/contracts/library_api.md`
- CLI contracts: `specs/004-claude-adapter/contracts/cli_spec.md`
- Quickstart guide: `specs/004-claude-adapter/quickstart.md`

### Quality Metrics

- Test coverage: 95%+ on ClaudeAdapter code paths
- mypy --strict: 0 errors
- ruff check: All passed
- Added 80+ new tests for Claude parsing, provider detection, and CLI integration
- Contract tests validate Claude export schema compliance

## [1.2.0] - 2025-12-07

### Added

#### New Commands

- **Stats Command**: Generate comprehensive conversation statistics
  - CLI: `echomine stats export.json`
  - Library: `calculate_statistics(file_path)`
  - Displays total conversations, messages, date ranges, word counts, and author analysis
  - Rich terminal output with formatted tables and statistics panels
  - JSON output support via `--json` flag

- **Get Command**: Retrieve and display individual conversations by ID
  - CLI: `echomine get export.json <conversation-id>`
  - Library: Already available via `OpenAIAdapter.stream_conversations()`
  - Rich terminal output with syntax highlighting
  - Multiple output formats: full, summary, messages-only via `--display` flag
  - JSON output support via `--json` flag

#### Export Enhancements

- **CSV Export**: Export conversations to CSV format
  - CLI: `echomine export export.json --format csv --output output.csv`
  - Library: `CSVExporter().export_conversation()`
  - Customizable field selection via `--fields` flag
  - Supports all conversation and message fields
  - Configurable delimiter and quoting options

- **YAML Frontmatter**: Markdown exports now include YAML frontmatter
  - Automatically includes: title, created date, updated date, message count, participants
  - Configurable metadata fields
  - Compatible with static site generators and markdown processors

#### Rich CLI Formatting

- **Color-Coded Output**: All commands use Rich library for enhanced terminal display
  - Syntax highlighting for code blocks and conversation content
  - Color-coded message roles (user, assistant, system)
  - Formatted tables with automatic column sizing
  - Progress bars for long-running operations

- **Enhanced List Output**: Improved conversation list display
  - Sortable columns: created, updated, messages, title
  - Compact and expanded view modes
  - Better date formatting and message count display

- **Enhanced Search Output**: Improved search results display
  - Highlighted matching snippets
  - Relevance score visualization
  - Sortable results with multiple criteria

#### New Data Models

- **Statistics Models**: New Pydantic models for statistics data
  - `ExportStatistics`: Overall export statistics
  - `ConversationStatistics`: Per-conversation statistics
  - `ConversationSummary`: Summary information
  - `RoleCount`: Message count by author role
  - `ExportMetadata`: Export file metadata

#### Library API Enhancements

- **Statistics Functions**: New public API for statistics calculation
  - `calculate_statistics()`: Calculate export-level statistics
  - `calculate_conversation_statistics()`: Calculate per-conversation statistics
  - Streaming-based with O(1) memory usage
  - Full type safety with Pydantic models

### Changed

- CLI exception handling now uses Rich error formatting for better readability
- Golden master tests updated with YAML frontmatter in expected outputs
- Export date formatting normalized across all output formats
- List command default output now uses Rich tables instead of plain text

### Fixed

- Fixed 4 golden master tests by adding date normalization helper
- Fixed failing CLI exception test to accept Rich error formatting
- Fixed ruff linting issues (unused imports, else-if patterns)
- Fixed edge cases in validation error handling paths

### Documentation

- Complete specification: `specs/003-baseline-enhancements/spec.md`
- Implementation plan: `specs/003-baseline-enhancements/plan.md`
- Task breakdown: `specs/003-baseline-enhancements/tasks.md`
- Library API contracts: `specs/003-baseline-enhancements/contracts/library_api.md`
- CLI contracts: `specs/003-baseline-enhancements/contracts/cli_spec.md`
- Quickstart guide: `specs/003-baseline-enhancements/quickstart.md`

### Quality Metrics

- Test coverage: 91.72% (1136 passed, 7 skipped, 0 failed)
- mypy --strict: 0 errors
- ruff check: All passed
- Added 40+ new tests for Rich formatting and validation error paths

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

[Unreleased]: https://github.com/aucontraire/echomine/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/aucontraire/echomine/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/aucontraire/echomine/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/aucontraire/echomine/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/aucontraire/echomine/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/aucontraire/echomine/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/aucontraire/echomine/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/aucontraire/echomine/releases/tag/v1.0.0
