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

from pathlib import Path

import pytest

from echomine.adapters import OpenAIAdapter
from echomine.models.image import ImageRef
from echomine.models.search import SearchQuery
from tests.factories import (
    make_openai_conversation,
    make_openai_export,
    make_openai_message,
    write_export,
)


# ============================================================================
# Test on_skip Callback (FR-107)
# ============================================================================


class TestOnSkipCallback:
    """Test on_skip callback functionality in stream_conversations."""

    def test_stream_conversations_on_skip_callback_invoked(self, tmp_path: Path) -> None:
        data = [
            {
                "id": "conv-malformed",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {},
                "moderation_results": [],
                "current_node": None,
            },
            make_openai_conversation(
                [make_openai_message(create_time=1700100000.0)],
                conv_id="conv-valid",
                title="Valid Conversation",
                create_time=1700100000.0,
                update_time=1700101000.0,
            ),
        ]

        file = write_export(data, tmp_path / "test_skip.json")

        skip_calls: list[tuple[str, str]] = []

        def on_skip_handler(conversation_id: str, reason: str) -> None:
            skip_calls.append((conversation_id, reason))

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file, on_skip=on_skip_handler))

        assert len(skip_calls) == 1
        assert skip_calls[0][0] == "conv-malformed"
        assert "validation error" in skip_calls[0][1].lower()

        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"
        assert conversations[0].title == "Valid Conversation"

    def test_stream_conversations_without_on_skip_callback(self, tmp_path: Path) -> None:
        data = [
            {
                "id": "conv-malformed",
                "create_time": 1700000000.0,
                "update_time": 1700001000.0,
                "mapping": {},
            },
            make_openai_conversation(
                [make_openai_message(create_time=1700100000.0)],
                conv_id="conv-valid",
                title="Valid Conversation",
                create_time=1700100000.0,
                update_time=1700101000.0,
            ),
        ]

        file = write_export(data, tmp_path / "test_no_callback.json")

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        assert len(conversations) == 1
        assert conversations[0].id == "conv-valid"


# ============================================================================
# Test Progress Callback in Search (FR-069)
# ============================================================================


class TestSearchProgressCallback:
    """Test progress_callback functionality in search method."""

    def test_search_progress_callback_invoked(self, tmp_path: Path) -> None:
        data = [
            make_openai_conversation(
                [
                    make_openai_message(
                        id=f"msg-{i:03d}",
                        parts=[f"Message {i}"],
                        create_time=1700000000.0 + i,
                    )
                ],
                conv_id=f"conv-{i:03d}",
                title=f"Conversation {i}",
                create_time=1700000000.0 + i,
                update_time=1700001000.0 + i,
            )
            for i in range(250)
        ]

        file = write_export(data, tmp_path / "test_search_progress.json")

        progress_calls: list[int] = []

        def progress_handler(count: int) -> None:
            progress_calls.append(count)

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["Message"])
        results = list(adapter.search(file, query, progress_callback=progress_handler))

        assert len(progress_calls) >= 3
        assert 100 in progress_calls
        assert 200 in progress_calls
        assert 250 in progress_calls

        assert len(results) > 0

    def test_search_without_progress_callback(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(parts=["Python code"])],
            conv_id="conv-001",
            title="Test Conversation",
        )

        file = write_export(data, tmp_path / "test_no_progress.json")

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["Python"])
        results = list(adapter.search(file, query))

        assert len(results) == 1
        assert results[0].conversation.id == "conv-001"


# ============================================================================
# Test Multimodal/Image Parsing (FR-018)
# ============================================================================


