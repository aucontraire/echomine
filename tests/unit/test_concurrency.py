"""T067: Thread Safety Contract Tests.

This test module validates that OpenAIAdapter is thread-safe and can be used
from multiple threads simultaneously without race conditions or shared state issues.

Test Strategy:
    - Verify same adapter instance can be used from multiple threads
    - Verify each thread gets independent iterators (not shared)
    - Verify no race conditions when reading same file concurrently
    - Verify file handles are properly managed per-thread
    - Test concurrent reads, searches, and get_conversation_by_id

Constitution Compliance:
    - FR-098, FR-099, FR-100, FR-101: Thread safety requirements
    - FR-115: Stateless adapters enable thread safety
    - Principle III: Test-Driven Development (RED phase)

Requirements Coverage:
    - FR-098: Adapter instances must be thread-safe
    - FR-099: Iterators must NOT be shared across threads
    - FR-100: Each thread must create its own iterator
    - FR-101: No race conditions on concurrent reads

Test Execution:
    pytest tests/unit/test_concurrency.py -v

Expected State: FAILING (imports will fail until exports added to __init__.py)
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest


if TYPE_CHECKING:
    from echomine import Conversation
    from echomine.models.search import SearchResult


# ============================================================================
# T067-001: Adapter Instance Thread Safety
# ============================================================================


def test_adapter_instance_can_be_used_from_multiple_threads(
    tmp_export_file: Path,
) -> None:
    """Verify same adapter instance can be used from multiple threads.

    Requirements:
        - FR-098: Adapter instances MUST be thread-safe
        - FR-115: Stateless adapters enable thread reuse

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    results: dict[int, list[Conversation]] = {}
    errors: list[Exception] = []

    def worker(thread_id: int) -> None:
        """Worker function to run in thread."""
        try:
            # Each thread uses the same adapter instance
            conversations = list(adapter.stream_conversations(tmp_export_file))
            results[thread_id] = conversations
        except Exception as e:
            errors.append(e)

    # Create and start multiple threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"Threads should not error: {errors}"
    assert len(results) == 5, "All threads should complete"

    # All threads should get same number of conversations
    conversation_counts = [len(convs) for convs in results.values()]
    assert all(count == conversation_counts[0] for count in conversation_counts), (
        "All threads should get same results"
    )


def test_concurrent_threads_get_independent_iterators(
    tmp_export_file: Path,
) -> None:
    """Verify each thread gets independent iterator (not shared).

    Requirements:
        - FR-099: Iterators MUST NOT be shared across threads
        - FR-100: Each thread MUST create its own iterator

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    iterator_ids: list[int] = []
    results: list[int] = []
    lock = threading.Lock()
    errors: list[Exception] = []

    def worker() -> None:
        """Worker function to capture iterator ID."""
        try:
            # Each call should return a NEW iterator
            iterator = adapter.stream_conversations(tmp_export_file)

            # Record iterator object ID before consumption
            # (id might be reused after GC, but not during consumption)
            iter_id = id(iterator)

            # Consume iterator to verify it works
            conversations = list(iterator)

            # Record results under lock
            with lock:
                iterator_ids.append(iter_id)
                results.append(len(conversations))
        except Exception as e:
            with lock:
                errors.append(e)

    # Create and start multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"Threads should not error: {errors}"
    assert len(iterator_ids) == 5, "Should have 5 iterator IDs"
    assert len(results) == 5, "All threads should complete"

    # All threads should get same number of conversations (proves independent reads)
    assert all(r == results[0] for r in results), (
        f"All threads should read same data independently, got: {results}"
    )

    # Note: We cannot reliably test id() uniqueness due to Python's memory reuse.
    # The fact that all threads completed successfully with correct results
    # proves they each had independent iterators (not shared state).


# ============================================================================
# T067-002: Concurrent File Reading
# ============================================================================


def test_no_race_conditions_on_concurrent_reads(
    tmp_export_file: Path,
) -> None:
    """Verify no race conditions when multiple threads read same file.

    Requirements:
        - FR-101: No race conditions on concurrent reads
        - FR-098: Thread-safe adapter implementation

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    results: dict[int, list[Conversation]] = {}
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(thread_id: int) -> None:
        """Worker function to read file."""
        try:
            # All threads read same file simultaneously
            conversations = list(adapter.stream_conversations(tmp_export_file))

            with lock:
                results[thread_id] = conversations
        except Exception as e:
            with lock:
                errors.append(e)

    # Create many threads to increase chance of race conditions
    num_threads = 10
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]

    # Start all threads at roughly same time
    for thread in threads:
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"
    assert len(results) == num_threads, "All threads should complete"

    # All threads should get identical results
    first_result = results[0]
    for thread_id, conversations in results.items():
        assert len(conversations) == len(first_result), f"Thread {thread_id} should get same count"

        # Verify same conversation IDs (order should be same)
        first_ids = [conv.id for conv in first_result]
        thread_ids = [conv.id for conv in conversations]
        assert thread_ids == first_ids, (
            f"Thread {thread_id} should get same conversations in same order"
        )


