"""Output formatters for CLI commands.

This module provides formatters for converting conversation data to
human-readable text tables and machine-readable JSON output.

Constitution Compliance:
    - Principle I: Library-first (formatters are pure functions, no side effects)
    - FR-018: Human-readable output with simple text tables
    - FR-019: Pipeline-friendly output (works with grep, awk, head)
    - CHK040: Simple text table format without Rich dependency for table rendering

Architecture:
    - format_text_table(): Default human-readable output
    - format_json(): Machine-readable JSON for pipelines (NDJSON)
    - Both functions are pure: input -> output, no I/O
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echomine.models.conversation import Conversation
    from echomine.models.search import SearchResult


def format_text_table(conversations: list[Conversation]) -> str:
    """Format conversations as simple text table (CHK040).

    Creates a pipeline-friendly text table with fixed-width columns:
    - ID column (36 chars for UUID)
    - Title column (30 chars, truncated with ...)
    - Created column (19 chars for ISO 8601 timestamp)
    - Messages column (8 chars, right-aligned)

    The table uses simple ASCII characters (no box drawing) for maximum
    compatibility with Unix tools (grep, awk, head, tail).

    Args:
        conversations: List of Conversation objects to format

    Returns:
        Formatted text table as string (includes trailing newline)

    Example:
        >>> convs = [conversation1, conversation2]
        >>> print(format_text_table(convs))
        ID                                    Title                          Created              Messages
        ────────────────────────────────────────────────────────────────────────────────────────────────────
        a1b2c3d4-e5f6-7890-abcd-ef1234567890  Python async best practices    2024-03-15 14:23:11        47
        b2c3d4e5-f6a7-8901-bcde-f12345678901  Fix database migration error   2024-03-14 09:15:42        12

    Requirements:
        - FR-018: Human-readable format
        - FR-019: Pipeline-friendly (plain text)
        - CHK040: Simple text table (no Rich)
    """
    # Column widths (total width: ~110 chars fits standard terminal)
    id_width = 36
    title_width = 30
    created_width = 19
    messages_width = 8

    # Build header row
    header = f"{'ID':<{id_width}}  {'Title':<{title_width}}  {'Created':<{created_width}}  {'Messages':>{messages_width}}"

    # Build separator (using box drawing character for better visual)
    separator = "─" * len(header)

    # Build data rows
    rows = []
    for conv in conversations:
        # Format ID (truncate if needed, but UUIDs are exactly 36 chars)
        conv_id = conv.id[:id_width]

        # Format title (truncate with ellipsis if >30 chars)
        title = conv.title
        if len(title) > title_width:
            title = title[:title_width - 3] + "..."

        # Format timestamp (ISO 8601 without timezone, just local representation)
        # Remove timezone info for display (tests expect "2024-03-15 14:23:11" format)
        created = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Format message count (right-aligned)
        message_count = str(conv.message_count)

        # Build row
        row = f"{conv_id:<{id_width}}  {title:<{title_width}}  {created:<{created_width}}  {message_count:>{messages_width}}"
        rows.append(row)

    # Handle empty conversation list
    if not rows:
        # Add a message indicating no conversations found
        rows.append("No conversations found")

    # Combine all parts
    lines = [header, separator] + rows

    # Return with trailing newline (required for pipeline compatibility)
    return "\n".join(lines) + "\n"


def format_json(conversations: list[Conversation]) -> str:
    """Format conversations as JSON array.

    Creates a standard JSON array (not NDJSON) for programmatic use.
    Each conversation is serialized as an object with key fields:
    - id: Conversation identifier
    - title: Conversation title
    - created_at: ISO 8601 timestamp (always present)
    - updated_at: ISO 8601 timestamp (uses created_at if never updated)
    - message_count: Number of messages

    The output is valid JSON that can be parsed with `jq` or other
    JSON processing tools.

    Timestamp Handling:
        - created_at: Always present (required field)
        - updated_at: Uses updated_at_or_created property (never null in output)
        - This ensures JSON consumers always get valid timestamps

    Args:
        conversations: List of Conversation objects to format

    Returns:
        JSON array string (compact format, includes trailing newline)

    Example:
        >>> convs = [conversation1, conversation2]
        >>> print(format_json(convs))
        [{"id": "a1b2...", "title": "Test", "created_at": "2024-03-15T14:23:11", "updated_at": "2024-03-15T14:23:11", "message_count": 47}]

    Requirements:
        - FR-018: Alternative JSON format for programmatic use
        - FR-019: Pipeline-friendly (valid JSON for jq)
        - FR-301-306: JSON output schema with created_at/updated_at
        - CLI spec: --format json flag
    """
    # Build list of conversation dicts
    conv_dicts = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": conv.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%S"),
            "message_count": conv.message_count,
        }
        conv_dicts.append(conv_dict)

    # Serialize to JSON (compact format for pipeline efficiency)
    # separators=(',', ':') removes whitespace for compact output
    json_output = json.dumps(conv_dicts, separators=(',', ':'), ensure_ascii=False)

    # Return with trailing newline (Unix convention)
    return json_output + "\n"


def format_search_results(results: list[SearchResult[Conversation]]) -> str:
    """Format search results as human-readable text table.

    Shows:
    - Score (0.00-1.00, higher = more relevant)
    - ID (conversation UUID, truncated to 36 chars)
    - Title (truncated to 30 chars)
    - Created date
    - Message count

    Args:
        results: List of SearchResult objects with scores

    Returns:
        Formatted text table

    Example Output:
        Score  ID                                    Title                          Created              Messages
        ─────────────────────────────────────────────────────────────────────────────────────────────────────────
        1.00   a1b2c3d4-e5f6-7890-abcd-ef1234567890  Python async best practices    2024-03-15 14:23:11        47
        0.85   b2c3d4e5-f6a7-8901-bcde-f12345678901  Intro to Python for beginners  2024-03-14 09:15:42        12

    Requirements:
        - FR-018: Human-readable format
        - FR-019: Pipeline-friendly output
        - CHK031: Output to stdout (caller responsibility)
    """
    if not results:
        return "No matching conversations found.\n"

    # Column widths (consistent with list command format)
    score_width = 6
    id_width = 36
    title_width = 30
    created_width = 20
    messages_width = 8

    # Header
    header = f"{'Score':<{score_width}} {'ID':<{id_width}}  {'Title':<{title_width}}  {'Created':<{created_width}}  {'Messages':>{messages_width}}"

    # Separator
    separator = "─" * len(header)

    # Build data rows
    rows = []
    for result in results:
        conv = result.conversation
        score_str = f"{result.score:.2f}"

        # Format ID (truncate if needed, but UUIDs are exactly 36 chars)
        conv_id = conv.id[:id_width]

        # Truncate title
        title = conv.title
        if len(title) > title_width:
            title = title[:title_width - 3] + "..."

        # Format created date
        created = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Message count
        msg_count = conv.message_count

        row = f"{score_str:<{score_width}} {conv_id:<{id_width}}  {title:<{title_width}}  {created:<{created_width}}  {msg_count:>{messages_width}}"
        rows.append(row)

    # Combine all parts
    lines = [header, separator] + rows

    # Return with trailing newline
    return "\n".join(lines) + "\n"


def format_search_results_json(
    results: list[SearchResult[Conversation]],
    query_keywords: list[str] | None = None,
    query_title_filter: str | None = None,
    query_from_date: str | None = None,
    query_to_date: str | None = None,
    query_limit: int = 10,
    total_results: int | None = None,
    skipped_conversations: int = 0,
    elapsed_seconds: float = 0.0,
) -> str:
    """Format search results as JSON with metadata wrapper (FR-301-306).

    JSON Schema (FR-301):
        {
          "results": [
            {
              "conversation_id": "uuid",
              "title": "string",
              "created_at": "ISO 8601 UTC",
              "updated_at": "ISO 8601 UTC",
              "score": 0.85,
              "matched_message_ids": ["msg-1", "msg-2"],
              "message_count": 42
            }
          ],
          "metadata": {
            "query": {
              "keywords": ["algorithm", "python"],
              "title_filter": null,
              "date_from": null,
              "date_to": null,
              "limit": 10
            },
            "total_results": 5,
            "skipped_conversations": 2,
            "elapsed_seconds": 1.234
          }
        }

    Timestamp Handling:
        - created_at: Always present (required field)
        - updated_at: Uses updated_at_or_created property (never null in output)
        - Format: ISO 8601 with UTC timezone (FR-304): YYYY-MM-DDTHH:MM:SSZ
        - This ensures JSON consumers always get valid timestamps

    Args:
        results: List of SearchResult objects
        query_keywords: Keywords used in search query
        query_title_filter: Title filter used in search query
        query_from_date: From date used in search query (ISO 8601 format)
        query_to_date: To date used in search query (ISO 8601 format)
        query_limit: Limit parameter used in search query
        total_results: Total number of results returned (defaults to len(results))
        skipped_conversations: Number of conversations skipped due to errors
        elapsed_seconds: Query execution time in seconds

    Returns:
        JSON string with results and metadata (FR-305: pretty-printed with 2-space indent)

    Requirements:
        - FR-301: Wrapper schema with results and metadata
        - FR-302: Flattened conversation fields (conversation_id, not nested)
        - FR-303: Metadata includes query, total_results, skipped_conversations, elapsed_seconds
        - FR-304: ISO 8601 timestamps with UTC (YYYY-MM-DDTHH:MM:SSZ)
        - FR-305: Valid JSON, pretty-printed with 2-space indentation
        - FR-019: Pipeline-friendly (valid JSON for jq)
        - CHK031: Output to stdout (caller responsibility)
    """
    # Build results array with flattened structure (FR-302)
    results_array = []
    for result in results:
        conv = result.conversation
        # FR-304: ISO 8601 with UTC timezone (append 'Z' for UTC)
        created_at = conv.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_at = conv.updated_at_or_created.strftime("%Y-%m-%dT%H:%M:%SZ")

        results_array.append({
            "conversation_id": conv.id,  # FR-302: Use conversation_id not nested id
            "title": conv.title,
            "created_at": created_at,
            "updated_at": updated_at,
            "score": result.score,
            "matched_message_ids": result.matched_message_ids,
            "message_count": conv.message_count,
        })

    # Build metadata object (FR-303)
    metadata = {
        "query": {
            "keywords": query_keywords,
            "title_filter": query_title_filter,
            "date_from": query_from_date,
            "date_to": query_to_date,
            "limit": query_limit,
        },
        "total_results": total_results if total_results is not None else len(results),
        "skipped_conversations": skipped_conversations,
        "elapsed_seconds": round(elapsed_seconds, 3),  # Round to millisecond precision
    }

    # Build final output with wrapper (FR-301)
    output = {
        "results": results_array,
        "metadata": metadata,
    }

    # FR-305: Pretty-print with 2-space indentation
    return json.dumps(output, indent=2, ensure_ascii=False) + "\n"
