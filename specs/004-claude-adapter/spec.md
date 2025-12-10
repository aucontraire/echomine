# Feature Specification: Claude Export Adapter

**Feature Branch**: `004-claude-adapter`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "Add support for parsing and searching Claude AI conversation exports with feature parity to the existing OpenAI adapter. Includes conversation parsing, message parsing, full search support with BM25 ranking, and provider auto-detection in CLI."

## Clarifications

### Session 2025-12-08

- Q: Should message content be extracted from `text` field or `content` blocks? → A: Parse `content` blocks (92% identical to text, 8% have richer tool context). Fall back to `text` if `content` is empty/missing.
- Q: Should tool_use/tool_result blocks be included in message content? → A: No, skip them (tool metadata not stored in this release, maintains feature parity with OpenAI).
- Q: Should shared utility functions for content block parsing be designed now? → A: Defer to planning phase (implementation detail, not spec concern).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Claude Export Parsing (Priority: P1)

As a researcher with Claude conversation exports, I want to parse Claude export JSON files so that I can analyze my Claude conversations the same way I analyze ChatGPT exports.

**Why this priority**: This is the foundation for all other features. Without conversation parsing, no other functionality is possible. It enables the core use case of accessing Claude conversation data.

**Independent Test**: Can be fully tested by calling `ClaudeAdapter.stream_conversations(file_path)` on a Claude export file and verifying conversations are returned with correct field mappings.

**Acceptance Scenarios**:

1. **Given** a valid Claude `conversations.json` export file, **When** I call `stream_conversations()`, **Then** I receive an iterator of Conversation objects with mapped fields (uuid→id, name→title, created_at→datetime, chat_messages→messages).

2. **Given** a Claude export with empty conversation names, **When** I parse the file, **Then** conversations are returned with empty string titles (data integrity preserved).

3. **Given** a Claude export with ISO 8601 timestamps, **When** I parse the file, **Then** timestamps are converted to timezone-aware datetime objects.

4. **Given** a large Claude export file (1000+ conversations), **When** I stream conversations, **Then** memory usage remains constant (O(1) via streaming).

---

### User Story 2 - Claude Message Parsing (Priority: P1)

As a researcher, I want Claude messages parsed with the same Message model so that my analysis code works across both providers without modification.

**Why this priority**: Messages are the core content of conversations. Proper message parsing with correct role mapping is essential for any analysis or search functionality.

**Independent Test**: Can be fully tested by parsing a Claude export and verifying each message has correct field mappings and role normalization.

**Acceptance Scenarios**:

1. **Given** a Claude conversation with messages, **When** I access the messages, **Then** each message has correct field mappings (uuid→id, text→content, sender→role, created_at→timestamp).

2. **Given** a Claude message with sender "human", **When** the message is parsed, **Then** the role is normalized to "user".

3. **Given** a Claude message with sender "assistant", **When** the message is parsed, **Then** the role remains "assistant".

4. **Given** a Claude message with attachments or files, **When** the message is parsed, **Then** attachments are mapped to the images/attachments structure (same as OpenAI).

5. **Given** a malformed message entry, **When** parsing is attempted, **Then** the entry is skipped with a WARNING log and processing continues.

---

### User Story 3 - Claude Search Support (Priority: P1)

As a researcher, I want to search Claude conversations using the same SearchQuery interface so that I can use one codebase for both OpenAI and Claude providers.

**Why this priority**: Search is the primary use case for echomine. Without search capability, the adapter provides limited value beyond basic listing.

**Independent Test**: Can be fully tested by creating a SearchQuery with various filters and verifying results match expected conversations with correct relevance ranking.

**Acceptance Scenarios**:

1. **Given** a Claude export and a keyword search query, **When** I call `search()`, **Then** I receive ranked results using BM25 algorithm (same as OpenAI).

2. **Given** a search query with phrase matching, **When** searching Claude conversations, **Then** exact phrase matches are found and ranked appropriately.

3. **Given** a search query with date filters (from_date/to_date), **When** searching, **Then** only conversations within the date range are returned.

4. **Given** a search query with title_filter, **When** searching Claude conversations with empty titles, **Then** conversations are filtered correctly (empty titles match empty filter).

5. **Given** a search query with role_filter="user", **When** searching, **Then** only messages from human/user role are searched.

6. **Given** a search query with exclude_keywords, **When** searching, **Then** conversations containing excluded terms are filtered out.

7. **Given** a search query with match_mode="all", **When** searching with multiple keywords, **Then** only conversations containing ALL keywords are returned.

---

### User Story 4 - Claude Conversation Retrieval (Priority: P2)

As a researcher, I want to retrieve specific Claude conversations by ID so that I can export or analyze individual conversations.

**Why this priority**: Direct retrieval by ID is needed for export functionality and detailed conversation analysis, but requires parsing to work first.

**Independent Test**: Can be fully tested by calling `get_conversation_by_id()` with a known conversation UUID and verifying the correct conversation is returned.

**Acceptance Scenarios**:

1. **Given** a valid conversation UUID from a Claude export, **When** I call `get_conversation_by_id()`, **Then** the matching conversation is returned.

