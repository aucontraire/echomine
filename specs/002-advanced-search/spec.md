# Feature Specification: Advanced Search Enhancement Package

**Feature Branch**: `002-advanced-search`
**Created**: 2025-12-03
**Status**: Draft
**Input**: User description: "Search Enhancement Package: Exact phrase matching, boolean AND/OR logic, exclude keywords, role filtering, and message context snippets for echomine CLI and library"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exact Phrase Matching (Priority: P1)

As a researcher analyzing my ChatGPT history, I want to search for exact phrases like "algo-insights" without tokenization splitting on hyphens, so that I can find conversations mentioning specific project names, technical terms, or multi-word concepts exactly as written.

**Why this priority**: This is the most requested feature addressing the core pain point where hyphenated terms and multi-word phrases are incorrectly tokenized, causing irrelevant results. Without this, users cannot reliably find specific project names or technical terms.

**Independent Test**: Can be fully tested by searching for a known hyphenated project name (e.g., "algo-insights") and verifying only conversations containing that exact string are returned.

**Acceptance Scenarios**:

1. **Given** an export file containing conversations with "algo-insights" and "algorithm insights" (separate words), **When** user runs `echomine search export.json --phrase "algo-insights"`, **Then** only conversations containing the exact string "algo-insights" are returned (not "algorithm insights").

2. **Given** an export file with mixed case occurrences ("Algo-Insights", "algo-insights"), **When** user runs phrase search, **Then** all case variations are matched (case-insensitive).

3. **Given** a user wants to search for multiple phrases, **When** user runs `echomine search export.json --phrase "algo-insights" --phrase "data pipeline"`, **Then** conversations containing either phrase are returned.

4. **Given** a user wants to combine phrases with keywords, **When** user runs `echomine search export.json -k "python" --phrase "algo-insights"`, **Then** conversations matching the keyword OR the phrase are returned (default behavior).

---

### User Story 2 - Boolean Match Mode (Priority: P1)

As a user searching for conversations about specific topics, I want to require ALL keywords to be present (AND) instead of ANY keyword (OR), so that I can narrow results to conversations that discuss multiple related concepts together.

**Why this priority**: Tied with P1 as it addresses precision vs. recall trade-off. Current OR-only logic returns too many results when searching for multiple terms. AND mode is essential for focused research.

**Independent Test**: Can be tested by searching for two common terms with --match-mode all and verifying only conversations containing BOTH terms are returned.

**Acceptance Scenarios**:

1. **Given** an export file with conversations about "python" only, "async" only, and both "python" and "async", **When** user runs `echomine search export.json -k "python" -k "async" --match-mode all`, **Then** only conversations containing BOTH "python" AND "async" are returned.

2. **Given** a user runs a search without specifying match mode, **When** the search executes, **Then** the default behavior is "any" (OR logic) preserving backward compatibility.

3. **Given** a user specifies `--match-mode any` explicitly, **When** the search executes, **Then** conversations matching ANY keyword are returned (current behavior).

4. **Given** a user combines `--match-mode all` with phrases, **When** searching, **Then** ALL specified keywords AND phrases must be present in the conversation.

---

### User Story 3 - Exclude Keywords (Priority: P2)

As a user refining search results, I want to exclude conversations containing certain terms, so that I can filter out irrelevant results (e.g., find "python" discussions but exclude "django").

**Why this priority**: High value for result refinement but less critical than core matching improvements. Users can work around this by manually filtering, but exclusion saves significant time.

**Independent Test**: Can be tested by searching for a common term while excluding another, verifying no results contain the excluded term.

**Acceptance Scenarios**:

1. **Given** an export file with conversations about "python with django" and "python with flask", **When** user runs `echomine search export.json -k "python" --exclude "django"`, **Then** only conversations without "django" are returned.

2. **Given** a user wants to exclude multiple terms, **When** user runs `echomine search export.json -k "python" --exclude "django" --exclude "flask"`, **Then** conversations containing NEITHER "django" NOR "flask" are returned.

3. **Given** exclusion is applied, **When** a conversation matches keywords but also contains excluded terms, **Then** that conversation is removed from results before ranking.

---

### User Story 4 - Filter by Message Role (Priority: P2)

As a user analyzing my conversation patterns, I want to search only within my messages (user) or only AI responses (assistant), so that I can find what I asked about or what the AI recommended.

**Why this priority**: Valuable for distinguishing between user questions and AI responses, but many users search both roles together. Lower priority than core search improvements.

**Independent Test**: Can be tested by searching with --role user and verifying all matched text is from user messages only.

**Acceptance Scenarios**:

1. **Given** a conversation where user asked about "refactoring" and assistant responded with "refactoring" advice, **When** user runs `echomine search export.json -k "refactoring" --role user`, **Then** only the user's messages mentioning "refactoring" contribute to the match.

2. **Given** a user wants to find AI recommendations, **When** user runs `echomine search export.json -k "recommend" --role assistant`, **Then** only assistant messages are searched.

3. **Given** a user omits the role filter, **When** search executes, **Then** all messages (user, assistant, system) are searched (current behavior).

4. **Given** system messages exist in some conversations, **When** user runs `--role system`, **Then** only system messages are searched.

---

### User Story 5 - Message Context Snippets (Priority: P3)

As a user reviewing search results, I want to see a snippet of the matched text in the CLI output, so that I can quickly assess relevance without opening each conversation.

**Why this priority**: Improves user experience but is not essential for core search functionality. Users can still use the tool effectively without snippets by examining full conversations.

**Independent Test**: Can be tested by running a search and verifying the CLI output includes a text snippet column showing matched content.

**Acceptance Scenarios**:

1. **Given** a search returns results, **When** displayed in human-readable format, **Then** each result shows the first ~100 characters of the first matched message.

