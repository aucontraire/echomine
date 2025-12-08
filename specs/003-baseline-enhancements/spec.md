# Feature Specification: Baseline Enhancement Package v1.2.0

**Feature Branch**: `003-baseline-enhancements`
**Created**: 2025-12-05
**Status**: Draft
**Input**: User description: "Baseline Enhancement Package v1.2.0: Message count filtering, statistics command, per-conversation stats, list messages, rich markdown export, Rich CLI formatting, sort results, CSV export, and library-first APIs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Conversations by Message Count (Priority: P1)

As a Researcher, I want to filter search results by conversation message count so that I can focus on conversations that match my depth criteria (substantial discussions vs. quick exchanges).

**Why this priority**: Message count filtering is essential for distinguishing between substantial technical discussions and quick Q&A exchanges. This directly impacts research efficiency by eliminating irrelevant results upfront.

**Independent Test**: Can be tested by searching with `--min-messages 10` and verifying all returned conversations have at least 10 messages.

**Acceptance Scenarios**:

1. **Given** an export file with conversations of varying lengths (2-100 messages), **When** user runs `echomine search export.json --keywords "architecture" --min-messages 10`, **Then** only conversations with 10+ messages are returned.

2. **Given** an export file, **When** user runs `echomine search export.json --max-messages 5`, **Then** only conversations with 5 or fewer messages are returned.

3. **Given** user specifies both bounds, **When** user runs `echomine search export.json --min-messages 5 --max-messages 20`, **Then** only conversations with 5-20 messages are returned.

4. **Given** user specifies invalid bounds (min > max), **When** search executes, **Then** system exits with error code 2 and clear error message.

5. **Given** JSON output requested, **When** search returns results, **Then** each result includes `message_count` field.

---

### User Story 2 - View Export Statistics (Priority: P1)

As a CLI User, I want to see comprehensive statistics about my conversation export so that I can understand the scope of my data and make informed filtering decisions.

**Why this priority**: Understanding export scope is fundamental before any filtering or search operation. Users need to know total counts, date ranges, and distribution to make informed decisions.

**Independent Test**: Can be tested by running `echomine stats export.json` and verifying output shows total conversations, messages, and date range.

**Acceptance Scenarios**:

1. **Given** a valid export file, **When** user runs `echomine stats export.json`, **Then** output displays: total conversations, total messages, date range (earliest to latest), average messages per conversation.

2. **Given** statistics command, **When** user adds `--json` flag, **Then** output is valid JSON with same schema fields.

3. **Given** a 1GB+ export file, **When** statistics are calculated, **Then** operation completes without excessive memory usage (streaming approach).

4. **Given** an export with malformed conversations, **When** statistics are calculated, **Then** malformed entries are logged as warnings and excluded from statistics.

5. **Given** a long-running statistics operation, **When** processing, **Then** progress is reported to stderr (e.g., "Analyzed 1000 conversations...").

---

### User Story 3 - View Per-Conversation Statistics (Priority: P2)

As a Researcher, I want to see detailed message-level statistics for a specific conversation so that I can understand the interaction dynamics (role distribution, temporal patterns).

**Why this priority**: Per-conversation analysis is valuable but secondary to overall export statistics. Useful for deep-dive analysis after initial filtering.

**Independent Test**: Can be tested by running `echomine stats export.json --conversation <id>` and verifying role breakdown and temporal patterns are displayed.

**Acceptance Scenarios**:

1. **Given** a valid conversation ID, **When** user runs `echomine stats export.json --conversation <id>`, **Then** output shows: title, dates, message count by role (user/assistant/system), first/last message timestamps.

2. **Given** per-conversation stats, **When** displayed, **Then** roles are color-coded (user=green, assistant=blue, system=yellow).

3. **Given** invalid conversation ID, **When** command runs, **Then** system exits with code 1 and error message "Conversation not found".

4. **Given** per-conversation stats, **When** user adds `--json` flag, **Then** output is valid JSON with all statistics fields.

