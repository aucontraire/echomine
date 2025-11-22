# Gap Resolution: Tier 1 Critical Gaps

**Feature**: 001-ai-chat-parser
**Date**: 2025-11-21
**Status**: In Progress
**Total Gaps Addressed**: 44 items (Tier 1 Critical)

---

## 1. Library Exception Contract (11 items)

### CHK005, CHK048: Exception Hierarchy & Public API Contract

**Gap**: Which exceptions are part of public API vs implementation details? Which MUST library consumers catch?

**Decision**:
Define a clear exception hierarchy where library consumers catch only public exceptions:

**Public API Exceptions** (library consumers MUST handle):
```python
EchomineError (base class)
├── ParseError (malformed JSON, schema violations)
├── ValidationError (Pydantic validation failures, invalid data)
├── SchemaVersionError (unsupported export schema version)
└── FileAccessError (file not found, permission denied, disk errors)
```

**Internal Exceptions** (bugs, should NOT be caught):
- `AssertionError`, `TypeError`, `AttributeError` → indicate library bugs, let them propagate
- `KeyboardInterrupt`, `SystemExit`, `MemoryError` → system-level, never catch

**Rationale**: Clear contract prevents cognivault from catching bugs as expected behavior. Public exceptions are documented, stable API. Internal exceptions indicate code defects.

**New Requirements**:
- **FR-035**: Library MUST define `EchomineError` base exception class that all public exceptions inherit from
- **FR-036**: Library MUST raise only public exception types (`ParseError`, `ValidationError`, `SchemaVersionError`, `FileAccessError`) for operational failures
- **FR-037**: Library documentation MUST specify which exceptions are part of public API contract and which indicate bugs
- **FR-038**: Standard Python exceptions (FileNotFoundError, PermissionError) MUST be re-raised as-is (not wrapped) for filesystem errors

---

### CHK049: Exception Message Format

**Gap**: Are exception message format requirements defined (structured vs prose, actionable context)?

**Decision**:
Exception messages MUST be actionable prose (not structured JSON) with three components:
1. **What failed**: Clear description of the operation
2. **Why it failed**: Root cause (missing field, invalid format, etc.)
3. **How to fix**: Actionable guidance for the user

**Format Template**:
```
{Operation} failed: {reason}. {actionable_guidance}
```

**Examples**:
```python
# Good
ParseError("Failed to parse conversation at line 1234: missing required field 'id'. Check export file integrity or re-export from ChatGPT.")

# Good
ValidationError("Invalid date format in conversation 'abc-123': expected ISO 8601 (YYYY-MM-DD), got '2024/01/01'. Use --from '2024-01-01' format.")

# Bad (not actionable)
ValueError("Invalid data")
```

**Rationale**: Users need to understand what went wrong and how to fix it without reading source code. Prose messages are more readable than JSON for CLI errors.

**New Requirements**:
- **FR-039**: All exception messages MUST follow the format: "{operation} failed: {reason}. {actionable_guidance}"
- **FR-040**: Exception messages MUST NOT expose raw stack traces, internal variable names, or implementation details
- **FR-041**: Exception messages MUST include context: conversation ID, file path, line number, or field name when applicable

---

### CHK050: Transient vs Permanent Errors

**Gap**: Are transient vs permanent error requirements distinguished (retry-able vs fail-fast)?

**Decision**:
**All errors are permanent (fail-fast)**. No retry logic in library.

**Permanent Errors** (library raises, does not retry):
- File not found → user must provide correct path
- Permission denied → user must fix permissions
- Malformed JSON → user must fix export file or re-export
- Unsupported schema → user must upgrade library or use compatible export

**Rationale**: Aligns with FR-033 (fail fast, no retries). Library consumers (like cognivault) can implement their own retry logic with backoff if needed. Library shouldn't guess retry strategies.

**New Requirements**:
- **FR-042**: Library MUST fail immediately on all errors (no automatic retries, no retry hints in exceptions)
- **FR-043**: Library MUST NOT implement retry logic for any operation (file access, parsing, validation)
- **FR-044**: Library consumers implementing retry logic MUST treat all exceptions as potentially permanent (no retry hints provided)

---

### CHK051: Exception Behavior in Iterators

**Gap**: Are requirements specified for exception behavior in iterators (StopIteration, cleanup guarantees)?

**Decision**:
Iterator exception protocol:
1. **Never raise StopIteration explicitly** (PEP 479 compliance)
2. **Raise custom exceptions** (ParseError, ValidationError) for failures
3. **Guarantee cleanup** via context managers (file handles closed even on exception)
4. **Include failure context** in exceptions (which conversation, which message)

**Pattern**:
```python
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    try:
        with open(file_path, 'rb') as f:
            for idx, conv_data in enumerate(ijson.items(f, 'item')):
                try:
                    yield parse_conversation(conv_data)
                except Exception as e:
                    raise ParseError(
                        f"Failed to parse conversation at index {idx}: {e}. "
                        f"File may be corrupted or use unsupported schema version."
                    ) from e
    except FileNotFoundError as e:
        raise  # Re-raise standard exceptions as-is
    except PermissionError as e:
        raise
```

**Rationale**: PEP 479 prevents StopIteration from leaking. Context managers guarantee cleanup. Exception chaining preserves debug info while providing user-friendly messages.

**New Requirements**:
- **FR-045**: Iterator methods MUST NOT raise StopIteration explicitly (use return to end iteration, per PEP 479)
- **FR-046**: Iterator methods MUST raise custom exceptions (ParseError, ValidationError) for parsing/validation failures during iteration
- **FR-047**: Iterator methods MUST use context managers to guarantee file handle cleanup even when exceptions occur
- **FR-048**: Iterator exceptions MUST include the item index or conversation ID where failure occurred

---

### CHK146: FileNotFoundError Behavior

**Gap**: Are requirements specified for FileNotFoundError behavior (message format, recovery guidance)?

**Decision**:
Raise standard `FileNotFoundError` (not wrapped) with actionable message:

```python
if not file_path.exists():
    raise FileNotFoundError(
        f"Export file not found: {file_path}. "
        f"Verify the file exists and the path is correct."
    )
```

**No wrapping**: Use standard Python exception for compatibility with existing error handling patterns.

**Rationale**: FileNotFoundError is well-understood by Python developers. Wrapping it breaks existing try/except patterns.

**New Requirements**:
- **FR-049**: Library MUST raise standard FileNotFoundError (not custom wrapper) when export file does not exist
- **FR-050**: FileNotFoundError message MUST include: full file path and suggestion to verify path correctness

---

### CHK147: PermissionError Behavior

**Gap**: Are requirements defined for PermissionError behavior (message format)?

**Decision**:
Raise standard `PermissionError` (not wrapped) with actionable message:

```python
try:
    with open(file_path, 'rb') as f:
        ...
except PermissionError:
    raise PermissionError(
        f"Cannot read export file: {file_path}. "
        f"Check file permissions (requires read access)."
    )
```

**Rationale**: Same as FileNotFoundError - standard exception for compatibility.

**New Requirements**:
- **FR-051**: Library MUST raise standard PermissionError (not custom wrapper) when file cannot be read due to permissions
- **FR-052**: PermissionError message MUST include: file path and guidance to check read permissions

---

### CHK148: ValueError in Library API

**Gap**: Are requirements specified for ValueError in library API (validation failures, when raised)?

**Decision**:
Use **custom ValidationError** (subclass of ValueError) for data validation failures:

```python
class ValidationError(ValueError, EchomineError):
    """Raised when conversation data fails validation (Pydantic, schema, formats)."""
    pass

# Usage
try:
    conversation = Conversation.model_validate(data)
except PydanticValidationError as e:
    raise ValidationError(
        f"Invalid conversation data in '{data.get('id', 'unknown')}': {e}. "
        f"Export file may be corrupted or use unsupported format."
    ) from e
```

**When raised**:
- Pydantic validation failures (missing fields, wrong types)
- Invalid date formats (not ISO 8601)
- Empty/invalid conversation IDs
- Malformed message structures

**Rationale**: Subclassing ValueError maintains compatibility with existing code catching ValueError, while providing specific exception type for Echomine validation failures.

**New Requirements**:
- **FR-053**: Library MUST define ValidationError exception (subclass of ValueError and EchomineError) for data validation failures
- **FR-054**: Library MUST raise ValidationError when Pydantic model validation fails with message including field name and expected format
- **FR-055**: ValidationError MUST be raised for: invalid date formats, missing required fields, malformed IDs, unsupported data types

---

### CHK149: StopIteration vs Custom Exceptions

**Gap**: Are requirements defined for StopIteration vs custom exceptions in iterator protocol?

**Decision**:
**Never explicitly raise StopIteration** from iterator methods (covered in CHK051).

**Rules**:
1. Use `return` to end iteration (implicit StopIteration)
2. Raise custom exceptions (ParseError, ValidationError) for actual failures
3. Python's iterator protocol handles StopIteration internally

**Anti-pattern**:
```python
# ❌ WRONG - explicit StopIteration
def stream_conversations():
    if not more_data:
        raise StopIteration  # PEP 479 violation
```

**Correct pattern**:
```python
# ✅ CORRECT - implicit via return
def stream_conversations():
    if not more_data:
        return  # Implicit StopIteration
    # Or just let generator exit naturally
```

**Rationale**: PEP 479 (Python 3.5+) converts StopIteration raised inside generators to RuntimeError. Explicit raises indicate code bug.

**New Requirements**:
- **FR-056**: Iterator methods MUST use `return` statements to end iteration (not explicit StopIteration)
- **FR-057**: If StopIteration is caught from underlying iterators (ijson), it MUST be allowed to propagate (not re-raised explicitly)

---

### CHK150: Exception Chaining

**Gap**: Are requirements specified for exception chaining (preserve original cause)?

**Decision**:
**Always use exception chaining** (`raise ... from ...`) to preserve debug context:

```python
try:
    data = json.loads(content)
except JSONDecodeError as e:
    raise ParseError(
        f"Failed to parse JSON at line {e.lineno}: {e.msg}. "
        f"Export file may be corrupted."
    ) from e  # ← Exception chaining preserves original
```

**Benefits**:
- Preserves full stack trace for debugging
- User sees friendly message
- Developers see technical details in `__cause__`

**Rationale**: Exception chaining is Python best practice. Provides both user-friendly messages and developer debug info.

**New Requirements**:
- **FR-058**: Library MUST use exception chaining (`raise NewException(...) from original`) when wrapping lower-level exceptions
- **FR-059**: Exception chains MUST preserve original exception in `__cause__` attribute for debugging
- **FR-060**: Top-level exception message MUST be user-friendly; chained exception MAY contain technical details

---

### CHK154: cognivault Error Handling Contract

**Gap**: Are requirements specified for which exceptions cognivault must catch?

**Decision**:
**cognivault MUST catch**:
```python
from echomine import OpenAIAdapter, EchomineError

try:
    adapter = OpenAIAdapter()
    for conversation in adapter.stream_conversations(file_path):
        cognivault.ingest(conversation)
except EchomineError as e:
    # All library operational errors
    logger.error(f"Echomine parsing failed: {e}")
except (FileNotFoundError, PermissionError) as e:
    # Filesystem errors
    logger.error(f"File access failed: {e}")
except Exception as e:
    # Unexpected errors (library bugs or system issues)
    logger.exception(f"Unexpected error: {e}")
    raise  # Re-raise bugs
```

