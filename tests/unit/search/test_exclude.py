"""Unit tests for exclude_filter() functionality.

Tests for FR-012-016: Exclude keywords filtering.

TDD: These tests are written FIRST and should FAIL until T034
implements the exclude_filter() function.
"""

from __future__ import annotations

from echomine.search.ranking import BM25Scorer, exclude_filter


class TestExcludeFilterBasic:
    """Basic exclude_filter() functionality."""

    def test_exclude_term_found(self) -> None:
        """Returns True (exclude) when excluded term is found."""
        text = "I use Django for web development"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=6.0)
        assert exclude_filter(text, ["django"], scorer) is True

    def test_exclude_term_not_found(self) -> None:
        """Returns False (keep) when excluded term is not found."""
        text = "I use Flask for web development"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=6.0)
        assert exclude_filter(text, ["django"], scorer) is False

    def test_exclude_any_of_multiple(self) -> None:
        """Returns True if ANY excluded term is found (OR logic)."""
        text = "I use Django and React"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert exclude_filter(text, ["angular", "django"], scorer) is True

    def test_exclude_none_of_multiple(self) -> None:
        """Returns False when NONE of the excluded terms are found."""
        text = "I use Flask and Vue"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert exclude_filter(text, ["django", "angular"], scorer) is False

    def test_empty_exclude_list(self) -> None:
        """Returns False (keep all) when exclude list is empty."""
        text = "Any text here"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=3.0)
        assert exclude_filter(text, [], scorer) is False


class TestExcludeFilterCaseSensitivity:
    """Case-insensitive matching for exclude_filter()."""

    def test_lowercase_exclude_matches_uppercase_text(self) -> None:
        """Lowercase excluded term matches uppercase text."""
        text = "I use DJANGO for development"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert exclude_filter(text, ["django"], scorer) is True

    def test_uppercase_exclude_matches_lowercase_text(self) -> None:
        """Uppercase excluded term matches lowercase text."""
        text = "I use django for development"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert exclude_filter(text, ["DJANGO"], scorer) is True

    def test_mixed_case_matches(self) -> None:
        """Mixed case variations match correctly."""
        text = "Django is a web framework"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        assert exclude_filter(text, ["dJaNgO"], scorer) is True


class TestExcludeFilterTokenization:
    """Tokenization behavior for exclude_filter()."""

    def test_uses_same_tokenization_as_bm25(self) -> None:
        """Uses same tokenization as BM25Scorer for consistency."""
        text = "Python's django-framework is popular"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # "django-framework" tokenizes to "django" + "framework"
        assert exclude_filter(text, ["django"], scorer) is True

    def test_multi_word_exclude_tokenized(self) -> None:
        """Multi-word exclusions are tokenized into individual tokens."""
        text = "Python is a programming language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # "python programming" -> ["python", "programming"]
        # If EITHER token is present, exclude
        assert exclude_filter(text, ["python programming"], scorer) is True

    def test_unicode_exclude(self) -> None:
        """Unicode exclusions work correctly."""
        text = "Python 编程 language"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # Chinese characters are tokenized individually
        assert exclude_filter(text, ["编"], scorer) is True


class TestExcludeFilterEdgeCases:
    """Edge cases for exclude_filter()."""

    def test_empty_text_returns_false(self) -> None:
        """Empty text never matches exclusions (keep empty)."""
        scorer = BM25Scorer(corpus=["test"], avg_doc_length=5.0)
        assert exclude_filter("", ["python"], scorer) is False

    def test_empty_text_empty_exclude(self) -> None:
        """Empty text with empty exclusions returns False (keep)."""
        scorer = BM25Scorer(corpus=["test"], avg_doc_length=5.0)
        assert exclude_filter("", [], scorer) is False

    def test_duplicate_exclusions(self) -> None:
        """Duplicate exclusions are handled correctly."""
        text = "Python is great"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=3.0)
        assert exclude_filter(text, ["python", "python"], scorer) is True

    def test_token_must_match_exactly(self) -> None:
        """Exclusion tokens must match tokenization boundaries."""
        text = "programming"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=1.0)
        # "prog" should not match "programming" at token level
        assert exclude_filter(text, ["prog"], scorer) is False
        # But "programming" should match
        assert exclude_filter(text, ["programming"], scorer) is True


class TestExcludeFilterIntegration:
    """Integration tests combining exclude with other features."""

    def test_exclude_with_matching_content(self) -> None:
        """Exclude should work after content matching."""
        # Text matches search keywords but should be excluded
        text = "Python Django tutorial for beginners"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=5.0)
        # Would match "python tutorial" but should be excluded due to "django"
        assert exclude_filter(text, ["django"], scorer) is True

    def test_exclude_does_not_affect_non_matching(self) -> None:
        """Exclude returns False for content without excluded terms."""
        text = "Flask tutorial for beginners"
        scorer = BM25Scorer(corpus=[text], avg_doc_length=4.0)
        assert exclude_filter(text, ["django"], scorer) is False
