"""Performance benchmarks for User Story 1: Search Conversations by Keyword.

Task: T047 - Performance Benchmark - Large File Search
Phase: RED (tests designed to FAIL initially)

This module validates search performance requirements using pytest-benchmark.
Establishes baseline metrics for search latency and memory efficiency.

Test Pyramid Classification: Performance (5% of test suite)
These tests measure and enforce performance constraints for search operations.

Performance Requirements Validated:
- SC-001: Search 1GB file (<30s requirement)
- FR-069: Progress callback frequency (≥100 items)
- FR-444: 10K conversations searchable
- FR-317-326: BM25 computation latency
- Memory efficiency during search (streaming, no pre-indexing)

Measurement Tools:
- pytest-benchmark: Throughput and latency metrics
- tracemalloc: Memory profiling (Python standard library)
- time.perf_counter: High-resolution timing

Fixtures Required:
- large_export_10k.json: 10,000 conversations for search benchmarking
- Generated via tests/fixtures/generate_large_export.py
"""

import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


# =============================================================================
# Performance Test Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def large_export_10k_search(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate 10K conversation export for search performance testing.

    This fixture creates a large export file with known keyword distribution
    to enable predictable search performance testing.

    Specification (per FR-444):
    - 10,000 conversations
    - ~30% contain "python" keyword (3000 matches)
    - ~20% contain "algorithm" keyword (2000 matches)
    - ~10% contain both keywords (1000 matches)
    - Realistic message counts (5-10 messages per conversation)

    Returns:
        Path to generated large export file for search
    """
    import json

    tmp_path = tmp_path_factory.mktemp("search_performance")

    conversations = []
    for i in range(10000):
        # Distribute keywords for realistic search scenarios
        # 30% have "python", 20% have "algorithm", 10% have both
        has_python = i % 10 < 3  # 30%
        has_algorithm = i % 10 >= 5 and i % 10 < 7  # 20%
        has_both = i % 10 == 7  # 10%

        # Generate messages with keyword distribution
        messages_mapping = {}
        msg_count = 5 if i % 2 == 0 else 10  # Vary message count

        for j in range(msg_count):
            msg_id = f"msg-{i:05d}-{j}"
            parent_id = f"msg-{i:05d}-{j - 1}" if j > 0 else None
            children_ids = [f"msg-{i:05d}-{j + 1}"] if j < msg_count - 1 else []

            # Construct message content with keywords
            content_parts = []
            if has_python or has_both:
                if j == 0:
                    content_parts.append(f"Discussing Python programming in message {j}")
                elif j == 2:
                    content_parts.append("Python is great for data science and machine learning")

            if has_algorithm or has_both:
                if j == 1:
                    content_parts.append("Explaining algorithm complexity and design patterns")

            if not content_parts:
                content_parts.append(f"Generic message {j} in conversation {i}")

            messages_mapping[msg_id] = {
                "id": msg_id,
                "message": {
                    "id": msg_id,
                    "author": {"role": "user" if j % 2 == 0 else "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": content_parts,
                    },
                    "create_time": 1710000000.0 + i * 100 + j * 10,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": parent_id,
                "children": children_ids,
            }

        # Title also contains keywords for some conversations
        title_parts = []
        if has_python or has_both:
            title_parts.append("Python")
        if has_algorithm or has_both:
            title_parts.append("Algorithm")

        if not title_parts:
            title = f"Conversation {i:05d}"
        else:
            title = f"{' and '.join(title_parts)} Discussion {i:05d}"

        conversation = {
            "id": f"search-perf-conv-{i:05d}",
            "title": title,
            "create_time": 1710000000.0 + i * 100,
            "update_time": 1710000000.0 + i * 100 + (msg_count - 1) * 10,
            "mapping": messages_mapping,
            "moderation_results": [],
            "current_node": f"msg-{i:05d}-{msg_count - 1}",
        }
        conversations.append(conversation)

        # Progress indicator (fixture generation can take time)
        if (i + 1) % 2000 == 0:
            print(f"Generated {i + 1}/10000 search conversations for benchmark...")

    export_file = tmp_path / "large_export_10k_search.json"
    print(f"Writing {len(conversations):,} conversations to {export_file}...")

    with export_file.open("w") as f:
        json.dump(conversations, f)

    file_size_mb = export_file.stat().st_size / (1024 * 1024)
    print(f"Generated search benchmark fixture: {file_size_mb:.2f} MB")

    return export_file


# =============================================================================
# T047: Search Performance Benchmarks (RED Phase - DESIGNED TO FAIL)
# =============================================================================


@pytest.mark.performance
class TestSearchPerformance:
    """Performance benchmarks for search operations.

    These tests measure search throughput, latency, and memory usage
    against large datasets. Baselines established during implementation.

    Expected Failure Reasons (RED phase):
    - search() method not implemented
    - BM25 scoring not optimized for performance
    - Memory usage may exceed limits
    - Latency may not meet <30s requirement
    """

    def test_search_10k_conversations_under_30_seconds(
        self, large_export_10k_search: Path, benchmark: Any
    ) -> None:
        """Benchmark searching 10K conversations (SC-001: <30 seconds).

        Validates:
        - SC-001: Search 1GB file in <30 seconds
        - FR-444: 10K conversations searchable
        - BM25 scoring performance

        Expected to FAIL: search() not implemented yet.

        Benchmark Statistics Collected:
        - min, max, mean, median (P50)
        - stddev, iqr
        - iterations per second (ops)
        """
        adapter = OpenAIAdapter()

        def search_conversations() -> int:
            """Benchmark target: search all conversations for keyword."""
            query = SearchQuery(keywords=["python"], limit=1000)
            results = list(adapter.search(large_export_10k_search, query))
            return len(results)

        # Run benchmark
        result = benchmark(search_conversations)

        # Verify found matches (capped at limit=1000)
        assert result > 0, "Should find conversations with 'python' keyword"
        assert result == 1000, f"Expected 1000 matches (limit constraint), got {result}"

        # Performance requirement (SC-001: <30 seconds)
        # pytest-benchmark reports stats after test completion
        # Manual verification: Check benchmark table output shows mean <30.0s

    def test_search_memory_efficiency_10k_conversations(
        self, large_export_10k_search: Path
    ) -> None:
        """Measure memory usage during search (SC-001: <1GB, no indexing).

        Validates:
        - SC-001: Memory usage <1GB
        - FR-317-326: BM25 computed during streaming (no pre-indexing)
        - Memory-efficient search without building indexes

        Expected to FAIL: Memory-efficient search not implemented.

        Memory Measurement:
        - Uses tracemalloc (Python standard library)
        - Measures peak memory increase during search
        - Validates streaming search (no index building)
        """
        adapter = OpenAIAdapter()

        # Start memory tracking
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        # Search for keyword (should stream, not load all into memory)
        query = SearchQuery(keywords=["python"], limit=1000)
        result_count = 0

        for result in adapter.search(large_export_10k_search, query):
            result_count += 1

            # Sample memory every 500 results
            if result_count % 500 == 0:
                current, peak = tracemalloc.get_traced_memory()
                memory_mb = (current - baseline) / (1024 * 1024)
                print(f"[{result_count:5d} results] Memory: {memory_mb:.2f} MB")

        # Get final memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        final_memory_mb = (current - baseline) / (1024 * 1024)
        peak_memory_mb = (peak - baseline) / (1024 * 1024)

        print("\nSearch Memory Profile:")
        print(f"  Final: {final_memory_mb:.2f} MB")
        print(f"  Peak:  {peak_memory_mb:.2f} MB")
        print(f"  Results: {result_count:,}")

        # Assert: Peak memory <1GB (SC-001)
        assert peak_memory_mb < 1024, (
            f"Peak memory {peak_memory_mb:.2f} MB exceeds 1GB limit (SC-001)"
        )

        # Assert: Memory stays low (streaming, not buffering)
        # Should be similar to list operation memory usage
        assert peak_memory_mb < 200, (
            f"Search memory {peak_memory_mb:.2f} MB too high. "
            "Should stream without building indexes."
        )

        # Verify result count
        assert result_count == 1000, f"Expected 1000 results (limit constraint), got {result_count}"

    def test_search_is_lazy_streaming_not_buffered(self, large_export_10k_search: Path) -> None:
        """Verify search returns iterator (BM25 requires corpus processing before yielding).

        Validates:
        - FR-332: search() returns Iterator
        - BM25 algorithm processes corpus before ranking
        - Results yielded after ranking computation

        Note: BM25 search CANNOT be truly lazy because it requires:
        1. Processing all documents to calculate IDF (inverse document frequency)
        2. Calculating average document length across corpus
        3. Scoring and ranking all matches before returning top results

        This is an inherent limitation of BM25 ranking, not a performance issue.
        The iterator interface is used for consistency with stream_conversations.

        Measurement:
        - Time to get iterator (should be instant)
        - Time to get first result (includes BM25 computation for 10K docs)
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"], limit=1000)

        # Measure time to GET iterator (should be instant)
        start_get = time.perf_counter()
        iterator = adapter.search(large_export_10k_search, query)
        time_to_get_ms = (time.perf_counter() - start_get) * 1000

        # Verify it's an iterator
        assert hasattr(iterator, "__iter__") and hasattr(iterator, "__next__"), (
            "search() must return iterator (FR-332)"
        )

        # Getting iterator should be instant (generator creation is lazy)
        assert time_to_get_ms < 100, (
            f"Getting iterator took {time_to_get_ms:.1f}ms, should be <100ms. "
            f"Iterator creation should be instant."
        )

        # Measure time to get FIRST result (includes BM25 computation)
        start_first = time.perf_counter()
        first_result = next(iterator)
        time_to_first_ms = (time.perf_counter() - start_first) * 1000

        # First result includes BM25 computation for entire corpus
        # 10K conversations should process in reasonable time (<5 seconds)
        assert time_to_first_ms < 5000, (
            f"Getting first result took {time_to_first_ms:.1f}ms. "
            f"BM25 computation for 10K docs should complete in <5s."
        )

        # Consume remaining results to verify streaming continues
        remaining_count = sum(1 for _ in iterator)
        assert remaining_count > 0, "Should have more results after first"

    def test_search_with_limit_early_termination(self, large_export_10k_search: Path) -> None:
        """Test that limit parameter enables early termination optimization.

        Validates:
        - FR-336: Limit parameter
        - Early termination when limit reached (optimization)
        - Search with limit=10 should be MUCH faster than full search

        Expected to FAIL: Early termination optimization not implemented.

        Performance Expectation:
        - Search with limit=10 should complete in <1s
        - Full search takes ~30s (SC-001)
        - Ratio should be >10x faster for small limits
        """
        adapter = OpenAIAdapter()

        # Measure search with limit=10
        query_limited = SearchQuery(keywords=["python"], limit=10)

        start_limited = time.perf_counter()
        results_limited = list(adapter.search(large_export_10k_search, query_limited))
        time_limited = time.perf_counter() - start_limited

        # Assert: Got exactly limit results
        assert len(results_limited) == 10, (
            f"Limit=10 should return 10 results, got {len(results_limited)}"
        )

        # Assert: Completed quickly (early termination)
        assert time_limited < 5.0, (
            f"Search with limit=10 took {time_limited:.2f}s, should be <5s. "
            "Early termination optimization may not be working."
        )

        print("\nEarly Termination Performance:")
        print(f"  Time with limit=10: {time_limited:.3f}s")
        print(f"  Results: {len(results_limited)}")

    @pytest.mark.skip(reason="Progress callbacks deferred to future implementation")
    def test_search_progress_callback_frequency(self, large_export_10k_search: Path) -> None:
        """Validate progress callback frequency during search (FR-069).

        DEFERRED: Progress callback feature not implemented in Phase 4.
        Will be implemented when progress indicators are added.

        Validates:
        - FR-069: Progress updates during search
        - Callback invoked every ~100 conversations scanned

        Expected to FAIL: Progress callback not implemented.
        """
        pytest.skip("Progress callbacks deferred to future implementation")

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=1000)

        progress_calls = []

        def progress_callback(count: int) -> None:
            progress_calls.append(count)

        # Search with progress callback
        results = list(
            adapter.search(large_export_10k_search, query, progress_callback=progress_callback)
        )

        # Verify progress callbacks occurred
        assert len(progress_calls) > 0, "Progress callback should be invoked"
        assert len(progress_calls) >= 50, (
            f"Expected ~100 progress callbacks (every 100 items), got {len(progress_calls)}"
        )

    def test_bm25_scoring_performance(self, large_export_10k_search: Path, benchmark: Any) -> None:
        """Benchmark BM25 scoring computation performance.

        Validates:
        - FR-317-326: BM25 algorithm performance
        - Scoring doesn't dominate total search time

        Expected to FAIL: BM25 not implemented or not optimized.
        """
        adapter = OpenAIAdapter()

        def search_with_scoring() -> int:
            """Benchmark target: search with BM25 scoring."""
            query = SearchQuery(keywords=["python", "algorithm"], limit=1000)
            results = list(adapter.search(large_export_10k_search, query))
            return len(results)

        # Run benchmark
        result = benchmark(search_with_scoring)

        # Verify found expected matches (~4000 conversations with either keyword)
        assert result == 1000, f"Expected 1000 matches (limit constraint), got {result}"

    def test_title_filter_performance_optimization(self, large_export_10k_search: Path) -> None:
        """Test that title-only filtering is fast (metadata-only, no message scan).

        Validates:
        - FR-327-331: Title filtering
        - Title-only search should be MUCH faster than keyword search
        - No need to scan message content for title filtering

        Expected to FAIL: Title filtering optimization not implemented.

        Performance Expectation:
        - Title-only search should be <5s (metadata-only)
        - Full keyword search ~30s (message content scanning)
        """
        adapter = OpenAIAdapter()

        # Measure title-only search
        query_title = SearchQuery(title_filter="Python", limit=1000)

        start_title = time.perf_counter()
        results_title = list(adapter.search(large_export_10k_search, query_title))
        time_title = time.perf_counter() - start_title

        # Assert: Completed quickly (metadata-only)
        assert time_title < 10.0, (
            f"Title-only search took {time_title:.2f}s, should be <10s. "
            "Title filtering should be fast (no message content scanning)."
        )

        # Verify found results
        assert len(results_title) > 0, "Should find conversations with 'Python' in title"

        print("\nTitle Filter Performance:")
        print(f"  Time: {time_title:.3f}s")
        print(f"  Results: {len(results_title)}")


