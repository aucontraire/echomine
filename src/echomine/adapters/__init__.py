"""Adapters for AI conversation export formats.

This module provides streaming adapters for different AI provider export formats,
enabling O(1) memory consumption regardless of export file size.

Public API:
    - OpenAIAdapter: Streams conversations from OpenAI ChatGPT export files

Constitution Compliance:
    - Principle VIII: Memory-efficient streaming (FR-003)
    - Principle I: Library-first design (importable adapters)
    - FR-122: ijson streaming parser for O(1) memory
"""

from echomine.adapters.openai import OpenAIAdapter


__all__ = ["OpenAIAdapter"]
