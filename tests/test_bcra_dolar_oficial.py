from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_dolar_oficial import (
    BcraDolarOficialConnector,
    normalize_bcra_dolar_oficial,
    parse_bcra_dolar_oficial_response,
    ParsedBcraDolarOficial,
)
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.testing.fixtures import load_fixture_json
from finance_news.testing.snapshots import assert_source_items_match


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_dolar_oficial"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraDolarOficialParserTests(unittest.TestCase):
    def test_parse_sample_response(self) -> None:
        """Test parsing a sample BCRA API response."""
        data = load_fixture_json("bcra_dolar_oficial", "sample_response.json")
        parsed = parse_bcra_dolar_oficial_response(data)

        self.assertEqual(len(parsed), 3)

        # Check first observation
        self.assertEqual(parsed[0].fecha, "2026-06-12")
        self.assertEqual(parsed[0].codigo_moneda, "REF")
        self.assertEqual(parsed[0].descripcion, "DOLAR REFERENCIA COM 3500")
        self.assertAlmostEqual(parsed[0].valor, 1430.8092, places=4)

        # Check second observation
        self.assertEqual(parsed[1].fecha, "2026-06-11")
        self.assertAlmostEqual(parsed[1].valor, 1429.0298, places=4)

        # Check third observation
        self.assertEqual(parsed[2].fecha, "2026-06-10")
        self.assertAlmostEqual(parsed[2].valor, 1436.585, places=4)

    def test_parse_non_dict_response_raises(self) -> None:
        """Test that non-dict responses raise ValueError."""
        with self.assertRaises(ValueError, msg="Response must be a dictionary"):
            parse_bcra_dolar_oficial_response([])

    def test_parse_non_200_status_raises(self) -> None:
        """Test that non-200 status codes raise ValueError."""
        data = {"status": 400, "errorMessages": ["Bad request"]}
        with self.assertRaises(ValueError, msg="API returned status 400"):
            parse_bcra_dolar_oficial_response(data)

    def test_parse_empty_results_raises(self) -> None:
        """Test that empty results raise ValueError."""
        data = {"status": 200, "results": []}
        with self.assertRaises(ValueError, msg="No results found"):
            parse_bcra_dolar_oficial_response(data)

    def test_parse_non_list_results_raises(self) -> None:
        """Test that non-list results raise ValueError."""
        data = {"status": 200, "results": "not a list"}
        with self.assertRaises(ValueError, msg="No results found"):
            parse_bcra_dolar_oficial_response(data)

    def test_parse_missing_detalle_skips_entry(self) -> None:
        """Test that entries without detalle are skipped."""
        data = {
            "status": 200,
            "results": [
                {
                    "fecha": "2026-06-12",
                    "detalle": [
                        {
                            "codigoMoneda": "REF",
                            "descripcion": "DOLAR REFERENCIA COM 3500",
                            "tipoPase": 0.0,
                            "tipoCotizacion": 1430.8092,
                        }
                    ],
                },
                {"fecha": "2026-06-11"},  # Missing detalle
                {
                    "fecha": "2026-06-10",
                    "detalle": [],  # Empty detalle
                },
            ],
        }
        parsed = parse_bcra_dolar_oficial_response(data)
        self.assertEqual(len(parsed), 1)

    def test_parse_non_ref_currency_ignored(self) -> None:
        """Test that non-REF currencies are ignored."""
        data = {
            "status": 200,
            "results": [
                {
                    "fecha": "2026-06-12",
                    "detalle": [
                        {
                            "codigoMoneda": "USD",
                            "descripcion": "DOLAR E.E.U.U.",
                            "tipoPase": 0.0,
                            "tipoCotizacion": 1428.0,
                        },
                        {
                            "codigoMoneda": "REF",
                            "descripcion": "DOLAR REFERENCIA COM 3500",
                            "tipoPase": 0.0,
                            "tipoCotizacion": 1430.8092,
                        },
                    ],
                },
            ],
        }
        parsed = parse_bcra_dolar_oficial_response(data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].codigo_moneda, "REF")

    def test_parse_no_ref_observations_raises(self) -> None:
        """Test that absence of REF observations raises ValueError."""
        data = {
            "status": 200,
            "results": [
                {
                    "fecha": "2026-06-12",
                    "detalle": [
                        {
                            "codigoMoneda": "USD",
                            "descripcion": "DOLAR E.E.U.U.",
                            "tipoPase": 0.0,
                            "tipoCotizacion": 1428.0,
                        }
                    ],
                },
            ],
        }
        with self.assertRaises(ValueError, msg="No REF currency observations"):
            parse_bcra_dolar_oficial_response(data)


