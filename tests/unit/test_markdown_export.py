"""Unit tests for Phase 9 - US5 Rich Markdown Export.

Task: T086-T093 - YAML frontmatter and message IDs
Phase: RED (tests designed to FAIL initially)

This module tests the enhanced markdown export functionality with:
- YAML frontmatter with conversation metadata (FR-030, FR-031)
- ISO 8601 datetime format with Z suffix (FR-031b)
- Message IDs in headers (FR-032, FR-032a, FR-032b)
- --no-metadata flag support (FR-033)

FR Requirements:
- FR-030: Markdown exports include YAML frontmatter by default
- FR-031: Frontmatter contains: id, title, created_at, updated_at, message_count, export_date, exported_by
- FR-031b: Datetime fields use ISO 8601 with UTC 'Z' suffix (e.g., 2024-01-15T10:30:00Z)
- FR-032: Message headers include message ID in inline code format
- FR-032a: Generated IDs use format msg-{conversation_id}-{zero_padded_index}
- FR-032b: Generated IDs are deterministic/reproducible
- FR-033: --no-metadata flag disables frontmatter
- FR-035: Library API has include_metadata and include_message_ids parameters

Test Pyramid Classification: Unit (70% of test suite)
These tests validate MarkdownExporter behavior in isolation.

Expected Failure Reasons:
- MarkdownExporter does NOT currently support include_metadata parameter
- MarkdownExporter does NOT currently support include_message_ids parameter
- YAML frontmatter generation not implemented
- Message IDs not included in headers
- Message ID generation not implemented
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from echomine.export.markdown import MarkdownExporter


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_conversation_with_ids(tmp_path: Path) -> Path:
    """Create export with conversation where messages have source IDs.

    This represents the ideal case where all messages have proper IDs
    from the source export.
    """
    conversation = {
        "id": "conv-abc123",
        "title": "Python Generators Deep Dive",
        "create_time": 1705314600.0,  # 2024-01-15T10:30:00Z
        "update_time": 1705329000.0,  # 2024-01-15T14:30:00Z
        "mapping": {
            "msg-source-001": {
                "id": "msg-source-001",
                "message": {
                    "id": "msg-source-001",
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Explain Python generators please"],
                    },
                    "create_time": 1705314600.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": None,
                "children": ["msg-source-002"],
            },
            "msg-source-002": {
                "id": "msg-source-002",
                "message": {
                    "id": "msg-source-002",
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Python generators are functions that use yield..."],
                    },
                    "create_time": 1705314647.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": "msg-source-001",
                "children": [],
            },
        },
        "moderation_results": [],
        "current_node": "msg-source-002",
    }

    export_file = tmp_path / "conversation_with_ids.json"
    with export_file.open("w") as f:
        json.dump([conversation], f)

    return export_file


@pytest.fixture
def sample_conversation_without_ids(tmp_path: Path) -> Path:
    """Create export with conversation where messages LACK source IDs.

    This tests the message ID generation functionality (FR-032a, FR-032b).
    """
    conversation = {
        "id": "conv-xyz789",
        "title": "Quick Python Question",
        "create_time": 1705401000.0,  # 2024-01-16T10:30:00Z
        "update_time": None,
        "mapping": {
            "node-1": {
                "id": "node-1",
                "message": {
                    # Message object has NO "id" field - needs generation
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "text",
                        "parts": ["What is asyncio?"],
                    },
                    "create_time": 1705401000.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": None,
                "children": ["node-2"],
            },
            "node-2": {
                "id": "node-2",
                "message": {
                    # Message object has NO "id" field - needs generation
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": ["AsyncIO is Python's async/await library"],
                    },
                    "create_time": 1705401010.0,
                    "update_time": None,
                    "metadata": {},
                },
                "parent": "node-1",
                "children": [],
            },
        },
        "moderation_results": [],
        "current_node": "node-2",
    }

    export_file = tmp_path / "conversation_without_ids.json"
    with export_file.open("w") as f:
        json.dump([conversation], f)

    return export_file


# =============================================================================
# T086: Unit Test - YAML Frontmatter Included by Default
# =============================================================================


@pytest.mark.unit
class TestYAMLFrontmatterDefault:
    """Test that markdown exports include YAML frontmatter by default (FR-030).

    Expected to FAIL: MarkdownExporter does not currently generate YAML frontmatter.
    """

    def test_export_includes_yaml_frontmatter_by_default(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that exported markdown includes YAML frontmatter delimiters.

        Validates:
        - FR-030: Frontmatter included by default
        - YAML format uses triple-dash delimiters (---) at start and end
        - Frontmatter appears at very beginning of file

        Expected to FAIL: No YAML frontmatter currently generated.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Markdown starts with YAML frontmatter delimiter
        assert markdown.startswith("---\n"), (
            "Markdown export should start with YAML frontmatter delimiter '---\\n'. "
            f"Got first line: {markdown.split(chr(10))[0]!r}"
        )

        # Assert: Second occurrence of '---' closes the frontmatter
        lines = markdown.split("\n")
        delimiter_count = sum(1 for line in lines[:20] if line.strip() == "---")

        assert delimiter_count >= 2, (
            f"YAML frontmatter should have opening and closing '---' delimiters. "
            f"Found {delimiter_count} delimiters in first 20 lines"
        )

    def test_frontmatter_appears_before_content(self, sample_conversation_with_ids: Path) -> None:
        """Test that YAML frontmatter appears before conversation content.

        Validates:
        - Frontmatter is at the very start of file
        - Content (title heading, messages) appears AFTER frontmatter
        - Clear separation between metadata and content

        Expected to FAIL: No frontmatter currently exists.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Find closing frontmatter delimiter
        lines = markdown.split("\n")
        closing_delimiter_idx = None

        for i, line in enumerate(lines[1:], start=1):  # Skip first ---
            if line.strip() == "---":
                closing_delimiter_idx = i
                break

        assert closing_delimiter_idx is not None, (
            "YAML frontmatter should have closing '---' delimiter"
        )

        # Assert: Content (title or messages) appears AFTER closing delimiter
        content_after_frontmatter = "\n".join(lines[closing_delimiter_idx + 1 :])

        assert len(content_after_frontmatter.strip()) > 0, (
            "Conversation content should appear after frontmatter"
        )

        # Assert: Title heading should appear after frontmatter
        assert "# Python Generators Deep Dive" in content_after_frontmatter, (
            "Title heading should appear in content section after frontmatter"
        )