---

### User Story 4 - List All Messages for a Conversation (Priority: P2)

As a Developer, I want to retrieve all message IDs with metadata for a conversation so that I can programmatically process individual messages or build message-level indices.

**Why this priority**: Message-level access supports advanced workflows like building indices or processing specific messages. Secondary to basic filtering and statistics.

**Independent Test**: Can be tested by running `echomine get messages export.json <conversation-id>` and verifying all messages are listed with IDs, roles, and timestamps.

**Acceptance Scenarios**:

1. **Given** a valid conversation ID, **When** user runs `echomine get messages export.json <id>`, **Then** output shows all messages with: message_id, role, timestamp, content preview (first 100 chars).

2. **Given** message listing, **When** user adds `--json` flag, **Then** output includes full message objects (id, role, timestamp, content).

3. **Given** invalid conversation ID, **When** command runs, **Then** system exits with code 1 and error message.

4. **Given** streaming mode, **When** finding conversation, **Then** system streams through file without loading entire export into memory.

---

### User Story 5 - Export Conversations with Rich Metadata (Priority: P2)

As a Data Analyst, I want exported markdown files to include YAML frontmatter with conversation metadata so that I can process exports with static site generators and knowledge management tools.

**Why this priority**: Rich metadata enables integration with documentation systems (Jekyll, Hugo, Obsidian). Important for knowledge management workflows.

**Independent Test**: Can be tested by exporting a conversation and verifying YAML frontmatter at start of file and message IDs in headers.

**Acceptance Scenarios**:

1. **Given** markdown export, **When** user runs `echomine export export.json <id> --output chat.md`, **Then** output includes YAML frontmatter with: id, title, created_at, updated_at, message_count, export_date, exported_by.

2. **Given** markdown export, **When** viewing message headers, **Then** each header includes message ID in inline code format (e.g., `## User (\`msg-1\`) - 2024-01-15 10:30:00 UTC`).

3. **Given** backward compatibility requirement, **When** user adds `--no-metadata` flag, **Then** frontmatter is omitted (original format).

4. **Given** frontmatter format, **When** file is parsed, **Then** frontmatter follows Jekyll/Hugo conventions (triple-dash delimiters).

---

### User Story 6 - View Rich Formatted CLI Output (Priority: P3)

As a CLI User, I want beautifully formatted terminal output with tables, colors, and progress bars so that I can quickly scan results and understand status at a glance.

**Why this priority**: UX enhancement that improves usability but doesn't add core functionality. Lower priority than data access features.

**Independent Test**: Can be tested by running list/search commands and verifying output uses table format with color-coded elements.

**Acceptance Scenarios**:

1. **Given** list or search command, **When** output is displayed, **Then** results appear in table format with columns: ID, Title, Messages, Created, Score (if search).

2. **Given** search results with scores, **When** displayed, **Then** scores are color-coded: high (>0.7 green), medium (0.4-0.7 yellow), low (<0.4 red).

3. **Given** long-running operation, **When** processing, **Then** progress bar shows in stderr with: operation name, percentage, item count, elapsed time.

4. **Given** stdout is not a TTY (piped), **When** output is displayed, **Then** all rich formatting is disabled (plain text).

5. **Given** `--json` flag is used, **When** output is displayed, **Then** rich formatting is disabled.

---

### User Story 7 - Sort Search Results (Priority: P3)

As a Researcher, I want control over search result ordering so that I can prioritize results by relevance, recency, title, or conversation depth.

**Why this priority**: Sorting is a convenience feature. Default score-based sorting works for most cases; custom sorting is an enhancement.

**Independent Test**: Can be tested by searching with `--sort date` and verifying results are ordered by updated_at timestamp.

**Acceptance Scenarios**:

1. **Given** search results, **When** user runs `echomine search export.json -k "python" --sort date`, **Then** results are ordered by updated_at (most recent first by default).

2. **Given** sort by title, **When** user runs `--sort title --order asc`, **Then** results are alphabetically ordered (case-insensitive).

