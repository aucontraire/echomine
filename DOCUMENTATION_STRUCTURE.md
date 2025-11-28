# Echomine Documentation Structure

This document provides an overview of the echomine documentation organization and explains where to find (and where to add) different types of documentation.

## Documentation Philosophy

Echomine follows industry best practices from mature Python open-source projects (requests, click, flask, pytest, pydantic):

1. **Separate concerns**: Contributors vs Maintainers vs Users
2. **Version control everything**: All workflows tracked in git for transparency
3. **Progressive disclosure**: Quick start → Detailed guides → Reference
4. **Multiple formats**: Root-level markdown (discoverability) + mkdocs (deep dives)

---

## Quick Reference: Where to Document What

| What You're Documenting | Where It Goes | Format | Audience |
|-------------------------|---------------|--------|----------|
| Contribution workflow (setup, TDD, PR process) | CONTRIBUTING.md | Markdown | Contributors |
| Release process, PyPI publishing | MAINTAINING.md | Markdown | Maintainers |
| User-facing changes (releases) | CHANGELOG.md | Keep a Changelog | All users |
| Bug reports | .github/ISSUE_TEMPLATE/bug_report.yml | GitHub Forms | Contributors |
| Feature requests | .github/ISSUE_TEMPLATE/feature_request.yml | GitHub Forms | Contributors |
| PR checklist | .github/PULL_REQUEST_TEMPLATE.md | Markdown | Contributors |
| Development workflows (adding features, fixing bugs) | docs/development/workflows.md | Mkdocs | Contributors |
| Development overview | docs/development/index.md | Mkdocs | Contributors |
| Maintainer overview | docs/maintaining/index.md | Mkdocs | Maintainers |
| API docstrings (functions, classes) | Code (Google style) | Python | Developers |
| User guides (how to use library/CLI) | docs/library-usage.md, docs/cli-usage.md | Mkdocs | End users |
| API reference | docs/api/ (auto-generated) | Mkdocstrings | Developers |

---

## Directory Structure

```
echomine/
├── Root-Level Documentation (Git-tracked, high visibility)
│   ├── README.md                    # Project overview, quick start
│   ├── CONTRIBUTING.md              # Contributor guide (setup, TDD, testing, PR process)
│   ├── MAINTAINING.md               # Maintainer guide (releases, PyPI, dependencies)
│   ├── CHANGELOG.md                 # User-facing release notes (Keep a Changelog format)
│   └── LICENSE                      # MIT License
│
├── GitHub Templates (.github/)
│   ├── PULL_REQUEST_TEMPLATE.md    # PR checklist and metadata
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.yml          # Structured bug reports
│       ├── feature_request.yml     # Feature request template
│       └── question.yml            # Questions/help template
│
├── Documentation (docs/ - mkdocs)
│   ├── index.md                    # Documentation home page
│   ├── quickstart.md               # 5-minute quick start guide
│   ├── installation.md             # Installation instructions
│   ├── library-usage.md            # Library API usage guide
│   ├── cli-usage.md                # CLI usage guide
│   ├── architecture.md             # Architecture overview
│   ├── contributing.md             # Links to CONTRIBUTING.md
│   │
│   ├── development/                # Development guides (contributors)
│   │   ├── index.md               # Development overview
│   │   └── workflows.md           # Common dev workflows
│   │
│   ├── maintaining/                # Maintainer guides
│   │   └── index.md               # Maintainer overview (links to MAINTAINING.md)
│   │
│   └── api/                        # API reference (auto-generated from docstrings)
│       ├── index.md
│       ├── models/
│       ├── adapters/
│       ├── search/
│       └── cli/
│
├── Inline Documentation (src/)
│   └── All Python files have:
│       ├── Module docstrings      # Top of file, describe module purpose
│       ├── Class docstrings       # Google style with attributes, examples
│       ├── Function docstrings    # Args, returns, raises, examples
│       └── Type hints             # All functions, variables (mypy --strict)
│
└── Configuration
    ├── mkdocs.yml                  # Mkdocs configuration (nav structure)
    └── pyproject.toml              # Project metadata (PyPI description)
```

---

## Documentation Types and Guidelines

### 1. Root-Level Documentation (Git-tracked)

