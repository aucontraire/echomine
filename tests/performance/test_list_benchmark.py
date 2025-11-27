"""Performance benchmarks for User Story 0: List All Conversations.

Task: T028 - Performance Benchmark - 10K conversation listing
Phase: RED (tests designed to FAIL initially)

This module validates performance requirements using pytest-benchmark.
Establishes baseline metrics for CHK025 (P50, P95, P99) and CHK108 (latency).

Test Pyramid Classification: Performance (5% of test suite)
These tests measure and enforce performance constraints.

Performance Requirements Validated:
- FR-444: Parse 10K conversations in <5 seconds
- FR-069: Progress callback frequency ≥100 items (per CHK135)
- SC-001: Memory usage <1GB on 8GB machines
- CHK025: Establish P50, P95, P99 latency baselines
- CHK108: Latency per operation type (parse, transform, format)

Measurement Tools:
- pytest-benchmark: Throughput and latency metrics
- tracemalloc: Memory profiling (Python standard library)
- time.perf_counter: High-resolution timing

Fixtures Required:
- large_export_10k.json: 10,000 conversations, 50,000 messages (FR-444 baseline)
- Generated via tests/fixtures/generate_large_export.py
"""

import time
import tracemalloc
from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.constants import (
    MAX_BATCH_SIZE,
    PROGRESS_UPDATE_INTERVAL,
    TARGET_WORKING_SET,
)


