"""Unit tests for list command --limit flag functionality.

Task: Design failing tests for US0-AS2 acceptance scenario fix
Phase: RED (tests designed to FAIL initially)

This module provides unit-level tests for the --limit parameter in the list command.
These tests focus on the isolated behavior of limit functionality without subprocess calls.

Test Pyramid Classification: Unit (70% of test suite)
These tests validate isolated functionality of the --limit flag at the function level.

Functional Requirements Validated:
- FR-443: List --limit flag MUST restrict output to top N conversations (after sorting)
- FR-440: List output MUST sort conversations by created_at descending (newest first)

Constitution Requirements:
- Principle I: Library-first architecture (tests at library level)
- Principle III: TDD - Write failing tests FIRST
- Principle VI: Strict typing - All tests must be type-safe

Expected Failure Reason:
- list_conversations function does not have limit parameter
- No logic to slice conversation list after sorting
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import typer

from echomine.cli.commands.list import list_conversations
from echomine.models import Conversation


# =============================================================================
# Helper Functions
# =============================================================================


def create_test_conversation(
    conv_id: str, title: str, created_at: datetime, message_count: int = 1
) -> Conversation:
    """Create a test Conversation object with specified fields.

    Args:
        conv_id: Conversation ID
        title: Conversation title
        created_at: Creation timestamp
        message_count: Number of messages (for metadata)

    Returns:
        Conversation object
    """
    from echomine.models import Message

    # Create minimal messages
    messages = []
    for i in range(message_count):
        msg = Message(
            id=f"{conv_id}-msg-{i}",
            role="user",
            content=f"Test message {i}",
            timestamp=created_at,
            parent_id=None,
        )
        messages.append(msg)

    return Conversation(
        id=conv_id,
        title=title,
        created_at=created_at,
        updated_at=created_at,
        messages=messages,
    )


# =============================================================================
# Unit Tests - FR-443: --limit parameter functionality
# =============================================================================


@pytest.mark.unit
class TestListLimitParameter:
    """Unit tests for list_conversations function with limit parameter.

    These tests mock the OpenAIAdapter to isolate the limit logic.
    All tests should FAIL initially because limit parameter doesn't exist.

    Expected Failure Mode:
    - TypeError: list_conversations() got an unexpected keyword argument 'limit'
    """

    def test_limit_parameter_restricts_to_n_conversations(self, tmp_path: Path) -> None:
        """Test limit parameter restricts output to N conversations.

        Validates:
        - FR-443: limit restricts output to top N
        - FR-440: Applied after sorting (newest first)

        Expected to FAIL: limit parameter not in function signature.
        """
        # Arrange: Create test file
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        # Create 10 test conversations with incrementing timestamps
        conversations = []
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(10):
            # Add i hours to base_time so conv-009 is newest
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        # Mock the adapter to return our conversations
        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            # Mock typer.echo to capture output
            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Call list_conversations with limit=5
                # This should NOT raise an exception if limit parameter exists
                list_conversations(file_path=test_file, format="text", limit=5)

        # Assert: Output should contain only 5 conversations (newest ones)
        output = outputs[0] if outputs else ""

        # The 5 newest should be conv-009, conv-008, conv-007, conv-006, conv-005
        assert "conv-009" in output, "Newest conversation should be included"
        assert "conv-008" in output
        assert "conv-007" in output
        assert "conv-006" in output
        assert "conv-005" in output

        # Older conversations should NOT be included
        assert "conv-004" not in output, "6th conversation should be excluded with limit=5"
        assert "conv-000" not in output, "Oldest conversation should be excluded"

    def test_limit_parameter_with_json_format(self, tmp_path: Path) -> None:
        """Test limit parameter works with JSON output format.

        Validates:
        - FR-443: limit works with --format json
        - FR-442: JSON output structure

        Expected to FAIL: limit parameter not in function signature.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        # Create 20 test conversations
        conversations = []
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(20):
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Call with limit=10 and JSON format
                list_conversations(file_path=test_file, format="json", limit=10)

        # Assert: Parse JSON output
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)

        # Should have exactly 10 conversations
        assert len(data) == 10, f"Expected 10 conversations with limit=10. Got {len(data)}"

        # Should be newest 10 (conv-019 down to conv-010)
        assert data[0]["id"] == "conv-019", "First should be newest"
        assert data[9]["id"] == "conv-010", "Last should be 10th from top"

    def test_limit_parameter_value_1_returns_single_conversation(
        self, tmp_path: Path
    ) -> None:
        """Test limit=1 returns only the newest conversation.

        Validates:
        - FR-443: limit=1 edge case

        Expected to FAIL: limit parameter not in function signature.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        conversations = []
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Call with limit=1
                list_conversations(file_path=test_file, format="json", limit=1)

        # Assert
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)

        assert len(data) == 1, f"Expected exactly 1 conversation. Got {len(data)}"
        assert data[0]["id"] == "conv-004", "Should return newest conversation"

    def test_limit_parameter_greater_than_total_returns_all(
        self, tmp_path: Path
    ) -> None:
        """Test limit > total conversations returns all conversations.

        Validates:
        - FR-443: limit N where N > total doesn't error

        Expected to FAIL: limit parameter not in function signature.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        # Create only 3 conversations
        conversations = []
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(3):
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Request limit=100 from file with only 3 conversations
                list_conversations(file_path=test_file, format="json", limit=100)

        # Assert: Should return all 3 conversations
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)

        assert len(data) == 3, "Should return all 3 available conversations"

    def test_limit_parameter_applies_after_sorting(self, tmp_path: Path) -> None:
        """Test limit is applied AFTER sorting by created_at descending.

        Validates:
        - FR-443: limit applies after sorting
        - FR-440: sort by created_at descending

        Expected to FAIL: limit parameter not in function signature.
        """
        # Arrange: Create conversations in NON-chronological order in source
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Create in random order: 5, 2, 8, 1, 9, 3, 7, 4, 6, 0
        creation_order = [5, 2, 8, 1, 9, 3, 7, 4, 6, 0]
        conversations = []
        for i in creation_order:
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Request top 3 with limit=3
                list_conversations(file_path=test_file, format="json", limit=3)

        # Assert: Should get conv-009, conv-008, conv-007 (newest 3 after sorting)
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)

        assert len(data) == 3
        assert data[0]["id"] == "conv-009", "First should be newest (hour=9)"
        assert data[1]["id"] == "conv-008", "Second should be hour=8"
        assert data[2]["id"] == "conv-007", "Third should be hour=7"


