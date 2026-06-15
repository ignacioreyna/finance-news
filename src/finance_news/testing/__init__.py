"""Testing helpers for fixtures and snapshots."""

from __future__ import annotations

from finance_news.testing.fixtures import (
    get_fixtures_base,
    load_fixture_bytes,
    load_fixture_json,
    load_fixture_text,
)
from finance_news.testing.snapshots import (
    assert_source_items_match,
    compare_snapshots,
    normalize_source_item,
)

__all__ = [
    # Fixture helpers
    "get_fixtures_base",
    "load_fixture_bytes",
    "load_fixture_text",
    "load_fixture_json",
    # Snapshot helpers
    "normalize_source_item",
    "compare_snapshots",
    "assert_source_items_match",
]