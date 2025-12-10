window.BENCHMARK_DATA = {
  "lastUpdate": 1765400858678,
  "repoUrl": "https://github.com/aucontraire/echomine",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "ocontreras.sf@gmail.com",
            "name": "aucontraire",
            "username": "aucontraire"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "c7c082357945d69e6023dbec48390d88422de56c",
          "message": "feat: v1.3.0 multi-provider support with Anthropic Claude adapter (#12)\n\n* feat: v1.3.0 multi-provider support with Anthropic Claude adapter\n\nAdd ClaudeAdapter implementing ConversationProvider protocol with full parity\nto OpenAIAdapter. Enables echomine to parse both OpenAI and Anthropic Claude\nconversation exports through unified API with automatic provider detection.\n\nCore Features:\n- ClaudeAdapter with ijson streaming parser (O(1) memory usage)\n- Auto-detection from export structure (chat_messages vs mapping field)\n- Explicit --provider flag for all CLI commands (list/search/get/export/stats)\n- Claude-specific schema handling (content blocks, tool messages, empty convos)\n- Provider detection utility (detect_provider, get_adapter functions)\n\nLibrary API:\n- from echomine import ClaudeAdapter\n- from echomine.cli.provider import detect_provider, get_adapter\n- Same search/stream/get methods as OpenAIAdapter (protocol compliance)\n\nClaude Export Support:\n- uuid → id, name → title, chat_messages → messages mappings\n- Multi-block content extraction (text blocks, skip tool_use/tool_result)\n- Timezone-aware timestamp parsing with fallback to created_at\n- Graceful empty conversation handling (placeholder message pattern)\n\nQuality Metrics:\n- 80+ new tests (unit/integration/contract/performance)\n- 95%+ coverage on ClaudeAdapter paths\n- mypy --strict: 0 errors, ruff: all passed\n- BM25 ranking parity verified between providers\n\nDocumentation:\n- Complete spec suite in specs/004-claude-adapter/\n- API docs in docs/api/adapters/claude.md\n- Updated quickstart with Claude examples\n- Validation report with 100% FR coverage\n\nVersion: 1.2.0 → 1.3.0\nFiles: 62 changed, 10,453 insertions(+), 206 deletions(-)\n\n* test: improve unit test coverage across core modules\n\nAdd comprehensive unit tests to address Codecov feedback on PR #12:\n- claude.py: 92.30% → 99.14% (new test_claude_adapter_coverage.py)\n- provider.py: 93.93% → 100% (enhanced test_provider_detection.py)\n- markdown.py: 78.43% → 92.45% (new test_markdown_coverage.py)\n- list.py: 87.50% → 98.08% (new test_list_search_stats_coverage.py)\n- search.py: 93.90% → 98.25% (new test_list_search_stats_coverage.py)\n- statistics.py: 95.65% → 97.89% (new test_list_search_stats_coverage.py)\n\nAll 1341 tests pass, mypy --strict compliant, ruff clean.\n\n* fix(test): increase early termination threshold for CI variance\n\nIncrease test threshold from 5s to 6s to account for CI environment\nvariance. Test was failing at 5.11s which is within acceptable\nperformance but marginally over the previous threshold.",
          "timestamp": "2025-12-10T13:04:49-08:00",
          "tree_id": "64396ab4107e0655887f5b968e618361eed5fecd",
          "url": "https://github.com/aucontraire/echomine/commit/c7c082357945d69e6023dbec48390d88422de56c"
        },
        "date": 1765400857951,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestPhraseSearchPerformance::test_phrase_search_latency",
            "value": 12.24853832091508,
            "unit": "iter/sec",
            "range": "stddev: 0.006444891908349223",
            "extra": "mean: 81.6423946923073 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestMatchModePerformance::test_match_mode_all_latency",
            "value": 12.379655252465199,
            "unit": "iter/sec",
            "range": "stddev: 0.006330336551026185",
            "extra": "mean: 80.77769369230754 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestExcludeKeywordsPerformance::test_exclude_keywords_latency",
            "value": 12.393810061815776,
            "unit": "iter/sec",
            "range": "stddev: 0.006573488983035614",
            "extra": "mean: 80.6854385384613 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestRoleFilterPerformance::test_role_filter_latency",
            "value": 12.464196571379173,
            "unit": "iter/sec",
            "range": "stddev: 0.0062835622218079135",
            "extra": "mean: 80.22980015384572 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestSnippetExtractionPerformance::test_snippet_extraction_latency",
            "value": 12.527208548902331,
            "unit": "iter/sec",
            "range": "stddev: 0.006041028558790568",
            "extra": "mean: 79.82624350000326 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestCombinedFeaturesPerformance::test_all_features_combined_latency",
            "value": 12.621667059225166,
            "unit": "iter/sec",
            "range": "stddev: 0.005822681549952522",
            "extra": "mean: 79.22883683333264 msec\nrounds: 12"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestListPerformance::test_list_10k_conversations_under_5_seconds",
            "value": 0.9854618698966686,
            "unit": "iter/sec",
            "range": "stddev: 0.020594850647286927",
            "extra": "mean: 1.0147526053999996 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_json_parsing_latency",
            "value": 3.3543720577469416,
            "unit": "iter/sec",
            "range": "stddev: 0.008820247999207723",
            "extra": "mean: 298.11839079999913 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_model_transformation_latency",
            "value": 0.9970151505985624,
            "unit": "iter/sec",
            "range": "stddev: 0.04604043462895072",
            "extra": "mean: 1.0029937853999968 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_search_10k_conversations_under_30_seconds",
            "value": 0.3791014619822544,
            "unit": "iter/sec",
            "range": "stddev: 0.0554767270364258",
            "extra": "mean: 2.6378162583999996 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_bm25_scoring_performance",
            "value": 0.36673000829081215,
            "unit": "iter/sec",
            "range": "stddev: 0.06203671312497776",
            "extra": "mean: 2.726801672600004 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchLatencyBreakdown::test_json_streaming_latency_for_search",
            "value": 0.37797849493862834,
            "unit": "iter/sec",
            "range": "stddev: 0.04178795827092417",
            "extra": "mean: 2.6456531611999994 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}