# =============================================================================
# T087: Unit Test - Frontmatter Contains All Required Fields (FR-031)
# =============================================================================


@pytest.mark.unit
class TestYAMLFrontmatterFields:
    """Test that YAML frontmatter contains all required fields (FR-031).

    Expected to FAIL: Frontmatter generation not implemented.
    """

    def test_frontmatter_contains_id_field(self, sample_conversation_with_ids: Path) -> None:
        """Test that frontmatter includes conversation ID.

        Validates:
        - FR-031: id field present
        - Field format: id: <conversation_id>
        - Exact conversation ID from source

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert f"id: {conversation_id}" in frontmatter, (
            f"Frontmatter should contain 'id: {conversation_id}'"
        )

    def test_frontmatter_contains_title_field(self, sample_conversation_with_ids: Path) -> None:
        """Test that frontmatter includes conversation title.

        Validates:
        - FR-031: title field present
        - Field format: title: <title>
        - Exact title from source

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"
        expected_title = "Python Generators Deep Dive"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert f"title: {expected_title}" in frontmatter, (
            f"Frontmatter should contain 'title: {expected_title}'"
        )

    def test_frontmatter_contains_created_at_field(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that frontmatter includes created_at timestamp.

        Validates:
        - FR-031: created_at field present
        - Field format: created_at: <datetime>

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert "created_at:" in frontmatter, "Frontmatter should contain 'created_at:' field"

    def test_frontmatter_contains_updated_at_field(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that frontmatter includes updated_at timestamp.

        Validates:
        - FR-031: updated_at field present
        - Field format: updated_at: <datetime> OR null/empty if not updated

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert "updated_at:" in frontmatter, "Frontmatter should contain 'updated_at:' field"

    def test_frontmatter_contains_message_count_field(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that frontmatter includes message count.

        Validates:
        - FR-031: message_count field present
        - Field format: message_count: <integer>
        - Accurate count (2 messages in fixture)

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert "message_count: 2" in frontmatter, (
            "Frontmatter should contain 'message_count: 2' (2 messages in fixture)"
        )

    def test_frontmatter_contains_export_date_field(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that frontmatter includes export_date timestamp.

        Validates:
        - FR-031: export_date field present
        - Field format: export_date: <datetime>
        - Represents current export time (not source data)

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert "export_date:" in frontmatter, "Frontmatter should contain 'export_date:' field"

    def test_frontmatter_contains_exported_by_field(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that frontmatter includes exported_by field.

        Validates:
        - FR-031: exported_by field present
        - Field format: exported_by: echomine

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter section
        frontmatter = self._extract_frontmatter(markdown)

        assert frontmatter is not None, "YAML frontmatter should be present"
        assert "exported_by: echomine" in frontmatter, (
            "Frontmatter should contain 'exported_by: echomine'"
        )

    def _extract_frontmatter(self, markdown: str) -> str | None:
        """Extract YAML frontmatter section from markdown.

        Args:
            markdown: Full markdown document

        Returns:
            Frontmatter content (between --- delimiters) or None if not found
        """
        if not markdown.startswith("---\n"):
            return None

        lines = markdown.split("\n")
        closing_idx = None

        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_idx = i
                break

        if closing_idx is None:
            return None

        return "\n".join(lines[1:closing_idx])


# =============================================================================
# T088: Unit Test - Datetime Fields Use ISO 8601 with Z Suffix (FR-031b)
# =============================================================================


@pytest.mark.unit
class TestYAMLFrontmatterDatetimeFormat:
    """Test that datetime fields use ISO 8601 format with UTC 'Z' suffix (FR-031b).

    Expected to FAIL: Frontmatter generation not implemented.
    """

    def test_created_at_uses_iso8601_with_z_suffix(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that created_at uses ISO 8601 format with Z suffix.

        Validates:
        - FR-031b: ISO 8601 format YYYY-MM-DDTHH:MM:SSZ
        - Z suffix indicates UTC timezone
        - create_time: 1705320600.0 = 2024-01-15T10:30:00Z

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter
        frontmatter = self._extract_frontmatter(markdown)
        assert frontmatter is not None, "YAML frontmatter should be present"

        # Assert: created_at uses ISO 8601 with Z suffix
        # Expected: 1705320600.0 = 2024-01-15T10:30:00Z
        assert "created_at: 2024-01-15T10:30:00Z" in frontmatter, (
            "created_at should use ISO 8601 format with Z suffix (2024-01-15T10:30:00Z)"
        )

    def test_updated_at_uses_iso8601_with_z_suffix(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that updated_at uses ISO 8601 format with Z suffix.

        Validates:
        - FR-031b: ISO 8601 format YYYY-MM-DDTHH:MM:SSZ
        - Z suffix indicates UTC timezone
        - update_time: 1705335000.0 = 2024-01-15T14:30:00Z

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter
        frontmatter = self._extract_frontmatter(markdown)
        assert frontmatter is not None, "YAML frontmatter should be present"

        # Assert: updated_at uses ISO 8601 with Z suffix
        # Expected: 1705335000.0 = 2024-01-15T14:30:00Z
        assert "updated_at: 2024-01-15T14:30:00Z" in frontmatter, (
            "updated_at should use ISO 8601 format with Z suffix (2024-01-15T14:30:00Z)"
        )

    def test_export_date_uses_iso8601_with_z_suffix(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that export_date uses ISO 8601 format with Z suffix.

        Validates:
        - FR-031b: ISO 8601 format YYYY-MM-DDTHH:MM:SSZ
        - Z suffix indicates UTC timezone
        - export_date is current time (not from source data)

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter
        frontmatter = self._extract_frontmatter(markdown)
        assert frontmatter is not None, "YAML frontmatter should be present"

        # Assert: export_date uses ISO 8601 with Z suffix
        # Pattern: YYYY-MM-DDTHH:MM:SSZ
        iso8601_z_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        export_date_match = re.search(
            rf"export_date: ({iso8601_z_pattern})",
            frontmatter,
        )

        assert export_date_match is not None, (
            "export_date should use ISO 8601 format with Z suffix (e.g., 2025-12-05T15:30:00Z)"
        )

    def test_z_suffix_not_plus_zero_offset(self, sample_conversation_with_ids: Path) -> None:
        """Test that Z suffix is used instead of +00:00 timezone offset.

        Validates:
        - FR-031b: Requires 'Z' suffix specifically, not '+00:00'
        - Consistency across all datetime fields

        Expected to FAIL: No frontmatter generation.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Extract frontmatter
        frontmatter = self._extract_frontmatter(markdown)
        assert frontmatter is not None, "YAML frontmatter should be present"

        # Assert: No +00:00 timezone offset (should use Z)
        assert "+00:00" not in frontmatter, (
            "Datetime fields should use 'Z' suffix, not '+00:00' timezone offset"
        )

        # Assert: All datetime fields use Z suffix
        assert "created_at: " in frontmatter and "Z" in frontmatter, (
            "created_at should use Z suffix"
        )

    def _extract_frontmatter(self, markdown: str) -> str | None:
        """Extract YAML frontmatter section from markdown."""
        if not markdown.startswith("---\n"):
            return None

        lines = markdown.split("\n")
        closing_idx = None

        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_idx = i
                break

        if closing_idx is None:
            return None

        return "\n".join(lines[1:closing_idx])


# =============================================================================
# T089: Unit Test - Message Headers Include Message ID in Backticks (FR-032)
# =============================================================================


@pytest.mark.unit
class TestMessageHeadersWithIDs:
    """Test that message headers include message ID in inline code format (FR-032).

    Expected to FAIL: Message ID not currently included in headers.
    """

    def test_message_headers_include_id_in_backticks(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that message headers include ID in inline code format.

        Validates:
        - FR-032: Message headers show ID in backticks
        - Format: ## User (`msg-source-001`) - 2024-01-15 10:30:00 UTC
        - ID appears between role and timestamp

        Expected to FAIL: Headers don't include message IDs currently.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Find user message header
        user_header_pattern = r"## User \(`msg-source-001`\) - \d{4}-\d{2}-\d{2}"
        user_match = re.search(user_header_pattern, markdown)

        assert user_match is not None, (
            "User message header should include ID in backticks: "
            "## User (`msg-source-001`) - <timestamp>"
        )

        # Assert: Find assistant message header
        assistant_header_pattern = r"## Assistant \(`msg-source-002`\) - \d{4}-\d{2}-\d{2}"
        assistant_match = re.search(assistant_header_pattern, markdown)

        assert assistant_match is not None, (
            "Assistant message header should include ID in backticks: "
            "## Assistant (`msg-source-002`) - <timestamp>"
        )

    def test_message_id_appears_between_role_and_timestamp(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that message ID appears between role name and timestamp.

        Validates:
        - FR-032: Specific header format
        - Order: Role (`ID`) - Timestamp
        - Consistent spacing

        Expected to FAIL: Headers don't include message IDs.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: Header follows pattern: Role (`ID`) - Timestamp
        # Pattern: ## <Role> (`<msg-id>`) - <ISO timestamp>
        header_pattern = r"## (User|Assistant) \(`[^`]+`\) - \d{4}-\d{2}-\d{2}"
        matches = re.findall(header_pattern, markdown)

        assert len(matches) >= 2, (
            "Should have at least 2 message headers with IDs in format: "
            "## Role (`msg-id`) - timestamp"
        )


# =============================================================================
# T090: Unit Test - Generated Message IDs Follow Format (FR-032a)
# =============================================================================


@pytest.mark.unit
class TestGeneratedMessageIDFormat:
    """Test that generated message IDs follow msg-{conv_id}-{index} format (FR-032a).

    Expected to FAIL: Message ID generation not implemented.
    """

    def test_generated_ids_use_correct_format(self, sample_conversation_without_ids: Path) -> None:
        """Test that generated IDs follow msg-{conversation_id}-{index} format.

        Validates:
        - FR-032a: Format is msg-{conv_id}-{zero_padded_index}
        - Example: msg-conv-xyz789-001, msg-conv-xyz789-002
        - Index is zero-padded to 3 digits

        Expected to FAIL: ID generation not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-xyz789"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_without_ids,
            conversation_id,
        )

        # Assert: First message has generated ID: msg-conv-xyz789-001
        first_msg_pattern = r"## User \(`msg-conv-xyz789-001`\) -"
        first_match = re.search(first_msg_pattern, markdown)

        assert first_match is not None, (
            "First message should have generated ID: msg-conv-xyz789-001"
        )

        # Assert: Second message has generated ID: msg-conv-xyz789-002
        second_msg_pattern = r"## Assistant \(`msg-conv-xyz789-002`\) -"
        second_match = re.search(second_msg_pattern, markdown)

        assert second_match is not None, (
            "Second message should have generated ID: msg-conv-xyz789-002"
        )

    def test_generated_ids_use_zero_padded_index(
        self, sample_conversation_without_ids: Path
    ) -> None:
        """Test that generated IDs use zero-padded index (001, 002, not 1, 2).

        Validates:
        - FR-032a: Index is zero-padded to 3 digits
        - Consistent width for sorting and readability

        Expected to FAIL: ID generation not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-xyz789"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_without_ids,
            conversation_id,
        )

        # Assert: IDs use 3-digit zero-padding
        # Should find: msg-conv-xyz789-001, msg-conv-xyz789-002
        # Should NOT find: msg-conv-xyz789-1, msg-conv-xyz789-2
        assert "msg-conv-xyz789-001" in markdown, (
            "Generated IDs should use 3-digit zero-padding: msg-conv-xyz789-001"
        )
        assert "msg-conv-xyz789-002" in markdown, (
            "Generated IDs should use 3-digit zero-padding: msg-conv-xyz789-002"
        )

        # Assert: No non-zero-padded IDs
        assert "msg-conv-xyz789-1)" not in markdown, (
            "Generated IDs should NOT use non-zero-padded index (msg-...-1)"
        )


# =============================================================================
# T091: Unit Test - Generated IDs Are Deterministic/Reproducible (FR-032b)
# =============================================================================


@pytest.mark.unit
class TestGeneratedMessageIDDeterminism:
    """Test that generated message IDs are deterministic/reproducible (FR-032b).

    Expected to FAIL: ID generation not implemented.
    """

    def test_generated_ids_are_deterministic(self, sample_conversation_without_ids: Path) -> None:
        """Test that same source produces same generated IDs.

        Validates:
        - FR-032b: Deterministic ID generation
        - Same file -> same IDs every time
        - Reproducibility for testing and archival

        Expected to FAIL: ID generation not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-xyz789"

        # Act: Export twice
        markdown1 = exporter.export_conversation(
            sample_conversation_without_ids,
            conversation_id,
        )
        markdown2 = exporter.export_conversation(
            sample_conversation_without_ids,
            conversation_id,
        )

        # Assert: Both exports produce identical message IDs
        # Extract all message IDs from both exports
        id_pattern = r"## (User|Assistant) \(`([^`]+)`\)"
        ids1 = [match[1] for match in re.findall(id_pattern, markdown1)]
        ids2 = [match[1] for match in re.findall(id_pattern, markdown2)]

        assert ids1 == ids2, (
            "Generated IDs should be deterministic (same source -> same IDs). "
            f"First export IDs: {ids1}, Second export IDs: {ids2}"
        )

    def test_generated_ids_match_message_order(self, sample_conversation_without_ids: Path) -> None:
        """Test that generated IDs match message chronological order.

        Validates:
        - FR-032b: IDs based on message position (deterministic)
        - Index 001 = first message, 002 = second, etc.
        - Order is stable and predictable

        Expected to FAIL: ID generation not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-xyz789"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_without_ids,
            conversation_id,
        )

        # Assert: Extract message headers in document order
        header_pattern = r"## (User|Assistant) \(`([^`]+)`\)"
        headers = re.findall(header_pattern, markdown)

        assert len(headers) == 2, "Should have 2 message headers"

        # Assert: First header has ID ending with -001
        first_role, first_id = headers[0]
        assert first_id == "msg-conv-xyz789-001", (
            f"First message should have ID msg-conv-xyz789-001, got {first_id}"
        )

        # Assert: Second header has ID ending with -002
        second_role, second_id = headers[1]
        assert second_id == "msg-conv-xyz789-002", (
            f"Second message should have ID msg-conv-xyz789-002, got {second_id}"
        )


# =============================================================================
# T092: Unit Test - include_metadata=False Disables Frontmatter (FR-033, FR-035)
# =============================================================================


@pytest.mark.unit
class TestIncludeMetadataParameter:
    """Test that include_metadata parameter controls frontmatter (FR-033, FR-035).

    Expected to FAIL: include_metadata parameter not implemented.
    """

    def test_include_metadata_false_disables_frontmatter(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that include_metadata=False disables YAML frontmatter.

        Validates:
        - FR-033: --no-metadata flag support
        - FR-035: Library API has include_metadata parameter
        - Frontmatter completely omitted when False
        - Content still exported normally

        Expected to FAIL: include_metadata parameter doesn't exist.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
            include_metadata=False,
        )

        # Assert: No YAML frontmatter delimiters
        assert not markdown.startswith("---\n"), (
            "With include_metadata=False, markdown should NOT start with YAML "
            "frontmatter delimiter '---'"
        )

        # Assert: No frontmatter fields
        assert "id:" not in markdown.split("##")[0], (
            "With include_metadata=False, no 'id:' field before first message"
        )
        assert "export_date:" not in markdown.split("##")[0], (
            "With include_metadata=False, no 'export_date:' field"
        )

        # Assert: Content still present (title heading and messages)
        assert "# Python Generators Deep Dive" in markdown, "Title heading should still be present"
        assert "## User" in markdown, "Message content should still be present"

    def test_include_metadata_true_enables_frontmatter(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that include_metadata=True enables YAML frontmatter (default).

        Validates:
        - FR-035: include_metadata parameter with default=True
        - Explicit True has same effect as default
        - Frontmatter is generated when True

        Expected to FAIL: include_metadata parameter doesn't exist.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
            include_metadata=True,
        )

        # Assert: YAML frontmatter present
        assert markdown.startswith("---\n"), (
            "With include_metadata=True, markdown should start with YAML frontmatter"
        )

        # Assert: Frontmatter contains expected fields
        frontmatter = self._extract_frontmatter(markdown)
        assert frontmatter is not None, "Frontmatter should be present"
        assert "id: conv-abc123" in frontmatter, "Frontmatter should have id field"

    def test_include_message_ids_false_disables_ids_in_headers(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test that include_message_ids=False disables IDs in headers.

        Validates:
        - FR-035: include_message_ids parameter
        - Headers revert to old format without IDs
        - Format: ## User - 2024-01-15 10:30:00 UTC (no ID)

        Expected to FAIL: include_message_ids parameter doesn't exist.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
            include_message_ids=False,
        )

        # Assert: No message IDs in headers
        # Headers should be: ## User - <timestamp> (no backtick ID)
        id_pattern = r"## (User|Assistant) \(`[^`]+`\)"
        id_matches = re.findall(id_pattern, markdown)

        assert len(id_matches) == 0, (
            "With include_message_ids=False, headers should NOT include IDs in backticks"
        )

        # Assert: Headers still present but without IDs (old emoji format)
        # When include_message_ids=False, falls back to emoji format
        emoji_header_pattern = r"## [👤🤖] (User|Assistant) · \d{4}-\d{2}-\d{2}"
        emoji_matches = re.findall(emoji_header_pattern, markdown)

        assert len(emoji_matches) >= 2, (
            "Headers should still be present in format: ## 👤 User · timestamp "
            "(old emoji format when message IDs disabled)"
        )

    def _extract_frontmatter(self, markdown: str) -> str | None:
        """Extract YAML frontmatter section from markdown."""
        if not markdown.startswith("---\n"):
            return None

        lines = markdown.split("\n")
        closing_idx = None

        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_idx = i
                break

        if closing_idx is None:
            return None

        return "\n".join(lines[1:closing_idx])


# =============================================================================
# T093: Contract Test - FR-030 Frontmatter Default Behavior
# =============================================================================


@pytest.mark.contract
class TestFR030FrontmatterDefault:
    """Contract test for FR-030: YAML frontmatter included by default.

    This test validates the contract between library and CLI:
    - Default behavior includes frontmatter
    - No parameter = frontmatter present

    Expected to FAIL: Frontmatter not implemented.
    """

    def test_fr030_default_export_includes_frontmatter(
        self, sample_conversation_with_ids: Path
    ) -> None:
        """Test FR-030: Markdown exports include YAML frontmatter by default.

        Validates:
        - No include_metadata parameter = frontmatter present (default True)
        - Backward compatibility consideration: new default behavior

        Expected to FAIL: Frontmatter not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "conv-abc123"

        # Act: Call without explicit include_metadata parameter (use default)
        markdown = exporter.export_conversation(
            sample_conversation_with_ids,
            conversation_id,
        )

        # Assert: YAML frontmatter present by default
        assert markdown.startswith("---\n"), (
            "FR-030: Markdown exports MUST include YAML frontmatter by default. "
            "Export without explicit include_metadata parameter should have frontmatter."
        )

        # Assert: Frontmatter contains minimum required fields
        frontmatter_section = markdown.split("---\n")[1] if "---\n" in markdown else ""

        required_fields = ["id:", "title:", "created_at:", "message_count:", "exported_by:"]
        for field in required_fields:
            assert field in frontmatter_section, (
                f"FR-030: Default frontmatter must contain '{field}' field"
            )
