from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.treasury_dts_cashflows import (
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    aggregate_cashflows_weekly_by_category,
    normalize_treasury_dts_cashflow_observation,
    parse_treasury_dts_cashflows_json,
    ParsedTreasuryDtsCashflowObservation,
    SOURCE_NAME,
    TreasuryDtsCashflowsConnector,
)
from finance_news.connectors.models import RecoverableConnectorError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "treasury_dts_cashflows"


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


class TreasuryDtsCashflowsParserTests(unittest.TestCase):
    def test_parse_cashflows_response(self) -> None:
        """Test parsing deposits/withdrawals response from FiscalData API."""
        import json

        response_data = json.loads(
            (FIXTURES_DIR / "cashflows.json").read_text(encoding="utf-8")
        )

        observations = parse_treasury_dts_cashflows_json(response_data)

        # Should have 10 observations from the fixture
        self.assertEqual(len(observations), 10)

        # Check first observation (2024-01-10, Taxes withdrawal)
        obs1 = observations[0]
        self.assertEqual(obs1.record_date, "2024-01-10")
        self.assertEqual(obs1.transaction_type, "withdrawals")
        self.assertEqual(obs1.category, "Taxes")
        self.assertAlmostEqual(obs1.amount, -2500.0)

        # Check second observation (2024-01-10, Federal Debt withdrawal)
        obs2 = observations[1]
        self.assertEqual(obs2.record_date, "2024-01-10")
        self.assertEqual(obs2.transaction_type, "withdrawals")
        self.assertEqual(obs2.category, "Federal Debt")
        self.assertAlmostEqual(obs2.amount, -3000.0)

        # Check third observation (2024-01-10, Taxes deposit)
        obs3 = observations[2]
        self.assertEqual(obs3.record_date, "2024-01-10")
        self.assertEqual(obs3.transaction_type, "deposits")
        self.assertEqual(obs3.category, "Taxes")
        self.assertAlmostEqual(obs3.amount, 5000.0)

        # Check fourth observation (2024-01-09, Expenditures withdrawal)
        obs4 = observations[3]
        self.assertEqual(obs4.record_date, "2024-01-09")
        self.assertEqual(obs4.transaction_type, "withdrawals")
        self.assertEqual(obs4.category, "Expenditures")
        self.assertAlmostEqual(obs4.amount, -1500.0)

        # Check fifth observation (2024-01-09, Federal Debt deposit)
        obs5 = observations[4]
        self.assertEqual(obs5.record_date, "2024-01-09")
        self.assertEqual(obs5.transaction_type, "deposits")
        self.assertEqual(obs5.category, "Federal Debt")
        self.assertAlmostEqual(obs5.amount, 2000.0)

        # Check sixth observation (2024-01-09, Other deposit)
        obs6 = observations[5]
        self.assertEqual(obs6.record_date, "2024-01-09")
        self.assertEqual(obs6.transaction_type, "deposits")
        self.assertEqual(obs6.category, "Other")
        self.assertAlmostEqual(obs6.amount, 1000.0)

        # Check seventh observation (2024-01-08, Taxes withdrawal)
        obs7 = observations[6]
        self.assertEqual(obs7.record_date, "2024-01-08")
        self.assertEqual(obs7.transaction_type, "withdrawals")
        self.assertEqual(obs7.category, "Taxes")
        self.assertAlmostEqual(obs7.amount, -1000.0)

        # Check eighth observation (2024-01-08, Expenditures withdrawal)
        obs8 = observations[7]
        self.assertEqual(obs8.record_date, "2024-01-08")
        self.assertEqual(obs8.transaction_type, "withdrawals")
        self.assertEqual(obs8.category, "Expenditures")
        self.assertAlmostEqual(obs8.amount, -2000.0)

        # Check ninth observation (2024-01-08, Expenditures deposit)
        obs9 = observations[8]
        self.assertEqual(obs9.record_date, "2024-01-08")
        self.assertEqual(obs9.transaction_type, "deposits")
        self.assertEqual(obs9.category, "Expenditures")
        self.assertAlmostEqual(obs9.amount, 500.0)

        # Check tenth observation (2024-01-08, Taxes deposit)
        obs10 = observations[9]
        self.assertEqual(obs10.record_date, "2024-01-08")
        self.assertEqual(obs10.transaction_type, "deposits")
        self.assertEqual(obs10.category, "Taxes")
        self.assertAlmostEqual(obs10.amount, 3000.0)

    def test_parse_empty_response(self) -> None:
        """Test parsing empty results from FiscalData API."""
        response_data = {"data": []}

        observations = parse_treasury_dts_cashflows_json(response_data)

        self.assertEqual(len(observations), 0)

    def test_parse_invalid_response_no_data(self) -> None:
        """Test parsing response with missing 'data' field."""
        response_data = {"meta": {"count": 0}}

        with self.assertRaises(ValueError) as ctx:
            parse_treasury_dts_cashflows_json(response_data)

        self.assertIn("Expected 'data' to be a list", str(ctx.exception))

    def test_parse_invalid_transaction_type(self) -> None:
        """Test parsing response with invalid transaction_type."""
        response_data = {
            "data": [
                {
                    "record_date": "2024-01-10",
                    "transaction_type": "invalid_type",
                    "transaction_catg": "Taxes",
                    "transaction_today_amt": "1000",
                }
            ]
        }

        with self.assertRaises(ValueError) as ctx:
            parse_treasury_dts_cashflows_json(response_data)

        self.assertIn("Unexpected transaction_type", str(ctx.exception))

    def test_parse_invalid_amount_format(self) -> None:
        """Test parsing response with invalid amount format."""
        response_data = {
            "data": [
                {
                    "record_date": "2024-01-10",
                    "transaction_type": "deposits",
                    "transaction_catg": "Taxes",
                    "transaction_today_amt": "not_a_number",
                }
            ]
        }

        with self.assertRaises(ValueError) as ctx:
            parse_treasury_dts_cashflows_json(response_data)

        self.assertIn("Invalid amount format", str(ctx.exception))


