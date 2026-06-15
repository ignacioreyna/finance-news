"""Local filesystem storage for raw payloads and normalized SourceItems.

MVP scope: single-process; no concurrent-write handling.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from finance_news.connectors.models import SourceItem


def _compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def _item_path(storage_root: Path, connector: str, external_id: str, date: datetime) -> Path:
    """Generate deterministic path for an item.

    Layout: storage/<connector>/YYYY-MM/<external_id>/
    """
    connector_dir = storage_root / connector
    month_dir = connector_dir / date.strftime("%Y-%m")
    item_dir = month_dir / external_id
    return item_dir


def _raw_path(item_path: Path) -> Path:
    """Path to raw.bin file."""
    return item_path / "raw.bin"


def _normalized_path(item_path: Path) -> Path:
    """Path to normalized.json file."""
    return item_path / "normalized.json"


def _metadata_path(item_path: Path) -> Path:
    """Path to metadata.json file."""
    return item_path / "metadata.json"


class LocalStorage:
    """Local filesystem storage for raw payloads and normalized SourceItems.

    Stores:
    - raw.bin: raw HTTP payload bytes
    - normalized.json: SourceItem.to_dict()
    - metadata.json: run metadata (hash, timestamps, etc.)

    Uses atomic writes via temporary files with os.replace().
    """

    def __init__(self, storage_root: Path) -> None:
        """Initialize storage with root directory.

        Args:
            storage_root: Root directory for storage (will be created if needed).
        """
        self.storage_root = Path(storage_root).resolve()

    def put_raw(self, raw: bytes, connector: str, external_id: str, date: datetime) -> str:
        """Store raw payload bytes at deterministic path.

        Args:
            raw: Raw payload bytes.
            connector: Connector name (e.g., "fomc_press_releases").
            external_id: External ID of the item.
            date: Date for partitioning (YYYY-MM).

        Returns:
            SHA-256 hash of the raw bytes.
        """
        hash_value = _compute_hash(raw)
        item_dir = _item_path(self.storage_root, connector, external_id, date)
        item_dir.mkdir(parents=True, exist_ok=True)

        raw_path = _raw_path(item_dir)
        temp_path = raw_path.with_suffix(".tmp")

        try:
            temp_path.write_bytes(raw)
            os.replace(temp_path, raw_path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

        return hash_value

    def put_item(self, item: SourceItem) -> None:
        """Store normalized SourceItem and its run metadata.

        Args:
            item: SourceItem to store (must already have raw stored via put_raw).

        Raises:
            FileNotFoundError: If raw.bin does not exist for this item.
        """
        connector = item.provenance.connector
        external_id = item.external_id
        date = item.provenance.fetched_at

        item_dir = _item_path(self.storage_root, connector, external_id, date)
        item_dir.mkdir(parents=True, exist_ok=True)

        raw_path = _raw_path(item_dir)
        if not raw_path.exists():
            raise FileNotFoundError(f"raw.bin not found for {connector}/{external_id}")

        # Store normalized SourceItem
        normalized_path = _normalized_path(item_dir)
        temp_normalized_path = normalized_path.with_suffix(".tmp")

        try:
            temp_normalized_path.write_text(json.dumps(item.to_dict(), indent=2, sort_keys=True))
            os.replace(temp_normalized_path, normalized_path)
        finally:
            if temp_normalized_path.exists():
                temp_normalized_path.unlink(missing_ok=True)

        # Store run metadata (latest only, overwrites on re-run)
        raw_bytes = raw_path.read_bytes()
        hash_value = _compute_hash(raw_bytes)

        metadata = {
            "external_id": external_id,
            "connector": connector,
            "source": item.source,
            "url": item.url,
            "fetched_at": item.provenance.fetched_at.isoformat(),
            "stored_at": datetime.now().isoformat(),
            "raw_hash": hash_value,
            "raw_size_bytes": len(raw_bytes),
            "parser_version": item.provenance.parser_version,
        }

        metadata_path = _metadata_path(item_dir)
        temp_metadata_path = metadata_path.with_suffix(".tmp")

        try:
            temp_metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))
            os.replace(temp_metadata_path, metadata_path)
        finally:
            if temp_metadata_path.exists():
                temp_metadata_path.unlink(missing_ok=True)

    def get_item(self, connector: str, external_id: str, date: datetime) -> SourceItem | None:
        """Retrieve normalized SourceItem.

        Args:
            connector: Connector name.
            external_id: External ID of the item.
            date: Date used for partitioning (YYYY-MM).

        Returns:
            SourceItem if found, None otherwise.
        """
        item_dir = _item_path(self.storage_root, connector, external_id, date)
        normalized_path = _normalized_path(item_dir)

        if not normalized_path.exists():
            return None

        data = json.loads(normalized_path.read_text())
        return SourceItem.from_dict(data)

    def get_raw(self, connector: str, external_id: str, date: datetime) -> bytes | None:
        """Retrieve raw payload bytes.

        Args:
            connector: Connector name.
            external_id: External ID of the item.
            date: Date used for partitioning (YYYY-MM).

        Returns:
            Raw bytes if found, None otherwise.
        """
        item_dir = _item_path(self.storage_root, connector, external_id, date)
        raw_path = _raw_path(item_dir)

        if not raw_path.exists():
            return None

        return raw_path.read_bytes()

    def get_metadata(self, connector: str, external_id: str, date: datetime) -> dict[str, Any] | None:
        """Retrieve run metadata.

        Args:
            connector: Connector name.
            external_id: External ID of the item.
            date: Date used for partitioning (YYYY-MM).

        Returns:
            Metadata dict if found, None otherwise.
        """
        item_dir = _item_path(self.storage_root, connector, external_id, date)
        metadata_path = _metadata_path(item_dir)

        if not metadata_path.exists():
            return None

        return json.loads(metadata_path.read_text())