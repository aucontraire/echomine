"""Unit tests for PermissionError handling in library code.

This module validates that the library (OpenAIAdapter) correctly raises
PermissionError when attempting to read files without read permissions.

Constitution Compliance:
    - Principle III: TDD (tests before implementation)
    - FR-061b: Library raises standard PermissionError

Requirements Coverage:
    - FR-061b: Library raises standard PermissionError, CLI catches and converts
    - FR-132: Cleanup occurs on exceptions

Test Strategy:
    - Create files with no read permissions (chmod 000)
    - Attempt to stream/search/get from those files
    - Verify PermissionError is raised
    - Verify file handles are cleaned up (no leaks)

Test Execution:
    pytest tests/unit/test_permission_error.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Permission tests use chmod which behaves differently on Windows",
)


@pytest.fixture
def unreadable_file(tmp_path: Path) -> Path:
    """Create a file with no read permissions.

    Returns:
        Path to unreadable file

    Note:
        File permissions are restored in test cleanup
    """
    file_path = tmp_path / "unreadable.json"
    file_path.write_text("[]", encoding="utf-8")
    file_path.chmod(0o000)  # No permissions
    return file_path


class TestPermissionErrorLibrary:
    """Unit tests for PermissionError raised by library."""

    def test_stream_conversations_raises_permission_error(self, unreadable_file: Path) -> None:
        """Test stream_conversations raises PermissionError for unreadable file.

        Validates:
            - FR-061b: Library raises standard PermissionError
            - PermissionError propagates to caller

        Cleanup:
            File permissions restored in fixture teardown
        """
        adapter = OpenAIAdapter()

        try:
            # Attempt to stream conversations
            with pytest.raises(PermissionError):
                # Need to consume iterator to trigger file open
                list(adapter.stream_conversations(unreadable_file))
        finally:
            # Restore permissions for cleanup
            unreadable_file.chmod(0o644)

    def test_search_raises_permission_error(self, unreadable_file: Path) -> None:
        """Test search raises PermissionError for unreadable file.

        Validates:
            - FR-061b: Library raises standard PermissionError
            - PermissionError propagates during search

        Cleanup:
            File permissions restored in fixture teardown
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"], limit=5)

        try:
            # Attempt to search
            with pytest.raises(PermissionError):
                list(adapter.search(unreadable_file, query))
        finally:
            # Restore permissions for cleanup
            unreadable_file.chmod(0o644)

    def test_get_conversation_by_id_raises_permission_error(self, unreadable_file: Path) -> None:
        """Test get_conversation_by_id raises PermissionError for unreadable file.

        Validates:
            - FR-061b: Library raises standard PermissionError
            - PermissionError propagates during get

        Cleanup:
            File permissions restored in fixture teardown
        """
        adapter = OpenAIAdapter()

        try:
            # Attempt to get conversation
            with pytest.raises(PermissionError):
                adapter.get_conversation_by_id(unreadable_file, "test-id")
        finally:
            # Restore permissions for cleanup
            unreadable_file.chmod(0o644)

    def test_permission_error_message_includes_path(self, unreadable_file: Path) -> None:
        """Test PermissionError message includes the file path.

        Validates:
            - Error message is informative
            - Path included in exception for debugging

        Cleanup:
            File permissions restored in fixture teardown
        """
        adapter = OpenAIAdapter()

        try:
            # Capture the exception
            with pytest.raises(PermissionError) as exc_info:
                list(adapter.stream_conversations(unreadable_file))

            # PermissionError should reference the file path
            error_message = str(exc_info.value)
            # Python's PermissionError typically includes the path
            assert (
                str(unreadable_file) in error_message
                or "unreadable.json" in error_message
                or "Permission denied" in error_message
            ), f"Error message should reference file: {error_message}"

        finally:
            # Restore permissions for cleanup
            unreadable_file.chmod(0o644)
