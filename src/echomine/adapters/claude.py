"""Anthropic Claude conversation export adapter with ijson streaming parser.

This module provides the ClaudeAdapter class for streaming conversations from
Anthropic Claude export files with O(1) memory complexity using ijson.

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

Claude Export Schema:
    Root: JSON array of conversation objects
    Each conversation:
        - uuid: string (unique identifier)
        - name: string (conversation title)
        - created_at: string (ISO 8601 timestamp)
        - updated_at: string (ISO 8601 timestamp)
        - chat_messages: list[MessageObject] (flat message array)

    MessageObject structure:
        - uuid: string (message identifier)
        - text: string (message content)
        - sender: string ("human" or "assistant")
        - created_at: string (ISO 8601 timestamp)
        - updated_at: string (ISO 8601 timestamp)
        - attachments: list[AttachmentObject] (optional)

Performance Targets:
    - 10K conversations parsed in <5 seconds (FR-444)
    - <1GB memory usage for large exports (SC-001)
    - Lazy iteration (no upfront file loading)
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import ijson
from pydantic import ValidationError as PydanticValidationError

from echomine.exceptions import ParseError
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.protocols import OnSkipCallback, ProgressCallback
from echomine.models.search import SearchQuery, SearchResult
from echomine.search.ranking import (
    BM25Scorer,
    all_terms_present,
    exclude_filter,
    phrase_matches,
)
from echomine.search.snippet import extract_snippet_from_messages


# Module logger for operational visibility
logger = logging.getLogger(__name__)


class ClaudeAdapter:
    """Adapter for streaming Anthropic Claude conversation exports.

    This adapter uses ijson to stream-parse Anthropic Claude export files with
    O(1) memory complexity. Conversations are yielded one at a time, enabling
    processing of arbitrarily large export files on modest hardware.

    Memory Model:
        - Streaming parser state: ~10-50MB (ijson buffer)
        - Per-conversation overhead: ~5MB (metadata + messages)
        - Total working set: <100MB regardless of file size

    Error Handling Strategy:
        - FileNotFoundError: Raised for missing files (fail-fast)
        - ParseError: Raised for invalid JSON syntax (fail-fast)
        - ValidationError: Raised for schema violations (fail-fast during streaming)
        - Malformed conversations: Logged and skipped (graceful degradation)

    Example:
        ```python
        from pathlib import Path
        from echomine.adapters import ClaudeAdapter

        adapter = ClaudeAdapter()

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

    def _find_matched_messages(self, messages: list[Message], keywords: list[str]) -> list[str]:
        """Find message IDs containing any of the keywords.

        Uses word-boundary matching to find keywords as complete tokens,
        not just substrings. This matches the BM25 tokenization approach.

        Tokenizes keywords the same way as BM25Scorer to handle multi-character
        keywords (e.g., Chinese characters).

        Args:
            messages: List of messages to search (pre-filtered by role if applicable)
            keywords: List of keywords to match (will be tokenized)

        Returns:
            List of message IDs containing keyword matches

        Example:
            ```python
            messages = [msg1, msg2, msg3]
            matched_ids = self._find_matched_messages(messages, ["python", "java"])
            # Returns IDs of messages containing "python" OR "java"
            ```
        """
        matched_ids: list[str] = []

        # Tokenize keywords (same as BM25Scorer)
        keyword_tokens: list[str] = []
        for keyword in keywords:
            kw_lower = keyword.lower()
            # Latin tokens
            keyword_tokens.extend(re.findall(r"[a-z0-9]+", kw_lower))
            # Non-Latin tokens (CJK characters)
            keyword_tokens.extend(re.findall(r"[^\W\d_a-z]", kw_lower))

        for message in messages:
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

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse ISO 8601 timestamp to timezone-aware datetime.

        Handles Z suffix (Zulu/UTC) by replacing with +00:00 for fromisoformat().

        Args:
            ts_str: ISO 8601 timestamp string (e.g., "2025-10-01T18:42:27.303515Z")

        Returns:
            Timezone-aware datetime in UTC

        Raises:
            ValueError: If timestamp string is invalid
        """
        # Handle Z suffix (Zulu/UTC) - fromisoformat doesn't support 'Z'
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)

    def _extract_content_from_blocks(self, content_blocks: list[dict[str, Any]]) -> str:
        """Extract text from content blocks, skipping tool blocks.

        Claude content blocks can be:
        - type="text": Regular text content (INCLUDE)
        - type="tool_use": Tool invocation (SKIP per FR-015a)
        - type="tool_result": Tool execution result (SKIP per FR-015a)

        Multiple text blocks are concatenated with newline separator.

        Args:
            content_blocks: List of content block dicts from Claude message

        Returns:
            Concatenated text from all text-type blocks, empty string if no text blocks

        Example:
            ```python
            blocks = [
                {"type": "text", "text": "Hello"},
                {"type": "tool_use", "id": "toolu_123", "name": "calc", "input": {}},
                {"type": "text", "text": "World"}
            ]
            # Returns: "Hello\\nWorld"
            ```
        """
        text_parts: list[str] = []
        for block in content_blocks:
            block_type = block.get("type", "")
            if block_type == "text":
                text_content = block.get("text", "")
                if text_content:  # Only add non-empty text
                    text_parts.append(text_content)
            # Skip tool_use and tool_result blocks (FR-015a)

        return "\n".join(text_parts)

    def _parse_message(
        self, raw_message: dict[str, Any], conversation_created_at: datetime
    ) -> Message:
        """Parse Claude message dict to Message model.

        Claude message structure:
            - uuid: string (message identifier)
            - text: string (fallback message content)
            - content: list[ContentBlock] (primary content source)
            - sender: string ("human" or "assistant")
            - created_at: ISO 8601 timestamp string (optional, falls back to conversation created_at)
            - updated_at: ISO 8601 timestamp string (unused for messages)

        Content extraction strategy (FR-012, FR-015):
            1. Extract text from content[type=text] blocks (skip tool_use/tool_result)
            2. If content extraction yields empty string, fall back to text field (FR-015b)

        Role mapping (FR-013):
            - "human" → "user"
            - "assistant" → "assistant"
            - unknown → "assistant" (safe fallback)

        Args:
            raw_message: Raw message dict from Claude export
            conversation_created_at: Conversation's created_at for timestamp fallback (FR-019)

        Returns:
            Validated Message object

        Raises:
            PydanticValidationError: If message violates Message schema
            KeyError: If required field missing
        """
        # Extract fields
        message_id = raw_message.get("uuid", "")
        text_field = raw_message.get("text", "")
        content_blocks = raw_message.get("content", [])
        sender = raw_message.get("sender", "assistant")
        created_at_str = raw_message.get("created_at", "")

        # Extract content from content blocks (FR-012, FR-015)
        content = self._extract_content_from_blocks(content_blocks)

        # Fallback to text field if content is empty (FR-015b)
        if not content:
            content = text_field

        # Parse timestamp with fallback to conversation created_at (FR-019)
        try:
            timestamp = (
                self._parse_timestamp(created_at_str) if created_at_str else conversation_created_at
            )
        except ValueError:
            # If timestamp parsing fails, use conversation created_at
            timestamp = conversation_created_at

        # Normalize role (FR-013)
        role_mapping = {
            "human": "user",
            "assistant": "assistant",
        }
        role = role_mapping.get(sender, "assistant")  # Safe fallback

        # Claude messages don't have parent_id in the flat array structure
        # All messages are at root level (no threading in Claude exports - FR-020)
        return Message(
            id=message_id,
            content=content,
            role=role,  # type: ignore[arg-type]  # Literal validated by Pydantic
            timestamp=timestamp,
            parent_id=None,  # Flat structure, no threading
            metadata={"original_sender": sender} if sender not in role_mapping else {},
        )

    def _parse_conversation(self, raw: dict[str, Any]) -> Conversation:
        """Parse Claude conversation dict to Conversation model.

        Claude conversation structure:
            - uuid: string (unique identifier)
            - name: string (conversation title, may be empty)
            - created_at: ISO 8601 timestamp string
            - updated_at: ISO 8601 timestamp string
            - chat_messages: list[MessageObject] (flat message array)
            - summary: string (IGNORED per FR-007)
            - account: dict (IGNORED per FR-008)

        Field mappings:
            - uuid → id (FR-002)
            - name → title (FR-003), empty string → "(No title)"
            - created_at → created_at (FR-004), parsed to datetime
            - updated_at → updated_at (FR-005), parsed to datetime
            - chat_messages → messages (FR-006)

        Args:
            raw: Raw conversation dict from Claude export

        Returns:
            Validated Conversation object

        Raises:
            PydanticValidationError: If conversation violates Conversation schema
            KeyError: If required field missing
        """
        # Extract fields
        conversation_id = raw.get("uuid", "")
        name = raw.get("name", "")
        created_at_str = raw.get("created_at", "")
        updated_at_str = raw.get("updated_at", "")
        chat_messages = raw.get("chat_messages", [])

        # Parse timestamps
        created_at = self._parse_timestamp(created_at_str)
        updated_at = self._parse_timestamp(updated_at_str)

        # Handle empty title (FR-003): empty string → "(No title)"
        title = name if name else "(No title)"

        # Parse messages (FR-006)
        # Handle empty conversations (FR-010): if chat_messages is empty, skip message parsing
        messages: list[Message] = []
        if chat_messages:
            for raw_message in chat_messages:
                try:
                    # Pass conversation created_at for timestamp fallback (FR-019)
                    message = self._parse_message(raw_message, created_at)
                    messages.append(message)
                except (PydanticValidationError, KeyError, ValueError) as e:
                    # Skip malformed messages within conversation
                    logger.warning(
                        "Skipped malformed message in conversation",
                        extra={
                            "conversation_id": conversation_id,
                            "message_id": raw_message.get("uuid", "unknown"),
                            "reason": str(e),
                        },
                    )
                    continue

        # Conversation model requires at least 1 message (min_length=1)
        # For empty conversations, we need to create a placeholder or skip entirely
        # Based on FR-010, we should handle zero messages gracefully
        # But Conversation model requires min_length=1, so we'll add a placeholder
        if not messages:
            # Create a placeholder message for empty conversations
            # This satisfies the Conversation model's min_length=1 requirement
            messages = [
                Message(
                    id=f"{conversation_id}-placeholder",
                    content="(Empty conversation)",
                    role="system",
                    timestamp=created_at,
                    parent_id=None,
                    metadata={"is_placeholder": True},
                )
            ]

        # FR-007, FR-008: summary and account are IGNORED (not stored in metadata)
        return Conversation(
            id=conversation_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata={},  # No provider-specific metadata stored
        )

    def stream_conversations(
        self,
        file_path: Path,
        *,
        progress_callback: ProgressCallback | None = None,
        on_skip: OnSkipCallback | None = None,
    ) -> Iterator[Conversation]:
        """Stream conversations from Claude export file with O(1) memory.

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
            file_path: Path to Claude export JSON file
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
            adapter = ClaudeAdapter()
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
        try:
            with open(file_path, "rb") as f:
                # Stream parse root array with ijson (FR-001, FR-009)
                items = ijson.items(f, "item")
                count = 0

                for raw in items:
                    try:
                        # Parse conversation (T019)
                        conversation = self._parse_conversation(raw)
                        count += 1

                        # Progress callback every 100 items (FR-069)
                        if progress_callback and count % 100 == 0:
                            progress_callback(count)

                        yield conversation

                    except (PydanticValidationError, KeyError, ValueError) as e:
                        # Graceful degradation: skip malformed conversation (FR-281-285)
                        conversation_id = raw.get("uuid", "unknown")
                        logger.warning(
                            "Skipped malformed conversation",
                            extra={
                                "conversation_id": conversation_id,
                                "reason": str(e),
                            },
                        )

                        # Invoke on_skip callback if provided (FR-107)
                        if on_skip:
                            on_skip(conversation_id, str(e))

                        continue

        except FileNotFoundError:
            # Fail-fast for missing files
            raise
        except ijson.JSONError as e:
            # Fail-fast for invalid JSON syntax
            raise ParseError(f"Failed to parse JSON: {e}") from e

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
            file_path: Path to Claude export file
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
            adapter = ClaudeAdapter()
            query = SearchQuery(keywords=["python"], limit=10)

            for result in adapter.search(Path("export.json"), query):
                print(f"{result.score:.2f}: {result.conversation.title}")
            ```
        """
        # Stream conversations and apply filters
        # Type: (conversation, filtered_messages) for snippet extraction
        conversations: list[tuple[Conversation, list[Message]]] = []
        corpus_texts: list[str] = []

        count = 0
        for conv in self.stream_conversations(file_path, on_skip=on_skip):
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

            # Message count filter
            if query.has_message_count_filter():
                msg_count = conv.message_count

                # Check min_messages (inclusive)
                if query.min_messages is not None and msg_count < query.min_messages:
                    continue

                # Check max_messages (inclusive)
                if query.max_messages is not None and msg_count > query.max_messages:
                    continue

            # Role filter
            if query.role_filter is not None:
                filtered_messages = [m for m in conv.messages if m.role == query.role_filter]
            else:
                filtered_messages = list(conv.messages)

            # Skip conversations with no messages matching the role filter
            if query.role_filter is not None and not filtered_messages:
                continue

            # Build corpus text
            # When role_filter is set, only search in filtered message content (not title)
            # When role_filter is None, include title for metadata-based matching
            if query.role_filter is not None:
                conv_text = " ".join(m.content for m in filtered_messages)
            else:
                conv_text = f"{conv.title} " + " ".join(m.content for m in filtered_messages)

            conversations.append((conv, filtered_messages))
            corpus_texts.append(conv_text)

        # Final progress callback
        if progress_callback:
            progress_callback(count)

        # Handle empty results
        if not conversations:
            return  # Empty iterator

        # Calculate average document length for BM25
        # Use regex tokenization to match BM25Scorer's tokenization
        def tokenize_for_length(text: str) -> int:
            """Count tokens using same method as BM25Scorer."""
            text_lower = text.lower()
            count_val = len(re.findall(r"[a-z0-9]+", text_lower))
            count_val += len(re.findall(r"[^\W\d_a-z]", text_lower))
            return count_val

        avg_doc_length = sum(tokenize_for_length(text) for text in corpus_texts) / len(corpus_texts)

        # Initialize BM25 scorer
        scorer = BM25Scorer(corpus=corpus_texts, avg_doc_length=avg_doc_length)

        # Score all conversations
        # Type: (conversation, score, matched_message_ids, filtered_messages)
        scored_conversations: list[tuple[Conversation, float, list[str], list[Message]]] = []

        for (conv, filtered_msgs), conv_text in zip(conversations, corpus_texts):
            score = 0.0
            matched_message_ids: list[str] = []
            has_keyword_match = False
            has_phrase_match = False

            # Check keyword matches (BM25 scoring)
            if query.has_keyword_search():
                assert query.keywords is not None  # Type narrowing

                # FR-029: match_mode='all' requires ALL keywords present
                if query.match_mode == "all":
                    if all_terms_present(conv_text, query.keywords, scorer):
                        # All keywords present - calculate score
                        score = scorer.score(conv_text, query.keywords)
                        matched_message_ids = self._find_matched_messages(
                            filtered_msgs, query.keywords
                        )
                        has_keyword_match = True
                    # else: keywords don't all match, but may still match phrases (checked below)
                else:
                    # Default 'any' mode: regular BM25 scoring
                    score = scorer.score(conv_text, query.keywords)
                    matched_message_ids = self._find_matched_messages(filtered_msgs, query.keywords)
                    if score > 0.0:
                        has_keyword_match = True

            # Check phrase matches (exact substring matching)
            # FR-023: Phrases use OR logic
            # Phrases can be combined with keywords (OR logic)
            if query.has_phrase_search():
                assert query.phrases is not None  # Type narrowing
                if phrase_matches(conv_text, query.phrases):
                    has_phrase_match = True
                    # If phrase matches but no keyword score, use 1.0
                    if score == 0.0:
                        score = 1.0
                    # Find messages that match the phrases (from filtered messages only)
                    for message in filtered_msgs:
                        if phrase_matches(message.content, query.phrases):
                            if message.id not in matched_message_ids:
                                matched_message_ids.append(message.id)

            # Skip conversations with no matches (neither keyword nor phrase)
            if not has_keyword_match and not has_phrase_match:
                # If no keywords or phrases specified, include all (title/date filter only)
                if not query.has_keyword_search() and not query.has_phrase_search():
                    score = 1.0
                else:
                    continue

            # FR-028: Apply exclude filter after matching, before ranking
            if query.has_exclude_keywords():
                assert query.exclude_keywords is not None  # Type narrowing
                if exclude_filter(conv_text, query.exclude_keywords, scorer):
                    continue  # Skip conversations containing excluded terms

            scored_conversations.append((conv, score, matched_message_ids, filtered_msgs))

        # Handle no results after filtering
        if not scored_conversations:
            return  # Empty iterator

        # Sort conversations based on query parameters (FR-030)
        # FR-043a: Tie-breaking by conversation_id (ascending, lexicographic)
        # FR-043b: Stable sort (Python's sort() is stable by default)
        def get_sort_key(
            item: tuple[Conversation, float, list[str], list[Message]],
        ) -> tuple[float | str | int, str]:
            """Get sort key based on query sort_by parameter.

            Returns tuple for multi-level sorting:
            - Primary: sort_by field value
            - Secondary: conversation_id (tie-breaker)
            """
            conv, score, _, _ = item

            primary_key: float | str | int
            if query.sort_by == "score":
                # Sort by BM25 relevance score
                primary_key = score
            elif query.sort_by == "date":
                # Use updated_at if present, otherwise created_at
                sort_date = conv.updated_at if conv.updated_at is not None else conv.created_at
                # Convert datetime to timestamp for numeric sorting
                primary_key = sort_date.timestamp()
            elif query.sort_by == "title":
                # Case-insensitive title sort
                primary_key = conv.title.lower()
            else:  # query.sort_by == "messages"
                # Sort by message count
                primary_key = conv.message_count

            # Tie-breaking by conversation_id (ascending)
            return (primary_key, conv.id)

        # Apply sorting with reverse based on sort_order
        reverse_sort = query.sort_order == "desc"
        scored_conversations.sort(key=get_sort_key, reverse=reverse_sort)

        # Normalize scores to [0.0, 1.0] range using BM25 normalization formula (FR-319)
        # Formula: score_normalized = score_raw / (score_raw + 1)
        # This ensures consistent score interpretation across queries
        scored_conversations = [
            (conv, score / (score + 1.0) if score > 0 else 0.0, msg_ids, msgs)
            for conv, score, msg_ids, msgs in scored_conversations
        ]

        # Apply limit (always positive integer per SearchQuery validation)
        scored_conversations = scored_conversations[: query.limit]

        # Yield SearchResult objects with snippet extraction
        for conv, score, matched_message_ids, filtered_msgs in scored_conversations:
            # Build keywords list for snippet extraction
            snippet_keywords: list[str] = []
            if query.keywords:
                snippet_keywords.extend(query.keywords)
            if query.phrases:
                snippet_keywords.extend(query.phrases)

            # Extract snippet from matched messages
            snippet, _ = extract_snippet_from_messages(
                filtered_msgs,
                snippet_keywords,
                matched_message_ids,
            )

            yield SearchResult[Conversation](
                conversation=conv,
                score=score,
                matched_message_ids=matched_message_ids,
                snippet=snippet,
            )

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str,
    ) -> Conversation | None:
        """Retrieve specific conversation by UUID (FR-036 to FR-040).

        Uses streaming search for memory efficiency - O(N) time, O(1) memory.
        For large files with frequent ID lookups, consider building an index.

        Supports partial ID matching (prefix) with minimum 4 characters.
        Matching is case-insensitive.

        Args:
            file_path: Path to Claude export JSON file
            conversation_id: UUID (full or prefix >=4 chars) to retrieve

        Returns:
            Conversation object if found, None otherwise (FR-038)

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If JSON is malformed

        Example:
            ```python
            adapter = ClaudeAdapter()

            # Full UUID match
            conv = adapter.get_conversation_by_id(
                Path("export.json"),
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            )

            # Partial prefix match (min 4 chars)
            conv = adapter.get_conversation_by_id(
                Path("export.json"),
                "a1b2"
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
        # Normalize search ID for case-insensitive matching (FR-037, FR-040)
        search_id = conversation_id.lower()
        min_prefix_length = 4

        # Stream conversations and search for match (FR-039)
        for conv in self.stream_conversations(file_path):
            conv_id_lower = conv.id.lower()

            # Full match (FR-037)
            if conv_id_lower == search_id:
                return conv

            # Partial match: prefix with minimum 4 chars (FR-040)
            if len(search_id) >= min_prefix_length and conv_id_lower.startswith(search_id):
                return conv

        # Not found (FR-038)
        return None

    def get_message_by_id(
        self,
        file_path: Path,
        message_id: str,
        *,
        conversation_id: str | None = None,
    ) -> tuple[Message, Conversation] | None:
        """Retrieve specific message by UUID with parent conversation context.

        Searches for a message by ID, optionally scoped to a specific conversation
        for performance optimization. Returns both the message and its parent
        conversation to provide full context.

        Uses streaming search for memory efficiency - O(1) memory usage.

        Args:
            file_path: Path to Claude export JSON file
            message_id: UUID of message to retrieve (FR-042)
            conversation_id: Optional conversation UUID to scope search (FR-043)

        Returns:
            Tuple of (Message, Conversation) if found, None otherwise (FR-044, FR-045).
            The Conversation is the parent containing the message.

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If JSON is malformed

        Example:
            ```python
            adapter = ClaudeAdapter()

            # Search with conversation hint (faster)
            result = adapter.get_message_by_id(
                Path("export.json"),
                "msg-123",
                conversation_id="conv-456"
            )

            # Search all conversations (slower)
            result = adapter.get_message_by_id(
                Path("export.json"),
                "msg-123"
            )

            if result:
                message, conversation = result
                print(f"Message: {message.content}")
                print(f"From conversation: {conversation.title}")
            else:
                print("Message not found")
            ```

        Performance:
            - With conversation_id:
                - Time: O(N) where N = conversations until match
                - Memory: O(1) for file size, O(M) for single conversation
            - Without conversation_id:
                - Time: O(N*M) where N = conversations, M = messages per conversation
                - Memory: O(1) for file size, O(M) for single conversation
            - Early termination: Returns immediately when match found

        Design Notes:
            Returns tuple instead of just Message to provide conversation context
            (title, timestamps, other messages) which is valuable for CLI display
            and analysis workflows.
        """
        # If conversation_id hint provided, search only that conversation (FR-043)
        if conversation_id is not None:
            conv = self.get_conversation_by_id(file_path, conversation_id)
            if conv is not None:
                # Use Conversation.get_message_by_id() for lookup
                msg = conv.get_message_by_id(message_id)
                if msg is not None:
                    return (msg, conv)
            # Conversation not found or message not in conversation
            return None

        # Otherwise, stream all conversations and search each (FR-042)
        for conv in self.stream_conversations(file_path):
            msg = conv.get_message_by_id(message_id)
            if msg is not None:
                return (msg, conv)

        # Not found in any conversation (FR-045)
        return None
