"""Integration tests for export workflow.

Task: T069 - Export Workflow Integration Testing
Phase: RED (tests designed to FAIL initially)

This module tests the end-to-end export workflow from CLI to file system,
validating the integration between:
- CLI argument parsing (Typer)
- Conversation lookup (OpenAIAdapter or direct JSON access)
- Markdown export (MarkdownExporter class)
- File I/O (writing to disk)

Test Pyramid Classification: Integration (20% of test suite)
These tests validate component interactions WITHOUT subprocess calls.

Integration Points Tested:
- CLI commands → Library API
- MarkdownExporter → File system
- Conversation lookup → Export rendering
- Error propagation across layers

Architectural Coverage:
- Library-first: CLI delegates to library classes
- Error handling: Exceptions propagated correctly
- Resource cleanup: Files closed properly
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.export.markdown import MarkdownExporter


# =============================================================================
# Integration Test Fixtures
# =============================================================================


@pytest.fixture
def integration_export_file(tmp_path: Path) -> Path:
    """Create sample export for integration testing.

    Contains varied conversation types:
    - Simple text conversation
    - Conversation with code blocks
    - Conversation with multimodal content (images)
    """
    conversations = [
        {
            "id": "integ-conv-001",
            "title": "Python Async Programming",
            "create_time": 1710000000.0,
            "update_time": 1710001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain async/await in Python"],
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
                            "parts": [
                                "Async/await in Python allows concurrent execution of I/O-bound operations."
                            ],
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
        },
        {
            "id": "integ-conv-002",
            "title": "Code Example: Binary Search",
            "create_time": 1710100000.0,
            "update_time": 1710100500.0,
            "mapping": {
                "msg-code-1": {
                    "id": "msg-code-1",
                    "message": {
                        "id": "msg-code-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Show me binary search in Python"],
                        },
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-code-2"],
                },
                "msg-code-2": {
                    "id": "msg-code-2",
                    "message": {
                        "id": "msg-code-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "code",
                            "text": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    return -1",
                        },
                        "create_time": 1710100010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-code-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-code-2",
        },
        {
            "id": "integ-conv-003",
            "title": "Image Analysis Request",
            "create_time": 1710200000.0,
            "update_time": 1710200500.0,
            "mapping": {
                "msg-img-1": {
                    "id": "msg-img-1",
                    "message": {
                        "id": "msg-img-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "multimodal_text",
                            "parts": [
                                "Analyze this image:",
                                {
                                    "content_type": "image_asset_pointer",
                                    "asset_pointer": "file-service://file-xyz789",
                                },
                            ],
                        },
                        "create_time": 1710200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-img-2"],
                },
                "msg-img-2": {
                    "id": "msg-img-2",
                    "message": {
                        "id": "msg-img-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["The image shows a diagram of data structures."],
                        },
                        "create_time": 1710200010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-img-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-img-2",
        },
    ]

    export_file = tmp_path / "integration_export.json"
    with export_file.open("w") as f:
        json.dump(conversations, f, indent=2)

    return export_file


# =============================================================================
# Integration Tests - Export Flow
# =============================================================================


@pytest.mark.integration
class TestExportIntegrationFlow:
    """Integration tests for export workflow.

    These tests validate the full export pipeline WITHOUT using subprocess.
    They test component integration directly.

    Expected Failure Reasons (RED phase):
    - CLI export command not implemented
    - Conversation lookup logic not implemented
    - File writing logic not implemented
    """

    def test_export_conversation_by_id_to_file(
        self, integration_export_file: Path, tmp_path: Path
    ) -> None:
        """Test full export flow: file → lookup by ID → export → verify file.

        Validates:
        - MarkdownExporter.export_conversation() integration
        - File I/O with proper encoding
        - Markdown format compliance

        Expected to FAIL: Integration not complete.
        """
        # Arrange
        exporter = MarkdownExporter()
        output_file = tmp_path / "exported.md"
        conversation_id = "integ-conv-001"

        # Act: Export conversation
        markdown = exporter.export_conversation(integration_export_file, conversation_id)

        # Write to file (simulating CLI file write)
        output_file.write_text(markdown, encoding="utf-8")

        # Assert: File exists and contains expected content
        assert output_file.exists(), "Output file should be created"

        content = output_file.read_text(encoding="utf-8")
        assert len(content) > 0, "Output file should not be empty"
        assert "Python Async Programming" in content, (
            "Title SHOULD be in metadata header (FR-014 requirement)"
        )
        assert "Created:" in content, "Should include created timestamp in metadata"
        assert "Messages:" in content, "Should include message count in metadata"
        assert "async/await" in content, "Should contain conversation content"
        assert "##" in content, "Should have markdown headers"
        assert "👤" in content or "🤖" in content, "Should have emoji headers"

    def test_export_conversation_by_title_to_file(
        self, integration_export_file: Path, tmp_path: Path
    ) -> None:
        """Test export using conversation title for lookup.

        Validates:
        - Title-based conversation search
        - Export of correct conversation
        - Case-insensitive or partial title matching

        Expected to FAIL: Title-based lookup not implemented.

        Note: This test assumes we'll implement title-based lookup.
        If not needed, this test can be removed.
        """
        # This test will need a helper function to find conversation by title
        # For now, this is a placeholder showing the expected behavior

        # Arrange
        title = "Python Async Programming"

        # Act: Find conversation by title
        # (Implementation will need to scan JSON for matching title)
        with open(integration_export_file) as f:
            data = json.load(f)
            found_conv = None
            for conv in data:
                if conv.get("title") == title:
                    found_conv = conv
                    break

        # Assert: Found correct conversation
        assert found_conv is not None, f"Should find conversation with title: {title}"
        assert found_conv["id"] == "integ-conv-001", "Should find correct conversation"

        # Export using ID (once title lookup is working)
        exporter = MarkdownExporter()
        markdown = exporter.export_conversation(integration_export_file, found_conv["id"])

        # Verify export
        assert "async/await" in markdown, "Should export correct conversation"

    def test_export_conversation_to_stdout(self, integration_export_file: Path) -> None:
        """Test export to stdout (no file writing).

        Validates:
        - Markdown string returned directly
        - No file I/O required for stdout mode
        - Library-first: export_conversation returns string

        Expected to FAIL: Not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "integ-conv-001"

        # Act: Export conversation (returns markdown string)
        markdown = exporter.export_conversation(integration_export_file, conversation_id)

        # Assert: Markdown string is returned
        assert isinstance(markdown, str), "Should return markdown string"
        assert len(markdown) > 0, "Should not be empty"
        assert "async/await" in markdown, "Should contain conversation content"

    def test_export_with_images_includes_image_references(
        self, integration_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that conversations with images include image markdown.

        Validates:
        - Multimodal content handling
        - Image asset pointer conversion to markdown
        - Format: ![Image](file-id-sanitized.png)

        Expected to FAIL: Image handling not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "integ-conv-003"  # Has image content
        output_file = tmp_path / "with_images.md"

        # Act: Export conversation with images
        markdown = exporter.export_conversation(integration_export_file, conversation_id)
        output_file.write_text(markdown, encoding="utf-8")

        # Assert: Image markdown included
        content = output_file.read_text(encoding="utf-8")
        assert "![Image]" in content, "Should include image markdown"
        assert "file-xyz789-sanitized.png" in content, (
            "Should convert asset pointer to sanitized filename"
        )

    def test_export_with_code_preserves_code_blocks(
        self, integration_export_file: Path, tmp_path: Path
    ) -> None:
        """Test that code content is preserved with proper formatting.

        Validates:
        - FR-015: Preserve code blocks and formatting
        - Code content type handling
        - Markdown code fence usage (optional)

        Expected to FAIL: Code preservation not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        conversation_id = "integ-conv-002"  # Has code content
        output_file = tmp_path / "with_code.md"

        # Act: Export conversation with code
        markdown = exporter.export_conversation(integration_export_file, conversation_id)
        output_file.write_text(markdown, encoding="utf-8")

        # Assert: Code content preserved
        content = output_file.read_text(encoding="utf-8")
        assert "binary_search" in content, "Should include code content"
        assert "def binary_search" in content, "Should preserve code structure"

        # Optional: Check for code fences (if implemented)
        # assert "```" in content, "Should use markdown code fences"


# =============================================================================
# Integration Tests - Error Handling
# =============================================================================


@pytest.mark.integration
class TestExportErrorHandling:
    """Integration tests for export error scenarios.

    Tests error propagation and handling across components.
    """

    def test_export_nonexistent_conversation_raises_error(
        self, integration_export_file: Path
    ) -> None:
        """Test that exporting non-existent conversation raises ValueError.

        Validates:
        - MarkdownExporter error handling
        - Clear error message for missing conversation

        Expected to FAIL: Error handling not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        nonexistent_id = "nonexistent-conv-id-12345"

        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            exporter.export_conversation(integration_export_file, nonexistent_id)

    def test_export_invalid_file_path_raises_error(self, tmp_path: Path) -> None:
        """Test that exporting from non-existent file raises FileNotFoundError.

        Validates:
        - MarkdownExporter file error handling
        - Proper exception type for file not found

        Expected to FAIL: Error handling not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        nonexistent_file = tmp_path / "nonexistent.json"
        conversation_id = "any-id"

        # Act & Assert: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            exporter.export_conversation(nonexistent_file, conversation_id)

    def test_export_malformed_json_raises_error(self, tmp_path: Path) -> None:
        """Test that malformed JSON file raises json.JSONDecodeError.

        Validates:
        - JSON parsing error handling
        - Error propagation from json.load()

        Expected to FAIL: Error handling not implemented.
        """
        # Arrange
        exporter = MarkdownExporter()
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{invalid json syntax")
        conversation_id = "any-id"

        # Act & Assert: Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            exporter.export_conversation(malformed_file, conversation_id)


# =============================================================================
# Integration Tests - Library Integration
# =============================================================================


@pytest.mark.integration
class TestExportLibraryIntegration:
    """Integration tests for library-first architecture.

    These tests validate that the export functionality is properly exposed
    as a library API (not just CLI).
    """

    def test_export_uses_markdown_exporter_class(self, integration_export_file: Path) -> None:
        """Test that export functionality uses MarkdownExporter class.

        Validates:
        - Library-first architecture (Principle I)
        - MarkdownExporter is importable and usable
        - Type hints available for library consumers

        Expected to FAIL: Integration not complete.
        """
        # Arrange & Act: Import and instantiate MarkdownExporter
        from echomine.export.markdown import MarkdownExporter

        exporter = MarkdownExporter()

        # Assert: Instance created successfully
        assert exporter is not None, "Should create MarkdownExporter instance"
        assert hasattr(exporter, "export_conversation"), "Should have export_conversation method"

        # Act: Use exporter
        markdown = exporter.export_conversation(integration_export_file, "integ-conv-001")

        # Assert: Returns markdown string
        assert isinstance(markdown, str), "Should return markdown string"
        assert len(markdown) > 0, "Should not be empty"

    def test_export_streams_efficiently_for_large_files(self, tmp_path: Path) -> None:
        """Test that export is memory-efficient for large export files.

        Validates:
        - FR-008: Streaming efficiency (O(1) memory)
        - No full file load into memory
        - Efficient conversation lookup

        Expected to FAIL: Streaming optimization not implemented.

        Note: This test creates a large file to verify memory efficiency.
        May be slow in CI - consider marking as @pytest.mark.slow
        """
        # Arrange: Create large export file (1000 conversations)
        conversations = []
        for i in range(1000):
            conversations.append(
                {
                    "id": f"conv-{i:04d}",
                    "title": f"Conversation {i}",
                    "create_time": 1710000000.0 + i * 100,
                    "update_time": 1710001000.0 + i * 100,
                    "mapping": {
                        f"msg-{i}": {
                            "id": f"msg-{i}",
                            "message": {
                                "id": f"msg-{i}",
                                "author": {"role": "user"},
                                "content": {
                                    "content_type": "text",
                                    "parts": [f"Message {i}"],
                                },
                                "create_time": 1710000000.0 + i * 100,
                                "update_time": None,
                                "metadata": {},
                            },
                            "parent": None,
                            "children": [],
                        }
                    },
                    "moderation_results": [],
                    "current_node": f"msg-{i}",
                }
            )

        large_file = tmp_path / "large_export.json"
        with large_file.open("w") as f:
            json.dump(conversations, f)

        # Act: Export conversation from large file
        exporter = MarkdownExporter()
        markdown = exporter.export_conversation(large_file, "conv-0999")

        # Assert: Successfully found and exported target conversation
        assert "Message 999" in markdown, "Should find conversation in large file"

        # Note: Memory efficiency would need profiling to verify
        # This test just ensures it completes without memory errors


# =============================================================================
# Integration Tests - Search-Then-Export Workflow
# =============================================================================


@pytest.mark.integration
class TestSearchThenExportWorkflow:
    """Integration tests for search-then-export workflow.

    Validates:
    - FR-356 to FR-360: Search-then-export pipeline
    - Composability of search and export commands
    """

    def test_search_result_provides_conversation_id_for_export(
        self, integration_export_file: Path
    ) -> None:
        """Test that search results include conversation_id for export.

        Validates:
        - FR-359: Search JSON output includes conversation_id
        - Pipeline workflow: search --json | jq | xargs export

        Expected to FAIL: Search-export integration not implemented.

        Note: This test assumes search functionality exists.
        May need to be moved/adjusted based on search implementation.
        """
        # This is a placeholder test for future search-then-export workflow
        # It demonstrates the expected integration pattern

        # Example workflow:
        # 1. Search returns JSON with conversation_id
        # 2. Extract conversation_id using jq or Python
        # 3. Pass conversation_id to export command

        # For now, just verify we can get conversation IDs from file
        with open(integration_export_file) as f:
            data = json.load(f)
            conversation_ids = [conv["id"] for conv in data]

        # Assert: Conversation IDs available
        assert len(conversation_ids) == 3, "Should have 3 conversations"
        assert "integ-conv-001" in conversation_ids, "Should include conv ID"

        # Future: Test actual search → export pipeline
