"""Tests for provider auto-detection (FR-046 to FR-050).

This module tests the auto-detection of export providers (OpenAI vs Claude)
based on file structure analysis.

Test Coverage:
    - T077: Auto-detect Claude format from chat_messages key (FR-046, FR-047)
    - T078: Auto-detect OpenAI format from mapping key (FR-046, FR-048)
    - T079: Detect Claude via chat_messages key (FR-047)
    - T080: Detect OpenAI via mapping key (FR-048)
    - T081: --provider flag selects adapter explicitly (FR-049)
    - T082: Clear error for unrecognized format (FR-050)

Constitution Compliance:
    - Principle III: TDD - Tests written FIRST (RED phase)
    - Principle VI: Strict typing with mypy --strict
    - Principle VIII: O(1) memory usage with ijson streaming
"""

from __future__ import annotations

from pathlib import Path

import pytest


# T077, T079: Test auto-detection of Claude format
def test_auto_detect_claude_format(tmp_path: Path) -> None:
    """FR-046, FR-047: Auto-detect Claude format from chat_messages key.

    Given a JSON file with Claude export structure (chat_messages key)
    When detect_provider() is called
    Then it returns "claude"
    """
    from echomine.cli.provider import detect_provider

    # Create minimal Claude export with chat_messages key
    claude_file = tmp_path / "claude_export.json"
    claude_file.write_text(
        '[{"uuid": "test-001", "chat_messages": []}]',
        encoding="utf-8",
    )

    result = detect_provider(claude_file)
    assert result == "claude"


def test_detect_claude_via_chat_messages_key(tmp_path: Path) -> None:
    """FR-047: Detect Claude by presence of chat_messages key.

    Given a conversation object with chat_messages key
    When detect_provider() is called
    Then it identifies it as Claude format
    """
    from echomine.cli.provider import detect_provider

    # Create Claude export with more complete structure
    claude_file = tmp_path / "claude_full.json"
    claude_file.write_text(
        """[{
            "uuid": "5551eb71-ada2-45bd-8f91-0c4945a1e5a6",
            "name": "Test Conversation",
            "summary": "Test summary",
            "created_at": "2025-10-01T18:42:27.303515Z",
            "updated_at": "2025-10-01T18:42:33.904627Z",
            "chat_messages": [
                {
                    "uuid": "msg-001",
                    "text": "Hello",
                    "sender": "human",
                    "created_at": "2025-10-01T18:42:28.370875Z"
                }
            ]
        }]""",
        encoding="utf-8",
    )

    result = detect_provider(claude_file)
    assert result == "claude"


# T078, T080: Test auto-detection of OpenAI format
def test_auto_detect_openai_format(tmp_path: Path) -> None:
    """FR-046, FR-048: Auto-detect OpenAI format from mapping key.

    Given a JSON file with OpenAI export structure (mapping key)
    When detect_provider() is called
    Then it returns "openai"
    """
    from echomine.cli.provider import detect_provider

    # Create minimal OpenAI export with mapping key
    openai_file = tmp_path / "openai_export.json"
    openai_file.write_text(
        '[{"id": "conv-001", "mapping": {}}]',
        encoding="utf-8",
    )

    result = detect_provider(openai_file)
    assert result == "openai"


def test_detect_openai_via_mapping_key(tmp_path: Path) -> None:
    """FR-048: Detect OpenAI by presence of mapping key.

    Given a conversation object with mapping key
    When detect_provider() is called
    Then it identifies it as OpenAI format
    """
    from echomine.cli.provider import detect_provider

    # Create OpenAI export with more complete structure
    openai_file = tmp_path / "openai_full.json"
    openai_file.write_text(
        """[{
            "id": "conv-001",
            "title": "Test Conversation",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-001": {
                    "id": "msg-001",
                    "message": {
                        "id": "msg-001",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello"]}
                    }
                }
            }
        }]""",
        encoding="utf-8",
    )

    result = detect_provider(openai_file)
    assert result == "openai"


# T081: Test explicit provider selection via --provider flag
def test_get_adapter_explicit_provider() -> None:
    """FR-049: --provider flag explicitly selects adapter without file inspection.

    Given an explicit provider string ("claude" or "openai")
    When get_adapter() is called
    Then it returns the appropriate adapter without reading the file
    """
    from echomine.adapters.claude import ClaudeAdapter
    from echomine.adapters.openai import OpenAIAdapter
    from echomine.cli.provider import get_adapter

    # Test explicit "claude" selection
    adapter = get_adapter("claude", Path("any.json"))
    assert isinstance(adapter, ClaudeAdapter)

    # Test explicit "openai" selection
    adapter = get_adapter("openai", Path("any.json"))
    assert isinstance(adapter, OpenAIAdapter)


