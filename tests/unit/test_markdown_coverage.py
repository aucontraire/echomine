"""Unit tests for markdown.py coverage gaps.

This module targets specific uncovered lines in src/echomine/export/markdown.py
identified by Codecov coverage reports.

Coverage Targets:
    - Lines 98-115: updated_at None handling in YAML frontmatter
    - Lines 120-129: include_metadata=False path (inline metadata)
    - Lines 238: Non-dict conversation in mapping
    - Lines 272: Tool role filtering
    - Lines 326-340: Multimodal content types and unknown content types
    - Lines 382-386: updated_at None in inline metadata
    - Lines 517-543: _render_metadata_header (deprecated path)
    - Lines 555, 576: _format_timestamp None handling

Constitution Compliance:
    - Principle III: TDD - Tests cover uncovered lines
    - Principle VI: Strict typing - All type hints validated
    - Test Pyramid: Unit tests (70% of test suite)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from echomine.export.markdown import MarkdownExporter
from echomine.models.conversation import Conversation
from echomine.models.message import Message


@pytest.fixture
def sample_conversation_with_updated_at() -> Conversation:
    """Create conversation with updated_at set."""
    return Conversation(
        id="conv-with-update",
        title="Updated Conversation",
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC),
        messages=[
            Message(
                id="msg-001",
                role="user",
                content="Test message",
                timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
                parent_id=None,
            )
        ],
    )


@pytest.fixture
def sample_conversation_without_updated_at() -> Conversation:
    """Create conversation without updated_at (None)."""
    return Conversation(
        id="conv-no-update",
        title="Never Updated Conversation",
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=None,  # Target: Line 103 branch
        messages=[
            Message(
                id="msg-001",
                role="user",
                content="Test message",
                timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
                parent_id=None,
            )
        ],
    )


@pytest.mark.unit
class TestMarkdownUpdatedAtHandling:
    """Test updated_at None handling in markdown export."""

    def test_export_conversation_from_model_without_updated_at(
        self, sample_conversation_without_updated_at: Conversation
    ) -> None:
        """Test YAML frontmatter when updated_at is None.

        Coverage Target: Lines 103-107 (updated_at conditional)
        Validates: FR-031 updated_at field is omitted when None
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation_from_model(
            sample_conversation_without_updated_at,
            include_metadata=True,
            include_message_ids=True,
        )

        # Assert: Extract frontmatter
        lines = markdown.split("\n")
        assert lines[0] == "---"

        # Find closing frontmatter delimiter
        closing_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_idx = i
                break

        assert closing_idx is not None, "Frontmatter should have closing delimiter"

        frontmatter = "\n".join(lines[1:closing_idx])

        # Assert: updated_at field is NOT present when None
        assert "updated_at:" not in frontmatter, (
            "updated_at field should be omitted when None (cleaner than 'updated_at: null')"
        )

        # Assert: Other required fields are present
        assert "id: conv-no-update" in frontmatter
        assert "title: Never Updated Conversation" in frontmatter
        assert "created_at:" in frontmatter
        assert "message_count: 1" in frontmatter

    def test_export_conversation_from_model_with_updated_at(
        self, sample_conversation_with_updated_at: Conversation
    ) -> None:
        """Test YAML frontmatter when updated_at is set.

        Coverage Target: Lines 104-106 (updated_at present branch)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation_from_model(
            sample_conversation_with_updated_at,
            include_metadata=True,
            include_message_ids=True,
        )

        # Assert: Extract frontmatter
        lines = markdown.split("\n")
        closing_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_idx = i
                break

        assert closing_idx is not None
        frontmatter = "\n".join(lines[1:closing_idx])

        # Assert: updated_at field IS present when not None
        assert "updated_at: 2024-01-15T14:30:00Z" in frontmatter


@pytest.mark.unit
class TestMarkdownIncludeMetadataFalse:
    """Test include_metadata=False path for inline metadata."""

    def test_export_conversation_from_model_no_metadata(
        self, sample_conversation_without_updated_at: Conversation
    ) -> None:
        """Test inline metadata when include_metadata=False and updated_at=None.

        Coverage Target: Lines 119-129 (inline metadata with updated_at=None)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation_from_model(
            sample_conversation_without_updated_at,
            include_metadata=False,
            include_message_ids=True,
        )

        # Assert: No YAML frontmatter
        assert not markdown.startswith("---\n"), "Should not have YAML frontmatter"

        # Assert: Inline metadata present
        assert "# Never Updated Conversation" in markdown
        assert "Created: 2024-01-15T10:30:00+00:00" in markdown
        assert "Messages: 1 message" in markdown

        # Assert: Updated line is NOT present (Lines 121-124)
        assert "Updated:" not in markdown, "Should not have Updated line when updated_at is None"

    def test_export_conversation_from_model_no_metadata_with_updated_at(
        self, sample_conversation_with_updated_at: Conversation
    ) -> None:
        """Test inline metadata when include_metadata=False and updated_at is set.

        Coverage Target: Lines 121-124 (inline metadata with updated_at present)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation_from_model(
            sample_conversation_with_updated_at,
            include_metadata=False,
            include_message_ids=True,
        )

        # Assert: Inline metadata with Updated line
        assert "Created: 2024-01-15T10:30:00+00:00" in markdown
        assert "Updated: 2024-01-15T14:30:00+00:00" in markdown
        assert "Messages: 1 message" in markdown


@pytest.mark.unit
class TestMarkdownExportEdgeCases:
    """Test edge cases in markdown export."""

    def test_export_conversation_non_dict_in_mapping(self, tmp_path: Path) -> None:
        """Test handling of non-dict conversation in mapping.

        Coverage Target: Line 238 (non-dict conversation skip)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Create export with non-dict item in conversations list
        export_data = [
            "not-a-dict",  # This should be skipped
            {
                "id": "conv-001",
                "title": "Valid Conversation",
                "create_time": 1705314600.0,
                "update_time": None,
                "mapping": {
                    "msg-1": {
                        "message": {
                            "id": "msg-1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                            "create_time": 1705314600.0,
                            "metadata": {},
                        }
                    }
                },
            },
        ]

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump(export_data, f)

        # Act - should find the valid conversation and skip non-dict
        markdown = exporter.export_conversation(export_file, "conv-001")

        # Assert: Valid conversation was found and exported
        assert "# Valid Conversation" in markdown
        assert "Hello" in markdown

    def test_extract_messages_tool_role_filtering(self, tmp_path: Path) -> None:
        """Test that tool role messages are filtered out.

        Coverage Target: Line 272 (tool role filtering)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Create export with tool role message
        conversation = {
            "id": "conv-tool-test",
            "title": "Conversation with Tool Messages",
            "create_time": 1705314600.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["User message"]},
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                },
                "msg-2": {
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "tool"},  # Tool role - should be filtered
                        "content": {"content_type": "text", "parts": ["Tool output"]},
                        "create_time": 1705314610.0,
                        "metadata": {},
                    }
                },
                "msg-3": {
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Assistant response"]},
                        "create_time": 1705314620.0,
                        "metadata": {},
                    }
                },
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act
        markdown = exporter.export_conversation(export_file, "conv-tool-test")

        # Assert: User and assistant messages present
        assert "User message" in markdown
        assert "Assistant response" in markdown

        # Assert: Tool message NOT present
        assert "Tool output" not in markdown

    def test_extract_content_multimodal_with_dict_part(self, tmp_path: Path) -> None:
        """Test multimodal content extraction with dict parts.

        Coverage Target: Lines 326-333 (multimodal dict part handling)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Create conversation with multimodal content including image
        conversation = {
            "id": "conv-multimodal",
            "title": "Multimodal Content",
            "create_time": 1705314600.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "multimodal_text",
                            "parts": [
                                "Here's an image: ",
                                {
                                    "content_type": "image_asset_pointer",
                                    "asset_pointer": "file-service://abc123-456def",
                                },
                                " What do you see?",
                            ],
                        },
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                }
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act
        markdown = exporter.export_conversation(export_file, "conv-multimodal")

        # Assert: Text parts are present
        assert "Here's an image:" in markdown
        assert "What do you see?" in markdown

        # Assert: Image reference is included
        assert "![Image](abc123-456def-sanitized.png)" in markdown

    def test_extract_content_code_type(self, tmp_path: Path) -> None:
        """Test code content type extraction.

        Coverage Target: Lines 336-337 (code content type)
        """
        # Arrange
        exporter = MarkdownExporter()

        conversation = {
            "id": "conv-code",
            "title": "Code Content",
            "create_time": 1705314600.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "code",
                            "text": "def hello():\n    print('Hello, World!')",
                        },
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                }
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act
        markdown = exporter.export_conversation(export_file, "conv-code")

        # Assert: Code content is present
        assert "def hello():" in markdown
        assert "print('Hello, World!')" in markdown

    def test_extract_content_unknown_type(self, tmp_path: Path) -> None:
        """Test unknown content type returns empty string.

        Coverage Target: Line 340 (unknown content type default)
        """
        # Arrange
        exporter = MarkdownExporter()

        conversation = {
            "id": "conv-unknown",
            "title": "Unknown Content Type",
            "create_time": 1705314600.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "future_unknown_type",
                            "data": "some data",
                        },
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                },
                "msg-2": {
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Valid response"]},
                        "create_time": 1705314610.0,
                        "metadata": {},
                    }
                },
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act
        markdown = exporter.export_conversation(export_file, "conv-unknown")

        # Assert: Valid message is present
        assert "Valid response" in markdown

        # Unknown content type produces empty content (message may still appear with header)
        # But the content should be minimal/empty
        lines = markdown.split("\n")
        # Check that we don't have "some data" in output
        assert "some data" not in markdown


