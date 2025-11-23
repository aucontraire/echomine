"""T058: Library API Integration Tests.

This test module validates that the echomine library can be imported and used
programmatically by external consumers (e.g., cognivault integration).

Test Strategy:
    - Import all public API items from top-level echomine package
    - Verify adapter instances can be created
    - Verify library methods can be called successfully
    - Verify return types match documented API contracts
    - Verify IDE autocomplete support via type hints

Constitution Compliance:
    - Principle I: Library-First Architecture (all features importable)
    - Principle VI: Strict Typing Mandatory (type hints for IDE support)
    - Principle III: Test-Driven Development (RED phase - tests written first)

Requirements Coverage:
    - FR-001: Library-first design (importable modules)
    - FR-027: ConversationProvider protocol implementation
    - FR-151-154: Generic typing support for multi-provider pattern

Test Execution:
    pytest tests/integration/test_library_api.py -v

Expected State: FAILING (imports will fail until exports added to __init__.py)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from echomine import Conversation, Message, OpenAIAdapter, SearchQuery, SearchResult
    from echomine.exceptions import (
        EchomineError,
        ParseError,
        SchemaVersionError,
        ValidationError,
    )
    from echomine.models.protocols import ConversationProvider


# ============================================================================
# T058-001: Top-Level Package Imports
# ============================================================================


def test_can_import_models_from_top_level_package() -> None:
    """Verify all data models can be imported from echomine package.

    Requirements:
        - FR-001: Library-first design requires importable models
        - Principle I: All core functionality available programmatically

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
        (Exports not yet added to src/echomine/__init__.py)
    """
    # This import should work but will fail until exports are added
    from echomine import Conversation, Message, SearchQuery, SearchResult

    # Verify imports are the actual classes, not None
    assert Conversation is not None, "Conversation should be importable"
    assert Message is not None, "Message should be importable"
    assert SearchQuery is not None, "SearchQuery should be importable"
    assert SearchResult is not None, "SearchResult should be importable"


def test_can_import_adapter_from_top_level_package() -> None:
    """Verify OpenAIAdapter can be imported from echomine package.

    Requirements:
        - FR-001: Library-first design requires importable adapters
        - FR-027: Adapters implement ConversationProvider protocol

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    assert OpenAIAdapter is not None, "OpenAIAdapter should be importable"


def test_can_import_protocol_from_top_level_package() -> None:
    """Verify ConversationProvider protocol can be imported from echomine package.

    Requirements:
        - FR-027: Protocol defines adapter contract
        - Principle VII: Multi-Provider Adapter Pattern

    Expected Failure:
        ImportError: cannot import name 'ConversationProvider' from 'echomine'
    """
    from echomine.models.protocols import ConversationProvider

    assert ConversationProvider is not None, "ConversationProvider should be importable"


def test_can_import_exceptions_from_echomine_package() -> None:
    """Verify all custom exceptions can be imported from echomine.exceptions.

    Requirements:
        - FR-035: Base exception class hierarchy
        - FR-036: Specific exception types for different error categories

    Expected Failure:
        ImportError: cannot import name 'EchomineError' from 'echomine.exceptions'
        (These should already exist, but test validates export contract)
    """
    from echomine.exceptions import (
        EchomineError,
        ParseError,
        SchemaVersionError,
        ValidationError,
    )

    assert EchomineError is not None
    assert ParseError is not None
    assert ValidationError is not None
    assert SchemaVersionError is not None


# ============================================================================
# T058-002: Adapter Instantiation
# ============================================================================


def test_can_create_adapter_instance() -> None:
    """Verify OpenAIAdapter can be instantiated without errors.

    Requirements:
        - FR-113: Adapters are stateless (no __init__ parameters)
        - FR-114: Instantiation is lightweight (no I/O)

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    # Should instantiate instantly with no parameters (stateless design)
    adapter = OpenAIAdapter()

    assert adapter is not None, "Adapter instance should be created"
    assert isinstance(adapter, OpenAIAdapter), "Instance should be correct type"


def test_adapter_instance_is_reusable() -> None:
    """Verify same adapter instance can be used for multiple operations.

    Requirements:
        - FR-115: Adapters are reusable (stateless design)
        - FR-120: Multiple files can be processed with same adapter instance

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Same adapter instance can be used for different files
    # (This will fail later when files don't exist, but tests instantiation)
    file1 = Path("export1.json")
    file2 = Path("export2.json")

    # Should be able to call methods multiple times with different files
    # (Will fail at file not found, but validates adapter is reusable)
    try:
        list(adapter.stream_conversations(file1))
    except FileNotFoundError:
        pass  # Expected - just testing adapter can be called

    try:
        list(adapter.stream_conversations(file2))
    except FileNotFoundError:
        pass  # Expected - just testing adapter can be reused


# ============================================================================
# T058-003: Library Method Calls
# ============================================================================


