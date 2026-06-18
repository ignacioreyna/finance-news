from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.dol_weekly_claims import (
    DolWeeklyClaimsConnector,
    FALLBACK_BEHAVIOR_DOCUMENTED,
    _parse_value,
    _parse_week_ending,
    _parse_dol_weekly_claims_csv,
    normalize_dol_weekly_claims_observations,
    parse_dol_weekly_claims_xml,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "dol_weekly_claims"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class DolWeeklyClaimsParserTests(unittest.TestCase):
    """Test pure parser functions for DOL weekly claims XML."""

    def test_parse_xml_extracts_initial_and_continued_claims(self) -> None:
        """Parser should extract both initial and continued claims from XML."""
        xml_text = (FIXTURES_DIR / "weekly_claims.xml").read_text(encoding="utf-8")
        observations = parse_dol_weekly_claims_xml(xml_text)

        # Should have both initial and continued claims
        self.assertEqual(len(observations), 2)

        # Check initial claims observation (AC#1)
        initial = [obs for obs in observations if obs.series_type == "initial"][0]
        self.assertEqual(initial.series_type, "initial")
        self.assertEqual(initial.week_ending, "2025-06-07")
        self.assertEqual(initial.value, "233000")
        self.assertEqual(initial.prior_week_revised, "229000")
        self.assertTrue(initial.seasonally_adjusted)

        # Check continued claims observation (AC#1)
        continued = [obs for obs in observations if obs.series_type == "continued"][0]
        self.assertEqual(continued.series_type, "continued")
        self.assertEqual(continued.week_ending, "2025-06-07")
        self.assertEqual(continued.value, "1843000")
        self.assertEqual(continued.prior_week_revised, "1835000")
        self.assertTrue(continued.seasonally_adjusted)

    def test_parse_xml_handles_missing_prior_week_revision(self) -> None:
        """Parser should handle observations without prior week revision."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<dol_weekly_claims>
  <weekly_data>
    <observation>
      <series_type>initial</series_type>
      <week_ending>2025-06-07</week_ending>
      <value>233000</value>
      <seasonally_adjusted>true</seasonally_adjusted>
    </observation>
  </weekly_data>
</dol_weekly_claims>
"""
        observations = parse_dol_weekly_claims_xml(xml_text)

        self.assertEqual(len(observations), 1)
        self.assertIsNone(observations[0].prior_week_revised)

    def test_parse_xml_raises_on_invalid_xml(self) -> None:
        """Parser should raise ValueError for invalid XML."""
        invalid_xml = "This is not valid XML at all"
        with self.assertRaises(ValueError) as cm:
            parse_dol_weekly_claims_xml(invalid_xml)
        self.assertIn("Invalid XML", str(cm.exception))

    def test_parse_xml_raises_on_empty_xml(self) -> None:
        """Parser should raise ValueError for XML with no observations."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<dol_weekly_claims>
  <weekly_data>
  </weekly_data>
</dol_weekly_claims>
"""
        with self.assertRaises(ValueError) as cm:
            parse_dol_weekly_claims_xml(empty_xml)
        self.assertIn("No weekly claims observations found", str(cm.exception))

    def test_parse_csv_extracts_initial_and_continued_claims(self) -> None:
        """CSV parser should extract both initial and continued claims."""
        csv_text = """Series_Type,Week_Ending,Value,Prior_Week_Revised
initial,2025-06-07,233000,229000
continued,2025-06-07,1843000,1835000
"""
        observations = _parse_dol_weekly_claims_csv(csv_text)

        # Should have both initial and continued claims
        self.assertEqual(len(observations), 2)

        # Check initial claims
        initial = [obs for obs in observations if obs.series_type == "initial"][0]
        self.assertEqual(initial.week_ending, "2025-06-07")
        self.assertEqual(initial.value, "233000")

        # Check continued claims
        continued = [obs for obs in observations if obs.series_type == "continued"][0]
        self.assertEqual(continued.week_ending, "2025-06-07")
        self.assertEqual(continued.value, "1843000")

    def test_parse_csv_handles_missing_columns(self) -> None:
        """CSV parser should handle missing optional columns."""
        csv_text = """Series_Type,Week_Ending,Value
initial,2025-06-07,233000
continued,2025-06-07,1843000
"""
        observations = _parse_dol_weekly_claims_csv(csv_text)

        self.assertEqual(len(observations), 2)
        # Both should have None for prior_week_revised
        for obs in observations:
            self.assertIsNone(obs.prior_week_revised)


class DolWeeklyClaimsHelperTests(unittest.TestCase):
    """Test helper functions for parsing DOL weekly claims values."""

    def test_parse_week_ending_iso_format(self) -> None:
        """Week ending parser should handle ISO format YYYY-MM-DD."""
        self.assertEqual(
            _parse_week_ending("2025-06-07"), datetime(2025, 6, 7, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_week_ending("2024-12-31"), datetime(2024, 12, 31, tzinfo=timezone.utc)
        )

    def test_parse_week_ending_us_format(self) -> None:
        """Week ending parser should handle US format MM/DD/YYYY."""
        self.assertEqual(
            _parse_week_ending("06/07/2025"), datetime(2025, 6, 7, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_week_ending("12/31/2024"), datetime(2024, 12, 31, tzinfo=timezone.utc)
        )

    def test_parse_week_ending_compact_format(self) -> None:
        """Week ending parser should handle compact format YYYYMMDD."""
        self.assertEqual(
            _parse_week_ending("20250607"), datetime(2025, 6, 7, tzinfo=timezone.utc)
        )

    def test_parse_week_ending_invalid_formats(self) -> None:
        """Week ending parser should reject invalid formats."""
        with self.assertRaises(ValueError):
            _parse_week_ending("2025-13-01")  # Invalid month
        with self.assertRaises(ValueError):
            _parse_week_ending("not-a-date")  # Invalid format

    def test_parse_value_numeric(self) -> None:
        """Value parser should handle numeric values with/without commas."""
        self.assertEqual(_parse_value("233000"), 233000)
        self.assertEqual(_parse_value("233,000"), 233000)
        self.assertEqual(_parse_value("1,843,000"), 1843000)
        self.assertEqual(_parse_value("0"), 0)

    def test_parse_value_empty_and_whitespace(self) -> None:
        """Value parser should return None for empty and whitespace values."""
        self.assertIsNone(_parse_value(""))
        self.assertIsNone(_parse_value("   "))
        self.assertIsNone(_parse_value(None))  # type: ignore[arg-type]


class DolWeeklyClaimsNormalizationTests(unittest.TestCase):
    """Test normalization of parsed observations to SourceItem objects."""

    def test_normalize_creates_source_items_for_all_observations(self) -> None:
        """Normalizer should create a SourceItem for each observation."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            ),
            ParsedDolWeeklyClaimsObservation(
                series_type="continued",
                week_ending="2025-06-07",
                value="1843000",
                prior_week_revised="1835000",
                seasonally_adjusted=True,
            ),
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        # Should have one item per observation
        self.assertEqual(len(items), 2)

    def test_normalize_populates_required_fields(self) -> None:
        """Normalizer should populate all required SourceItem fields."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            )
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        self.assertEqual(len(items), 1)
        item = items[0]

        # Check required fields
        self.assertIsNotNone(item.external_id)
        self.assertEqual(item.source, "dol")
        self.assertIsNotNone(item.published_at)
        self.assertIsNotNone(item.title)
        self.assertIsNone(item.body)  # XML has no body
        self.assertIsNotNone(item.summary)
        self.assertEqual(item.url, "https://oui.doleta.gov/unemploy/claims.asp")

        # Check provenance
        self.assertEqual(item.provenance.connector, "dol_weekly_claims")
        self.assertEqual(item.provenance.source, "dol")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.provenance.fetched_at, fetched_at)

        # Check freshness
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, 7 * 24 * 60 * 60)

    def test_normalize_includes_metadata_with_fuente(self) -> None:
        """Normalizer should include metadata with fuente field (AC#1)."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            )
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        metadata = items[0].metadata

        # Check metadata fields (AC#1: semana, valor, revision si existe, fuente)
        self.assertEqual(metadata["series_type"], "initial")
        self.assertEqual(metadata["week_ending"], "2025-06-07")  # semana
        self.assertEqual(metadata["value"], 233000)  # valor
        self.assertEqual(metadata["prior_week_revised"], 229000)  # revision
        self.assertEqual(metadata["fuente"], "DOL/ETA")  # fuente
        self.assertTrue(metadata["seasonally_adjusted"])

    def test_normalize_handles_missing_revision(self) -> None:
        """Normalizer should handle None for missing prior week revision."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="continued",
                week_ending="2025-06-07",
                value="1843000",
                prior_week_revised=None,
                seasonally_adjusted=True,
            )
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        metadata = items[0].metadata
        self.assertIsNone(metadata["prior_week_revised"])

    def test_normalize_generates_unique_external_ids(self) -> None:
        """Normalizer should generate unique external_ids for each observation."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            ),
            ParsedDolWeeklyClaimsObservation(
                series_type="continued",
                week_ending="2025-06-07",
                value="1843000",
                prior_week_revised="1835000",
                seasonally_adjusted=True,
            ),
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        external_ids = [item.external_id for item in items]
        self.assertEqual(len(set(external_ids)), len(external_ids))
        self.assertIn("dol_weekly_claims_initial_2025-06-07", external_ids)
        self.assertIn("dol_weekly_claims_continued_2025-06-07", external_ids)

    def test_normalize_builds_meaningful_titles(self) -> None:
        """Normalizer should build meaningful titles for each series type."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            ),
            ParsedDolWeeklyClaimsObservation(
                series_type="continued",
                week_ending="2025-06-07",
                value="1843000",
                prior_week_revised="1835000",
                seasonally_adjusted=True,
            ),
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        titles = [item.title for item in items]
        initial_title = [t for t in titles if "Initial" in t][0]
        continued_title = [t for t in titles if "Continued" in t][0]

        self.assertIn("Initial Unemployment Claims", initial_title)
        self.assertIn("Week Ending 2025-06-07", initial_title)
        self.assertIn("Continued Unemployment Claims", continued_title)
        self.assertIn("Week Ending 2025-06-07", continued_title)

    def test_normalize_includes_summary_with_available_data(self) -> None:
        """Normalizer should include summary with available claims data."""
        from finance_news.connectors.dol_weekly_claims import ParsedDolWeeklyClaimsObservation

        observations = [
            ParsedDolWeeklyClaimsObservation(
                series_type="initial",
                week_ending="2025-06-07",
                value="233000",
                prior_week_revised="229000",
                seasonally_adjusted=True,
            )
        ]

        fetched_at = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_dol_weekly_claims_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://oui.doleta.gov/unemploy/claims.asp",
            cursor=None,
        )

        summary = items[0].summary
        self.assertIn("initial claims", summary)
        self.assertIn("2025-06-07", summary)
        self.assertIn("Value:", summary)
        self.assertIn("233,000", summary)
        self.assertIn("Prior week revised:", summary)
        self.assertIn("229,000", summary)
        self.assertIn("Seasonally Adjusted", summary)


class DolWeeklyClaimsConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Test the async connector implementation."""

    async def test_fetch_page_returns_all_observations(self) -> None:
        """Connector should fetch and return all weekly claims observations."""
        xml_text = (FIXTURES_DIR / "weekly_claims.xml").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={"Content-Type": "application/xml"},
                body=xml_text.encode("utf-8"),
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)
        result = await connector.fetch_page()

        # Should return both initial and continued claims (AC#1)
        self.assertEqual(len(result.items), 2)

        # No pagination
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Should have used correct URL
        self.assertEqual(
            transport.requests[0].url, "https://oui.doleta.gov/unemploy/claims.asp"
        )

    async def test_fetch_page_includes_both_initial_and_continued(self) -> None:
        """Connector should return both initial and continued claims with metadata (AC#1)."""
        xml_text = (FIXTURES_DIR / "weekly_claims.xml").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={"Content-Type": "application/xml"},
                body=xml_text.encode("utf-8"),
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)
        result = await connector.fetch_page()

        # Check AC#1: both series present
        self.assertEqual(len(result.items), 2)

        # Check initial claims metadata
        initial_item = [item for item in result.items if "initial" in item.external_id][0]
        self.assertEqual(initial_item.metadata["series_type"], "initial")
        self.assertEqual(initial_item.metadata["week_ending"], "2025-06-07")  # semana
        self.assertEqual(initial_item.metadata["value"], 233000)  # valor
        self.assertEqual(initial_item.metadata["prior_week_revised"], 229000)  # revision
        self.assertEqual(initial_item.metadata["fuente"], "DOL/ETA")  # fuente

        # Check continued claims metadata
        continued_item = [item for item in result.items if "continued" in item.external_id][0]
        self.assertEqual(continued_item.metadata["series_type"], "continued")
        self.assertEqual(continued_item.metadata["week_ending"], "2025-06-07")  # semana
        self.assertEqual(continued_item.metadata["value"], 1843000)  # valor
        self.assertEqual(continued_item.metadata["prior_week_revised"], 1835000)  # revision
        self.assertEqual(continued_item.metadata["fuente"], "DOL/ETA")  # fuente

    async def test_fetch_page_raises_recoverable_for_404(self) -> None:
        """Connector should raise RecoverableConnectorError for 404."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={},
                body=b"",
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("not found", str(cm.exception).lower())

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={},
                body=b"",
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_raises_recoverable_for_html_only(self) -> None:
        """Connector should raise RecoverableConnectorError when only HTML is available (AC#3 fallback)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=b"<html>Only HTML available</html>",
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        error_msg = str(cm.exception)
        self.assertIn("HTML format", error_msg)
        self.assertIn("XML/spreadsheet unavailable", error_msg)
        self.assertIn("retry later", error_msg)

    async def test_fetch_page_raises_value_for_unexpected_status(self) -> None:
        """Connector should raise ValueError for unexpected status codes."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # 3xx should raise ValueError
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={},
                body=b"",
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()
        self.assertIn("301", str(cm.exception))

    async def test_fetch_page_includes_transport_metadata(self) -> None:
        """Connector should include transport metadata in provenance."""
        xml_text = (FIXTURES_DIR / "weekly_claims.xml").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://oui.doleta.gov/unemploy/claims.asp",
                headers={"Content-Type": "application/xml; charset=utf-8"},
                body=xml_text.encode("utf-8"),
            )
        )

        connector = DolWeeklyClaimsConnector(transport=transport)
        result = await connector.fetch_page()

        # Check that items have transport metadata
        self.assertEqual(len(result.items), 2)
        transport_metadata = result.items[0].provenance.transport_metadata
        self.assertEqual(transport_metadata["status_code"], 200)
        self.assertEqual(transport_metadata["content_type"], "application/xml; charset=utf-8")
        self.assertEqual(transport_metadata["observation_count"], 2)

    def test_fallback_behavior_is_documented(self) -> None:
        """Fallback behavior for HTML/PDF-only weeks should be documented (AC#3)."""
        # Test that the module-level constant exists and documents the fallback
        self.assertIsNotNone(FALLBACK_BEHAVIOR_DOCUMENTED)
        self.assertIn("HTML/PDF", FALLBACK_BEHAVIOR_DOCUMENTED)
        self.assertIn("retry", FALLBACK_BEHAVIOR_DOCUMENTED.lower())

        # Test that the connector docstring documents the fallback
        docstring = DolWeeklyClaimsConnector.__doc__
        self.assertIsNotNone(docstring)
        self.assertIn("fallback", docstring.lower())
        self.assertIn("html", docstring.lower())
        self.assertIn("pdf", docstring.lower())
        self.assertIn("retry", docstring.lower())

    def test_connector_name_and_registry_name(self) -> None:
        """Connector should use correct module, class, and registry names."""
        # Test module-level constants
        from finance_news.connectors.dol_weekly_claims import (
            CONNECTOR_NAME,
            SOURCE_NAME,
        )

        self.assertEqual(CONNECTOR_NAME, "dol_weekly_claims")
        self.assertEqual(SOURCE_NAME, "dol")

        # Test connector class attributes
        self.assertEqual(DolWeeklyClaimsConnector.name, "dol_weekly_claims")
        self.assertEqual(DolWeeklyClaimsConnector.source, "dol")


if __name__ == "__main__":
    unittest.main()