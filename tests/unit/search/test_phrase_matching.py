"""Unit tests for phrase_matches() function.

Tests for FR-001-006: Exact phrase matching functionality.

TDD: These tests are written FIRST and should FAIL until T015 implements
the phrase_matches() function.
"""

from __future__ import annotations

from echomine.search.ranking import phrase_matches


class TestPhraseMatchesBasic:
    """Basic phrase matching functionality."""

    def test_single_phrase_match(self) -> None:
        """Single phrase found in text returns True."""
        text = "We use algo-insights for data analysis"
        assert phrase_matches(text, ["algo-insights"]) is True

    def test_single_phrase_no_match(self) -> None:
        """Single phrase not found returns False."""
        text = "We use algorithm insights for data analysis"
        assert phrase_matches(text, ["algo-insights"]) is False

    def test_empty_phrases_list(self) -> None:
        """Empty phrases list returns False (no matches possible)."""
        text = "Any text content here"
        assert phrase_matches(text, []) is False

    def test_empty_text(self) -> None:
        """Empty text returns False for any phrase."""
        assert phrase_matches("", ["algo-insights"]) is False


class TestPhraseMatchesCaseSensitivity:
    """FR-003: Case-insensitive phrase matching."""

    def test_lowercase_phrase_matches_uppercase_text(self) -> None:
        """Lowercase phrase matches uppercase text."""
        text = "We use ALGO-INSIGHTS for analysis"
        assert phrase_matches(text, ["algo-insights"]) is True

    def test_uppercase_phrase_matches_lowercase_text(self) -> None:
        """Uppercase phrase matches lowercase text."""
        text = "We use algo-insights for analysis"
        assert phrase_matches(text, ["ALGO-INSIGHTS"]) is True

    def test_mixed_case_matches(self) -> None:
        """Mixed case variations all match."""
        text = "We use Algo-Insights for analysis"
        assert phrase_matches(text, ["algo-insights"]) is True
        assert phrase_matches(text, ["ALGO-INSIGHTS"]) is True
        assert phrase_matches(text, ["Algo-Insights"]) is True


class TestPhraseMatchesSpecialCharacters:
    """FR-006: Special characters matched literally."""

    def test_hyphenated_phrase(self) -> None:
        """Hyphens in phrases are matched literally."""
        text = "The algo-insights project is complete"
        assert phrase_matches(text, ["algo-insights"]) is True
        # Should NOT match if text has no hyphen
        text_no_hyphen = "The algo insights project is complete"
        assert phrase_matches(text_no_hyphen, ["algo-insights"]) is False

    def test_underscored_phrase(self) -> None:
        """Underscores in phrases are matched literally."""
        text = "Use the data_pipeline module"
        assert phrase_matches(text, ["data_pipeline"]) is True
        text_no_underscore = "Use the data pipeline module"
        assert phrase_matches(text_no_underscore, ["data_pipeline"]) is False

    def test_dotted_phrase(self) -> None:
        """Dots in phrases are matched literally."""
        text = "Import from utils.helpers module"
        assert phrase_matches(text, ["utils.helpers"]) is True

    def test_phrase_with_spaces(self) -> None:
        """Spaces in phrases are matched literally."""
        text = "The quick brown fox jumps"
        assert phrase_matches(text, ["quick brown"]) is True
        assert phrase_matches(text, ["quickbrown"]) is False


class TestPhraseMatchesMultiplePhrases:
    """FR-002: Multiple phrases (OR logic)."""

    def test_multiple_phrases_first_matches(self) -> None:
        """First phrase matches, returns True."""
        text = "We use algo-insights for analysis"
        assert phrase_matches(text, ["algo-insights", "data pipeline"]) is True

    def test_multiple_phrases_second_matches(self) -> None:
        """Second phrase matches, returns True."""
        text = "We use data pipeline for analysis"
        assert phrase_matches(text, ["algo-insights", "data pipeline"]) is True

    def test_multiple_phrases_both_match(self) -> None:
        """Both phrases match, returns True."""
        text = "We use algo-insights and data pipeline"
        assert phrase_matches(text, ["algo-insights", "data pipeline"]) is True

    def test_multiple_phrases_none_match(self) -> None:
        """No phrases match, returns False."""
        text = "We use different tools for analysis"
        assert phrase_matches(text, ["algo-insights", "data pipeline"]) is False


class TestPhraseMatchesEdgeCases:
    """Edge cases from spec.md."""

    def test_phrase_only_special_characters(self) -> None:
        """Phrase with only special characters (e.g., '---')."""
        text = "Line 1 --- Line 2"
        assert phrase_matches(text, ["---"]) is True
        text_no_match = "Line 1 - Line 2"
        assert phrase_matches(text_no_match, ["---"]) is False

    def test_phrase_substring_of_word(self) -> None:
        """Phrase matches as substring (per spec edge case)."""
        # From spec: 'log' WILL match in 'catalog' (substring matching)
        text = "Check the catalog for items"
        assert phrase_matches(text, ["log"]) is True

    def test_phrase_at_start_of_text(self) -> None:
        """Phrase at the start of text matches."""
        text = "algo-insights is our main tool"
        assert phrase_matches(text, ["algo-insights"]) is True

    def test_phrase_at_end_of_text(self) -> None:
        """Phrase at the end of text matches."""
        text = "We rely on algo-insights"
        assert phrase_matches(text, ["algo-insights"]) is True

    def test_phrase_with_newlines(self) -> None:
        """Phrase matching across text with newlines."""
        text = "Line 1\nalgo-insights\nLine 3"
        assert phrase_matches(text, ["algo-insights"]) is True

    def test_unicode_phrase(self) -> None:
        """Unicode phrases are matched correctly."""
        text = "This is a test"
        assert phrase_matches(text, [""]) is True
        text_utf8 = "Python"
        assert phrase_matches(text_utf8, [""]) is True