3. **Given** sort by messages, **When** user runs `--sort messages --order asc`, **Then** shortest conversations appear first.

4. **Given** no sort flag, **When** search executes, **Then** default ordering is by score (descending).

---

### User Story 8 - Export Results to CSV Format (Priority: P3)

As a Data Analyst, I want to export conversation data to CSV format so that I can analyze results in Excel, R, pandas, or other data analysis tools.

**Why this priority**: CSV export enables data analysis workflows. Lower priority as JSON export already exists and can be converted.

**Independent Test**: Can be tested by running search with `--format csv` and verifying output is valid CSV with proper headers and escaping.

**Acceptance Scenarios**:

1. **Given** search results, **When** user runs `echomine search export.json -k "python" --format csv`, **Then** output is RFC 4180 compliant CSV with headers: conversation_id, title, created_at, updated_at, message_count, score.

2. **Given** CSV output, **When** content contains commas or quotes, **Then** values are properly escaped.

3. **Given** message-level detail requested, **When** user adds `--csv-messages` flag, **Then** output includes per-message rows: conversation_id, message_id, role, timestamp, content.

4. **Given** large result set, **When** CSV is generated, **Then** streaming writer is used (constant memory).

---

### User Story 9 - Library-First Message Count Filtering (Priority: P1)

As a Developer, I want to programmatically filter conversations by message count in my Python code so that I can build custom data pipelines without shelling out to the CLI.

**Why this priority**: Library-first architecture is a core project principle. All CLI features must be accessible programmatically.

**Independent Test**: Can be tested by creating SearchQuery with min_messages/max_messages and verifying adapter.search() respects these filters.

**Acceptance Scenarios**:

1. **Given** SearchQuery model, **When** instantiated with `min_messages=10`, **Then** model validates and stores the value.

2. **Given** OpenAIAdapter.search() with message count filters, **When** streaming results, **Then** only conversations matching count criteria are yielded.

3. **Given** type hints, **When** mypy --strict runs, **Then** zero type errors for message count fields.

4. **Given** invalid values (min > max, negative numbers), **When** SearchQuery is created, **Then** Pydantic raises ValidationError.

---

### User Story 10 - Library-First Statistics API (Priority: P1)

As a Developer, I want to calculate export and conversation statistics programmatically so that I can build dashboards, monitoring tools, or data quality checks.

**Why this priority**: Library-first architecture requirement. Statistics API enables integration with monitoring and analysis tools.

**Independent Test**: Can be tested by calling calculate_statistics() and verifying returned ExportStatistics model contains all expected fields.

**Acceptance Scenarios**:

1. **Given** calculate_statistics() function, **When** called with file_path, **Then** returns ExportStatistics with: total_conversations, total_messages, date_range, average_messages.

2. **Given** calculate_conversation_statistics() function, **When** called with Conversation, **Then** returns ConversationStatistics with: message_count_by_role, duration, average_gap.

3. **Given** large export, **When** calculate_statistics() runs, **Then** uses streaming (O(1) memory).

4. **Given** progress callback parameter, **When** provided, **Then** callback is invoked periodically during processing.

---

### Edge Cases

