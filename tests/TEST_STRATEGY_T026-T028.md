# Test Strategy: User Story 0 - List All Conversations

**Phase**: RED (Pre-Implementation)
**Tasks**: T026, T027, T028
**Status**: TESTS DESIGNED TO FAIL
**Date**: 2025-11-22

---

## Executive Summary

This document outlines the comprehensive failing test strategy for User Story 0 (List All Conversations) following strict TDD RED-GREEN-REFACTOR principles. All tests are **designed to fail initially** (RED phase) and will guide implementation during the GREEN phase.

### Test Coverage Summary

| Task | Test Type | File | Test Count | Status |
|------|-----------|------|------------|--------|
| T026 | Integration | `tests/integration/test_list_flow.py` | 11 tests | RED (FAIL) |
| T027 | Contract | `tests/contract/test_cli_contract.py` | 14 tests | RED (FAIL) |
| T028 | Performance | `tests/performance/test_list_benchmark.py` | 9 tests | RED (FAIL) |
| **TOTAL** | **3 types** | **3 files** | **34 tests** | **RED** |

---

## Test Pyramid Compliance

Per echomine test pyramid requirements:

- **Unit Tests**: 70% (not in this phase - will test individual components later)
- **Integration Tests**: 20% → **T026 provides integration coverage**
- **Contract Tests**: 5% → **T027 validates CLI contract**
- **Performance Tests**: 5% → **T028 establishes benchmarks**

This phase focuses on integration, contract, and performance tests that will drive implementation. Unit tests will be added as individual components are developed.

---

## T026: Integration Tests - End-to-End List Workflow

**File**: `/Users/omarcontreras/PycharmProjects/echomine/tests/integration/test_list_flow.py`

### Purpose
Validate the complete chain: **File → Parser → Adapter → Models**

Tests the integration of:
- Streaming JSON parser (ijson)
- OpenAIAdapter transformation layer
- Conversation model immutability
- Error handling (malformed JSON, missing fields, file I/O)

### Test Scope

#### 11 Integration Tests:

1. **test_list_all_conversations_from_realistic_export**
   - Validates: FR-018 (list all conversations), FR-003 (streaming), FR-222-227 (immutability)
   - Data: 10 conversations with realistic OpenAI structure
   - Verifies: Correct parsing, Unicode handling, long titles

2. **test_stream_conversations_is_lazy_iterator**
   - Validates: FR-003 (O(1) memory via lazy streaming)
   - Verifies: Returns iterator, not list (lazy evaluation)

3. **test_empty_export_yields_no_conversations**
   - Validates: Edge case handling
   - Verifies: Empty file succeeds (returns zero results, not error)

4. **test_conversations_are_immutable**
   - Validates: FR-222 (frozen=True immutability)
   - Verifies: Pydantic frozen model behavior

5. **test_message_count_is_accurate**
   - Validates: FR-018 (metadata includes message count)
   - Verifies: Counting logic for various conversation structures

6. **test_timestamps_are_parsed_correctly**
   - Validates: FR-222 (datetime conversion, UTC timezone)
   - Verifies: Unix timestamp → datetime transformation

7. **test_invalid_json_raises_parse_error**
   - Validates: FR-033 (fail fast on invalid JSON)
   - Verifies: ParseError exception handling

8. **test_missing_required_field_raises_validation_error**
   - Validates: Pydantic validation enforcement
   - Verifies: ValidationError for schema violations

9. **test_file_not_found_raises_error**
   - Validates: FR-033 (proper error handling)
   - Verifies: FileNotFoundError for missing files

10. **test_large_message_content_does_not_break_parsing**
    - Validates: FR-003 (handles large individual messages)
    - Data: 1MB message content
    - Verifies: No memory issues with large content

### Realistic Fixtures

**Built-in Fixture**: `realistic_openai_export` (10 conversations)

Includes edge cases:
- Simple Q&A (2 messages)
- Multi-turn threading (5 messages)
- Long titles (>100 chars)
- Unicode content (Chinese, emojis: "学习中文编程 🇨🇳")
- Code blocks in messages
- Various threading patterns

### Expected Failure Reasons (RED Phase)

- `ModuleNotFoundError: No module named 'echomine.adapters'`
- `OpenAIAdapter` class doesn't exist
- `stream_conversations()` method not implemented
- `Conversation` model incomplete
- Exception classes (`ParseError`, `ValidationError`) not defined