def test_get_adapter_auto_detect_claude(tmp_path: Path) -> None:
    """FR-049: get_adapter() auto-detects when provider is None.

    Given provider=None and a Claude export file
    When get_adapter() is called
    Then it auto-detects and returns ClaudeAdapter
    """
    from echomine.adapters.claude import ClaudeAdapter
    from echomine.cli.provider import get_adapter

    # Create Claude export
    claude_file = tmp_path / "claude.json"
    claude_file.write_text(
        '[{"uuid": "test-001", "chat_messages": []}]',
        encoding="utf-8",
    )

    # Auto-detect with provider=None
    adapter = get_adapter(None, claude_file)
    assert isinstance(adapter, ClaudeAdapter)


def test_get_adapter_auto_detect_openai(tmp_path: Path) -> None:
    """FR-049: get_adapter() auto-detects when provider is None.

    Given provider=None and an OpenAI export file
    When get_adapter() is called
    Then it auto-detects and returns OpenAIAdapter
    """
    from echomine.adapters.openai import OpenAIAdapter
    from echomine.cli.provider import get_adapter

    # Create OpenAI export
    openai_file = tmp_path / "openai.json"
    openai_file.write_text(
        '[{"id": "conv-001", "mapping": {}}]',
        encoding="utf-8",
    )

    # Auto-detect with provider=None
    adapter = get_adapter(None, openai_file)
    assert isinstance(adapter, OpenAIAdapter)


# T082: Test error handling for unrecognized formats
def test_unrecognized_format_error(tmp_path: Path) -> None:
    """FR-050: Clear error message for unrecognized export format.

    Given a JSON file without chat_messages or mapping keys
    When detect_provider() is called
    Then it raises ValueError with clear error message
    """
    from echomine.cli.provider import detect_provider

    # Create file with neither chat_messages nor mapping
    unrecognized = tmp_path / "unknown.json"
    unrecognized.write_text(
        '[{"id": "123", "title": "test", "data": "value"}]',
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        detect_provider(unrecognized)

    error_msg = str(exc_info.value)
    assert "Unsupported export format" in error_msg
    assert "mapping" in error_msg  # Should mention OpenAI key
    assert "chat_messages" in error_msg  # Should mention Claude key


def test_empty_file_defaults_to_openai(tmp_path: Path) -> None:
    """Empty export file defaults to OpenAI for backwards compatibility.

    Given an empty JSON array
    When detect_provider() is called
    Then it defaults to "openai" provider (backwards compatible behavior)

    Note: Empty JSON arrays are valid exports with zero conversations.
    We default to OpenAI as the original provider for compatibility.
    """
    from echomine.cli.provider import detect_provider

    # Create empty JSON array
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]", encoding="utf-8")

    # Empty files default to OpenAI for backwards compatibility
    result = detect_provider(empty_file)
    assert result == "openai"


def test_invalid_json_error(tmp_path: Path) -> None:
    """FR-050: Clear error for malformed JSON.

    Given a file with invalid JSON syntax
    When detect_provider() is called
    Then it raises ValueError mentioning JSON error
    """
    from echomine.cli.provider import detect_provider

    # Create file with invalid JSON
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        detect_provider(invalid_file)

    assert "Invalid JSON" in str(exc_info.value)


# Edge case: Test with actual fixture files
def test_detect_real_claude_fixture() -> None:
    """Integration test: Detect real Claude fixture file.

    Given the actual Claude sample export fixture
    When detect_provider() is called
    Then it correctly identifies it as Claude format
    """
    from echomine.cli.provider import detect_provider

    fixture_path = Path("tests/fixtures/claude/sample_export.json")
    if not fixture_path.exists():
        pytest.skip("Claude fixture file not found")

    result = detect_provider(fixture_path)
    assert result == "claude"


def test_detect_real_openai_fixture() -> None:
    """Integration test: Detect real OpenAI fixture file.

    Given the actual OpenAI sample export fixture
    When detect_provider() is called
    Then it correctly identifies it as OpenAI format
    """
    from echomine.cli.provider import detect_provider

    fixture_path = Path("tests/fixtures/sample_export.json")
    if not fixture_path.exists():
        pytest.skip("OpenAI fixture file not found")

    result = detect_provider(fixture_path)
    assert result == "openai"
