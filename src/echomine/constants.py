"""Memory and performance constants for echomine.

These constants establish bounded resource usage for streaming operations,
ensuring O(1) memory complexity regardless of file size (Constitution Principle VIII).

Checklist Items Resolved:
- CHK007: Streaming requirements quantified (memory bounds)
- CHK043: "Operations >2 seconds" quantified for progress indicators
- CHK135: Progress indicator threshold specified

Architecture Decision Record:
- Memory budget designed for 8GB RAM machines with 1.6GB files (SC-001)
- Conservative bounds ensure predictable performance
- Progress indicators balance user feedback with terminal noise
"""

# ============================================================================
# Memory Bounds (CHK007)
# ============================================================================

MAX_PARSER_STATE_MEMORY = 50_000_000  # 50MB - ijson parser buffer + state
"""Maximum memory for ijson parser state including buffers and nested structure tracking.

Based on ijson 3.2.0+ performance characteristics with deeply nested JSON.
Handles nesting up to ~1000 levels (far exceeds ChatGPT export format).
"""

MAX_CONVERSATION_OVERHEAD = 5_000_000  # 5MB - per-conversation metadata
"""Maximum memory overhead per Conversation object in memory.

Breakdown:
- Metadata (id, title, timestamps): ~1KB
- Message list metadata (not full content): ~100 messages × 500 bytes = 50KB
- Python object overhead: ~2-3MB (conservative estimate)
- Safety margin: ~2MB
"""

MAX_BATCH_SIZE = 100  # conversations before yield
"""Maximum number of conversations to hold in memory before yielding.

With MAX_CONVERSATION_OVERHEAD = 5MB per conversation:
- Worst case: 100 × 5MB = 500MB
- Parser state: 50MB
- Total: ~550MB worst case
- Well under 1GB threshold for 8GB machines
"""

TARGET_WORKING_SET = 100_000_000  # 100MB - realistic target
"""Target working set size for normal operations.

Actual usage typically much lower than worst-case MAX_BATCH_SIZE scenario.
Most conversations are smaller than MAX_CONVERSATION_OVERHEAD estimate.
"""

# ============================================================================
# Performance Thresholds (CHK043, CHK135)
# ============================================================================

PROGRESS_DELAY_SECONDS = 2.0  # Show progress after 2 seconds
"""Time threshold for showing progress indicators (FR-021).

Operations completing in <2 seconds show no progress (avoid flicker).
After 2 seconds, progress updates appear on stderr.

Rationale:
- Fast operations (<2s) complete before progress appears
- Self-calibrating: no false positives for quick files
- Balances user feedback with terminal cleanliness
"""

PROGRESS_UPDATE_INTERVAL = 100  # Update every 100 items
"""Item interval for progress updates (FR-069).

Progress indicator updates after every 100 conversations processed.
Balances update frequency (user feedback) with stderr noise.

On fast machines: ~10 updates/second max
On slow machines: Less frequent but still responsive
"""

# ============================================================================
# Platform Compatibility (CHK124)
# ============================================================================

SUPPORTED_PLATFORMS = frozenset(["linux", "darwin", "win32"])
"""Platforms where echomine is tested and supported.

- linux: Ubuntu, Debian, Fedora, etc.
- darwin: macOS (Intel and Apple Silicon)
- win32: Windows 10+

Platform-specific considerations:
- File paths: Use pathlib.Path (handles Windows/Unix differences)
- ijson backends: Prefer yajl2_c (C extension), fallback to python (pure)
- Line endings: JSON uses \\n, but handle \\r\\n in text output
"""

SUPPORTED_PYTHON_VERSIONS = frozenset(["3.12", "3.13"])
"""Python versions where echomine is tested.

Minimum: Python 3.12 (required for PEP 695 type parameter syntax)
Maximum: Latest stable release (currently 3.13)

Features used from 3.12+:
- PEP 695: Type parameter syntax (generic functions/classes)
- PEP 701: Multi-line f-strings (improved error messages)
- typing.override: Explicit protocol implementation
"""

# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Memory bounds
    "MAX_PARSER_STATE_MEMORY",
    "MAX_CONVERSATION_OVERHEAD",
    "MAX_BATCH_SIZE",
    "TARGET_WORKING_SET",
    # Performance thresholds
    "PROGRESS_DELAY_SECONDS",
    "PROGRESS_UPDATE_INTERVAL",
    # Platform compatibility
    "SUPPORTED_PLATFORMS",
    "SUPPORTED_PYTHON_VERSIONS",
]
