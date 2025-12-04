"""Integration tests for exclude keywords search end-to-end.

Tests for User Story 3: Exclude Keywords (Priority: P2)

TDD: These tests are written FIRST and should FAIL until T034-T036
implement the exclude functionality.

Independent Test: Search with exclude_keywords returns only conversations
without the excluded terms.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def exclude_export_file(tmp_path: Path) -> Path:
    """Create export with exclude testable content."""
    conversations = [
        {
            "id": "conv-python-django",
            "title": "Python Django Tutorial",
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
                            "parts": ["Django is a great framework for Python web apps"],
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
            "id": "conv-python-flask",
            "title": "Python Flask Tutorial",
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
                            "parts": ["Flask is a lightweight Python web framework"],
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
            "id": "conv-python-fastapi",
            "title": "Python FastAPI Tutorial",
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
                            "parts": ["FastAPI is a modern Python web framework"],
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
            "id": "conv-javascript",
            "title": "JavaScript React Tutorial",
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
                            "parts": ["React is a JavaScript library for UIs"],
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

    export_file = tmp_path / "exclude_test.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.integration
class TestExcludeAcceptance:
    """Acceptance tests from spec.md User Story 3."""

    def test_us3_as1_exclude_single_term(
        self, exclude_export_file: Path
    ) -> None:
        """AS1: Exclude single term filters out matching conversations.

        Given an export with conversations about different frameworks,
        When user searches for Python but excludes Django,
        Then Django conversations are filtered out.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], exclude_keywords=["django"])

        results = list(adapter.search(exclude_export_file, query))

        # Should find flask and fastapi, but NOT django
        result_ids = [r.conversation.id for r in results]

        assert "conv-python-flask" in result_ids
        assert "conv-python-fastapi" in result_ids
        assert "conv-python-django" not in result_ids
        assert len(results) == 2

    def test_us3_as2_exclude_multiple_terms(
        self, exclude_export_file: Path
    ) -> None:
        """AS2: Exclude multiple terms filters out all matching.

        Given an export with conversations about different frameworks,
        When user searches with multiple excluded terms,
        Then all matching conversations are filtered out.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["django", "flask"],
        )

        results = list(adapter.search(exclude_export_file, query))

        # Should only find fastapi
        result_ids = [r.conversation.id for r in results]

        assert "conv-python-fastapi" in result_ids
        assert "conv-python-django" not in result_ids
        assert "conv-python-flask" not in result_ids
        assert len(results) == 1

    def test_us3_as3_exclude_all_results(
        self, exclude_export_file: Path
    ) -> None:
        """AS3: Excluding all matching results returns empty.

        Given all matching conversations contain excluded terms,
        When user searches with exclude,
        Then no results are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["django", "flask", "fastapi"],
        )

        results = list(adapter.search(exclude_export_file, query))

        # All Python conversations excluded
        assert len(results) == 0

    def test_us3_as4_exclude_no_effect_on_non_matching(
        self, exclude_export_file: Path
    ) -> None:
        """AS4: Exclude has no effect when term not present.

        Given conversations that don't contain the excluded term,
        When user searches with exclude,
        Then those conversations are still returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["angular"],  # Not in any Python conversation
        )

        results = list(adapter.search(exclude_export_file, query))

        # All Python conversations should be returned
        result_ids = [r.conversation.id for r in results]

        assert "conv-python-django" in result_ids
        assert "conv-python-flask" in result_ids
        assert "conv-python-fastapi" in result_ids
        assert len(results) == 3


@pytest.mark.integration
class TestExcludeEdgeCases:
    """Edge case tests for exclude functionality."""

    def test_exclude_case_insensitive(self, exclude_export_file: Path) -> None:
        """Exclude matching is case-insensitive."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], exclude_keywords=["DJANGO"])

        results = list(adapter.search(exclude_export_file, query))

        result_ids = [r.conversation.id for r in results]
        assert "conv-python-django" not in result_ids
        assert len(results) == 2

    def test_exclude_with_match_mode_all(self, exclude_export_file: Path) -> None:
        """Exclude works with match_mode='all'."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python", "framework"],
            match_mode="all",
            exclude_keywords=["django"],
        )

        results = list(adapter.search(exclude_export_file, query))

        # All Python framework conversations except Django
        result_ids = [r.conversation.id for r in results]
        assert "conv-python-django" not in result_ids

    def test_exclude_with_phrases(self, exclude_export_file: Path) -> None:
        """Exclude works with phrase matching."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            phrases=["web framework"],
            exclude_keywords=["django"],
        )

        results = list(adapter.search(exclude_export_file, query))

        # Should find flask and fastapi (have "web framework") but not django
        result_ids = [r.conversation.id for r in results]
        assert "conv-python-django" not in result_ids
        # Flask and FastAPI mention "web framework"
        assert len(results) >= 1

    def test_empty_exclude_returns_all_matches(
        self, exclude_export_file: Path
    ) -> None:
        """Empty exclude_keywords returns all matching results."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], exclude_keywords=[])

        results = list(adapter.search(exclude_export_file, query))

        # All Python conversations returned
        assert len(results) == 3
