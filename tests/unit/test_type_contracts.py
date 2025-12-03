"""T059: Type Safety Contract Tests.

This test module validates that the echomine library maintains strict type safety
and passes mypy --strict validation. It ensures the public API has no 'Any' types
and provides complete type annotations for IDE autocomplete support.

Test Strategy:
    - Run mypy --strict on sample library consumer code
    - Verify no 'Any' types in public API signatures
    - Verify all public functions have complete type annotations
    - Verify generic types work correctly (SearchResult[Conversation])
    - Validate runtime type checking with Protocol classes

Constitution Compliance:
    - Principle VI: Strict Typing Mandatory (mypy --strict MUST pass)
    - Principle I: Library-First Architecture (typed public API)
    - Principle III: Test-Driven Development (RED phase)

Requirements Coverage:
    - FR-151-154: Generic typing support for multi-provider pattern
    - FR-215-221: Complete method signatures with proper types
    - Principle VI: ZERO TOLERANCE - mypy --strict must pass

Test Execution:
    pytest tests/unit/test_type_contracts.py -v

Expected State: FAILING (imports will fail until exports added to __init__.py)
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, get_args, get_origin


# ============================================================================
# T059-001: Mypy Strict Mode Validation
# ============================================================================


def test_mypy_strict_passes_on_library_consumer_code() -> None:
    """Verify mypy --strict passes on typical library usage code.

    This test creates a sample Python script that uses the library in typical
    ways (imports, creates adapter, calls methods) and runs mypy --strict on it.

    Requirements:
        - Principle VI: ZERO TOLERANCE - mypy --strict MUST pass
        - FR-215-221: Complete method signatures with proper types
        - No 'Any' types exposed in public API

    Expected Failure:
        Will fail when run because imports in consumer code will fail
        (exports not yet added to __init__.py)
    """
    # Sample library consumer code (simulates cognivault usage)
    consumer_code = '''
"""Sample library consumer code for mypy validation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

# These imports should work and pass mypy --strict
from echomine import OpenAIAdapter, SearchQuery, SearchResult, Conversation, Message
from echomine.exceptions import EchomineError, ParseError
from echomine.models.protocols import ConversationProvider


def process_conversations(export_path: Path) -> list[Conversation]:
    """Example function using library - should pass mypy --strict.

    Args:
        export_path: Path to OpenAI export file

    Returns:
        List of conversations from export
    """
    adapter: OpenAIAdapter = OpenAIAdapter()

    # This should be typed as Iterator[Conversation]
    conversations_iter = adapter.stream_conversations(export_path)

    # Converting to list should preserve type
    conversations: list[Conversation] = list(conversations_iter)

    return conversations


def search_conversations(
    export_path: Path,
    keywords: list[str]
) -> list[SearchResult[Conversation]]:
    """Example search function - should pass mypy --strict.

    Args:
        export_path: Path to export file
        keywords: Search keywords

    Returns:
        List of search results with relevance scores
    """
    adapter: OpenAIAdapter = OpenAIAdapter()
    query: SearchQuery = SearchQuery(keywords=keywords, limit=10)

    # This should be typed as Iterator[SearchResult[Conversation]]
    results_iter = adapter.search(export_path, query)

    # Converting to list should preserve type
    results: list[SearchResult[Conversation]] = list(results_iter)

    return results


def get_conversation(export_path: Path, conv_id: str) -> Conversation | None:
    """Example get function - should pass mypy --strict.

    Args:
        export_path: Path to export file
        conv_id: Conversation ID to retrieve

    Returns:
        Conversation if found, None otherwise
    """
    adapter: OpenAIAdapter = OpenAIAdapter()

    # This should be typed as Optional[Conversation]
    conversation: Conversation | None = adapter.get_conversation_by_id(
        export_path, conv_id
    )

    return conversation


def handle_errors(export_path: Path) -> None:
    """Example error handling - should pass mypy --strict.

    Args:
        export_path: Path to export file
    """
    adapter: OpenAIAdapter = OpenAIAdapter()

    try:
        conversations: list[Conversation] = list(
            adapter.stream_conversations(export_path)
        )
    except EchomineError as e:
        # All library exceptions inherit from EchomineError
        print(f"Library error: {e}")
    except FileNotFoundError as e:
        # Standard library exceptions also handled
        print(f"File not found: {e}")


