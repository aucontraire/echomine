"""Performance benchmarks for ClaudeAdapter."""

from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.models.search import SearchQuery


# Skip if large fixture doesn't exist
pytestmark = pytest.mark.skipif(
    not Path("tests/fixtures/claude/large_export.json").exists(),
    reason="Large export fixture not generated. Run: python tests/fixtures/claude/generate_large_export.py",
)


@pytest.fixture
def large_export() -> Path:
    return Path("tests/fixtures/claude/large_export.json")


@pytest.fixture
def adapter() -> ClaudeAdapter:
    return ClaudeAdapter()


# T106: Performance benchmark for 1000+ conversations
def test_stream_1000_conversations_performance(
    adapter: ClaudeAdapter, large_export: Path, benchmark: Any
) -> None:
    """Benchmark: Stream 1000+ conversations."""

    def stream_all() -> int:
        count = 0
        for _ in adapter.stream_conversations(large_export):
            count += 1
        return count

    result = benchmark(stream_all)
    assert result >= 1000, f"Expected 1000+ conversations, got {result}"


def test_search_performance(adapter: ClaudeAdapter, large_export: Path, benchmark: Any) -> None:
    """Benchmark: Search with keywords."""
    query = SearchQuery(keywords=["python"], limit=100)

    def do_search() -> list[Any]:
        return list(adapter.search(large_export, query))

    results = benchmark(do_search)
    assert len(results) <= 100


# T107: Memory efficiency benchmark
def test_memory_efficiency(adapter: ClaudeAdapter, large_export: Path) -> None:
    """Verify O(1) memory usage via streaming."""
    import tracemalloc

    tracemalloc.start()

    # Stream all conversations without storing
    count = 0
    for conv in adapter.stream_conversations(large_export):
        count += 1
        # Don't store conversations - memory should stay constant

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Peak memory should be reasonable (<500MB for 1000+ conversations)
    peak_mb = peak / (1024 * 1024)
    assert peak_mb < 500, f"Peak memory {peak_mb:.1f}MB exceeds 500MB limit"

    print(f"\nMemory usage: current={current / 1024 / 1024:.1f}MB, peak={peak_mb:.1f}MB")
    print(f"Processed {count} conversations")


# T108: Search time validation (SC-002: <30s for 10K)
def test_search_completes_in_30_seconds(adapter: ClaudeAdapter, large_export: Path) -> None:
    """SC-002: Search <30s for 10K conversations."""
    import time

    query = SearchQuery(keywords=["python"], limit=100)

    start = time.time()
    results = list(adapter.search(large_export, query))
    elapsed = time.time() - start

    assert elapsed < 30, f"Search took {elapsed:.1f}s, expected <30s"
    print(f"\nSearch completed in {elapsed:.2f}s")