**cognivault should NOT catch**:
- `KeyboardInterrupt` (user cancellation)
- `SystemExit` (shutdown signals)
- `MemoryError` (system-level, can't recover)

**Rationale**: Catching EchomineError base class handles all library errors. Standard filesystem exceptions handled separately. Other exceptions indicate bugs or system failures.

**New Requirements**:
- **FR-061**: Library documentation MUST specify exception handling contract for library consumers (which exceptions to catch)
- **FR-062**: quickstart.md MUST include example showing cognivault catching EchomineError, FileNotFoundError, PermissionError
- **FR-063**: Library consumers MUST NOT catch KeyboardInterrupt, SystemExit, or MemoryError (let them propagate)

---

## Summary: Library Exception Contract

**Total Gaps Resolved**: 11
**New Functional Requirements**: FR-035 through FR-063 (29 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-035 to FR-063)
- ✅ data-model.md (add exception class definitions)
- ✅ contracts/conversation_provider_protocol.py (add exception specifications to docstrings)
- ✅ quickstart.md (add exception handling examples for cognivault)

---

## 2. Progress Indicator Behavior (9 items)

### CHK034, CHK035, CHK166, CHK167: Progress When Total Count Unknown

**Gap**: How do progress indicators work when ijson streaming doesn't know total count upfront?

**Decision**:
Use **spinner mode** (not percentage) when total count is unknown:

**Progress Modes**:
1. **Spinner mode** (default for streaming): Indeterminate progress showing activity
2. **Percentage mode** (only when total known): Progress bar with % complete

**ijson Streaming Challenge**:
- ijson parses incrementally → total conversation count unknown until file end
- Cannot show "45% complete" without knowing total
- Solution: Show spinner with item count: "Parsed 123 conversations..."

**Implementation**:
```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    TextColumn("[cyan]{task.fields[count]} conversations"),
) as progress:
    task = progress.add_task("Parsing", count=0)
    for idx, conversation in enumerate(adapter.stream_conversations(file_path)):
        progress.update(task, count=idx + 1)
```

**Rationale**: Spinner + count provides user feedback without false precision. Percentage requires knowing total upfront (defeats streaming's memory advantage).

**New Requirements**:
- **FR-064**: Progress indicators MUST use spinner mode (not percentage) when total item count is unknown upfront
- **FR-065**: Progress indicators in spinner mode MUST display running count of items processed ("Parsed 123 conversations...")
- **FR-066**: Progress indicators MAY switch to percentage mode if total count becomes known (not required for v1.0)
- **FR-067**: Progress indicators MUST use rich library for terminal rendering (spinners, text formatting)

---

### CHK110, CHK168: Progress Update Frequency

**Gap**: How often should progress indicators update?

**Decision**:
**Time-based updates** (not every item) to avoid terminal flickering:

**Update Strategy**:
- Update every **100ms** (10 updates/second) OR every **100 items**, whichever comes first
- For fast parsing (>1000 items/sec): Update by item count to avoid excessive redraws
- For slow parsing (<10 items/sec): Update by time to show responsiveness

**Implementation**:
```python
import time

last_update = time.time()
update_interval = 0.1  # 100ms

for idx, conversation in enumerate(conversations):
    now = time.time()
    if now - last_update >= update_interval or idx % 100 == 0:
        progress.update(task, count=idx + 1)
        last_update = now
```

**Rationale**: Balance responsiveness (user sees activity) vs performance (avoid terminal slowdown). 100ms is imperceptible delay, 10 updates/sec feels fluid.

**New Requirements**:
- **FR-068**: Progress indicators MUST update at most every 100ms (time-based) to avoid excessive terminal redraws
- **FR-069**: Progress indicators MUST update at least every 100 items (item-based) to show progress on fast operations
- **FR-070**: Progress update frequency MAY be adaptive based on parsing speed (slower operations update more frequently)

---

### CHK116, CHK169: Progress Indicator Formats & Cleanup

**Gap**: What formats are used? How is cleanup handled?

**Decision**:
**Standard formats**:
- **Spinner**: Rotating character (⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
- **Count**: "Parsed 1,234 conversations"
- **Rate**: "Parsing at 145 conversations/sec" (optional)
- **No ETA**: Cannot estimate time without total count

**Cleanup** (automatic via rich):
- Progress bar cleared on completion (cursor restored)
- Final summary line persists: "✓ Parsed 1,234 conversations in 8.5s"
- No manual cleanup needed (rich Context Manager handles it)

**New Requirements**:
- **FR-071**: Progress indicators MUST use spinner animation from rich library (rotating characters, not static text)
- **FR-072**: Progress indicators MUST display item count with thousand separators ("1,234" not "1234")
- **FR-073**: Progress indicators SHOULD display parsing rate (items/second) when available
- **FR-074**: Progress indicators MUST NOT display ETA (estimated time remaining) when total count is unknown
- **FR-075**: Progress indicators MUST clear on completion and display final summary with total count and elapsed time

---

### CHK170: Progress in Library vs CLI

**Gap**: How are progress indicators split between library and CLI?

**Decision**:
**Library emits events → CLI renders progress**

**Architecture**:
```python
# Library: Emit progress events (callback pattern)
from typing import Callable, Optional

def stream_conversations(
    file_path: Path,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Iterator[Conversation]:
    """
    Stream conversations with optional progress reporting.

    Args:
        file_path: Export file path
        progress_callback: Optional callback(count) called periodically with item count
    """
    for idx, conversation in enumerate(parse_file(file_path)):
        if progress_callback and idx % 100 == 0:
            progress_callback(idx + 1)
        yield conversation

# CLI: Render progress with rich
def cli_search_command(file_path, keywords):
    with Progress(...) as progress:
        task = progress.add_task("Searching", count=0)

        def update_progress(count):
            progress.update(task, count=count)

        adapter = OpenAIAdapter()
        results = adapter.search(file_path, query, progress_callback=update_progress)
```

**Rationale**: Library stays generic (no terminal dependencies). CLI owns rendering. Allows library consumers to implement custom progress (logging, web UI, etc.).

**New Requirements**:
- **FR-076**: Library methods accepting large datasets (stream_conversations, search) MUST accept optional progress_callback parameter
- **FR-077**: progress_callback MUST be called periodically with current item count (not percentage)
- **FR-078**: Library MUST NOT depend on rich or other terminal libraries (progress rendering is CLI responsibility)
- **FR-079**: CLI MUST implement progress rendering using rich library and invoke library methods with progress callbacks

---

## Summary: Progress Indicator Behavior

**Total Gaps Resolved**: 9
**New Functional Requirements**: FR-064 through FR-079 (16 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-064 to FR-079)
- ✅ data-model.md (add progress_callback signature to protocol methods)
- ✅ contracts/conversation_provider_protocol.py (add progress_callback to method signatures)
- ✅ quickstart.md (add example showing library consumers implementing custom progress)

---

## 3. Schema Version Detection (8 items)

### CHK079, CHK080, CHK161: Detecting Schema Versions

**Gap**: How does the library detect which OpenAI export schema version is used?

**Decision**:
**Heuristic-based detection** (no version field in current OpenAI exports):

**Detection Strategy**:
1. **Check for version field** (future-proofing): `data.get('version')` or `data.get('schema_version')`
2. **Heuristic checks** (current exports have no version):
   - **v1 (current)**: Top-level array with `mapping` field in conversations
   - **Future v2**: Might use different structure (detect via field presence)

**Implementation**:
```python
def detect_schema_version(export_data: dict) -> str:
    """Detect OpenAI export schema version via heuristics."""

    # Future: Explicit version field
    if 'version' in export_data:
        return export_data['version']

    # v1 heuristic: Has 'mapping' field in first conversation
    if isinstance(export_data, list) and len(export_data) > 0:
        first_conv = export_data[0]
        if 'mapping' in first_conv and 'create_time' in first_conv:
            return "1.0"  # Current ChatGPT export format

    # Unknown schema
    raise SchemaVersionError(
        f"Unsupported export schema version. "
        f"This file does not match any known OpenAI export format. "
        f"Upgrade echomine or re-export from ChatGPT with current format."
    )
```

**Rationale**: OpenAI doesn't include version in exports (as of 2024). Heuristics detect current format. Future versions can add explicit version field.

**New Requirements**:
- **FR-080**: Library MUST attempt to detect export schema version using heuristic checks on export structure
- **FR-081**: Library MUST check for explicit version field ('version' or 'schema_version') before falling back to heuristics
- **FR-082**: Schema detection MUST occur before parsing conversations (fail fast if unsupported)
- **FR-083**: Schema detection MUST use field presence checks (e.g., 'mapping' field indicates v1.0 format)

---

### CHK162, CHK164: Supported Schema Versions & Migration

**Gap**: Which schema versions are supported? How does migration work?

**Decision**:
**v1.0 only in MVP** (OpenAI current format), extensible architecture for future versions:

**Supported Versions**:
- **v1.0**: Current ChatGPT export format (2024) - SUPPORTED
- **v2.0+**: Future OpenAI changes - NOT SUPPORTED (graceful error)

**Migration Strategy** (future):
- Adapters can internally normalize v1/v2 to common Conversation model
- Library consumers see same API regardless of schema version
- Not implemented in v1.0 (single schema supported)

**New Requirements**:
- **FR-084**: Library v1.0 MUST support only OpenAI export schema v1.0 (current ChatGPT format as of 2024)
- **FR-085**: Library MUST raise SchemaVersionError for any detected schema version other than v1.0
- **FR-086**: Future library versions MAY support multiple schema versions by normalizing to common Conversation model
- **FR-087**: Schema version support MUST be documented in README and library docstrings

---

### CHK163, CHK165: Schema Version Error Messages & Logging

**Gap**: What do users see when unsupported version detected? Where is it logged?

**Decision**:
**Actionable error message + INFO log**:

**Error Message**:
```python
raise SchemaVersionError(
    f"Unsupported export schema version: {detected_version}. "
    f"Echomine v1.0 supports only OpenAI export format v1.0 (current as of 2024). "
    f"To fix: (1) Re-export from ChatGPT, or (2) Upgrade echomine if newer version available."
)
```

**Logging**:
```python
logger.info(
    "schema_version_detected",
    version=detected_version,
    file_name=file_path.name,
    supported=detected_version == "1.0"
)
```

**Rationale**: Error message guides user to fix. Log captures version for analytics (helps decide when to support v2).

**New Requirements**:
- **FR-088**: SchemaVersionError message MUST include: detected version, supported versions, and remediation steps
- **FR-089**: Library MUST log schema version detection at INFO level with fields: version, file_name, supported (bool)
- **FR-090**: Schema version errors MUST suggest re-exporting from ChatGPT as first remediation step

---

### CHK132: Handling Future OpenAI Format Changes

**Gap**: What's the strategy for handling future schema changes?

**Decision**:
**Graceful failure + version-gated support**:

**Strategy**:
1. **Detect new schema** via heuristics (unknown fields, structure changes)
2. **Fail with clear error** (not cryptic parse errors)
3. **Release new library version** supporting both v1.0 and v2.0 if needed
4. **Deprecation path**: Eventually drop v1.0 support (semantic versioning MAJOR bump)

**Not in v1.0**: Multi-version support deferred until v2 schema actually exists.

**New Requirements**:
- **FR-091**: When future schema changes are detected, library MUST fail with SchemaVersionError (not generic parse errors)
- **FR-092**: Future library versions adding new schema support MUST maintain backward compatibility with v1.0 (MINOR version bump)
- **FR-093**: Dropping support for old schemas MUST trigger MAJOR version bump per semantic versioning

---

## Summary: Schema Version Detection

**Total Gaps Resolved**: 8
**New Functional Requirements**: FR-080 through FR-093 (14 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-080 to FR-093)
- ✅ data-model.md (add SchemaVersionError exception, schema detection logic)
- ✅ contracts/conversation_provider_protocol.py (add schema version detection requirements)

---

## 4. Concurrent Access Patterns (10 items)

### CHK010, CHK011, CHK086, CHK087, CHK175, CHK176: File Locking & Concurrent Reads

**Gap**: Can multiple processes read the same export file? Are locks needed?

**Decision**:
**Read-only, no file locking** - OS handles concurrent reads:

**Concurrency Model**:
- **Multiple processes** can read same file simultaneously (OS read locks are shared)
- **No file locking by library** (read-only access doesn't need exclusive locks)
- **Thread-safe file opening** (each process/thread opens independent file handle)
- **OS guarantees**: File content consistent during read (POSIX, Windows both support)

**Safe Patterns**:
```python
# ✅ SAFE: Multiple processes reading same file
# Process 1
adapter1 = OpenAIAdapter()
for conv in adapter1.stream_conversations(Path("export.json")):
    process(conv)

# Process 2 (concurrent)
adapter2 = OpenAIAdapter()
for conv in adapter2.stream_conversations(Path("export.json")):
    index(conv)

# Each process has independent file handle
```

**Unsafe Patterns**:
```python
# ❌ UNSAFE: Concurrent writes (NOT SUPPORTED)
# Library is read-only, but if external process modifies file during read:
# - Behavior undefined (partial writes, corruption possible)
# - Library does not detect mid-read modifications
```

**Rationale**: Export files are read-only artifacts (not databases). OS provides read concurrency. Adding locks hurts performance with no benefit.

**New Requirements**:
- **FR-094**: Library MUST support concurrent reads of same export file by multiple processes (each with independent file handle)
- **FR-095**: Library MUST NOT acquire file locks (advisory or exclusive) when opening export files for reading
- **FR-096**: Library ASSUMES export files are immutable during read (behavior undefined if file modified concurrently)
- **FR-097**: Library documentation MUST state that concurrent writes to export files are NOT supported

---

### CHK177, CHK179, CHK180: Thread Safety & Race Conditions

**Gap**: Is OpenAIAdapter thread-safe? Can one instance be used across threads?

**Decision**:
**Adapters are thread-safe for concurrent reads, but iterators are NOT**:

**Thread Safety Model**:
- **Adapter instances**: Thread-safe (stateless, no shared mutable state)
- **Iterators**: NOT thread-safe (one thread per iterator)

**Safe Patterns**:
```python
# ✅ SAFE: Share adapter, use separate iterators per thread
adapter = OpenAIAdapter()  # Shared across threads

def worker_thread():
    # Each thread creates its own iterator
    for conv in adapter.stream_conversations(file_path):
        process(conv)

threads = [Thread(target=worker_thread) for _ in range(4)]
```

**Unsafe Patterns**:
```python
# ❌ UNSAFE: Multiple threads sharing same iterator
adapter = OpenAIAdapter()
iterator = adapter.stream_conversations(file_path)

def worker_thread():
    for conv in iterator:  # Multiple threads consuming same iterator
        process(conv)  # RACE CONDITION: iterator state corrupted
```

**Rationale**: Adapters are stateless factories (thread-safe). Iterators maintain internal state (file position, buffers) → not thread-safe.

**New Requirements**:
- **FR-098**: OpenAIAdapter instances MUST be thread-safe (safe to share across threads)
- **FR-099**: Iterators returned by stream_conversations/search MUST NOT be shared across threads (undefined behavior)
- **FR-100**: Each thread MUST create its own iterator by calling stream_conversations/search separately
- **FR-101**: Library documentation MUST specify thread safety guarantees for adapters and iterators

---

### CHK178: File Modification During Reading

**Gap**: What happens if export file is modified while library is reading it?

**Decision**:
**Undefined behavior - library does not detect mid-read modifications**:

**Scenarios**:
1. **File appended during read**: May or may not see new data (OS-dependent)
2. **File truncated during read**: Likely parse error or incomplete data
3. **File deleted during read**: Open file handle continues (Unix), or error (Windows)

**Library Response**:
- **No detection**: Library doesn't monitor file modifications
- **Best effort parsing**: Parse whatever data is available
- **Fail on corruption**: If modification causes malformed JSON → ParseError

**Guidance to Users**:
- Treat export files as **immutable** during parsing
- Use temp copies if concurrent modification possible

**Rationale**: Detecting file modifications adds complexity (inotify, polling) with marginal benefit. Export files are artifacts, not live databases.

**New Requirements**:
- **FR-102**: Library behavior is UNDEFINED if export file is modified (appended, truncated, deleted) during parsing
- **FR-103**: Library MUST NOT implement file modification detection (no inotify, stat polling, checksums)
- **FR-104**: Documentation MUST advise users to treat export files as immutable during parsing

---

## Summary: Concurrent Access Patterns

**Total Gaps Resolved**: 10
**New Functional Requirements**: FR-094 through FR-104 (11 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-094 to FR-104)
- ✅ quickstart.md (add concurrent access examples, thread safety warnings)

---

## 5. Graceful Degradation UX (6 items)

### CHK078, CHK171: What Library Consumers See When Entries Skipped

**Gap**: FR-004 says log warnings when skipping malformed entries. Do library consumers see anything?

**Decision**:
**Callbacks + structured logs** (no console output from library):

**Library Behavior**:
- **Emit structured log** (WARNING level): `logger.warning("conversation_skipped", conversation_id=..., reason=...)`
- **Optional callback**: `on_skip_callback(conversation_id, reason)` parameter
- **No console output**: Library writes to logger (stderr), not directly to console

**Library Consumer Options**:
1. **Check logs**: Consumers configure structlog to capture warnings
2. **Use callback**: Consumers provide callback to track skipped entries in real-time
3. **Ignore**: Consumers see only successfully parsed conversations (warnings optional)

**Example**:
```python
skipped = []

def handle_skip(conv_id, reason):
    skipped.append((conv_id, reason))

adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(file_path, on_skip=handle_skip):
    process(conv)

print(f"Skipped {len(skipped)} conversations")
```

**Rationale**: Library consumers decide how to handle skips (logs, UI, silent). Library doesn't assume terminal output.

**New Requirements**:
- **FR-105**: Library MUST emit structured WARNING log when skipping malformed entries with fields: conversation_id, reason, file_name
- **FR-106**: Library methods (stream_conversations, search) MAY accept optional on_skip callback parameter
- **FR-107**: on_skip callback MUST receive conversation_id (or index) and reason string when entry is skipped
- **FR-108**: Library MUST NOT write skip messages directly to console (only to structured logger)

---

### CHK117, CHK172, CHK173, CHK174: Summary Reporting & Partial Success

**Gap**: Should library provide summary after processing? How to indicate partial success?

**Decision**:
**CLI shows summary, library emits completion log**:

**Library**: Emit INFO log on completion
```python
logger.info(
    "parsing_completed",
    total_conversations=1234,
    skipped_conversations=5,
    file_name=file_path.name,
    duration_seconds=8.5
)
```

**CLI**: Display summary to user
```
✓ Parsed 1,234 conversations in 8.5s
⚠ Skipped 5 conversations (see logs for details)
```

**Partial Success Indicators**:
- **Exit code 0**: Parsing completed (even with skips)
- **WARNING logs**: Indicate skipped entries
- **Summary line**: Shows total vs skipped

**No Failure**: Skipping malformed entries is not a failure (per FR-004 requirement to continue).

**Rationale**: Separation of concerns (library logs, CLI renders). Users get summary without forcing library to know about console.

**New Requirements**:
- **FR-109**: Library MUST emit INFO log on completion with fields: total_conversations, skipped_conversations, duration_seconds
- **FR-110**: CLI MUST display summary line showing total conversations and skip count after parsing completes
- **FR-111**: CLI MUST exit with code 0 even when conversations are skipped (partial success is success)
- **FR-112**: CLI summary MUST reference logs for details when conversations are skipped ("see logs for details")

---

## Summary: Graceful Degradation UX

**Total Gaps Resolved**: 6
**New Functional Requirements**: FR-105 through FR-112 (8 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-105 to FR-112)
- ✅ data-model.md (add on_skip callback signature)
- ✅ contracts/conversation_provider_protocol.py (add on_skip parameter to methods)
- ✅ quickstart.md (add example showing cognivault handling skipped entries)

---

## FINAL SUMMARY: All Tier 1 Critical Gaps Resolved

**Total Gaps Addressed**: 44 items across 5 critical areas
**Total New Functional Requirements**: 78 (FR-035 through FR-112)
**Status**: ✅ Complete

---

### Gap Resolution Breakdown

| Area | Gaps | New FRs | Key Decisions |
|------|------|---------|---------------|
| **1. Library Exception Contract** | 11 | 29 | EchomineError hierarchy, actionable messages, PEP 479 compliance, exception chaining |
| **2. Progress Indicator Behavior** | 9 | 16 | Spinner mode for streaming, 100ms update frequency, callback pattern, rich library |
| **3. Schema Version Detection** | 8 | 14 | Heuristic detection, v1.0 only for MVP, graceful failure, INFO logging |
| **4. Concurrent Access Patterns** | 10 | 11 | No file locking, thread-safe adapters, single-thread iterators, read-only assumption |
| **5. Graceful Degradation UX** | 6 | 8 | on_skip callbacks, completion logging, partial success = exit code 0, CLI summary |
| **TOTAL** | **44** | **78** | |

---

### Artifacts Requiring Updates

**1. spec.md**:
- Add FR-035 through FR-112 (78 new functional requirements)
- Sections: Functional Requirements → Library Interface, Error Handling, Observability

**2. data-model.md**:
- Add exception class hierarchy (EchomineError, ParseError, ValidationError, SchemaVersionError, FileAccessError)
- Add progress_callback and on_skip callback type signatures
- Add schema version detection models

**3. contracts/conversation_provider_protocol.py**:
- Update method signatures with progress_callback and on_skip parameters
- Add exception specifications to docstrings
- Document thread safety guarantees

**4. quickstart.md**:
- Add cognivault exception handling example (catching EchomineError)
- Add custom progress reporting example for library consumers
- Add concurrent access patterns and thread safety warnings
- Add on_skip callback usage example

---

### Key Architectural Decisions

**Exception Contract**:
- Public API exceptions inherit from EchomineError base class
- Standard Python exceptions (FileNotFoundError, PermissionError) re-raised as-is
- Exception messages follow "{operation} failed: {reason}. {guidance}" format
- Always use exception chaining (`raise ... from ...`) to preserve debug context

**Progress Reporting**:
- Library uses callback pattern (no terminal dependencies)
- CLI renders progress with rich library
- Spinner mode for streaming (total count unknown)
- Update frequency: 100ms or 100 items, whichever comes first

**Schema Versioning**:
- Heuristic-based detection (no version field in OpenAI exports)
- v1.0 only supported in MVP
- Graceful failure with SchemaVersionError for unsupported versions
- Future: multi-version support with normalization to common Conversation model

**Concurrency**:
- Multiple processes can read same file concurrently (no locking)
- Adapter instances are thread-safe (stateless)
- Iterators are NOT thread-safe (one thread per iterator)
- Export files assumed immutable during read (no modification detection)

**Graceful Degradation**:
- Skip malformed entries with WARNING log
- Optional on_skip callback for library consumers
- CLI shows summary with skip count on completion
- Exit code 0 even with skips (partial success is success)

---

### Next Steps

1. ✅ Update spec.md with FR-035 through FR-112
2. ✅ Update data-model.md with exception classes and callback signatures
3. ✅ Update contracts/conversation_provider_protocol.py with new method signatures
4. ✅ Update quickstart.md with practical examples
5. Ready for `/speckit.tasks` to generate implementation tasks

---
# TIER 2: HIGH-PRIORITY ARCHITECTURAL GAPS

**Total Gaps**: 23 items
**Status**: In Progress

---

## 6. Core Library API (6 items)

### CHK001: Adapter Initialization

**Gap**: Are initialization requirements defined for all adapter classes (OpenAIAdapter constructor signatures, parameters, validation)?

**Decision**:
**Stateless constructors with no configuration parameters**:

```python
class OpenAIAdapter:
    """Stateless adapter for OpenAI ChatGPT exports.
    
    Thread-safe (per FR-098): Can be shared across threads.
    File paths passed to methods, not constructor.
    """
    
    def __init__(self) -> None:
        """Initialize adapter.
        
        No configuration needed - adapter is stateless.
        File paths are passed to methods (stream_conversations, search).
        """
        pass
```

**Rationale**:
- Stateless design enables thread safety (FR-098)
- No configuration = no state to manage
- File paths in method calls (not constructor) allow adapter reuse across different files
- Simpler API for library consumers

**New Requirements**:
- **FR-113**: OpenAIAdapter constructor MUST NOT accept configuration parameters (stateless design)
- **FR-114**: Adapter instances MUST be reusable across different export files (file paths passed to methods)
- **FR-115**: Adapter __init__ MUST be lightweight (no I/O, no validation, instantiation should be instant)

---

### CHK003: Iterator Behavior

**Gap**: Are iterator behavior requirements specified (what happens on iteration errors, partial failures, cleanup)?

**Decision**:
**Iterators are single-use, with guaranteed cleanup via context managers**:

**Single-Use Iterators**:
```python
adapter = OpenAIAdapter()

# First iteration - works
for conv in adapter.stream_conversations(file_path):
    process(conv)

# Second call returns NEW iterator (not resuming old one)
for conv in adapter.stream_conversations(file_path):
    # This works - new iterator from start of file
    process(conv)
```

**Early Termination Cleanup**:
```python
# Cleanup happens even if iteration stops early
for conv in adapter.stream_conversations(file_path):
    if some_condition:
        break  # File handle closed automatically via context manager
```

**Rationale**: Python generators with context managers naturally handle cleanup. Explicit cleanup methods would be redundant.

**New Requirements**:
- **FR-116**: Iterators MUST be single-use (exhausted after complete iteration)
- **FR-117**: Calling stream_conversations/search multiple times MUST return independent iterators (not resume previous)
- **FR-118**: File handles MUST be closed when iteration stops early (break, exception, or completion)
- **FR-119**: Library MUST use context managers internally to guarantee file handle cleanup

---

### CHK004: Context Manager Support

**Gap**: Are context manager requirements defined for file handle cleanup (with statement support)?

**Decision**:
**Adapters do NOT need to be context managers** (they're stateless), but **methods use context managers internally**:

```python
# ✅ Adapters are NOT context managers (no need)
adapter = OpenAIAdapter()  # No 'with' statement needed

# ✅ Methods use context managers internally
for conv in adapter.stream_conversations(file_path):
    process(conv)  # File handle managed internally

# ❌ This syntax is NOT supported (adapters not context managers)
# with OpenAIAdapter() as adapter:  # Not needed
#     ...
```

**Internal Implementation** (uses context manager):
```python
def stream_conversations(self, file_path: Path) -> Iterator[Conversation]:
    with open(file_path, 'rb') as f:  # Context manager guarantees cleanup
        for conversation in ijson.items(f, 'item'):
            yield parse_conversation(conversation)
    # File closed automatically when generator exits
```

**Rationale**: Adapters are stateless (no resources to manage). File handles managed internally by methods.

**New Requirements**:
- **FR-120**: Adapter classes MUST NOT implement context manager protocol (__enter__, __exit__)
- **FR-121**: Library methods MUST use context managers internally for all file I/O operations
- **FR-122**: File handles MUST be opened and closed within method scope (not stored in adapter state)

---

### CHK006: Versioning Policy

**Gap**: Are requirements defined for library version compatibility (semantic versioning policy, deprecation warnings)?

**Decision**:
**Strict semantic versioning with 2-release deprecation period**:

**Semantic Versioning**:
- **MAJOR** (X.0.0): Breaking API changes
  - Method signature changes (removing parameters, changing types)
  - Removed public classes/functions
  - Changed exception types in API contract
  - Example: Removing `on_skip` parameter from `stream_conversations`
  
- **MINOR** (0.X.0): Backward-compatible additions
  - New methods on existing classes
  - New optional parameters (with defaults)
  - New exception types (additions to hierarchy)
  - New export format support (e.g., Claude adapter)
  - Example: Adding `progress_callback` parameter (optional, defaults to None)
  
- **PATCH** (0.0.X): Bug fixes, no API changes
  - Performance improvements
  - Bug fixes in parsing logic
  - Documentation updates
  - Example: Fixing TF-IDF scoring bug

**Deprecation Process**:
1. Release N: Add deprecation warning (DeprecationWarning)
2. Release N+1: Warning remains, document migration path
3. Release N+2 (MAJOR): Remove deprecated feature

**Deprecation Example**:
```python
import warnings

def old_method(self):
    warnings.warn(
        "old_method() is deprecated and will be removed in v2.0.0. "
        "Use new_method() instead. See migration guide: https://...",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method()
```

**Rationale**: Clear versioning prevents breaking library consumers. 2-release warning gives time to migrate.

**New Requirements**:
- **FR-123**: Library MUST follow semantic versioning (MAJOR.MINOR.PATCH) strictly
- **FR-124**: Breaking API changes MUST trigger MAJOR version bump
- **FR-125**: New optional parameters or features MUST trigger MINOR version bump
- **FR-126**: Bug fixes with no API changes MUST trigger PATCH version bump
- **FR-127**: Deprecated features MUST emit DeprecationWarning for at least 2 releases before removal
- **FR-128**: Deprecation warnings MUST include: removal version, replacement method, and migration guide URL
- **FR-129**: Library version MUST be available via `echomine.__version__` attribute

---

### CHK008: Generator Cleanup

**Gap**: Are generator cleanup requirements specified (what happens when iteration stops early, resource disposal)?

**Decision**:
**Context managers guarantee cleanup, even with early termination**:

**Implementation Pattern**:
```python
def stream_conversations(
    self,
    file_path: Path,
    progress_callback: Optional[ProgressCallback] = None,
    on_skip: Optional[OnSkipCallback] = None
) -> Iterator[Conversation]:
    with open(file_path, 'rb') as f:
        try:
            for idx, conv_data in enumerate(ijson.items(f, 'item')):
                # Progress callback
                if progress_callback and idx % 100 == 0:
                    progress_callback(idx + 1)
                
                # Parse and yield
                try:
                    yield parse_conversation(conv_data)
                except ValidationError as e:
                    # Skip malformed entry
                    if on_skip:
                        on_skip(conv_data.get('id', str(idx)), str(e))
        finally:
            # Cleanup happens here (context manager ensures it runs)
            # Even if:
            # - Consumer breaks early
            # - Exception raised during iteration
            # - Generator garbage collected without being exhausted
            pass
    # File handle closed when exiting 'with' block
```

**Guaranteed Cleanup Scenarios**:
- ✅ Normal completion (iterator exhausted)
- ✅ Early break by consumer
- ✅ Exception during iteration
- ✅ Generator garbage collected (never started or partially consumed)

**Rationale**: Python's context manager + try/finally guarantees cleanup in ALL scenarios.

**New Requirements**:
- **FR-130**: Generator functions MUST use try/finally to guarantee cleanup code execution
- **FR-131**: File handles MUST be managed via context managers (not manual open/close)
- **FR-132**: Cleanup MUST occur even when: iteration breaks early, exceptions raised, or generator garbage collected
- **FR-133**: Library MUST NOT rely on __del__ methods for cleanup (use context managers instead)

---

### CHK009: Backpressure Handling

**Gap**: Are backpressure handling requirements defined for consumers processing slower than parser yields?

**Decision**:
**No explicit backpressure mechanism needed - Python generators handle it naturally**:

**How Python Generators Handle Backpressure**:
```python
def stream_conversations(file_path: Path) -> Iterator[Conversation]:
    with open(file_path, 'rb') as f:
        for conv_data in ijson.items(f, 'item'):
            # Parser PAUSES here until consumer requests next item
            # No memory buildup - ijson only reads what's needed
            yield parse_conversation(conv_data)

# Consumer controls pace
adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(large_file):
    # Slow processing (e.g., network call)
    time.sleep(1)  # Generator pauses automatically
    cognivault.ingest(conv)
```

**No Buffering**:
- ijson reads JSON incrementally (constant memory)
- Generator yields one item at a time
- If consumer is slow, parsing slows down (no buffering)
- If consumer is fast, parsing runs at max speed

**Memory Safety**:
- Slow consumer → Parser waits, no memory buildup
- Fast consumer → Parser runs at ijson speed (~1000 items/sec)
- Memory usage stays constant regardless of consumer speed

**Rationale**: Python generators are pull-based (consumer controls flow). No need for explicit backpressure mechanisms (queues, buffers, rate limiting).

**New Requirements**:
- **FR-134**: Library MUST NOT implement explicit backpressure mechanisms (queues, buffers, rate limiters)
- **FR-135**: Generators MUST yield one item at a time (no internal buffering beyond ijson buffers)
- **FR-136**: Memory usage MUST remain constant regardless of consumer processing speed
- **FR-137**: Documentation MUST explain that consumers control parsing pace (generators pause when consumer processing)

---

## Summary: Core Library API

**Total Gaps Resolved**: 6
**New Functional Requirements**: FR-113 through FR-137 (25 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-113 to FR-137)
- ✅ data-model.md (add adapter initialization, versioning policy)
- ✅ contracts/conversation_provider_protocol.py (add initialization requirements, cleanup guarantees)
- ✅ quickstart.md (add examples showing adapter reuse, cleanup behavior)

---

# TIER 2: HIGH-PRIORITY ARCHITECTURAL GAPS (Chunk 2/3)

## 2. Type Safety & Contracts (7 items)

### CHK015: Pydantic Validation Error Handling

**Gap**: Are requirements defined for handling type validation failures from Pydantic (what exceptions, error messages)?

**Decision**:
**ValidationError with field-level details**:

**Error Handling Contract**:
- Pydantic raises `pydantic.ValidationError` on model validation failures
- Library MUST catch and re-raise as `echomine.ValidationError` (inherits from ValueError and EchomineError)
- Error messages MUST include: field name, invalid value, expected type, constraint violation

**Example Scenario**:
```python
# Invalid conversation data (missing required 'title' field)
conv_data = {
    "id": "conv-123",
    "created_at": "2024-01-15T10:30:00Z",
    # Missing: title field
    "messages": []
}

# Library catches pydantic.ValidationError and re-raises
try:
    conv = Conversation.model_validate(conv_data)
except pydantic.ValidationError as e:
    raise ValidationError(
        f"Conversation validation failed at index 42: {e}. "
        f"Missing required field: 'title'. "
        f"Export file may be corrupted or from unsupported schema version."
    ) from e
```

**Error Message Format**:
```
Conversation validation failed at index {idx}: {pydantic_error}.
{field_details}
{remediation_guidance}
```

**Field-Level Details** (from Pydantic):
- `Field required: title` (missing required field)
- `Input should be a valid string: received int` (type mismatch)
- `String should have at most 500 characters: received 1024` (constraint violation)

**Rationale**: Pydantic provides excellent validation errors. Re-wrapping as `ValidationError` maintains library exception contract while preserving Pydantic's detailed messages.

**New Requirements**:
- **FR-138**: Library MUST catch `pydantic.ValidationError` and re-raise as `echomine.ValidationError`
- **FR-139**: ValidationError messages MUST include: conversation/message index, field name, and invalid value summary
- **FR-140**: ValidationError messages MUST preserve Pydantic's field-level error details via exception chaining (`raise ... from e`)
- **FR-141**: ValidationError MUST include remediation guidance (e.g., "Check export schema version" or "Re-export from ChatGPT")

---

### CHK016: Immutability Contract Documentation

**Gap**: Are immutability contract requirements documented (prohibition of in-place modifications, copy-on-write patterns)?

**Decision**:
**Frozen Pydantic models - all models immutable**:

**Immutability Contract**:
- ALL data models (`Conversation`, `Message`, `SearchResult`, `SearchQuery`) MUST be frozen
- Pydantic configuration: `model_config = ConfigDict(frozen=True)`
- In-place modifications raise `pydantic.ValidationError` with clear message
- Modifications require creating new instance via `.model_copy(update={...})`

**Example**:
```python
from echomine.models import Conversation

# ✅ Creating conversation
conv = Conversation(
    id="conv-123",
    title="My Conversation",
    created_at=datetime.now(),
    messages=[]
)

# ❌ In-place modification (raises ValidationError)
try:
    conv.title = "Updated Title"
except ValidationError as e:
    print(e)  # "Instance is frozen: cannot set attribute 'title'"

# ✅ Copy-on-write pattern (correct approach)
updated_conv = conv.model_copy(update={"title": "Updated Title"})
assert conv.title == "My Conversation"  # Original unchanged
assert updated_conv.title == "Updated Title"  # New instance
```

**Why Immutability**:
1. **Thread safety**: Immutable objects safe to share across threads
2. **Predictability**: No hidden state mutations
3. **Library API clarity**: Clear that library returns read-only data
4. **Hash stability**: Can use conversations as dict keys (if needed)

**Rationale**: Immutability prevents accidental mutations and makes library behavior predictable. cognivault can safely share conversation objects across threads.

**New Requirements**:
- **FR-142**: ALL Pydantic models (`Conversation`, `Message`, `SearchResult`, `SearchQuery`) MUST be frozen (frozen=True)
- **FR-143**: Attempting to modify frozen models MUST raise `pydantic.ValidationError` with message "Instance is frozen"
- **FR-144**: Documentation MUST recommend `.model_copy(update={...})` for creating modified instances
- **FR-145**: Library MUST document immutability guarantee in data-model.md and quickstart.md

---

### CHK017: mypy --strict Compliance Enforcement

**Gap**: Are mypy --strict compliance requirements enforced in test suite (how verified, CI integration)?

**Decision**:
**mypy --strict enforced in CI, with no exceptions**:

**Enforcement Strategy**:
- `mypy --strict src/ tests/` MUST pass in CI pipeline
- NO `# type: ignore` comments allowed (exceptions require code review + documented justification)
- ALL public APIs MUST have complete type annotations
- NO `Any` types in public API signatures

**pyproject.toml Configuration**:
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

**CI Integration**:
```yaml
# .github/workflows/ci.yml
- name: Type Check
  run: |
    poetry run mypy --strict src/ tests/
    # Fail build if mypy finds errors
```

**Type Annotation Coverage**:
- ✅ ALL function signatures (parameters + return types)
- ✅ ALL class attributes
- ✅ ALL module-level variables
- ✅ Protocol definitions with complete type hints

**Exceptions** (rare, require justification):
- Third-party library stubs missing (create stub file instead of ignoring)
- Platform-specific code (use `sys.platform` type narrowing)

**Rationale**: mypy --strict catches type errors at development time, before runtime. Full type coverage enables IDE autocomplete and refactoring safety.

**New Requirements**:
- **FR-146**: Library source code MUST pass `mypy --strict` with zero errors
- **FR-147**: CI pipeline MUST run `mypy --strict src/ tests/` and fail build on errors
- **FR-148**: Public API functions MUST NOT use `Any` type in signatures (use TypeVar, Protocol, or Union instead)
- **FR-149**: Type ignore comments (`# type: ignore`) MUST be avoided; if unavoidable, MUST include justification comment and issue link
- **FR-150**: Library MUST provide py.typed marker file for downstream mypy compatibility

---

### CHK018: Generic Type Parameters in Protocol Definitions

**Gap**: Are requirements specified for generic type parameters in protocol definitions (TypeVar usage, constraints)?

**Decision**:
**Use TypeVar for provider-agnostic result types**:

**TypeVar Usage**:
```python
from typing import Protocol, TypeVar, Iterator

# TypeVar for conversation types (OpenAI, Anthropic, Google may have different models)
ConversationT = TypeVar('ConversationT', bound='BaseConversation')

class ConversationProvider(Protocol[ConversationT]):
    """Generic protocol supporting different conversation types."""

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None
    ) -> Iterator[ConversationT]:
        """Stream conversations of provider-specific type."""
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str
    ) -> Optional[ConversationT]:
        """Get conversation by ID, returning provider-specific type."""
        ...
```

**Concrete Adapter Implementation**:
```python
class OpenAIAdapter:
    """Implements ConversationProvider[Conversation]."""

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None
    ) -> Iterator[Conversation]:  # Concrete type
        ...

    def get_conversation_by_id(
        self,
        file_path: Path,
        conversation_id: str
    ) -> Optional[Conversation]:  # Concrete type
        ...
```

**SearchResult Generic**:
```python
from typing import Generic

class SearchResult(Generic[ConversationT]):
    """Search result wrapping any conversation type."""
    conversation: ConversationT
    relevance_score: float
    matched_keywords: list[str]
    excerpt: str
```

**Type Safety Benefits**:
```python
# mypy understands the concrete type
adapter: OpenAIAdapter = OpenAIAdapter()
convs: Iterator[Conversation] = adapter.stream_conversations(file_path)

for conv in convs:
    # IDE autocomplete knows conv.title, conv.messages, etc.
    print(conv.title)  # Type: str (not Any)
```

**Rationale**: Generics enable type-safe multi-provider support. Future Claude/Gemini adapters can return provider-specific types while adhering to protocol.

**New Requirements**:
- **FR-151**: ConversationProvider protocol MUST use TypeVar for generic conversation type support
- **FR-152**: SearchResult MUST be generic (`Generic[ConversationT]`) to support different conversation types
- **FR-153**: Concrete adapter implementations MUST specify concrete types (e.g., `Iterator[Conversation]`, not `Iterator[ConversationT]`)
- **FR-154**: Library MUST use `bound=` TypeVar constraint to ensure conversation types inherit from BaseConversation (if needed for shared interface)

---

### CHK151: Generic Type Parameters (SearchResult[T], Iterator[Conversation])

**Gap**: Are requirements specified for generic type parameters (SearchResult[T], Iterator[Conversation])?

**Decision**:
**Covered by CHK018** - SearchResult is generic, Iterator specifies concrete type.

**Additional Clarification**:
```python
# SearchResult is generic (supports any conversation type)
class SearchResult(Generic[ConversationT]):
    conversation: ConversationT
    relevance_score: float
    matched_keywords: list[str]
    excerpt: str

# OpenAI adapter returns Iterator with concrete type
class OpenAIAdapter:
    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None
    ) -> Iterator[SearchResult[Conversation]]:  # Concrete: SearchResult[Conversation]
        ...
```

**Type Inference**:
```python
# mypy infers types correctly
results: Iterator[SearchResult[Conversation]] = adapter.search(file_path, query)

for result in results:
    # result.conversation is type Conversation (not ConversationT or Any)
    title: str = result.conversation.title  # ✅ Type-safe
```

**Rationale**: No additional requirements needed beyond FR-151 to FR-154.

---

### CHK152: Type Narrowing (Optional Unwrapping, Union Handling)

**Gap**: Are requirements defined for type narrowing (Optional unwrapping, Union type handling)?

**Decision**:
**Use explicit None checks for Optional unwrapping**:

**Optional Unwrapping Pattern**:
```python
from typing import Optional

def get_conversation_by_id(
    self,
    file_path: Path,
    conversation_id: str
) -> Optional[Conversation]:
    """Returns None if not found."""
    ...

# Consumer code - explicit None check (type narrowing)
conv: Optional[Conversation] = adapter.get_conversation_by_id(file_path, "conv-123")

if conv is not None:
    # mypy narrows type from Optional[Conversation] to Conversation
    print(conv.title)  # ✅ Type-safe (no Optional warning)
else:
    print("Conversation not found")

# ❌ BAD: No None check (mypy error)
# print(conv.title)  # Error: Item "None" of "Optional[Conversation]" has no attribute "title"
```

**Union Type Handling** (for message roles):
```python
from typing import Literal

MessageRole = Literal["user", "assistant", "system"]

class Message(BaseModel):
    role: MessageRole  # Union of literal strings
    content: str

# Type narrowing with match statement (Python 3.10+)
def process_message(msg: Message) -> None:
    match msg.role:
        case "user":
            # mypy knows role is "user" here
            handle_user_message(msg)
        case "assistant":
            handle_assistant_message(msg)
        case "system":
            handle_system_message(msg)
        case _:
            # Exhaustiveness check (mypy warns if missing case)
            assert_never(msg.role)
```

**Rationale**: Explicit None checks and pattern matching enable type narrowing. mypy catches missing checks.

**New Requirements**:
- **FR-155**: Functions returning Optional[T] MUST document when None is returned (in docstring)
- **FR-156**: Library code MUST use explicit None checks (`if x is not None:`) before accessing Optional values
- **FR-157**: Union types MUST use Literal types for enums (e.g., `Literal["user", "assistant", "system"]`, not plain `str`)
- **FR-158**: Library MUST use match statements (Python 3.10+) for exhaustive Union type handling where applicable

---

### CHK153: Runtime Type Validation (Pydantic vs mypy)

**Gap**: Are requirements specified for runtime type validation (Pydantic vs mypy, when each applies)?

**Decision**:
**Pydantic for runtime, mypy for static checks - complementary systems**:

**Division of Responsibilities**:

**Pydantic (Runtime Validation)**:
- Validates external data (JSON from export files)
- Enforces constraints (string length, date formats, required fields)
- Coerces types (string → datetime, int → float)
- Runs at parse time (every file load)

**mypy (Static Type Checking)**:
- Validates internal code (function calls, variable assignments)
- Catches type errors before runtime (at development time)
- No runtime overhead (pure static analysis)
- Runs in CI/IDE (not in production)

**Example - Both Systems Working Together**:
```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal

MessageRole = Literal["user", "assistant", "system"]

class Message(BaseModel):
    """Message model with both runtime (Pydantic) and static (mypy) validation."""

    # mypy: Enforces role is MessageRole type (compile-time)
    # Pydantic: Validates role is one of the literal values (runtime)
    role: MessageRole

    # mypy: Enforces content is str (compile-time)
    # Pydantic: Validates content is non-empty string (runtime)
    content: str = Field(min_length=1)

    # mypy: Enforces timestamp is datetime (compile-time)
    # Pydantic: Coerces ISO 8601 string → datetime object (runtime)
    timestamp: datetime

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        # Runtime: Additional validation beyond type
        if v not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {v}")
        return v

# Usage
msg_data = {"role": "user", "content": "Hello", "timestamp": "2024-01-15T10:30:00Z"}

# Pydantic: Runtime validation (parses JSON, validates constraints)
msg = Message.model_validate(msg_data)

# mypy: Static validation (checks this function call is type-safe)
def process_user_message(msg: Message) -> None:
    # mypy knows msg.role is MessageRole (not just str)
    # mypy knows msg.content is str
    # mypy knows msg.timestamp is datetime (not str)
    print(f"{msg.role}: {msg.content} at {msg.timestamp}")
```

**When to Use Each**:

| Scenario | Use Pydantic | Use mypy |
|----------|--------------|----------|
| Validating export file JSON | ✅ Required | ❌ N/A (external data) |
| Checking function parameter types | ❌ Not needed | ✅ Required |
| Enforcing string length limits | ✅ Required | ❌ Can't express |
| Catching typos in variable names | ❌ Not detected | ✅ Detected |
| Runtime type coercion (str → datetime) | ✅ Required | ❌ N/A (static) |
| IDE autocomplete | ❌ Indirect (via types) | ✅ Direct |

**Rationale**: Pydantic and mypy solve different problems. Both are necessary for robust type safety.

**New Requirements**:
- **FR-159**: Library MUST use Pydantic for runtime validation of all external data (JSON from export files)
- **FR-160**: Library MUST use mypy for static type checking of all internal code (function calls, variable assignments)
- **FR-161**: Data models MUST define both Pydantic constraints (Field, validators) AND type annotations (for mypy)
- **FR-162**: Documentation MUST explain the difference between Pydantic (runtime) and mypy (static) validation
- **FR-163**: Library MUST NOT use runtime type checks (`isinstance()`, `type()`) where mypy can statically verify types

---

## Summary: Type Safety & Contracts

**Total Gaps Resolved**: 7
**New Functional Requirements**: FR-138 through FR-163 (26 requirements)
**Artifacts to Update**:
- ✅ spec.md (add FR-138 to FR-163)
- ✅ data-model.md (add Pydantic validation handling, immutability contract, generics)
- ✅ contracts/conversation_provider_protocol.py (add generic TypeVar definitions)
- quickstart.md (add type safety examples showing mypy, Pydantic, immutability)

---

# TIER 2: HIGH-PRIORITY ARCHITECTURAL GAPS (Chunk 3/3)

## 3. Multi-Provider Protocol (10 items)

### CHK020: Future Adapter Implementation Requirements

**Gap**: Are requirements defined for future adapter implementations (what must be preserved, what can vary)?

**Decision**:
**Protocol contract is sacred, implementation details can vary**:

**What MUST Be Preserved** (immutable across all adapters):
1. **Method signatures**: All protocol methods (stream_conversations, search, get_conversation_by_id)
2. **Exception contract**: Must raise same exception types (FileNotFoundError, ParseError, ValidationError, SchemaVersionError)
3. **Memory efficiency**: Must use streaming (no full-file loading)
4. **Thread safety**: Adapter instances must be thread-safe
5. **Return types**: Must return Iterator (not List), types must match protocol

**What CAN Vary** (adapter-specific implementation):
1. **Parsing logic**: ijson for JSON, xml.etree for XML, csv.reader for CSV
2. **Internal data structures**: Adapters can use different internal models before converting to Conversation
3. **Performance characteristics**: Some adapters may be faster than others
4. **File format quirks**: OpenAI has nested JSON, Claude might have JSONL, Gemini might use protobuf
5. **Metadata extraction**: Provider-specific fields can be mapped differently

**Example - Future Anthropic Adapter**:
```python
class AnthropicAdapter:
    """Implements ConversationProvider[Conversation] for Claude export format.

    Format differences from OpenAI:
    - JSONL instead of single JSON array
    - Different field names (claude_message vs message)
    - Different role names (human/assistant vs user/assistant)

    But protocol contract is identical!
    """

    def __init__(self) -> None:
        """Stateless constructor (per FR-113)."""
        pass

    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[Conversation]:
        """Stream Claude conversations (JSONL format).

        Implementation differs from OpenAI:
        - Uses line-by-line parsing (JSONL)
        - Maps 'human' → 'user', 'assistant' → 'assistant'
        - Different JSON structure

        But contract is identical: returns Iterator[Conversation]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                try:
                    # Parse JSONL (one JSON object per line)
                    claude_conv_data = json.loads(line)

                    # Convert Claude format → Conversation model
                    conv = self._convert_claude_to_conversation(claude_conv_data)

                    if progress_callback and idx % 100 == 0:
                        progress_callback(idx + 1)

                    yield conv
                except (json.JSONDecodeError, ValidationError) as e:
                    if on_skip:
                        on_skip(claude_conv_data.get('id', str(idx)), str(e))

    def _convert_claude_to_conversation(self, claude_data: dict) -> Conversation:
        """Convert Claude-specific format to shared Conversation model."""
        # Provider-specific implementation detail (can vary)
        ...
```

**Rationale**: Protocol defines **what** adapters do (contract). Implementation defines **how** (internal details). This enables multiple providers while maintaining predictable API.

**New Requirements**:
- **FR-164**: Future adapter implementations MUST implement ConversationProvider protocol exactly (no method signature changes)
- **FR-165**: Adapters MUST raise the same exception types as defined in protocol (FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError)
- **FR-166**: Adapters MUST use streaming (Iterator, not List) regardless of source format
- **FR-167**: Adapter internal implementation details (parsing libraries, data structures) MAY vary as long as protocol contract is satisfied
- **FR-168**: Documentation MUST include "Adding a New Provider Adapter" guide showing implementation requirements

---

### CHK021: Shared Pydantic Model Requirements

**Gap**: Are shared Pydantic model requirements documented (which fields mandatory across all providers, which optional)?

**Decision**:
**Core fields required, provider-specific fields in metadata dict**:

**Required Fields** (ALL providers must map to these):
```python
class Conversation(BaseModel):
    """Shared conversation model (provider-agnostic).

    All adapters MUST populate these fields from their export format.
    """

    model_config = ConfigDict(frozen=True)

    # REQUIRED: All providers must have these
    id: str  # UUID or provider-specific ID
    title: str  # Conversation title (or generated from first message)
    created_at: datetime  # ISO 8601 timestamp
    updated_at: datetime  # ISO 8601 timestamp
    messages: list[Message]  # At least one message

    # OPTIONAL: Provider-specific metadata
    metadata: dict[str, Any] = {}  # Provider-specific fields


class Message(BaseModel):
    """Shared message model (provider-agnostic)."""

    model_config = ConfigDict(frozen=True)

    # REQUIRED: All providers must have these
    id: str  # UUID or provider-specific ID
    role: Literal["user", "assistant", "system"]  # Normalized roles
    content: str  # Message text content
    timestamp: datetime  # ISO 8601 timestamp

    # OPTIONAL: Hierarchical structure (for branching)
    parent_id: Optional[str] = None
    child_ids: list[str] = []

    # OPTIONAL: Provider-specific metadata
    metadata: dict[str, Any] = {}
```

**Mapping Provider-Specific Roles**:
```python
# OpenAI → Shared model
"user" → "user"
"assistant" → "assistant"
"system" → "system"

# Anthropic Claude → Shared model
"human" → "user"
"assistant" → "assistant"
(no system role in Claude v1)

# Google Gemini → Shared model
"user" → "user"
"model" → "assistant"
(system instructions in separate field)
```

**Provider-Specific Metadata Example**:
```python
# OpenAI-specific fields stored in metadata
conv = Conversation(
    id="conv-123",
    title="Debugging Python",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    messages=[...],
    metadata={
        "openai_model": "gpt-4",  # OpenAI-specific
        "openai_conversation_template_id": "template-456",  # OpenAI-specific
        "openai_plugin_ids": ["plugin-789"],  # OpenAI-specific
    }
)

# Anthropic-specific fields stored in metadata
conv = Conversation(
    id="conv-abc",
    title="Writing Code",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    messages=[...],
    metadata={
        "claude_model": "claude-3-sonnet",  # Anthropic-specific
        "claude_workspace_id": "ws-xyz",  # Anthropic-specific
    }
)
```

**Rationale**: Required fields ensure library consumers (cognivault) get predictable data. Metadata dict allows provider-specific extensions without breaking shared models.

**New Requirements**:
- **FR-169**: Conversation model MUST define required fields: id, title, created_at, updated_at, messages
- **FR-170**: Message model MUST define required fields: id, role, content, timestamp
- **FR-171**: Adapters MUST normalize provider-specific role names to Literal["user", "assistant", "system"]
- **FR-172**: Provider-specific fields MUST be stored in metadata dict (not top-level fields)
- **FR-173**: If provider lacks a required field (e.g., title), adapter MUST generate sensible default (e.g., first 50 chars of first message)

---

### CHK022: Provider-Specific Quirks Isolation

**Gap**: Are requirements specified for provider-specific quirks isolation (where divergent format handling belongs)?

**Decision**:
**Isolate quirks in adapter implementation, never leak to protocol**:

**Quirk Isolation Strategy**:

**Layer 1: Adapter-Internal Parsing** (quirks stay here)
```python
class OpenAIAdapter:
    """OpenAI-specific quirks isolated in private methods."""

    def stream_conversations(self, file_path: Path, ...) -> Iterator[Conversation]:
        """Public protocol method (quirk-free)."""
        with open(file_path, 'rb') as f:
            for conv_data in ijson.items(f, 'item'):
                # Delegate to quirk-handling method
                yield self._parse_openai_conversation(conv_data)

    def _parse_openai_conversation(self, raw_data: dict) -> Conversation:
        """Private method isolating OpenAI quirks."""

        # QUIRK 1: OpenAI sometimes has null 'title' field
        title = raw_data.get('title') or self._generate_title_from_messages(raw_data['mapping'])

        # QUIRK 2: OpenAI uses 'mapping' dict instead of 'messages' list
        messages = self._flatten_openai_message_tree(raw_data['mapping'])

        # QUIRK 3: OpenAI timestamps are float seconds (not ISO 8601)
        created_at = datetime.fromtimestamp(raw_data['create_time'], tz=timezone.utc)

        # Return normalized Conversation model
        return Conversation(
            id=raw_data['id'],
            title=title,
            created_at=created_at,
            updated_at=datetime.fromtimestamp(raw_data['update_time'], tz=timezone.utc),
            messages=messages,
            metadata={"openai_model": raw_data.get('model', 'unknown')}
        )

    def _flatten_openai_message_tree(self, mapping: dict) -> list[Message]:
        """Handle OpenAI's weird nested message structure."""
        # Complex tree-flattening logic (quirk-specific)
        ...

    def _generate_title_from_messages(self, mapping: dict) -> str:
        """Generate title when OpenAI doesn't provide one."""
        first_msg = self._get_first_message(mapping)
        return first_msg['content'][:50] if first_msg else "Untitled Conversation"
```

**Layer 2: Shared Protocol Interface** (no quirks)
```python
# Consumer (cognivault) sees only clean protocol
adapter = OpenAIAdapter()  # Could swap with AnthropicAdapter seamlessly
for conv in adapter.stream_conversations(file_path):
    # conv is normalized Conversation model
    # No OpenAI-specific quirks visible
    print(conv.title, conv.created_at)
```

**Quirk Examples Across Providers**:
- **OpenAI**: Nested message tree (`mapping` dict), null titles, float timestamps
- **Anthropic**: JSONL format, "human" role name, workspace metadata
- **Google**: Protobuf serialization, "model" role name, system instructions separate

**Rationale**: Isolating quirks in adapter internals keeps protocol clean. Consumers don't need to know about provider differences.

**New Requirements**:
- **FR-174**: Adapter implementations MUST isolate provider-specific quirks in private methods (prefixed with _)
- **FR-175**: Public protocol methods MUST return normalized Conversation/Message models (no provider-specific types)
- **FR-176**: Adapters MUST NOT expose provider-specific parsing details in public API
- **FR-177**: Quirk-handling code MUST be documented with comments explaining provider-specific behavior
- **FR-178**: If provider format changes, adapter MUST absorb changes internally without affecting protocol

---

### CHK023: Adapter Registration/Discovery

**Gap**: Are adapter registration/discovery requirements defined (how cognivault selects correct adapter for a given export file)?

**Decision**:
**Explicit adapter selection (no auto-detection for v1.0)**:

**Approach for v1.0** (simplicity):
```python
# Library consumer explicitly selects adapter
from echomine import OpenAIAdapter

# User knows file is from ChatGPT
adapter = OpenAIAdapter()
for conv in adapter.stream_conversations(Path("chatgpt_export.json")):
    cognivault.ingest(conv)
```

**No Magic** (deferred to post-v1.0):
- NO format auto-detection (error-prone)
- NO adapter registry (over-engineering for single provider)
- NO plugin system (YAGNI for v1.0)

**Future** (when 2+ providers supported):
```python
# v2.0+ might add helper for auto-detection
from echomine import detect_adapter

adapter = detect_adapter(Path("export.json"))  # Inspects file format
# Returns: OpenAIAdapter, AnthropicAdapter, or GoogleAdapter
```

**How cognivault Integrates** (v1.0):
```python
# cognivault configuration
EXPORT_ADAPTERS = {
    "openai": OpenAIAdapter,
    # Future: "anthropic": AnthropicAdapter,
    # Future: "google": GoogleAdapter,
}

# cognivault user specifies provider
def ingest_export(file_path: Path, provider: str):
    adapter_class = EXPORT_ADAPTERS[provider]
    adapter = adapter_class()

    for conv in adapter.stream_conversations(file_path):
        cognivault.knowledge_graph.add(conv)
```

**Rationale**: Explicit beats implicit. Auto-detection adds complexity/fragility. Defer until 2+ providers exist.

**New Requirements**:
- **FR-179**: Library v1.0 MUST NOT implement adapter auto-detection or registry
- **FR-180**: Library consumers MUST explicitly instantiate adapter class (e.g., `OpenAIAdapter()`)
- **FR-181**: Documentation MUST explain how to select correct adapter for export source
- **FR-182**: Future adapter auto-detection (v2.0+) MAY be added as opt-in helper function
- **FR-183**: Adapters MUST NOT share global state (each instantiation is independent)

---

### CHK024: Export Format Provider Detection

**Gap**: Are requirements specified for detecting export format provider (OpenAI vs future Claude/Gemini)?

**Decision**:
**Detection deferred to v2.0+ (explicit selection for v1.0)**:

**v1.0 Approach** (no detection):
- User knows where export came from (ChatGPT, Claude, etc.)
- User explicitly selects adapter
- No heuristics, no magic

**Future Detection Strategy** (v2.0+ if needed):
```python
def detect_adapter(file_path: Path) -> type[ConversationProvider]:
    """Detect provider format via heuristics (v2.0+).

    Detection strategy:
    1. Check file extension (.json, .jsonl, .csv, .xml)
    2. Peek at first 1KB of file (detect structure)
    3. Look for provider-specific markers
    4. Return appropriate adapter class

    Raises:
        UnknownFormatError: If provider cannot be determined
    """

    # Peek at file structure
    with open(file_path, 'rb') as f:
        header = f.read(1024).decode('utf-8', errors='ignore')

    # Heuristic 1: OpenAI exports have "mapping" and "create_time" fields
    if '"mapping"' in header and '"create_time"' in header:
        return OpenAIAdapter

    # Heuristic 2: Anthropic exports are JSONL with "claude" in metadata
    if header.count('\n') > 0 and '"claude' in header.lower():
        return AnthropicAdapter

    # Heuristic 3: Google exports have protobuf magic bytes
    if header.startswith(b'\x08\x01\x12'):
        return GoogleAdapter

    raise UnknownFormatError(
        f"Cannot determine export format for {file_path.name}. "
        f"Please specify adapter explicitly."
    )
```

**Rationale**: Detection is error-prone (false positives/negatives). Wait until 2+ providers exist to design heuristics properly.

**New Requirements**:
- **FR-184**: Library v1.0 MUST NOT implement automatic format detection
- **FR-185**: If format detection is added in future versions, it MUST be opt-in (not mandatory)
- **FR-186**: Format detection (if added) MUST raise UnknownFormatError if provider cannot be determined
- **FR-187**: Documentation MUST recommend explicit adapter selection over auto-detection for reliability

---

### CHK143: Protocol Compliance Test Requirements

**Gap**: Are protocol compliance test requirements defined (shared test suite all adapters must pass)?

**Decision**:
**Contract test suite using pytest parametrization**:

**Shared Contract Tests** (all adapters must pass):
```python
# tests/contract/test_provider_protocol.py
import pytest
from pathlib import Path
from echomine import OpenAIAdapter  # Future: AnthropicAdapter, GoogleAdapter
from echomine.models import Conversation, SearchQuery

# Parametrize over all adapter implementations
ADAPTERS = [
    OpenAIAdapter,
    # Future adapters added here automatically inherit tests
]

@pytest.fixture(params=ADAPTERS)
def adapter(request):
    """Fixture providing each adapter implementation."""
    return request.param()

@pytest.fixture
def sample_export_file(adapter, tmp_path):
    """Fixture creating provider-specific test export."""
    # Each adapter provides its own fixture factory
    return adapter.create_test_export(tmp_path)


# CONTRACT TEST 1: Memory Efficiency
def test_stream_conversations_memory_bounded(adapter, sample_export_file):
    """Process large file with constant memory (per FR-027, FR-116)."""
    import tracemalloc

    tracemalloc.start()
    peak_before = tracemalloc.get_traced_memory()[1]

    # Process 1000 conversations
    count = 0
    for conv in adapter.stream_conversations(sample_export_file):
        count += 1
        if count >= 1000:
            break

    peak_after = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    # Memory delta should be < 100MB (constant, not O(n))
    memory_delta_mb = (peak_after - peak_before) / (1024 * 1024)
    assert memory_delta_mb < 100, f"Memory usage grew by {memory_delta_mb}MB (should be constant)"


# CONTRACT TEST 2: Fail-Fast Error Handling
def test_stream_conversations_fail_fast(adapter, tmp_path):
    """Raise FileNotFoundError immediately (per FR-049, FR-042)."""
    missing_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        # Should fail immediately, not on first iteration
        iterator = adapter.stream_conversations(missing_file)
        next(iterator)  # Exception raised here or before


# CONTRACT TEST 3: Search Results Sorted
def test_search_results_sorted_by_relevance(adapter, sample_export_file):
    """Results returned in descending relevance order (per FR-008)."""
    query = SearchQuery(keywords=["test"], limit=10)
    results = list(adapter.search(sample_export_file, query))

    # Verify descending order
    scores = [r.relevance_score for r in results]
    assert scores == sorted(scores, reverse=True), "Results not sorted by relevance"


# CONTRACT TEST 4: Thread Safety
def test_adapter_instance_thread_safe(adapter, sample_export_file):
    """Single adapter instance can be used across threads (per FR-098)."""
    from threading import Thread

    results = []

    def worker():
        # Each thread creates its own iterator
        convs = list(adapter.stream_conversations(sample_export_file))
        results.append(len(convs))

    threads = [Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get same count (no corruption)
    assert len(set(results)) == 1, "Thread safety violation: inconsistent results"


# CONTRACT TEST 5: Type Safety
def test_stream_conversations_returns_correct_types(adapter, sample_export_file):
    """Returns Iterator[Conversation], not List or other type (per FR-153)."""
    from typing import get_args
    import inspect

    # Check return type annotation
    sig = inspect.signature(adapter.stream_conversations)
    return_type = sig.return_annotation

    # Should be Iterator[Conversation]
    assert "Iterator" in str(return_type), f"Expected Iterator, got {return_type}"
```

**CI Integration**:
```yaml
# .github/workflows/contract-tests.yml
- name: Run Contract Tests
  run: |
    pytest tests/contract/ -v
    # All adapters must pass ALL contract tests
```

**Rationale**: Contract tests ensure adapters are interchangeable. Adding new adapter requires zero test code (automatically inherits suite).

**New Requirements**:
- **FR-188**: Library MUST provide shared contract test suite in tests/contract/ directory
- **FR-189**: ALL adapter implementations MUST pass ALL contract tests (100% compliance)
- **FR-190**: Contract tests MUST verify: memory efficiency, fail-fast errors, result ordering, thread safety, type correctness
- **FR-191**: CI pipeline MUST run contract tests against ALL adapters and fail build on any failures
- **FR-192**: New adapter implementations MUST be added to contract test parametrization (via pytest.mark.parametrize)

---

### CHK144: Protocol Versioning Requirements

**Gap**: Are requirements specified for protocol versioning (how to evolve protocol without breaking existing adapters)?

**Decision**:
**Semantic versioning + 2-release deprecation for protocol changes**:

**Protocol Versioning Strategy**:

**MAJOR Version** (breaking protocol changes):
- Adding required parameters to methods
- Removing methods from protocol
- Changing method return types (non-backward compatible)
- Example: `stream_conversations(file_path)` → `stream_conversations(file_path, required_schema_version)`

**MINOR Version** (backward-compatible protocol additions):
- Adding new optional parameters (with defaults)
- Adding new methods to protocol
- Example: Adding `def export_to_format(...)` method

**Protocol Evolution Example**:
```python
# v1.0.0: Initial protocol
class ConversationProvider(Protocol[ConversationT]):
    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Iterator[ConversationT]:
        ...

# v1.1.0: MINOR - Add optional parameter (backward compatible)
class ConversationProvider(Protocol[ConversationT]):
    def stream_conversations(
        self,
        file_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,  # NEW: optional, default None
    ) -> Iterator[ConversationT]:
        ...
    # Old adapters still work (they ignore on_skip)

# v2.0.0: MAJOR - Add required parameter (breaking change)
class ConversationProvider(Protocol[ConversationT]):
    def stream_conversations(
        self,
        file_path: Path,
        schema_version: str,  # NEW: required parameter
        progress_callback: Optional[ProgressCallback] = None,
        on_skip: Optional[OnSkipCallback] = None,
    ) -> Iterator[ConversationT]:
        ...
    # Old adapters BREAK (missing required parameter)
```

**Deprecation Process for Protocol Changes**:
1. **v1.5.0**: Announce deprecation in docs, add new method alongside old
2. **v1.6.0**: Emit DeprecationWarning when old method used
3. **v2.0.0**: Remove old method (MAJOR bump)

**Adapter Compatibility Matrix**:
```markdown
| Adapter Version | Protocol v1.0 | Protocol v1.1 | Protocol v2.0 |
|-----------------|---------------|---------------|---------------|
| OpenAIAdapter v1.0 | ✅ Compatible | ✅ Compatible | ❌ Incompatible |
| OpenAIAdapter v1.1 | ✅ Compatible | ✅ Compatible | ❌ Incompatible |
| OpenAIAdapter v2.0 | ❌ Incompatible | ❌ Incompatible | ✅ Compatible |
```

**Rationale**: Protocol stability is critical for library consumers. Breaking changes require MAJOR version bump and clear migration path.

**New Requirements**:
- **FR-193**: Protocol changes MUST follow semantic versioning strictly (MAJOR for breaking, MINOR for additions)
- **FR-194**: Adding required parameters to protocol methods MUST trigger MAJOR version bump
- **FR-195**: New protocol methods MUST be optional (provide default implementation or make optional via Union[...])
- **FR-196**: Protocol breaking changes MUST be documented in CHANGELOG with migration guide
- **FR-197**: Library MUST maintain protocol version constant (e.g., `echomine.PROTOCOL_VERSION = "1.0"`)

---

### CHK145: Adapter Capability Detection

**Gap**: Are requirements defined for adapter capability detection (does adapter support date filtering, title search)?

**Decision**:
**Capabilities deferred to v2.0+ (all v1.0 adapters have same capabilities)**:

**v1.0 Assumption** (homogeneous capabilities):
- All adapters support same features (stream, search, get_by_id)
- No partial implementations
- No capability detection needed

**Future Capability System** (v2.0+ if needed):
```python
from enum import Flag, auto

class AdapterCapability(Flag):
    """Flags indicating adapter capabilities."""
    STREAM = auto()          # Can stream conversations
    SEARCH = auto()          # Can search by keywords
    TITLE_SEARCH = auto()    # Can filter by title
    DATE_FILTER = auto()     # Can filter by date range
    GET_BY_ID = auto()       # Can retrieve by conversation ID
    EXPORT_MARKDOWN = auto() # Can export to markdown
    EXPORT_PDF = auto()      # Can export to PDF


class OpenAIAdapter:
    """OpenAI adapter with full capabilities."""

    CAPABILITIES = (
        AdapterCapability.STREAM |
        AdapterCapability.SEARCH |
        AdapterCapability.TITLE_SEARCH |
        AdapterCapability.DATE_FILTER |
        AdapterCapability.GET_BY_ID
    )

    @classmethod
    def supports(cls, capability: AdapterCapability) -> bool:
        """Check if adapter supports capability."""
        return bool(cls.CAPABILITIES & capability)


# Consumer checks capabilities before using
if OpenAIAdapter.supports(AdapterCapability.DATE_FILTER):
    query = SearchQuery(from_date=date(2024, 1, 1))
else:
    # Fallback: filter in-memory after fetching
    query = SearchQuery()
```

**Rationale**: v1.0 has single provider (OpenAI). Capability detection is premature. Add when 2+ providers with different features exist.

**New Requirements**:
- **FR-198**: Library v1.0 MUST NOT implement adapter capability detection
- **FR-199**: ALL v1.0 adapters MUST implement full protocol (no partial implementations)
- **FR-200**: Future capability system (v2.0+) MAY use Flag enum for feature detection
- **FR-201**: If capability detection added, adapters MUST declare capabilities via class constant (not runtime detection)

---

### CHK158: Adding New Search Filters (SearchQuery Extensibility)

**Gap**: Are requirements specified for adding new search filters (extensibility points in SearchQuery model)?

**Decision**:
**Frozen model + semantic versioning for new filters**:

**Current SearchQuery** (v1.0):
```python
class SearchQuery(BaseModel):
    """Search query model (v1.0)."""

    model_config = ConfigDict(frozen=True)

    keywords: Optional[list[str]] = None
    title_filter: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    limit: int = 10
```

**Adding New Filters** (backward-compatible):
```python
# v1.1.0: Add new optional filters
class SearchQuery(BaseModel):
    """Search query model (v1.1.0)."""

    model_config = ConfigDict(frozen=True)

    # Existing filters (unchanged)
    keywords: Optional[list[str]] = None
    title_filter: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    limit: int = 10

    # NEW: Optional filters (default None = backward compatible)
    author_filter: Optional[str] = None  # Filter by author name
    min_message_count: Optional[int] = None  # Minimum messages in conversation
    tag_filter: Optional[list[str]] = None  # Filter by user-defined tags
```

**Backward Compatibility**:
```python
# v1.0 code still works with v1.1.0 library
query = SearchQuery(keywords=["python"], limit=5)
# New fields default to None (ignored)

# v1.1.0 code uses new filters
query = SearchQuery(
    keywords=["python"],
    author_filter="user@example.com",  # NEW
    min_message_count=5,  # NEW
    limit=10
)
```

**Adapter Handling**:
```python
class OpenAIAdapter:
    def search(self, file_path: Path, query: SearchQuery, ...) -> Iterator[SearchResult]:
        """Search with backward-compatible filter handling."""
        for conv in self.stream_conversations(file_path):
            # Apply filters (skip unknown filters gracefully)
            if query.keywords and not self._matches_keywords(conv, query.keywords):
                continue
            if query.title_filter and query.title_filter not in conv.title:
                continue
            if query.from_date and conv.created_at.date() < query.from_date:
                continue
            if query.to_date and conv.created_at.date() > query.to_date:
                continue

            # NEW filters (v1.1.0+) - old adapters ignore these
            if query.author_filter and not self._matches_author(conv, query.author_filter):
                continue
            if query.min_message_count and len(conv.messages) < query.min_message_count:
                continue

            yield SearchResult(conversation=conv, ...)
```

**Rationale**: Optional fields with defaults maintain backward compatibility. Adapters can adopt new filters incrementally.

**New Requirements**:
- **FR-202**: New search filters MUST be added as optional fields with default values (backward compatible)
- **FR-203**: Adding new filters MUST trigger MINOR version bump (not MAJOR)
- **FR-204**: Adapters MAY ignore unknown filters (fail gracefully, don't raise exceptions)
- **FR-205**: Documentation MUST specify which filters are supported by each adapter version

---

### CHK159: Custom Export Formats (Plugin Architecture)

**Gap**: Are requirements defined for custom export formats (plugin architecture, format registry)?

**Decision**:
**No plugin system for v1.0 (YAGNI), explicit imports sufficient**:

**v1.0 Approach** (no plugins):
```python
# Library provides adapters as importable classes
from echomine import OpenAIAdapter
# Future: from echomine import AnthropicAdapter, GoogleAdapter

# No plugin discovery, no registry, no entry points
```

**Why No Plugins for v1.0**:
1. Only 1 provider (OpenAI) → no need for extensibility
2. Plugin systems add complexity (discovery, loading, versioning)
3. Library consumers can use explicit imports (simpler)
4. Can add plugins in v2.0+ if demand exists

**Future Plugin System** (v2.0+ if needed):
```python
# Entry points in pyproject.toml
[project.entry-points."echomine.adapters"]
openai = "echomine.adapters:OpenAIAdapter"
anthropic = "echomine_anthropic:AnthropicAdapter"  # Third-party plugin
google = "echomine_google:GoogleAdapter"  # Third-party plugin

# Plugin discovery (v2.0+)
from echomine import discover_adapters

adapters = discover_adapters()  # Returns: {"openai": OpenAIAdapter, ...}
adapter = adapters["anthropic"]()
```

**Third-Party Adapter Package** (v2.0+):
```python
# echomine-anthropic package (separate repository)
from echomine.protocols import ConversationProvider
from echomine.models import Conversation

class AnthropicAdapter:
    """Third-party adapter implementing ConversationProvider."""

    def stream_conversations(...) -> Iterator[Conversation]:
        # Implementation
        ...
```

**Rationale**: YAGNI for v1.0. Plugins add complexity without benefit when only 1 provider exists. Defer until ecosystem grows.

**New Requirements**:
- **FR-206**: Library v1.0 MUST NOT implement plugin discovery or adapter registry
- **FR-207**: Adapters MUST be importable as explicit classes (e.g., `from echomine import OpenAIAdapter`)
- **FR-208**: Future plugin system (v2.0+) MAY use entry points for third-party adapters
- **FR-209**: Plugin architecture (if added) MUST NOT break explicit imports (backward compatible)

---

### CHK160: Custom Ranking Algorithms (Pluggable Scorers)

**Gap**: Are requirements specified for custom ranking algorithms (alternative to TF-IDF, pluggable scorers)?

**Decision**:
**TF-IDF fixed for v1.0, custom scorers deferred to v2.0+**:

**v1.0 Approach** (fixed algorithm):
```python
class OpenAIAdapter:
    def search(self, file_path: Path, query: SearchQuery, ...) -> Iterator[SearchResult]:
        """Search using TF-IDF ranking (fixed algorithm)."""
        # Collect matching conversations
        matches = []
        for conv in self.stream_conversations(file_path):
            if self._matches_filters(conv, query):
                score = self._calculate_tfidf_score(conv, query.keywords)
                matches.append((conv, score))

        # Sort by relevance (descending)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Yield top results
        for conv, score in matches[:query.limit]:
            yield SearchResult(
                conversation=conv,
                relevance_score=score,
                matched_keywords=query.keywords or [],
                excerpt=self._extract_excerpt(conv, query.keywords)
            )
```

**Future Custom Scorers** (v2.0+ if needed):
```python
from typing import Protocol

class RankingAlgorithm(Protocol):
    """Protocol for custom ranking algorithms."""

    def calculate_score(
        self,
        conversation: Conversation,
        keywords: list[str]
    ) -> float:
        """Calculate relevance score (0.0 to 1.0)."""
        ...


class TFIDFScorer:
    """Default TF-IDF ranking."""
    def calculate_score(self, conversation: Conversation, keywords: list[str]) -> float:
        # TF-IDF implementation
        ...


class BM25Scorer:
    """Alternative BM25 ranking (better for short documents)."""
    def calculate_score(self, conversation: Conversation, keywords: list[str]) -> float:
        # BM25 implementation
        ...


# v2.0+: Pluggable scorer
class OpenAIAdapter:
    def search(
        self,
        file_path: Path,
        query: SearchQuery,
        ranking_algorithm: RankingAlgorithm = TFIDFScorer(),  # NEW: pluggable
        ...
    ) -> Iterator[SearchResult]:
        """Search with custom ranking algorithm."""
        matches = []
        for conv in self.stream_conversations(file_path):
            if self._matches_filters(conv, query):
                # Use custom scorer
                score = ranking_algorithm.calculate_score(conv, query.keywords)
                matches.append((conv, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        for conv, score in matches[:query.limit]:
            yield SearchResult(...)
```

**Rationale**: TF-IDF is well-understood baseline. Custom scorers add complexity without proven demand. Defer until users request it.

**New Requirements**:
- **FR-210**: Library v1.0 MUST use TF-IDF for keyword ranking (no alternatives)
- **FR-211**: TF-IDF implementation MUST be tested for correctness (contract test)
- **FR-212**: Future custom ranking algorithms (v2.0+) MAY be added as optional parameters
- **FR-213**: Custom scorers (if added) MUST implement RankingAlgorithm protocol with calculate_score method
- **FR-214**: Default ranking algorithm MUST remain TF-IDF (backward compatible)

---

## Summary: Multi-Provider Protocol

**Total Gaps Resolved**: 10
**New Functional Requirements**: FR-164 through FR-214 (51 requirements)
**Artifacts to Update**:
- spec.md (add FR-164 to FR-214)
- data-model.md (add adapter implementation guidelines, shared model requirements, metadata dict)
- contracts/conversation_provider_protocol.py (add contract test documentation)
- quickstart.md (add multi-adapter examples, capability detection notes)

---

