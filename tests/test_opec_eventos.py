from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.opec_eventos import (
    DEFAULT_TTL_SECONDS,
    normalize_opec_event,
    OpecEventosConnector,
    parse_opec_press_release_html,
    ParsedOpecEvent,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "opec_eventos"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class OpecEventosParserTests(unittest.TestCase):
    def test_parse_press_release_html_returns_three_events(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        self.assertEqual(len(events), 3)

    def test_parse_event_june_2024_production_cut(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        event_a = next((e for e in events if "2024-06-02" in e.external_id), None)
        self.assertIsNotNone(event_a)

        self.assertEqual(event_a.meeting_date, datetime(2024, 6, 2, tzinfo=timezone.utc))
        self.assertIn("production cuts", event_a.decision.lower())
        self.assertEqual(len(event_a.affected_countries), 8)
        self.assertIn("Saudi Arabia", event_a.affected_countries)
        self.assertIn("Russia", event_a.affected_countries)
        self.assertEqual(event_a.effective_date, datetime(2024, 7, 1, tzinfo=timezone.utc))
        self.assertIsNotNone(event_a.event_url)
        self.assertEqual(event_a.external_id, "opec_event_2024-06-02")

    def test_parse_event_december_2023_maintain_levels(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        event_b = next((e for e in events if "2023-11-30" in e.external_id), None)
        self.assertIsNotNone(event_b)

        self.assertEqual(event_b.meeting_date, datetime(2023, 11, 30, tzinfo=timezone.utc))
        self.assertIn("maintain", event_b.decision.lower())
        self.assertEqual(len(event_b.affected_countries), 8)
        self.assertEqual(event_b.effective_date, datetime(2024, 1, 1, tzinfo=timezone.utc))
        self.assertIsNotNone(event_b.event_url)
        self.assertEqual(event_b.external_id, "opec_event_2023-11-30")

    def test_parse_event_april_2023_voluntary_cuts(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        event_c = next((e for e in events if "2023-04-03" in e.external_id), None)
        self.assertIsNotNone(event_c)

        self.assertEqual(event_c.meeting_date, datetime(2023, 4, 3, tzinfo=timezone.utc))
        self.assertIn("voluntary production cuts", event_c.decision.lower())
        self.assertEqual(len(event_c.affected_countries), 7)
        self.assertIn("Saudi Arabia", event_c.affected_countries)
        self.assertEqual(event_c.effective_date, datetime(2023, 5, 1, tzinfo=timezone.utc))
        self.assertIsNotNone(event_c.event_url)
        self.assertEqual(event_c.external_id, "opec_event_2023-04-03")

    def test_parsed_event_serialization(self) -> None:
        event = ParsedOpecEvent(
            meeting_date=datetime(2024, 6, 2, tzinfo=timezone.utc),
            decision="Extend voluntary production cuts of 2.2 million barrels per day",
            affected_countries=["Saudi Arabia", "Russia", "Iraq"],
            effective_date=datetime(2024, 7, 1, tzinfo=timezone.utc),
            event_url="/opec_web/en/press_room/7658.htm",
            external_id="opec_event_2024-06-02",
        )

        data = event.to_dict()
        self.assertEqual(data["decision"], "Extend voluntary production cuts of 2.2 million barrels per day")
        self.assertEqual(data["meeting_date"], "2024-06-02T00:00:00+00:00")
        self.assertEqual(len(data["affected_countries"]), 3)

        restored = ParsedOpecEvent.from_dict(data)
        self.assertEqual(restored.decision, event.decision)
        self.assertEqual(restored.meeting_date, event.meeting_date)
        self.assertEqual(restored.effective_date, event.effective_date)
        self.assertEqual(restored.affected_countries, event.affected_countries)
        self.assertEqual(restored.external_id, event.external_id)


class OpecEventosNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        parsed = ParsedOpecEvent(
            meeting_date=datetime(2024, 6, 2, tzinfo=timezone.utc),
            decision="Extend voluntary production cuts of 2.2 million barrels per day",
            affected_countries=["Saudi Arabia", "Russia", "Iraq", "United Arab Emirates"],
            effective_date=datetime(2024, 7, 1, tzinfo=timezone.utc),
            event_url="/opec_web/en/press_room/7658.htm",
            external_id="opec_event_2024-06-02",
        )

        fetched_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        item = normalize_opec_event(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.opec.org/opec_web/en/press_room/28.htm",
            cursor=None,
        )

        self.assertEqual(item.external_id, "opec_event_2024-06-02")
        self.assertEqual(item.source, "opec")
        self.assertEqual(item.published_at, datetime(2024, 6, 2, tzinfo=timezone.utc))
        self.assertIn("OPEC Event - 2024-06-02", item.title)
        self.assertIn("production cuts", item.summary.lower())
        self.assertEqual(item.url, "/opec_web/en/press_room/7658.htm")
        self.assertEqual(item.metadata["decision"], "Extend voluntary production cuts of 2.2 million barrels per day")
        self.assertEqual(len(item.metadata["affected_countries"]), 4)
        self.assertEqual(item.metadata["effective_date"], "2024-07-01T00:00:00+00:00")
        self.assertEqual(item.provenance.connector, "opec_eventos")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)

    def test_normalize_event_with_missing_effective_date(self) -> None:
        parsed = ParsedOpecEvent(
            meeting_date=datetime(2023, 11, 30, tzinfo=timezone.utc),
            decision="Maintain current production levels",
            affected_countries=["Saudi Arabia", "Russia"],
            effective_date=None,
            event_url="/opec_web/en/press_room/7532.htm",
            external_id="opec_event_2023-11-30",
        )

        fetched_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        item = normalize_opec_event(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.opec.org/opec_web/en/press_room/28.htm",
            cursor=None,
        )

        self.assertIsNone(item.metadata["effective_date"])
        self.assertNotIn("Effective:", item.summary)


class OpecEventosConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_events(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.opec.org/opec_web/en/press_room/28.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = OpecEventosConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 3)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        first_item = result.items[0]
        self.assertEqual(first_item.source, "opec")
        self.assertIn("decision", first_item.metadata)
        self.assertIn("meeting_date", first_item.metadata)
        self.assertIn("affected_countries", first_item.metadata)

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url="https://www.opec.org/opec_web/en/press_room/28.htm",
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = OpecEventosConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url="https://www.opec.org/opec_web/en/press_room/28.htm",
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = OpecEventosConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url="https://www.opec.org/opec_web/en/press_room/28.htm",
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = OpecEventosConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = OpecEventosConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "opec_eventos")
        self.assertEqual(connector.source, "opec")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class OpecEventosFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.opec.org/opec_web/en/press_room/28.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = OpecEventosConnector(transport=transport)
        result = await connector.fetch_page()

        for item in result.items:
            self.assertIsNotNone(item.freshness)
            self.assertIsNotNone(item.freshness.fetched_at)
            self.assertIsNotNone(item.freshness.first_seen_at)
            self.assertFalse(item.freshness.is_stale)
            self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
            if item.published_at is not None:
                self.assertEqual(item.freshness.published_at, item.published_at)


class OpecEventosAcceptanceCriteriaTests(unittest.TestCase):
    def test_ac1_connector_returns_events_with_required_fields(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        self.assertEqual(len(events), 3)

        for event in events:
            self.assertIsNotNone(event.meeting_date)
            self.assertIsNotNone(event.decision)
            self.assertIsNotNone(event.affected_countries)
            self.assertIsInstance(event.affected_countries, list)
            self.assertGreater(len(event.affected_countries), 0)
            self.assertIsNotNone(event.effective_date)
            self.assertIsNotNone(event.event_url)
            self.assertIsNotNone(event.external_id)

    def test_ac2_offline_fixture_parsing(self) -> None:
        html = (FIXTURES_DIR / "press_release.html").read_text(encoding="utf-8")
        events = parse_opec_press_release_html(html)

        self.assertEqual(len(events), 3)

        event_a = next((e for e in events if "2024-06-02" in e.external_id), None)
        self.assertIsNotNone(event_a)
        self.assertEqual(event_a.meeting_date, datetime(2024, 6, 2, tzinfo=timezone.utc))
        self.assertIn("production cuts", event_a.decision.lower())
        self.assertEqual(len(event_a.affected_countries), 8)
        self.assertEqual(event_a.effective_date, datetime(2024, 7, 1, tzinfo=timezone.utc))
        self.assertIsNotNone(event_a.event_url)

        event_b = next((e for e in events if "2023-11-30" in e.external_id), None)
        self.assertIsNotNone(event_b)
        self.assertEqual(event_b.meeting_date, datetime(2023, 11, 30, tzinfo=timezone.utc))
        self.assertIn("maintain", event_b.decision.lower())

        event_c = next((e for e in events if "2023-04-03" in e.external_id), None)
        self.assertIsNotNone(event_c)
        self.assertEqual(event_c.meeting_date, datetime(2023, 4, 3, tzinfo=timezone.utc))
        self.assertIn("voluntary", event_c.decision.lower())

    def test_ac3_momr_limitation_documented(self) -> None:
        from finance_news.connectors.opec_eventos import __doc__

        self.assertIsNotNone(__doc__)
        self.assertIn("MOMR", __doc__)
        self.assertIn("NOT freely available", __doc__)
        self.assertIn("paid", __doc__)


if __name__ == "__main__":
    unittest.main()