### Success Criteria (GREEN Phase)

All 11 tests pass when:
- OpenAIAdapter implemented with streaming parser
- Conversation models validated via Pydantic
- Error handling implemented
- Immutability enforced via `frozen=True`

---

## T027: CLI Contract Tests - List Command Interface

**File**: `/Users/omarcontreras/PycharmProjects/echomine/tests/contract/test_cli_contract.py`

### Purpose
Validate CLI interface contract compliance per `cli_spec.md`

These are **BLACK BOX tests** - invoke CLI as subprocess and validate external behavior.

### Contract Requirements Validated

- **CHK031**: stdout/stderr separation (data on stdout, progress on stderr)
- **CHK032**: Exit codes (0=success, 1=error, 2=invalid input)
- **FR-018**: Human-readable output format
- **FR-019**: Pipeline-friendly output (grep, awk, head)

### Test Scope

#### 14 Contract Tests:

**Success Path Tests:**
1. **test_stdout_contains_conversation_data_on_success**
   - Validates: CHK031 (data goes to stdout)
   - Verifies: Conversation titles appear in stdout

2. **test_stderr_used_for_progress_indicators**
   - Validates: CHK031 (progress on stderr, not stdout)
   - Verifies: No progress keywords in stdout

3. **test_exit_code_0_on_success**
   - Validates: CHK032 (exit code 0 for success)

**Error Handling Tests:**
4. **test_exit_code_1_on_file_not_found**
   - Validates: CHK032 (exit 1), FR-033 (clear error messages)

5. **test_exit_code_2_on_invalid_arguments**
   - Validates: CHK032 (exit 2 for invalid input)

6. **test_exit_code_1_on_invalid_json**
   - Validates: CHK032, FR-033 (fail fast on parse errors)

**Output Format Tests:**
7. **test_human_readable_output_format**
   - Validates: FR-018, CHK040 (simple text table)
   - Verifies: Table structure with ID, Title, Messages columns

8. **test_pipeline_friendly_output**
   - Validates: FR-019, CHK040 (Unix composability)
   - Tests: `head`, `grep`, `wc` pipeline integration

9. **test_json_output_format_flag**
   - Validates: CLI spec (--format json)
   - Verifies: Valid JSON array output

**Edge Cases:**
10. **test_empty_file_succeeds_with_zero_conversations**
    - Validates: Empty file handling (exit 0, not error)

11. **test_help_flag_displays_usage**
    - Validates: --help flag behavior

12. **test_unicode_in_output_does_not_break_display**
    - Validates: CHK126 (UTF-8 encoding)

13. **test_absolute_and_relative_paths_work**
    - Validates: Path handling (pathlib compatibility)

14. **test_permission_denied_error_handling**
    - Validates: FR-033 (permission error messages)
    - Note: Skipped on Windows

### Sample Fixture

**Built-in Fixture**: `sample_cli_export` (3 conversations)

Smaller dataset for faster CLI testing:
- 3 conversations with varied message counts
- Realistic OpenAI structure
- Sufficient for contract validation

### Expected Failure Reasons (RED Phase)

- `ModuleNotFoundError: No module named 'echomine.cli'`
- CLI entry point doesn't exist
- `list` command not implemented
- Argument parsing not implemented
- Output formatting not implemented
- Exit code handling not implemented

### Success Criteria (GREEN Phase)

All 14 tests pass when:
- CLI entry point (`echomine.cli.app`) exists
- `list` command implemented with correct arguments
- stdout/stderr separation enforced
- Exit codes (0, 1, 2) properly returned
- Human-readable table format implemented
- JSON format flag (`--format json`) works
- Pipeline compatibility verified

---

## T028: Performance Benchmarks - 10K Conversation Listing

**File**: `/Users/omarcontreras/PycharmProjects/echomine/tests/performance/test_list_benchmark.py`

### Purpose
Validate performance requirements and establish baseline metrics

Uses:
- **pytest-benchmark**: Throughput and latency metrics
- **tracemalloc**: Memory profiling (Python stdlib)
- **time.perf_counter**: High-resolution timing

### Performance Requirements Validated

- **FR-444**: Parse 10K conversations in <5 seconds
- **FR-069**: Progress callback frequency ≥100 items (CHK135)
- **SC-001**: Memory usage <1GB on 8GB machines
- **CHK025**: Establish P50, P95, P99 latency baselines
- **CHK108**: Latency per operation type (parse, transform, format)
- **CHK007**: Memory bounds (550MB worst-case)

