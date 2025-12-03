# Feature Backlog - AI Chat Parser

**Feature**: Echomine AI Chat Parser
**Version**: 1.0.0 (current release scope)
**Last Updated**: 2025-11-22

## Overview

This document tracks functional requirements that are explicitly deferred to post-v1.0 releases. These FRs are documented in spec.md but intentionally have no tasks in tasks.md for the v1.0 release.

---

## Post-v1.0 Extensibility Features

### FR-191-192: CI/Contract Testing Extensibility

**Scope**: Automated testing infrastructure for multi-adapter systems

- **FR-191**: CI pipeline MUST run contract tests against ALL adapters and fail build on any failures
- **FR-192**: New adapter implementations MUST be added to contract test parametrization (via pytest.mark.parametrize)

**Status**: Deferred (implement when second adapter is added)

**Rationale**: v1.0 only supports OpenAI adapter. Multi-adapter contract testing becomes relevant when we add Anthropic, Google, or other providers.

---

### FR-193-201: Protocol Versioning & Evolution

**Scope**: Adapter protocol backward compatibility and capability detection

- **FR-193**: Protocol changes MUST follow semantic versioning strictly (MAJOR for breaking, MINOR for additions)
- **FR-194**: Adding required parameters to protocol methods MUST trigger MAJOR version bump
- **FR-195**: New protocol methods MUST be optional (provide default implementation or make optional via Union[...])
- **FR-196**: Protocol breaking changes MUST be documented in CHANGELOG with migration guide
- **FR-197**: Library MUST maintain protocol version constant (e.g., `echomine.PROTOCOL_VERSION = "1.0"`)
- **FR-198**: Library v1.0 MUST NOT implement adapter capability detection
- **FR-199**: ALL v1.0 adapters MUST implement full protocol (no partial implementations)
- **FR-200**: Future capability system (v2.0+) MAY use Flag enum for feature detection
- **FR-201**: If capability detection added, adapters MUST declare capabilities via class constant (not runtime detection)

**Status**: Guidelines documented, capability detection deferred to v2.0+

**Rationale**: v1.0 protocol is simple and stable. Capability detection adds complexity without current need. We'll implement when adapters diverge in feature support.

---

### FR-202-205: Search Filter Extensibility

**Scope**: Adding new search filters in future releases

- **FR-202**: New search filters MUST be added as optional fields with default values (backward compatible)
- **FR-203**: Adding new filters MUST trigger MINOR version bump (not MAJOR)
- **FR-204**: Adapters MAY ignore unknown filters (fail gracefully, don't raise exceptions)
- **FR-205**: Documentation MUST specify which filters are supported by each adapter version

**Status**: Guidelines documented, no new filters planned for v1.0

**Rationale**: v1.0 filters (keywords, title, date range, limit) are sufficient for MVP. Future filters (e.g., participant, sentiment, language) can be added without breaking changes.

---

### FR-206-209: Plugin Architecture

**Scope**: Third-party adapter discovery and registration

- **FR-206**: Library v1.0 MUST NOT implement plugin discovery or adapter registry
- **FR-207**: Adapters MUST be importable as explicit classes (e.g., `from echomine import OpenAIAdapter`)
- **FR-208**: Future plugin system (v2.0+) MAY use entry points for third-party adapters
- **FR-209**: Plugin architecture (if added) MUST NOT break explicit imports (backward compatible)

**Status**: Deferred to v2.0+ when third-party adapters exist

**Rationale**: Explicit imports are simpler and sufficient for v1.0. Plugin discovery adds complexity without current ecosystem demand. We'll revisit when community adapters emerge.

---

### FR-210-214: Custom Ranking Algorithms

**Scope**: Pluggable scoring algorithms for search results

- **FR-210**: Library v1.0 MUST use TF-IDF for keyword ranking (no alternatives)
- **FR-211**: TF-IDF implementation MUST be tested for correctness (contract test)
- **FR-212**: Future custom ranking algorithms (v2.0+) MAY be added as optional parameters
- **FR-213**: Custom scorers (if added) MUST implement RankingAlgorithm protocol with calculate_score method
- **FR-214**: Default ranking algorithm MUST remain TF-IDF (backward compatible)

**Status**: TF-IDF hardcoded in v1.0, pluggable scorers deferred to v2.0+

**Rationale**: TF-IDF is proven and sufficient for most use cases. Custom scoring (BM25, semantic similarity, LLM-based) adds complexity. We'll implement when users request specific ranking needs.

---

## Version Planning

### v1.0 (Current Release)
- User Stories 0-4: List, Search, Library, Export, Date Filtering
- Single adapter: OpenAI ChatGPT exports
- Fixed TF-IDF ranking
- Explicit imports only

### v2.0+ (Future)
- Multi-adapter contract testing (FR-191-192)
- Adapter capability detection (FR-198, FR-200-201)
- Plugin architecture for third-party adapters (FR-206, FR-208-209)
- Custom ranking algorithms (FR-212-213)
- Additional search filters as needed (FR-202-205)

---

## Contributing

When adding new features to spec.md that are deferred to post-v1.0:

1. Document the FR in spec.md with clear "(v2.0+)" or "(future)" markers
2. Add the FR to this backlog.md with rationale
3. Do NOT create tasks in tasks.md for deferred features
4. Update version planning section with target release

This ensures we capture good ideas without scope creep in current release.
