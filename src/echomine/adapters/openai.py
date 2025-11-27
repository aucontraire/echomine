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
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import ijson
from pydantic import ValidationError as PydanticValidationError

from echomine.exceptions import ParseError
from echomine.models.conversation import Conversation
from echomine.models.image import ImageRef
from echomine.models.message import Message
from echomine.models.protocols import OnSkipCallback, ProgressCallback
from echomine.models.search import SearchQuery, SearchResult
from echomine.search.ranking import BM25Scorer


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

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: ProgressCallback | None = None,
        on_skip: OnSkipCallback | None = None,
    ) -> Iterator[Conversation]:
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
            progress_callback: Optional callback invoked every 100 conversations (FR-069)
            on_skip: Optional callback invoked when malformed entries skipped (FR-107)

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
                    count = 0  # Track for progress_callback (FR-069)

                    for raw_conversation in items:
                        # Parse individual conversation
                        # Memory: O(N) where N = messages in this conversation
                        try:
                            conversation = self._parse_conversation(raw_conversation)
                            count += 1

                            # Invoke progress callback every 100 items (FR-069)
                            if progress_callback and count % 100 == 0:
                                progress_callback(count)

                            yield conversation
                        except PydanticValidationError as e:
                            # Graceful degradation: skip malformed entries (FR-281)
                            conversation_id = raw_conversation.get("id", "unknown")
                            reason = f"Validation error: {e}"

                            # Invoke on_skip callback if provided (FR-107)
                            if on_skip:
                                on_skip(conversation_id, reason)

                            # Log warning but continue processing (FR-281)
                            logger.warning(
                                "Skipped malformed conversation",
                                extra={
                                    "conversation_id": conversation_id,
                                    "reason": reason,
                                },
                            )
                            continue  # Skip this conversation, process next

                except ijson.JSONError as e:
                    # ijson.JSONError raised for malformed JSON
                    # Convert to our ParseError for consistent error handling (FR-039, FR-041)
                    raise ParseError(
                        f"JSON parsing failed: {e}. "
                        f"Verify export file '{file_path}' is valid JSON from OpenAI ChatGPT."
                    ) from e

        except FileNotFoundError:
            # Re-raise FileNotFoundError without wrapping
            # This is a standard Python exception, no conversion needed
            raise

    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        *,
        progress_callback: ProgressCallback | None = None,
        on_skip: OnSkipCallback | None = None,
    ) -> Iterator[SearchResult[Conversation]]:
        """Search conversations with BM25 relevance ranking.

        Algorithm:
        1. Stream all conversations (O(1) memory per conversation)
        2. Apply title filter if specified (metadata-only, fast)
        3. Apply date range filter if specified
        4. Build corpus and calculate BM25 scores
        5. Rank by relevance (descending)
        6. Apply limit if specified
        7. Yield SearchResult objects one at a time

        Args:
            file_path: Path to OpenAI export file
            query: SearchQuery with keywords, title_filter, limit
            progress_callback: Optional callback invoked per conversation processed
            on_skip: Optional callback for malformed entries

        Yields:
            SearchResult[Conversation] with ranked results and scores

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If JSON is malformed

        Performance:
            - Memory: O(N) where N = matching conversations
            - Time: O(M) where M = total conversations in file
            - Early termination: Not implemented (stream all for BM25)

        Example:
            ```python
            adapter = OpenAIAdapter()
            query = SearchQuery(keywords=["python"], limit=10)

            for result in adapter.search(Path("export.json"), query):
                print(f"{result.score:.2f}: {result.conversation.title}")
            ```
        """
        # Stream conversations and apply filters
        conversations: list[Conversation] = []
        corpus_texts: list[str] = []

        count = 0
        for conv in self.stream_conversations(file_path):
            count += 1

            # Progress callback (every 100 items per FR-069)
            if progress_callback and count % 100 == 0:
                progress_callback(count)

            # Title filter (fast metadata check)
            if query.has_title_filter():
                assert query.title_filter is not None  # Type narrowing
                if query.title_filter.lower() not in conv.title.lower():
                    continue  # Skip non-matching titles

            # Date range filter
            if query.has_date_filter():
                conv_date = conv.created_at.date()

                # Check from_date (inclusive)
                if query.from_date is not None and conv_date < query.from_date:
                    continue

                # Check to_date (inclusive)
                if query.to_date is not None and conv_date > query.to_date:
                    continue

            # Build corpus text (title + all message content)
            conv_text = f"{conv.title} " + " ".join(m.content for m in conv.messages)

            conversations.append(conv)
            corpus_texts.append(conv_text)

        # Final progress callback
        if progress_callback:
            progress_callback(count)

        # Handle empty results
        if not conversations:
            return  # Empty iterator

        # Calculate average document length for BM25
        # Use regex tokenization to match BM25Scorer's tokenization
        import re

        def tokenize_for_length(text: str) -> int:
            """Count tokens using same method as BM25Scorer."""
            text_lower = text.lower()
            count = len(re.findall(r"[a-z0-9]+", text_lower))
            count += len(re.findall(r"[^\W\d_a-z]", text_lower))
            return count

        avg_doc_length = sum(tokenize_for_length(text) for text in corpus_texts) / len(corpus_texts)

        # Initialize BM25 scorer
        scorer = BM25Scorer(corpus=corpus_texts, avg_doc_length=avg_doc_length)

        # Score all conversations
        scored_conversations: list[tuple[Conversation, float, list[str]]] = []

        for conv, conv_text in zip(conversations, corpus_texts):
            if query.has_keyword_search():
                assert query.keywords is not None  # Type narrowing
                # Calculate BM25 score for keywords
                score = scorer.score(conv_text, query.keywords)

                # Track which messages contain keyword matches
                matched_message_ids = self._find_matched_messages(conv, query.keywords)

                # Skip conversations with no matches (score = 0)
                if score == 0.0:
                    continue
            else:
                # No keywords - all have score 1.0 (title/date filter only)
                score = 1.0
                matched_message_ids = []

            scored_conversations.append((conv, score, matched_message_ids))

        # Handle no results after filtering
        if not scored_conversations:
            return  # Empty iterator

        # Sort by relevance (descending)
        scored_conversations.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores to [0.0, 1.0] range using BM25 normalization formula (FR-319)
        # Formula: score_normalized = score_raw / (score_raw + 1)
        # This ensures consistent score interpretation across queries
        scored_conversations = [
            (conv, score / (score + 1.0) if score > 0 else 0.0, msg_ids)
            for conv, score, msg_ids in scored_conversations
        ]

        # Apply limit if specified
        if query.limit:
            scored_conversations = scored_conversations[: query.limit]

        # Yield SearchResult objects
        for conv, score, matched_message_ids in scored_conversations:
            yield SearchResult[Conversation](
                conversation=conv,
                score=score,
                matched_message_ids=matched_message_ids,
            )

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Conversation | None:
        """Retrieve specific conversation by UUID (FR-155, FR-217, FR-356).

        Uses streaming search for memory efficiency - O(N) time, O(1) memory.
        For large files with frequent ID lookups, consider building an index.

        Args:
            file_path: Path to OpenAI export JSON file
            conversation_id: UUID of conversation to retrieve

        Returns:
            Conversation object if found, None otherwise (FR-155)

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If JSON is malformed

        Example:
            ```python
            adapter = OpenAIAdapter()
            conv = adapter.get_conversation_by_id(
                Path("export.json"),
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            )
            if conv:
                print(f"Found: {conv.title}")
            else:
                print("Conversation not found")
            ```

        Performance:
            - Time: O(N) where N = conversations in file (streaming search)
            - Memory: O(1) for file size, O(M) for single conversation
            - Early termination: Returns immediately when match found
        """
        # Stream conversations and return first match
        for conversation in self.stream_conversations(file_path):
            if conversation.id == conversation_id:
                return conversation

        # Not found - return None per FR-155
        return None

    def _find_matched_messages(self, conversation: Conversation, keywords: list[str]) -> list[str]:
        """Find message IDs containing any of the keywords.

        Uses word-boundary matching to find keywords as complete tokens,
        not just substrings. This matches the BM25 tokenization approach.

        Tokenizes keywords the same way as BM25Scorer to handle multi-character
        keywords (e.g., Chinese "编程" -> ["编", "程"]).

        Args:
            conversation: Conversation to search
            keywords: List of keywords to match (will be tokenized)

        Returns:
            List of message IDs containing keyword matches

        Example:
            ```python
            conv = Conversation(...)
            matched_ids = self._find_matched_messages(conv, ["python", "java"])
            # Returns IDs of messages containing "python" OR "java"
            ```
        """
        import re

        matched_ids: list[str] = []

        # Tokenize keywords (same as BM25Scorer)
        keyword_tokens: list[str] = []
        for keyword in keywords:
            kw_lower = keyword.lower()
            # Latin tokens
            keyword_tokens.extend(re.findall(r"[a-z0-9]+", kw_lower))
            # Non-Latin tokens (CJK characters)
            keyword_tokens.extend(re.findall(r"[^\W\d_a-z]", kw_lower))

        for message in conversation.messages:
            # Tokenize message content using same method as BM25Scorer
            content_lower = message.content.lower()
            message_tokens: list[str] = []

            # Latin tokens
            message_tokens.extend(re.findall(r"[a-z0-9]+", content_lower))
            # Non-Latin tokens (CJK characters)
            message_tokens.extend(re.findall(r"[^\W\d_a-z]", content_lower))

            # Check if any keyword token is in the message tokens
            if any(kw_token in message_tokens for kw_token in keyword_tokens):
                matched_ids.append(message.id)

        return matched_ids

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
        messages = self._extract_messages_from_mapping(raw_data.get("mapping", {}))

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
        #
        # Timestamp Handling Strategy:
        # - created_at: REQUIRED - if null, raise ValidationError (malformed data)
        # - updated_at: OPTIONAL - if null, set to None (Conversation model handles fallback)
        #
        # Rationale: Every conversation MUST have creation time (data integrity).
        # Updates are optional - None means "never modified" (semantically correct).
        if create_time is None:
            # Missing creation timestamp = malformed data, fail validation
            raise PydanticValidationError.from_exception_data(
                "Conversation",
                [
                    {
                        "type": "missing",
                        "loc": ("create_time",),
                        "input": raw_data,
                    }
                ],
            )

        created_at = datetime.fromtimestamp(float(create_time), tz=UTC)

        # Handle optional updated_at - None is valid (conversation never updated)
        updated_at: datetime | None = (
            datetime.fromtimestamp(float(update_time), tz=UTC) if update_time is not None else None
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

    def _extract_messages_from_mapping(self, mapping: dict[str, Any]) -> list[Message]:
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
                logger.warning(f"Skipping malformed message in node {node_id}: {e}")
                continue

        # Sort messages chronologically
        # Memory: O(N) - in-place sort
        messages.sort(key=lambda m: m.timestamp)

        return messages

    def _parse_message(self, message_data: dict[str, Any], node_data: dict[str, Any]) -> Message:
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
        # - Multimodal messages: content.parts is list[str | dict] with image_asset_pointer
        # - Image messages: content is dict with content_type='image_asset_pointer'
        # - Other types: may have different structures
        content_data = message_data.get("content", {})
        images: list[ImageRef] = []  # Initialize images list

        if isinstance(content_data, dict):
            content_type = content_data.get("content_type", "text")

            if content_type == "multimodal_text":
                # Multimodal message - extract text and images from parts
                content_parts = content_data.get("parts", [])
                content, images = self._parse_multimodal_parts(content_parts)
            elif content_type == "text":
                # Standard text message - extract from parts array
                content_parts = content_data.get("parts", [])
                content = (
                    content_parts[0] if content_parts and isinstance(content_parts[0], str) else ""
                )
            elif content_type in ("image_asset_pointer", "image"):
                # Image message - use placeholder text
                content = "[Image]"
            elif content_type == "code":
                # Code message - extract from parts if available
                content_parts = content_data.get("parts", [])
                content = (
                    content_parts[0]
                    if content_parts and isinstance(content_parts[0], str)
                    else "[Code]"
                )
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
            images=images,  # Pass extracted images (empty list for non-multimodal)
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

    def _parse_multimodal_parts(self, parts: list[Any]) -> tuple[str, list[ImageRef]]:
        """Extract text and images from multimodal_text content parts.

        OpenAI's multimodal_text content contains mixed text and image_asset_pointer
        objects in the parts array. This method separates them into:
        - Concatenated text content (string parts joined with spaces)
        - List of ImageRef objects (from image_asset_pointer parts)

        Args:
            parts: List of parts from multimodal_text content
                   Can contain strings (text) and dicts (image_asset_pointer)

        Returns:
            Tuple of (concatenated_text, image_refs)
            - concatenated_text: All text parts joined with spaces
            - image_refs: List of ImageRef objects for images

        Example OpenAI structure:
            ```json
            {
              "content_type": "multimodal_text",
              "parts": [
                {
                  "content_type": "image_asset_pointer",
                  "asset_pointer": "sediment://file_xxx",
                  "size_bytes": 89512,
                  "width": 1536,
                  "height": 503
                },
                "Here is the diagram you requested"
              ]
            }
            ```

        Memory: O(N) where N = number of parts
        """
        text_parts: list[str] = []
        images: list[ImageRef] = []

        for part in parts:
            if isinstance(part, str):
                # Text part - add to text_parts
                text_parts.append(part)
            elif isinstance(part, dict):
                # Check if it's an image_asset_pointer
                content_type = part.get("content_type")
                if content_type == "image_asset_pointer":
                    # Extract image data and create ImageRef
                    try:
                        asset_pointer = part.get("asset_pointer", "")
                        if asset_pointer:  # Only create ImageRef if asset_pointer exists
                            image_ref = ImageRef(
                                asset_pointer=asset_pointer,
                                size_bytes=part.get("size_bytes"),
                                width=part.get("width"),
                                height=part.get("height"),
                                metadata={
                                    k: v
                                    for k, v in part.items()
                                    if k
                                    not in {
                                        "asset_pointer",
                                        "content_type",
                                        "size_bytes",
                                        "width",
                                        "height",
                                    }
                                },
                            )
                            images.append(image_ref)
                    except (KeyError, PydanticValidationError) as e:
                        # Skip malformed image references (graceful degradation)
                        logger.warning(f"Skipping malformed image_asset_pointer: {e}")
                        continue
                else:
                    # Other dict types - skip or log
                    logger.debug(f"Skipping non-image dict part: {content_type}")
            # Ignore other types (list, int, etc.)

        # Concatenate text parts with spaces
        concatenated_text = " ".join(text_parts)

        return concatenated_text, images
