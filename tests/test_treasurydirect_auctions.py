from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.treasurydirect_auctions import (
    ANNOUNCED_URL,
    AUCTIONED_URL,
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    normalize_treasurydirect_auction_record,
    parse_treasurydirect_announced_securities,
    parse_treasurydirect_auctioned_securities,
    ParsedTreasurydirectAuctionRecord,
    SOURCE_NAME,
    TreasurydirectAuctionsConnector,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "treasurydirect_auctions"


class _FakeTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if not self.responses:
            raise RuntimeError("No more responses available")
        return self.responses.pop(0)


class TreasurydirectAuctionsParserTests(unittest.TestCase):
    def test_parse_announced_securities(self) -> None:
        """Test parsing announced securities response (AC#1, AC#3)."""
        import json

        response_data = json.loads(
            (FIXTURES_DIR / "announced_and_auctioned_response.json").read_text(
                encoding="utf-8"
            )
        )

        records = parse_treasurydirect_announced_securities(response_data, ANNOUNCED_URL)

        self.assertEqual(len(records), 3)

        # Check first announced record (2-Year Note)
        record1 = records[0]
        self.assertEqual(record1.status, "announced")
        self.assertEqual(record1.cusip, "91282CAZ5")
        self.assertEqual(record1.security_type, "Note")
        self.assertEqual(record1.auction_date, "2026-06-22")
        self.assertEqual(record1.maturity_date, "2028-06-30")
        self.assertAlmostEqual(record1.offering_amount, 54000.0)
        self.assertIsNone(record1.high_rate)  # Not available for announced
        self.assertIsNone(record1.accepted_amount)  # Not available for announced
        self.assertEqual(record1.security_term, "2-Year")
        self.assertFalse(record1.is_refunding)

        # Check second announced record (13-Week Bill)
        record2 = records[1]
        self.assertEqual(record2.status, "announced")
        self.assertEqual(record2.cusip, "912797KZ0")
        self.assertEqual(record2.security_type, "Bill")
        self.assertEqual(record2.auction_date, "2026-06-23")
        self.assertEqual(record2.maturity_date, "2026-09-25")
        self.assertAlmostEqual(record2.offering_amount, 75000.0)
        self.assertEqual(record2.security_term, "13-Week")

        # Check third announced record (30-Year Bond)
        record3 = records[2]
        self.assertEqual(record3.status, "announced")
        self.assertEqual(record3.cusip, "912810SL7")
        self.assertEqual(record3.security_type, "Bond")
        self.assertEqual(record3.auction_date, "2026-06-24")
        self.assertEqual(record3.maturity_date, "2056-05-15")
        self.assertAlmostEqual(record3.offering_amount, 22000.0)
        self.assertEqual(record3.security_term, "30-Year")

    def test_parse_auctioned_securities(self) -> None:
        """Test parsing auctioned securities response (AC#1, AC#3)."""
        import json

        response_data = json.loads(
            (FIXTURES_DIR / "announced_and_auctioned_response.json").read_text(
                encoding="utf-8"
            )
        )

        records = parse_treasurydirect_auctioned_securities(response_data, AUCTIONED_URL)

        self.assertEqual(len(records), 4)

        # Check first auctioned record (2-Year Note)
        record1 = records[0]
        self.assertEqual(record1.status, "auctioned")
        self.assertEqual(record1.cusip, "91282CAX8")
        self.assertEqual(record1.security_type, "Note")
        self.assertEqual(record1.auction_date, "2026-06-15")
        self.assertEqual(record1.maturity_date, "2028-06-30")
        self.assertAlmostEqual(record1.offering_amount, 54000.0)
        self.assertAlmostEqual(record1.high_rate, 4.65)
        self.assertAlmostEqual(record1.accepted_amount, 54000.0)
        self.assertEqual(record1.security_term, "2-Year")
        self.assertFalse(record1.is_refunding)

        # Check second auctioned record (13-Week Bill)
        record2 = records[1]
        self.assertEqual(record2.status, "auctioned")
        self.assertEqual(record2.cusip, "912797KY8")
        self.assertEqual(record2.security_type, "Bill")
        self.assertEqual(record2.auction_date, "2026-06-14")
        self.assertAlmostEqual(record2.high_rate, 5.23)
        self.assertAlmostEqual(record2.accepted_amount, 75000.0)
        self.assertEqual(record2.security_term, "13-Week")

        # Check third auctioned record (TIPS)
        record3 = records[2]
        self.assertEqual(record3.status, "auctioned")
        self.assertEqual(record3.cusip, "912828Z45")
        self.assertEqual(record3.security_type, "TIPS")
        self.assertAlmostEqual(record3.high_rate, 1.875)
        self.assertEqual(record3.security_term, "10-Year")

        # Check fourth auctioned record (Refunding Note, AC#3)
        record4 = records[3]
        self.assertEqual(record4.status, "auctioned")
        self.assertEqual(record4.cusip, "91282CBY2")
        self.assertEqual(record4.security_type, "Note")
        self.assertEqual(record4.security_term, "6-Month")
        self.assertTrue(record4.is_refunding)  # Refunding flag

    def test_parse_empty_response(self) -> None:
        """Test parsing empty results from TreasuryDirect API (AC#2)."""
        import json

        announced_data = json.loads(
            (FIXTURES_DIR / "empty_response.json").read_text(encoding="utf-8")
        )
        auctioned_data = json.loads(
            (FIXTURES_DIR / "empty_response.json").read_text(encoding="utf-8")
        )

        announced_records = parse_treasurydirect_announced_securities(announced_data, ANNOUNCED_URL)
        auctioned_records = parse_treasurydirect_auctioned_securities(auctioned_data, AUCTIONED_URL)

        self.assertEqual(len(announced_records), 0)
        self.assertEqual(len(auctioned_records), 0)

    def test_parse_invalid_data_format_raises(self) -> None:
        """Test that parsing invalid data format raises ValueError."""
        invalid_response = {"announcedSecurities": "not a list"}

        with self.assertRaises(ValueError) as cm:
            parse_treasurydirect_announced_securities(invalid_response, ANNOUNCED_URL)

        self.assertIn("Expected 'announcedSecurities' to be a list", str(cm.exception))

    def test_parse_missing_cusip_raises(self) -> None:
        """Test that parsing missing cusip raises ValueError."""
        invalid_response = {
            "announcedSecurities": [
                {
                    "securityType": "Note",
                    "auctionDate": "2026-06-22",
                    "maturityDate": "2028-06-30",
                    "offeringAmount": 54000,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_treasurydirect_announced_securities(invalid_response, ANNOUNCED_URL)

        self.assertIn("Invalid or missing cusip", str(cm.exception))

    def test_parse_invalid_offering_amount_raises(self) -> None:
        """Test that parsing invalid offering amount raises ValueError."""
        invalid_response = {
            "announcedSecurities": [
                {
                    "cusip": "91282CAZ5",
                    "securityType": "Note",
                    "auctionDate": "2026-06-22",
                    "maturityDate": "2028-06-30",
                    "offeringAmount": "not_a_number",
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_treasurydirect_announced_securities(invalid_response, ANNOUNCED_URL)

        self.assertIn("Invalid offeringAmount", str(cm.exception))

    def test_parse_auctioned_with_high_rate(self) -> None:
        """Test parsing auctioned securities with high rate (AC#1)."""
        response_data = {
            "auctionedSecurities": [
                {
                    "securityType": "Bill",
                    "cusip": "912797KY8",
                    "auctionDate": "2026-06-14",
                    "issueDate": "2026-06-17",
                    "maturityDate": "2026-09-15",
                    "offeringAmount": 75000,
                    "acceptedAmount": 75000,
                    "highRate": 5.23,
                    "lowRate": 5.21,
                    "medianRate": 5.22,
                    "securityTerm": "13-Week",
                }
            ]
        }

        records = parse_treasurydirect_auctioned_securities(response_data, AUCTIONED_URL)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.status, "auctioned")
        self.assertAlmostEqual(record.high_rate, 5.23)
        self.assertAlmostEqual(record.accepted_amount, 75000.0)

    def test_normalize_announced_record(self) -> None:
        """Test normalizing an announced auction record (AC#1)."""
        parsed = ParsedTreasurydirectAuctionRecord(
            status="announced",
            cusip="91282CAZ5",
            security_type="Note",
            announcement_date=None,
            auction_date="2026-06-22",
            maturity_date="2028-06-30",
            offering_amount=54000.0,
            high_rate=None,
            accepted_amount=None,
            security_term="2-Year",
            is_refunding=False,
            url=ANNOUNCED_URL,
        )
        fetched_at = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

        item = normalize_treasurydirect_auction_record(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=ANNOUNCED_URL,
        )

        self.assertEqual(item.external_id, "treasury_auction_announced_91282CAZ5_2026-06-22")
        self.assertEqual(item.source, SOURCE_NAME)
        self.assertEqual(item.published_at, datetime(2026, 6, 22, tzinfo=timezone.utc))
        self.assertIn("[ANNOUNCED]", item.title)
        self.assertIn("Note", item.title)
        self.assertIn("91282CAZ5", item.title)
        self.assertIn("(2-Year)", item.title)
        self.assertIn("Announced", item.summary)
        self.assertIn("cusip: 91282CAZ5", item.summary)
        self.assertIn("date: 2026-06-22", item.summary)
        self.assertIn("maturity: 2028-06-30", item.summary)
        self.assertIn("offering: $54,000M", item.summary)
        self.assertNotIn("high rate", item.summary)

        # Check metadata
        self.assertEqual(item.metadata["content_type"], "treasury_auction")
        self.assertEqual(item.metadata["status"], "announced")
        self.assertEqual(item.metadata["cusip"], "91282CAZ5")
        self.assertEqual(item.metadata["security_type"], "Note")
        self.assertEqual(item.metadata["auction_date"], "2026-06-22")
        self.assertEqual(item.metadata["maturity_date"], "2028-06-30")
        self.assertAlmostEqual(item.metadata["offering_amount_millions"], 54000.0)
        self.assertEqual(item.metadata["currency"], "USD")
        self.assertEqual(item.metadata["unit"], "millions")
        self.assertNotIn("high_rate_percent", item.metadata)
        self.assertNotIn("is_refunding", item.metadata)

        # Check provenance
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.source, SOURCE_NAME)

        # Check freshness
        self.assertEqual(item.freshness.published_at, datetime(2026, 6, 22, tzinfo=timezone.utc))
        self.assertEqual(item.freshness.first_seen_at, fetched_at)
        self.assertEqual(item.freshness.fetched_at, fetched_at)
        self.assertFalse(item.freshness.is_stale)
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)

    def test_normalize_auctioned_record_with_high_rate(self) -> None:
        """Test normalizing an auctioned record with high rate (AC#1)."""
        parsed = ParsedTreasurydirectAuctionRecord(
            status="auctioned",
            cusip="91282CAX8",
            security_type="Note",
            announcement_date=None,
            auction_date="2026-06-15",
            maturity_date="2028-06-30",
            offering_amount=54000.0,
            high_rate=4.65,
            accepted_amount=54000.0,
            security_term="2-Year",
            is_refunding=False,
            url=AUCTIONED_URL,
        )
        fetched_at = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

        item = normalize_treasurydirect_auction_record(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=AUCTIONED_URL,
        )

        self.assertEqual(item.external_id, "treasury_auction_auctioned_91282CAX8_2026-06-15")
        self.assertIn("[AUCTIONED]", item.title)
        self.assertIn("high rate: 4.650%", item.summary)
        self.assertIn("accepted: $54,000M", item.summary)

        # Check metadata includes high rate
        self.assertAlmostEqual(item.metadata["high_rate_percent"], 4.65)
        self.assertAlmostEqual(item.metadata["accepted_amount_millions"], 54000.0)

    def test_normalize_refunding_record(self) -> None:
        """Test normalizing a refunding/reopening record (AC#3)."""
        parsed = ParsedTreasurydirectAuctionRecord(
            status="auctioned",
            cusip="91282CBY2",
            security_type="Note",
            announcement_date=None,
            auction_date="2026-06-12",
            maturity_date="2026-12-15",
            offering_amount=65000.0,
            high_rate=5.42,
            accepted_amount=65000.0,
            security_term="6-Month",
            is_refunding=True,  # Refunding flag
            url=AUCTIONED_URL,
        )
        fetched_at = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

        item = normalize_treasurydirect_auction_record(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=AUCTIONED_URL,
        )

        self.assertIn("[REFUNDING/REOPENING]", item.summary)
        self.assertTrue(item.metadata["is_refunding"])
        self.assertEqual(item.metadata["refunding_note"], "This is a refunding/reopening auction")

    def test_normalize_invalid_auction_date_format_raises(self) -> None:
        """Test that normalizing invalid auction_date format raises ValueError."""
        parsed = ParsedTreasurydirectAuctionRecord(
            status="announced",
            cusip="91282CAZ5",
            security_type="Note",
            announcement_date=None,
            auction_date="invalid-date",
            maturity_date="2028-06-30",
            offering_amount=54000.0,
            high_rate=None,
            accepted_amount=None,
            security_term="2-Year",
            is_refunding=False,
            url=ANNOUNCED_URL,
        )
        fetched_at = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_treasurydirect_auction_record(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url=ANNOUNCED_URL,
            )

        self.assertIn("Invalid auction_date format", str(cm.exception))


class TreasurydirectAuctionsConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_returns_auction_records(self) -> None:
        """Test that fetch_page returns auction records (AC#1, AC#3)."""
        import json

        response_data = (
            FIXTURES_DIR / "announced_and_auctioned_response.json"
        ).read_text(encoding="utf-8")

        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=200,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=response_data.encode("utf-8"),
                ),
                HttpResponse(
                    status_code=200,
                    url=AUCTIONED_URL,
                    headers={"Content-Type": "application/json"},
                    body=response_data.encode("utf-8"),
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 7)  # 3 announced + 4 auctioned

        # Verify status distinction
        announced_items = [item for item in result.items if item.metadata["status"] == "announced"]
        auctioned_items = [item for item in result.items if item.metadata["status"] == "auctioned"]
        self.assertEqual(len(announced_items), 3)
        self.assertEqual(len(auctioned_items), 4)

        # Check announced item
        announced = announced_items[0]
        self.assertEqual(announced.source, SOURCE_NAME)
        self.assertIn("[ANNOUNCED]", announced.title)
        self.assertEqual(announced.metadata["security_type"], "Note")
        self.assertIsNone(announced.metadata.get("high_rate_percent"))

        # Check auctioned item
        auctioned = auctioned_items[0]
        self.assertEqual(auctioned.source, SOURCE_NAME)
        self.assertIn("[AUCTIONED]", auctioned.title)
        self.assertEqual(auctioned.metadata["security_type"], "Note")
        self.assertIsNotNone(auctioned.metadata.get("high_rate_percent"))

        # Check refunding item
        refunding_items = [
            item for item in result.items if item.metadata.get("is_refunding")
        ]
        self.assertEqual(len(refunding_items), 1)
        self.assertTrue(refunding_items[0].metadata["is_refunding"])
        self.assertIn("[REFUNDING/REOPENING]", refunding_items[0].summary)

        # Verify request parameters
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(transport.requests[0].method, "GET")
        self.assertEqual(transport.requests[0].url, ANNOUNCED_URL)
        self.assertEqual(transport.requests[0].headers["Accept"], "application/json")
        self.assertEqual(transport.requests[1].method, "GET")
        self.assertEqual(transport.requests[1].url, AUCTIONED_URL)
        self.assertEqual(transport.requests[1].headers["Accept"], "application/json")

    async def test_fetch_page_empty_results(self) -> None:
        """Test that fetch_page returns empty results (AC#2)."""
        import json

        empty_response = (FIXTURES_DIR / "empty_response.json").read_text(
            encoding="utf-8"
        )

        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=200,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=empty_response.encode("utf-8"),
                ),
                HttpResponse(
                    status_code=200,
                    url=AUCTIONED_URL,
                    headers={"Content-Type": "application/json"},
                    body=empty_response.encode("utf-8"),
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(result.items, ())

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=503,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "service unavailable"}',
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_4xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 4xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=404,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "not found"}',
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("404", str(cm.exception))

    async def test_fetch_page_3xx_raises_value_error(self) -> None:
        """Test that fetch_page with 3xx raises ValueError."""
        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=301,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=b"",
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected TreasuryDirect status code 301", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=200,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=b"not valid json",
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_auction_records_have_required_fields(self) -> None:
        """Test that auction records include all required normalized fields (AC#1)."""
        import json

        response_data = (
            FIXTURES_DIR / "announced_and_auctioned_response.json"
        ).read_text(encoding="utf-8")

        transport = _FakeTransport(
            [
                HttpResponse(
                    status_code=200,
                    url=ANNOUNCED_URL,
                    headers={"Content-Type": "application/json"},
                    body=response_data.encode("utf-8"),
                ),
                HttpResponse(
                    status_code=200,
                    url=AUCTIONED_URL,
                    headers={"Content-Type": "application/json"},
                    body=response_data.encode("utf-8"),
                ),
            ]
        )
        connector = TreasurydirectAuctionsConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 7)
        for item in result.items:
            # Verify all required normalized fields (AC#1)
            self.assertIsNotNone(item.published_at)  # auction_date
            self.assertIsNotNone(item.metadata["status"])  # announced/auctioned
            self.assertIsNotNone(item.metadata["cusip"])  # CUSIP
            self.assertIsNotNone(item.metadata["security_type"])  # Bill/Note/Bond/TIPS
            self.assertIsNotNone(item.metadata["auction_date"])  # auction date
            self.assertIsNotNone(item.metadata["maturity_date"])  # maturity date
            self.assertIsNotNone(item.metadata["offering_amount_millions"])  # amount
            self.assertEqual(item.metadata["currency"], "USD")  # currency
            self.assertEqual(item.metadata["unit"], "millions")  # unit

    def test_connector_name_and_source_attributes(self) -> None:
        connector = TreasurydirectAuctionsConnector(
            transport=_FakeTransport(
                [
                    HttpResponse(
                        status_code=200,
                        url=ANNOUNCED_URL,
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    ),
                    HttpResponse(
                        status_code=200,
                        url=AUCTIONED_URL,
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    ),
                ]
            )
        )
        self.assertEqual(connector.name, "treasurydirect_auctions")
        self.assertEqual(connector.source, "treasurydirect")

    def test_retry_and_rate_limit_policies_exist(self) -> None:
        connector = TreasurydirectAuctionsConnector(
            transport=_FakeTransport(
                [
                    HttpResponse(
                        status_code=200,
                        url=ANNOUNCED_URL,
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    ),
                    HttpResponse(
                        status_code=200,
                        url=AUCTIONED_URL,
                        headers={"Content-Type": "application/json"},
                        body=b"{}",
                    ),
                ]
            )
        )
        self.assertIsNotNone(connector.retry_policy)
        self.assertIsNotNone(connector.rate_limit_policy)
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.retry_policy.base_delay_seconds, 1.0)
        self.assertEqual(connector.retry_policy.max_delay_seconds, 8.0)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)
        self.assertEqual(connector.rate_limit_policy.burst, 1)

    def test_frozen_dataclass_to_dict_from_dict(self) -> None:
        """Test that frozen dataclass supports to_dict/from_dict (conventions)."""
        original = ParsedTreasurydirectAuctionRecord(
            status="auctioned",
            cusip="91282CAX8",
            security_type="Note",
            announcement_date=None,
            auction_date="2026-06-15",
            maturity_date="2028-06-30",
            offering_amount=54000.0,
            high_rate=4.65,
            accepted_amount=54000.0,
            security_term="2-Year",
            is_refunding=False,
            url=AUCTIONED_URL,
        )

        # Test to_dict
        data = original.to_dict()
        self.assertEqual(data["status"], "auctioned")
        self.assertEqual(data["cusip"], "91282CAX8")
        self.assertAlmostEqual(data["offering_amount"], 54000.0)

        # Test from_dict
        restored = ParsedTreasurydirectAuctionRecord.from_dict(data)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.cusip, original.cusip)
        self.assertAlmostEqual(restored.offering_amount, original.offering_amount)
        self.assertAlmostEqual(restored.high_rate, original.high_rate)
        self.assertEqual(restored.is_refunding, original.is_refunding)


if __name__ == "__main__":
    unittest.main()