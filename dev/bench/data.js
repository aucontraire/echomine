window.BENCHMARK_DATA = {
  "lastUpdate": 1776358793477,
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
          "id": "871b99eec6af5c9c0e38b693ff899024b96b9af4",
          "message": "ci: bump softprops/action-gh-release from 2 to 3 (#18)\n\nBumps [softprops/action-gh-release](https://github.com/softprops/action-gh-release) from 2 to 3.\n- [Release notes](https://github.com/softprops/action-gh-release/releases)\n- [Changelog](https://github.com/softprops/action-gh-release/blob/master/CHANGELOG.md)\n- [Commits](https://github.com/softprops/action-gh-release/compare/v2...v3)\n\n---\nupdated-dependencies:\n- dependency-name: softprops/action-gh-release\n  dependency-version: '3'\n  dependency-type: direct:production\n  update-type: version-update:semver-major\n...\n\nSigned-off-by: dependabot[bot] <support@github.com>\nCo-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
          "timestamp": "2026-04-16T09:57:21-07:00",
          "tree_id": "23cc24a3d6f75620322d80a64887f36351a9bf3f",
          "url": "https://github.com/aucontraire/echomine/commit/871b99eec6af5c9c0e38b693ff899024b96b9af4"
        },
        "date": 1776358793065,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestPhraseSearchPerformance::test_phrase_search_latency",
            "value": 12.256929530536967,
            "unit": "iter/sec",
            "range": "stddev: 0.005956974986391705",
            "extra": "mean: 81.58650153846409 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestMatchModePerformance::test_match_mode_all_latency",
            "value": 12.266061567631498,
            "unit": "iter/sec",
            "range": "stddev: 0.006405497147450904",
            "extra": "mean: 81.5257606923209 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestExcludeKeywordsPerformance::test_exclude_keywords_latency",
            "value": 12.360232158626616,
            "unit": "iter/sec",
            "range": "stddev: 0.006368849772682948",
            "extra": "mean: 80.90462923077595 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestRoleFilterPerformance::test_role_filter_latency",
            "value": 12.355050570468515,
            "unit": "iter/sec",
            "range": "stddev: 0.006010139782874461",
            "extra": "mean: 80.93855984614387 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestSnippetExtractionPerformance::test_snippet_extraction_latency",
            "value": 12.448879001576612,
            "unit": "iter/sec",
            "range": "stddev: 0.005658455589977487",
            "extra": "mean: 80.32851792304777 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestCombinedFeaturesPerformance::test_all_features_combined_latency",
            "value": 12.414325540367498,
            "unit": "iter/sec",
            "range": "stddev: 0.00570140346101183",
            "extra": "mean: 80.55210061539898 msec\nrounds: 13"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestListPerformance::test_list_10k_conversations_under_5_seconds",
            "value": 0.9733149273381076,
            "unit": "iter/sec",
            "range": "stddev: 0.05562617313649733",
            "extra": "mean: 1.027416689000006 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_json_parsing_latency",
            "value": 3.264101283777908,
            "unit": "iter/sec",
            "range": "stddev: 0.007584808769818732",
            "extra": "mean: 306.36304240001664 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_model_transformation_latency",
            "value": 1.0135757841854423,
            "unit": "iter/sec",
            "range": "stddev: 0.02540448871209772",
            "extra": "mean: 986.6060492000088 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_search_10k_conversations_under_30_seconds",
            "value": 0.371876519914654,
            "unit": "iter/sec",
            "range": "stddev: 0.06877259703306161",
            "extra": "mean: 2.6890646395999966 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_bm25_scoring_performance",
            "value": 0.36866647587208656,
            "unit": "iter/sec",
            "range": "stddev: 0.0452160292339551",
            "extra": "mean: 2.712478799799965 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchLatencyBreakdown::test_json_streaming_latency_for_search",
            "value": 0.37122150436829454,
            "unit": "iter/sec",
            "range": "stddev: 0.04674839500797019",
            "extra": "mean: 2.693809459399972 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}