- What happens when min_messages equals max_messages? System should return conversations with exactly that message count.
- How are conversations with 0 messages handled? Excluded from statistics; logged as warning.
- What if export file is empty (no conversations)? Statistics command returns zeros with appropriate message.
- How does CSV handle newlines in message content? Newlines are preserved inside quoted fields per RFC 4180 (not escaped as `\n`).
- What if all conversations are filtered out by message count? Empty result set returned with exit code 0.
- How does Rich formatting behave in CI environments? Auto-detected as non-TTY; plain text output.
- What happens when multiple conversations have the same sort value (e.g., same title)? System uses conversation_id as secondary sort key (ascending, lexicographic) for deterministic ordering.
- How are NULL values handled in CSV (e.g., updated_at when None)? Represented as empty fields (zero-length) per RFC 4180 for compatibility with Excel and pandas.
- What happens if user specifies `--format csv --json`? Last flag wins (--json); WARNING emitted to stderr: "Conflicting output formats: using JSON (last flag wins)".
- What if a message in the source has no ID? A deterministic ID is generated: `msg-{conversation_id}-{index}` (e.g., `msg-abc123-001`).
- How are sort stability guarantees documented? Python's sorted() is stable; equal-scored items maintain their relative order.
- What happens when sorting by date and updated_at is NULL? Falls back to created_at for comparison.
- What happens if user specifies both `--format csv` and `--csv-messages`? Exit code 2 with error: "Error: --format csv and --csv-messages are mutually exclusive."
- What happens on file permission denied? Exit code 1 with error: "Error: Permission denied: {file_path}. Check file read permissions."
- What happens when user presses Ctrl+C? Immediate exit with code 130; partial output may be present; file handles closed via context managers.
- Does `echomine list` support `--sort`? Yes, supports `--sort date|title|messages` (not score); buffers results for sorting.

## Requirements *(mandatory)*

### Functional Requirements

#### Message Count Filtering (US1, US9)

- **FR-001**: CLI search command MUST support `--min-messages N` flag to filter conversations with at least N messages
- **FR-002**: CLI search command MUST support `--max-messages N` flag to filter conversations with at most N messages
- **FR-003**: Both flags MUST be combinable with existing search options (keywords, title, date filters)
- **FR-004**: SearchQuery model MUST include `min_messages: int | None` and `max_messages: int | None` fields
- **FR-005**: Validation MUST enforce: min >= 1, max >= min (when both provided)
- **FR-006**: Filtering MUST use streaming approach (O(1) memory)
- **FR-007**: JSON output MUST include `message_count` field for each result
- **FR-008**: Invalid bounds (min > max) MUST result in exit code 2 with clear error message

#### Export Statistics Command (US2, US10)

- **FR-009**: System MUST provide `echomine stats <export.json>` command
- **FR-010**: Stats output MUST include: total_conversations, total_messages, date_range, average_messages
- **FR-011**: Stats output MUST include: largest_conversation (title, id, count), smallest_conversation (title, id, count)
- **FR-012**: Command MUST support `--json` flag for machine-readable output
- **FR-013**: Statistics calculation MUST use streaming (O(1) memory) for 1GB+ files
- **FR-014**: Progress MUST be reported to stderr during calculation
- **FR-015**: Malformed conversations MUST be logged as warnings and excluded from statistics
- **FR-016**: Library MUST provide `calculate_statistics(file_path: Path, progress_callback: ProgressCallback | None = None) -> ExportStatistics` function
- **FR-017**: ExportStatistics MUST be a Pydantic model with all statistics fields

#### Per-Conversation Statistics (US3, US10)

- **FR-018**: Stats command MUST support `--conversation <id>` option for per-conversation analysis
- **FR-019**: Per-conversation stats MUST show: title, created_at, updated_at, duration
- **FR-020**: Per-conversation stats MUST show message count breakdown by role (user, assistant, system)
- **FR-021**: Per-conversation stats MUST show temporal patterns: first/last message timestamps, average gap
- **FR-022**: Library MUST provide `calculate_conversation_statistics(conversation: Conversation) -> ConversationStatistics` function
- **FR-023**: ConversationStatistics MUST be a Pydantic model with: message_count_by_role, duration, average_gap
- **FR-024**: Per-conversation stats MUST support `--json` flag

#### List Messages Command (US4)

- **FR-025**: System MUST provide `echomine get messages <export.json> <conversation-id>` command
- **FR-026**: Output MUST show messages in chronological order (oldest first): message_id, role, timestamp, content preview (first 100 chars)
- **FR-027**: Command MUST support `--json` flag with full message objects
- **FR-028**: Invalid conversation ID MUST result in exit code 1 with "Conversation not found" error
- **FR-029**: System MUST use streaming to find conversation without loading entire export

