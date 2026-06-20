from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bls_timeseries import (
    BlsTimeseriesConnector,
    CONNECTOR_NAME,
    DEFAULT_SERIES,
    DEFAULT_TTL_SECONDS,
    normalize_bls_observation,
    parse_bls_period,
    parse_bls_series_json,
    ParsedBlsObservation,
    SOURCE_NAME,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bls_timeseries"


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


class BlsParserTests(unittest.TestCase):
    def test_parse_bls_period_monthly(self) -> None:
        """Test parsing monthly period codes."""
        dt = parse_bls_period("2026", "M05")
        self.assertEqual(dt, datetime(2026, 5, 1, tzinfo=timezone.utc))

        dt = parse_bls_period("2026", "M01")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

        dt = parse_bls_period("2026", "M12")
        self.assertEqual(dt, datetime(2026, 12, 1, tzinfo=timezone.utc))

    def test_parse_bls_period_quarterly(self) -> None:
        """Test parsing quarterly period codes."""
        dt = parse_bls_period("2026", "Q01")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

        dt = parse_bls_period("2026", "Q02")
        self.assertEqual(dt, datetime(2026, 4, 1, tzinfo=timezone.utc))

        dt = parse_bls_period("2026", "Q04")
        self.assertEqual(dt, datetime(2026, 10, 1, tzinfo=timezone.utc))

    def test_parse_bls_period_annual(self) -> None:
        """Test parsing annual period codes."""
        dt = parse_bls_period("2026", "A01")
        self.assertEqual(dt, datetime(2026, 1, 1, tzinfo=timezone.utc))

    def test_parse_bls_period_invalid_month_raises(self) -> None:
        """Test that invalid month period codes raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_period("2026", "M00")

        self.assertIn("Invalid month period", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bls_period("2026", "M13")

        self.assertIn("Invalid month period", str(cm.exception))

    def test_parse_bls_period_invalid_quarter_raises(self) -> None:
        """Test that invalid quarter period codes raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_period("2026", "Q00")

        self.assertIn("Invalid quarter period", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            parse_bls_period("2026", "Q05")

        self.assertIn("Invalid quarter period", str(cm.exception))

    def test_parse_bls_period_unsupported_code_raises(self) -> None:
        """Test that unsupported period codes raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_period("2026", "W01")  # Weekly not supported

        self.assertIn("Unsupported period code", str(cm.exception))

    def test_parse_bls_series_json_success(self) -> None:
        """Test parsing successful BLS API response (AC#1)."""
        import json

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bls_series_json(
            response_text,
            series_ids=["CUSR0000SA0", "LNS14000000", "CES0000000001"],
        )

        # Should have 8 observations total (3 CPI + 3 unemployment + 2 payrolls)
        self.assertEqual(len(observations), 8)

        # Check CPI observations (CUSR0000SA0)
        cpi_obs = [o for o in observations if o.series_id == "CUSR0000SA0"]
        self.assertEqual(len(cpi_obs), 3)
        self.assertEqual(cpi_obs[0].year, "2026")
        self.assertEqual(cpi_obs[0].period, "M05")
        self.assertEqual(cpi_obs[0].period_name, "May")
        self.assertAlmostEqual(cpi_obs[0].value, 317.123)
        self.assertEqual(len(cpi_obs[0].footnotes), 1)
        self.assertEqual(cpi_obs[0].footnotes[0]["code"], "P")

        # Check unemployment observations (LNS14000000)
        unemp_obs = [o for o in observations if o.series_id == "LNS14000000"]
        self.assertEqual(len(unemp_obs), 3)
        self.assertEqual(unemp_obs[0].year, "2026")
        self.assertEqual(unemp_obs[0].period, "M05")
        self.assertEqual(unemp_obs[0].period_name, "May")
        self.assertAlmostEqual(unemp_obs[0].value, 4.0)

        # Check payrolls observations (CES0000000001)
        payroll_obs = [o for o in observations if o.series_id == "CES0000000001"]
        self.assertEqual(len(payroll_obs), 2)
        self.assertEqual(payroll_obs[0].year, "2026")
        self.assertEqual(payroll_obs[0].period, "M05")
        self.assertEqual(payroll_obs[0].period_name, "May")
        self.assertAlmostEqual(payroll_obs[0].value, 150000.5)

    def test_parse_bls_series_json_empty_data(self) -> None:
        """Test parsing BLS response with empty data array."""
        import json

        response_text = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        observations = parse_bls_series_json(
            response_text,
            series_ids=["CUSR0000SA0"],
        )

        self.assertEqual(len(observations), 0)

    def test_parse_bls_series_json_not_found_status(self) -> None:
        """Test parsing BLS response with NOT_FOUND status (AC#2)."""
        import json

        response_text = (FIXTURES_DIR / "not_found_response.json").read_text(
            encoding="utf-8"
        )

        with self.assertRaises(ValueError) as cm:
            parse_bls_series_json(
                response_text,
                series_ids=["INVALID_SERIES_ID_12345"],
            )

        self.assertIn("BLS API request failed", str(cm.exception))
        self.assertIn("NOT_FOUND", str(cm.exception))

    def test_parse_bls_series_json_invalid_json_raises(self) -> None:
        """Test that parsing invalid JSON raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_series_json("not valid json", series_ids=["CUSR0000SA0"])

        self.assertIn("Invalid JSON response", str(cm.exception))

    def test_parse_bls_series_json_missing_results_raises(self) -> None:
        """Test that parsing response missing Results raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_series_json(
                '{"status": "REQUEST_SUCCEEDED"}',
                series_ids=["CUSR0000SA0"],
            )

        self.assertIn("Missing or invalid 'Results' field", str(cm.exception))

    def test_parse_bls_series_json_missing_series_raises(self) -> None:
        """Test that parsing response missing series raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parse_bls_series_json(
                '{"status": "REQUEST_SUCCEEDED", "Results": {}}',
                series_ids=["CUSR0000SA0"],
            )

        self.assertIn("Missing 'series' field in Results", str(cm.exception))

    def test_normalize_bls_observation(self) -> None:
        """Test normalizing a BLS observation (AC#1)."""
        parsed = ParsedBlsObservation(
            series_id="CUSR0000SA0",
            year="2026",
            period="M05",
            period_name="May",
            value=317.123,
            footnotes=[{"code": "P", "text": "Preliminary"}],
        )
        fetched_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_bls_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
        )

        # Check external_id format
        self.assertEqual(item.external_id, "CUSR0000SA0_2026_M05")

        # Check source
        self.assertEqual(item.source, SOURCE_NAME)

        # Check published_at
        self.assertEqual(item.published_at, datetime(2026, 5, 1, tzinfo=timezone.utc))

        # Check title
        self.assertIn("CUSR0000SA0", item.title)
        self.assertIn("May", item.title)
        self.assertIn("2026", item.title)

        # Check summary
        self.assertIn("CUSR0000SA0", item.summary)
        self.assertIn("May 2026", item.summary)
        self.assertIn("317.123", item.summary)

        # Check metadata
        self.assertEqual(item.metadata["content_type"], "bls_timeseries_observation")
        self.assertEqual(item.metadata["series_id"], "CUSR0000SA0")
        self.assertEqual(item.metadata["year"], "2026")
        self.assertEqual(item.metadata["period"], "M05")
        self.assertEqual(item.metadata["period_name"], "May")
        self.assertAlmostEqual(item.metadata["value"], 317.123)
        self.assertEqual(item.metadata["frequency"], "monthly")
        self.assertEqual(item.metadata["source"], "Bureau of Labor Statistics (BLS)")
        self.assertEqual(len(item.metadata["footnotes"]), 1)
        self.assertEqual(item.metadata["footnotes"][0]["code"], "P")

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

    def test_normalize_bls_observation_quarterly(self) -> None:
        """Test normalizing a quarterly BLS observation."""
        parsed = ParsedBlsObservation(
            series_id="GDP2026",
            year="2026",
            period="Q02",
            period_name="Q2",
            value=21000.5,
            footnotes=[],
        )
        fetched_at = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_bls_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
        )

        self.assertEqual(item.external_id, "GDP2026_2026_Q02")
        self.assertEqual(item.published_at, datetime(2026, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(item.metadata["frequency"], "quarterly")

    def test_normalize_bls_observation_annual(self) -> None:
        """Test normalizing an annual BLS observation."""
        parsed = ParsedBlsObservation(
            series_id="GDP2026",
            year="2026",
            period="A01",
            period_name="Annual",
            value=85000.0,
            footnotes=[],
        )
        fetched_at = datetime(2027, 1, 15, 12, 0, tzinfo=timezone.utc)

        item = normalize_bls_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
        )

        self.assertEqual(item.external_id, "GDP2026_2026_A01")
        self.assertEqual(item.published_at, datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(item.metadata["frequency"], "annual")


class BlsTimeseriesConnectorTests(unittest.IsolatedAsyncioTestCase):
    def test_connector_attributes(self) -> None:
        """Test connector name, source, and policies."""
        connector = BlsTimeseriesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        self.assertEqual(connector.name, "bls_timeseries")
        self.assertEqual(connector.source, "bls")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)

    async def test_fetch_page_default_series(self) -> None:
        """Test fetch_page with DEFAULT_SERIES (no cursor) (AC#1)."""
        import json

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page()

        # Should return 8 observations from the fixture
        self.assertEqual(len(result.items), 8)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Check that request was made with DEFAULT_SERIES
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertIn("CUSR0000SA0", request.params["seriesid"])
        self.assertIn("LNS14000000", request.params["seriesid"])

    async def test_fetch_page_with_cursor(self) -> None:
        """Test fetch_page with custom series IDs via cursor (AC#1)."""
        import json

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page(cursor="CUSR0000SA0,LNS14000000")

        # Should return 6 observations (3 CPI + 3 unemployment)
        self.assertEqual(len(result.items), 6)

        # Check that request was made with cursor series
        request = transport.requests[0]
        self.assertEqual(request.params["seriesid"], "CUSR0000SA0,LNS14000000")

    async def test_fetch_page_empty_results(self) -> None:
        """Test fetch_page with empty data array."""
        import json

        response_text = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 0)
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that 5xx errors raise RecoverableConnectorError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"status": "SERVER_ERROR"}',
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_4xx_raises_value_error(self) -> None:
        """Test that 4xx errors raise ValueError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"status": "NOT_FOUND"}',
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("404", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that invalid JSON raises ValueError (AC#2)."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that unexpected status codes raise ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=301,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=b'{"status": "MOVED"}',
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected BLS API status code 301", str(cm.exception))

    def test_get_api_key_without_env_var(self) -> None:
        """Test that get_api_key returns None when env var is not set (AC#3)."""
        import os

        # Ensure env var is not set
        if "BLS_API_KEY" in os.environ:
            del os.environ["BLS_API_KEY"]

        connector = BlsTimeseriesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
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
        os.environ["BLS_API_KEY"] = "test_api_key_12345"

        try:
            connector = BlsTimeseriesConnector(
                transport=_FakeTransport(
                    HttpResponse(
                        status_code=200,
                        url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    )
                )
            )

            api_key = connector._get_api_key()
            self.assertEqual(api_key, "test_api_key_12345")
        finally:
            # Clean up
            del os.environ["BLS_API_KEY"]

    async def test_fetch_page_includes_api_key_when_set(self) -> None:
        """Test that fetch_page includes API key in request when set (AC#3)."""
        import os

        # Set env var
        os.environ["BLS_API_KEY"] = "test_api_key_12345"

        try:
            response_text = (FIXTURES_DIR / "success_response.json").read_text(
                encoding="utf-8"
            )

            transport = _FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                    headers={"Content-Type": "application/json"},
                    body=response_text.encode("utf-8"),
                )
            )
            connector = BlsTimeseriesConnector(transport=transport)

            result = await connector.fetch_page()

            # Verify the API key was included in the request
            request = transport.requests[0]
            self.assertEqual(request.params.get("registrationkey"), "test_api_key_12345")
        finally:
            # Clean up
            del os.environ["BLS_API_KEY"]

    async def test_fetch_page_without_api_key_when_not_set(self) -> None:
        """Test that fetch_page works without API key when env var is not set (AC#3)."""
        import os

        # Ensure env var is not set
        if "BLS_API_KEY" in os.environ:
            del os.environ["BLS_API_KEY"]

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page()

        # Should return observations successfully
        self.assertEqual(len(result.items), 8)

        # Verify the API key was NOT included in the request
        request = transport.requests[0]
        self.assertNotIn("registrationkey", request.params)

    def test_build_request_params_with_year_range(self) -> None:
        """Test building request parameters with year range."""
        connector = BlsTimeseriesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            ),
            startyear="2020",
            endyear="2025",
        )

        params = connector._build_request_params(["CUSR0000SA0"])

        self.assertEqual(params["seriesid"], "CUSR0000SA0")
        self.assertEqual(params["startyear"], "2020")
        self.assertEqual(params["endyear"], "2025")

    def test_build_request_params_exceeds_max_series_raises(self) -> None:
        """Test that requesting more than 50 series raises ValueError."""
        connector = BlsTimeseriesConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        # Try to request 51 series
        series_ids = [f"SERIES_{i}" for i in range(51)]

        with self.assertRaises(ValueError) as cm:
            connector._build_request_params(series_ids)

        self.assertIn("Cannot request more than 50 series", str(cm.exception))

    def test_default_series_is_non_empty(self) -> None:
        """Test that DEFAULT_SERIES is non-empty (AC#1)."""
        self.assertIsInstance(DEFAULT_SERIES, list)
        self.assertGreater(len(DEFAULT_SERIES), 0)

        # Check for expected series IDs
        self.assertIn("CUSR0000SA0", DEFAULT_SERIES)  # CPI headline
        self.assertIn("CES0000000001", DEFAULT_SERIES)  # Payrolls
        self.assertIn("LNS14000000", DEFAULT_SERIES)  # Unemployment
        self.assertIn("CES0500000003", DEFAULT_SERIES)  # AHE
        self.assertIn("JTS000000000000000JOL", DEFAULT_SERIES)  # JOLTS openings

    async def test_items_sorted_by_series_and_date(self) -> None:
        """Test that items are sorted deterministically by series_id and date."""
        import json

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page()

        # Check that items are sorted by series_id then date
        series_ids = [item.metadata["series_id"] for item in result.items]
        dates = [item.published_at for item in result.items]

        # All items from the same series should be grouped together
        # and sorted by date within each series
        for i in range(len(series_ids) - 1):
            if series_ids[i] == series_ids[i + 1]:
                # Same series: check date ordering
                self.assertLessEqual(dates[i], dates[i + 1])
            else:
                # Different series: check series_id ordering
                self.assertLessEqual(series_ids[i], series_ids[i + 1])

    async def test_fetch_page_no_cursor_empty_default_raises(self) -> None:
        """Test that fetch_page raises ValueError when no cursor and empty DEFAULT_SERIES."""
        # Mock empty DEFAULT_SERIES temporarily
        import finance_news.connectors.bls_timeseries as bls_module
        original_series = bls_module.DEFAULT_SERIES
        bls_module.DEFAULT_SERIES = []

        try:
            transport = _FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
            connector = BlsTimeseriesConnector(transport=transport)

            with self.assertRaises(ValueError) as cm:
                await connector.fetch_page()

            self.assertIn("No series IDs provided", str(cm.exception))
        finally:
            # Restore original DEFAULT_SERIES
            bls_module.DEFAULT_SERIES = original_series

    async def test_fetch_page_with_single_series(self) -> None:
        """Test fetch_page with a single series ID."""
        import json

        response_text = (FIXTURES_DIR / "success_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
                headers={"Content-Type": "application/json"},
                body=response_text.encode("utf-8"),
            )
        )
        connector = BlsTimeseriesConnector(transport=transport)

        result = await connector.fetch_page(cursor="CUSR0000SA0")

        # Should return 3 CPI observations
        self.assertEqual(len(result.items), 3)

        # All items should be from the requested series
        for item in result.items:
            self.assertEqual(item.metadata["series_id"], "CUSR0000SA0")


if __name__ == "__main__":
    unittest.main()