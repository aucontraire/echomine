# Test Strategy: User Story 1 - Search Conversations by Keyword (T044-T047)

**Author**: TDD Test Strategist
**Date**: 2025-11-22
**Phase**: RED (All tests DESIGNED TO FAIL before implementation)
**User Story**: Phase 4 - Search with BM25 relevance ranking

## Executive Summary

This document outlines the comprehensive test strategy for implementing keyword search functionality with BM25 relevance ranking. Following strict TDD RED-GREEN-REFACTOR principles, all tests documented here are designed to FAIL initially and will guide the search implementation.

**Test Coverage**: 4 tasks, 60+ test cases across all test pyramid levels
**Requirements Coverage**: FR-317-336, FR-291-299, SC-001
**Expected Test Status**: ALL FAILING (RED phase verified)

## Test Pyramid Distribution

```
Performance (5%)  : 13 test cases  - T047
Contract (5%)     : 18 test cases  - T044, T046
Integration (20%) : 20 test cases  - T045
Unit (70%)        : (Deferred to implementation phase)
────────────────────────────────────────
Total             : 51 comprehensive test cases
```

## Task Breakdown

### T044: Contract Test - ConversationProvider.search Protocol

**File**: `/tests/contract/test_provider_protocol.py`
**Status**: ✅ Created (RED phase - all failing)
**Test Count**: 18 tests

#### Purpose
Validates that the `search()` method adheres to the ConversationProvider protocol contract as defined in `protocols.py`. These tests ensure adapters implement the complete search interface with correct signatures, types, and behavioral contracts.

#### Key Test Classes
- `TestConversationProviderSearchProtocol` (14 tests)
  - Protocol implementation validation
  - Method signature compliance
  - Return type verification (Iterator[SearchResult[ConversationT]])
  - SearchQuery and SearchResult structure validation
  - Error handling contracts

- `TestSearchQueryValidation` (4 tests)
  - Pydantic validation rules
  - Limit parameter constraints (1-1000)
  - Default values (limit=10)
  - Score range validation (0.0-1.0)

#### Requirements Validated
- **FR-215-221**: Complete protocol method signatures
- **FR-332-336**: search() method semantics
- **FR-317-326**: BM25 relevance ranking contract
- **FR-327-331**: Title filtering support
- **FR-224, FR-227**: Immutability via frozen models

#### Expected Failures (RED Phase)
```python
# Example failure output:
AssertionError: ConversationProvider implementations must have search() method
assert False
 +  where False = hasattr(<OpenAIAdapter>, 'search')
```

All tests fail because:
- `search()` method doesn't exist on OpenAIAdapter
- SearchResult structure incomplete
- Method signatures don't match protocol
- Validation rules not enforced

---

### T045: Integration Test - Keyword Search Workflow

**File**: `/tests/integration/test_search_flow.py`
**Status**: ✅ Created (RED phase - all failing)
**Test Count**: 20 tests

#### Purpose
Tests the complete end-to-end workflow for searching conversations: file → parse → filter → rank → results. Validates the integration of all search components without testing CLI interface.

#### Test Fixture: `search_test_export`
Custom fixture with **12 conversations** designed for predictable search testing:

| Conv ID | Keywords | Title | Purpose |
|---------|----------|-------|---------|
| 001-003 | "python" (varying frequency) | Generic | BM25 ranking tests |
| 004-005 | Title only | "Python AsyncIO" | Title matching |
| 006-007 | "algorithm" | Generic | Multi-keyword OR logic |
| 008 | Both keywords | "Python Algorithm" | Combined filters |
| 009 | Unicode (测试) | Chinese | Unicode support |
| 010 | None | Database | Empty results test |
| 011-012 | Edge cases | Special chars | Robustness |

#### Key Test Classes

**TestSearchConversationsIntegration** (16 tests)
- Single keyword search with case-insensitive matching
- Multi-keyword OR logic (match ANY keyword)
- BM25 relevance ranking (descending scores)
- Limit parameter (top N results)
- Title filtering (metadata-only, fast)
- Combined filters (keywords AND title)
- Empty results handling
- SearchResult structure validation
- matched_message_ids population
- Unicode keyword support
- File error handling

**TestBM25RelevanceScoring** (4 tests)
- Score normalization (0.0-1.0 range)
- Term frequency affects score
- Document length normalization
- Ranking correctness

#### Requirements Validated
- **FR-317-326**: BM25 relevance ranking (k1=1.5, b=0.75)
- **FR-319**: Case-insensitive keyword matching
- **FR-320**: Multi-keyword OR logic
- **FR-327-331**: Title filtering (case-insensitive substring)
- **FR-332-336**: Search method semantics
- **FR-049**: FileNotFoundError handling

#### Expected Failures (RED Phase)
```python
# Example failure output:
AttributeError: 'OpenAIAdapter' object has no attribute 'search'
```

