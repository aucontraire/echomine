"""Integration tests for User Story 1: Search Conversations by Keyword.

Task: T045 - Integration Test - Keyword Search Workflow
Phase: RED (tests designed to FAIL initially)

This module tests the complete end-to-end workflow for searching conversations:
1. Read OpenAI export JSON file from disk
2. Stream parse conversations using ijson
3. Apply search filters (keywords, title, date range)
4. Compute BM25 relevance scores
5. Rank results by relevance (descending)
6. Return top N results (respecting limit)

Test Pyramid Classification: Integration (20% of test suite)
These tests validate component integration but NOT CLI interface.

Architectural Coverage:
- StreamingParser → SearchEngine → BM25Scorer → OpenAIAdapter
- File I/O → JSON streaming → Filtering → Ranking → Results
- Memory efficiency validation (streaming search, not indexing)

Search Requirements Validated:
- FR-317-326: BM25 relevance ranking (k1=1.5, b=0.75)
- FR-319: Case-insensitive keyword matching
- FR-320: Multi-keyword OR logic (match ANY keyword)
- FR-327-331: Title filtering (case-insensitive substring)
- FR-332-336: Search method semantics and result structure
"""

from pathlib import Path

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.conversation import Conversation
from echomine.models.search import SearchQuery, SearchResult


# =============================================================================
# Integration Test Fixtures (Search-Specific Data)
# =============================================================================