class BcraDolarOficialNormalizationTests(unittest.TestCase):
    def test_normalize_creates_valid_source_item(self) -> None:
        """Test that normalization creates a valid SourceItem."""
        parsed = ParsedBcraDolarOficial(
            fecha="2026-06-12",
            valor=1430.8092,
            codigo_moneda="REF",
            descripcion="DOLAR REFERENCIA COM 3500",
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
        fetch_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF"

        item = normalize_bcra_dolar_oficial(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=fetch_url,
            cursor=None,
            transport_metadata={"status_code": 200},
        )

        self.assertEqual(item.external_id, "REF_2026-06-12")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(item.url, fetch_url)
        self.assertEqual(item.metadata["currency_code"], "REF")
        self.assertEqual(item.metadata["currency_description"], "DOLAR REFERENCIA COM 3500")
        self.assertAlmostEqual(item.metadata["value"], 1430.8092, places=4)
        self.assertEqual(item.metadata["value_type"], "exchange_rate")
        self.assertEqual(item.provenance.connector, "bcra_dolar_oficial")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(item.freshness.ttl_seconds, 86400)
        self.assertFalse(item.freshness.is_stale)

    def test_normalize_creates_descriptive_title_and_summary(self) -> None:
        """Test that normalization creates meaningful title and summary."""
        parsed = ParsedBcraDolarOficial(
            fecha="2026-06-12",
            valor=1430.8092,
            codigo_moneda="REF",
            descripcion="DOLAR REFERENCIA COM 3500",
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
        fetch_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF"

        item = normalize_bcra_dolar_oficial(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=fetch_url,
            cursor=None,
        )

        self.assertIn("Dólar Oficial (A3500)", item.title)
        self.assertIn("1430.81", item.title)
        self.assertIn("2026-06-12", item.title)

        self.assertIn("BCRA official dollar rate", item.summary)
        self.assertIn("Comunicación A3500", item.summary)
        self.assertIn("1430.81", item.summary)
        self.assertIn("2026-06-12", item.summary)

    def test_normalize_serialization_roundtrip(self) -> None:
        """Test that SourceItem serialization/deserialization works."""
        parsed = ParsedBcraDolarOficial(
            fecha="2026-06-12",
            valor=1430.8092,
            codigo_moneda="REF",
            descripcion="DOLAR REFERENCIA COM 3500",
        )
        fetched_at = datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
        fetch_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF"

        original = normalize_bcra_dolar_oficial(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=fetch_url,
            cursor=None,
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = original.__class__.from_dict(data)

        # Verify they match
        assert_source_items_match(restored, original)


class BcraDolarOficialConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_normalized_items(self) -> None:
        """Test that fetch_page returns properly normalized items."""
        fixture_data = load_fixture_json("bcra_dolar_oficial", "sample_response.json")
        response = HttpResponse(
            status_code=200,
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={"Content-Type": "application/json"},
            body=json.dumps(fixture_data).encode("utf-8"),
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)

        # Check first item
        item = result.items[0]
        self.assertEqual(item.external_id, "REF_2026-06-12")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.metadata["currency_code"], "REF")
        self.assertAlmostEqual(item.metadata["value"], 1430.8092, places=4)

        # Check request was made correctly
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url,
            "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
        )
        self.assertEqual(request.params["limit"], "1000")

    async def test_fetch_page_raises_recoverable_for_404(self) -> None:
        """Test that 404 status raises RecoverableConnectorError."""
        response = HttpResponse(
            status_code=404,
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={},
            body=b"",
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("404", str(cm.exception))
        self.assertIn("temporarily unavailable", str(cm.exception))

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Test that 5xx status raises RecoverableConnectorError."""
        for status in [500, 502, 503, 504]:
            with self.subTest(status=status):
                response = HttpResponse(
                    status_code=status,
                    url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
                    headers={},
                    body=b"",
                )
                transport = _FakeTransport(response)
                connector = BcraDolarOficialConnector(transport=transport)

                with self.assertRaises(RecoverableConnectorError) as cm:
                    await connector.fetch_page()

                self.assertIn(str(status), str(cm.exception))
                self.assertIn("server error", str(cm.exception))

    async def test_fetch_page_raises_recoverable_for_4xx(self) -> None:
        """Test that 4xx status (except 404) raises RecoverableConnectorError."""
        for status in [429, 400]:
            with self.subTest(status=status):
                response = HttpResponse(
                    status_code=status,
                    url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
                    headers={},
                    body=b"",
                )
                transport = _FakeTransport(response)
                connector = BcraDolarOficialConnector(transport=transport)

                with self.assertRaises(RecoverableConnectorError) as cm:
                    await connector.fetch_page()

                self.assertIn(str(status), str(cm.exception))

    async def test_fetch_page_raises_value_for_unexpected_status(self) -> None:
        """Test that unexpected status codes raise ValueError."""
        response = HttpResponse(
            status_code=302,  # redirect - genuinely unhandled/unexpected
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={},
            body=b"",
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("302", str(cm.exception))
        self.assertIn("unexpected status", str(cm.exception))

    async def test_fetch_page_raises_value_for_invalid_json(self) -> None:
        """Test that invalid JSON raises ValueError."""
        response = HttpResponse(
            status_code=200,
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={"Content-Type": "application/json"},
            body=b"not json",
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON", str(cm.exception))

    async def test_fetch_page_raises_value_for_parse_error(self) -> None:
        """Test that parse errors raise ValueError."""
        invalid_data = {"status": 200, "results": []}  # Empty results
        response = HttpResponse(
            status_code=200,
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={"Content-Type": "application/json"},
            body=json.dumps(invalid_data).encode("utf-8"),
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Failed to parse", str(cm.exception))

    async def test_fetch_page_populates_transport_metadata(self) -> None:
        """Test that transport metadata is correctly populated."""
        fixture_data = load_fixture_json("bcra_dolar_oficial", "sample_response.json")
        response = HttpResponse(
            status_code=200,
            url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
            headers={"Content-Type": "application/json", "X-Custom": "test"},
            body=json.dumps(fixture_data).encode("utf-8"),
        )
        transport = _FakeTransport(response)
        connector = BcraDolarOficialConnector(transport=transport)

        result = await connector.fetch_page()

        # Check that transport metadata is populated
        item = result.items[0]
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(
            item.provenance.transport_metadata["content_type"], "application/json"
        )

    def test_connector_has_required_attributes(self) -> None:
        """Test that connector has required protocol attributes."""
        connector = BcraDolarOficialConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF",
                    headers={},
                    body=b"{}",
                )
            )
        )

        self.assertEqual(connector.name, "bcra_dolar_oficial")
        self.assertEqual(connector.source, "bcra")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


if __name__ == "__main__":
    unittest.main()