"""Treasury DTS TGA (Daily Treasury Statement - General Account) connector.

This connector consumes the FiscalData Daily Treasury Statement operating_cash_balance
API to fetch daily Treasury General Account (TGA) balances from the U.S. Treasury.

Data Source:
    FiscalData API - https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
    API Endpoint: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance

Key Fields:
    - record_date: The date of the observation
    - account_type: "Federal Reserve Account" (TGA)
    - open_today_bal: Opening balance for the day (in millions of USD)
    - close_today_bal: Closing balance for the day (in millions of USD)

Holiday/Non-Business Day Handling:
    The FiscalData DTS API only publishes data on federal business days (excluding
    weekends and federal holidays). On non-business days, the connector returns
    empty results (no data available for that date). This is documented behavior:
    the connector does not error on holidays/weekends; it simply returns no items.

Freshness:
    Daily DEFAULT_TTL_SECONDS is used since TGA data is published daily on business days.
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

CONNECTOR_NAME = "treasury_dts_tga"
SOURCE_NAME = "fiscaldata_treasury"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for daily TGA data

# Filter for Federal Reserve Account (TGA)
ACCOUNT_TYPE_FILTER = "Federal Reserve Account"


@dataclass(frozen=True)
class ParsedTreasuryDtsTgaObservation:
    """A parsed observation from the FiscalData DTS operating cash balance API."""

    record_date: str  # YYYY-MM-DD format
    account_type: str  # "Federal Reserve Account"
    open_today_bal: float  # Opening balance in millions of USD
    close_today_bal: float  # Closing balance in millions of USD
    daily_change: float  # Calculated as close_today_bal - open_today_bal


def parse_treasury_dts_tga_response(
    response_data: dict[str, Any],
) -> list[ParsedTreasuryDtsTgaObservation]:
    """Parse a FiscalData DTS operating cash balance API response into observations.

    Args:
        response_data: The JSON response from the FiscalData API.

    Returns:
        A list of parsed observations.

    Raises:
        ValueError: If the response format is invalid.
    """
    data = response_data.get("data")
    if not isinstance(data, list):
        raise ValueError(f"Expected 'data' to be a list, got {type(data)}")

    if not data:
        # Empty results - no observations available (e.g., on holidays/weekends)
        return []

    observations = []
    for entry in data:
        record_date = entry.get("record_date")
        account_type = entry.get("account_type")
        open_today_bal = entry.get("open_today_bal")
        close_today_bal = entry.get("close_today_bal")

        # Validate required fields
        if not isinstance(record_date, str):
            raise ValueError(f"Invalid record_date format: {record_date!r}")
        if account_type != ACCOUNT_TYPE_FILTER:
            raise ValueError(
                f"Unexpected account_type: {account_type!r}. "
                f"Expected '{ACCOUNT_TYPE_FILTER}'."
            )

        # Parse balance values (they come as strings like "215160")
        try:
            open_balance = float(open_today_bal) if open_today_bal else 0.0
            close_balance = float(close_today_bal) if close_today_bal else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid balance format: open_today_bal={open_today_bal!r}, "
                f"close_today_bal={close_today_bal!r}"
            ) from exc

        # Calculate daily change
        daily_change = close_balance - open_balance

        observations.append(
            ParsedTreasuryDtsTgaObservation(
                record_date=record_date,
                account_type=account_type,
                open_today_bal=open_balance,
                close_today_bal=close_balance,
                daily_change=daily_change,
            )
        )

    return observations


def normalize_treasury_dts_tga_observation(
    *,
    parsed: ParsedTreasuryDtsTgaObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed Treasury DTS TGA observation into a SourceItem.

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the observation.
    """
    # Parse the record_date (assume FiscalData returns dates in YYYY-MM-DD format)
    try:
        year, month, day = map(int, parsed.record_date.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid record_date format: {parsed.record_date!r}") from exc

    # Build title with date and TGA balance
    title = (
        f"TGA Federal Reserve Account: {parsed.record_date} - "
        f"Close ${parsed.close_today_bal:.0f}M, "
        f"Daily Change ${parsed.daily_change:+.0f}M"
    )

    # Build summary with context
    summary = (
        f"Treasury General Account (TGA) - Federal Reserve Account: "
        f"${parsed.close_today_bal:.0f}M closing balance on {parsed.record_date}. "
        f"Daily change: ${parsed.daily_change:+.0f}M "
        f"(from ${parsed.open_today_bal:.0f}M opening)."
    )

    # Build metadata
    item_metadata: dict[str, Any] = {
        "content_type": "tga_daily_observation",
        "account_type": parsed.account_type,
        "record_date": parsed.record_date,
        "open_today_bal_millions": parsed.open_today_bal,
        "close_today_bal_millions": parsed.close_today_bal,
        "daily_change_millions": parsed.daily_change,
        "currency": "USD",
        "unit": "millions",
        "frequency": "daily",
        "holiday_handling": (
            "On federal holidays and weekends, the connector returns empty results "
            "since FiscalData DTS only publishes on business days."
        ),
    }

    return SourceItem(
        external_id=f"tga_federal_reserve_account_{parsed.record_date}",
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
            canonical_url=fetch_url,
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


class TreasuryDtsTgaConnector:
    """Fetch daily Treasury General Account (TGA) balances from FiscalData DTS API.

    This connector retrieves the Federal Reserve Account (TGA) operating cash
    balance from the U.S. Treasury's Daily Treasury Statement.

    Data includes:
    - Daily opening and closing balances (in millions of USD)
    - Calculated daily change
    - Record date for each observation

    Pagination:
        This connector returns all available observations in a single page.
        No cursor is used; the connector always fetches the most recent data.

    Holiday/Non-Business Day Handling:
        The FiscalData DTS API only publishes data on federal business days.
        On weekends, federal holidays, or other non-business days, the API
        returns empty results. The connector handles this gracefully by
        returning an empty PageResult without errors.
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
        limit: int = 100,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
            limit: Maximum number of observations to fetch (default: 100).
        """
        self._transport = transport
        self._limit = limit

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of TGA daily observations.

        The connector fetches the most recent Federal Reserve Account (TGA)
        operating cash balance observations from FiscalData DTS.

        Args:
            cursor: Not used for this connector (always fetches latest data).
            since: Optional start date for filtering (not currently supported).

        Returns:
            A PageResult containing the TGA observations. Returns empty items
            on holidays/weekends when no data is available.

        Raises:
            ValueError: If API returns unexpected status or invalid format.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del cursor, since  # Not used for this connector

        # Build the API URL with filter for Federal Reserve Account
        params = {
            "filter": f"account_type:eq:{ACCOUNT_TYPE_FILTER}",
            "sort": "-record_date",  # Most recent first
            "limit": str(self._limit),
        }

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_URL,
                params=params,
                headers={"Accept": "application/json"},
            )
        )

        # Handle response status codes
        if 500 <= response.status_code < 600:
            raise RecoverableConnectorError(
                f"FiscalData API returned {response.status_code} for {response.url}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected FiscalData status code {response.status_code} for {response.url}"
            )

        # Parse the JSON response
        try:
            response_data = json.loads(response.text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from {response.url}") from exc

        # Parse the observations
        try:
            observations = parse_treasury_dts_tga_response(response_data)
        except ValueError as exc:
            raise ValueError(f"Failed to parse FiscalData response from {response.url}") from exc

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_treasury_dts_tga_observation(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        # This connector returns all data in a single page
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)