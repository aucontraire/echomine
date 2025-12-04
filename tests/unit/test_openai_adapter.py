"""Unit tests for OpenAI adapter coverage gaps.

This module tests specific OpenAI adapter features that were missing coverage:
- on_skip callback in stream_conversations (FR-107)
- progress_callback in search (FR-069)
- Multimodal/image parsing (_parse_multimodal_parts)

Constitution Compliance:
    - Principle III: Test-driven development
    - FR-107: on_skip callback for malformed entries
    - FR-069: Progress callback invocation
    - FR-018: Multimodal content parsing

Test Strategy:
    - AAA pattern (Arrange, Act, Assert)
    - Test callback invocation with real data
    - Test edge cases in multimodal parsing
"""

from __future__ import annotations

import json
from pathlib import Path

from echomine.adapters import OpenAIAdapter
from echomine.models.image import ImageRef
from echomine.models.search import SearchQuery


# ============================================================================
# Test on_skip Callback (FR-107)
# ============================================================================


class TestOnSkipCallback:
    """Test on_skip callback functionality in stream_conversations.

    Coverage Target: src/echomine/adapters/openai.py line 209
    """

    def test_stream_conversations_on_skip_callback_invoked(self, tmp_path: Path) -> None:
        """Test on_skip callback is invoked when malformed conversation encountered.

        Validates:
        - openai.py line 209: on_skip callback invoked with conversation_id and reason
        - Callback receives correct parameters
        - Processing continues after skip
        """
        # Arrange: Create export with malformed and valid conversations
        data = [
            {
                # Missing required field 'title' - will trigger ValidationError
                "id": "conv-malformed",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {},
                "moderation_results": [],
                "current_node": None,
            },
            {
                "id": "conv-valid",
                "title": "Valid Conversation",
                "create_time": 1700100000.0,
                "update_time": 1700101000.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1700100000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            },
        ]

        file = tmp_path / "test_skip.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Track callback invocations
        skip_calls: list[tuple[str, str]] = []

        def on_skip_handler(conversation_id: str, reason: str) -> None:
            skip_calls.append((conversation_id, reason))

        # Act: Stream with on_skip callback
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file, on_skip=on_skip_handler))

        # Assert: Callback was invoked for malformed conversation
        assert len(skip_calls) == 1
        assert skip_calls[0][0] == "conv-malformed"
        assert "validation error" in skip_calls[0][1].lower()

        # Assert: Valid conversation was still processed
        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"
        assert conversations[0].title == "Valid Conversation"

    def test_stream_conversations_without_on_skip_callback(self, tmp_path: Path) -> None:
        """Test stream_conversations continues without on_skip callback (optional).

        Validates:
        - on_skip parameter is optional (None by default)
        - Processing continues normally without callback
        """
        # Arrange: Same data as above
        data = [
            {
                "id": "conv-malformed",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {},
            },
            {
                "id": "conv-valid",
                "title": "Valid Conversation",
                "create_time": 1700100000.0,
                "update_time": 1700101000.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Test"]},
                            "create_time": 1700100000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            },
        ]

        file = tmp_path / "test_no_callback.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Act: Stream without on_skip callback
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        # Assert: Valid conversation still processed
        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"


# ============================================================================
# Test Progress Callback in Search (FR-069)
# ============================================================================


class TestSearchProgressCallback:
    """Test progress_callback functionality in search method.

    Coverage Target: src/echomine/adapters/openai.py line 291
    """

    def test_search_progress_callback_invoked(self, tmp_path: Path) -> None:
        """Test progress callback is invoked during search processing.

        Validates:
        - openai.py line 291: progress_callback invoked every 100 conversations
        - Callback receives correct count
        """
        # Arrange: Create export with 250 conversations (triggers callback 2x)
        data = []
        for i in range(250):
            data.append(
                {
                    "id": f"conv-{i:03d}",
                    "title": f"Conversation {i}",
                    "create_time": 1700000000.0 + i,
                    "update_time": 1700001000.0 + i,
                    "mapping": {
                        f"msg-{i:03d}": {
                            "id": f"msg-{i:03d}",
                            "message": {
                                "id": f"msg-{i:03d}",
                                "author": {"role": "user"},
                                "content": {"content_type": "text", "parts": [f"Message {i}"]},
                                "create_time": 1700000000.0 + i,
                                "update_time": None,
                                "metadata": {},
                            },
                            "parent": None,
                            "children": [],
                        }
                    },
                    "moderation_results": [],
                    "current_node": f"msg-{i:03d}",
                }
            )

        file = tmp_path / "test_search_progress.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Track callback invocations
        progress_calls: list[int] = []

        def progress_handler(count: int) -> None:
            progress_calls.append(count)

        # Act: Search with progress callback
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["Message"])
        results = list(adapter.search(file, query, progress_callback=progress_handler))

        # Assert: Callback was invoked at 100, 200, and final count (250)
        assert len(progress_calls) >= 3
        assert 100 in progress_calls
        assert 200 in progress_calls
        assert 250 in progress_calls  # Final callback

        # Assert: Search still returns results
        assert len(results) > 0

    def test_search_without_progress_callback(self, tmp_path: Path) -> None:
        """Test search works without progress_callback (optional parameter).

        Validates:
        - progress_callback parameter is optional
        - Search completes normally without callback
        """
        # Arrange: Small export
        data = [
            {
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
                            "content": {"content_type": "text", "parts": ["Python code"]},
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            }
        ]

        file = tmp_path / "test_no_progress.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Act: Search without progress callback
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["Python"])
        results = list(adapter.search(file, query))

        # Assert: Results returned normally
        assert len(results) == 1
        assert results[0].conversation.id == "conv-001"


