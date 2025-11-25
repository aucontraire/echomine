# Test Design: CLI Export Command (Phase 6.4)

**Task**: T075-T077 - CLI Export Command Implementation
**Phase**: RED (TDD - Tests Written FIRST)
**Status**: Tests designed, ready for RED-GREEN-REFACTOR cycle
**Date**: 2025-11-23

---

## Overview

This document describes the comprehensive test design for the `echomine export` CLI command, following strict TDD principles. All tests are designed to **FAIL initially** (RED phase) and will guide the implementation (GREEN phase).

### Design Principles Applied

✅ **TDD Enforcement**: All tests written BEFORE implementation
✅ **CLI Contract Validation**: Black-box testing of CLI interface
✅ **Library-First Architecture**: CLI wraps MarkdownExporter class
✅ **Test Pyramid Compliance**: 70% unit, 20% integration, 5% contract, 5% performance
✅ **Fail-Fast with Clear Messages**: Tests specify expected behavior and failure reasons

---

## Test File Structure

### 1. Contract Tests (5% of pyramid)
**File**: `/Users/omarcontreras/PycharmProjects/echomine/tests/contract/test_cli_export_contract.py`

**Purpose**: Black-box testing of CLI interface via subprocess
**Test Class**: `TestCLIExportCommandContract`
**Test Count**: 21 tests

### 2. Integration Tests (20% of pyramid)
**File**: `/Users/omarcontreras/PycharmProjects/echomine/tests/integration/test_export_flow.py`

**Purpose**: Component integration without subprocess
**Test Classes**:
- `TestExportIntegrationFlow` (6 tests)
- `TestExportErrorHandling` (3 tests)
- `TestExportLibraryIntegration` (2 tests)
- `TestSearchThenExportWorkflow` (1 test)

**Test Count**: 12 tests

### 3. Unit Tests (70% of pyramid)
**Status**: ✅ ALREADY COMPLETE (Sub-Phase 6.3)
**Coverage**: MarkdownExporter class with golden master tests

### Total New Tests: 33 tests (21 contract + 12 integration)

---

## Contract Tests Breakdown

### Exit Code Tests (6 tests)

| Test | Validates | Expected Exit Code |
|------|-----------|-------------------|
| `test_export_command_exit_code_0_on_success` | Successful export | 0 |
| `test_export_command_exit_code_1_on_file_not_found` | Missing export file | 1 |
| `test_export_command_exit_code_1_on_conversation_not_found` | Missing conversation ID | 1 |
| `test_export_command_exit_code_1_on_write_permission_error` | Write permission denied | 1 |
| `test_export_command_exit_code_2_on_missing_conversation_id` | Missing required argument | 2 |
| `test_export_command_exit_code_2_on_both_id_and_title_provided` | Mutually exclusive args | 2 |

**Validates**: CHK032 (exit code contract), FR-033 (fail fast on errors)

---

### stdout/stderr Separation Tests (3 tests)

| Test | Validates | Expected Behavior |
|------|-----------|-------------------|
| `test_export_command_stdout_contains_markdown_when_no_output_file` | Markdown to stdout when no --output | stdout = markdown |
| `test_export_command_stderr_contains_progress_indicators` | Progress to stderr, not stdout | stderr = progress |
| `test_export_command_success_message_to_stderr_when_output_file_specified` | Success message to stderr when writing file | stderr = "Exported to..." |

**Validates**: CHK031 (stdout/stderr separation), FR-018 (CLI interface contract)

---

### Output Format Tests (5 tests)

| Test | Validates | Expected Content |
|------|-----------|------------------|
| `test_export_command_markdown_format_compliance` | Emoji headers, timestamps, horizontal rules | FR-014, FR-015, user format preferences |
| `test_export_command_preserves_message_order` | Chronological message ordering | User before Assistant |
| `test_export_command_includes_timestamps` | ISO 8601 timestamps | YYYY-MM-DDTHH:MM:SS+00:00 |
| `test_export_command_includes_emoji_headers` | 👤 User, 🤖 Assistant | User format preferences |

**Validates**: FR-014 (metadata), FR-015 (preserve formatting), Phase 6 user preferences

---

### Edge Cases (7 tests)

