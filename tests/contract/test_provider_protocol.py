"""Contract tests for ConversationProvider protocol compliance.

Task: T044 - Contract Test - ConversationProvider.search Protocol
Phase: RED (tests designed to FAIL initially)

This module validates that ConversationProvider protocol implementations
comply with the search() method contract as defined in protocols.py.

Test Pyramid Classification: Contract (5% of test suite)
These tests ensure adapters implement the complete protocol interface.

Contract Requirements Validated:
- FR-215-221: Complete method signatures with proper types
- FR-332-336: search() method semantics (query, limit, ranking)
- FR-317-326: BM25 relevance ranking algorithm
- FR-327-331: Title filtering support
- Protocol runtime checkability via @runtime_checkable

Architectural Coverage:
- ConversationProvider protocol definition
- SearchQuery and SearchResult type safety
- Iterator-based search results (streaming)
- Generic typing (ConversationProvider[ConversationT])
"""

from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.protocols import ConversationProvider
from echomine.models.search import SearchQuery, SearchResult


# =============================================================================
# T044: ConversationProvider.search Protocol Contract Tests (RED Phase)
# =============================================================================


@pytest.mark.contract
class TestConversationProviderSearchProtocol:
    """Contract tests for ConversationProvider.search() method.

    These tests validate protocol compliance - NOT implementation details.
    We test that adapters implement the search() method with correct
    signature, return types, and behavioral contracts.

    Expected Failure Reasons (RED phase):
    - search() method doesn't exist on OpenAIAdapter
    - Method signature doesn't match protocol
    - Return type is incorrect (not Iterator[SearchResult[ConversationT]])
    - SearchResult structure doesn't match specification
    """

    def test_openai_adapter_implements_conversation_provider_protocol(self) -> None:
        """Test that OpenAIAdapter implements ConversationProvider protocol.

        Validates:
        - FR-027: All adapters must implement ConversationProvider protocol
        - FR-215: Protocol defines complete interface contract
        - runtime_checkable decorator enables isinstance() validation

        Expected to FAIL: OpenAIAdapter may not fully implement protocol yet.
        """
        adapter = OpenAIAdapter()

        # Assert: OpenAIAdapter implements ConversationProvider protocol
        assert isinstance(adapter, ConversationProvider), (
            "OpenAIAdapter must implement ConversationProvider protocol. "
            "Missing protocol methods or incorrect signatures."
        )

    def test_search_method_exists_on_adapter(self, tmp_export_file: Path) -> None:
        """Test that search() method exists on ConversationProvider implementations.

        Validates:
        - FR-332: search() method defined in protocol
        - Method is callable and accessible

        Expected to FAIL: search() method not implemented yet.
        """
        adapter = OpenAIAdapter()

        # Assert: search() method exists
        assert hasattr(adapter, "search"), (
            "ConversationProvider implementations must have search() method"
        )
        assert callable(adapter.search), "search() must be callable method"

    def test_search_method_signature_matches_protocol(self, tmp_export_file: Path) -> None:
        """Test that search() method signature matches protocol definition.

        Validates:
        - FR-332: search(file_path: Path, query: SearchQuery, ...) signature
        - FR-076: Optional progress_callback parameter
        - FR-106: Optional on_skip parameter
        - FR-152: Returns Iterator[SearchResult[ConversationT]]

        Expected to FAIL: Method signature doesn't match protocol.
        """
        adapter = OpenAIAdapter()

        # Create minimal SearchQuery
        query = SearchQuery(keywords=["test"])

        # Act: Call search() with required parameters
        # This should NOT raise TypeError about unexpected arguments
        try:
            result = adapter.search(tmp_export_file, query)
        except TypeError as e:
            pytest.fail(
                f"search() method signature doesn't match protocol: {e}. "
                f"Expected: search(file_path: Path, query: SearchQuery, *, "
                f"progress_callback=None, on_skip=None)"
            )

        # Assert: Returns iterator (not list, not SearchResult directly)
        assert hasattr(result, "__iter__") and hasattr(result, "__next__"), (
            "search() must return Iterator[SearchResult[ConversationT]], "
            "not list or single SearchResult"
        )

    def test_search_returns_iterator_of_search_results(self, tmp_export_file: Path) -> None:
        """Test that search() returns Iterator[SearchResult[Conversation]].

        Validates:
        - FR-152: Generic return type Iterator[SearchResult[ConversationT]]
        - SearchResult contains conversation + score + metadata
        - Proper typing for type checkers (mypy --strict)

        Expected to FAIL: Return type is incorrect.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"])

        # Act: Get search results
        results = adapter.search(tmp_export_file, query)

        # Assert: Iterator yields SearchResult objects
        first_result = next(results, None)

        if first_result is not None:
            # Verify SearchResult structure
            assert isinstance(first_result, SearchResult), (
                f"Iterator must yield SearchResult instances, got {type(first_result)}"
            )

            # Verify SearchResult has required attributes
            assert hasattr(first_result, "conversation"), (
                "SearchResult must have 'conversation' attribute"
            )
            assert hasattr(first_result, "score"), (
                "SearchResult must have 'score' attribute (relevance)"
            )
            assert hasattr(first_result, "matched_message_ids"), (
                "SearchResult must have 'matched_message_ids' attribute"
            )

            # Verify conversation type
            assert isinstance(first_result.conversation, Conversation), (
                f"SearchResult.conversation must be Conversation type, "
                f"got {type(first_result.conversation)}"
            )

            # Verify score is float in range [0.0, 1.0]
            assert isinstance(first_result.score, float), (
                f"SearchResult.score must be float, got {type(first_result.score)}"
            )
            assert 0.0 <= first_result.score <= 1.0, (
                f"SearchResult.score must be in range [0.0, 1.0], got {first_result.score}"
            )

    def test_search_respects_limit_parameter(self, tmp_export_file: Path) -> None:
        """Test that search respects SearchQuery.limit parameter.

        Validates:
        - FR-336: Limit parameter controls max results returned
        - FR-332: search() honors query parameters

        Expected to FAIL: Limit not implemented yet.
        """
        adapter = OpenAIAdapter()

        # Query with limit=2
        query = SearchQuery(keywords=["python"], limit=2)

        # Act: Search with limit
        results = list(adapter.search(tmp_export_file, query))

        # Assert: No more than limit results returned
        assert len(results) <= 2, (
            f"search() must respect limit parameter. Expected max 2 results, got {len(results)}"
        )

    def test_search_returns_results_sorted_by_relevance(self, tmp_export_file: Path) -> None:
        """Test that search results are sorted by relevance (descending).

        Validates:
        - FR-332: Results MUST be sorted by relevance_score (descending)
        - FR-317-326: BM25 relevance ranking

        Expected to FAIL: Ranking not implemented yet.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])

        # Act: Get search results
        results = list(adapter.search(tmp_export_file, query))

        if len(results) >= 2:
            # Assert: Results sorted by score (descending)
            scores = [r.score for r in results]
            sorted_scores = sorted(scores, reverse=True)

            assert scores == sorted_scores, (
                f"Search results must be sorted by relevance (descending). "
                f"Got scores: {scores}, expected: {sorted_scores}"
            )

    def test_search_handles_empty_results_gracefully(self, tmp_export_file: Path) -> None:
        """Test that search with no matches returns empty iterator.

        Validates:
        - FR-332: Empty results handled gracefully (not error)
        - Protocol contract: search() always returns Iterator

        Expected to FAIL: Empty result handling not implemented.
        """
        adapter = OpenAIAdapter()

        # Query that matches nothing
        query = SearchQuery(keywords=["zzzz_nonexistent_keyword_zzzz"])

        # Act: Search for non-matching keyword
        results = list(adapter.search(tmp_export_file, query))

        # Assert: Empty list (not exception)
        assert isinstance(results, list), "search() should return iterable"
        assert len(results) == 0, "Search with no matches should return empty results, not error"

    def test_search_with_title_filter(self, tmp_export_file: Path) -> None:
        """Test that search supports title filtering.

        Validates:
        - FR-327-331: Title filtering support
        - FR-332: search() honors all SearchQuery parameters

        Expected to FAIL: Title filtering not implemented yet.
        """
        adapter = OpenAIAdapter()

        # Query with title filter only
        query = SearchQuery(title_filter="Python")

        # Act: Search with title filter
        results = list(adapter.search(tmp_export_file, query))

        # Assert: All results have matching title
        for result in results:
            assert "python" in result.conversation.title.lower(), (
                f"Title filter 'Python' should match conversation title, "
                f"got: {result.conversation.title}"
            )

    def test_search_with_combined_filters(self, tmp_export_file: Path) -> None:
        """Test that search supports combined keyword + title filters.

        Validates:
        - FR-332: Multiple filters applied together (AND logic)
        - FR-327-331: Title filtering
        - FR-317-326: Keyword matching

        Expected to FAIL: Combined filtering not implemented yet.
        """
        adapter = OpenAIAdapter()

        # Query with both keywords AND title filter
        query = SearchQuery(keywords=["async"], title_filter="Python")

        # Act: Search with combined filters
        results = list(adapter.search(tmp_export_file, query))

        # Assert: Results match BOTH filters
        for result in results:
            # Title must match
            assert "python" in result.conversation.title.lower(), (
                f"Combined filter: title should contain 'Python', got: {result.conversation.title}"
            )

            # Keyword must be present (in title or messages)
            # Note: Full content validation requires message content access
            # For contract test, we just verify search returns something
            assert result.score > 0.0, "Combined filter: results should have relevance score > 0"

    def test_search_with_progress_callback_parameter(self, tmp_export_file: Path) -> None:
        """Test that search() accepts optional progress_callback parameter.

        Validates:
        - FR-076: Optional progress_callback parameter
        - FR-332: Callback signature matches ProgressCallback type

        Expected to FAIL: Progress callback not implemented yet.

        Note: This test only validates the parameter is ACCEPTED, not
        that it's invoked correctly (that's integration test T045).
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])

        progress_calls = []

        def progress_callback(count: int) -> None:
            progress_calls.append(count)

        # Act: Call search() with progress_callback
        # Should NOT raise TypeError about unexpected keyword argument
        try:
            results = list(
                adapter.search(tmp_export_file, query, progress_callback=progress_callback)
            )
        except TypeError as e:
            pytest.fail(f"search() must accept progress_callback parameter: {e}")

        # If callback is implemented, it should have been called
        # (but not required for contract test - just verify parameter accepted)

    def test_search_with_on_skip_callback_parameter(self, tmp_export_file: Path) -> None:
        """Test that search() accepts optional on_skip parameter.

        Validates:
        - FR-106: Optional on_skip callback parameter
        - FR-332: Callback signature matches OnSkipCallback type

        Expected to FAIL: on_skip callback not implemented yet.

        Note: This test only validates the parameter is ACCEPTED, not
        that it's invoked correctly (that's integration test T045).
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])

        skip_calls = []

        def on_skip(conversation_id: str, reason: str) -> None:
            skip_calls.append((conversation_id, reason))

        # Act: Call search() with on_skip callback
        # Should NOT raise TypeError about unexpected keyword argument
        try:
            results = list(adapter.search(tmp_export_file, query, on_skip=on_skip))
        except TypeError as e:
            pytest.fail(f"search() must accept on_skip parameter: {e}")

        # If callback is implemented, it should have been called for malformed entries
        # (but not required for contract test - just verify parameter accepted)

    def test_search_raises_file_not_found_for_missing_file(self) -> None:
        """Test that search raises FileNotFoundError for missing files.

        Validates:
        - FR-049: FileNotFoundError for non-existent files
        - FR-033: Proper error handling

        Expected to FAIL: Error handling not implemented.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"])
        non_existent = Path("/tmp/this_file_does_not_exist_12345.json")

        # Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            list(adapter.search(non_existent, query))

    def test_search_query_immutability(self) -> None:
        """Test that SearchQuery is immutable (frozen Pydantic model).

        Validates:
        - FR-224, FR-227: Immutability via frozen=True
        - Pydantic frozen model behavior

        Expected to FAIL: SearchQuery may not be frozen.
        """
        query = SearchQuery(keywords=["python"], limit=10)

        # Assert: Modifying frozen field should raise error
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            query.keywords = ["modified"]  # type: ignore[misc]

    def test_search_result_immutability(self, sample_conversation_data: dict) -> None:
        """Test that SearchResult is immutable (frozen Pydantic model).

        Validates:
        - FR-224, FR-227: Immutability via frozen=True
        - Pydantic frozen model behavior

        Expected to FAIL: SearchResult may not be frozen.
        """
        from datetime import UTC, datetime

        # Create a minimal Conversation for testing
        from echomine.models.message import Message

        conversation = Conversation(
            id="test-conv",
            title="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            messages=[
                Message(
                    id="msg-1",
                    role="user",
                    content="test",
                    timestamp=datetime.now(UTC),
                )
            ],
        )

        result = SearchResult(
            conversation=conversation,
            score=0.85,
            matched_message_ids=["msg-1"],
        )

        # Assert: Modifying frozen field should raise error
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            result.score = 0.95  # type: ignore[misc]


@pytest.mark.contract
class TestSearchQueryValidation:
    """Contract tests for SearchQuery validation rules.

    These tests validate that SearchQuery enforces its constraints
    via Pydantic validation.
    """

    def test_search_query_limit_must_be_positive(self) -> None:
        """Test that SearchQuery.limit must be > 0.

        Validates:
        - FR-332: limit must be in range (1, 1000)
        - Pydantic validation enforcement

        Expected to FAIL: Validation not implemented.
        """
        from pydantic import ValidationError

        # Assert: limit=0 raises ValidationError
        with pytest.raises(ValidationError, match="limit"):
            SearchQuery(keywords=["test"], limit=0)

        # Assert: negative limit raises ValidationError
        with pytest.raises(ValidationError, match="limit"):
            SearchQuery(keywords=["test"], limit=-1)

    def test_search_query_limit_max_1000(self) -> None:
        """Test that SearchQuery.limit cannot exceed 1000.

        Validates:
        - FR-332: limit max value = 1000
        - Pydantic validation enforcement

        Expected to FAIL: Max validation not implemented.
        """
        from pydantic import ValidationError

        # Assert: limit > 1000 raises ValidationError
        with pytest.raises(ValidationError, match="limit"):
            SearchQuery(keywords=["test"], limit=1001)

    def test_search_query_default_limit_is_10(self) -> None:
        """Test that SearchQuery.limit defaults to 10.

        Validates:
        - FR-332: Default limit = 10
        - Pydantic default value

        Expected to FAIL: Default not set correctly.
        """
        query = SearchQuery(keywords=["test"])

        assert query.limit == 10, f"SearchQuery.limit should default to 10, got {query.limit}"

    def test_search_result_score_must_be_0_to_1(self) -> None:
        """Test that SearchResult.score must be in range [0.0, 1.0].

        Validates:
        - SearchResult validation rules
        - Pydantic field constraints (ge=0.0, le=1.0)

        Expected to FAIL: Score validation not implemented.
        """
        from datetime import UTC, datetime

        from pydantic import ValidationError

        from echomine.models.message import Message

        conversation = Conversation(
            id="test-conv",
            title="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            messages=[
                Message(
                    id="msg-1",
                    role="user",
                    content="test",
                    timestamp=datetime.now(UTC),
                )
            ],
        )

        # Assert: score > 1.0 raises ValidationError
        with pytest.raises(ValidationError, match="score"):
            SearchResult(conversation=conversation, score=1.5, matched_message_ids=[])

        # Assert: score < 0.0 raises ValidationError
        with pytest.raises(ValidationError, match="score"):
            SearchResult(conversation=conversation, score=-0.1, matched_message_ids=[])
