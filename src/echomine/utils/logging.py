"""Structured logging configuration for echomine.

This module configures structlog for JSON-formatted logging with contextual
fields, enabling observability and debugging in production environments.

Constitution Compliance:
    - Principle IV: Observability & Debuggability (JSON logs, context fields)
    - FR-028 to FR-032: Structured logging requirements

Log Format:
    All log entries are JSON objects with these required fields:
    - timestamp: ISO 8601 UTC timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - operation: Operation being performed (e.g., "stream_conversations", "search")
    - message: Human-readable log message

    Optional contextual fields:
    - file_name: Export file being processed
    - conversation_id: Current conversation identifier
    - message_id: Current message identifier
    - count: Progress counter
    - error: Exception details (for ERROR/CRITICAL logs)

Example Log Entry:
    ```json
    {
        "timestamp": "2024-03-15T10:30:00.123Z",
        "level": "INFO",
        "operation": "stream_conversations",
        "message": "Processing conversation",
        "file_name": "export.json",
        "conversation_id": "conv-abc-123",
        "count": 42
    }
    ```

Usage:
    ```python
    from echomine.utils.logging import get_logger

    logger = get_logger(__name__)

    logger.info(
        "Starting search",
        operation="search",
        file_name="export.json",
        keyword_count=3
    )
    ```
"""

import logging
import sys
from typing import Any, cast

import structlog


# ============================================================================
# Structlog Configuration
# ============================================================================


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog for JSON logging with required fields.

    This function should be called once at application startup to configure
    the logging system. It sets up JSON formatting, timestamp rendering,
    and exception formatting.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Requirements:
        - FR-028: Structured JSON logging
        - FR-029: Required fields (timestamp, level, operation, message)
        - FR-030: ISO 8601 timestamps in UTC
        - FR-031: Exception stack traces in ERROR logs
        - FR-032: Contextual fields (file_name, conversation_id, etc.)

    Example:
        ```python
        # In application entry point (CLI or library init)
        from echomine.utils.logging import configure_logging

        configure_logging(level="INFO")
        ```
    """
    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level.upper()),
    )

    # Structlog processor chain
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add timestamp in ISO 8601 UTC format (per FR-030)
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add exception info (per FR-031)
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Unwrap event dict for rendering
            structlog.processors.UnicodeDecoder(),
            # Render as JSON (per FR-028)
            structlog.processors.JSONRenderer(),
        ],
        # Use standard library logging as backend
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured structlog logger instance

    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("Processing started", operation="stream_conversations")
        ```

    Requirements:
        - FR-029: Logger provides required fields (timestamp, level, message)
        - FR-032: Logger supports arbitrary contextual fields
    """
    # Explicit cast needed: structlog.get_logger returns Any in type stubs
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))


# ============================================================================
# Progress Logging Helpers
# ============================================================================


class ProgressLogger:
    """Helper for logging progress during streaming operations.

    Provides rate-limited progress logging (per FR-069: every 100 items)
    with consistent field names and formatting.

    Example:
        ```python
        logger = get_logger(__name__)
        progress = ProgressLogger(logger, operation="stream_conversations")

        for i, conversation in enumerate(stream, start=1):
            progress.log(i, file_name="export.json")
            # ... process conversation
        ```

    Requirements:
        - FR-069: Progress updates at least every 100 items
        - FR-077: Progress logging for CLI progress indicators
        - FR-032: Consistent contextual fields
    """

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        operation: str,
        interval: int = 100,
    ) -> None:
        """Initialize progress logger.

        Args:
            logger: Structured logger instance
            operation: Operation name (e.g., "stream_conversations", "search")
            interval: Log interval in items (default: 100 per FR-069)
        """
        self.logger = logger
        self.operation = operation
        self.interval = interval
        self.last_logged = 0

    def log(
        self,
        count: int,
        **extra_context: Any,
    ) -> None:
        """Log progress if interval reached.

        Args:
            count: Current item count
            **extra_context: Additional contextual fields (file_name, etc.)

        Example:
            ```python
            progress.log(
                150,
                file_name="export.json",
                conversation_id="conv-123"
            )
            ```
        """
        if count - self.last_logged >= self.interval or count == 1:
            self.logger.info(
                "Progress update",
                operation=self.operation,
                count=count,
                **extra_context,
            )
            self.last_logged = count

    def log_complete(self, total: int, **extra_context: Any) -> None:
        """Log completion with total count.

        Args:
            total: Final item count
            **extra_context: Additional contextual fields

        Example:
            ```python
            progress.log_complete(1234, file_name="export.json")
            # Logs: "Operation complete" with count=1234
            ```
        """
        self.logger.info(
            "Operation complete",
            operation=self.operation,
            total=total,
            **extra_context,
        )


class SkipLogger:
    """Helper for logging skipped entries during graceful degradation.

    Provides consistent formatting for skip warnings when malformed entries
    are encountered (per FR-281 to FR-285).

    Example:
        ```python
        logger = get_logger(__name__)
        skip_log = SkipLogger(logger, operation="stream_conversations")

        # When encountering malformed conversation
        skip_log.log_skip(
            conversation_id="conv-bad-123",
            reason="Missing required field: title",
            file_name="export.json"
        )
        ```

    Requirements:
        - FR-281: Log skipped entries with WARNING level
        - FR-282: Include conversation_id and reason
        - FR-283: Graceful degradation - continue after skip
    """

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        operation: str,
    ) -> None:
        """Initialize skip logger.

        Args:
            logger: Structured logger instance
            operation: Operation name (e.g., "stream_conversations")
        """
        self.logger = logger
        self.operation = operation
        self.skip_count = 0

    def log_skip(
        self,
        conversation_id: str | None,
        reason: str,
        **extra_context: Any,
    ) -> None:
        """Log skipped entry with WARNING level.

        Args:
            conversation_id: Skipped conversation ID (may be None if unavailable)
            reason: Human-readable skip reason
            **extra_context: Additional contextual fields (file_name, etc.)

        Example:
            ```python
            skip_log.log_skip(
                conversation_id="conv-123",
                reason="Invalid timestamp format",
                file_name="export.json"
            )
            ```

        Requirements:
            - FR-281: WARNING level for skipped entries
            - FR-282: Include conversation_id and reason
        """
        self.skip_count += 1
        self.logger.warning(
            "Skipped malformed entry",
            operation=self.operation,
            conversation_id=conversation_id or "unknown",
            reason=reason,
            skip_count=self.skip_count,
            **extra_context,
        )

    def get_skip_count(self) -> int:
        """Get total number of skipped entries.

        Returns:
            Total skip count

        Example:
            ```python
            if skip_log.get_skip_count() > 0:
                logger.info("Data quality issues detected", skips=skip_log.get_skip_count())
            ```
        """
        return self.skip_count


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ProgressLogger",
    "SkipLogger",
    "configure_logging",
    "get_logger",
]
