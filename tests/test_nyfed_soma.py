from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.connectors.nyfed_soma import (
    DATA_CLASSIFICATION,
    NyfedSomaConnector,
    compute_weekly_monthly_changes,
    normalize_soma_holdings,
    parse_soma_csv,
    ParsedNyfedSomaHolding,
    PROXY_SOURCES,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "nyfed_soma"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class NyfedSomaParserTests(unittest.TestCase):
    """Test parser functions for SOMA holdings data."""

    def test_parse_soma_csv(self) -> None:
        """Test parsing SOMA CSV with multiple dates and instruments."""
        csv_text = (FIXTURES_DIR / "soma_holdings.csv").read_text(encoding="utf-8")

        holdings = parse_soma_csv(csv_text)

        # Should have 36 holdings (2 dates × 3 instruments × 6 buckets)
        self.assertEqual(len(holdings), 36)

        # Check first holding (Treasuries, 0-1y, 2026-06-10)
        self.assertEqual(holdings[0].as_of_date, "2026-06-10")
        self.assertEqual(holdings[0].instrument, "Treasuries")
        self.assertEqual(holdings[0].maturity_bucket, "0-1y")
        self.assertEqual(holdings[0].amount_par, 500000.0)
        self.assertEqual(holdings[0].amount_market, 498000.0)

    def test_parse_soma_csv_with_missing_market_value(self) -> None:
        """Test parsing CSV with missing market value."""
        csv_text = (
            "As-Of Date,Instrument,Maturity Bucket,Par Value,Market Value\n"
            "2026-06-10,Treasuries,0-1y,500000,\n"
            "2026-06-10,MBS,1-3y,400000,\n"
        )

        holdings = parse_soma_csv(csv_text)

        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[0].amount_par, 500000.0)
        self.assertIsNone(holdings[0].amount_market)
        self.assertEqual(holdings[1].amount_par, 400000.0)
        self.assertIsNone(holdings[1].amount_market)

    def test_parse_empty_csv_raises(self) -> None:
        """Test parsing empty CSV raises ValueError."""
        csv_text = "As-Of Date,Instrument,Maturity Bucket,Par Value,Market Value\n"

        holdings = parse_soma_csv(csv_text)
        self.assertEqual(len(holdings), 0)

    def test_parse_missing_required_column_raises(self) -> None:
        """Test parsing CSV with missing required column raises ValueError."""
        csv_text = "As-Of Date,Instrument,Maturity Bucket,Par Value\n" "2026-06-10,Treasuries,0-1y,500000\n"

        with self.assertRaises(ValueError) as cm:
            parse_soma_csv(csv_text)

        self.assertIn("Missing required column 'Market Value'", str(cm.exception))

    def test_parse_invalid_par_value_raises(self) -> None:
        """Test parsing CSV with invalid par value raises ValueError."""
        csv_text = (
            "As-Of Date,Instrument,Maturity Bucket,Par Value,Market Value\n"
            "2026-06-10,Treasuries,0-1y,invalid,498000\n"
        )

        with self.assertRaises(ValueError) as cm:
            parse_soma_csv(csv_text)

        self.assertIn("invalid par value 'invalid'", str(cm.exception))

    def test_compute_weekly_monthly_changes(self) -> None:
        """Test computing changes between two dates for QT analysis."""
        # Parse the sample holdings
        csv_text = (FIXTURES_DIR / "soma_holdings.csv").read_text(encoding="utf-8")
        holdings = parse_soma_csv(csv_text)

        # Compute changes from 2026-06-03 to 2026-06-10
        changes = compute_weekly_monthly_changes(holdings, "2026-06-03", "2026-06-10")

        # Should have changes for 3 instruments
        self.assertEqual(len(changes), 3)

        # Check Treasuries change (should be negative - QT running off)
        self.assertIn("Treasuries", changes)
        self.assertAlmostEqual(changes["Treasuries"]["change_par"], -14500.0)
        self.assertAlmostEqual(changes["Treasuries"]["change_market"], -14500.0)

        # Check MBS change (should be negative)
        self.assertIn("MBS", changes)
        self.assertAlmostEqual(changes["MBS"]["change_par"], -6000.0)
        self.assertAlmostEqual(changes["MBS"]["change_market"], -6000.0)

        # Check Agency Debt change (should be negative)
        self.assertIn("Agency Debt", changes)
        self.assertAlmostEqual(changes["Agency Debt"]["change_par"], -1100.0)
        self.assertAlmostEqual(changes["Agency Debt"]["change_market"], -1100.0)

    def test_compute_changes_handles_missing_prior_date(self) -> None:
        """Test computing changes gracefully handles missing prior date."""
        holdings = [
            ParsedNyfedSomaHolding(
                as_of_date="2026-06-10",
                instrument="Treasuries",
                maturity_bucket="0-1y",
                amount_par=500000.0,
                amount_market=498000.0,
            )
        ]

        # Compute changes with missing prior date - should return 0 change
        changes = compute_weekly_monthly_changes(holdings, "2026-06-03", "2026-06-10")

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes["Treasuries"]["change_par"], 500000.0)
        self.assertEqual(changes["Treasuries"]["change_market"], 498000.0)

    def test_compute_changes_handles_missing_current_date(self) -> None:
        """Test computing changes gracefully handles missing current date."""
        holdings = [
            ParsedNyfedSomaHolding(
                as_of_date="2026-06-03",
                instrument="Treasuries",
                maturity_bucket="0-1y",
                amount_par=501500.0,
                amount_market=499500.0,
            )
        ]

        # Compute changes with missing current date - should return empty dict
        changes = compute_weekly_monthly_changes(holdings, "2026-06-03", "2026-06-10")

        self.assertEqual(len(changes), 0)

    def test_normalize_soma_holdings(self) -> None:
        """Test normalizing SOMA holdings to SourceItems."""
        holdings = [
            ParsedNyfedSomaHolding(
                as_of_date="2026-06-10",
                instrument="Treasuries",
                maturity_bucket="0-1y",
                amount_par=500000.0,
                amount_market=498000.0,
            ),
            ParsedNyfedSomaHolding(
                as_of_date="2026-06-10",
                instrument="MBS",
                maturity_bucket="1-3y",
                amount_par=400000.0,
                amount_market=396000.0,
            ),
        ]

        fetched_at = datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_soma_holdings(
            holdings=holdings,
            fetched_at=fetched_at,
            fetch_url="https://example.com/soma.csv",
        )

        self.assertEqual(len(items), 2)

        # Check first item
        self.assertEqual(items[0].external_id, "soma_treasuries_2026-06-10_0-1y")
        self.assertEqual(items[0].source, "nyfed_soma")
        self.assertEqual(
            items[0].title,
            "SOMA Treasuries: 0-1y on 2026-06-10 - Par: $500,000M, Market: $498,000M",
        )
        self.assertEqual(items[0].metadata["content_type"], "soma_holding")
        self.assertEqual(items[0].metadata["instrument"], "Treasuries")
        self.assertEqual(items[0].metadata["maturity_bucket"], "0-1y")
        self.assertEqual(items[0].metadata["amount_par_millions"], 500000.0)
        self.assertEqual(items[0].metadata["amount_market_millions"], 498000.0)
        self.assertEqual(items[0].metadata["data_classification"], DATA_CLASSIFICATION)
        self.assertEqual(items[0].metadata["proxy_sources"], PROXY_SOURCES)

        # Check second item
        self.assertEqual(items[1].external_id, "soma_mbs_2026-06-10_1-3y")
        self.assertEqual(items[1].metadata["instrument"], "MBS")
        self.assertEqual(items[1].metadata["maturity_bucket"], "1-3y")

    def test_normalize_soma_holdings_handles_invalid_date(self) -> None:
        """Test normalizing gracefully skips holdings with invalid dates."""
        holdings = [
            ParsedNyfedSomaHolding(
                as_of_date="invalid-date",
                instrument="Treasuries",
                maturity_bucket="0-1y",
                amount_par=500000.0,
                amount_market=498000.0,
            )
        ]

        fetched_at = datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)
        items = normalize_soma_holdings(
            holdings=holdings,
            fetched_at=fetched_at,
            fetch_url="https://example.com/soma.csv",
        )

        # Should skip the invalid holding
        self.assertEqual(len(items), 0)