# ============================================================================
# Test Multimodal/Image Parsing (FR-018)
# ============================================================================


class TestMultimodalParsing:
    """Test multimodal content parsing in OpenAI adapter.

    Coverage Target: src/echomine/adapters/openai.py lines 950-996
    """

    def test_parse_multimodal_parts_with_image_asset_pointer(self) -> None:
        """Test parsing multimodal_text with image_asset_pointer content type.

        Validates:
        - openai.py lines 960-983: image_asset_pointer parsing
        - ImageRef extraction from multimodal parts
        """
        # Arrange
        adapter = OpenAIAdapter()
        parts = [
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "sediment://file_abc123",
                "size_bytes": 89512,
                "width": 1536,
                "height": 503,
            },
            "Here is the diagram you requested",
        ]

        # Act
        text, images = adapter._parse_multimodal_parts(parts)

        # Assert: Text extracted correctly
        assert text == "Here is the diagram you requested"

        # Assert: Image extracted correctly
        assert len(images) == 1
        assert isinstance(images[0], ImageRef)
        assert images[0].asset_pointer == "sediment://file_abc123"
        assert images[0].size_bytes == 89512
        assert images[0].width == 1536
        assert images[0].height == 503

    def test_parse_multimodal_parts_with_image_content_type(self, tmp_path: Path) -> None:
        """Test parsing message with 'image' content type.

        Validates:
        - openai.py line 840-842: 'image' content type handling
        - Placeholder text for image messages
        """
        # Arrange: Create conversation with image content type
        data = [
            {
                "id": "conv-001",
                "title": "Image Test",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {
                                "content_type": "image",
                                "image_url": "https://example.com/image.jpg",
                            },
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            }
        ]

        file = tmp_path / "test_image_content.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        # Assert: Image placeholder used
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == "[Image]"

    def test_parse_multimodal_parts_with_code_content_type(self, tmp_path: Path) -> None:
        """Test parsing message with 'code' content type.

        Validates:
        - openai.py lines 843-850: 'code' content type handling
        - Code content extraction from parts
        """
        # Arrange: Create conversation with code content type
        data = [
            {
                "id": "conv-001",
                "title": "Code Test",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "assistant"},
                            "content": {
                                "content_type": "code",
                                "parts": ["print('Hello, World!')"],
                            },
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            }
        ]

        file = tmp_path / "test_code_content.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        # Assert: Code content extracted
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == "print('Hello, World!')"

    def test_parse_multimodal_parts_unknown_content_type(self, tmp_path: Path) -> None:
        """Test parsing message with unknown content type (fallback behavior).

        Validates:
        - openai.py lines 851-853: Unknown content type fallback
        - Placeholder format: [content_type]
        """
        # Arrange: Create conversation with unknown content type
        data = [
            {
                "id": "conv-001",
                "title": "Unknown Content Test",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {
                    "msg-001": {
                        "id": "msg-001",
                        "message": {
                            "id": "msg-001",
                            "author": {"role": "user"},
                            "content": {
                                "content_type": "future_feature_xyz",
                            },
                            "create_time": 1700000000.0,
                            "update_time": None,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
                "moderation_results": [],
                "current_node": "msg-001",
            }
        ]

        file = tmp_path / "test_unknown_content.json"
        file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        # Assert: Unknown content type uses placeholder
        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == "[future_feature_xyz]"

    def test_parse_multimodal_parts_multiple_images(self) -> None:
        """Test parsing multimodal parts with multiple images and text.

        Validates:
        - openai.py line 950-996: Multiple image handling
        - Text concatenation with spaces
        """
        # Arrange
        adapter = OpenAIAdapter()
        parts = [
            "Here are two images:",
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "sediment://file_image1",
                "size_bytes": 10000,
                "width": 800,
                "height": 600,
            },
            "and another one:",
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "sediment://file_image2",
                "size_bytes": 20000,
                "width": 1024,
                "height": 768,
            },
            "Both images shown above.",
        ]

        # Act
        text, images = adapter._parse_multimodal_parts(parts)

        # Assert: All text parts concatenated with spaces
        assert text == "Here are two images: and another one: Both images shown above."

        # Assert: Both images extracted
        assert len(images) == 2
        assert images[0].asset_pointer == "sediment://file_image1"
        assert images[0].size_bytes == 10000
        assert images[1].asset_pointer == "sediment://file_image2"
        assert images[1].size_bytes == 20000

    def test_parse_multimodal_parts_empty_asset_pointer(self) -> None:
        """Test parsing multimodal parts with empty asset_pointer (edge case).

        Validates:
        - openai.py line 964: Skip image if asset_pointer is empty
        - Graceful handling of malformed image data
        """
        # Arrange
        adapter = OpenAIAdapter()
        parts = [
            "Some text",
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "",  # Empty asset pointer
                "size_bytes": 1000,
            },
            "More text",
        ]

        # Act
        text, images = adapter._parse_multimodal_parts(parts)

        # Assert: Text extracted
        assert text == "Some text More text"

        # Assert: Image with empty asset_pointer skipped
        assert len(images) == 0

    def test_parse_multimodal_parts_non_image_dict(self) -> None:
        """Test parsing multimodal parts with non-image dict entries.

        Validates:
        - openai.py lines 988-990: Skip non-image dict parts
        - Graceful handling of unexpected structures
        """
        # Arrange
        adapter = OpenAIAdapter()
        parts = [
            "Text part",
            {
                "content_type": "some_other_type",
                "data": "not an image",
            },
            "Another text part",
        ]

        # Act
        text, images = adapter._parse_multimodal_parts(parts)

        # Assert: Text extracted
        assert text == "Text part Another text part"

        # Assert: Non-image dict skipped
        assert len(images) == 0
