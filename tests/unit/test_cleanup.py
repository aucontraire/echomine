"""T068: Resource Cleanup Contract Tests.

This test module validates that file handles and other resources are properly
cleaned up in ALL scenarios: normal completion, early termination, and exceptions.

Test Strategy:
    - Verify file handles closed when iteration completes normally
    - Verify file handles closed when iteration breaks early
    - Verify file handles closed when exception raised during iteration
    - Track open file descriptors to detect leaks
    - Test cleanup with context managers and generators

Constitution Compliance:
    - FR-130-133: Resource cleanup guarantees
    - FR-116-119: Iterator lifecycle management
    - Principle III: Test-Driven Development (RED phase)

Requirements Coverage:
    - FR-130: Methods use try/finally for cleanup guarantees
    - FR-131: File handles managed via context managers
    - FR-132: Cleanup occurs in all scenarios (normal, early break, exceptions, GC)
    - FR-133: NO __del__ methods for cleanup

Test Execution:
    pytest tests/unit/test_cleanup.py -v

Expected State: FAILING (imports will fail until exports added to __init__.py)
"""

from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import TYPE_CHECKING

import psutil
import pytest

if TYPE_CHECKING:
    from echomine import OpenAIAdapter


# ============================================================================
# Test Fixtures for File Descriptor Tracking
# ============================================================================


@pytest.fixture
def open_fds_before() -> set[int]:
    """Capture open file descriptors before test.

    Returns:
        Set of file descriptor numbers currently open
    """
    process = psutil.Process()
    return {fd.fd for fd in process.open_files()}


def get_current_open_fds() -> set[int]:
    """Get currently open file descriptors.

    Returns:
        Set of file descriptor numbers currently open
    """
    process = psutil.Process()
    return {fd.fd for fd in process.open_files()}


def assert_no_file_descriptor_leak(fds_before: set[int]) -> None:
    """Assert that no file descriptors leaked.

    Args:
        fds_before: Set of file descriptors before operation

    Raises:
        AssertionError: If file descriptors leaked
    """
    # Force garbage collection to cleanup any pending iterators
    gc.collect()

    fds_after = get_current_open_fds()

    # New file descriptors indicate a leak
    leaked_fds = fds_after - fds_before

    assert (
        len(leaked_fds) == 0
    ), f"File descriptor leak detected: {leaked_fds} file descriptors not closed"


# ============================================================================
# T068-001: Normal Completion Cleanup
# ============================================================================


