# Pre-Tasks Readiness Checklist: Claude Export Adapter

**Purpose**: Validate spec/plan requirements quality before `/speckit.tasks` generation. Combined Architecture Review + Pre-Tasks Readiness scope.
**Created**: 2025-12-08
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)
**Domains**: Streaming/Memory, Protocol Compliance, Data Mapping, CLI Integration, Test Coverage

**Delegation Key**: Items marked with `[Delegate: agent-name]` suggest which specialist agent should own validation.

---

## Requirement Completeness

- [x] CHK001 - Are all 55 FRs (FR-001 through FR-055) traceable to acceptance scenarios in the spec? [Completeness, Spec §Requirements] [Delegate: tdd-test-strategy-engineer]
- [x] CHK002 - Are streaming memory requirements (O(1) constraint) specified for all data access methods? [Completeness, Spec §FR-009, FR-039] [Delegate: streaming-parser-specialist]
- [x] CHK003 - Are error handling requirements defined for all parsing failure modes (invalid JSON, missing fields, invalid timestamps)? [Completeness, Spec §FR-017-018] [Delegate: streaming-parser-specialist]
- [x] CHK004 - Are protocol method signatures documented for `stream_conversations`, `search`, `get_conversation_by_id`, `get_message_by_id`? [Completeness, Plan §API Contracts] [Delegate: multi-provider-adapter-architect]
- [x] CHK005 - Are fixture requirements specified for all test categories (unit, integration, contract, performance)? [Completeness, Plan §Test Strategy] [Delegate: tdd-test-strategy-engineer]
- [x] CHK006 - Are content block extraction requirements complete for all block types (`text`, `tool_use`, `tool_result`)? [Completeness, Spec §FR-015, FR-015a] [Delegate: streaming-parser-specialist]
- [x] CHK007 - Are attachment/file mapping requirements specified for ImageRef compatibility? [Completeness, Spec §FR-016] [Delegate: pydantic-data-modeling-expert]

## Requirement Clarity

- [x] CHK008 - Is "O(1) memory" quantified with specific limits (e.g., <100MB working set per conversation)? [Clarity, Plan §Technical Context] [Delegate: performance-profiling-specialist]
- [x] CHK009 - Is the content block concatenation strategy explicitly specified (newline vs space join)? [Clarity, Plan §R-001] [Delegate: streaming-parser-specialist]
- [x] CHK010 - Is "partial ID matching" in FR-040 defined with specific matching rules (prefix, suffix, substring)? [Ambiguity, Spec §FR-040] [Delegate: search-ranking-engineer]
- [x] CHK011 - Are timestamp parsing requirements clear about timezone handling (preserve vs convert to UTC)? [Clarity, Spec §FR-004, FR-014] [Delegate: pydantic-data-modeling-expert]
- [x] CHK012 - Is "empty string titles" preservation vs "(Untitled)" display clearly separated between parse and display layers? [Clarity, Spec §FR-003, FR-034] [Delegate: cli-ux-designer]
- [x] CHK013 - Are BM25 scoring requirements clear about using "same formula as OpenAI adapter"? [Ambiguity, Spec §FR-032] [Delegate: search-ranking-engineer]

## Requirement Consistency

- [x] CHK014 - Are role normalization requirements consistent between spec (FR-013) and data-model.md mapping table? [Consistency, Spec §FR-013, data-model.md] [Delegate: pydantic-data-modeling-expert]
- [x] CHK015 - Are content extraction requirements consistent between spec (FR-012, FR-015) and research.md R-001? [Consistency] [Delegate: streaming-parser-specialist]
- [x] CHK016 - Are provider detection requirements consistent between spec (FR-046-048) and cli_spec.md? [Consistency] [Delegate: cli-ux-designer]
- [x] CHK017 - Are error message formats consistent between spec (FR-050) and cli_spec.md error messages section? [Consistency] [Delegate: cli-ux-designer]
- [x] CHK018 - Are timestamp parsing method requirements consistent (`datetime.fromisoformat()` vs `dateutil.parser.isoparse()`)? [Conflict, Plan §R-004 vs data-model.md] [Delegate: pydantic-data-modeling-expert]

## Protocol Compliance Requirements

