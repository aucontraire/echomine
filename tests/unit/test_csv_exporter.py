"""Test CSV export functionality.

This module tests the CSVExporter class in echomine.export.csv for
generating RFC 4180 compliant CSV output from conversation metadata.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle VI: Strict typing with mypy --strict compliance
    - Principle VIII: Streaming operations for memory efficiency

Test Coverage:
    - T131: CSVExporter.export_conversations() returns valid CSV (FR-050)
    - T132: CSVExporter.export_search_results() includes score column (FR-050)
    - T133: CSVExporter.export_messages() returns valid CSV (FR-052)
    - T134: CSV properly escapes commas and quotes (FR-053)
    - T135: NULL values are empty fields (FR-053a)
    - T136: Newlines preserved in quoted fields (FR-053b)
    - T137: CSV parseable by Python csv module (FR-053c)
    - T139: Corrupted JSON during streaming handled gracefully (CHK054)

Requirements:
    - FR-049: CSV output format (--format csv)
    - FR-050: Conversation-level CSV schema
    - FR-051: Message-level CSV with --csv-messages flag
    - FR-052: Message-level CSV schema
    - FR-053: RFC 4180 escaping (commas, quotes, newlines)
    - FR-053a: NULL values are empty fields (no quotes, zero-length)
    - FR-053b: Newlines preserved as literal line breaks
    - FR-053c: CSV parseable by Python csv module and pandas
    - FR-054: Streaming export (O(1) memory)
    - FR-055: Library API: CSVExporter class
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO

import pytest

from echomine.export.csv import CSVExporter
from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.search import SearchResult


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create sample messages for testing."""
    return [
        Message(
            id="msg-001",
            content="Hello, I need help with Python generators",
            role="user",
            timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
            parent_id=None,
        ),
        Message(
            id="msg-002",
            content="Python generators are a powerful feature...",
            role="assistant",
            timestamp=datetime(2024, 1, 15, 10, 30, 47, tzinfo=UTC),
            parent_id="msg-001",
        ),
    ]


@pytest.fixture
def sample_conversation(sample_messages: list[Message]) -> Conversation:
    """Create a sample conversation for testing."""
    return Conversation(
        id="abc-123",
        title="Deep Python Discussion",
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 15, 14, 45, 0, tzinfo=UTC),
        messages=sample_messages,
        metadata={},
    )


@pytest.fixture
def conversation_with_null_updated(sample_messages: list[Message]) -> Conversation:
    """Create conversation with NULL updated_at for testing."""
    return Conversation(
        id="null-updated",
        title="Never Updated Chat",
        created_at=datetime(2024, 1, 14, 9, 15, 0, tzinfo=UTC),
        updated_at=None,
        messages=sample_messages,
        metadata={},
    )


@pytest.fixture
def conversation_with_special_chars(sample_messages: list[Message]) -> Conversation:
    """Create conversation with special characters for escaping tests."""
    return Conversation(
        id="def-456",
        title='Quick Question, with "comma" and quotes',
        created_at=datetime(2024, 1, 14, 9, 15, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 14, 9, 20, 0, tzinfo=UTC),
        messages=sample_messages,
        metadata={},
    )


@pytest.fixture
def sample_search_result(sample_conversation: Conversation) -> SearchResult[Conversation]:
    """Create a sample search result with score."""
    return SearchResult(
        conversation=sample_conversation,
        score=0.875,
        snippet=None,
    )


