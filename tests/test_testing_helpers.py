from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors.models import (
    Freshness,
    Provenance,
    SourceItem,
)
from finance_news.testing import (
    assert_source_items_match,
    compare_snapshots,
    get_fixtures_base,
    load_fixture_bytes,
    load_fixture_json,
    load_fixture_text,
    normalize_source_item,
)


class FixtureHelpersTests(unittest.TestCase):
    def test_get_fixtures_base_default(self) -> None:
        """Test default fixtures base path resolution."""
        fixtures_base = get_fixtures_base()
        self.assertTrue(fixtures_base.exists())
        self.assertEqual(fixtures_base.name, "fixtures")

    def test_get_fixtures_base_env_var(self) -> None:
        """Test fixtures base path from environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original = os.environ.get("FINANCE_NEWS_FIXTURES_BASE")
            try:
                os.environ["FINANCE_NEWS_FIXTURES_BASE"] = tmpdir
                fixtures_base = get_fixtures_base()
                self.assertEqual(str(fixtures_base), tmpdir)
            finally:
                if original is None:
                    os.environ.pop("FINANCE_NEWS_FIXTURES_BASE", None)
                else:
                    os.environ["FINANCE_NEWS_FIXTURES_BASE"] = original

    def test_get_fixtures_base_arg_override(self) -> None:
        """Test fixtures base path from function argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixtures_base = get_fixtures_base(tmpdir)
            self.assertEqual(str(fixtures_base), tmpdir)

    def test_load_fixture_bytes(self) -> None:
        """Test loading a fixture as raw bytes."""
        content = load_fixture_bytes("bcra_comunicaciones_a", "A8060.txt")
        self.assertIsInstance(content, bytes)
        self.assertIn("Suspensión Rueda BCRA", content.decode("utf-8"))

    def test_load_fixture_text(self) -> None:
        """Test loading a fixture as text."""
        content = load_fixture_text("bcra_comunicaciones_a", "A8060.txt")
        self.assertIsInstance(content, str)
        self.assertIn("Suspensión Rueda BCRA", content)

    def test_load_fixture_json(self) -> None:
        """Test loading a fixture as parsed JSON."""
        data = load_fixture_json("test_connector", "snapshot.json")
        self.assertIsInstance(data, dict)
        self.assertEqual(data["external_id"], "test-001")
        self.assertEqual(data["title"], "Test Snapshot")

    def test_load_fixture_not_found(self) -> None:
        """Test loading a non-existent fixture raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_fixture_text("nonexistent_connector", "missing.txt")


class SnapshotHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures for snapshot tests."""
        now = datetime(2024, 6, 15, 13, 0, 0, tzinfo=timezone.utc)
        published = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        self.provenance = Provenance(
            connector="test_connector",
            source="test",
            fetch_url="https://example.com/api/test-001",
            canonical_url="https://example.com/test-001",
            cursor="test-001",
            fetched_at=now,
            parser_version="1.0.0",
            transport_metadata={"status_code": 200},
        )

        self.freshness = Freshness(
            published_at=published,
            first_seen_at=now,
            fetched_at=now,
            is_stale=False,
            ttl_seconds=3600,
        )

        self.source_item = SourceItem(
            external_id="test-001",
            source="test",
            published_at=published,
            title="Test Snapshot",
            body=None,
            summary=None,
            url="https://example.com/test-001",
            metadata={"key1": "value1", "key2": "value2"},
            provenance=self.provenance,
            freshness=self.freshness,
        )

    def test_normalize_source_item(self) -> None:
        """Test normalizing a SourceItem to deterministic form."""
        normalized = normalize_source_item(self.source_item)

        self.assertIsInstance(normalized, dict)
        self.assertEqual(normalized["external_id"], "test-001")
        self.assertEqual(normalized["title"], "Test Snapshot")

        # Check that metadata is sorted
        metadata_keys = list(normalized["metadata"].keys())
        self.assertEqual(metadata_keys, sorted(metadata_keys))

        # Check nested provenance transport_metadata is sorted
        transport_keys = list(normalized["provenance"]["transport_metadata"].keys())
        self.assertEqual(transport_keys, sorted(transport_keys))

    def test_compare_snapshots_match(self) -> None:
        """Test comparing matching snapshots."""
        actual = normalize_source_item(self.source_item)
        expected = normalize_source_item(self.source_item)

        matches, diff_lines = compare_snapshots(actual, expected)

        self.assertTrue(matches)
        self.assertEqual(len(diff_lines), 0)

    def test_compare_snapshots_mismatch_diff(self) -> None:
        """Test comparing mismatched snapshots generates diff."""
        actual = normalize_source_item(self.source_item)

        # Create a mismatched version
        mismatched_item = SourceItem(
            external_id="test-002",
            source="test",
            published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            title="Different Title",
            body=None,
            summary=None,
            url="https://example.com/test-002",
            metadata={"key1": "value1", "key2": "value2"},
            provenance=self.provenance,
            freshness=self.freshness,
        )
        expected = normalize_source_item(mismatched_item)

        matches, diff_lines = compare_snapshots(actual, expected)

        self.assertFalse(matches)
        self.assertGreater(len(diff_lines), 0)

        # Check that diff contains expected fields
        diff_text = "\n".join(diff_lines)
        self.assertIn("external_id", diff_text)
        self.assertIn("title", diff_text)

    def test_compare_snapshots_nested_diff(self) -> None:
        """Test comparing snapshots with nested mismatches."""
        actual = normalize_source_item(self.source_item)

        # Create a version with nested mismatch in metadata
        mismatched_item = SourceItem(
            external_id="test-001",
            source="test",
            published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            title="Test Snapshot",
            body=None,
            summary=None,
            url="https://example.com/test-001",
            metadata={"key1": "different_value", "key2": "value2"},
            provenance=self.provenance,
            freshness=self.freshness,
        )
        expected = normalize_source_item(mismatched_item)

        matches, diff_lines = compare_snapshots(actual, expected)

        self.assertFalse(matches)
        self.assertGreater(len(diff_lines), 0)

        # Check that diff shows nested path
        diff_text = "\n".join(diff_lines)
        self.assertIn("metadata", diff_text)
        self.assertIn("key1", diff_text)

    def test_assert_source_items_match(self) -> None:
        """Test asserting matching SourceItem objects."""
        # This should not raise
        assert_source_items_match(self.source_item, self.source_item)

    def test_assert_source_items_match_fails_with_diff(self) -> None:
        """Test asserting mismatching SourceItem objects raises with diff."""
        mismatched_item = SourceItem(
            external_id="test-002",
            source="test",
            published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            title="Different Title",
            body=None,
            summary=None,
            url="https://example.com/test-002",
            metadata={"key1": "value1", "key2": "value2"},
            provenance=self.provenance,
            freshness=self.freshness,
        )

        with self.assertRaises(AssertionError) as context:
            assert_source_items_match(self.source_item, mismatched_item)

        error_message = str(context.exception)
        self.assertIn("SourceItem snapshots do not match", error_message)
        self.assertIn("external_id", error_message)


class ReadmeDocumentationTests(unittest.TestCase):
    def test_readme_exists_and_documented(self) -> None:
        """Test that README.md exists and contains key documentation."""
        readme_path = (
            Path(__file__).resolve().parents[1] / "src" / "finance_news" / "testing" / "README.md"
        )

        self.assertTrue(readme_path.exists())

        content = readme_path.read_text(encoding="utf-8")

        # Check for key documentation sections
        self.assertIn("Fixture Naming Convention", content)
        self.assertIn("YYYY-MM-DD__source__case.ext", content)
        self.assertIn("Loading Fixtures", content)
        self.assertIn("Comparing SourceItem Snapshots", content)
        self.assertIn("load_fixture_text", content)
        self.assertIn("assert_source_items_match", content)


if __name__ == "__main__":
    unittest.main()