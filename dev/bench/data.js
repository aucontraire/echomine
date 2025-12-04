window.BENCHMARK_DATA = {
  "lastUpdate": 1764889595678,
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
          "id": "b3ca6951a7d20a70b0628306db1b3411ea70dba7",
          "message": "feat: v1.1.0 Advanced Search Enhancement Package (#10)\n\n* fix(search): resolve division by zero with --role system filter\n\n- Fix BM25 scorer crash when avg_doc_length is 0 (sparse system messages)\n- Add 5 edge case tests for BM25 zero/sparse corpus scenarios\n- Document filter combination logic (phrases OR keywords, then AND filters)\n- Comprehensive v1.1.0 feature documentation across all docs\n\nBug: Searching with --role system caused \"float division by zero\" when\nconversations had sparse or empty system messages.\n\nFix: Guard against zero division in BM25 scorer using ternary operator.\n\nDocumentation updates:\n- README.md, docs/cli-usage.md, docs/library-usage.md, docs/quickstart.md\n- docs/api/models/search.md, docs/index.md\n- specs/002-advanced-search/quickstart.md\n- src/echomine/cli/commands/search.py (docstring)\n\nTests: 859 passed, 7 skipped\n\n* docs(readme): fix broken links to constitution and quickstart\n\n- Constitution: specs/001-ai-chat-parser/constitution.md → .specify/memory/constitution.md\n- Quickstart: specs/001-ai-chat-parser/quickstart.md → docs/quickstart.md\n\n* chore: bump version to 1.1.0 for Advanced Search release\n\nNew features in v1.1.0:\n- Exact phrase matching (--phrase)\n- Boolean match mode (--match-mode all/any)\n- Exclude keywords (--exclude)\n- Role filtering (--role user/assistant/system)\n- Automatic snippet extraction in search results\n\n* fix: remove unused imports in test files\n\n* style: apply ruff formatting to all files\n\n* fix(ci): resolve Windows charmap encoding and pre-commit issues\n\n- Add global UTF-8 encoding configuration for Windows compatibility\n  in CLI entry point (_configure_encoding in app.py)\n- Fix mypy strict Counter type error in get.py by using Counter[str]\n- Add structlog to pre-commit mypy additional_dependencies\n- Add ruff per-file-ignores for examples/ directory (T201, S101, DTZ001)\n\nFixes Windows CI test failures caused by cp1252 encoding on Unicode output.\n\n* fix(export): add trailing newline to markdown output for POSIX compliance\n\nThe pre-commit end-of-file-fixer added trailing newlines to expected.md\nfiles, causing golden master tests to fail. Fixed by:\n- Adding trailing newline to MarkdownExporter output (POSIX convention)\n- Regenerating expected.md for test 002 to match actual output\n\n* fix(export): strip trailing whitespace from markdown content\n\nEnsures markdown export output is compatible with pre-commit\ntrailing-whitespace hook by stripping trailing whitespace from\neach line of message content. Also adds POSIX-compliant trailing\nnewline.\n\n* chore(ci): exclude Windows-specific encoding code from coverage\n\nThe _configure_encoding() function only executes branches on Windows\nwhen encoding is not UTF-8. Adding pragma comments to exclude these\nplatform-specific lines from coverage reports.\n\n* test: fix coverage by reverting incorrect pragmas and adding proper tests\n\nPROBLEM:\n- PR #10 has Codecov patch coverage failure at 94.47% (target 90.27%)\n- Previous assistant incorrectly added pragma comments to testable code\n- Coverage gaps in snippet.py, openai.py, and app.py\n\nSOLUTION:\n1. Reverted incorrect pragma comments from non-OS-specific code:\n   - src/echomine/search/snippet.py: Removed pragmas from testable loops\n   - src/echomine/adapters/openai.py: Removed pragmas from phrase matching\n\n2. Added tests to cover missing branches:\n   - test_snippet.py: Added test for invalid message IDs in map\n   - test_search_phrase.py: Added tests for phrase+keyword zero score branch\n   - test_search_phrase.py: Added test for duplicate message ID prevention\n\n3. Fixed redundant conditional in openai.py:\n   - Removed \"if query.limit:\" check (limit is always > 0 per model)\n   - Simplified code by removing always-true conditional\n\n4. Kept correct pragmas for truly untestable code:\n   - app.py: OS-specific Windows encoding (import io)\n   - app.py: Exception handlers (typer.Exit, KeyboardInterrupt, Exception)\n\nRESULTS:\n- All 863 tests pass\n- Overall coverage: 93.39% (up from ~91%)\n- snippet.py: 97.56% coverage (only 2 minor branch partials)\n- openai.py: 96.06% coverage\n- No mypy errors (--strict mode)\n\nCOMPLIANCE:\n- Constitution Principle III: TDD - Tests written for all coverage gaps\n- Constitution Principle VI: Strict typing - mypy --strict passes\n- Only use pragmas for truly untestable code (OS-specific, signals)",
          "timestamp": "2025-12-04T15:04:00-08:00",
          "tree_id": "1bf1e2538585737b21ca983f2b426c517a60e1c4",
          "url": "https://github.com/aucontraire/echomine/commit/b3ca6951a7d20a70b0628306db1b3411ea70dba7"
        },
        "date": 1764889594650,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestPhraseSearchPerformance::test_phrase_search_latency",
            "value": 12.516311424677605,
            "unit": "iter/sec",
            "range": "stddev: 0.006109944004790386",
            "extra": "mean: 79.89574292857274 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestMatchModePerformance::test_match_mode_all_latency",
            "value": 12.704720335659708,
            "unit": "iter/sec",
            "range": "stddev: 0.005998106426667052",
            "extra": "mean: 78.71090221428899 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestExcludeKeywordsPerformance::test_exclude_keywords_latency",
            "value": 12.866925663440894,
            "unit": "iter/sec",
            "range": "stddev: 0.00533631544570887",
            "extra": "mean: 77.7186428333323 msec\nrounds: 12"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestRoleFilterPerformance::test_role_filter_latency",
            "value": 12.835382721099542,
            "unit": "iter/sec",
            "range": "stddev: 0.005783789017059614",
            "extra": "mean: 77.9096363333321 msec\nrounds: 12"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestSnippetExtractionPerformance::test_snippet_extraction_latency",
            "value": 12.709207513098246,
            "unit": "iter/sec",
            "range": "stddev: 0.005735290554045498",
            "extra": "mean: 78.68311214286094 msec\nrounds: 14"
          },
          {
            "name": "tests/performance/test_advanced_search_benchmark.py::TestCombinedFeaturesPerformance::test_all_features_combined_latency",
            "value": 12.838124642699064,
            "unit": "iter/sec",
            "range": "stddev: 0.005763135297274294",
            "extra": "mean: 77.89299666666594 msec\nrounds: 12"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestListPerformance::test_list_10k_conversations_under_5_seconds",
            "value": 0.9748010423225494,
            "unit": "iter/sec",
            "range": "stddev: 0.028988087910714114",
            "extra": "mean: 1.0258503597999975 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_json_parsing_latency",
            "value": 3.3420698939442945,
            "unit": "iter/sec",
            "range": "stddev: 0.011018152200897652",
            "extra": "mean: 299.21576499999674 msec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_list_benchmark.py::TestLatencyBreakdown::test_model_transformation_latency",
            "value": 0.9921765466437743,
            "unit": "iter/sec",
            "range": "stddev: 0.019178703571340744",
            "extra": "mean: 1.0078851423999993 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_search_10k_conversations_under_30_seconds",
            "value": 0.3639930397277145,
            "unit": "iter/sec",
            "range": "stddev: 0.07978846039184181",
            "extra": "mean: 2.747305280200004 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchPerformance::test_bm25_scoring_performance",
            "value": 0.3592554637215615,
            "unit": "iter/sec",
            "range": "stddev: 0.028988148412599033",
            "extra": "mean: 2.7835345623999843 sec\nrounds: 5"
          },
          {
            "name": "tests/performance/test_search_benchmark.py::TestSearchLatencyBreakdown::test_json_streaming_latency_for_search",
            "value": 0.37717460968867067,
            "unit": "iter/sec",
            "range": "stddev: 0.062477984112749636",
            "extra": "mean: 2.65129193300001 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}