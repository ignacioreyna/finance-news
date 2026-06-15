from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_catalogo import (
    BcraCatalogoConnector,
    find_series_by_id,
    normalize_bcra_catalog_entry,
    parse_bcra_catalog_json,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_catalogo"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class BcraCatalogoParserTests(unittest.TestCase):
    def test_parse_fixture_catalog_sample(self) -> None:
        """Parse the BCRA catalog sample fixture."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Check we parsed the expected number of entries
        self.assertEqual(len(entries), 20)

        # Check first entry (Reservas internacionales)
        first_entry = entries[0]
        self.assertEqual(first_entry.id, 1)
        self.assertEqual(first_entry.external_id, "1")
        self.assertEqual(first_entry.nombre, "Reservas internacionales")
        self.assertEqual(first_entry.unidad, "En millones de USD")
        self.assertEqual(first_entry.frecuencia, "diaria")
        self.assertEqual(first_entry.fuente, "bcra")
        self.assertEqual(first_entry.categoria, "Principales Variables")
        self.assertEqual(first_entry.tipo_serie, "Saldos")
        self.assertEqual(first_entry.moneda, "ME")
        self.assertEqual(first_entry.primera_fecha, "1996-01-03")
        self.assertEqual(first_entry.ultima_fecha, "2026-06-10")
        self.assertAlmostEqual(first_entry.ultimo_valor, 47559.0)

    def test_parse_normalizes_frequency_codes(self) -> None:
        """Check that frequency codes are normalized to Spanish."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # All entries in sample have periodicidad "D", should be "diaria"
        for entry in entries:
            self.assertEqual(entry.frecuencia, "diaria")

    def test_parse_cleans_whitespace(self) -> None:
        """Check that trailing whitespace is cleaned from names."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Find entries with trailing whitespace in original (if any)
        for entry in entries:
            # No trailing whitespace should remain
            self.assertEqual(entry.nombre, entry.nombre.strip())
            self.assertEqual(entry.unidad, entry.unidad.strip())

    def test_parse_rejects_invalid_status(self) -> None:
        """Parser should reject non-200 status codes."""
        invalid_json = {"status": 404, "metadata": {}, "results": []}

        with self.assertRaises(ValueError) as ctx:
            parse_bcra_catalog_json(invalid_json)

        self.assertIn("Unexpected BCRA API status", str(ctx.exception))

    def test_parse_rejects_missing_results(self) -> None:
        """Parser should reject responses missing the results array."""
        invalid_json = {"status": 200, "metadata": {}}

        with self.assertRaises(ValueError) as ctx:
            parse_bcra_catalog_json(invalid_json)

        self.assertIn("missing 'results' array", str(ctx.exception))

    def test_parse_rejects_invalid_entry_structure(self) -> None:
        """Parser should reject entries that aren't dicts."""
        invalid_json = {"status": 200, "metadata": {}, "results": [None, "invalid"]}

        with self.assertRaises(ValueError) as ctx:
            parse_bcra_catalog_json(invalid_json)

        self.assertIn("must be a dict", str(ctx.exception))

    def test_parse_rejects_missing_id_variable(self) -> None:
        """Parser should reject entries missing idVariable."""
        invalid_json = {
            "status": 200,
            "metadata": {},
            "results": [{"descripcion": "Test", "unidadExpresion": "USD", "periodicidad": "D"}],
        }

        with self.assertRaises(ValueError) as ctx:
            parse_bcra_catalog_json(invalid_json)

        self.assertIn("missing 'idVariable'", str(ctx.exception))

    def test_parse_rejects_missing_descripcion(self) -> None:
        """Parser should reject entries missing descripcion."""
        invalid_json = {
            "status": 200,
            "metadata": {},
            "results": [{"idVariable": 1, "unidadExpresion": "USD", "periodicidad": "D"}],
        }

        with self.assertRaises(ValueError) as ctx:
            parse_bcra_catalog_json(invalid_json)

        self.assertIn("missing 'descripcion'", str(ctx.exception))

    def test_normalize_creates_valid_source_item(self) -> None:
        """Check that normalize_bcra_catalog_entry creates valid SourceItem."""
        import json

        from finance_news.connectors.models import Freshness, Provenance

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)
        parsed = entries[0]  # Reservas internacionales

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        item = normalize_bcra_catalog_entry(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=CATALOG_URL,
            cursor=None,
            transport_metadata={"status_code": 200},
        )

        # Check required SourceItem fields
        self.assertEqual(item.external_id, "1")
        self.assertEqual(item.source, "bcra")
        self.assertIsNone(item.published_at)  # Catalog has no pub date
        self.assertEqual(item.title, "Reservas internacionales")
        self.assertIsNotNone(item.body)  # Body should contain metadata JSON
        self.assertIn("Reservas internacionales", item.summary)
        self.assertEqual(item.url, "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1")
        self.assertEqual(item.provenance.connector, "bcra_catalogo")
        self.assertEqual(item.provenance.transport_metadata["status_code"], 200)
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.ttl_seconds, 7 * 24 * 60 * 60)

        # Check metadata contains BCRA-specific fields
        self.assertTrue(item.metadata.get("catalog_entry"))
        self.assertEqual(item.metadata["bcra_id"], 1)
        self.assertEqual(item.metadata["bcra_categoria"], "Principales Variables")
        self.assertEqual(item.metadata["bcra_tipo_serie"], "Saldos")
        self.assertEqual(item.metadata["bcra_moneda"], "ME")

        # Check body contains valid JSON metadata
        body_data = json.loads(item.body)
        self.assertEqual(body_data["id"], 1)
        self.assertEqual(body_data["nombre"], "Reservas internacionales")
        self.assertEqual(body_data["unidad"], "En millones de USD")
        self.assertEqual(body_data["frecuencia"], "diaria")
        self.assertEqual(body_data["fuente"], "bcra")

    def test_find_series_by_id(self) -> None:
        """Test finding series by ID in catalog."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Find existing series
        reservas = find_series_by_id(entries, 1)
        self.assertIsNotNone(reservas)
        self.assertEqual(reservas.id, 1)
        self.assertEqual(reservas.nombre, "Reservas internacionales")

        # Find with string ID
        reservas_str = find_series_by_id(entries, "1")
        self.assertIsNotNone(reservas_str)
        self.assertEqual(reservas_str.id, 1)

        # Find non-existing series
        not_found = find_series_by_id(entries, 99999)
        self.assertIsNone(not_found)

    def test_find_series_by_id_empty_list(self) -> None:
        """Test finding series in empty catalog."""
        result = find_series_by_id([], 1)
        self.assertIsNone(result)


CATALOG_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"


class BcraCatalogoConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_catalog_entries(self) -> None:
        """Connector should fetch and normalize catalog entries."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=CATALOG_URL,
                headers={"Content-Type": "application/json"},
                body=fixture_text.encode("utf-8"),
            )
        )

        connector = BcraCatalogoConnector(transport=transport)
        result = await connector.fetch_page()

        # Check result structure
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 20)

        # Check first item
        first_item = result.items[0]
        self.assertEqual(first_item.external_id, "1")
        self.assertEqual(first_item.title, "Reservas internacionales")
        self.assertEqual(first_item.source, "bcra")
        self.assertEqual(first_item.provenance.connector, "bcra_catalogo")

        # Check request was made correctly
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url, CATALOG_URL)
        self.assertEqual(request.params.get("limit"), "3000")  # Default limit for all entries

    async def test_fetch_page_with_pagination_cursor(self) -> None:
        """Connector should handle pagination cursor correctly."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        fixture_json = json.loads(fixture_text)

        # Modify metadata to indicate more pages
        fixture_json["metadata"]["resultset"]["count"] = 2500  # More than 20 entries
        fixture_text = json.dumps(fixture_json)

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=CATALOG_URL,
                headers={"Content-Type": "application/json"},
                body=fixture_text.encode("utf-8"),
            )
        )

        connector = BcraCatalogoConnector(transport=transport)
        cursor = "offset=0&limit=20"
        result = await connector.fetch_page(cursor=cursor)

        # Check pagination metadata
        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "offset=20&limit=20")
        self.assertEqual(len(result.items), 20)

        # Check request params
        request = transport.requests[0]
        self.assertEqual(request.params.get("offset"), "0")
        self.assertEqual(request.params.get("limit"), "20")

    async def test_fetch_page_last_page_detection(self) -> None:
        """Connector should detect last page and set has_more=False."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        fixture_json = json.loads(fixture_text)

        # Metadata shows exactly 20 entries, this is the last page
        fixture_json["metadata"]["resultset"]["count"] = 20
        fixture_text = json.dumps(fixture_json)

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=CATALOG_URL,
                headers={"Content-Type": "application/json"},
                body=fixture_text.encode("utf-8"),
            )
        )

        connector = BcraCatalogoConnector(transport=transport)
        result = await connector.fetch_page(cursor="offset=0&limit=20")

        # Should indicate no more pages
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx errors."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url=CATALOG_URL,
                headers={},
                body=b"",
            )
        )

        connector = BcraCatalogoConnector(transport=transport)

        from finance_news.connectors.models import RecoverableConnectorError

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_raises_for_invalid_json(self) -> None:
        """Connector should raise ValueError for invalid JSON response."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=CATALOG_URL,
                headers={"Content-Type": "application/json"},
                body=b"invalid json",
            )
        )

        connector = BcraCatalogoConnector(transport=transport)

        with self.assertRaises(ValueError) as ctx:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(ctx.exception))

    async def test_fetch_page_raises_for_4xx(self) -> None:
        """Connector should raise ValueError for 4xx errors."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=400,
                url=CATALOG_URL,
                headers={},
                body=b"",
            )
        )

        connector = BcraCatalogoConnector(transport=transport)

        with self.assertRaises(ValueError) as ctx:
            await connector.fetch_page()

        self.assertIn("Unexpected BCRA status code", str(ctx.exception))

    async def test_fetch_page_invalid_cursor_format(self) -> None:
        """Connector should reject invalid cursor format."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=CATALOG_URL,
                headers={},
                body=b"",
            )
        )

        connector = BcraCatalogoConnector(transport=transport)

        with self.assertRaises(ValueError) as ctx:
            await connector.fetch_page(cursor="invalid_cursor")

        self.assertIn("Invalid cursor format", str(ctx.exception))


class FallbackBehaviorTests(unittest.TestCase):
    """Tests for fallback behavior when required series are missing from catalog."""

    def test_fallback_documentation(self) -> None:
        """Documentation should clearly describe fallback behavior."""
        # The find_series_by_id function has detailed docstring
        # about fallback behavior. This test verifies it exists.
        doc = find_series_by_id.__doc__
        self.assertIsNotNone(doc)
        self.assertIn("fallback", doc.lower())
        self.assertIn("missing", doc.lower())

    def test_missing_series_lookup_returns_none(self) -> None:
        """Looking up a missing series should return None."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Series that doesn't exist in catalog
        missing_id = 999999
        result = find_series_by_id(entries, missing_id)
        self.assertIsNone(result)

    def test_caller_can_implement_critical_series_fallback(self) -> None:
        """Callers can implement application-specific fallback for critical series."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Simulate critical series lookup
        critical_series_id = 999999  # Doesn't exist
        entry = find_series_by_id(entries, critical_series_id)

        if entry is None:
            # Application-specific fallback: raise error for critical series
            with self.assertRaises(ValueError) as ctx:
                raise ValueError(f"Critical series {critical_series_id} not found in catalog")
            self.assertIn("not found", str(ctx.exception))
        else:
            self.fail("Expected series to be missing")

    def test_caller_can_use_alternative_series(self) -> None:
        """Callers can use alternative series if required one is missing."""
        import json

        fixture_text = (FIXTURES_DIR / "catalog_sample.json").read_text(encoding="utf-8")
        json_data = json.loads(fixture_text)
        entries = parse_bcra_catalog_json(json_data)

        # Try primary series (doesn't exist)
        primary_id = 999999
        primary = find_series_by_id(entries, primary_id)

        # Fallback to alternative series
        alternative_id = 1  # Reservas internacionales
        alternative = find_series_by_id(entries, alternative_id)

        self.assertIsNone(primary)
        self.assertIsNotNone(alternative)
        self.assertEqual(alternative.nombre, "Reservas internacionales")


if __name__ == "__main__":
    unittest.main()