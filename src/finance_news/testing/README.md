# Testing Helpers: Fixtures and Snapshots

This module provides offline testing helpers for loading fixtures and comparing `SourceItem` snapshots in a deterministic way.

## Fixture Naming Convention

Place fixture files under `tests/fixtures/<connector>/` using the following naming pattern:

```
YYYY-MM-DD__source__case.ext
```

Or when date is not the best discriminator:

```
source__case__variant.ext
```

Examples:
- `2024-07-11__bcra__A8060.txt`
- `2024-06-12__bora__listing.html`
- `page-01.html`
- `empty.json`

## Loading Fixtures

```python
from finance_news.testing import load_fixture_text, load_fixture_bytes, load_fixture_json

# Load text fixture (default UTF-8)
html = load_fixture_text("bora_financial", "listing_20260612.html")

# Load raw bytes
pdf_bytes = load_fixture_bytes("bcra_comunicaciones_a", "A8060.txt")

# Load JSON fixture
snapshot = load_fixture_json("my_connector", "snapshot.json")
```

## Comparing SourceItem Snapshots

```python
from finance_news.testing import assert_source_items_match

# Compare two SourceItem objects with readable diff on failure
assert_source_items_match(actual_item, expected_item)
```

## Environment Variables

- `FINANCE_NEWS_FIXTURES_BASE`: Override the default fixtures base directory.

## Implementation Notes

- All fixture loading is offline-only; no network requests are made.
- Snapshot comparison is deterministic: dictionaries are sorted, lists compared in order, and datetime fields use stable ISO format.
- Diffs show exact field paths and values for easy debugging.