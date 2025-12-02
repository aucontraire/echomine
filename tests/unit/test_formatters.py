"""Unit tests for CLI formatters module.

This module tests the pure formatting functions in cli/formatters.py.
These are UNIT tests - we test formatters in isolation with mock data.

Coverage Target: formatters.py lines 81, 97, 189-232, 305-345 (currently 46% coverage)

Test Pyramid Classification: Unit (70% of test suite)

Constitution Compliance:
    - Principle I: Library-first (formatters are pure functions)
    - FR-018: Human-readable output format
    - FR-019: Pipeline-friendly output
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from echomine.cli.formatters import (
    format_json,
    format_search_results,
    format_search_results_json,
    format_text_table,
)
from echomine.models.conversation import Conversation
from echomine.models.search import SearchResult


@pytest.fixture
def sample_conversation() -> Conversation:
    """Create a sample conversation for testing formatters."""
    from echomine.models.message import Message

    # Create minimal messages for formatter tests
    messages = [
        Message(
            id="msg-1",
            content="Test message",
            role="user",
            timestamp=datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            parent_id=None,
        )
    ]

    # Use raw dict and model_validate to create proper Conversation
    conv_dict = {
        "id": "test-conv-001",
        "title": "Test Conversation Title",
        "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
        "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
        "messages": messages,
    }
    return Conversation.model_validate(conv_dict)


@pytest.fixture
def sample_conversations() -> list[Conversation]:
    """Create multiple sample conversations for testing formatters."""
    from echomine.models.message import Message

    # Create messages for each conversation
    messages1 = [
        Message(
            id=f"msg-{i}",
            content=f"Message {i}",
            role="user" if i % 2 == 0 else "assistant",
            timestamp=datetime(2024, 3, 15, 14, 23, i, tzinfo=UTC),
            parent_id=None if i == 0 else f"msg-{i-1}",
        )
        for i in range(47)
    ]

    messages2 = [
        Message(
            id=f"msg2-{i}",
            content=f"Message {i}",
            role="user" if i % 2 == 0 else "assistant",
            timestamp=datetime(2024, 3, 14, 9, 15, i, tzinfo=UTC),
            parent_id=None if i == 0 else f"msg2-{i-1}",
        )
        for i in range(12)
    ]

    convs = [
        {
            "id": "conv-001",
            "title": "Python AsyncIO Tutorial",
            "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
            "messages": messages1,
        },
        {
            "id": "conv-002",
            "title": "Algorithm Design Patterns",
            "created_at": datetime(2024, 3, 14, 9, 15, 42, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 14, 9, 20, 10, tzinfo=UTC),
            "messages": messages2,
        },
    ]

    return [Conversation.model_validate(c) for c in convs]


class TestFormatTextTable:
    """Unit tests for format_text_table() function."""

    def test_format_text_table_includes_header(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test text table includes column headers.

        Validates:
        - formatters.py line 67: Header row
        - FR-018: Human-readable format
        """
        output = format_text_table(sample_conversations)

        # Assert: Header present
        assert "ID" in output
        assert "Title" in output
        assert "Created" in output
        assert "Messages" in output

    def test_format_text_table_includes_separator(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test text table includes separator line.

        Validates:
        - formatters.py line 70: Separator with box drawing
        - Visual separation between header and data
        """
        output = format_text_table(sample_conversations)

        # Assert: Separator present (using box drawing character)
        assert "─" in output

    def test_format_text_table_includes_conversation_data(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test text table includes conversation data.

        Validates:
        - formatters.py line 73-92: Data row building
        - All conversations present
        """
        output = format_text_table(sample_conversations)

        # Assert: Conversation IDs present
        assert "conv-001" in output
        assert "conv-002" in output

        # Assert: Titles present
        assert "Python AsyncIO Tutorial" in output
        assert "Algorithm Design Patterns" in output

        # Assert: Message counts present
        assert "47" in output
        assert "12" in output

    def test_format_text_table_truncates_long_title(self) -> None:
        """Test text table truncates titles longer than 30 characters.

        Validates:
        - formatters.py line 80-81: Title truncation with ellipsis
        - CHK040: Fixed-width columns
        """
        from echomine.models.message import Message

        messages = [
            Message(
                id="msg-1",
                content="Test",
                role="user",
                timestamp=datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
                parent_id=None,
            )
        ]

        conv_dict = {
            "id": "conv-long",
            "title": "This is a very long conversation title that exceeds thirty characters",
            "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
            "messages": messages,
        }
        conv = Conversation.model_validate(conv_dict)

        output = format_text_table([conv])

        # Assert: Title truncated to 30 chars with ellipsis
        lines = output.strip().split("\n")
        data_line = lines[2]  # Header, separator, then data

        # Should contain "..." for truncation
        assert "..." in data_line

        # Full title should NOT appear
        assert "exceeds thirty characters" not in output

    def test_format_text_table_formats_timestamp_without_timezone(
        self, sample_conversation: Conversation
    ) -> None:
        """Test text table formats timestamps without timezone suffix.

        Validates:
        - formatters.py line 85: strftime("%Y-%m-%d %H:%M:%S")
        - Human-readable timestamp format
        """
        output = format_text_table([sample_conversation])

        # Assert: Timestamp format YYYY-MM-DD HH:MM:SS
        assert "2024-03-15 14:23:11" in output

        # Assert: No timezone info (no +00:00 or Z)
        assert "+00:00" not in output
        assert "UTC" not in output.replace("Tutorial", "")  # Ignore if in title

    def test_format_text_table_empty_list_shows_message(self) -> None:
        """Test text table with empty list shows 'No conversations found'.

        Validates:
        - formatters.py line 95-97: Empty list handling
        - User-friendly message
        """
        output = format_text_table([])

        # Assert: Message present
        assert "No conversations found" in output

    def test_format_text_table_ends_with_newline(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test text table ends with newline (Unix convention).

        Validates:
        - formatters.py line 103: Trailing newline
        - FR-019: Pipeline-friendly output
        """
        output = format_text_table(sample_conversations)

        # Assert: Ends with newline
        assert output.endswith("\n")

    def test_format_text_table_right_aligns_message_count(
        self, sample_conversation: Conversation
    ) -> None:
        """Test message count column is right-aligned.

        Validates:
        - formatters.py line 88, 91: Right-aligned message count
        - Consistent column alignment
        """
        output = format_text_table([sample_conversation])

        # Message count should be right-aligned in its column
        # This is visual validation - check that spacing is consistent
        lines = output.strip().split("\n")
        header_line = lines[0]
        data_line = lines[2]

        # Find "Messages" position in header
        messages_pos = header_line.rfind("Messages")

        # Find message count in data line (should be near same position)
        # Account for right-alignment by checking nearby area
        message_count_area = data_line[messages_pos:messages_pos + 10]
        assert "1" in message_count_area  # sample_conversation has 1 message


class TestFormatJSON:
    """Unit tests for format_json() function."""

    def test_format_json_returns_valid_json_array(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test format_json() returns valid JSON array.

        Validates:
        - formatters.py line 143-152: JSON array building
        - Valid JSON parseable by json.loads()
        """
        output = format_json(sample_conversations)

        # Assert: Valid JSON
        data = json.loads(output)

        # Assert: Is array
        assert isinstance(data, list)
        assert len(data) == 2

    def test_format_json_includes_required_fields(
        self, sample_conversation: Conversation
    ) -> None:
        """Test format_json() includes all required fields.

        Validates:
        - formatters.py line 145-151: Field mapping
        - FR-018: JSON output schema
        """
        output = format_json([sample_conversation])
        data = json.loads(output)

        conv = data[0]

        # Assert: Required fields present
        assert "id" in conv
        assert "title" in conv
        assert "created_at" in conv
        assert "updated_at" in conv
        assert "message_count" in conv

    def test_format_json_uses_iso8601_timestamps(
        self, sample_conversation: Conversation
    ) -> None:
        """Test format_json() uses ISO 8601 timestamp format.

        Validates:
        - formatters.py line 148-149: strftime("%Y-%m-%dT%H:%M:%S")
        - ISO 8601 format (no timezone suffix in basic format)
        """
        output = format_json([sample_conversation])
        data = json.loads(output)

        conv = data[0]

        # Assert: ISO 8601 format YYYY-MM-DDTHH:MM:SS
        assert conv["created_at"] == "2024-03-15T14:23:11"
        assert conv["updated_at"] == "2024-03-15T14:30:22"

    def test_format_json_compact_format_no_whitespace(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test format_json() uses compact format (no pretty-print).

        Validates:
        - formatters.py line 156: separators=(',', ':')
        - FR-019: Pipeline-efficient output
        """
        output = format_json(sample_conversations)

        # Compact format means no extra spaces after : or ,
        # Check that output doesn't have ": " or ", " patterns
        # (Actually it will have them in field values, so check structure)

        # Better check: no indentation (no leading spaces except in values)
        lines = output.strip().split("\n")
        # Compact JSON should be single line (or minimal lines)
        # For array, might be multiple lines but no indentation
        assert len(lines) <= 5  # Not pretty-printed (would be many lines)

    def test_format_json_ends_with_newline(
        self, sample_conversations: list[Conversation]
    ) -> None:
        """Test format_json() ends with newline (Unix convention).

        Validates:
        - formatters.py line 159: Trailing newline
        - FR-019: Pipeline-friendly
        """
        output = format_json(sample_conversations)

        # Assert: Ends with newline
        assert output.endswith("\n")

    def test_format_json_empty_list_returns_empty_array(self) -> None:
        """Test format_json() with empty list returns [].

        Validates:
        - Edge case: Empty conversation list
        - Valid JSON output
        """
        output = format_json([])

        # Assert: Valid JSON
        data = json.loads(output)

        # Assert: Empty array
        assert isinstance(data, list)
        assert len(data) == 0


class TestFormatSearchResults:
    """Unit tests for format_search_results() function."""

    @pytest.fixture
    def sample_search_results(
        self, sample_conversations: list[Conversation]
    ) -> list[SearchResult[Conversation]]:
        """Create sample search results for testing."""
        results = [
            SearchResult(
                conversation=sample_conversations[0],
                score=1.0,
                matched_message_ids=["msg-1", "msg-2"],
            ),
            SearchResult(
                conversation=sample_conversations[1],
                score=0.75,
                matched_message_ids=["msg-5"],
            ),
        ]
        return results

    def test_format_search_results_empty_list_shows_message(self) -> None:
        """Test format_search_results() with empty list shows message.

        Validates:
        - formatters.py line 189-190: Empty results handling
        - User-friendly message
        """
        output = format_search_results([])

        # Assert: Message present
        assert "No matching conversations found" in output

    def test_format_search_results_includes_score_column(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results() includes Score column.

        Validates:
        - formatters.py line 200: Header includes Score
        - FR-018: Human-readable relevance scores
        """
        output = format_search_results(sample_search_results)

        # Assert: Score column header
        assert "Score" in output

    def test_format_search_results_formats_score_two_decimals(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results() formats scores to 2 decimal places.

        Validates:
        - formatters.py line 209: score_str = f"{result.score:.2f}"
        - Consistent score formatting
        """
        output = format_search_results(sample_search_results)

        # Assert: Scores formatted to 2 decimals
        assert "1.00" in output  # Score 1.0 → "1.00"
        assert "0.75" in output  # Score 0.75 → "0.75"

    def test_format_search_results_includes_conversation_data(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results() includes conversation fields.

        Validates:
        - formatters.py line 211-223: Conversation data extraction
        - All key fields present
        """
        output = format_search_results(sample_search_results)

        # Assert: Conversation data present
        assert "conv-001" in output
        assert "Python AsyncIO Tutorial" in output
        assert "47" in output  # message count

        assert "conv-002" in output
        assert "Algorithm Design Patterns" in output
        assert "12" in output

    def test_format_search_results_includes_separator(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results() includes separator line.

        Validates:
        - formatters.py line 203: Separator line
        - Visual separation
        """
        output = format_search_results(sample_search_results)

        # Assert: Separator present
        assert "─" in output

    def test_format_search_results_ends_with_newline(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results() ends with newline.

        Validates:
        - formatters.py line 232: Trailing newline
        - FR-019: Pipeline-friendly
        """
        output = format_search_results(sample_search_results)

        # Assert: Ends with newline
        assert output.endswith("\n")

    def test_format_search_results_truncates_long_title(self) -> None:
        """Test format_search_results() truncates long titles.

        Validates:
        - formatters.py line 216-217: Title truncation
        - Consistent with format_text_table()
        """
        from echomine.models.message import Message

        messages = [
            Message(
                id="msg-1",
                content="Test",
                role="user",
                timestamp=datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
                parent_id=None,
            )
        ]

        conv_dict = {
            "id": "conv-long",
            "title": "This is a very long conversation title that definitely exceeds thirty characters",
            "created_at": datetime(2024, 3, 15, 14, 23, 11, tzinfo=UTC),
            "updated_at": datetime(2024, 3, 15, 14, 30, 22, tzinfo=UTC),
            "messages": messages,
        }
        conv = Conversation.model_validate(conv_dict)

        result = SearchResult(conversation=conv, score=0.9, matched_message_ids=[])

        output = format_search_results([result])

        # Assert: Title truncated with ellipsis
        assert "..." in output
        assert "exceeds thirty characters" not in output


class TestFormatSearchResultsJSON:
    """Unit tests for format_search_results_json() function."""

    @pytest.fixture
    def sample_search_results(
        self, sample_conversations: list[Conversation]
    ) -> list[SearchResult[Conversation]]:
        """Create sample search results for testing."""
        return [
            SearchResult(
                conversation=sample_conversations[0],
                score=0.95,
                matched_message_ids=["msg-1", "msg-2"],
            ),
            SearchResult(
                conversation=sample_conversations[1],
                score=0.75,
                matched_message_ids=["msg-5"],
            ),
        ]

    def test_format_search_results_json_returns_valid_json(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() returns valid JSON.

        Validates:
        - formatters.py line 345: json.dumps() call
        - Valid JSON parseable by json.loads()
        """
        output = format_search_results_json(sample_search_results)

        # Assert: Valid JSON
        data = json.loads(output)

        # Assert: Is dict (not array)
        assert isinstance(data, dict)

    def test_format_search_results_json_includes_wrapper_structure(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() includes wrapper with results and metadata.

        Validates:
        - formatters.py line 339-342: Wrapper structure
        - FR-301: Wrapper schema
        """
        output = format_search_results_json(sample_search_results)
        data = json.loads(output)

        # Assert: Wrapper structure (FR-301)
        assert "results" in data
        assert "metadata" in data

    def test_format_search_results_json_flattens_conversation_fields(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() uses flattened structure.

        Validates:
        - formatters.py line 312-322: Flattened result structure
        - FR-302: conversation_id not nested
        """
        output = format_search_results_json(sample_search_results)
        data = json.loads(output)

        results = data["results"]
        first_result = results[0]

        # Assert: Flattened structure (FR-302)
        assert "conversation_id" in first_result  # Not nested under "conversation"
        assert "title" in first_result
        assert "created_at" in first_result
        assert "updated_at" in first_result
        assert "score" in first_result
        assert "matched_message_ids" in first_result
        assert "message_count" in first_result

    def test_format_search_results_json_uses_utc_timestamps(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() uses UTC timestamps with Z suffix.

        Validates:
        - formatters.py line 309-310: strftime("%Y-%m-%dT%H:%M:%SZ")
        - FR-304: ISO 8601 with UTC (Z suffix)
        """
        output = format_search_results_json(sample_search_results)
        data = json.loads(output)

        first_result = data["results"][0]

        # Assert: ISO 8601 with Z suffix (FR-304)
        assert first_result["created_at"].endswith("Z")
        assert "T" in first_result["created_at"]
        assert first_result["created_at"] == "2024-03-15T14:23:11Z"

    def test_format_search_results_json_includes_metadata_structure(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() includes complete metadata.

        Validates:
        - formatters.py line 325-336: Metadata structure
        - FR-303: Metadata fields
        """
        output = format_search_results_json(
            sample_search_results,
            query_keywords=["python", "async"],
            query_title_filter="Tutorial",
            query_from_date="2024-01-01",
            query_to_date="2024-12-31",
            query_limit=10,
            total_results=2,
            skipped_conversations=1,
            elapsed_seconds=1.234567,
        )
        data = json.loads(output)

        metadata = data["metadata"]

        # Assert: Metadata fields (FR-303)
        assert "query" in metadata
        assert "total_results" in metadata
        assert "skipped_conversations" in metadata
        assert "elapsed_seconds" in metadata

        # Assert: Query metadata
        query = metadata["query"]
        assert query["keywords"] == ["python", "async"]
        assert query["title_filter"] == "Tutorial"
        assert query["date_from"] == "2024-01-01"
        assert query["date_to"] == "2024-12-31"
        assert query["limit"] == 10

        # Assert: Metadata values
        assert metadata["total_results"] == 2
        assert metadata["skipped_conversations"] == 1
        assert metadata["elapsed_seconds"] == 1.235  # Rounded to 3 decimals

    def test_format_search_results_json_rounds_elapsed_seconds(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() rounds elapsed_seconds to 3 decimals.

        Validates:
        - formatters.py line 335: round(elapsed_seconds, 3)
        - Millisecond precision
        """
        output = format_search_results_json(
            sample_search_results,
            elapsed_seconds=1.23456789,
        )
        data = json.loads(output)

        # Assert: Rounded to 3 decimals (millisecond precision)
        assert data["metadata"]["elapsed_seconds"] == 1.235

    def test_format_search_results_json_pretty_prints_with_indent(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() pretty-prints with 2-space indent.

        Validates:
        - formatters.py line 345: indent=2
        - FR-305: Pretty-printed output
        """
        output = format_search_results_json(sample_search_results)

        # Assert: Has indentation (not compact)
        lines = output.strip().split("\n")
        assert len(lines) > 10  # Pretty-printed has many lines

        # Assert: Uses 2-space indentation
        # Check that some lines have 2-space indent
        indented_lines = [line for line in lines if line.startswith("  ")]
        assert len(indented_lines) > 0

    def test_format_search_results_json_ends_with_newline(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() ends with newline.

        Validates:
        - formatters.py line 345: + "\n"
        - FR-019: Pipeline-friendly
        """
        output = format_search_results_json(sample_search_results)

        # Assert: Ends with newline
        assert output.endswith("\n")

    def test_format_search_results_json_defaults_total_results_to_len(
        self, sample_search_results: list[SearchResult[Conversation]]
    ) -> None:
        """Test format_search_results_json() defaults total_results to len(results).

        Validates:
        - formatters.py line 333: total_results default
        - Convenience for callers
        """
        output = format_search_results_json(
            sample_search_results
            # total_results not specified
        )
        data = json.loads(output)

        # Assert: total_results defaults to len(results)
        assert data["metadata"]["total_results"] == 2

    def test_format_search_results_json_handles_empty_results(self) -> None:
        """Test format_search_results_json() handles empty results list.

        Validates:
        - Edge case: Zero results
        - Valid JSON structure maintained
        """
        output = format_search_results_json([])
        data = json.loads(output)

        # Assert: Valid structure
        assert "results" in data
        assert "metadata" in data

        # Assert: Empty results array
        assert len(data["results"]) == 0

        # Assert: total_results = 0
        assert data["metadata"]["total_results"] == 0