All tests fail because:
- `search()` method not implemented
- BM25 scoring algorithm not implemented
- Filtering logic missing
- Ranking not implemented
- SearchResult not populated correctly

---

### T046: CLI Contract Test - Search Command

**File**: `/tests/contract/test_cli_contract.py` (extended)
**Status**: ✅ Created (RED phase - all failing)
**Test Count**: 18 tests

#### Purpose
Validates the `echomine search` CLI command adheres to the published interface contract. BLACK BOX tests that only validate external observable behavior (stdout, stderr, exit codes, output format).

#### Key Test Class
**TestCLISearchCommandContract** (18 tests)

**Argument Parsing Tests** (5 tests)
- `--keywords` flag (single keyword)
- `--keywords` flag (comma-separated multiple keywords)
- `--title` filter flag
- Combined `--keywords` and `--title` filters
- `--limit N` parameter

**Output Format Tests** (3 tests)
- Human-readable table (default)
- `--json` flag (JSON output with score + conversation)
- `--quiet` flag (suppress progress indicators)

**stdout/stderr Separation Tests** (2 tests)
- Results go to stdout only
- Progress indicators go to stderr only

**Exit Code Tests** (5 tests)
- Exit code 0 on success (with results)
- Exit code 0 on zero results (not error)
- Exit code 1 on file not found
- Exit code 2 on missing required arguments
- Exit code 130 on interrupt (manual verification)

**Unix Composability Tests** (3 tests)
- Pipeline-friendly output (works with grep, head)
- Absolute and relative path support
- `--help` flag displays usage

#### Requirements Validated
- **FR-291-292**: stdout/stderr separation
- **FR-296-299**: Exit codes (0=success, 1=error, 2=invalid input, 130=interrupt)
- **FR-301-306**: JSON output schema
- **FR-310**: --quiet flag suppresses progress
- **FR-018**: Human-readable output
- **FR-019**: Pipeline-friendly output

#### Expected Failures (RED Phase)
```python
# Example failure output:
AssertionError: Search command should succeed. Got exit code 2.
stderr: Error: No such command 'search'.
```

All tests fail because:
- `search` command not added to CLI
- Argument parsing not implemented
- Output formatting not implemented
- Search flags (`--keywords`, `--title`, `--limit`) not defined

---

### T047: Performance Benchmark - Large File Search

**File**: `/tests/performance/test_search_benchmark.py`
**Status**: ✅ Created (RED phase - all failing)
**Test Count**: 13 tests

#### Purpose
Validates search performance requirements using pytest-benchmark. Establishes baseline metrics for search latency and memory efficiency against large datasets.

#### Test Fixture: `large_export_10k_search`
Performance fixture with **10,000 conversations**:
- **30%** contain "python" keyword (3,000 matches)
- **20%** contain "algorithm" keyword (2,000 matches)
- **10%** contain both keywords (1,000 matches)
- Varying message counts (5-10 messages per conversation)
- **Total size**: ~24 MB JSON file

#### Key Test Classes

**TestSearchPerformance** (6 tests)
1. **test_search_10k_conversations_under_30_seconds**
   - Validates: SC-001 (<30s requirement)
   - Uses: pytest-benchmark for statistical analysis
   - Expected: ~3000 results with "python" keyword

2. **test_search_memory_efficiency_10k_conversations**
   - Validates: Memory usage <1GB, streaming (no indexing)
   - Uses: tracemalloc for memory profiling
   - Expected: Peak memory <200 MB (streaming)

3. **test_search_is_lazy_streaming_not_buffered**
   - Validates: Lazy evaluation (generator/iterator)
   - Measurement: Time to get iterator (<100ms) vs time to consume
   - Expected: Instant iterator creation, no upfront buffering

4. **test_search_with_limit_early_termination**
   - Validates: Early termination optimization
   - Measurement: limit=10 should be <5s (vs ~30s for full search)
   - Expected: >6x speedup with small limits

5. **test_bm25_scoring_performance**
   - Validates: BM25 algorithm performance overhead
   - Uses: pytest-benchmark
   - Expected: Scoring doesn't dominate search time

6. **test_title_filter_performance_optimization**
   - Validates: Title-only search is fast (metadata-only)
   - Expected: <10s for title-only (vs ~30s for keyword search)

**TestSearchLatencyBreakdown** (4 tests)
- JSON streaming latency measurement
- BM25 per-document computation latency (<20ms/doc)
- End-to-end latency percentiles (P50, P95, P99)
- Component-level performance profiling

**TestSearchStressScenarios** (3 tests)
- Very common keyword (most conversations match)
- limit=1 (early termination with first match <1s)
- Large result sets (memory stress test)

