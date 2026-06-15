from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_tasas_cer_tamar import (
    BcraTasasCerTamarConnector,
    normalize_bcra_rate_observation,
    parse_bcra_monetarias_response,
    ParsedBcraRateObservation,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_tasas_cer_tamar"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraTasasCerTamarParserTests(unittest.TestCase):
    def test_parse_cer_response(self) -> None:
        """Test parsing CER response from BCRA API."""
        response_data = (FIXTURES_DIR / "cer_response.json").read_text(encoding="utf-8")
        import json

        observations = parse_bcra_monetarias_response(json.loads(response_data), "CER")

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-15")
        self.assertAlmostEqual(observations[0].valor, 790.9415888555)
        self.assertEqual(observations[0].rate_name, "CER")
        self.assertEqual(observations[0].variable_id, 30)

    def test_parse_tamar_response(self) -> None:
        """Test parsing TAMAR response from BCRA API."""
        response_data = (FIXTURES_DIR / "tamar_response.json").read_text(encoding="utf-8")
        import json

        observations = parse_bcra_monetarias_response(json.loads(response_data), "TAMAR")

        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[0].fecha, "2026-06-11")
        self.assertAlmostEqual(observations[0].valor, 21.5)
        self.assertEqual(observations[0].rate_name, "TAMAR")
        self.assertEqual(observations[0].variable_id, 44)

    def test_parse_empty_response(self) -> None:
        """Test parsing empty results from BCRA API."""
        response_data = (FIXTURES_DIR / "not_found_response.json").read_text(
            encoding="utf-8"
        )
        import json

        observations = parse_bcra_monetarias_response(json.loads(response_data), "CER")

        self.assertEqual(len(observations), 0)

    def test_parse_invalid_status_raises(self) -> None:
        """Test that parsing non-200 status raises ValueError."""
        invalid_response = {
            "status": 500,
            "metadata": {"resultset": {"count": 0, "offset": 0, "limit": 1000}},
            "results": [],
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "CER")

        self.assertIn("Unexpected status code", str(cm.exception))

    def test_parse_invalid_detalle_format_raises(self) -> None:
        """Test that parsing invalid detalle format raises ValueError."""
        invalid_response = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [{"idVariable": 30, "detalle": "not a list"}],
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "CER")

        self.assertIn("Expected 'detalle' to be a list", str(cm.exception))

    def test_parse_invalid_observation_format_raises(self) -> None:
        """Test that parsing invalid observation format raises ValueError."""
        invalid_response = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [{"idVariable": 30, "detalle": [{"fecha": "2026-06-15"}]}],  # Missing valor
        }

        with self.assertRaises(ValueError) as cm:
            parse_bcra_monetarias_response(invalid_response, "CER")

        self.assertIn("Invalid observation format", str(cm.exception))

    def test_normalize_cer_observation(self) -> None:
        """Test normalizing a CER observation."""
        parsed = ParsedBcraRateObservation(
            fecha="2026-06-15", valor=790.9415888555, variable_id=30, rate_name="CER"
        )
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        item = normalize_bcra_rate_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
        )

        self.assertEqual(item.external_id, "CER_2026-06-15")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 6, 15, tzinfo=timezone.utc))
        self.assertIn("CER:", item.title)
        self.assertIn("790.94", item.title)
        self.assertIn("Coeficiente de estabilización", item.summary)
        self.assertEqual(item.metadata["content_type"], "rate_observation")
        self.assertEqual(item.metadata["rate_name"], "CER")
        self.assertEqual(item.metadata["variable_id"], 30)
        self.assertEqual(item.metadata["frequency"], "D")
        self.assertEqual(item.metadata["unit"], "Índice base 2.2.02=1")
        # Verify separation from BCRA norms: no document_type or circular_reference
        self.assertNotIn("document_type", item.metadata)
        self.assertNotIn("circular_reference", item.metadata)
        # Verify rate-specific metadata present
        self.assertEqual(item.metadata["category"], "Principales Variables")
        self.assertEqual(item.metadata["series_type"], "Índice")

    def test_normalize_tamar_observation(self) -> None:
        """Test normalizing a TAMAR observation."""
        parsed = ParsedBcraRateObservation(
            fecha="2026-06-11", valor=21.5, variable_id=44, rate_name="TAMAR"
        )
        fetched_at = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)

        item = normalize_bcra_rate_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/44",
        )

        self.assertEqual(item.external_id, "TAMAR_2026-06-11")
        self.assertEqual(item.source, "bcra")
        self.assertEqual(item.published_at, datetime(2026, 6, 11, tzinfo=timezone.utc))
        self.assertIn("TAMAR:", item.title)
        self.assertIn("21.5", item.title)
        self.assertIn("Tasa de interes TAMAR", item.summary)
        self.assertEqual(item.metadata["content_type"], "rate_observation")
        self.assertEqual(item.metadata["rate_name"], "TAMAR")
        self.assertEqual(item.metadata["variable_id"], 44)
        self.assertEqual(item.metadata["frequency"], "D")
        self.assertEqual(item.metadata["unit"], "En porcentaje nominal anual")
        # Verify separation from BCRA norms
        self.assertNotIn("document_type", item.metadata)
        self.assertNotIn("circular_reference", item.metadata)
        self.assertEqual(item.metadata["category"], "Principales Variables")
        self.assertEqual(item.metadata["series_type"], "Tasa de interés")

    def test_normalize_unknown_rate_name_raises(self) -> None:
        """Test that normalizing unknown rate name raises ValueError."""
        parsed = ParsedBcraRateObservation(
            fecha="2026-06-15", valor=100.0, variable_id=99, rate_name="UNKNOWN"
        )
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_bcra_rate_observation(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/99",
            )

        self.assertIn("Unknown rate name", str(cm.exception))

    def test_normalize_invalid_fecha_format_raises(self) -> None:
        """Test that normalizing invalid fecha format raises ValueError."""
        parsed = ParsedBcraRateObservation(
            fecha="invalid-date", valor=100.0, variable_id=30, rate_name="CER"
        )
        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_bcra_rate_observation(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
            )

        self.assertIn("Invalid fecha format", str(cm.exception))


class BcraTasasCerTamarConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_no_cursor_fetches_cer(self) -> None:
        """Test that fetch_page with no cursor fetches CER and sets cursor to TAMAR."""
        response_data = (FIXTURES_DIR / "cer_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "TAMAR")
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].metadata["rate_name"], "CER")
        self.assertEqual(transport.requests[0].url, "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?limit=1000")

    async def test_fetch_page_cursor_cer(self) -> None:
        """Test that fetch_page with cursor='CER' fetches CER."""
        response_data = (FIXTURES_DIR / "cer_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        result = await connector.fetch_page(cursor="CER")

        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "TAMAR")
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].metadata["rate_name"], "CER")

    async def test_fetch_page_cursor_tamar(self) -> None:
        """Test that fetch_page with cursor='TAMAR' fetches TAMAR."""
        response_data = (FIXTURES_DIR / "tamar_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/44?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        result = await connector.fetch_page(cursor="TAMAR")

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].metadata["rate_name"], "TAMAR")
        self.assertEqual(transport.requests[0].url, "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/44?limit=1000")

    async def test_fetch_page_invalid_cursor_raises(self) -> None:
        """Test that fetch_page with invalid cursor raises ValueError."""
        connector = BcraTasasCerTamarConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="INVALID")

        self.assertIn("Invalid cursor", str(cm.exception))

    async def test_fetch_page_404_returns_empty(self) -> None:
        """Test that fetch_page with 404 returns empty results."""
        response_data = (FIXTURES_DIR / "not_found_response.json").read_text(
            encoding="utf-8"
        )
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/99",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        result = await connector.fetch_page(cursor="CER")

        self.assertEqual(result.items, ())
        self.assertTrue(result.has_more)  # Should still have more (TAMAR)
        self.assertEqual(result.next_cursor, "TAMAR")

    async def test_fetch_page_4xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 4xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=429,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "rate limited"}',
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor="CER")

        self.assertIn("429", str(cm.exception))

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "service unavailable"}',
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor="CER")

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that fetch_page with unexpected status raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # Redirect - not expected for this API
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
                headers={"Content-Type": "application/json"},
                body=b'{"redirect": "somewhere"}',
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="CER")

        self.assertIn("Unexpected BCRA status code 301", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="CER")

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_custom_limit(self) -> None:
        """Test that fetch_page respects custom limit parameter."""
        response_data = (FIXTURES_DIR / "cer_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?limit=10",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport, limit=10)

        result = await connector.fetch_page(cursor="CER")

        self.assertEqual(len(result.items), 3)
        self.assertIn("limit=10", transport.requests[0].url)

    async def test_rate_observations_separated_from_norms(self) -> None:
        """Test that rate observations are separated from BCRA norms via metadata."""
        response_data = (FIXTURES_DIR / "cer_response.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/30?limit=1000",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = BcraTasasCerTamarConnector(transport=transport)

        result = await connector.fetch_page(cursor="CER")

        # Verify rate observation metadata
        self.assertEqual(len(result.items), 3)
        for item in result.items:
            # Rate observations have content_type="rate_observation"
            self.assertEqual(item.metadata["content_type"], "rate_observation")
            # Rate observations have rate_name, variable_id, frequency
            self.assertIn("rate_name", item.metadata)
            self.assertIn("variable_id", item.metadata)
            self.assertIn("frequency", item.metadata)
            # Rate observations do NOT have normative fields
            self.assertNotIn("document_type", item.metadata)
            self.assertNotIn("circular_reference", item.metadata)
            self.assertNotIn("document_number", item.metadata)


if __name__ == "__main__":
    unittest.main()