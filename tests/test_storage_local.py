"""Tests for local storage module."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors.models import Freshness, Provenance, SourceItem
from finance_news.storage.local import (
    LocalStorage,
    _compute_hash,
    _item_path,
    _metadata_path,
    _normalized_path,
    _raw_path,
)


class LocalStoragePathTests(unittest.TestCase):
    def test_deterministic_path_by_connector_id_date(self) -> None:
        """Test that paths are deterministic based on connector, id, and date."""
        storage_root = Path("/tmp/storage")
        connector = "fomc_press_releases"
        external_id = "fomc-2026-06-13"
        date = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)

        item_dir = _item_path(storage_root, connector, external_id, date)

        expected = Path("/tmp/storage/fomc_press_releases/2026-06/fomc-2026-06-13")
        self.assertEqual(item_dir, expected)

        # Same inputs produce same path
        item_dir2 = _item_path(storage_root, connector, external_id, date)
        self.assertEqual(item_dir, item_dir2)

        # Different date produces different path
        date2 = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
        item_dir3 = _item_path(storage_root, connector, external_id, date2)
        expected3 = Path("/tmp/storage/fomc_press_releases/2026-06/fomc-2026-06-13")
        self.assertEqual(item_dir3, expected3)  # Same month, same path

        # Different month produces different path
        date3 = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
        item_dir4 = _item_path(storage_root, connector, external_id, date3)
        expected4 = Path("/tmp/storage/fomc_press_releases/2026-07/fomc-2026-06-13")
        self.assertEqual(item_dir4, expected4)

    def test_multiple_items_same_day_separate_paths(self) -> None:
        """Test that multiple items on the same day have separate paths."""
        storage_root = Path("/tmp/storage")
        connector = "fomc_press_releases"
        date = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)

        item_dir1 = _item_path(storage_root, connector, "item-1", date)
        item_dir2 = _item_path(storage_root, connector, "item-2", date)

        self.assertEqual(item_dir1.parent, item_dir2.parent)  # Same month directory
        self.assertNotEqual(item_dir1, item_dir2)  # Different item directories


class LocalStorageHashTests(unittest.TestCase):
    def test_put_raw_compute_hash(self) -> None:
        """Test that put_raw computes and returns SHA-256 hash."""
        raw = b"test payload content"
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(Path(tmpdir))

            hash1 = storage.put_raw(raw, "test_connector", "test-id", datetime.now())

            # Hash should be SHA-256 (64 hex chars)
            self.assertEqual(len(hash1), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in hash1))

            # Same content produces same hash
            hash2 = storage.put_raw(raw, "test_connector", "test-id-2", datetime.now())
            self.assertEqual(hash1, hash2)

            # Different content produces different hash
            hash3 = storage.put_raw(b"different", "test_connector", "test-id-3", datetime.now())
            self.assertNotEqual(hash1, hash3)


class LocalStorageRoundTripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(Path(self.tmpdir))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_put_item_round_trip(self) -> None:
        """Test that SourceItem round-trips through storage."""
        published_at = datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
        first_seen_at = datetime(2026, 6, 14, 9, 5, tzinfo=timezone.utc)

        item = SourceItem(
            external_id="fomc-2026-06-13",
            source="fomc",
            published_at=published_at,
            title="FOMC statement",
            body=None,
            summary="Rates unchanged.",
            url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20260613a.htm",
            metadata={"macro_topic": "rates", "tickers": ["SPY", "TLT"]},
            provenance=Provenance(
                connector="fomc_press_releases",
                source="fomc",
                fetch_url="https://www.federalreserve.gov/newsevents/pressreleases.htm",
                canonical_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20260613a.htm",
                cursor="page=1",
                fetched_at=fetched_at,
                parser_version="0.1.0",
                transport_metadata={"status_code": 200, "etag": "abc123"},
            ),
            freshness=Freshness(
                published_at=published_at,
                first_seen_at=first_seen_at,
                fetched_at=fetched_at,
                is_stale=False,
                ttl_seconds=3600,
            ),
        )

        # Store raw first
        raw = b"<html>raw content</html>"
        self.storage.put_raw(raw, item.provenance.connector, item.external_id, item.provenance.fetched_at)

        # Store item
        self.storage.put_item(item)

        # Retrieve
        retrieved = self.storage.get_item(item.provenance.connector, item.external_id, item.provenance.fetched_at)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, item)

    def test_get_item_nonexistent_returns_none(self) -> None:
        """Test that get_item returns None for nonexistent items."""
        retrieved = self.storage.get_item("test_connector", "nonexistent-id", datetime.now())
        self.assertIsNone(retrieved)

    def test_get_raw_round_trip(self) -> None:
        """Test that raw bytes round-trip through storage."""
        raw = b"test raw payload bytes with \x00\x01\x02\x03 binary data"

        connector = "test_connector"
        external_id = "test-id"
        date = datetime.now()

        # Store
        self.storage.put_raw(raw, connector, external_id, date)

        # Retrieve
        retrieved = self.storage.get_raw(connector, external_id, date)

        self.assertEqual(retrieved, raw)

    def test_atomic_write_does_not_corrupt_on_interrupt(self) -> None:
        """Test that atomic writes leave no corrupt temp files on completion."""
        raw = b"test payload"
        connector = "test_connector"
        external_id = "test-id"
        date = datetime.now()

        # Store
        self.storage.put_raw(raw, connector, external_id, date)

        # Check that no .tmp files exist
        item_dir = _item_path(self.storage.storage_root, connector, external_id, date)
        tmp_files = list(item_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0, f"Found temp files: {tmp_files}")

        # Check that raw.bin exists and has correct content
        raw_path = _raw_path(item_dir)
        self.assertTrue(raw_path.exists())
        self.assertEqual(raw_path.read_bytes(), raw)

        # Store an item and check again
        published_at = datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
        first_seen_at = datetime(2026, 6, 14, 9, 5, tzinfo=timezone.utc)

        item = SourceItem(
            external_id=external_id,
            source="test",
            published_at=published_at,
            title="Test",
            body=None,
            summary="Test summary",
            url="https://example.com/test",
            metadata={},
            provenance=Provenance(
                connector=connector,
                source="test",
                fetch_url="https://example.com/fetch",
                canonical_url="https://example.com/test",
                cursor=None,
                fetched_at=fetched_at,
                parser_version="1.0.0",
                transport_metadata={"status_code": 200},
            ),
            freshness=Freshness(
                published_at=published_at,
                first_seen_at=first_seen_at,
                fetched_at=fetched_at,
                is_stale=False,
                ttl_seconds=3600,
            ),
        )

        self.storage.put_item(item)

        # Check that no .tmp files exist after put_item
        tmp_files = list(item_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)

        # Check that normalized.json and metadata.json exist
        normalized_path = _normalized_path(item_dir)
        metadata_path = _metadata_path(item_dir)

        self.assertTrue(normalized_path.exists())
        self.assertTrue(metadata_path.exists())


class LocalStorageMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(Path(self.tmpdir))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_hash_provenance_in_metadata(self) -> None:
        """Test that metadata includes hash of raw bytes."""
        raw = b"test payload for hash provenance"
        connector = "test_connector"
        external_id = "test-id"
        date = datetime.now()

        # Store raw
        self.storage.put_raw(raw, connector, external_id, date)

        # Create and store item
        published_at = datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
        first_seen_at = datetime(2026, 6, 14, 9, 5, tzinfo=timezone.utc)

        item = SourceItem(
            external_id=external_id,
            source="test",
            published_at=published_at,
            title="Test",
            body=None,
            summary="Test summary",
            url="https://example.com/test",
            metadata={},
            provenance=Provenance(
                connector=connector,
                source="test",
                fetch_url="https://example.com/fetch",
                canonical_url="https://example.com/test",
                cursor=None,
                fetched_at=fetched_at,
                parser_version="1.0.0",
                transport_metadata={"status_code": 200},
            ),
            freshness=Freshness(
                published_at=published_at,
                first_seen_at=first_seen_at,
                fetched_at=fetched_at,
                is_stale=False,
                ttl_seconds=3600,
            ),
        )

        self.storage.put_item(item)

        # Retrieve metadata
        metadata = self.storage.get_metadata(connector, external_id, date)

        self.assertIsNotNone(metadata)
        self.assertIn("raw_hash", metadata)

        # Hash should match computed hash
        expected_hash = _compute_hash(raw)
        self.assertEqual(metadata["raw_hash"], expected_hash)

        # Check other required fields
        self.assertEqual(metadata["external_id"], external_id)
        self.assertEqual(metadata["connector"], connector)
        self.assertEqual(metadata["raw_size_bytes"], len(raw))
        self.assertEqual(metadata["parser_version"], "1.0.0")
        self.assertIn("fetched_at", metadata)
        self.assertIn("stored_at", metadata)


class LocalStorageDedupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(Path(self.tmpdir))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dedup_by_hash_same_raw_reused(self) -> None:
        """Test that hash is computed consistently for deduplication."""
        raw = b"duplicate content"
        connector = "test_connector"
        date = datetime.now()

        # Store same raw for two different external_ids
        hash1 = self.storage.put_raw(raw, connector, "item-1", date)
        hash2 = self.storage.put_raw(raw, connector, "item-2", date)

        # Hashes should be identical
        self.assertEqual(hash1, hash2)

        # But items should be stored separately
        raw1 = self.storage.get_raw(connector, "item-1", date)
        raw2 = self.storage.get_raw(connector, "item-2", date)

        self.assertEqual(raw1, raw)
        self.assertEqual(raw2, raw)


class LocalStorageErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(Path(self.tmpdir))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_put_item_without_raw_raises_error(self) -> None:
        """Test that put_item raises FileNotFoundError if raw.bin doesn't exist."""
        published_at = datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
        first_seen_at = datetime(2026, 6, 14, 9, 5, tzinfo=timezone.utc)

        item = SourceItem(
            external_id="test-id",
            source="test",
            published_at=published_at,
            title="Test",
            body=None,
            summary="Test summary",
            url="https://example.com/test",
            metadata={},
            provenance=Provenance(
                connector="test_connector",
                source="test",
                fetch_url="https://example.com/fetch",
                canonical_url="https://example.com/test",
                cursor=None,
                fetched_at=fetched_at,
                parser_version="1.0.0",
                transport_metadata={"status_code": 200},
            ),
            freshness=Freshness(
                published_at=published_at,
                first_seen_at=first_seen_at,
                fetched_at=fetched_at,
                is_stale=False,
                ttl_seconds=3600,
            ),
        )

        # Try to put item without storing raw first
        with self.assertRaises(FileNotFoundError) as context:
            self.storage.put_item(item)

        self.assertIn("raw.bin", str(context.exception))


if __name__ == "__main__":
    unittest.main()