### Test Scope

#### 9 Performance Tests:

**Throughput Tests:**
1. **test_list_10k_conversations_under_5_seconds** (benchmark)
   - Validates: FR-444 (<5s for 10K conversations)
   - Metrics: min, max, mean, median, stddev, ops/second
   - Threshold: `benchmark.stats.mean < 5.0`

**Memory Efficiency Tests:**
2. **test_streaming_memory_efficiency_10k_conversations**
   - Validates: FR-003 (O(1) memory), SC-001 (<1GB), CHK007 (550MB)
   - Uses: tracemalloc for peak memory tracking
   - Samples memory every 1000 conversations
   - Thresholds:
     - Peak <1GB (SC-001)
     - Peak <600MB (CHK007 architectural bounds)

3. **test_streaming_is_lazy_not_eager**
   - Validates: FR-003 (lazy streaming, not buffering)
   - Measures: Time to get iterator vs time to consume
   - Threshold: Get iterator <100ms (near-instant)
   - Ratio: Consume/get >10x (proves laziness)

**Progress Callback Tests:**
4. **test_progress_callback_frequency**
   - Validates: FR-069, CHK135 (update every 100 items)
   - Verifies: ~100 callbacks for 10K conversations
   - Checks: Incremental counts, final count = 10000

5. **test_batch_size_constraint**
   - Validates: CHK007 (MAX_BATCH_SIZE = 100)
   - Verifies: Consistent batching intervals
   - Uses: Coefficient of variation (CV) <1.0

**Latency Breakdown Tests (CHK108):**
6. **test_json_parsing_latency** (benchmark)
   - Measures: Raw ijson parsing latency
   - Reports: Throughput (conversations/s)

7. **test_model_transformation_latency** (benchmark)
   - Measures: Parse + Pydantic transformation latency
   - Reports: End-to-end throughput

8. **test_end_to_end_latency_percentiles**
   - Validates: CHK025 (P50, P95, P99 baselines)
   - Runs: 10 iterations
   - Reports: P50, P95, P99, min, max
   - Threshold: P99 <5s (FR-444)

**Stress Tests:**
9. **test_50k_conversation_stress_test** (marked `@pytest.mark.slow`)
   - Validates: Scalability beyond baseline (10x FR-444)
   - Data: 50,000 conversations
   - Skipped in regular runs (run with `pytest -m slow`)

### Large Fixture Generation

**Module-Scoped Fixture**: `large_export_10k`

- **Size**: 10,000 conversations, 50,000 messages
- **Scope**: `module` (generate once, reuse across tests)
- **Generation time**: ~10-30 seconds
- **File size**: ~10-15 MB
- **Structure**: Realistic OpenAI format with threading

Progress indicator shows generation status:
```
Generated 2000/10000 conversations for benchmark...
Generated 4000/10000 conversations for benchmark...
...
Generated benchmark fixture: 12.45 MB
```

### Expected Failure Reasons (RED Phase)

- Implementation doesn't exist
- Performance requirements not met initially
- Memory usage exceeds limits
- Progress callbacks not implemented
- Batching logic not implemented

### Success Criteria (GREEN Phase)

All 9 tests pass when:
- List operation completes in <5s for 10K conversations
- Memory usage stays <1GB (ideally <600MB)
- Streaming is lazy (iterator creation <100ms)
- Progress callbacks fire every 100 items
- Batching respects MAX_BATCH_SIZE
- P50, P95, P99 latencies documented
- Stress test (50K) passes with acceptable performance

---

## Running the Tests

### RED Phase Verification (Current State)

**All tests should FAIL:**

```bash
# Integration tests (expect import errors)
pytest tests/integration/test_list_flow.py -v

# Contract tests (expect CLI module not found)
pytest tests/contract/test_cli_contract.py -v

# Performance tests (expect import errors)
pytest tests/performance/test_list_benchmark.py -v
```

**Expected Output**:
```
ModuleNotFoundError: No module named 'echomine.adapters'
ModuleNotFoundError: No module named 'echomine.cli'
```

### GREEN Phase (After Implementation)

**Run by test type:**

```bash
# Integration tests only
pytest tests/integration/ -v

# Contract tests only
pytest tests/contract/ -v

# Performance benchmarks (without slow tests)
pytest tests/performance/ -v -m "not slow"

# All benchmarks with detailed output
pytest tests/performance/ -v --benchmark-only

# Stress tests (explicit opt-in)
pytest tests/performance/ -v -m slow
```