@pytest.mark.unit
class TestMarkdownRenderInlineMetadata:
    """Test _render_markdown inline metadata path."""

    def test_render_markdown_inline_metadata_with_updated_at_none(self, tmp_path: Path) -> None:
        """Test inline metadata rendering when update_time is None.

        Coverage Target: Lines 382-386 (updated_at None in inline metadata)
        """
        # Arrange
        exporter = MarkdownExporter()

        conversation = {
            "id": "conv-no-update",
            "title": "Never Updated",
            "create_time": 1705314600.0,
            "update_time": None,  # Target line 382 condition
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Hello"]},
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                }
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act - use include_metadata=False to trigger inline metadata path
        markdown = exporter.export_conversation(
            export_file, "conv-no-update", include_metadata=False
        )

        # Assert: No Updated line when update_time is None
        assert "Created: 2024-01-15T10:30:00+00:00" in markdown
        assert "Updated:" not in markdown  # Line 382-384 branch not taken
        assert "Messages: 1 message" in markdown


@pytest.mark.unit
class TestMarkdownTimestampFormatting:
    """Test timestamp formatting helper methods."""

    def test_format_timestamp_with_none(self) -> None:
        """Test _format_timestamp with None returns 'N/A'.

        Coverage Target: Lines 554-555 (None timestamp handling)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        result = exporter._format_timestamp(None)

        # Assert
        assert result == "N/A"

    def test_format_timestamp_iso8601_z_with_none(self) -> None:
        """Test _format_timestamp_iso8601_z with None returns 'N/A'.

        Coverage Target: Lines 575-576 (None timestamp handling)
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act
        result = exporter._format_timestamp_iso8601_z(None)

        # Assert
        assert result == "N/A"

    def test_format_timestamp_iso8601_z_with_valid_timestamp(self) -> None:
        """Test _format_timestamp_iso8601_z with valid timestamp."""
        # Arrange
        exporter = MarkdownExporter()
        # Use a known timestamp and verify format rather than exact value
        timestamp = 1705320600.0

        # Act
        result = exporter._format_timestamp_iso8601_z(timestamp)

        # Assert: Verify ISO 8601 format with Z suffix
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result), (
            f"Result should be in ISO 8601 format with Z suffix, got: {result}"
        )
        # Also verify it contains the date portion
        assert "2024-01-15" in result


