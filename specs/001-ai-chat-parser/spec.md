# Feature Specification: Echomine AI Chat Parser

**Feature Branch**: `001-ai-chat-parser`
**Created**: 2025-11-21
**Status**: Draft
**Input**: User description: "Echomine is a library and CLI tool for parsing, searching, and extracting insights from AI conversation exports. Primary use case: Extract specific conversation threads from large ChatGPT exports (1GB+ JSON files) for documentation, knowledge synthesis, or feeding into other tools."

## Clarifications

### Session 2025-11-21

- Q: Where should exported files be saved? → A: Export to current working directory by default, allow --output <path> flag to specify custom location
- Q: What logging format and levels should be used? → A: JSON structured logs with standard levels (INFO, WARNING, ERROR) and contextual fields (file_name, conversation_id, operation)
- Q: How should file system errors be handled (disk full, permissions, missing files)? → A: Fail fast with clear error message and non-zero exit code (no retries)
- Q: What is the maximum data volume for performance testing? → A: 10,000 conversations with 50,000 total messages (heavy user scale)
- Q: How long should search result excerpts be? → A: 200 characters (balanced, roughly 1-2 sentences of context)

## User Scenarios & Testing *(mandatory)*

### Usage Patterns

Echomine is architected to serve two complementary usage patterns:

**Pattern 1: Direct CLI Usage** - Individual developers and researchers use echomine interactively to search, filter, and export their chat history. This pattern emphasizes ease of use and immediate value.

**Pattern 2: Library Integration (Primary Driver)** - External services like **cognivault** use echomine as a programmatic data ingestion layer. This pattern is the *primary architectural driver* - the library-first design (Constitution Principle I) ensures echomine can be embedded into automated pipelines.

**Example: cognivault Integration**
```python
from echomine import OpenAIAdapter

# cognivault uses echomine to ingest user chat exports
adapter = OpenAIAdapter("user_export.json")
for conversation in adapter.search(keywords=["project-x"]):
    cognivault.knowledge_graph.ingest(conversation)
```

The CLI is built *on top of* the library - ensuring any capability available via command-line is also available programmatically.

### CLI Search Patterns

**Title-based search (metadata-only, <5s for 10K conversations per FR-444)**
```bash
# Find conversations by exact or partial title
echomine search conversations.json --title "Algo Insights"
```

**Keyword search (comprehensive, full-text)**
```bash
# Search across all message content
echomine search conversations.json --keywords "algorithm,leetcode"
```

**Combined filtering (precision)**
```bash
# Title filter + keyword search within those conversations
echomine search conversations.json --title "Project" --keywords "refactor" --limit 5
```

### CLI Advanced Usage Examples

**stdout/stderr Separation** (per FR-428, FR-291, FR-292, FR-293)
```bash
# Results to stdout, progress to stderr
echomine search conversations.json --keywords "algorithm"
# Progress: 1000 conversations scanned...

# Pipe results while suppressing progress
echomine search conversations.json --keywords "algorithm" 2>/dev/null | head -n 5

# Redirect errors separately
echomine search missing.json --keywords "test" 2>errors.log
```

**JSON Output with Complete Schema** (per FR-431, FR-301, FR-302, FR-303)
```bash
# JSON output format
echomine search conversations.json --keywords "python" --json
```

**Example JSON output**:
```json
{
  "results": [
    {
      "conversation_id": "conv-abc-123",
      "title": "Python AsyncIO Tutorial",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:45:00Z",
      "score": 0.87,
      "matched_message_ids": ["msg-1", "msg-3", "msg-7"],
      "message_count": 12
    },
    {
      "conversation_id": "conv-xyz-789",
      "title": "Python Best Practices",
      "created_at": "2024-02-20T14:00:00Z",
      "updated_at": "2024-02-20T15:30:00Z",
      "score": 0.65,
      "matched_message_ids": ["msg-2", "msg-5"],
      "message_count": 8
    }
  ],
  "metadata": {
    "query": {
      "keywords": ["python"],
      "limit": null
    },
    "total_results": 2,
    "skipped_conversations": 3,
    "elapsed_seconds": 1.24
  }
}
```

**Pipeline Composition** (per FR-430, FR-307, FR-308, FR-309)
```bash
# Example 1: Extract top 3 conversation IDs
echomine search export.json --keywords "algorithm" --json | \
  jq -r '.results[:3] | .[].conversation_id'

# Example 2: Filter by score threshold
echomine search export.json --keywords "python" --json | \
  jq '.results[] | select(.score > 0.8) | {title, score}'

# Example 3: Count high-relevance results
echomine search export.json --keywords "leetcode" --json | \
  jq '.results[] | select(.score > 0.7)' | \
  wc -l

# Example 4: Export matching conversation IDs to file
echomine search export.json --keywords "refactor" --json | \
  jq -r '.results[].conversation_id' > conversation_ids.txt

# Example 5: Batch export using xargs
echomine search export.json --keywords "algorithm" --json | \
  jq -r '.results[].conversation_id' | \
  xargs -I {} echomine export export.json {} --output ./exports/
```

**Exit Codes** (per FR-429, FR-296, FR-297, FR-298, FR-299, FR-300)
```bash
# Exit code 0: Success (even with 0 results)
echomine search conversations.json --keywords "nonexistent"
echo $?  # Output: 0

# Exit code 1: Operational errors
echomine search missing.json --keywords "test"
echo $?  # Output: 1 (file not found)

# Exit code 2: Usage errors
echomine search --keywords "test"  # Missing file path
echo $?  # Output: 2

# Exit code 130: Interrupted (Ctrl+C)
echomine search large_file.json --keywords "test"
# User presses Ctrl+C
echo $?  # Output: 130
```

**Help and Version Output** (per FR-432, FR-294)

**`echomine --help` output**:
```
echomine - AI conversation export parser

USAGE:
    echomine search <FILE> [OPTIONS]
    echomine export <FILE> <CONVERSATION_ID> [OPTIONS]

COMMANDS:
    search      Search conversations by keywords or title
    export      Export conversation to markdown

SEARCH OPTIONS:
    --keywords <KEYWORDS>    Comma-separated keywords to search
    --title <TITLE>          Filter by conversation title (substring match)
    --from <DATE>            Filter conversations after date (ISO 8601)
    --to <DATE>              Filter conversations before date (ISO 8601)
    --limit <N>              Return top N results (default: unlimited)
    --json                   Output results as JSON
    --quiet                  Suppress progress indicators

EXIT CODES:
    0    Success (including 0 results)
    1    Operational error (file not found, parse error, etc.)
    2    Usage error (invalid arguments)
    130  Interrupted (Ctrl+C)

EXAMPLES:
    echomine search conversations.json --keywords "algorithm"
    echomine search export.json --title "Project" --json
    echomine export conversations.json conv-abc-123 --output ./output

For more information, visit https://github.com/yourorg/echomine
```

**`echomine --version` output**:
```
echomine 1.0.0
Python library for parsing AI conversation exports
```

### User Story 0 - List All Conversations (Priority: P0)

As a user with an AI chat export file, I need to see a list of all conversations in the file, so I can browse what's available before searching or exporting.

**Why this priority**: This is a foundational discovery operation - users need to know what's in their export file before they can effectively search or export. Like `ls` for files, this enables basic file exploration and verification. Without this, users must search blindly or guess conversation IDs.

**Independent Test**: Load export file with known conversations, run list command, verify all conversations displayed with title, date, and message count in chronological order.

**Acceptance Scenarios**:

1. **Given** an export file with 100 conversations, **When** I run `echomine list conversations.json`, **Then** I see all 100 conversations with title, created date, and message count
2. **Given** a large export file, **When** I run `echomine list conversations.json --limit 20`, **Then** I see only the 20 most recent conversations (sorted by created_at descending)
3. **Given** I want machine-readable output, **When** I run `echomine list conversations.json --json`, **Then** I get JSON array with conversation metadata (id, title, created_at, updated_at, message_count)
4. **Given** conversations stored in random order in export, **When** I list them, **Then** they appear sorted by created_at descending (newest first)
5. **Given** a very large export file (1GB+), **When** I run list, **Then** I see results within 5 seconds using streaming (not full load)
6. **Given** I want to count conversations, **When** I run `echomine list conversations.json --json | jq 'length'`, **Then** I get the total conversation count
7. **Given** an empty export file, **When** I run list, **Then** I see "No conversations found" message with exit code 0