**Run by marker:**

```bash
# Integration tests
pytest -m integration

# Contract tests
pytest -m contract

# Performance tests
pytest -m performance
```

**Full test suite:**

```bash
# All T026-T028 tests
pytest tests/integration/ tests/contract/ tests/performance/ -v
```

### Performance Benchmark Reports

**Generate detailed benchmark reports:**

```bash
# JSON report
pytest tests/performance/ --benchmark-only --benchmark-json=benchmark_results.json

# HTML report (if plugin installed)
pytest tests/performance/ --benchmark-only --benchmark-histogram=benchmark_histogram.svg

# Compare with baseline (after establishing initial metrics)
pytest tests/performance/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

---

## Test Data Requirements

### Integration Test Fixtures

**Location**: Embedded in `test_list_flow.py` fixtures

1. **realistic_openai_export** (10 conversations):
   - Simple Q&A (2 messages)
   - Multi-turn threading (5 messages)
   - Long title (>100 chars)
   - Unicode content (Chinese, emojis)
   - Code blocks
   - Total: ~15 KB

2. **empty_openai_export**: Valid JSON array `[]`

3. **Malformed fixtures** (in tests):
   - Invalid JSON syntax
   - Missing required fields
   - Large message content (1MB)

### Contract Test Fixtures

**Location**: Embedded in `test_cli_contract.py` fixtures

1. **sample_cli_export** (3 conversations):
   - Minimal valid structure
   - Fast test execution
   - Total: ~2 KB

### Performance Test Fixtures

**Location**: Generated dynamically in module-scoped fixture

1. **large_export_10k** (10,000 conversations):
   - Auto-generated on first test run
   - Cached for module duration
   - 5 messages per conversation
   - Total: ~10-15 MB

**Manual Generation** (optional):

```bash
# Generate 10K baseline
python tests/fixtures/generate_large_export.py --conversations 10000 --messages-per-conversation 5