# =============================================================================
# Unit Tests - Input Validation
# =============================================================================


@pytest.mark.unit
class TestListLimitParameterValidation:
    """Unit tests for limit parameter validation.

    Tests that invalid limit values are rejected with proper error handling.

    Expected Failure Mode:
    - limit parameter doesn't exist yet, so validation doesn't exist
    """

    def test_limit_parameter_rejects_zero_with_typer_exit_2(
        self, tmp_path: Path
    ) -> None:
        """Test limit=0 raises typer.Exit(2) with error message.

        Validates:
        - FR-443: limit must be > 0
        - Principle II: Exit code 2 for usage errors

        Expected to FAIL: limit parameter and validation not implemented.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        # Act & Assert: Should raise typer.Exit with code 2
        with pytest.raises(typer.Exit) as exc_info:
            list_conversations(file_path=test_file, format="text", limit=0)

        assert exc_info.value.exit_code == 2, "Should exit with code 2 for invalid limit"

    def test_limit_parameter_rejects_negative_with_typer_exit_2(
        self, tmp_path: Path
    ) -> None:
        """Test negative limit raises typer.Exit(2).

        Validates:
        - FR-443: limit must be > 0
        - Input validation

        Expected to FAIL: limit parameter and validation not implemented.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        # Act & Assert
        with pytest.raises(typer.Exit) as exc_info:
            list_conversations(file_path=test_file, format="text", limit=-5)

        assert exc_info.value.exit_code == 2

    def test_limit_parameter_error_message_written_to_stderr(
        self, tmp_path: Path
    ) -> None:
        """Test invalid limit writes error message to stderr.

        Validates:
        - Principle II: Errors to stderr
        - Clear error messages

        Expected to FAIL: limit parameter not implemented.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        stderr_messages: list[str] = []

        def capture_stderr(text: str, err: bool = False) -> None:
            if err:
                stderr_messages.append(text)

        with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_stderr):
            # Act
            try:
                list_conversations(file_path=test_file, format="text", limit=0)
            except typer.Exit:
                pass  # Expected

        # Assert: Error message on stderr mentions limit
        assert len(stderr_messages) > 0, "Should write error to stderr"
        error_text = " ".join(stderr_messages).lower()
        assert "limit" in error_text, "Error should mention limit parameter"


# =============================================================================
# Unit Tests - Edge Cases
# =============================================================================


@pytest.mark.unit
class TestListLimitEdgeCases:
    """Edge case unit tests for limit parameter."""

    def test_limit_parameter_with_empty_file_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Test limit with empty file returns empty array (not error).

        Validates:
        - FR-445: Empty file is success
        - FR-443: limit on empty returns []

        Expected to FAIL: limit parameter not implemented.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = []  # Empty
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Should not raise exception
                list_conversations(file_path=test_file, format="json", limit=10)

        # Assert: Empty array
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)
        assert data == [], "Empty file should return empty array"

    def test_limit_parameter_none_returns_all_conversations(
        self, tmp_path: Path
    ) -> None:
        """Test limit=None (default) returns all conversations (no limit).

        Validates:
        - FR-443: limit is optional, default behavior unchanged
        - Backwards compatibility

        Expected to FAIL: limit parameter not implemented.
        """
        # Arrange
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")

        conversations = []
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(10):
            created_at = base_time.replace(hour=i)
            conv = create_test_conversation(
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                created_at=created_at,
            )
            conversations.append(conv)

        with patch("echomine.cli.commands.list.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.stream_conversations.return_value = conversations
            mock_adapter_class.return_value = mock_adapter

            outputs: list[str] = []

            def capture_echo(text: str, nl: bool = True) -> None:
                outputs.append(text)

            with patch("echomine.cli.commands.list.typer.echo", side_effect=capture_echo):
                # Act: Call without limit parameter (or limit=None)
                # This tests default behavior when --limit flag not provided
                list_conversations(file_path=test_file, format="json")

        # Assert: All 10 conversations returned
        import json

        output = outputs[0] if outputs else "[]"
        data = json.loads(output)
        assert len(data) == 10, "Without limit, should return all conversations"