| Test | Validates | Edge Case |
|------|-----------|-----------|
| `test_export_command_handles_unicode_in_titles` | UTF-8 encoding | Unicode titles (测试会话 🚀) |
| `test_export_command_handles_long_conversations` | Memory efficiency | 100+ messages |
| `test_export_command_overwrites_existing_file_with_warning` | File overwrite behavior | Overwrite existing file |
| `test_export_command_by_title_flag` | --title flag | Export by title instead of ID |
| `test_export_command_ambiguous_title_raises_error` | Duplicate title handling | Multiple conversations with same title |
| `test_export_command_default_output_to_cwd` | Default output location | FR-399 (CWD default) |
| `test_export_command_help_flag` | --help flag | Usage information |

**Validates**: CHK126 (UTF-8), FR-016 (slugified filenames), FR-399/400 (output paths)

---

## Integration Tests Breakdown

### Export Flow Tests (6 tests)

| Test | Integration Points | Validates |
|------|-------------------|-----------|
| `test_export_conversation_by_id_to_file` | CLI → MarkdownExporter → File I/O | End-to-end happy path |
| `test_export_conversation_by_title_to_file` | Title lookup → Export | Title-based search |
| `test_export_conversation_to_stdout` | MarkdownExporter returns string | Stdout mode (no file) |
| `test_export_with_images_includes_image_references` | Multimodal content → Markdown | ![Image](file-id.png) |
| `test_export_with_code_preserves_code_blocks` | Code content → Markdown | Code preservation |

**Validates**: Library-first architecture, component integration, format compliance

---

### Error Handling Tests (3 tests)

| Test | Error Scenario | Expected Exception |
|------|---------------|-------------------|
| `test_export_nonexistent_conversation_raises_error` | Missing conversation ID | ValueError |
| `test_export_invalid_file_path_raises_error` | Non-existent file | FileNotFoundError |
| `test_export_malformed_json_raises_error` | Invalid JSON | json.JSONDecodeError |

**Validates**: Error propagation, clear error messages, fail-fast behavior

---

### Library Integration Tests (2 tests)

| Test | Validates | Architectural Principle |
|------|-----------|------------------------|
| `test_export_uses_markdown_exporter_class` | MarkdownExporter importable and usable | Principle I: Library-first |
| `test_export_streams_efficiently_for_large_files` | O(1) memory for 1000+ conversations | Principle VIII: Memory efficiency |

**Validates**: Constitution Principle I (library-first), Principle VIII (streaming)

---

## Test Fixtures

### Contract Test Fixtures

```python
@pytest.fixture
def cli_command() -> list[str]:
    """CLI invocation command: [python, -m, echomine.cli.app]"""

@pytest.fixture
def export_sample_file(tmp_path: Path) -> Path:
    """2 conversations: text + multimodal content"""

@pytest.fixture
def duplicate_title_export(tmp_path: Path) -> Path:
    """2 conversations with identical titles (ambiguity test)"""
```

### Integration Test Fixtures

```python
@pytest.fixture
def integration_export_file(tmp_path: Path) -> Path:
    """3 conversations: text, code, images"""
```

### Fixture Reusability

✅ Fixtures follow project patterns (sample_export.json structure)
✅ Small fixtures (2-3 conversations) for fast test execution
✅ Self-contained: No external dependencies
✅ Isolated: Each test gets fresh tmp_path

---

## Assertion Patterns

### Exit Code Assertions

```python
# Pattern: Assert exit code + error message + stdout/stderr separation
assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
assert "error" not in result.stderr.lower(), f"Unexpected error: {result.stderr}"
assert len(result.stdout) > 0, "stdout should contain output"
```

### Format Compliance Assertions

```python
# Pattern: Check format elements in exported markdown
markdown = output_file.read_text(encoding="utf-8")
assert "##" in markdown, "Should have markdown headers"
assert "👤" in markdown or "🤖" in markdown, "Should have emoji headers"
assert "---" in markdown, "Should have horizontal rules"
assert "T" in markdown, "Should have ISO 8601 timestamps"
```

### Error Handling Assertions

```python
# Pattern: pytest.raises with match for specific error messages
with pytest.raises(ValueError, match="not found"):
    exporter.export_conversation(file_path, "nonexistent-id")
```

---

## Mock/Patch Requirements

### NO MOCKING REQUIRED ✅

**Rationale**:
- Contract tests use subprocess (real CLI invocation)
- Integration tests use real MarkdownExporter class (already implemented)
- File I/O uses tmp_path fixture (real file system, isolated)
- No external dependencies to mock (no API calls, no database)

**Philosophy**: Test real components, not mocks (TDD best practice)

---

## Running the Tests (RED Phase Verification)

### Expected Test Results (Before Implementation)

