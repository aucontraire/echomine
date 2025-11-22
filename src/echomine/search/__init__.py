"""Search functionality for echomine.

Provides BM25-based relevance ranking for conversation search.
"""

from echomine.search.ranking import BM25Scorer

__all__ = ["BM25Scorer"]
