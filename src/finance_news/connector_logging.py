"""Structured logging helpers for finance news connectors.

This module provides event builders and logging utilities for connector operations,
specifically partial failures and run summaries aligned with the connector quality matrix.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PartialFailureEvent:
    """Event emitted when a connector experiences a partial failure.

    A partial failure is an error that doesn't invalidate the entire run,
    such as a failed page, invalid subset, or recoverable error.
    """

    connector: str
    source: str
    run_id: str
    cursor: str | None
    fetch_url: str
    error_type: str
    error_message: str
    recoverable: bool
    fetched_at: datetime
    parser_version: str
    attempt: int | None = None
    status_code: int | None = None
    items_received: int = 0
    items_emitted: int = 0
    items_dropped: int = 0
    has_more: bool = False
    next_cursor: str | None = None
    latency_ms: float | None = None
    retry_after_seconds: float | None = None
    response_bytes: int | None = None
    content_type: str | None = None
    trace_id: str | None = None
    sample_external_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        result = {
            "event": "connector.partial_failure",
            "connector": self.connector,
            "source": self.source,
            "run_id": self.run_id,
            "cursor": self.cursor,
            "fetch_url": self.fetch_url,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "recoverable": self.recoverable,
            "fetched_at": self.fetched_at.isoformat(),
            "parser_version": self.parser_version,
        }

        if self.attempt is not None:
            result["attempt"] = self.attempt

        if self.status_code is not None:
            result["status_code"] = self.status_code

        result["items_received"] = self.items_received
        result["items_emitted"] = self.items_emitted
        result["items_dropped"] = self.items_dropped
        result["has_more"] = self.has_more

        if self.next_cursor is not None:
            result["next_cursor"] = self.next_cursor

        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms

        if self.retry_after_seconds is not None:
            result["retry_after_seconds"] = self.retry_after_seconds

        if self.response_bytes is not None:
            result["response_bytes"] = self.response_bytes

        if self.content_type is not None:
            result["content_type"] = self.content_type

        if self.trace_id is not None:
            result["trace_id"] = self.trace_id

        if self.sample_external_ids:
            result["sample_external_ids"] = self.sample_external_ids

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PartialFailureEvent:
        """Create event from dict."""
        fetched_at = data["fetched_at"]

        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)

        return cls(
            connector=data["connector"],
            source=data["source"],
            run_id=data["run_id"],
            cursor=data.get("cursor"),
            fetch_url=data["fetch_url"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            recoverable=data["recoverable"],
            fetched_at=fetched_at,
            parser_version=data["parser_version"],
            attempt=data.get("attempt"),
            status_code=data.get("status_code"),
            items_received=data.get("items_received", 0),
            items_emitted=data.get("items_emitted", 0),
            items_dropped=data.get("items_dropped", 0),
            has_more=data.get("has_more", False),
            next_cursor=data.get("next_cursor"),
            latency_ms=data.get("latency_ms"),
            retry_after_seconds=data.get("retry_after_seconds"),
            response_bytes=data.get("response_bytes"),
            content_type=data.get("content_type"),
            trace_id=data.get("trace_id"),
            sample_external_ids=data.get("sample_external_ids", []),
        )


@dataclass(frozen=True)
class RunSummaryEvent:
    """Event emitted when a connector run completes.

    Provides a summary of the entire run including success status,
    item counts, and error statistics.
    """

    connector: str
    source: str
    run_id: str
    started_at: datetime
    finished_at: datetime
    status: str
    pages_fetched: int
    items_received_total: int
    items_emitted_total: int
    items_dropped_total: int
    recoverable_errors_total: int
    non_recoverable_errors_total: int
    stale_items_total: int

    def to_dict(self) -> dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        return {
            "event": "connector.run_summary",
            "connector": self.connector,
            "source": self.source,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "status": self.status,
            "pages_fetched": self.pages_fetched,
            "items_received_total": self.items_received_total,
            "items_emitted_total": self.items_emitted_total,
            "items_dropped_total": self.items_dropped_total,
            "recoverable_errors_total": self.recoverable_errors_total,
            "non_recoverable_errors_total": self.non_recoverable_errors_total,
            "stale_items_total": self.stale_items_total,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunSummaryEvent:
        """Create event from dict."""
        started_at = data["started_at"]

        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        finished_at = data["finished_at"]

        if isinstance(finished_at, str):
            finished_at = datetime.fromisoformat(finished_at)

        return cls(
            connector=data["connector"],
            source=data["source"],
            run_id=data["run_id"],
            started_at=started_at,
            finished_at=finished_at,
            status=data["status"],
            pages_fetched=data["pages_fetched"],
            items_received_total=data["items_received_total"],
            items_emitted_total=data["items_emitted_total"],
            items_dropped_total=data["items_dropped_total"],
            recoverable_errors_total=data["recoverable_errors_total"],
            non_recoverable_errors_total=data["non_recoverable_errors_total"],
            stale_items_total=data["stale_items_total"],
        )


_SECRET_KEYS = {
    "api_key",
    "apikey",
    "api-key",
    "token",
    "password",
    "passwd",
    "secret",
    "authorization",
    "auth",
    "userid",
    "user_id",
    "username",
}

_PAYLOAD_TRUNCATE_THRESHOLD = 256


def _redact(context: dict[str, Any]) -> dict[str, Any]:
    """Redact secrets and truncate large payloads from context.

    This function processes a dictionary context and:
    1. Replaces values for known secret keys with a redaction marker
    2. Truncates large payload/body fields to a size marker

    Args:
        context: The context dictionary to redact

    Returns:
        A new dictionary with secrets redacted and payloads truncated
    """
    if not isinstance(context, dict):
        return context

    redacted = {}

    for key, value in context.items():
        key_lower = key.lower()

        if key_lower in _SECRET_KEYS:
            redacted[key] = "[REDACTED]"
        elif key_lower in {"raw_body", "payload", "body", "content"}:
            if isinstance(value, str):
                if len(value) > _PAYLOAD_TRUNCATE_THRESHOLD:
                    size = len(value)
                    content_hash = hashlib.sha256(value.encode()).hexdigest()[:8]
                    redacted[key] = f"[TRUNCATED:{size}b:hash:{content_hash}]"
                else:
                    redacted[key] = value
            else:
                redacted[key] = value
        elif isinstance(value, dict):
            redacted[key] = _redact(value)
        elif isinstance(value, list):
            redacted[key] = [_redact(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted[key] = value

    return redacted


def emit_event(event: PartialFailureEvent | RunSummaryEvent) -> dict[str, Any]:
    """Emit a structured event as a JSON-serializable dict.

    This function converts event objects to dictionaries that can be logged
    or sent to monitoring systems. It does not perform any network I/O.

    Args:
        event: The event to emit (PartialFailureEvent or RunSummaryEvent)

    Returns:
        A dictionary representation of the event

    Raises:
        TypeError: If event is not a supported event type
    """
    if isinstance(event, (PartialFailureEvent, RunSummaryEvent)):
        return event.to_dict()

    raise TypeError(f"Unsupported event type: {type(event)}")


def log_event(
    event: PartialFailureEvent | RunSummaryEvent,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Log a structured event to the given logger.

    This function serializes the event to JSON and logs it at INFO level.
    If no logger is provided, it uses the module-level logger.

    Args:
        event: The event to log (PartialFailureEvent or RunSummaryEvent)
        logger: Optional logger instance (uses module logger if None)

    Returns:
        A dictionary representation of the event

    Raises:
        TypeError: If event is not a supported event type
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    event_dict = emit_event(event)
    logger.info(json.dumps(event_dict))

    return event_dict