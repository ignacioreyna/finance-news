from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fomc_calendario import (
    DEFAULT_TTL_SECONDS,
    FomcCalendarioConnector,
    normalize_fomc_meeting,
    parse_fomc_calendario_html,
    ParsedFomcMeeting,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fomc_calendario"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FomcCalendarioParserTests(unittest.TestCase):
    def test_parse_calendar_html_returns_three_meetings(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        self.assertEqual(len(meetings), 3)

    def test_parse_meeting_a_regular_with_statement_and_minutes(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        meeting_a = next((m for m in meetings if "2025-01-28" in m.external_id), None)
        self.assertIsNotNone(meeting_a)

        self.assertEqual(meeting_a.date, datetime(2025, 1, 28, tzinfo=timezone.utc))
        self.assertEqual(meeting_a.meeting_type, "regular")
        self.assertFalse(meeting_a.has_sep)
        self.assertIsNotNone(meeting_a.statement_url)
        self.assertIsNotNone(meeting_a.minutes_url)
        self.assertIsNone(meeting_a.sep_url)
        self.assertIsNone(meeting_a.implementation_note_url)
        self.assertIsNone(meeting_a.press_conference_url)
        self.assertEqual(meeting_a.external_id, "fomc_meeting_2025-01-28")

    def test_parse_meeting_b_with_sep_and_press_conference(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        meeting_b = next((m for m in meetings if "2025-03-18" in m.external_id), None)
        self.assertIsNotNone(meeting_b)

        self.assertEqual(meeting_b.date, datetime(2025, 3, 18, tzinfo=timezone.utc))
        self.assertEqual(meeting_b.meeting_type, "sep")
        self.assertTrue(meeting_b.has_sep)
        self.assertIsNotNone(meeting_b.statement_url)
        self.assertIsNone(meeting_b.minutes_url)
        self.assertIsNotNone(meeting_b.sep_url)
        self.assertIsNotNone(meeting_b.implementation_note_url)
        self.assertIsNotNone(meeting_b.press_conference_url)
        self.assertEqual(meeting_b.external_id, "fomc_meeting_2025-03-18")

    def test_parse_meeting_c_missing_minutes(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        meeting_c = next((m for m in meetings if "2025-06-10" in m.external_id), None)
        self.assertIsNotNone(meeting_c)

        self.assertEqual(meeting_c.date, datetime(2025, 6, 10, tzinfo=timezone.utc))
        self.assertEqual(meeting_c.meeting_type, "regular")
        self.assertFalse(meeting_c.has_sep)
        self.assertIsNotNone(meeting_c.statement_url)
        self.assertIsNone(meeting_c.minutes_url)
        self.assertIsNone(meeting_c.sep_url)
        self.assertIsNone(meeting_c.implementation_note_url)
        self.assertIsNone(meeting_c.press_conference_url)
        self.assertEqual(meeting_c.external_id, "fomc_meeting_2025-06-10")

    def test_parsed_meeting_serialization(self) -> None:
        meeting = ParsedFomcMeeting(
            date=datetime(2025, 1, 28, tzinfo=timezone.utc),
            meeting_type="regular",
            has_sep=False,
            statement_url="/newsevents/pressreleases/monetary20250129a.htm",
            minutes_url="/monetarypolicy/fomcminutes20250129.htm",
            sep_url=None,
            implementation_note_url=None,
            press_conference_url=None,
            external_id="fomc_meeting_2025-01-28",
        )

        data = meeting.to_dict()
        self.assertEqual(data["meeting_type"], "regular")
        self.assertEqual(data["date"], "2025-01-28T00:00:00+00:00")
        self.assertFalse(data["has_sep"])

        restored = ParsedFomcMeeting.from_dict(data)
        self.assertEqual(restored.meeting_type, meeting.meeting_type)
        self.assertEqual(restored.date, meeting.date)
        self.assertEqual(restored.external_id, meeting.external_id)


class FomcCalendarioNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        parsed = ParsedFomcMeeting(
            date=datetime(2025, 1, 28, tzinfo=timezone.utc),
            meeting_type="regular",
            has_sep=False,
            statement_url="/newsevents/pressreleases/monetary20250129a.htm",
            minutes_url="/monetarypolicy/fomcminutes20250129.htm",
            sep_url=None,
            implementation_note_url=None,
            press_conference_url=None,
            external_id="fomc_meeting_2025-01-28",
        )

        fetched_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)
        item = normalize_fomc_meeting(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            cursor=None,
        )

        self.assertEqual(item.external_id, "fomc_meeting_2025-01-28")
        self.assertEqual(item.source, "fed")
        self.assertEqual(item.published_at, datetime(2025, 1, 28, tzinfo=timezone.utc))
        self.assertIn("FOMC Meeting - 2025-01-28", item.title)
        self.assertIn("regular", item.summary)
        self.assertEqual(item.url, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
        self.assertEqual(item.metadata["meeting_type"], "regular")
        self.assertFalse(item.metadata["has_sep"])
        self.assertEqual(item.metadata["statement_url"], "/newsevents/pressreleases/monetary20250129a.htm")
        self.assertEqual(item.metadata["minutes_url"], "/monetarypolicy/fomcminutes20250129.htm")
        self.assertIsNone(item.metadata["sep_url"])
        self.assertEqual(item.provenance.connector, "fomc_calendario")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)

    def test_normalize_meeting_with_sep(self) -> None:
        parsed = ParsedFomcMeeting(
            date=datetime(2025, 3, 18, tzinfo=timezone.utc),
            meeting_type="sep",
            has_sep=True,
            statement_url="/newsevents/pressreleases/monetary20250319a.htm",
            minutes_url=None,
            sep_url="/monetarypolicy/fomcprojtabl20250319.htm",
            implementation_note_url="/newsevents/pressreleases/monetarypolicyimplementationnote20250319a.htm",
            press_conference_url="/mediacenter/files/FOMCpresconf20250319.pdf",
            external_id="fomc_meeting_2025-03-18",
        )

        fetched_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)
        item = normalize_fomc_meeting(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            cursor=None,
        )

        self.assertIn("(with SEP)", item.title)
        self.assertIn("Includes SEP/Projections", item.summary)
        self.assertTrue(item.metadata["has_sep"])
        self.assertEqual(item.metadata["meeting_type"], "sep")
        self.assertEqual(item.metadata["sep_url"], "/monetarypolicy/fomcprojtabl20250319.htm")
        self.assertEqual(item.metadata["implementation_note_url"], "/newsevents/pressreleases/monetarypolicyimplementationnote20250319a.htm")
        self.assertEqual(item.metadata["press_conference_url"], "/mediacenter/files/FOMCpresconf20250319.pdf")

    def test_normalize_meeting_missing_child_urls(self) -> None:
        parsed = ParsedFomcMeeting(
            date=datetime(2025, 6, 10, tzinfo=timezone.utc),
            meeting_type="regular",
            has_sep=False,
            statement_url="/newsevents/pressreleases/monetary20250611a.htm",
            minutes_url=None,
            sep_url=None,
            implementation_note_url=None,
            press_conference_url=None,
            external_id="fomc_meeting_2025-06-10",
        )

        fetched_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)
        item = normalize_fomc_meeting(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            cursor=None,
        )

        self.assertEqual(item.metadata["statement_url"], "/newsevents/pressreleases/monetary20250611a.htm")
        self.assertIsNone(item.metadata["minutes_url"])
        self.assertIsNone(item.metadata["sep_url"])
        self.assertIsNone(item.metadata["implementation_note_url"])
        self.assertIsNone(item.metadata["press_conference_url"])


class FomcCalendarioConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_meetings(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcCalendarioConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 3)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        first_item = result.items[0]
        self.assertEqual(first_item.source, "fed")
        self.assertIn("meeting_type", first_item.metadata)
        self.assertIn("has_sep", first_item.metadata)

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = FomcCalendarioConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = FomcCalendarioConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = FomcCalendarioConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = FomcCalendarioConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "fomc_calendario")
        self.assertEqual(connector.source, "fed")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class FomcCalendarioFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcCalendarioConnector(transport=transport)
        result = await connector.fetch_page()

        for item in result.items:
            self.assertIsNotNone(item.freshness)
            self.assertIsNotNone(item.freshness.fetched_at)
            self.assertIsNotNone(item.freshness.first_seen_at)
            self.assertFalse(item.freshness.is_stale)
            self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
            if item.published_at is not None:
                self.assertEqual(item.freshness.published_at, item.published_at)


class FomcCalendarioAcceptanceCriteriaTests(unittest.TestCase):
    def test_ac1_connector_returns_normalized_meetings(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        self.assertEqual(len(meetings), 3)

        for meeting in meetings:
            self.assertIsNotNone(meeting.date)
            self.assertIsNotNone(meeting.meeting_type)
            self.assertIsNotNone(meeting.external_id)
            self.assertIsInstance(meeting.has_sep, bool)
            self.assertIsInstance(meeting.statement_url, (str, type(None)))
            self.assertIsInstance(meeting.minutes_url, (str, type(None)))
            self.assertIsInstance(meeting.sep_url, (str, type(None)))
            self.assertIsInstance(meeting.implementation_note_url, (str, type(None)))
            self.assertIsInstance(meeting.press_conference_url, (str, type(None)))

    def test_ac2_offline_fixture_parsing(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        self.assertEqual(len(meetings), 3)

        meeting_a = next((m for m in meetings if "2025-01-28" in m.external_id), None)
        self.assertIsNotNone(meeting_a)
        self.assertIsNotNone(meeting_a.statement_url)
        self.assertIsNotNone(meeting_a.minutes_url)

        meeting_b = next((m for m in meetings if "2025-03-18" in m.external_id), None)
        self.assertIsNotNone(meeting_b)
        self.assertTrue(meeting_b.has_sep)
        self.assertIsNotNone(meeting_b.sep_url)
        self.assertIsNotNone(meeting_b.press_conference_url)

        meeting_c = next((m for m in meetings if "2025-06-10" in m.external_id), None)
        self.assertIsNotNone(meeting_c)
        self.assertIsNone(meeting_c.minutes_url)

    def test_ac3_sep_and_missing_urls_no_crash(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        meetings = parse_fomc_calendario_html(html)

        meeting_b = next((m for m in meetings if "2025-03-18" in m.external_id), None)
        self.assertIsNotNone(meeting_b)
        self.assertTrue(meeting_b.has_sep)

        meeting_c = next((m for m in meetings if "2025-06-10" in m.external_id), None)
        self.assertIsNotNone(meeting_c)
        self.assertIsNone(meeting_c.minutes_url)

        fetched_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)

        item_b = normalize_fomc_meeting(
            parsed=meeting_b,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            cursor=None,
        )

        self.assertTrue(item_b.metadata["has_sep"])
        self.assertIsNotNone(item_b.metadata["sep_url"])

        item_c = normalize_fomc_meeting(
            parsed=meeting_c,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            cursor=None,
        )

        self.assertIsNone(item_c.metadata["minutes_url"])


if __name__ == "__main__":
    unittest.main()