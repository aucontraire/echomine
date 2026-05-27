"""Shared test data factories for OpenAI and Claude export structures.

Eliminates the 30-50 line JSON boilerplate that every adapter test
repeats for conversation/message construction.
"""

from __future__ import annotations

import json
from pathlib import Path


# ── OpenAI ─────────────────────────────────────────────────────────────


def make_openai_message(
    *,
    id: str = "msg-001",
    role: str = "user",
    content_type: str = "text",
    parts: list[object] | None = None,
    create_time: float = 1700000001.0,
    **extra: object,
) -> dict[str, object]:
    """Build a minimal OpenAI message dict.

    Extra kwargs become top-level message keys (e.g. metadata, recipient).
    Pass ``content=`` to override the auto-generated content dict entirely.
    """
    msg: dict[str, object] = {
        "id": id,
        "author": {"role": role},
        "create_time": create_time,
        "content": {
            "content_type": content_type,
            "parts": parts if parts is not None else ["Hello"],
        },
    }
    msg.update(extra)
    return msg


def make_openai_conversation(
    messages: list[dict[str, object]],
    *,
    conv_id: str = "conv-001",
    title: str = "Test Conversation",
    create_time: float = 1700000000.0,
    update_time: float = 1700001000.0,
) -> dict[str, object]:
    """Build a single OpenAI conversation dict with auto-linked mapping nodes."""
    mapping: dict[str, object] = {}
    prev_id: str | None = None
    for msg in messages:
        node_id = f"node-{msg['id']}"
        mapping[node_id] = {
            "id": node_id,
            "parent": f"node-{prev_id}" if prev_id else None,
            "message": msg,
        }
        prev_id = str(msg["id"])
    return {
        "id": conv_id,
        "title": title,
        "create_time": create_time,
        "update_time": update_time,
        "mapping": mapping,
    }


def make_openai_export(
    messages: list[dict[str, object]],
    *,
    conv_id: str = "conv-test",
    title: str = "Test",
    create_time: float = 1700000000.0,
    update_time: float = 1700001000.0,
) -> list[dict[str, object]]:
    """Build a single-conversation OpenAI export from a list of message dicts."""
    return [
        make_openai_conversation(
            messages,
            conv_id=conv_id,
            title=title,
            create_time=create_time,
            update_time=update_time,
        )
    ]


# ── Claude ─────────────────────────────────────────────────────────────


def make_claude_message(
    *,
    uuid: str = "msg-001",
    sender: str = "human",
    text: str = "",
    content: list[dict[str, object]] | None = None,
    created_at: str = "2025-10-01T18:00:01Z",
    **extra: object,
) -> dict[str, object]:
    """Build a minimal Claude message dict.

    Extra kwargs become top-level message keys (e.g. attachments, files).
    """
    msg: dict[str, object] = {
        "uuid": uuid,
        "text": text,
        "sender": sender,
        "created_at": created_at,
    }
    if content is not None:
        msg["content"] = content
    msg.update(extra)
    return msg


def make_claude_export(
    messages: list[dict[str, object]],
    *,
    conv_id: str = "conv-test",
    title: str = "Test",
    created_at: str = "2025-10-01T18:00:00Z",
    updated_at: str = "2025-10-01T18:01:00Z",
) -> list[dict[str, object]]:
    """Build a single-conversation Claude export from a list of message dicts."""
    return [
        {
            "uuid": conv_id,
            "name": title,
            "created_at": created_at,
            "updated_at": updated_at,
            "chat_messages": messages,
        }
    ]


# ── File helpers ───────────────────────────────────────────────────────


def write_export(data: list[dict[str, object]], path: Path) -> Path:
    """Write export data as JSON and return the path."""
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
