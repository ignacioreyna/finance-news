"""Treasury DTS Cashflows connector.

This connector consumes the FiscalData Daily Treasury Statement
deposits_withdrawals_operating_cash API to fetch daily Treasury
cash flows by category (taxes, federal debt, expenditures, etc.) from the U.S. Treasury.

Data Source:
    FiscalData API - https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
    API Endpoint: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash

Key Fields:
    - record_date: The date of the observation
    - transaction_type: "deposits" or "withdrawals"
    - transaction_catg: Category (e.g., "Taxes", "Federal Debt", "Expenditures")
    - transaction_today_amt: Amount for the transaction (in millions of USD)

Holiday/Non-Business Day Handling:
    The FiscalData DTS API only publishes data on federal business days (excluding
    weekends and federal holidays). On non-business days, the connector returns
    empty results (no data available for that date). This is documented behavior:
    the connector does not error on holidays/weekends; it simply returns no items.

Freshness:
    Daily DEFAULT_TTL_SECONDS is used since cash flows are published daily on business days.
"""

from __future__ import annotations

import json
from collections import defaultdict
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

CONNECTOR_NAME = "treasury_dts_cashflows"
SOURCE_NAME = "fiscaldata_treasury"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for daily cash flow data


@dataclass(frozen=True)
class ParsedTreasuryDtsCashflowObservation:
    """A parsed observation from the FiscalData DTS deposits/withdrawals API."""

    record_date: str  # YYYY-MM-DD format
    transaction_type: str  # "deposits" or "withdrawals"
    category: str  # e.g., "Taxes", "Federal Debt", "Expenditures"
    amount: float  # Amount in millions of USD (positive for deposits, negative for withdrawals)


