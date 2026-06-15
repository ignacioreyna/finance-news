from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bora_financial import (
    BoraFinancialConnector,
    build_detail_url,
    build_listing_url,
    classify_bora_entry,
    normalize_bora_entry,
    parse_bora_detail,
    parse_bora_listing,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bora_financial"


class _FakeTransport:
    def __init__(self, responses: dict[str, HttpResponse]) -> None:
        self._responses = responses
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self._responses[request.url]


class BoraFinancialParserTests(unittest.TestCase):
    def test_parse_listing_extracts_notice_urls_and_metadata(self) -> None:
        entries = parse_bora_listing(
            (FIXTURES_DIR / "listing_20260612.html").read_text(encoding="utf-8")
        )

        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0].notice_id, "343047")
        self.assertEqual(entries[0].edition_date, "20260612")
        self.assertEqual(entries[0].organism, "MINISTERIO DE ECONOMÍA")
        self.assertEqual(entries[0].document_type, "resoluciones")
        self.assertEqual(
            entries[2].summary,
            "Procedimiento. Cómputo de plazos en materia impositiva, aduanera y de los recursos de la seguridad social.",
        )

    def test_parse_detail_extracts_body_and_dates(self) -> None:
        detail = parse_bora_detail(
            (FIXTURES_DIR / "detail_343047.html").read_text(encoding="utf-8")
        )

        self.assertEqual(detail.publication_date, datetime(2026, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(detail.signed_date, datetime(2026, 6, 10, tzinfo=timezone.utc))
        self.assertIn("deuda pública", detail.body)
        self.assertIn("energía", detail.body)

    def test_classify_matches_organisms_and_keywords(self) -> None:
        classification = classify_bora_entry(
            organism="BANCO CENTRAL DE LA REPÚBLICA ARGENTINA",
            title="Aviso Oficial",
            body="Se sustancia un sumario en lo cambiario.",
        )

        self.assertTrue(classification.is_relevant)
        self.assertEqual(classification.matched_organizations, ("bcra",))
        self.assertEqual(classification.matched_keywords, ("cambios",))

    def test_normalize_maps_to_source_item(self) -> None:
        entry = parse_bora_listing(
            (FIXTURES_DIR / "listing_20260612.html").read_text(encoding="utf-8")
        )[0]
        detail = parse_bora_detail(
            (FIXTURES_DIR / "detail_343047.html").read_text(encoding="utf-8")
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)

        item = normalize_bora_entry(
            entry=entry,
            detail=detail,
            fetched_at=fetched_at,
            cursor="20260612",
            transport_metadata={"detail_status_code": 200},
        )

        self.assertEqual(item.external_id, "primera-343047")
        self.assertEqual(item.source, "bora")
        self.assertEqual(item.published_at, datetime(2026, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(item.metadata["organism"], "MINISTERIO DE ECONOMÍA")
        self.assertEqual(item.metadata["matched_keywords"], ["deuda", "energia"])
        self.assertEqual(item.provenance.connector, "bora_financial")


class BoraFinancialConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_filters_only_financial_relevant_entries(self) -> None:
        responses = {
            build_listing_url("20260612"): HttpResponse(
                status_code=200,
                url=build_listing_url("20260612"),
                headers={"Content-Type": "text/html"},
                body=(FIXTURES_DIR / "listing_20260612.html").read_bytes(),
            ),
            build_detail_url("343047", "20260612"): HttpResponse(
                status_code=200,
                url=build_detail_url("343047", "20260612"),
                headers={"Content-Type": "text/html"},
                body=(FIXTURES_DIR / "detail_343047.html").read_bytes(),
            ),
            build_detail_url("343048", "20260612"): HttpResponse(
                status_code=200,
                url=build_detail_url("343048", "20260612"),
                headers={"Content-Type": "text/html"},
                body=(FIXTURES_DIR / "detail_343048.html").read_bytes(),
            ),
            build_detail_url("343063", "20260612"): HttpResponse(
                status_code=200,
                url=build_detail_url("343063", "20260612"),
                headers={"Content-Type": "text/html"},
                body=(FIXTURES_DIR / "detail_343063.html").read_bytes(),
            ),
            build_detail_url("343070", "20260612"): HttpResponse(
                status_code=200,
                url=build_detail_url("343070", "20260612"),
                headers={"Content-Type": "text/html"},
                body=(FIXTURES_DIR / "detail_343070.html").read_bytes(),
            ),
        }
        transport = _FakeTransport(responses)
        connector = BoraFinancialConnector(transport=transport)

        result = await connector.fetch_page(cursor="20260612")

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            [item.external_id for item in result.items],
            ["primera-343047", "primera-343063", "primera-343070"],
        )
        self.assertEqual(transport.requests[0].url, build_listing_url("20260612"))
        self.assertEqual(transport.requests[-1].url, build_detail_url("343070", "20260612"))

    async def test_fetch_page_raises_recoverable_for_listing_5xx(self) -> None:
        connector = BoraFinancialConnector(
            transport=_FakeTransport(
                {
                    build_listing_url("20260612"): HttpResponse(
                        status_code=503,
                        url=build_listing_url("20260612"),
                        headers={"Content-Type": "text/html"},
                        body=b"",
                    )
                }
            )
        )

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor="20260612")

    async def test_fetch_page_requires_cursor(self) -> None:
        connector = BoraFinancialConnector(transport=_FakeTransport({}))

        with self.assertRaises(ValueError):
            await connector.fetch_page()


if __name__ == "__main__":
    unittest.main()