class TreasuryDtsCashflowsNormalizationTests(unittest.TestCase):
    def test_normalize_cashflow_observation(self) -> None:
        """Test normalizing a parsed cashflow observation into a SourceItem."""
        obs = ParsedTreasuryDtsCashflowObservation(
            record_date="2024-01-10",
            transaction_type="deposits",
            category="Taxes",
            amount=5000.0,
        )

        fetched_at = datetime(2024, 1, 11, 12, 0, 0, tzinfo=timezone.utc)
        fetch_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash"

        item = normalize_treasury_dts_cashflow_observation(
            parsed=obs,
            fetched_at=fetched_at,
            fetch_url=fetch_url,
        )

        self.assertEqual(item.source, SOURCE_NAME)
        self.assertEqual(item.external_id, "treasury_cashflow_deposits_Taxes_2024-01-10")
        self.assertEqual(item.published_at, datetime(2024, 1, 10, tzinfo=timezone.utc))
        self.assertEqual(
            item.title,
            "Treasury Cash Flow: 2024-01-10 - Deposit Taxes $+5000M",
        )
        self.assertIn("Deposit of $5000M in Taxes", item.summary)
        self.assertEqual(item.url, fetch_url)

        # Check metadata
        self.assertEqual(item.metadata["content_type"], "treasury_cashflow_observation")
        self.assertEqual(item.metadata["record_date"], "2024-01-10")
        self.assertEqual(item.metadata["transaction_type"], "deposits")
        self.assertEqual(item.metadata["category"], "Taxes")
        self.assertAlmostEqual(item.metadata["amount_millions"], 5000.0)
        self.assertEqual(item.metadata["currency"], "USD")
        self.assertEqual(item.metadata["unit"], "millions")

        # Check provenance
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.source, SOURCE_NAME)
        self.assertEqual(item.provenance.fetch_url, fetch_url)
        self.assertEqual(item.provenance.parser_version, "0.1.0")

        # Check freshness
        self.assertEqual(item.published_at, item.freshness.published_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)

    def test_normalize_withdrawal_observation(self) -> None:
        """Test normalizing a withdrawal observation (negative amount)."""
        obs = ParsedTreasuryDtsCashflowObservation(
            record_date="2024-01-10",
            transaction_type="withdrawals",
            category="Federal Debt",
            amount=-3000.0,
        )

        fetched_at = datetime(2024, 1, 11, 12, 0, 0, tzinfo=timezone.utc)
        fetch_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash"

        item = normalize_treasury_dts_cashflow_observation(
            parsed=obs,
            fetched_at=fetched_at,
            fetch_url=fetch_url,
        )

        self.assertEqual(item.external_id, "treasury_cashflow_withdrawals_Federal Debt_2024-01-10")
        self.assertEqual(
            item.title,
            "Treasury Cash Flow: 2024-01-10 - Withdrawal Federal Debt $-3000M",
        )
        self.assertIn("Withdrawal of $3000M in Federal Debt", item.summary)

    def test_normalize_invalid_record_date(self) -> None:
        """Test normalizing observation with invalid record_date."""
        obs = ParsedTreasuryDtsCashflowObservation(
            record_date="invalid-date",
            transaction_type="deposits",
            category="Taxes",
            amount=5000.0,
        )

        with self.assertRaises(ValueError) as ctx:
            normalize_treasury_dts_cashflow_observation(
                parsed=obs,
                fetched_at=datetime.now(timezone.utc),
                fetch_url="https://example.com",
            )

        self.assertIn("Invalid record_date format", str(ctx.exception))


