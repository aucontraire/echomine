"""Contract tests for ContentTypeCategory vocabulary.

Validates the pinned 7-value vocabulary, ensures all provider mappings are
complete with no overlap, and verifies the contract guarantees from
specs/005-content-fidelity/contracts/content_contract.md.

Constitution Compliance:
    - Principle III: TDD (RED phase — these tests MUST fail before implementation)
    - Principle VI: Strict typing
"""

from __future__ import annotations

from typing import ClassVar, get_args

from echomine.models.content_types import (
    CLAUDE_CATEGORY_MAP,
    OPENAI_CATEGORY_MAP,
    ContentTypeCategory,
    classify_content_type,
)


class TestVocabularyContract:
    """The pinned vocabulary MUST have exactly 7 values."""

    EXPECTED_CATEGORIES: ClassVar[set[str]] = {
        "conversational",
        "reasoning",
        "tool_io",
        "system",
        "media",
        "attachment",
        "unknown",
    }

    def test_literal_has_exactly_7_values(self) -> None:
        values = set(get_args(ContentTypeCategory))
        assert values == self.EXPECTED_CATEGORIES

    def test_every_map_value_is_valid_category(self) -> None:
        valid = self.EXPECTED_CATEGORIES
        for raw_type, category in OPENAI_CATEGORY_MAP.items():
            assert category in valid, f"OpenAI '{raw_type}' maps to invalid '{category}'"
        for block_type, category in CLAUDE_CATEGORY_MAP.items():
            assert category in valid, f"Claude '{block_type}' maps to invalid '{category}'"


class TestProviderMappingCompleteness:
    """All documented provider types must have mappings."""

    OPENAI_DOCUMENTED_TYPES: ClassVar[set[str]] = {
        "text",
        "multimodal_text",
        "thoughts",
        "reasoning_recap",
        "code",
        "execution_output",
        "tether_quote",
        "tether_browsing_display",
        "user_editable_context",
        "app_pairing_content",
        "system_error",
        "image_asset_pointer",
        "image",
    }

    CLAUDE_DOCUMENTED_TYPES: ClassVar[set[str]] = {
        "text",
        "voice_note",
        "thinking",
        "tool_use",
        "tool_result",
        "token_budget",
    }

    def test_openai_map_covers_all_documented_types(self) -> None:
        assert set(OPENAI_CATEGORY_MAP.keys()) == self.OPENAI_DOCUMENTED_TYPES

    def test_claude_map_covers_all_documented_types(self) -> None:
        assert set(CLAUDE_CATEGORY_MAP.keys()) == self.CLAUDE_DOCUMENTED_TYPES


class TestUnknownFallback:
    """Unmapped types MUST return 'unknown', never raise."""

    def test_openai_unmapped_returns_unknown(self) -> None:
        assert classify_content_type("nonexistent_openai_type", "openai") == "unknown"

    def test_claude_unmapped_returns_unknown(self) -> None:
        assert classify_content_type("nonexistent_claude_block", "claude") == "unknown"

    def test_unknown_provider_returns_unknown(self) -> None:
        assert classify_content_type("text", "unknown_provider") == "unknown"
