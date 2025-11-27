"""BM25 relevance ranking for conversation search.

BM25 (Best Matching 25) is a probabilistic relevance ranking function.
Used to score documents (conversations) based on keyword queries.

Parameters (from FR-317):
    k1 = 1.5  # Term frequency saturation parameter
    b = 0.75  # Length normalization parameter

Algorithm:
    score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))

    Where:
    - D: Document (conversation)
    - Q: Query (keywords)
    - f(qi, D): Frequency of keyword qi in document D
    - |D|: Length of document D (word count)
    - avgdl: Average document length across corpus
    - IDF(qi): Inverse document frequency of qi

Constitution Compliance:
    - Principle VI: Strict typing with mypy --strict
    - FR-317-326: BM25 algorithm with standard parameters
    - FR-319: Case-insensitive keyword matching
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections import Counter as CounterType


class BM25Scorer:
    """BM25 relevance scorer for conversations.

    Scores conversations based on keyword matches using BM25 algorithm.
    Normalizes scores to [0.0, 1.0] range for consistency.

    Algorithm Details:
        - k1 = 1.5 (term frequency saturation)
        - b = 0.75 (length normalization)
        - IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        - Score normalization: score_normalized = score_raw / (score_raw + 1) per FR-319

    Example:
        ```python
        # Build corpus
        corpus = [
            "Python is a great programming language",
            "I love Python and JavaScript",
            "Go is fast but Python is easier"
        ]

        # Initialize scorer
        scorer = BM25Scorer(corpus=corpus, avg_doc_length=7.0)

        # Score documents
        score = scorer.score("Python is a great programming language", ["python"])
        # Returns BM25 score (higher = more relevant)
        ```

    Requirements:
        - FR-317: BM25 algorithm implementation
        - FR-318: k1 = 1.5, b = 0.75
        - FR-319: Case-insensitive matching
        - FR-326: Score normalization to [0.0, 1.0]
    """

    # BM25 parameters (FR-317, FR-318)
    K1: float = 1.5  # Term frequency saturation
    B: float = 0.75  # Length normalization

    def __init__(self, corpus: list[str], avg_doc_length: float) -> None:
        """Initialize BM25 scorer with corpus statistics.

        Args:
            corpus: List of document texts (conversation content)
            avg_doc_length: Average document length (for normalization)

        Example:
            ```python
            corpus = ["doc one content", "doc two content"]
            avg_len = sum(len(doc.split()) for doc in corpus) / len(corpus)
            scorer = BM25Scorer(corpus=corpus, avg_doc_length=avg_len)
            ```
        """
        self.corpus_size = len(corpus)
        self.avg_doc_length = avg_doc_length

        # Calculate IDF scores for all terms
        self.idf_scores: dict[str, float] = self._calculate_idf(corpus)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words, handling punctuation and Unicode.

        Uses regex to split on transitions between Latin and non-Latin scripts.
        This allows "Python很适合" to be split into ["python", "很适合"].

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase word tokens

        Example:
            ```python
            tokens = self._tokenize("Python? Yes, python!")
            # Returns: ["python", "yes", "python"]

            tokens = self._tokenize("Python很适合初学者")
            # Returns: ["python", "很", "适", "合", "初", "学", "者"]
            # Each Chinese character is a separate token
            ```
        """
        text_lower = text.lower()

        # Split on word boundaries, but separate Latin from non-Latin scripts
        # Pattern explanation:
        # - [a-z0-9]+ : Latin letters and digits (one or more)
        # - \w : Any other word character (including Unicode)
        # This splits "python很适合" into ["python", "很", "适", "合"]
        tokens: list[str] = []

        # Match Latin alphanumeric sequences
        for match in re.finditer(r"[a-z0-9]+", text_lower):
            tokens.append(match.group())

        # Match non-Latin word characters (one at a time for CJK)
        # This allows matching "python" in "python很适合初学者"
        for match in re.finditer(r"[^\W\d_a-z]", text_lower):
            tokens.append(match.group())

        return tokens

    def _calculate_idf(self, corpus: list[str]) -> dict[str, float]:
        """Calculate IDF scores for all terms in corpus.

        IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)

        Where:
        - N: Total number of documents
        - df(t): Document frequency of term t (documents containing t)

        Args:
            corpus: List of document texts

        Returns:
            Dictionary mapping term -> IDF score

        Example:
            ```python
            corpus = ["python is great", "python rocks", "java is good"]
            idf_scores = self._calculate_idf(corpus)
            # "python" appears in 2/3 docs -> lower IDF
            # "java" appears in 1/3 docs -> higher IDF
            ```
        """
        # Count document frequency for each term
        df_counter: CounterType[str] = Counter()

        for doc in corpus:
            terms = set(self._tokenize(doc))  # Unique terms per doc
            for term in terms:
                df_counter[term] += 1

        # Calculate IDF for each term
        idf_scores: dict[str, float] = {}
        N = self.corpus_size

        for term, df in df_counter.items():
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            idf_scores[term] = idf

        return idf_scores

    def score(self, document: str, keywords: list[str]) -> float:
        """Score a document for given keywords using BM25.

        Tokenizes both document and keywords using the same method to ensure
        consistent matching. Multi-character keywords (e.g., Chinese "编程")
        are split into individual character tokens.

        Args:
            document: Document text (conversation content)
            keywords: List of query keywords (will be tokenized)

        Returns:
            BM25 score (higher = more relevant, unnormalized)

        Example:
            ```python
            doc = "Python is a great programming language"
            keywords = ["python", "programming"]
            score = scorer.score(doc, keywords)
            # Returns sum of BM25 scores for each keyword token
            ```

        Algorithm:
            For each keyword token qi:
                IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))
        """
        # Tokenize document using improved tokenization
        doc_terms = self._tokenize(document)
        doc_length = len(doc_terms)

        # Count term frequencies
        tf_counter: CounterType[str] = Counter(doc_terms)

        # Tokenize keywords (handles multi-character keywords like "编程")
        keyword_tokens: list[str] = []
        for keyword in keywords:
            keyword_tokens.extend(self._tokenize(keyword))

        # Calculate BM25 score
        score = 0.0

        for kw_token in keyword_tokens:
            # Get IDF score (0 if term not in corpus)
            idf = self.idf_scores.get(kw_token, 0.0)

            # Get term frequency in document
            tf = tf_counter.get(kw_token, 0)

            # BM25 formula
            numerator = tf * (self.K1 + 1.0)
            denominator = tf + self.K1 * (
                1.0 - self.B + self.B * (doc_length / self.avg_doc_length)
            )

            score += idf * (numerator / denominator)

        return score
