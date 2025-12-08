"""Output formatters for CLI commands.

This module provides formatters for converting conversation data to
human-readable text tables and machine-readable JSON output.

Constitution Compliance:
    - Principle I: Library-first (formatters are pure functions, no side effects)
    - FR-018: Human-readable output with simple text tables
    - FR-019: Pipeline-friendly output (works with grep, awk, head)
    - CHK040: Simple text table format without Rich dependency for table rendering
    - FR-036: Rich table format for enhanced terminal output
    - FR-037: Score color coding (>0.7 green, 0.4-0.7 yellow, <0.4 red)
    - FR-038: Role color coding (user=green, assistant=blue, system=yellow)
    - FR-040: Rich disabled when stdout not TTY
    - FR-041: Rich disabled with --json flag

Architecture:
    - format_text_table(): Default human-readable output (plain text)
    - format_json(): Machine-readable JSON for pipelines (NDJSON)
    - create_rich_table(): Rich table format for TTY output
    - get_score_color(): Color coding for relevance scores
    - get_role_color(): Color coding for message roles
    - is_rich_enabled(): TTY detection for Rich formatting
    - Both functions are pure: input -> output, no I/O
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Literal

from rich.table import Table


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
            title = title[: title_width - 3] + "..."

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
    json_output = json.dumps(conv_dicts, separators=(",", ":"), ensure_ascii=False)

    # Return with trailing newline (Unix convention)
    return json_output + "\n"


def format_search_results(results: list[SearchResult[Conversation]]) -> str:
    """Format search results as human-readable text table.

    Shows:
    - Score (0.00-1.00, higher = more relevant)
    - ID (conversation UUID, truncated to 36 chars)
    - Title (truncated to 30 chars)
    - Snippet (matched text, truncated to 40 chars) [FR-021]
    - Created date
    - Message count

    Args:
        results: List of SearchResult objects with scores

    Returns:
        Formatted text table

    Example Output:
        Score  ID                                    Title                          Snippet                                   Created              Messages
        ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
        1.00   a1b2c3d4-e5f6-7890-abcd-ef1234567890  Python async best practices    Python is great for...                    2024-03-15 14:23:11        47
        0.85   b2c3d4e5-f6a7-8901-bcde-f12345678901  Intro to Python for beginners  Learn Python basics...                    2024-03-14 09:15:42        12

    Requirements:
        - FR-018: Human-readable format
        - FR-019: Pipeline-friendly output
        - FR-021: Snippet column in output
        - CHK031: Output to stdout (caller responsibility)
    """
    if not results:
        return "No matching conversations found.\n"

    # Column widths (consistent with list command format)
    score_width = 6
    id_width = 36
    title_width = 30
    snippet_width = 40  # FR-021: Snippet column
    created_width = 20
    messages_width = 8

    # Header
    header = f"{'Score':<{score_width}} {'ID':<{id_width}}  {'Title':<{title_width}}  {'Snippet':<{snippet_width}}  {'Created':<{created_width}}  {'Messages':>{messages_width}}"

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
            title = title[: title_width - 3] + "..."

        # Format snippet (FR-021)
        snippet = result.snippet or ""
        if len(snippet) > snippet_width:
            snippet = snippet[: snippet_width - 3] + "..."

        # Format created date
        created = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Message count
        msg_count = conv.message_count

        row = f"{score_str:<{score_width}} {conv_id:<{id_width}}  {title:<{title_width}}  {snippet:<{snippet_width}}  {created:<{created_width}}  {msg_count:>{messages_width}}"
        rows.append(row)

    # Combine all parts
    lines = [header, separator] + rows

    # Return with trailing newline
    return "\n".join(lines) + "\n"


def format_search_results_json(
    results: list[SearchResult[Conversation]],
    query_keywords: list[str] | None = None,
    query_phrases: list[str] | None = None,
    query_match_mode: str = "any",
    query_exclude_keywords: list[str] | None = None,
    query_role_filter: str | None = None,
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

        results_array.append(
            {
                "conversation_id": conv.id,  # FR-302: Use conversation_id not nested id
                "title": conv.title,
                "created_at": created_at,
                "updated_at": updated_at,
                "score": result.score,
                "matched_message_ids": result.matched_message_ids,
                "message_count": conv.message_count,
                "snippet": result.snippet,  # FR-024: Snippet in JSON output
            }
        )

    # Build metadata object (FR-303)
    metadata = {
        "query": {
            "keywords": query_keywords,
            "phrases": query_phrases,  # v1.1.0: Phrase search (FR-001)
            "match_mode": query_match_mode,  # v1.1.0: Boolean match mode (FR-007)
            "exclude_keywords": query_exclude_keywords,  # v1.1.0: Exclude keywords (FR-012)
            "role_filter": query_role_filter,  # v1.1.0: Role filter (FR-017)
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


# ============================================================================
# Rich Formatting Functions (FR-036 to FR-041)
# ============================================================================


def get_score_color(score: float) -> str:
    """Get color name for relevance score based on threshold.

    Color Coding (FR-037):
        - > 0.7: green (high relevance)
        - 0.4 - 0.7: yellow (medium relevance)
        - < 0.4: red (low relevance)

    Args:
        score: Relevance score (0.0 to 1.0)

    Returns:
        Color name string compatible with Rich styling

    Example:
        >>> get_score_color(0.85)
        'green'
        >>> get_score_color(0.55)
        'yellow'
        >>> get_score_color(0.25)
        'red'

    Requirements:
        - FR-037: Score color coding
    """
    if score > 0.7:
        return "green"
    if score >= 0.4:
        return "yellow"
    return "red"


def get_role_color(role: str) -> str:
    """Get color name for message role.

    Color Coding (FR-038):
        - user: green
        - assistant: blue
        - system: yellow
        - other: white (default)

    Args:
        role: Message role string

    Returns:
        Color name string compatible with Rich styling

    Example:
        >>> get_role_color("user")
        'green'
        >>> get_role_color("assistant")
        'blue'
        >>> get_role_color("system")
        'yellow'

    Requirements:
        - FR-038: Role color coding
    """
    role_colors: dict[str, str] = {
        "user": "green",
        "assistant": "blue",
        "system": "yellow",
    }
    return role_colors.get(role, "white")


def is_rich_enabled(json_flag: bool, force: bool = False) -> bool:
    """Check if Rich formatting should be enabled.

    Rich formatting is enabled when:
        1. stdout is a TTY (not piped or redirected)
        2. --json flag is NOT set
        3. OR force=True (for testing/debugging)

    Args:
        json_flag: True if --json flag is set
        force: Force Rich on regardless of TTY (for testing)

    Returns:
        True if Rich should be used, False for plain text

    Example:
        >>> is_rich_enabled(json_flag=False)  # TTY
        True
        >>> is_rich_enabled(json_flag=True)  # --json set
        False

    Requirements:
        - FR-040: Rich disabled when stdout not TTY
        - FR-041: Rich disabled with --json flag
    """
    # Force flag overrides all checks (for testing)
    if force:
        return True

    # --json flag disables Rich (FR-041)
    if json_flag:
        return False

    # Check if stdout is TTY (FR-040)
    return sys.stdout.isatty()


def create_rich_table(conversations: list[Conversation]) -> Table:
    """Create Rich table for conversation list display.

    Creates a visually enhanced table with:
        - Box borders with Unicode characters
        - Column headers (ID, Title, Messages, Created)
        - Right-aligned message count
        - Formatted timestamps

    Args:
        conversations: List of Conversation objects to display

    Returns:
        Rich Table instance ready for console.print()

    Example:
        >>> table = create_rich_table([conversation1, conversation2])
        >>> console = Console()
        >>> console.print(table)

    Requirements:
        - FR-036: Rich table format for list/search results
    """
    # Create table with box borders
    table = Table(show_header=True, header_style="bold cyan", border_style="blue")

    # Add columns with alignment
    table.add_column("ID", style="dim", width=36)
    table.add_column("Title", style="cyan", width=30)
    table.add_column("Messages", justify="right", style="magenta")
    table.add_column("Created", style="green")

    # Add rows
    for conv in conversations:
        # Format timestamp (remove timezone for display)
        created = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate title if needed
        title = conv.title
        if len(title) > 30:
            title = title[:27] + "..."

        # Add row
        table.add_row(
            conv.id,
            title,
            str(conv.message_count),
            created,
        )

    return table


def create_rich_search_table(results: list[SearchResult[Conversation]]) -> Table:
    """Create Rich table for search results with colored scores.

    Creates a visually enhanced table with:
        - Box borders with Unicode characters
        - Column headers (Score, ID, Title, Snippet, Created, Messages)
        - Color-coded scores (FR-037: >0.7 green, 0.4-0.7 yellow, <0.4 red)
        - Right-aligned message count
        - Formatted timestamps

    Args:
        results: List of SearchResult objects to display

    Returns:
        Rich Table instance ready for console.print()

    Example:
        >>> table = create_rich_search_table([result1, result2])
        >>> console = Console()
        >>> console.print(table)

    Requirements:
        - FR-036: Rich table format for search results
        - FR-037: Score color coding
    """
    # Create table with box borders
    table = Table(show_header=True, header_style="bold cyan", border_style="blue")

    # Add columns with alignment
    table.add_column("Score", justify="right", style="bold")
    table.add_column("ID", style="dim", width=36)
    table.add_column("Title", style="cyan", width=30)
    table.add_column("Snippet", style="white", width=40)
    table.add_column("Created", style="green")
    table.add_column("Messages", justify="right", style="magenta")

    # Add rows with color-coded scores
    for result in results:
        conv = result.conversation

        # Format score with color (FR-037)
        score_color = get_score_color(result.score)
        score_text = f"[{score_color}]{result.score:.2f}[/{score_color}]"

        # Format timestamp
        created = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate title if needed
        title = conv.title
        if len(title) > 30:
            title = title[:27] + "..."

        # Truncate snippet if needed
        snippet = result.snippet or ""
        if len(snippet) > 40:
            snippet = snippet[:37] + "..."

        # Add row
        table.add_row(
            score_text,
            conv.id,
            title,
            snippet,
            created,
            str(conv.message_count),
        )

    return table


def resolve_format_conflict(
    format: str, json: bool, json_comes_last: bool
) -> Literal["text", "json", "csv"]:
    """Resolve conflicting format flags with last-wins policy.

    When both --format and --json flags are specified, the last flag wins.
    Emits a warning to stderr about the conflict.

    Args:
        format: Value of --format flag (e.g., "csv", "text", "json")
        json: True if --json flag is set
        json_comes_last: True if --json appeared after --format in args

    Returns:
        Final format choice based on last-wins policy

    Example:
        >>> resolve_format_conflict("csv", True, json_comes_last=True)
        'json'  # --json wins
        >>> resolve_format_conflict("csv", True, json_comes_last=False)
        'csv'  # --format wins

    Requirements:
        - FR-041a: Conflicting format flags - last wins with warning
    """
    # Check if there's a conflict
    # Conflict occurs when --json is set AND --format is not "json"
    if json and format != "json":
        # Emit warning to stderr
        if json_comes_last:
            winner = "JSON"
            sys.stderr.write(
                f"WARNING: Conflicting output formats: using {winner} (last flag wins)\n"
            )
            return "json"
        winner = format.upper()
        sys.stderr.write(f"WARNING: Conflicting output formats: using {winner} (last flag wins)\n")
        return format  # type: ignore[return-value]

    # No conflict - use json if flag set, otherwise format
    if json:
        return "json"
    return format  # type: ignore[return-value]