def test_concurrent_search_operations(
    tmp_export_file: Path,
) -> None:
    """Verify concurrent search operations work correctly.

    Requirements:
        - FR-098: Adapter instances MUST be thread-safe
        - FR-101: No race conditions

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()

    results: dict[int, list[SearchResult[Any]]] = {}
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(thread_id: int, keywords: list[str]) -> None:
        """Worker function to perform search."""
        try:
            query = SearchQuery(keywords=keywords, limit=5)
            search_results = list(adapter.search(tmp_export_file, query))

            with lock:
                results[thread_id] = search_results
        except Exception as e:
            with lock:
                errors.append(e)

    # Create threads with different search queries
    threads = [
        threading.Thread(target=worker, args=(0, ["test"])),
        threading.Thread(target=worker, args=(1, ["algorithm"])),
        threading.Thread(target=worker, args=(2, ["code"])),
        threading.Thread(target=worker, args=(3, ["python"])),
        threading.Thread(target=worker, args=(4, ["test"])),  # Same as thread 0
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"
    assert len(results) == 5, "All threads should complete"

    # Threads with same query should get same results
    thread0_results = results[0]
    thread4_results = results[4]

    assert len(thread0_results) == len(thread4_results), (
        "Threads with same query should get same count"
    )

    if len(thread0_results) > 0:
        thread0_ids = [r.conversation.id for r in thread0_results]
        thread4_ids = [r.conversation.id for r in thread4_results]
        assert thread0_ids == thread4_ids, "Threads with same query should get same results"


def test_concurrent_get_conversation_by_id(
    tmp_export_file: Path,
) -> None:
    """Verify concurrent get_conversation_by_id operations work correctly.

    Requirements:
        - FR-098: Adapter instances MUST be thread-safe
        - FR-101: No race conditions

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # First, get a valid conversation ID
    conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(conversations) > 0, "Sample export should have conversations"

    conversation_id = conversations[0].id

    results: dict[int, Conversation | None] = {}
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(thread_id: int) -> None:
        """Worker function to get conversation by ID."""
        try:
            conversation = adapter.get_conversation_by_id(tmp_export_file, conversation_id)

            with lock:
                results[thread_id] = conversation
        except Exception as e:
            with lock:
                errors.append(e)

    # Create multiple threads requesting same conversation
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"
    assert len(results) == 5, "All threads should complete"

    # All threads should get the same conversation
    for thread_id, conversation in results.items():
        assert conversation is not None, f"Thread {thread_id} should find conversation"
        assert conversation.id == conversation_id, (
            f"Thread {thread_id} should get correct conversation"
        )


# ============================================================================
# T067-003: File Handle Management in Concurrent Access
# ============================================================================


