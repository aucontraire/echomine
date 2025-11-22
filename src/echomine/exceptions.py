"""Exception hierarchy for echomine library.

This module defines all custom exceptions raised by the echomine library.
All exceptions inherit from EchomineError base class, enabling consumers
to catch all library exceptions with a single except clause.

Exception Categories (per FR-286 to FR-290):
    - Operational Errors: File access, permissions, disk space (fail-fast)
    - Data Quality Errors: Malformed JSON, validation failures (skip with warning)
    - Schema Errors: Unsupported export versions (fail-fast)

Constitution Compliance:
    - Principle IV: Observability (structured exception messages)
    - FR-249: Fail fast for operational errors
    - FR-251: Distinguish fail-fast vs skip-malformed
    - FR-253: No retries for any error type

Exception Contract (per FR-035 to FR-041):
    - All library exceptions inherit from EchomineError
    - Exception messages include actionable context
    - Operational errors raised immediately (fail-fast)
    - Data quality errors logged and skipped (graceful degradation)
"""


class EchomineError(Exception):
    """Base exception for all echomine errors (per FR-035, FR-286).

    All custom exceptions in the echomine library inherit from this class,
    enabling library consumers to catch all echomine-specific errors with
    a single except clause.

    This exception should NOT be raised directly - use specific subclasses
    for different error categories (ParseError, ValidationError, etc.).

    Example:
        ```python
        from echomine import OpenAIAdapter
        from echomine.exceptions import EchomineError

        try:
            adapter = OpenAIAdapter()
            conversations = list(adapter.stream_conversations(Path("export.json")))
        except EchomineError as e:
            # Catches all echomine-specific errors
            print(f"Library error: {e}")
        ```

    Requirements:
        - FR-035: Base exception class for library hierarchy
        - FR-286: Enables selective exception handling
    """


class ParseError(EchomineError):
    """Export file parsing error (per FR-036, FR-287).

    Raised when export file has invalid JSON syntax, corrupted data, or
    structure that doesn't match expected provider format. This is a
    fail-fast error - parsing cannot continue.

    Common Causes:
        - Invalid JSON syntax (missing brackets, commas, quotes)
        - Truncated/corrupted file
        - Export format doesn't match provider schema
        - Required top-level fields missing (e.g., conversations array)

    Example:
        ```python
        try:
            conversations = list(adapter.stream_conversations(Path("export.json")))
        except ParseError as e:
            print(f"Invalid export format: {e}")
            # Log and alert user - cannot recover
        ```

    Requirements:
        - FR-036: Raised for invalid export format
        - FR-249: Fail-fast error (no retry)
        - FR-287: Distinct from data quality errors
    """


class ValidationError(EchomineError):
    """Pydantic validation error for conversation data (per FR-036, FR-054, FR-288).

    Raised when conversation or message data fails Pydantic model validation.
    This typically indicates data quality issues (missing fields, wrong types,
    invalid values) rather than file corruption.

    Handling Strategy:
        - For streaming operations: Skip entry with WARNING log, invoke on_skip callback
        - For single-conversation lookups: Raise immediately (fail-fast)

    Common Causes:
        - Missing required fields (id, title, content, timestamp)
        - Wrong field types (string instead of int, etc.)
        - Invalid timestamps (timezone-naive, future dates)
        - Empty required strings (title, id)

    Example:
        ```python
        try:
            conv = adapter.get_conversation_by_id(Path("export.json"), "conv-123")
        except ValidationError as e:
            print(f"Conversation data invalid: {e}")
            # Log and skip - data quality issue
        ```

    Requirements:
        - FR-036: Raised for Pydantic validation failures
        - FR-054: Validation enforced at parse time
        - FR-288: Distinct error type for data quality issues
        - FR-281: Skipped during streaming (graceful degradation)
    """


class SchemaVersionError(EchomineError):
    """Unsupported export schema version (per FR-036, FR-085, FR-289).

    Raised when export file schema version is not supported by this adapter.
    This is a fail-fast error - incompatible schemas cannot be parsed safely.

    AI providers may change export formats over time. This error indicates
    the export was created with a schema version this library doesn't support
    (too old or too new).

    Example:
        ```python
        try:
            conversations = list(adapter.stream_conversations(Path("export.json")))
        except SchemaVersionError as e:
            print(f"Incompatible export version: {e}")
            print("Please update echomine or export from your AI provider again")
        ```

    Requirements:
        - FR-036: Raised for unsupported schema versions
        - FR-085: Schema detection must occur before parsing
        - FR-289: Distinct error type for version incompatibility
        - FR-249: Fail-fast error (no retry, no degradation)
    """


# ============================================================================
# Exception Exports
# ============================================================================

__all__ = [
    "EchomineError",
    "ParseError",
    "ValidationError",
    "SchemaVersionError",
]
