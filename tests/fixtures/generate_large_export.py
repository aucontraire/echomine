"""Generate large OpenAI export fixture for performance testing.

This script generates a synthetic OpenAI export file with configurable number
of conversations and messages. Used for benchmarking streaming performance,
memory efficiency, and search operations.

Requirements:
    - CHK026: Performance test baseline (10K conversations, 50K messages)
    - FR-444: List must complete in <5s for 10K conversations
    - FR-003: Memory usage must remain constant regardless of file size

Usage:
    ```bash
    # Generate 10K conversations (performance baseline)
    python generate_large_export.py --conversations 10000 --messages-per-conversation 5

    # Generate 1GB+ file (stress test)
    python generate_large_export.py --conversations 50000 --messages-per-conversation 10
    ```
"""

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any


def generate_conversation(
    conversation_index: int,
    messages_per_conversation: int,
) -> dict[str, Any]:
    """Generate a single conversation with messages.

    Args:
        conversation_index: Sequential conversation number
        messages_per_conversation: Number of messages in conversation

    Returns:
        OpenAI conversation dict with mapping structure
    """
    conv_id = f"conv-{conversation_index:06d}"
    base_timestamp = 1700000000.0 + (conversation_index * 1000)

    # Generate message mapping
    mapping: dict[str, Any] = {}
    for msg_index in range(messages_per_conversation):
        msg_id = f"msg-{conversation_index:06d}-{msg_index:02d}"
        parent_id = f"msg-{conversation_index:06d}-{msg_index - 1:02d}" if msg_index > 0 else None
        children_ids = (
            [f"msg-{conversation_index:06d}-{msg_index + 1:02d}"]
            if msg_index < messages_per_conversation - 1
            else []
        )

        role = "user" if msg_index % 2 == 0 else "assistant"
        content = (
            f"User message {msg_index} in conversation {conversation_index}"
            if role == "user"
            else f"Assistant response {msg_index} in conversation {conversation_index}"
        )

        mapping[msg_id] = {
            "id": msg_id,
            "message": {
                "id": msg_id,
                "author": {"role": role},
                "content": {"content_type": "text", "parts": [content]},
                "create_time": base_timestamp + (msg_index * 10),
                "update_time": None,
                "metadata": {},
            },
            "parent": parent_id,
            "children": children_ids,
        }

    # Conversation structure
    return {
        "id": conv_id,
        "title": f"Test Conversation {conversation_index}",
        "create_time": base_timestamp,
        "update_time": base_timestamp + ((messages_per_conversation - 1) * 10),
        "mapping": mapping,
        "moderation_results": [],
        "current_node": f"msg-{conversation_index:06d}-{messages_per_conversation - 1:02d}",
    }


def generate_export(
    num_conversations: int,
    messages_per_conversation: int,
    output_path: Path,
) -> None:
    """Generate large export file.

    Args:
        num_conversations: Number of conversations to generate
        messages_per_conversation: Messages per conversation
        output_path: Output file path

    Example:
        ```python
        generate_export(
            num_conversations=10000,
            messages_per_conversation=5,
            output_path=Path("large_export.json")
        )
        ```
    """
    conversations = []
    for i in range(num_conversations):
        conversation = generate_conversation(i, messages_per_conversation)
        conversations.append(conversation)

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1:,} conversations...")

    # Write to file
    print(f"Writing to {output_path}...")
    with output_path.open("w") as f:
        json.dump(conversations, f, indent=None)  # No indentation for smaller file

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✓ Generated {num_conversations:,} conversations")
    print(f"✓ Total messages: {num_conversations * messages_per_conversation:,}")
    print(f"✓ File size: {file_size_mb:.2f} MB")


def main() -> None:
    """Command-line entry point."""
    parser = ArgumentParser(
        description="Generate large OpenAI export fixture for performance testing"
    )
    parser.add_argument(
        "--conversations",
        type=int,
        default=10000,
        help="Number of conversations to generate (default: 10000)",
    )
    parser.add_argument(
        "--messages-per-conversation",
        type=int,
        default=5,
        help="Messages per conversation (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/fixtures/large_export.json"),
        help="Output file path (default: tests/fixtures/large_export.json)",
    )

    args = parser.parse_args()

    generate_export(
        num_conversations=args.conversations,
        messages_per_conversation=args.messages_per_conversation,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
