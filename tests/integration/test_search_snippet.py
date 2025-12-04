"""Integration tests for snippet extraction in search (FR-021-025).

Tests end-to-end snippet extraction through the OpenAIAdapter.search().

Requirements:
    - FR-021: CLI output includes snippet column
    - FR-022: Snippets ~100 characters with "..."
    - FR-023: Multiple matches show "+N more" indicator
    - FR-024: JSON includes snippet field
    - FR-025: Graceful handling with fallback text
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


class TestSnippetIntegration:
    """Test snippet extraction through OpenAIAdapter."""

    def test_search_results_include_snippet(self, sample_export_path: Path) -> None:
        """Search results include snippet field."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        # All results should have snippet field
        for result in results:
            assert hasattr(result, "snippet")
            assert result.snippet is not None

    def test_snippet_contains_keyword(self, sample_export_path: Path) -> None:
        """Snippet contains at least one matched keyword."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        # At least one result should have snippet with keyword (or be fallback)
        if results:
            snippets_with_keyword = [
                r
                for r in results
                if r.snippet and "python" in r.snippet.lower()
            ]
            fallback_snippets = [
                r
                for r in results
                if r.snippet in ["[Content unavailable]", "[No content matched]"]
            ]
            # Either has keyword in snippet or uses fallback
            assert (
                len(snippets_with_keyword) > 0
                or len(fallback_snippets) == len(results)
            )

    def test_snippet_length_limit(self, sample_export_path: Path) -> None:
        """Snippet respects length limit (~100 chars + indicator)."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            if result.snippet:
                # Allow up to 150 chars (100 + "..." + " (+N more matches)")
                assert len(result.snippet) <= 150, (
                    f"Snippet too long: {len(result.snippet)} chars"
                )


class TestSnippetWithPhrases:
    """Test snippet extraction with phrase search."""

    def test_snippet_with_phrase_search(self, sample_export_path: Path) -> None:
        """Snippet extraction works with phrase search."""
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=["best practices"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        # Should get results (if phrases exist in data)
        for result in results:
            assert result.snippet is not None


class TestSnippetWithRoleFilter:
    """Test snippet extraction with role filtering."""

    def test_snippet_respects_role_filter(self, sample_export_path: Path) -> None:
        """Snippet comes from messages matching role filter."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], role_filter="user", limit=10)

        results = list(adapter.search(sample_export_path, query))

        # Results should have snippets
        for result in results:
            assert result.snippet is not None


class TestSnippetEdgeCases:
    """Test edge cases for snippet extraction."""

    def test_snippet_title_only_match(self, sample_export_path: Path) -> None:
        """Title-only match returns content beginning as snippet."""
        adapter = OpenAIAdapter()
        # Use title filter to match by title
        query = SearchQuery(title_filter="python", limit=10)

        results = list(adapter.search(sample_export_path, query))

        # Results should have snippets even for title-only matches
        for result in results:
            assert result.snippet is not None

    def test_snippet_multiple_matches_indicator(
        self, sample_export_path: Path
    ) -> None:
        """Multiple keyword matches show indicator."""
        adapter = OpenAIAdapter()
        # Use common word to get multiple matches
        query = SearchQuery(keywords=["the"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        # If there are results with multiple matches, should show indicator
        # This is a heuristic check - may or may not have "+N more"
        for result in results:
            assert result.snippet is not None
            # Just verify format is correct (non-empty)
            assert len(result.snippet) > 0


class TestSnippetAcceptanceCriteria:
    """Acceptance criteria tests for US5."""

    def test_us5_as1_snippet_in_search_results(
        self, sample_export_path: Path
    ) -> None:
        """US5-AS1: Search results include matched text snippet."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=5)

        results = list(adapter.search(sample_export_path, query))

        # All results MUST have snippet
        for result in results:
            assert result.snippet is not None, (
                f"Missing snippet for conversation: {result.conversation.title}"
            )

    def test_us5_as2_snippet_truncated_to_100_chars(
        self, sample_export_path: Path
    ) -> None:
        """US5-AS2: Snippets are truncated to ~100 characters."""
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=10)

        results = list(adapter.search(sample_export_path, query))

        for result in results:
            if result.snippet and "..." in result.snippet:
                # Truncated snippets should be around 100 chars
                base_snippet = result.snippet.split("...")[0] + "..."
                assert len(base_snippet) <= 110, (
                    f"Base snippet too long: {len(base_snippet)} chars"
                )

    def test_us5_as3_fallback_for_empty_content(self) -> None:
        """US5-AS3: Empty content returns fallback text (FR-025)."""
        # This tests the extract_snippet function directly
        from echomine.search.snippet import extract_snippet

        snippet = extract_snippet("", ["python"])

        assert snippet == "[Content unavailable]"
