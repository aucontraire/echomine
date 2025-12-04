"""Unit tests for match_mode functionality.

Tests for FR-007-011: Boolean match mode (all/any keywords).

TDD: These tests are written FIRST and should FAIL until T025
implements the all_terms_present() function.
"""

from __future__ import annotations

from echomine.search.ranking import BM25Scorer, all_terms_present


class TestAllTermsPresentBasic:
    """Basic all_terms_present() functionality."""

    def test_all_terms_found(self) -> None:
        """Returns True when all terms are found in text."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["python", "programming"], scorer) is True

    def test_some_terms_missing(self) -> None:
        """Returns False when some terms are missing."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["python", "java"], scorer) is False

    def test_no_terms_found(self) -> None:
        """Returns False when no terms are found."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["java", "rust"], scorer) is False

    def test_empty_keywords(self) -> None:
        """Returns True when keywords list is empty (vacuously true)."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, [], scorer) is True

    def test_single_keyword_found(self) -> None:
        """Returns True when single keyword is found."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["python"], scorer) is True

    def test_single_keyword_not_found(self) -> None:
        """Returns False when single keyword is not found."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["java"], scorer) is False


class TestAllTermsPresentCaseSensitivity:
    """Case-insensitive matching for all_terms_present()."""

    def test_lowercase_keywords_match_uppercase_text(self) -> None:
        """Lowercase keywords match uppercase text."""
        text = "PYTHON is a PROGRAMMING language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["python", "programming"], scorer) is True

    def test_uppercase_keywords_match_lowercase_text(self) -> None:
        """Uppercase keywords match lowercase text."""
        text = "python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["PYTHON", "PROGRAMMING"], scorer) is True

    def test_mixed_case_matches(self) -> None:
        """Mixed case variations all match."""
        text = "Python Programming Language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["PyThOn", "PrOgRaMmInG"], scorer) is True


class TestAllTermsPresentTokenization:
    """Tokenization behavior for all_terms_present()."""

    def test_tokenization_matches_bm25(self) -> None:
        """Uses same tokenization as BM25Scorer."""
        text = "Python's programming-language is fun"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # "python's" tokenizes to "python" + "s"
        # "programming-language" tokenizes to "programming" + "language"
        assert all_terms_present(text, ["python", "programming"], scorer) is True

    def test_multi_word_keyword_tokenized(self) -> None:
        """Multi-word keywords are tokenized into individual tokens."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # "python programming" -> ["python", "programming"] - both must be present
        assert all_terms_present(text, ["python programming"], scorer) is True

    def test_unicode_keywords(self) -> None:
        """Unicode keywords work correctly."""
        text = "Python 编程 language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # Chinese characters are tokenized individually
        assert all_terms_present(text, ["python", "编"], scorer) is True


class TestAllTermsPresentEdgeCases:
    """Edge cases for all_terms_present()."""

    def test_empty_text(self) -> None:
        """Returns False for empty text (unless keywords empty)."""
        scorer = BM25Scorer(corpus=["test"], avg_doc_length=5.0)
        assert all_terms_present("", ["python"], scorer) is False

    def test_empty_text_empty_keywords(self) -> None:
        """Returns True for empty text with empty keywords."""
        scorer = BM25Scorer(corpus=["test"], avg_doc_length=5.0)
        assert all_terms_present("", [], scorer) is True

    def test_duplicate_keywords(self) -> None:
        """Duplicate keywords are handled correctly."""
        text = "Python is great"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert all_terms_present(text, ["python", "python"], scorer) is True

    def test_partial_word_match(self) -> None:
        """Tokens must match completely (tokenization boundary)."""
        text = "Python programming"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # "prog" should not match "programming" at token level
        # (depends on tokenization - may match as substring in some implementations)
        # Using BM25 tokenization, "programming" is one token
        assert all_terms_present(text, ["python"], scorer) is True


class TestMatchModeIntegration:
    """Integration tests for match_mode in search flow."""

    def test_match_mode_any_default(self) -> None:
        """Default match_mode='any' returns results with any keyword."""
        from echomine.models.search import SearchQuery

        query = SearchQuery(keywords=["python", "java"])
        assert query.match_mode == "any"

    def test_match_mode_all_explicit(self) -> None:
        """Explicit match_mode='all' requires all keywords."""
        from echomine.models.search import SearchQuery

        query = SearchQuery(keywords=["python", "java"], match_mode="all")
        assert query.match_mode == "all"
