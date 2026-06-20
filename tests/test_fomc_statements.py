from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fomc_statements import (
    FomcStatementsConnector,
    ParsedFomcStatement,
    DEFAULT_TTL_SECONDS,
    _classify_decision,
    _clean_body_text,
    _extract_target_range,
    _extract_votes,
    _parse_fed_date,
    normalize_fomc_statement,
    parse_fomc_statement_html,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fomc_statements"
STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20250618a.htm"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FomcStatementsParserTests(unittest.TestCase):
    def test_parse_statement_html(self) -> None:
        html = (FIXTURES_DIR / "statement.html").read_text(encoding="utf-8")
        parsed = parse_fomc_statement_html(html, statement_url=STATEMENT_URL)

        self.assertIsNotNone(parsed.date)
        self.assertEqual(parsed.date, datetime(2025, 6, 18, tzinfo=timezone.utc))
        self.assertEqual(parsed.decision, "raise")
        self.assertEqual(parsed.target_range, "5-1/4 to 5-1/2")
        self.assertEqual(parsed.votes_for, 8)
        self.assertEqual(parsed.votes_against, 2)
        self.assertIsNotNone(parsed.body_text)
        self.assertGreater(len(parsed.body_text), 100)
        self.assertIn("fomc_statement_20250618", parsed.external_id)
        self.assertEqual(parsed.statement_url, STATEMENT_URL)

    def test_parse_statement_body_content(self) -> None:
        html = (FIXTURES_DIR / "statement.html").read_text(encoding="utf-8")
        parsed = parse_fomc_statement_html(html, statement_url=STATEMENT_URL)

        self.assertIsNotNone(parsed.body_text)
        self.assertIn("maximum employment", parsed.body_text.lower())
        self.assertIn("inflation", parsed.body_text.lower())
        self.assertIn("federal funds rate", parsed.body_text.lower())

    def test_parse_fed_date_valid(self) -> None:
        result = _parse_fed_date("June 18, 2025")
        self.assertEqual(result, datetime(2025, 6, 18, tzinfo=timezone.utc))

        result = _parse_fed_date("March 19, 2025")
        self.assertEqual(result, datetime(2025, 3, 19, tzinfo=timezone.utc))

        result = _parse_fed_date("January 28, 2026")
        self.assertEqual(result, datetime(2026, 1, 28, tzinfo=timezone.utc))

    def test_parse_fed_date_invalid(self) -> None:
        result = _parse_fed_date(None)
        self.assertIsNone(result)

        result = _parse_fed_date("")
        self.assertIsNone(result)

        result = _parse_fed_date("invalid date")
        self.assertIsNone(result)

    def test_classify_decision_raise(self) -> None:
        text = "The Committee decided to raise the target range for the federal funds rate"
        result = _classify_decision(text)
        self.assertEqual(result, "raise")

        text = "The Committee decided to increase the target range"
        result = _classify_decision(text)
        self.assertEqual(result, "raise")

    def test_classify_decision_cut(self) -> None:
        text = "The Committee decided to lower the target range for the federal funds rate"
        result = _classify_decision(text)
        self.assertEqual(result, "cut")

        text = "The Committee decided to cut the target range"
        result = _classify_decision(text)
        self.assertEqual(result, "cut")

        text = "The Committee decided to decrease the target range"
        result = _classify_decision(text)
        self.assertEqual(result, "cut")

    def test_classify_decision_hold(self) -> None:
        text = "The Committee decided to maintain the target range for the federal funds rate"
        result = _classify_decision(text)
        self.assertEqual(result, "hold")

        text = "The target range for the federal funds rate remains unchanged"
        result = _classify_decision(text)
        self.assertEqual(result, "hold")

    def test_classify_decision_unknown(self) -> None:
        text = "The Committee met today"
        result = _classify_decision(text)
        self.assertEqual(result, "unknown")

    def test_extract_target_range(self) -> None:
        text = "raise the target range for the federal funds rate to 5-1/4 to 5-1/2 percent"
        result = _extract_target_range(text)
        self.assertEqual(result, "5-1/4 to 5-1/2")

        text = "lower the target range for the federal funds rate to 4-1/2 to 4-3/4 percent"
        result = _extract_target_range(text)
        self.assertEqual(result, "4-1/2 to 4-3/4")

    def test_extract_votes(self) -> None:
        text = """Voting for the FOMC monetary policy action were: Jerome H. Powell, Chair; John C. Williams, Vice Chair; Michael S. Barr. Voting against the action was Thomas I. Barkin."""
        votes_for, votes_against = _extract_votes(text)
        self.assertEqual(votes_for, 3)
        self.assertEqual(votes_against, 1)

        text = """Voting for the FOMC monetary policy action were: Powell and Williams."""
        votes_for, votes_against = _extract_votes(text)
        self.assertEqual(votes_for, 2)
        self.assertEqual(votes_against, 0)

    def test_clean_body_text(self) -> None:
        paragraphs = [
            "The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent over the longer run.",
            "Short",
            "The Committee judges that the risks to achieving its employment and inflation goals are roughly in balance.",
        ]
        result = _clean_body_text(paragraphs)
        self.assertNotIn("Short", result)
        self.assertIn("maximum employment", result)
        self.assertIn("risks", result)


class FomcStatementsNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        parsed = ParsedFomcStatement(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            decision="raise",
            target_range="5-1/4 to 5-1/2",
            votes_for=8,
            votes_against=2,
            body_text="The Committee seeks to achieve maximum employment...",
            external_id="fomc_statement_20250618",
            statement_url=STATEMENT_URL,
        )

        fetched_at = datetime(2025, 6, 19, 10, 0, tzinfo=timezone.utc)
        item = normalize_fomc_statement(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=STATEMENT_URL,
            cursor=STATEMENT_URL,
        )

        self.assertEqual(item.external_id, "fomc_statement_20250618")
        self.assertEqual(item.source, "fed")
        self.assertEqual(item.published_at, datetime(2025, 6, 18, tzinfo=timezone.utc))
        self.assertIn("FOMC Statement", item.title)
        self.assertIn("2025-06-18", item.title)
        self.assertIn("raise", item.summary)
        self.assertEqual(item.url, STATEMENT_URL)
        self.assertEqual(item.metadata["decision"], "raise")
        self.assertEqual(item.metadata["target_range"], "5-1/4 to 5-1/2")
        self.assertEqual(item.metadata["votes_for"], 8)
        self.assertEqual(item.metadata["votes_against"], 2)
        self.assertEqual(item.provenance.connector, "fomc_statements")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)


class FomcStatementsConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_statement(self) -> None:
        html = (FIXTURES_DIR / "statement.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url=STATEMENT_URL,
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)

        result = await connector.fetch_page(cursor=STATEMENT_URL)

        self.assertEqual(len(result.items), 1)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        item = result.items[0]
        self.assertEqual(item.source, "fed")
        self.assertIn("decision", item.metadata)
        self.assertIn("target_range", item.metadata)
        self.assertIn("votes_for", item.metadata)
        self.assertIn("votes_against", item.metadata)

    async def test_fetch_page_without_cursor_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=200,
            url=STATEMENT_URL,
            headers={"Content-Type": "text/html"},
            body=b"test",
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("cursor", str(cm.exception).lower())

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url=STATEMENT_URL,
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)

        result = await connector.fetch_page(cursor=STATEMENT_URL)

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url=STATEMENT_URL,
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor=STATEMENT_URL)

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url=STATEMENT_URL,
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor=STATEMENT_URL)

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = FomcStatementsConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "fomc_statements")
        self.assertEqual(connector.source, "fed")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class FomcStatementsFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        html = (FIXTURES_DIR / "statement.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url=STATEMENT_URL,
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FomcStatementsConnector(transport=transport)
        result = await connector.fetch_page(cursor=STATEMENT_URL)

        item = result.items[0]
        self.assertIsNotNone(item.freshness)
        self.assertIsNotNone(item.freshness.fetched_at)
        self.assertIsNotNone(item.freshness.first_seen_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        if item.published_at is not None:
            self.assertEqual(item.freshness.published_at, item.published_at)


class ParsedFomcStatementSerializationTests(unittest.TestCase):
    def test_to_dict(self) -> None:
        parsed = ParsedFomcStatement(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            decision="raise",
            target_range="5-1/4 to 5-1/2",
            votes_for=8,
            votes_against=2,
            body_text="The Committee seeks to achieve maximum employment...",
            external_id="fomc_statement_20250618",
            statement_url=STATEMENT_URL,
        )

        result = parsed.to_dict()

        self.assertEqual(result["decision"], "raise")
        self.assertEqual(result["target_range"], "5-1/4 to 5-1/2")
        self.assertEqual(result["votes_for"], 8)
        self.assertEqual(result["votes_against"], 2)
        self.assertEqual(result["external_id"], "fomc_statement_20250618")
        self.assertEqual(result["statement_url"], STATEMENT_URL)
        self.assertEqual(result["date"], "2025-06-18T00:00:00+00:00")

    def test_from_dict(self) -> None:
        data = {
            "date": "2025-06-18T00:00:00+00:00",
            "decision": "raise",
            "target_range": "5-1/4 to 5-1/2",
            "votes_for": 8,
            "votes_against": 2,
            "body_text": "The Committee seeks to achieve maximum employment...",
            "external_id": "fomc_statement_20250618",
            "statement_url": STATEMENT_URL,
        }

        parsed = ParsedFomcStatement.from_dict(data)

        self.assertEqual(parsed.decision, "raise")
        self.assertEqual(parsed.target_range, "5-1/4 to 5-1/2")
        self.assertEqual(parsed.votes_for, 8)
        self.assertEqual(parsed.votes_against, 2)
        self.assertEqual(parsed.external_id, "fomc_statement_20250618")
        self.assertEqual(parsed.statement_url, STATEMENT_URL)
        self.assertEqual(parsed.date, datetime(2025, 6, 18, tzinfo=timezone.utc))

    def test_serialization_roundtrip(self) -> None:
        original = ParsedFomcStatement(
            date=datetime(2025, 6, 18, tzinfo=timezone.utc),
            decision="raise",
            target_range="5-1/4 to 5-1/2",
            votes_for=8,
            votes_against=2,
            body_text="The Committee seeks to achieve maximum employment...",
            external_id="fomc_statement_20250618",
            statement_url=STATEMENT_URL,
        )

        data = original.to_dict()
        restored = ParsedFomcStatement.from_dict(data)

        self.assertEqual(original.decision, restored.decision)
        self.assertEqual(original.target_range, restored.target_range)
        self.assertEqual(original.votes_for, restored.votes_for)
        self.assertEqual(original.votes_against, restored.votes_against)
        self.assertEqual(original.external_id, restored.external_id)
        self.assertEqual(original.statement_url, restored.statement_url)
        self.assertEqual(original.date, restored.date)


if __name__ == "__main__":
    unittest.main()