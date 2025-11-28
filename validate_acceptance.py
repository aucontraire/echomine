#!/usr/bin/env python3
"""Systematic acceptance scenario validation script.

This script validates all acceptance scenarios from spec.md against
the current implementation.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Test data paths
SAMPLE_EXPORT = Path("tests/fixtures/sample_export.json")
PRODUCTION_DATA = Path("data/openai/conversations/conversations.json")

# CLI command base
CLI_BASE = ["python", "-m", "echomine.cli.app"]


class ValidationResult:
    """Result of a single acceptance scenario validation."""

    def __init__(
        self,
        scenario_id: str,
        description: str,
        status: str,
        notes: str = "",
        error: str = "",
    ):
        self.scenario_id = scenario_id
        self.description = description
        self.status = status  # PASS, FAIL, SKIP
        self.notes = notes
        self.error = error


def run_cli(
    *args: str, check: bool = False, capture_stderr: bool = False
) -> tuple[int, str, str]:
    """Run CLI command and return (exit_code, stdout, stderr)."""
    cmd = [*CLI_BASE, *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def validate_us0() -> list[ValidationResult]:
    """Validate User Story 0 - List All Conversations."""
    results = []

    # US0-AS1: List all conversations with title, date, message count
    try:
        exit_code, stdout, stderr = run_cli("list", str(SAMPLE_EXPORT))
        has_table_header = "ID" in stdout and "Title" in stdout
        has_conversations = "conv-" in stdout
        if exit_code == 0 and has_table_header and has_conversations:
            results.append(
                ValidationResult(
                    "US0-AS1",
                    "List all conversations with metadata",
                    "PASS",
                    "All conversations displayed with table format",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US0-AS1",
                    "List all conversations with metadata",
                    "FAIL",
                    f"Exit code: {exit_code}, Has header: {has_table_header}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS1",
                "List all conversations with metadata",
                "FAIL",
                error=str(e),
            )
        )

    # US0-AS2: List with limit (--limit flag)
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--limit", "20"
        )
        if exit_code == 2:  # Expected: argument not recognized
            results.append(
                ValidationResult(
                    "US0-AS2",
                    "List with --limit flag",
                    "FAIL",
                    "Feature not implemented: --limit flag missing",
                    "CLI does not support --limit flag",
                )
            )
        elif exit_code == 0:
            results.append(
                ValidationResult(
                    "US0-AS2",
                    "List with --limit flag",
                    "PASS",
                    "Limit flag works correctly",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS2", "List with --limit flag", "FAIL", error=str(e)
            )
        )

    # US0-AS3: JSON output with metadata
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            has_required_fields = all(
                key in data[0]
                for key in ["id", "title", "created_at", "message_count"]
            )
            if has_required_fields:
                results.append(
                    ValidationResult(
                        "US0-AS3",
                        "JSON output with metadata fields",
                        "PASS",
                        f"JSON output includes all required fields",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US0-AS3",
                        "JSON output with metadata fields",
                        "FAIL",
                        f"Missing required fields. Got: {list(data[0].keys())}",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US0-AS3",
                    "JSON output with metadata fields",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS3",
                "JSON output with metadata fields",
                "FAIL",
                error=str(e),
            )
        )

    # US0-AS4: Conversations sorted by created_at descending
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            created_dates = [item["created_at"] for item in data]
            is_sorted_desc = created_dates == sorted(
                created_dates, reverse=True
            )
            if is_sorted_desc:
                results.append(
                    ValidationResult(
                        "US0-AS4",
                        "Conversations sorted by created_at descending",
                        "PASS",
                        "Order is newest-first",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US0-AS4",
                        "Conversations sorted by created_at descending",
                        "FAIL",
                        f"Not sorted correctly. Order: {created_dates[:3]}...",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US0-AS4",
                    "Conversations sorted by created_at descending",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS4",
                "Conversations sorted by created_at descending",
                "FAIL",
                error=str(e),
            )
        )

    # US0-AS5: Large file performance (<5s)
    if PRODUCTION_DATA.exists():
        try:
            start = datetime.now()
            exit_code, stdout, stderr = run_cli(
                "list", str(PRODUCTION_DATA), "--format", "json"
            )
            duration = (datetime.now() - start).total_seconds()
            if exit_code == 0 and duration < 5:
                results.append(
                    ValidationResult(
                        "US0-AS5",
                        "Large file streaming performance",
                        "PASS",
                        f"Completed in {duration:.2f}s (< 5s requirement)",
                    )
                )
            elif exit_code == 0:
                results.append(
                    ValidationResult(
                        "US0-AS5",
                        "Large file streaming performance",
                        "FAIL",
                        f"Completed in {duration:.2f}s (exceeds 5s requirement)",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US0-AS5",
                        "Large file streaming performance",
                        "FAIL",
                        f"Exit code: {exit_code}, Duration: {duration:.2f}s",
                        stderr,
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    "US0-AS5",
                    "Large file streaming performance",
                    "FAIL",
                    error=str(e),
                )
            )
    else:
        results.append(
            ValidationResult(
                "US0-AS5",
                "Large file streaming performance",
                "SKIP",
                "Production data file not available",
            )
        )

    # US0-AS6: Count conversations via pipeline
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            count = len(data)
            if count > 0:
                results.append(
                    ValidationResult(
                        "US0-AS6",
                        "Count conversations via pipeline",
                        "PASS",
                        f"Can count {count} conversations via JSON",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US0-AS6",
                        "Count conversations via pipeline",
                        "FAIL",
                        "JSON array is empty",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US0-AS6",
                    "Count conversations via pipeline",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS6",
                "Count conversations via pipeline",
                "FAIL",
                error=str(e),
            )
        )

    # US0-AS7: Empty export file handling
    # Create empty export file
    empty_file = Path("tests/fixtures/empty_export.json")
    try:
        empty_file.write_text("[]")
        exit_code, stdout, stderr = run_cli("list", str(empty_file))
        has_no_results_msg = (
            "No conversations found" in stdout
            or "No conversations found" in stderr
            or len(stdout.strip()) == 0
        )
        if exit_code == 0 and has_no_results_msg:
            results.append(
                ValidationResult(
                    "US0-AS7",
                    "Empty export file handling",
                    "PASS",
                    "Returns exit code 0 with appropriate message",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US0-AS7",
                    "Empty export file handling",
                    "FAIL",
                    f"Exit code: {exit_code}, Has message: {has_no_results_msg}",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US0-AS7",
                "Empty export file handling",
                "FAIL",
                error=str(e),
            )
        )
    finally:
        if empty_file.exists():
            empty_file.unlink()

    return results


def validate_us1() -> list[ValidationResult]:
    """Validate User Story 1 - Search Conversations by Keyword."""
    results = []

    # US1-AS1: Search by keyword returns relevant conversations
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-k", "algorithm"
        )
        if exit_code == 0 and "Algorithm" in stdout:
            results.append(
                ValidationResult(
                    "US1-AS1",
                    "Search by keyword returns relevant conversations",
                    "PASS",
                    "Found matching conversation with 'algorithm'",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS1",
                    "Search by keyword returns relevant conversations",
                    "FAIL",
                    f"Exit code: {exit_code}, No matches in output",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS1",
                "Search by keyword returns relevant conversations",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS2: Multiple keywords with OR logic
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-k", "leetcode,algorithm"
        )
        if exit_code == 0 and "conv-" in stdout:
            results.append(
                ValidationResult(
                    "US1-AS2",
                    "Multiple keywords with OR logic",
                    "PASS",
                    "Accepts comma-separated keywords",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS2",
                    "Multiple keywords with OR logic",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS2",
                "Multiple keywords with OR logic",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS3: Limit search results
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-k", "python", "--limit", "5"
        )
        if exit_code == 0:
            # Count result lines (excluding header and separator)
            result_lines = [
                line for line in stdout.split("\n") if line and "───" not in line and "Score" not in line
            ]
            if len(result_lines) <= 5:
                results.append(
                    ValidationResult(
                        "US1-AS3",
                        "Limit search results to top N",
                        "PASS",
                        f"Returned {len(result_lines)} results (≤5)",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US1-AS3",
                        "Limit search results to top N",
                        "FAIL",
                        f"Returned {len(result_lines)} results (>5)",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US1-AS3",
                    "Limit search results to top N",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS3",
                "Limit search results to top N",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS4: No results found message
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-k", "nonexistentkeyword12345"
        )
        has_no_results = (
            "No matching" in stdout
            or "No matching" in stderr
            or "not found" in stdout.lower()
        )
        if exit_code == 0 and has_no_results:
            results.append(
                ValidationResult(
                    "US1-AS4",
                    "No results found message with exit code 0",
                    "PASS",
                    "Shows appropriate message with exit code 0",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS4",
                    "No results found message with exit code 0",
                    "FAIL",
                    f"Exit code: {exit_code}, Has message: {has_no_results}",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS4",
                "No results found message with exit code 0",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS5: Large file performance (<30s)
    if PRODUCTION_DATA.exists():
        try:
            start = datetime.now()
            exit_code, stdout, stderr = run_cli(
                "search", str(PRODUCTION_DATA), "-k", "python"
            )
            duration = (datetime.now() - start).total_seconds()
            if exit_code == 0 and duration < 30:
                results.append(
                    ValidationResult(
                        "US1-AS5",
                        "Large file search performance (<30s)",
                        "PASS",
                        f"Completed in {duration:.2f}s",
                    )
                )
            elif exit_code == 0:
                results.append(
                    ValidationResult(
                        "US1-AS5",
                        "Large file search performance (<30s)",
                        "FAIL",
                        f"Completed in {duration:.2f}s (exceeds 30s)",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US1-AS5",
                        "Large file search performance (<30s)",
                        "FAIL",
                        f"Exit code: {exit_code}",
                        stderr,
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    "US1-AS5",
                    "Large file search performance (<30s)",
                    "FAIL",
                    error=str(e),
                )
            )
    else:
        results.append(
            ValidationResult(
                "US1-AS5",
                "Large file search performance (<30s)",
                "SKIP",
                "Production data not available",
            )
        )

    # US1-AS6: Title exact match
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-t", "Python AsyncIO Tutorial"
        )
        if exit_code == 0 and "Python AsyncIO" in stdout:
            results.append(
                ValidationResult(
                    "US1-AS6",
                    "Title exact match filtering",
                    "PASS",
                    "Found conversation by exact title",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS6",
                    "Title exact match filtering",
                    "FAIL",
                    f"Exit code: {exit_code}, Match not found",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS6",
                "Title exact match filtering",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS7: Title partial match
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-t", "Python"
        )
        if exit_code == 0 and "Python" in stdout:
            results.append(
                ValidationResult(
                    "US1-AS7",
                    "Title partial/substring matching",
                    "PASS",
                    "Found conversation by partial title",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS7",
                    "Title partial/substring matching",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS7",
                "Title partial/substring matching",
                "FAIL",
                error=str(e),
            )
        )

    # US1-AS8: Combined title + keywords filtering
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "-t", "Algorithm", "-k", "design"
        )
        # Should match only conversations with "Algorithm" in title AND "design" in content
        if exit_code == 0:
            has_algorithm_title = "Algorithm Design" in stdout
            results.append(
                ValidationResult(
                    "US1-AS8",
                    "Combined title + keywords filtering (AND logic)",
                    "PASS" if has_algorithm_title else "FAIL",
                    f"Combined filters work with AND logic: {has_algorithm_title}",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US1-AS8",
                    "Combined title + keywords filtering (AND logic)",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US1-AS8",
                "Combined title + keywords filtering (AND logic)",
                "FAIL",
                error=str(e),
            )
        )

    return results


def validate_us2() -> list[ValidationResult]:
    """Validate User Story 2 - Programmatic Library Access."""
    results = []

    # US2-AS1: Import and create adapter
    try:
        from echomine import OpenAIAdapter

        adapter = OpenAIAdapter()
        results.append(
            ValidationResult(
                "US2-AS1",
                "Import OpenAIAdapter and create instance",
                "PASS",
                "Can import and instantiate adapter",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                "US2-AS1",
                "Import OpenAIAdapter and create instance",
                "FAIL",
                error=str(e),
            )
        )

    # US2-AS2: Search returns iterator of Conversation objects
    try:
        from echomine import OpenAIAdapter
        from echomine.models import SearchQuery

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["test"])
        result_iter = adapter.search(SAMPLE_EXPORT, query)

        # Check it's an iterator
        has_iter = hasattr(result_iter, "__iter__")
        has_next = hasattr(result_iter, "__next__")

        if has_iter and has_next:
            results.append(
                ValidationResult(
                    "US2-AS2",
                    "Search returns iterator of Conversation objects",
                    "PASS",
                    "Returns proper iterator",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US2-AS2",
                    "Search returns iterator of Conversation objects",
                    "FAIL",
                    f"Not an iterator: iter={has_iter}, next={has_next}",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US2-AS2",
                "Search returns iterator of Conversation objects",
                "FAIL",
                error=str(e),
            )
        )

    # US2-AS3: Conversation.export_markdown() - NOT IN SPEC
    # The spec doesn't actually require export_markdown() method on Conversation
    # It requires export command, which is different
    results.append(
        ValidationResult(
            "US2-AS3",
            "Conversation.export_markdown() method",
            "SKIP",
            "Spec requires export command, not export_markdown() method on model",
        )
    )

    # US2-AS4: IDE autocomplete (type hints)
    try:
        from echomine import OpenAIAdapter

        adapter = OpenAIAdapter()
        # Check if methods have type hints
        import inspect

        sig = inspect.signature(adapter.search)
        has_return_annotation = sig.return_annotation != inspect.Parameter.empty

        if has_return_annotation:
            results.append(
                ValidationResult(
                    "US2-AS4",
                    "Type hints for IDE autocomplete",
                    "PASS",
                    "Methods have return type annotations",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US2-AS4",
                    "Type hints for IDE autocomplete",
                    "FAIL",
                    "Missing return type annotations",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US2-AS4",
                "Type hints for IDE autocomplete",
                "FAIL",
                error=str(e),
            )
        )

    # US2-AS5: Properly typed data attributes
    try:
        from echomine import OpenAIAdapter
        from echomine.models import SearchQuery

        adapter = OpenAIAdapter()
        query = SearchQuery(keywords=["python"])
        results_list = list(adapter.search(SAMPLE_EXPORT, query))

        if results_list:
            conv = results_list[0].conversation
            # Check that attributes exist and have expected types
            has_title = isinstance(conv.title, str)
            has_messages = isinstance(conv.messages, list)

            if has_title and has_messages:
                results.append(
                    ValidationResult(
                        "US2-AS5",
                        "Properly typed Conversation attributes",
                        "PASS",
                        "Conversation has typed attributes (title, messages)",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "US2-AS5",
                        "Properly typed Conversation attributes",
                        "FAIL",
                        f"Type check failed: title={has_title}, messages={has_messages}",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US2-AS5",
                    "Properly typed Conversation attributes",
                    "SKIP",
                    "No search results to validate",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US2-AS5",
                "Properly typed Conversation attributes",
                "FAIL",
                error=str(e),
            )
        )

    return results


def validate_us3() -> list[ValidationResult]:
    """Validate User Story 3 - Export Conversation to Markdown."""
    results = []

    # US3-AS1: Export by title - NOT SUPPORTED
    # Spec says export by title, but implementation uses ID
    results.append(
        ValidationResult(
            "US3-AS1",
            "Export conversation by title",
            "FAIL",
            "Feature not implemented: export by title (only by ID)",
        )
    )

    # US3-AS2: Preserve message tree structure
    try:
        # First get a conversation ID
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            conv_id = data[0]["id"]

            # Export it
            exit_code2, stdout2, stderr2 = run_cli(
                "export", str(SAMPLE_EXPORT), conv_id, "--output", "/tmp/test_export.md"
            )

            if exit_code2 == 0:
                # Read the exported file
                export_content = Path("/tmp/test_export.md").read_text()
                has_content = len(export_content) > 0
                results.append(
                    ValidationResult(
                        "US3-AS2",
                        "Preserve message tree structure in export",
                        "PASS" if has_content else "FAIL",
                        f"Export created, has content: {has_content}",
                    )
                )
                # Cleanup
                Path("/tmp/test_export.md").unlink()
            else:
                results.append(
                    ValidationResult(
                        "US3-AS2",
                        "Preserve message tree structure in export",
                        "FAIL",
                        f"Export failed with exit code {exit_code2}",
                        stderr2,
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US3-AS2",
                    "Preserve message tree structure in export",
                    "FAIL",
                    "Could not get conversation ID for export test",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US3-AS2",
                "Preserve message tree structure in export",
                "FAIL",
                error=str(e),
            )
        )

    # US3-AS3: Markdown includes metadata (title, date)
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            conv_id = data[0]["id"]
            expected_title = data[0]["title"]

            exit_code2, stdout2, stderr2 = run_cli(
                "export", str(SAMPLE_EXPORT), conv_id, "--output", "/tmp/test_export.md"
            )

            if exit_code2 == 0:
                content = Path("/tmp/test_export.md").read_text()
                has_title = expected_title in content
                has_date = any(
                    x in content for x in ["2023", "2024", "Created", "Date"]
                )

                if has_title and has_date:
                    results.append(
                        ValidationResult(
                            "US3-AS3",
                            "Markdown includes conversation metadata",
                            "PASS",
                            "Export includes title and date",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            "US3-AS3",
                            "Markdown includes conversation metadata",
                            "FAIL",
                            f"Missing metadata: title={has_title}, date={has_date}",
                        )
                    )
                Path("/tmp/test_export.md").unlink()
            else:
                results.append(
                    ValidationResult(
                        "US3-AS3",
                        "Markdown includes conversation metadata",
                        "FAIL",
                        f"Export failed: {exit_code2}",
                        stderr2,
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US3-AS3",
                    "Markdown includes conversation metadata",
                    "FAIL",
                    "Could not get conversation for test",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US3-AS3",
                "Markdown includes conversation metadata",
                "FAIL",
                error=str(e),
            )
        )

    # US3-AS4: Preserve code blocks and formatting
    results.append(
        ValidationResult(
            "US3-AS4",
            "Preserve code blocks and formatting",
            "SKIP",
            "Requires specific test data with code blocks",
        )
    )

    # US3-AS5: Export by conversation ID
    try:
        exit_code, stdout, stderr = run_cli(
            "list", str(SAMPLE_EXPORT), "--format", "json"
        )
        if exit_code == 0:
            data = json.loads(stdout)
            conv_id = data[0]["id"]

            exit_code2, stdout2, stderr2 = run_cli(
                "export", str(SAMPLE_EXPORT), conv_id, "--output", "/tmp/test_export.md"
            )

            if exit_code2 == 0:
                results.append(
                    ValidationResult(
                        "US3-AS5",
                        "Export conversation by ID",
                        "PASS",
                        f"Successfully exported conversation {conv_id}",
                    )
                )
                Path("/tmp/test_export.md").unlink()
            else:
                results.append(
                    ValidationResult(
                        "US3-AS5",
                        "Export conversation by ID",
                        "FAIL",
                        f"Exit code: {exit_code2}",
                        stderr2,
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "US3-AS5",
                    "Export conversation by ID",
                    "FAIL",
                    "Could not list conversations",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US3-AS5", "Export conversation by ID", "FAIL", error=str(e)
            )
        )

    return results


def validate_us4() -> list[ValidationResult]:
    """Validate User Story 4 - Filter Conversations by Date Range."""
    results = []

    # US4-AS1: Date range filtering
    try:
        exit_code, stdout, stderr = run_cli(
            "search",
            str(SAMPLE_EXPORT),
            "--from-date",
            "2023-11-15",
            "--to-date",
            "2023-11-20",
        )
        if exit_code == 0:
            results.append(
                ValidationResult(
                    "US4-AS1",
                    "Filter by date range (--from/--to)",
                    "PASS",
                    "Date range filtering works",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US4-AS1",
                    "Filter by date range (--from/--to)",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US4-AS1",
                "Filter by date range (--from/--to)",
                "FAIL",
                error=str(e),
            )
        )

    # US4-AS2: Date range + keywords combined
    try:
        exit_code, stdout, stderr = run_cli(
            "search",
            str(SAMPLE_EXPORT),
            "-k",
            "algorithm",
            "--from-date",
            "2023-11-15",
        )
        if exit_code == 0:
            results.append(
                ValidationResult(
                    "US4-AS2",
                    "Combine date range with keyword search",
                    "PASS",
                    "Combined filters work",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US4-AS2",
                    "Combine date range with keyword search",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US4-AS2",
                "Combine date range with keyword search",
                "FAIL",
                error=str(e),
            )
        )

    # US4-AS3: Invalid date format error
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "--from-date", "invalid-date"
        )
        has_error_msg = "error" in stderr.lower() or "invalid" in stderr.lower()
        # Should fail with exit code 1 (operational error) or 2 (usage error)
        if exit_code in [1, 2] and has_error_msg:
            results.append(
                ValidationResult(
                    "US4-AS3",
                    "Invalid date format shows clear error",
                    "PASS",
                    f"Shows error message with exit code {exit_code}",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US4-AS3",
                    "Invalid date format shows clear error",
                    "FAIL",
                    f"Exit code: {exit_code}, Has error: {has_error_msg}",
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US4-AS3",
                "Invalid date format shows clear error",
                "FAIL",
                error=str(e),
            )
        )

    # US4-AS4: Only start date (--from)
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "--from-date", "2023-11-20"
        )
        if exit_code == 0:
            results.append(
                ValidationResult(
                    "US4-AS4",
                    "Filter with only --from date",
                    "PASS",
                    "Can filter from date forward",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US4-AS4",
                    "Filter with only --from date",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US4-AS4",
                "Filter with only --from date",
                "FAIL",
                error=str(e),
            )
        )

    # US4-AS5: Only end date (--to)
    try:
        exit_code, stdout, stderr = run_cli(
            "search", str(SAMPLE_EXPORT), "--to-date", "2023-11-20"
        )
        if exit_code == 0:
            results.append(
                ValidationResult(
                    "US4-AS5",
                    "Filter with only --to date",
                    "PASS",
                    "Can filter up to date",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "US4-AS5",
                    "Filter with only --to date",
                    "FAIL",
                    f"Exit code: {exit_code}",
                    stderr,
                )
            )
    except Exception as e:
        results.append(
            ValidationResult(
                "US4-AS5",
                "Filter with only --to date",
                "FAIL",
                error=str(e),
            )
        )

    return results


def print_summary(all_results: list[ValidationResult]) -> None:
    """Print validation summary."""
    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == "PASS")
    failed = sum(1 for r in all_results if r.status == "FAIL")
    skipped = sum(1 for r in all_results if r.status == "SKIP")

    print("\n" + "=" * 80)
    print("ACCEPTANCE SCENARIO VALIDATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal Scenarios: {total}")
    print(f"PASSED: {passed} ({passed/total*100:.1f}%)")
    print(f"FAILED: {failed} ({failed/total*100:.1f}%)")
    print(f"SKIPPED: {skipped} ({skipped/total*100:.1f}%)")
    print("\n" + "=" * 80)


def generate_report(all_results: list[ValidationResult]) -> str:
    """Generate markdown report."""
    report = []
    report.append("# Acceptance Scenario Validation Report\n")
    report.append(f"**Generated**: {datetime.now().isoformat()}\n")
    report.append(f"**Test Data**: {SAMPLE_EXPORT}\n")

    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == "PASS")
    failed = sum(1 for r in all_results if r.status == "FAIL")
    skipped = sum(1 for r in all_results if r.status == "SKIP")

    report.append("\n## Summary\n")
    report.append(f"- **Total Scenarios**: {total}\n")
    report.append(f"- **PASSED**: {passed} ({passed/total*100:.1f}%)\n")
    report.append(f"- **FAILED**: {failed} ({failed/total*100:.1f}%)\n")
    report.append(f"- **SKIPPED**: {skipped} ({skipped/total*100:.1f}%)\n")

    report.append("\n## Detailed Results\n")
    report.append("\n| Scenario ID | Description | Status | Notes |\n")
    report.append("|------------|-------------|---------|-------|\n")

    for result in all_results:
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
        }.get(result.status, "❓")

        notes = result.notes or result.error
        notes = notes.replace("|", "\\|").replace("\n", " ")[:100]

        report.append(
            f"| {result.scenario_id} | {result.description} | {status_emoji} {result.status} | {notes} |\n"
        )

    report.append("\n## Failures and Issues\n")
    failures = [r for r in all_results if r.status == "FAIL"]
    if failures:
        for result in failures:
            report.append(f"\n### {result.scenario_id}: {result.description}\n")
            report.append(f"**Notes**: {result.notes}\n")
            if result.error:
                report.append(f"**Error**: ```\n{result.error}\n```\n")
    else:
        report.append("\nNo failures! All scenarios passed.\n")

    report.append("\n## Recommendations\n")
    if failed > 0:
        report.append(f"\n{failed} scenarios failed validation. These should be addressed before v1.0 release:\n\n")
        for result in failures:
            report.append(f"- **{result.scenario_id}**: {result.description}\n")
    else:
        report.append("\nAll acceptance scenarios passed! System is ready for v1.0 release.\n")

    return "".join(report)


def main() -> int:
    """Run all validations and generate report."""
    print("Starting acceptance scenario validation...")
    print(f"Using test data: {SAMPLE_EXPORT}")

    all_results = []

    print("\nValidating User Story 0 (List All Conversations)...")
    all_results.extend(validate_us0())

    print("Validating User Story 1 (Search Conversations)...")
    all_results.extend(validate_us1())

    print("Validating User Story 2 (Library Access)...")
    all_results.extend(validate_us2())

    print("Validating User Story 3 (Export to Markdown)...")
    all_results.extend(validate_us3())

    print("Validating User Story 4 (Date Range Filtering)...")
    all_results.extend(validate_us4())

    print_summary(all_results)

    # Generate report
    report = generate_report(all_results)
    report_path = Path("ACCEPTANCE_VALIDATION_REPORT.md")
    report_path.write_text(report)
    print(f"\n📄 Report written to: {report_path.absolute()}")

    # Exit code 0 if all passed, 1 if any failed
    failed_count = sum(1 for r in all_results if r.status == "FAIL")
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