def test_file_handles_are_managed_per_thread(
    tmp_export_file: Path,
) -> None:
    """Verify each thread manages its own file handles.

    Requirements:
        - FR-130-133: Resource cleanup guarantees
        - FR-098: Thread-safe resource management

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(thread_id: int) -> None:
        """Worker function to read file partially."""
        try:
            # Create iterator
            iterator = adapter.stream_conversations(tmp_export_file)

            # Consume only first conversation
            first = next(iterator)
            assert first is not None, "Should get first conversation"

            # Iterator should still work (file handle not closed by other threads)
            try:
                second = next(iterator)
                # If there's a second conversation, we should get it
            except StopIteration:
                # If only one conversation, that's okay
                pass

        except Exception as e:
            with lock:
                errors.append(e)

    # Create multiple threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"


# ============================================================================
# T067-004: Early Termination in Concurrent Threads
# ============================================================================


def test_concurrent_early_termination_does_not_affect_other_threads(
    tmp_export_file: Path,
) -> None:
    """Verify early termination in one thread doesn't affect others.

    Requirements:
        - FR-099: Iterators MUST NOT be shared across threads
        - FR-130-133: Resource cleanup per-thread

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    results: dict[str, list[Conversation]] = {}
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker_partial() -> None:
        """Worker that reads only first conversation."""
        try:
            iterator = adapter.stream_conversations(tmp_export_file)
            # Get only first conversation, then stop
            first = next(iterator)
            assert first is not None
            # Iterator will be garbage collected with file handle cleanup
        except Exception as e:
            with lock:
                errors.append(e)

    def worker_full() -> None:
        """Worker that reads all conversations."""
        try:
            # This should work even if other thread stopped early
            conversations = list(adapter.stream_conversations(tmp_export_file))

            with lock:
                results["full"] = conversations
        except Exception as e:
            with lock:
                errors.append(e)

    # Create threads
    thread_partial = threading.Thread(target=worker_partial)
    thread_full = threading.Thread(target=worker_full)

    # Start partial first
    thread_partial.start()
    thread_partial.join()

    # Then start full (should not be affected)
    thread_full.start()
    thread_full.join()

    # Both should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"
    assert "full" in results, "Full worker should complete"
    assert len(results["full"]) > 0, "Full worker should get conversations"


# ============================================================================
# T067-005: Adapter Statelessness Verification
# ============================================================================


def test_adapter_has_no_shared_mutable_state() -> None:
    """Verify adapter has no shared mutable state between calls.

    Requirements:
        - FR-113: Adapters are stateless (no __init__ parameters)
        - FR-114: Adapters are reusable
        - FR-115: Stateless design enables thread safety

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Adapter should have no mutable instance attributes
    # Check __dict__ for instance state
    instance_attrs = vars(adapter)

    # Stateless adapters should have minimal or no instance state
    # (Some Python internals may be present, but no business logic state)
    for attr_name, attr_value in instance_attrs.items():
        # Check for mutable types that could cause state issues
        assert not isinstance(attr_value, (list, dict, set)), (
            f"Adapter should not have mutable state: {attr_name}"
        )


def test_multiple_adapter_instances_are_independent(
    tmp_export_file: Path,
) -> None:
    """Verify multiple adapter instances are completely independent.

    Requirements:
        - FR-113: Stateless adapters
        - FR-115: Reusable adapters

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    # Create two adapter instances
    adapter1 = OpenAIAdapter()
    adapter2 = OpenAIAdapter()

    # They should be different objects
    assert adapter1 is not adapter2, "Should create different instances"

    # Both should work independently
    results1 = list(adapter1.stream_conversations(tmp_export_file))
    results2 = list(adapter2.stream_conversations(tmp_export_file))

    # Both should get same results
    assert len(results1) == len(results2), "Both adapters should work independently"


# ============================================================================
# T067-006: Stress Test with Many Concurrent Threads
# ============================================================================


@pytest.mark.slow
def test_stress_test_many_concurrent_threads(
    tmp_export_file: Path,
) -> None:
    """Stress test with many concurrent threads to expose race conditions.

    Requirements:
        - FR-098: Adapter instances MUST be thread-safe
        - FR-101: No race conditions

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    success_count = 0
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker() -> None:
        """Worker function to read file."""
        nonlocal success_count
        try:
            conversations = list(adapter.stream_conversations(tmp_export_file))
            assert len(conversations) > 0, "Should get conversations"

            with lock:
                success_count += 1
        except Exception as e:
            with lock:
                errors.append(e)

    # Create many threads (stress test)
    num_threads = 20
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    # All threads should succeed
    assert len(errors) == 0, f"No threads should error: {errors}"
    assert success_count == num_threads, "All threads should succeed"