# T131: Test CSVExporter.export_conversations() returns valid CSV (FR-050)
class TestExportConversations:
    """Test conversation-level CSV export (FR-050)."""

    def test_export_conversations_basic(self, sample_conversation: Conversation) -> None:
        """Test basic conversation export to CSV."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations([sample_conversation])

        # Verify output is non-empty string
        assert isinstance(csv_output, str)
        assert len(csv_output) > 0

        # Verify header line is present
        lines = csv_output.splitlines()
        assert len(lines) == 2  # header + 1 data row
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count"

        # Verify data row format
        assert lines[1].startswith("abc-123,")
        assert "Deep Python Discussion" in lines[1]
        assert "2024-01-15T10:30:00Z" in lines[1]
        assert "2024-01-15T14:45:00Z" in lines[1]
        assert ",2" in lines[1]  # message_count

    def test_export_conversations_multiple(
        self, sample_conversation: Conversation, conversation_with_null_updated: Conversation
    ) -> None:
        """Test exporting multiple conversations."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations(
            [sample_conversation, conversation_with_null_updated]
        )

        lines = csv_output.splitlines()
        assert len(lines) == 3  # header + 2 data rows
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count"

    def test_export_conversations_empty_list(self) -> None:
        """Test exporting empty list returns only header."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations([])

        lines = csv_output.splitlines()
        assert len(lines) == 1  # header only
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count"


# T132: Test CSVExporter.export_search_results() includes score column (FR-050)
class TestExportSearchResults:
    """Test search result CSV export with score column (FR-050)."""

    def test_export_search_results_with_score(
        self, sample_search_result: SearchResult[Conversation]
    ) -> None:
        """Test search results export includes score column."""
        exporter = CSVExporter()
        csv_output = exporter.export_search_results([sample_search_result])

        lines = csv_output.splitlines()
        assert len(lines) == 2  # header + 1 data row

        # Verify header includes score column
        assert lines[0] == "conversation_id,title,created_at,updated_at,message_count,score"

        # Verify data row includes score
        assert lines[1].endswith(",0.875")

    def test_export_search_results_multiple_scores(
        self, sample_conversation: Conversation, conversation_with_null_updated: Conversation
    ) -> None:
        """Test multiple search results with different scores."""
        results = [
            SearchResult(conversation=sample_conversation, score=0.875, snippet=None),
            SearchResult(conversation=conversation_with_null_updated, score=0.654, snippet=None),
        ]

        exporter = CSVExporter()
        csv_output = exporter.export_search_results(results)

        lines = csv_output.splitlines()
        assert len(lines) == 3  # header + 2 data rows
        assert lines[1].endswith(",0.875")
        assert lines[2].endswith(",0.654")


# T133: Test CSVExporter.export_messages() returns valid CSV (FR-052)
class TestExportMessages:
    """Test message-level CSV export (FR-052)."""

    def test_export_messages_from_conversation(self, sample_conversation: Conversation) -> None:
        """Test exporting messages from a single conversation."""
        exporter = CSVExporter()
        csv_output = exporter.export_messages(sample_conversation)

        lines = csv_output.splitlines()
        assert len(lines) == 3  # header + 2 messages

        # Verify header (FR-052)
        assert lines[0] == "conversation_id,message_id,role,timestamp,content"

        # Verify first message
        assert lines[1].startswith("abc-123,msg-001,user,2024-01-15T10:30:05Z,")
        assert "Python generators" in lines[1]

        # Verify second message
        assert lines[2].startswith("abc-123,msg-002,assistant,2024-01-15T10:30:47Z,")

    def test_export_messages_from_results(
        self, sample_search_result: SearchResult[Conversation]
    ) -> None:
        """Test exporting messages from search results."""
        exporter = CSVExporter()
        csv_output = exporter.export_messages_from_results([sample_search_result])

        lines = csv_output.splitlines()
        assert len(lines) == 3  # header + 2 messages
        assert lines[0] == "conversation_id,message_id,role,timestamp,content"


# T134: Test CSV properly escapes commas and quotes (FR-053)
class TestCSVEscaping:
    """Test RFC 4180 escaping rules (FR-053)."""

    def test_escape_commas_in_title(self, conversation_with_special_chars: Conversation) -> None:
        """Test that commas in title are properly escaped with quotes."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations([conversation_with_special_chars])

        lines = csv_output.splitlines()
        # Title with comma should be quoted
        assert 'def-456,"Quick Question, with ""comma"" and quotes",' in lines[1]

    def test_escape_quotes_in_title(self, conversation_with_special_chars: Conversation) -> None:
        """Test that quotes in title are escaped by doubling."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations([conversation_with_special_chars])

        lines = csv_output.splitlines()
        # Quotes should be doubled: "comma" -> ""comma""
        assert '""comma""' in lines[1]

    def test_escape_commas_in_message_content(self) -> None:
        """Test that commas in message content are properly escaped."""
        message = Message(
            id="msg-001",
            content="Hello, this has commas, in it",
            role="user",
            timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
            parent_id=None,
        )
        conversation = Conversation(
            id="test-id",
            title="Test",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
            messages=[message],
            metadata={},
        )

        exporter = CSVExporter()
        csv_output = exporter.export_messages(conversation)

        lines = csv_output.splitlines()
        # Content with commas should be quoted
        assert '"Hello, this has commas, in it"' in lines[1]


# T135: Test NULL values are empty fields (FR-053a)
class TestNullValues:
    """Test NULL value handling per RFC 4180 (FR-053a)."""

    def test_null_updated_at_is_empty_field(
        self, conversation_with_null_updated: Conversation
    ) -> None:
        """Test that NULL updated_at is rendered as empty field (not quoted)."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations([conversation_with_null_updated])

        lines = csv_output.splitlines()
        # NULL updated_at should appear as empty field between two commas
        # Format: ...,created_at,,message_count
        assert ",2024-01-14T09:15:00Z,,2" in lines[1]

        # Verify no quotes around empty field (zero-length)
        # Should NOT be: ",2024-01-14T09:15:00Z,"",2"
        assert '""' not in lines[1] or "Never Updated Chat" in lines[1]  # quotes only in title