- [x] CHK019 - Are `ConversationProvider` protocol method signatures explicitly documented in requirements? [Coverage, Spec §FR-051] [Delegate: multi-provider-adapter-architect]
- [x] CHK020 - Are statelessness requirements (no `__init__` params, no instance state) explicitly stated with validation criteria? [Clarity, Spec §FR-052] [Delegate: multi-provider-adapter-architect]
- [x] CHK021 - Are callback type requirements (`ProgressCallback`, `OnSkipCallback`) specified for all streaming methods? [Gap, library_api.md] [Delegate: multi-provider-adapter-architect]
- [x] CHK022 - Is the requirement to reuse shared models (`Conversation`, `Message`) testable? [Measurability, Spec §FR-053] [Delegate: python-strict-typing-enforcer]
- [x] CHK023 - Are protocol runtime-checkability requirements (`isinstance` check) documented? [Gap, library_api.md] [Delegate: multi-provider-adapter-architect]

## Data Mapping Requirements

- [x] CHK024 - Are all Claude→Echomine field mappings documented with transformation logic? [Completeness, data-model.md] [Delegate: pydantic-data-modeling-expert]
- [x] CHK025 - Are optional vs required field requirements clear for both Conversation and Message models? [Clarity, data-model.md] [Delegate: pydantic-data-modeling-expert]
- [x] CHK026 - Are metadata storage requirements defined (which Claude fields go to `metadata` dict)? [Completeness, data-model.md §Conversation Mapping] [Delegate: pydantic-data-modeling-expert]
- [x] CHK027 - Is fallback behavior for missing `content` array explicitly documented with decision tree? [Coverage, data-model.md] [Delegate: streaming-parser-specialist]
- [x] CHK028 - Are validation rules for malformed entries documented with skip conditions? [Completeness, data-model.md §Validation Rules] [Delegate: pydantic-data-modeling-expert]

## Streaming/Memory Requirements

- [x] CHK029 - Are ijson streaming patterns explicitly required (not just "use ijson")? [Clarity, Spec §FR-009] [Delegate: streaming-parser-specialist]
- [x] CHK030 - Are context manager requirements for file handle cleanup specified? [Gap, Plan] [Delegate: streaming-parser-specialist]
- [x] CHK031 - Are generator/iterator requirements consistent across all methods returning `Iterator[T]`? [Consistency, library_api.md] [Delegate: streaming-parser-specialist]
- [x] CHK032 - Are progress callback frequency requirements specified (every N items or N ms)? [Gap, library_api.md] [Delegate: streaming-parser-specialist]
- [x] CHK033 - Are memory usage test requirements quantified with specific thresholds? [Measurability, Plan §Test Strategy] [Delegate: performance-profiling-specialist]

## CLI Integration Requirements

- [x] CHK034 - Are auto-detection algorithm steps explicitly documented in requirements? [Completeness, cli_spec.md] [Delegate: cli-ux-designer]
- [x] CHK035 - Are `--provider` flag requirements documented for ALL CLI commands (list, search, get, export, stats)? [Coverage, Spec §FR-049] [Delegate: cli-ux-designer]
- [x] CHK036 - Are exit code requirements (0, 1, 2) defined for all error scenarios? [Completeness, cli_spec.md] [Delegate: cli-ux-designer]
- [x] CHK037 - Are stdout/stderr separation requirements consistent with Constitution Principle II? [Consistency] [Delegate: cli-ux-designer]
- [x] CHK038 - Are provider mismatch warning requirements (explicit flag vs detected) testable? [Measurability, cli_spec.md] [Delegate: cli-ux-designer]

## Test Coverage Requirements

- [x] CHK039 - Are test categories (unit, integration, contract, performance) defined with coverage targets? [Completeness, Plan §Test Strategy] [Delegate: tdd-test-strategy-engineer]
- [x] CHK040 - Are test fixture specifications complete (file names, content requirements, edge cases)? [Completeness, Plan §Test Fixtures Required] [Delegate: tdd-test-strategy-engineer]
- [x] CHK041 - Are contract test requirements mapped to specific FR ranges? [Traceability, Plan §Contract Tests] [Delegate: tdd-test-strategy-engineer]
- [x] CHK042 - Are performance benchmark requirements quantified (<30s for 10K conversations)? [Measurability, Spec §SC-002] [Delegate: performance-profiling-specialist]
- [x] CHK043 - Are TDD workflow requirements (RED-GREEN-REFACTOR) referenced in implementation phases? [Gap, Plan §Implementation Phases] [Delegate: tdd-test-strategy-engineer]