2. **Given** a matched message is longer than 100 characters, **When** displayed, **Then** the snippet is truncated with "..." at the end.

3. **Given** a conversation has multiple matched messages, **When** displayed, **Then** only the first match snippet is shown with a count indicator (e.g., "+3 more matches").

4. **Given** a user requests JSON output, **When** `--json` flag is used, **Then** the output includes a `snippet` field in addition to existing `matched_message_ids`.

---

### Edge Cases

- What happens when a phrase contains only special characters (e.g., `--phrase "---"`)? System should handle gracefully with no matches or appropriate error.
- How does the system handle empty exclude list? Same as not using exclude (no filtering applied).
- What if `--match-mode all` is used with no keywords or phrases? System should return an error indicating at least one search term is required.
- How are role filters handled when a conversation has no messages of that role? Conversation is excluded from results.
- What happens when snippet extraction fails (malformed message content)? Show "[Content unavailable]" as fallback.
- What if a phrase is also a substring of a longer word? Phrases use substring matching for simplicity (e.g., "log" WILL match in "catalog"). Users should use more specific phrases if needed (e.g., "log error" instead of "log"). This trade-off follows Constitution Principle V (Simplicity).

## Requirements *(mandatory)*

### Functional Requirements

#### Phrase Matching
- **FR-001**: System MUST support `--phrase` CLI flag accepting a string to match exactly (no tokenization)
- **FR-002**: System MUST allow multiple `--phrase` flags in a single search command
- **FR-003**: Phrase matching MUST be case-insensitive (consistent with keyword search)
- **FR-004**: Phrases MUST be combinable with keywords (`-k` and `--phrase` together)
- **FR-005**: Library API MUST accept `phrases: list[str] | None` in SearchQuery model
- **FR-006**: Phrases with special characters (hyphens, underscores, dots) MUST be matched literally

#### Boolean Match Mode
- **FR-007**: System MUST support `--match-mode` CLI flag with values "all" or "any"
- **FR-008**: Default match mode MUST be "any" to preserve backward compatibility
- **FR-009**: When match mode is "all", ALL keywords AND phrases MUST be present in conversation
- **FR-010**: When match mode is "any", ANY keyword OR phrase match returns the conversation
- **FR-011**: Library API MUST accept `match_mode: Literal["all", "any"]` in SearchQuery model with default "any"

#### Exclude Keywords
- **FR-012**: System MUST support `--exclude` CLI flag for terms to exclude
- **FR-013**: Multiple `--exclude` flags MUST be supported
- **FR-014**: Exclusion MUST be applied after keyword/phrase matching but before ranking
- **FR-015**: Excluded terms MUST use the same tokenization as regular keywords
- **FR-016**: Library API MUST accept `exclude_keywords: list[str] | None` in SearchQuery model

#### Role Filtering
- **FR-017**: System MUST support `--role` CLI flag with values "user", "assistant", or "system"
- **FR-018**: Role filter MUST be applied before keyword/phrase matching
- **FR-019**: Omitting `--role` MUST search all message roles (current behavior)
- **FR-020**: Library API MUST accept `role_filter: Literal["user", "assistant", "system"] | None` in SearchQuery model

#### Message Snippets
- **FR-021**: CLI human-readable output MUST include a snippet column showing matched text
- **FR-022**: Snippets MUST be truncated to approximately 100 characters with "..." suffix
- **FR-023**: Multiple matches MUST show first match with count indicator (e.g., "+3 more")
- **FR-024**: JSON output MUST include `snippet` field in each search result
- **FR-025**: Snippet extraction MUST gracefully handle malformed content with fallback text

#### General
- **FR-026**: All new features MUST maintain streaming/memory-efficient processing
- **FR-027**: All new SearchQuery fields MUST be optional with sensible defaults
- **FR-028**: Existing search queries without new parameters MUST work unchanged (backward compatibility)

### Key Entities

- **SearchQuery**: Extended with new optional fields: `phrases`, `match_mode`, `exclude_keywords`, `role_filter`
- **SearchResult**: Extended with `snippet` field containing matched text excerpt
- **Message**: Existing entity, role field used for role filtering

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find exact hyphenated project names (e.g., "algo-insights") with 100% precision (no false positives from tokenization)
- **SC-002**: Search with `--match-mode all` reduces average result count by at least 50% compared to default OR mode (when using 2+ keywords)
- **SC-003**: Search performance remains under 30 seconds for 1.6GB export files (existing performance maintained)
- **SC-004**: All new CLI flags work without breaking existing search commands (100% backward compatibility)
- **SC-005**: Users can assess result relevance from snippet preview without opening conversations in 80% of cases
- **SC-006**: Memory usage remains constant regardless of file size when using new features

### SC-005 Validation Approach

**Criterion**: Users can assess result relevance from snippet preview without opening conversations in 80% of cases

**Measurement Strategy**: Qualitative/UX metric, validated through:
1. **Dogfooding**: Development team uses snippets on real exports during testing
2. **Heuristic Proxy**: Snippet contains at least one matched keyword (automated check in T047)
3. **User Feedback**: Post-release feedback from cognivault integration users

**Why Not Fully Automated**: Relevance assessment is subjective; 80% threshold requires user study (out of scope for library-first tool).

**Acceptance Gate**: If dogfooding reveals snippets consistently miss matched text, revisit extract_snippet() logic.

## Assumptions

- Users are familiar with basic search concepts (AND/OR logic, exclusion)
- Export files follow the existing OpenAI conversation format
- Role values in messages are normalized to "user", "assistant", or "system"
- Phrase matching does not require fuzzy/approximate matching (exact string only)
- Snippet length of ~100 characters is sufficient for relevance assessment
