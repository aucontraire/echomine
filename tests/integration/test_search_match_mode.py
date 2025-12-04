"""Integration tests for match mode search end-to-end.

Tests for User Story 2: Boolean Match Mode (Priority: P1)

TDD: These tests are written FIRST and should FAIL until T025-T026
implement the match mode functionality.

Independent Test: Search with match_mode='all' returns only conversations
with ALL specified keywords.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def match_mode_export_file(tmp_path: Path) -> Path:
    """Create export with match mode testable content."""
    conversations = [
        {
            "id": "conv-both-python-java",
            "title": "Python and Java Discussion",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "msg-1": {
                    "id": "msg-1",
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["I use both Python and Java in my projects"],
                        },
                        "create_time": 1700000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-1",
        },
        {
            "id": "conv-python-only",
            "title": "Python Only Project",
            "create_time": 1700002000.0,
            "update_time": 1700003000.0,
            "mapping": {
                "msg-2": {
                    "id": "msg-2",
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Python is my favorite programming language"],
                        },
                        "create_time": 1700002000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-2",
        },
        {
            "id": "conv-java-only",
            "title": "Java Enterprise Project",
            "create_time": 1700004000.0,
            "update_time": 1700005000.0,
            "mapping": {
                "msg-3": {
                    "id": "msg-3",
                    "message": {
                        "id": "msg-3",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Java is great for enterprise applications"],
                        },
                        "create_time": 1700004000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-3",
        },
        {
            "id": "conv-neither",
            "title": "Rust Discussion",
            "create_time": 1700006000.0,
            "update_time": 1700007000.0,
            "mapping": {
                "msg-4": {
                    "id": "msg-4",
                    "message": {
                        "id": "msg-4",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Rust is a systems programming language"],
                        },
                        "create_time": 1700006000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-4",
        },
    ]

    export_file = tmp_path / "match_mode_test.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.integration
class TestMatchModeAcceptance:
    """Acceptance tests from spec.md User Story 2."""

    def test_us2_as1_match_mode_any_default(
        self, match_mode_export_file: Path
    ) -> None:
        """AS1: Default match_mode='any' returns conversations with ANY keyword.

        Given an export with conversations containing different keywords,
        When user searches with multiple keywords (default 'any' mode),
        Then conversations containing ANY of the keywords are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python", "java"])  # Default: match_mode='any'

        results = list(adapter.search(match_mode_export_file, query))

        # Should find conv-both, conv-python-only, conv-java-only (3 conversations)
        # Should NOT find conv-neither (has neither python nor java)
        result_ids = [r.conversation.id for r in results]

        assert "conv-both-python-java" in result_ids
        assert "conv-python-only" in result_ids
        assert "conv-java-only" in result_ids
        assert "conv-neither" not in result_ids
        assert len(results) == 3

    def test_us2_as2_match_mode_all_requires_all(
        self, match_mode_export_file: Path
    ) -> None:
        """AS2: match_mode='all' returns only conversations with ALL keywords.

        Given an export with conversations containing different keywords,
        When user searches with match_mode='all',
        Then only conversations containing ALL keywords are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python", "java"], match_mode="all")

        results = list(adapter.search(match_mode_export_file, query))

        # Should ONLY find conv-both (has both python AND java)
        result_ids = [r.conversation.id for r in results]

        assert "conv-both-python-java" in result_ids
        assert "conv-python-only" not in result_ids
        assert "conv-java-only" not in result_ids
        assert "conv-neither" not in result_ids
        assert len(results) == 1

    def test_us2_as3_match_mode_all_no_matches(
        self, match_mode_export_file: Path
    ) -> None:
        """AS3: match_mode='all' returns empty when no conversation has all keywords.

        Given keywords that don't all appear together in any conversation,
        When user searches with match_mode='all',
        Then no results are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python", "rust"], match_mode="all")

        results = list(adapter.search(match_mode_export_file, query))

        # No conversation has both python AND rust
        assert len(results) == 0

    def test_us2_as4_single_keyword_both_modes_same(
        self, match_mode_export_file: Path
    ) -> None:
        """AS4: Single keyword behaves the same in both modes.

        Given a single keyword,
        When user searches in 'any' or 'all' mode,
        Then results should be the same.
        """
        adapter = OpenAIAdapter()
        query_any = SearchQuery(keywords=["python"], match_mode="any")
        query_all = SearchQuery(keywords=["python"], match_mode="all")

        results_any = list(adapter.search(match_mode_export_file, query_any))
        results_all = list(adapter.search(match_mode_export_file, query_all))

        # Both should return the same results
        ids_any = sorted(r.conversation.id for r in results_any)
        ids_all = sorted(r.conversation.id for r in results_all)

        assert ids_any == ids_all


@pytest.mark.integration
class TestMatchModeEdgeCases:
    """Edge case tests for match mode."""

    def test_match_mode_all_with_phrases(self, match_mode_export_file: Path) -> None:
        """match_mode affects keywords, not phrases (phrases always OR)."""
        adapter = OpenAIAdapter()
        # Phrases use OR logic regardless of match_mode
        query = SearchQuery(
            keywords=["python", "java"],
            phrases=["enterprise"],
            match_mode="all",
        )

        results = list(adapter.search(match_mode_export_file, query))

        # Should find:
        # - conv-both (has python AND java - matches match_mode='all')
        # - conv-java-only (has phrase "enterprise" - phrases are OR)
        result_ids = [r.conversation.id for r in results]

        assert "conv-both-python-java" in result_ids
        assert "conv-java-only" in result_ids

    def test_match_mode_explicit_any(self, match_mode_export_file: Path) -> None:
        """Explicit match_mode='any' behaves like default."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python", "java"], match_mode="any")

        results = list(adapter.search(match_mode_export_file, query))

        # Should find all conversations with python OR java
        assert len(results) == 3

    def test_match_mode_case_insensitive(self, match_mode_export_file: Path) -> None:
        """match_mode='all' works with case-insensitive keywords."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["PYTHON", "JAVA"], match_mode="all")

        results = list(adapter.search(match_mode_export_file, query))

        # Should find conv-both (case-insensitive match)
        result_ids = [r.conversation.id for r in results]
        assert "conv-both-python-java" in result_ids
        assert len(results) == 1