class TestMultimodalParsing:
    """Test multimodal content parsing in OpenAI adapter."""

    def test_parse_multimodal_parts_with_image_asset_pointer(self) -> None:
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

        text, images = adapter._parse_multimodal_parts(parts)

        assert text == "Here is the diagram you requested"
        assert len(images) == 1
        assert isinstance(images[0], ImageRef)
        assert images[0].asset_pointer == "sediment://file_abc123"
        assert images[0].size_bytes == 89512
        assert images[0].width == 1536
        assert images[0].height == 503

    def test_parse_multimodal_parts_with_image_content_type(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    content={"content_type": "image", "image_url": "https://example.com/image.jpg"},
                )
            ],
            title="Image Test",
        )

        file = write_export(data, tmp_path / "test_image_content.json")

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == ""

    def test_parse_multimodal_parts_with_code_content_type(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="assistant", content_type="code", parts=["print('Hello, World!')"]
                )
            ],
            title="Code Test",
        )
        file = write_export(data, tmp_path / "test_code_content.json")

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == ""
        assert conversations[0].messages[0].metadata["content_type_category"] == "tool_io"

    def test_parse_multimodal_parts_unknown_content_type(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(content_type="future_feature_xyz")],
            title="Unknown Content Test",
        )
        file = write_export(data, tmp_path / "test_unknown_content.json")

        adapter = OpenAIAdapter()
        conversations = list(adapter.stream_conversations(file))

        assert len(conversations) == 1
        assert len(conversations[0].messages) == 1
        assert conversations[0].messages[0].content == ""
        assert conversations[0].messages[0].metadata["content_type_category"] == "unknown"

    def test_parse_multimodal_parts_multiple_images(self) -> None:
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

        text, images = adapter._parse_multimodal_parts(parts)

        assert text == "Here are two images:\nand another one:\nBoth images shown above."
        assert len(images) == 2
        assert images[0].asset_pointer == "sediment://file_image1"
        assert images[0].size_bytes == 10000
        assert images[1].asset_pointer == "sediment://file_image2"
        assert images[1].size_bytes == 20000

    def test_parse_multimodal_parts_empty_asset_pointer(self) -> None:
        adapter = OpenAIAdapter()
        parts = [
            "Some text",
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "",
                "size_bytes": 1000,
            },
            "More text",
        ]

        text, images = adapter._parse_multimodal_parts(parts)

        assert text == "Some text\nMore text"
        assert len(images) == 0

    def test_parse_multimodal_parts_non_image_dict(self) -> None:
        adapter = OpenAIAdapter()
        parts = [
            "Text part",
            {
                "content_type": "some_other_type",
                "data": "not an image",
            },
            "Another text part",
        ]

        text, images = adapter._parse_multimodal_parts(parts)

        assert text == "Text part\nAnother text part"
        assert len(images) == 0


# ============================================================================
# Test Content Type Classification (FR-001, FR-002, FR-003) — T007
# ============================================================================


