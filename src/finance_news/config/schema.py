from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping


@dataclass(frozen=True)
class FreshnessSpec:
    """Freshness configuration for a source or series."""

    ttl_seconds: int
    freshness_tolerance_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ttl_seconds": self.ttl_seconds,
            "freshness_tolerance_seconds": self.freshness_tolerance_seconds,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FreshnessSpec":
        return cls(
            ttl_seconds=int(data["ttl_seconds"]),
            freshness_tolerance_seconds=int(data["freshness_tolerance_seconds"]),
        )


@dataclass(frozen=True)
class SourceConfig:
    """Configuration for a single data source."""

    source_id: str
    connector: str
    base_url: str
    frequency: Literal["daily", "weekly", "monthly", "eventual"]
    freshness: FreshnessSpec
    priority: Literal["alta", "media", "baja"]
    category: Literal["primary", "proxy", "manual"]
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "connector": self.connector,
            "base_url": self.base_url,
            "frequency": self.frequency,
            "freshness": self.freshness.to_dict(),
            "priority": self.priority,
            "category": self.category,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceConfig":
        return cls(
            source_id=str(data["source_id"]),
            connector=str(data["connector"]),
            base_url=str(data["base_url"]),
            frequency=data["frequency"],
            freshness=FreshnessSpec.from_dict(data["freshness"]),
            priority=data["priority"],
            category=data["category"],
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(frozen=True)
class SeriesConfig:
    """Configuration for a specific data series within a source."""

    series_id: str
    source_id: str
    path: str
    filters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "source_id": self.source_id,
            "path": self.path,
            "filters": dict(self.filters),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SeriesConfig":
        return cls(
            series_id=str(data["series_id"]),
            source_id=str(data["source_id"]),
            path=str(data["path"]),
            filters=dict(data.get("filters", {})),
        )