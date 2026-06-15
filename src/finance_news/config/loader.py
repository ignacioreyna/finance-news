from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from finance_news.config.schema import SeriesConfig, SourceConfig


class ConfigValidationError(Exception):
    """Raised when configuration fails validation."""


def _validate_frequency(value: str, context: str) -> None:
    """Validate frequency field."""
    valid_frequencies = {"daily", "weekly", "monthly", "eventual"}
    if value not in valid_frequencies:
        raise ConfigValidationError(
            f"Invalid frequency '{value}' for {context}. Must be one of: {', '.join(sorted(valid_frequencies))}"
        )


def _validate_priority(value: str, context: str) -> None:
    """Validate priority field."""
    valid_priorities = {"alta", "media", "baja"}
    if value not in valid_priorities:
        raise ConfigValidationError(
            f"Invalid priority '{value}' for {context}. Must be one of: {', '.join(sorted(valid_priorities))}"
        )


def _validate_category(value: str, context: str) -> None:
    """Validate category field."""
    valid_categories = {"primary", "proxy", "manual"}
    if value not in valid_categories:
        raise ConfigValidationError(
            f"Invalid category '{value}' for {context}. Must be one of: {', '.join(sorted(valid_categories))}"
        )


def _validate_positive_int(value: Any, field_name: str, context: str) -> int:
    """Validate and convert a field to a positive integer."""
    if not isinstance(value, int):
        raise ConfigValidationError(
            f"Field '{field_name}' for {context} must be an integer, got {type(value).__name__}"
        )
    if value <= 0:
        raise ConfigValidationError(
            f"Field '{field_name}' for {context} must be positive, got {value}"
        )
    return value


def _validate_required_fields(data: dict[str, Any], required_fields: list[str], context: str) -> None:
    """Validate that all required fields are present."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ConfigValidationError(
            f"Missing required fields for {context}: {', '.join(missing_fields)}"
        )


def _validate_source_config(source_id: str, data: dict[str, Any]) -> None:
    """Validate a single source configuration."""
    context = f"source '{source_id}'"

    _validate_required_fields(
        data,
        ["connector", "base_url", "frequency", "freshness", "priority", "category"],
        context,
    )

    if not isinstance(data["connector"], str) or not data["connector"]:
        raise ConfigValidationError(f"Field 'connector' for {context} must be a non-empty string")

    if not isinstance(data["base_url"], str) or not data["base_url"]:
        raise ConfigValidationError(f"Field 'base_url' for {context} must be a non-empty string")

    if not isinstance(data["frequency"], str):
        raise ConfigValidationError(f"Field 'frequency' for {context} must be a string")
    _validate_frequency(data["frequency"], context)

    if not isinstance(data["freshness"], dict):
        raise ConfigValidationError(f"Field 'freshness' for {context} must be a dictionary")

    freshness = data["freshness"]
    if "ttl_seconds" not in freshness:
        raise ConfigValidationError(f"Field 'freshness.ttl_seconds' is required for {context}")
    if "freshness_tolerance_seconds" not in freshness:
        raise ConfigValidationError(f"Field 'freshness.freshness_tolerance_seconds' is required for {context}")

    _validate_positive_int(freshness["ttl_seconds"], "freshness.ttl_seconds", context)
    _validate_positive_int(
        freshness["freshness_tolerance_seconds"], "freshness.freshness_tolerance_seconds", context
    )

    if not isinstance(data["priority"], str):
        raise ConfigValidationError(f"Field 'priority' for {context} must be a string")
    _validate_priority(data["priority"], context)

    if not isinstance(data["category"], str):
        raise ConfigValidationError(f"Field 'category' for {context} must be a string")
    _validate_category(data["category"], context)

    if "enabled" in data and not isinstance(data["enabled"], bool):
        raise ConfigValidationError(f"Field 'enabled' for {context} must be a boolean")


def _validate_series_config(series_id: str, data: dict[str, Any]) -> None:
    """Validate a single series configuration."""
    context = f"series '{series_id}'"

    _validate_required_fields(data, ["source_id", "path"], context)

    if not isinstance(data["source_id"], str) or not data["source_id"]:
        raise ConfigValidationError(f"Field 'source_id' for {context} must be a non-empty string")

    if not isinstance(data["path"], str) or not data["path"]:
        raise ConfigValidationError(f"Field 'path' for {context} must be a non-empty string")

    if "filters" in data and not isinstance(data["filters"], dict):
        raise ConfigValidationError(f"Field 'filters' for {context} must be a dictionary")


def load_config(config_path: Path | str) -> dict[str, Any]:
    """Load and validate configuration from a TOML file."""
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigValidationError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML in {config_path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigValidationError(f"Root of configuration file must be a dictionary, got {type(data).__name__}")

    if "sources" not in data:
        raise ConfigValidationError("Missing required field 'sources' in configuration")

    if not isinstance(data["sources"], dict):
        raise ConfigValidationError("Field 'sources' must be a dictionary")

    # Validate each source
    for source_id, source_data in data["sources"].items():
        if not isinstance(source_data, dict):
            raise ConfigValidationError(f"Source '{source_id}' must be a dictionary")
        _validate_source_config(source_id, source_data)

    # Validate each series if present
    if "series" in data:
        if not isinstance(data["series"], dict):
            raise ConfigValidationError("Field 'series' must be a dictionary")
        for series_id, series_data in data["series"].items():
            if not isinstance(series_data, dict):
                raise ConfigValidationError(f"Series '{series_id}' must be a dictionary")
            _validate_series_config(series_id, series_data)

    return data


def parse_source_configs(config_path: Path | str) -> dict[str, SourceConfig]:
    """Load and parse source configurations from a YAML file."""
    data = load_config(config_path)

    sources = {}
    for source_id, source_data in data["sources"].items():
        # Add source_id to the data for from_dict
        enriched_data = {"source_id": source_id, **source_data}
        sources[source_id] = SourceConfig.from_dict(enriched_data)

    return sources


def parse_series_configs(config_path: Path | str) -> dict[str, SeriesConfig]:
    """Load and parse series configurations from a YAML file."""
    data = load_config(config_path)

    series = {}
    if "series" in data:
        for series_id, series_data in data["series"].items():
            # Add series_id to the data for from_dict
            enriched_data = {"series_id": series_id, **series_data}
            series[series_id] = SeriesConfig.from_dict(enriched_data)

    return series