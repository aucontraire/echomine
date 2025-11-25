# Golden Master Test Fixtures

This directory contains golden master conversations used to validate the markdown export functionality.

## Structure

Each golden master directory (`001_simple_text`, `002_with_images`, `003_with_code`) contains:

| File | Purpose | Used in Tests? |
|------|---------|----------------|
| `raw.json` | Original OpenAI conversation export | ✅ Yes - Input for export |
| `expected.md` | Expected markdown output (ground truth) | ✅ Yes - Validation target |
| `reference.html` | How chat.html renders this conversation | ❌ No - Documentation only |

## Golden Masters

### 001_simple_text
- **Conversation**: "Indigenous DNA in Mexico"
- **Characteristics**: Simple text-only conversation, 2 user-assistant turns
- **Tests**: Basic message ordering, timestamps, role headers

### 002_with_images
- **Conversation**: "Interpretación pintura surrealista"
- **Characteristics**: Multimodal content with image attachment
- **Tests**: Image reference handling, multimodal parsing

### 003_with_code
- **Conversation**: "Gmail API Management in Java"
- **Characteristics**: Multiple messages with code blocks
- **Tests**: Code content handling, longer conversations

## Usage

Golden master tests are in `tests/integration/test_golden_master.py`:

```python
# Tests validate that MarkdownExporter produces output matching expected.md
def test_simple_text_conversation(golden_master_001):
    raw_path, expected_path = golden_master_001
    exporter = MarkdownExporter()
    actual_md = exporter.export(raw_path)
    expected_md = expected_path.read_text()
    assert actual_md == expected_md
```

## Expected Markdown Format

All `expected.md` files follow this format:

```markdown
## 👤 User · 2025-10-15T04:37:46+00:00

Message content here...

---

## 🤖 Assistant · 2025-10-15T04:38:12+00:00

Response content here...
```

### Format Requirements
- Headers with emoji: `## 👤 User` or `## 🤖 Assistant`
- ISO 8601 timestamps: `YYYY-MM-DDTHH:MM:SS+00:00`
- Message separators: `---` (horizontal rule)
- Images: `![Image](file-id-sanitized.png)` markdown syntax
- NO blockquotes for user messages

## Reference HTML Files

The `reference.html` files show how OpenAI's `chat.html` renders each conversation. These are **for manual reference only** and are not used in automated tests.

### Why Reference HTML?
1. **Manual verification** - Compare our markdown against actual chat.html output
2. **Documentation** - Understand the ground truth source format
3. **Future validation** - Cross-reference if needed

### HTML Structure Notes
- Images: `[File]: <a href="file-id-filename.jpeg">...</a>`
- Code blocks: XML entities escaped (`&lt;`, `&gt;`, `&amp;`)
- Messages: `<pre class="message">` with `<div class="author">user|ChatGPT</div>`

## Maintenance

When adding new golden masters:
1. Extract `raw.json` from OpenAI export
2. Generate `expected.md` using the format above (or run exporter and verify manually)
3. Optionally save HTML snippet from chat.html to `reference.html`
4. Update this README with new golden master description
5. Add test fixtures in `test_golden_master.py`