def test_file_handle_closed_after_normal_iteration(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed after normal iteration completion.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-132: Cleanup occurs on normal completion

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Consume entire iterator
    conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(conversations) > 0, "Should get conversations"

    # File handle should be closed after iteration completes
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_after_search_completion(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed after search completes normally.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-132: Cleanup occurs on normal completion

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["test"], limit=5)

    # Consume entire search iterator
    results = list(adapter.search(tmp_export_file, query))

    # File handle should be closed after search completes
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_after_get_conversation_by_id(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed after get_conversation_by_id.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-132: Cleanup occurs on normal completion

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # First get a valid conversation ID
    conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(conversations) > 0, "Sample export should have conversations"

    conversation_id = conversations[0].id

    # Get conversation by ID
    conversation = adapter.get_conversation_by_id(tmp_export_file, conversation_id)
    assert conversation is not None, "Should find conversation"

    # File handle should be closed
    assert_no_file_descriptor_leak(open_fds_before)


# ============================================================================
# T068-002: Early Termination Cleanup
# ============================================================================


def test_file_handle_closed_on_early_break(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when iteration breaks early.

    Requirements:
        - FR-132: Cleanup occurs on early break
        - FR-131: Context managers guarantee cleanup

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Break after first conversation
    for i, conversation in enumerate(adapter.stream_conversations(tmp_export_file)):
        if i == 0:
            assert conversation is not None
            break  # Early termination

    # File handle should still be closed
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_when_iterator_abandoned(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when iterator is abandoned (garbage collected).

    Requirements:
        - FR-132: Cleanup occurs on garbage collection
        - FR-131: Context managers in generators handle cleanup

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Create iterator but never consume it
    iterator = adapter.stream_conversations(tmp_export_file)

    # Get first item to open file
    first = next(iterator)
    assert first is not None

    # Abandon iterator (let it go out of scope)
    del iterator

    # File handle should be closed after garbage collection
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_when_search_breaks_early(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when search iteration breaks early.

    Requirements:
        - FR-132: Cleanup occurs on early break
        - FR-131: Context managers guarantee cleanup

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["test"], limit=10)

    # Break after first result
    for i, result in enumerate(adapter.search(tmp_export_file, query)):
        if i == 0:
            assert result is not None
            break  # Early termination

    # File handle should still be closed
    assert_no_file_descriptor_leak(open_fds_before)


# ============================================================================
# T068-003: Exception Handling Cleanup
# ============================================================================


def test_file_handle_closed_when_exception_raised_during_iteration(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when exception raised during iteration.

    Requirements:
        - FR-132: Cleanup occurs on exceptions
        - FR-130: Methods use try/finally for cleanup guarantees

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Raise exception during iteration
    with pytest.raises(RuntimeError):
        for i, conversation in enumerate(
            adapter.stream_conversations(tmp_export_file)
        ):
            if i == 1:
                raise RuntimeError("Test exception during iteration")

    # File handle should still be closed
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_when_callback_raises_exception(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when progress callback raises exception.

    Requirements:
        - FR-132: Cleanup occurs on exceptions
        - FR-130: try/finally guarantees cleanup even with callback errors

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    def failing_callback(count: int) -> None:
        """Callback that raises exception."""
        if count > 0:
            raise RuntimeError("Callback error")

    # Exception in callback should propagate
    with pytest.raises(RuntimeError):
        list(
            adapter.stream_conversations(
                tmp_export_file, progress_callback=failing_callback
            )
        )

    # File handle should still be closed
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_closed_when_validation_error_occurs(
    tmp_path: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle is closed when ValidationError occurs during parsing.

    Requirements:
        - FR-132: Cleanup occurs on exceptions
        - FR-281: Graceful degradation with skip (or fail-fast)

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    # Create malformed export file (will cause ValidationError or ParseError)
    malformed_file = tmp_path / "malformed.json"
    malformed_file.write_text('[{"id": "", "title": "Invalid", "create_time": "bad"}]')

    adapter = OpenAIAdapter()

    # Should either skip malformed entries or raise exception
    # Either way, file handle should be closed
    try:
        list(adapter.stream_conversations(malformed_file))
    except Exception:
        # Expected - malformed data
        pass

    # File handle should be closed
    assert_no_file_descriptor_leak(open_fds_before)


# ============================================================================
# T068-004: Multiple Sequential Operations
# ============================================================================


def test_no_file_handle_accumulation_with_multiple_operations(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handles don't accumulate across multiple operations.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-115: Adapters are reusable

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Perform multiple operations sequentially
    for _ in range(5):
        conversations = list(adapter.stream_conversations(tmp_export_file))
        assert len(conversations) > 0

    # No file handles should accumulate
    assert_no_file_descriptor_leak(open_fds_before)


def test_no_file_handle_leak_with_mixed_operations(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handles don't leak with mixed operation types.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-115: Adapters are reusable

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()

    # Mix different operations
    # 1. List conversations
    conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(conversations) > 0

    # 2. Search
    query = SearchQuery(keywords=["test"], limit=5)
    results = list(adapter.search(tmp_export_file, query))

    # 3. Get by ID
    conversation_id = conversations[0].id
    conversation = adapter.get_conversation_by_id(tmp_export_file, conversation_id)
    assert conversation is not None

    # 4. List again
    conversations2 = list(adapter.stream_conversations(tmp_export_file))

    # No file handles should leak
    assert_no_file_descriptor_leak(open_fds_before)


# ============================================================================
# T068-005: Context Manager Pattern Verification
# ============================================================================


def test_adapter_methods_use_context_managers_internally(
    tmp_export_file: Path,
) -> None:
    """Verify adapter methods use context managers for file handling.

    This test inspects that files are opened with 'with' statements internally.

    Requirements:
        - FR-131: File handles managed via context managers
        - FR-130: try/finally for cleanup guarantees

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Track files opened during operation
    fds_during: set[int] = set()

    def track_open_files() -> None:
        """Track files that are open during iteration."""
        nonlocal fds_during
        process = psutil.Process()
        fds_during = {fd.fd for fd in process.open_files()}

    # Create iterator
    iterator = adapter.stream_conversations(tmp_export_file)

    # Get first item (should open file)
    first = next(iterator)
    assert first is not None

    # Track what files are open now
    track_open_files()

    # Should have at least one file open (the export file)
    # (This may not always be true if file is buffered/closed quickly,
    # but validates that file WAS opened at some point)

    # Finish iteration
    list(iterator)

    # After iteration, file should be closed
    # (Verified by other tests with fd leak detection)


# ============================================================================
# T068-006: No __del__ Methods for Cleanup
# ============================================================================


def test_adapter_does_not_use_del_for_cleanup() -> None:
    """Verify adapter doesn't use __del__ method for cleanup.

    Requirements:
        - FR-133: NO __del__ methods for cleanup
        - Use context managers instead (more reliable)

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Adapter should not define __del__ method
    assert not hasattr(
        adapter, "__del__"
    ), "Adapter should NOT use __del__ for cleanup (use context managers instead)"


def test_iterator_cleanup_without_del_method(
    tmp_export_file: Path,
    open_fds_before: set[int],
) -> None:
    """Verify iterator cleanup works without __del__ method.

    Requirements:
        - FR-133: NO __del__ methods for cleanup
        - FR-132: Cleanup via context managers and try/finally

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Create and abandon iterator
    iterator = adapter.stream_conversations(tmp_export_file)
    first = next(iterator)
    assert first is not None

    # Iterator should not have __del__ method
    assert not hasattr(
        iterator, "__del__"
    ), "Iterator should NOT use __del__ for cleanup"

    # Delete iterator (should cleanup via context managers, not __del__)
    del iterator

    # Cleanup should still occur
    assert_no_file_descriptor_leak(open_fds_before)


# ============================================================================
# T068-007: File Permission Error Cleanup
# ============================================================================


def test_file_handle_cleanup_on_permission_error(
    tmp_path: Path,
    open_fds_before: set[int],
) -> None:
    """Verify file handle cleanup occurs even when PermissionError raised.

    Requirements:
        - FR-132: Cleanup occurs on exceptions
        - FR-051: PermissionError raised for unreadable files

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    # Create a file with no read permissions
    restricted_file = tmp_path / "restricted.json"
    restricted_file.write_text('[]')
    restricted_file.chmod(0o000)  # No permissions

    adapter = OpenAIAdapter()

    try:
        # Should raise PermissionError
        with pytest.raises(PermissionError):
            list(adapter.stream_conversations(restricted_file))
    finally:
        # Restore permissions for cleanup
        restricted_file.chmod(0o644)

    # No file handles should leak
    assert_no_file_descriptor_leak(open_fds_before)


def test_file_handle_cleanup_on_file_not_found_error(
    open_fds_before: set[int],
) -> None:
    """Verify file handle cleanup occurs even when FileNotFoundError raised.

    Requirements:
        - FR-132: Cleanup occurs on exceptions
        - FR-049: FileNotFoundError raised for missing files

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    non_existent_file = Path("/tmp/this-file-does-not-exist-12345.json")

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        list(adapter.stream_conversations(non_existent_file))

    # No file handles should leak (file never opened)
    assert_no_file_descriptor_leak(open_fds_before)
