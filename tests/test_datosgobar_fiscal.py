from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.datosgobar_fiscal import (
    DatosgobarFiscalConnector,
    METHODOLOGY,
    METHODOLOGY_DESCRIPTION,
    normalize_datosgobar_fiscal,
    parse_datosgobar_fiscal_json,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "datosgobar_fiscal"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        # Update response URL to match the request URL with params
        from urllib.parse import urlencode

        if request.params:
            params_str = urlencode(request.params)
            updated_url = f"{request.url}?{params_str}"
            response_with_url = HttpResponse(
                status_code=self.response.status_code,
                url=updated_url,
                headers=self.response.headers,
                body=self.response.body,
            )
            return response_with_url
        return self.response


class DatosgobarFiscalParserTests(unittest.TestCase):
    def test_parse_series_response_json(self) -> None:
        json_text = (FIXTURES_DIR / "series_response.json").read_text(encoding="utf-8")
        parsed = parse_datosgobar_fiscal_json(json_text, "452.3_RESULTADO_RIO_0_M_18_54")

        self.assertEqual(parsed.external_id, "452.3_RESULTADO_RIO_0_M_18_54_2016-03")
        self.assertEqual(parsed.series_id, "452.3_RESULTADO_RIO_0_M_18_54")
        self.assertEqual(parsed.period, datetime(2016, 3, 1, tzinfo=timezone.utc))
        self.assertEqual(parsed.concepto, "IMIG. Resultado primario")
        self.assertEqual(parsed.valor, -30012.10000000001)
        self.assertEqual(parsed.unidad, "Millones de pesos")
        self.assertEqual(parsed.fuente, "datos.gob.ar")

    def test_parse_invalid_json_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json("not json", "452.3_RESULTADO_RIO_0_M_18_54")
        self.assertIn("Invalid JSON response", str(cm.exception))

    def test_parse_missing_data_field_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json('{"meta": []}', "452.3_RESULTADO_RIO_0_M_18_54")
        self.assertIn("Missing or invalid 'data' field", str(cm.exception))

    def test_parse_empty_data_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json('{"data": [], "meta": [{"field": {"id": "test"}}]}', "452.3_RESULTADO_RIO_0_M_18_54")
        self.assertIn("No observations found", str(cm.exception))

    def test_parse_missing_meta_field_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json('{"data": [["2016-01-01", 100.0]]}', "452.3_RESULTADO_RIO_0_M_18_54")
        self.assertIn("Missing or invalid 'meta' field", str(cm.exception))

    def test_parse_invalid_observation_format_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json(
                '{"data": [["2016-01-01"]], "meta": [{"field": {"id": "test"}}]}', "test"
            )
        self.assertIn("Invalid observation format", str(cm.exception))

    def test_parse_invalid_date_format_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json(
                '{"data": [["invalid", 100.0]], "meta": [{"field": {"id": "test"}}]}', "test"
            )
        self.assertIn("Invalid date format", str(cm.exception))

    def test_parse_series_id_mismatch_raises_value_error(self) -> None:
        json_text = (FIXTURES_DIR / "series_response.json").read_text(encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            parse_datosgobar_fiscal_json(json_text, "different_series_id")
        self.assertIn("Series ID mismatch", str(cm.exception))

    def test_normalize_populates_required_source_item_fields(self) -> None:
        from finance_news.connectors.datosgobar_fiscal import ParsedFiscalObservation

        parsed = ParsedFiscalObservation(
            external_id="test_id",
            period=datetime(2024, 1, 1, tzinfo=timezone.utc),
            concepto="Test Concept",
            valor=1000.0,
            unidad="Millones de pesos",
            fuente="Test Source",
            series_id="test_series",
        )
        fetched_at = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        item = normalize_datosgobar_fiscal(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://example.com/api/series",
            cursor="test_cursor",
            transport_metadata={"status_code": 200},
        )

        self.assertEqual(item.external_id, "test_id")
        self.assertEqual(item.source, "datosgobar")
        self.assertEqual(item.title, "Test Concept - 2024-01")
        self.assertEqual(item.summary, "1000.0 Millones de pesos")
        self.assertEqual(item.url, "https://example.com/api/series")
        self.assertEqual(item.metadata["period"], "2024-01-01T00:00:00+00:00")
        self.assertEqual(item.metadata["concepto"], "Test Concept")
        self.assertEqual(item.metadata["valor"], 1000.0)
        self.assertEqual(item.metadata["unidad"], "Millones de pesos")
        self.assertEqual(item.metadata["fuente"], "Test Source")
        self.assertEqual(item.metadata["series_id"], "test_series")
        self.assertEqual(item.metadata["metodologia"], "base_caja")
        self.assertEqual(
            item.metadata["metodologia_descripcion"],
            "Series published by Secretaria de Hacienda use cash basis (base caja) methodology, measuring actual cash flows for income and expenditures.",
        )
        self.assertEqual(item.provenance.connector, "datosgobar_fiscal")
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(item.freshness.first_seen_at, fetched_at)

    def test_module_documentation_constants_exist(self) -> None:
        """Verify that methodology constants are documented (AC#3)."""
        self.assertEqual(METHODOLOGY, "base_caja")
        self.assertIn("cash basis", METHODOLOGY_DESCRIPTION.lower())
        self.assertIn("Hacienda", METHODOLOGY_DESCRIPTION)


class DatosgobarFiscalConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_normalized_item(self) -> None:
        json_text = (FIXTURES_DIR / "series_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apis.datos.gob.ar/series/api/series/?ids=452.3_RESULTADO_RIO_0_M_18_54&format=json&limit=1",
                headers={"Content-Type": "application/json"},
                body=json_text.encode("utf-8"),
            )
        )
        connector = DatosgobarFiscalConnector(transport=transport)

        result = await connector.fetch_page(cursor="452.3_RESULTADO_RIO_0_M_18_54")

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].external_id, "452.3_RESULTADO_RIO_0_M_18_54_2016-03")
        self.assertEqual(
            result.items[0].title, "IMIG. Resultado primario - 2016-03"
        )
        self.assertEqual(
            transport.requests[0].url,
            "https://apis.datos.gob.ar/series/api/series/",
        )
        self.assertEqual(transport.requests[0].method, "GET")
        self.assertEqual(transport.requests[0].headers["Accept"], "application/json")
        self.assertEqual(
            transport.requests[0].params["ids"], "452.3_RESULTADO_RIO_0_M_18_54"
        )
        self.assertEqual(transport.requests[0].params["format"], "json")
        self.assertEqual(transport.requests[0].params["limit"], "1")

    async def test_fetch_page_returns_empty_on_404(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=404,
                    url="https://apis.datos.gob.ar/series/api/series/?ids=invalid_id&format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "not found"}',
                )
            )
        )

        result = await connector.fetch_page(cursor="invalid_id")

        self.assertEqual(result.items, ())
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

    async def test_fetch_page_raises_recoverable_for_upstream_5xx(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=503,
                    url="https://apis.datos.gob.ar/series/api/series/?ids=452.3_RESULTADO_RIO_0_M_18_54&format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "service unavailable"}',
                )
            )
        )

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor="452.3_RESULTADO_RIO_0_M_18_54")
        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_raises_value_for_client_error(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=400,
                    url="https://apis.datos.gob.ar/series/api/series/?ids=invalid_id&format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "bad request"}',
                )
            )
        )

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="invalid_id")
        self.assertIn("400", str(cm.exception))

    async def test_fetch_page_requires_cursor(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apis.datos.gob.ar/series/api/series/?format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()
        self.assertIn("requires a series ID cursor", str(cm.exception))

    def test_connector_name_and_source_attributes(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apis.datos.gob.ar/series/api/series/?format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )
        self.assertEqual(connector.name, "datosgobar_fiscal")
        self.assertEqual(connector.source, "datosgobar")

    def test_retry_and_rate_limit_policies_exist(self) -> None:
        connector = DatosgobarFiscalConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apis.datos.gob.ar/series/api/series/?format=json&limit=1",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )
        self.assertIsNotNone(connector.retry_policy)
        self.assertIsNotNone(connector.rate_limit_policy)
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)


if __name__ == "__main__":
    unittest.main()