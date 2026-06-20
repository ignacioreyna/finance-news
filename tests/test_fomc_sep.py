from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fomc_sep import (
    FomcSepConnector,
    DOTS_LIMITATION,
    normalize_sep_projections,
    parse_sep_csv,
    ParsedSepProjection,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fomc_sep"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class SepParserTests(unittest.TestCase):
    """Test pure parser functions for SEP CSV."""

    def test_parse_sep_csv_extracts_all_projections(self) -> None:
        """Parser should extract all valid projections from the CSV fixture."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        # Should have 5 variables x 4 horizons = 20 projections
        self.assertEqual(len(projections), 20)

    def test_parse_sep_csv_extracts_key_variables(self) -> None:
        """Parser should extract the 5 key variables."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        # Check that all 5 key variables are present
        variables = {proj.variable for proj in projections}
        expected_variables = {
            "GDP Growth",
            "Unemployment Rate",
            "PCE Inflation",
            "Core PCE Inflation",
            "Federal Funds Rate",
        }
        self.assertEqual(variables, expected_variables)

    def test_parse_sep_csv_extracts_all_horizons(self) -> None:
        """Parser should extract projections for all 4 horizons."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        # Check that all 4 horizons are present
        horizons = {proj.horizon for proj in projections}
        expected_horizons = {
            "Current Year",
            "Year +1",
            "Year +2",
            "Longer Run",
        }
        self.assertEqual(horizons, expected_horizons)

    def test_parse_sep_csv_handles_numeric_values(self) -> None:
        """Parser should correctly parse numeric values."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        # Check GDP Growth values
        gdp_projections = [proj for proj in projections if proj.variable == "GDP Growth"]
        self.assertEqual(len(gdp_projections), 4)  # 4 horizons
        gdp_values = {proj.horizon: proj.value for proj in gdp_projections}
        self.assertEqual(gdp_values["Current Year"], 2.1)
        self.assertEqual(gdp_values["Year +1"], 1.9)
        self.assertEqual(gdp_values["Year +2"], 1.8)
        self.assertEqual(gdp_values["Longer Run"], 1.8)

        # Check Federal Funds Rate values
        fed_funds_projections = [proj for proj in projections if proj.variable == "Federal Funds Rate"]
        self.assertEqual(len(fed_funds_projections), 4)
        fed_funds_values = {proj.horizon: proj.value for proj in fed_funds_projections}
        self.assertEqual(fed_funds_values["Current Year"], 5.25)
        self.assertEqual(fed_funds_values["Year +1"], 4.00)
        self.assertEqual(fed_funds_values["Year +2"], 3.00)
        self.assertEqual(fed_funds_values["Longer Run"], 2.50)

    def test_parse_sep_csv_uses_frozen_dataclass(self) -> None:
        """ParsedSepProjection should be a frozen dataclass."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        self.assertGreater(len(projections), 0)
        proj = projections[0]

        # Should have all expected fields
        self.assertIsInstance(proj, ParsedSepProjection)
        self.assertIsInstance(proj.variable, str)
        self.assertIsInstance(proj.horizon, str)
        self.assertIsInstance(proj.value, float)

        # Should be frozen (immutable)
        with self.assertRaises(Exception):  # frozen dataclasses raise on attribute assignment
            proj.variable = "modified"

    def test_parse_sep_csv_supports_serialization(self) -> None:
        """ParsedSepProjection should support to_dict/from_dict."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        proj = projections[0]
        proj_dict = proj.to_dict()

        # Check dict structure
        self.assertIn("variable", proj_dict)
        self.assertIn("horizon", proj_dict)
        self.assertIn("value", proj_dict)
        self.assertEqual(proj_dict["variable"], proj.variable)
        self.assertEqual(proj_dict["horizon"], proj.horizon)
        self.assertEqual(proj_dict["value"], proj.value)

        # Check round-trip
        restored = ParsedSepProjection.from_dict(proj_dict)
        self.assertEqual(restored.variable, proj.variable)
        self.assertEqual(restored.horizon, proj.horizon)
        self.assertEqual(restored.value, proj.value)

    def test_parse_sep_csv_raises_on_empty_file(self) -> None:
        """Parser should raise ValueError for empty CSV."""
        with self.assertRaises(ValueError) as cm:
            parse_sep_csv("")
        self.assertIn("Empty CSV", str(cm.exception))

    def test_parse_sep_csv_raises_on_missing_required_column(self) -> None:
        """Parser should raise ValueError for missing required columns."""
        invalid_csv = "Invalid,Header,Format\nTest,Data,Value"
        with self.assertRaises(ValueError) as cm:
            parse_sep_csv(invalid_csv)
        self.assertIn("expected", str(cm.exception).lower())

    def test_parse_sep_csv_raises_on_invalid_row_length(self) -> None:
        """Parser should raise ValueError for rows with wrong field count."""
        invalid_csv = "Variable,Current Year,Year +1,Year +2,Longer Run\nOnly,Three,Fields"
        with self.assertRaises(ValueError) as cm:
            parse_sep_csv(invalid_csv)
        self.assertIn("expected", str(cm.exception).lower())

    def test_parse_sep_csv_raises_on_invalid_numeric_value(self) -> None:
        """Parser should raise ValueError for non-numeric value fields."""
        invalid_csv = "Variable,Current Year,Year +1,Year +2,Longer Run\nGDP Growth,not_a_number,1.9,1.8,1.8"
        with self.assertRaises(ValueError) as cm:
            parse_sep_csv(invalid_csv)
        self.assertIn("invalid value", str(cm.exception).lower())


class SepNormalizationTests(unittest.TestCase):
    """Test normalization of parsed projections to SourceItem objects."""

    def test_normalize_creates_single_source_item(self) -> None:
        """Normalizer should create a single SourceItem for all projections."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        # Should be a single item
        self.assertIsNotNone(item)
        self.assertEqual(item.source, "fed")

    def test_normalize_populates_required_fields(self) -> None:
        """Normalizer should populate all required SourceItem fields."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        # Check required fields
        self.assertIsNotNone(item.external_id)
        self.assertEqual(item.source, "fed")
        self.assertIsNotNone(item.published_at)
        self.assertIsNotNone(item.title)
        self.assertIsNone(item.body)  # CSV has no body
        self.assertIsNotNone(item.summary)
        self.assertEqual(item.url, "https://example.com/fomcprojtabl20250319.htm")

        # Check provenance
        self.assertEqual(item.provenance.connector, "fomc_sep")
        self.assertEqual(item.provenance.source, "fed")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.provenance.fetched_at, fetched_at)

        # Check freshness
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, 90 * 24 * 60 * 60)  # 90 days

    def test_normalize_includes_metadata_with_projections(self) -> None:
        """Normalizer should include SEP-specific metadata with projections."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        metadata = item.metadata

        # Check metadata fields
        self.assertEqual(metadata["content_type"], "fomc_sep_projections")
        self.assertEqual(metadata["meeting_date"], "2025-03-19")
        self.assertEqual(metadata["variable_count"], 5)
        self.assertEqual(metadata["horizon_count"], 4)
        self.assertTrue(metadata["has_sep"])  # Flag indicating SEP is present

        # Check projections list
        self.assertIn("projections", metadata)
        self.assertIsInstance(metadata["projections"], list)
        self.assertEqual(len(metadata["projections"]), 20)  # 5 variables x 4 horizons

        # Check structure of first projection in metadata
        first_proj = metadata["projections"][0]
        self.assertIn("variable", first_proj)
        self.assertIn("horizon", first_proj)
        self.assertIn("value", first_proj)

    def test_normalize_includes_dots_limitation_in_metadata(self) -> None:
        """Normalizer should include dots limitation documentation in metadata."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        metadata = item.metadata
        self.assertIn("dots_limitation", metadata)
        dots_limitation = metadata["dots_limitation"]
        self.assertIn("median projections", dots_limitation.lower())
        self.assertIn("dot plot", dots_limitation.lower())
        self.assertIn("manual parsing", dots_limitation.lower())

    def test_normalize_includes_dots_limitation_in_summary(self) -> None:
        """Normalizer should include dots limitation in summary."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        summary = item.summary
        self.assertIn("median projections", summary.lower())
        self.assertIn("dot plot", summary.lower())

    def test_normalize_builds_meaningful_title(self) -> None:
        """Normalizer should build meaningful title."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        self.assertIn("FOMC SEP Projections", item.title)
        self.assertIn("2025-03-19", item.title)

    def test_normalize_generates_unique_external_id(self) -> None:
        """Normalizer should generate unique external_id based on meeting date."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        self.assertEqual(item.external_id, "fomc_sep_2025-03-19")

    def test_normalize_parses_meeting_date_correctly(self) -> None:
        """Normalizer should correctly parse meeting date."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date="2025-03-19",
            fetched_at=fetched_at,
            fetch_url="https://example.com/fomcprojtabl20250319.htm",
            cursor=None,
        )

        self.assertIsNotNone(item.published_at)
        self.assertEqual(item.published_at.year, 2025)
        self.assertEqual(item.published_at.month, 3)
        self.assertEqual(item.published_at.day, 19)
        self.assertEqual(item.published_at.tzinfo, timezone.utc)

    def test_normalize_raises_on_invalid_date_format(self) -> None:
        """Normalizer should raise ValueError for invalid date format."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")
        projections = parse_sep_csv(csv_text)

        fetched_at = datetime(2025, 3, 19, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            normalize_sep_projections(
                projections=projections,
                meeting_date="invalid-date",
                fetched_at=fetched_at,
                fetch_url="https://example.com/fomcprojtabl20250319.htm",
                cursor=None,
            )


class DotsLimitationTests(unittest.TestCase):
    """Test dots limitation documentation."""

    def test_dots_limitation_constant_exists(self) -> None:
        """Module should have constant documenting dots limitation."""
        self.assertIsInstance(DOTS_LIMITATION, str)
        self.assertGreater(len(DOTS_LIMITATION), 50)

    def test_dots_limitation_content(self) -> None:
        """Dots limitation documentation should explain what's not extracted."""
        self.assertIn("median", DOTS_LIMITATION.lower())
        self.assertIn("dot plot", DOTS_LIMITATION.lower())
        self.assertIn("dispersion", DOTS_LIMITATION.lower())
        self.assertIn("manual parsing", DOTS_LIMITATION.lower())
        self.assertIn("pdf", DOTS_LIMITATION.lower())


class SepConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Test the async connector implementation."""

    async def test_fetch_page_returns_projections(self) -> None:
        """Connector should fetch and return SEP projections."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"
        result = await connector.fetch_page(cursor=cursor)

        # Should return one item with all projections
        self.assertEqual(len(result.items), 1)

        # No pagination
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Should have used correct URL
        self.assertEqual(
            transport.requests[0].url,
            "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
        )

        # Check the item
        item = result.items[0]
        self.assertEqual(item.external_id, "fomc_sep_2025-03-19")
        self.assertEqual(item.source, "fed")
        self.assertEqual(item.provenance.connector, "fomc_sep")

        # Check metadata has projections
        self.assertIn("projections", item.metadata)
        self.assertEqual(len(item.metadata["projections"]), 20)  # 5 variables x 4 horizons

    async def test_fetch_page_extracts_meeting_date_from_url(self) -> None:
        """Connector should extract meeting date from SEP URL."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"
        result = await connector.fetch_page(cursor=cursor)

        item = result.items[0]
        self.assertEqual(item.metadata["meeting_date"], "2025-03-19")
        self.assertEqual(item.external_id, "fomc_sep_2025-03-19")

    async def test_fetch_page_handles_encoding_correctly(self) -> None:
        """Connector should handle UTF-8 encoding."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"
        result = await connector.fetch_page(cursor=cursor)

        # Should successfully parse without encoding errors
        self.assertEqual(len(result.items), 1)
        self.assertEqual(len(result.items[0].metadata["projections"]), 20)

    async def test_fetch_page_raises_recoverable_for_404(self) -> None:
        """Connector should raise RecoverableConnectorError for 404."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={},
                body=b"",
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor=cursor)
        self.assertIn("not found", str(cm.exception).lower())

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={},
                body=b"",
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page(cursor=cursor)
        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_raises_value_for_unexpected_status(self) -> None:
        """Connector should raise ValueError for unexpected status codes."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # 3xx should raise ValueError, not RecoverableConnectorError
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={},
                body=b"",
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor=cursor)
        self.assertIn("301", str(cm.exception))

    async def test_fetch_page_raises_value_without_cursor(self) -> None:
        """Connector should raise ValueError when cursor is not provided."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={},
                body=b"",
            )
        )

        connector = FomcSepConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()
        self.assertIn("cursor", str(cm.exception).lower())

    async def test_fetch_page_includes_transport_metadata(self) -> None:
        """Connector should include transport metadata in provenance."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={"Content-Type": "text/csv; charset=utf-8"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"
        result = await connector.fetch_page(cursor=cursor)

        # Check that item has transport metadata
        self.assertEqual(len(result.items), 1)
        transport_metadata = result.items[0].provenance.transport_metadata
        self.assertEqual(transport_metadata["status_code"], 200)
        self.assertEqual(transport_metadata["content_type"], "text/csv; charset=utf-8")
        self.assertEqual(transport_metadata["projection_count"], 20)

    async def test_fetch_page_includes_has_sep_flag(self) -> None:
        """Connector should include has_sep flag in metadata."""
        csv_text = (FIXTURES_DIR / "sep_medians_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FomcSepConnector(transport=transport)
        cursor = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm"
        result = await connector.fetch_page(cursor=cursor)

        metadata = result.items[0].metadata
        self.assertTrue(metadata["has_sep"])

    async def test_connector_name_and_source(self) -> None:
        """Connector should have correct name and source."""
        connector = FomcSepConnector(
            transport=_FakeTransport(
                HttpResponse(status_code=200, url="", headers={}, body=b"")
            )
        )

        self.assertEqual(connector.name, "fomc_sep")
        self.assertEqual(connector.source, "fed")


if __name__ == "__main__":
    unittest.main()