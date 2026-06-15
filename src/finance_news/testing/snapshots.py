"""Deterministic snapshot comparison for SourceItem objects."""

from __future__ import annotations

import json
from typing import Any

from finance_news.connectors.models import SourceItem


def normalize_source_item(item: SourceItem) -> dict[str, Any]:
    """Normalize a SourceItem to a deterministic JSON-serializable form.

    This uses SourceItem.to_dict() and ensures the output is stable for
    comparison by sorting dictionary keys. The datetime fields are already
    handled by to_dict() which converts them to ISO format strings.

    Args:
        item: The SourceItem to normalize.

    Returns:
        A normalized dictionary representation suitable for comparison.
    """
    # Reuse the existing to_dict() method which handles datetime serialization
    data = item.to_dict()

    # Sort all nested dictionaries recursively for deterministic comparison
    return _sort_dict_recursively(data)


def _sort_dict_recursively(obj: Any) -> Any:
    """Recursively sort all dictionaries in an object for deterministic comparison.

    Args:
        obj: The object to sort recursively.

    Returns:
        The object with all dictionaries sorted by key.
    """
    if isinstance(obj, dict):
        return {k: _sort_dict_recursively(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_sort_dict_recursively(item) for item in obj]
    return obj


def compare_snapshots(
    actual: dict[str, Any],
    expected: dict[str, Any],
    *,
    path: str = "",
) -> tuple[bool, list[str]]:
    """Compare two snapshot dictionaries and generate a readable diff.

    This performs a deep comparison and generates human-readable diff output
    showing exactly what differs between the snapshots.

    Args:
        actual: The actual snapshot dictionary.
        expected: The expected snapshot dictionary.
        path: Current path in the nested structure (for recursive calls).

    Returns:
        A tuple of (matches, diff_lines). If matches is True, the snapshots
        are identical. If False, diff_lines contains a readable diff.
    """
    diff_lines: list[str] = []

    # Get all unique keys from both dicts
    all_keys = sorted(set(actual.keys()) | set(expected.keys()))

    for key in all_keys:
        current_path = f"{path}.{key}" if path else key
        actual_value = actual.get(key, "<missing>")
        expected_value = expected.get(key, "<missing>")

        if isinstance(actual_value, dict) and isinstance(expected_value, dict):
            # Recursively compare nested dictionaries
            matches, nested_diff = compare_snapshots(
                actual_value, expected_value, path=current_path
            )
            if not matches:
                diff_lines.extend(nested_diff)
        elif isinstance(actual_value, list) and isinstance(expected_value, list):
            # Compare lists element by element
            if len(actual_value) != len(expected_value):
                diff_lines.append(
                    f"  {current_path}: list length mismatch "
                    f"(actual={len(actual_value)}, expected={len(expected_value)})"
                )
                diff_lines.append(f"    actual:   {json.dumps(actual_value)}")
                diff_lines.append(f"    expected: {json.dumps(expected_value)}")
            else:
                for i, (actual_item, expected_item) in enumerate(
                    zip(actual_value, expected_value)
                ):
                    item_path = f"{current_path}[{i}]"
                    if isinstance(actual_item, dict) and isinstance(
                        expected_item, dict
                    ):
                        matches, nested_diff = compare_snapshots(
                            actual_item, expected_item, path=item_path
                        )
                        if not matches:
                            diff_lines.extend(nested_diff)
                    elif actual_item != expected_item:
                        diff_lines.append(f"  {item_path}: value mismatch")
                        diff_lines.append(f"    actual:   {json.dumps(actual_item)}")
                        diff_lines.append(
                            f"    expected: {json.dumps(expected_item)}"
                        )
        elif actual_value != expected_value:
            diff_lines.append(f"  {current_path}: value mismatch")
            diff_lines.append(f"    actual:   {json.dumps(actual_value)}")
            diff_lines.append(f"    expected: {json.dumps(expected_value)}")

    matches = len(diff_lines) == 0
    return matches, diff_lines


def assert_source_items_match(
    actual: SourceItem,
    expected: SourceItem,
    msg: str = "",
) -> None:
    """Assert that two SourceItem objects match, with a readable diff on failure.

    This is a helper for unittest tests that provides better error messages
    than plain assertEqual when comparing SourceItem objects.

    Args:
        actual: The actual SourceItem.
        expected: The expected SourceItem.
        msg: Optional message to prepend to the assertion error.

    Raises:
        AssertionError: If the SourceItem objects do not match.
    """
    actual_normalized = normalize_source_item(actual)
    expected_normalized = normalize_source_item(expected)

    matches, diff_lines = compare_snapshots(actual_normalized, expected_normalized)

    if matches:
        return

    # Build a readable error message
    error_parts = []
    if msg:
        error_parts.append(msg)
    error_parts.append("SourceItem snapshots do not match:")
    error_parts.extend(diff_lines)

    raise AssertionError("\n".join(error_parts))