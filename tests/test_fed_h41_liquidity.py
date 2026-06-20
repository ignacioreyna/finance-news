from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fed_h41_liquidity import (
    FedH41LiquidityConnector,
    FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS,
    _parse_date,
    normalize_h41_observations,
    parse_h41_csv,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fed_h41_liquidity"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FedH41ParserTests(unittest.TestCase):
    """Test pure parser functions for Fed H.4.1 CSV."""

    def test_parse_h41_csv_extracts_all_observations(self) -> None:
        """Parser should extract all valid observations from the CSV fixture."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Should have multiple observations (5 series x 3 weeks = 15 rows)
        self.assertEqual(len(observations), 15)

        # Check first observation (Total Assets for 2026-06-10)
        first = observations[0]
        self.assertEqual(first.series_name, "Total Assets")
        self.assertIn("Federal Reserve total assets", first.series_description)
        self.assertEqual(first.unit, "Millions of Dollars")
        self.assertEqual(first.date, "2026-06-10")
        self.assertEqual(first.value, 8541234.0)

    def test_parse_h41_csv_extracts_key_series(self) -> None:
        """Parser should extract the 5 key series for liquidity analysis."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Check that all 5 key series are present
        series_names = {obs.series_name for obs in observations}
        expected_series = {
            "Total Assets",
            "Securities Held Outright",
            "Overnight Reverse Repurchase Agreements",
            "Treasury General Account",
            "Reserve Balances",
        }
        self.assertEqual(series_names, expected_series)

    def test_parse_h41_csv_handles_multiple_dates(self) -> None:
        """Parser should extract observations for multiple weeks."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        dates = {obs.date for obs in observations}
        expected_dates = {"2026-06-10", "2026-06-03", "2026-05-27"}
        self.assertEqual(dates, expected_dates)

    def test_parse_h41_csv_handles_numeric_values(self) -> None:
        """Parser should correctly parse large numeric values."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Check a specific large value (Total Assets)
        total_assets_obs = [obs for obs in observations if obs.series_name == "Total Assets"][0]
        self.assertEqual(total_assets_obs.value, 8541234.0)
        self.assertIsInstance(total_assets_obs.value, float)

        # Check a smaller value (ON RRP)
        on_rrp_obs = [obs for obs in observations if obs.series_name == "Overnight Reverse Repurchase Agreements"][0]
        self.assertEqual(on_rrp_obs.value, 876543.0)
        self.assertIsInstance(on_rrp_obs.value, float)

    def test_parse_h41_csv_raises_on_empty_file(self) -> None:
        """Parser should raise ValueError for empty CSV."""
        with self.assertRaises(ValueError) as cm:
            parse_h41_csv("")
        self.assertIn("Empty CSV", str(cm.exception))

    def test_parse_h41_csv_raises_on_missing_required_column(self) -> None:
        """Parser should raise ValueError for missing required columns."""
        invalid_csv = "Invalid,Header,Format\nTest,Data,Value"
        with self.assertRaises(ValueError) as cm:
            parse_h41_csv(invalid_csv)
        self.assertIn("Missing required column", str(cm.exception))

    def test_parse_h41_csv_raises_on_invalid_row_length(self) -> None:
        """Parser should raise ValueError for rows with wrong field count."""
        invalid_csv = "Series Name,Series Description,Unit,Multipliers,Date,Value\nOnly,Three,Fields"
        with self.assertRaises(ValueError) as cm:
            parse_h41_csv(invalid_csv)
        self.assertIn("expected at least", str(cm.exception))

    def test_parse_h41_csv_raises_on_invalid_numeric_value(self) -> None:
        """Parser should raise ValueError for non-numeric value fields."""
        invalid_csv = "Series Name,Series Description,Unit,Multipliers,Date,Value\nTotal Assets,Fed total assets,Millions of Dollars,,2026-06-10,not_a_number"
        with self.assertRaises(ValueError) as cm:
            parse_h41_csv(invalid_csv)
        self.assertIn("invalid value", str(cm.exception).lower())


class FedH41HelperTests(unittest.TestCase):
    """Test helper functions for parsing H.4.1 values."""

    def test_parse_date_valid_formats(self) -> None:
        """Date parser should handle valid YYYY-MM-DD formats."""
        self.assertEqual(
            _parse_date("2026-06-10"), datetime(2026, 6, 10, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_date("2026-06-03"), datetime(2026, 6, 3, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_date("2026-05-27"), datetime(2026, 5, 27, tzinfo=timezone.utc)
        )

    def test_parse_date_invalid_formats(self) -> None:
        """Date parser should reject invalid formats."""
        with self.assertRaises(ValueError):
            _parse_date("2026/06/10")  # Wrong separator
        with self.assertRaises(ValueError):
            _parse_date("2026-06-10-extra")  # Too many parts
        with self.assertRaises(ValueError):
            _parse_date("abcd-06-10")  # Non-numeric year
        with self.assertRaises(ValueError):
            _parse_date("2026-13-01")  # Invalid month


class FedH41NormalizationTests(unittest.TestCase):
    """Test normalization of parsed observations to SourceItem objects."""

    def test_normalize_creates_source_items_for_all_observations(self) -> None:
        """Normalizer should create a SourceItem for each observation."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        # Should have one item per observation
        self.assertEqual(len(items), len(observations))

    def test_normalize_populates_required_fields(self) -> None:
        """Normalizer should populate all required SourceItem fields."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Test with Total Assets observation
        total_assets_obs = [obs for obs in observations if obs.series_name == "Total Assets"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=[total_assets_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        self.assertEqual(len(items), 1)
        item = items[0]

        # Check required fields
        self.assertIsNotNone(item.external_id)
        self.assertEqual(item.source, "federal_reserve_h41")
        self.assertIsNotNone(item.published_at)
        self.assertIsNotNone(item.title)
        self.assertIsNone(item.body)  # CSV has no body
        self.assertIsNotNone(item.summary)
        self.assertEqual(item.url, "https://example.com/h41.csv")

        # Check provenance
        self.assertEqual(item.provenance.connector, "fed_h41_liquidity")
        self.assertEqual(item.provenance.source, "federal_reserve_h41")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.provenance.fetched_at, fetched_at)

        # Check freshness
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, 7 * 24 * 60 * 60)  # 7 days

    def test_normalize_includes_metadata(self) -> None:
        """Normalizer should include H.4.1-specific metadata."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Test with ON RRP observation
        on_rrp_obs = [obs for obs in observations if obs.series_name == "Overnight Reverse Repurchase Agreements"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=[on_rrp_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        self.assertEqual(len(items), 1)
        metadata = items[0].metadata

        # Check metadata fields
        self.assertEqual(metadata["content_type"], "h41_weekly_observation")
        self.assertEqual(metadata["series_name"], "Overnight Reverse Repurchase Agreements")
        self.assertIn("ON RRP", metadata["series_description"])
        self.assertEqual(metadata["unit"], "Millions of Dollars")
        self.assertEqual(metadata["date"], "2026-06-10")
        self.assertEqual(metadata["value_millions"], 876543.0)
        self.assertEqual(metadata["currency"], "USD")
        self.assertEqual(metadata["frequency"], "weekly")

    def test_normalize_includes_frequency_difference_documentation(self) -> None:
        """Normalizer should include frequency difference vs FiscalData DTS in metadata."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=observations[:1],  # Just first observation
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        metadata = items[0].metadata
        self.assertIn("frequency_difference_vs_fiscaldata_dts", metadata)
        freq_diff = metadata["frequency_difference_vs_fiscaldata_dts"]
        self.assertIn("weekly", freq_diff.lower())
        self.assertIn("daily", freq_diff.lower())
        self.assertIn("fiscaldata dts", freq_diff.lower())

    def test_normalize_generates_unique_external_ids(self) -> None:
        """Normalizer should generate unique external_ids for each observation."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        external_ids = [item.external_id for item in items]
        # All external IDs should be unique
        self.assertEqual(len(external_ids), len(set(external_ids)))

    def test_normalize_builds_meaningful_titles(self) -> None:
        """Normalizer should build meaningful titles for each observation."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        # Check Total Assets title
        total_assets_items = [item for item in items if item.external_id.startswith("h41_total_assets")]
        self.assertGreater(len(total_assets_items), 0)
        self.assertIn("Total Assets", total_assets_items[0].title)
        self.assertIn("2026-06-10", total_assets_items[0].title)

    def test_normalize_includes_summary_with_available_data(self) -> None:
        """Normalizer should include summary with available H.4.1 data."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")
        observations = parse_h41_csv(csv_text)

        # Use a Reserve Balances observation for 2026-06-10
        reserves_obs = [obs for obs in observations if obs.series_name == "Reserve Balances" and obs.date == "2026-06-10"][0]

        fetched_at = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        items = normalize_h41_observations(
            observations=[reserves_obs],
            fetched_at=fetched_at,
            fetch_url="https://example.com/h41.csv",
            cursor=None,
        )

        summary = items[0].summary
        self.assertIn("Federal Reserve H.4.1", summary)
        self.assertIn("Reserve Balances", summary)
        self.assertIn("3,321,456", summary)  # Formatted value
        self.assertIn("2026-06-10", summary)
        self.assertIn("Millions of Dollars", summary)


class FedH41FrequencyDifferenceTests(unittest.TestCase):
    """Test frequency difference documentation vs FiscalData DTS."""

    def test_frequency_difference_constant_exists(self) -> None:
        """Module should have constant documenting frequency difference."""
        self.assertIsInstance(FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS, str)
        self.assertGreater(len(FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS), 50)

    def test_frequency_difference_documentation_content(self) -> None:
        """Frequency difference documentation should mention weekly vs daily."""
        self.assertIn("weekly", FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS.lower())
        self.assertIn("daily", FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS.lower())
        self.assertIn("h.4.1", FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS.lower())
        self.assertIn("fiscaldata dts", FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS.lower())
        self.assertIn("wednesday", FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS.lower())


class FedH41ConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Test the async connector implementation."""

    async def test_fetch_page_returns_all_observations(self) -> None:
        """Connector should fetch and return all H.4.1 observations."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)
        result = await connector.fetch_page()

        # Should return all observations
        self.assertEqual(len(result.items), 15)  # 5 series x 3 weeks

        # No pagination
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Should have used correct URL
        self.assertEqual(
            transport.requests[0].url,
            "https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
        )

    async def test_fetch_page_handles_encoding_correctly(self) -> None:
        """Connector should handle UTF-8 encoding."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={"Content-Type": "text/csv"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)
        result = await connector.fetch_page()

        # Should successfully parse without encoding errors
        self.assertEqual(len(result.items), 15)

    async def test_fetch_page_raises_recoverable_for_404(self) -> None:
        """Connector should raise RecoverableConnectorError for 404."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={},
                body=b"",
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("not found", str(cm.exception).lower())

    async def test_fetch_page_raises_recoverable_for_5xx(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={},
                body=b"",
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()
        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_raises_value_for_unexpected_status(self) -> None:
        """Connector should raise ValueError for unexpected status codes."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,  # 3xx should raise ValueError, not RecoverableConnectorError
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={},
                body=b"",
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()
        self.assertIn("301", str(cm.exception))

    async def test_fetch_page_includes_transport_metadata(self) -> None:
        """Connector should include transport metadata in provenance."""
        csv_text = (FIXTURES_DIR / "h41_sample.csv").read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41",
                headers={"Content-Type": "text/csv; charset=utf-8"},
                body=csv_text.encode("utf-8"),
            )
        )

        connector = FedH41LiquidityConnector(transport=transport)
        result = await connector.fetch_page()

        # Check that items have transport metadata
        self.assertEqual(len(result.items), 15)
        transport_metadata = result.items[0].provenance.transport_metadata
        self.assertEqual(transport_metadata["status_code"], 200)
        self.assertEqual(transport_metadata["content_type"], "text/csv; charset=utf-8")
        self.assertEqual(transport_metadata["observation_count"], 15)

    async def test_fetch_page_documentation_frequency_difference(self) -> None:
        """Connector docstring should document frequency difference vs FiscalData DTS."""
        connector = FedH41LiquidityConnector(
            transport=_FakeTransport(HttpResponse(status_code=200, url="", headers={}, body=b""))
        )

        docstring = FedH41LiquidityConnector.__doc__
        self.assertIsNotNone(docstring)
        self.assertIn("weekly", docstring.lower())
        self.assertIn("daily", docstring.lower())
        self.assertIn("fiscaldata dts", docstring.lower())
        # Should mention the Wednesday alignment
        self.assertIn("wednesday", docstring.lower())


if __name__ == "__main__":
    unittest.main()