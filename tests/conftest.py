"""Shared pytest fixtures for echomine tests.

This module provides common fixtures used across unit, integration, contract,
and performance tests. Fixtures are organized by scope and purpose.

Test Organization:
- tests/unit/: Unit tests for individual components
- tests/integration/: End-to-end workflow tests
- tests/contract/: Protocol and interface contract tests
- tests/performance/: Benchmark and performance tests

Fixture Naming Convention:
- `sample_*`: Pre-defined test data (conversations, messages, etc.)
- `tmp_*`: Temporary files/directories (auto-cleanup)
- `mock_*`: Mocked dependencies
- `fixture_*`: Test data generators
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_message_data() -> dict[str, Any]:
    """Sample OpenAI message data structure.

    Returns a minimal valid message dict matching OpenAI export format.
    Used for testing message parsing and validation.
    """
    return {
        "id": "msg-001",
        "author": {"role": "user"},
        "content": {"content_type": "text", "parts": ["Hello, world!"]},
        "create_time": 1700000000.0,
        "update_time": None,
        "metadata": {},
    }


@pytest.fixture
def sample_conversation_data() -> dict[str, Any]:
    """Sample OpenAI conversation data structure.

    Returns a minimal valid conversation dict matching OpenAI export format.
    Used for testing conversation parsing and validation.
    """
    return {
        "id": "conv-001",
        "title": "Test Conversation",
        "create_time": 1700000000.0,
        "update_time": 1700000100.0,
        "mapping": {
            "msg-001": {
                "id": "msg-001",
                "message": {
                    "id": "msg-001",
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["Hello"]},
                    "create_time": 1700000000.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": None,
                "children": ["msg-002"],
            },
            "msg-002": {
                "id": "msg-002",
                "message": {
                    "id": "msg-002",
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Hi! How can I help you today?"],
                    },
                    "create_time": 1700000010.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": "msg-001",
                "children": [],
            },
        },
        "moderation_results": [],
        "current_node": "msg-002",
    }


@pytest.fixture
def sample_export_data(sample_conversation_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Sample OpenAI export file data (array of conversations).

    Returns a list of conversation dicts representing a minimal valid export file.
    Used for testing file parsing and streaming.
    """
    return [sample_conversation_data]


# =============================================================================
# Temporary File Fixtures
# =============================================================================


@pytest.fixture
def tmp_export_file(tmp_path: Path, sample_export_data: list[dict[str, Any]]) -> Path:
    """Create a temporary OpenAI export JSON file.

    Args:
        tmp_path: pytest's temporary directory fixture
        sample_export_data: Sample conversation data

    Returns:
        Path to temporary export file (auto-cleaned up after test)

    Example:
        ```python
        def test_parse_export(tmp_export_file: Path):
            adapter = OpenAIAdapter()
            conversations = list(adapter.stream_conversations(tmp_export_file))
            assert len(conversations) == 1
        ```
    """
    export_file = tmp_path / "export.json"
    with export_file.open("w") as f:
        json.dump(sample_export_data, f, indent=2)
    return export_file


@pytest.fixture
def tmp_empty_export_file(tmp_path: Path) -> Path:
    """Create a temporary empty OpenAI export JSON file.

    Returns:
        Path to temporary empty export file (valid JSON array with no conversations)
    """
    export_file = tmp_path / "empty_export.json"
    with export_file.open("w") as f:
        json.dump([], f)
    return export_file


@pytest.fixture
def tmp_large_export_file(tmp_path: Path) -> Path:
    """Create a temporary large export file for performance testing.

    Generates 1000 conversations with 10 messages each (10K total messages).
    Used for benchmarking streaming performance.

    Returns:
        Path to temporary large export file
    """
    conversations = []
    for i in range(1000):
        messages_mapping = {}
        for j in range(10):
            msg_id = f"msg-{i}-{j}"
            parent_id = f"msg-{i}-{j - 1}" if j > 0 else None
            children_ids = [f"msg-{i}-{j + 1}"] if j < 9 else []

            messages_mapping[msg_id] = {
                "id": msg_id,
                "message": {
                    "id": msg_id,
                    "author": {"role": "user" if j % 2 == 0 else "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": [f"Message {j} content for conversation {i}"],
                    },
                    "create_time": 1700000000.0 + i * 100 + j,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": parent_id,
                "children": children_ids,
            }

        conversation = {
            "id": f"conv-{i:04d}",
            "title": f"Conversation {i}",
            "create_time": 1700000000.0 + i * 100,
            "update_time": 1700000000.0 + i * 100 + 90,
            "mapping": messages_mapping,
            "moderation_results": [],
            "current_node": f"msg-{i}-9",
        }
        conversations.append(conversation)

    export_file = tmp_path / "large_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)
    return export_file


# =============================================================================
# Timestamp Fixtures
# =============================================================================


@pytest.fixture
def fixed_datetime() -> datetime:
    """Fixed datetime for deterministic testing.

    Returns:
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    """
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers.

    Registers test markers for different test categories.
    """
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for end-to-end workflows")
    config.addinivalue_line("markers", "contract: Contract tests for protocols and interfaces")
    config.addinivalue_line("markers", "performance: Performance benchmarks and stress tests")
