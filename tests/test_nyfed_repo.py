from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.connectors.nyfed_repo import (
    DATA_CLASSIFICATION,
    NyfedRepoConnector,
    normalize_nyfed_repo_operation,
    parse_nyfed_repo_response,
    ParsedNyfedRepoOperation,
    PROXY_SOURCES,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "nyfed_repo"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class NyfedRepoParserTests(unittest.TestCase):
    def test_parse_on_rrp_operation(self) -> None:
        """Test parsing an ON RRP operation from NY Fed API."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        import json

        operations = parse_nyfed_repo_response(json.loads(response_data))

        self.assertEqual(len(operations), 4)

        # First ON RRP operation
        on_rrp = operations[0]
        self.assertEqual(on_rrp.operation_date, "2026-06-16")
        self.assertEqual(on_rrp.operation_type, "ON_RRP")
        self.assertAlmostEqual(on_rrp.amount_accepted, 1205.6)
        self.assertAlmostEqual(on_rrp.award_rate, 5.30)
        self.assertEqual(on_rrp.number_counterparties, 96)

    def test_parse_srf_repo_operation(self) -> None:
        """Test parsing an SRF repo operation from NY Fed API."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        import json

        operations = parse_nyfed_repo_response(json.loads(response_data))

        self.assertEqual(len(operations), 4)

        # First SRF repo operation
        srf_repo = operations[2]
        self.assertEqual(srf_repo.operation_date, "2026-06-16")
        self.assertEqual(srf_repo.operation_type, "SRF_REPO")
        self.assertAlmostEqual(srf_repo.amount_accepted, 45.0)
        self.assertAlmostEqual(srf_repo.award_rate, 5.25)
        self.assertEqual(srf_repo.number_counterparties, 12)

    def test_parse_both_types_present(self) -> None:
        """Test that both ON RRP and SRF repo types are present (AC#3)."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        import json

        operations = parse_nyfed_repo_response(json.loads(response_data))

        # AC#3: Verify both types are present
        operation_types = {op.operation_type for op in operations}
        self.assertIn("ON_RRP", operation_types)
        self.assertIn("SRF_REPO", operation_types)

        # Verify we have at least one of each
        on_rrp_ops = [op for op in operations if op.operation_type == "ON_RRP"]
        srf_ops = [op for op in operations if op.operation_type == "SRF_REPO"]
        self.assertGreater(len(on_rrp_ops), 0)
        self.assertGreater(len(srf_ops), 0)

    def test_parse_empty_operations_returns_empty_list(self) -> None:
        """Test parsing empty repoOperations returns empty list."""
        response_data = {"repoOperations": []}

        operations = parse_nyfed_repo_response(response_data)

        self.assertEqual(len(operations), 0)

    def test_parse_invalid_operations_type_raises(self) -> None:
        """Test that parsing non-list repoOperations raises ValueError."""
        response_data = {"repoOperations": "not a list"}

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Expected 'repoOperations' to be a list", str(cm.exception))

    def test_parse_missing_operation_date_raises(self) -> None:
        """Test that parsing missing operationDate raises ValueError."""
        response_data = {
            "repoOperations": [
                {
                    "operationType": "ON_RRP",
                    "amountAccepted": 1205.6,
                    "awardRate": 5.30,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Invalid operationDate", str(cm.exception))

    def test_parse_invalid_operation_date_type_raises(self) -> None:
        """Test that parsing non-string operationDate raises ValueError."""
        response_data = {
            "repoOperations": [
                {
                    "operationDate": 20260616,  # Number instead of string
                    "operationType": "ON_RRP",
                    "amountAccepted": 1205.6,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Invalid operationDate", str(cm.exception))

    def test_parse_missing_operation_type_raises(self) -> None:
        """Test that parsing missing operationType raises ValueError."""
        response_data = {
            "repoOperations": [
                {
                    "operationDate": "2026-06-16",
                    "amountAccepted": 1205.6,
                    "awardRate": 5.30,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Invalid operationType", str(cm.exception))

    def test_parse_missing_amount_accepted_raises(self) -> None:
        """Test that parsing missing amountAccepted raises ValueError."""
        response_data = {
            "repoOperations": [
                {
                    "operationDate": "2026-06-16",
                    "operationType": "ON_RRP",
                    "awardRate": 5.30,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Invalid amountAccepted", str(cm.exception))

    def test_parse_missing_award_rate_raises(self) -> None:
        """Test that parsing missing awardRate raises ValueError."""
        response_data = {
            "repoOperations": [
                {
                    "operationDate": "2026-06-16",
                    "operationType": "ON_RRP",
                    "amountAccepted": 1205.6,
                }
            ]
        }

        with self.assertRaises(ValueError) as cm:
            parse_nyfed_repo_response(response_data)

        self.assertIn("Invalid awardRate", str(cm.exception))

    def test_parse_operation_without_counterparties(self) -> None:
        """Test parsing operation with missing numberCounterparties."""
        response_data = {
            "repoOperations": [
                {
                    "operationDate": "2026-06-16",
                    "operationType": "ON_RRP",
                    "amountSubmitted": 0.0,
                    "amountAccepted": 1205.6,
                    "awardRate": 5.30,
                }
            ]
        }

        operations = parse_nyfed_repo_response(response_data)

        self.assertEqual(len(operations), 1)
        self.assertIsNone(operations[0].number_counterparties)

    def test_normalize_on_rrp_operation(self) -> None:
        """Test normalizing an ON RRP operation (AC#1)."""
        parsed = ParsedNyfedRepoOperation(
            operation_date="2026-06-16",
            operation_type="ON_RRP",
            amount_submitted=0.0,
            amount_accepted=1205.6,
            award_rate=5.30,
            number_counterparties=96,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        item = normalize_nyfed_repo_operation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
        )

        # AC#1: Verify operation_date, type, amount, rate, and participants
        self.assertEqual(item.external_id, "on_rrp_2026-06-16")
        self.assertEqual(item.source, "nyfed")
        self.assertEqual(item.published_at, datetime(2026, 6, 16, tzinfo=timezone.utc))
        self.assertEqual(item.url, "https://markets.newyorkfed.org/api/repo/operations/last/100.json")
        self.assertIn("ON RRP", item.title)
        self.assertIn("$1205.6B", item.title)
        self.assertIn("5.30%", item.title)
        self.assertIn("96 counterparties", item.title)

        # AC#1: Verify metadata includes all required fields
        self.assertEqual(item.metadata["content_type"], "repo_operation")
        self.assertEqual(item.metadata["operation_date"], "2026-06-16")
        self.assertEqual(item.metadata["type"], "on_rrp")
        self.assertAlmostEqual(item.metadata["amount_accepted"], 1205.6)
        self.assertAlmostEqual(item.metadata["amount_submitted"], 0.0)
        self.assertAlmostEqual(item.metadata["award_rate"], 5.30)
        self.assertEqual(item.metadata["number_counterparties"], 96)

    def test_normalize_srf_repo_operation(self) -> None:
        """Test normalizing an SRF repo operation (AC#1)."""
        parsed = ParsedNyfedRepoOperation(
            operation_date="2026-06-16",
            operation_type="SRF_REPO",
            amount_submitted=125.0,
            amount_accepted=45.0,
            award_rate=5.25,
            number_counterparties=12,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        item = normalize_nyfed_repo_operation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
        )

        # AC#1: Verify operation_date, type, amount, rate, and participants
        self.assertEqual(item.external_id, "srf_repo_2026-06-16")
        self.assertEqual(item.source, "nyfed")
        self.assertEqual(item.published_at, datetime(2026, 6, 16, tzinfo=timezone.utc))
        self.assertIn("Standing Repo Facility", item.title)
        self.assertIn("$45.0B", item.title)
        self.assertIn("5.25%", item.title)
        self.assertIn("12 counterparties", item.title)

        # AC#1: Verify metadata includes all required fields
        self.assertEqual(item.metadata["content_type"], "repo_operation")
        self.assertEqual(item.metadata["operation_date"], "2026-06-16")
        self.assertEqual(item.metadata["type"], "srf_repo")
        self.assertAlmostEqual(item.metadata["amount_accepted"], 45.0)
        self.assertAlmostEqual(item.metadata["amount_submitted"], 125.0)
        self.assertAlmostEqual(item.metadata["award_rate"], 5.25)
        self.assertEqual(item.metadata["number_counterparties"], 12)

    def test_normalize_operation_without_counterparties(self) -> None:
        """Test normalizing operation with no counterparties."""
        parsed = ParsedNyfedRepoOperation(
            operation_date="2026-06-16",
            operation_type="ON_RRP",
            amount_submitted=0.0,
            amount_accepted=1205.6,
            award_rate=5.30,
            number_counterparties=None,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        item = normalize_nyfed_repo_operation(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
        )

        # Should not include counterparties in title
        self.assertIn("ON RRP", item.title)
        self.assertNotIn("counterparties", item.title)

        # Metadata should have None for counterparties
        self.assertIsNone(item.metadata["number_counterparties"])

    def test_normalize_invalid_operation_date_format_raises(self) -> None:
        """Test that normalizing invalid operation_date format raises ValueError."""
        parsed = ParsedNyfedRepoOperation(
            operation_date="invalid-date",
            operation_type="ON_RRP",
            amount_submitted=0.0,
            amount_accepted=1205.6,
            award_rate=5.30,
            number_counterparties=96,
        )
        fetched_at = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError) as cm:
            normalize_nyfed_repo_operation(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
            )

        self.assertIn("Invalid operation_date format", str(cm.exception))


class NyfedRepoConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_default_limit(self) -> None:
        """Test that fetch_page with default limit fetches repo operations."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        result = await connector.fetch_page()

        # No pagination for this connector
        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 4)

        # Verify the URL was built correctly
        self.assertEqual(
            transport.requests[0].url,
            "https://markets.newyorkfed.org/api/repo/operations/last/100.json",
        )

    async def test_fetch_page_custom_limit(self) -> None:
        """Test that fetch_page respects custom limit parameter."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/5.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport, limit=5)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 4)  # All 4 operations in fixture
        self.assertIn("last/5.json", transport.requests[0].url)

    async def test_fetch_page_empty_results(self) -> None:
        """Test that fetch_page with empty results returns empty items."""
        response_data = {"repoOperations": []}
        import json

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_data).encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(result.items, ())
        self.assertFalse(result.has_more)

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        """Test that fetch_page with 5xx raises RecoverableConnectorError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=503,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "service unavailable"}',
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError) as cm:
            await connector.fetch_page()

        self.assertIn("503", str(cm.exception))

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        """Test that fetch_page with unexpected status raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=404,  # 4xx should raise ValueError
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b'{"error": "not found"}',
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Unexpected NY Fed status code 404", str(cm.exception))

    async def test_fetch_page_invalid_json_raises_value_error(self) -> None:
        """Test that fetch_page with invalid JSON raises ValueError."""
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=b"not valid json",
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Invalid JSON response", str(cm.exception))

    async def test_fetch_page_invalid_parse_raises_value_error(self) -> None:
        """Test that fetch_page with invalid parse raises ValueError."""
        # Invalid repoOperations type
        response_data = {"repoOperations": "not a list"}
        import json

        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_data).encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page()

        self.assertIn("Failed to parse NY Fed repo response", str(cm.exception))

    async def test_operations_have_all_required_fields(self) -> None:
        """Test that operations include all required normalized fields (AC#1)."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 4)

        # Check ON RRP operation (AC#1)
        on_rrp = [item for item in result.items if item.metadata["type"] == "on_rrp"][0]
        self.assertIsNotNone(on_rrp.published_at)  # operation_date
        self.assertEqual(on_rrp.metadata["type"], "on_rrp")
        self.assertAlmostEqual(on_rrp.metadata["amount_accepted"], 1205.6)
        self.assertAlmostEqual(on_rrp.metadata["award_rate"], 5.30)
        self.assertEqual(on_rrp.metadata["number_counterparties"], 96)

        # Check SRF operation (AC#1)
        srf = [item for item in result.items if item.metadata["type"] == "srf_repo"][0]
        self.assertIsNotNone(srf.published_at)  # operation_date
        self.assertEqual(srf.metadata["type"], "srf_repo")
        self.assertAlmostEqual(srf.metadata["amount_accepted"], 45.0)
        self.assertAlmostEqual(srf.metadata["award_rate"], 5.25)
        self.assertEqual(srf.metadata["number_counterparties"], 12)

    async def test_parser_non_empty_and_has_both_types(self) -> None:
        """Test that parser returns non-empty operations and both ON RRP and SRF repo types (AC#1, AC#3)."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        import json

        operations = parse_nyfed_repo_response(json.loads(response_data))

        # AC#1: Parser should be non-empty
        self.assertGreater(len(operations), 0)

        # AC#3: Both types should be present
        operation_types = {op.operation_type for op in operations}
        self.assertIn("ON_RRP", operation_types)
        self.assertIn("SRF_REPO", operation_types)

        # Verify we have at least one of each
        on_rrp_ops = [op for op in operations if op.operation_type == "ON_RRP"]
        srf_ops = [op for op in operations if op.operation_type == "SRF_REPO"]
        self.assertGreater(len(on_rrp_ops), 0)
        self.assertGreater(len(srf_ops), 0)

    async def test_data_classification_is_primary(self) -> None:
        """Test that NY Fed repo is marked as primary data source (AC#3)."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        result = await connector.fetch_page()

        self.assertEqual(len(result.items), 4)

        # AC#3: All items should have primary classification
        for item in result.items:
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
        self.assertEqual(NyfedRepoConnector.name, "nyfed_repo")
        self.assertEqual(NyfedRepoConnector.source, "nyfed")

        # Verify retry policy exists
        self.assertIsNotNone(NyfedRepoConnector.retry_policy)
        self.assertEqual(NyfedRepoConnector.retry_policy.max_attempts, 3)

        # Verify rate limit policy exists
        self.assertIsNotNone(NyfedRepoConnector.rate_limit_policy)
        self.assertEqual(NyfedRepoConnector.rate_limit_policy.concurrency, 1)

    async def test_on_rrp_vs_srf_distinction(self) -> None:
        """Test that ON RRP and SRF repo operations are clearly distinguished (AC#3)."""
        response_data = (FIXTURES_DIR / "operations.json").read_text(encoding="utf-8")
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url="https://markets.newyorkfed.org/api/repo/operations/last/100.json",
                headers={"Content-Type": "application/json"},
                body=response_data.encode("utf-8"),
            )
        )
        connector = NyfedRepoConnector(transport=transport)

        result = await connector.fetch_page()

        # AC#3: Verify types are clearly distinguished in metadata
        on_rrp_items = [item for item in result.items if item.metadata["type"] == "on_rrp"]
        srf_items = [item for item in result.items if item.metadata["type"] == "srf_repo"]

        self.assertGreater(len(on_rrp_items), 0)
        self.assertGreater(len(srf_items), 0)

        # AC#3: Verify ON RRP items have distinctive titles
        for item in on_rrp_items:
            self.assertIn("ON RRP", item.title)
            self.assertEqual(item.metadata["type"], "on_rrp")

        # AC#3: Verify SRF items have distinctive titles
        for item in srf_items:
            self.assertIn("Standing Repo Facility", item.title)
            self.assertEqual(item.metadata["type"], "srf_repo")


if __name__ == "__main__":
    unittest.main()