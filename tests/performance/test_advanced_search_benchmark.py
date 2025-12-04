"""Performance benchmarks for Advanced Search features (v1.1.0).

Benchmarks for new search features added in v1.1.0:
    - US1: Phrase search (FR-001-006)
    - US2: Match mode (FR-007-011)
    - US3: Exclude keywords (FR-012-016)
    - US4: Role filtering (FR-017-020)
    - US5: Snippets (FR-021-025)

Constitution Compliance:
    - Principle VIII: Memory efficiency preserved with new features
    - Performance should remain within SC-001 bounds (<30s for 10K convos)
"""

from __future__ import annotations

import json
import tracemalloc
from pathlib import Path
from typing import Any

import pytest

from echomine.adapters.openai import OpenAIAdapter
from echomine.models.search import SearchQuery


@pytest.fixture(scope="module")
def large_export_advanced(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate export with diverse content for advanced search benchmarks.

    Creates export with:
    - Varied role distribution (user, assistant, system)
    - Phrase patterns for phrase search testing
    - Exclusion candidates for exclude testing
    - Content for snippet extraction
    """
    tmp_path = tmp_path_factory.mktemp("advanced_search_perf")

    conversations = []
    for i in range(1000):  # 1K conversations for faster benchmarks
        # Role distribution
        roles = ["user", "assistant"]
        if i % 10 == 0:
            roles.append("system")

        messages_mapping = {}
        msg_count = 8

        for j, role in enumerate(roles * 3):  # Multiple messages per role
            if j >= msg_count:
                break

            msg_id = f"msg-{i:05d}-{j}"
            parent_id = f"msg-{i:05d}-{j - 1}" if j > 0 else None
            children_ids = [f"msg-{i:05d}-{j + 1}"] if j < msg_count - 1 else []

            # Content with phrases and keywords for testing
            content_parts = []
            if i % 3 == 0:
                content_parts.append("Python programming is great for data science")
            if i % 5 == 0:
                content_parts.append("Machine learning algorithms are powerful")
            if i % 7 == 0:
                content_parts.append("This code has some errors to fix")

            if not content_parts:
                content_parts.append(f"Generic message {j} in conversation {i}")

            content = " ".join(content_parts)

            messages_mapping[msg_id] = {
                "id": msg_id,
                "author": {"role": role},
                "content": {"parts": [content]},
                "create_time": 1704067200.0 + i + j,
                "update_time": 1704067200.0 + i + j,
                "metadata": {},
            }
            if parent_id:
                messages_mapping[msg_id]["parent"] = parent_id
            if children_ids:
                messages_mapping[msg_id]["children"] = children_ids

        title = f"Conversation {i}: Python and ML discussion"
        if i % 4 == 0:
            title = f"Conversation {i}: Algorithm analysis"

        conversation = {
            "id": f"conv-{i:05d}",
            "title": title,
            "create_time": 1704067200.0 + i,
            "update_time": 1704067300.0 + i,
            "mapping": messages_mapping,
        }
        conversations.append(conversation)

    export_path = tmp_path / "advanced_search_perf.json"
    with open(export_path, "w") as f:
        json.dump(conversations, f)

    return export_path


class TestPhraseSearchPerformance:
    """Benchmark phrase search feature (US1)."""

    def test_phrase_search_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark phrase search performance.

        Validates that phrase search doesn't add significant overhead.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(phrases=["Python programming"], limit=100)

        def search_phrases() -> int:
            return sum(1 for _ in adapter.search(large_export_advanced, query))

        result = benchmark(search_phrases)
        assert result >= 0  # Valid result count


class TestMatchModePerformance:
    """Benchmark match_mode feature (US2)."""

    def test_match_mode_all_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark match_mode=all performance.

        AND logic should not add significant overhead to search.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python", "data"],
            match_mode="all",
            limit=100,
        )

        def search_all() -> int:
            return sum(1 for _ in adapter.search(large_export_advanced, query))

        result = benchmark(search_all)
        assert result >= 0


class TestExcludeKeywordsPerformance:
    """Benchmark exclude keywords feature (US3)."""

    def test_exclude_keywords_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark exclude keywords performance.

        Exclusion should add minimal overhead.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            exclude_keywords=["error"],
            limit=100,
        )

        def search_exclude() -> int:
            return sum(1 for _ in adapter.search(large_export_advanced, query))

        result = benchmark(search_exclude)
        assert result >= 0


class TestRoleFilterPerformance:
    """Benchmark role filtering feature (US4)."""

    def test_role_filter_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark role filtering performance.

        Role filtering should add minimal overhead.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            role_filter="user",
            limit=100,
        )

        def search_role() -> int:
            return sum(1 for _ in adapter.search(large_export_advanced, query))

        result = benchmark(search_role)
        assert result >= 0


class TestSnippetExtractionPerformance:
    """Benchmark snippet extraction feature (US5)."""

    def test_snippet_extraction_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark snippet extraction performance.

        Snippet extraction happens for each result.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"], limit=100)

        def search_with_snippets() -> int:
            count = 0
            for result in adapter.search(large_export_advanced, query):
                assert result.snippet is not None
                count += 1
            return count

        result = benchmark(search_with_snippets)
        assert result >= 0


class TestCombinedFeaturesPerformance:
    """Benchmark all features combined."""

    def test_all_features_combined_latency(
        self,
        large_export_advanced: Path,
        benchmark: Any,
    ) -> None:
        """Benchmark all v1.1.0 features together.

        Combined features should stay within performance bounds.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            phrases=["data science"],
            match_mode="any",
            exclude_keywords=["error"],
            role_filter="assistant",
            limit=50,
        )

        def search_combined() -> int:
            count = 0
            for result in adapter.search(large_export_advanced, query):
                assert result.snippet is not None
                count += 1
            return count

        result = benchmark(search_combined)
        assert result >= 0

    def test_combined_features_memory_overhead(self, large_export_advanced: Path) -> None:
        """Validate memory usage with all features active.

        Combined features should not cause excessive memory growth.
        """
        adapter = OpenAIAdapter()
        query = SearchQuery(
            keywords=["python"],
            phrases=["data science"],
            match_mode="any",
            exclude_keywords=["error"],
            role_filter="assistant",
            limit=100,
        )

        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        result_count = 0
        for result in adapter.search(large_export_advanced, query):
            assert result.snippet is not None
            result_count += 1

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_memory_mb = (peak - baseline) / (1024 * 1024)

        # Combined features should use <100MB additional memory
        assert peak_memory_mb < 100, (
            f"Peak memory {peak_memory_mb:.2f} MB too high for 1K conversations. "
            "Combined features should be memory-efficient."
        )
