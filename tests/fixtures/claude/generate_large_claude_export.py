#!/usr/bin/env python3
"""Generate large Claude export fixture for performance testing.

Usage:
    python generate_large_export.py --conversations 1000 --output large_export.json
"""

import argparse
import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


SAMPLE_TEXTS = [
    "Can you help me with this Python code?",
    "How do I implement a binary search algorithm?",
    "What are the best practices for async programming?",
    "Can you explain how generators work in Python?",
    "I need help debugging this function.",
]

SAMPLE_RESPONSES = [
    "Sure, I'd be happy to help! Let me explain...",
    "Here's how you can implement that...",
    "The key concept here is...",
    "There are several approaches to this problem...",
    "Let me walk you through the solution...",
]


def generate_message(index: int, sender: str, base_time: datetime) -> dict[str, Any]:
    """Generate a single message."""
    text = random.choice(SAMPLE_TEXTS if sender == "human" else SAMPLE_RESPONSES)
    msg_time = base_time + timedelta(minutes=index)

    return {
        "uuid": str(uuid.uuid4()),
        "text": text,
        "content": [{"type": "text", "text": text}],
        "sender": sender,
        "created_at": msg_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "updated_at": msg_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "attachments": [],
        "files": [],
    }


def generate_conversation(index: int, base_time: datetime, num_messages: int = 4) -> dict[str, Any]:
    """Generate a single conversation with messages."""
    conv_time = base_time - timedelta(days=index)
    messages = []

    for i in range(num_messages):
        sender = "human" if i % 2 == 0 else "assistant"
        messages.append(generate_message(i, sender, conv_time))

    return {
        "uuid": str(uuid.uuid4()),
        "name": f"Conversation {index + 1} - Technical Discussion",
        "summary": f"Technical discussion #{index + 1}",
        "created_at": conv_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "updated_at": (conv_time + timedelta(minutes=num_messages)).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        "account": {"uuid": str(uuid.uuid4())},
        "chat_messages": messages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate large Claude export for testing")
    parser.add_argument("--conversations", type=int, default=1000, help="Number of conversations")
    parser.add_argument(
        "--messages-per-conv", type=int, default=4, help="Messages per conversation"
    )
    parser.add_argument("--output", type=str, default="large_export.json", help="Output file path")
    args = parser.parse_args()

    print(f"Generating {args.conversations} conversations...")

    base_time = datetime.now(UTC)
    conversations = [
        generate_conversation(i, base_time, args.messages_per_conv)
        for i in range(args.conversations)
    ]

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2)

    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    print(f"Generated {output_path} ({file_size:.2f} MB)")
    print(f"  Conversations: {len(conversations)}")
    print(f"  Messages per conversation: {args.messages_per_conv}")
    print(f"  Total messages: {len(conversations) * args.messages_per_conv}")


if __name__ == "__main__":
    main()