# Generate 50K stress test
python tests/fixtures/generate_large_export.py --conversations 50000 --output tests/fixtures/stress_50k.json
```

---

## Checklist Requirements Mapping

### CHK031: stdout/stderr Separation

**Validated by**:
- T027: `test_stdout_contains_conversation_data_on_success`
- T027: `test_stderr_used_for_progress_indicators`

**Requirements**:
- Data output → stdout (machine-readable)
- Progress/status → stderr (human-readable)
- Errors → stderr

### CHK032: Exit Code Requirements

**Validated by**:
- T027: `test_exit_code_0_on_success`
- T027: `test_exit_code_1_on_file_not_found`
- T027: `test_exit_code_2_on_invalid_arguments`
- T027: `test_exit_code_1_on_invalid_json`

**Requirements**:
- 0 = Success (including empty results)
- 1 = Error (file not found, parse error, permission denied)
- 2 = Invalid input (missing arguments, invalid flags)

### CHK025: Performance Thresholds (P50, P95, P99)

**Validated by**:
- T028: `test_list_10k_conversations_under_5_seconds` (establishes P50)
- T028: `test_end_to_end_latency_percentiles` (measures P50, P95, P99)

**Requirements**:
- Baselines established empirically during first GREEN run
- Regression detection via `--benchmark-compare`

### CHK108: Latency Requirements per Operation

**Validated by**:
- T028: `test_json_parsing_latency` (ijson parse latency)
- T028: `test_model_transformation_latency` (Pydantic transform latency)
- T028: `test_end_to_end_latency_percentiles` (complete operation latency)

**Requirements**:
- Document individual operation latencies
- Identify bottlenecks for optimization

### CHK040: Human-Readable Format

**Validated by**:
- T027: `test_human_readable_output_format`
- T027: `test_pipeline_friendly_output`
- T027: `test_json_output_format_flag`

**Requirements**:
- Default: Simple text table (no Rich dependency)
- Alternative: JSON format via `--format json`
- Pipeline-friendly (works with grep, awk, head)

### CHK135: Progress Indicator Threshold

**Validated by**:
- T028: `test_progress_callback_frequency`

**Requirements**:
- Update interval: 100 conversations (PROGRESS_UPDATE_INTERVAL)
- ~100 callbacks for 10K conversations

### FR-444: Performance Baseline

**Validated by**:
- T028: `test_list_10k_conversations_under_5_seconds`
- T028: `test_end_to_end_latency_percentiles` (P99 <5s)

**Requirements**:
- Parse 10,000 conversations in <5 seconds
- P99 latency <5s (99% of operations complete within 5s)

### FR-069: Progress Callback Frequency

**Validated by**:
- T028: `test_progress_callback_frequency`

**Requirements**:
- Callback invoked every 100 items (CHK135)
- Provides user feedback during long operations

### SC-001: Memory Efficiency

**Validated by**:
- T028: `test_streaming_memory_efficiency_10k_conversations`

**Requirements**:
- Peak memory <1GB for 10K conversations
- Architectural bounds <600MB (CHK007)

### CHK007: Memory Bounds

**Validated by**:
- T028: `test_streaming_memory_efficiency_10k_conversations`
- T028: `test_batch_size_constraint`

**Requirements**:
- MAX_PARSER_STATE_MEMORY = 50MB
- MAX_CONVERSATION_OVERHEAD = 5MB
- MAX_BATCH_SIZE = 100
- Worst-case: 550MB (100 conversations × 5MB + 50MB)

---

## RED-GREEN-REFACTOR Workflow

### Current Phase: RED

**Status**: All 34 tests FAIL (expected)

**Verification**:
```bash
pytest tests/integration/ tests/contract/ tests/performance/ -v 2>&1 | grep -E "(FAILED|ERROR|passed)"
```

**Expected**:
- 0 passed
- 34 failed or error

### Next Phase: GREEN

**Objective**: Implement minimal code to pass tests

**Implementation Order** (recommended):

1. **Core Models** (enables T026 integration tests):
   - `src/echomine/models/conversation.py` (Conversation, Message models)
   - `src/echomine/exceptions.py` (ParseError, ValidationError)

2. **OpenAI Adapter** (enables T026):
   - `src/echomine/adapters/__init__.py`
   - `src/echomine/adapters/openai.py` (OpenAIAdapter with streaming)

3. **CLI Foundation** (enables T027):
   - `src/echomine/cli/__init__.py`
   - `src/echomine/cli/app.py` (Typer CLI entry point)
   - `src/echomine/cli/commands/list.py` (list command)

4. **Output Formatting** (enables T027):
   - `src/echomine/cli/formatters.py` (table and JSON formatters)

5. **Performance Optimization** (enables T028):
   - Verify streaming implementation
   - Add progress callbacks
   - Optimize memory usage

**Test-Driven Development Loop**:
```bash
# 1. Run specific failing test
pytest tests/integration/test_list_flow.py::TestListConversationsIntegration::test_list_all_conversations_from_realistic_export -v

# 2. Implement minimal code to pass test

# 3. Re-run test (should turn GREEN)
pytest tests/integration/test_list_flow.py::TestListConversationsIntegration::test_list_all_conversations_from_realistic_export -v

# 4. Move to next failing test
```

### Final Phase: REFACTOR

**Objective**: Improve code quality while maintaining GREEN tests

**Refactoring Opportunities**:
- Extract common parsing logic
- Optimize performance hotspots
- Improve error messages
- Add docstrings and type hints
- Simplify complex conditionals

**Safety Net**:
```bash
# Run full test suite after each refactor
pytest tests/ -v

# Ensure no regressions
pytest --lf  # Run last failed tests
```

---

## Test Maintenance

### Adding New Tests

**Integration Tests**:
```python
@pytest.mark.integration
def test_new_integration_scenario(realistic_openai_export: Path) -> None:
    """Test description."""
    # Arrange, Act, Assert
```

**Contract Tests**:
```python
@pytest.mark.contract
def test_new_cli_contract(cli_command: list[str], sample_cli_export: Path) -> None:
    """Test CLI contract requirement."""
    # Black box subprocess testing
```

**Performance Tests**:
```python
@pytest.mark.performance
def test_new_performance_metric(large_export_10k: Path, benchmark: Any) -> None:
    """Benchmark new operation."""
    # Use pytest-benchmark