#### Rich Markdown Export (US5)

- **FR-030**: Markdown exports MUST include YAML frontmatter by default
- **FR-031**: Frontmatter MUST contain: id, title, created_at, updated_at, message_count, export_date, exported_by
- **FR-031b**: Frontmatter datetime fields (created_at, updated_at, export_date) MUST use ISO 8601 format with UTC 'Z' suffix (e.g., `2024-01-15T10:30:00Z`)
- **FR-032**: Message headers MUST include message ID in inline code format
- **FR-032a**: When source message lacks ID field, adapter MUST generate deterministic ID using format `msg-{conversation_id}-{zero_padded_index}` where index is message's position (001, 002, etc.)
- **FR-032b**: Generated message IDs MUST be deterministic (same source conversation always produces same IDs) to ensure reproducibility
- **FR-033**: CLI export MUST support `--no-metadata` flag to disable frontmatter
- **FR-034**: Frontmatter MUST use triple-dash delimiters (Jekyll/Hugo convention)
- **FR-035**: Library export_to_markdown() MUST accept `include_metadata: bool = True` parameter

#### Rich CLI Formatting (US6)

- **FR-036**: List and search commands MUST display results in table format with columns: ID, Title, Messages, Created, Score
- **FR-037**: Search scores MUST be color-coded: high (>0.7 green), medium (0.4-0.7 yellow), low (<0.4 red)
- **FR-038**: Roles MUST be color-coded: user=green, assistant=blue, system=yellow
- **FR-039**: Long-running operations MUST show progress bar to stderr with: operation name, percentage, item count, elapsed time
- **FR-040**: Rich formatting MUST be disabled when stdout is not a TTY
- **FR-041**: Rich formatting MUST be disabled when `--json` or `--format csv` flags are used
- **FR-041a**: When conflicting output format flags are specified (`--json`, `--format csv`), the LAST flag takes precedence; a WARNING MUST be emitted to stderr indicating the conflict and selected format
- **FR-042**: Error messages MUST use rich formatting with clear hierarchy

#### Sort Results (US7)

- **FR-043**: CLI search MUST support `--sort {score,date,title,messages}` flag
- **FR-043a**: Sort operations MUST use deterministic tie-breaking: when primary sort values are equal, secondary sort is by conversation_id (ascending, lexicographic)
- **FR-043b**: Search result sorting MUST use stable sort (preserving relative order of equal-scored conversations), leveraging Python's sorted() stability guarantee
- **FR-044**: CLI search MUST support `--order {asc,desc}` flag
- **FR-045**: Default sort MUST be by score (descending)
- **FR-046**: Sort by date MUST use updated_at field
- **FR-046a**: When sorting by date and updated_at is NULL, conversations MUST use created_at as fallback for comparison
- **FR-046b**: Sort order for date-based sorting MUST be descending (newest first) unless explicitly specified otherwise
- **FR-047**: Sort by title MUST be case-insensitive
- **FR-048**: SearchQuery model MUST include `sort_by` and `sort_order` fields
- **FR-048a**: CLI list command MUST support `--sort {date,title,messages}` flag (score not applicable to list)
- **FR-048b**: List command with `--sort` MUST buffer all conversations in memory for sorting (breaks O(1) streaming, acceptable for explicit user request)
- **FR-048c**: List command default sort order MUST be: date=descending (newest first), title=ascending (alphabetical), messages=descending (highest count first)

#### CSV Export (US8)

