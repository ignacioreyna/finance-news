"""TreasuryDirect auctions connector.

Fetches announced and auctioned U.S. Treasury securities from TreasuryDirect Web API.
Provides normalized auction records with status, CUSIP, security type, dates, rates,
and amounts for both announced (future) and auctioned (completed) securities.

Data Source:
    TreasuryDirect Web API - Public endpoints, no authentication required
    Announced: https://www.treasurydirect.gov/TA_WS/securities/announced?format=json
    Auctioned: https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json

Key Fields:
    - status: "announced" or "auctioned"
    - cusip: CUSIP identifier
    - security_type: Type of security (Bill, Note, Bond, TIPS, FRN, CMB)
    - announcement_date: When the auction was announced
    - auction_date: Date of the auction
    - maturity_date: Maturity date of the security
    - offering_amount: Amount offered (in millions of USD)
    - high_rate: High acceptance rate (only for auctioned securities)
    - accepted_amount: Amount accepted (only for auctioned securities)
    - url: Source URL

Refunding Coverage:
    Refunding auctions (re-opening of existing issues) are indicated by the
    presence of refunding-related fields or flags in the auctioned securities data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ._http import AsyncHttpTransport, HttpRequest
from .models import (
    Freshness,
    PageResult,
    Provenance,
    RateLimitPolicy,
    RecoverableConnectorError,
    RetryPolicy,
    SourceItem,
)

CONNECTOR_NAME = "treasurydirect_auctions"
SOURCE_NAME = "treasurydirect"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for auction data

ANNOUNCED_URL = "https://www.treasurydirect.gov/TA_WS/securities/announced?format=json"
AUCTIONED_URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json"

QUARTERLY_REFUNDING_URL = (
    "https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding"
)


@dataclass(frozen=True)
class ParsedTreasurydirectAuctionRecord:
    """A parsed auction record from TreasuryDirect API."""

    status: str  # "announced" or "auctioned"
    cusip: str
    security_type: str  # Bill, Note, Bond, TIPS, FRN, CMB
    announcement_date: str | None  # YYYY-MM-DD format or None
    auction_date: str  # YYYY-MM-DD format
    maturity_date: str  # YYYY-MM-DD format
    offering_amount: float  # in millions of USD
    high_rate: float | None  # High rate (yield), None for announced
    accepted_amount: float | None  # Accepted amount, None for announced
    security_term: str | None  # e.g., "2-Year", "13-Week"
    is_refunding: bool  # Whether this is a refunding/reopening auction
    url: str  # Source URL

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "cusip": self.cusip,
            "security_type": self.security_type,
            "announcement_date": self.announcement_date,
            "auction_date": self.auction_date,
            "maturity_date": self.maturity_date,
            "offering_amount": self.offering_amount,
            "high_rate": self.high_rate,
            "accepted_amount": self.accepted_amount,
            "security_term": self.security_term,
            "is_refunding": self.is_refunding,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParsedTreasurydirectAuctionRecord":
        return cls(
            status=str(data["status"]),
            cusip=str(data["cusip"]),
            security_type=str(data["security_type"]),
            announcement_date=data.get("announcement_date"),
            auction_date=str(data["auction_date"]),
            maturity_date=str(data["maturity_date"]),
            offering_amount=float(data["offering_amount"]),
            high_rate=data.get("high_rate"),
            accepted_amount=data.get("accepted_amount"),
            security_term=data.get("security_term"),
            is_refunding=bool(data["is_refunding"]),
            url=str(data["url"]),
        )


def parse_treasurydirect_announced_securities(
    response_data: dict[str, Any], url: str
) -> list[ParsedTreasurydirectAuctionRecord]:
    """Parse announced securities response from TreasuryDirect API.

    Args:
        response_data: The JSON response from the announced endpoint.
        url: The source URL.

    Returns:
        A list of parsed auction records with status="announced".

    Raises:
        ValueError: If the response format is invalid.
    """
    securities = response_data.get("announcedSecurities")
    if not isinstance(securities, list):
        raise ValueError(f"Expected 'announcedSecurities' to be a list, got {type(securities)}")

    records = []
    for entry in securities:
        if not isinstance(entry, dict):
            raise ValueError(f"Expected security entry to be a dict, got {type(entry)}")

        cusip = entry.get("cusip")
        security_type = entry.get("securityType")
        auction_date = entry.get("auctionDate")
        maturity_date = entry.get("maturityDate")
        offering_amount = entry.get("offeringAmount")
        security_term = entry.get("securityTerm")

        # Validate required fields
        if not isinstance(cusip, str) or not cusip:
            raise ValueError(f"Invalid or missing cusip in announced entry: {entry!r}")
        if not isinstance(security_type, str) or not security_type:
            raise ValueError(f"Invalid or missing securityType in announced entry: {entry!r}")
        if not isinstance(auction_date, str) or not auction_date:
            raise ValueError(f"Invalid or missing auctionDate in announced entry: {entry!r}")
        if not isinstance(maturity_date, str) or not maturity_date:
            raise ValueError(f"Invalid or missing maturityDate in announced entry: {entry!r}")

        # Parse offering amount (may be numeric or string)
        try:
            amount = float(offering_amount) if offering_amount is not None else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid offeringAmount in announced entry: {offering_amount!r}"
            ) from exc

        records.append(
            ParsedTreasurydirectAuctionRecord(
                status="announced",
                cusip=cusip,
                security_type=security_type,
                announcement_date=None,  # Announced securities don't have separate announcement date
                auction_date=auction_date,
                maturity_date=maturity_date,
                offering_amount=amount,
                high_rate=None,  # Not available for announced
                accepted_amount=None,  # Not available for announced
                security_term=security_term,
                is_refunding=False,  # Refunding only for auctioned
                url=url,
            )
        )

    return records


def parse_treasurydirect_auctioned_securities(
    response_data: dict[str, Any], url: str
) -> list[ParsedTreasurydirectAuctionRecord]:
    """Parse auctioned securities response from TreasuryDirect API.

    Args:
        response_data: The JSON response from the auctioned endpoint.
        url: The source URL.

    Returns:
        A list of parsed auction records with status="auctioned".

    Raises:
        ValueError: If the response format is invalid.
    """
    securities = response_data.get("auctionedSecurities")
    if not isinstance(securities, list):
        raise ValueError(f"Expected 'auctionedSecurities' to be a list, got {type(securities)}")

    records = []
    for entry in securities:
        if not isinstance(entry, dict):
            raise ValueError(f"Expected security entry to be a dict, got {type(entry)}")

        cusip = entry.get("cusip")
        security_type = entry.get("securityType")
        auction_date = entry.get("auctionDate")
        maturity_date = entry.get("maturityDate")
        offering_amount = entry.get("offeringAmount")
        accepted_amount = entry.get("acceptedAmount")
        high_rate = entry.get("highRate")
        security_term = entry.get("securityTerm")
        is_refunding = entry.get("isRefunding", False)

        # Validate required fields
        if not isinstance(cusip, str) or not cusip:
            raise ValueError(f"Invalid or missing cusip in auctioned entry: {entry!r}")
        if not isinstance(security_type, str) or not security_type:
            raise ValueError(f"Invalid or missing securityType in auctioned entry: {entry!r}")
        if not isinstance(auction_date, str) or not auction_date:
            raise ValueError(f"Invalid or missing auctionDate in auctioned entry: {entry!r}")
        if not isinstance(maturity_date, str) or not maturity_date:
            raise ValueError(f"Invalid or missing maturityDate in auctioned entry: {entry!r}")

        # Parse amounts (may be numeric or string)
        try:
            offering = float(offering_amount) if offering_amount is not None else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid offeringAmount in auctioned entry: {offering_amount!r}"
            ) from exc

        try:
            accepted = float(accepted_amount) if accepted_amount is not None else None
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid acceptedAmount in auctioned entry: {accepted_amount!r}"
            ) from exc

        # Parse high rate (may be numeric or string)
        try:
            high = float(high_rate) if high_rate is not None else None
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid highRate in auctioned entry: {high_rate!r}") from exc

        records.append(
            ParsedTreasurydirectAuctionRecord(
                status="auctioned",
                cusip=cusip,
                security_type=security_type,
                announcement_date=None,  # Not available in auctioned endpoint
                auction_date=auction_date,
                maturity_date=maturity_date,
                offering_amount=offering,
                high_rate=high,
                accepted_amount=accepted,
                security_term=security_term,
                is_refunding=bool(is_refunding),
                url=url,
            )
        )

    return records


def normalize_treasurydirect_auction_record(
    *,
    parsed: ParsedTreasurydirectAuctionRecord,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed TreasuryDirect auction record into a SourceItem.

    Args:
        parsed: The parsed auction record.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the auction record.
    """
    # Parse auction date (assume YYYY-MM-DD format)
    try:
        year, month, day = map(int, parsed.auction_date.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid auction_date format: {parsed.auction_date!r}") from exc

    # Build title with key information
    title_parts = [
        f"[{parsed.status.upper()}]",
        parsed.security_type,
        f"CUSIP {parsed.cusip}",
    ]
    if parsed.security_term:
        title_parts.append(f"({parsed.security_term})")
    title = " ".join(title_parts)

    # Build summary
    summary_parts = [
        f"{parsed.status.capitalize()} {parsed.security_type} auction",
        f"cusip: {parsed.cusip}",
        f"date: {parsed.auction_date}",
        f"maturity: {parsed.maturity_date}",
        f"offering: ${parsed.offering_amount:,.0f}M",
    ]
    if parsed.high_rate is not None:
        summary_parts.append(f"high rate: {parsed.high_rate:.3f}%")
    if parsed.accepted_amount is not None:
        summary_parts.append(f"accepted: ${parsed.accepted_amount:,.0f}M")
    if parsed.is_refunding:
        summary_parts.append("[REFUNDING/REOPENING]")
    summary = "; ".join(summary_parts)

    # Build metadata
    item_metadata: dict[str, Any] = {
        "content_type": "treasury_auction",
        "status": parsed.status,
        "cusip": parsed.cusip,
        "security_type": parsed.security_type,
        "auction_date": parsed.auction_date,
        "maturity_date": parsed.maturity_date,
        "offering_amount_millions": parsed.offering_amount,
        "currency": "USD",
        "unit": "millions",
    }
    if parsed.high_rate is not None:
        item_metadata["high_rate_percent"] = parsed.high_rate
    if parsed.accepted_amount is not None:
        item_metadata["accepted_amount_millions"] = parsed.accepted_amount
    if parsed.security_term:
        item_metadata["security_term"] = parsed.security_term
    if parsed.is_refunding:
        item_metadata["is_refunding"] = True
        item_metadata["refunding_note"] = "This is a refunding/reopening auction"

    return SourceItem(
        external_id=f"treasury_auction_{parsed.status}_{parsed.cusip}_{parsed.auction_date}",
        source=SOURCE_NAME,
        published_at=published_at,
        title=title,
        body=None,
        summary=summary,
        url=fetch_url,
        metadata=item_metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=QUARTERLY_REFUNDING_URL,
            cursor=None,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=published_at,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class TreasurydirectAuctionsConnector:
    """Fetch announced and auctioned U.S. Treasury securities from TreasuryDirect.

    This connector retrieves auction data from both the announced and auctioned
    endpoints, providing a comprehensive view of the Treasury auction calendar
    and results.

    Data includes:
    - Announced securities: Future auctions with offering amounts, terms, and dates
    - Auctioned securities: Completed auctions with acceptance rates, high/low/median rates,
      bid-to-cover ratios, and refunding indicators

    Status Distinction:
        Each record carries a status field:
        - "announced": Future auctions, no results yet
        - "auctioned": Completed auctions with full results

    Refunding Coverage:
        Refunding auctions (re-opening of existing issues) are indicated by the
        is_refunding flag in the record metadata.

    Pagination:
        This connector returns all available records in a single page.
        No cursor is used; the connector always fetches the latest data.
    """

    name = CONNECTOR_NAME
    source = SOURCE_NAME
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=8.0,
    )
    rate_limit_policy = RateLimitPolicy(concurrency=1, burst=1)

    def __init__(
        self,
        *,
        transport: AsyncHttpTransport,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of TreasuryDirect auction records.

        The connector fetches both announced and auctioned securities from
        TreasuryDirect, returning all records in a single page.

        Args:
            cursor: Not used for this connector (always fetches latest data).
            since: Optional start date for filtering (not currently supported).

        Returns:
            A PageResult containing the auction records.

        Raises:
            ValueError: If API returns unexpected status or invalid format.
            RecoverableConnectorError: For recoverable HTTP errors (5xx, 4xx).
        """
        del cursor, since  # Not used for this connector

        all_items = []

        # Fetch announced securities
        announced_response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=ANNOUNCED_URL,
                headers={"Accept": "application/json"},
            )
        )

        announced_items = await self._process_response(
            announced_response, ANNOUNCED_URL, parse_treasurydirect_announced_securities
        )
        all_items.extend(announced_items)

        # Fetch auctioned securities
        auctioned_response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=AUCTIONED_URL,
                headers={"Accept": "application/json"},
            )
        )

        auctioned_items = await self._process_response(
            auctioned_response, AUCTIONED_URL, parse_treasurydirect_auctioned_securities
        )
        all_items.extend(auctioned_items)

        # This connector returns all data in a single page
        return PageResult(items=tuple(all_items), next_cursor=None, has_more=False)

    async def _process_response(
        self,
        response,
        url: str,
        parse_fn,
    ) -> list[SourceItem]:
        """Process a single API response.

        Args:
            response: The HTTP response.
            url: The URL that was fetched.
            parse_fn: The parser function to use.

        Returns:
            A list of normalized SourceItems.

        Raises:
            ValueError: For unexpected status codes or invalid data.
            RecoverableConnectorError: For recoverable HTTP errors.
        """
        # Handle response status codes
        status_code = response.status_code
        if 500 <= status_code < 600:
            raise RecoverableConnectorError(
                f"TreasuryDirect API returned {status_code} for {response.url}"
            )
        if 400 <= status_code < 500:
            raise RecoverableConnectorError(
                f"TreasuryDirect API returned {status_code} for {response.url}"
            )
        if status_code != 200:
            raise ValueError(
                f"Unexpected TreasuryDirect status code {status_code} for {response.url}"
            )

        # Parse the JSON response
        try:
            response_data = json.loads(response.text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from {response.url}") from exc

        # Parse the auction records
        try:
            records = parse_fn(response_data, response.url)
        except ValueError as exc:
            raise ValueError(f"Failed to parse TreasuryDirect response from {response.url}") from exc

        # Normalize each record
        fetched_at = datetime.now(timezone.utc)
        items = []
        for record in records:
            item = normalize_treasurydirect_auction_record(
                parsed=record,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        return items


__all__ = [
    "ANNOUNCED_URL",
    "AUCTIONED_URL",
    "CONNECTOR_NAME",
    "DEFAULT_TTL_SECONDS",
    "PARSER_VERSION",
    "ParsedTreasurydirectAuctionRecord",
    "QUARTERLY_REFUNDING_URL",
    "SOURCE_NAME",
    "TreasurydirectAuctionsConnector",
    "normalize_treasurydirect_auction_record",
    "parse_treasurydirect_announced_securities",
    "parse_treasurydirect_auctioned_securities",
]