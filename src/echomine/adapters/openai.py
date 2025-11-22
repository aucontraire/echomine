"""OpenAI conversation export adapter with ijson streaming parser.

This module provides the OpenAIAdapter class for streaming conversations from
OpenAI ChatGPT export files with O(1) memory complexity using ijson.

Memory Characteristics:
    - O(1) memory consumption for export file size (streaming parser)
    - O(N) memory per conversation (where N = message count in single conversation)
    - Parser buffer: ~50MB max (ijson state + current conversation)
    - No unbounded data structures - yields conversations immediately

Constitution Compliance:
    - Principle VIII: Memory-efficient streaming (FR-003, SC-001)
    - Principle VI: Type safety with mypy --strict
    - Principle IV: Observability (error context, structured logging)
    - FR-122: ijson>=3.2.0 for streaming JSON parsing
    - FR-281-285: Graceful degradation for malformed entries

OpenAI Export Schema:
    Root: JSON array of conversation objects
    Each conversation:
        - id: string (unique identifier)
        - title: string (conversation title)
        - create_time: float (Unix timestamp)
        - update_time: float (Unix timestamp)
        - mapping: dict[str, NodeObject] (message tree structure)

    NodeObject structure:
        - id: string (node identifier)
        - message: MessageObject | null (null for non-message nodes)
        - parent: string | null (parent node id)
        - children: list[str] (child node ids)

    MessageObject structure:
        - id: string (message identifier)
        - author: {"role": str} (user, assistant, system, etc.)
        - content: {"content_type": str, "parts": list[str]}
        - create_time: float (Unix timestamp)
        - metadata: dict (provider-specific fields)

Performance Targets (T028):
    - 10K conversations parsed in <5 seconds (FR-444)
    - <1GB memory usage for large exports (SC-001)
    - Lazy iteration (no upfront file loading)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Literal

import ijson
from pydantic import ValidationError as PydanticValidationError

from echomine.exceptions import ParseError, ValidationError
from echomine.models.conversation import Conversation
from echomine.models.message import Message

if TYPE_CHECKING:
    from decimal import Decimal

# Module logger for operational visibility
logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """Adapter for streaming OpenAI conversation exports.

    This adapter uses ijson to stream-parse OpenAI ChatGPT export files with
    O(1) memory complexity. Conversations are yielded one at a time, enabling
    processing of arbitrarily large export files on modest hardware.

    Memory Model:
        - Streaming parser state: ~10-50MB (ijson buffer)
        - Per-conversation overhead: ~5MB (metadata + message tree)
        - Total working set: <100MB regardless of file size

    Error Handling Strategy:
        - FileNotFoundError: Raised for missing files (fail-fast)
        - ParseError: Raised for invalid JSON syntax (fail-fast)
        - ValidationError: Raised for schema violations (fail-fast during streaming)
        - Malformed conversations: Logged and skipped (graceful degradation)

    Example:
        ```python
        from pathlib import Path
        from echomine.adapters import OpenAIAdapter

        adapter = OpenAIAdapter()

        # Stream all conversations (lazy iteration)
        for conversation in adapter.stream_conversations(Path("export.json")):
            print(f"{conversation.title}: {conversation.message_count} messages")

        # Process first N conversations only (memory-efficient)
        conversations = []
        for i, conv in enumerate(adapter.stream_conversations(Path("export.json"))):
            conversations.append(conv)
            if i >= 9:  # First 10 conversations
                break
        ```

    Requirements:
        - FR-003: O(1) memory streaming implementation
        - FR-018: Extract conversation metadata (id, title, timestamps)
        - FR-122: Use ijson for incremental JSON parsing
        - FR-281-285: Skip malformed entries with warning logs
        - SC-001: Memory usage <1GB for large exports
    """

    def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
        """Stream conversations from OpenAI export file with O(1) memory.

        This method uses ijson to incrementally parse the export file, yielding
        Conversation objects one at a time. The entire file is NEVER loaded into
        memory - only the current conversation being parsed.

        Streaming Behavior:
            - Returns iterator (lazy evaluation)
            - Conversations yielded in file order
            - Parser state bounded by ijson buffer (~50MB)
            - No buffering between conversations

        Error Handling:
            - Invalid JSON: Raises ParseError immediately
            - Missing file: Raises FileNotFoundError
            - Schema violations: Raises ValidationError (Pydantic)
            - Empty array: Succeeds, yields zero conversations

        Args:
            file_path: Path to OpenAI export JSON file

        Yields:
            Conversation objects parsed from export

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If JSON is malformed (syntax errors)
            ValidationError: If conversation data violates schema

        Example:
            ```python
            # Basic usage
            adapter = OpenAIAdapter()
            for conv in adapter.stream_conversations(Path("export.json")):
                print(f"Conversation: {conv.title}")

            # Handle errors
            try:
                conversations = list(adapter.stream_conversations(path))
            except ParseError as e:
                print(f"Invalid export format: {e}")
            except ValidationError as e:
                print(f"Schema violation: {e}")
            ```

        Memory Complexity: O(1) for file size, O(N) for single conversation
        Time Complexity: O(M) where M = total conversations in file
        """
        # Open file in binary mode for ijson (required for streaming)
        # FileNotFoundError raised naturally by open() if file missing
        try:
            with open(file_path, "rb") as f:
                # Stream top-level array items using ijson
                # Memory: O(1) - ijson maintains bounded buffer
                # Each "item" is a complete conversation object
                try:
                    items = ijson.items(f, "item")

                    for raw_conversation in items:
                        # Parse individual conversation
                        # Memory: O(N) where N = messages in this conversation
                        try:
                            conversation = self._parse_conversation(raw_conversation)
                            yield conversation
                        except PydanticValidationError as e:
                            # Convert Pydantic ValidationError to our ValidationError
                            # Re-raise with conversation context for debugging
                            conversation_id = raw_conversation.get("id", "unknown")
                            error_msg = f"Validation error in conversation {conversation_id}: {e}"
                            raise ValidationError(error_msg) from e

                except ijson.JSONError as e:
                    # ijson.JSONError raised for malformed JSON
                    # Convert to our ParseError for consistent error handling
                    raise ParseError(f"Invalid JSON in export file: {e}") from e

        except FileNotFoundError:
            # Re-raise FileNotFoundError without wrapping
            # This is a standard Python exception, no conversion needed
            raise

    def _parse_conversation(self, raw_data: dict[str, Any]) -> Conversation:
        """Parse raw OpenAI conversation dict to Conversation model.

        Transforms OpenAI export structure to unified Conversation model:
        1. Extract messages from mapping tree structure
        2. Convert Unix timestamps to UTC datetime
        3. Normalize nested fields (author.role, content.parts)
        4. Build Message and Conversation objects with Pydantic validation

        Args:
            raw_data: Raw conversation dict from OpenAI export

        Returns:
            Validated Conversation object

        Raises:
            PydanticValidationError: If data violates Conversation schema
            KeyError: If required field missing from raw data

        Memory: O(N) where N = message count in conversation
        """
        # Extract messages from mapping structure
        # Memory: O(N) - creates list of N messages
        messages = self._extract_messages_from_mapping(
            raw_data.get("mapping", {})
        )

        # Validate required fields exist before attempting conversion
        # Missing fields will cause KeyError, which we catch and re-raise as PydanticValidationError
        try:
            conversation_id = raw_data["id"]
            title = raw_data["title"]
            create_time = raw_data["create_time"]
            update_time = raw_data["update_time"]
        except KeyError as e:
            # Convert KeyError to PydanticValidationError for consistency
            # This ensures test expectations are met (ValidationError expected)
            # Use from_exception_data correctly with error list
            missing_field = str(e.args[0])
            raise PydanticValidationError.from_exception_data(
                "Conversation",
                [
                    {
                        "type": "missing",
                        "loc": (missing_field,),
                        "input": raw_data,
                    }
                ],
            ) from e

        # Convert Unix timestamps to UTC datetime
        # OpenAI uses float timestamps (seconds since epoch)
        # ijson returns Decimal objects - convert to float first
        # Handle None timestamps (can occur in real exports) - use Unix epoch as fallback
        created_at = (
            datetime.fromtimestamp(float(create_time), tz=UTC)
            if create_time is not None
            else datetime.fromtimestamp(0, tz=UTC)  # Unix epoch: 1970-01-01
        )
        updated_at = (
            datetime.fromtimestamp(float(update_time), tz=UTC)
            if update_time is not None
            else datetime.fromtimestamp(0, tz=UTC)  # Unix epoch: 1970-01-01
        )

        # Build Conversation model (Pydantic validation automatic)
        # Raises PydanticValidationError if required fields missing
        return Conversation(
            id=conversation_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata={
                "moderation_results": raw_data.get("moderation_results", []),
                "current_node": raw_data.get("current_node"),
            },
        )

    def _extract_messages_from_mapping(
        self, mapping: dict[str, Any]
    ) -> list[Message]:
        """Extract messages from OpenAI mapping tree structure.

        OpenAI stores messages in a dict-based tree where:
        - Keys are node IDs
        - Values are node objects with message, parent, children
        - Some nodes have null message field (non-message nodes)

        This method:
        1. Filters nodes with non-null message field
        2. Extracts message data from nested structure
        3. Converts to Message models
        4. Sorts chronologically by timestamp

        Args:
            mapping: OpenAI mapping dict (node_id -> node_object)

        Returns:
            List of Message objects sorted by timestamp

        Memory: O(N) where N = message count
        """
        messages: list[Message] = []

        # Iterate through mapping nodes
        # Memory: O(1) per iteration - no accumulation
        for node_id, node_data in mapping.items():
            # Skip nodes without message field (navigation nodes)
            message_data = node_data.get("message")
            if message_data is None:
                continue

            # Parse message from node
            # Memory: O(1) per message
            try:
                message = self._parse_message(message_data, node_data)
                messages.append(message)
            except (KeyError, ValueError, PydanticValidationError) as e:
                # Graceful degradation: skip malformed messages
                # FR-281: Log and continue instead of failing
                logger.warning(
                    f"Skipping malformed message in node {node_id}: {e}"
                )
                continue

        # Sort messages chronologically
        # Memory: O(N) - in-place sort
        messages.sort(key=lambda m: m.timestamp)

        return messages

    def _parse_message(
        self, message_data: dict[str, Any], node_data: dict[str, Any]
    ) -> Message:
        """Parse OpenAI message dict to Message model.

        Handles nested OpenAI structure:
        - author.role -> role (normalized to user/assistant/system)
        - content.parts[0] -> content (first part only)
        - create_time -> timestamp (Unix to datetime)
        - parent field from node_data -> parent_id

        Args:
            message_data: Message object from OpenAI export
            node_data: Parent node object (contains parent field)

        Returns:
            Validated Message object

        Raises:
            PydanticValidationError: If message violates Message schema
            KeyError: If required nested field missing

        Memory: O(1)
        """
        # Extract and normalize role
        # OpenAI uses various roles: user, assistant, system, tool
        # We normalize to our three-role model
        raw_role = message_data["author"]["role"]
        role = self._normalize_role(raw_role)

        # Extract content from parts array or handle special content types
        # OpenAI content structure varies by type:
        # - Text messages: content.parts is list[str]
        # - Image messages: content is dict with content_type='image_asset_pointer'
        # - Other types: may have different structures
        content_data = message_data.get("content", {})

        if isinstance(content_data, dict):
            content_type = content_data.get("content_type", "text")

            if content_type == "text":
                # Standard text message - extract from parts array
                content_parts = content_data.get("parts", [])
                content = content_parts[0] if content_parts and isinstance(content_parts[0], str) else ""
            elif content_type in ("image_asset_pointer", "image"):
                # Image message - use placeholder text
                content = "[Image]"
            elif content_type == "code":
                # Code message - extract from parts if available
                content_parts = content_data.get("parts", [])
                content = content_parts[0] if content_parts and isinstance(content_parts[0], str) else "[Code]"
            else:
                # Unknown content type - use placeholder
                content = f"[{content_type}]"
        else:
            # Unexpected content structure - use empty string
            content = ""

        # Convert Unix timestamp to UTC datetime
        # ijson returns Decimal objects - convert to float first
        # Handle None timestamps (can occur in real exports) - use Unix epoch as fallback
        create_time = message_data.get("create_time")
        timestamp = (
            datetime.fromtimestamp(float(create_time), tz=UTC)
            if create_time is not None
            else datetime.fromtimestamp(0, tz=UTC)  # Unix epoch: 1970-01-01
        )

        # Extract parent_id from node structure
        # None for root messages
        parent_id = node_data.get("parent")

        # Build Message model (Pydantic validation automatic)
        return Message(
            id=message_data["id"],
            content=content,
            role=role,
            timestamp=timestamp,
            parent_id=parent_id,
            metadata={
                "original_role": raw_role,
                "update_time": message_data.get("update_time"),
            },
        )

    def _normalize_role(self, raw_role: str) -> Literal["user", "assistant", "system"]:
        """Normalize OpenAI role to standard user/assistant/system.

        OpenAI supports various roles:
        - user: Human input
        - assistant: AI response
        - system: System messages
        - tool: Tool execution (maps to assistant)

        Args:
            raw_role: Original role from OpenAI export

        Returns:
            Normalized role: "user", "assistant", or "system"

        Memory: O(1)
        """
        # Map OpenAI roles to our normalized roles
        role_mapping: dict[str, Literal["user", "assistant", "system"]] = {
            "user": "user",
            "assistant": "assistant",
            "system": "system",
            "tool": "assistant",  # Tool calls are assistant actions
        }

        # Default unknown roles to assistant
        return role_mapping.get(raw_role, "assistant")