class TestOpenAIContentTypeClassification:
    """Verify content_type and content_type_category metadata on every message."""

    @pytest.mark.parametrize(
        ("content_type", "expected_category", "expected_content"),
        [
            ("text", "conversational", "Hello"),
            ("multimodal_text", "conversational", "Check this"),
            ("thoughts", "reasoning", ""),
            ("reasoning_recap", "reasoning", ""),
            ("code", "tool_io", ""),
            ("execution_output", "tool_io", ""),
            ("tether_quote", "tool_io", ""),
            ("tether_browsing_display", "tool_io", ""),
            ("user_editable_context", "system", ""),
            ("app_pairing_content", "system", ""),
            ("system_error", "system", ""),
        ],
    )
    def test_content_type_metadata(
        self,
        tmp_path: Path,
        content_type: str,
        expected_category: str,
        expected_content: str,
    ) -> None:
        parts: list[object] = ["Hello"] if content_type == "text" else []
        if content_type == "multimodal_text":
            parts = ["Check this"]
        elif content_type not in ("text", "image_asset_pointer", "image"):
            parts = ["some raw data"]
        data = make_openai_export([make_openai_message(content_type=content_type, parts=parts)])
        f = write_export(data, tmp_path / "ct.json")

        conversations = list(OpenAIAdapter().stream_conversations(f))
        m = conversations[0].messages[0]
        assert m.metadata["content_type"] == content_type
        assert m.metadata["content_type_category"] == expected_category
        assert m.content == expected_content

    def test_media_category_image_asset_pointer(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="assistant", content_type="image_asset_pointer", parts=[])]
        )
        f = write_export(data, tmp_path / "media.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "media"
        assert m.content == ""

    def test_media_category_image(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="assistant", content_type="image", parts=[])]
        )
        f = write_export(data, tmp_path / "media2.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "media"
        assert m.content == ""

    def test_unknown_type_gets_unknown_category(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="assistant", content_type="brand_new_type", parts=["data"])]
        )
        f = write_export(data, tmp_path / "unknown.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type"] == "brand_new_type"
        assert m.metadata["content_type_category"] == "unknown"
        assert m.content == ""

    def test_placeholder_elimination(self, tmp_path: Path) -> None:
        """user_editable_context must NOT leak as '[user_editable_context]' in content."""
        data = make_openai_export(
            [
                make_openai_message(
                    role="system",
                    content_type="user_editable_context",
                    parts=["Custom instructions"],
                )
            ]
        )
        f = write_export(data, tmp_path / "placeholder.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert "[user_editable_context]" not in m.content
        assert m.content == ""

    def test_recipient_preserved(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="assistant",
                    content_type="code",
                    parts=["import os"],
                    recipient="python",
                )
            ]
        )
        f = write_export(data, tmp_path / "recipient.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["recipient"] == "python"

    def test_tool_authored_text_is_tool_io(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="tool", content_type="text", parts=["tool output"])]
        )
        f = write_export(data, tmp_path / "tool_text.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "tool_io"
        assert m.content == ""

    def test_tool_authored_multimodal_text_is_tool_io(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="tool",
                    content_type="multimodal_text",
                    parts=["<!DOCTYPE html><html>...50KB of HTML...</html>"],
                )
            ]
        )
        f = write_export(data, tmp_path / "tool_multimodal.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "tool_io"
        assert m.content == ""

    def test_tool_role_preserves_original_role(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="tool", content_type="text", parts=["result"])]
        )
        f = write_export(data, tmp_path / "tool_role.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["original_role"] == "tool"

    def test_non_tool_text_stays_conversational(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(role="assistant", content_type="text", parts=["Hello"])]
        )
        f = write_export(data, tmp_path / "assistant_text.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "conversational"
        assert m.content == "Hello"


# ============================================================================
# Test Multi-Part Text Joining (FR-005) — T008
# ============================================================================


class TestMultiPartTextJoining:
    """Multi-part text messages must join all string parts with newline."""

    def test_single_part_unchanged(self, tmp_path: Path) -> None:
        data = make_openai_export([make_openai_message(parts=["Single part message"])])
        f = write_export(data, tmp_path / "sp.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.content == "Single part message"

    def test_three_parts_joined_with_newline(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="assistant",
                    parts=["First part", "Second part", "Third part"],
                )
            ]
        )
        f = write_export(data, tmp_path / "mp.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.content == "First part\nSecond part\nThird part"

    def test_mixed_types_skip_non_strings(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [make_openai_message(parts=["Text before", {"non": "string"}, "Text after"])]
        )
        f = write_export(data, tmp_path / "mixed.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.content == "Text before\nText after"

    def test_empty_parts_gives_empty_content(self, tmp_path: Path) -> None:
        data = make_openai_export([make_openai_message(role="assistant", parts=[])])
        f = write_export(data, tmp_path / "empty.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.content == ""

    def test_multimodal_text_joins_with_newline(self, tmp_path: Path) -> None:
        """Multimodal text parts should also join with newline, not space."""
        data = make_openai_export(
            [
                make_openai_message(
                    content_type="multimodal_text",
                    parts=[
                        "First paragraph",
                        {
                            "content_type": "image_asset_pointer",
                            "asset_pointer": "sediment://file_abc",
                            "size_bytes": 100,
                            "width": 10,
                            "height": 10,
                        },
                        "Second paragraph",
                    ],
                )
            ]
        )
        f = write_export(data, tmp_path / "mmjoin.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.content == "First paragraph\nSecond paragraph"


# ============================================================================
# Test OpenAI Reasoning Metadata (FR-007) — T019
# ============================================================================


class TestOpenAIReasoningMetadata:
    """Verify thoughts/reasoning_recap produce metadata['thinking']."""

    def test_thoughts_produces_thinking_metadata(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="assistant",
                    content_type="thoughts",
                    parts=["Let me reason about this..."],
                )
            ]
        )
        f = write_export(data, tmp_path / "thoughts.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "reasoning"
        assert m.content == ""
        assert "thinking" in m.metadata
        assert m.metadata["thinking"]["content"] == "Let me reason about this..."

    def test_reasoning_recap_produces_thinking_metadata(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="assistant",
                    content_type="reasoning_recap",
                    parts=["To summarize my reasoning..."],
                )
            ]
        )
        f = write_export(data, tmp_path / "recap.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["content_type_category"] == "reasoning"
        assert m.content == ""
        assert m.metadata["thinking"]["content"] == "To summarize my reasoning..."

    def test_thinking_key_symmetric_with_claude(self, tmp_path: Path) -> None:
        """Both providers must use 'thinking' as the metadata key."""
        data = make_openai_export(
            [make_openai_message(role="assistant", content_type="thoughts", parts=["thinking..."])]
        )
        f = write_export(data, tmp_path / "sym.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert "thinking" in m.metadata


# ============================================================================
# Test Hidden Message Flag (FR-012) — T023
# ============================================================================


class TestOpenAIHiddenMessageFlag:
    """Verify is_visually_hidden metadata flag."""

    def test_hidden_message_gets_flag(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="system",
                    parts=["System context"],
                    metadata={"is_visually_hidden_from_conversation": True},
                )
            ]
        )
        f = write_export(data, tmp_path / "hidden.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert m.metadata["is_visually_hidden"] is True

    def test_non_hidden_message_no_flag(self, tmp_path: Path) -> None:
        data = make_openai_export([make_openai_message(metadata={})])
        f = write_export(data, tmp_path / "visible.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert "is_visually_hidden" not in m.metadata

    def test_hidden_flag_false_not_set(self, tmp_path: Path) -> None:
        data = make_openai_export(
            [
                make_openai_message(
                    role="system",
                    parts=["Visible system"],
                    metadata={"is_visually_hidden_from_conversation": False},
                )
            ]
        )
        f = write_export(data, tmp_path / "flag_false.json")
        m = next(iter(OpenAIAdapter().stream_conversations(f))).messages[0]
        assert "is_visually_hidden" not in m.metadata

    def test_hidden_message_still_in_output(self, tmp_path: Path) -> None:
        """Hidden messages must still appear — flag is additive only."""
        data = make_openai_export(
            [
                make_openai_message(
                    id="msg-001",
                    role="system",
                    parts=["Hidden"],
                    metadata={"is_visually_hidden_from_conversation": True},
                ),
                make_openai_message(
                    id="msg-002",
                    create_time=1700000002.0,
                    parts=["Visible"],
                ),
            ]
        )
        f = write_export(data, tmp_path / "both.json")
        messages = next(iter(OpenAIAdapter().stream_conversations(f))).messages
        assert len(messages) == 2
        ids = {m.id for m in messages}
        assert "msg-001" in ids
        assert "msg-002" in ids


# ============================================================================
# Test ImageRef Literal Expansion — T027
# ============================================================================


class TestImageRefLiteralExpansion:
    """ImageRef.content_type must accept both 'image_asset_pointer' and 'image'."""

    def test_image_asset_pointer_accepted(self) -> None:
        ref = ImageRef(asset_pointer="sediment://file_abc", content_type="image_asset_pointer")
        assert ref.content_type == "image_asset_pointer"

    def test_image_content_type_accepted(self) -> None:
        ref = ImageRef(asset_pointer="sediment://file_abc", content_type="image")
        assert ref.content_type == "image"


# ============================================================================
# Test DALL-E Metadata Preservation — T030
# ============================================================================


class TestDallEMetadataPreservation:
    """DALL-E metadata (gen_id, prompt, seed) must be preserved on ImageRef."""

    def test_dalle_metadata_on_image_ref(self) -> None:
        adapter = OpenAIAdapter()
        parts: list[object] = [
            {
                "content_type": "image_asset_pointer",
                "asset_pointer": "sediment://file_dalle",
                "size_bytes": 50000,
                "width": 512,
                "height": 512,
                "gen_id": "gen_abc123",
                "prompt": "a cat in space",
                "seed": 42,
            },
            "Here is your image",
        ]
        text, images = adapter._parse_multimodal_parts(parts)
        assert len(images) == 1
        assert images[0].metadata["gen_id"] == "gen_abc123"
        assert images[0].metadata["prompt"] == "a cat in space"
        assert images[0].metadata["seed"] == 42