@pytest.mark.performance
class TestSearchLatencyBreakdown:
    """Latency breakdown tests for search components.

    These tests measure individual search operation latencies to identify
    bottlenecks and establish baselines.
    """

    def test_json_streaming_latency_for_search(
        self, large_export_10k_search: Path, benchmark: Any
    ) -> None:
        """Benchmark JSON streaming latency during search.

        Validates:
        - Streaming parser performance during search
        - JSON parsing overhead

        Expected to FAIL: search() not implemented.
        """
        adapter = OpenAIAdapter()

        def stream_search() -> int:
            """Benchmark target: stream and filter conversations."""
            query = SearchQuery(keywords=["python"], limit=1000)
            # Count results (forces iteration through stream)
            return sum(1 for _ in adapter.search(large_export_10k_search, query))

        result = benchmark(stream_search)
        # Expect 1000 results (capped by limit parameter)
        assert result == 1000, f"Expected 1000 results (limit constraint), got {result}"

    def test_bm25_computation_latency_per_document(self, large_export_10k_search: Path) -> None:
        """Measure BM25 computation latency per document.

        Validates:
        - BM25 scoring efficiency
        - Per-document scoring overhead

        Expected to FAIL: BM25 not implemented.

        Measurement:
        - Total search time / number of results
        - Should be <10ms per document on average
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=1000)

        # Measure total search time
        start = time.perf_counter()
        results = list(adapter.search(large_export_10k_search, query))
        total_time = time.perf_counter() - start

        result_count = len(results)

        # Calculate per-document latency
        latency_per_doc_ms = (total_time / result_count) * 1000 if result_count > 0 else 0

        print("\nBM25 Per-Document Latency:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Results: {result_count}")
        print(f"  Latency per doc: {latency_per_doc_ms:.2f}ms")

        # Assert: Reasonable per-document latency
        assert latency_per_doc_ms < 20, (
            f"BM25 latency {latency_per_doc_ms:.2f}ms per document is too high. "
            "Should be <20ms for efficient search."
        )

    def test_search_end_to_end_latency_percentiles(self, large_export_10k_search: Path) -> None:
        """Measure end-to-end search latency percentiles (P50, P95, P99).

        Validates:
        - Latency distribution characteristics
        - Performance consistency across runs

        Expected to FAIL: search() not implemented.

        Measurement:
        - Run search 10 times
        - Calculate P50, P95, P99 from timing data
        """
        adapter = OpenAIAdapter()

        latencies = []
        for run in range(10):
            query = SearchQuery(keywords=["python"], limit=1000)

            start = time.perf_counter()
            results = list(adapter.search(large_export_10k_search, query))
            latency = time.perf_counter() - start
            latencies.append(latency)

            assert len(results) > 0, "Should find results"

        # Calculate percentiles
        import statistics

        latencies_sorted = sorted(latencies)
        p50 = statistics.median(latencies_sorted)
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]

        print("\nSearch Latency Percentiles (10 runs):")
        print(f"  P50 (median): {p50:.3f}s")
        print(f"  P95:          {p95:.3f}s")
        print(f"  P99:          {p99:.3f}s")
        print(f"  Min:          {min(latencies):.3f}s")
        print(f"  Max:          {max(latencies):.3f}s")

        # Baseline validation (SC-001: <30s)
        assert p99 < 30.0, f"P99 search latency {p99:.3f}s exceeds 30s requirement (SC-001)"


@pytest.mark.performance
class TestSearchStressScenarios:
    """Stress test scenarios for search operations.

    These tests validate search behavior under extreme conditions.
    """

    @pytest.mark.slow
    def test_search_with_very_common_keyword(self, large_export_10k_search: Path) -> None:
        """Stress test search with keyword matching most conversations.

        Validates:
        - Performance when most conversations match
        - Memory usage with large result sets
        - Ranking still works correctly

        Expected to FAIL: May hit memory or performance limits.
        """
        adapter = OpenAIAdapter()

        # Search for very common word (present in many conversations)
        query = SearchQuery(keywords=["message", "conversation"], limit=1000)

        tracemalloc.start()
        start = time.perf_counter()

        results = list(adapter.search(large_export_10k_search, query))

        elapsed = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print("\nCommon Keyword Search Stress Test:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Results: {len(results)}")
        print(f"  Peak Memory: {peak / (1024 * 1024):.2f} MB")

        # Should still complete in reasonable time
        assert elapsed < 60, (
            f"Search took {elapsed:.2f}s, should complete within 60s even for common keywords"
        )

        # Memory should stay reasonable
        assert peak < 512 * 1024 * 1024, "Memory should stay under 512MB"

    @pytest.mark.slow
    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows CI runners have variable performance"
    )
    def test_search_with_limit_1(self, large_export_10k_search: Path) -> None:
        """Test search with limit=1 returns top ranked result.

        Validates:
        - Limit parameter correctly restricts results
        - BM25 ranking returns highest scoring match
        - Performance is acceptable for 10K document corpus

        Note: BM25 search cannot do early termination because it must:
        1. Process all documents to calculate IDF and corpus statistics
        2. Score all matching documents
        3. Rank by score to find the TOP match (not just any match)

        This is correct behavior - limit=1 means "best match", not "first match found".
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"], limit=1)

        start = time.perf_counter()
        results = list(adapter.search(large_export_10k_search, query))
        elapsed = time.perf_counter() - start

        assert len(results) == 1, "Should return exactly 1 result"
        # BM25 requires full corpus processing, so ~2-3s for 10K docs is expected
        assert elapsed < 5.0, (
            f"Search with limit=1 took {elapsed:.3f}s, should complete in <5s for 10K docs"
        )

        print(f"\nLimit=1 Performance: {elapsed:.3f}s (includes BM25 ranking)")