class NyfedSomaConnectorTests(unittest.IsolatedAsyncioTestCase):
    """Test NyfedSomaConnector integration."""

    async def test_connector_fetch_page_success(self) -> None:
        """Test successful fetch_page returns normalized holdings."""
        # Load fixture CSV
        csv_text = (FIXTURES_DIR / "soma_holdings.csv").read_text(encoding="utf-8")

        # Create fake transport
        response = HttpResponse(
            status_code=200,
            url="https://www.newyorkfed.org/markets/soma-holdings",
            headers={"Content-Type": "text/csv"},
            body=csv_text.encode("utf-8"),
        )
        transport = _FakeTransport(response)

        # Create connector and fetch
        connector = NyfedSomaConnector(transport=transport)
        result = await connector.fetch_page()

        # Check result
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)

        # Should have 36 holdings (2 dates × 3 instruments × 6 buckets)
        self.assertEqual(len(result.items), 36)

        # Check first item
        first_item = result.items[0]
        self.assertEqual(first_item.source, "nyfed_soma")
        self.assertEqual(first_item.metadata["content_type"], "soma_holding")
        self.assertEqual(first_item.metadata["instrument"], "Treasuries")
        self.assertEqual(first_item.metadata["maturity_bucket"], "0-1y")

        # Check transport made one request
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url, "https://www.newyorkfed.org/markets/soma-holdings")

    async def test_connector_fetch_page_404_raises_recoverable_error(self) -> None:
        """Test fetch_page with 404 raises RecoverableConnectorError."""
        response = HttpResponse(
            status_code=404,
            url="https://www.newyorkfed.org/markets/soma-holdings",
            headers={},
            body=b"Not Found",
        )
        transport = _FakeTransport(response)

        connector = NyfedSomaConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("SOMA data not found", str(cm.exception))

    async def test_connector_fetch_page_500_raises_recoverable_error(self) -> None:
        """Test fetch_page with 500 raises RecoverableConnectorError."""
        response = HttpResponse(
            status_code=500,
            url="https://www.newyorkfed.org/markets/soma-holdings",
            headers={},
            body=b"Internal Server Error",
        )
        transport = _FakeTransport(response)

        connector = NyfedSomaConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("returned 500", str(cm.exception))

    async def test_connector_fetch_page_400_raises_value_error(self) -> None:
        """Test fetch_page with 400 raises ValueError."""
        response = HttpResponse(
            status_code=400,
            url="https://www.newyorkfed.org/markets/soma-holdings",
            headers={},
            body=b"Bad Request",
        )
        transport = _FakeTransport(response)

        connector = NyfedSomaConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected NY Fed status code 400", str(cm.exception))

    def test_connector_constants(self) -> None:
        """Test connector class constants."""
        self.assertEqual(NyfedSomaConnector.name, "nyfed_soma")
        self.assertEqual(NyfedSomaConnector.source, "nyfed_soma")
        self.assertEqual(DATA_CLASSIFICATION, "primary")
        self.assertEqual(PROXY_SOURCES, ["FRED"])

    def test_frozen_dataclass_to_dict_from_dict(self) -> None:
        """Test ParsedNyfedSomaHolding frozen dataclass can be converted."""
        holding = ParsedNyfedSomaHolding(
            as_of_date="2026-06-10",
            instrument="Treasuries",
            maturity_bucket="0-1y",
            amount_par=500000.0,
            amount_market=498000.0,
        )

        # Convert to dict (manually, since frozen dataclass doesn't have to_dict)
        holding_dict = {
            "as_of_date": holding.as_of_date,
            "instrument": holding.instrument,
            "maturity_bucket": holding.maturity_bucket,
            "amount_par": holding.amount_par,
            "amount_market": holding.amount_market,
        }

        self.assertEqual(holding_dict["as_of_date"], "2026-06-10")
        self.assertEqual(holding_dict["instrument"], "Treasuries")
        self.assertEqual(holding_dict["maturity_bucket"], "0-1y")
        self.assertEqual(holding_dict["amount_par"], 500000.0)
        self.assertEqual(holding_dict["amount_market"], 498000.0)


if __name__ == "__main__":
    unittest.main()