def parse_treasury_dts_cashflows_json(
    response_data: dict[str, Any],
) -> list[ParsedTreasuryDtsCashflowObservation]:
    """Parse a FiscalData DTS deposits/withdrawals API response into observations.

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
        transaction_type = entry.get("transaction_type")
        category = entry.get("transaction_catg")
        transaction_today_amt = entry.get("transaction_today_amt")

        # Validate required fields
        if not isinstance(record_date, str):
            raise ValueError(f"Invalid record_date format: {record_date!r}")
        if transaction_type not in ("deposits", "withdrawals"):
            raise ValueError(
                f"Unexpected transaction_type: {transaction_type!r}. "
                f"Expected 'deposits' or 'withdrawals'."
            )
        if not isinstance(category, str):
            raise ValueError(f"Invalid transaction_catg format: {category!r}")

        # Parse amount value (it comes as a string like "5000" or "-2500")
        try:
            amount = float(transaction_today_amt) if transaction_today_amt else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid amount format: transaction_today_amt={transaction_today_amt!r}"
            ) from exc

        observations.append(
            ParsedTreasuryDtsCashflowObservation(
                record_date=record_date,
                transaction_type=transaction_type,
                category=category,
                amount=amount,
            )
        )

    return observations


def normalize_treasury_dts_cashflow_observation(
    *,
    parsed: ParsedTreasuryDtsCashflowObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed Treasury DTS cashflow observation into a SourceItem.

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

    # Build title with date, type, category, and amount
    type_label = "Deposit" if parsed.transaction_type == "deposits" else "Withdrawal"
    amount_str = f"${parsed.amount:+.0f}M"
    title = (
        f"Treasury Cash Flow: {parsed.record_date} - "
        f"{type_label} {parsed.category} {amount_str}"
    )

    # Build summary with context
    summary = (
        f"Treasury cash flow on {parsed.record_date}: "
        f"{type_label} of ${abs(parsed.amount):.0f}M in {parsed.category}. "
        f"Source: FiscalData Daily Treasury Statement."
    )

    # Build metadata
    item_metadata: dict[str, Any] = {
        "content_type": "treasury_cashflow_observation",
        "record_date": parsed.record_date,
        "transaction_type": parsed.transaction_type,
        "category": parsed.category,
        "amount_millions": parsed.amount,
        "currency": "USD",
        "unit": "millions",
        "frequency": "daily",
        "holiday_handling": (
            "On federal holidays and weekends, the connector returns empty results "
            "since FiscalData DTS only publishes on business days."
        ),
    }

    return SourceItem(
        external_id=(
            f"treasury_cashflow_{parsed.transaction_type}_{parsed.category}_"
            f"{parsed.record_date}"
        ),
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


def aggregate_cashflows_weekly_by_category(
    observations: list[ParsedTreasuryDtsCashflowObservation],
) -> dict[str, dict[str, float]]:
    """Aggregate cashflows to weekly totals per category, keeping deposits and withdrawals separate.

    This function groups observations by ISO week (year-week format) and category,
    then sums deposits and withdrawals separately. The results are never netted together.

    Args:
        observations: A list of parsed cashflow observations.

    Returns:
        A nested dictionary where the outer key is the week identifier (e.g., "2024-W02")
        and the inner dictionary maps category to a dict with "deposits" and "withdrawals"
        totals. Only categories with non-zero totals are included for each transaction type.

    Example:
        >>> obs = [
        ...     ParsedTreasuryDtsCashflowObservation("2024-01-08", "deposits", "Taxes", 5000),
        ...     ParsedTreasuryDtsCashflowObservation("2024-01-08", "withdrawals", "Taxes", -2500),
        ... ]
        >>> result = aggregate_cashflows_weekly_by_category(obs)
        >>> result["2024-W02"]["Taxes"]
        {'deposits': 5000.0, 'withdrawals': -2500.0}
    """
    # Use nested defaultdict to accumulate totals
    weekly_totals: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"deposits": 0.0, "withdrawals": 0.0})
    )

    for obs in observations:
        # Parse the date to get ISO week
        try:
            year, month, day = map(int, obs.record_date.split("-"))
            dt = datetime(year, month, day)
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid record_date format: {obs.record_date!r}") from exc

        # Add to the appropriate bucket based on transaction type
        if obs.transaction_type == "deposits":
            weekly_totals[week_key][obs.category]["deposits"] += obs.amount
        elif obs.transaction_type == "withdrawals":
            weekly_totals[week_key][obs.category]["withdrawals"] += obs.amount
        else:
            raise ValueError(
                f"Unknown transaction_type: {obs.transaction_type!r}. "
                f"Expected 'deposits' or 'withdrawals'."
            )

    # Convert to a regular dict and remove zero entries
    result: dict[str, dict[str, float]] = {}
    for week_key, categories in weekly_totals.items():
        week_dict: dict[str, dict[str, float]] = {}
        for category, totals in categories.items():
            # Only include non-zero totals for each type
            non_zero_totals = {k: v for k, v in totals.items() if v != 0.0}
            if non_zero_totals:
                week_dict[category] = non_zero_totals
        if week_dict:
            result[week_key] = week_dict

    return result


class TreasuryDtsCashflowsConnector:
    """Fetch daily Treasury cash flows by category from FiscalData DTS API.

    This connector retrieves deposits and withdrawals of operating cash
    from the U.S. Treasury's Daily Treasury Statement, broken down by category.

    Data includes:
    - Daily deposits and withdrawals (in millions of USD)
    - Transaction category (e.g., Taxes, Federal Debt, Expenditures)
    - Record date for each observation

    Pagination:
        This connector returns all available observations in a single page.
        No cursor is used; the connector always fetches the most recent data.

    Holiday/Non-Business Day Handling:
        The FiscalData DTS API only publishes data on federal business days.
        On weekends, federal holidays, or other non-business days, the API
        returns empty results. The connector handles this gracefully by
        returning an empty PageResult without errors.

    Weekly Aggregation:
        The connector provides a helper function `aggregate_cashflows_weekly_by_category`
        that aggregates daily flows to weekly totals per category, keeping deposits
        and withdrawals completely separate (never netted).
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
        """Fetch a page of Treasury cash flow daily observations.

        The connector fetches the most recent deposits and withdrawals of
        operating cash observations from FiscalData DTS.

        Args:
            cursor: Not used for this connector (always fetches latest data).
            since: Optional start date for filtering (not currently supported).

        Returns:
            A PageResult containing the cash flow observations. Returns empty items
            on holidays/weekends when no data is available.

        Raises:
            ValueError: If API returns unexpected status or invalid format.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del cursor, since  # Not used for this connector

        # Build the API URL
        params = {
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
            observations = parse_treasury_dts_cashflows_json(response_data)
        except ValueError as exc:
            raise ValueError(f"Failed to parse FiscalData response from {response.url}") from exc

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_treasury_dts_cashflow_observation(
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