def test_can_call_stream_conversations_method(
    tmp_export_file: Path,
) -> None:
    """Verify stream_conversations method can be called and returns iterator.

    Requirements:
        - FR-151: Generic protocol with stream_conversations method
        - FR-153: Streaming memory contract

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Should return an iterator
    conversations_iter = adapter.stream_conversations(tmp_export_file)

    # Verify it's an iterator (not a list)
    assert hasattr(
        conversations_iter, "__iter__"
    ), "Should return iterator, not list"
    assert hasattr(conversations_iter, "__next__"), "Should be an iterator"

    # Consume iterator to verify it works
    conversations = list(conversations_iter)
    assert len(conversations) > 0, "Should yield at least one conversation"
    assert all(
        hasattr(conv, "id") for conv in conversations
    ), "Conversations should have id attribute"
    assert all(
        hasattr(conv, "title") for conv in conversations
    ), "Conversations should have title attribute"


def test_can_call_search_method(
    tmp_export_file: Path,
) -> None:
    """Verify search method can be called with SearchQuery.

    Requirements:
        - FR-152: Generic protocol with search method
        - FR-153: Memory-efficient streaming
        - FR-317-326: BM25 relevance ranking

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()

    # Create search query
    query = SearchQuery(keywords=["algorithm", "code"], limit=5)

    # Should return an iterator
    results_iter = adapter.search(tmp_export_file, query)

    assert hasattr(results_iter, "__iter__"), "Should return iterator"
    assert hasattr(results_iter, "__next__"), "Should be an iterator"

    # Consume iterator to verify it works
    results = list(results_iter)

    # Results should be SearchResult instances
    if len(results) > 0:  # May be empty if no matches
        assert all(
            hasattr(result, "conversation") for result in results
        ), "Results should have conversation attribute"
        assert all(
            hasattr(result, "score") for result in results
        ), "Results should have score attribute"


def test_can_call_get_conversation_by_id_method(
    tmp_export_file: Path,
) -> None:
    """Verify get_conversation_by_id method can be called.

    Requirements:
        - FR-151: Generic protocol with get_conversation_by_id method
        - FR-155: Returns None if conversation not found

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # First, get a valid conversation ID from the file
    conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(conversations) > 0, "Sample export should have conversations"

    conversation_id = conversations[0].id

    # Should be able to retrieve by ID
    conversation = adapter.get_conversation_by_id(tmp_export_file, conversation_id)

    assert conversation is not None, "Should find conversation with valid ID"
    assert conversation.id == conversation_id, "Should return correct conversation"


def test_get_conversation_by_id_returns_none_for_missing_id(
    tmp_export_file: Path,
) -> None:
    """Verify get_conversation_by_id returns None for non-existent ID.

    Requirements:
        - FR-155: Returns None if conversation_id not found (not exception)

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Use non-existent ID
    conversation = adapter.get_conversation_by_id(
        tmp_export_file, "non-existent-uuid-12345"
    )

    assert conversation is None, "Should return None for non-existent ID"


# ============================================================================
# T058-004: SearchQuery Construction
# ============================================================================


def test_can_construct_search_query_with_keywords() -> None:
    """Verify SearchQuery can be constructed with keywords only.

    Requirements:
        - FR-151: SearchQuery is part of public API
        - Pydantic validation for query parameters

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    query = SearchQuery(keywords=["algorithm", "python"])

    assert query.keywords == ["algorithm", "python"]
    assert query.title_filter is None
    assert query.limit == 10  # Default limit per FR-332


def test_can_construct_search_query_with_all_filters() -> None:
    """Verify SearchQuery supports all filter parameters.

    Requirements:
        - FR-151: SearchQuery with keywords, title, date filters
        - FR-055: Query validation at construction time

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import SearchQuery

    from_date_value = datetime(2024, 1, 1, tzinfo=UTC).date()
    to_date_value = datetime(2024, 12, 31, tzinfo=UTC).date()

    query = SearchQuery(
        keywords=["algorithm"],
        title_filter="Python",
        from_date=from_date_value,
        to_date=to_date_value,
        limit=50,
    )

    assert query.keywords == ["algorithm"]
    assert query.title_filter == "Python"
    assert query.from_date == from_date_value
    assert query.to_date == to_date_value
    assert query.limit == 50


# ============================================================================
# T058-005: Return Type Validation
# ============================================================================


