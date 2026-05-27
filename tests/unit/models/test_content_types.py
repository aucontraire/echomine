"""Unit tests for ContentTypeCategory mappings and classify_content_type helper.

Tests every raw provider content type maps to the expected category,
unknown types fall back to 'unknown', and classify_content_type dispatches correctly.

Constitution Compliance:
    - Principle III: TDD (RED phase — these tests MUST fail before implementation)
    - Principle VI: Strict typing
"""

from __future__ import annotations

import pytest

from echomine.models.content_types import (
    CLAUDE_CATEGORY_MAP,
    OPENAI_CATEGORY_MAP,
    ContentTypeCategory,
    classify_content_type,
)


class TestOpenAICategoryMap:
    """Verify every OpenAI raw content type maps to the correct category."""

    @pytest.mark.parametrize(
        ("raw_type", "expected_category"),
        [
            ("text", "conversational"),
            ("multimodal_text", "conversational"),
            ("thoughts", "reasoning"),
            ("reasoning_recap", "reasoning"),
            ("code", "tool_io"),
            ("execution_output", "tool_io"),
            ("tether_quote", "tool_io"),
            ("tether_browsing_display", "tool_io"),
            ("user_editable_context", "system"),
            ("app_pairing_content", "system"),
            ("system_error", "system"),
            ("image_asset_pointer", "media"),
            ("image", "media"),
        ],
    )
    def test_known_types(self, raw_type: str, expected_category: ContentTypeCategory) -> None:
        assert OPENAI_CATEGORY_MAP[raw_type] == expected_category

    def test_map_has_exactly_13_entries(self) -> None:
        assert len(OPENAI_CATEGORY_MAP) == 13

    def test_unknown_type_not_in_map(self) -> None:
        assert "some_future_type" not in OPENAI_CATEGORY_MAP


class TestClaudeCategoryMap:
    """Verify every Claude block type maps to the correct category."""

    @pytest.mark.parametrize(
        ("block_type", "expected_category"),
        [
            ("text", "conversational"),
            ("voice_note", "conversational"),
            ("thinking", "reasoning"),
            ("tool_use", "tool_io"),
            ("tool_result", "tool_io"),
            ("token_budget", "system"),
        ],
    )
    def test_known_types(self, block_type: str, expected_category: ContentTypeCategory) -> None:
        assert CLAUDE_CATEGORY_MAP[block_type] == expected_category

    def test_map_has_exactly_6_entries(self) -> None:
        assert len(CLAUDE_CATEGORY_MAP) == 6

    def test_unknown_type_not_in_map(self) -> None:
        assert "some_future_block" not in CLAUDE_CATEGORY_MAP


class TestClassifyContentType:
    """Verify classify_content_type dispatches correctly by provider."""

    def test_openai_known_type(self) -> None:
        assert classify_content_type("text", "openai") == "conversational"

    def test_openai_unknown_type_returns_unknown(self) -> None:
        assert classify_content_type("brand_new_type", "openai") == "unknown"

    def test_claude_known_type(self) -> None:
        assert classify_content_type("thinking", "claude") == "reasoning"

    def test_claude_unknown_type_returns_unknown(self) -> None:
        assert classify_content_type("brand_new_block", "claude") == "unknown"

    def test_unknown_provider_returns_unknown(self) -> None:
        assert classify_content_type("text", "gemini") == "unknown"

    def test_return_type_is_valid_category(self) -> None:
        result = classify_content_type("text", "openai")
        valid: set[ContentTypeCategory] = {
            "conversational",
            "reasoning",
            "tool_io",
            "system",
            "media",
            "attachment",
            "unknown",
        }
        assert result in valid
