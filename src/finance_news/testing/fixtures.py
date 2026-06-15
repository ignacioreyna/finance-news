"""Offline fixture loading helpers for connector tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def get_fixtures_base(base_path: str | None = None) -> Path:
    """Get the base fixtures directory.

    Args:
        base_path: Optional override path. If None, checks FINANCE_NEWS_FIXTURES_BASE
            env var, then defaults to the repository's tests/fixtures directory.

    Returns:
        Path to the fixtures base directory.
    """
    if base_path is not None:
        return Path(base_path)

    env_path = os.environ.get("FINANCE_NEWS_FIXTURES_BASE")
    if env_path is not None:
        return Path(env_path)

    # Default to tests/fixtures relative to the repo root
    # We resolve this by going up from the src directory
    current_file = Path(__file__).resolve()
    src_dir = current_file.parent.parent.parent
    repo_root = src_dir.parent
    return repo_root / "tests" / "fixtures"


def _resolve_fixture_path(connector: str, name: str, base_path: Path) -> Path:
    """Resolve a fixture path under a connector's fixtures directory.

    Args:
        connector: The connector name (e.g., "bcra_comunicaciones_a").
        name: The fixture filename (e.g., "A8060.txt").
        base_path: The fixtures base directory.

    Returns:
        The resolved path to the fixture file.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
    """
    fixture_path = base_path / connector / name
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return fixture_path


def load_fixture_bytes(
    connector: str,
    name: str,
    *,
    base_path: str | None = None,
) -> bytes:
    """Load a fixture file as raw bytes.

    This is an offline-only operation and never touches the network.

    Args:
        connector: The connector name (e.g., "bcra_comunicaciones_a").
        name: The fixture filename (e.g., "A8060.txt").
        base_path: Optional override for the fixtures base directory.

    Returns:
        The raw bytes of the fixture file.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        IOError: If there's an error reading the file.
    """
    fixtures_base = get_fixtures_base(base_path)
    fixture_path = _resolve_fixture_path(connector, name, fixtures_base)
    return fixture_path.read_bytes()


def load_fixture_text(
    connector: str,
    name: str,
    *,
    encoding: str = "utf-8",
    base_path: str | None = None,
) -> str:
    """Load a fixture file as text.

    This is an offline-only operation and never touches the network.

    Args:
        connector: The connector name (e.g., "bcra_comunicaciones_a").
        name: The fixture filename (e.g., "A8060.txt").
        encoding: The text encoding to use (default: "utf-8").
        base_path: Optional override for the fixtures base directory.

    Returns:
        The text content of the fixture file.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        IOError: If there's an error reading the file.
        UnicodeDecodeError: If the file cannot be decoded with the given encoding.
    """
    fixtures_base = get_fixtures_base(base_path)
    fixture_path = _resolve_fixture_path(connector, name, fixtures_base)
    return fixture_path.read_text(encoding=encoding)


def load_fixture_json(
    connector: str,
    name: str,
    *,
    base_path: str | None = None,
) -> dict[str, Any]:
    """Load a fixture file as parsed JSON.

    This is an offline-only operation and never touches the network.

    Args:
        connector: The connector name (e.g., "bcra_comunicaciones_a").
        name: The fixture filename (e.g., "snapshot.json").
        base_path: Optional override for the fixtures base directory.

    Returns:
        The parsed JSON content as a dictionary.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        IOError: If there's an error reading the file.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON does not parse to a dictionary.
    """
    text = load_fixture_text(connector, name, base_path=base_path)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"JSON fixture must be a dict, got {type(data).__name__}")
    return data