---

### User Story 1 - Search Conversations by Keyword (Priority: P1)

As a developer working with AI chat logs, I need to quickly find conversations about specific topics (e.g., "leetcode", "algorithm design") from my large ChatGPT export file, so I can reference past discussions without manually scrolling through hundreds of conversations.

**Why this priority**: This is the core value proposition - making conversation history searchable. Without this, users are stuck with unsearchable JSON archives. This story delivers immediate value and validates the entire concept.

**Independent Test**: Can be fully tested by providing a sample export file with known conversations, running a keyword search, and verifying that relevant conversations are returned with titles, dates, and excerpts.

**Acceptance Scenarios**:

1. **Given** a ChatGPT export file with 100+ conversations, **When** I search for keyword "algorithm", **Then** I see a list of matching conversations with title, date, and relevant excerpt
2. **Given** multiple search keywords separated by commas, **When** I search for "leetcode,algorithm", **Then** I see conversations matching any of the keywords, ranked by relevance
3. **Given** a search that returns many results, **When** I specify a limit (e.g., --limit 5), **Then** I see only the top 5 most relevant matches
4. **Given** a search keyword that doesn't match any conversation, **When** I run the search, **Then** I see a message indicating no results found with suggested next steps
5. **Given** a very large export file (1GB+), **When** I run a search, **Then** I see a progress indicator and results appear within 30 seconds
6. **Given** I know my conversation's exact title from the ChatGPT app, **When** I search with `--title "Algo Insights Project"`, **Then** I see only conversations matching that exact title (faster than full-text keyword search)
7. **Given** I partially remember a title, **When** I search with `--title "Algo"`, **Then** I see all conversations with titles containing "Algo" as a substring
8. **Given** I want precise filtering, **When** I search with `--title "Project" --keywords "refactor"`, **Then** I see only conversations with "Project" in title AND "refactor" in message content

---

### User Story 2 - Programmatic Library Access (Priority: P2)

As a developer building AI-powered tools, I need to use Echomine as a Python library, so I can programmatically parse and process conversation data in my own applications (like cognivault).

**Why this priority**: **This is the primary architectural driver for Echomine** - cognivault and other external services depend on the library API for chat export ingestion and processing. The library-first architecture (Constitution Principle I) is foundational: the library MUST be designed first, with the CLI built on top as a consumer of the library. This ensures any capability available via command-line is also available programmatically, enabling automated pipeline integration and external service workflows.

**Independent Test**: Can be fully tested by importing the library, creating an adapter instance, calling search/export methods, and verifying the returned data structures match the documented API.

**Acceptance Scenarios**:

1. **Given** I import `from echomine import OpenAIAdapter`, **When** I create an adapter with a file path, **Then** I get a typed adapter instance ready for parsing
2. **Given** an OpenAIAdapter instance, **When** I call `adapter.search(keywords=["test"])`, **Then** I get an iterator of Conversation objects with proper type hints
3. **Given** a Conversation object, **When** I call `conv.export_markdown(path)`, **Then** a markdown file is created at the specified path
4. **Given** I use the library in an IDE, **When** I type `adapter.`, **Then** I see autocomplete suggestions for available methods
5. **Given** a Conversation object, **When** I access its attributes (title, created_at, messages), **Then** I get properly typed data (str, datetime, list) without casting

---

### User Story 3 - Export Conversation to Markdown (Priority: P3)

As a documentation writer, I need to export specific AI conversations to markdown format, so I can include them in my project documentation or knowledge base without copying and pasting messages manually.

**Why this priority**: Once users find conversations via search (P1) and the library API is established (P2), exporting to markdown enables the documentation use case. This builds on the library foundation - the export functionality can be consumed both programmatically and via CLI.

**Independent Test**: Can be fully tested by selecting a conversation (by title or ID), exporting it to markdown, and verifying the output file contains all messages in readable format with proper threading.

**Acceptance Scenarios**:

1. **Given** a conversation identified by its title, **When** I export it with --title "Algo Insights Project", **Then** I get a markdown file with all messages in chronological order
2. **Given** a conversation with branching message threads (multiple responses to one message), **When** I export it, **Then** the markdown file preserves the tree structure with indentation or clear parent-child markers
3. **Given** an exported markdown file, **When** I open it, **Then** I see conversation metadata (title, date, participants) at the top, followed by formatted messages
4. **Given** a conversation with code blocks or formatting, **When** I export it, **Then** the markdown preserves code fencing and formatting
5. **Given** a conversation ID instead of title, **When** I export using --id <uuid>, **Then** I get the correct conversation exported

---

### User Story 4 - Filter Conversations by Date Range (Priority: P4)

