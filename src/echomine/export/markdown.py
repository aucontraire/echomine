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
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from echomine.models.conversation import Conversation


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

    def export_conversation_from_model(
        self,
        conversation: Conversation,
        *,
        include_metadata: bool = True,
        include_message_ids: bool = True,
    ) -> str:
        """Export a Conversation model to markdown format (multi-provider support).

        This method works with any provider (OpenAI, Claude, etc.) by accepting
        a Conversation object directly instead of parsing provider-specific JSON.

        Args:
            conversation: Conversation model to export
            include_metadata: Include YAML frontmatter (default: True) (FR-030, FR-035)
            include_message_ids: Include message IDs in headers (default: True) (FR-035)

        Returns:
            Markdown string formatted for VS Code preview

        Example:
            ```python
            from echomine.cli.provider import get_adapter
            from echomine.export import MarkdownExporter

            # Get conversation using appropriate adapter
            adapter = get_adapter(None, Path("export.json"))
            conversation = adapter.get_conversation_by_id(Path("export.json"), "abc-123")

            # Export to markdown
            exporter = MarkdownExporter()
            md = exporter.export_conversation_from_model(conversation)
            print(md)
            ```

        Multi-Provider Support:
            - Works with OpenAI, Claude, and future providers
            - Uses normalized Conversation model (provider-agnostic)
            - Constitution Principle VII: Multi-provider adapter pattern
        """
        lines = []

        # Render YAML frontmatter if enabled (FR-030, FR-031)
        if include_metadata:
            lines.append("---")
            lines.append(f"id: {conversation.id}")
            lines.append(f"title: {conversation.title}")
            lines.append(f"created_at: {conversation.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')}")
            if conversation.updated_at:
                lines.append(
                    f"updated_at: {conversation.updated_at.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                )
            lines.append(f"message_count: {conversation.message_count}")
            export_date = datetime.now(UTC)
            lines.append(f"export_date: {export_date.strftime('%Y-%m-%dT%H:%M:%SZ')}")
            lines.append("exported_by: echomine")
            lines.append("---")
            lines.append("")

        # Always render title heading
        lines.append(f"# {conversation.title}")
        lines.append("")

        # Render inline metadata fields only when frontmatter disabled (backward compatibility)
        if not include_metadata:
            lines.append(f"Created: {conversation.created_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')}")
            if conversation.updated_at:
                lines.append(
                    f"Updated: {conversation.updated_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')}"
                )
            message_str = "message" if conversation.message_count == 1 else "messages"
            lines.append(f"Messages: {conversation.message_count} {message_str}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Render messages
        for i, message in enumerate(conversation.messages):
            # Render header with optional message ID and timestamp
            role_name = "User" if message.role == "user" else "Assistant"
            timestamp = message.timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00")

            # Build header with optional message ID (FR-032)
            if include_message_ids:
                lines.append(f"## {role_name} (`{message.id}`) - {timestamp}")
            else:
                # Backward compatibility: keep emojis when IDs disabled
                emoji = "👤" if message.role == "user" else "🤖"
                lines.append(f"## {emoji} {role_name} · {timestamp}")

            lines.append("")

            # Render content, stripping trailing whitespace from each line
            content_lines = message.content.strip().split("\n")
            content = "\n".join(line.rstrip() for line in content_lines)
            lines.append(content)

            # Add separator between messages (but not after last)
            if i < len(conversation.messages) - 1:
                lines.append("")
                lines.append("---")
                lines.append("")

        # Add trailing newline for POSIX text file compliance
        return "\n".join(lines) + "\n"

    def export_conversation(
        self,
        export_file: Path,
        conversation_id: str,
        *,
        include_metadata: bool = True,
        include_message_ids: bool = True,
    ) -> str:
        """Export a single conversation to markdown format (OpenAI format only).

        DEPRECATED: This method only supports OpenAI format. For multi-provider
        support, use export_conversation_from_model() instead.

        Args:
            export_file: Path to OpenAI export JSON file
            conversation_id: ID of conversation to export
            include_metadata: Include YAML frontmatter (default: True) (FR-030, FR-035)
            include_message_ids: Include message IDs in headers (default: True) (FR-035)

        Returns:
            Markdown string formatted for VS Code preview

        Raises:
            FileNotFoundError: If export_file does not exist
            ValueError: If conversation_id not found in export
            json.JSONDecodeError: If export file is not valid JSON

        Example:
            ```python
            exporter = MarkdownExporter()

            # With metadata and IDs (default)
            md = exporter.export_conversation(Path("export.json"), "abc-123")

            # Without metadata
            md = exporter.export_conversation(
                Path("export.json"),
                "abc-123",
                include_metadata=False
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
        return self._render_markdown(
            messages,
            conversation_data,
            include_metadata=include_metadata,
            include_message_ids=include_message_ids,
        )

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

            # Get message ID from source, or None if missing (will be generated later)
            message_id = msg_data.get("id")

            messages.append(
                {
                    "id": message_id,
                    "role": role,
                    "timestamp": msg_data.get("create_time"),
                    "content": content,
                    "images": images,
                }
            )

        # Sort by timestamp
        messages.sort(key=lambda m: m["timestamp"] if m["timestamp"] else 0)

        # Generate deterministic IDs for messages without source IDs (FR-032a, FR-032b)
        conversation_id = conversation_data.get("id", "unknown")
        for i, msg in enumerate(messages, start=1):
            if msg["id"] is None:
                # Format: msg-{conversation_id}-{zero_padded_index}
                msg["id"] = f"msg-{conversation_id}-{i:03d}"

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
        *,
        include_metadata: bool = True,
        include_message_ids: bool = True,
    ) -> str:
        """Render messages as markdown string with optional YAML frontmatter.

        Args:
            messages: List of message dicts
            conversation_data: Conversation metadata from OpenAI export
            include_metadata: Include YAML frontmatter (FR-030)
            include_message_ids: Include message IDs in headers (FR-032)

        Returns:
            Formatted markdown string with optional frontmatter and messages
        """
        lines = []

        # Render YAML frontmatter if enabled (FR-030, FR-031)
        if include_metadata:
            frontmatter = self._render_yaml_frontmatter(conversation_data, len(messages))
            lines.append(frontmatter)
            lines.append("")

        # Always render title heading
        title = conversation_data.get("title", "Untitled Conversation")
        lines.append(f"# {title}")
        lines.append("")

        # Render inline metadata fields only when frontmatter disabled (backward compatibility)
        if not include_metadata:
            # Add Created/Updated/Messages fields after title
            create_time = conversation_data.get("create_time")
            created_str = self._format_timestamp(create_time)
            lines.append(f"Created: {created_str}")

            update_time = conversation_data.get("update_time")
            if update_time is not None:
                updated_str = self._format_timestamp(update_time)
                lines.append(f"Updated: {updated_str}")

            message_str = "message" if len(messages) == 1 else "messages"
            lines.append(f"Messages: {len(messages)} {message_str}")
            lines.append("")
            lines.append("---")
            lines.append("")

        for i, msg in enumerate(messages):
            # Render header with optional message ID and timestamp
            role = msg["role"]
            role_name = "User" if role == "user" else "Assistant"
            timestamp = self._format_timestamp(msg["timestamp"])

            # Build header with optional message ID (FR-032)
            # New format (no emojis): ## User (`msg-id`) - timestamp
            if include_message_ids:
                message_id = msg["id"]
                lines.append(f"## {role_name} (`{message_id}`) - {timestamp}")
            else:
                # Backward compatibility: keep emojis when IDs disabled
                emoji = "👤" if role == "user" else "🤖"
                lines.append(f"## {emoji} {role_name} · {timestamp}")

            lines.append("")

            # Render images before content
            for image in msg["images"]:
                lines.append(f"![Image]({image})")
                lines.append("")

            # Render content, stripping trailing whitespace from each line
            content_lines = msg["content"].strip().split("\n")
            content = "\n".join(line.rstrip() for line in content_lines)
            lines.append(content)

            # Add separator between messages (but not after last)
            if i < len(messages) - 1:
                lines.append("")
                lines.append("---")
                lines.append("")

        # Add trailing newline for POSIX text file compliance
        return "\n".join(lines) + "\n"

    def _render_yaml_frontmatter(
        self,
        conversation_data: dict[str, Any],
        message_count: int,
    ) -> str:
        """Render YAML frontmatter for Jekyll/Hugo compatibility.

        Generates YAML frontmatter with conversation metadata per FR-031.

        Args:
            conversation_data: OpenAI conversation object with metadata
            message_count: Number of messages in conversation

        Returns:
            YAML frontmatter block enclosed in --- delimiters

        Format (FR-031):
            ---
            id: conversation-id
            title: Conversation Title
            created_at: 2024-01-15T10:30:00Z
            updated_at: 2024-01-15T14:30:00Z
            message_count: 42
            export_date: 2025-12-05T15:30:00Z
            exported_by: echomine
            ---
        """
        lines = []

        # Opening delimiter
        lines.append("---")

        # id field (FR-031)
        conv_id = conversation_data.get("id", "unknown")
        lines.append(f"id: {conv_id}")

        # title field (FR-031)
        title = conversation_data.get("title", "Untitled Conversation")
        lines.append(f"title: {title}")

        # created_at field (FR-031, FR-031b)
        create_time = conversation_data.get("create_time")
        created_str = self._format_timestamp_iso8601_z(create_time)
        lines.append(f"created_at: {created_str}")

        # updated_at field (FR-031, FR-031b)
        # Can be None if conversation never updated
        update_time = conversation_data.get("update_time")
        if update_time is not None:
            updated_str = self._format_timestamp_iso8601_z(update_time)
            lines.append(f"updated_at: {updated_str}")
        else:
            # Omit field if never updated (cleaner than "updated_at: null")
            pass

        # message_count field (FR-031)
        lines.append(f"message_count: {message_count}")

        # export_date field (FR-031, FR-031b) - current time
        export_date = datetime.now(UTC)
        export_date_str = export_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        lines.append(f"export_date: {export_date_str}")

        # exported_by field (FR-031)
        lines.append("exported_by: echomine")

        # Closing delimiter
        lines.append("---")

        return "\n".join(lines)

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

    def _format_timestamp_iso8601_z(self, timestamp: float | None) -> str:
        """Format Unix timestamp to ISO 8601 format with Z suffix.

        This format is required for YAML frontmatter per FR-031b.

        Args:
            timestamp: Unix timestamp (seconds since epoch)

        Returns:
            ISO 8601 formatted string with Z suffix (YYYY-MM-DDTHH:MM:SSZ)

        Example:
            >>> exporter._format_timestamp_iso8601_z(1705320600.0)
            '2024-01-15T10:30:00Z'
        """
        if timestamp is None:
            return "N/A"

        dt = datetime.fromtimestamp(timestamp, tz=UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
