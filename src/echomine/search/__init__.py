"""Search functionality for echomine.

Provides BM25-based relevance ranking for conversation search
and snippet extraction for search results.
"""

from echomine.search.ranking import BM25Scorer
from echomine.search.snippet import extract_snippet, extract_snippet_from_messages


__all__ = ["BM25Scorer", "extract_snippet", "extract_snippet_from_messages"]
