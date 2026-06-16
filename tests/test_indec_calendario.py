from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.indec_calendario import (
    IndecCalendarioConnector,
    extract_json_from_html,
    filter_weekly_report_events,
    normalize_calendario_event,
    parse_calendario_html,
    parse_calendario_json,
    ParsedCalendarioEvent,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "indec_calendario"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class ExtractJsonTests(unittest.TestCase):
    def test_extract_json_from_valid_html(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        json_text = extract_json_from_html(html)

        self.assertIn('"eventos"', json_text)
        self.assertIn('"IPC"', json_text)

    def test_extract_json_raises_on_missing_script_tag(self) -> None:
        html = (FIXTURES_DIR / "no_script.html").read_text(encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            extract_json_from_html(html)

        self.assertIn("calendario-data", str(ctx.exception))

    def test_extract_json_raises_on_empty_json(self) -> None:
        html = (FIXTURES_DIR / "empty_json.html").read_text(encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            extract_json_from_html(html)

        self.assertIn("empty", str(ctx.exception).lower())


class ParseCalendarioJsonTests(unittest.TestCase):
    def test_parse_valid_json(self) -> None:
        json_text = '{"eventos": [{"id": "evt-001", "fecha": "2026-06-15", "hora": "09:30", "dataset": "IPC", "titulo": "IPC Mayo 2026", "fuente": "https://example.com", "tipo": "mensual"}]}'
        events = parse_calendario_json(json_text)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_id, "evt-001")
        self.assertEqual(events[0].dataset, "IPC")
        self.assertEqual(events[0].published_at, datetime(2026, 6, 15, 9, 30, tzinfo=timezone.utc))

    def test_parse_json_raises_on_invalid_json(self) -> None:
        html = (FIXTURES_DIR / "invalid_json.html").read_text(encoding="utf-8")
        json_text = extract_json_from_html(html)

        with self.assertRaises(ValueError) as ctx:
            parse_calendario_json(json_text)

        self.assertIn("Invalid JSON", str(ctx.exception))

    def test_parse_json_raises_on_missing_eventos_key(self) -> None:
        json_text = '{"data": []}'

        with self.assertRaises(ValueError) as ctx:
            parse_calendario_json(json_text)

        self.assertIn("eventos", str(ctx.exception))

    def test_parse_json_raises_on_eventos_not_list(self) -> None:
        json_text = '{"eventos": {}}'

        with self.assertRaises(ValueError) as ctx:
            parse_calendario_json(json_text)

        self.assertIn("list", str(ctx.exception))

    def test_parse_json_raises_on_missing_required_field(self) -> None:
        json_text = '{"eventos": [{"id": "evt-001", "fecha": "2026-06-15"}]}'

        with self.assertRaises(ValueError) as ctx:
            parse_calendario_json(json_text)

        self.assertIn("hora", str(ctx.exception))


class ParseCalendarioHtmlTests(unittest.TestCase):
    def test_parse_html_returns_events(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        events = parse_calendario_html(html)

        self.assertEqual(len(events), 9)
        self.assertEqual(events[0].dataset, "IPC")
        self.assertEqual(events[1].dataset, "EMAE")
        self.assertEqual(events[2].dataset, "Salarios")
        self.assertEqual(events[3].dataset, "Canasta")
        self.assertEqual(events[4].dataset, "Pobreza")
        self.assertEqual(events[5].dataset, "IPC")
        self.assertEqual(events[6].dataset, "EPH")
        self.assertEqual(events[7].dataset, "EMAE")
        self.assertEqual(events[8].dataset, "Pobreza")

    def test_parse_html_event_structure(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        events = parse_calendario_html(html)

        event = events[0]
        self.assertEqual(event.event_id, "evt-001")
        self.assertEqual(event.fecha, "2026-06-15")
        self.assertEqual(event.hora, "09:30")
        self.assertEqual(event.dataset, "IPC")
        self.assertEqual(
            event.titulo, "Índice de Precios al Consumidor - Mayo 2026"
        )
        self.assertEqual(
            event.fuente, "https://www.indec.gob.ar/Nivel4/Tema/3/5/31"
        )
        self.assertEqual(event.tipo, "mensual")
        self.assertEqual(
            event.published_at, datetime(2026, 6, 15, 9, 30, tzinfo=timezone.utc)
        )


class FilterWeeklyReportEventsTests(unittest.TestCase):
    def test_filter_keeps_only_relevant_datasets(self) -> None:
        events = [
            ParsedCalendarioEvent(
                event_id="evt-1",
                fecha="2026-06-15",
                hora="09:30",
                dataset="IPC",
                titulo="IPC Mayo 2026",
                fuente="https://example.com/ipc",
                tipo="mensual",
            ),
            ParsedCalendarioEvent(
                event_id="evt-2",
                fecha="2026-06-16",
                hora="10:00",
                dataset="EMAE",
                titulo="EMAE Abril 2026",
                fuente="https://example.com/emae",
                tipo="mensual",
            ),
            ParsedCalendarioEvent(
                event_id="evt-3",
                fecha="2026-06-17",
                hora="11:00",
                dataset="OtroIndicador",
                titulo="Otro Indicador",
                fuente="https://example.com/otro",
                tipo="mensual",
            ),
        ]

        filtered = filter_weekly_report_events(events)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].dataset, "IPC")
        self.assertEqual(filtered[1].dataset, "EMAE")

    def test_filter_includes_all_relevant_datasets(self) -> None:
        events = [
            ParsedCalendarioEvent(
                event_id=f"evt-{i}",
                fecha="2026-06-15",
                hora="09:30",
                dataset=dataset,
                titulo=f"{dataset} 2026",
                fuente=f"https://example.com/{dataset.lower()}",
                tipo="mensual",
            )
            for i, dataset in enumerate(["IPC", "EMAE", "EPH", "Salarios", "Canasta", "Pobreza"])
        ]

        filtered = filter_weekly_report_events(events)

        self.assertEqual(len(filtered), 6)
        datasets = {event.dataset for event in filtered}
        self.assertEqual(datasets, {"IPC", "EMAE", "EPH", "Salarios", "Canasta", "Pobreza"})


class NormalizeCalendarioEventTests(unittest.TestCase):
    def test_normalize_creates_valid_source_item(self) -> None:
        event = ParsedCalendarioEvent(
            event_id="evt-001",
            fecha="2026-06-15",
            hora="09:30",
            dataset="IPC",
            titulo="Índice de Precios al Consumidor - Mayo 2026",
            fuente="https://www.indec.gob.ar/Nivel4/Tema/3/5/31",
            tipo="mensual",
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)

        item = normalize_calendario_event(
            parsed=event,
            fetched_at=fetched_at,
            fetch_url="https://www.indec.gob.ar/Calendario/Fecha/0",
            cursor=None,
            transport_metadata={"status_code": 200},
        )

        self.assertEqual(item.external_id, "evt-001")
        self.assertEqual(item.source, "indec")
        self.assertEqual(item.title, event.titulo)
        self.assertEqual(item.summary, "IPC - Índice de Precios al Consumidor - Mayo 2026")
        self.assertEqual(item.url, event.fuente)
        self.assertEqual(item.metadata["dataset"], "IPC")
        self.assertEqual(item.metadata["event_type"], "mensual")
        self.assertEqual(item.metadata["publication_time"], "09:30")
        self.assertEqual(item.provenance.connector, "indec_calendario")
        self.assertEqual(item.provenance.source, "indec")
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.ttl_seconds, 6 * 60 * 60)

    def test_normalize_populates_published_at(self) -> None:
        event = ParsedCalendarioEvent(
            event_id="evt-001",
            fecha="2026-06-15",
            hora="09:30",
            dataset="IPC",
            titulo="IPC Mayo 2026",
            fuente="https://example.com",
            tipo="mensual",
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)

        item = normalize_calendario_event(
            parsed=event,
            fetched_at=fetched_at,
            fetch_url="https://www.indec.gob.ar/Calendario/Fecha/0",
            cursor=None,
        )

        self.assertEqual(item.published_at, datetime(2026, 6, 15, 9, 30, tzinfo=timezone.utc))


class IndecCalendarioConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_all_events(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=html.encode("utf-8"),
            )
        )
        connector = IndecCalendarioConnector(transport=transport, filter_weekly_report=False)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 9)
        self.assertEqual(
            transport.requests[0].url, "https://www.indec.gob.ar/Calendario/Fecha/0"
        )

    async def test_fetch_page_filters_weekly_report_events(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=html.encode("utf-8"),
            )
        )
        connector = IndecCalendarioConnector(transport=transport, filter_weekly_report=True)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 9)  # All events in fixture are relevant
        datasets = {item.metadata["dataset"] for item in result.items}
        self.assertEqual(datasets, {"IPC", "EMAE", "EPH", "Salarios", "Canasta", "Pobreza"})

    async def test_fetch_page_returns_empty_on_empty_events(self) -> None:
        html = (FIXTURES_DIR / "empty_json.html").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=html.encode("utf-8"),
            )
        )
        connector = IndecCalendarioConnector(transport=transport)

        with self.assertRaises(ValueError):
            await connector.fetch_page()

    async def test_fetch_page_raises_recoverable_for_upstream_5xx(self) -> None:
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html"},
                body=b"Service Unavailable",
            )
        )
        connector = IndecCalendarioConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_raises_value_error_on_4xx(self) -> None:
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html"},
                body=b"Not Found",
            )
        )
        connector = IndecCalendarioConnector(transport=transport)

        with self.assertRaises(ValueError):
            await connector.fetch_page()

    async def test_fetch_page_items_have_required_fields(self) -> None:
        html = (FIXTURES_DIR / "calendario.html").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/Calendario/Fecha/0",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=html.encode("utf-8"),
            )
        )
        connector = IndecCalendarioConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertGreater(len(result.items), 0)

        item = result.items[0]
        self.assertIsNotNone(item.external_id)
        self.assertIsNotNone(item.source)
        self.assertIsNotNone(item.published_at)
        self.assertIsNotNone(item.title)
        self.assertIsNotNone(item.url)
        self.assertIn("dataset", item.metadata)
        self.assertIn("event_type", item.metadata)


if __name__ == "__main__":
    unittest.main()