2. **Given** an invalid or non-existent conversation UUID, **When** I call `get_conversation_by_id()`, **Then** None is returned (not an exception).

3. **Given** a large Claude export, **When** retrieving a conversation by ID, **Then** memory usage remains constant (streaming approach).

---

### User Story 5 - Claude Message Retrieval (Priority: P2)

As a researcher, I want to retrieve specific messages by ID so that I can reference individual message context.

**Why this priority**: Message-level retrieval supports detailed analysis and cross-referencing, but is secondary to conversation-level operations.

**Independent Test**: Can be fully tested by calling `get_message_by_id()` with a known message UUID and verifying both the message and parent conversation are returned.

**Acceptance Scenarios**:

1. **Given** a valid message UUID, **When** I call `get_message_by_id()`, **Then** a tuple of (Message, Conversation) is returned.

2. **Given** a message UUID with optional conversation_id hint, **When** I call `get_message_by_id()`, **Then** the message is found more efficiently.

3. **Given** an invalid message UUID, **When** I call `get_message_by_id()`, **Then** None is returned.

---

### User Story 6 - Provider Auto-Detection (Priority: P2)

As a library consumer and CLI user, I want provider auto-detection so that the CLI can automatically use the correct adapter without manual flags.

**Why this priority**: Improves user experience by eliminating the need to specify provider explicitly, but requires both adapters to be working first.

**Independent Test**: Can be fully tested by providing different export files to the CLI and verifying the correct adapter is selected automatically.

**Acceptance Scenarios**:

1. **Given** a Claude export file (with `chat_messages` keys), **When** I run a CLI command without --provider flag, **Then** ClaudeAdapter is automatically selected.

2. **Given** an OpenAI export file (with `mapping` keys), **When** I run a CLI command without --provider flag, **Then** OpenAIAdapter is automatically selected.

3. **Given** an explicit `--provider claude` flag, **When** I run a CLI command, **Then** ClaudeAdapter is used regardless of file content.

4. **Given** an unrecognized export format, **When** I run a CLI command, **Then** a clear error message is displayed: "Unsupported export format. Expected OpenAI or Claude export JSON."

---

### Edge Cases

- What happens when a Claude conversation has zero messages? (Return conversation with empty messages list)
- How does system handle conversations with only assistant messages (no human messages)? (Parse normally, search may return no matches for role_filter="user")
- What happens when `content` blocks array is empty or missing? (Fall back to `text` field per FR-015b)
- What happens when message has only `tool_use`/`tool_result` blocks and no text blocks? (Content is empty string, message still parsed)
- How does system handle very long message content? (Same as OpenAI - no truncation at parse time)
- What happens when timestamp parsing fails? (Skip entry with WARNING, continue processing)

## Requirements *(mandatory)*

### Functional Requirements

#### Conversation Parsing (FR-001 to FR-010)

- **FR-001**: System MUST parse Claude export JSON files with root array structure (list of conversations)
- **FR-002**: System MUST map `uuid` field to conversation `id`
- **FR-003**: System MUST map `name` field to conversation `title`. Empty names MUST use "(No title)" placeholder to satisfy model validation (min_length=1). Display layer shows "(Untitled)" per FR-034
- **FR-004**: System MUST parse `created_at` ISO 8601 string to timezone-aware datetime
- **FR-005**: System MUST parse `updated_at` ISO 8601 string to timezone-aware datetime
- **FR-006**: System MUST map `chat_messages` array to conversation `messages` list
- **FR-007**: System MUST ignore `summary` field (no OpenAI equivalent, not stored)
- **FR-008**: System MUST ignore `account` field (internal metadata)
- **FR-009**: System MUST use ijson streaming for O(1) memory usage
- **FR-010**: System MUST handle empty conversations (zero messages) without error

#### Message Parsing (FR-011 to FR-020)

- **FR-011**: System MUST map message `uuid` field to message `id`
- **FR-012**: System MUST extract message content from `content` array blocks (not `text` field)
- **FR-013**: System MUST normalize `sender` field: "human" → "user", "assistant" → "assistant"
- **FR-014**: System MUST parse message `created_at` ISO 8601 string to `timestamp`
- **FR-015**: System MUST concatenate all `text`-type blocks from `content` array to form message content
- **FR-015a**: System MUST skip `tool_use` and `tool_result` blocks when extracting content (tool metadata not stored)
- **FR-015b**: System MUST fall back to `text` field if `content` array is empty or missing
- **FR-016**: System MUST map `attachments` and `files` arrays to ImageRef/attachment model
- **FR-017**: System MUST skip malformed message entries with WARNING log
- **FR-018**: System MUST continue processing after skipping malformed entries
- **FR-019**: System MUST handle messages without timestamps (use conversation created_at as fallback)
- **FR-020**: System MUST set `parent_id` to None for all messages (Claude uses linear structure, not tree)

#### Search Support (FR-021 to FR-035)