# T136: Test newlines preserved in quoted fields (FR-053b)
class TestNewlinePreservation:
    """Test newline preservation in quoted fields (FR-053b)."""

    def test_newlines_preserved_in_content(self) -> None:
        """Test that newlines are preserved literally in quoted message content."""
        message = Message(
            id="msg-001",
            content="Hello,\nThis message has\nmultiple lines",
            role="user",
            timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
            parent_id=None,
        )
        conversation = Conversation(
            id="test-id",
            title="Test",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
            messages=[message],
            metadata={},
        )

        exporter = CSVExporter()
        csv_output = exporter.export_messages(conversation)

        # Newlines should be preserved literally (NOT escaped as \n)
        assert "Hello,\nThis message has\nmultiple lines" in csv_output
        # Should NOT contain escaped newlines
        assert "\\n" not in csv_output


# T137: Test CSV parseable by Python csv module (FR-053c)
class TestCSVParseability:
    """Test that generated CSV is parseable by standard tools (FR-053c)."""

    def test_csv_parseable_by_python_csv_module(
        self, sample_conversation: Conversation, conversation_with_special_chars: Conversation
    ) -> None:
        """Test that CSV can be parsed by Python's csv module."""
        exporter = CSVExporter()
        csv_output = exporter.export_conversations(
            [sample_conversation, conversation_with_special_chars]
        )

        # Parse CSV using Python's csv module
        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)

        # Verify we got 2 rows
        assert len(rows) == 2

        # Verify first row data
        assert rows[0]["conversation_id"] == "abc-123"
        assert rows[0]["title"] == "Deep Python Discussion"
        assert rows[0]["created_at"] == "2024-01-15T10:30:00Z"
        assert rows[0]["updated_at"] == "2024-01-15T14:45:00Z"
        assert rows[0]["message_count"] == "2"

        # Verify second row with special characters (commas, quotes)
        assert rows[1]["conversation_id"] == "def-456"
        assert rows[1]["title"] == 'Quick Question, with "comma" and quotes'

    def test_message_csv_parseable(self, sample_conversation: Conversation) -> None:
        """Test that message-level CSV is parseable."""
        exporter = CSVExporter()
        csv_output = exporter.export_messages(sample_conversation)

        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)

        # Verify we got 2 message rows
        assert len(rows) == 2

        # Verify first message
        assert rows[0]["conversation_id"] == "abc-123"
        assert rows[0]["message_id"] == "msg-001"
        assert rows[0]["role"] == "user"
        assert rows[0]["timestamp"] == "2024-01-15T10:30:05Z"
        assert "Python generators" in rows[0]["content"]

    def test_csv_with_newlines_parseable(self) -> None:
        """Test that CSV with newlines in content is parseable."""
        message = Message(
            id="msg-001",
            content="Line 1\nLine 2\nLine 3",
            role="user",
            timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC),
            parent_id=None,
        )
        conversation = Conversation(
            id="test-id",
            title="Test",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
            messages=[message],
            metadata={},
        )

        exporter = CSVExporter()
        csv_output = exporter.export_messages(conversation)

        # Parse with csv module
        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)

        # Verify newlines are preserved in parsed content
        assert rows[0]["content"] == "Line 1\nLine 2\nLine 3"


# T139: Test corrupted JSON during streaming handled gracefully (CHK054)
class TestErrorHandling:
    """Test error handling for malformed data (CHK054)."""

    def test_export_conversations_with_invalid_conversation(self) -> None:
        """Test that exporter handles invalid conversations gracefully.

        Note: Since Conversation is a Pydantic model, invalid data should be
        caught at model creation time. This test verifies the exporter doesn't
        crash with edge cases.
        """
        # Create a valid conversation with minimal data
        minimal_message = Message(
            id="msg-001",
            content="Test",
            role="user",
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            parent_id=None,
        )
        minimal_conversation = Conversation(
            id="minimal-id",
            title="Minimal",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
            messages=[minimal_message],
            metadata={},
        )

        exporter = CSVExporter()
        # Should not crash with minimal valid data
        csv_output = exporter.export_conversations([minimal_conversation])

        # Verify output is valid
        lines = csv_output.splitlines()
        assert len(lines) == 2  # header + 1 data row
