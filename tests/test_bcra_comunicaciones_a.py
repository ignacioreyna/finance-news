from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_comunicaciones_a import (
    BcraComunicacionesAConnector,
    build_document_url,
    normalize_bcra_comunicacion_a,
    parse_bcra_comunicacion_a_text,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_comunicaciones_a"


class _StaticExtractor:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def extract_text(self, pdf_bytes: bytes) -> str:
        self.calls += 1
        return self.text


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraComunicacionesAParserTests(unittest.TestCase):
    def test_parse_fixture_a8060(self) -> None:
        parsed = parse_bcra_comunicacion_a_text(
            (FIXTURES_DIR / "A8060.txt").read_text(encoding="utf-8")
        )

        self.assertEqual(parsed.external_id, "A8060")
        self.assertEqual(parsed.number, "8060")
        self.assertEqual(parsed.published_at, datetime(2024, 7, 11, tzinfo=timezone.utc))
        self.assertEqual(
            parsed.title,
            "Suspensión Rueda BCRA. Compra-Venta de Letras Fiscales de Liquidez.",
        )
        self.assertEqual(parsed.circular_reference, "REMON 1-1118")
        self.assertIn("Letras Fiscales de Liquidez", parsed.text)

    def test_parse_fixture_a8083_multiline_title(self) -> None:
        parsed = parse_bcra_comunicacion_a_text(
            (FIXTURES_DIR / "A8083.txt").read_text(encoding="utf-8")
        )

        self.assertEqual(parsed.external_id, "A8083")
        self.assertEqual(
            parsed.title,
            "Compra-Venta de Letras Fiscales de Liquidez (Comunicación “A” 8060). Adecuación de horarios.",
        )
        self.assertEqual(parsed.circular_reference, "REMON 1-1120")

    def test_normalize_populates_required_source_item_fields(self) -> None:
        parsed = parse_bcra_comunicacion_a_text(
            (FIXTURES_DIR / "A8060.txt").read_text(encoding="utf-8")
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
        item = normalize_bcra_comunicacion_a(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=build_document_url("8060"),
            cursor="8060",
            transport_metadata={"status_code": 200},
        )

        self.assertEqual(item.external_id, "A8060")
        self.assertEqual(item.title, parsed.title)
        self.assertEqual(item.url, "https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8060.pdf")
        self.assertEqual(item.metadata["document_number"], "8060")
        self.assertEqual(item.metadata["circular_reference"], "REMON 1-1118")
        self.assertEqual(item.provenance.connector, "bcra_comunicaciones_a")
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(item.freshness.first_seen_at, fetched_at)


class BcraComunicacionesAConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_downloads_pdf_and_returns_normalized_item(self) -> None:
        text = (FIXTURES_DIR / "A8060.txt").read_text(encoding="utf-8")
        extractor = _StaticExtractor(text)
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=build_document_url(8060),
                headers={"Content-Type": "application/pdf"},
                body=b"%PDF-1.4 fake",
            )
        )
        connector = BcraComunicacionesAConnector(
            transport=transport,
            text_extractor=extractor,
        )

        result = await connector.fetch_page(cursor="8060")

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].external_id, "A8060")
        self.assertEqual(
            transport.requests[0].url,
            "https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8060.pdf",
        )
        self.assertEqual(extractor.calls, 1)

    async def test_fetch_page_returns_empty_on_404(self) -> None:
        connector = BcraComunicacionesAConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=404,
                    url=build_document_url(9999),
                    headers={"Content-Type": "application/pdf"},
                    body=b"",
                )
            ),
            text_extractor=_StaticExtractor("unused"),
        )

        result = await connector.fetch_page(cursor="9999")

        self.assertEqual(result.items, ())
        self.assertFalse(result.has_more)

    async def test_fetch_page_raises_recoverable_for_upstream_5xx(self) -> None:
        connector = BcraComunicacionesAConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=503,
                    url=build_document_url(8060),
                    headers={"Content-Type": "application/pdf"},
                    body=b"",
                )
            ),
            text_extractor=_StaticExtractor("unused"),
        )

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor="8060")

    async def test_fetch_page_requires_cursor(self) -> None:
        connector = BcraComunicacionesAConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url=build_document_url(8060),
                    headers={"Content-Type": "application/pdf"},
                    body=b"",
                )
            ),
            text_extractor=_StaticExtractor("unused"),
        )

        with self.assertRaises(ValueError):
            await connector.fetch_page()


if __name__ == "__main__":
    unittest.main()