class TreasuryDtsCashflowsWeeklyAggregationTests(unittest.TestCase):
    def test_aggregate_weekly_by_category(self) -> None:
        """Test weekly aggregation of cashflows by category."""
        # Use observations from the fixture (2024-01-08 to 2024-01-10)
        # These fall in week 2024-W02 (Jan 8-14, 2024)
        obs = [
            # 2024-01-10 (Thursday of week 2)
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "withdrawals", "Taxes", -2500),
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "withdrawals", "Federal Debt", -3000),
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "deposits", "Taxes", 5000),
            # 2024-01-09 (Wednesday of week 2)
            ParsedTreasuryDtsCashflowObservation("2024-01-09", "withdrawals", "Expenditures", -1500),
            ParsedTreasuryDtsCashflowObservation("2024-01-09", "deposits", "Federal Debt", 2000),
            ParsedTreasuryDtsCashflowObservation("2024-01-09", "deposits", "Other", 1000),
            # 2024-01-08 (Tuesday of week 2)
            ParsedTreasuryDtsCashflowObservation("2024-01-08", "withdrawals", "Taxes", -1000),
            ParsedTreasuryDtsCashflowObservation("2024-01-08", "withdrawals", "Expenditures", -2000),
            ParsedTreasuryDtsCashflowObservation("2024-01-08", "deposits", "Expenditures", 500),
            ParsedTreasuryDtsCashflowObservation("2024-01-08", "deposits", "Taxes", 3000),
        ]

        result = aggregate_cashflows_weekly_by_category(obs)

        # Should have one week (2024-W02)
        self.assertEqual(len(result), 1)
        self.assertIn("2024-W02", result)

        # Check each category's totals
        week_data = result["2024-W02"]

        # Taxes: deposits 5000+3000=8000, withdrawals -2500-1000=-3500
        self.assertIn("Taxes", week_data)
        self.assertAlmostEqual(week_data["Taxes"]["deposits"], 8000.0)
        self.assertAlmostEqual(week_data["Taxes"]["withdrawals"], -3500.0)

        # Federal Debt: deposits 2000, withdrawals -3000
        self.assertIn("Federal Debt", week_data)
        self.assertAlmostEqual(week_data["Federal Debt"]["deposits"], 2000.0)
        self.assertAlmostEqual(week_data["Federal Debt"]["withdrawals"], -3000.0)

        # Expenditures: deposits 500, withdrawals -1500-2000=-3500
        self.assertIn("Expenditures", week_data)
        self.assertAlmostEqual(week_data["Expenditures"]["deposits"], 500.0)
        self.assertAlmostEqual(week_data["Expenditures"]["withdrawals"], -3500.0)

        # Other: deposits 1000, no withdrawals
        self.assertIn("Other", week_data)
        self.assertAlmostEqual(week_data["Other"]["deposits"], 1000.0)
        # withdrawals should not be present for Other (no withdrawals in data)
        self.assertNotIn("withdrawals", week_data["Other"])

    def test_aggregate_separates_deposits_and_withdrawals(self) -> None:
        """Test that weekly aggregation keeps deposits and withdrawals separate."""
        obs = [
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "deposits", "Taxes", 5000),
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "withdrawals", "Taxes", -2500),
        ]

        result = aggregate_cashflows_weekly_by_category(obs)

        # Verify both are present separately, not netted
        week_data = result["2024-W02"]
        self.assertIn("deposits", week_data["Taxes"])
        self.assertIn("withdrawals", week_data["Taxes"])

        # They should be separate values
        self.assertAlmostEqual(week_data["Taxes"]["deposits"], 5000.0)
        self.assertAlmostEqual(week_data["Taxes"]["withdrawals"], -2500.0)

        # AC#3 requirement: deposits != withdrawals (separate, not netted)
        self.assertNotEqual(week_data["Taxes"]["deposits"], week_data["Taxes"]["withdrawals"])

    def test_aggregate_multiple_weeks(self) -> None:
        """Test weekly aggregation across multiple weeks."""
        obs = [
            # Week 2024-W02 (Jan 8-14)
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "deposits", "Taxes", 5000),
            # Week 2024-W03 (Jan 15-21)
            ParsedTreasuryDtsCashflowObservation("2024-01-15", "deposits", "Taxes", 6000),
        ]

        result = aggregate_cashflows_weekly_by_category(obs)

        # Should have two weeks
        self.assertEqual(len(result), 2)
        self.assertIn("2024-W02", result)
        self.assertIn("2024-W03", result)

        # Each week should have its own totals
        self.assertAlmostEqual(result["2024-W02"]["Taxes"]["deposits"], 5000.0)
        self.assertAlmostEqual(result["2024-W03"]["Taxes"]["deposits"], 6000.0)

    def test_aggregate_removes_zero_entries(self) -> None:
        """Test that aggregation removes categories with zero totals."""
        obs = [
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "deposits", "Taxes", 5000),
            # Federal Debt has only withdrawals (no deposits), so deposits=0 should not appear
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "withdrawals", "Federal Debt", -3000),
        ]

        result = aggregate_cashflows_weekly_by_category(obs)

        week_data = result["2024-W02"]

        # Taxes should have deposits present
        self.assertIn("deposits", week_data["Taxes"])

        # Federal Debt should have withdrawals present, but not deposits (which would be 0)
        self.assertIn("withdrawals", week_data["Federal Debt"])
        # deposits key should not be present for Federal Debt since it's 0
        self.assertNotIn("deposits", week_data["Federal Debt"])

    def test_aggregate_empty_observations(self) -> None:
        """Test weekly aggregation with empty observations."""
        result = aggregate_cashflows_weekly_by_category([])

        self.assertEqual(len(result), 0)

    def test_aggregate_invalid_record_date(self) -> None:
        """Test weekly aggregation with invalid record_date."""
        obs = [
            ParsedTreasuryDtsCashflowObservation("invalid-date", "deposits", "Taxes", 5000),
        ]

        with self.assertRaises(ValueError) as ctx:
            aggregate_cashflows_weekly_by_category(obs)

        self.assertIn("Invalid record_date format", str(ctx.exception))

    def test_aggregate_unknown_transaction_type(self) -> None:
        """Test weekly aggregation with unknown transaction type."""
        obs = [
            ParsedTreasuryDtsCashflowObservation("2024-01-10", "unknown", "Taxes", 5000),
        ]

        with self.assertRaises(ValueError) as ctx:
            aggregate_cashflows_weekly_by_category(obs)

        self.assertIn("Unknown transaction_type", str(ctx.exception))


