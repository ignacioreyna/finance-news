from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bea_real_gdp import (
    BeaRealGdpConnector,
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    normalize_bea_observation,
    parse_bea_gdp_json,
    parse_bea_period,
    ParsedBeaObservation,
    SOURCE_NAME,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bea_real_gdp"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        # Update response URL to match the request URL with params
        from urllib.parse import urlencode

        if request.params:
            params_str = urlencode(request.params)
            updated_url = f"{request.url}?{params_str}"
            response_with_url = HttpResponse(
                status_code=self.response.status_code,
                url=updated_url,
                headers=self.response.headers,
                body=self.response.body,
            )
            return response_with_url
        return self.response


class BeaParserTests(unittest.TestCase):
    def test_parse_bea_period_q1(self) -> None:
        """Test parsing Q1 period codes (AC#1)."""
        dt = parse_bea_period("2025Q1")
        self.assertEqual(dt, datetime(2025, 1, 1, tzinfo=timezone.utc))

    def test_parse_bea_period_q2(self) -> None:
        """Test parsing Q2 period codes (AC#1)."""
        dt = parse_bea_period("2025Q2")
        self.assertEqual(dt, datetime(2025, 4, 1, tzinfo=timezone.utc))

    def test_parse_bea_period_q3(self) -> None:
        """Test parsing Q3 period codes (AC#1)."""
        dt = parse_bea_period("2025Q3")
        self.assertEqual(dt, datetime(2025, 7, 1, tzinfo=timezone.utc))

    def test_parse_bea_period_q4(self) -> None:
        """Test parsing Q4 period codes (AC#1)."""
        dt = parse_bea_period("2025Q4")
        self.assertEqual(dt, datetime(2025, 10, 1, tzinfo=timezone.utc))

    def test_parse_bea_period_invalid_format_raises(self) -> None:
        """Test that invalid period formats raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_period("2025-01")  # Wrong format

        self.assertIn("Invalid time_period format", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bea_period("")  # Empty

        self.assertIn("Empty time_period", str(cm.exception))

    def test_parse_bea_period_invalid_quarter_raises(self) -> None:
        """Test that invalid quarter codes raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_period("2025Q0")  # Invalid quarter

        self.assertIn("Invalid quarter", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bea_period("2025Q5")  # Invalid quarter

        self.assertIn("Invalid quarter", str(cm.exception))

    def test_parse_bea_gdp_json_success(self) -> None:
        """Test parsing successful BEA API response (AC#1, AC#2)."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bea_gdp_json(response_text)

        # Should have 4 quarterly observations
        self.assertEqual(len(observations), 4)

        # Check first observation (2025Q1)
        obs = observations[0]
        self.assertEqual(obs.time_period, "2025Q1")
        self.assertAlmostEqual(obs.data_value, 2.1)
        self.assertEqual(obs.unit, "Percent")
        self.assertEqual(obs.line_number, "1")
        self.assertIn("Gross domestic product", obs.line_description)

        # Check second observation (2024Q4)
        obs = observations[1]
        self.assertEqual(obs.time_period, "2024Q4")
        self.assertAlmostEqual(obs.data_value, 3.4)

        # Check third observation (2024Q3)
        obs = observations[2]
        self.assertEqual(obs.time_period, "2024Q3")
        self.assertAlmostEqual(obs.data_value, 4.9)

        # Check fourth observation (2024Q2)
        obs = observations[3]
        self.assertEqual(obs.time_period, "2024Q2")
        self.assertAlmostEqual(obs.data_value, 2.1)

    def test_parse_bea_gdp_json_empty_data(self) -> None:
        """Test parsing BEA response with empty data array (AC#2)."""
        response_text = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bea_gdp_json(response_text)

        self.assertEqual(len(observations), 0)

    def test_parse_bea_gdp_json_api_error(self) -> None:
        """Test parsing BEA response with API error (AC#2)."""
        response_text = (FIXTURES_DIR / "error_response.json").read_text(
            encoding="utf-8"
        )

        with self.assertRaises(ValueError) as cm:
            parse_bea_gdp_json(response_text)

        self.assertIn("BEA API error", str(cm.exception))
        self.assertIn("404", str(cm.exception))

    def test_parse_bea_gdp_json_invalid_json_raises(self) -> None:
        """Test that parsing invalid JSON raises ValueError (AC#2)."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_gdp_json("not valid json")

        self.assertIn("Invalid JSON response", str(cm.exception))

    def test_parse_bea_gdp_json_missing_beaapi_raises(self) -> None:
        """Test that parsing response missing BEAAPI raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_gdp_json('{"status": "OK"}')

        self.assertIn("Missing or invalid 'BEAAPI' field", str(cm.exception))

    def test_parse_bea_gdp_json_missing_results_raises(self) -> None:
        """Test that parsing response missing Results raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_gdp_json('{"BEAAPI": {}}')

        self.assertIn("Missing or invalid 'Results' field", str(cm.exception))

    def test_parse_bea_gdp_json_missing_data_raises(self) -> None:
        """Test that parsing response missing Data raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_gdp_json('{"BEAAPI": {"Results": {}}}')

        self.assertIn("Missing 'Data' field in Results", str(cm.exception))

    def test_normalize_bea_observation(self) -> None:
        """Test normalizing a BEA observation (AC#1)."""
        parsed = ParsedBeaObservation(
            time_period="2025Q1",
            data_value=2.1,
            unit="Percent",
            line_number="1",
            line_description="Gross domestic product (seasonally adjusted annual rate)",
            note_ref="0",
        )
        fetched_at = datetime(2025, 4, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_bea_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://apps.bea.gov/api/data/",
        )

        # Check external_id format
        self.assertEqual(item.external_id, "bea_gdp_2025Q1")

        # Check source
        self.assertEqual(item.source, SOURCE_NAME)

        # Check published_at (Q1 starts in January)
        self.assertEqual(item.published_at, datetime(2025, 1, 1, tzinfo=timezone.utc))

        # Check title
        self.assertIn("BEA Real GDP", item.title)
        self.assertIn("2025Q1", item.title)

        # Check summary
        self.assertIn("2025Q1", item.summary)
        self.assertIn("2.1", item.summary)
        self.assertIn("Percent", item.summary)
        self.assertIn("BEA NIPA T10101", item.summary)

        # Check metadata (AC#1)
        self.assertEqual(item.metadata["content_type"], "bea_real_gdp_observation")
        self.assertEqual(item.metadata["time_period"], "2025Q1")
        self.assertAlmostEqual(item.metadata["value"], 2.1)
        self.assertEqual(item.metadata["units"], "Percent")
        self.assertEqual(item.metadata["fuente"], "BEA NIPA T10101")
        self.assertEqual(item.metadata["frequency"], "quarterly")
        self.assertEqual(item.metadata["source"], "Bureau of Economic Analysis (BEA)")
        self.assertEqual(item.metadata["dataset"], "NIPA")
        self.assertEqual(item.metadata["table"], "T10101")

        # Check provenance
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.source, SOURCE_NAME)
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertIn("bea.gov", item.provenance.canonical_url)

        # Check freshness
        self.assertEqual(item.freshness.published_at, datetime(2025, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)


class BeaRealGdpConnectorTests(unittest.IsolatedAsyncioTestCase):
    def test_connector_attributes(self) -> None:
        """Test connector name, source, and policies."""
        connector = BeaRealGdpConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        self.assertEqual(connector.name, "bea_real_gdp")
        self.assertEqual(connector.source, "bea")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)

    async def test_fetch_page_success(self) -> None:
        """Test fetch_page with successful response (AC#1)."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        # Should return 4 observations from the fixture
        self.assertEqual(len(result.items), 4)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Check that request was made with correct parameters
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.params["method"], "GetData")
        self.assertEqual(request.params["DataSetName"], "NIPA")
        self.assertEqual(request.params["TableName"], "T10101")
        self.assertEqual(request.params["Frequency"], "Q")
        self.assertEqual(request.params["ResultFormat"], "JSON")

    async def test_fetch_page_empty_results(self) -> None:
        """Test fetch_page with empty data array (AC#2)."""
        response_text = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 0)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that 5xx errors raise RecoverableConnectorError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"BEAAPI": {"Results": {}}}',
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_4xx_raises_value_error(self) -> None:
        """Test that 4xx errors raise ValueError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"BEAAPI": {"Results": {}}}',
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("404", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that invalid JSON raises ValueError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that unexpected status codes raise ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"BEAAPI": {"Results": {}}}',
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected BEA API status code 301", str(cm.exception))

    def test_get_api_key_without_env_var(self) -> None:
        """Test that get_api_key returns None when env var is not set (AC#3)."""
        import os

        # Ensure env var is not set
        if "BEA_API_KEY" in os.environ:
            del os.environ["BEA_API_KEY"]

        connector = BeaRealGdpConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        api_key = connector._get_api_key()
        self.assertIsNone(api_key)

    def test_get_api_key_with_env_var(self) -> None:
        """Test that get_api_key returns the key when env var is set (AC#3)."""
        import os

        # Set env var
        os.environ["BEA_API_KEY"] = "test_api_key_123456789012345678901234567890"

        try:
            connector = BeaRealGdpConnector(
                transport=_FakeTransport(
                    HttpResponse(
                        status_code=200,
                        url="https://apps.bea.gov/api/data/",
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    )
                )
            )

            api_key = connector._get_api_key()
            self.assertEqual(api_key, "test_api_key_123456789012345678901234567890")
        finally:
            # Clean up
            del os.environ["BEA_API_KEY"]

    async def test_fetch_page_includes_api_key_when_set(self) -> None:
        """Test that fetch_page includes API key in request when set (AC#3)."""
        import os

        # Set env var
        os.environ["BEA_API_KEY"] = "test_api_key_123456789012345678901234567890"

        try:
            response_text = (FIXTURES_DIR / "success_response.json").read_text(
                encoding="utf-8"
            )

            transport = _FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=response_text.encode("utf-8"),
                )
            )
            connector = BeaRealGdpConnector(transport=transport)

            result = await connector.fetch_page()

            # Verify the API key was included in the request
            request = transport.requests[0]
            self.assertEqual(
                request.params.get("UserID"),
                "test_api_key_123456789012345678901234567890"
            )
        finally:
            # Clean up
            del os.environ["BEA_API_KEY"]

    async def test_fetch_page_without_api_key_when_not_set(self) -> None:
        """Test that fetch_page works without API key when env var is not set (AC#3)."""
        import os

        # Ensure env var is not set
        if "BEA_API_KEY" in os.environ:
            del os.environ["BEA_API_KEY"]

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        # Should return observations successfully
        self.assertEqual(len(result.items), 4)

        # Verify UserID was set to empty string
        request = transport.requests[0]
        self.assertEqual(request.params.get("UserID"), "")

    def test_build_request_params_default_years(self) -> None:
        """Test building request parameters with default years."""
        connector = BeaRealGdpConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        params = connector._build_request_params()

        self.assertEqual(params["method"], "GetData")
        self.assertEqual(params["DataSetName"], "NIPA")
        self.assertEqual(params["TableName"], "T10101")
        self.assertEqual(params["Frequency"], "Q")
        self.assertEqual(params["Year"], "2024,2025")
        self.assertEqual(params["ResultFormat"], "JSON")
        self.assertEqual(params["UserID"], "")

    def test_build_request_params_custom_years(self) -> None:
        """Test building request parameters with custom years."""
        connector = BeaRealGdpConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            ),
            years="2023,2024,2025",
        )

        params = connector._build_request_params()

        self.assertEqual(params["Year"], "2023,2024,2025")

    async def test_items_sorted_by_date(self) -> None:
        """Test that items are sorted deterministically by date."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        # Check that items are sorted by published_at
        dates = [item.published_at for item in result.items]

        for i in range(len(dates) - 1):
            self.assertLessEqual(dates[i], dates[i + 1])

    async def test_metadata_includes_fuente_field(self) -> None:
        """Test that metadata includes fuente field (AC#1)."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        # All items should have fuente field
        for item in result.items:
            self.assertIn("fuente", item.metadata)
            self.assertEqual(item.metadata["fuente"], "BEA NIPA T10101")

    async def test_metadata_includes_all_required_fields(self) -> None:
        """Test that metadata includes all required fields (AC#1)."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BeaRealGdpConnector(transport=transport)

        result = await connector.fetch_page()

        # All items should have required metadata fields
        for item in result.items:
            # Check period (time_period)
            self.assertIn("time_period", item.metadata)
            self.assertIsInstance(item.metadata["time_period"], str)

            # Check value
            self.assertIn("value", item.metadata)
            self.assertIsInstance(item.metadata["value"], (int, float))

            # Check units
            self.assertIn("units", item.metadata)
            self.assertIsInstance(item.metadata["units"], str)

            # Check fuente
            self.assertIn("fuente", item.metadata)
            self.assertEqual(item.metadata["fuente"], "BEA NIPA T10101")


if __name__ == "__main__":
    unittest.main()