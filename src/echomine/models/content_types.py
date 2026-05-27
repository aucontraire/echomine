"""Provider-agnostic content type classification for conversation messages."""

from __future__ import annotations

from typing import Literal


ContentTypeCategory = Literal[
    "conversational",
    "reasoning",
    "tool_io",
    "system",
    "media",
    "attachment",
    "unknown",
]

OPENAI_CATEGORY_MAP: dict[str, ContentTypeCategory] = {
    "text": "conversational",
    "multimodal_text": "conversational",
    "thoughts": "reasoning",
    "reasoning_recap": "reasoning",
    "code": "tool_io",
    "execution_output": "tool_io",
    "tether_quote": "tool_io",
    "tether_browsing_display": "tool_io",
    "user_editable_context": "system",
    "app_pairing_content": "system",
    "system_error": "system",
    "image_asset_pointer": "media",
    "image": "media",
}

CLAUDE_CATEGORY_MAP: dict[str, ContentTypeCategory] = {
    "text": "conversational",
    "voice_note": "conversational",
    "thinking": "reasoning",
    "tool_use": "tool_io",
    "tool_result": "tool_io",
    "token_budget": "system",
}

_PROVIDER_MAPS: dict[str, dict[str, ContentTypeCategory]] = {
    "openai": OPENAI_CATEGORY_MAP,
    "claude": CLAUDE_CATEGORY_MAP,
}


def classify_content_type(raw_type: str, provider: str) -> ContentTypeCategory:
    """Classify a raw content type string into a standardized category.

    Args:
        raw_type: Provider-specific content type (e.g., "text", "thinking")
        provider: Provider name ("openai" or "claude")

    Returns:
        Standardized category from the pinned vocabulary, or "unknown"
    """
    provider_map = _PROVIDER_MAPS.get(provider)
    if provider_map is None:
        return "unknown"
    return provider_map.get(raw_type, "unknown")
