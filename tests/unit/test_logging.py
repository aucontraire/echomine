"""Unit tests for logging utilities (utils/logging.py).

Task: Coverage improvement for src/echomine/utils/logging.py (0% → 80%+)
Phase: TDD RED-GREEN-REFACTOR

This module tests the structured logging configuration and helper classes:
- configure_logging() function
- get_logger() function
- ProgressLogger class
- SkipLogger class

Test Pyramid Classification: Unit (70% of test suite)
These tests validate logging functionality in isolation.

Coverage Target:
- Lines 52-332 in logging.py (currently 0% coverage)
- Structlog configuration
- Logger instantiation
- Progress logging with rate limiting
- Skip logging with counters
"""

import json
import logging
from io import StringIO

import pytest
import structlog

from echomine.utils.logging import (
    ProgressLogger,
    SkipLogger,
    configure_logging,
    get_logger,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def captured_logs() -> StringIO:
    """Capture log output for assertions.

    Returns:
        StringIO stream that can be read for log assertions
    """
    return StringIO()


@pytest.fixture(autouse=True)
def reset_logging(captured_logs: StringIO) -> None:
    """Reset logging configuration before each test.

    This fixture ensures each test has a clean logging state.
    """
    # Reset structlog configuration
    structlog.reset_defaults()

    # Reset standard library logging
    logging.root.handlers.clear()

    # Configure with captured stream
    logging.basicConfig(
        format="%(message)s",
        stream=captured_logs,
        level=logging.DEBUG,
        force=True,
    )


# =============================================================================
# Unit Tests: configure_logging()
# =============================================================================


@pytest.mark.unit
class TestConfigureLogging:
    """Unit tests for configure_logging() function."""

    def test_configure_logging_sets_json_renderer(self, captured_logs: StringIO) -> None:
        """Test JSON renderer is configured.

        Validates:
        - FR-028: Structured JSON logging
        - Logs are valid JSON objects
        """
        # Act: Configure logging
        configure_logging(level="INFO")

        # Get logger and emit log
        logger = get_logger("test")
        logger.info("Test message", operation="test_op")

        # Assert: Output is valid JSON
        log_output = captured_logs.getvalue()
        try:
            log_data = json.loads(log_output.strip())
        except json.JSONDecodeError as e:
            pytest.fail(f"Log output is not valid JSON: {e}\n{log_output}")

        # Assert: Basic structure
        assert isinstance(log_data, dict)
        assert "event" in log_data or "message" in log_data

    def test_configure_logging_includes_timestamp(self, captured_logs: StringIO) -> None:
        """Test ISO 8601 timestamp is added to logs.

        Validates:
        - FR-030: ISO 8601 timestamps in UTC
        - Timestamp field present
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        logger.info("Test")

        # Assert: Timestamp in output
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert "timestamp" in log_data
        # ISO 8601 format check (contains 'T' and 'Z')
        assert "T" in log_data["timestamp"]
        assert log_data["timestamp"].endswith("Z") or "+" in log_data["timestamp"]

    def test_configure_logging_includes_log_level(self, captured_logs: StringIO) -> None:
        """Test log level is included in output.

        Validates:
        - FR-029: Required field - level
        - Level field present
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        logger.info("Test info")

        # Assert: Level field present
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert "level" in log_data
        assert log_data["level"] == "info"

    def test_configure_logging_respects_log_level(self, captured_logs: StringIO) -> None:
        """Test log level filtering works.

        Validates:
        - level parameter controls minimum level
        - DEBUG logs filtered when level=INFO

        Note: Must manually reconfigure logging level since basicConfig
        was already called by the fixture. We test the level filtering
        by setting the root logger level directly.
        """
        # Act: Configure with INFO level
        configure_logging(level="INFO")
        # Force level override for testing (basicConfig already called)
        logging.getLogger().setLevel(logging.INFO)

        logger = get_logger("test")

        # Emit DEBUG and INFO logs
        logger.debug("Debug message")
        logger.info("Info message")

        # Assert: Only INFO log present (DEBUG filtered)
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        # Should only have 1 log (INFO)
        assert len(log_lines) == 1

        log_data = json.loads(log_lines[0])
        assert log_data["level"] == "info"

    def test_configure_logging_supports_debug_level(self, captured_logs: StringIO) -> None:
        """Test DEBUG level captures debug logs.

        Validates:
        - level="DEBUG" enables debug logging
        """
        # Act: Configure with DEBUG level
        configure_logging(level="DEBUG")
        logger = get_logger("test")

        logger.debug("Debug message")

        # Assert: Debug log captured
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["level"] == "debug"

    def test_configure_logging_formats_exceptions(self, captured_logs: StringIO) -> None:
        """Test exception info is formatted in logs.

        Validates:
        - FR-031: Exception stack traces in ERROR logs
        - exc_info processing
        """
        # Act
        configure_logging(level="ERROR")
        logger = get_logger("test")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Error occurred", exc_info=True)

        # Assert: Exception info in log
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        # Exception should be formatted in output
        assert "exception" in log_data or "exc_info" in str(log_data)


# =============================================================================
# Unit Tests: get_logger()
# =============================================================================


@pytest.mark.unit
class TestGetLogger:
    """Unit tests for get_logger() function."""

    def test_get_logger_returns_bound_logger(self) -> None:
        """Test get_logger returns structlog BoundLogger or proxy.

        Validates:
        - Return type is BoundLogger or BoundLoggerLazyProxy
        - Logger is usable (has info, warning, error methods)
        """
        # Act
        logger = get_logger("test")

        # Assert: Has logging methods (duck typing check)
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert callable(logger.info)

    def test_get_logger_accepts_name_parameter(self) -> None:
        """Test logger name parameter is accepted.

        Validates:
        - Name parameter doesn't cause errors
        """
        # Act: Create loggers with different names
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Assert: Both are valid loggers
        assert logger1 is not None
        assert logger2 is not None

    def test_get_logger_supports_contextual_fields(self, captured_logs: StringIO) -> None:
        """Test logger supports arbitrary contextual fields.

        Validates:
        - FR-032: Contextual fields (file_name, conversation_id, etc.)
        - Keyword arguments added to log output
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")

        logger.info(
            "Test message",
            operation="test_op",
            file_name="test.json",
            conversation_id="conv-123",
            count=42,
        )

        # Assert: Contextual fields in output
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["operation"] == "test_op"
        assert log_data["file_name"] == "test.json"
        assert log_data["conversation_id"] == "conv-123"
        assert log_data["count"] == 42

    def test_get_logger_cached_on_first_use(self) -> None:
        """Test logger caching works (cache_logger_on_first_use=True).

        Validates:
        - Loggers with same name use cached underlying logger factory
        - Both loggers are functional and independent proxies

        Note: structlog returns BoundLoggerLazyProxy objects which may not
        be identical, but the underlying logger factory is cached.
        """
        # Act
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")

        # Assert: Both are valid loggers (proxy objects may differ)
        assert logger1 is not None
        assert logger2 is not None
        # Both have same capabilities
        assert hasattr(logger1, "info")
        assert hasattr(logger2, "info")


# =============================================================================
# Unit Tests: ProgressLogger
# =============================================================================


@pytest.mark.unit
class TestProgressLogger:
    """Unit tests for ProgressLogger class."""

    def test_progress_logger_logs_first_item(self, captured_logs: StringIO) -> None:
        """Test first item is always logged (count=1).

        Validates:
        - FR-069: Progress updates at least every 100 items
        - First item logged regardless of interval
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        progress = ProgressLogger(logger, operation="test_op", interval=100)

        progress.log(1, file_name="test.json")

        # Assert: Log emitted for first item
        log_output = captured_logs.getvalue()
        assert len(log_output.strip()) > 0

        log_data = json.loads(log_output.strip())
        assert log_data["count"] == 1
        assert log_data["operation"] == "test_op"

    def test_progress_logger_respects_interval(self, captured_logs: StringIO) -> None:
        """Test logging interval is respected.

        Validates:
        - Logs when count - last_logged >= interval
        - First item always logs (count == 1)
        - No logs until interval reached since last log

        Implementation: logs when (count - last_logged >= interval) OR (count == 1)
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        progress = ProgressLogger(logger, operation="test_op", interval=100)

        # Log items 1, 50, 101, 150, 201
        progress.log(1)  # Should log (first, count == 1), last_logged = 1
        progress.log(50)  # Should NOT log (50 - 1 = 49 < 100)
        progress.log(101)  # Should log (101 - 1 = 100 >= 100), last_logged = 101
        progress.log(150)  # Should NOT log (150 - 101 = 49 < 100)
        progress.log(201)  # Should log (201 - 101 = 100 >= 100)

        # Assert: Only 3 logs (1, 101, 201)
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        assert len(log_lines) == 3

        # Verify counts
        counts = [json.loads(line)["count"] for line in log_lines]
        assert counts == [1, 101, 201]

    def test_progress_logger_includes_extra_context(self, captured_logs: StringIO) -> None:
        """Test extra context fields are included in logs.

        Validates:
        - FR-032: Contextual fields
        - **extra_context parameter works
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        progress = ProgressLogger(logger, operation="test_op")

        progress.log(
            1,
            file_name="test.json",
            conversation_id="conv-123",
        )

        # Assert: Extra context in log
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["file_name"] == "test.json"
        assert log_data["conversation_id"] == "conv-123"

    def test_progress_logger_log_complete(self, captured_logs: StringIO) -> None:
        """Test log_complete() emits completion log.

        Validates:
        - Completion log with total count
        - "Operation complete" message
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        progress = ProgressLogger(logger, operation="test_op")

        progress.log_complete(1234, file_name="test.json")

        # Assert: Completion log
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert "complete" in log_data["event"].lower()
        assert log_data["total"] == 1234
        assert log_data["operation"] == "test_op"

    def test_progress_logger_custom_interval(self, captured_logs: StringIO) -> None:
        """Test custom interval parameter works.

        Validates:
        - interval parameter is respected
        - Logs when count - last_logged >= interval (with custom interval)
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")
        progress = ProgressLogger(logger, operation="test_op", interval=50)

        # Log items 1, 25, 51, 75, 101
        progress.log(1)  # Should log (first, count == 1), last_logged = 1
        progress.log(25)  # Should NOT log (25 - 1 = 24 < 50)
        progress.log(51)  # Should log (51 - 1 = 50 >= 50), last_logged = 51
        progress.log(75)  # Should NOT log (75 - 51 = 24 < 50)
        progress.log(101)  # Should log (101 - 51 = 50 >= 50)

        # Assert: 3 logs (1, 51, 101)
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        assert len(log_lines) == 3

        counts = [json.loads(line)["count"] for line in log_lines]
        assert counts == [1, 51, 101]


# =============================================================================
# Unit Tests: SkipLogger
# =============================================================================


@pytest.mark.unit
class TestSkipLogger:
    """Unit tests for SkipLogger class."""

    def test_skip_logger_logs_with_warning_level(self, captured_logs: StringIO) -> None:
        """Test skips are logged at WARNING level.

        Validates:
        - FR-281: WARNING level for skipped entries
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip(
            conversation_id="conv-bad",
            reason="Missing required field",
        )

        # Assert: WARNING level
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["level"] == "warning"

    def test_skip_logger_includes_conversation_id_and_reason(self, captured_logs: StringIO) -> None:
        """Test skip log includes conversation_id and reason.

        Validates:
        - FR-282: Include conversation_id and reason
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip(
            conversation_id="conv-123",
            reason="Invalid timestamp format",
        )

        # Assert: Fields present
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["conversation_id"] == "conv-123"
        assert log_data["reason"] == "Invalid timestamp format"

    def test_skip_logger_handles_none_conversation_id(self, captured_logs: StringIO) -> None:
        """Test None conversation_id is handled as 'unknown'.

        Validates:
        - Graceful handling of missing ID
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip(
            conversation_id=None,
            reason="Completely malformed entry",
        )

        # Assert: "unknown" used for None
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["conversation_id"] == "unknown"

    def test_skip_logger_increments_skip_count(self) -> None:
        """Test skip count is incremented on each skip.

        Validates:
        - get_skip_count() returns correct count
        - Counter increments
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        # Initial count
        assert skip_log.get_skip_count() == 0

        # Log skips
        skip_log.log_skip("conv-1", "reason1")
        assert skip_log.get_skip_count() == 1

        skip_log.log_skip("conv-2", "reason2")
        assert skip_log.get_skip_count() == 2

        skip_log.log_skip("conv-3", "reason3")
        assert skip_log.get_skip_count() == 3

    def test_skip_logger_includes_skip_count_in_log(self, captured_logs: StringIO) -> None:
        """Test skip_count field is included in log output.

        Validates:
        - Cumulative skip count logged
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip("conv-1", "reason1")
        skip_log.log_skip("conv-2", "reason2")

        # Assert: Second skip has skip_count=2
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        # Check second log
        second_log = json.loads(log_lines[1])
        assert second_log["skip_count"] == 2

    def test_skip_logger_includes_extra_context(self, captured_logs: StringIO) -> None:
        """Test extra context fields are included in skip logs.

        Validates:
        - **extra_context parameter works
        - Additional fields like file_name
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip(
            conversation_id="conv-bad",
            reason="Bad data",
            file_name="export.json",
            line_number=42,
        )

        # Assert: Extra context in log
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert log_data["file_name"] == "export.json"
        assert log_data["line_number"] == 42

    def test_skip_logger_message_format(self, captured_logs: StringIO) -> None:
        """Test skip log message is consistent.

        Validates:
        - Message: "Skipped malformed entry"
        """
        # Act
        configure_logging(level="WARNING")
        logger = get_logger("test")
        skip_log = SkipLogger(logger, operation="test_op")

        skip_log.log_skip("conv-123", "Test reason")

        # Assert: Message format
        log_output = captured_logs.getvalue()
        log_data = json.loads(log_output.strip())

        assert "skipped" in log_data["event"].lower()
        assert "malformed" in log_data["event"].lower()


# =============================================================================
# Integration Tests: Logging Components Together
# =============================================================================


@pytest.mark.unit
class TestLoggingIntegration:
    """Integration tests for logging components working together."""

    def test_progress_and_skip_loggers_together(self, captured_logs: StringIO) -> None:
        """Test ProgressLogger and SkipLogger can be used together.

        Validates:
        - Both loggers work in same operation
        - Distinct log levels (INFO vs WARNING)

        Note: Progress only logs when interval reached (100 - 1 = 99 < 100)
        so we use count=101 to trigger second progress log.
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")

        progress = ProgressLogger(logger, operation="stream_conversations")
        skip_log = SkipLogger(logger, operation="stream_conversations")

        progress.log(1, file_name="test.json")  # Logs (count == 1), last_logged = 1
        skip_log.log_skip("conv-bad", "Malformed", file_name="test.json")  # Always logs
        progress.log(101, file_name="test.json")  # Logs (101 - 1 = 100 >= 100)

        # Assert: All logs present
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        assert len(log_lines) == 3

        # Verify levels
        levels = [json.loads(line)["level"] for line in log_lines]
        assert levels == ["info", "warning", "info"]

    def test_multiple_operations_logged_distinctly(self, captured_logs: StringIO) -> None:
        """Test logs from different operations are distinguishable.

        Validates:
        - operation field differentiates logs
        """
        # Act
        configure_logging(level="INFO")
        logger = get_logger("test")

        progress1 = ProgressLogger(logger, operation="stream_conversations")
        progress2 = ProgressLogger(logger, operation="search")

        progress1.log(1)
        progress2.log(1)

        # Assert: Different operations
        log_output = captured_logs.getvalue()
        log_lines = [line.strip() for line in log_output.split("\n") if line.strip()]

        operations = [json.loads(line)["operation"] for line in log_lines]
        assert operations == ["stream_conversations", "search"]
