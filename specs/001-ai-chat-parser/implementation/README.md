# Implementation Plans Directory

**Purpose**: Detailed, phase-specific implementation plans with architecture decisions, testing strategies, and checkpoint-based rollouts.

**Last Updated**: 2025-11-25

---

## Overview

This directory contains **deep-dive implementation plans** for complex features that require:
- Architecture decisions and trade-off analysis
- Phased rollouts with validation checkpoints
- Detailed task breakdowns with effort estimates
- Sub-agent coordination strategies
- Quality gate validation at each checkpoint

These plans complement the high-level [plan.md](../plan.md) and task-oriented [tasks.md](../tasks.md).

---

## Active Implementation Plans

### Phase 6: Export Conversation to Markdown ✅ COMPLETE
- **File**: [phase-6-export.md](phase-6-export.md)
- **Status**: ✅ Complete (Sub-Phases 6.1-6.4 delivered)
- **Effort**: 4 sub-phases over multiple sessions
- **Key Decisions**:
  - Golden master testing approach with 3 representative conversations
  - ImageRef model for multimodal content (images)
  - MarkdownExporter library-first design
  - CLI export command with title search and stdout/file output
- **Deliverables**:
  - `src/echomine/export/markdown.py` - MarkdownExporter class
  - `src/echomine/models/image.py` - ImageRef model
  - `src/echomine/cli/commands/export.py` - CLI export command
  - 31 comprehensive tests (20 contract + 11 integration + 5 golden master)
- **Quality Metrics**:
  - 207 total tests passing
  - 87.79% code coverage for MarkdownExporter
  - mypy --strict compliance verified
- **Lessons Learned**: See [phase-6-export.md § Lessons Learned](phase-6-export.md#lessons-learned)

---

## Planned Implementation Plans

### Phase 7: Filter Conversations by Date Range
- **File**: `phase-7-date-filtering.md` (not yet created)
- **Status**: ⏸️ Pending
- **Scope**: T080-T086 from [tasks.md](../tasks.md#phase-7)
- **Estimated Effort**: 2-3 sub-phases
- **Key Decisions Needed**:
  - Date parsing strategy (ISO 8601, natural language, multiple formats?)
  - Filter performance optimization for large exports
  - SearchQuery model extension vs new DateRangeQuery

### Phase 8: Polish & Cross-Cutting Concerns
- **File**: `phase-8-polish.md` (not yet created)
- **Status**: ⏸️ Pending
- **Scope**: T087-T097+ from [tasks.md](../tasks.md#phase-8)
- **Estimated Effort**: Multiple sub-phases (documentation, error handling, UX)
- **Key Decisions Needed**:
  - Documentation strategy (sphinx, mkdocs, or manual)
  - Error message templates and actionable guidance
  - CLI UX improvements (--help examples, suggested next steps)

---

## When to Create an Implementation Plan

**Create a detailed plan when**:
- Feature spans multiple sub-phases (>3 checkpoints)
- Architecture decisions require trade-off analysis
- Testing strategy needs design (golden master, property-based, benchmarks)
- Multiple sub-agents need coordination
- Effort estimate >10 hours or complexity is high

**Don't create a plan for**:
- Simple, single-step tasks (just implement directly)
- Bug fixes (use tasks.md with bug ticket reference)
- Minor refactoring (commit message is sufficient)

---

## Implementation Plan Template

Each implementation plan should include:

### 1. Header Metadata
- **Status**: In Progress / Complete / Deferred
- **Dependencies**: Prerequisites (e.g., "Phase 5 complete")
- **Estimated Effort**: Hours over sub-phases
- **Created/Updated/Completed**: Dates

### 2. Overview Section
- Goal statement
- Key decisions summary
- Quick navigation links

### 3. Architecture Decision(s)
- The question being decided
- Options considered (with pros/cons)
- Decision rationale
- Agent consensus (if applicable)

### 4. Testing Strategy
- Test pyramid breakdown (unit/integration/contract/performance)
- Coverage targets
- Test data strategy (fixtures, factories, property-based)

### 5. Sub-Phases (3-5 checkpoints)
Each sub-phase should have:
- **⏸️ CHECKPOINT N**: Goal statement
- **Duration**: Estimated hours
- **Tasks**: Detailed task breakdown with file changes
- **Deliverables**: Checklist of files to create/modify
- **Validation**: How to verify checkpoint success
- **Checkpoint Questions**: Gate for proceeding to next phase

### 6. File Changes Summary
- New files (count)
- Modified files (count)
- Fixture files (if applicable)

### 7. Success Criteria
- Functional requirements checklist
- Quality gates (tests, mypy, coverage, performance)
- Documentation requirements

### 8. Agent Coordination Matrix
| Agent | Role | Sub-Phases | Tasks |
|-------|------|------------|-------|
| ... | ... | ... | ... |

### 9. Lessons Learned
- What went well
- What could be improved
- Unexpected discoveries
- Architecture changes

### 10. References
- Links to parent plan, tasks, contracts, etc.

---

## Directory Structure

```
specs/001-ai-chat-parser/implementation/
├── README.md                  # This file (index and guidelines)
├── phase-6-export.md          # Phase 6 detailed plan (COMPLETE)
├── phase-7-date-filtering.md  # Phase 7 detailed plan (future)
└── phase-8-polish.md          # Phase 8 detailed plan (future)
```

---

## Related Documentation

- **High-Level Plan**: [../plan.md](../plan.md) - Overall project architecture and phases
- **Task Breakdown**: [../tasks.md](../tasks.md) - Complete task list with dependencies
- **Data Model Spec**: [../data-model.md](../data-model.md) - Pydantic model designs
- **CLI Contract**: [../contracts/cli_spec.md](../contracts/cli_spec.md) - CLI interface contract
- **Constitution**: [../plan.md#constitution](../plan.md#constitution-principles) - 8 non-negotiable principles

---

## Maintenance

- Update this README when new implementation plans are added
- Mark plans as COMPLETE with final metrics when done
- Keep "Lessons Learned" sections current for knowledge sharing
- Archive deprecated plans to `archived/` subdirectory

---

**Document Status**: Living index - updated when implementation plans change
**Next Update**: When Phase 7 implementation plan is created
