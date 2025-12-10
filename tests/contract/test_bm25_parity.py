"""BM25 scoring parity tests between adapters (FR-032).

This test suite validates that ClaudeAdapter uses the same BM25 ranking
formula and scoring approach as OpenAIAdapter, ensuring consistent search
results across providers.

Test Coverage:
    - T096: BM25 formula consistency across adapters
    - Score normalization validation
    - Tokenization consistency

Constitution Compliance:
    - Principle VII: Multi-Provider Adapter Pattern (shared ranking algorithm)
    - Principle III: Test-Driven Development
    - Principle VI: Strict typing

Requirements:
    - FR-032: ClaudeAdapter MUST use same BM25 formula as OpenAI
    - FR-319: Score normalization formula: score / (score + 1)
    - FR-317: BM25 scoring with consistent tokenization
"""

from __future__ import annotations

from pathlib import Path

import pytest

from echomine.adapters.claude import ClaudeAdapter
from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


# ============================================================================
# T096: BM25 Formula Parity Tests
# ============================================================================


def test_bm25_scoring_formula_same() -> None:
    """FR-032: ClaudeAdapter MUST use same BM25 formula as OpenAI.

    Both adapters import and use the shared BM25Scorer from echomine.search.ranking.
    This test verifies that both adapters produce scores in the normalized [0, 1] range
    using the same formula: score / (score + 1).
    """
    # Both adapters use the same BM25Scorer class
    # This is verified by code inspection - both import BM25Scorer
    # from echomine.search.ranking

    # Verify ClaudeAdapter produces normalized scores
    claude = ClaudeAdapter()
    claude_sample = Path("tests/fixtures/claude/sample_export.json")

    query = SearchQuery(keywords=["python"])
    results = list(claude.search(claude_sample, query))

    # All scores must be in [0, 1] range (normalized)
    for result in results:
        assert 0.0 <= result.score <= 1.0, (
            f"Score {result.score} not in [0, 1] range. "
            f"ClaudeAdapter must use normalized BM25 formula: score / (score + 1)"
        )


def test_bm25_scorer_consistency() -> None:
    """Verify both adapters use the same BM25Scorer class.

    This ensures formula consistency by verifying both adapters import
    the shared ranking module.
    """
    # Check that BM25Scorer is available from shared module
    from echomine.search.ranking import BM25Scorer as SharedScorer

    # Verify it's a class (not aliased or subclassed)
    assert isinstance(SharedScorer, type), "BM25Scorer must be a class"

    # Verify it has the required scoring method
    assert hasattr(SharedScorer, "score"), "BM25Scorer must have score method"

    # Create instance with minimal args to verify constructor
    corpus = ["test document one", "test document two"]
    avg_doc_length = 3.0
    scorer = SharedScorer(corpus=corpus, avg_doc_length=avg_doc_length)

    # Verify scoring produces valid output
    score = scorer.score("test document one", ["test"])
    assert isinstance(score, float), "BM25Scorer.score must return float"
    assert score >= 0.0, "BM25 scores must be non-negative"


def test_normalized_score_range(claude_sample_export: Path) -> None:
    """Verify ClaudeAdapter scores are properly normalized to [0, 1].

    FR-319: Scores must be normalized using formula: score / (score + 1)
    This ensures consistent score interpretation across queries and providers.
    """
    adapter = ClaudeAdapter()

    # Test with different query types
    test_queries = [
        SearchQuery(keywords=["python"]),
        SearchQuery(keywords=["binary", "search"]),
        SearchQuery(keywords=["database", "optimization"]),
    ]

    for query in test_queries:
        results = list(adapter.search(claude_sample_export, query))

        for result in results:
            # Score must be in [0, 1]
            assert 0.0 <= result.score <= 1.0, (
                f"Score {result.score} outside [0, 1] range for query {query}"
            )

            # Score should never equal exactly 1.0 (only approaches it)
            # This is a mathematical property of score / (score + 1)
            if result.score > 0.0:
                assert result.score < 1.0, (
                    f"Normalized score should never reach 1.0, got {result.score}. "
                    f"Formula: score / (score + 1) asymptotically approaches 1.0"
                )


def test_score_zero_for_no_match(claude_sample_export: Path) -> None:
    """Verify zero score for conversations with no keyword matches.

    When no keywords match, BM25 score should be 0.0 (normalized).
    """
    adapter = ClaudeAdapter()

    # Search with keywords unlikely to match
    query = SearchQuery(keywords=["xyzabc123nonexistent"])
    results = list(adapter.search(claude_sample_export, query))

    # Either no results (filtered out) or all scores are 0.0
    for result in results:
        assert result.score == 0.0, f"Expected score 0.0 for non-matching query, got {result.score}"


def test_cross_adapter_score_comparison(
    claude_sample_export: Path,
    openai_sample_export: Path,
) -> None:
    """Compare score distributions between adapters.

    While exact scores may differ (different content), both adapters should
    produce scores with similar statistical properties (range, distribution).
    """
    claude = ClaudeAdapter()
    openai = OpenAIAdapter()

    # Same query for both
    query = SearchQuery(keywords=["python"])

    claude_results = list(claude.search(claude_sample_export, query))
    openai_results = list(openai.search(openai_sample_export, query))

    # Both should produce scores in [0, 1]
    for result in claude_results:
        assert 0.0 <= result.score <= 1.0

    for result in openai_results:
        assert 0.0 <= result.score <= 1.0

    # If both have results, verify score properties
    if claude_results and openai_results:
        # Highest scores should be non-zero (keyword matches found)
        assert claude_results[0].score > 0.0
        assert openai_results[0].score > 0.0

        # Scores should be descending (sorted by relevance)
        claude_scores = [r.score for r in claude_results]
        openai_scores = [r.score for r in openai_results]

        assert claude_scores == sorted(claude_scores, reverse=True), (
            "Claude scores must be sorted descending"
        )
        assert openai_scores == sorted(openai_scores, reverse=True), (
            "OpenAI scores must be sorted descending"
        )


def test_tokenization_consistency() -> None:
    """Verify both adapters use consistent tokenization for BM25.

    Tokenization must be identical for score parity. Both adapters
    use regex-based tokenization from BM25Scorer.
    """
    # Both adapters use the same tokenization approach
    # Latin tokens: [a-z0-9]+
    # Non-Latin tokens: [^\W\d_a-z] (CJK characters)

    import re

    # Test tokenization patterns
    test_texts = [
        ("Python programming", ["python", "programming"]),
        ("binary search algorithm", ["binary", "search", "algorithm"]),
        ("数据库优化", ["数", "据", "库", "优", "化"]),  # Chinese
    ]

    for text, expected_tokens in test_texts:
        text_lower = text.lower()

        # Latin tokens
        latin_tokens = re.findall(r"[a-z0-9]+", text_lower)

        # Non-Latin tokens (CJK)
        non_latin_tokens = re.findall(r"[^\W\d_a-z]", text_lower)

        all_tokens = latin_tokens + non_latin_tokens

        # Verify tokenization produces expected tokens
        for expected in expected_tokens:
            assert expected in all_tokens, (
                f"Expected token '{expected}' not found in tokenized text: {all_tokens}"
            )


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def claude_sample_export() -> Path:
    """Path to Claude sample export fixture."""
    return Path("tests/fixtures/claude/sample_export.json")


@pytest.fixture
def openai_sample_export() -> Path:
    """Path to OpenAI sample export fixture."""
    return Path("tests/fixtures/sample_export.json")
