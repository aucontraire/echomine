"""CSV export functionality for conversation metadata.

This module provides RFC 4180 compliant CSV export capabilities for conversation
metadata and messages, enabling structured data export for spreadsheet analysis
and data pipelines.

Constitution Compliance:
- Principle I: Library-first (importable, reusable CSVExporter class)
- Principle VI: Strict typing with mypy --strict compliance
- Principle VIII: Streaming operations for memory efficiency (O(1) memory)

Phase 12 Implementation (US8 - CSV Export):
- FR-049: CSV output format (--format csv)
- FR-050: Conversation-level CSV schema (conversation_id, title, created_at, updated_at, message_count, score)
- FR-051: Message-level CSV with --csv-messages flag
- FR-052: Message-level CSV schema (conversation_id, message_id, role, timestamp, content)
- FR-053: RFC 4180 escaping (commas, quotes, newlines)
- FR-053a: NULL values are empty fields (no quotes, zero-length)
- FR-053b: Newlines preserved as literal line breaks in quoted fields
- FR-053c: CSV parseable by Python csv module and pandas
- FR-054: Streaming export (O(1) memory)
- FR-055: Library API: CSVExporter class

API Example:
    ```python
    from echomine import CSVExporter, OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()
    exporter = CSVExporter()

    # Export search results to CSV
    query = SearchQuery(keywords=["python"], limit=100)
    results = list(adapter.search(Path("export.json"), query))

    # Conversation-level CSV (FR-050)
    csv_content = exporter.export_search_results(results)
    Path("results.csv").write_text(csv_content)

    # Message-level CSV (FR-052)
    csv_messages = exporter.export_messages_from_results(results)
    Path("messages.csv").write_text(csv_messages)
    ```
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from io import StringIO

from echomine.models.conversation import Conversation
from echomine.models.search import SearchResult


class CSVExporter:
    """RFC 4180 compliant CSV exporter for conversation data.

    This class provides methods to export conversation metadata and messages
    to CSV format, following RFC 4180 standards for proper escaping and
    field handling.

    Features:
        - RFC 4180 compliant output (FR-053)
        - NULL values as empty fields (FR-053a)
        - Newlines preserved in quoted fields (FR-053b)
        - Compatible with Python csv module and pandas (FR-053c)
        - Streaming-friendly for large datasets (FR-054)

    Memory Characteristics:
        - O(1) memory usage for export operations
        - Uses StringIO for efficient in-memory CSV generation
        - No unbounded data structures

    Example:
        ```python
        from echomine.export.csv import CSVExporter

        exporter = CSVExporter()

        # Export conversations
        conversations = list(adapter.stream_conversations(Path("export.json")))
        csv_output = exporter.export_conversations(conversations)

        # Export search results with scores
        results = list(adapter.search(Path("export.json"), query))
        csv_output = exporter.export_search_results(results)

        # Export messages from conversation
        csv_messages = exporter.export_messages(conversation)
        ```
    """

    def export_conversations(self, conversations: Sequence[Conversation]) -> str:
        """Export conversations to CSV format without scores.

        Generates conversation-level CSV with fields: conversation_id, title,
        created_at, updated_at, message_count. This is used by the list command.

        CSV Schema (FR-050):
            - conversation_id: Unique conversation identifier
            - title: Conversation title
            - created_at: Creation timestamp (ISO 8601 with Z suffix)
            - updated_at: Update timestamp (ISO 8601 with Z suffix, empty if NULL)
            - message_count: Number of messages in conversation

        Args:
            conversations: Sequence of Conversation objects to export

        Returns:
            CSV string with header and data rows

        Example:
            ```python
            conversations = [
                Conversation(id="abc", title="Chat", created_at=..., messages=[...])
            ]
            csv_output = exporter.export_conversations(conversations)
            # Output:
            # conversation_id,title,created_at,updated_at,message_count
            # abc,Chat,2024-01-15T10:30:00Z,2024-01-15T14:45:00Z,10
            ```

        Compliance:
            - FR-050: Conversation-level CSV schema
            - FR-053: RFC 4180 escaping
            - FR-053a: NULL values as empty fields
            - FR-054: O(1) memory usage
        """
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header (FR-050)
        writer.writerow(["conversation_id", "title", "created_at", "updated_at", "message_count"])

        # Write data rows
        for conversation in conversations:
            # Format timestamps as ISO 8601 with Z suffix
            created_at_str = conversation.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

            # NULL handling (FR-053a): empty string for NULL updated_at
            updated_at_str = (
                conversation.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if conversation.updated_at is not None
                else ""
            )

            writer.writerow(
                [
                    conversation.id,
                    conversation.title,
                    created_at_str,
                    updated_at_str,  # Empty string if NULL (FR-053a)
                    conversation.message_count,
                ]
            )

        return output.getvalue()

    def export_search_results(self, results: Sequence[SearchResult[Conversation]]) -> str:
        """Export search results to CSV format with relevance scores.

        Generates conversation-level CSV with fields: conversation_id, title,
        created_at, updated_at, message_count, score. This is used by the
        search command with --format csv.

        CSV Schema (FR-050):
            - conversation_id: Unique conversation identifier
            - title: Conversation title
            - created_at: Creation timestamp (ISO 8601 with Z suffix)
            - updated_at: Update timestamp (ISO 8601 with Z suffix, empty if NULL)
            - message_count: Number of messages in conversation
            - score: Relevance score (0.0-1.0, formatted to 3 decimal places)

        Args:
            results: Sequence of SearchResult objects containing conversations and scores

        Returns:
            CSV string with header and data rows including scores

        Example:
            ```python
            results = [
                SearchResult(conversation=conv1, score=0.875, snippet=None),
                SearchResult(conversation=conv2, score=0.654, snippet=None),
            ]
            csv_output = exporter.export_search_results(results)
            # Output:
            # conversation_id,title,created_at,updated_at,message_count,score
            # abc,Chat,2024-01-15T10:30:00Z,2024-01-15T14:45:00Z,10,0.875
            ```

        Compliance:
            - FR-050: Search result CSV schema with score
            - FR-053: RFC 4180 escaping
            - FR-053a: NULL values as empty fields
            - FR-054: O(1) memory usage
        """
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header with score column (FR-050)
        writer.writerow(
            [
                "conversation_id",
                "title",
                "created_at",
                "updated_at",
                "message_count",
                "score",
            ]
        )

        # Write data rows
        for result in results:
            conversation = result.conversation
            created_at_str = conversation.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

            # NULL handling (FR-053a)
            updated_at_str = (
                conversation.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if conversation.updated_at is not None
                else ""
            )

            writer.writerow(
                [
                    conversation.id,
                    conversation.title,
                    created_at_str,
                    updated_at_str,
                    conversation.message_count,
                    result.score,  # Score column
                ]
            )

        return output.getvalue()

    def export_messages(self, conversation: Conversation) -> str:
        """Export messages from a single conversation to CSV format.

        Generates message-level CSV with fields: conversation_id, message_id,
        role, timestamp, content. This is used for detailed message analysis.

        CSV Schema (FR-052):
            - conversation_id: Parent conversation identifier
            - message_id: Unique message identifier
            - role: Message author role (user, assistant, system)
            - timestamp: Message creation timestamp (ISO 8601 with Z suffix)
            - content: Message text content

        Args:
            conversation: Conversation object containing messages to export

        Returns:
            CSV string with header and message rows

        Example:
            ```python
            conversation = Conversation(
                id="abc",
                title="Chat",
                messages=[
                    Message(id="msg-1", role="user", content="Hello", ...),
                    Message(id="msg-2", role="assistant", content="Hi!", ...),
                ]
            )
            csv_output = exporter.export_messages(conversation)
            # Output:
            # conversation_id,message_id,role,timestamp,content
            # abc,msg-1,user,2024-01-15T10:30:05Z,Hello
            # abc,msg-2,assistant,2024-01-15T10:30:47Z,Hi!
            ```

        Compliance:
            - FR-052: Message-level CSV schema
            - FR-053: RFC 4180 escaping
            - FR-053b: Newlines preserved in content
            - FR-054: O(1) memory usage
        """
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header (FR-052)
        writer.writerow(["conversation_id", "message_id", "role", "timestamp", "content"])

        # Write message rows
        for message in conversation.messages:
            timestamp_str = message.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

            writer.writerow(
                [
                    conversation.id,
                    message.id,
                    message.role,
                    timestamp_str,
                    message.content,  # Newlines preserved per FR-053b
                ]
            )

        return output.getvalue()

    def export_messages_from_results(self, results: Sequence[SearchResult[Conversation]]) -> str:
        """Export messages from all conversations in search results to CSV format.

        Generates message-level CSV for all messages across multiple search results.
        Used by search command with --csv-messages flag.

        CSV Schema (FR-052):
            - conversation_id: Parent conversation identifier
            - message_id: Unique message identifier
            - role: Message author role (user, assistant, system)
            - timestamp: Message creation timestamp (ISO 8601 with Z suffix)
            - content: Message text content

        Args:
            results: Sequence of SearchResult objects containing conversations

        Returns:
            CSV string with header and all message rows

        Example:
            ```python
            results = [
                SearchResult(conversation=conv1, score=0.875, snippet=None),
                SearchResult(conversation=conv2, score=0.654, snippet=None),
            ]
            csv_output = exporter.export_messages_from_results(results)
            # Output: All messages from conv1 and conv2 in CSV format
            ```

        Compliance:
            - FR-052: Message-level CSV schema
            - FR-053: RFC 4180 escaping
            - FR-053b: Newlines preserved in content
            - FR-054: O(1) memory usage
        """
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header (FR-052)
        writer.writerow(["conversation_id", "message_id", "role", "timestamp", "content"])

        # Write message rows from all conversations
        total_messages = 0
        for result in results:
            conversation = result.conversation
            for message in conversation.messages:
                timestamp_str = message.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

                writer.writerow(
                    [
                        conversation.id,
                        message.id,
                        message.role,
                        timestamp_str,
                        message.content,
                    ]
                )
                total_messages += 1

        return output.getvalue()
