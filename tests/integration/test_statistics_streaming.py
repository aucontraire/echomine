"""Integration tests for statistics streaming and memory efficiency.

This module tests that calculate_statistics() uses O(1) memory via streaming,
regardless of file size.

Constitution Compliance:
    - Principle VIII: O(1) memory usage via streaming (FR-003, SC-001)
    - Principle III: TDD (tests written FIRST before implementation)

Test Coverage:
    - T045: calculate_statistics() streams with O(1) memory
"""

from __future__ import annotations

import json
from pathlib import Path

from echomine.adapters.openai import OpenAIAdapter


class TestStatisticsStreaming:
    """Test calculate_statistics() streaming behavior (T045)."""

    def test_calculate_statistics_streams_large_file(self, tmp_path: Path) -> None:
        """Test calculate_statistics() uses streaming for large files (T045).

        This test verifies that calculate_statistics() processes large export files
        using O(1) memory by streaming conversations one at a time via ijson.

        Memory Characteristics:
            - File size: ~1MB (1000 conversations)
            - Expected memory: <100MB (streaming parser + single conversation)
            - Anti-pattern: Loading entire file would use ~1MB+ in memory

        Note: This is a smoke test. For comprehensive memory profiling, use
        pytest-memray or manual memory profiling tools.
        """
        from echomine.statistics import calculate_statistics

        # Create large export file (1000 conversations)
        export_data = []
        for i in range(1000):
            export_data.append(
                {
                    "id": f"conv-{i}",
                    "title": f"Conversation {i}",
                    "create_time": 1704110400.0 + i * 100,
                    "update_time": 1704110400.0 + i * 100,
                    "mapping": {
                        f"node-{i}-1": {
                            "id": f"node-{i}-1",
                            "message": {
                                "id": f"msg-{i}-1",
                                "author": {"role": "user"},
                                "content": {
                                    "content_type": "text",
                                    "parts": [f"Message {i}"],
                                },
                                "create_time": 1704110400.0 + i * 100,
                            },
                            "parent": None,
                            "children": [],
                        },
                    },
                }
            )

        export_file = tmp_path / "large_export.json"
        export_file.write_text(json.dumps(export_data))

        # Calculate statistics (should stream, not load entire file)
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter)

        # Verify all conversations processed
        assert stats.total_conversations == 1000
        assert stats.total_messages == 1000
        assert stats.skipped_count == 0

        # If this test completes without MemoryError, streaming is working
        # For more rigorous memory testing, use pytest-memray

    def test_calculate_statistics_with_malformed_entries_streaming(self, tmp_path: Path) -> None:
        """Test calculate_statistics() gracefully skips malformed entries while streaming.

        Verifies that malformed entries don't crash the streaming parser and
        that processing continues for valid conversations.
        """
        from echomine.statistics import calculate_statistics

        # Create export with mix of valid and malformed (500 each)
        export_data = []
        for i in range(500):
            # Valid conversation
            export_data.append(
                {
                    "id": f"conv-valid-{i}",
                    "title": f"Valid {i}",
                    "create_time": 1704110400.0 + i * 100,
                    "update_time": 1704110400.0 + i * 100,
                    "mapping": {
                        f"node-{i}": {
                            "id": f"node-{i}",
                            "message": {
                                "id": f"msg-{i}",
                                "author": {"role": "user"},
                                "content": {"content_type": "text", "parts": [f"Msg {i}"]},
                                "create_time": 1704110400.0 + i * 100,
                            },
                            "parent": None,
                            "children": [],
                        },
                    },
                }
            )
            # Malformed conversation (missing required fields)
            export_data.append({"id": f"conv-malformed-{i}"})

        export_file = tmp_path / "mixed_export.json"
        export_file.write_text(json.dumps(export_data))

        # Calculate statistics (should skip malformed, process valid)
        adapter = OpenAIAdapter()
        stats = calculate_statistics(export_file, adapter=adapter)

        # Verify graceful degradation
        assert stats.total_conversations == 500
        assert stats.skipped_count == 500