class TreasuryDtsCashflowsConnectorTests(unittest.IsolatedAsyncioTestCase):
    def test_connector_metadata(self) -> None:
        """Test connector name and metadata."""
        connector = TreasuryDtsCashflowsConnector(
            transport=_FakeTransport(HttpResponse(200, "https://example.com", {}, b"{}"))
        )

        self.assertEqual(connector.name, CONNECTOR_NAME)
        self.assertEqual(connector.source, SOURCE_NAME)

    async def test_fetch_page_success(self) -> None:
        """Test successful fetch of cashflow data."""
        import json

        # Load fixture
        fixture_data = json.loads((FIXTURES_DIR / "cashflows.json").read_text(encoding="utf-8"))

        # Create fake transport
        response = HttpResponse(
            status_code=200,
            url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash",
            headers={"Content-Type": "application/json"},
            body=json.dumps(fixture_data).encode("utf-8"),
        )
        transport = _FakeTransport(response)

        # Create connector and fetch
        connector = TreasuryDtsCashflowsConnector(transport=transport)
        page_result = await connector.fetch_page()

        # Check results
        self.assertEqual(len(page_result.items), 10)
        self.assertFalse(page_result.has_more)
        self.assertIsNone(page_result.next_cursor)

        # Check that a request was made
        self.assertEqual(len(transport.requests), 1)

    async def test_fetch_page_500_error(self) -> None:
        """Test 500 error handling."""
        response = HttpResponse(
            status_code=500,
            url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash",
            headers={},
            body=b"Internal Server Error",
        )
        transport = _FakeTransport(response)

        connector = TreasuryDtsCashflowsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as ctx:
            await connector.fetch_page()

        self.assertIn("500", str(ctx.exception))

    async def test_fetch_page_404_error(self) -> None:
        """Test 404 error handling."""
        response = HttpResponse(
            status_code=404,
            url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash",
            headers={},
            body=b"Not Found",
        )
        transport = _FakeTransport(response)

        connector = TreasuryDtsCashflowsConnector(transport=transport)

        with self.assertRaises(ValueError) as ctx:
            await connector.fetch_page()

        self.assertIn("404", str(ctx.exception))

    async def test_fetch_page_invalid_json(self) -> None:
        """Test invalid JSON response handling."""
        response = HttpResponse(
            status_code=200,
            url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash",
            headers={"Content-Type": "application/json"},
            body=b"not valid json",
        )
        transport = _FakeTransport(response)

        connector = TreasuryDtsCashflowsConnector(transport=transport)

        with self.assertRaises(ValueError) as ctx:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(ctx.exception))

    async def test_fetch_page_empty_results(self) -> None:
        """Test handling of empty results (e.g., on holidays)."""
        response = HttpResponse(
            status_code=200,
            url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash",
            headers={"Content-Type": "application/json"},
            body=b'{"data": [], "meta": {"count": 0}}',
        )
        transport = _FakeTransport(response)

        connector = TreasuryDtsCashflowsConnector(transport=transport)
        page_result = await connector.fetch_page()

        # Should return empty PageResult without error
        self.assertEqual(len(page_result.items), 0)
        self.assertFalse(page_result.has_more)
        self.assertIsNone(page_result.next_cursor)


if __name__ == "__main__":
    unittest.main()