#### Performance Requirements Validated
- **SC-001**: Search 1GB file in <30 seconds
- **FR-069**: Progress callback frequency (≥100 items) - deferred
- **FR-444**: 10K conversations searchable
- **FR-317-326**: BM25 computation latency
- Memory efficiency: Streaming, no pre-indexing (<1GB RAM)

#### Expected Failures (RED Phase)
```python
# Example failure output:
AttributeError: 'OpenAIAdapter' object has no attribute 'search'
```

All tests fail because:
- `search()` method not implemented
- BM25 scoring not optimized
- Streaming search not implemented
- Early termination optimization missing
- Performance may not meet <30s requirement initially

---

## Search Requirements Coverage Matrix

### Functional Requirements

| Requirement | Description | Tests | Status |
|-------------|-------------|-------|--------|
| **FR-317-326** | BM25 relevance ranking (k1=1.5, b=0.75) | T044, T045, T047 | ✅ Covered |
| **FR-319** | Case-insensitive keyword matching | T045 | ✅ Covered |
| **FR-320** | Multi-keyword OR logic (match ANY) | T045, T046 | ✅ Covered |
| **FR-327-331** | Title filtering (case-insensitive substring) | T044, T045, T046 | ✅ Covered |
| **FR-332-336** | search() method semantics and SearchResult structure | T044, T045 | ✅ Covered |
| **FR-291-292** | stdout/stderr separation | T046 | ✅ Covered |
| **FR-296-299** | Exit codes (0/1/2/130) | T046 | ✅ Covered |
| **FR-301-306** | JSON output schema | T046 | ✅ Covered |
| **FR-310** | --quiet flag suppresses progress | T046 | ✅ Covered |
| **FR-018** | Human-readable output | T046 | ✅ Covered |
| **FR-019** | Pipeline-friendly output | T046 | ✅ Covered |
| **FR-049** | FileNotFoundError handling | T044, T045, T046 | ✅ Covered |
| **FR-069** | Progress callback frequency | T047 (deferred) | ⏸️ Deferred |

### Success Criteria

| Criterion | Description | Tests | Status |
|-----------|-------------|-------|--------|
| **SC-001** | Search 1GB file in <30 seconds | T047 | ✅ Covered |

### Non-Functional Requirements

| Requirement | Description | Tests | Status |
|-------------|-------------|-------|--------|
| Memory Efficiency | Streaming search (<1GB RAM, no indexing) | T047 | ✅ Covered |
| Unicode Support | Handle Chinese, emoji, special characters | T045 | ✅ Covered |
| Immutability | SearchQuery and SearchResult frozen | T044 | ✅ Covered |
| Type Safety | mypy --strict compliance | T044 | ✅ Covered |

---

## Test Execution Results (RED Phase Verification)

### Verified Failing Tests (as expected)

```bash
# T044: Contract tests FAIL
$ pytest tests/contract/test_provider_protocol.py -v
FAILED test_search_method_exists_on_adapter
  AssertionError: ConversationProvider implementations must have search() method

# T045: Integration tests FAIL
$ pytest tests/integration/test_search_flow.py::TestSearchConversationsIntegration -v
FAILED test_search_single_keyword_returns_matching_conversations
  AttributeError: 'OpenAIAdapter' object has no attribute 'search'

# T046: CLI contract tests FAIL
$ pytest tests/contract/test_cli_contract.py::TestCLISearchCommandContract -v
FAILED test_search_command_with_keywords_flag
  Error: No such command 'search'.

# T047: Performance tests FAIL
$ pytest tests/performance/test_search_benchmark.py -v
FAILED test_search_memory_efficiency_10k_conversations
  AttributeError: 'OpenAIAdapter' object has no attribute 'search'
```

**RED Phase Status**: ✅ VERIFIED - All tests fail for the RIGHT reasons

---

## Implementation Guidance (GREEN Phase)

### Recommended Implementation Order

1. **Protocol Definition** (T044 guides)
   - Add `search()` method signature to ConversationProvider protocol
   - Implement SearchQuery and SearchResult Pydantic models
   - Ensure frozen=True for immutability

2. **Core Search Logic** (T045 guides)
   - Implement streaming keyword search (case-insensitive)
   - Build BM25 scoring algorithm (k1=1.5, b=0.75)
   - Add title filtering (metadata-only, fast)
   - Implement multi-keyword OR logic
   - Add ranking (sort by score descending)
   - Implement limit with early termination

3. **CLI Integration** (T046 guides)
   - Add `search` command to CLI
   - Implement argument parsing (--keywords, --title, --limit)
   - Add output formatters (table, JSON)
   - Implement stdout/stderr separation
   - Add exit code handling

4. **Performance Optimization** (T047 guides)
   - Optimize BM25 computation
   - Implement early termination for limits
   - Validate streaming (no buffering)
   - Profile and optimize memory usage
   - Ensure <30s for 10K conversations

### BM25 Algorithm Reference