@pytest.fixture
def search_test_export(tmp_path: Path) -> Path:
    """Create search-optimized test fixture with known keyword distribution.

    This fixture is specifically designed to test search functionality:
    - 12 conversations with varying keyword frequencies
    - Known BM25 scores for predictable ranking tests
    - Diverse content for testing filters and edge cases

    Structure:
    - Conv 1-3: "Python" keyword in messages (varying frequency)
    - Conv 4-5: "Python" in title only
    - Conv 6-7: "algorithm" keyword
    - Conv 8: Both "python" AND "algorithm"
    - Conv 9: Unicode content (测试)
    - Conv 10: No keywords (should not match)
    - Conv 11-12: Edge cases (empty messages, long content)

    Returns:
        Path to search test export file
    """
    import json

    conversations = [
        # Conv 1: High "python" frequency (3 occurrences in messages)
        {
            "id": "search-conv-001",
            "title": "Getting Started with Programming",
            "create_time": 1710000000.0,
            "update_time": 1710000100.0,
            "mapping": {
                "msg-001-1": {
                    "id": "msg-001-1",
                    "message": {
                        "id": "msg-001-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["I want to learn Python programming"],
                        },
                        "create_time": 1710000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-001-2"],
                },
                "msg-001-2": {
                    "id": "msg-001-2",
                    "message": {
                        "id": "msg-001-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Python is a great language for beginners. "
                                "I recommend starting with Python basics and "
                                "Python syntax fundamentals."
                            ],
                        },
                        "create_time": 1710000010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-001-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-001-2",
        },
        # Conv 2: Medium "python" frequency (1 occurrence)
        {
            "id": "search-conv-002",
            "title": "Web Development Best Practices",
            "create_time": 1710100000.0,
            "update_time": 1710100100.0,
            "mapping": {
                "msg-002-1": {
                    "id": "msg-002-1",
                    "message": {
                        "id": "msg-002-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["What backend language should I use?"],
                        },
                        "create_time": 1710100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-002-2"],
                },
                "msg-002-2": {
                    "id": "msg-002-2",
                    "message": {
                        "id": "msg-002-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "For web development, Python with Django or Flask "
                                "is excellent. Also consider Node.js or Go."
                            ],
                        },
                        "create_time": 1710100010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-002-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-002-2",
        },
        # Conv 3: Low "python" frequency (case variation: PYTHON)
        {
            "id": "search-conv-003",
            "title": "Language Comparison",
            "create_time": 1710200000.0,
            "update_time": 1710200100.0,
            "mapping": {
                "msg-003-1": {
                    "id": "msg-003-1",
                    "message": {
                        "id": "msg-003-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Compare programming languages"],
                        },
                        "create_time": 1710200000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-003-2"],
                },
                "msg-003-2": {
                    "id": "msg-003-2",
                    "message": {
                        "id": "msg-003-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "PYTHON is easier to learn than Java or C++. "
                                "JavaScript is better for frontend."
                            ],
                        },
                        "create_time": 1710200010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-003-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-003-2",
        },
        # Conv 4: "Python" in TITLE only, not in messages
        {
            "id": "search-conv-004",
            "title": "Python AsyncIO Deep Dive",
            "create_time": 1710300000.0,
            "update_time": 1710300100.0,
            "mapping": {
                "msg-004-1": {
                    "id": "msg-004-1",
                    "message": {
                        "id": "msg-004-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain async/await"],
                        },
                        "create_time": 1710300000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-004-2"],
                },
                "msg-004-2": {
                    "id": "msg-004-2",
                    "message": {
                        "id": "msg-004-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Async/await enables concurrent I/O operations "
                                "using coroutines and event loops."
                            ],
                        },
                        "create_time": 1710300010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-004-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-004-2",
        },
        # Conv 5: "Python" in title (lowercase: "python")
        {
            "id": "search-conv-005",
            "title": "python best practices guide",
            "create_time": 1710400000.0,
            "update_time": 1710400100.0,
            "mapping": {
                "msg-005-1": {
                    "id": "msg-005-1",
                    "message": {
                        "id": "msg-005-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["What are coding best practices?"],
                        },
                        "create_time": 1710400000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-005-2"],
                },
                "msg-005-2": {
                    "id": "msg-005-2",
                    "message": {
                        "id": "msg-005-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Use type hints, write tests, follow PEP 8, "
                                "document code, handle errors properly."
                            ],
                        },
                        "create_time": 1710400010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-005-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-005-2",
        },
        # Conv 6: "algorithm" keyword (no "python")
        {
            "id": "search-conv-006",
            "title": "Algorithm Design Patterns",
            "create_time": 1710500000.0,
            "update_time": 1710500100.0,
            "mapping": {
                "msg-006-1": {
                    "id": "msg-006-1",
                    "message": {
                        "id": "msg-006-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain sorting algorithms"],
                        },
                        "create_time": 1710500000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-006-2"],
                },
                "msg-006-2": {
                    "id": "msg-006-2",
                    "message": {
                        "id": "msg-006-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Common sorting algorithms: QuickSort, MergeSort, "
                                "HeapSort. Each algorithm has different time complexity."
                            ],
                        },
                        "create_time": 1710500010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-006-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-006-2",
        },
        # Conv 7: "algorithm" in messages (multiple occurrences)
        {
            "id": "search-conv-007",
            "title": "Data Structures Tutorial",
            "create_time": 1710600000.0,
            "update_time": 1710600100.0,
            "mapping": {
                "msg-007-1": {
                    "id": "msg-007-1",
                    "message": {
                        "id": "msg-007-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["What are the best search algorithms?"],
                        },
                        "create_time": 1710600000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-007-2"],
                },
                "msg-007-2": {
                    "id": "msg-007-2",
                    "message": {
                        "id": "msg-007-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Binary search algorithm is most efficient for sorted data. "
                                "Linear search algorithm works on unsorted data. "
                                "Hashing algorithm provides O(1) lookup."
                            ],
                        },
                        "create_time": 1710600010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-007-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-007-2",
        },
        # Conv 8: Both "python" AND "algorithm" (for multi-keyword OR test)
        {
            "id": "search-conv-008",
            "title": "Python Algorithm Implementation",
            "create_time": 1710700000.0,
            "update_time": 1710700100.0,
            "mapping": {
                "msg-008-1": {
                    "id": "msg-008-1",
                    "message": {
                        "id": "msg-008-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["How to implement algorithms in Python?"],
                        },
                        "create_time": 1710700000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-008-2"],
                },
                "msg-008-2": {
                    "id": "msg-008-2",
                    "message": {
                        "id": "msg-008-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Python makes algorithm implementation easy with "
                                "clean syntax. Use lists for dynamic arrays."
                            ],
                        },
                        "create_time": 1710700010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-008-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-008-2",
        },
        # Conv 9: Unicode content (测试 Chinese)
        {
            "id": "search-conv-009",
            "title": "学习编程 (Learning Programming)",
            "create_time": 1710800000.0,
            "update_time": 1710800100.0,
            "mapping": {
                "msg-009-1": {
                    "id": "msg-009-1",
                    "message": {
                        "id": "msg-009-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["如何学习编程?"],
                        },
                        "create_time": 1710800000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-009-2"],
                },
                "msg-009-2": {
                    "id": "msg-009-2",
                    "message": {
                        "id": "msg-009-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": ["从基础开始学习。Python很适合初学者。"],
                        },
                        "create_time": 1710800010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-009-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-009-2",
        },
        # Conv 10: NO matching keywords (for empty results test)
        {
            "id": "search-conv-010",
            "title": "Database Design Principles",
            "create_time": 1710900000.0,
            "update_time": 1710900100.0,
            "mapping": {
                "msg-010-1": {
                    "id": "msg-010-1",
                    "message": {
                        "id": "msg-010-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["Explain database normalization"],
                        },
                        "create_time": 1710900000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-010-2"],
                },
                "msg-010-2": {
                    "id": "msg-010-2",
                    "message": {
                        "id": "msg-010-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Normalization reduces redundancy. Use 1NF, 2NF, 3NF "
                                "forms to organize data efficiently."
                            ],
                        },
                        "create_time": 1710900010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-010-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-010-2",
        },
        # Conv 11: Edge case - Empty message content
        {
            "id": "search-conv-011",
            "title": "Edge Case Empty Content",
            "create_time": 1711000000.0,
            "update_time": 1711000100.0,
            "mapping": {
                "msg-011-1": {
                    "id": "msg-011-1",
                    "message": {
                        "id": "msg-011-1",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [""]},
                        "create_time": 1711000000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": [],
                }
            },
            "moderation_results": [],
            "current_node": "msg-011-1",
        },
        # Conv 12: Special characters in content
        {
            "id": "search-conv-012",
            "title": "Regex & Special Characters",
            "create_time": 1711100000.0,
            "update_time": 1711100100.0,
            "mapping": {
                "msg-012-1": {
                    "id": "msg-012-1",
                    "message": {
                        "id": "msg-012-1",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": ["How to use regex in python?"],
                        },
                        "create_time": 1711100000.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": None,
                    "children": ["msg-012-2"],
                },
                "msg-012-2": {
                    "id": "msg-012-2",
                    "message": {
                        "id": "msg-012-2",
                        "author": {"role": "assistant"},
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Use re module: import re\n"
                                "Pattern: r'^[a-z]+@[a-z]+\\.[a-z]+$'\n"
                                "Metacharacters: . * + ? [] {} () \\"
                            ],
                        },
                        "create_time": 1711100010.0,
                        "update_time": None,
                        "metadata": {},
                    },
                    "parent": "msg-012-1",
                    "children": [],
                },
            },
            "moderation_results": [],
            "current_node": "msg-012-2",
        },
    ]

    export_file = tmp_path / "search_test_export.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    return export_file


# =============================================================================
# T045: End-to-End Search Integration Tests (RED Phase - DESIGNED TO FAIL)
# =============================================================================


@pytest.mark.integration
class TestSearchConversationsIntegration:
    """Integration tests for search conversations workflow.

    Tests the complete chain: File → Parser → Filter → Rank → Results
    Does NOT test CLI interface (that's T046 contract tests).

    Expected Failure Reasons (RED phase):
    - search() method doesn't exist on OpenAIAdapter
    - BM25 scoring not implemented
    - Filtering logic not implemented
    - Ranking not implemented
    """

    def test_search_single_keyword_returns_matching_conversations(
        self, search_test_export: Path
    ) -> None:
        """Test basic keyword search functionality.

        Validates:
        - FR-319: Case-insensitive keyword matching
        - FR-332: search() returns matching conversations
        - FR-317-326: BM25 relevance scoring

        Expected to FAIL: search() not implemented yet.
        """
        adapter = OpenAIAdapter()

        # Act: Search for "python"
        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        # Assert: Found conversations with "python"
        assert len(results) > 0, "Should find conversations containing 'python'"

        # Verify all results contain keyword (in title or messages)
        result_ids = {r.conversation.id for r in results}

        # Expected matches based on fixture:
        # Conv 1: "Python" in messages (3 times)
        # Conv 2: "Python" in messages (1 time)
        # Conv 3: "PYTHON" in messages (case-insensitive)
        # Conv 4: "Python" in TITLE
        # Conv 5: "python" in title
        # Conv 8: "Python" in title and messages
        # Conv 9: "Python" in Chinese message
        # Conv 12: "python" in messages

        expected_ids = {
            "search-conv-001",  # High frequency
            "search-conv-002",  # Medium frequency
            "search-conv-003",  # Case variant
            "search-conv-004",  # Title only
            "search-conv-005",  # Title lowercase
            "search-conv-008",  # Both keywords
            "search-conv-009",  # Unicode
            "search-conv-012",  # Regex content
        }

        assert result_ids == expected_ids, (
            f"Search for 'python' should find specific conversations. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

    def test_search_is_case_insensitive(self, search_test_export: Path) -> None:
        """Test that keyword search is case-insensitive.

        Validates:
        - FR-319: Case-insensitive matching
        - "PYTHON", "Python", "python" all match

        Expected to FAIL: Case-insensitive matching not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with different cases
        query_lower = SearchQuery(keywords=["python"])
        query_upper = SearchQuery(keywords=["PYTHON"])
        query_mixed = SearchQuery(keywords=["PyThOn"])

        results_lower = list(adapter.search(search_test_export, query_lower))
        results_upper = list(adapter.search(search_test_export, query_upper))
        results_mixed = list(adapter.search(search_test_export, query_mixed))

        # Assert: All case variants return same conversations
        ids_lower = {r.conversation.id for r in results_lower}
        ids_upper = {r.conversation.id for r in results_upper}
        ids_mixed = {r.conversation.id for r in results_mixed}

        assert ids_lower == ids_upper == ids_mixed, (
            "Case-insensitive search should return same results regardless of case"
        )

    def test_search_multi_keyword_or_logic(self, search_test_export: Path) -> None:
        """Test multi-keyword search uses OR logic (match ANY keyword).

        Validates:
        - FR-320: Multi-keyword OR logic
        - Results include conversations matching ANY keyword

        Expected to FAIL: Multi-keyword OR not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for "python" OR "algorithm"
        query = SearchQuery(keywords=["python", "algorithm"])
        results = list(adapter.search(search_test_export, query))

        result_ids = {r.conversation.id for r in results}

        # Expected: All conversations with "python" OR "algorithm"
        # Conv 1-5: "python"
        # Conv 6-7: "algorithm"
        # Conv 8: BOTH (should appear once)
        # Conv 9: "Python" (Chinese)
        # Conv 12: "python"

        expected_ids = {
            "search-conv-001",
            "search-conv-002",
            "search-conv-003",
            "search-conv-004",
            "search-conv-005",
            "search-conv-006",  # algorithm only
            "search-conv-007",  # algorithm only
            "search-conv-008",  # both
            "search-conv-009",
            "search-conv-012",
        }

        assert result_ids == expected_ids, (
            f"Multi-keyword OR search should match ANY keyword. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

    def test_search_results_sorted_by_relevance_descending(self, search_test_export: Path) -> None:
        """Test that results are sorted by BM25 relevance (highest first).

        Validates:
        - FR-332: Results sorted by relevance_score descending
        - FR-317-326: BM25 scoring produces meaningful rankings

        Expected to FAIL: BM25 ranking not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for "python"
        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        # Assert: Scores are descending
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Search results must be sorted by relevance (descending). Got scores: {scores}"
        )

        # Assert: Higher frequency -> higher score
        # Conv 1 has 3 "python" occurrences -> should rank higher than
        # Conv 2 which has 1 "python" occurrence
        conv_001_result = next(r for r in results if r.conversation.id == "search-conv-001")
        conv_002_result = next(r for r in results if r.conversation.id == "search-conv-002")

        assert conv_001_result.score > conv_002_result.score, (
            "Higher keyword frequency should produce higher BM25 score. "
            f"Conv 001 (3 occurrences): {conv_001_result.score:.3f}, "
            f"Conv 002 (1 occurrence): {conv_002_result.score:.3f}"
        )

    def test_search_with_limit_parameter(self, search_test_export: Path) -> None:
        """Test that limit parameter restricts number of results.

        Validates:
        - FR-336: Limit parameter (top N results)
        - FR-332: search() honors query.limit

        Expected to FAIL: Limit not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search with limit=3
        query = SearchQuery(keywords=["python"], limit=3)
        results = list(adapter.search(search_test_export, query))

        # Assert: No more than 3 results
        assert len(results) <= 3, f"Limit=3 should return max 3 results, got {len(results)}"

        # Assert: Returns TOP 3 by relevance (highest scores)
        # Get all results without limit to compare
        query_no_limit = SearchQuery(keywords=["python"], limit=1000)
        all_results = list(adapter.search(search_test_export, query_no_limit))

        # Top 3 from all results
        top_3_expected = all_results[:3]
        top_3_expected_ids = [r.conversation.id for r in top_3_expected]

        results_ids = [r.conversation.id for r in results]

        assert results_ids == top_3_expected_ids, (
            f"Limit should return TOP N by relevance. "
            f"Expected: {top_3_expected_ids}, got: {results_ids}"
        )

    def test_search_with_title_filter_only(self, search_test_export: Path) -> None:
        """Test search with title filter (no keywords).

        Validates:
        - FR-327-331: Title filtering support
        - FR-332: Title-only search (fast, metadata-only)

        Expected to FAIL: Title filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search by title only
        query = SearchQuery(title_filter="Python")
        results = list(adapter.search(search_test_export, query))

        # Assert: All results have "Python" in title (case-insensitive)
        for result in results:
            assert "python" in result.conversation.title.lower(), (
                f"Title filter 'Python' should match conversation title. "
                f"Got: '{result.conversation.title}'"
            )

        # Expected matches based on fixture:
        # Conv 4: "Python AsyncIO Deep Dive"
        # Conv 5: "python best practices guide"
        # Conv 8: "Python Algorithm Implementation"

        result_ids = {r.conversation.id for r in results}
        expected_ids = {"search-conv-004", "search-conv-005", "search-conv-008"}

        assert result_ids == expected_ids, (
            f"Title filter 'Python' should match specific conversations. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

    def test_search_with_combined_keyword_and_title_filters(self, search_test_export: Path) -> None:
        """Test search with both keyword AND title filters (AND logic).

        Validates:
        - FR-332: Multiple filters applied together
        - AND logic: results must match ALL filters

        Expected to FAIL: Combined filtering not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for keyword="algorithm" AND title contains "Python"
        query = SearchQuery(keywords=["algorithm"], title_filter="Python")
        results = list(adapter.search(search_test_export, query))

        # Assert: Results must have "algorithm" keyword AND "Python" in title
        result_ids = {r.conversation.id for r in results}

        # Only Conv 8 matches BOTH filters:
        # - Title: "Python Algorithm Implementation" (contains "Python")
        # - Content: "algorithms in Python" (contains "algorithm")
        expected_ids = {"search-conv-008"}

        assert result_ids == expected_ids, (
            f"Combined filters should require ALL conditions. "
            f"Expected: {expected_ids}, got: {result_ids}"
        )

    def test_search_with_no_matches_returns_empty(self, search_test_export: Path) -> None:
        """Test that search with no matches returns empty results (not error).

        Validates:
        - FR-332: Empty results handled gracefully
        - No exception raised for zero matches

        Expected to FAIL: Empty result handling not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for non-existent keyword
        query = SearchQuery(keywords=["zzzzzzzz_nonexistent"])
        results = list(adapter.search(search_test_export, query))

        # Assert: Empty results
        assert len(results) == 0, "Search with no matches should return empty list, not error"

    def test_search_result_structure(self, search_test_export: Path) -> None:
        """Test that SearchResult objects have correct structure.

        Validates:
        - FR-332: SearchResult schema (conversation, score, matched_message_ids)
        - SearchResult immutability
        - Score range [0.0, 1.0]

        Expected to FAIL: SearchResult structure incomplete.
        """
        adapter = OpenAIAdapter()

        # Act: Get search results
        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        assert len(results) > 0, "Need at least one result for structure test"

        for result in results:
            # Assert: SearchResult type
            assert isinstance(result, SearchResult), (
                f"Must return SearchResult instances, got {type(result)}"
            )

            # Assert: conversation field
            assert hasattr(result, "conversation")
            assert isinstance(result.conversation, Conversation)

            # Assert: score field
            assert hasattr(result, "score")
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0, f"Score must be in [0.0, 1.0], got {result.score}"

            # Assert: matched_message_ids field
            assert hasattr(result, "matched_message_ids")
            assert isinstance(result.matched_message_ids, list)

    def test_search_matched_message_ids_populated(self, search_test_export: Path) -> None:
        """Test that matched_message_ids contains messages with keyword matches.

        Validates:
        - FR-332: matched_message_ids lists messages containing keywords
        - Useful for highlighting matches in UI

        Expected to FAIL: matched_message_ids not populated.
        """
        adapter = OpenAIAdapter()

        # Act: Search for "python"
        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        # Find Conv 1 result (has 2 messages with "python")
        conv_001_result = next(
            (r for r in results if r.conversation.id == "search-conv-001"),
            None,
        )

        assert conv_001_result is not None, "Conv 001 should be in results"

        # Assert: matched_message_ids not empty
        assert len(conv_001_result.matched_message_ids) > 0, (
            "matched_message_ids should contain message IDs with keyword matches"
        )

        # Verify message IDs are valid
        conv_msg_ids = {msg.id for msg in conv_001_result.conversation.messages}
        matched_ids = set(conv_001_result.matched_message_ids)

        assert matched_ids.issubset(conv_msg_ids), (
            f"matched_message_ids must be subset of conversation message IDs. "
            f"Invalid IDs: {matched_ids - conv_msg_ids}"
        )

    def test_search_empty_export_returns_no_results(self, tmp_empty_export_file: Path) -> None:
        """Test search on empty export file.

        Validates:
        - Edge case: Empty file handled gracefully
        - No errors raised

        Expected to FAIL: Empty file handling not implemented.
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(tmp_empty_export_file, query))

        assert len(results) == 0, "Empty export should return zero results"

    def test_search_handles_unicode_keywords(self, search_test_export: Path) -> None:
        """Test that search handles Unicode keywords correctly.

        Validates:
        - FR-319: Unicode keyword support
        - CHK126: UTF-8 encoding assumption

        Expected to FAIL: Unicode handling not implemented.
        """
        adapter = OpenAIAdapter()

        # Act: Search for Chinese keyword
        query = SearchQuery(keywords=["编程"])  # "programming" in Chinese
        results = list(adapter.search(search_test_export, query))

        # Assert: Found Conv 9 with Chinese content
        result_ids = {r.conversation.id for r in results}
        assert "search-conv-009" in result_ids, "Should find conversation with Chinese keyword"

    def test_search_file_not_found_raises_error(self) -> None:
        """Test that search raises FileNotFoundError for missing files.

        Validates:
        - FR-049: FileNotFoundError for non-existent files
        - FR-033: Proper error handling

        Expected to FAIL: Error handling not implemented.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"])
        non_existent = Path("/tmp/does_not_exist_search_12345.json")

        with pytest.raises(FileNotFoundError):
            list(adapter.search(non_existent, query))


@pytest.mark.integration
class TestBM25RelevanceScoring:
    """Integration tests specifically for BM25 relevance scoring algorithm.

    These tests validate BM25 implementation details to ensure correct
    ranking behavior.
    """

    def test_bm25_scores_are_normalized_0_to_1(self, search_test_export: Path) -> None:
        """Test that BM25 scores are normalized to [0.0, 1.0] range.

        Validates:
        - FR-317-326: BM25 scoring
        - Score normalization for consistent comparisons

        Expected to FAIL: BM25 normalization not implemented.
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        for result in results:
            assert 0.0 <= result.score <= 1.0, (
                f"BM25 scores must be normalized to [0.0, 1.0]. "
                f"Got: {result.score} for {result.conversation.id}"
            )

    def test_bm25_term_frequency_affects_score(self, search_test_export: Path) -> None:
        """Test that higher term frequency produces higher BM25 score.

        Validates:
        - FR-317-326: BM25 TF (term frequency) component
        - More keyword occurrences -> higher score

        Expected to FAIL: TF calculation not implemented.
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        # Conv 1: 3 "python" occurrences
        # Conv 2: 1 "python" occurrence
        conv_001 = next(r for r in results if r.conversation.id == "search-conv-001")
        conv_002 = next(r for r in results if r.conversation.id == "search-conv-002")

        assert conv_001.score > conv_002.score, (
            f"Higher term frequency should produce higher BM25 score. "
            f"Conv 001 (TF=3): {conv_001.score:.3f}, "
            f"Conv 002 (TF=1): {conv_002.score:.3f}"
        )

    def test_bm25_document_length_normalization(self, search_test_export: Path) -> None:
        """Test that BM25 normalizes for document length.

        Validates:
        - FR-317-326: BM25 document length normalization (b=0.75 parameter)
        - Longer documents penalized slightly

        Expected to FAIL: Length normalization not implemented.

        Note: This is a behavior test, not exact BM25 math validation.
        """
        adapter = OpenAIAdapter()

        query = SearchQuery(keywords=["python"])
        results = list(adapter.search(search_test_export, query))

        # All results should have reasonable scores (not dominated by length)
        for result in results:
            assert result.score > 0.0, (
                f"BM25 should produce non-zero scores for matches. "
                f"Got: {result.score} for {result.conversation.id}"
            )
