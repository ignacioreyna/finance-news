"""Tests for EIA WPSR connector."""

from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, "src")

from finance_news.connectors._http import HttpRequest, HttpResponse
from finance_news.connectors.eia_wpsr import (
    EiaWpsrConnector,
    ParsedEiaWpsrObservation,
    compute_weekly_variation,
    normalize_eia_wpsr_observations,
    parse_eia_wpsr_csv,
)
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.testing.fixtures import load_fixture_text


@dataclass(frozen=True)
class FakeTransport:
    """Fake HTTP transport for offline testing."""

    status_code: int = 200
    url: str = "https://example.com/test"
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)

    async def send(self, request: HttpRequest) -> HttpResponse:
        """Return a fake response."""
        return HttpResponse(
            status_code=self.status_code,
            url=self.url,
            headers=self.headers,
            body=self.body,
        )


class TestParseEiaWpsrCsv(unittest.TestCase):
    """Test CSV parsing for EIA WPSR data."""

    def test_parse_valid_csv(self) -> None:
        """Test parsing a valid CSV file."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)

        # Should have 5 weeks * 7 series = 35 observations
        self.assertEqual(len(observations), 35)

        # Check first observation (crude_stocks_mmbbl for 2024-05-31)
        first_obs = observations[0]
        self.assertEqual(first_obs.week_ending, "2024-05-31")
        self.assertEqual(first_obs.release_date, "2024-06-05")
        self.assertEqual(first_obs.series_name, "crude_stocks_mmbbl")
        self.assertEqual(first_obs.value, 445.2)
        self.assertEqual(first_obs.unit, "million barrels")

        # Check a different series (production_thousand_bpd for 2024-05-24)
        production_obs = [o for o in observations if o.series_name == "production_thousand_bpd" and o.week_ending == "2024-05-24"][0]
        self.assertEqual(production_obs.value, 13020.0)
        self.assertEqual(production_obs.unit, "thousand barrels per day")

    def test_parse_empty_csv(self) -> None:
        """Test parsing an empty CSV file raises ValueError."""
        with self.assertRaises(ValueError) as context:
            parse_eia_wpsr_csv("")
        self.assertIn("Empty CSV file", str(context.exception))

    def test_parse_csv_missing_required_column(self) -> None:
        """Test parsing CSV with missing required column raises ValueError."""
        bad_csv = "week_ending,crude_stocks_mmbbl\n2024-05-31,445.2"
        with self.assertRaises(ValueError) as context:
            parse_eia_wpsr_csv(bad_csv)
        self.assertIn("Missing required column", str(context.exception))

    def test_parse_csv_invalid_value(self) -> None:
        """Test parsing CSV with invalid numeric value raises ValueError."""
        bad_csv = "week_ending,release_date,crude_stocks_mmbbl\n2024-05-31,2024-06-05,not_a_number"
        with self.assertRaises(ValueError) as context:
            parse_eia_wpsr_csv(bad_csv)
        self.assertIn("invalid value", str(context.exception))

    def test_parse_csv_empty_values(self) -> None:
        """Test parsing CSV with empty values defaults to 0.0."""
        csv_with_empty = "week_ending,release_date,crude_stocks_mmbbl\n2024-05-31,2024-06-05,"
        observations = parse_eia_wpsr_csv(csv_with_empty)
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].value, 0.0)


class TestComputeWeeklyVariation(unittest.TestCase):
    """Test weekly variation computation."""

    def test_compute_variation_for_key_series(self) -> None:
        """Test computing weekly variation for the 5 key series."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        # Should have variations for 5 key series * 5 weeks = 25 entries
        self.assertEqual(len(variations), 25)

        # Check that we have all key series
        series_in_variations = set(key.rsplit("_", 1)[0] for key in variations.keys())
        expected_series = {
            "crude_stocks_mmbbl",
            "cushing_stocks_mmbbl",
            "gasoline_stocks_mmbbl",
            "distillate_stocks_mmbbl",
            "production_thousand_bpd",
        }
        self.assertEqual(series_in_variations, expected_series)

    def test_variation_first_week_has_none_delta(self) -> None:
        """Test that the earliest week has delta=None (no prior week)."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        # Find the earliest week for crude_stocks_mmbbl
        crude_keys = sorted([k for k in variations.keys() if k.startswith("crude_stocks_mmbbl")])
        earliest_key = crude_keys[0]
        self.assertIsNone(variations[earliest_key]["delta"])

    def test_variation_calculation_correctness(self) -> None:
        """Test that variation calculation is mathematically correct."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        # Check crude stocks: 2024-05-31 value is 445.2, 2024-05-24 value is 438.7
        # Delta should be 445.2 - 438.7 = 6.5
        crude_key = "crude_stocks_mmbbl_2024-05-31"
        self.assertIsNotNone(variations[crude_key]["delta"])
        self.assertAlmostEqual(variations[crude_key]["delta"], 6.5, places=1)

        # Check Cushing: 2024-05-24 value is 32.1, 2024-05-17 value is 30.5
        # Delta should be 32.1 - 30.5 = 1.6
        cushing_key = "cushing_stocks_mmbbl_2024-05-24"
        self.assertIsNotNone(variations[cushing_key]["delta"])
        self.assertAlmostEqual(variations[cushing_key]["delta"], 1.6, places=1)

        # Check production: 2024-05-24 value is 13020, 2024-05-17 value is 12980
        # Delta should be 13020 - 12980 = 40
        production_key = "production_thousand_bpd_2024-05-24"
        self.assertIsNotNone(variations[production_key]["delta"])
        self.assertAlmostEqual(variations[production_key]["delta"], 40.0, places=1)

    def test_variation_negative_changes(self) -> None:
        """Test that negative weekly changes are computed correctly."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        # Check distillates: 2024-05-24 value is 115.8, 2024-05-17 value is 118.2
        # Delta should be 115.8 - 118.2 = -2.4
        distillate_key = "distillate_stocks_mmbbl_2024-05-24"
        self.assertIsNotNone(variations[distillate_key]["delta"])
        self.assertAlmostEqual(variations[distillate_key]["delta"], -2.4, places=1)


class TestNormalizeEiaWpsrObservations(unittest.TestCase):
    """Test normalization of parsed observations to SourceItems."""

    def test_normalize_observations_to_source_items(self) -> None:
        """Test normalizing observations creates valid SourceItems."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        fetched_at = datetime(2024, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_eia_wpsr_observations(
            observations=observations,
            variations=variations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Should have one SourceItem per observation
        self.assertEqual(len(items), 35)

        # Check first item
        first_item = items[0]
        self.assertEqual(
            first_item.external_id, "eia_wpsr_crude_stocks_mmbbl_2024-05-31"
        )
        self.assertEqual(first_item.source, "eia_wpsr")
        self.assertEqual(first_item.provenance.connector, "eia_wpsr")
        self.assertEqual(first_item.provenance.parser_version, "0.1.0")

        # Check metadata
        self.assertEqual(first_item.metadata["week_ending"], "2024-05-31")
        self.assertEqual(first_item.metadata["release_date"], "2024-06-05")
        self.assertEqual(first_item.metadata["series_name"], "crude_stocks_mmbbl")
        self.assertEqual(first_item.metadata["value"], 445.2)
        self.assertEqual(first_item.metadata["unit"], "million barrels")
        self.assertEqual(first_item.metadata["frequency"], "weekly")

        # Check that weekly_variation is included for key series
        self.assertIn("weekly_variation", first_item.metadata)
        self.assertIsNotNone(first_item.metadata["weekly_variation"])

    def test_normalize_item_titles_include_variation(self) -> None:
        """Test that item titles include weekly variation when available."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        fetched_at = datetime(2024, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_eia_wpsr_observations(
            observations=observations,
            variations=variations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Find crude stocks item for 2024-05-31 (delta should be +6.5)
        crude_item = next(
            (i for i in items if i.external_id == "eia_wpsr_crude_stocks_mmbbl_2024-05-31")
        )
        self.assertIn("(+6.5)", crude_item.title)

        # Find crude stocks item for 2024-05-24 (delta should be +3.6)
        crude_item_524 = next(
            (i for i in items if i.external_id == "eia_wpsr_crude_stocks_mmbbl_2024-05-24")
        )
        self.assertIn("(+3.6)", crude_item_524.title)

    def test_normalize_item_summaries_include_variation(self) -> None:
        """Test that item summaries include weekly variation when available."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        fetched_at = datetime(2024, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_eia_wpsr_observations(
            observations=observations,
            variations=variations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Check summary includes variation
        crude_item = next(
            (i for i in items if i.external_id == "eia_wpsr_crude_stocks_mmbbl_2024-05-31")
        )
        self.assertIn("Weekly change:", crude_item.summary)

    def test_normalize_uses_release_date_as_published_at(self) -> None:
        """Test that release_date is used as published_at, not week_ending."""
        csv_text = load_fixture_text("eia_wpsr", "weekly_data.csv")
        observations = parse_eia_wpsr_csv(csv_text)
        variations = compute_weekly_variation(observations)

        fetched_at = datetime(2024, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_eia_wpsr_observations(
            observations=observations,
            variations=variations,
            fetched_at=fetched_at,
            fetch_url="https://example.com/test.csv",
            cursor=None,
        )

        # Check that published_at is the release date (2024-06-05)
        crude_item = next(
            (i for i in items if i.external_id == "eia_wpsr_crude_stocks_mmbbl_2024-05-31")
        )
        expected_published_at = datetime(2024, 6, 5, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(crude_item.published_at, expected_published_at)


class TestEiaWpsrConnector(unittest.IsolatedAsyncioTestCase):
    """Test the EIA WPSR connector."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.csv_data = load_fixture_text("eia_wpsr", "weekly_data.csv")

    async def test_fetch_page_returns_observations(self) -> None:
        """Test that fetch_page returns observations from CSV."""
        transport = FakeTransport(
            status_code=200,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=self.csv_data.encode("utf-8"),
            headers={"Content-Type": "text/csv"},
        )
        connector = EiaWpsrConnector(transport=transport)

        result = await connector.fetch_page()

        # Should have 35 observations (5 weeks * 7 series)
        self.assertEqual(len(result.items), 35)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

    async def test_fetch_page_includes_weekly_variation(self) -> None:
        """Test that fetch_page includes weekly variation in metadata."""
        transport = FakeTransport(
            status_code=200,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=self.csv_data.encode("utf-8"),
            headers={"Content-Type": "text/csv"},
        )
        connector = EiaWpsrConnector(transport=transport)

        result = await connector.fetch_page()

        # Check that items have weekly_variation in metadata for key series
        crude_item = next(
            (i for i in result.items if i.external_id == "eia_wpsr_crude_stocks_mmbbl_2024-05-31")
        )
        self.assertIn("weekly_variation", crude_item.metadata)
        self.assertIsNotNone(crude_item.metadata["weekly_variation"])

    async def test_fetch_page_404_raises_recoverable_error(self) -> None:
        """Test that 404 status raises RecoverableConnectorError."""
        transport = FakeTransport(
            status_code=404,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=b"Not Found",
        )
        connector = EiaWpsrConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as context:
            await connector.fetch_page()
        self.assertIn("not found", str(context.exception).lower())

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        """Test that 5xx status raises RecoverableConnectorError."""
        transport = FakeTransport(
            status_code=503,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=b"Service Unavailable",
        )
        connector = EiaWpsrConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as context:
            await connector.fetch_page()
        self.assertIn("503", str(context.exception))

    async def test_fetch_page_400_raises_value_error(self) -> None:
        """Test that 400 status raises ValueError (not recoverable)."""
        transport = FakeTransport(
            status_code=400,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=b"Bad Request",
        )
        connector = EiaWpsrConnector(transport=transport)

        with self.assertRaises(ValueError) as context:
            await connector.fetch_page()
        self.assertIn("400", str(context.exception))

    async def test_fetch_page_invalid_csv_raises_value_error(self) -> None:
        """Test that invalid CSV raises ValueError."""
        transport = FakeTransport(
            status_code=200,
            url="https://www.eia.gov/petroleum/supply/weekly/csv_data.csv",
            body=b"not valid csv,,,",
            headers={"Content-Type": "text/csv"},
        )
        connector = EiaWpsrConnector(transport=transport)

        with self.assertRaises(ValueError) as context:
            await connector.fetch_page()
        self.assertIn("Failed to parse WPSR CSV", str(context.exception))

    def test_connector_name_and_source(self) -> None:
        """Test that connector has correct name and source."""
        connector = EiaWpsrConnector(transport=FakeTransport())
        self.assertEqual(connector.name, "eia_wpsr")
        self.assertEqual(connector.source, "eia_wpsr")

    def test_connector_retry_policy(self) -> None:
        """Test that connector has retry policy configured."""
        connector = EiaWpsrConnector(transport=FakeTransport())
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)

    def test_connector_rate_limit_policy(self) -> None:
        """Test that connector has rate limit policy configured."""
        connector = EiaWpsrConnector(transport=FakeTransport())
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)


if __name__ == "__main__":
    unittest.main()