def access_conversation_attributes(conversation: Conversation) -> None:
    """Example attribute access - should pass mypy --strict.

    Args:
        conversation: Conversation object
    """
    # These attributes should be typed
    conv_id: str = conversation.id
    title: str = conversation.title
    created: datetime = conversation.created_at
    # Use updated_at_or_created property for guaranteed non-null datetime
    updated: datetime = conversation.updated_at_or_created
    messages: list[Message] = conversation.messages

    # Message attributes should also be typed
    if len(messages) > 0:
        msg: Message = messages[0]
        msg_id: str = msg.id
        content: str = msg.content
        role: str = msg.role
        timestamp: datetime = msg.timestamp


def generic_adapter_usage(adapter: ConversationProvider[Conversation]) -> None:
    """Example generic function - should pass mypy --strict.

    This tests that ConversationProvider protocol works with generic types.

    Args:
        adapter: Any adapter implementing ConversationProvider protocol
    """
    export_path = Path("export.json")

    # Protocol methods should be typed
    conversations: list[Conversation] = list(
        adapter.stream_conversations(export_path)
    )

    query: SearchQuery = SearchQuery(keywords=["test"])
    results: list[SearchResult[Conversation]] = list(
        adapter.search(export_path, query)
    )
'''

    # Write consumer code to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(consumer_code)
        tmp_path = Path(tmp_file.name)

    try:
        # Run mypy --strict on the consumer code
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "--show-error-codes",
                "--pretty",
                str(tmp_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )

        # mypy should exit with code 0 (no errors)
        assert result.returncode == 0, (
            f"mypy --strict failed on library consumer code:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    finally:
        # Clean up temporary file
        tmp_path.unlink(missing_ok=True)


# ============================================================================
# T059-002: No 'Any' Types in Public API
# ============================================================================


def test_public_api_has_no_any_types() -> None:
    """Verify no 'Any' types exposed in public API signatures.

    Requirements:
        - Principle VI: No 'Any' types (use Protocol or TypeVar)
        - Strict typing for all public methods

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # Check stream_conversations return type annotation
    stream_method = adapter.stream_conversations
    if hasattr(stream_method, "__annotations__"):
        annotations = stream_method.__annotations__
        for param_name, annotation in annotations.items():
            assert annotation != Any, f"Parameter '{param_name}' should not be Any type"

    # Check search return type annotation
    search_method = adapter.search
    if hasattr(search_method, "__annotations__"):
        annotations = search_method.__annotations__
        for param_name, annotation in annotations.items():
            assert annotation != Any, f"Parameter '{param_name}' should not be Any type"

    # Check get_conversation_by_id return type annotation
    get_method = adapter.get_conversation_by_id
    if hasattr(get_method, "__annotations__"):
        annotations = get_method.__annotations__
        for param_name, annotation in annotations.items():
            assert annotation != Any, f"Parameter '{param_name}' should not be Any type"


# ============================================================================
# T059-003: Complete Type Annotations
# ============================================================================


def test_all_public_functions_have_type_annotations() -> None:
    """Verify all public functions have complete type annotations.

    Requirements:
        - Principle VI: Type hints on ALL functions, methods, variables
        - FR-215-221: Complete method signatures

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # All public methods (not starting with _) should have annotations
    public_methods = [
        name
        for name in dir(adapter)
        if not name.startswith("_") and callable(getattr(adapter, name))
    ]

    for method_name in public_methods:
        method = getattr(adapter, method_name)
        assert hasattr(method, "__annotations__"), (
            f"Method '{method_name}' should have type annotations"
        )
        assert len(method.__annotations__) > 0, (
            f"Method '{method_name}' annotations should not be empty"
        )


def test_model_classes_have_type_annotations() -> None:
    """Verify Pydantic model classes have complete field annotations.

    Requirements:
        - Principle VI: Type hints on ALL variables
        - Pydantic v2 strict validation

    Expected Failure:
        ImportError: cannot import name 'Conversation' from 'echomine'
    """
    from echomine import Conversation, Message, SearchQuery, SearchResult

    # All model classes should have __annotations__
    for model_class in [Conversation, Message, SearchQuery, SearchResult]:
        assert hasattr(model_class, "__annotations__"), (
            f"Model {model_class.__name__} should have field annotations"
        )
        assert len(model_class.__annotations__) > 0, (
            f"Model {model_class.__name__} should have fields"
        )


# ============================================================================
# T059-004: Generic Types Work Correctly
# ============================================================================


def test_search_result_generic_type_works() -> None:
    """Verify SearchResult[Conversation] generic type works correctly.

    Requirements:
        - FR-152: SearchResult[ConversationT] generic type
        - Generic typing for multi-provider pattern

    Expected Failure:
        ImportError: cannot import name 'SearchResult' from 'echomine'

    Note:
        Pydantic v2 models with Generic don't preserve runtime type info
        like pure Python generics, but type checkers validate them correctly.
        We verify that parameterization creates a distinct type.
    """
    from echomine import Conversation, SearchResult

    # Should be able to use as generic type (mypy validates this)
    result_type = SearchResult[Conversation]

    # Pydantic creates parameterized class at runtime
    assert result_type is not SearchResult, "Parameterized type should be distinct"
    assert "Conversation" in str(result_type), "Type should show parameterization"

    # Verify SearchResult has Generic in its bases (Pydantic pattern)
    import typing

    assert hasattr(SearchResult, "__orig_bases__"), "Should have __orig_bases__"
    bases = SearchResult.__orig_bases__
    assert any(
        isinstance(base, typing._GenericAlias)  # type: ignore[attr-defined]
        for base in bases
    ), "Should inherit from Generic"


def test_conversation_provider_protocol_generic_type() -> None:
    """Verify ConversationProvider[ConversationT] generic protocol works.

    Requirements:
        - FR-151: ConversationProvider[ConversationT] generic protocol
        - Multi-provider adapter pattern

    Expected Failure:
        ImportError: cannot import name 'ConversationProvider' from module
    """
    from echomine import Conversation
    from echomine.models.protocols import ConversationProvider

    # Should be able to use as generic type
    provider_type = ConversationProvider[Conversation]

    # Verify it's a generic alias
    origin = get_origin(provider_type)
    args = get_args(provider_type)

    # ConversationProvider should be generic
    assert origin is not None or args, "ConversationProvider should support generic types"


# ============================================================================
# T059-005: Runtime Type Checking with Protocol
# ============================================================================


def test_adapter_implements_conversation_provider_protocol() -> None:
    """Verify OpenAIAdapter implements ConversationProvider protocol at runtime.

    Requirements:
        - FR-027: Adapters implement ConversationProvider protocol
        - Protocol is runtime_checkable

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter
    from echomine.models.protocols import ConversationProvider

    adapter = OpenAIAdapter()

    # Should pass runtime protocol check
    assert isinstance(adapter, ConversationProvider), (
        "OpenAIAdapter should implement ConversationProvider protocol"
    )


def test_protocol_has_all_required_methods() -> None:
    """Verify ConversationProvider protocol defines all required methods.

    Requirements:
        - FR-215-221: Complete protocol method signatures
        - FR-151: Protocol defines adapter contract

    Expected Failure:
        ImportError: cannot import name 'ConversationProvider'
    """
    from echomine.models.protocols import ConversationProvider

    # Protocol should define these methods
    required_methods = ["stream_conversations", "search", "get_conversation_by_id"]

    for method_name in required_methods:
        assert hasattr(ConversationProvider, method_name), (
            f"ConversationProvider should define {method_name}"
        )


# ============================================================================
# T059-006: Type Inference for IDE Autocomplete
# ============================================================================


def test_iterator_type_inference_works(
    tmp_export_file: Path,
) -> None:
    """Verify IDE can infer types from iterator methods.

    This test ensures that IDE autocomplete will work correctly when
    developers use the library.

    Requirements:
        - Principle VI: Strict typing for IDE support
        - FR-151-154: Generic typing

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    # When we call stream_conversations, IDE should infer it returns Iterator[Conversation]
    conversations_iter = adapter.stream_conversations(tmp_export_file)

    # When we consume iterator, IDE should know each item is a Conversation
    conversations = list(conversations_iter)

    if len(conversations) > 0:
        conversation = conversations[0]

        # IDE should provide autocomplete for these attributes
        # (This test validates runtime, but mypy validates static types)
        assert hasattr(conversation, "id"), "Should have id attribute"
        assert hasattr(conversation, "title"), "Should have title attribute"
        assert hasattr(conversation, "created_at"), "Should have created_at attribute"
        assert hasattr(conversation, "messages"), "Should have messages attribute"


def test_search_result_type_inference_works(
    tmp_export_file: Path,
) -> None:
    """Verify IDE can infer SearchResult types correctly.

    Requirements:
        - FR-152: SearchResult[ConversationT] generic type
        - IDE autocomplete support

    Expected Failure:
        ImportError: cannot import name 'SearchQuery' from 'echomine'
    """
    from echomine import OpenAIAdapter, SearchQuery

    adapter = OpenAIAdapter()
    query = SearchQuery(keywords=["test"], limit=1)

    # When we call search, IDE should infer it returns Iterator[SearchResult[Conversation]]
    results_iter = adapter.search(tmp_export_file, query)

    # When we consume iterator, IDE should know each item is a SearchResult
    results = list(results_iter)

    if len(results) > 0:
        result = results[0]

        # IDE should provide autocomplete for SearchResult attributes
        assert hasattr(result, "conversation"), "Should have conversation attribute"
        assert hasattr(result, "score"), "Should have score attribute"
        assert hasattr(result, "matched_message_ids"), "Should have matched_message_ids attribute"

        # IDE should know conversation is a Conversation object
        conversation = result.conversation
        assert hasattr(conversation, "id"), "Conversation should have id"
        assert hasattr(conversation, "title"), "Conversation should have title"


# ============================================================================
# T059-007: Type Safety for Callbacks
# ============================================================================


def test_callback_type_annotations_are_correct() -> None:
    """Verify callback type aliases are properly typed.

    Requirements:
        - FR-076: Progress callback type
        - FR-106: Skip callback type
        - Principle VI: Strict typing

    Expected Failure:
        ImportError: cannot import callbacks from protocols module
    """
    from echomine.models.protocols import OnSkipCallback, ProgressCallback

    # Verify callback types are Callable with correct signatures
    assert ProgressCallback is not None, "ProgressCallback should be defined"
    assert OnSkipCallback is not None, "OnSkipCallback should be defined"

    # Verify they are Callable types
    origin_progress = get_origin(ProgressCallback)
    origin_skip = get_origin(OnSkipCallback)

    # Both should be based on Callable
    assert origin_progress is not None, "ProgressCallback should be Callable type"
    assert origin_skip is not None, "OnSkipCallback should be Callable type"


def test_adapter_accepts_typed_callbacks(
    tmp_large_export_file: Path,
) -> None:
    """Verify adapter methods accept properly typed callbacks.

    Requirements:
        - FR-076, FR-077: Progress callback support
        - FR-106, FR-107: Skip callback support
        - Type safety for callback parameters

    Expected Failure:
        ImportError: cannot import name 'OpenAIAdapter' from 'echomine'
    """
    from echomine import OpenAIAdapter

    adapter = OpenAIAdapter()

    progress_count = 0
    skip_count = 0

    def progress_callback(count: int) -> None:
        """Properly typed progress callback."""
        nonlocal progress_count
        progress_count = count

    def skip_callback(conversation_id: str, reason: str) -> None:
        """Properly typed skip callback."""
        nonlocal skip_count
        skip_count += 1

    # Should accept typed callbacks (large file has 1000 conversations)
    conversations = list(
        adapter.stream_conversations(
            tmp_large_export_file,
            progress_callback=progress_callback,
            on_skip=skip_callback,
        )
    )

    # Progress callback should have been called at 100, 200, ..., 1000
    # (called every 100 items per FR-069)
    assert progress_count > 0, "Progress callback should have been called"
    assert progress_count >= 100, (
        f"Progress callback should reach at least 100, got {progress_count}"
    )


# ============================================================================
# T059-008: Exception Type Safety
# ============================================================================


def test_exception_hierarchy_is_properly_typed() -> None:
    """Verify exception classes have proper type annotations.

    Requirements:
        - FR-035: Exception class hierarchy
        - FR-286: Selective exception handling
        - Principle VI: Strict typing

    Expected Failure:
        ImportError: cannot import exceptions
    """
    from echomine.exceptions import (
        EchomineError,
        ParseError,
        SchemaVersionError,
        ValidationError,
    )

    # All exceptions should be Exception subclasses
    assert issubclass(EchomineError, Exception), "EchomineError should inherit from Exception"
    assert issubclass(ParseError, EchomineError), "ParseError should inherit from EchomineError"
    assert issubclass(ValidationError, EchomineError), (
        "ValidationError should inherit from EchomineError"
    )
    assert issubclass(SchemaVersionError, EchomineError), (
        "SchemaVersionError should inherit from EchomineError"
    )

    # Should be able to instantiate with string message
    try:
        raise ParseError("Test error message")
    except ParseError as e:
        assert str(e) == "Test error message", "Exception message should be preserved"
