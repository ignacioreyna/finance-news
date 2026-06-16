from __future__ import annotations

import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_calendario import (
    BcraCalendarioConnector,
    DEFAULT_TTL_SECONDS,
    _infer_frequency,
    _parse_spanish_date,
    normalize_bcra_calendario_event,
    parse_bcra_calendario_html,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_calendario"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraCalendarioParserTests(unittest.TestCase):
    def test_parse_calendar_html(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        events = parse_bcra_calendario_html(html)

        # Check that we got multiple events
        self.assertGreater(len(events), 50)

        # Check specific events
        rem_events = [e for e in events if "REM" in e.informe]
        self.assertGreater(len(rem_events), 0)

        # Check that daily row is excluded
        daily_events = [e for e in events if "diario" in e.informe.lower() and e.fecha is None]
        self.assertEqual(len(daily_events), 0)

    def test_parse_specific_events(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        events = parse_bcra_calendario_html(html)

        # Check REM event
        rem_event = next((e for e in events if "REM" in e.informe and "01-07" in e.external_id), None)
        self.assertIsNotNone(rem_event)
        self.assertEqual(rem_event.informe, "Relevamiento de Expectativas de Mercado (REM)")
        self.assertEqual(rem_event.fecha, datetime(2026, 1, 7, tzinfo=timezone.utc))
        self.assertEqual(rem_event.frecuencia, "mensual")
        self.assertEqual(rem_event.fuente, "BCRA")

        # Check Boletín Estadístico
        boletin_event = next((e for e in events if "Boletín Estadístico" in e.informe and "01-14" in e.external_id), None)
        self.assertIsNotNone(boletin_event)
        self.assertEqual(boletin_event.informe, "Boletín Estadístico")
        self.assertEqual(boletin_event.fecha, datetime(2026, 1, 14, tzinfo=timezone.utc))
        self.assertEqual(boletin_event.frecuencia, "mensual")

        # Check IPOM
        ipom_event = next((e for e in events if "IPOM" in e.informe), None)
        self.assertIsNotNone(ipom_event)
        self.assertEqual(ipom_event.informe, "Informe de Política Monetaria (IPOM)")
        self.assertEqual(ipom_event.frecuencia, "periódica")

        # Check Balance Cambiario
        balance_event = next((e for e in events if "Balance Cambiario" in e.informe and "01-30" in e.external_id), None)
        self.assertIsNotNone(balance_event)
        self.assertEqual(balance_event.informe, "Informe de Evolución del Mercado de Cambios y Balance Cambiario")
        self.assertEqual(balance_event.frecuencia, "mensual")

    def test_parse_spanish_date_valid(self) -> None:
        result = _parse_spanish_date("07 ene 2026")
        self.assertEqual(result, datetime(2026, 1, 7, tzinfo=timezone.utc))

        result = _parse_spanish_date("13 abr 2026")
        self.assertEqual(result, datetime(2026, 4, 13, tzinfo=timezone.utc))

        result = _parse_spanish_date("31 dic 2026")
        self.assertEqual(result, datetime(2026, 12, 31, tzinfo=timezone.utc))

    def test_parse_spanish_date_invalid(self) -> None:
        result = _parse_spanish_date("Actualización diaria *")
        self.assertIsNone(result)

        result = _parse_spanish_date("invalid date")
        self.assertIsNone(result)

        result = _parse_spanish_date("")
        self.assertIsNone(result)

    def test_infer_frequency(self) -> None:
        self.assertEqual(_infer_frequency("Informe Monetario Diario"), "diaria")
        self.assertEqual(_infer_frequency("Informe Monetario Mensual"), "mensual")
        self.assertEqual(_infer_frequency("Boletín Estadístico"), "mensual")
        self.assertEqual(_infer_frequency("Relevamiento de Expectativas de Mercado (REM)"), "mensual")
        self.assertEqual(_infer_frequency("Informe de Política Monetaria (IPOM)"), "periódica")
        self.assertEqual(_infer_frequency("Informe de Evolución del Mercado de Cambios y Balance Cambiario"), "mensual")
        self.assertEqual(_infer_frequency("Informe sobre Bancos"), "mensual")
        self.assertEqual(_infer_frequency("Informe de Inversión Extranjera Directa"), "mensual")
        self.assertEqual(_infer_frequency("Informe de Pagos Minoristas"), "mensual")
        self.assertEqual(_infer_frequency("Encuesta de Condiciones Crediticias (ECC)"), "mensual")
        self.assertEqual(_infer_frequency("Informe de Estabilidad Financiera (IEF)"), "mensual")
        self.assertEqual(_infer_frequency("Informe de Inclusión Financiera"), "mensual")
        self.assertEqual(_infer_frequency("Informe sobre Protección a las Personas Usuarias de Servicios Financieros"), "mensual")
        self.assertEqual(_infer_frequency("Estados Contables"), "mensual")


class BcraCalendarioNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        from finance_news.connectors.bcra_calendario import ParsedCalendarEvent

        parsed = ParsedCalendarEvent(
            informe="Informe Monetario Mensual",
            fecha=datetime(2026, 1, 8, tzinfo=timezone.utc),
            frecuencia="mensual",
            fuente="BCRA",
            external_id="informe_monetario_mensual_2026-01-08",
        )

        fetched_at = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
        item = normalize_bcra_calendario_event(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.bcra.gob.ar/calendario-de-informes/",
            cursor=None,
        )

        self.assertEqual(item.external_id, "informe_monetario_mensual_2026-01-08")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 1, 8, tzinfo=timezone.utc))
        self.assertIn("Informe Monetario Mensual", item.title)
        self.assertIn("2026-01-08", item.title)
        self.assertIn("mensual", item.summary)
        self.assertEqual(item.url, "https://www.bcra.gob.ar/calendario-de-informes/")
        self.assertEqual(item.metadata["informe"], "Informe Monetario Mensual")
        self.assertEqual(item.metadata["frecuencia"], "mensual")
        self.assertEqual(item.metadata["fuente"], "BCRA")
        self.assertEqual(item.provenance.connector, "bcra_calendario")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)


class BcraCalendarioConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_events(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.bcra.gob.ar/calendario-de-informes/",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = BcraCalendarioConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertGreater(len(result.items), 50)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        # Check that the first item has expected fields
        first_item = result.items[0]
        self.assertEqual(first_item.source, "bcra")
        self.assertIn("informe", first_item.metadata)
        self.assertIn("frecuencia", first_item.metadata)
        self.assertIn("fuente", first_item.metadata)

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url="https://www.bcra.gob.ar/calendario-de-informes/",
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = BcraCalendarioConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url="https://www.bcra.gob.ar/calendario-de-informes/",
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = BcraCalendarioConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url="https://www.bcra.gob.ar/calendario-de-informes/",
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = BcraCalendarioConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = BcraCalendarioConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "bcra_calendario")
        self.assertEqual(connector.source, "bcra")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class BcraCalendarioFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        from finance_news.connectors.bcra_calendario import ParsedCalendarEvent

        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.bcra.gob.ar/calendario-de-informes/",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = BcraCalendarioConnector(transport=transport)
        result = await connector.fetch_page()

        # Check that all items have proper freshness metadata
        for item in result.items:
            self.assertIsNotNone(item.freshness)
            self.assertIsNotNone(item.freshness.fetched_at)
            self.assertIsNotNone(item.freshness.first_seen_at)
            self.assertFalse(item.freshness.is_stale)
            self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
            # published_at should match the event date
            if item.published_at is not None:
                self.assertEqual(item.freshness.published_at, item.published_at)


if __name__ == "__main__":
    unittest.main()