"""Provider detection utilities for CLI commands.

This module implements auto-detection of export providers (OpenAI vs Claude)
based on JSON structure analysis, enabling seamless multi-provider support.

Detection Algorithm:
    1. Stream first conversation object from JSON array (O(1) memory)
    2. Check for provider-specific keys:
       - Claude: "chat_messages" key present (FR-047)
       - OpenAI: "mapping" key present (FR-048)
    3. Return provider identifier or raise ValueError

Functions:
    detect_provider: Auto-detect provider from file structure
    get_adapter: Get appropriate adapter based on provider flag or auto-detection

Constitution Compliance:
    - Principle I: Library-first (returns adapter instances, no business logic)
    - Principle VI: Strict typing with mypy --strict
    - Principle VIII: O(1) memory usage with ijson streaming

FR Coverage:
    - FR-046: Auto-detect provider from JSON schema structure
    - FR-047: Detect Claude format by chat_messages key
    - FR-048: Detect OpenAI format by mapping key
    - FR-049: Support --provider flag for explicit provider selection
    - FR-050: Clear error message for unrecognized formats

Usage:
    # Auto-detect provider
    provider = detect_provider(Path("export.json"))

    # Get adapter with explicit provider
    adapter = get_adapter("claude", Path("export.json"))

    # Get adapter with auto-detection
    adapter = get_adapter(None, Path("export.json"))
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import ijson

from echomine.adapters.claude import ClaudeAdapter
from echomine.adapters.openai import OpenAIAdapter


# Type aliases for clarity
ProviderType = Literal["openai", "claude"]
AdapterType = OpenAIAdapter | ClaudeAdapter


def detect_provider(file_path: Path) -> ProviderType:
    """Auto-detect export provider from file structure.

    Streams the first conversation object from the JSON array and inspects
    it for provider-specific keys using ijson for O(1) memory usage.

    Detection Rules:
        1. If "chat_messages" key present → Claude (FR-047)
        2. If "mapping" key present → OpenAI (FR-048)
        3. Otherwise → raise ValueError (FR-050)

    Args:
        file_path: Path to export JSON file

    Returns:
        Provider identifier: "openai" or "claude"

    Raises:
        ValueError: If file is empty, has invalid JSON, or unrecognized format
        FileNotFoundError: If file_path does not exist
        PermissionError: If file cannot be read

    Example:
        ```python
        provider = detect_provider(Path("export.json"))
        if provider == "claude":
            adapter = ClaudeAdapter()
        else:
            adapter = OpenAIAdapter()
        ```

    Constitution Compliance:
        - Principle VIII: O(1) memory - only reads first object
        - FR-046: Auto-detection from JSON structure
        - FR-047: Claude detection via chat_messages key
        - FR-048: OpenAI detection via mapping key
        - FR-050: Clear error messages
    """
    try:
        with open(file_path, "rb") as f:
            # Use ijson to stream first object only (O(1) memory)
            # "item" prefix reads array elements
            parser = ijson.items(f, "item")
            first_obj = next(parser, None)

            # Handle empty file - default to OpenAI for backwards compatibility
            # Empty JSON arrays are valid exports with zero conversations
            if first_obj is None:
                return "openai"  # Default provider for empty files

            # FR-047: Detect Claude by chat_messages key
            if "chat_messages" in first_obj:
                return "claude"

            # FR-048: Detect OpenAI by mapping key
            if "mapping" in first_obj:
                return "openai"

            # FR-050: Unrecognized format with clear error message
            raise ValueError(
                "Unsupported export format. "
                "Expected OpenAI export (with 'mapping' key) or "
                "Claude export (with 'chat_messages' key)."
            )

    except ijson.JSONError as e:
        # FR-050: Clear error for invalid JSON
        raise ValueError(f"Invalid JSON: {e}") from e


def get_adapter(
    provider: str | None,
    file_path: Path,
) -> AdapterType:
    """Get appropriate adapter based on provider flag or auto-detection.

    If provider is explicitly specified, returns that adapter without
    inspecting the file. If provider is None, auto-detects from file structure.

    Args:
        provider: Explicit provider ("openai", "claude") or None for auto-detect
        file_path: Path to export file (used only for auto-detection)

    Returns:
        OpenAIAdapter or ClaudeAdapter instance

    Raises:
        ValueError: If provider is invalid or auto-detection fails
        FileNotFoundError: If file_path does not exist (auto-detect only)
        PermissionError: If file cannot be read (auto-detect only)

    Example:
        ```python
        # Explicit provider selection (FR-049)
        adapter = get_adapter("claude", Path("export.json"))

        # Auto-detection (FR-046)
        adapter = get_adapter(None, Path("export.json"))
        ```

    Constitution Compliance:
        - Principle I: Library-first - returns adapter instances
        - Principle VII: Multi-provider pattern - stateless adapters
        - FR-049: --provider flag support
        - FR-046: Auto-detection fallback
    """
    # FR-049: Explicit provider selection
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "claude":
        return ClaudeAdapter()
    if provider is None:
        # FR-046: Auto-detect provider from file structure
        detected = detect_provider(file_path)
        if detected == "claude":
            return ClaudeAdapter()
        # detected == "openai"
        return OpenAIAdapter()
    # Invalid provider value (should not happen with Typer validation)
    raise ValueError(f"Invalid provider '{provider}'. Must be 'openai', 'claude', or None.")
