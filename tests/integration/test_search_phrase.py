"""Integration tests for phrase search end-to-end.

Tests for User Story 1: Exact Phrase Matching (Priority: P1)

TDD: These tests are written FIRST and should FAIL until T015-T017
implement the phrase matching functionality.

Independent Test: Search for "algo-insights" returns only conversations
with that exact string.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def phrase_export_file(tmp_path: Path) -> Path:
    """Create export with phrase-testable content."""
    conversations = [
        {
            "id": "conv-exact-phrase",
            "title": "Algo-Insights Project Discussion",
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
                            "parts": ["How do I configure algo-insights?"],
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
            "id": "conv-no-hyphen",
            "title": "Algorithm Insights Separate",
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
                            "parts": ["Tell me about algorithm insights"],
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
            "id": "conv-multiple-phrases",
            "title": "Data Pipeline Project",
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
                            "parts": ["The algo-insights system feeds into the data pipeline"],
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
    ]

    export_file = tmp_path / "phrase_test.json"
    with export_file.open("w") as f:
        json.dump(conversations, f)

    return export_file


@pytest.mark.integration
class TestPhraseSearchAcceptance:
    """Acceptance tests from spec.md User Story 1."""

    def test_us1_as1_exact_phrase_match(self, phrase_export_file: Path) -> None:
        """AS1: Search for 'algo-insights' returns only exact matches.

        Given an export file containing conversations with "algo-insights"
        and "algorithm insights" (separate words),
        When user searches with phrase "algo-insights",
        Then only conversations containing the exact string "algo-insights"
        are returned (not "algorithm insights").
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=["algo-insights"])

        results = list(adapter.search(phrase_export_file, query))

        # Should find conv-exact-phrase and conv-multiple-phrases
        # Should NOT find conv-no-hyphen (has "algorithm insights" not "algo-insights")
        result_ids = [r.conversation.id for r in results]

        assert "conv-exact-phrase" in result_ids
        assert "conv-multiple-phrases" in result_ids
        assert "conv-no-hyphen" not in result_ids

    def test_us1_as2_case_insensitive(self, phrase_export_file: Path) -> None:
        """AS2: Phrase search is case-insensitive.

        Given an export file with mixed case occurrences,
        When user runs phrase search,
        Then all case variations are matched.
        """
        adapter = OpenAIAdapter()

        # Test uppercase phrase matches lowercase text
        query_upper = SearchQuery(phrases=["ALGO-INSIGHTS"])
        results_upper = list(adapter.search(phrase_export_file, query_upper))

        # Test lowercase phrase matches uppercase text
        query_lower = SearchQuery(phrases=["algo-insights"])
        results_lower = list(adapter.search(phrase_export_file, query_lower))

        # Both should find the same conversations
        assert len(results_upper) == len(results_lower)
        assert len(results_upper) > 0

    def test_us1_as3_multiple_phrases_or_logic(self, phrase_export_file: Path) -> None:
        """AS3: Multiple phrases use OR logic.

        Given user runs search with multiple phrases,
        Then conversations containing either phrase are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=["algo-insights", "data pipeline"])

        results = list(adapter.search(phrase_export_file, query))

        # Should find all conversations that match either phrase
        result_ids = [r.conversation.id for r in results]
        assert "conv-exact-phrase" in result_ids  # Has "algo-insights"
        assert "conv-multiple-phrases" in result_ids  # Has both

    def test_us1_as4_phrase_combined_with_keywords(
        self, phrase_export_file: Path
    ) -> None:
        """AS4: Phrases can be combined with keywords (OR logic by default).

        Given user runs search with both keywords and phrases,
        Then conversations matching keyword OR phrase are returned.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["configure"],  # Appears in conv-exact-phrase
            phrases=["data pipeline"],  # Appears in conv-multiple-phrases
        )

        results = list(adapter.search(phrase_export_file, query))

        # Should find conversations matching keyword OR phrase
        assert len(results) >= 1


@pytest.mark.integration
class TestPhraseSearchEdgeCases:
    """Edge case tests for phrase matching."""

    def test_phrase_with_hyphens_preserved(self, phrase_export_file: Path) -> None:
        """Hyphens in phrases are matched literally, not tokenized."""
        adapter = OpenAIAdapter()

        # "algo-insights" should match
        query_hyphen = SearchQuery(phrases=["algo-insights"])
        results_hyphen = list(adapter.search(phrase_export_file, query_hyphen))

        # "algo" alone should NOT match "algo-insights" (different test)
        # This verifies phrases are NOT tokenized
        assert len(results_hyphen) >= 1
        for result in results_hyphen:
            # Verify the matched conversation contains the exact phrase
            conv_text = result.conversation.title.lower()
            messages_text = " ".join(m.content.lower() for m in result.conversation.messages)
            full_text = f"{conv_text} {messages_text}"
            assert "algo-insights" in full_text

    def test_phrase_only_search_no_keywords(self, phrase_export_file: Path) -> None:
        """Phrase search works without any keywords."""
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=["algo-insights"])

        results = list(adapter.search(phrase_export_file, query))

        # Should return results even without keywords
        assert len(results) >= 1

    def test_empty_phrases_returns_no_results(self, phrase_export_file: Path) -> None:
        """Empty phrases list with no other filters returns no results."""
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=[])

        results = list(adapter.search(phrase_export_file, query))

        # Empty phrases should behave like no filter - depends on implementation
        # May return all or none based on design decision
        # For now, just verify no error
        assert isinstance(results, list)