```

### Updating Fixtures

**Modify realistic export**:
- Edit `realistic_openai_export` fixture in `test_list_flow.py`
- Add new edge cases as needed

**Regenerate large fixture**:
```bash
python tests/fixtures/generate_large_export.py --conversations 10000
```

### Performance Baseline Updates

**After significant optimizations**:

1. Run benchmarks and save new baseline:
```bash
pytest tests/performance/ --benchmark-only --benchmark-save=baseline_v2
```

2. Update constants in `src/echomine/constants.py` if thresholds change

3. Document baseline changes in commit message

---

## Coverage Analysis

### Expected Coverage (After GREEN Phase)

**Integration Tests (T026)**:
- OpenAIAdapter: 100%
- Conversation/Message models: 100%
- Exception handling: 100%
- Streaming parser integration: 100%

**Contract Tests (T027)**:
- CLI entry point: 100%
- List command: 100%
- Output formatters: 100%
- Error handling: 100%

**Performance Tests (T028)**:
- Full integration path (no new coverage, validates performance)

**Run coverage report**:
```bash
pytest tests/integration/ tests/contract/ --cov=echomine --cov-report=html
open htmlcov/index.html
```

### Coverage Gaps

After GREEN phase, add **unit tests** for:
- Individual model validators
- Parsing edge cases
- Formatter edge cases
- Error message formatting

**Target**: 90%+ overall coverage

---

## Troubleshooting

### Tests Won't Collect

**Error**: `ImportError while importing test module`

**Solution**: Ensure project installed in editable mode:
```bash
pip install -e .
```

### Performance Tests Too Slow

**Problem**: Fixture generation takes too long

**Solution**: Use smaller dataset for development:
```python
# In large_export_10k fixture, change:
for i in range(1000):  # Instead of 10000
```

**Note**: Restore to 10000 before committing

### Benchmark Results Inconsistent

**Problem**: High variance in benchmark runs

**Solution**:
1. Close background applications
2. Run on AC power (not battery)
3. Increase min_rounds:
```bash
pytest tests/performance/ --benchmark-min-rounds=10
```

### Memory Tests Fail

**Problem**: `tracemalloc` shows high memory usage

**Solution**:
1. Verify streaming implementation (not buffering)
2. Check for memory leaks (object references)
3. Profile with `memory_profiler`:
```bash
pip install memory_profiler
mprof run python -c "from echomine.adapters.openai import OpenAIAdapter; list(OpenAIAdapter().stream_conversations('large.json'))"
mprof plot
```

---

## Success Metrics

### RED Phase (Current)

- ✅ All 34 tests written
- ✅ All tests FAIL as expected
- ✅ Comprehensive coverage of requirements
- ✅ Realistic test data created

### GREEN Phase (Next)

- [ ] All 34 tests PASS
- [ ] Coverage ≥90% for tested components
- [ ] No test skips (except `@pytest.mark.slow`)
- [ ] All checklist requirements validated

### REFACTOR Phase (Final)

- [ ] Code quality: ruff clean, mypy strict
- [ ] Performance: All benchmarks within thresholds
- [ ] Documentation: All docstrings complete
- [ ] Test maintenance: Easy to add new tests

---

## Next Steps

1. **Begin GREEN Phase**: Implement OpenAIAdapter
   - Start with `test_list_all_conversations_from_realistic_export`
   - Implement minimal streaming parser integration
   - Verify test turns GREEN

2. **Iterate TDD Cycle**:
   - Pick next failing test
   - Implement minimal code
   - Verify test passes
   - Refactor if needed

3. **Track Progress**:
   ```bash
   # Watch tests turn GREEN
   pytest tests/integration/ tests/contract/ tests/performance/ -v | grep -E "(passed|failed)"
   ```

4. **Celebrate Milestones**:
   - First integration test GREEN
   - All integration tests GREEN
   - First CLI contract test GREEN
   - All contract tests GREEN
   - Performance benchmarks GREEN
   - **All 34 tests GREEN** 🎉

---

## Appendix: Test File Locations

```
/Users/omarcontreras/PycharmProjects/echomine/
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_list_flow.py           # T026 (11 tests)
│   ├── contract/
│   │   ├── __init__.py
│   │   └── test_cli_contract.py        # T027 (14 tests)
│   ├── performance/
│   │   ├── __init__.py
│   │   └── test_list_benchmark.py      # T028 (9 tests)
│   ├── fixtures/
│   │   ├── README.md
│   │   ├── generate_large_export.py
│   │   └── sample_export.json
│   └── conftest.py                     # Shared fixtures
└── TEST_STRATEGY_T026-T028.md          # This document
```

---

**Document Version**: 1.0
**Author**: TDD Test Strategy Engineer
**Status**: RED Phase Complete ✅
**Next**: Begin GREEN Phase Implementation
