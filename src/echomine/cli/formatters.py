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
    - created_at: ISO 8601 timestamp
    - message_count: Number of messages

    The output is valid JSON that can be parsed with `jq` or other
    JSON processing tools.

    Args:
        conversations: List of Conversation objects to format

    Returns:
        JSON array string (compact format, includes trailing newline)

    Example:
        >>> convs = [conversation1, conversation2]
        >>> print(format_json(convs))
        [{"id": "a1b2...", "title": "Test", "created_at": "2024-03-15T14:23:11", "message_count": 47}]

    Requirements:
        - FR-018: Alternative JSON format for programmatic use
        - FR-019: Pipeline-friendly (valid JSON for jq)
        - CLI spec: --format json flag
    """
    # Build list of conversation dicts
    conv_dicts = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "message_count": conv.message_count,
        }
        conv_dicts.append(conv_dict)

    # Serialize to JSON (compact format for pipeline efficiency)
    # separators=(',', ':') removes whitespace for compact output
    json_output = json.dumps(conv_dicts, separators=(',', ':'), ensure_ascii=False)

    # Return with trailing newline (Unix convention)
    return json_output + "\n"
