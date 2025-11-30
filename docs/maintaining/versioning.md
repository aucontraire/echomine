# Versioning Policy

Echomine follows [Semantic Versioning 2.0.0](https://semver.org/) (SemVer).

## Version Format

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug fixes (backward compatible)
  │     └──────── New features (backward compatible)
  └────────────── Breaking changes
```

**Example**: `1.2.3`
- Major: 1
- Minor: 2
- Patch: 3

## When to Increment

### PATCH (1.0.0 → 1.0.1)

Increment for **backward-compatible bug fixes**:

- Fix crashes or errors
- Fix incorrect behavior
- Security patches
- Performance improvements (same API)
- Documentation fixes

**Examples**:
- Fix: search returning wrong results for date filters
- Fix: crash when export has null timestamps
- Fix: memory leak in streaming parser

### MINOR (1.0.0 → 1.1.0)

Increment for **backward-compatible new features**:

- New functions or methods
- New optional parameters
- New CLI commands or flags
- Deprecations (old API still works)

**Examples**:
- Add: `--title` flag to search command
- Add: `export_to_html()` function
- Add: Claude adapter support
- Deprecate: `--keywords-only` (replaced by `--title`)

### MAJOR (1.0.0 → 2.0.0)

Increment for **breaking changes**:

- Remove functions or methods
- Change function signatures (required params)
- Change return types
- Change default behavior
- Remove deprecated features

**Examples**:
- Remove: deprecated `search_legacy()` function
- Change: `search()` returns `Iterator` instead of `List`
- Change: `--output` is now required for export command
- Change: minimum Python version from 3.11 to 3.12

## Backward Compatibility

### What is Backward Compatible?

Changes that don't break existing code:

```python
# v1.0.0 - Original
def search(path: Path, query: SearchQuery) -> Iterator[SearchResult]:
    pass

# v1.1.0 - Backward compatible (new optional param)
def search(
    path: Path,
    query: SearchQuery,
    *,
    progress_callback: Optional[Callable] = None,  # New, optional
) -> Iterator[SearchResult]:
    pass
```

### What is NOT Backward Compatible?

Changes that break existing code:

```python
# v1.0.0 - Original
def search(path: Path, query: SearchQuery) -> list[SearchResult]:
    pass

# v2.0.0 - Breaking (return type changed)
def search(path: Path, query: SearchQuery) -> Iterator[SearchResult]:
    pass
```

## Pre-Release Versions

For testing before stable release:

```
1.0.0-alpha.1  # Early development
1.0.0-beta.1   # Feature complete, testing
1.0.0-rc.1     # Release candidate
1.0.0          # Stable release
```

### Usage

```bash
# Install pre-release
pip install echomine==1.0.0-beta.1

# Install stable only (default)
pip install echomine
```

## Development Versions

For local development:

```
1.0.0.dev1     # Development snapshot
1.0.0.dev2     # Later snapshot
```

These are never published to PyPI.

## Version in Code

Version is defined in `pyproject.toml`:

```toml
[project]
name = "echomine"
version = "1.2.0"
```

Access programmatically:

```python
from importlib.metadata import version

echomine_version = version("echomine")
print(f"Echomine {echomine_version}")
```

Or via CLI:

```bash
echomine --version
# echomine 1.2.0
```

## Deprecation Policy

### How to Deprecate

1. **Mark as deprecated** with warning:

```python
import warnings

def old_function():
    """Old function.

    .. deprecated:: 1.2.0
        Use :func:`new_function` instead.
    """
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_function()
```

2. **Document in CHANGELOG**:

```markdown
### Deprecated
- `old_function()` - Use `new_function()` instead. Will be removed in v2.0.0.
```

3. **Keep working** for at least one minor version

4. **Remove** in next major version

### Deprecation Timeline

```
v1.0.0: Function introduced
v1.1.0: Function deprecated (still works, emits warning)
v1.2.0: Function still works (minimum one minor version)
v2.0.0: Function removed
```

## API Stability

### Stable (Public) API

Everything documented in:
- API Reference documentation
- README examples
- CLI `--help` output

**Stability guarantee**: Follow SemVer strictly.

### Unstable (Internal) API

- Functions/classes prefixed with `_`
- Modules in `_internal/` directories
- Anything not documented

**No stability guarantee**: May change without notice.

```python
# Stable - follows SemVer
from echomine import OpenAIAdapter, SearchQuery

# Unstable - may change anytime
from echomine._internal import _parse_raw_message
```

## Python Version Support

### Policy

Support Python versions that are:
- Not end-of-life (EOL)
- At least 12 months old (for ecosystem stability)

### Current Support

| Python | Status | Notes |
|--------|--------|-------|
| 3.12+ | Supported | Minimum version |
| 3.11 | Not supported | Missing required features |
| 3.10 | Not supported | Missing required features |

### Dropping Python Versions

Dropping a Python version is a **major** version bump:

```
echomine 1.x: Python 3.12+
echomine 2.x: Python 3.13+ (hypothetical)
```

## Version Comparison

Users can compare versions:

```python
from packaging.version import Version

current = Version("1.2.0")
required = Version("1.1.0")

if current >= required:
    print("Version OK")
```

## FAQ

### When should I use a pre-release?

For significant changes that need community testing before stable release.

### Can I skip version numbers?

Yes. Version numbers don't need to be sequential:
- 1.0.0 → 1.0.5 is fine (skipped 1.0.1-1.0.4)
- 1.2.0 → 2.0.0 is fine (skipped 1.3.0+)

### What about 0.x versions?

For initial development before first stable release:
- 0.x.y: Anything may change at any time
- Breaking changes don't require major bump

Once you release 1.0.0, commit to SemVer.

### How do I handle urgent security fixes?

Release a patch version immediately:
1. Fix on a hotfix branch
2. Increment patch version
3. Release ASAP

## Next Steps

- [Release Process](release-process.md): How to release
- [PyPI Publishing](pypi-publishing.md): Publishing setup

---

**Last Updated**: 2025-11-30