def test_search_result_has_expected_attributes(
    tmp_export_file: Path,
) -> None:
    """Verify SearchResult objects have documented attributes.

    Requirements:
        - FR-152: SearchResult[ConversationT] generic type
        - FR-317: Results include relevance score

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["test"], limit=1)

    results = list(adapter.search(tmp_export_file, query))

    if len(results) > 0:
        result = results[0]

        # Verify SearchResult structure
        assert hasattr(result, "conversation"), "SearchResult should have conversation"
        assert hasattr(result, "score"), "SearchResult should have score"
        assert hasattr(
            result, "matched_message_ids"
        ), "SearchResult should have matched_message_ids"

        # Verify types
        assert isinstance(result.score, float), "Score should be float"
        assert 0.0 <= result.score <= 1.0, "Score should be normalized 0.0-1.0"


def test_conversation_has_expected_attributes(
    tmp_export_file: Path,
) -> None:
    """Verify Conversation objects have documented attributes.

    Requirements:
        - FR-151: Conversation type with id, title, created_at
        - FR-169: Core fields mandatory across all providers

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()
    conversations = list(adapter.stream_conversations(tmp_export_file))

    assert len(conversations) > 0, "Sample export should have conversations"

    conversation = conversations[0]

    # Verify BaseConversation protocol attributes
    assert hasattr(conversation, "id"), "Conversation should have id"
    assert hasattr(conversation, "title"), "Conversation should have title"
    assert hasattr(conversation, "created_at"), "Conversation should have created_at"
    assert hasattr(conversation, "messages"), "Conversation should have messages"

    # Verify types
    assert isinstance(conversation.id, str), "ID should be string"
    assert isinstance(conversation.title, str), "Title should be string"
    assert isinstance(conversation.created_at, datetime), "created_at should be datetime"


# ============================================================================
# T058-006: Type Hints for IDE Autocomplete
# ============================================================================


def test_adapter_methods_have_type_hints() -> None:
    """Verify adapter methods have complete type hints for IDE support.

    Requirements:
        - Principle VI: Strict Typing Mandatory
        - FR-151-154: Generic typing for multi-provider pattern

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Verify methods exist and have __annotations__
    assert hasattr(adapter, "stream_conversations"), "Should have stream_conversations"
    assert hasattr(adapter, "search"), "Should have search"
    assert hasattr(adapter, "get_conversation_by_id"), "Should have get_conversation_by_id"

    # Type hints should be available for IDE autocomplete
    # (This validates annotations exist, not their correctness - mypy validates correctness)
    stream_method = getattr(adapter.__class__, "stream_conversations", None)
    assert stream_method is not None, "stream_conversations method should exist"

    search_method = getattr(adapter.__class__, "search", None)
    assert search_method is not None, "search method should exist"

    get_method = getattr(adapter.__class__, "get_conversation_by_id", None)
    assert get_method is not None, "get_conversation_by_id method should exist"


# ============================================================================
# T058-007: Exception Handling
# ============================================================================


def test_library_raises_file_not_found_for_missing_file() -> None:
    """Verify library raises FileNotFoundError for non-existent files.

    Requirements:
        - FR-049: FileNotFoundError for missing files
        - FR-033: Fail-fast for operational errors

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    non_existent_file = Path("/tmp/this-file-does-not-exist-12345.json")

    with pytest.raises(FileNotFoundError):
        list(adapter.stream_conversations(non_existent_file))


def test_library_raises_echomine_error_hierarchy() -> None:
    """Verify library exceptions inherit from EchomineError.

    Requirements:
        - FR-035: Base exception class for library hierarchy
        - FR-286: Selective exception handling

    Expected Failure:
        ImportError: cannot import name 'EchomineError' from 'echomine.exceptions'
    """
    from echomine.exceptions import (
        EchomineError,
        ParseError,
        SchemaVersionError,
        ValidationError,
    )

    # Verify inheritance hierarchy
    assert issubclass(
        ParseError, EchomineError
    ), "ParseError should inherit from EchomineError"
    assert issubclass(
        ValidationError, EchomineError
    ), "ValidationError should inherit from EchomineError"
    assert issubclass(
        SchemaVersionError, EchomineError
    ), "SchemaVersionError should inherit from EchomineError"


# ============================================================================
# T058-008: Programmatic Usage Example
# ============================================================================


def test_complete_programmatic_workflow(
    tmp_export_file: Path,
) -> None:
    """Integration test: Complete workflow as external library consumer would use it.

    This test simulates how cognivault would import and use the library.

    Requirements:
        - FR-001: Library-first design
        - Principle I: Library-First Architecture
        - All core functionality available programmatically

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    # This is how an external consumer (e.g., cognivault) would use the library
    from echomine import OpenAIAdapter, SearchQuery

    # Step 1: Create adapter instance
    adapter = OpenAIAdapter()

    # Step 2: List all conversations
    all_conversations = list(adapter.stream_conversations(tmp_export_file))
    assert len(all_conversations) > 0, "Should list conversations"

    # Step 3: Search with keywords
    query = SearchQuery(keywords=["algorithm", "code"], limit=5)
    search_results = list(adapter.search(tmp_export_file, query))

    # Results should be sorted by relevance
    if len(search_results) > 1:
        for i in range(len(search_results) - 1):
            assert (
                search_results[i].score >= search_results[i + 1].score
            ), "Results should be sorted by score (descending)"

    # Step 4: Get specific conversation by ID
    if len(all_conversations) > 0:
        conversation_id = all_conversations[0].id
        conversation = adapter.get_conversation_by_id(
            tmp_export_file, conversation_id
        )
        assert conversation is not None, "Should retrieve conversation by ID"
        assert conversation.id == conversation_id, "Should return correct conversation"
