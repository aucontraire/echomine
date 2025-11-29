"""Unit tests for markdown export metadata header functionality.

Task: US3-AS3 - Markdown includes conversation metadata
Phase: RED (tests designed to FAIL initially)

This module tests that the MarkdownExporter includes a proper metadata header
section at the beginning of the exported markdown file per FR-014.

FR-014 Requirements:
- System MUST include conversation metadata in exported files
- Metadata includes: title, created date, updated date (if present), message count

Test Pyramid Classification: Unit (70% of test suite)
These tests validate MarkdownExporter behavior in isolation.

Expected Failure Reason:
- MarkdownExporter._render_markdown() does NOT currently include metadata header
- Only renders message-level headers (role + timestamp)
- Missing conversation-level metadata at top of export
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from echomine.export.markdown import MarkdownExporter


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def conversation_with_updated_at(tmp_path: Path) -> Path:
    """Create export with conversation that has both created_at and updated_at.

    This represents a conversation that has been modified after creation.
    """
    conversation = {
        "id": "conv-updated-001",
        "title": "Python Best Practices",
        "create_time": 1710000000.0,  # 2024-03-09 16:00:00 UTC
        "update_time": 1710086400.0,  # 2024-03-10 16:00:00 UTC (24 hours later)
        "mapping": {
            "msg-1": {
                "id": "msg-1",
                "message": {
                    "id": "msg-1",
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "text",
                        "parts": ["What are Python best practices?"],
                    },
                    "create_time": 1710000000.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": None,
                "children": ["msg-2"],
            },
            "msg-2": {
                "id": "msg-2",
                "message": {
                    "id": "msg-2",
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Follow PEP 8, use type hints, write tests."],
                    },
                    "create_time": 1710000010.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": "msg-1",
                "children": [],
            },
        },
        "moderation_results": [],
        "current_node": "msg-2",
    }

    export_file = tmp_path / "conversation_with_updated.json"
    with export_file.open("w") as f:
        json.dump([conversation], f)

    return export_file


@pytest.fixture
def conversation_without_updated_at(tmp_path: Path) -> Path:
    """Create export with conversation that has only created_at (no updates).

    This represents a conversation that was never modified after creation.
    """
    conversation = {
        "id": "conv-no-update-001",
        "title": "Quick Question About Async",
        "create_time": 1710200000.0,  # 2024-03-11 23:33:20 UTC
        "update_time": None,  # Never updated
        "mapping": {
            "msg-quick-1": {
                "id": "msg-quick-1",
                "message": {
                    "id": "msg-quick-1",
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Is async worth learning?"],
                    },
                    "create_time": 1710200000.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": None,
                "children": [],
            },
        },
        "moderation_results": [],
        "current_node": "msg-quick-1",
    }

    export_file = tmp_path / "conversation_without_updated.json"
    with export_file.open("w") as f:
        json.dump([conversation], f)

    return export_file


@pytest.fixture
def conversation_with_many_messages(tmp_path: Path) -> Path:
    """Create export with conversation containing multiple messages.

    Used to test that message count is correctly displayed in metadata.
    """
    # Generate 15 messages for message count validation
    mapping = {}
    for i in range(15):
        mapping[f"msg-{i}"] = {
            "id": f"msg-{i}",
            "message": {
                "id": f"msg-{i}",
                "author": {"role": "user" if i % 2 == 0 else "assistant"},
                "content": {
                    "content_type": "text",
                    "parts": [f"Message content {i}"],
                },
                "create_time": 1710000000.0 + (i * 60),  # 1 minute apart
                "update_time": None,
                "metadata": {},
            },
            "parent": f"msg-{i - 1}" if i > 0 else None,
            "children": [f"msg-{i + 1}"] if i < 14 else [],
        }

    conversation = {
        "id": "conv-many-msgs-001",
        "title": "Long Conversation Thread",
        "create_time": 1710000000.0,
        "update_time": 1710000840.0,  # 14 minutes later (last message)
        "mapping": mapping,
        "moderation_results": [],
        "current_node": "msg-14",
    }

    export_file = tmp_path / "conversation_with_many_messages.json"
    with export_file.open("w") as f:
        json.dump([conversation], f)

    return export_file


# =============================================================================
# Unit Tests - Metadata Header Presence (RED Phase)
# =============================================================================


@pytest.mark.unit
class TestMarkdownMetadataHeaderPresence:
    """Test that markdown exports include a metadata header section.

    FR-014: System MUST include conversation metadata in exported files.

    These tests validate that the MarkdownExporter produces markdown output
    with a metadata header BEFORE the message content.

    Expected to FAIL: MarkdownExporter currently does NOT include metadata header.
    """

    def test_markdown_export_includes_metadata_header_section(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that exported markdown contains a distinct metadata header section.

        Validates:
        - FR-014: Metadata included in exported files
        - Metadata appears BEFORE message content
        - Clear visual separation from message content

        Expected to FAIL: No metadata header currently rendered.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Metadata header exists
        assert "# " in markdown or "## " in markdown, (
            "Markdown should contain headers (metadata or messages)"
        )

        # Split into lines for analysis
        lines = markdown.split("\n")

        # Find first occurrence of message header (## 👤 User or ## 🤖 Assistant)
        first_message_header_idx = None
        for i, line in enumerate(lines):
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_header_idx = i
                break

        assert first_message_header_idx is not None, (
            "Markdown should contain message headers"
        )

        # Assert: Metadata should appear BEFORE first message header
        # Look for metadata keywords in lines BEFORE first message
        metadata_section = "\n".join(lines[:first_message_header_idx])

        # Metadata header should contain conversation-level info
        # This will FAIL because metadata header doesn't exist yet
        assert any(
            keyword in metadata_section
            for keyword in ["Title:", "Created:", "Updated:", "Messages:"]
        ), (
            "Metadata header section missing. Expected conversation metadata "
            "BEFORE first message header. Got metadata section:\n"
            f"{metadata_section[:200]}"
        )

    def test_markdown_export_includes_title_in_metadata(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that exported markdown includes conversation title in metadata.

        Validates:
        - FR-014: Title included in metadata
        - Title appears prominently (h1 or labeled field)
        - Exact title text preserved

        Expected to FAIL: Title not in current export output.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"
        expected_title = "Python Best Practices"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Title appears in markdown
        # This will FAIL - title is NOT currently in export
        assert expected_title in markdown, (
            f"Exported markdown should include conversation title '{expected_title}'. "
            f"Title not found in export. First 300 chars:\n{markdown[:300]}"
        )

        # Assert: Title appears before first message (in metadata section)
        lines = markdown.split("\n")
        title_line_idx = None
        first_message_idx = None

        for i, line in enumerate(lines):
            if expected_title in line and title_line_idx is None:
                title_line_idx = i
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_idx = i
                break

        assert title_line_idx is not None, "Title should be present in markdown"
        assert first_message_idx is not None, "Messages should be present"
        assert title_line_idx < first_message_idx, (
            f"Title (line {title_line_idx}) should appear BEFORE first message "
            f"(line {first_message_idx}) in metadata header"
        )

    def test_markdown_export_includes_created_date_in_metadata(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that exported markdown includes created_at date in metadata.

        Validates:
        - FR-014: Created date included in metadata
        - Date formatted readably (ISO 8601)
        - Labeled clearly (e.g., "Created:" or "Created At:")

        Expected to FAIL: Created date not in metadata section.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"
        # Expected created_at: 1710000000.0 = 2024-03-09 16:00:00 UTC

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Created date appears in markdown
        # Look for ISO 8601 format or readable date
        assert any(
            date_marker in markdown
            for date_marker in ["2024-03-09", "Created:", "Created At:"]
        ), (
            "Exported markdown should include created_at date in metadata. "
            f"Date markers not found. First 300 chars:\n{markdown[:300]}"
        )

        # Assert: Created date appears before first message
        lines = markdown.split("\n")
        created_line_idx = None
        first_message_idx = None

        for i, line in enumerate(lines):
            if "Created" in line or "2024-03-09" in line:
                if created_line_idx is None:
                    created_line_idx = i
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_idx = i
                break

        # This assertion will FAIL if created date is in message timestamps only
        if created_line_idx is not None and first_message_idx is not None:
            assert created_line_idx < first_message_idx, (
                f"Created date (line {created_line_idx}) should appear in metadata "
                f"header BEFORE first message (line {first_message_idx})"
            )

    def test_markdown_export_includes_updated_date_when_present(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that updated_at date is included when conversation was updated.

        Validates:
        - FR-014: Updated date included when present
        - Distinguished from created_at (different timestamps)
        - Labeled clearly (e.g., "Updated:" or "Last Updated:")

        Expected to FAIL: Updated date not in metadata section.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"
        # Expected updated_at: 1710086400.0 = 2024-03-10 16:00:00 UTC (24h later)

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Updated date appears in markdown
        assert any(
            update_marker in markdown
            for update_marker in ["2024-03-10", "Updated:", "Last Updated:"]
        ), (
            "Exported markdown should include updated_at date in metadata. "
            f"Update markers not found. First 300 chars:\n{markdown[:300]}"
        )

        # Assert: Both created and updated dates present (different values)
        has_created = "2024-03-09" in markdown
        has_updated = "2024-03-10" in markdown

        assert has_created, "Should show created date (2024-03-09)"
        assert has_updated, "Should show updated date (2024-03-10)"

    def test_markdown_export_omits_updated_date_when_null(
        self, conversation_without_updated_at: Path
    ) -> None:
        """Test that updated_at is omitted or labeled when null.

        Validates:
        - FR-014: Updated date handling when not present
        - Either omit the field OR show "Never updated" / "N/A"
        - Created date still shown

        Expected to FAIL: Metadata section doesn't exist yet.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-no-update-001"
        # This conversation has update_time: None

        # Act
        markdown = exporter.export_conversation(
            conversation_without_updated_at, conversation_id
        )

        # Assert: Created date is present
        assert "2024-03-11" in markdown or "Created" in markdown, (
            "Should show created date even when updated_at is null"
        )

        # Assert: Updated date handling
        # Either: (1) "Updated:" field is absent, OR
        #         (2) "Updated:" shows "Never" / "N/A" / similar
        lines = markdown.split("\n")
        metadata_lines = []

        for line in lines:
            if "👤" in line or "🤖" in line:
                break  # Stop at first message
            metadata_lines.append(line)

        metadata_text = "\n".join(metadata_lines)

        # Check if "Updated:" appears in metadata
        has_updated_field = "Updated" in metadata_text

        if has_updated_field:
            # If field is present, it should indicate null/never
            assert any(
                indicator in metadata_text
                for indicator in ["Never", "N/A", "None", "not updated"]
            ), (
                "When updated_at is null, metadata should indicate this clearly. "
                f"Metadata section:\n{metadata_text}"
            )

    def test_markdown_export_includes_message_count_in_metadata(
        self, conversation_with_many_messages: Path
    ) -> None:
        """Test that message count is included in metadata header.

        Validates:
        - FR-014: Message count included in metadata
        - Count is accurate (15 messages in fixture)
        - Labeled clearly (e.g., "Messages:" or "Message Count:")

        Expected to FAIL: Message count not in metadata section.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-many-msgs-001"
        expected_count = 15

        # Act
        markdown = exporter.export_conversation(
            conversation_with_many_messages, conversation_id
        )

        # Assert: Message count appears in markdown
        # Look for patterns like "15 messages", "Messages: 15", "Message Count: 15"
        assert any(
            count_pattern in markdown
            for count_pattern in [
                f"{expected_count} message",
                f"Messages: {expected_count}",
                f"Message Count: {expected_count}",
                f"Count: {expected_count}",
            ]
        ), (
            f"Metadata should include message count ({expected_count}). "
            f"Count not found. First 400 chars:\n{markdown[:400]}"
        )


# =============================================================================
# Unit Tests - Metadata Header Format (RED Phase)
# =============================================================================


@pytest.mark.unit
class TestMarkdownMetadataHeaderFormat:
    """Test the format and structure of the metadata header.

    These tests validate the markdown formatting of the metadata section,
    ensuring it's visually distinct and properly formatted.

    Expected to FAIL: Metadata header doesn't exist yet.
    """

    def test_metadata_header_uses_markdown_heading(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that metadata uses proper markdown heading syntax.

        Validates:
        - Metadata header uses # (h1) or ## (h2) syntax
        - Clear visual hierarchy (metadata header at top level)
        - Consistent heading level throughout metadata

        Expected to FAIL: No metadata heading exists.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: First non-empty line should be metadata header
        lines = [line for line in markdown.split("\n") if line.strip()]

        assert len(lines) > 0, "Markdown should not be empty"

        first_line = lines[0]

        # First line should be a heading (title or "Conversation Metadata")
        assert first_line.startswith("#"), (
            f"First line should be a markdown heading (metadata header). "
            f"Got: {first_line}"
        )

        # Should be h1 (#) or h2 (##) level
        assert first_line.startswith("# ") or first_line.startswith("## "), (
            f"Metadata header should use h1 (#) or h2 (##). Got: {first_line}"
        )

    def test_metadata_fields_use_consistent_label_format(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that metadata fields use consistent labeling.

        Validates:
        - Fields use "Label: Value" format OR markdown list syntax
        - Consistent formatting across all fields
        - Readable and scannable layout

        Expected to FAIL: Metadata fields don't exist.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Metadata uses consistent label format
        # Extract metadata section (before first message)
        lines = markdown.split("\n")
        metadata_lines = []

        for line in lines:
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                break
            metadata_lines.append(line)

        metadata_text = "\n".join(metadata_lines)

        # Check for consistent patterns:
        # Option 1: "Label: Value" format
        # Option 2: Markdown list with "- Label: Value"
        has_label_colon_format = (
            "Title:" in metadata_text or
            "Created:" in metadata_text or
            "Messages:" in metadata_text
        )

        has_markdown_list_format = any(
            line.strip().startswith("- ") for line in metadata_lines
        )

        assert has_label_colon_format or has_markdown_list_format, (
            "Metadata should use consistent label format "
            "(either 'Label: Value' or markdown list). "
            f"Metadata section:\n{metadata_text}"
        )

    def test_metadata_header_separated_from_messages(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that metadata header is visually separated from messages.

        Validates:
        - Blank line OR horizontal rule between metadata and first message
        - Clear visual boundary for readability
        - Metadata doesn't blend with message content

        Expected to FAIL: No metadata section to separate.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: Find metadata section and first message
        lines = markdown.split("\n")

        first_message_idx = None
        for i, line in enumerate(lines):
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                first_message_idx = i
                break

        assert first_message_idx is not None, "Should have message content"
        assert first_message_idx > 0, "Messages should not be first line"

        # Check for separator before first message
        # Should have at least one blank line OR horizontal rule (---)
        lines_before_message = lines[:first_message_idx]

        has_blank_separator = any(
            line.strip() == "" for line in lines_before_message[-3:]
        )
        has_hr_separator = any(
            line.strip() == "---" for line in lines_before_message
        )

        assert has_blank_separator or has_hr_separator, (
            "Metadata header should be separated from messages by blank line "
            "or horizontal rule. Lines before first message:\n"
            f"{lines_before_message[-5:]}"
        )


# =============================================================================
# Unit Tests - Metadata Values Accuracy (RED Phase)
# =============================================================================


@pytest.mark.unit
class TestMarkdownMetadataValuesAccuracy:
    """Test that metadata values are accurate and properly formatted.

    These tests validate the correctness of metadata field values,
    ensuring dates are formatted properly and counts are accurate.

    Expected to FAIL: Metadata values don't exist in current export.
    """

    def test_metadata_created_date_uses_iso8601_format(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that created_at date uses ISO 8601 format.

        Validates:
        - Date format: YYYY-MM-DDTHH:MM:SS+00:00 (or similar)
        - Timezone included (UTC preferred)
        - Machine-readable and human-readable

        Expected to FAIL: Created date not in metadata.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: ISO 8601 format present
        # Expected: 1710000000.0 = 2024-03-09T16:00:00+00:00
        assert "2024-03-09T16:00:00" in markdown, (
            "Created date should use ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            f"Not found in export. First 400 chars:\n{markdown[:400]}"
        )

    def test_metadata_updated_date_uses_iso8601_format(
        self, conversation_with_updated_at: Path
    ) -> None:
        """Test that updated_at date uses ISO 8601 format.

        Validates:
        - Date format: YYYY-MM-DDTHH:MM:SS+00:00
        - Same format as created_at (consistency)
        - Timezone included

        Expected to FAIL: Updated date not in metadata.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-updated-001"

        # Act
        markdown = exporter.export_conversation(
            conversation_with_updated_at, conversation_id
        )

        # Assert: ISO 8601 format for updated date
        # Expected: 1710086400.0 = 2024-03-10T16:00:00+00:00
        assert "2024-03-10T16:00:00" in markdown, (
            "Updated date should use ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            f"Not found in export. First 400 chars:\n{markdown[:400]}"
        )

    def test_metadata_message_count_matches_actual_messages(
        self, conversation_with_many_messages: Path
    ) -> None:
        """Test that message count in metadata matches actual message count.

        Validates:
        - Count is accurate (not hardcoded)
        - Counts all messages in export
        - Integer value displayed correctly

        Expected to FAIL: Message count not in metadata.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-many-msgs-001"
        expected_count = 15

        # Act
        markdown = exporter.export_conversation(
            conversation_with_many_messages, conversation_id
        )

        # Assert: Count appears and is correct
        # Count message headers in export to verify
        message_header_count = markdown.count("##")

        # At least one header for metadata + 15 for messages = 16 total
        # OR if no metadata header, exactly 15 message headers
        # This test validates metadata count matches reality

        # Look for count in metadata section
        lines = markdown.split("\n")
        metadata_section = []

        for line in lines:
            if ("👤" in line or "🤖" in line) and line.startswith("##"):
                break
            metadata_section.append(line)

        metadata_text = "\n".join(metadata_section)

        # Should find "15" associated with message count
        assert f"{expected_count}" in metadata_text, (
            f"Metadata should show message count of {expected_count}. "
            f"Metadata section:\n{metadata_text}"
        )


# =============================================================================
# Unit Tests - Edge Cases (RED Phase)
# =============================================================================


@pytest.mark.unit
class TestMarkdownMetadataEdgeCases:
    """Test edge cases for metadata header handling.

    These tests validate robustness and proper handling of unusual cases.

    Expected to FAIL: Metadata functionality doesn't exist yet.
    """

    def test_metadata_handles_unicode_in_title(
        self, tmp_path: Path
    ) -> None:
        """Test that metadata preserves Unicode characters in title.

        Validates:
        - UTF-8 encoding preservation
        - Emoji, CJK characters, accents handled correctly
        - No mojibake or encoding errors

        Expected to FAIL: Title not in metadata.
        """
        # Arrange
        conversation = {
            "id": "conv-unicode-001",
            "title": "测试会话 🚀 Python Émojis & Accénts",
            "create_time": 1710000000.0,
            "update_time": 1710086400.0,
            "mapping": {
                "msg-u1": {
                    "id": "msg-u1",
                    "message": {
                        "id": "msg-u1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Hello 世界"],
                        },
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-u1",
        }

        unicode_file = tmp_path / "unicode_conversation.json"
        with unicode_file.open("w", encoding="utf-8") as f:
            json.dump([conversation], f, ensure_ascii=False)

        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation(unicode_file, "conv-unicode-001")

        # Assert: Unicode title preserved
        expected_title = "测试会话 🚀 Python Émojis & Accénts"
        assert expected_title in markdown, (
            f"Metadata should preserve Unicode title exactly. "
            f"Expected: {expected_title}\n"
            f"Not found in: {markdown[:400]}"
        )

    def test_metadata_handles_very_long_title(
        self, tmp_path: Path
    ) -> None:
        """Test that metadata handles very long conversation titles.

        Validates:
        - Long titles don't break formatting
        - Either truncate with ellipsis OR wrap properly
        - Metadata section remains readable

        Expected to FAIL: Title not in metadata.
        """
        # Arrange
        long_title = "This is a very long conversation title that goes on and on " * 5
        long_title = long_title[:300]  # Limit to 300 chars

        conversation = {
            "id": "conv-long-title-001",
            "title": long_title,
            "create_time": 1710000000.0,
            "update_time": None,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Test"]},
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-1",
        }

        long_title_file = tmp_path / "long_title_conversation.json"
        with long_title_file.open("w") as f:
            json.dump([conversation], f)

        exporter = MarkdownExporter()

        # Act
        markdown = exporter.export_conversation(
            long_title_file, "conv-long-title-001"
        )

        # Assert: Title appears (truncated or full)
        # Either full title or truncated with "..."
        title_in_markdown = long_title[:100] in markdown or long_title in markdown

        assert title_in_markdown, (
            "Metadata should include title (full or truncated). "
            f"Title not found. First 400 chars:\n{markdown[:400]}"
        )

    def test_metadata_handles_single_message_conversation(
        self, conversation_without_updated_at: Path
    ) -> None:
        """Test metadata for conversation with only 1 message.

        Validates:
        - Message count shows "1 message" (singular)
        - Metadata still displayed correctly
        - No formatting errors with minimal content

        Expected to FAIL: Message count not in metadata.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-no-update-001"
        # This fixture has only 1 message

        # Act
        markdown = exporter.export_conversation(
            conversation_without_updated_at, conversation_id
        )

        # Assert: Shows "1 message" (singular form)
        assert any(
            singular_form in markdown
            for singular_form in ["1 message", "Messages: 1", "Message Count: 1"]
        ), (
            "Metadata should show '1 message' for single-message conversation. "
            f"Not found. First 400 chars:\n{markdown[:400]}"
        )
