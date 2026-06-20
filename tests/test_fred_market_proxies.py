from __future__ import annotations

import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fred_market_proxies import (
    DEFAULT_SERIES,
    FredMarketProxiesConnector,
    _parse_observation_date,
    _parse_value,
    normalize_fred_observations,
    parse_fred_csv,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fred_market_proxies"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FredCsvParserTests(unittest.TestCase):
    """Test pure parser functions for FRED CSV."""

    def test_parse_fred_csv_extracts_all_observations(self) -> None:
        """Parser should extract all valid observations from the CSV fixture."""
        csv_text = (FIXTURES_DIR / "DCOILWTICO.csv").read_text(encoding="utf-8")
        observations = parse_fred_csv(csv_text, "DCOILWTICO")

        # Should have 9 observations
        self.assertEqual(len(observations), 9)

        # Check first observation
        first = observations[0]
        self.assertEqual(first.series_id, "DCOILWTICO")
        self.assertEqual(first.observation_date, "2024-01-02")
        self.assertEqual(first.value, "72.50")

        # Check last observation
        last = observations[-1]
        self.assertEqual(last.observation_date, "2024-01-12")
        self.assertEqual(last.value, "72.40")

    def test_parse_fred_csv_handles_primary_series(self) -> None:
        """Parser should handle primary series like DFII10."""
        csv_text = (FIXTURES_DIR / "DFII10.csv").read_text(encoding="utf-8")
        observations = parse_fred_csv(csv_text, "DFII10")

        # Should have 9 observations
        self.assertEqual(len(observations), 9)

        # All should have DFII10 series_id
        for obs in observations:
            self.assertEqual(obs.series_id, "DFII10")

    def test_parse_fred_csv_handles_proxy_series(self) -> None:
        """Parser should handle proxy series like T10YIE."""
        csv_text = (FIXTURES_DIR / "T10YIE.csv").read_text(encoding="utf-8")
        observations = parse_fred_csv(csv_text, "T10YIE")

        # Should have 9 observations
        self.assertEqual(len(observations), 9)

        # All should have T10YIE series_id
        for obs in observations:
            self.assertEqual(obs.series_id, "T10YIE")

    def test_parse_fred_csv_raises_on_empty_file(self) -> None:
        """Parser should raise ValueError for empty CSV."""
        with self.assertRaises(ValueError) as cm:
            parse_fred_csv("", "TEST")
        self.assertIn("Empty CSV", str(cm.exception))

    def test_parse_fred_csv_raises_on_invalid_header(self) -> None:
        """Parser should raise ValueError for invalid header."""
        invalid_csv = "SingleColumn\n2024-01-02,72.50"
        with self.assertRaises(ValueError) as cm:
            parse_fred_csv(invalid_csv, "TEST")
        self.assertIn("Unexpected CSV header", str(cm.exception))

    def test_parse_fred_csv_raises_on_invalid_row_length(self) -> None:
        """Parser should raise ValueError for rows with wrong field count."""
        invalid_csv = (
            "observation_date,VALUE\n"
            "2024-01-02"  # Only 1 field
        )
        with self.assertRaises(ValueError) as cm:
            parse_fred_csv(invalid_csv, "TEST")
        self.assertIn("has 1 fields, expected at least 2", str(cm.exception))


class FredHelperTests(unittest.TestCase):
    """Test helper functions for parsing FRED values."""

    def test_parse_observation_date_valid_formats(self) -> None:
        """Date parser should handle valid YYYY-MM-DD formats."""
        self.assertEqual(
            _parse_observation_date("2024-01-02"), datetime(2024, 1, 2, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_observation_date("2024-12-31"), datetime(2024, 12, 31, tzinfo=timezone.utc)
        )
        self.assertEqual(
            _parse_observation_date("2026-06-20"), datetime(2026, 6, 20, tzinfo=timezone.utc)
        )

    def test_parse_observation_date_invalid_length(self) -> None:
        """Date parser should raise ValueError for invalid length."""
        with self.assertRaises(ValueError) as cm:
            _parse_observation_date("2024-01-2")
        self.assertIn("Invalid date format", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            _parse_observation_date("2024-01")
        self.assertIn("Invalid date format", str(cm.exception))

    def test_parse_observation_date_invalid_components(self) -> None:
        """Date parser should raise ValueError for invalid date components."""
        with self.assertRaises(ValueError) as cm:
            _parse_observation_date("2024-13-01")
        self.assertIn("Invalid month", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            _parse_observation_date("2024-01-32")
        self.assertIn("Invalid day", str(cm.exception))

    def test_parse_value_valid_numbers(self) -> None:
        """Value parser should handle valid numeric values."""
        self.assertEqual(_parse_value("72.50"), 72.50)
        self.assertEqual(_parse_value("1.85"), 1.85)
        self.assertEqual(_parse_value("0.00"), 0.00)
        self.assertEqual(_parse_value("-1.25"), -1.25)

    def test_parse_value_missing_data(self) -> None:
        """Value parser should return None for missing data."""
        self.assertIsNone(_parse_value("."))
        self.assertIsNone(_parse_value(""))
        self.assertIsNone(_parse_value("   "))

    def test_parse_value_invalid_format(self) -> None:
        """Value parser should raise ValueError for invalid values."""
        with self.assertRaises(ValueError) as cm:
            _parse_value("not_a_number")
        self.assertIn("Invalid value format", str(cm.exception))


class FredNormalizationTests(unittest.TestCase):
    """Test normalization of FRED observations to SourceItem."""

    def test_normalize_fred_observations_creates_source_items(self) -> None:
        """Normalizer should create SourceItem for each observation."""
        csv_text = (FIXTURES_DIR / "DCOILWTICO.csv").read_text(encoding="utf-8")
        observations = parse_fred_csv(csv_text, "DCOILWTICO")

        fetched_at = datetime.now(timezone.utc)
        items = normalize_fred_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url="https://test.url/fredgraph.csv?id=DCOILWTICO",
            cursor="DCOILWTICO",
        )

        # Should have 9 items
        self.assertEqual(len(items), 9)

        # Check first item
        first = items[0]
        self.assertEqual(first.source, "fred")
        self.assertEqual(first.published_at, datetime(2024, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(first.metadata["series_id"], "DCOILWTICO")
        self.assertEqual(first.metadata["series_label"], "WTI Crude Oil Spot Price")
        self.assertEqual(first.metadata["series_classification"], "proxy")
        self.assertEqual(first.metadata["value"], 72.50)

    def test_normalize_fred_observations_includes_classification(self) -> None:
        """Normalizer should include series classification in metadata."""
        # Test proxy series
        csv_text = (FIXTURES_DIR / "DCOILWTICO.csv").read_text(encoding="utf-8")
        proxy_observations = parse_fred_csv(csv_text, "DCOILWTICO")
        proxy_items = normalize_fred_observations(
            observations=proxy_observations,
            fetched_at=datetime.now(timezone.utc),
            fetch_url="https://test.url/fredgraph.csv?id=DCOILWTICO",
            cursor="DCOILWTICO",
        )
        self.assertEqual(proxy_items[0].metadata["series_classification"], "proxy")

        # Test primary series
        csv_text = (FIXTURES_DIR / "DFII10.csv").read_text(encoding="utf-8")
        primary_observations = parse_fred_csv(csv_text, "DFII10")
        primary_items = normalize_fred_observations(
            observations=primary_observations,
            fetched_at=datetime.now(timezone.utc),
            fetch_url="https://test.url/fredgraph.csv?id=DFII10",
            cursor="DFII10",
        )
        self.assertEqual(primary_items[0].metadata["series_classification"], "primary")

    def test_normalize_fred_observations_handles_missing_values(self) -> None:
        """Normalizer should handle missing values (represented as '.')."""
        # Create observation with missing value
        from finance_news.connectors.fred_market_proxies import ParsedFredObservation

        observations = [
            ParsedFredObservation(
                series_id="TEST",
                observation_date="2024-01-02",
                value="."
            ),
        ]

        items = normalize_fred_observations(
            observations=observations,
            fetched_at=datetime.now(timezone.utc),
            fetch_url="https://test.url/fredgraph.csv?id=TEST",
            cursor="TEST",
        )

        # Should create item with None value
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0].metadata["value"])

    def test_normalize_fred_observations_skips_invalid_dates(self) -> None:
        """Normalizer should skip observations with invalid dates."""
        from finance_news.connectors.fred_market_proxies import ParsedFredObservation

        observations = [
            ParsedFredObservation(
                series_id="TEST",
                observation_date="invalid-date",
                value="72.50"
            ),
            ParsedFredObservation(
                series_id="TEST",
                observation_date="2024-01-02",
                value="72.50"
            ),
        ]

        items = normalize_fred_observations(
            observations=observations,
            fetched_at=datetime.now(timezone.utc),
            fetch_url="https://test.url/fredgraph.csv?id=TEST",
            cursor="TEST",
        )

        # Should only create item for valid date
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].published_at, datetime(2024, 1, 2, tzinfo=timezone.utc))


class FredSeriesMetadataTests(unittest.TestCase):
    """Test DEFAULT_SERIES metadata."""

    def test_default_series_includes_all_expected_series(self) -> None:
        """DEFAULT_SERIES should include all expected FRED series IDs."""
        expected_series = {
            "DCOILWTICO",
            "DCOILBRENTEU",
            "DFII10",
            "DFII5",
            "DTWEXBGS",
            "T5YIE",
            "T10YIE",
            "T5YIFR",
        }
        self.assertEqual(set(DEFAULT_SERIES.keys()), expected_series)

    def test_default_series_has_proxy_classification(self) -> None:
        """Proxy series should be marked as 'proxy'."""
        proxy_series = ["DCOILWTICO", "DCOILBRENTEU", "T5YIE", "T10YIE", "T5YIFR"]
        for series_id in proxy_series:
            self.assertEqual(
                DEFAULT_SERIES[series_id]["classification"],
                "proxy",
                f"Series {series_id} should be proxy"
            )

    def test_default_series_has_primary_classification(self) -> None:
        """Primary series should be marked as 'primary'."""
        primary_series = ["DFII10", "DFII5", "DTWEXBGS"]
        for series_id in primary_series:
            self.assertEqual(
                DEFAULT_SERIES[series_id]["classification"],
                "primary",
                f"Series {series_id} should be primary"
            )

    def test_default_series_has_required_metadata(self) -> None:
        """Each series should have label, classification, and description."""
        for series_id, metadata in DEFAULT_SERIES.items():
            self.assertIn("label", metadata, f"Series {series_id} missing label")
            self.assertIn("classification", metadata, f"Series {series_id} missing classification")
            self.assertIn("description", metadata, f"Series {series_id} missing description")
            self.assertIn(metadata["classification"], ["primary", "proxy"])


class FredConnectorTests(unittest.TestCase):
    """Test FredMarketProxiesConnector integration."""

    def test_connector_has_correct_name_and_source(self) -> None:
        """Connector should have correct name and source."""
        connector = FredMarketProxiesConnector(transport=_FakeTransport(HttpResponse(
            status_code=200,
            url="https://test.url",
            headers={},
            body=b""
        )))
        self.assertEqual(connector.name, "fred_market_proxies")
        self.assertEqual(connector.source, "fred")

    def test_fetch_page_raises_without_cursor(self) -> None:
        """Connector should raise ValueError without a series ID cursor."""
        connector = FredMarketProxiesConnector(transport=_FakeTransport(HttpResponse(
            status_code=200,
            url="https://test.url",
            headers={},
            body=b""
        )))

        async def test():
            with self.assertRaises(ValueError) as cm:
                await connector.fetch_page(cursor=None)
            self.assertIn("requires a series ID cursor", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_raises_for_unknown_series(self) -> None:
        """Connector should raise ValueError for unknown series ID."""
        connector = FredMarketProxiesConnector(transport=_FakeTransport(HttpResponse(
            status_code=200,
            url="https://test.url",
            headers={},
            body=b""
        )))

        async def test():
            with self.assertRaises(ValueError) as cm:
                await connector.fetch_page(cursor="UNKNOWN_SERIES")
            self.assertIn("Unknown FRED series ID", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_handles_404(self) -> None:
        """Connector should raise RecoverableConnectorError for 404."""
        response = HttpResponse(
            status_code=404,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={},
            body=b"Not Found"
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test():
            with self.assertRaises(RecoverableConnectorError) as cm:
                await connector.fetch_page(cursor="DCOILWTICO")
            self.assertIn("not found", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_handles_5xx_errors(self) -> None:
        """Connector should raise RecoverableConnectorError for 5xx errors."""
        response = HttpResponse(
            status_code=503,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={},
            body=b"Service Unavailable"
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test():
            with self.assertRaises(RecoverableConnectorError) as cm:
                await connector.fetch_page(cursor="DCOILWTICO")
            self.assertIn("503", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_raises_for_4xx_errors(self) -> None:
        """Connector should raise ValueError for 4xx errors (except 404)."""
        response = HttpResponse(
            status_code=400,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={},
            body=b"Bad Request"
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test():
            with self.assertRaises(ValueError) as cm:
                await connector.fetch_page(cursor="DCOILWTICO")
            self.assertIn("400", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_raises_for_unexpected_status(self) -> None:
        """Connector should raise ValueError for unexpected status codes."""
        response = HttpResponse(
            status_code=301,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={},
            body=b"Moved Permanently"
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test():
            with self.assertRaises(ValueError) as cm:
                await connector.fetch_page(cursor="DCOILWTICO")
            self.assertIn("301", str(cm.exception))

        asyncio.run(test())

    def test_fetch_page_parses_and_returns_observations(self) -> None:
        """Connector should parse CSV and return normalized observations."""
        csv_text = (FIXTURES_DIR / "DCOILWTICO.csv").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={"Content-Type": "text/csv"},
            body=csv_text.encode("utf-8")
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test():
            result = await connector.fetch_page(cursor="DCOILWTICO")

            # Should have items and no pagination
            self.assertGreater(len(result.items), 0)
            self.assertFalse(result.has_more)
            self.assertIsNone(result.next_cursor)

            # Check first item
            first_item = result.items[0]
            self.assertEqual(first_item.source, "fred")
            self.assertEqual(first_item.metadata["series_id"], "DCOILWTICO")
            self.assertEqual(first_item.metadata["series_classification"], "proxy")
            self.assertEqual(first_item.metadata["value"], 72.50)

        asyncio.run(test())

    def test_fetch_page_includes_classification_in_metadata(self) -> None:
        """Connector should include series classification in item metadata."""
        # Test proxy series
        csv_text = (FIXTURES_DIR / "DCOILWTICO.csv").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            headers={"Content-Type": "text/csv"},
            body=csv_text.encode("utf-8")
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test_proxy():
            result = await connector.fetch_page(cursor="DCOILWTICO")
            self.assertEqual(result.items[0].metadata["series_classification"], "proxy")

        asyncio.run(test_proxy())

        # Test primary series
        csv_text = (FIXTURES_DIR / "DFII10.csv").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10",
            headers={"Content-Type": "text/csv"},
            body=csv_text.encode("utf-8")
        )
        connector = FredMarketProxiesConnector(transport=_FakeTransport(response))

        async def test_primary():
            result = await connector.fetch_page(cursor="DFII10")
            self.assertEqual(result.items[0].metadata["series_classification"], "primary")

        asyncio.run(test_primary())


if __name__ == "__main__":
    unittest.main()