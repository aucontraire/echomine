"""Markdown exporter for AI conversation data.

This module provides the MarkdownExporter class for converting conversation
data from OpenAI exports into human-readable markdown format.

Constitution Compliance:
- Principle I: Library-first (importable, reusable class)
- Principle VI: Strict typing with mypy --strict compliance
- Principle V: YAGNI - Only implements markdown export, nothing more
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class MarkdownExporter:
    """Export OpenAI conversation data to markdown format.

    This class converts conversation exports into markdown files optimized
    for viewing in VS Code markdown preview with the following format:

    - Headers with emoji: ## 👤 User · [ISO timestamp]
    - Message content with proper markdown formatting
    - Horizontal rules (---) between messages
    - Image references: ![Image](file-id-sanitized.png)
    - NO blockquotes

    Example:
        ```python
        from echomine.export import MarkdownExporter
        from pathlib import Path

        exporter = MarkdownExporter()
        markdown = exporter.export_conversation(
            Path("conversations.json"),
            conversation_id="abc-123"
        )
        print(markdown)
        ```

    Design Notes:
        - Stateless: No instance variables (follows adapter pattern)
        - Pure functions: All methods are pure transformations
        - Minimal dependencies: Uses only standard library + echomine models
    """

    def export_conversation(
        self,
        export_file: Path,
        conversation_id: str,
    ) -> str:
        """Export a single conversation to markdown format.

        Args:
            export_file: Path to OpenAI export JSON file
            conversation_id: ID of conversation to export

        Returns:
            Markdown string formatted for VS Code preview

        Raises:
            FileNotFoundError: If export_file does not exist
            ValueError: If conversation_id not found in export
            json.JSONDecodeError: If export file is not valid JSON

        Example:
            ```python
            exporter = MarkdownExporter()
            md = exporter.export_conversation(
                Path("export.json"),
                "abc-123"
            )
            ```
        """
        # Load conversation data
        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)

        # Find the conversation
        conversation_data = self._find_conversation(data, conversation_id)
        if conversation_data is None:
            raise ValueError(f"Conversation {conversation_id} not found in {export_file}")

        # Extract messages from mapping structure
        messages = self._extract_messages(conversation_data)

        # Convert to markdown with conversation metadata
        return self._render_markdown(messages, conversation_data)

    def _find_conversation(self, data: Any, conversation_id: str) -> dict[str, Any] | None:
        """Find conversation by ID in OpenAI export data.

        Args:
            data: Parsed JSON data (list or single conversation)
            conversation_id: ID to search for

        Returns:
            Conversation dict if found, None otherwise
        """
        # Handle both list of conversations and single conversation
        conversations: list[Any] = data if isinstance(data, list) else [data]

        for conv in conversations:
            if not isinstance(conv, dict):
                continue
            if conv.get("id") == conversation_id or conv.get("conversation_id") == conversation_id:
                # Type narrowed to dict[str, Any] by isinstance check
                return dict(conv)

        return None

    def _extract_messages(self, conversation_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract messages from OpenAI conversation mapping structure.

        Args:
            conversation_data: OpenAI conversation object with mapping

        Returns:
            List of message dicts with id, role, timestamp, content, images
        """
        mapping = conversation_data.get("mapping", {})
        messages = []

        for node_id, node in mapping.items():
            msg_data = node.get("message")
            if msg_data is None:
                continue

            # Skip system messages and hidden messages
            author = msg_data.get("author", {})
            role = author.get("role")
            metadata = msg_data.get("metadata", {})

            if role == "system":
                continue
            if metadata.get("is_visually_hidden_from_conversation"):
                continue
            if role == "tool":
                continue

            # Extract content and images
            content, images = self._extract_content_and_images(msg_data)

            messages.append(
                {
                    "id": msg_data["id"],
                    "role": role,
                    "timestamp": msg_data.get("create_time"),
                    "content": content,
                    "images": images,
                }
            )

        # Sort by timestamp
        messages.sort(key=lambda m: m["timestamp"] if m["timestamp"] else 0)

        return messages

    def _extract_content_and_images(self, msg_data: dict[str, Any]) -> tuple[str, list[str]]:
        """Extract text content and image references from message.

        Args:
            msg_data: OpenAI message object

        Returns:
            Tuple of (text_content, list_of_image_asset_pointers)
        """
        content_data = msg_data.get("content", {})
        content_type = content_data.get("content_type")

        if content_type == "text":
            parts = content_data.get("parts", [])
            return " ".join(parts), []

        if content_type == "multimodal_text":
            parts = content_data.get("parts", [])
            text_parts = []
            images = []

            for part in parts:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    if part.get("content_type") == "image_asset_pointer":
                        asset_pointer = part.get("asset_pointer", "")
                        if asset_pointer.startswith("file-service://"):
                            # Convert to filename format
                            file_id = asset_pointer.replace("file-service://", "")
                            images.append(f"{file_id}-sanitized.png")

            return " ".join(text_parts), images

        if content_type == "code":
            return content_data.get("text", ""), []

        # Unknown content type - return empty
        return "", []

    def _render_markdown(
        self,
        messages: list[dict[str, Any]],
        conversation_data: dict[str, Any],
    ) -> str:
        """Render messages as markdown string with conversation metadata header.

        Args:
            messages: List of message dicts
            conversation_data: Conversation metadata from OpenAI export

        Returns:
            Formatted markdown string with metadata header followed by messages
        """
        lines = []

        # Render conversation metadata header (FR-014)
        metadata_header = self._render_metadata_header(conversation_data, len(messages))
        lines.append(metadata_header)
        lines.append("")

        for i, msg in enumerate(messages):
            # Render header with emoji and timestamp
            role = msg["role"]
            emoji = "👤" if role == "user" else "🤖"
            role_name = "User" if role == "user" else "Assistant"
            timestamp = self._format_timestamp(msg["timestamp"])

            lines.append(f"## {emoji} {role_name} · {timestamp}")
            lines.append("")

            # Render images before content
            for image in msg["images"]:
                lines.append(f"![Image]({image})")
                lines.append("")

            # Render content
            lines.append(msg["content"].strip())

            # Add separator between messages (but not after last)
            if i < len(messages) - 1:
                lines.append("")
                lines.append("---")
                lines.append("")

        # Add trailing newline for POSIX text file compliance
        return "\n".join(lines) + "\n"

    def _render_metadata_header(
        self,
        conversation_data: dict[str, Any],
        message_count: int,
    ) -> str:
        """Render conversation metadata as markdown header.

        Includes title, created date, updated date (if present), and message count
        per FR-014 requirements.

        Args:
            conversation_data: OpenAI conversation object with metadata
            message_count: Number of messages in conversation

        Returns:
            Formatted metadata header string with title and metadata fields
        """
        lines = []

        # Title as H1 heading
        title = conversation_data.get("title", "Untitled Conversation")
        lines.append(f"# {title}")
        lines.append("")

        # Created timestamp
        create_time = conversation_data.get("create_time")
        created_str = self._format_timestamp(create_time)
        lines.append(f"Created: {created_str}")

        # Updated timestamp (optional - only if present and not null)
        update_time = conversation_data.get("update_time")
        if update_time is not None:
            updated_str = self._format_timestamp(update_time)
            lines.append(f"Updated: {updated_str}")

        # Message count (singular vs plural)
        message_str = "message" if message_count == 1 else "messages"
        lines.append(f"Messages: {message_count} {message_str}")

        # Separator line before messages
        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _format_timestamp(self, timestamp: float | None) -> str:
        """Format Unix timestamp to ISO 8601 format in UTC.

        Args:
            timestamp: Unix timestamp (seconds since epoch)

        Returns:
            ISO 8601 formatted string in UTC (YYYY-MM-DDTHH:MM:SS+00:00)
        """
        if timestamp is None:
            return "N/A"

        dt = datetime.fromtimestamp(timestamp, tz=UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
