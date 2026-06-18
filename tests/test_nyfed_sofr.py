from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.connectors.nyfed_sofr import (
    DATA_CLASSIFICATION,
    NyfedSofrConnector,
    normalize_nyfed_sofr_observation,
    parse_nyfed_sofr_response,
    ParsedNyfedSofrObservation,
    PROXY_SOURCES,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "nyfed_sofr"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class NyfedSofrParserTests(unittest.TestCase):
    def test_parse_single_observation(self) -> None:
        """Test parsing a single SOFR observation from NY Fed API."""
        response_data = (FIXTURES_DIR / "last_1.json").read_text(encoding="utf-8")
        import json

        observations = parse_nyfed_sofr_response(json.loads(response_data))

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].effective_date, "2026-06-16")
        self.assertAlmostEqual(observations[0].percent_rate, 3.63)
        self.assertAlmostEqual(observations[0].volume_in_billions, 3137)
        self.assertAlmostEqual(observations[0].percentile_1, 3.60)
        self.assertAlmostEqual(observations[0].percentile_25, 3.61)
        self.assertAlmostEqual(observations[0].percentile_75, 3.69)
        self.assertAlmostEqual(observations[0].percentile_99, 3.72)

    def test_parse_multiple_observations(self) -> None:
        """Test parsing multiple SOFR observations from NY Fed API."""
        response_data = (FIXTURES_DIR / "last_3.json").read_text(encoding="utf-8")
        import json

        observations = parse_nyfed_sofr_response(json.loads(response_data))

        self.assertEqual(len(observations), 3)

        # First observation
        self.assertEqual(observations[0].effective_date, "2026-06-16")
        self.assertAlmostEqual(observations[0].percent_rate, 3.63)

        # Second observation
        self.assertEqual(observations[1].effective_date, "2026-06-15")
        self.assertAlmostEqual(observations[1].percent_rate, 3.64)

        # Third observation
        self.assertEqual(observations[2].effective_date, "2026-06-14")
        self.assertAlmostEqual(observations[2].percent_rate, 3.65)

    def test_parse_empty_ref_rates_returns_empty_list(self) -> None:
        """Test parsing empty refRates returns empty list."""
        response_data = {"refRates": []}

        observations = parse_nyfed_sofr_response(response_data)

        self.assertEqual(len(observations), 0)

    def test_parse_invalid_ref_rates_type_raises(self) -> None:
        """Test that parsing non-list refRates raises ValueError."""
        response_data = {"refRates": "not a list"}

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Expected 'refRates' to be a list", str(cm.exception))

    def test_parse_missing_effective_date_raises(self) -> None:
        """Test that parsing missing effectiveDate raises ValueError."""
        response_data = {
            "refRates": [
                {
                    "type": "SOFR",
                    "percentRate": 3.63,
                    "volumeInBillions": 3137,
                    "percentPercentile1": 3.60,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Invalid effectiveDate", str(cm.exception))

    def test_parse_invalid_effective_date_type_raises(self) -> None:
        """Test that parsing non-string effectiveDate raises ValueError."""
        response_data = {
            "refRates": [
                {
                    "effectiveDate": 20260616,  # Number instead of string
                    "type": "SOFR",
                    "percentRate": 3.63,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Invalid effectiveDate", str(cm.exception))

    def test_parse_missing_percent_rate_raises(self) -> None:
        """Test that parsing missing percentRate raises ValueError."""
        response_data = {
            "refRates": [
                {
                    "effectiveDate": "2026-06-16",
                    "type": "SOFR",
                    "volumeInBillions": 3137,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Invalid percentRate", str(cm.exception))

    def test_parse_missing_volume_raises(self) -> None:
        """Test that parsing missing volumeInBillions raises ValueError."""
        response_data = {
            "refRates": [
                {
                    "effectiveDate": "2026-06-16",
                    "type": "SOFR",
                    "percentRate": 3.63,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Invalid volumeInBillions", str(cm.exception))

    def test_parse_missing_percentile_raises(self) -> None:
        """Test that parsing missing percentiles raises ValueError."""
        response_data = {
            "refRates": [
                {
                    "effectiveDate": "2026-06-16",
                    "type": "SOFR",
                    "percentRate": 3.63,
                    "volumeInBillions": 3137,
                    "percentPercentile1": 3.60,
                    "percentPercentile25": 3.61,
                    "percentPercentile75": 3.69,
                    # Missing percentPercentile99
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_sofr_response(response_data)

        self.assertIn("Invalid percentPercentile99", str(cm.exception))

    def test_normalize_sofr_observation(self) -> None:
        """Test normalizing a SOFR observation."""
        parsed = ParsedNyfedSofrObservation(
            effective_date="2026-06-16",
            percent_rate=3.63,
            volume_in_billions=3137.0,
            percentile_1=3.60,
            percentile_25=3.61,
            percentile_75=3.69,
            percentile_99=3.72,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        item = normalize_nyfed_sofr_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json",
        )

        # AC#1: Verify effectiveDate and source_url are included
        self.assertEqual(item.external_id, "SOFR_2026-06-16")
        self.assertEqual(item.source, "nyfed")
        self.assertEqual(item.published_at, datetime(2026, 6, 16, tzinfo=timezone.utc))
        self.assertEqual(item.url, "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json")
        self.assertIn("SOFR: 3.63%", item.title)
        self.assertIn("2026-06-16", item.title)
        self.assertIn("Volume: $3137B", item.title)

        # AC#1: Verify SOFR rate, volume, and percentiles are in summary
        self.assertIn("SOFR rate: 3.63%", item.summary)
        self.assertIn("volume: $3137B", item.summary)
        self.assertIn("1st=3.6%", item.summary)
        self.assertIn("25th=3.61%", item.summary)
        self.assertIn("75th=3.69%", item.summary)
        self.assertIn("99th=3.72%", item.summary)

        # Verify metadata
        self.assertEqual(item.metadata["content_type"], "sofr_observation")
        self.assertAlmostEqual(item.metadata["rate"], 3.63)
        self.assertAlmostEqual(item.metadata["volume_in_billions"], 3137.0)
        self.assertAlmostEqual(item.metadata["percentile_1"], 3.60)
        self.assertAlmostEqual(item.metadata["percentile_25"], 3.61)
        self.assertAlmostEqual(item.metadata["percentile_75"], 3.69)
        self.assertAlmostEqual(item.metadata["percentile_99"], 3.72)

        # AC#3: Verify primary classification and proxy sources
        self.assertEqual(item.metadata["data_classification"], "primary")
        self.assertEqual(item.metadata["proxy_sources"], ["FRED"])

    def test_normalize_invalid_effective_date_format_raises(self) -> None:
        """Test that normalizing invalid effective_date format raises ValueError."""
        parsed = ParsedNyfedSofrObservation(
            effective_date="invalid-date",
            percent_rate=3.63,
            volume_in_billions=3137.0,
            percentile_1=3.60,
            percentile_25=3.61,
            percentile_75=3.69,
            percentile_99=3.72,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_nyfed_sofr_observation(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json",
            )

        self.assertIn("Invalid effective_date format", str(cm.exception))


class NyfedSofrConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_default_limit(self) -> None:
        """Test that fetch_page with default limit fetches SOFR data."""
        response_data = (FIXTURES_DIR / "last_3.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        result = await connector.fetch_page()

        # No pagination for this connector
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)

        # Verify the URL was built correctly
        self.assertEqual(
            transport.requests[0].url,
            "https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
        )

    async def test_fetch_page_custom_limit(self) -> None:
        """Test that fetch_page respects custom limit parameter."""
        response_data = (FIXTURES_DIR / "last_5.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/5.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport, limit=5)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 5)
        self.assertIn("last/5.json", transport.requests[0].url)

    async def test_fetch_page_empty_results(self) -> None:
        """Test that fetch_page with empty results returns empty items."""
        response_data = {"refRates": []}
        import json

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_data).encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(result.items, ())
        self.assertFalse(result.has_more)

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "service unavailable"}',
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that fetch_page with unexpected status raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,  # 4xx should raise ValueError
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "not found"}',
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected NY Fed status code 404", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_invalid_parse_raises_value_error(self) -> None:
        """Test that fetch_page with invalid parse raises ValueError."""
        # Invalid refRates type
        response_data = {"refRates": "not a list"}
        import json

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_data).encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Failed to parse NY Fed SOFR response", str(cm.exception))

    async def test_sofr_observations_have_all_required_fields(self) -> None:
        """Test that SOFR observations include all required normalized fields (AC#1)."""
        response_data = (FIXTURES_DIR / "last_1.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 1)
        item = result.items[0]

        # AC#1: Verify effectiveDate and source_url in provenance
        self.assertIsNotNone(item.published_at)  # effective_date
        self.assertEqual(item.url, "https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json")

        # AC#1: Verify SOFR rate, volume, and percentiles
        self.assertEqual(item.metadata["rate"], 3.63)
        self.assertEqual(item.metadata["volume_in_billions"], 3137.0)
        self.assertEqual(item.metadata["percentile_1"], 3.60)
        self.assertEqual(item.metadata["percentile_25"], 3.61)
        self.assertEqual(item.metadata["percentile_75"], 3.69)
        self.assertEqual(item.metadata["percentile_99"], 3.72)

    async def test_data_classification_is_primary(self) -> None:
        """Test that NY Fed SOFR is marked as primary data source (AC#3)."""
        response_data = (FIXTURES_DIR / "last_1.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/rates/secured/sofr/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedSofrConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 1)
        item = result.items[0]

        # AC#3: Verify data_classification is "primary"
        self.assertEqual(item.metadata["data_classification"], "primary")

        # AC#3: Verify FRED is listed as a proxy source
        self.assertEqual(item.metadata["proxy_sources"], ["FRED"])

    def test_module_constants_define_classification(self) -> None:
        """Test that module-level constants define primary classification (AC#3)."""
        # AC#3: Verify module-level constants
        self.assertEqual(DATA_CLASSIFICATION, "primary")
        self.assertEqual(PROXY_SOURCES, ["FRED"])

    def test_connector_has_required_attributes(self) -> None:
        """Test that connector has required name, source, and policies."""
        # Verify module name
        self.assertEqual(NyfedSofrConnector.name, "nyfed_sofr")
        self.assertEqual(NyfedSofrConnector.source, "nyfed")

        # Verify retry policy exists
        self.assertIsNotNone(NyfedSofrConnector.retry_policy)
        self.assertEqual(NyfedSofrConnector.retry_policy.max_attempts, 3)

        # Verify rate limit policy exists
        self.assertIsNotNone(NyfedSofrConnector.rate_limit_policy)
        self.assertEqual(NyfedSofrConnector.rate_limit_policy.concurrency, 1)


if __name__ == "__main__":
    unittest.main()