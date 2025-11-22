"""Search models for query parameters and results.

This module defines the SearchQuery and SearchResult Pydantic models for
encapsulating search parameters and returned results with relevance scoring.

Constitution Compliance:
- Principle VI: Strict typing with mypy --strict compliance
- Principle I: Library-first (importable, reusable models)
- FR-224, FR-227: Immutability via frozen=True
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from echomine.models.conversation import Conversation


class SearchQuery(BaseModel):
    """Search query parameters with filters.

    Encapsulates all search parameters including keywords, title filtering,
    date range filtering, and result limits. All filters are optional but
    at least one should be provided for meaningful results.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        from datetime import date

        # Keyword search
        query = SearchQuery(keywords=["algorithm", "design"], limit=10)

        # Title filter only (fast, metadata-only)
        query = SearchQuery(title_filter="Project")

        # Combined filters
        query = SearchQuery(
            keywords=["refactor"],
            title_filter="Project",
            from_date=date(2024, 1, 1),
            to_date=date(2024, 3, 31),
            limit=20
        )

        # Check filter types
        if query.has_keyword_search():
            print("Performing full-text search")
        ```

    Attributes:
        keywords: Keywords for full-text search (OR logic, case-insensitive)
        title_filter: Partial match on conversation title (metadata-only, fast)
        from_date: Start date for date range filter (inclusive)
        to_date: End date for date range filter (inclusive)
        limit: Maximum results to return (1-1000, default: 10)
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    # Optional Search Filters
    keywords: Optional[list[str]] = Field(
        None,
        description="Keywords for full-text search (OR logic, case-insensitive)",
    )
    title_filter: Optional[str] = Field(
        None,
        description="Partial match on conversation title (metadata-only, case-insensitive)",
    )
    from_date: Optional[date] = Field(
        None,
        description="Start date for date range filter (inclusive)",
    )
    to_date: Optional[date] = Field(
        None,
        description="End date for date range filter (inclusive)",
    )

    # Result Limit (per FR-332)
    limit: int = Field(
        10,
        gt=0,
        le=1000,
        description="Maximum results to return (1-1000, default: 10)",
    )

    def has_keyword_search(self) -> bool:
        """Check if keyword search is requested.

        Returns:
            True if keywords provided and non-empty, False otherwise

        Example:
            ```python
            query = SearchQuery(keywords=["algorithm"])
            assert query.has_keyword_search() is True
            ```
        """
        return self.keywords is not None and len(self.keywords) > 0

    def has_title_filter(self) -> bool:
        """Check if title filtering is requested.

        Returns:
            True if title_filter provided and non-empty, False otherwise

        Example:
            ```python
            query = SearchQuery(title_filter="Project")
            assert query.has_title_filter() is True
            ```
        """
        return self.title_filter is not None and len(self.title_filter.strip()) > 0

    def has_date_filter(self) -> bool:
        """Check if date range filtering is requested.

        Returns:
            True if either from_date or to_date provided, False otherwise

        Example:
            ```python
            from datetime import date

            query = SearchQuery(from_date=date(2024, 1, 1))
            assert query.has_date_filter() is True
            ```
        """
        return self.from_date is not None or self.to_date is not None


class SearchResult(BaseModel):
    """Search result with relevance scoring.

    Represents a conversation match from a search query with relevance
    metadata. Results are typically sorted by score (descending) before
    being returned to the user.

    Immutability:
        This model is FROZEN - attempting to modify fields will raise ValidationError.
        Use .model_copy(update={...}) to create modified instances.

    Example:
        ```python
        result = SearchResult(
            conversation=conversation,
            score=0.85,
            matched_message_ids=["msg-001", "msg-005"]
        )

        print(f"Relevance: {result.score:.2f}")
        print(f"Title: {result.conversation.title}")
        print(f"Matched {len(result.matched_message_ids)} messages")

        # Sort results by relevance
        results = sorted(results, reverse=True)  # Uses __lt__
        ```

    Attributes:
        conversation: Matched conversation object (full conversation, not just ID)
        score: Relevance score (0.0-1.0, higher = better match)
        matched_message_ids: Message IDs containing keyword matches
    """

    model_config = ConfigDict(
        frozen=True,  # Immutability
        strict=True,  # Strict validation
        extra="forbid",  # Reject unknown fields
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    conversation: Conversation = Field(
        ...,
        description="Matched conversation object (full conversation, not just ID)",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0-1.0, higher = better match)",
    )
    matched_message_ids: list[str] = Field(
        default_factory=list,
        description="Message IDs containing keyword matches",
    )

    def __lt__(self, other: "SearchResult") -> bool:
        """Enable sorting by relevance (descending).

        When using sorted() or .sort(), results will be ordered by
        relevance score in descending order (highest score first).

        Args:
            other: Another SearchResult to compare against

        Returns:
            True if self.score > other.score (reversed for descending sort)

        Example:
            ```python
            results = [
                SearchResult(conversation=c1, score=0.5, matched_message_ids=[]),
                SearchResult(conversation=c2, score=0.9, matched_message_ids=[]),
                SearchResult(conversation=c3, score=0.7, matched_message_ids=[]),
            ]

            # Sort descending by relevance
            sorted_results = sorted(results, reverse=True)
            # Order: [0.9, 0.7, 0.5]
            ```
        """
        return self.score > other.score  # Reverse for descending sort
