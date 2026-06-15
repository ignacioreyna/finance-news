from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.indec_ipc import (
    IndecIpcConnector,
    _parse_decimal_value,
    _parse_period,
    normalize_ipc_observations,
    parse_ipc_csv,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "indec_ipc"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class IndecIpcParserTests(unittest.TestCase):
    """Test pure parser functions for INDEC IPC CSV."""

    def test_parse_ipc_csv_extracts_all_observations(self) -> None:
        """Parser should extract all valid observations from the CSV fixture."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        # Should have multiple observations
        self.assertGreater(len(observations), 10)

        # Check first observation (NIVEL GENERAL, GBA, 201612)
        first = observations[0]
        self.assertEqual(first.code, "0")
        self.assertEqual(first.description, "NIVEL GENERAL")
        self.assertEqual(first.classifier, "Nivel general y divisiones COICOP")
        self.assertEqual(first.period, "201612")
        self.assertEqual(first.index_value, "100")
        self.assertEqual(first.monthly_variation, "NA")
        self.assertEqual(first.annual_variation, "NA")
        self.assertEqual(first.region, "GBA")

        # Check that we have special categories (Estacional, Regulados, B, S)
        codes = [obs.code for obs in observations]
        descriptions = [obs.description for obs in observations]
        self.assertIn("", codes)  # Special categories have empty code
        self.assertIn("Estacional", descriptions)
        self.assertIn("Regulados", descriptions)

    def test_parse_ipc_csv_handles_multiple_regions(self) -> None:
        """Parser should extract observations for all regions."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        regions = {obs.region for obs in observations}
        expected_regions = {
            "GBA",
            "Pampeana",
            "Noreste",
            "Noroeste",
            "Cuyo",
            "Patagonia",
            "Nacional",
        }
        self.assertEqual(regions, expected_regions)

    def test_parse_ipc_csv_handles_multiple_periods(self) -> None:
        """Parser should extract observations for multiple periods."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        periods = {obs.period for obs in observations}
        self.assertIn("201612", periods)  # Base period
        self.assertIn("202601", periods)  # Recent period

    def test_parse_ipc_csv_handles_special_categories(self) -> None:
        """Parser should extract special categories (Estacional, Regulados, B, S)."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        # Find special category observations
        special_obs = [obs for obs in observations if not obs.code]
        special_descriptions = {obs.description for obs in special_obs}

        self.assertIn("Estacional", special_descriptions)
        self.assertIn("Regulados", special_descriptions)

        # B and S categories have "Bienes y servicios" as description
        bs_obs = [obs for obs in special_obs if obs.description == "Bienes y servicios"]
        bs_codes = {obs.code for obs in bs_obs}
        # B and S have empty code but are distinguished by other context
        # In our fixture, they're separate rows with same description

    def test_parse_ipc_csv_raises_on_empty_file(self) -> None:
        """Parser should raise ValueError for empty CSV."""
        with self.assertRaises(ValueError) as cm:
            parse_ipc_csv("")
        self.assertIn("Empty CSV", str(cm.exception))

    def test_parse_ipc_csv_raises_on_invalid_header(self) -> None:
        """Parser should raise ValueError for invalid header."""
        invalid_csv = "Invalid;Header;Format\n0;Test;Data;202601;100;1;1;GBA"
        with self.assertRaises(ValueError) as cm:
            parse_ipc_csv(invalid_csv)
        self.assertIn("Unexpected CSV header", str(cm.exception))

    def test_parse_ipc_csv_raises_on_invalid_row_length(self) -> None:
        """Parser should raise ValueError for rows with wrong field count."""
        invalid_csv = (
            "Codigo;Descripcion;Clasificador;Periodo;Indice_IPC;v_m_IPC;v_i_a_IPC;Region\n"
            "0;Test;Data"  # Only 3 fields
        )
        with self.assertRaises(ValueError) as cm:
            parse_ipc_csv(invalid_csv)
        self.assertIn("has 3 fields, expected 8", str(cm.exception))


class IndecIpcHelperTests(unittest.TestCase):
    """Test helper functions for parsing IPC values."""

    def test_parse_period_valid_formats(self) -> None:
        """Period parser should handle valid YYYYMM formats."""
        self.assertEqual(
            _parse_period("201612"), datetime(2016, 12, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_period("202601"), datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_period("202506"), datetime(2025, 6, 1, tzinfo=timezone.utc)
        )

    def test_parse_period_invalid_formats(self) -> None:
        """Period parser should reject invalid formats."""
        with self.assertRaises(ValueError):
            _parse_period("2016")  # Too short
        with self.assertRaises(ValueError):
            _parse_period("2016123")  # Too long
        with self.assertRaises(ValueError):
            _parse_period("abcd12")  # Non-numeric
        with self.assertRaises(ValueError):
            _parse_period("201613")  # Invalid month

    def test_parse_decimal_value_numeric(self) -> None:
        """Decimal parser should handle comma-separated values."""
        self.assertEqual(_parse_decimal_value("100"), 100.0)
        self.assertEqual(_parse_decimal_value("11594,5499"), 11594.5499)
        self.assertEqual(_parse_decimal_value("2,3"), 2.3)
        self.assertEqual(_parse_decimal_value("0,5"), 0.5)

    def test_parse_decimal_value_na_and_empty(self) -> None:
        """Decimal parser should return None for NA and empty values."""
        self.assertIsNone(_parse_decimal_value("NA"))
        self.assertIsNone(_parse_decimal_value("na"))
        self.assertIsNone(_parse_decimal_value(""))
        self.assertIsNone(_parse_decimal_value(None))  # type: ignore[arg-type]


class IndecIpcNormalizationTests(unittest.TestCase):
    """Test normalization of parsed observations to SourceItem objects."""

    def test_normalize_creates_source_items_for_all_observations(self) -> None:
        """Normalizer should create a SourceItem for each observation."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Should have one item per observation
        self.assertEqual(len(items), len(observations))

    def test_normalize_populates_required_fields(self) -> None:
        """Normalizer should populate all required SourceItem fields."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        # Test with NIVEL GENERAL observation
        nivel_general_obs = [obs for obs in observations if obs.code == "0"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=[nivel_general_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        self.assertEqual(len(items), 1)
        item = items[0]

        # Check required fields
        self.assertIsNotNone(item.external_id)
        self.assertEqual(item.source, "indec")
        self.assertIsNotNone(item.published_at)
        self.assertIsNotNone(item.title)
        self.assertIsNone(item.body)  # CSV has no body
        self.assertIsNotNone(item.summary)
        self.assertEqual(item.url, "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv")

        # Check provenance
        self.assertEqual(item.provenance.connector, "indec_ipc")
        self.assertEqual(item.provenance.source, "indec")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.provenance.fetched_at, fetched_at)

        # Check freshness
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, 24 * 60 * 60)

    def test_normalize_includes_metadata(self) -> None:
        """Normalizer should include IPC-specific metadata."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        # Test with a division observation
        division_obs = [obs for obs in observations if obs.code == "01"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=[division_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        self.assertEqual(len(items), 1)
        metadata = items[0].metadata

        # Check metadata fields
        self.assertEqual(metadata["category_code"], "01")
        self.assertIn("Alimentos", metadata["category_description"])
        self.assertEqual(metadata["classifier"], "Nivel general y divisiones COICOP")
        self.assertEqual(metadata["period"], "201612")
        self.assertEqual(metadata["region"], "GBA")
        self.assertEqual(metadata["index_value"], 100.0)
        self.assertIsNone(metadata["monthly_variation_pct"])
        self.assertIsNone(metadata["annual_variation_pct"])

    def test_normalize_generates_unique_external_ids(self) -> None:
        """Normalizer should generate unique external_ids for each observation."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        external_ids = [item.external_id for item in items]
        # All external IDs should be unique
        self.assertEqual(len(external_ids), len(set(external_ids)))

    def test_normalize_builds_meaningful_titles(self) -> None:
        """Normalizer should build meaningful titles for each observation."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Check NIVEL GENERAL title
        nivel_general_items = [item for item in items if item.external_id.startswith("ipc_0_")]
        self.assertGreater(len(nivel_general_items), 0)
        self.assertIn("IPC Nacional", nivel_general_items[0].title)

        # Check division title
        division_items = [item for item in items if item.external_id.startswith("ipc_01_")]
        self.assertGreater(len(division_items), 0)
        self.assertIn("Alimentos", division_items[0].title)

    def test_normalize_includes_summary_with_available_data(self) -> None:
        """Normalizer should include summary with available IPC data."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )
        observations = parse_ipc_csv(csv_text)

        # Use a recent observation with actual values (not NA)
        recent_obs = [obs for obs in observations if obs.period == "202601" and obs.code == "0"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_ipc_observations(
            observations=[recent_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        summary = items[0].summary
        self.assertIn("202601", summary)
        self.assertIn("Índice:", summary)
        self.assertIn("Var. mensual:", summary)
        self.assertIn("Var. interanual:", summary)
        self.assertIn("Región:", summary)


class IndecIpcConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Test the async connector implementation."""

    async def test_fetch_page_returns_all_observations(self) -> None:
        """Connector should fetch and return all IPC observations."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("iso-8859-1"),
            )
        )

        connector = IndecIpcConnector(transport=transport)
        result = await connector.fetch_page()

        # Should return all observations
        self.assertGreater(len(result.items), 10)

        # No pagination
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Should have used correct URL
        self.assertEqual(
            transport.requests[0].url,
            "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
        )

    async def test_fetch_page_handles_encoding_correctly(self) -> None:
        """Connector should handle ISO-8859-1 encoding."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("iso-8859-1"),
            )
        )

        connector = IndecIpcConnector(transport=transport)
        result = await connector.fetch_page()

        # Should successfully parse without encoding errors
        self.assertGreater(len(result.items), 0)

    async def test_fetch_page_raises_recoverable_for_404(self) -> None:
        """Connector should raise RecoverableConnectorError for 404."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={},
                body=b"",
            )
        )

        connector = IndecIpcConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("not found", str(cm.exception).lower())

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={},
                body=b"",
            )
        )

        connector = IndecIpcConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_raises_value_for_unexpected_status(self) -> None:
        """Connector should raise ValueError for unexpected status codes."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # 3xx should raise ValueError, not RecoverableConnectorError
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={},
                body=b"",
            )
        )

        connector = IndecIpcConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()
        self.assertIn("301", str(cm.exception))

    async def test_fetch_page_includes_transport_metadata(self) -> None:
        """Connector should include transport metadata in provenance."""
        csv_text = (FIXTURES_DIR / "serie_ipc_divisiones.csv").read_text(
            encoding="iso-8859-1"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
                headers={"Content-Type": "text/csv; charset=ISO-8859-1"},
                body=csv_text.encode("iso-8859-1"),
            )
        )

        connector = IndecIpcConnector(transport=transport)
        result = await connector.fetch_page()

        # Check that items have transport metadata
        self.assertGreater(len(result.items), 0)
        transport_metadata = result.items[0].provenance.transport_metadata
        self.assertEqual(transport_metadata["status_code"], 200)
        self.assertEqual(transport_metadata["content_type"], "text/csv; charset=ISO-8859-1")
        self.assertIn("observation_count", transport_metadata)

    async def test_fetch_page_documentation_note_on_ipc_nucleo(self) -> None:
        """Connector docstring should document the IPC núcleo gap."""
        # This test verifies that the connector's docstring documents the
        # known gap about IPC núcleo not being available as a downloadable series
        connector = IndecIpcConnector(transport=_FakeTransport(HttpResponse(status_code=200, url="", headers={}, body=b"")))

        docstring = IndecIpcConnector.__doc__
        self.assertIsNotNone(docstring)
        self.assertIn("núcleo", docstring.lower())
        # The docstring should mention that it's NOT available as CSV/XLS
        self.assertTrue(
            "does not publish" in docstring.lower() or "not available" in docstring.lower() or "gap" in docstring.lower(),
            f"Docstring should mention IPC núcleo gap: {docstring}"
        )


if __name__ == "__main__":
    unittest.main()