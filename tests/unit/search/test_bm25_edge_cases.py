"""Unit tests for BM25 edge cases.

Tests for BM25 scorer handling of edge cases that could cause errors,
particularly division by zero scenarios.

Bug Reference:
    - Role filter with very sparse "system" messages causes division by zero
    - When avg_doc_length is 0, BM25 score calculation fails
"""

from __future__ import annotations

from echomine.search.ranking import BM25Scorer


class TestBM25ZeroAvgDocLength:
    """Test BM25 scorer behavior when avg_doc_length is zero."""

    def test_zero_avg_doc_length_does_not_raise_error(self) -> None:
        """BM25 scorer should handle zero avg_doc_length without ZeroDivisionError.

        This is a regression test for the bug where searching with --role system
        on data with sparse/empty system messages caused 'float division by zero'.
        """
        # Create corpus with empty documents (simulates filtered system messages)
        corpus = ["", "", ""]

        # avg_doc_length = 0 when all documents are empty
        avg_doc_length = 0.0

        # This should not raise an error
        scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_doc_length)

        # Scoring should not raise ZeroDivisionError
        score = scorer.score("some content to score", ["some"])

        # Score should be a valid number (not NaN or Inf)
        assert score >= 0.0
        import math

        assert not math.isnan(score)
        assert not math.isinf(score)

    def test_zero_avg_doc_length_with_matching_keywords(self) -> None:
        """Score calculation works with zero avg_doc_length and matching keywords."""
        corpus = ["python", ""]  # One non-empty, one empty
        avg_doc_length = 0.0  # Edge case: pretend avg is zero

        scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_doc_length)

        # Should not raise
        score = scorer.score("python programming", ["python"])

        assert score >= 0.0

    def test_empty_corpus_with_zero_avg(self) -> None:
        """Empty corpus with zero avg_doc_length is handled gracefully."""
        corpus: list[str] = []
        avg_doc_length = 0.0

        scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_doc_length)

        # Should not raise even with empty corpus
        score = scorer.score("some content", ["keyword"])

        assert score >= 0.0


class TestBM25SparseCorpus:
    """Test BM25 with sparse corpus scenarios (few tokens)."""

    def test_corpus_with_only_punctuation(self) -> None:
        """Corpus with only punctuation (no tokenizable content) doesn't crash."""
        # Content that tokenizes to zero tokens
        corpus = ["!!!", "???", "..."]

        # This would result in zero tokens, so avg would be 0
        avg_doc_length = 0.0

        scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_doc_length)
        score = scorer.score("hello world", ["hello"])

        assert score >= 0.0

    def test_corpus_with_special_characters_only(self) -> None:
        """Corpus with only special characters is handled."""
        corpus = ["@#$%^&", "!!!", ""]
        avg_doc_length = 0.0

        scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_doc_length)
        score = scorer.score("test", ["test"])

        assert score >= 0.0
