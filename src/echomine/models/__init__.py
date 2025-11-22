"""Pydantic data models for AI conversation exports.

This module provides immutable, strictly typed data models for representing
conversations, messages, search queries, and results.

All models follow Constitution Principle VI (Strict Typing) with mypy --strict
compliance and Pydantic v2 validation.

Public API:
    Message: Single message in a conversation with threading support
    Conversation: Complete conversation with metadata and tree navigation
    SearchQuery: Search parameters with filters (keywords, title, dates, limit)
    SearchResult: Search result with conversation and relevance score

Example:
    ```python
    from echomine.models import Message, Conversation, SearchQuery, SearchResult
    from datetime import datetime, UTC

    # Create a message
    msg = Message(
        id="msg-001",
        content="Hello, world!",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None
    )

    # Create a conversation
    conversation = Conversation(
        id="conv-001",
        title="Greeting",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        messages=[msg]
    )

    # Create a search query
    query = SearchQuery(keywords=["algorithm"], limit=10)

    # Create a search result
    result = SearchResult(
        conversation=conversation,
        score=0.85,
        matched_message_ids=["msg-001"]
    )
    ```
"""

from echomine.models.conversation import Conversation
from echomine.models.message import Message
from echomine.models.search import SearchQuery, SearchResult

__all__ = [
    "Message",
    "Conversation",
    "SearchQuery",
    "SearchResult",
]
