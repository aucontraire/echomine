# Test Fixtures

This directory contains test fixtures for echomine tests.

## Files

### Valid Fixtures

- **`sample_export.json`**: Sample OpenAI export with 10 conversations and ~20 messages total
  - Use for: Integration tests, contract tests, basic functionality validation
  - Size: Small (~5 KB)
  - Conversations: 10 (various topics)

- **`generate_large_export.py`**: Script to generate large export files
  - Use for: Performance benchmarks, memory efficiency tests, stress tests
  - Default: 10,000 conversations (performance baseline per CHK026)
  - Configurable: `--conversations` and `--messages-per-conversation` flags

### Malformed Fixtures (Error Handling Tests)

- **`malformed_invalid_json.json`**: Invalid JSON syntax (missing closing brace)
  - Tests: ParseError handling, fail-fast behavior
  - Expected: ParseError raised immediately

- **`malformed_missing_field.json`**: Missing required field (title)
  - Tests: ValidationError handling, graceful degradation
  - Expected: ValidationError raised or entry skipped (depending on operation)

- **`malformed_invalid_timestamp.json`**: Invalid timestamp format
  - Tests: Pydantic validation, type coercion failure
  - Expected: ValidationError with clear error message

## Usage

### In Tests

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_export_file() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_export.json"

def test_stream_conversations(sample_export_file: Path):
    adapter = OpenAIAdapter()
    conversations = list(adapter.stream_conversations(sample_export_file))
    assert len(conversations) == 10
```

### Generate Large Export

```bash
# Generate 10K conversations (performance baseline)
python tests/fixtures/generate_large_export.py --conversations 10000

# Generate 50K conversations (stress test)
python tests/fixtures/generate_large_export.py --conversations 50000 --messages-per-conversation 10

# Custom output path
python tests/fixtures/generate_large_export.py --output /tmp/huge_export.json --conversations 100000
```

## Performance Baselines

Per CHK026 and FR-444:
- **10,000 conversations**: Performance baseline for list operation (<5s)
- **50,000 messages**: Total messages for comprehensive testing
- **1GB+ file**: Stress test for memory efficiency validation

## Maintenance

When updating fixtures:
1. Update this README with changes
2. Regenerate large exports if schema changes
3. Add new malformed fixtures for new validation scenarios
4. Keep sample_export.json small and diverse (different conversation patterns)
