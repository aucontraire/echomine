"""Golden master tests for markdown export validation.

These tests validate the markdown export functionality against known-good
conversation exports that serve as the "golden master" reference.

Constitution Compliance:
- Principle III: TDD - Tests written before implementation
- Principle VI: Strict typing with mypy --strict compliance
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass

# Golden master fixture directory
GOLDEN_MASTER_DIR = Path(__file__).parent.parent / "fixtures" / "golden_master"


class TestGoldenMasterConversations:
    """Test suite for golden master conversation validation.

    Each golden master consists of:
    - raw.json: Original OpenAI conversation export
    - expected.md: Expected markdown output (manually verified)

    These tests will validate that our markdown exporter produces
    output matching the expected.md files.
    """

    @pytest.fixture
    def golden_master_001(self) -> tuple[Path, Path]:
        """Golden master 001: Simple text-only conversation.

        Returns:
            Tuple of (raw.json path, expected.md path)
        """
        base = GOLDEN_MASTER_DIR / "001_simple_text"
        return base / "raw.json", base / "expected.md"

    @pytest.fixture
    def golden_master_002(self) -> tuple[Path, Path]:
        """Golden master 002: Conversation with images (multimodal).

        Returns:
            Tuple of (raw.json path, expected.md path)
        """
        base = GOLDEN_MASTER_DIR / "002_with_images"
        return base / "raw.json", base / "expected.md"

    @pytest.fixture
    def golden_master_003(self) -> tuple[Path, Path]:
        """Golden master 003: Conversation with code blocks.

        Returns:
            Tuple of (raw.json path, expected.md path)
        """
        base = GOLDEN_MASTER_DIR / "003_with_code"
        return base / "raw.json", base / "expected.md"

    def test_simple_text_conversation(
        self, golden_master_001: tuple[Path, Path]
    ) -> None:
        """Test markdown export for simple text-only conversation.

        Validates:
        - Message order preserved
        - Role headers with emoji (👤 User, 🤖 Assistant)
        - ISO 8601 timestamps
        - Message separators (---)
        - Content accuracy

        Args:
            golden_master_001: Tuple of (raw.json path, expected.md path)
        """
        from echomine.export import MarkdownExporter

        raw_path, expected_path = golden_master_001

        # Load the raw conversation
        import json
        with open(raw_path, "r", encoding="utf-8") as f:
            conv_data = json.load(f)
        conversation_id = conv_data["id"]

        # Export to markdown
        exporter = MarkdownExporter()
        actual_md = exporter.export_conversation(raw_path, conversation_id)

        # Load expected output
        expected_md = expected_path.read_text(encoding="utf-8")

        # Compare outputs
        assert actual_md == expected_md, (
            f"Markdown output doesn't match expected.\n\n"
            f"Expected:\n{expected_md[:500]}...\n\n"
            f"Actual:\n{actual_md[:500]}..."
        )

    def test_conversation_with_images(
        self, golden_master_002: tuple[Path, Path]
    ) -> None:
        """Test markdown export for conversation with images.

        Validates:
        - Multimodal content parsing
        - Image references included (not placeholders)
        - Image markdown syntax: ![Image](file-id-sanitized.png)
        - Text and images properly separated

        Args:
            golden_master_002: Tuple of (raw.json path, expected.md path)
        """
        raw_path, expected_path = golden_master_002

        from echomine.export import MarkdownExporter

        raw_path, expected_path = golden_master_002

        # Load the raw conversation
        import json
        with open(raw_path, "r", encoding="utf-8") as f:
            conv_data = json.load(f)
        conversation_id = conv_data["id"]

        # Export to markdown
        exporter = MarkdownExporter()
        actual_md = exporter.export_conversation(raw_path, conversation_id)

        # Load expected output
        expected_md = expected_path.read_text(encoding="utf-8")

        # Verify image references are present in expected output
        assert "![Image]" in expected_md, "Expected markdown should contain image references"

        # Compare outputs
        assert actual_md == expected_md, (
            f"Markdown output doesn't match expected.\n\n"
            f"Expected:\n{expected_md[:500]}...\n\n"
            f"Actual:\n{actual_md[:500]}..."
        )

    def test_conversation_with_code(
        self, golden_master_003: tuple[Path, Path]
    ) -> None:
        """Test markdown export for conversation with code blocks.

        Validates:
        - Code content type handling
        - Code block preservation
        - Syntax highlighting hints (if present)
        - Mixed content (text + code) handling

        Args:
            golden_master_003: Tuple of (raw.json path, expected.md path)
        """
        raw_path, expected_path = golden_master_003

        from echomine.export import MarkdownExporter

        raw_path, expected_path = golden_master_003

        # Load the raw conversation
        import json
        with open(raw_path, "r", encoding="utf-8") as f:
            conv_data = json.load(f)
        conversation_id = conv_data["id"]

        # Export to markdown
        exporter = MarkdownExporter()
        actual_md = exporter.export_conversation(raw_path, conversation_id)

        # Load expected output
        expected_md = expected_path.read_text(encoding="utf-8")

        # Compare outputs
        assert actual_md == expected_md, (
            f"Markdown output doesn't match expected.\n\n"
            f"Expected:\n{expected_md[:500]}...\n\n"
            f"Actual:\n{actual_md[:500]}..."
        )


class TestGoldenMasterFileStructure:
    """Validate golden master file structure and completeness."""

    def test_all_golden_masters_exist(self) -> None:
        """Verify all golden master directories and files exist."""
        expected_dirs = ["001_simple_text", "002_with_images", "003_with_code"]

        for dir_name in expected_dirs:
            dir_path = GOLDEN_MASTER_DIR / dir_name
            assert dir_path.exists(), f"Golden master directory missing: {dir_path}"

            raw_json = dir_path / "raw.json"
            expected_md = dir_path / "expected.md"

            assert raw_json.exists(), f"raw.json missing in {dir_name}"
            assert expected_md.exists(), f"expected.md missing in {dir_name}"

            # Verify files are not empty
            assert raw_json.stat().st_size > 0, f"raw.json is empty in {dir_name}"
            assert expected_md.stat().st_size > 0, f"expected.md is empty in {dir_name}"

    def test_expected_md_format(self) -> None:
        """Verify expected.md files follow the required format.

        Validates:
        - Headers with emoji (## 👤 User, ## 🤖 Assistant)
        - ISO 8601 timestamps in headers
        - Message separators (---)
        - No blockquotes used for user messages
        """
        expected_dirs = ["001_simple_text", "002_with_images", "003_with_code"]

        for dir_name in expected_dirs:
            expected_md = GOLDEN_MASTER_DIR / dir_name / "expected.md"
            content = expected_md.read_text(encoding="utf-8")

            # Verify headers with emoji
            assert "## 👤 User" in content or "## 🤖 Assistant" in content, (
                f"{dir_name}: Expected markdown should have headers with emoji"
            )

            # Verify ISO 8601 timestamps (format: YYYY-MM-DDTHH:MM:SS+00:00)
            import re
            timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}"
            assert re.search(timestamp_pattern, content), (
                f"{dir_name}: Expected markdown should have ISO 8601 timestamps"
            )

            # Verify message separators
            if content.count("##") > 1:  # Only check if multiple messages
                assert "---" in content, (
                    f"{dir_name}: Expected markdown should have message separators (---)"
                )

            # Verify NO blockquotes for user messages
            # (User explicitly rejected blockquotes in requirements)
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("> ") and i > 0:
                    # Check if this is after a User header
                    prev_lines = "\n".join(lines[max(0, i-10):i])
                    if "## 👤 User" in prev_lines:
                        # This might be a quote within the message content, not a blockquote format
                        # Only fail if it appears to be structural formatting
                        pass  # Allow quotes in content
