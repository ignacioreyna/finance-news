from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bea_personal_income import (
    BeaPersonalIncomeConnector,
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    normalize_bea_observation,
    parse_bea_series_json,
    parse_bea_time_period,
    ParsedBeaObservation,
    SOURCE_NAME,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bea_personal_income"


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
    def test_parse_bea_time_period_monthly(self) -> None:
        """Test parsing monthly TimePeriod strings (AC#1)."""
        dt = parse_bea_time_period("2026M05")
        self.assertEqual(dt, datetime(2026, 5, 1, tzinfo=timezone.utc))

        dt = parse_bea_time_period("2026M01")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

        dt = parse_bea_time_period("2026M12")
        self.assertEqual(dt, datetime(2026, 12, 1, tzinfo=timezone.utc))

    def test_parse_bea_time_period_quarterly(self) -> None:
        """Test parsing quarterly TimePeriod strings."""
        dt = parse_bea_time_period("2026Q01")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

        dt = parse_bea_time_period("2026Q02")
        self.assertEqual(dt, datetime(2026, 4, 1, tzinfo=timezone.utc))

        dt = parse_bea_time_period("2026Q04")
        self.assertEqual(dt, datetime(2026, 10, 1, tzinfo=timezone.utc))

    def test_parse_bea_time_period_annual(self) -> None:
        """Test parsing annual TimePeriod strings."""
        dt = parse_bea_time_period("2026")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

    def test_parse_bea_time_period_invalid_month_raises(self) -> None:
        """Test that invalid month TimePeriod strings raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_time_period("2026M00")

        self.assertIn("Invalid month", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bea_time_period("2026M13")

        self.assertIn("Invalid month", str(cm.exception))

    def test_parse_bea_time_period_invalid_quarter_raises(self) -> None:
        """Test that invalid quarter TimePeriod strings raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_time_period("2026Q00")

        self.assertIn("Invalid quarter", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bea_time_period("2026Q05")

        self.assertIn("Invalid quarter", str(cm.exception))

    def test_parse_bea_time_period_unsupported_format_raises(self) -> None:
        """Test that unsupported TimePeriod formats raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_time_period("2026W01")  # Weekly not supported

        self.assertIn("Unsupported TimePeriod format", str(cm.exception))

    def test_parse_bea_series_json_success(self) -> None:
        """Test parsing successful BEA API response (AC#1)."""
        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bea_series_json(response_text, table_name="T20600")

        # Should have 5 observations total
        self.assertEqual(len(observations), 5)

        # Check Personal income observations (A069RC)
        income_obs = [o for o in observations if o.series_code == "A069RC"]
        self.assertEqual(len(income_obs), 3)
        self.assertEqual(income_obs[0].time_period, "2026M05")
        self.assertEqual(income_obs[0].line_description, "Personal income")
        self.assertAlmostEqual(income_obs[0].data_value, 21500.5)
        self.assertEqual(income_obs[0].cl_unit, "Billions of Dollars")

        # Check Wages and salaries observations (W198RC1)
        wages_obs = [o for o in observations if o.series_code == "W198RC1"]
        self.assertEqual(len(wages_obs), 2)
        self.assertEqual(wages_obs[0].time_period, "2026M05")
        self.assertEqual(wages_obs[0].line_description, "Wages and salaries")
        self.assertAlmostEqual(wages_obs[0].data_value, 12500.3)

    def test_parse_bea_series_json_empty_data(self) -> None:
        """Test parsing BEA response with empty Data array (AC#2)."""
        response_text = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bea_series_json(response_text, table_name="T20600")

        self.assertEqual(len(observations), 0)

    def test_parse_bea_series_json_invalid_json_raises(self) -> None:
        """Test that parsing invalid JSON raises ValueError (AC#2)."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_series_json("not valid json", table_name="T20600")

        self.assertIn("Invalid JSON response", str(cm.exception))

    def test_parse_bea_series_json_missing_beaapi_raises(self) -> None:
        """Test that parsing response missing BEAAPI raises ValueError (AC#2)."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_series_json('{"status": "OK"}', table_name="T20600")

        self.assertIn("Missing or invalid 'BEAAPI' field", str(cm.exception))

    def test_parse_bea_series_json_missing_results_raises(self) -> None:
        """Test that parsing response missing Results raises ValueError (AC#2)."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_series_json('{"BEAAPI": {}}', table_name="T20600")

        self.assertIn("Missing or invalid 'Results' field", str(cm.exception))

    def test_parse_bea_series_json_invalid_data_type_raises(self) -> None:
        """Test that parsing response with invalid Data type raises ValueError (AC#2)."""
        with self.assertRaises(ValueError) as cm:
            parse_bea_series_json('{"BEAAPI": {"Results": {"Data": "not a list"}}}', table_name="T20600")

        self.assertIn("Expected 'Data' to be a list", str(cm.exception))

    def test_normalize_bea_observation(self) -> None:
        """Test normalizing a BEA observation (AC#1)."""
        parsed = ParsedBeaObservation(
            table_name="T20600",
            series_code="A069RC",
            line_number="1",
            line_description="Personal income",
            time_period="2026M05",
            data_value=21500.5,
            cl_unit="Billions of Dollars",
            unit_num="3",
        )
        fetched_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_bea_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://apps.bea.gov/api/data/",
        )

        # Check external_id format
        self.assertEqual(item.external_id, "A069RC_2026M05")

        # Check source
        self.assertEqual(item.source, SOURCE_NAME)

        # Check published_at
        self.assertEqual(item.published_at, datetime(2026, 5, 1, tzinfo=timezone.utc))

        # Check title
        self.assertIn("Personal income", item.title)
        self.assertIn("2026M05", item.title)

        # Check summary
        self.assertIn("Personal income", item.summary)
        self.assertIn("2026M05", item.summary)
        self.assertIn("21500.5", item.summary)
        self.assertIn("Billions of Dollars", item.summary)

        # Check metadata
        self.assertEqual(item.metadata["content_type"], "bea_nipa_observation")
        self.assertEqual(item.metadata["table_name"], "T20600")
        self.assertEqual(item.metadata["series_code"], "A069RC")
        self.assertEqual(item.metadata["line_description"], "Personal income")
        self.assertEqual(item.metadata["time_period"], "2026M05")
        self.assertAlmostEqual(item.metadata["data_value"], 21500.5)
        self.assertEqual(item.metadata["cl_unit"], "Billions of Dollars")
        self.assertEqual(item.metadata["frequency"], "monthly")
        self.assertEqual(item.metadata["fuente"], "BEA NIPA T20600")
        self.assertEqual(item.metadata["source"], "Bureau of Economic Analysis (BEA)")

        # Check provenance
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.source, SOURCE_NAME)
        self.assertEqual(item.provenance.parser_version, "0.1.0")

        # Check freshness
        self.assertEqual(item.freshness.published_at, datetime(2026, 5, 1, tzinfo=timezone.utc))
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)

    def test_normalize_bea_observation_quarterly(self) -> None:
        """Test normalizing a quarterly BEA observation."""
        parsed = ParsedBeaObservation(
            table_name="T20600",
            series_code="A191RX",
            line_number="1",
            line_description="Real GDP",
            time_period="2026Q02",
            data_value=21000.5,
            cl_unit="Billions of Chained 2017 Dollars",
            unit_num="3",
        )
        fetched_at = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_bea_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://apps.bea.gov/api/data/",
        )

        self.assertEqual(item.external_id, "A191RX_2026Q02")
        self.assertEqual(item.published_at, datetime(2026, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(item.metadata["frequency"], "quarterly")

    def test_normalize_bea_observation_annual(self) -> None:
        """Test normalizing an annual BEA observation."""
        parsed = ParsedBeaObservation(
            table_name="T20600",
            series_code="A191RX",
            line_number="1",
            line_description="Real GDP",
            time_period="2026",
            data_value=85000.0,
            cl_unit="Billions of Chained 2017 Dollars",
            unit_num="3",
        )
        fetched_at = datetime(2027, 1, 15, 12, 0, tzinfo=timezone.utc)

        item = normalize_bea_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://apps.bea.gov/api/data/",
        )

        self.assertEqual(item.external_id, "A191RX_2026")
        self.assertEqual(item.published_at, datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(item.metadata["frequency"], "annual")


class BeaPersonalIncomeConnectorTests(unittest.IsolatedAsyncioTestCase):
    def test_connector_attributes(self) -> None:
        """Test connector name, source, and policies."""
        connector = BeaPersonalIncomeConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://apps.bea.gov/api/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        self.assertEqual(connector.name, "bea_personal_income")
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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        result = await connector.fetch_page()

        # Should return 5 observations from the fixture
        self.assertEqual(len(result.items), 5)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Check that request was made with correct params
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.params["method"], "GetData")
        self.assertEqual(request.params["DataSetName"], "NIPA")
        self.assertEqual(request.params["TableName"], "T20600")
        self.assertEqual(request.params["Frequency"], "M")
        self.assertEqual(request.params["Year"], "2026")

    async def test_fetch_page_empty_results(self) -> None:
        """Test fetch_page with empty Data array (AC#2)."""
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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that unexpected status codes raise ValueError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,
                url="https://apps.bea.gov/api/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"BEAAPI": {"Results": {}}}',
            )
        )
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected BEA API status code 301", str(cm.exception))

    def test_get_api_key_without_env_var(self) -> None:
        """Test that get_api_key returns None when env var is not set (AC#3)."""
        # Ensure env var is not set
        if "BEA_API_KEY" in __import__("os").environ:
            del __import__("os").environ["BEA_API_KEY"]

        connector = BeaPersonalIncomeConnector(
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
        os = __import__("os")
        # Set env var
        os.environ["BEA_API_KEY"] = "test_api_key_123456789012345678901234"

        try:
            connector = BeaPersonalIncomeConnector(
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
            self.assertEqual(api_key, "test_api_key_123456789012345678901234")
        finally:
            # Clean up
            del os.environ["BEA_API_KEY"]

    async def test_fetch_page_includes_api_key_when_set(self) -> None:
        """Test that fetch_page includes API key in request when set (AC#3)."""
        os = __import__("os")
        # Set env var
        os.environ["BEA_API_KEY"] = "test_api_key_123456789012345678901234"

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
            connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

            result = await connector.fetch_page()

            # Verify the API key was included in the request
            request = transport.requests[0]
            self.assertEqual(request.params.get("UserID"), "test_api_key_123456789012345678901234")
        finally:
            # Clean up
            del os.environ["BEA_API_KEY"]

    async def test_fetch_page_without_api_key_when_not_set(self) -> None:
        """Test that fetch_page works without API key when env var is not set (AC#3)."""
        os = __import__("os")
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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        result = await connector.fetch_page()

        # Should return observations successfully
        self.assertEqual(len(result.items), 5)

        # Verify the API key was NOT included in the request
        request = transport.requests[0]
        self.assertNotIn("UserID", request.params)

    async def test_items_sorted_by_time_period(self) -> None:
        """Test that items are sorted deterministically by time period."""
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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        result = await connector.fetch_page()

        # Check that items are sorted by published_at (time period)
        dates = [item.published_at for item in result.items]

        for i in range(len(dates) - 1):
            self.assertLessEqual(dates[i], dates[i + 1])

    async def test_metadata_includes_fuente(self) -> None:
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
        connector = BeaPersonalIncomeConnector(transport=transport, year="2026")

        result = await connector.fetch_page()

        # All items should have fuente in metadata
        for item in result.items:
            self.assertIn("fuente", item.metadata)
            self.assertEqual(item.metadata["fuente"], "BEA NIPA T20600")


if __name__ == "__main__":
    unittest.main()