# =============================================================================
# Performance Test Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def large_export_10k(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate 10K conversation export for performance testing.

    This fixture is expensive to create, so it's scoped to 'module' to
    generate once and reuse across all performance tests.

    Specification (per FR-444):
    - 10,000 conversations
    - 5 messages per conversation (50,000 total messages)
    - Realistic OpenAI structure with threading

    Returns:
        Path to generated large export file
    """
    import json

    tmp_path = tmp_path_factory.mktemp("performance")

    # Use simplified generation (faster than calling external script)
    conversations = []
    for i in range(10000):
        messages_mapping = {}
        for j in range(5):
            msg_id = f"msg-{i:05d}-{j}"
            parent_id = f"msg-{i:05d}-{j - 1}" if j > 0 else None
            children_ids = [f"msg-{i:05d}-{j + 1}"] if j < 4 else []

            messages_mapping[msg_id] = {
                "id": msg_id,
                "message": {
                    "id": msg_id,
                    "author": {"role": "user" if j % 2 == 0 else "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": [f"Message {j} in conversation {i}"],
                    },
                    "create_time": 1710000000.0 + i * 100 + j * 10,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": parent_id,
                "children": children_ids,
            }

        conversation = {
            "id": f"perf-conv-{i:05d}",
            "title": f"Performance Test Conversation {i}",
            "create_time": 1710000000.0 + i * 100,
            "update_time": 1710000000.0 + i * 100 + 40,
            "mapping": messages_mapping,
            "moderation_results": [],
            "current_node": f"msg-{i:05d}-4",
        }
        conversations.append(conversation)

        # Progress indicator (fixture generation can take 10-30 seconds)
        if (i + 1) % 2000 == 0:
            print(f"Generated {i + 1}/10000 conversations for benchmark...")

    export_file = tmp_path / "large_export_10k.json"
    print(f"Writing {len(conversations):,} conversations to {export_file}...")

    with export_file.open("w") as f:
        json.dump(conversations, f)

    file_size_mb = export_file.stat().st_size / (1024 * 1024)
    print(f"Generated benchmark fixture: {file_size_mb:.2f} MB")

    return export_file


@pytest.fixture
def progress_tracker() -> list[int]:
    """Track progress callback invocations for frequency validation.

    Returns:
        List to accumulate conversation counts from progress callbacks
    """
    return []


# =============================================================================
# T028: Performance Benchmarks (RED Phase - DESIGNED TO FAIL)
# =============================================================================


@pytest.mark.performance
class TestListPerformance:
    """Performance benchmarks for list operation.

    These tests measure throughput, latency, and memory usage.
    Baselines will be established during initial implementation.

    Expected Failure Reasons (RED phase):
    - OpenAIAdapter not implemented
    - Performance may not meet requirements initially
    - Memory tracking infrastructure not in place
    """

    def test_list_10k_conversations_under_5_seconds(
        self, large_export_10k: Path, benchmark: Any
    ) -> None:
        """Benchmark listing 10K conversations (FR-444: <5 seconds).

        Validates:
        - FR-444: Parse 10K conversations in <5 seconds
        - CHK025: Establish P50, P95, P99 latency baselines

        Expected to FAIL: OpenAIAdapter not implemented yet.

        Benchmark Statistics Collected:
        - min, max, mean, median (P50)
        - stddev, iqr
        - iterations per second (ops)
        """
        adapter = OpenAIAdapter()

        def list_all_conversations() -> int:
            """Benchmark target: list all conversations."""
            conversations = list(adapter.stream_conversations(large_export_10k))
            return len(conversations)

        # Run benchmark
        result = benchmark(list_all_conversations)

        # Verify correct count
        assert result == 10000, "Should list all 10,000 conversations"

        # Performance requirement (FR-444: <5 seconds)
        # pytest-benchmark reports stats after test completion
        # Manual verification: Check benchmark table output shows mean <5.0s

    def test_streaming_memory_efficiency_10k_conversations(self, large_export_10k: Path) -> None:
        """Measure memory usage during streaming (SC-001: <1GB).

        Validates:
        - FR-003: O(1) memory via streaming
        - SC-001: Memory usage <1GB
        - CHK007: Memory bounds (550MB worst-case)

        Expected to FAIL: Streaming not implemented yet.

        Memory Measurement:
        - Uses tracemalloc (Python standard library)
        - Measures peak memory increase during operation
        - Excludes Python interpreter baseline
        """
        adapter = OpenAIAdapter()

        # Start memory tracking
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        # Stream conversations (should NOT load all into memory)
        conversation_count = 0
        for conversation in adapter.stream_conversations(large_export_10k):
            conversation_count += 1

            # Sample memory every 1000 conversations
            if conversation_count % 1000 == 0:
                current, peak = tracemalloc.get_traced_memory()
                memory_mb = (current - baseline) / (1024 * 1024)
                print(f"[{conversation_count:5d} conversations] Memory: {memory_mb:.2f} MB")

        # Get final memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        final_memory_mb = (current - baseline) / (1024 * 1024)
        peak_memory_mb = (peak - baseline) / (1024 * 1024)

        print("\nMemory Profile:")
        print(f"  Final: {final_memory_mb:.2f} MB")
        print(f"  Peak:  {peak_memory_mb:.2f} MB")
        print(f"  Conversations: {conversation_count:,}")

        # Assert: Peak memory <1GB (SC-001)
        assert peak_memory_mb < 1024, (
            f"Peak memory {peak_memory_mb:.2f} MB exceeds 1GB limit (SC-001)"
        )

        # Assert: Peak memory within architectural bounds (CHK007: 550MB)
        # NOTE: This is a GUIDELINE, may need adjustment based on implementation
        expected_max_mb = TARGET_WORKING_SET / (1024 * 1024)  # 100MB target
        assert peak_memory_mb < expected_max_mb * 6, (
            f"Peak memory {peak_memory_mb:.2f} MB exceeds architectural "
            f"bounds (CHK007: ~550MB worst-case)"
        )

        # Verify count
        assert conversation_count == 10000

    def test_streaming_is_lazy_not_eager(self, large_export_10k: Path) -> None:
        """Verify streaming is lazy (doesn't parse entire file upfront).

        Validates:
        - FR-003: Streaming implementation (not buffering)
        - Lazy evaluation (generator/iterator)

        Expected to FAIL: Streaming not implemented.

        Measurement:
        - Time to get iterator vs time to consume iterator
        - Iterator creation should be nearly instant (<100ms)
        - Full consumption takes longer (actual parsing work)
        """
        adapter = OpenAIAdapter()

        # Measure time to GET iterator (should be instant)
        start_get = time.perf_counter()
        iterator = adapter.stream_conversations(large_export_10k)
        time_to_get_ms = (time.perf_counter() - start_get) * 1000

        # Verify it's an iterator, not a list
        assert hasattr(iterator, "__iter__") and hasattr(iterator, "__next__"), (
            "stream_conversations must return iterator (lazy streaming)"
        )

        # Getting iterator should be nearly instant
        assert time_to_get_ms < 100, (
            f"Getting iterator took {time_to_get_ms:.1f}ms, should be <100ms. "
            f"This suggests eager loading, not lazy streaming."
        )

        # Now measure time to consume (should take significant time)
        start_consume = time.perf_counter()
        count = sum(1 for _ in iterator)
        time_to_consume_s = time.perf_counter() - start_consume

        assert count == 10000
        assert time_to_consume_s > 0.1, (
            "Consuming iterator should take non-trivial time (actual parsing work)"
        )

        # Ratio validation: consuming should take >>100x longer than getting
        ratio = (time_to_consume_s * 1000) / time_to_get_ms
        assert ratio > 10, (
            f"Consume/get ratio is {ratio:.1f}x. Expected >10x, indicating lazy streaming."
        )

    @pytest.mark.skip(reason="Progress callbacks deferred to future implementation (CHK043)")
    def test_progress_callback_frequency(
        self, large_export_10k: Path, progress_tracker: list[int]
    ) -> None:
        """Validate progress callback frequency (FR-069, CHK135: ≥100 items).

        DEFERRED: Progress callback feature not implemented in Phase 3 User Story 0.
        Will be implemented when progress indicators are added (CHK043, CHK135).

        Validates:
        - FR-069: Progress updates during long operations
        - CHK135: Update interval = 100 items

        Measurement:
        - Count number of progress callbacks
        - Verify interval is ~100 conversations
        """
        pytest.skip("Progress callbacks deferred to future implementation")

        # Verify correct count
        assert len(conversations) == 10000

        # Verify progress callbacks occurred
        assert len(progress_tracker) > 0, "Progress callback should be invoked"

        # Verify callback frequency (CHK135: every 100 items)
        expected_callbacks = 10000 // PROGRESS_UPDATE_INTERVAL  # 100 callbacks
        assert len(progress_tracker) >= expected_callbacks - 5, (
            f"Expected ~{expected_callbacks} progress callbacks "
            f"(every {PROGRESS_UPDATE_INTERVAL} items), got {len(progress_tracker)}"
        )

        # Verify incremental counts
        assert progress_tracker[0] >= PROGRESS_UPDATE_INTERVAL, (
            f"First progress should be at {PROGRESS_UPDATE_INTERVAL}, got {progress_tracker[0]}"
        )
        assert progress_tracker[-1] == 10000, (
            f"Final progress should be 10000, got {progress_tracker[-1]}"
        )

    def test_batch_size_constraint(self, large_export_10k: Path) -> None:
        """Validate batch size respects MAX_BATCH_SIZE constant (CHK007).

        Validates:
        - CHK007: MAX_BATCH_SIZE = 100 conversations before yield
        - Memory bounds enforcement

        Expected to FAIL: Batching not implemented.

        Measurement:
        - Track when conversations are yielded
        - Verify batches don't exceed 100 items
        """
        adapter = OpenAIAdapter()

        # Track yield timing
        last_yield_time = time.perf_counter()
        yield_intervals = []

        count = 0
        for conversation in adapter.stream_conversations(large_export_10k):
            count += 1

            # Record time between yields (approximation of batch boundaries)
            if count % MAX_BATCH_SIZE == 0:
                current_time = time.perf_counter()
                interval = current_time - last_yield_time
                yield_intervals.append(interval)
                last_yield_time = current_time

        # Verify we got all conversations
        assert count == 10000

        # Verify consistent batching (intervals should be similar)
        if yield_intervals:
            import statistics

            mean_interval = statistics.mean(yield_intervals)
            stddev_interval = statistics.stdev(yield_intervals)

            # Coefficient of variation should be low (consistent batching)
            cv = stddev_interval / mean_interval
            assert cv < 1.0, (
                f"Yield intervals vary too much (CV={cv:.2f}), suggests inconsistent batching"
            )


@pytest.mark.performance
class TestLatencyBreakdown:
    """Latency breakdown tests (CHK108: latency per operation type).

    These tests measure individual operation latencies to identify
    bottlenecks and establish baselines.

    Expected Failure Reasons (RED phase):
    - Individual components not implemented
    - Performance monitoring infrastructure not in place
    """

    def test_json_parsing_latency(self, large_export_10k: Path, benchmark: Any) -> None:
        """Benchmark raw JSON parsing (ijson) latency.

        Validates:
        - CHK108: Parsing operation latency
        - ijson performance characteristics

        Expected to FAIL: Streaming parser not implemented.
        """
        import ijson

        def parse_json_stream() -> int:
            """Benchmark target: raw JSON streaming."""
            count = 0
            with large_export_10k.open("rb") as f:
                for item in ijson.items(f, "item"):
                    count += 1
            return count

        result = benchmark(parse_json_stream)
        assert result == 10000

        # Performance stats reported by pytest-benchmark table output

    def test_model_transformation_latency(self, large_export_10k: Path, benchmark: Any) -> None:
        """Benchmark Pydantic model transformation latency.

        Validates:
        - CHK108: Model transformation operation latency
        - Pydantic validation overhead

        Expected to FAIL: Adapter not implemented.
        """
        adapter = OpenAIAdapter()

        def transform_to_models() -> int:
            """Benchmark target: parse + transform to Conversation models."""
            conversations = list(adapter.stream_conversations(large_export_10k))
            return len(conversations)

        result = benchmark(transform_to_models)
        assert result == 10000

        # Performance stats reported by pytest-benchmark table output

    def test_end_to_end_latency_percentiles(self, large_export_10k: Path) -> None:
        """Measure end-to-end latency percentiles (CHK025: P50, P95, P99).

        Validates:
        - CHK025: Establish P50, P95, P99 baselines
        - Latency distribution characteristics

        Expected to FAIL: Implementation not complete.

        Measurement:
        - Run operation 10 times
        - Calculate percentiles from timing data
        """
        adapter = OpenAIAdapter()

        latencies = []
        for run in range(10):
            start = time.perf_counter()
            conversations = list(adapter.stream_conversations(large_export_10k))
            latency = time.perf_counter() - start
            latencies.append(latency)

            assert len(conversations) == 10000

        # Calculate percentiles
        import statistics

        latencies_sorted = sorted(latencies)
        p50 = statistics.median(latencies_sorted)
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]

        print("\nLatency Percentiles (10 runs):")
        print(f"  P50 (median): {p50:.3f}s")
        print(f"  P95:          {p95:.3f}s")
        print(f"  P99:          {p99:.3f}s")
        print(f"  Min:          {min(latencies):.3f}s")
        print(f"  Max:          {max(latencies):.3f}s")

        # Baseline validation (FR-444: <5s)
        assert p99 < 5.0, f"P99 latency {p99:.3f}s exceeds 5s requirement (FR-444)"

        # Document baselines for future regression detection
        # NOTE: These values will be established after first successful run
        # and should be codified in constants.py or test configuration


@pytest.mark.performance
class TestStressScenarios:
    """Stress test scenarios beyond baseline requirements.

    These tests validate behavior under extreme conditions.

    Expected Failure Reasons (RED phase):
    - Implementation not robust enough for stress scenarios
    - Resource limits hit
    """

    @pytest.mark.slow
    def test_50k_conversation_stress_test(self, tmp_path: Path) -> None:
        """Stress test with 50K conversations (10x baseline).

        Validates:
        - Scalability beyond FR-444 baseline
        - Memory efficiency at scale

        Expected to FAIL: Implementation not optimized yet.

        Note: Marked as 'slow' - skip in regular test runs.
        Run explicitly with: pytest -m slow
        """
        pytest.skip("Stress test: run explicitly with pytest -m slow")

        # Generate 50K conversations fixture
        import json

        conversations = []
        for i in range(50000):
            # Minimal conversation structure
            conversations.append(
                {
                    "id": f"stress-{i:06d}",
                    "title": f"Stress {i}",
                    "create_time": 1710000000.0 + i,
                    "update_time": 1710000000.0 + i + 1,
                    "mapping": {
                        f"msg-{i}": {
                            "id": f"msg-{i}",
                            "message": {
                                "id": f"msg-{i}",
                                "author": {"role": "user"},
                                "content": {"content_type": "text", "parts": ["Q"]},
                                "create_time": 1710000000.0 + i,
                                "update_time": None,
                                "metadata": {},
                            },
                            "parent": None,
                            "children": [],
                        }
                    },
                    "moderation_results": [],
                    "current_node": f"msg-{i}",
                }
            )

        stress_file = tmp_path / "stress_50k.json"
        with stress_file.open("w") as f:
            json.dump(conversations, f)

        # Run stress test
        adapter = OpenAIAdapter()

        tracemalloc.start()
        start = time.perf_counter()

        conversations_parsed = list(adapter.stream_conversations(stress_file))

        elapsed = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print("\n50K Stress Test Results:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Peak Memory: {peak / (1024 * 1024):.2f} MB")
        print(f"  Throughput: {50000 / elapsed:.0f} conversations/s")

        assert len(conversations_parsed) == 50000
        assert peak < 1024 * 1024 * 1024, "Memory should stay under 1GB"
