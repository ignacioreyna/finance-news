from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_variables_reservas import (
    BcraVariablesReservasConnector,
    normalize_bcra_monetarias_observation,
    parse_bcra_monetarias_response,
    ParsedBcraMonetariasObservation,
    _SERIES_METADATA,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_variables_reservas"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraVariablesReservasParserTests(unittest.TestCase):
    def test_parse_reservas_response(self) -> None:
        """Test parsing reservas internacionales response from BCRA API."""
        response_data = (FIXTURES_DIR / "reservas_internacionales_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data), "Reservas internacionales"
        )

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-10")
        self.assertAlmostEqual(observations[0].valor, 47559.0)
        self.assertEqual(observations[0].variable_id, 1)
        self.assertEqual(observations[0].series_name, "Reservas internacionales")

    def test_parse_base_monetaria_response(self) -> None:
        """Test parsing base monetaria response from BCRA API."""
        response_data = (FIXTURES_DIR / "base_monetaria_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data), "Base monetaria"
        )

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-10")
        self.assertAlmostEqual(observations[0].valor, 41998049.0)
        self.assertEqual(observations[0].variable_id, 15)
        self.assertEqual(observations[0].series_name, "Base monetaria")

    def test_parse_circulacion_monetaria_response(self) -> None:
        """Test parsing circulación monetaria response from BCRA API."""
        response_data = (FIXTURES_DIR / "circulacion_monetaria_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data), "Circulación monetaria"
        )

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-10")
        self.assertAlmostEqual(observations[0].valor, 26301838.0)
        self.assertEqual(observations[0].variable_id, 16)
        self.assertEqual(observations[0].series_name, "Circulación monetaria")

    def test_parse_efectivo_entidades_response(self) -> None:
        """Test parsing efectivo en entidades response from BCRA API."""
        response_data = (FIXTURES_DIR / "efectivo_entidades_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data), "Efectivo en entidades financieras"
        )

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-10")
        self.assertAlmostEqual(observations[0].valor, 1981476.0)
        self.assertEqual(observations[0].variable_id, 18)

    def test_parse_depositos_cc_bcra_response(self) -> None:
        """Test parsing depósitos en cuenta corriente BCRA response."""
        response_data = (FIXTURES_DIR / "depositos_cc_bcra_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data),
            "Depósitos de las entidades financieras en cuenta corriente en el BCRA",
        )

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-10")
        self.assertAlmostEqual(observations[0].valor, 15696211.0)
        self.assertEqual(observations[0].variable_id, 19)

    def test_parse_empty_response(self) -> None:
        """Test parsing empty results from BCRA API."""
        response_data = (FIXTURES_DIR / "not_found_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(
            json.loads(response_data), "Reservas internacionales"
        )

        self.assertEqual(len(observations), 0)

    def test_parse_invalid_status_raises(self) -> None:
        """Test that parsing non-200 status raises ValueError."""
        invalid_response = {
            "status": 500,
            "metadata": {"resultset": {"count": 0, "offset": 0, "limit": 1000}},
            "results": [],
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "Reservas internacionales")

        self.assertIn("Unexpected status code", str(cm.exception))

    def test_parse_invalid_detalle_format_raises(self) -> None:
        """Test that parsing invalid detalle format raises ValueError."""
        invalid_response = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [{"idVariable": 1, "detalle": "not a list"}],
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "Reservas internacionales")

        self.assertIn("Expected 'detalle' to be a list", str(cm.exception))

    def test_parse_invalid_observation_format_raises(self) -> None:
        """Test that parsing invalid observation format raises ValueError."""
        invalid_response = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [{"idVariable": 1, "detalle": [{"fecha": "2026-06-10"}]}],  # Missing valor
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "Reservas internacionales")

        self.assertIn("Invalid observation format", str(cm.exception))

    def test_normalize_reservas_observation(self) -> None:
        """Test normalizing a reservas internacionales observation."""
        parsed = ParsedBcraMonetariasObservation(
            fecha="2026-06-10",
            valor=47559.0,
            variable_id=1,
            series_name="Reservas internacionales",
        )
        metadata = _SERIES_METADATA[1]
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        item = normalize_bcra_monetarias_observation(
            parsed=parsed,
            metadata=metadata,
            fetched_at=fetched_at,
            fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
        )

        self.assertEqual(item.external_id, "Reservas internacionales_2026-06-10")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 6, 10, tzinfo=timezone.utc))
        self.assertIn("Reservas internacionales:", item.title)
        self.assertIn("47559.0", item.title)
        self.assertIn("En millones de USD", item.title)
        self.assertIn("Reservas internacionales", item.summary)
        self.assertEqual(item.metadata["content_type"], "monetarias_observation")
        self.assertEqual(item.metadata["series_name"], "Reservas internacionales")
        self.assertEqual(item.metadata["variable_id"], 1)
        self.assertEqual(item.metadata["frequency"], "D")
        self.assertEqual(item.metadata["unit"], "En millones de USD")
        self.assertEqual(item.metadata["category"], "Principales Variables")
        self.assertEqual(item.metadata["series_type"], "Saldos")
        self.assertEqual(item.metadata["currency"], "ME")

    def test_normalize_base_monetaria_observation(self) -> None:
        """Test normalizing a base monetaria observation."""
        parsed = ParsedBcraMonetariasObservation(
            fecha="2026-06-10",
            valor=41998049.0,
            variable_id=15,
            series_name="Base monetaria",
        )
        metadata = _SERIES_METADATA[15]
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        item = normalize_bcra_monetarias_observation(
            parsed=parsed,
            metadata=metadata,
            fetched_at=fetched_at,
            fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/15",
        )

        self.assertEqual(item.external_id, "Base monetaria_2026-06-10")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 6, 10, tzinfo=timezone.utc))
        self.assertIn("Base monetaria:", item.title)
        self.assertIn("41998049.0", item.title)
        self.assertIn("En millones de ARS", item.title)
        self.assertEqual(item.metadata["content_type"], "monetarias_observation")
        self.assertEqual(item.metadata["series_name"], "Base monetaria")
        self.assertEqual(item.metadata["variable_id"], 15)
        self.assertEqual(item.metadata["frequency"], "D")
        self.assertEqual(item.metadata["unit"], "En millones de ARS")
        self.assertEqual(item.metadata["currency"], "ML")

    def test_normalize_invalid_fecha_format_raises(self) -> None:
        """Test that normalizing invalid fecha format raises ValueError."""
        parsed = ParsedBcraMonetariasObservation(
            fecha="invalid-date",
            valor=100.0,
            variable_id=1,
            series_name="Reservas internacionales",
        )
        metadata = _SERIES_METADATA[1]
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_bcra_monetarias_observation(
                parsed=parsed,
                metadata=metadata,
                fetched_at=fetched_at,
                fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
            )

        self.assertIn("Invalid fecha format", str(cm.exception))


class BcraVariablesReservasConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_no_cursor_fetches_reservas(self) -> None:
        """Test that fetch_page with no cursor starts with reservas."""
        response_data = (
            FIXTURES_DIR / "reservas_internacionales_response.json"
        ).read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "15")  # Next is base monetaria
        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            result.items[0].metadata["series_name"], "Reservas internacionales"
        )
        self.assertEqual(
            transport.requests[0].url,
            "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?limit=1000",
        )

    async def test_fetch_page_cursor_reservas(self) -> None:
        """Test that fetch_page with cursor='1' fetches reservas."""
        response_data = (
            FIXTURES_DIR / "reservas_internacionales_response.json"
        ).read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page(cursor="1")

        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "15")
        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            result.items[0].metadata["series_name"], "Reservas internacionales"
        )

    async def test_fetch_page_cursor_base_monetaria(self) -> None:
        """Test that fetch_page with cursor='15' fetches base monetaria."""
        response_data = (FIXTURES_DIR / "base_monetaria_response.json").read_text(
            encoding="utf-8"
        )
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/15?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page(cursor="15")

        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "16")  # Next is circulación monetaria
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].metadata["series_name"], "Base monetaria")

    async def test_fetch_page_cursor_last_series(self) -> None:
        """Test that fetch_page with cursor for last series has no more."""
        response_data = (FIXTURES_DIR / "depositos_cc_bcra_response.json").read_text(
            encoding="utf-8"
        )
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/19?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page(cursor="19")

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            result.items[0].metadata["series_name"],
            "Depósitos de las entidades financieras en cuenta corriente en el BCRA",
        )

    async def test_fetch_page_invalid_cursor_raises(self) -> None:
        """Test that fetch_page with invalid cursor raises ValueError."""
        connector = BcraVariablesReservasConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="INVALID")

        self.assertIn("Invalid cursor", str(cm.exception))

    async def test_fetch_page_unsupported_variable_id_raises(self) -> None:
        """Test that fetch_page with unsupported variable ID raises ValueError."""
        connector = BcraVariablesReservasConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/99",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="99")

        self.assertIn("Invalid cursor", str(cm.exception))

    async def test_fetch_page_empty_results(self) -> None:
        """Test that fetch_page with empty results returns empty items."""
        response_data = (FIXTURES_DIR / "not_found_response.json").read_text(
            encoding="utf-8"
        )
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page(cursor="1")

        self.assertEqual(result.items, ())
        self.assertTrue(result.has_more)  # Should still have more series
        self.assertEqual(result.next_cursor, "15")

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "service unavailable"}',
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor="1")

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that fetch_page with unexpected status raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # Redirect - not expected for this API
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
                headers={"Content-Type": "application/json"},
                body=b'{"redirect": "somewhere"}',
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="1")

        self.assertIn("Unexpected BCRA status code 301", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="1")

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_custom_limit(self) -> None:
        """Test that fetch_page respects custom limit parameter."""
        response_data = (
            FIXTURES_DIR / "reservas_internacionales_response.json"
        ).read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?limit=10",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport, limit=10)

        result = await connector.fetch_page(cursor="1")

        self.assertEqual(len(result.items), 3)
        self.assertIn("limit=10", transport.requests[0].url)

    async def test_monetarias_observations_have_normalized_fields(self) -> None:
        """Test that monetarias observations include all required normalized fields."""
        response_data = (
            FIXTURES_DIR / "reservas_internacionales_response.json"
        ).read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraVariablesReservasConnector(transport=transport)

        result = await connector.fetch_page(cursor="1")

        self.assertEqual(len(result.items), 3)
        for item in result.items:
            # Verify all required normalized fields (AC#1)
            self.assertIsNotNone(item.published_at)  # fecha
            self.assertIn(item.metadata["unit"], item.title)  # valor + unidad
            self.assertIn(item.metadata["frequency"], item.summary)  # frecuencia
            self.assertEqual(item.source, "bcra")  # fuente
            self.assertIn(item.metadata["series_name"], item.title)  # series name

    async def test_daily_net_intervention_not_included(self) -> None:
        """Test that daily net intervention is NOT included (AC#3)."""
        # Check that no variable ID corresponds to intervention diaria neta
        # This is documented in the connector docstring
        from finance_news.connectors import bcra_variables_reservas

        doc = bcra_variables_reservas.BcraVariablesReservasConnector.__doc__
        self.assertIsNotNone(doc)
        self.assertIn("Daily net intervention", doc)
        self.assertIn("NOT included", doc)
        self.assertIn("source_research_bcra.md", doc)

        # Verify none of the supported series is intervention diaria neta
        for series_id in bcra_variables_reservas._SUPPORTED_VARIABLE_IDS:
            series_name = bcra_variables_reservas._SERIES_METADATA[series_id]["nombre"]
            self.assertNotIn("intervención", series_name.lower())
            self.assertNotIn("net intervention", series_name.lower())


if __name__ == "__main__":
    unittest.main()