@pytest.mark.unit
class TestMarkdownMessageIdsDisabled:
    """Test message header formatting when include_message_ids=False."""

    def test_export_conversation_from_model_no_message_ids_shows_emojis(
        self, sample_conversation_with_updated_at: Conversation
    ) -> None:
        """Test emoji headers when include_message_ids=False.

        Coverage Target: Lines 142-143 (emoji header fallback)
        Validates: Backward compatibility - emojis shown when IDs disabled
        """
        # Arrange
        exporter = MarkdownExporter()

        # Act - disable message IDs
        markdown = exporter.export_conversation_from_model(
            sample_conversation_with_updated_at,
            include_metadata=True,
            include_message_ids=False,  # Target line 142-143
        )

        # Assert: Message header has emoji format (not ID format)
        assert "👤 User ·" in markdown or "🤖 Assistant ·" in markdown

        # Assert: Message IDs NOT in headers
        assert "msg-001" not in markdown or "`msg-001`" not in markdown

    def test_render_markdown_no_message_ids_shows_emojis(self, tmp_path: Path) -> None:
        """Test emoji headers in deprecated export_conversation method.

        Coverage Target: Lines 142-143, 405-406 (emoji header fallback)
        """
        # Arrange
        exporter = MarkdownExporter()

        conversation = {
            "id": "conv-emojis",
            "title": "Emoji Test",
            "create_time": 1705314600.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["User message"]},
                        "create_time": 1705314600.0,
                        "metadata": {},
                    }
                },
                "msg-2": {
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Assistant response"]},
                        "create_time": 1705314610.0,
                        "metadata": {},
                    }
                },
            },
        }

        export_file = tmp_path / "export.json"
        with export_file.open("w") as f:
            json.dump([conversation], f)

        # Act
        markdown = exporter.export_conversation(
            export_file, "conv-emojis", include_message_ids=False
        )

        # Assert: Emoji headers present
        assert "👤 User ·" in markdown
        assert "🤖 Assistant ·" in markdown

        # Assert: Message IDs NOT in headers
        assert "`msg-1`" not in markdown
        assert "`msg-2`" not in markdown