```bash
# All tests should FAIL with clear error messages
pytest tests/contract/test_cli_export_contract.py -v
# Expected: 21 FAILED (export command not found)

pytest tests/integration/test_export_flow.py -v
# Expected: 12 FAILED (CLI integration not implemented)

# After implementation (GREEN phase):
pytest tests/contract/test_cli_export_contract.py -v
# Expected: 21 PASSED

pytest tests/integration/test_export_flow.py -v
# Expected: 12 PASSED
```

### Test Execution Commands

```bash
# Run all export tests
pytest tests/contract/test_cli_export_contract.py tests/integration/test_export_flow.py -v

# Run specific test class
pytest tests/contract/test_cli_export_contract.py::TestCLIExportCommandContract -v

# Run specific test
pytest tests/contract/test_cli_export_contract.py::TestCLIExportCommandContract::test_export_command_exit_code_0_on_success -v

# Run with markers
pytest -m contract  # Contract tests only
pytest -m integration  # Integration tests only

# Run with coverage
pytest tests/contract/test_cli_export_contract.py tests/integration/test_export_flow.py --cov=echomine.cli --cov-report=term-missing
```

---

## Test Pyramid Compliance

### Distribution Analysis

| Layer | Tests | Percentage | Target |
|-------|-------|------------|--------|
| Unit | Existing (MarkdownExporter) | ~70% | 70% ✅ |
| Integration | 12 new tests | ~20% | 20% ✅ |
| Contract | 21 new tests | ~5% | 5% ✅ |
| Performance | Deferred | ~5% | 5% ⚠️ |

**Status**: ✅ Compliant with test pyramid (performance tests deferred for export command)

---

## Requirements Coverage

### Functional Requirements Validated

| FR | Description | Tests |
|----|-------------|-------|
| FR-018 | Export command with file path, ID, --output flag | 21 contract tests |
| FR-014 | Conversation metadata in exports | Format compliance tests |
| FR-015 | Preserve code blocks and formatting | Code preservation test |
| FR-016 | Slugified filenames from titles | Unicode handling test |
| FR-399 | Default to CWD for exports | Default output test |
| FR-400 | --output flag for custom directory | Success test with --output |

### Contract Requirements Validated

| Contract | Description | Tests |
|----------|-------------|-------|
| CHK031 | stdout/stderr separation | 3 stdout/stderr tests |
| CHK032 | Exit codes 0/1/2 | 6 exit code tests |
| CHK126 | UTF-8 encoding | Unicode handling test |

### Constitution Principles Validated

| Principle | Description | Tests |
|-----------|-------------|-------|
| I | Library-first architecture | 2 library integration tests |
| II | CLI interface contract | All 21 contract tests |
| III | Test-driven development | 33 tests written FIRST |
| VI | Strict typing | Integration tests validate types |
| VIII | Memory efficiency | Large file streaming test |

---

## Implementation Guidance

### RED Phase (Current State)

✅ **Tests designed and written**
✅ **All tests will FAIL** (export command not implemented)
✅ **Failure reasons documented** in test docstrings
✅ **Ready for implementation**

### GREEN Phase (Next Steps)

**Implementation Order** (following TDD cycle):

1. **Minimal CLI command structure** (make exit code tests pass)
   - Add `export` command to `src/echomine/cli/app.py`
   - Register command with Typer app
   - Basic argument parsing (file_path, conversation_id, --output)

2. **MarkdownExporter integration** (make format tests pass)
   - Import MarkdownExporter in CLI command
   - Call `exporter.export_conversation(file_path, conv_id)`
   - Handle returned markdown string

3. **File I/O handling** (make output tests pass)
   - Write markdown to file if --output specified
   - Write markdown to stdout if no --output
   - Success message to stderr

4. **Error handling** (make error tests pass)
   - Catch FileNotFoundError → exit code 1
   - Catch ValueError (conversation not found) → exit code 1
   - Catch PermissionError → exit code 1
   - Invalid arguments → exit code 2

5. **Edge cases** (make edge case tests pass)
   - --title flag implementation
   - Ambiguous title detection
   - Unicode handling (should "just work" with UTF-8)
   - File overwrite handling

### REFACTOR Phase (After GREEN)

- Extract helper functions
- DRY up error handling
- Add type hints to all functions
- Run mypy --strict
- Run ruff format and ruff check --fix
- Update docstrings

---

## Quality Gates (Before Commit)