## Edge Case Coverage

- [x] CHK044 - Are zero-message conversation handling requirements explicitly defined? [Coverage, Spec §Edge Cases] [Delegate: streaming-parser-specialist]
- [x] CHK045 - Are empty `content` array fallback requirements testable? [Measurability, Spec §FR-015b] [Delegate: streaming-parser-specialist]
- [x] CHK046 - Are tool-only message (no text blocks) handling requirements defined? [Coverage, Spec §Edge Cases] [Delegate: streaming-parser-specialist]
- [x] CHK047 - Are malformed timestamp recovery requirements specified (fallback to conversation created_at)? [Coverage, Spec §FR-019] [Delegate: pydantic-data-modeling-expert]
- [x] CHK048 - Are missing required field skip-and-continue requirements documented? [Coverage, Spec §FR-017-018] [Delegate: streaming-parser-specialist]

## Acceptance Criteria Quality

- [x] CHK049 - Are all 8 Success Criteria (SC-001 through SC-008) measurable? [Measurability, Spec §Success Criteria] [Delegate: tdd-test-strategy-engineer]
- [x] CHK050 - Is "100% of SearchQuery filters work identically" (SC-004) testable? [Measurability, Spec §SC-004] [Delegate: search-ranking-engineer]
- [x] CHK051 - Is "zero code changes in OpenAI adapter" (SC-006) verifiable? [Measurability, Spec §SC-006] [Delegate: multi-provider-adapter-architect]
- [x] CHK052 - Is "CLI auto-detects correct provider for 100% of valid files" (SC-005) defined with test cases? [Measurability, Spec §SC-005] [Delegate: cli-ux-designer]

## Dependencies & Assumptions

- [x] CHK053 - Is the assumption "Claude exports do not use tree/branching" validated against real data? [Assumption, Spec §Assumptions] [Delegate: streaming-parser-specialist]
- [x] CHK054 - Is the assumption "timestamps always ISO 8601 with timezone" validated? [Assumption, Spec §Assumptions] [Delegate: pydantic-data-modeling-expert]
- [x] CHK055 - Are dependencies on existing BM25 implementation explicitly documented? [Dependency, Spec §Assumptions] [Delegate: search-ranking-engineer]
- [x] CHK056 - Are dependencies on existing `Conversation`/`Message` models documented with version requirements? [Dependency, Plan] [Delegate: pydantic-data-modeling-expert]

## Architecture Alignment

- [x] CHK057 - Does the plan structure align with Constitution Principle I (Library-First)? [Consistency, Plan §Constitution Check] [Delegate: software-architect]
- [x] CHK058 - Are all 8 Constitution Principles checked with PASS/FAIL status? [Completeness, Plan §Constitution Check] [Delegate: software-architect]
- [x] CHK059 - Are complexity violations tracked (currently "N/A" - is this accurate)? [Completeness, Plan §Complexity Tracking] [Delegate: software-architect]
- [x] CHK060 - Is module placement (`adapters/claude.py`) consistent with multi-provider pattern? [Consistency, Plan §Project Structure] [Delegate: software-architect]

---

## Summary

| Quality Dimension | Items | Delegation Coverage |
|-------------------|-------|---------------------|
| Completeness | 14 | All delegated |
| Clarity | 6 | All delegated |
| Consistency | 5 | All delegated |
| Protocol Compliance | 5 | multi-provider-adapter-architect |
| Data Mapping | 5 | pydantic-data-modeling-expert |
| Streaming/Memory | 5 | streaming-parser-specialist |
| CLI Integration | 5 | cli-ux-designer |
| Test Coverage | 5 | tdd-test-strategy-engineer |
| Edge Cases | 5 | streaming-parser-specialist |
| Acceptance Criteria | 4 | tdd-test-strategy-engineer |
| Dependencies | 4 | Various |
| Architecture | 4 | software-architect |

**Total Items**: 60
**Traceability**: 100% (all items reference spec section, plan section, or gap marker)

---

## Notes

- Check items off as completed: `[x]`
- Use `[Delegate: agent-name]` hints to route validation to specialist agents
- Items marked `[Gap]` indicate missing requirements that should be added to spec/plan
- Items marked `[Ambiguity]` or `[Conflict]` require clarification before task generation
- Run `/speckit.tasks` after all critical items are resolved
