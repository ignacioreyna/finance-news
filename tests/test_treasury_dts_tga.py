from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.treasury_dts_tga import (
    ACCOUNT_TYPE_FILTER,
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    normalize_treasury_dts_tga_observation,
    parse_treasury_dts_tga_response,
    ParsedTreasuryDtsTgaObservation,
    SOURCE_NAME,
    TreasuryDtsTgaConnector,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "treasury_dts_tga"


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


class TreasuryDtsTgaParserTests(unittest.TestCase):
    def test_parse_operating_cash_balance_response(self) -> None:
        """Test parsing operating cash balance response from FiscalData API."""
        import json

        response_data = json.loads(
            (FIXTURES_DIR / "operating_cash_balance_response.json").read_text(
                encoding="utf-8"
            )
        )

        observations = parse_treasury_dts_tga_response(response_data)

        self.assertEqual(len(observations), 3)

        # Check first observation (2021-09-30)
        obs1 = observations[0]
        self.assertEqual(obs1.record_date, "2021-09-30")
        self.assertEqual(obs1.account_type, ACCOUNT_TYPE_FILTER)
        self.assertAlmostEqual(obs1.open_today_bal, 173745.0)
        self.assertAlmostEqual(obs1.close_today_bal, 215160.0)
        self.assertAlmostEqual(obs1.daily_change, 41415.0)  # 215160 - 173745

        # Check second observation (2021-09-29)
        obs2 = observations[1]
        self.assertEqual(obs2.record_date, "2021-09-29")
        self.assertEqual(obs2.account_type, ACCOUNT_TYPE_FILTER)
        self.assertAlmostEqual(obs2.open_today_bal, 172920.0)
        self.assertAlmostEqual(obs2.close_today_bal, 173745.0)
        self.assertAlmostEqual(obs2.daily_change, 825.0)  # 173745 - 172920

        # Check third observation (2021-09-28)
        obs3 = observations[2]
        self.assertEqual(obs3.record_date, "2021-09-28")
        self.assertEqual(obs3.account_type, ACCOUNT_TYPE_FILTER)
        self.assertAlmostEqual(obs3.open_today_bal, 217019.0)
        self.assertAlmostEqual(obs3.close_today_bal, 172920.0)
        self.assertAlmostEqual(obs3.daily_change, -44099.0)  # 172920 - 217019

    def test_parse_empty_response(self) -> None:
        """Test parsing empty results from FiscalData API."""
        import json

        response_data = json.loads(
            (FIXTURES_DIR / "empty_response.json").read_text(encoding="utf-8")
        )

        observations = parse_treasury_dts_tga_response(response_data)

        self.assertEqual(len(observations), 0)

    def test_parse_invalid_data_format_raises(self) -> None:
        """Test that parsing invalid data format raises ValueError."""
        invalid_response = {"data": "not a list"}

        with self.assertRaises(ValueError) as cm:
            parse_treasury_dts_tga_response(invalid_response)

        self.assertIn("Expected 'data' to be a list", str(cm.exception))

    def test_parse_missing_record_date_raises(self) -> None:
        """Test that parsing missing record_date raises ValueError."""
        invalid_response = {
            "data": [
                {
                    "account_type": ACCOUNT_TYPE_FILTER,
                    "close_today_bal": "215160",
                    "open_today_bal": "173745",
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_treasury_dts_tga_response(invalid_response)

        self.assertIn("Invalid record_date format", str(cm.exception))

    def test_parse_wrong_account_type_raises(self) -> None:
        """Test that parsing wrong account type raises ValueError."""
        invalid_response = {
            "data": [
                {
                    "record_date": "2021-09-30",
                    "account_type": "Wrong Account Type",
                    "close_today_bal": "215160",
                    "open_today_bal": "173745",
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_treasury_dts_tga_response(invalid_response)

        self.assertIn("Unexpected account_type", str(cm.exception))
        self.assertIn("Wrong Account Type", str(cm.exception))

    def test_parse_invalid_balance_format_raises(self) -> None:
        """Test that parsing invalid balance format raises ValueError."""
        invalid_response = {
            "data": [
                {
                    "record_date": "2021-09-30",
                    "account_type": ACCOUNT_TYPE_FILTER,
                    "close_today_bal": "not_a_number",
                    "open_today_bal": "173745",
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_treasury_dts_tga_response(invalid_response)

        self.assertIn("Invalid balance format", str(cm.exception))

    def test_normalize_tga_observation(self) -> None:
        """Test normalizing a TGA observation."""
        parsed = ParsedTreasuryDtsTgaObservation(
            record_date="2021-09-30",
            account_type=ACCOUNT_TYPE_FILTER,
            open_today_bal=173745.0,
            close_today_bal=215160.0,
            daily_change=41415.0,
        )
        fetched_at = datetime(2021, 10, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_treasury_dts_tga_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type:eq:Federal%20Reserve%20Account",
        )

        self.assertEqual(
            item.external_id, "tga_federal_reserve_account_2021-09-30"
        )
        self.assertEqual(item.source, SOURCE_NAME)
        self.assertEqual(item.published_at, datetime(2021, 9, 30, tzinfo=timezone.utc))
        self.assertIn("TGA Federal Reserve Account", item.title)
        self.assertIn("2021-09-30", item.title)
        self.assertIn("215160", item.title)  # Close balance
        self.assertIn("+41415", item.title)  # Daily change
        self.assertIn("Treasury General Account", item.summary)
        self.assertIn("215160", item.summary)
        self.assertIn("41415", item.summary)

        # Check metadata
        self.assertEqual(item.metadata["content_type"], "tga_daily_observation")
        self.assertEqual(item.metadata["account_type"], ACCOUNT_TYPE_FILTER)
        self.assertEqual(item.metadata["record_date"], "2021-09-30")
        self.assertAlmostEqual(item.metadata["open_today_bal_millions"], 173745.0)
        self.assertAlmostEqual(item.metadata["close_today_bal_millions"], 215160.0)
        self.assertAlmostEqual(item.metadata["daily_change_millions"], 41415.0)
        self.assertEqual(item.metadata["currency"], "USD")
        self.assertEqual(item.metadata["unit"], "millions")
        self.assertEqual(item.metadata["frequency"], "daily")
        self.assertIn("holiday_handling", item.metadata)
        self.assertIn("federal holidays", item.metadata["holiday_handling"])

        # Check provenance
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.source, SOURCE_NAME)

        # Check freshness
        self.assertEqual(item.freshness.published_at, datetime(2021, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)

    def test_normalize_negative_daily_change(self) -> None:
        """Test normalizing a TGA observation with negative daily change."""
        parsed = ParsedTreasuryDtsTgaObservation(
            record_date="2021-09-28",
            account_type=ACCOUNT_TYPE_FILTER,
            open_today_bal=217019.0,
            close_today_bal=172920.0,
            daily_change=-44099.0,
        )
        fetched_at = datetime(2021, 10, 1, 12, 0, tzinfo=timezone.utc)

        item = normalize_treasury_dts_tga_observation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
        )

        self.assertIn("-44099", item.title)
        self.assertEqual(item.metadata["daily_change_millions"], -44099.0)

    def test_normalize_invalid_record_date_format_raises(self) -> None:
        """Test that normalizing invalid record_date format raises ValueError."""
        parsed = ParsedTreasuryDtsTgaObservation(
            record_date="invalid-date",
            account_type=ACCOUNT_TYPE_FILTER,
            open_today_bal=100.0,
            close_today_bal=200.0,
            daily_change=100.0,
        )
        fetched_at = datetime(2021, 10, 1, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_treasury_dts_tga_observation(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
            )

        self.assertIn("Invalid record_date format", str(cm.exception))


class TreasuryDtsTgaConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_tga_observations(self) -> None:
        """Test that fetch_page returns TGA observations."""
        import json

        response_data = (
            FIXTURES_DIR / "operating_cash_balance_response.json"
        ).read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type%3Aeq%3AFederal+Reserve+Account&sort=-record_date&limit=100",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 3)

        # Check first item
        item1 = result.items[0]
        self.assertEqual(item1.source, SOURCE_NAME)
        self.assertEqual(item1.external_id, "tga_federal_reserve_account_2021-09-30")
        self.assertIn("TGA Federal Reserve Account", item1.title)
        self.assertAlmostEqual(item1.metadata["close_today_bal_millions"], 215160.0)
        self.assertAlmostEqual(item1.metadata["daily_change_millions"], 41415.0)

        # Verify request parameters
        self.assertEqual(transport.requests[0].method, "GET")
        self.assertEqual(
            transport.requests[0].url,
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
        )
        self.assertEqual(transport.requests[0].headers["Accept"], "application/json")
        self.assertIn("account_type", transport.requests[0].params["filter"])
        self.assertEqual(transport.requests[0].params["sort"], "-record_date")
        self.assertEqual(transport.requests[0].params["limit"], "100")

    async def test_fetch_page_empty_results_on_holiday(self) -> None:
        """Test that fetch_page returns empty results on holidays/weekends (AC#3)."""
        import json

        response_data = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type%3Aeq%3AFederal+Reserve+Account&sort=-record_date&limit=100",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(result.items, ())
        # Should NOT raise an error on empty results (holiday handling)

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "service unavailable"}',
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that fetch_page with unexpected status raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=400,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "bad request"}',
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected FiscalData status code 400", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_custom_limit(self) -> None:
        """Test that fetch_page respects custom limit parameter."""
        import json

        response_data = (
            FIXTURES_DIR / "operating_cash_balance_response.json"
        ).read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type%3Aeq%3AFederal+Reserve+Account&sort=-record_date&limit=10",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport, limit=10)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 3)
        # Check that the limit parameter is set correctly
        self.assertEqual(transport.requests[0].params["limit"], "10")

    async def test_tga_observations_have_required_fields(self) -> None:
        """Test that TGA observations include all required normalized fields (AC#1)."""
        import json

        response_data = (
            FIXTURES_DIR / "operating_cash_balance_response.json"
        ).read_text(encoding="utf-8")

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type%3Aeq%3AFederal+Reserve+Account&sort=-record_date&limit=100",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = TreasuryDtsTgaConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 3)
        for item in result.items:
            # Verify all required normalized fields (AC#1)
            self.assertIsNotNone(item.published_at)  # record_date
            self.assertIn("TGA Federal Reserve Account", item.title)  # account type
            self.assertIn("USD", item.metadata["currency"])  # currency
            self.assertIn("millions", item.metadata["unit"])  # unit
            self.assertEqual(item.metadata["frequency"], "daily")  # frequency
            self.assertIn(
                "open_today_bal_millions", item.metadata
            )  # opening balance
            self.assertIn(
                "close_today_bal_millions", item.metadata
            )  # closing balance
            self.assertIn("daily_change_millions", item.metadata)  # daily change
            self.assertIn("holiday_handling", item.metadata)  # holiday behavior

    def test_connector_name_and_source_attributes(self) -> None:
        connector = TreasuryDtsTgaConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )
        self.assertEqual(connector.name, "treasury_dts_tga")
        self.assertEqual(connector.source, "fiscaldata_treasury")

    def test_retry_and_rate_limit_policies_exist(self) -> None:
        connector = TreasuryDtsTgaConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )
        self.assertIsNotNone(connector.retry_policy)
        self.assertIsNotNone(connector.rate_limit_policy)
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)

    async def test_connector_documents_holiday_handling(self) -> None:
        """Test that connector documents holiday/non-business day handling (AC#3)."""
        connector = TreasuryDtsTgaConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                    headers={"Content-Type": "application/json"},
                    body=b"{}",
                )
            )
        )

        # Check docstring mentions holiday handling
        self.assertIsNotNone(connector.__doc__)
        self.assertIn("holiday", connector.__doc__.lower())
        self.assertIn("weekend", connector.__doc__.lower())
        self.assertIn("federal", connector.__doc__.lower())


if __name__ == "__main__":
    unittest.main()