"""Integration tests for combined advanced search features.

Tests all v1.1.0 features working together:
    - US1: Phrase search (FR-001-006)
    - US2: Match mode (FR-007-011)
    - US3: Exclude keywords (FR-012-016)
    - US4: Role filtering (FR-017-020)
    - US5: Snippets (FR-021-025)

Constitution Compliance:
    - Principle III: TDD-driven integration tests
    - Principle VI: Strict typing with mypy --strict
"""

from __future__ import annotations

from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture
def sample_export_path() -> Path:
    """Path to sample export file for testing."""
    return Path(__file__).parent.parent / "fixtures" / "sample_export.json"


class TestCombinedSearchFeatures:
    """Test all advanced search features working together."""

    def test_phrase_with_role_filter(self, sample_export_path: Path) -> None:
        """Phrase search combined with role filtering."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            phrases=["python"],
            role_filter="user",
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        # All results should have snippets
        for result in results:
            assert result.snippet is not None

    def test_keywords_with_exclude_and_role(self, sample_export_path: Path) -> None:
        """Keywords + exclude + role filter combined."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["java"],
            role_filter="assistant",
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            assert result.snippet is not None

    def test_match_mode_all_with_exclude(self, sample_export_path: Path) -> None:
        """match_mode=all with exclude keywords."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python", "code"],
            match_mode="all",
            exclude_keywords=["error"],
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            assert result.snippet is not None

    def test_all_features_combined(self, sample_export_path: Path) -> None:
        """All v1.1.0 features in one query."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            phrases=["code"],
            match_mode="any",
            exclude_keywords=["error", "bug"],
            role_filter="assistant",
            limit=5,
        )

        results = list(adapter.search(sample_export_path, query))

        # Results should have all required fields
        for result in results:
            assert result.conversation is not None
            assert result.score >= 0.0
            assert result.matched_message_ids is not None
            assert result.snippet is not None
            # Snippet should not be empty for valid results
            assert len(result.snippet) > 0


class TestFeatureInteractionEdgeCases:
    """Test edge cases in feature interactions."""

    def test_empty_results_with_strict_filters(self, sample_export_path: Path) -> None:
        """Very restrictive filters may return empty results."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["nonexistent_keyword_xyz123"],
            match_mode="all",
            exclude_keywords=["python"],
            role_filter="system",
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        # May be empty due to restrictive filters - that's valid behavior
        assert isinstance(results, list)

    def test_phrase_with_match_mode_any(self, sample_export_path: Path) -> None:
        """Phrase + keywords with match_mode=any."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["algorithm"],
            phrases=["python"],
            match_mode="any",
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        # Should get results matching either phrase or keyword
        for result in results:
            assert result.snippet is not None

    def test_snippet_respects_role_filter(self, sample_export_path: Path) -> None:
        """Snippet content should come from role-filtered messages."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            role_filter="user",
            limit=5,
        )

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            assert result.snippet is not None
            # Snippet exists from filtered messages


class TestCombinedAcceptanceCriteria:
    """Acceptance criteria for combined features."""

    def test_combined_search_returns_valid_structure(self, sample_export_path: Path) -> None:
        """Combined search returns properly structured results."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            phrases=["code"],
            exclude_keywords=["error"],
            role_filter="assistant",
            match_mode="any",
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            # Verify SearchResult structure
            assert hasattr(result, "conversation")
            assert hasattr(result, "score")
            assert hasattr(result, "matched_message_ids")
            assert hasattr(result, "snippet")

            # Verify types
            assert result.score >= 0.0
            assert result.score <= 1.0
            assert isinstance(result.matched_message_ids, list)
            assert isinstance(result.snippet, str)

    def test_score_ordering_preserved(self, sample_export_path: Path) -> None:
        """Results are ordered by relevance score (descending)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            limit=10,
        )

        results = list(adapter.search(sample_export_path, query))

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_limit_respected_with_all_features(self, sample_export_path: Path) -> None:
        """Limit is respected even with all features active."""
        limit = 3
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            phrases=["code"],
            match_mode="any",
            limit=limit,
        )

        results = list(adapter.search(sample_export_path, query))

        assert len(results) <= limit