**Purpose**: High visibility, GitHub auto-surfaces these files

#### README.md
- **Audience**: Everyone (first impression)
- **Content**:
  - Project description (what/why)
  - Quick install: `pip install echomine`
  - 30-second usage example (library + CLI)
  - Links to full documentation
  - Badges (build status, coverage, PyPI version)
- **Keep it short**: 1-2 screens max, link to docs for details

#### CONTRIBUTING.md
- **Audience**: Contributors (open-source developers)
- **Content**:
  - Development setup (`pip install -e ".[dev]"`)
  - TDD workflow (RED-GREEN-REFACTOR)
  - Running tests, type checking, linting
  - Pre-commit hooks
  - PR process and commit message format
  - Code quality standards (mypy --strict, ruff)
  - Architecture principles
- **Style**: Comprehensive, example-heavy, step-by-step

#### MAINTAINING.md
- **Audience**: Maintainers only
- **Content**:
  - Release process (step-by-step)
  - PyPI publishing workflow
  - Versioning policy (semantic versioning)
  - Dependency management
  - Issue/PR triage
  - Security response process
  - Documentation deployment
- **Style**: Detailed checklists, commands, workflows

#### CHANGELOG.md
- **Audience**: All users (what changed in each version)
- **Format**: [Keep a Changelog](https://keepachangelog.com/)
- **Content**:
  - Unreleased (next version)
  - Each version with: Added, Changed, Deprecated, Removed, Fixed, Security
  - Date and version number
  - Links to GitHub releases
- **Update**: Every PR that affects users

### 2. GitHub Templates (.github/)

**Purpose**: Standardize contributions, collect necessary info

#### PULL_REQUEST_TEMPLATE.md
- Summary, changes, testing, checklist
- Constitution compliance checkboxes
- Pre-filled sections for consistency

#### ISSUE_TEMPLATE/*.yml
- Structured forms (not free-form)
- Required fields to ensure quality
- Automatic labeling
- Templates: bug_report, feature_request, question

### 3. Mkdocs Documentation (docs/)

**Purpose**: Deep-dive guides, searchable, version-able

#### User Guides
- **library-usage.md**: Library API usage with examples
- **cli-usage.md**: CLI commands, options, examples
- **quickstart.md**: 5-minute tutorial
- **architecture.md**: Design patterns, principles

#### Development Guides (docs/development/)
- **index.md**: Development overview, quick commands
- **workflows.md**: Step-by-step workflows (features, bugs, deps, docs)

#### Maintaining Guides (docs/maintaining/)
- **index.md**: Maintainer overview (links to MAINTAINING.md for details)

#### API Reference (docs/api/)
- **Auto-generated** from docstrings via mkdocstrings
- Update by improving docstrings in code
- Build: `mkdocs build` (regenerates from code)

### 4. Inline Documentation (Code)

**Purpose**: Explain code to developers reading source

#### Docstrings (Google Style)
```python
def function(arg1: str, arg2: int) -> list[str]:
    """One-line summary.

    Detailed explanation if needed. Multiple paragraphs OK.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: If arg1 is invalid

    Example:
        ```python
        result = function("value", 42)
        print(result)  # ['output']
        ```
    """
```

**Requirements**:
- All public classes, functions, methods
- Google style (compatible with mkdocstrings)
- Include examples for complex APIs
- Type hints in signature, not docstring

---

## Workflows: When to Update What

### Scenario: Adding a New Feature

1. **Before coding**: Read `specs/001-ai-chat-parser/spec.md`
2. **During development**: Follow `docs/development/workflows.md`
3. **In code**: Add docstrings to new functions/classes
4. **After coding**:
   - Update `docs/library-usage.md` (if public API)
   - Update `docs/cli-usage.md` (if CLI command)
   - Add to `CHANGELOG.md` under "Unreleased → Added"
5. **In PR**: Fill out `PULL_REQUEST_TEMPLATE.md`

### Scenario: Fixing a Bug

1. **Before fixing**: Create issue via `.github/ISSUE_TEMPLATE/bug_report.yml`
2. **During development**: Follow TDD workflow in `CONTRIBUTING.md`
3. **After fixing**:
   - Add to `CHANGELOG.md` under "Unreleased → Fixed"
   - Update docs if behavior documented incorrectly
4. **In PR**: Reference issue number, include regression test

### Scenario: Releasing a New Version

1. **Follow**: `MAINTAINING.md` → Release Process
2. **Update**:
   - `pyproject.toml` (version number)
   - `CHANGELOG.md` (move Unreleased to version section)
3. **Build and publish**: PyPI workflow in `MAINTAINING.md`
4. **Tag**: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. **GitHub release**: Copy CHANGELOG entry

### Scenario: Updating Documentation

1. **User guides**: Edit `docs/library-usage.md` or `docs/cli-usage.md`
2. **API reference**: Update docstrings in code, rebuild with `mkdocs build`
3. **Development guides**: Edit `docs/development/*.md`
4. **Contributor/maintainer guides**: Edit `CONTRIBUTING.md` or `MAINTAINING.md`
5. **Preview**: `mkdocs serve` (http://127.0.0.1:8000)
6. **Deploy** (maintainers): `mkdocs gh-deploy`

---

## Documentation Quality Standards

### All Documentation Must:

1. **Be accurate**: Verify examples actually work
2. **Be current**: Update when code changes
3. **Be clear**: Simple language, avoid jargon
4. **Be concise**: Respect reader's time
5. **Include examples**: Show, don't just tell
6. **Be scannable**: Headers, bullets, code blocks

### Docstrings Must:

- Follow Google style
- Include examples for non-trivial functions
- Match type hints (don't duplicate, just explain)
- Describe why, not just what
- Use present tense ("Returns", not "Will return")

### User Guides Must:

- Start with simplest use case
- Progress from basic to advanced
- Include complete, runnable examples
- Explain when/why to use features
- Link to API reference for details

### Workflow Docs Must:

- Provide step-by-step instructions
- Include actual commands to run
- Explain expected output
- Cover error cases and troubleshooting
- Use checklists for multi-step processes

---

## Building and Deploying Documentation

### Local Development

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build static site
mkdocs build

# Serve with live reload
mkdocs serve
# Visit: http://127.0.0.1:8000

# Check for broken links
# (No built-in tool, manually review or use external link checker)
```

### Deployment (Maintainers)

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy

# Verify at: https://echomine.github.io/echomine/
```

### Versioned Docs (Future)

Using `mike` for version-specific docs:

```bash
# Deploy docs for version 1.1
mike deploy 1.1 latest --update-aliases

# Set default version
mike set-default latest

# Push to GitHub Pages
mike deploy --push 1.1 latest
```

---

## Documentation Checklist for PRs

Before submitting PR:

- [ ] Code has docstrings (Google style) with examples
- [ ] User guide updated (if public API changed)
- [ ] CLI guide updated (if CLI changed)
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] Examples tested and working
- [ ] `mkdocs build` succeeds
- [ ] `mkdocs serve` shows changes correctly
- [ ] No broken internal links

---

## FAQs

### Q: Where do I document a new CLI command?

**A**: Three places:
1. **Docstring in code** (`src/echomine/cli/commands.py`)
2. **User guide** (`docs/cli-usage.md`)
3. **CHANGELOG.md** under "Added"

### Q: I fixed a bug. What docs need updating?

**A**:
1. **CHANGELOG.md** under "Fixed"
2. **User guide** (if documented behavior was wrong)
3. **Code comments** (if bug was due to unclear code)

### Q: How do I add a new development workflow?

**A**: Edit `docs/development/workflows.md` with step-by-step instructions and examples.

### Q: Where do I document the release process?

**A**: Already documented in `MAINTAINING.md`. Update that file if process changes.

### Q: How do I update the API reference?

**A**: Update docstrings in code, then run `mkdocs build`. API reference auto-generates from docstrings.

### Q: Should I document internal functions?

**A**: Yes, with docstrings, but they won't appear in public API reference (prefix with `_` for private).

---

## External Resources

- [Keep a Changelog](https://keepachangelog.com/) - CHANGELOG.md format
- [Semantic Versioning](https://semver.org/) - Versioning policy
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [mkdocs Documentation](https://www.mkdocs.org/)
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)

---

**Last Updated**: 2025-11-28
**Maintained By**: Echomine maintainers
