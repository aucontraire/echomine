"""Cross-provider content fidelity integration tests.

Verifies symmetric content_type_category values across OpenAI and Claude
adapters for semantically equivalent messages.
"""

from __future__ import annotations

from pathlib import Path

from echomine.adapters import OpenAIAdapter
from echomine.adapters.claude import ClaudeAdapter
from tests.factories import (
    make_claude_export,
    make_claude_message,
    make_openai_export,
    make_openai_message,
    write_export,
)


class TestCrossProviderContentFidelity:
    """Both adapters must produce symmetric content_type_category values."""

    def test_conversational_symmetric(self, tmp_path: Path) -> None:
        openai_data = make_openai_export([make_openai_message(id="m1")])
        claude_data = make_claude_export(
            [make_claude_message(uuid="m1", content=[{"type": "text", "text": "Hello"}])]
        )

        of = write_export(openai_data, tmp_path / "openai.json")
        cf = write_export(claude_data, tmp_path / "claude.json")

        om = next(iter(OpenAIAdapter().stream_conversations(of))).messages[0]
        cm = next(iter(ClaudeAdapter().stream_conversations(cf))).messages[0]

        assert om.metadata["content_type_category"] == "conversational"
        assert cm.metadata["content_type_category"] == "conversational"
        assert om.metadata["content_type_category"] == cm.metadata["content_type_category"]

    def test_every_message_has_content_type_fields(self, tmp_path: Path) -> None:
        openai_data = make_openai_export(
            [
                make_openai_message(id="m1"),
                make_openai_message(
                    id="m2",
                    role="assistant",
                    content_type="code",
                    parts=["x=1"],
                    create_time=1700000002.0,
                ),
            ]
        )
        claude_data = make_claude_export(
            [
                make_claude_message(uuid="m1", content=[{"type": "text", "text": "Hello"}]),
                make_claude_message(
                    uuid="m2",
                    sender="assistant",
                    created_at="2025-10-01T18:00:02Z",
                    content=[{"type": "tool_use", "id": "t1", "name": "calc", "input": {}}],
                ),
            ]
        )

        of = write_export(openai_data, tmp_path / "openai.json")
        cf = write_export(claude_data, tmp_path / "claude.json")

        VALID_CATEGORIES = {
            "conversational",
            "reasoning",
            "tool_io",
            "system",
            "media",
            "attachment",
            "unknown",
        }

        for msg in next(iter(OpenAIAdapter().stream_conversations(of))).messages:
            assert "content_type" in msg.metadata
            assert "content_type_category" in msg.metadata
            assert msg.metadata["content_type_category"] in VALID_CATEGORIES

        for msg in next(iter(ClaudeAdapter().stream_conversations(cf))).messages:
            assert "content_type" in msg.metadata
            assert "content_type_category" in msg.metadata
            assert msg.metadata["content_type_category"] in VALID_CATEGORIES
