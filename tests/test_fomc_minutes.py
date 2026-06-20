from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fomc_minutes import (
    FomcMinutesConnector,
    ParsedFomcMinutes,
    DEFAULT_TTL_SECONDS,
    _clean_text,
    _normalize_sections,
    _parse_fed_date,
    normalize_fomc_minutes,
    parse_fomc_minutes_html,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fomc_minutes"
MINUTES_URL = "https://www.federalreserve.gov/monetarypolicy/fomcminutes20250618.htm"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FomcMinutesParserTests(unittest.TestCase):
    def test_parse_minutes_html(self) -> None:
        html = (FIXTURES_DIR / "minutes.html").read_text(encoding="utf-8")
        parsed = parse_fomc_minutes_html(html, minutes_url=MINUTES_URL)

        self.assertIsNotNone(parsed.date)
        self.assertEqual(parsed.date, datetime(2025, 6, 18, tzinfo=timezone.utc))
        self.assertIsNotNone(parsed.clean_text)
        self.assertGreater(len(parsed.clean_text), 100)
        self.assertGreater(len(parsed.sections), 0)
        self.assertIn("fomc_minutes_20250618", parsed.external_id)
        self.assertEqual(parsed.minutes_url, MINUTES_URL)

    def test_parse_minutes_sections(self) -> None:
        html = (FIXTURES_DIR / "minutes.html").read_text(encoding="utf-8")
        parsed = parse_fomc_minutes_html(html, minutes_url=MINUTES_URL)

        self.assertIn("financial_markets", parsed.sections)
        self.assertIn("economic_outlook", parsed.sections)
        self.assertIn("staff_outlook", parsed.sections)
        self.assertIn("policy_discussion", parsed.sections)
        self.assertIn("financial_review", parsed.sections)
        self.assertIn("policy_action", parsed.sections)

    def test_parse_minutes_body_content(self) -> None:
        html = (FIXTURES_DIR / "minutes.html").read_text(encoding="utf-8")
        parsed = parse_fomc_minutes_html(html, minutes_url=MINUTES_URL)

        self.assertIsNotNone(parsed.clean_text)
        self.assertIn("Financial markets", parsed.clean_text)
        self.assertIn("economic activity", parsed.clean_text)
        self.assertIn("inflation", parsed.clean_text)

    def test_parse_fed_date_valid(self) -> None:
        result = _parse_fed_date("June 18-19, 2025")
        self.assertEqual(result, datetime(2025, 6, 18, tzinfo=timezone.utc))

        result = _parse_fed_date("March 19-20, 2025")
        self.assertEqual(result, datetime(2025, 3, 19, tzinfo=timezone.utc))

        result = _parse_fed_date("January 28-29, 2026")
        self.assertEqual(result, datetime(2026, 1, 28, tzinfo=timezone.utc))

    def test_parse_fed_date_invalid(self) -> None:
        result = _parse_fed_date(None)
        self.assertIsNone(result)

        result = _parse_fed_date("")
        self.assertIsNone(result)

        result = _parse_fed_date("invalid date")
        self.assertIsNone(result)

    def test_clean_text(self) -> None:
        paragraphs = [
            "Financial markets showed mixed performance during the intermeeting period.",
            "Short",
            "Market participants highlighted uncertainties regarding the path of future rate decisions.",
        ]
        result = _clean_text(paragraphs)
        self.assertNotIn("Short", result)
        self.assertIn("Financial markets", result)
        self.assertIn("uncertainties", result)

    def test_normalize_sections(self) -> None:
        sections = {
            "Developments in Financial Markets and Open Market Operations": "Content about markets...",
            "Discussion of Economic Conditions and Policy": "Content about policy...",
            "Inflation": "Content about inflation...",
        }
        result = _normalize_sections(sections)

        self.assertIn("financial_markets", result)
        self.assertIn("policy_discussion", result)
        self.assertIn("inflation", result)

    def test_normalize_sections_empty(self) -> None:
        result = _normalize_sections({})
        self.assertEqual(result, {})


class FomcMinutesNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        parsed = ParsedFomcMinutes(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            clean_text="Financial markets showed mixed performance...",
            sections={
                "financial_markets": "Content about markets...",
                "inflation": "Content about inflation...",
            },
            external_id="fomc_minutes_20250618",
            minutes_url=MINUTES_URL,
        )

        fetched_at = datetime(2025, 6, 19, 10, 0, tzinfo=timezone.utc)
        item = normalize_fomc_minutes(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=MINUTES_URL,
            cursor=MINUTES_URL,
        )

        self.assertEqual(item.external_id, "fomc_minutes_20250618")
        self.assertEqual(item.source, "fed")
        self.assertEqual(item.published_at, datetime(2025, 6, 18, tzinfo=timezone.utc))
        self.assertIn("FOMC Minutes", item.title)
        self.assertIn("2025-06-18", item.title)
        self.assertIn("Date:", item.summary)
        self.assertEqual(item.url, MINUTES_URL)
        self.assertIn("sections", item.metadata)
        self.assertEqual(item.metadata["section_count"], 2)
        self.assertEqual(item.provenance.connector, "fomc_minutes")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)


class FomcMinutesConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_minutes(self) -> None:
        html = (FIXTURES_DIR / "minutes.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url=MINUTES_URL,
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)

        result = await connector.fetch_page(cursor=MINUTES_URL)

        self.assertEqual(len(result.items), 1)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        item = result.items[0]
        self.assertEqual(item.source, "fed")
        self.assertIn("sections", item.metadata)
        self.assertIn("minutes_url", item.metadata)
        self.assertGreater(item.metadata["section_count"], 0)

    async def test_fetch_page_without_cursor_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=200,
            url=MINUTES_URL,
            headers={"Content-Type": "text/html"},
            body=b"test",
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("cursor", str(cm.exception).lower())

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url=MINUTES_URL,
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)

        result = await connector.fetch_page(cursor=MINUTES_URL)

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url=MINUTES_URL,
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor=MINUTES_URL)

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url=MINUTES_URL,
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor=MINUTES_URL)

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = FomcMinutesConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "fomc_minutes")
        self.assertEqual(connector.source, "fed")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class FomcMinutesFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        html = (FIXTURES_DIR / "minutes.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url=MINUTES_URL,
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcMinutesConnector(transport=transport)
        result = await connector.fetch_page(cursor=MINUTES_URL)

        item = result.items[0]
        self.assertIsNotNone(item.freshness)
        self.assertIsNotNone(item.freshness.fetched_at)
        self.assertIsNotNone(item.freshness.first_seen_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        if item.published_at is not None:
            self.assertEqual(item.freshness.published_at, item.published_at)


class ParsedFomcMinutesSerializationTests(unittest.TestCase):
    def test_to_dict(self) -> None:
        parsed = ParsedFomcMinutes(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            clean_text="Financial markets showed mixed performance...",
            sections={"financial_markets": "Content..."},
            external_id="fomc_minutes_20250618",
            minutes_url=MINUTES_URL,
        )

        result = parsed.to_dict()

        self.assertEqual(result["clean_text"], "Financial markets showed mixed performance...")
        self.assertIn("financial_markets", result["sections"])
        self.assertEqual(result["external_id"], "fomc_minutes_20250618")
        self.assertEqual(result["minutes_url"], MINUTES_URL)
        self.assertEqual(result["date"], "2025-06-18T00:00:00+00:00")

    def test_from_dict(self) -> None:
        data = {
            "date": "2025-06-18T00:00:00+00:00",
            "clean_text": "Financial markets showed mixed performance...",
            "sections": {"financial_markets": "Content..."},
            "external_id": "fomc_minutes_20250618",
            "minutes_url": MINUTES_URL,
        }

        parsed = ParsedFomcMinutes.from_dict(data)

        self.assertEqual(parsed.clean_text, "Financial markets showed mixed performance...")
        self.assertIn("financial_markets", parsed.sections)
        self.assertEqual(parsed.external_id, "fomc_minutes_20250618")
        self.assertEqual(parsed.minutes_url, MINUTES_URL)
        self.assertEqual(parsed.date, datetime(2025, 6, 18, tzinfo=timezone.utc))

    def test_serialization_roundtrip(self) -> None:
        original = ParsedFomcMinutes(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            clean_text="Financial markets showed mixed performance...",
            sections={"financial_markets": "Content...", "inflation": "Inflation content..."},
            external_id="fomc_minutes_20250618",
            minutes_url=MINUTES_URL,
        )

        data = original.to_dict()
        restored = ParsedFomcMinutes.from_dict(data)

        self.assertEqual(original.clean_text, restored.clean_text)
        self.assertEqual(original.sections, restored.sections)
        self.assertEqual(original.external_id, restored.external_id)
        self.assertEqual(original.minutes_url, restored.minutes_url)
        self.assertEqual(original.date, restored.date)


if __name__ == "__main__":
    unittest.main()