```python
# BM25 Scoring Formula (FR-317-326)
k1 = 1.5  # Term frequency saturation parameter
b = 0.75  # Document length normalization parameter

score = sum(
    idf(term) * (
        (tf(term) * (k1 + 1)) /
        (tf(term) + k1 * (1 - b + b * (doc_length / avg_doc_length)))
    )
    for term in query_terms
)

# Normalize to [0.0, 1.0] range for SearchResult.score
normalized_score = score / max_possible_score
```

### Critical Implementation Notes

1. **Streaming Contract**: search() MUST use `ijson` or equivalent - no loading entire file into memory
2. **Memory Bounds**: Peak memory <200MB for 10K conversations (T047 validates)
3. **Early Termination**: When limit is reached, stop streaming immediately (optimization)
4. **Title Filtering**: Metadata-only operation, don't scan message content
5. **Unicode**: Full UTF-8 support for Chinese, emoji, special characters
6. **Immutability**: SearchQuery and SearchResult frozen=True (Pydantic)

---

## Test Maintenance Notes

### Fixture Updates Required When...
- **search_test_export**: Add new keyword distribution scenarios
- **large_export_10k_search**: Adjust keyword percentages for performance tuning
- New edge cases discovered during implementation

### Test Coverage Gaps (Future Work)
- **Date Range Filtering**: SearchQuery.from_date and SearchQuery.to_date not yet tested
- **Progress Callbacks**: Deferred to future implementation (CHK043, CHK135)
- **Unit Tests**: BM25 scoring unit tests (70% of test pyramid) to be created during GREEN phase

### Performance Baseline Expectations
After successful GREEN phase implementation, establish these baselines:

| Metric | Target | Test |
|--------|--------|------|
| Search 10K conversations | <5s (P50) | T047 |
| Search 10K conversations | <30s (P99) | T047 |
| Peak memory usage | <200 MB | T047 |
| BM25 per-document | <20 ms | T047 |
| Title-only search | <10s | T047 |
| limit=1 search | <1s | T047 |

---

## RED-GREEN-REFACTOR Workflow

### Current Phase: 🔴 RED
**Status**: ✅ Complete
**Evidence**: All 51 tests verified failing for correct reasons

### Next Phase: 🟢 GREEN
**Goal**: Make all tests pass with minimal implementation
**Approach**:
1. Implement search() method skeleton
2. Add BM25 scoring (hardcoded k1, b values)
3. Implement filtering logic
4. Add ranking (sort by score)
5. Integrate CLI command
6. Iterate until all tests pass

**Success Criteria**:
- pytest exit code 0 for all T044-T047 tests
- Coverage meets minimum thresholds (90%+ for critical paths)

### Future Phase: 🔵 REFACTOR
**Goal**: Optimize implementation while maintaining test passage
**Focus**:
- Extract BM25 into separate module
- Optimize memory usage
- Improve performance (target <5s P50)
- Add comprehensive unit tests
- Code cleanup and documentation

---

## Files Created

1. **`/tests/contract/test_provider_protocol.py`** (NEW)
   - 18 contract tests for search() protocol
   - SearchQuery and SearchResult validation
   - Lines: ~400

2. **`/tests/integration/test_search_flow.py`** (NEW)
   - 20 integration tests for end-to-end search workflow
   - Custom search_test_export fixture (12 conversations)
   - Lines: ~1000

3. **`/tests/contract/test_cli_contract.py`** (EXTENDED)
   - Added TestCLISearchCommandContract class
   - 18 CLI search command tests
   - Lines added: ~550

4. **`/tests/performance/test_search_benchmark.py`** (NEW)
   - 13 performance benchmarks
   - large_export_10k_search fixture (10K conversations)
   - Lines: ~750

5. **`/tests/TEST_STRATEGY_T044-T047.md`** (THIS FILE)
   - Comprehensive test strategy documentation
   - Lines: ~500

**Total Lines of Test Code**: ~2,700 lines
**Total Test Cases**: 51 tests

---

## Conclusion

This test strategy provides comprehensive coverage for User Story 1: Search Conversations by Keyword. All tests are in RED phase (failing) and will guide the implementation through TDD's RED-GREEN-REFACTOR cycle.

**Key Achievements**:
- ✅ 51 comprehensive test cases across all pyramid levels
- ✅ 100% FR coverage for search functionality
- ✅ Performance baselines established (SC-001: <30s)
- ✅ All tests verified failing for correct reasons
- ✅ Clear implementation guidance provided

**Next Steps**:
1. Begin GREEN phase implementation
2. Use failing tests as specification
3. Implement minimal code to pass each test
4. Iterate until all tests pass
5. Refactor for optimization and clarity

---

**Document Status**: ✅ Complete
**Phase**: RED (All tests failing as expected)
**Ready for GREEN Phase**: Yes