- **FR-021**: ClaudeAdapter MUST implement `search(file_path, query)` method returning `Iterator[SearchResult]`
- **FR-022**: System MUST support `keywords` search with BM25 ranking algorithm
- **FR-023**: System MUST support `phrases` for exact phrase matching
- **FR-024**: System MUST support `title_filter` for partial title matching
- **FR-025**: System MUST support `from_date` and `to_date` for date range filtering
- **FR-026**: System MUST support `min_messages` and `max_messages` for message count filtering
- **FR-027**: System MUST support `role_filter` to search only user or assistant messages
- **FR-028**: System MUST support `exclude_keywords` to filter out unwanted results
- **FR-029**: System MUST support `match_mode` ("all" or "any") for keyword matching logic
- **FR-030**: System MUST support `sort_by` and `sort_order` for result ordering
- **FR-031**: System MUST generate snippets from matched messages (same as OpenAI)
- **FR-032**: System MUST use same BM25 scoring formula as OpenAI adapter
- **FR-033**: System MUST return SearchResult with conversation, score, and matched_message_ids
- **FR-034**: System MUST handle empty titles in display as "(Untitled)" placeholder
- **FR-035**: System MUST support `limit` parameter to restrict result count

#### Conversation Retrieval (FR-036 to FR-040)

- **FR-036**: ClaudeAdapter MUST implement `get_conversation_by_id(file_path, id)` returning `Conversation | None`
- **FR-037**: System MUST search by `uuid` field from export
- **FR-038**: System MUST return None for non-existent conversation ID (not exception)
- **FR-039**: System MUST use streaming approach for O(1) memory
- **FR-040**: System MUST support both full UUID and partial ID matching (same as OpenAI): prefix match with minimum 4 characters, case-insensitive, returns first match if multiple conversations share prefix

#### Message Retrieval (FR-041 to FR-045)

- **FR-041**: ClaudeAdapter MUST implement `get_message_by_id(file_path, message_id, conversation_id=None)` returning `tuple[Message, Conversation] | None`
- **FR-042**: System MUST search by message `uuid` field
- **FR-043**: System MUST accept optional `conversation_id` hint for performance
- **FR-044**: System MUST return both message and parent conversation for context
- **FR-045**: System MUST return None for non-existent message ID

#### Provider Auto-Detection (FR-046 to FR-050)

- **FR-046**: CLI MUST auto-detect provider based on JSON schema structure
- **FR-047**: CLI MUST detect Claude format by presence of `chat_messages` key in conversation objects
- **FR-048**: CLI MUST detect OpenAI format by presence of `mapping` key in conversation objects
- **FR-049**: CLI MUST support `--provider` flag for explicit provider selection (values: "openai", "claude")
- **FR-050**: CLI MUST display clear error message for unrecognized export formats

#### Protocol Compliance (FR-051 to FR-055)

- **FR-051**: ClaudeAdapter MUST implement ConversationProvider protocol
- **FR-052**: ClaudeAdapter MUST be stateless (no __init__ parameters, no instance state)
- **FR-053**: ClaudeAdapter MUST use shared Conversation and Message models (no provider-specific subclasses)
- **FR-054**: ClaudeAdapter MUST follow same error handling patterns as OpenAI adapter
- **FR-055**: ClaudeAdapter MUST be exported from echomine package (`from echomine import ClaudeAdapter`)

### Key Entities

- **Conversation**: Represents a Claude chat session with id, title, created_at, updated_at, and messages. Maps directly from Claude export structure.
- **Message**: Represents a single message in a conversation with id, content, role (user/assistant), and timestamp. Normalized from Claude's "human"/"assistant" sender values.
- **SearchResult**: Contains matched conversation, relevance score, matched message IDs, and snippet. Same structure as OpenAI results.
- **ClaudeAdapter**: Stateless adapter implementing ConversationProvider protocol for Claude exports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Researchers can parse Claude exports with same API as OpenAI (`stream_conversations`, `search`, `get_conversation_by_id`)
- **SC-002**: Search operations complete within same performance envelope as OpenAI (< 30s for 10K conversations)
- **SC-003**: Memory usage remains constant regardless of Claude export size (O(1) streaming)
- **SC-004**: 100% of existing SearchQuery filters work identically for Claude exports
- **SC-005**: CLI auto-detects correct provider for 100% of valid export files
- **SC-006**: Zero code changes required in existing OpenAI adapter (backward compatible)
- **SC-007**: All CLI commands work transparently with both providers
- **SC-008**: Graceful degradation handles malformed entries without crashing (same as OpenAI)

## Assumptions

- Users have already unzipped their Claude data export and have `conversations.json` available
- Claude export format follows the official Anthropic export schema (uuid, name, chat_messages structure)
- The `content` array contains structured blocks; text-type blocks are concatenated for message content (`text` field is fallback only)
- Claude exports do not use tree/branching structure (messages are linear within each conversation)
- Timestamp strings are always in ISO 8601 format with timezone information
- The existing BM25 implementation and search infrastructure can be reused without modification

## Out of Scope

- Support for browser extension export formats (only official Claude export)
- ZIP file extraction (assume already unzipped)
- Model version tracking (not available in OpenAI exports, maintaining parity)
- Artifact extraction as first-class entities (may be future enhancement)
- Branch/regeneration handling (Claude exports appear linear)
- Real-time streaming from Claude API (file-based parsing only)