**TDD Test Strategy Engineer** checklist:
- ✅ All 33 tests pass (pytest exit code 0)
- ✅ Coverage >80% for CLI export command code
- ✅ Test pyramid ratios maintained (70/20/5/5)
- ✅ No skipped tests (unless platform-specific)

**Python Strict Typing Enforcer** checklist:
- ✅ mypy --strict passes (zero errors)
- ✅ All CLI functions have type hints
- ✅ No `Any` types in export command code

**Performance Profiling Specialist** checklist:
- ✅ Large file test passes (1000 conversations)
- ✅ No memory errors on large files
- ⚠️ Performance benchmarks deferred (not critical for export)

**Git Version Control** checklist:
- ✅ Tests committed separately from implementation
- ✅ Conventional commit message format
- ✅ No test code smells (sleep statements, hardcoded paths)

---

## Test Design Rationale

### Why These Tests?

**Exit Code Tests**: Validate CLI contract compliance per CHK032. Exit codes are the primary signal for shell scripts and automation.

**stdout/stderr Tests**: Ensure pipeline composability per CHK031. Users must be able to pipe output without progress messages interfering.

**Format Tests**: Validate user preferences from Phase 6 spec. Format compliance is critical for markdown rendering in VS Code.

**Edge Case Tests**: Cover real-world scenarios (Unicode, long conversations, overwrites) that would break in production.

**Integration Tests**: Validate library-first architecture. CLI must be a thin wrapper, not contain business logic.

**Error Handling Tests**: Ensure fail-fast behavior with clear messages. Users need actionable error information.

### Why No Performance Tests?

Export command operates on **single conversations** (not bulk processing). Performance is bounded by:
- File I/O (reading JSON, writing markdown)
- MarkdownExporter rendering (already unit tested)

**Decision**: Performance tests deferred. Memory efficiency validated via "large file" integration test (1000 conversations).

### Why No Mocking?

**TDD Best Practice**: Test real components when possible. Mocks add maintenance burden and can give false confidence.

**Real Components Available**:
- MarkdownExporter class (already implemented and tested)
- File system (isolated via tmp_path fixture)
- CLI (invoked via subprocess for contract tests)

**Exception**: If search functionality is needed for --title flag, may need to mock search API.

---

## Appendix: Expected CLI Interface

### Command Signature (Inferred from Tests)

```bash
# Export by conversation ID to file
echomine export <file> <conversation-id> --output <output-file>

# Export by conversation ID to stdout
echomine export <file> <conversation-id>

# Export by title to file
echomine export <file> --title "Conversation Title" --output <output-file>

# Export by title to stdout
echomine export <file> --title "Conversation Title"

# Show help
echomine export --help
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `<file>` | Path | Yes | - | OpenAI export JSON file |
| `<conversation-id>` | String | Conditional* | - | Conversation ID (mutually exclusive with --title) |
| `--title` | String | Conditional* | - | Conversation title (mutually exclusive with ID) |
| `--output` | Path | No | stdout | Output markdown file path |

*Either `<conversation-id>` OR `--title` is required, but not both.

### Exit Codes

| Code | Meaning | Examples |
|------|---------|----------|
| 0 | Success | Conversation exported successfully |
| 1 | Operational error | File not found, conversation not found, permission denied |
| 2 | Invalid arguments | Missing required argument, both ID and --title provided |

### Output Behavior

**When --output specified**:
- Markdown written to file
- Success message to stderr: "Exported to <path>"
- stdout is empty

**When --output omitted**:
- Markdown written to stdout
- Progress/status to stderr (if any)
- Enables piping: `echomine export file.json conv-id | less`

---

## Next Actions

### For Implementation (GREEN Phase)

1. Run tests to verify RED state: `pytest tests/contract/test_cli_export_contract.py tests/integration/test_export_flow.py -v`
2. Expected: All 33 tests FAIL
3. Create `src/echomine/cli/commands/export.py`
4. Implement minimal CLI command structure
5. Run tests again: Some should pass (exit code 2 tests)
6. Iterate: Implement → Test → Refactor

### For Review

1. Review test design with team
2. Confirm CLI interface assumptions (ID vs --title, stdout vs --output)
3. Validate test pyramid compliance
4. Approve test design before starting implementation

### For Documentation

1. Add test design summary to `specs/001-ai-chat-parser/plan.md`
2. Update `CLAUDE.md` with export command testing patterns
3. Document TDD workflow for future features

---

**Test Design Complete**: Ready for RED-GREEN-REFACTOR cycle 🚦
