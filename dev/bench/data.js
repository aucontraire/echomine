window.BENCHMARK_DATA = {
  "lastUpdate": 1782600871413,
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
          "id": "aead8320da2fb760de2a5bbe86992b091be49d91",
          "message": "feat: surface LLM model identifier on Message and Conversation (v1.5.0) (#24)\n\n- Add Message.model (str | None) for per-message model provenance\n- Add Conversation.models_used (list[str]) for conversation-level summary\n- OpenAI adapter reads metadata.model_slug, falls back to default_model_slug\n- Claude adapter: None/empty (Anthropic export has no model info)\n- 13 new tests covering both adapters and model defaults\n- Docs: library-usage, API reference, CHANGELOG, README updated",
          "timestamp": "2026-06-27T15:51:52-07:00",
          "tree_id": "8a1d73725a606d07b234f5b90624477e0ba4c534",
          "url": "https://github.com/aucontraire/echomine/commit/aead8320da2fb760de2a5bbe86992b091be49d91"
        },
        "date": 1782600870247,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestPhraseSearchPerformance::test_phrase_search_latency",
            "value": 12.000917442444015,
            "unit": "iter/sec",
            "range": "stddev: 0.0048386876570851904",
            "extra": "mean: 83.32696269230794 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestMatchModePerformance::test_match_mode_all_latency",
            "value": 12.116171567897416,
            "unit": "iter/sec",
            "range": "stddev: 0.00424116536269869",
            "extra": "mean: 82.53432153846063 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestExcludeKeywordsPerformance::test_exclude_keywords_latency",
            "value": 12.118118978404564,
            "unit": "iter/sec",
            "range": "stddev: 0.004214453290283327",
            "extra": "mean: 82.52105807692416 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestRoleFilterPerformance::test_role_filter_latency",
            "value": 12.1556841112657,
            "unit": "iter/sec",
            "range": "stddev: 0.0044137525190444974",
            "extra": "mean: 82.26604038461443 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestSnippetExtractionPerformance::test_snippet_extraction_latency",
            "value": 12.150289332643508,
            "unit": "iter/sec",
            "range": "stddev: 0.004258261333234343",
            "extra": "mean: 82.30256684615365 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestCombinedFeaturesPerformance::test_all_features_combined_latency",
            "value": 12.183091068788077,
            "unit": "iter/sec",
            "range": "stddev: 0.004313584427422463",
            "extra": "mean: 82.08097553845798 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestListPerformance::test_list_10k_conversations_under_5_seconds",
            "value": 0.9349142951462998,
            "unit": "iter/sec",
            "range": "stddev: 0.04345567811978899",
            "extra": "mean: 1.0696167607999996 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_json_parsing_latency",
            "value": 3.320189394121397,
            "unit": "iter/sec",
            "range": "stddev: 0.0030177267090095512",
            "extra": "mean: 301.18763760000036 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_model_transformation_latency",
            "value": 0.9532667881632871,
            "unit": "iter/sec",
            "range": "stddev: 0.023286606279620703",
            "extra": "mean: 1.0490242736000028 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_search_10k_conversations_under_30_seconds",
            "value": 0.36715434258217766,
            "unit": "iter/sec",
            "range": "stddev: 0.04074528952808869",
            "extra": "mean: 2.7236502037999912 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_bm25_scoring_performance",
            "value": 0.3597103353704697,
            "unit": "iter/sec",
            "range": "stddev: 0.03581389191309611",
            "extra": "mean: 2.7800146442000027 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchLatencyBreakdown::test_json_streaming_latency_for_search",
            "value": 0.3725322887956125,
            "unit": "iter/sec",
            "range": "stddev: 0.04551715549572095",
            "extra": "mean: 2.684331076999996 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}