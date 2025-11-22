"""Integration tests for User Story 0: List All Conversations.

Task: T026 - Integration Test - End-to-end list workflow
Phase: RED (tests designed to FAIL initially)

This module tests the complete end-to-end workflow for listing conversations:
1. Read OpenAI export JSON file from disk
2. Stream parse conversations using ijson
3. Transform to unified Conversation models via OpenAIAdapter
4. Format output using CLI formatter
5. Verify output matches specification

Test Pyramid Classification: Integration (20% of test suite)
These tests validate component integration but NOT CLI interface.

Architectural Coverage:
- StreamingParser → OpenAIAdapter → ConversationProvider protocol
- File I/O → JSON streaming → Model transformation
- Memory efficiency validation (streaming, not buffering)

Fixtures Required:
- sample_export_realistic.json: 10 conversations with realistic OpenAI data
- Edge cases: empty export, single conversation, large messages, Unicode content
"""

from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation


# =============================================================================
# Integration Test Fixtures (Realistic OpenAI Export Data)
# =============================================================================


@pytest.fixture
def realistic_openai_export(tmp_path: Path) -> Path:
    """Create realistic OpenAI export fixture with 10 conversations.

    This fixture represents ACTUAL OpenAI export structure based on
    documented schema. Used to validate real-world integration.

    Structure:
    - 10 conversations with varied characteristics
    - Realistic message counts (2-30 messages)
    - Proper threading structure (parent/child relationships)
    - Mixed roles (user, assistant, system)
    - Realistic timestamps (2024 dates)
    - Unicode content (emojis, code blocks, special chars)
    - Edge cases: empty conversations, long titles

    Returns:
        Path to temporary realistic export file
    """
    import json

    conversations = [
        # Conversation 1: Simple Q&A (2 messages)
        {
            "id": "conv-001",
            "title": "Python list comprehension basics",
            "create_time": 1710000000.0,  # 2024-03-09
            "update_time": 1710000100.0,
            "mapping": {
                "msg-001-1": {
                    "id": "msg-001-1",
                    "message": {
                        "id": "msg-001-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["How do I write a list comprehension in Python?"],
                        },
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-001-2"],
                },
                "msg-001-2": {
                    "id": "msg-001-2",
                    "message": {
                        "id": "msg-001-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "List comprehensions provide a concise way to create lists. "
                                "Syntax: [expression for item in iterable if condition]"
                            ],
                        },
                        "create_time": 1710000050.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-001-2",
        },
        # Conversation 2: Multi-turn with threading (5 messages)
        {
            "id": "conv-002",
            "title": "Async/await in JavaScript deep dive 🚀",
            "create_time": 1710100000.0,
            "update_time": 1710100400.0,
            "mapping": {
                "msg-002-1": {
                    "id": "msg-002-1",
                    "message": {
                        "id": "msg-002-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain async/await in JavaScript"],
                        },
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-002-2"],
                },
                "msg-002-2": {
                    "id": "msg-002-2",
                    "message": {
                        "id": "msg-002-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "async/await is syntactic sugar for Promises. "
                                "An async function returns a Promise."
                            ],
                        },
                        "create_time": 1710100100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-1",
                    "children": ["msg-002-3"],
                },
                "msg-002-3": {
                    "id": "msg-002-3",
                    "message": {
                        "id": "msg-002-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Can you show an example?"],
                        },
                        "create_time": 1710100200.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-2",
                    "children": ["msg-002-4"],
                },
                "msg-002-4": {
                    "id": "msg-002-4",
                    "message": {
                        "id": "msg-002-4",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "```javascript\nasync function fetchData() {\n  "
                                "const response = await fetch('/api/data');\n  "
                                "return response.json();\n}\n```"
                            ],
                        },
                        "create_time": 1710100300.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-3",
                    "children": ["msg-002-5"],
                },
                "msg-002-5": {
                    "id": "msg-002-5",
                    "message": {
                        "id": "msg-002-5",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Thanks! That's clear now."],
                        },
                        "create_time": 1710100400.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-4",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-002-5",
        },
        # Conversation 3: Long title edge case
        {
            "id": "conv-003",
            "title": (
                "How to implement a production-ready microservices architecture "
                "with Kubernetes, Docker, and CI/CD pipeline integration"
            ),
            "create_time": 1710200000.0,
            "update_time": 1710200050.0,
            "mapping": {
                "msg-003-1": {
                    "id": "msg-003-1",
                    "message": {
                        "id": "msg-003-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["I need help with microservices"],
                        },
                        "create_time": 1710200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-003-2"],
                },
                "msg-003-2": {
                    "id": "msg-003-2",
                    "message": {
                        "id": "msg-003-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Let me help you design your architecture."],
                        },
                        "create_time": 1710200050.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-003-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-003-2",
        },
        # Conversation 4: Unicode edge case (Chinese, emojis, special chars)
        {
            "id": "conv-004",
            "title": "学习中文编程 🇨🇳 (Learning Chinese Programming)",
            "create_time": 1710300000.0,
            "update_time": 1710300100.0,
            "mapping": {
                "msg-004-1": {
                    "id": "msg-004-1",
                    "message": {
                        "id": "msg-004-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["如何学习Python? 💻"],
                        },
                        "create_time": 1710300000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-004-2"],
                },
                "msg-004-2": {
                    "id": "msg-004-2",
                    "message": {
                        "id": "msg-004-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Python很容易学习！✨ Start with basics."],
                        },
                        "create_time": 1710300100.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-004-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-004-2",
        },
        # Conversations 5-10: Additional variety (simplified for brevity)
        *[
            {
                "id": f"conv-{i:03d}",
                "title": f"Test conversation {i}",
                "create_time": 1710000000.0 + (i * 100000),
                "update_time": 1710000000.0 + (i * 100000) + 1000,
                "mapping": {
                    f"msg-{i:03d}-1": {
                        "id": f"msg-{i:03d}-1",
                        "message": {
                            "id": f"msg-{i:03d}-1",
                            "author": {"role": "user"},
                            "content": {
                                "content_type": "text",
                                "parts": [f"Question {i}"],
                            },
                            "create_time": 1710000000.0 + (i * 100000),
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [f"msg-{i:03d}-2"],
                    },
                    f"msg-{i:03d}-2": {
                        "id": f"msg-{i:03d}-2",
                        "message": {
                            "id": f"msg-{i:03d}-2",
                            "author": {"role": "assistant"},
                            "content": {
                                "content_type": "text",
                                "parts": [f"Answer {i}"],
                            },
                            "create_time": 1710000000.0 + (i * 100000) + 500,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": f"msg-{i:03d}-1",
                        "children": [],
                    },
                },
                "moderation_results": [],
                "current_node": f"msg-{i:03d}-2",
            }
            for i in range(5, 11)
        ],
    ]

    export_file = tmp_path / "realistic_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


@pytest.fixture
def empty_openai_export(tmp_path: Path) -> Path:
    """Create empty OpenAI export (valid JSON array, zero conversations).

    Tests edge case: empty file should succeed, not error.
    """
    import json

    export_file = tmp_path / "empty_export.json"
    with export_file.open("w") as f:
        json.dump([], f)
    return export_file


# =============================================================================
# T026: End-to-End Integration Tests (RED Phase - DESIGNED TO FAIL)
# =============================================================================


@pytest.mark.integration
class TestListConversationsIntegration:
    """Integration tests for list conversations workflow.

    Tests the complete chain: File → Parser → Adapter → Models
    Does NOT test CLI interface (that's T027 contract tests).

    Expected Failure Reasons (RED phase):
    - OpenAIAdapter class doesn't exist yet
    - stream_conversations() method doesn't exist
    - Conversation model may not be complete
    - Streaming parser integration not implemented
    """

    def test_list_all_conversations_from_realistic_export(
        self, realistic_openai_export: Path
    ) -> None:
        """Test streaming all conversations from realistic OpenAI export.

        Validates:
        - FR-018: List all conversations with metadata
        - FR-003: Streaming implementation (O(1) memory)
        - FR-222-227: Conversation model immutability

        Expected to FAIL: OpenAIAdapter not implemented yet.
        """
        # Arrange: Create adapter (WILL FAIL - class doesn't exist)
        adapter = OpenAIAdapter()

        # Act: Stream conversations (WILL FAIL - method doesn't exist)
        conversations = list(adapter.stream_conversations(realistic_openai_export))

        # Assert: Verify we got all 10 conversations
        assert len(conversations) == 10, "Should parse all 10 conversations"

        # Verify first conversation structure
        first_conv = conversations[0]
        assert isinstance(first_conv, Conversation)
        assert first_conv.id == "conv-001"
        assert first_conv.title == "Python list comprehension basics"
        assert first_conv.message_count == 2

        # Verify conversation with emoji/Unicode
        unicode_conv = next(c for c in conversations if c.id == "conv-004")
        assert "学习中文编程" in unicode_conv.title
        assert "🇨🇳" in unicode_conv.title

        # Verify long title handling
        long_title_conv = next(c for c in conversations if c.id == "conv-003")
        assert len(long_title_conv.title) > 100

    def test_stream_conversations_is_lazy_iterator(
        self, realistic_openai_export: Path
    ) -> None:
        """Test that streaming doesn't load entire file into memory.

        Validates:
        - FR-003: O(1) memory complexity via streaming
        - SC-001: Memory usage <1GB for large files

        Expected to FAIL: stream_conversations not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Get iterator WITHOUT consuming it
        iterator = adapter.stream_conversations(realistic_openai_export)

        # Assert: Should be generator/iterator, not list
        assert hasattr(iterator, "__iter__") and hasattr(iterator, "__next__"), (
            "stream_conversations must return iterator, not list "
            "(streaming requirement)"
        )

        # Verify we can consume it lazily
        first = next(iterator)
        assert isinstance(first, Conversation)

        second = next(iterator)
        assert isinstance(second, Conversation)
        assert second.id != first.id  # Different conversations

    def test_empty_export_yields_no_conversations(
        self, empty_openai_export: Path
    ) -> None:
        """Test that empty export file is handled gracefully.

        Validates:
        - Edge case: Empty array should succeed, not error
        - FR-033: Graceful error handling

        Expected to FAIL: OpenAIAdapter not implemented.
        """
        adapter = OpenAIAdapter()

        conversations = list(adapter.stream_conversations(empty_openai_export))

        assert len(conversations) == 0, "Empty export should yield zero conversations"

    def test_conversations_are_immutable(self, realistic_openai_export: Path) -> None:
        """Test that returned Conversation objects are immutable.

        Validates:
        - FR-222: Conversation immutability via frozen=True
        - Pydantic frozen model behavior

        Expected to FAIL: Conversation model may not be frozen.
        """
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(realistic_openai_export))

        first_conv = conversations[0]

        # Assert: Modifying frozen field should raise error
        with pytest.raises(Exception):  # Pydantic raises ValidationError or AttributeError
            first_conv.title = "Modified title"  # type: ignore[misc]

    def test_message_count_is_accurate(self, realistic_openai_export: Path) -> None:
        """Test that message_count reflects actual number of messages.

        Validates:
        - FR-018: Metadata includes message count
        - Message counting logic accuracy

        Expected to FAIL: message_count property not implemented.
        """
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(realistic_openai_export))

        # Verify specific message counts
        conv_001 = next(c for c in conversations if c.id == "conv-001")
        assert conv_001.message_count == 2, "conv-001 has 2 messages"

        conv_002 = next(c for c in conversations if c.id == "conv-002")
        assert conv_002.message_count == 5, "conv-002 has 5 messages (multi-turn)"

    def test_timestamps_are_parsed_correctly(
        self, realistic_openai_export: Path
    ) -> None:
        """Test that Unix timestamps are converted to datetime objects.

        Validates:
        - FR-222: created_at and updated_at as datetime
        - Timezone handling (UTC)

        Expected to FAIL: Timestamp conversion not implemented.
        """
        from datetime import UTC, datetime

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(realistic_openai_export))

        first_conv = conversations[0]

        # Assert: Timestamps should be datetime objects
        assert isinstance(first_conv.created_at, datetime)
        assert isinstance(first_conv.updated_at, datetime)

        # Verify timezone is UTC
        assert first_conv.created_at.tzinfo == UTC
        assert first_conv.updated_at.tzinfo == UTC

        # Verify timestamp values
        assert first_conv.created_at.year == 2024
        assert first_conv.updated_at >= first_conv.created_at

    def test_invalid_json_raises_parse_error(self, tmp_path: Path) -> None:
        """Test that malformed JSON raises ParseError.

        Validates:
        - FR-033: Fail fast on invalid JSON
        - Proper exception handling

        Expected to FAIL: ParseError exception not defined.
        """
        from echomine.exceptions import ParseError

        # Arrange: Create malformed JSON file
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{invalid json")

        adapter = OpenAIAdapter()

        # Assert: Should raise ParseError
        with pytest.raises(ParseError, match="Invalid JSON"):
            list(adapter.stream_conversations(malformed_file))

    def test_missing_required_field_raises_validation_error(
        self, tmp_path: Path
    ) -> None:
        """Test that conversations missing required fields raise ValidationError.

        Validates:
        - FR-222-227: Pydantic validation enforces required fields
        - Fail fast on schema violations

        Expected to FAIL: ValidationError handling not implemented.
        """
        import json

        from echomine.exceptions import ValidationError

        # Arrange: Conversation missing 'title' field
        invalid_conversation = {
            "id": "conv-invalid",
            # "title": MISSING!
            "create_time": 1710000000.0,
            "update_time": 1710000100.0,
            "mapping": {},
            "moderation_results": [],
            "current_node": None,
        }

        invalid_file = tmp_path / "invalid_export.json"
        with invalid_file.open("w") as f:
            json.dump([invalid_conversation], f)

        adapter = OpenAIAdapter()

        # Assert: Should raise ValidationError
        with pytest.raises(ValidationError, match="title"):
            list(adapter.stream_conversations(invalid_file))

    def test_file_not_found_raises_error(self) -> None:
        """Test that non-existent file raises FileNotFoundError.

        Validates:
        - FR-033: Proper error handling for file I/O
        - Python standard exceptions

        Expected to FAIL: May not handle file errors correctly.
        """
        adapter = OpenAIAdapter()
        non_existent_file = Path("/tmp/does_not_exist_123456789.json")

        with pytest.raises(FileNotFoundError):
            list(adapter.stream_conversations(non_existent_file))


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


@pytest.mark.integration
class TestEdgeCases:
    """Edge case integration tests for list operation."""

    def test_large_message_content_does_not_break_parsing(
        self, tmp_path: Path
    ) -> None:
        """Test that conversations with very large messages parse correctly.

        Validates:
        - FR-003: Streaming handles large individual messages
        - No memory issues with large content

        Expected to FAIL: Large content handling not implemented.
        """
        import json

        # Create conversation with 1MB message content
        large_content = "x" * (1024 * 1024)  # 1MB of 'x'

        conversation = {
            "id": "conv-large",
            "title": "Large message test",
            "create_time": 1710000000.0,
            "update_time": 1710000100.0,
            "mapping": {
                "msg-large-1": {
                    "id": "msg-large-1",
                    "message": {
                        "id": "msg-large-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [large_content]},
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-large-1",
        }

        large_file = tmp_path / "large_message_export.json"
        with large_file.open("w") as f:
            json.dump([conversation], f)

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(large_file))

        assert len(conversations) == 1
        assert conversations[0].id == "conv-large"
        assert conversations[0].message_count == 1
