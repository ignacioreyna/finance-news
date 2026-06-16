from __future__ import annotations

import hashlib
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.connectors.tesoro_licitaciones import (
    BASE_ORIGIN,
    CONNECTOR_NAME,
    DEFAULT_PAGE_URL,
    ParsedTesoroInstrumento,
    ParsedTesoroLink,
    TesoroLicitacionesConnector,
    normalize_tesoro_instrumento,
    parse_tesoro_licitaciones_html,
    parse_tesoro_listing_html,
    resolve_download_link,
    resolve_download_links,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "tesoro_licitaciones"
RESULTADO_URL = (
    "https://www.argentina.gob.ar/noticias/"
    "resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-"
    "nacional-denominados-4"
)
LLAMADO_URL = (
    "https://www.argentina.gob.ar/noticias/"
    "llamado-licitacion-de-instrumentos-del-tesoro-nacional-denominados-"
    "en-pesos-y-en-dolares-5"
)


def _read(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class TesoroResultadoParserTests(unittest.TestCase):
    """AC#1: normalized resultado events per instrument with fecha/moneda/monto/url."""

    def setUp(self) -> None:
        self.rows = parse_tesoro_licitaciones_html(
            _read("resultado.html"), page_url=RESULTADO_URL
        )

    def test_detects_resultado_event_type_and_fecha(self) -> None:
        self.assertGreater(len(self.rows), 0)
        self.assertTrue(all(r.event_type == "resultado" for r in self.rows))
        self.assertEqual(self.rows[0].fecha, datetime(2026, 6, 10, tzinfo=timezone.utc))

    def test_first_instrument_official_fields_are_precise(self) -> None:
        first = self.rows[0]
        self.assertIn("DICIEMBRE DE 2028", first.instrumento)
        self.assertEqual(first.moneda, "ARS")
        self.assertEqual(first.vno_ofertado, 1940448.0)
        self.assertEqual(first.vno_adjudicado, 1624039.0)
        self.assertEqual(first.ve_adjudicado, 1445395.0)
        self.assertEqual(first.precio_corte, 890.0)
        self.assertEqual(first.tirea, 4.76)

    def test_includes_usd_instrument(self) -> None:
        usd = [r for r in self.rows if r.moneda == "USD"]
        self.assertGreater(len(usd), 0)
        # Dolar-linked / BONAR USD carry USD-denominated VNO.
        self.assertTrue(any(r.vno_adjudicado is not None for r in usd))

    def test_every_event_carries_fecha_moneda_monto_and_url(self) -> None:
        # AC#1: every normalized event has fecha, moneda, a monto and the url.
        for row in self.rows:
            self.assertIsNotNone(row.fecha)
            self.assertIn(row.moneda, {"ARS", "USD"})
            self.assertEqual(row.source_url, RESULTADO_URL)
            monto = row.ve_adjudicado or row.vno_adjudicado or row.monto_maximo
            self.assertIsNotNone(monto)

    def test_summary_total_rows_are_excluded(self) -> None:
        # Totals/cantidad summary rows must not leak as instruments.
        names = " ".join(r.instrumento for r in self.rows).lower()
        self.assertNotIn("cantidad de ofertas", names)


class TesoroLlamadoParserTests(unittest.TestCase):
    """AC#1: llamado events carry instrumento, fecha, moneda, monto, vencimiento."""

    def setUp(self) -> None:
        self.rows = parse_tesoro_licitaciones_html(
            _read("llamado.html"), page_url=LLAMADO_URL
        )

    def test_detects_llamado_event_type_and_fecha(self) -> None:
        self.assertGreater(len(self.rows), 0)
        self.assertTrue(all(r.event_type == "llamado" for r in self.rows))
        self.assertEqual(self.rows[0].fecha, datetime(2026, 6, 8, tzinfo=timezone.utc))

    def test_llamado_carries_vencimiento_and_official_monto_text(self) -> None:
        first = self.rows[0]
        self.assertIsNotNone(first.vencimiento)
        self.assertRegex(first.vencimiento, r"\d{2}/\d{2}/\d{4}")
        # Official monto statement is textual on llamado pages and must be kept.
        self.assertIsNotNone(first.monto_maximo_text)
        self.assertEqual(first.source_url, LLAMADO_URL)


class TesoroNormalizeTests(unittest.TestCase):
    """AC#3: distinguish official vs derived; preserve source_url/retrieved_at/raw_hash."""

    def _resultado_item(self) -> object:
        rows = parse_tesoro_licitaciones_html(
            _read("resultado.html"), page_url=RESULTADO_URL
        )
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        return normalize_tesoro_instrumento(
            parsed=rows[0],
            fetched_at=fetched_at,
            fetch_url=RESULTADO_URL,
            raw_hash="0" * 64,
        )

    def test_official_fields_separated_from_derived(self) -> None:
        item = self._resultado_item()
        md = item.metadata
        # Official data straight from the page.
        self.assertEqual(md["data_classification"], "official_primary")
        self.assertIn("vno_adjudicado", md["official"])
        self.assertEqual(md["official"]["vno_adjudicado"], 1624039.0)
        # Derived value is computed and explicitly flagged.
        self.assertIn("derived", md)
        self.assertIn("adjudication_rate", md["derived"])
        self.assertAlmostEqual(
            md["derived"]["adjudication_rate"], 1624039.0 / 1940448.0, places=4
        )
        self.assertTrue(md["derived"]["is_derived"])

    def test_llamado_has_no_derived_metric(self) -> None:
        rows = parse_tesoro_licitaciones_html(
            _read("llamado.html"), page_url=LLAMADO_URL
        )
        item = normalize_tesoro_instrumento(
            parsed=rows[0],
            fetched_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
            fetch_url=LLAMADO_URL,
            raw_hash="1" * 64,
        )
        self.assertEqual(item.metadata["data_classification"], "official_primary")
        self.assertFalse(item.metadata["derived"]["is_derived"])

    def test_provenance_preserves_source_url_retrieved_at_raw_hash(self) -> None:
        item = self._resultado_item()
        prov = item.provenance
        self.assertEqual(prov.connector, CONNECTOR_NAME)
        # source_url
        self.assertEqual(prov.fetch_url, RESULTADO_URL)
        self.assertEqual(prov.canonical_url, RESULTADO_URL)
        # retrieved_at
        self.assertEqual(prov.fetched_at, datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc))
        # raw_hash
        self.assertEqual(prov.transport_metadata["raw_hash"], "0" * 64)
        self.assertRegex(
            prov.transport_metadata["raw_hash"], r"^[0-9a-f]{64}$"
        )
        # freshness carries published_at + ttl
        self.assertEqual(item.freshness.published_at, item.published_at)
        self.assertIsNotNone(item.freshness.ttl_seconds)

    def test_instrumento_dataclass_roundtrip(self) -> None:
        rows = parse_tesoro_licitaciones_html(
            _read("resultado.html"), page_url=RESULTADO_URL
        )
        first = rows[0]
        restored = ParsedTesoroInstrumento.from_dict(first.to_dict())
        self.assertEqual(restored, first)
        self.assertEqual(restored.external_id, first.external_id)

    def test_link_dataclass_roundtrip(self) -> None:
        link = ParsedTesoroLink(text="x", url="https://x/y.pdf", kind="download")
        self.assertEqual(ParsedTesoroLink.from_dict(link.to_dict()), link)


class TesoroListingAndDownloadTests(unittest.TestCase):
    """AC#2: offline HTML listing fixtures + download-link resolution cases."""

    def test_parse_hub_listing_resolves_subpage_links(self) -> None:
        links = parse_tesoro_listing_html(_read("listing.html"), base_url=BASE_ORIGIN)
        urls = {link.url for link in links}
        self.assertIn(
            "https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-"
            "letras-y-bonos-del-tesoro/cronograma-2026",
            urls,
        )
        self.assertIn(
            "https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-"
            "letras-y-bonos-del-tesoro/historico-de-resultados",
            urls,
        )
        self.assertIn(
            "https://www.argentina.gob.ar/economia/finanzas/deudapublica/"
            "colocacionesdedeuda",
            urls,
        )
        self.assertTrue(all(link.kind == "page" for link in links))

    def test_resolve_download_links_from_cronograma(self) -> None:
        downloads = resolve_download_links(
            _read("cronograma.html"), base_url=BASE_ORIGIN
        )
        self.assertEqual(len(downloads), 3)
        self.assertTrue(
            any(u.endswith("cronograma-licitaciones-2026.xlsx") for u in downloads)
        )
        self.assertTrue(
            any(u.endswith("resultados-licitacion-2026-06-30.pdf") for u in downloads)
        )
        self.assertTrue(
            any(u.endswith("colocaciones-deuda-2026-07.csv") for u in downloads)
        )

    def test_resolve_download_link_relative_and_absolute(self) -> None:
        relative = resolve_download_link(
            "/sites/default/files/2026-06/cronograma.xlsx", base_url=BASE_ORIGIN
        )
        self.assertEqual(
            relative,
            "https://www.argentina.gob.ar/sites/default/files/2026-06/cronograma.xlsx",
        )
        absolute = resolve_download_link(
            "https://www.argentina.gob.ar/x/y.pdf", base_url=BASE_ORIGIN
        )
        self.assertEqual(absolute, "https://www.argentina.gob.ar/x/y.pdf")

    def test_resolve_download_link_rejects_non_download(self) -> None:
        self.assertIsNone(
            resolve_download_link("/noticias/llamado-julio-2026", base_url=BASE_ORIGIN)
        )
        self.assertIsNone(resolve_download_link("", base_url=BASE_ORIGIN))
        self.assertIsNone(resolve_download_link(None, base_url=BASE_ORIGIN))

    def test_listing_excludes_social_share_links(self) -> None:
        downloads = resolve_download_links(
            _read("cronograma.html"), base_url=BASE_ORIGIN
        )
        for url in downloads:
            self.assertNotIn("facebook", url)
            self.assertNotIn("twitter", url)


class TesoroConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Connector async flow + HTTP status handling."""

    async def test_fetch_page_200_emits_normalized_items_with_raw_hash(self) -> None:
        body = _read("resultado.html").encode("utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=RESULTADO_URL,
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=body,
            )
        )
        connector = TesoroLicitacionesConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertGreater(len(result.items), 0)
        expected_hash = hashlib.sha256(body).hexdigest()
        # AC#3: raw_hash computed from the fetched bytes and preserved.
        self.assertEqual(
            result.items[0].provenance.transport_metadata["raw_hash"], expected_hash
        )
        # AC#1: items carry fecha/moneda/monto/url.
        first = result.items[0]
        self.assertIsNotNone(first.published_at)
        self.assertIn(first.metadata["moneda"], {"ARS", "USD"})
        self.assertEqual(first.url, RESULTADO_URL)

    async def test_fetch_page_uses_cursor_url(self) -> None:
        body = _read("llamado.html").encode("utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=LLAMADO_URL,
                headers={"Content-Type": "text/html"},
                body=body,
            )
        )
        connector = TesoroLicitacionesConnector(transport=transport)

        result = await connector.fetch_page(cursor=LLAMADO_URL)

        self.assertEqual(transport.requests[0].url, LLAMADO_URL)
        self.assertTrue(
            all(i.metadata["event_type"] == "llamado" for i in result.items)
        )

    async def test_fetch_page_defaults_to_default_url(self) -> None:
        body = _read("resultado.html").encode("utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=DEFAULT_PAGE_URL,
                headers={"Content-Type": "text/html"},
                body=body,
            )
        )
        connector = TesoroLicitacionesConnector(transport=transport)

        await connector.fetch_page()

        self.assertEqual(transport.requests[0].url, DEFAULT_PAGE_URL)

    async def test_fetch_page_404_raises_recoverable(self) -> None:
        connector = TesoroLicitacionesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=404,
                    url="https://www.argentina.gob.ar/missing",
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor="https://www.argentina.gob.ar/missing")

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        connector = TesoroLicitacionesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=503,
                    url=DEFAULT_PAGE_URL,
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_3xx_raises_value_error(self) -> None:
        connector = TesoroLicitacionesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=302,
                    url=DEFAULT_PAGE_URL,
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(ValueError):
            await connector.fetch_page()

    async def test_fetch_page_1xx_raises_value_error(self) -> None:
        connector = TesoroLicitacionesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=100,
                    url=DEFAULT_PAGE_URL,
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(ValueError):
            await connector.fetch_page()


if __name__ == "__main__":
    unittest.main()
