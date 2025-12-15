window.BENCHMARK_DATA = {
  "lastUpdate": 1765780909459,
  "repoUrl": "https://github.com/aucontraire/echomine",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "49699333+dependabot[bot]@users.noreply.github.com",
            "name": "dependabot[bot]",
            "username": "dependabot[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "9bb3ca01099523d0f30ce2591143a52bed1c59ad",
          "message": "ci: bump actions/upload-artifact from 4 to 6 (#13)\n\nBumps [actions/upload-artifact](https://github.com/actions/upload-artifact) from 4 to 6.\n- [Release notes](https://github.com/actions/upload-artifact/releases)\n- [Commits](https://github.com/actions/upload-artifact/compare/v4...v6)\n\n---\nupdated-dependencies:\n- dependency-name: actions/upload-artifact\n  dependency-version: '6'\n  dependency-type: direct:production\n  update-type: version-update:semver-major\n...\n\nSigned-off-by: dependabot[bot] <support@github.com>\nCo-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
          "timestamp": "2025-12-14T22:39:16-08:00",
          "tree_id": "c3cee0a80edad4984c7b1ffd7f89af7b3c7fea90",
          "url": "https://github.com/aucontraire/echomine/commit/9bb3ca01099523d0f30ce2591143a52bed1c59ad"
        },
        "date": 1765780908910,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestPhraseSearchPerformance::test_phrase_search_latency",
            "value": 11.984260528590537,
            "unit": "iter/sec",
            "range": "stddev: 0.00852221876782572",
            "extra": "mean: 83.44277876923037 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestMatchModePerformance::test_match_mode_all_latency",
            "value": 12.136379257072077,
            "unit": "iter/sec",
            "range": "stddev: 0.009046749831680842",
            "extra": "mean: 82.39689769230661 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestExcludeKeywordsPerformance::test_exclude_keywords_latency",
            "value": 12.444103408791461,
            "unit": "iter/sec",
            "range": "stddev: 0.007346698796998693",
            "extra": "mean: 80.35934507692406 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestRoleFilterPerformance::test_role_filter_latency",
            "value": 12.598071827312475,
            "unit": "iter/sec",
            "range": "stddev: 0.0064658433583854235",
            "extra": "mean: 79.3772264285723 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestSnippetExtractionPerformance::test_snippet_extraction_latency",
            "value": 12.61835903605377,
            "unit": "iter/sec",
            "range": "stddev: 0.0063538192752833865",
            "extra": "mean: 79.24960742856919 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestCombinedFeaturesPerformance::test_all_features_combined_latency",
            "value": 12.563013429883508,
            "unit": "iter/sec",
            "range": "stddev: 0.00688464973213007",
            "extra": "mean: 79.59873684615431 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestListPerformance::test_list_10k_conversations_under_5_seconds",
            "value": 0.9698671116151601,
            "unit": "iter/sec",
            "range": "stddev: 0.030194739953694177",
            "extra": "mean: 1.031069089800002 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_json_parsing_latency",
            "value": 3.391714001992547,
            "unit": "iter/sec",
            "range": "stddev: 0.011632370133762946",
            "extra": "mean: 294.8361800000015 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_model_transformation_latency",
            "value": 0.9336914852117187,
            "unit": "iter/sec",
            "range": "stddev: 0.019412782056811746",
            "extra": "mean: 1.0710175854000057 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_search_10k_conversations_under_30_seconds",
            "value": 0.3608521562844775,
            "unit": "iter/sec",
            "range": "stddev: 0.0344984604106008",
            "extra": "mean: 2.7712180253999947 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_bm25_scoring_performance",
            "value": 0.34998043029127085,
            "unit": "iter/sec",
            "range": "stddev: 0.07552650020380723",
            "extra": "mean: 2.857302618800003 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchLatencyBreakdown::test_json_streaming_latency_for_search",
            "value": 0.35838018266812693,
            "unit": "iter/sec",
            "range": "stddev: 0.0818374147129465",
            "extra": "mean: 2.7903328597999972 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}