- **FR-049**: List and search commands MUST support `--format csv` flag
- **FR-050**: Conversation-level CSV schema: conversation_id, title, created_at, updated_at, message_count, score
- **FR-051**: Message-level CSV MUST be available via `--csv-messages` flag
- **FR-051a**: Flags `--format csv` and `--csv-messages` MUST be mutually exclusive (exit code 2 if both specified)
- **FR-051b**: Error message for flag conflict: "Error: --format csv and --csv-messages are mutually exclusive. Use --format csv for conversation-level or --csv-messages for message-level export."
- **FR-052**: Message-level CSV schema: conversation_id, message_id, role, timestamp, content
- **FR-053**: CSV output MUST be RFC 4180 compliant with proper escaping
- **FR-053a**: NULL values (e.g., updated_at when None) MUST be represented as empty fields (zero-length, no quotes) in CSV output per RFC 4180
- **FR-053b**: Message content fields with embedded newlines MUST be quoted with newlines preserved as literal line breaks (not escaped as `\n`)
- **FR-053c**: CSV export MUST be parseable by standard tools (Python csv module, pandas, Excel) without data loss or corruption
- **FR-054**: CSV generation MUST use streaming writer (O(1) memory)
- **FR-055**: Library MUST provide CSVExporter class following MarkdownExporter pattern

#### General Requirements

- **FR-056**: All new features MUST maintain O(1) memory usage (streaming architecture)
- **FR-057**: All new SearchQuery fields MUST be optional with sensible defaults
- **FR-058**: All new features MUST maintain backward compatibility with v1.1.0
- **FR-059**: All library functions MUST have comprehensive docstrings with examples
- **FR-060**: All library functions MUST pass mypy --strict with zero errors
- **FR-060a**: All new operations MUST emit structured JSON logs: INFO for operation start/completion (with file_name, item_count, elapsed_seconds), WARNING for recoverable issues (malformed entries), ERROR for unrecoverable failures

#### Error Handling & Interruption

- **FR-061**: CLI MUST exit with code 1 when export file cannot be read due to permission errors (consistent with FileNotFoundError handling)
- **FR-061a**: Permission error message format: "Error: Permission denied: {file_path}. Check file read permissions."
- **FR-061b**: Library MUST raise standard PermissionError (not wrapped), CLI catches and converts to exit code 1
- **FR-062**: CLI MUST exit with code 130 immediately when SIGINT (Ctrl+C) received
- **FR-062a**: File handles MUST be closed automatically via context managers even on SIGINT (no explicit signal handler cleanup needed)
- **FR-062b**: Partial output to stdout during streaming operations (search, list, export) is acceptable when interrupted - no guarantees about output completeness after SIGINT
- **FR-062c**: Library MUST NOT implement signal handlers (CLI layer handles KeyboardInterrupt exception and exits with code 130)

### Key Entities

- **SearchQuery**: Extended with `min_messages`, `max_messages`, `sort_by`, `sort_order` fields
- **ExportStatistics**: New Pydantic model with total_conversations, total_messages, date_range, average_messages, largest_conversation, smallest_conversation
- **ConversationStatistics**: New Pydantic model with message_count_by_role, duration, average_gap
- **CSVExporter**: New exporter class following MarkdownExporter pattern

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can filter out irrelevant short conversations, reducing result noise by 70%+ when using `--min-messages`
- **SC-002**: Statistics command completes in under 5 seconds for 10,000 conversations
- **SC-003**: All CLI features are accessible programmatically via library APIs (100% library-first compliance)
- **SC-004**: Memory usage remains constant (O(1)) regardless of export file size for all new features
- **SC-005**: 100% backward compatibility: existing v1.1.0 commands work unchanged
- **SC-006**: Users can assess export scope in under 10 seconds using statistics command
- **SC-007**: Rich formatting improves result scanning speed (qualitative: easier to identify high-relevance results)
- **SC-008**: CSV export enables direct import into data analysis tools (Excel, pandas, R) without manual preprocessing

## Assumptions

- Users are familiar with basic CLI conventions (flags, arguments)
- Export files follow the existing OpenAI conversation format
- Role values in messages are normalized to "user", "assistant", or "system"
- Users have terminal environments that support ANSI color codes (for Rich formatting)
- CSV consumers expect RFC 4180 standard format
- Statistics calculations use integer message counts (no partial messages)
- Frontmatter metadata follows YAML 1.2 specification
- Progress callbacks are optional and do not affect correctness