As a researcher analyzing my AI usage patterns, I need to filter conversations by date range, so I can focus on discussions from a specific time period (e.g., last quarter's project work).

**Why this priority**: Complements search functionality (P1) by adding temporal filtering. This is an additive feature that enhances the core search capability but is not required for the primary use cases (library integration and keyword search).

**Independent Test**: Can be fully tested by specifying a date range (start and end dates), running a filtered search, and verifying only conversations within that range are returned.

**Acceptance Scenarios**:

1. **Given** a date range using --from "2024-01-01" --to "2024-03-31", **When** I search conversations, **Then** I see only conversations created within Q1 2024
2. **Given** a date range filter combined with keywords, **When** I search for "algorithm" within a date range, **Then** I see conversations matching both the keyword and date criteria
3. **Given** an invalid date format, **When** I specify a date filter, **Then** I see a clear error message with the expected format (ISO 8601: YYYY-MM-DD)
4. **Given** only a start date (--from), **When** I search, **Then** I see all conversations from that date forward
5. **Given** only an end date (--to), **When** I search, **Then** I see all conversations up to and including that date

---

### Edge Cases

- What happens when the export file is corrupted or has invalid JSON?
  - System MUST skip malformed entries, log warnings, and continue processing valid entries
- What happens when a conversation has no title?
  - System MUST use conversation ID or generate a title from the first message excerpt
- What happens when a message has no content (deleted/redacted)?
  - System MUST represent these as "[deleted]" or "[no content]" in exports
- What happens when searching a multi-gigabyte file?
  - System MUST show progress indicators and complete within 30 seconds for 1GB files
- What happens when exporting a conversation with very long messages (100K+ characters)?
  - System MUST handle without truncation unless explicitly requested via a flag
- What happens when two conversations have identical titles?
  - System MUST disambiguate using conversation ID or creation date when exporting
- What happens when the export format changes (OpenAI updates their schema)?
  - System MUST detect version and handle multiple schema versions gracefully
- What happens when the input file doesn't exist or can't be read?
  - System MUST fail immediately with clear error message to stderr and exit code 1
- What happens when output directory lacks write permissions?
  - System MUST fail immediately with permission error message and exit code 1
- What happens when disk is full during export?
  - System MUST fail immediately with disk space error message and exit code 1

## Requirements *(mandatory)*

### Functional Requirements

**Parsing & Data Integrity**

- **FR-001**: System MUST parse OpenAI's conversations.json export format and extract conversation metadata (title, ID, timestamps, participant roles)
- **FR-002**: System MUST preserve message tree structures including parent-child relationships and conversation branching
- **FR-003**: System MUST handle export files up to 2GB in size without loading the entire file into memory
- **FR-004**: System MUST skip malformed JSON entries and continue processing, emitting structured JSON log entries at WARNING level for each skipped entry with contextual fields (file_name, entry_position, error_reason)
- **FR-005**: System MUST detect and handle multiple versions of the OpenAI export schema

**Search & Filtering**

- **FR-006**: System MUST support keyword search across all conversation messages, not just titles
- **FR-007**: System MUST support multiple comma-separated keywords with OR logic (match any keyword)
- **FR-008**: System MUST rank search results by relevance based on keyword frequency and position
- **FR-009**: System MUST support filtering conversations by date range with ISO 8601 format (YYYY-MM-DD)
- **FR-010**: System MUST support limiting search results to a specified number (e.g., top 5)
- **FR-011**: System MUST support filtering by conversation title using partial matches
- **FR-034**: System MUST include excerpts of up to 200 characters in search results showing keyword context (approximately 1-2 sentences)

**Export & Output**

- **FR-012**: System MUST export conversations to markdown format with proper message threading
- **FR-013**: System MUST export conversations to JSON format preserving the full data structure
- **FR-014**: System MUST include conversation metadata in exported files (title, date, participant info)
- **FR-015**: System MUST preserve code blocks, formatting, and special characters in exported content
- **FR-016**: System MUST generate human-readable filenames for exports using conversation titles (slugified)

**CLI Interface**

- **FR-017**: System MUST provide a `search` command that accepts file path and supports these filters: --keywords (full-text search across messages), --title (conversation title partial match, metadata-only), --from/--to (date range), and --limit (max results)
- **FR-018**: System MUST provide an `export` command that accepts file path, conversation identifier, and output format; exports MUST be written to the current working directory by default with optional `--output <path>` flag to specify custom location
- **FR-019**: System MUST output search results to stdout in human-readable format by default
- **FR-020**: System MUST support JSON output format for search results via --json flag
- **FR-021**: System MUST display progress indicators for operations taking longer than 2 seconds
- **FR-022**: System MUST write error messages to stderr and use non-zero exit codes on failure
- **FR-033**: System MUST fail immediately (no retries) on file system errors (file not found, permission denied, disk full) with descriptive error messages and exit code 1

**Library Interface**

- **FR-023**: System MUST provide a public Python API with type hints for all functions and classes
- **FR-024**: System MUST expose an OpenAIAdapter class for parsing OpenAI exports
- **FR-025**: System MUST return conversation data as strongly-typed Pydantic models (Message, Conversation)
- **FR-026**: System MUST use iterator patterns for memory-efficient processing of large datasets
- **FR-027**: System MUST provide a ConversationProvider protocol for future adapter implementations

**Exception Handling & Error Contract**

- **FR-035**: Library MUST define `EchomineError` base exception class that all public exceptions inherit from
- **FR-036**: Library MUST raise only public exception types (`ParseError`, `ValidationError`, `SchemaVersionError`, `FileAccessError`) for operational failures
- **FR-037**: Library documentation MUST specify which exceptions are part of public API contract and which indicate bugs
- **FR-038**: Standard Python exceptions (FileNotFoundError, PermissionError) MUST be re-raised as-is (not wrapped) for filesystem errors
- **FR-039**: All exception messages MUST follow the format: "{operation} failed: {reason}. {actionable_guidance}"
- **FR-040**: Exception messages MUST NOT expose raw stack traces, internal variable names, or implementation details
- **FR-041**: Exception messages MUST include context: conversation ID, file path, line number, or field name when applicable
- **FR-042**: Library MUST fail immediately on all errors (no automatic retries, no retry hints in exceptions)
- **FR-043**: Library MUST NOT implement retry logic for any operation (file access, parsing, validation)
- **FR-044**: Library consumers implementing retry logic MUST treat all exceptions as potentially permanent (no retry hints provided)
- **FR-045**: Iterator methods MUST NOT raise StopIteration explicitly (use return to end iteration, per PEP 479)
- **FR-046**: Iterator methods MUST raise custom exceptions (ParseError, ValidationError) for parsing/validation failures during iteration
- **FR-047**: Iterator methods MUST use context managers to guarantee file handle cleanup even when exceptions occur
- **FR-048**: Iterator exceptions MUST include the item index or conversation ID where failure occurred
- **FR-049**: Library MUST raise standard FileNotFoundError (not custom wrapper) when export file does not exist
- **FR-050**: FileNotFoundError message MUST include: full file path and suggestion to verify path correctness
- **FR-051**: Library MUST raise standard PermissionError (not custom wrapper) when file cannot be read due to permissions
- **FR-052**: PermissionError message MUST include: file path and guidance to check read permissions
- **FR-053**: Library MUST define ValidationError exception (subclass of ValueError and EchomineError) for data validation failures
- **FR-054**: Library MUST raise ValidationError when Pydantic model validation fails with message including field name and expected format
- **FR-055**: ValidationError MUST be raised for: invalid date formats, missing required fields, malformed IDs, unsupported data types
- **FR-056**: Iterator methods MUST use `return` statements to end iteration (not explicit StopIteration)
- **FR-057**: If StopIteration is caught from underlying iterators (ijson), it MUST be allowed to propagate (not re-raised explicitly)
- **FR-058**: Library MUST use exception chaining (`raise NewException(...) from original`) when wrapping lower-level exceptions
- **FR-059**: Exception chains MUST preserve original exception in `__cause__` attribute for debugging
- **FR-060**: Top-level exception message MUST be user-friendly; chained exception MAY contain technical details
- **FR-061**: Library documentation MUST specify exception handling contract for library consumers (which exceptions to catch)
- **FR-062**: quickstart.md MUST include example showing cognivault catching EchomineError, FileNotFoundError, PermissionError
- **FR-063**: Library consumers MUST NOT catch KeyboardInterrupt, SystemExit, or MemoryError (let them propagate)

**Progress Indicators**

- **FR-064**: Progress indicators MUST use spinner mode (not percentage) when total item count is unknown upfront
- **FR-065**: Progress indicators in spinner mode MUST display running count of items processed ("Parsed 123 conversations...")
- **FR-066**: Progress indicators MAY switch to percentage mode if total count becomes known (not required for v1.0)
- **FR-067**: Progress indicators MUST use rich library for terminal rendering (spinners, text formatting)
- **FR-068**: Progress indicators MUST update at most every 100ms (time-based) to avoid excessive terminal redraws
- **FR-069**: Progress indicators MUST update at least every 100 items (item-based) to show progress on fast operations
- **FR-070**: Progress update frequency MAY be adaptive based on parsing speed (slower operations update more frequently)
- **FR-071**: Progress indicators MUST use spinner animation from rich library (rotating characters, not static text)
- **FR-072**: Progress indicators MUST display item count with thousand separators ("1,234" not "1234")
- **FR-073**: Progress indicators SHOULD display parsing rate (items/second) when available
- **FR-074**: Progress indicators MUST NOT display ETA (estimated time remaining) when total count is unknown
- **FR-075**: Progress indicators MUST clear on completion and display final summary with total count and elapsed time
- **FR-076**: Library methods accepting large datasets (stream_conversations, search) MUST accept optional progress_callback parameter
- **FR-077**: progress_callback MUST be called periodically with current item count (not percentage)
- **FR-078**: Library MUST NOT depend on rich or other terminal libraries (progress rendering is CLI responsibility)
- **FR-079**: CLI MUST implement progress rendering using rich library and invoke library methods with progress callbacks

**Schema Version Management**

- **FR-080**: Library MUST attempt to detect export schema version using heuristic checks on export structure
- **FR-081**: Library MUST check for explicit version field ('version' or 'schema_version') before falling back to heuristics
- **FR-082**: Schema detection MUST occur before parsing conversations (fail fast if unsupported)
- **FR-083**: Schema detection MUST use field presence checks (e.g., 'mapping' field indicates v1.0 format)
- **FR-084**: Library v1.0 MUST support only OpenAI export schema v1.0 (current ChatGPT format as of 2024)
- **FR-085**: Library MUST raise SchemaVersionError for any detected schema version other than v1.0
- **FR-086**: Future library versions MAY support multiple schema versions by normalizing to common Conversation model
- **FR-087**: Schema version support MUST be documented in README and library docstrings
- **FR-088**: SchemaVersionError message MUST include: detected version, supported versions, and remediation steps
- **FR-089**: Library MUST log schema version detection at INFO level with fields: version, file_name, supported (bool)
- **FR-090**: Schema version errors MUST suggest re-exporting from ChatGPT as first remediation step
- **FR-091**: When future schema changes are detected, library MUST fail with SchemaVersionError (not generic parse errors)
- **FR-092**: Future library versions adding new schema support MUST maintain backward compatibility with v1.0 (MINOR version bump)
- **FR-093**: Dropping support for old schemas MUST trigger MAJOR version bump per semantic versioning

**Concurrency & Thread Safety**

- **FR-094**: Library MUST support concurrent reads of same export file by multiple processes (each with independent file handle)
- **FR-095**: Library MUST NOT acquire file locks (advisory or exclusive) when opening export files for reading
- **FR-096**: Library ASSUMES export files are immutable during read (behavior undefined if file modified concurrently)
- **FR-097**: Library documentation MUST state that concurrent writes to export files are NOT supported
- **FR-098**: OpenAIAdapter instances MUST be thread-safe (safe to share across threads)
- **FR-099**: Iterators returned by stream_conversations/search MUST NOT be shared across threads (undefined behavior)
- **FR-100**: Each thread MUST create its own iterator by calling stream_conversations/search separately
- **FR-101**: Library documentation MUST specify thread safety guarantees for adapters and iterators
- **FR-102**: Library behavior is UNDEFINED if export file is modified (appended, truncated, deleted) during parsing
- **FR-103**: Library MUST NOT implement file modification detection (no inotify, stat polling, checksums)
- **FR-104**: Documentation MUST advise users to treat export files as immutable during parsing

**Graceful Degradation**

- **FR-105**: Library MUST emit structured WARNING log when skipping malformed entries with fields: conversation_id, reason, file_name
- **FR-106**: Library methods (stream_conversations, search) MAY accept optional on_skip callback parameter
- **FR-107**: on_skip callback MUST receive conversation_id (or index) and reason string when entry is skipped
- **FR-108**: Library MUST NOT write skip messages directly to console (only to structured logger)
- **FR-109**: Library MUST emit INFO log on completion with fields: total_conversations, skipped_conversations, duration_seconds
- **FR-110**: CLI MUST display summary line showing total conversations and skip count after parsing completes
- **FR-111**: CLI MUST exit with code 0 even when conversations are skipped (partial success is success)
- **FR-112**: CLI summary MUST reference logs for details when conversations are skipped ("see logs for details")

**Adapter Design & Lifecycle**

- **FR-113**: OpenAIAdapter constructor MUST NOT accept configuration parameters (stateless design)
- **FR-114**: Adapter instances MUST be reusable across different export files (file paths passed to methods)
- **FR-115**: Adapter __init__ MUST be lightweight (no I/O, no validation, instantiation should be instant)
- **FR-116**: Iterators MUST be single-use (exhausted after complete iteration)
- **FR-117**: Calling stream_conversations/search multiple times MUST return independent iterators (not resume previous)
- **FR-118**: File handles MUST be closed when iteration stops early (break, exception, or completion)
- **FR-119**: Library MUST use context managers internally to guarantee file handle cleanup
- **FR-120**: Adapter classes MUST NOT implement context manager protocol (__enter__, __exit__)
- **FR-121**: Library methods MUST use context managers internally for all file I/O operations
- **FR-122**: File handles MUST be opened and closed within method scope (not stored in adapter state)

**Versioning & Deprecation**

- **FR-123**: Library MUST follow semantic versioning (MAJOR.MINOR.PATCH) strictly
- **FR-124**: Breaking API changes MUST trigger MAJOR version bump
- **FR-125**: New optional parameters or features MUST trigger MINOR version bump
- **FR-126**: Bug fixes with no API changes MUST trigger PATCH version bump
- **FR-127**: Deprecated features MUST emit DeprecationWarning for at least 2 releases before removal
- **FR-128**: Deprecation warnings MUST include: removal version, replacement method, and migration guide URL
- **FR-129**: Library version MUST be available via `echomine.__version__` attribute

**Resource Management**

- **FR-130**: Generator functions MUST use try/finally to guarantee cleanup code execution
- **FR-131**: File handles MUST be managed via context managers (not manual open/close)
- **FR-132**: Cleanup MUST occur even when: iteration breaks early, exceptions raised, or generator garbage collected
- **FR-133**: Library MUST NOT rely on __del__ methods for cleanup (use context managers instead)
- **FR-134**: Library MUST NOT implement explicit backpressure mechanisms (queues, buffers, rate limiters)
- **FR-135**: Generators MUST yield one item at a time (no internal buffering beyond ijson buffers)
- **FR-136**: Memory usage MUST remain constant regardless of consumer processing speed
- **FR-137**: Documentation MUST explain that consumers control parsing pace (generators pause when consumer processing)

**Type Safety & Validation**

- **FR-138**: Library MUST catch `pydantic.ValidationError` and re-raise as `echomine.ValidationError`
- **FR-139**: ValidationError messages MUST include: conversation/message index, field name, and invalid value summary
- **FR-140**: ValidationError messages MUST preserve Pydantic's field-level error details via exception chaining (`raise ... from e`)
- **FR-141**: ValidationError MUST include remediation guidance (e.g., "Check export schema version" or "Re-export from ChatGPT")
- **FR-159**: Library MUST use Pydantic for runtime validation of all external data (JSON from export files)
- **FR-160**: Library MUST use mypy for static type checking of all internal code (function calls, variable assignments)
- **FR-161**: Data models MUST define both Pydantic constraints (Field, validators) AND type annotations (for mypy)
- **FR-162**: Documentation MUST explain the difference between Pydantic (runtime) and mypy (static) validation
- **FR-163**: Library MUST NOT use runtime type checks (`isinstance()`, `type()`) where mypy can statically verify types

**Immutability & Data Integrity**

- **FR-142**: ALL Pydantic models (`Conversation`, `Message`, `SearchResult`, `SearchQuery`) MUST be frozen (frozen=True)
- **FR-143**: Attempting to modify frozen models MUST raise `pydantic.ValidationError` with message "Instance is frozen"
- **FR-144**: Documentation MUST recommend `.model_copy(update={...})` for creating modified instances
- **FR-145**: Library MUST document immutability guarantee in data-model.md and quickstart.md

**Static Type Checking**

- **FR-146**: Library source code MUST pass `mypy --strict` with zero errors
- **FR-147**: CI pipeline MUST run `mypy --strict src/ tests/` and fail build on errors
- **FR-148**: Public API functions MUST NOT use `Any` type in signatures (use TypeVar, Protocol, or Union instead)
- **FR-149**: Type ignore comments (`# type: ignore`) MUST be avoided; if unavoidable, MUST include justification comment and issue link
- **FR-150**: Library MUST provide py.typed marker file for downstream mypy compatibility

**Generic Types & Protocols**

- **FR-151**: ConversationProvider protocol MUST use TypeVar for generic conversation type support
- **FR-152**: SearchResult MUST be generic (`Generic[ConversationT]`) to support different conversation types
- **FR-153**: Concrete adapter implementations MUST specify concrete types (e.g., `Iterator[Conversation]`, not `Iterator[ConversationT]`)
- **FR-154**: Library MUST use `bound=` TypeVar constraint to ensure conversation types inherit from BaseConversation (if needed for shared interface)

**Type Narrowing & Optional Handling**

- **FR-155**: Functions returning Optional[T] MUST document when None is returned (in docstring)
- **FR-156**: Library code MUST use explicit None checks (`if x is not None:`) before accessing Optional values
- **FR-157**: Union types MUST use Literal types for enums (e.g., `Literal["user", "assistant", "system"]`, not plain `str`)
- **FR-158**: Library MUST use match statements (Python 3.10+) for exhaustive Union type handling where applicable

**Observability**

- **FR-028**: System MUST emit structured JSON logs with standard log levels (INFO, WARNING, ERROR) for all operations
- **FR-029**: Log entries MUST include contextual fields: operation name, file_name, conversation_id (when applicable), timestamp, and level
- **FR-030**: INFO level MUST log operation start/completion (parsing started, search completed, export finished)
- **FR-031**: WARNING level MUST log recoverable issues (malformed entries skipped, missing optional fields)
- **FR-032**: ERROR level MUST log unrecoverable failures (file not found, permission denied, invalid format)

**Multi-Provider Adapter Pattern**

- **FR-164**: Future adapter implementations MUST implement ConversationProvider protocol exactly (no method signature changes)
- **FR-165**: Adapters MUST raise the same exception types as defined in protocol (FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError)
- **FR-166**: Adapters MUST use streaming (Iterator, not List) regardless of source format
- **FR-167**: Adapter internal implementation details (parsing libraries, data structures) MAY vary as long as protocol contract is satisfied
- **FR-168**: Documentation MUST include "Adding a New Provider Adapter" guide showing implementation requirements
- **FR-174**: Adapter implementations MUST isolate provider-specific quirks in private methods (prefixed with _)
- **FR-175**: Public protocol methods MUST return normalized Conversation/Message models (no provider-specific types)
- **FR-176**: Adapters MUST NOT expose provider-specific parsing details in public API
- **FR-177**: Quirk-handling code MUST be documented with comments explaining provider-specific behavior
- **FR-178**: If provider format changes, adapter MUST absorb changes internally without affecting protocol
- **FR-179**: Library v1.0 MUST NOT implement adapter auto-detection or registry
- **FR-180**: Library consumers MUST explicitly instantiate adapter class (e.g., `OpenAIAdapter()`)
- **FR-181**: Documentation MUST explain how to select correct adapter for export source
- **FR-182**: Future adapter auto-detection (v2.0+) MAY be added as opt-in helper function
- **FR-183**: Adapters MUST NOT share global state (each instantiation is independent)
- **FR-184**: Library v1.0 MUST NOT implement automatic format detection
- **FR-185**: If format detection is added in future versions, it MUST be opt-in (not mandatory)
- **FR-186**: Format detection (if added) MUST raise UnknownFormatError if provider cannot be determined
- **FR-187**: Documentation MUST recommend explicit adapter selection over auto-detection for reliability

**Shared Data Models**

- **FR-169**: Conversation model MUST define required fields: id, title, created_at, updated_at, messages
- **FR-170**: Message model MUST define required fields: id, role, content, timestamp
- **FR-171**: Adapters MUST normalize provider-specific role names to Literal["user", "assistant", "system"]
- **FR-172**: Provider-specific fields MUST be stored in metadata dict (not top-level fields)
- **FR-173**: If provider lacks a required field (e.g., title), adapter MUST generate sensible default (e.g., first 50 chars of first message)

**Protocol Compliance & Testing**

- **FR-188**: Library MUST provide shared contract test suite in tests/contract/ directory
- **FR-189**: ALL adapter implementations MUST pass ALL contract tests (100% compliance)
- **FR-190**: Contract tests MUST verify: memory efficiency, fail-fast errors, result ordering, thread safety, type correctness
- **FR-191**: CI pipeline MUST run contract tests against ALL adapters and fail build on any failures
- **FR-192**: New adapter implementations MUST be added to contract test parametrization (via pytest.mark.parametrize)

**Protocol Versioning & Evolution**

- **FR-193**: Protocol changes MUST follow semantic versioning strictly (MAJOR for breaking, MINOR for additions)
- **FR-194**: Adding required parameters to protocol methods MUST trigger MAJOR version bump
- **FR-195**: New protocol methods MUST be optional (provide default implementation or make optional via Union[...])
- **FR-196**: Protocol breaking changes MUST be documented in CHANGELOG with migration guide
- **FR-197**: Library MUST maintain protocol version constant (e.g., `echomine.PROTOCOL_VERSION = "1.0"`)
- **FR-198**: Library v1.0 MUST NOT implement adapter capability detection
- **FR-199**: ALL v1.0 adapters MUST implement full protocol (no partial implementations)
- **FR-200**: Future capability system (v2.0+) MAY use Flag enum for feature detection
- **FR-201**: If capability detection added, adapters MUST declare capabilities via class constant (not runtime detection)

**Search Query Extensibility**

- **FR-202**: New search filters MUST be added as optional fields with default values (backward compatible)
- **FR-203**: Adding new filters MUST trigger MINOR version bump (not MAJOR)
- **FR-204**: Adapters MAY ignore unknown filters (fail gracefully, don't raise exceptions)
- **FR-205**: Documentation MUST specify which filters are supported by each adapter version

**Plugin Architecture & Extensibility**

- **FR-206**: Library v1.0 MUST NOT implement plugin discovery or adapter registry
- **FR-207**: Adapters MUST be importable as explicit classes (e.g., `from echomine import OpenAIAdapter`)
- **FR-208**: Future plugin system (v2.0+) MAY use entry points for third-party adapters
- **FR-209**: Plugin architecture (if added) MUST NOT break explicit imports (backward compatible)

**Ranking Algorithms**

- **FR-210**: Library v1.0 MUST use TF-IDF for keyword ranking (no alternatives)
- **FR-211**: TF-IDF implementation MUST be tested for correctness (contract test)
- **FR-212**: Future custom ranking algorithms (v2.0+) MAY be added as optional parameters
- **FR-213**: Custom scorers (if added) MUST implement RankingAlgorithm protocol with calculate_score method
- **FR-214**: Default ranking algorithm MUST remain TF-IDF (backward compatible)

**Protocol Method Signatures (Type Safety & API Contract)**

- **FR-215**: ConversationProvider protocol MUST define `stream_conversations` method with signature: `(file_path: Path, *, progress_callback: Optional[ProgressCallback] = None, on_skip: Optional[OnSkipCallback] = None) -> Iterator[Conversation]`
- **FR-216**: ConversationProvider protocol MUST define `search` method with signature: `(file_path: Path, query: SearchQuery, *, progress_callback: Optional[ProgressCallback] = None, on_skip: Optional[OnSkipCallback] = None) -> Iterator[SearchResult]`
- **FR-217**: ConversationProvider protocol MUST define `get_conversation_by_id` method with signature: `(file_path: Path, conversation_id: str) -> Optional[Conversation]`
- **FR-218**: All protocol methods MUST document ALL raised exceptions (FileNotFoundError, PermissionError, ParseError, ValidationError, SchemaVersionError) in docstrings
- **FR-219**: Protocol MUST define type aliases for callbacks: `ProgressCallback = Callable[[int], None]` and `OnSkipCallback = Callable[[str, str], None]`
- **FR-220**: All protocol methods MUST use keyword-only arguments (after `*`) for optional parameters to prevent positional argument brittleness
- **FR-221**: Protocol documentation MUST specify memory guarantees, thread safety, and determinism for each method

**Pydantic Model Configuration**

- **FR-222**: Conversation model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-223**: Message model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-224**: SearchResult model MUST use `model_config = ConfigDict(frozen=True, strict=True, extra="forbid")`
- **FR-225**: SearchQuery model MAY use `frozen=False` for user convenience but MUST use `strict=True, extra="forbid"`
- **FR-226**: All Pydantic models MUST set `arbitrary_types_allowed=False` to prevent non-serializable types
- **FR-227**: Library MUST document immutability contract in all model docstrings

**Type Annotation Policy**

- **FR-228**: ALL public functions and methods MUST have complete type annotations for parameters and return types
- **FR-229**: Public API MUST NOT use `Any` type in function signatures (parameters or returns)
- **FR-230**: Public API MAY use `Any` only in: (1) metadata dictionaries (`dict[str, Any]`), (2) private implementation functions, (3) JSON parsing intermediate results
- **FR-231**: Library MUST enforce `mypy --strict` in CI pipeline for all public API modules
- **FR-232**: Library MUST achieve 100% type coverage for public API (measured by mypy)
- **FR-233**: Library MUST use Protocol for callback types instead of `Callable[..., Any]`

**Provider-Agnostic Data Models**

- **FR-234**: Conversation model MUST contain ONLY fields common to all AI providers (id, title, created_at, updated_at, messages)
- **FR-235**: Conversation model MUST NOT include provider-specific fields (moderation_results, plugin_ids, workspace_id, etc.)
- **FR-236**: Conversation model MUST provide `metadata: dict[str, Any]` field for provider-specific data
- **FR-237**: Adapter implementations MUST store provider-specific fields in metadata dict, NOT as top-level Conversation fields
- **FR-238**: Library documentation MUST warn consumers NOT to rely on specific metadata fields (not part of stable API)

**Message Role Normalization**

- **FR-239**: Message model MUST use normalized role type: `Literal["user", "assistant", "system"]`
- **FR-240**: Adapters MUST map provider-specific roles to normalized roles: "human" → "user", "model" → "assistant"
- **FR-241**: Adapters MUST preserve original provider role in `metadata["original_role"]` field
- **FR-242**: Adapters MUST handle providers lacking certain role types (e.g., Claude lacking "system") by storing instructions in metadata
- **FR-243**: Library documentation MUST define role normalization mapping for each supported provider

**Timestamp Normalization**

- **FR-244**: ALL datetime fields (created_at, updated_at, timestamp) MUST be timezone-aware Python datetime objects
- **FR-245**: ALL datetime fields MUST be normalized to UTC timezone before creating Conversation/Message objects
- **FR-246**: Pydantic models MUST include field validators rejecting naive datetimes (no timezone)
- **FR-247**: Adapters MUST convert provider-specific timestamp formats (Unix, ISO 8601, RFC 3339) to UTC datetime objects
- **FR-248**: Pydantic JSON serialization MUST output timestamps as ISO 8601 strings with 'Z' suffix (UTC indicator)

**Fail Fast vs Skip Malformed Clarification**

- **FR-249**: Library MUST fail fast (raise exception immediately) for operational errors: file access, permissions, disk space, schema version
- **FR-250**: Library MUST skip & continue for data quality issues: malformed entries, missing fields, invalid formats within individual conversations
- **FR-251**: Library MUST distinguish "fail fast" (operational) from "skip malformed" (data quality) in documentation
- **FR-252**: Skipped entries MUST trigger on_skip callback (if provided) and MUST be logged at WARNING level
- **FR-253**: Library MUST NOT retry any operation (operational or data quality) - fail fast means single attempt

**Streaming vs Relevance Ranking Resolution**

- **FR-254**: Search with keywords MUST use two-pass streaming: (1) filter and score, (2) sort and yield
- **FR-255**: Search with keywords MUST buffer only matching conversations in memory (not entire file)
- **FR-256**: Search without keywords MUST use single-pass streaming (true O(1) memory)
- **FR-257**: Search memory usage MUST be O(matching_result_count), NOT O(file_size)
- **FR-258**: Library documentation MUST document memory trade-offs for keyword vs non-keyword search

**YAGNI vs Multi-Provider Resolution**

- **FR-259**: Library MUST define ConversationProvider Protocol in v1.0 even with only one adapter
- **FR-260**: Library MUST implement only OpenAI adapter in v1.0 (no Anthropic/Google adapters until explicitly requested)
- **FR-261**: Library MUST include protocol compliance test suite that all current and future adapters must pass
- **FR-262**: Library documentation MUST explain multi-provider architecture and how to add future adapters
- **FR-263**: Future adapter implementations MUST be added only when users explicitly request support for that provider

**Malformed Entry Categories**

- **FR-264**: Library MUST categorize malformed entries as: (1) JSON syntax errors, (2) schema violations (missing required fields), (3) validation failures (invalid field values)
- **FR-265**: Library MUST skip all three categories of malformed entries and continue processing (not raise exceptions)
- **FR-266**: Library MUST log warnings for each skipped entry with category-specific error messages
- **FR-267**: on_skip callback MUST receive conversation ID (or "line-N" if ID unavailable) and category-specific error message
- **FR-268**: Library documentation MUST provide examples of each malformed entry category and expected handling

**Conversation Metadata Enumeration**

- **FR-269**: Conversation metadata MUST include exactly five required fields: id, title, created_at, updated_at, messages
- **FR-270**: Conversation id MUST be non-empty string, unique within export file
- **FR-271**: Conversation title MUST be non-empty string, MAY contain any UTF-8 characters
- **FR-272**: Conversation created_at and updated_at MUST be timezone-aware datetime in UTC
- **FR-273**: Conversation updated_at MUST be >= created_at (Pydantic validator enforced)
- **FR-274**: Conversation messages MUST be non-empty list (conversations with zero messages are invalid)
- **FR-275**: Conversation metadata dict is for provider-specific fields only, NOT part of stable API

**Message Tree Structure**

- **FR-276**: Message tree structure MUST be represented using parent_id references (adjacency list pattern)
- **FR-277**: Message parent_id MUST reference valid message ID within same conversation (Pydantic validator enforced)
- **FR-278**: Conversation MUST provide tree navigation helper methods: get_root_messages(), get_children(), get_thread(), get_all_threads()
- **FR-279**: JSON serialization MUST use flat message list (not nested objects) with parent_id references
- **FR-280**: Library documentation MUST include tree structure examples and navigation patterns

**Malformed Entry Handling in Streaming**

- **FR-281**: stream_conversations MUST skip malformed entries (JSON syntax errors, validation failures) without raising exceptions
- **FR-282**: Skipped entries MUST be logged at WARNING level with conversation ID, line number, error type, and reason
- **FR-283**: Skipped entries MUST invoke on_skip callback (if provided) with conversation ID and error reason
- **FR-284**: Skipped entries MUST NOT stop iteration (continue processing remaining conversations)
- **FR-285**: Library documentation MUST include example of tracking skipped entries via on_skip callback

**Public Exception API Contract**

- **FR-286**: Library public exception API MUST consist of: EchomineError (base), ParseError, ValidationError, SchemaVersionError
- **FR-287**: Library MUST re-raise standard Python exceptions as-is (FileNotFoundError, PermissionError, OSError) without wrapping
- **FR-288**: Library documentation MUST include exception handling example showing correct pattern
- **FR-289**: Future library versions MAY add new EchomineError subclasses (consumers catching EchomineError are forward-compatible)
- **FR-290**: Library MUST guarantee exception API stability (listed exceptions will not be removed or renamed in MAJOR version)

**CLI Interface Contract (stdout/stderr Separation & Exit Codes)**

- **FR-291**: CLI MUST write search results (default and --json format) to stdout
- **FR-292**: CLI MUST write progress indicators, warnings, and diagnostic messages to stderr
- **FR-293**: CLI MUST write error messages to stderr
- **FR-294**: CLI MUST write help text (--help) and version info (--version) to stdout
- **FR-295**: CLI MUST NOT mix result data and metadata in same stream (strict separation)
- **FR-296**: CLI MUST exit with code 0 for successful operations (even if some entries were skipped)
- **FR-297**: CLI MUST exit with code 1 for operational errors (file not found, permission denied, parse errors, validation errors)
- **FR-298**: CLI MUST exit with code 2 for usage errors (invalid arguments, missing required parameters)
- **FR-299**: CLI MUST exit with code 130 when interrupted by user (Ctrl+C / SIGINT)
- **FR-300**: CLI MUST document exit codes in --help text and documentation

**CLI JSON Output Format & Composability**

- **FR-301**: CLI --json flag MUST output valid JSON with schema: `{"results": [...], "metadata": {...}}`
- **FR-302**: JSON results array MUST include fields: conversation_id, title, created_at, updated_at, score, matched_message_ids, message_count
- **FR-303**: JSON metadata object MUST include fields: query, total_results, skipped_conversations, elapsed_seconds
- **FR-304**: JSON timestamps MUST use ISO 8601 format with UTC timezone (YYYY-MM-DDTHH:MM:SSZ)
- **FR-305**: JSON output MUST be valid (parseable by standard JSON libraries) and pretty-printed with 2-space indentation
- **FR-306**: CLI documentation MUST include JSON schema specification and jq usage examples
- **FR-307**: CLI MUST be composable in Unix pipelines (results to stdout, metadata to stderr)
- **FR-308**: CLI --json output MUST be valid JSON parseable by jq and standard JSON libraries
- **FR-309**: CLI documentation MUST include at least 5 pipeline examples showing composition with jq, grep, xargs
- **FR-310**: CLI MUST support quiet mode (suppress progress to stderr) for cleaner pipeline integration
- **FR-311**: CLI error messages MUST be actionable and include exit codes in documentation

**CLI Exit Code Consistency**

- **FR-312**: CLI exit codes MUST be consistent with FR-022 (non-zero on failure) and FR-033 (exit 1 for file system errors)
- **FR-313**: CLI MUST use exit code 0 for all successful operations (including 0 results)
- **FR-314**: CLI MUST use exit code 1 for all operational failures (file access, parsing, validation)
- **FR-315**: CLI MUST use exit code 2 for usage errors (invalid arguments, missing parameters)
- **FR-316**: CLI MUST use exit code 130 for user interrupts (SIGINT)

**BM25 Relevance Scoring**

- **FR-317**: Library MUST use BM25 algorithm for keyword relevance scoring (not classic TF-IDF)
- **FR-318**: BM25 parameters MUST be: k1=1.5 (term saturation), b=0.75 (length normalization)
- **FR-319**: BM25 scores MUST be normalized to 0.0-1.0 range using: score_normalized = score_raw / (score_raw + 1)
- **FR-320**: Library documentation MUST explain BM25 formula, parameters, and score interpretation
- **FR-321**: SearchResult.score field MUST contain normalized BM25 score (0.0-1.0)

**Keyword Frequency Calculation**

- **FR-322**: Keyword frequency MUST be calculated across all messages in a conversation (conversation = document)
- **FR-323**: BM25 scoring MUST treat concatenated conversation messages as single document
- **FR-324**: Keyword position within messages MUST NOT affect relevance score in v1.0 (only frequency matters)
- **FR-325**: SearchResult.matched_message_ids MUST list IDs of messages containing any query keyword
- **FR-326**: Keyword matching MUST be case-insensitive ("Python" matches "python")

**Title Filtering Semantics**

- **FR-327**: Title filtering MUST use case-insensitive substring matching
- **FR-328**: Title filter "algo" MUST match titles: "Algorithm", "Algorithms", "algorithm design"
- **FR-329**: Title filtering MUST NOT use fuzzy matching or edit distance in v1.0
- **FR-330**: Title filter with spaces MUST match literal substring (e.g., "algo design" requires exact phrase)
- **FR-331**: Library documentation MUST include title filtering examples showing substring matching behavior

**Search Limit Semantics**

- **FR-332**: Search limit MUST be applied AFTER relevance ranking (return top N by score, not first N encountered)
- **FR-333**: Search results MUST be sorted by relevance score descending before applying limit
- **FR-334**: Search with limit=5 MUST return the 5 highest-scored conversations (even if 1000+ match)
- **FR-335**: Search without limit MUST return ALL matching conversations sorted by relevance descending
- **FR-336**: Library documentation MUST clarify that limit returns "top N most relevant" not "first N found"

**cognivault Integration Workflow**

- **FR-337**: cognivault integration MUST follow workflow: adapter creation → streaming → transformation → ingestion → summary
- **FR-338**: cognivault MUST use progress_callback to track ingestion progress (log every 100 conversations)
- **FR-339**: cognivault MUST use on_skip callback to track skipped entries and include in summary report
- **FR-340**: cognivault MUST transform Conversation objects to cognivault schema before ingestion
- **FR-341**: cognivault integration MUST return summary with: ingested_count, skipped_count, skipped_entries list

**Rate Limiting & Backpressure**

- **FR-342**: Library MUST NOT implement rate limiting or throttling (consumers control pace via pull-based iteration)
- **FR-343**: Library generators MUST yield next item immediately when consumer requests it (no delays)
- **FR-344**: cognivault MAY implement rate limiting by adding delays between iterations
- **FR-345**: Library documentation MUST include rate limiting examples showing consumer-side patterns

**cognivault Transformation Specifics**

- **FR-346**: cognivault transformation MUST convert datetime fields to ISO 8601 strings using `.isoformat()`
- **FR-347**: cognivault transformation MUST include all required fields: conversation_id, title, created_at, updated_at, messages
- **FR-348**: cognivault transformation MUST include thread structure using `conversation.get_all_threads()`
- **FR-349**: cognivault transformation MUST preserve provider-specific metadata in separate fields
- **FR-350**: Library documentation MUST include complete transformation function example

**Ingestion Patterns**

- **FR-351**: cognivault MAY use one-at-a-time ingestion pattern for simplicity and low memory usage
- **FR-352**: cognivault MAY use batched ingestion pattern for higher throughput (recommended batch size: 100-1000)
- **FR-353**: cognivault MAY use concurrent ingestion with multiple threads/tasks for maximum throughput
- **FR-354**: Library documentation MUST include examples of all three ingestion patterns
- **FR-355**: Library iterators MUST be safe for concurrent consumption by multiple threads (each thread gets own iterator)

**Search-Then-Export Workflow**

- **FR-356**: Library MUST support search-then-export workflow: search() returns results with IDs, get_conversation_by_id() retrieves full conversation
- **FR-357**: SearchResult MUST include full Conversation object to enable single-pass export (no re-parsing needed)
- **FR-358**: CLI MUST support exporting conversation by ID: `echomine export FILE CONVERSATION_ID`
- **FR-359**: CLI search --json output MUST include conversation_id field for easy extraction and piping to export command
- **FR-360**: Library documentation MUST include complete search-then-export workflow examples (both two-step and optimized patterns)

**Batch Processing Support**

- **FR-361**: Library MUST support sequential batch processing (same adapter instance for multiple files)
- **FR-362**: Library MUST support concurrent batch processing (separate adapter instances per thread, per FR-099)
- **FR-363**: Adapter instances MUST be reusable across different files (stateless design per FR-114)
- **FR-364**: CLI MUST be composable for batch processing via shell loops and parallel utilities
- **FR-365**: Library documentation MUST include batch processing examples (sequential and concurrent patterns)

**Search Fallback Patterns**

- **FR-366**: Library MUST NOT implement automatic title fallback when keyword search returns zero results
- **FR-367**: Users MAY implement fallback logic by making sequential search calls with different query parameters
- **FR-368**: Library documentation MUST include fallback pattern example showing user-controlled retry
- **FR-369**: SearchQuery MUST support combined filters (keywords + title) with AND logic (not OR/fallback)

**Pagination vs Iteration**

- **FR-370**: Library search() MUST return iterator (not paginated results)
- **FR-371**: Library MUST NOT implement pagination API (no page_size, page_number parameters)
- **FR-372**: Consumers MUST use SearchQuery.limit to bound result set size (recommended for large result sets)
- **FR-373**: Consumers MAY use itertools.islice() to consume first N results from unlimited search
- **FR-374**: Library documentation MUST explain handling large result sets via limit, itertools, and lazy iteration

**Partial Result Delivery**

- **FR-375**: Library MUST NOT support partial result delivery in v1.0 (ranking requires scoring all matches before returning top N)
- **FR-376**: Library MAY provide progress_callback to indicate scoring progress while results are being computed
- **FR-377**: Future versions MAY add chronological ordering to enable partial result delivery (non-ranked search)
- **FR-378**: Library documentation MUST explain that ranking requires buffering all matching results before yielding any

**Required Field Validation**

- **FR-379**: Library MUST skip conversations missing required fields (id, title, created_at, updated_at, messages)
- **FR-380**: Library MUST skip conversations with empty id or title (empty string after trimming whitespace)
- **FR-381**: Library MUST skip conversations with zero messages (empty messages array)
- **FR-382**: Skipped conversations MUST trigger on_skip callback with descriptive reason including which fields are missing
- **FR-383**: Skipped conversations MUST be logged at WARNING level with fields: conversation_id, line_number, missing_fields

**Empty Content Handling**

- **FR-384**: Message content field MUST accept empty strings (represents deleted/redacted messages)
- **FR-385**: Library MUST NOT trim or normalize message content (preserve whitespace, empty strings as-is)
- **FR-386**: Missing content field MUST raise ValidationError (content field required, but can be empty string)
- **FR-387**: Empty content messages MUST NOT match keyword searches (no content to search)
- **FR-388**: Empty content messages MUST be included in conversation (preserved for tree structure integrity)

**Retry Logic & Fail-Fast Behavior**

- **FR-389**: Library MUST NOT implement retry logic for any operation (file access, parsing, validation, network)
- **FR-390**: Library consumers MAY implement retry logic using decorator libraries (tenacity, backoff)
- **FR-391**: Library MUST fail immediately on all errors (no delays, no retry hints in exceptions)
- **FR-392**: Library documentation MUST state that NO retries are performed and consumers must implement retry if needed
- **FR-393**: All exceptions MUST be raised immediately (no internal retry attempts before raising)

**Resource Cleanup Guarantees**

- **FR-394**: Library MUST use context managers (with statements) for all file I/O operations
- **FR-395**: File handles MUST be closed even when: exceptions raised, iteration breaks early, generators garbage collected
- **FR-396**: Library MUST NOT create temporary files (no temp file cleanup needed)
- **FR-397**: Library MUST use try/finally blocks to guarantee cleanup code execution
- **FR-398**: Library documentation MUST document cleanup guarantees (resources always released)

**Export Path Behavior**

- **FR-399**: CLI MUST default to current working directory for export output (per FR-018)
- **FR-400**: CLI MUST support --output flag to specify custom export directory
- **FR-401**: Library export functions MUST require explicit output_path parameter (no default)
- **FR-402**: Library MUST NOT use current working directory as default (explicit over implicit)
- **FR-403**: Documentation MUST explain CLI vs library export path behavior differences

**Date Range Filtering Input Formats**

- **FR-404**: Library SearchQuery MUST accept date_from/date_to as: datetime objects, date objects, OR ISO 8601 strings
- **FR-405**: Library MUST automatically parse ISO 8601 date strings to datetime objects (Pydantic validator)
- **FR-406**: CLI MUST parse --from/--to flags as ISO 8601 strings and convert to datetime for SearchQuery
- **FR-407**: Date filtering MUST use datetime comparison internally (consistent behavior across input formats)
- **FR-408**: Library documentation MUST show all three date input formats with examples

**Search Limit CLI vs Library Alignment**

- **FR-409**: CLI --limit flag MUST map directly to SearchQuery.limit field (no transformation)
- **FR-410**: Both CLI and library MUST default to None (no limit, return all results)
- **FR-411**: Both CLI and library MUST validate limit >= 1 (if specified)
- **FR-412**: Both CLI and library MUST interpret limit as "top N by relevance score" (not "first N encountered")
- **FR-413**: Documentation MUST show CLI and library limit usage with identical semantics

**Exception Handling CLI vs Library Alignment**

- **FR-414**: CLI MUST catch all library exceptions and map to appropriate exit codes (FileNotFoundError → 1, etc.)
- **FR-415**: CLI MUST write all error messages to stderr (never stdout)
- **FR-416**: CLI MUST preserve exception messages from library (don't obscure root cause)
- **FR-417**: CLI MUST handle KeyboardInterrupt separately (exit 130, not 1)
- **FR-418**: Library exceptions and CLI exit codes MUST be documented together (mapping table)

**Keyword Search Scope Consistency**

- **FR-419**: Keyword search (FR-006, FR-017) MUST search across ALL messages in conversation (not just title or first message)
- **FR-420**: CLI --keywords flag MUST map to SearchQuery.keywords field (consistent naming)
- **FR-421**: Both library and CLI MUST use same search algorithm (BM25 relevance scoring)
- **FR-422**: Documentation MUST clarify FR-006 (library) and FR-017 (CLI) describe same feature

**quickstart.md Alignment**

- **FR-423**: quickstart.md examples MUST use keyword-only arguments for all protocol methods
- **FR-424**: quickstart.md MUST include tree navigation examples (get_all_threads, get_thread)
- **FR-425**: quickstart.md MUST show Pydantic ConfigDict configuration
- **FR-426**: quickstart.md MUST show role normalization and timestamp handling
- **FR-427**: quickstart.md MUST be reviewed for consistency after every spec update

**spec.md CLI Examples Alignment**

- **FR-428**: spec.md CLI examples MUST demonstrate stdout/stderr separation
- **FR-429**: spec.md MUST document all CLI exit codes (0, 1, 2, 130) with examples
- **FR-430**: spec.md MUST include at least 3 pipeline composition examples
- **FR-431**: spec.md CLI examples MUST use complete --json schema (results + metadata)
- **FR-432**: spec.md MUST show --help and --version output examples

**data-model.md Pydantic Alignment**

- **FR-433**: data-model.md MUST document all Pydantic model_config settings (frozen, strict, extra)
- **FR-434**: data-model.md MUST document all field validators with examples
- **FR-435**: data-model.md MUST show complete field type specifications (Literal, Optional, etc.)
- **FR-436**: data-model.md MUST include JSON serialization examples for all models
- **FR-437**: data-model.md MUST be kept in sync with src/ Pydantic model implementations

**List All Conversations (User Story 0 - P0)**

- **FR-438**: CLI MUST provide `list` command with signature: `echomine list FILE [--limit N] [--json]`
- **FR-439**: List command MUST stream conversations using ConversationProvider.stream_conversations without filters
- **FR-440**: List output MUST sort conversations by created_at descending (newest first) by default
- **FR-441**: List human-readable format MUST display: created_at date, title, message count per conversation
- **FR-442**: List --json format MUST output array of objects with fields: id, title, created_at, updated_at, message_count
- **FR-443**: List --limit flag MUST restrict output to top N conversations (after sorting)
- **FR-444**: List MUST complete in <5 seconds for 10K conversations (streaming, not full load)
- **FR-445**: List MUST display "No conversations found" with exit code 0 for empty export files
- **FR-446**: List MUST write conversation list to stdout (pipeable)
- **FR-447**: List MUST write progress/errors to stderr (consistent with search command)

### Key Entities

- **Conversation**: Represents a complete conversation thread with metadata (title, ID, creation timestamp, last update), a collection of messages, and participant information. A conversation can contain branching message trees.

- **Message**: Represents a single message in a conversation with content (text), author role (user/assistant/system), timestamp, unique ID, parent message ID (for threading), and optional child message IDs (for branches).

- **SearchResult**: Represents a conversation match from a search query with the conversation object, relevance score (0.0-1.0), matching excerpt (up to 200 characters showing keyword context), and matched keywords list.

- **ExportAdapter**: Represents a provider-specific parser (e.g., OpenAIAdapter) that conforms to the ConversationProvider protocol. Responsible for reading export files, parsing provider-specific formats, and yielding Conversation objects.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can search a 1.6GB ChatGPT export file and receive results within 30 seconds
- **SC-002**: Users can find relevant conversations with 90%+ accuracy when searching by known keywords
- **SC-003**: Exported markdown files are immediately usable in documentation tools without manual reformatting
- **SC-004**: Library users can integrate Echomine into their projects in under 10 minutes following documentation
- **SC-005**: System successfully processes up to 10,000 conversations (50,000 total messages) without crashing or running out of memory on a machine with 8GB RAM; 1000+ conversations represents minimum viable scale
- **SC-006**: All operations complete with clear error messages when invalid inputs are provided (no cryptic stack traces exposed to users)
- **SC-007**: Search results return the top 5 most relevant conversations 95% of the time when users search for specific topics they know exist
- **SC-008**: Malformed export files (up to 10% corrupted entries) can still be processed with only the corrupted entries skipped

### Assumptions

- Users have Python 3.12+ installed on their system
- Export files follow OpenAI's documented JSON structure (as of 2024)
- Users are comfortable using command-line tools or have basic programming knowledge for library use
- Export files are stored locally (not on remote servers requiring authentication)
- Default text encoding for export files is UTF-8
- Users want to preserve the original conversation content without modification
- Keyword search uses case-insensitive matching by default
- "Relevance" for search ranking is determined by keyword frequency and position (TF-IDF-like scoring)
- Performance testing baseline targets 10,000 conversations with 50,000 total messages (heavy user scale); minimum viable performance is 1000+ conversations

### Out of Scope (v1.0)

- ❌ Claude, Gemini, or other AI provider export support (future adapters)
- ❌ Semantic search using embeddings or vector databases
- ❌ Web-based user interface
- ❌ Conversation editing, modification, or merging capabilities
- ❌ Cloud storage integration (S3, Google Drive, etc.)
- ❌ Real-time conversation streaming or monitoring
- ❌ Analytics or statistics about conversation patterns
- ❌ Multi-user collaboration or sharing features
- ❌ Conversation summarization or AI-generated insights
