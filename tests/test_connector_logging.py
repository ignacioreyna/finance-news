import logging
import logging.handlers
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, "src")

from finance_news.connector_logging import (
    _PAYLOAD_TRUNCATE_THRESHOLD,
    _SECRET_KEYS,
    _redact,
    emit_event,
    log_event,
    PartialFailureEvent,
    RunSummaryEvent,
)


class PartialFailureEventTest(unittest.TestCase):
    """Test PartialFailureEvent functionality."""

    def test_minimal_event_creation(self):
        """Test creating a minimal PartialFailureEvent."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            cursor="cursor-1",
            fetch_url="https://example.com/data",
            error_type="TimeoutError",
            error_message="Connection timed out after 30s",
            recoverable=True,
            fetched_at=fetched_at,
            parser_version="1.0.0",
        )

        event_dict = event.to_dict()

        self.assertEqual(event_dict["event"], "connector.partial_failure")
        self.assertEqual(event_dict["connector"], "test_connector")
        self.assertEqual(event_dict["source"], "test_source")
        self.assertEqual(event_dict["run_id"], "run-123")
        self.assertEqual(event_dict["cursor"], "cursor-1")
        self.assertEqual(event_dict["fetch_url"], "https://example.com/data")
        self.assertEqual(event_dict["error_type"], "TimeoutError")
        self.assertEqual(event_dict["error_message"], "Connection timed out after 30s")
        self.assertTrue(event_dict["recoverable"])
        self.assertEqual(event_dict["fetched_at"], "2026-06-21T10:00:00+00:00")
        self.assertEqual(event_dict["parser_version"], "1.0.0")

    def test_full_event_creation(self):
        """Test creating a PartialFailureEvent with all fields."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            cursor="cursor-1",
            fetch_url="https://example.com/data",
            error_type="HTTPError",
            error_message="Server error 429",
            recoverable=True,
            fetched_at=fetched_at,
            parser_version="1.0.0",
            attempt=2,
            status_code=429,
            items_received=100,
            items_emitted=85,
            items_dropped=15,
            has_more=True,
            next_cursor="cursor-2",
            latency_ms=1234.5,
            retry_after_seconds=5.0,
            response_bytes=10240,
            content_type="application/json",
            trace_id="trace-abc-123",
            sample_external_ids=["id-1", "id-2", "id-3"],
        )

        event_dict = event.to_dict()

        self.assertEqual(event_dict["attempt"], 2)
        self.assertEqual(event_dict["status_code"], 429)
        self.assertEqual(event_dict["items_received"], 100)
        self.assertEqual(event_dict["items_emitted"], 85)
        self.assertEqual(event_dict["items_dropped"], 15)
        self.assertTrue(event_dict["has_more"])
        self.assertEqual(event_dict["next_cursor"], "cursor-2")
        self.assertEqual(event_dict["latency_ms"], 1234.5)
        self.assertEqual(event_dict["retry_after_seconds"], 5.0)
        self.assertEqual(event_dict["response_bytes"], 10240)
        self.assertEqual(event_dict["content_type"], "application/json")
        self.assertEqual(event_dict["trace_id"], "trace-abc-123")
        self.assertEqual(event_dict["sample_external_ids"], ["id-1", "id-2", "id-3"])

    def test_from_dict_minimal(self):
        """Test creating PartialFailureEvent from minimal dict."""
        data = {
            "event": "connector.partial_failure",
            "connector": "test_connector",
            "source": "test_source",
            "run_id": "run-123",
            "cursor": "cursor-1",
            "fetch_url": "https://example.com/data",
            "error_type": "TimeoutError",
            "error_message": "Connection timed out",
            "recoverable": True,
            "fetched_at": "2026-06-21T10:00:00+00:00",
            "parser_version": "1.0.0",
        }

        event = PartialFailureEvent.from_dict(data)

        self.assertEqual(event.connector, "test_connector")
        self.assertEqual(event.source, "test_source")
        self.assertEqual(event.run_id, "run-123")
        self.assertEqual(event.cursor, "cursor-1")
        self.assertEqual(event.fetch_url, "https://example.com/data")
        self.assertEqual(event.error_type, "TimeoutError")
        self.assertEqual(event.error_message, "Connection timed out")
        self.assertTrue(event.recoverable)
        self.assertEqual(event.fetched_at, datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(event.parser_version, "1.0.0")

    def test_from_dict_full(self):
        """Test creating PartialFailureEvent from full dict."""
        data = {
            "event": "connector.partial_failure",
            "connector": "test_connector",
            "source": "test_source",
            "run_id": "run-123",
            "cursor": "cursor-1",
            "fetch_url": "https://example.com/data",
            "error_type": "HTTPError",
            "error_message": "Server error",
            "recoverable": True,
            "fetched_at": "2026-06-21T10:00:00+00:00",
            "parser_version": "1.0.0",
            "attempt": 2,
            "status_code": 429,
            "items_received": 100,
            "items_emitted": 85,
            "items_dropped": 15,
            "has_more": True,
            "next_cursor": "cursor-2",
            "latency_ms": 1234.5,
            "retry_after_seconds": 5.0,
            "response_bytes": 10240,
            "content_type": "application/json",
            "trace_id": "trace-abc-123",
            "sample_external_ids": ["id-1", "id-2"],
        }

        event = PartialFailureEvent.from_dict(data)

        self.assertEqual(event.attempt, 2)
        self.assertEqual(event.status_code, 429)
        self.assertEqual(event.items_received, 100)
        self.assertEqual(event.items_emitted, 85)
        self.assertEqual(event.items_dropped, 15)
        self.assertTrue(event.has_more)
        self.assertEqual(event.next_cursor, "cursor-2")
        self.assertEqual(event.latency_ms, 1234.5)

    def test_round_trip(self):
        """Test to_dict and from_dict round trip."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        original = PartialFailureEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            cursor="cursor-1",
            fetch_url="https://example.com/data",
            error_type="TimeoutError",
            error_message="Connection timed out",
            recoverable=True,
            fetched_at=fetched_at,
            parser_version="1.0.0",
            attempt=2,
            items_emitted=10,
        )

        data = original.to_dict()
        restored = PartialFailureEvent.from_dict(data)

        self.assertEqual(restored.connector, original.connector)
        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.run_id, original.run_id)
        self.assertEqual(restored.cursor, original.cursor)
        self.assertEqual(restored.fetch_url, original.fetch_url)
        self.assertEqual(restored.error_type, original.error_type)
        self.assertEqual(restored.error_message, original.error_message)
        self.assertEqual(restored.recoverable, original.recoverable)
        self.assertEqual(restored.fetched_at, original.fetched_at)
        self.assertEqual(restored.parser_version, original.parser_version)
        self.assertEqual(restored.attempt, original.attempt)
        self.assertEqual(restored.items_emitted, original.items_emitted)

    def test_immutable(self):
        """Test that PartialFailureEvent is immutable."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            cursor=None,
            fetch_url="https://example.com",
            error_type="Error",
            error_message="msg",
            recoverable=False,
            fetched_at=fetched_at,
            parser_version="1.0",
        )

        with self.assertRaises(Exception):
            event.connector = "new"

    def test_event_name_required(self):
        """Test that event field is set correctly."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            cursor=None,
            fetch_url="https://example.com",
            error_type="Error",
            error_message="msg",
            recoverable=False,
            fetched_at=fetched_at,
            parser_version="1.0",
        )

        self.assertEqual(event.to_dict()["event"], "connector.partial_failure")


class RunSummaryEventTest(unittest.TestCase):
    """Test RunSummaryEvent functionality."""

    def test_minimal_event_creation(self):
        """Test creating a minimal RunSummaryEvent."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            pages_fetched=5,
            items_received_total=100,
            items_emitted_total=100,
            items_dropped_total=0,
            recoverable_errors_total=0,
            non_recoverable_errors_total=0,
            stale_items_total=0,
        )

        event_dict = event.to_dict()

        self.assertEqual(event_dict["event"], "connector.run_summary")
        self.assertEqual(event_dict["connector"], "test_connector")
        self.assertEqual(event_dict["source"], "test_source")
        self.assertEqual(event_dict["run_id"], "run-123")
        self.assertEqual(event_dict["started_at"], "2026-06-21T10:00:00+00:00")
        self.assertEqual(event_dict["finished_at"], "2026-06-21T10:05:00+00:00")
        self.assertEqual(event_dict["status"], "success")
        self.assertEqual(event_dict["pages_fetched"], 5)
        self.assertEqual(event_dict["items_received_total"], 100)
        self.assertEqual(event_dict["items_emitted_total"], 100)
        self.assertEqual(event_dict["items_dropped_total"], 0)
        self.assertEqual(event_dict["recoverable_errors_total"], 0)
        self.assertEqual(event_dict["non_recoverable_errors_total"], 0)
        self.assertEqual(event_dict["stale_items_total"], 0)

    def test_partial_success_status(self):
        """Test RunSummaryEvent with partial_success status."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            started_at=started_at,
            finished_at=finished_at,
            status="partial_success",
            pages_fetched=5,
            items_received_total=100,
            items_emitted_total=85,
            items_dropped_total=15,
            recoverable_errors_total=2,
            non_recoverable_errors_total=0,
            stale_items_total=0,
        )

        event_dict = event.to_dict()

        self.assertEqual(event_dict["status"], "partial_success")
        self.assertEqual(event_dict["items_emitted_total"], 85)
        self.assertEqual(event_dict["items_dropped_total"], 15)
        self.assertEqual(event_dict["recoverable_errors_total"], 2)

    def test_failed_status(self):
        """Test RunSummaryEvent with failed status."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 2, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            pages_fetched=1,
            items_received_total=0,
            items_emitted_total=0,
            items_dropped_total=0,
            recoverable_errors_total=0,
            non_recoverable_errors_total=1,
            stale_items_total=0,
        )

        event_dict = event.to_dict()

        self.assertEqual(event_dict["status"], "failed")
        self.assertEqual(event_dict["non_recoverable_errors_total"], 1)

    def test_from_dict(self):
        """Test creating RunSummaryEvent from dict."""
        data = {
            "event": "connector.run_summary",
            "connector": "test_connector",
            "source": "test_source",
            "run_id": "run-123",
            "started_at": "2026-06-21T10:00:00+00:00",
            "finished_at": "2026-06-21T10:05:00+00:00",
            "status": "success",
            "pages_fetched": 5,
            "items_received_total": 100,
            "items_emitted_total": 100,
            "items_dropped_total": 0,
            "recoverable_errors_total": 0,
            "non_recoverable_errors_total": 0,
            "stale_items_total": 0,
        }

        event = RunSummaryEvent.from_dict(data)

        self.assertEqual(event.connector, "test_connector")
        self.assertEqual(event.source, "test_source")
        self.assertEqual(event.run_id, "run-123")
        self.assertEqual(event.started_at, datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(event.finished_at, datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc))
        self.assertEqual(event.status, "success")

    def test_round_trip(self):
        """Test to_dict and from_dict round trip."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        original = RunSummaryEvent(
            connector="test_connector",
            source="test_source",
            run_id="run-123",
            started_at=started_at,
            finished_at=finished_at,
            status="partial_success",
            pages_fetched=10,
            items_received_total=200,
            items_emitted_total=180,
            items_dropped_total=20,
            recoverable_errors_total=3,
            non_recoverable_errors_total=0,
            stale_items_total=5,
        )

        data = original.to_dict()
        restored = RunSummaryEvent.from_dict(data)

        self.assertEqual(restored.connector, original.connector)
        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.run_id, original.run_id)
        self.assertEqual(restored.started_at, original.started_at)
        self.assertEqual(restored.finished_at, original.finished_at)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.pages_fetched, original.pages_fetched)
        self.assertEqual(restored.items_received_total, original.items_received_total)
        self.assertEqual(restored.items_emitted_total, original.items_emitted_total)
        self.assertEqual(restored.items_dropped_total, original.items_dropped_total)
        self.assertEqual(restored.recoverable_errors_total, original.recoverable_errors_total)
        self.assertEqual(restored.non_recoverable_errors_total, original.non_recoverable_errors_total)
        self.assertEqual(restored.stale_items_total, original.stale_items_total)

    def test_immutable(self):
        """Test that RunSummaryEvent is immutable."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            pages_fetched=1,
            items_received_total=10,
            items_emitted_total=10,
            items_dropped_total=0,
            recoverable_errors_total=0,
            non_recoverable_errors_total=0,
            stale_items_total=0,
        )

        with self.assertRaises(Exception):
            event.status = "failed"

    def test_event_name_required(self):
        """Test that event field is set correctly."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            pages_fetched=1,
            items_received_total=10,
            items_emitted_total=10,
            items_dropped_total=0,
            recoverable_errors_total=0,
            non_recoverable_errors_total=0,
            stale_items_total=0,
        )

        self.assertEqual(event.to_dict()["event"], "connector.run_summary")


class RedactionTest(unittest.TestCase):
    """Test secret redaction functionality."""

    def test_redact_api_key(self):
        """Test that api_key is redacted."""
        context = {
            "api_key": "secret-123",
            "other_field": "value",
        }

        redacted = _redact(context)

        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["other_field"], "value")

    def test_redact_multiple_secret_keys(self):
        """Test that all known secret keys are redacted."""
        context = {
            "api_key": "secret-1",
            "token": "secret-2",
            "password": "secret-3",
            "authorization": "Bearer token",
            "safe_field": "safe-value",
        }

        redacted = _redact(context)

        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["token"], "[REDACTED]")
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["authorization"], "[REDACTED]")
        self.assertEqual(redacted["safe_field"], "safe-value")

    def test_redact_case_insensitive(self):
        """Test that secret key matching is case-insensitive."""
        context = {
            "API_KEY": "secret",
            "Api-Key": "secret",
            "TOKEN": "secret",
            "User_ID": "secret",
        }

        redacted = _redact(context)

        self.assertEqual(redacted["API_KEY"], "[REDACTED]")
        self.assertEqual(redacted["Api-Key"], "[REDACTED]")
        self.assertEqual(redacted["TOKEN"], "[REDACTED]")
        self.assertEqual(redacted["User_ID"], "[REDACTED]")

    def test_redact_nested_dicts(self):
        """Test that nested dicts are processed."""
        context = {
            "outer": {
                "inner": {
                    "api_key": "secret",
                },
                "safe": "value",
            },
        }

        redacted = _redact(context)

        self.assertEqual(redacted["outer"]["inner"]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["outer"]["safe"], "value")

    def test_redact_nested_lists(self):
        """Test that lists of dicts are processed."""
        context = {
            "items": [
                {"id": "1", "api_key": "secret-1"},
                {"id": "2", "token": "secret-2"},
                {"id": "3", "safe": "value"},
            ],
        }

        redacted = _redact(context)

        self.assertEqual(redacted["items"][0]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["items"][1]["token"], "[REDACTED]")
        self.assertEqual(redacted["items"][2]["safe"], "value")

    def test_redact_truncate_large_payload(self):
        """Test that large payloads are truncated."""
        large_body = "x" * 500
        context = {
            "raw_body": large_body,
            "other_field": "value",
        }

        redacted = _redact(context)

        self.assertTrue(redacted["raw_body"].startswith("[TRUNCATED:500b:hash:"))
        self.assertEqual(redacted["other_field"], "value")

    def test_redact_keep_small_payload(self):
        """Test that small payloads are kept as-is."""
        small_body = "x" * 100
        context = {
            "raw_body": small_body,
        }

        redacted = _redact(context)

        self.assertEqual(redacted["raw_body"], small_body)

    def test_redact_exactly_threshold(self):
        """Test payload exactly at threshold."""
        exact_body = "x" * _PAYLOAD_TRUNCATE_THRESHOLD
        context = {
            "raw_body": exact_body,
        }

        redacted = _redact(context)

        self.assertEqual(redacted["raw_body"], exact_body)

    def test_redact_threshold_plus_one(self):
        """Test payload one byte over threshold."""
        large_body = "x" * (_PAYLOAD_TRUNCATE_THRESHOLD + 1)
        context = {
            "raw_body": large_body,
        }

        redacted = _redact(context)

        self.assertTrue(redacted["raw_body"].startswith("[TRUNCATED:257b:hash:"))

    def test_redact_payload_field_variants(self):
        """Test that all payload field variants are truncated."""
        large_data = "x" * 500
        context = {
            "raw_body": large_data,
            "payload": large_data,
            "body": large_data,
            "content": large_data,
        }

        redacted = _redact(context)

        for field in ["raw_body", "payload", "body", "content"]:
            self.assertTrue(redacted[field].startswith("[TRUNCATED:500b:hash:"))

    def test_redact_non_string_payload(self):
        """Test that non-string payloads are preserved."""
        context = {
            "payload": 123,
            "body": None,
            "raw_body": ["list", "of", "items"],
        }

        redacted = _redact(context)

        self.assertEqual(redacted["payload"], 123)
        self.assertIsNone(redacted["body"])
        self.assertEqual(redacted["raw_body"], ["list", "of", "items"])

    def test_redact_empty_dict(self):
        """Test that empty dict is handled."""
        redacted = _redact({})
        self.assertEqual(redacted, {})

    def test_redact_none(self):
        """Test that None is handled."""
        redacted = _redact(None)
        self.assertIsNone(redacted)

    def test_redact_non_dict(self):
        """Test that non-dict values are returned as-is."""
        self.assertEqual(_redact(123), 123)
        self.assertEqual(_redact("string"), "string")
        self.assertEqual(_redact([1, 2, 3]), [1, 2, 3])


class EmitEventTest(unittest.TestCase):
    """Test emit_event functionality."""

    def test_emit_partial_failure(self):
        """Test emitting a PartialFailureEvent."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            cursor=None,
            fetch_url="https://example.com",
            error_type="Error",
            error_message="msg",
            recoverable=False,
            fetched_at=fetched_at,
            parser_version="1.0",
        )

        result = emit_event(event)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event"], "connector.partial_failure")
        self.assertEqual(result["connector"], "test")

    def test_emit_run_summary(self):
        """Test emitting a RunSummaryEvent."""
        started_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 6, 21, 10, 5, 0, tzinfo=timezone.utc)
        event = RunSummaryEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            pages_fetched=1,
            items_received_total=10,
            items_emitted_total=10,
            items_dropped_total=0,
            recoverable_errors_total=0,
            non_recoverable_errors_total=0,
            stale_items_total=0,
        )

        result = emit_event(event)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event"], "connector.run_summary")
        self.assertEqual(result["connector"], "test")

    def test_emit_unsupported_type(self):
        """Test that unsupported event types raise TypeError."""
        with self.assertRaises(TypeError):
            emit_event("not an event")

        with self.assertRaises(TypeError):
            emit_event(123)


class LogEventTest(unittest.TestCase):
    """Test log_event functionality."""

    def test_log_event_returns_dict(self):
        """Test that log_event returns the event dict."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            cursor=None,
            fetch_url="https://example.com",
            error_type="Error",
            error_message="msg",
            recoverable=False,
            fetched_at=fetched_at,
            parser_version="1.0",
        )

        result = log_event(event)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event"], "connector.partial_failure")

    def test_log_event_with_custom_logger(self):
        """Test logging with a custom logger."""
        fetched_at = datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc)
        event = PartialFailureEvent(
            connector="test",
            source="test_source",
            run_id="run-1",
            cursor=None,
            fetch_url="https://example.com",
            error_type="Error",
            error_message="msg",
            recoverable=False,
            fetched_at=fetched_at,
            parser_version="1.0",
        )

        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)

        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)

        result = log_event(event, logger=logger)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event"], "connector.partial_failure")

        logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()