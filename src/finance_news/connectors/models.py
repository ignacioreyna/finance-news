"""Normalized connector models and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _deserialize_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    base_delay_seconds: float
    max_delay_seconds: float
    jitter: bool = True


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_minute: int | None = None
    concurrency: int = 1
    burst: int = 1


@dataclass(frozen=True)
class Freshness:
    published_at: datetime | None
    first_seen_at: datetime
    fetched_at: datetime
    is_stale: bool
    ttl_seconds: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "published_at": _serialize_datetime(self.published_at),
            "first_seen_at": _serialize_datetime(self.first_seen_at),
            "fetched_at": _serialize_datetime(self.fetched_at),
            "is_stale": self.is_stale,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Freshness":
        return cls(
            published_at=_deserialize_datetime(data.get("published_at")),
            first_seen_at=_deserialize_datetime(data["first_seen_at"]),
            fetched_at=_deserialize_datetime(data["fetched_at"]),
            is_stale=bool(data["is_stale"]),
            ttl_seconds=data.get("ttl_seconds"),
        )


@dataclass(frozen=True)
class Provenance:
    connector: str
    source: str
    fetch_url: str
    canonical_url: str
    cursor: str | None
    fetched_at: datetime
    parser_version: str
    transport_metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "source": self.source,
            "fetch_url": self.fetch_url,
            "canonical_url": self.canonical_url,
            "cursor": self.cursor,
            "fetched_at": _serialize_datetime(self.fetched_at),
            "parser_version": self.parser_version,
            "transport_metadata": dict(self.transport_metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Provenance":
        return cls(
            connector=str(data["connector"]),
            source=str(data["source"]),
            fetch_url=str(data["fetch_url"]),
            canonical_url=str(data["canonical_url"]),
            cursor=data.get("cursor"),
            fetched_at=_deserialize_datetime(data["fetched_at"]),
            parser_version=str(data["parser_version"]),
            transport_metadata=dict(data.get("transport_metadata", {})),
        )


@dataclass(frozen=True)
class SourceItem:
    external_id: str
    source: str
    published_at: datetime | None
    title: str
    body: str | None
    summary: str | None
    url: str
    metadata: Mapping[str, Any]
    provenance: Provenance
    freshness: Freshness

    def to_dict(self) -> dict[str, Any]:
        return {
            "external_id": self.external_id,
            "source": self.source,
            "published_at": _serialize_datetime(self.published_at),
            "title": self.title,
            "body": self.body,
            "summary": self.summary,
            "url": self.url,
            "metadata": dict(self.metadata),
            "provenance": self.provenance.to_dict(),
            "freshness": self.freshness.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceItem":
        return cls(
            external_id=str(data["external_id"]),
            source=str(data["source"]),
            published_at=_deserialize_datetime(data.get("published_at")),
            title=str(data["title"]),
            body=data.get("body"),
            summary=data.get("summary"),
            url=str(data["url"]),
            metadata=dict(data.get("metadata", {})),
            provenance=Provenance.from_dict(data["provenance"]),
            freshness=Freshness.from_dict(data["freshness"]),
        )


@dataclass(frozen=True)
class PageResult:
    items: Sequence[SourceItem]
    next_cursor: str | None
    has_more: bool


class RecoverableConnectorError(Exception):
    """Retryable connector failure."""


class Connector(Protocol):
    name: str
    source: str
    retry_policy: RetryPolicy
    rate_limit_policy: RateLimitPolicy

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of normalized items."""
