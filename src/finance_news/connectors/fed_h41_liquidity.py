"""Federal Reserve H.4.1 Factors Affecting Reserve Balances connector.

This connector fetches weekly H.4.1 data from the Federal Reserve, providing
a snapshot of the Fed's balance sheet and key liquidity indicators.

Data Source:
    Federal Reserve H.4.1 Data Download - https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41
    Published weekly on Thursdays at 4:30 p.m. ET (as-of-Wednesday data)

Key Series:
    - Total Assets: Federal Reserve total assets (all items)
    - Securities Held Outright: U.S. Treasury securities and agency MBS held outright
    - ON RRP: Overnight reverse repurchase agreement facility usage
    - TGA: U.S. Treasury General Account balance at the Fed
    - Reserve Balances: Reserve balances with Federal Reserve Banks

Frequency and Frequency Difference vs FiscalData DTS:
    IMPORTANT: H.4.1 data is WEEKLY (as-of-Wednesday, published Thursdays),
    while FiscalData DTS TGA data is DAILY (federal business days).

    The Fed H.4.1 provides weekly snapshots of the balance sheet as of Wednesday
    close. This is fundamentally different from the daily Treasury General Account
    (TGA) data available from FiscalData DTS, which provides end-of-day balances
    on each federal business day.

    - H.4.1 (this connector): WEEKLY frequency, one observation per week per series
    - FiscalData DTS TGA (treasury_dts_tga): DAILY frequency, observations on business days

    When comparing TGA levels between these sources:
    - Align by using the Wednesday close date from H.4.1 with the corresponding
      DTS daily observation for that Wednesday (or nearest business day)
    - Be aware that DTS TGA may show more granular daily movements that are
      smoothed in the weekly H.4.1 snapshot
    - The weekly H.4.1 TGA value is the Fed's balance sheet view, while DTS TGA
      is the Treasury's own accounting view; small differences can occur due to
      timing and accounting treatment

Freshness:
    Weekly DEFAULT_TTL_SECONDS is used since H.4.1 is published once per week.
    Data is considered fresh for 7 days after publication.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

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

CONNECTOR_NAME = "fed_h41_liquidity"
SOURCE_NAME = "federal_reserve_h41"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for weekly H.4.1 data

# Frequency difference documentation (string constant for tests)
FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS = (
    "H.4.1 is weekly (as-of-Wednesday, published Thursdays); "
    "FiscalData DTS is daily (federal business days). "
    "Align by comparing H.4.1 Wednesday snapshot with DTS daily observation."
)


@dataclass(frozen=True)
class ParsedFedH41Observation:
    """A single H.4.1 observation from the CSV.

    Attributes:
        series_name: The name of the H.4.1 series (e.g., "Total Assets", "ON RRP")
        series_description: Detailed description of the series
        unit: Unit of measurement (e.g., "Millions of Dollars")
        date: The reference date for the observation (as-of Wednesday)
        value: The numeric value for the series on that date
    """

    series_name: str
    series_description: str
    unit: str
    date: str  # YYYY-MM-DD format
    value: float


def parse_h41_csv(csv_text: str) -> list[ParsedFedH41Observation]:
    """Parse Federal Reserve H.4.1 CSV text into structured observations.

    The H.4.1 CSV format from the Fed's Data Download includes columns for
    Series Name, Series Description, Unit, Multipliers, Date, and Value.

    Args:
        csv_text: Raw CSV text from H.4.1 Data Download (UTF-8 encoding,
            comma-delimited).

    Returns:
        List of parsed H.4.1 observations, excluding the header row.

    Raises:
        ValueError: If the CSV format is invalid or required fields are missing.
    """
    # Normalize line endings
    normalized_text = csv_text.replace("\r\n", "\n").replace("\r", "\n")

    # Parse CSV with comma delimiter
    reader = csv.reader(normalized_text.splitlines(), delimiter=",")

    # Read and validate header
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("Empty CSV file")

    # Expected header columns (order may vary, check by name)
    expected_columns = [
        "Series Name",
        "Series Description",
        "Unit",
        "Multipliers",
        "Date",
        "Value",
    ]

    # Build column index map
    header_map = {col.strip(): idx for idx, col in enumerate(header)}

    # Check that all required columns are present
    for col in expected_columns:
        if col not in header_map:
            raise ValueError(f"Missing required column '{col}' in CSV header")

    # Get column indices
    series_name_idx = header_map["Series Name"]
    series_desc_idx = header_map["Series Description"]
    unit_idx = header_map["Unit"]
    date_idx = header_map["Date"]
    value_idx = header_map["Value"]

    # Parse rows
    observations: list[ParsedFedH41Observation] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) < len(header):
            raise ValueError(f"Row {row_num} has {len(row)} fields, expected at least {len(header)}")

        # Extract fields
        series_name = row[series_name_idx].strip()
        series_description = row[series_desc_idx].strip()
        unit = row[unit_idx].strip()
        date_str = row[date_idx].strip()
        value_str = row[value_idx].strip()

        # Skip empty rows
        if not any(row):
            continue

        # Parse value
        try:
            value = float(value_str) if value_str else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Row {row_num}: invalid value '{value_str}' for series '{series_name}'") from exc

        observations.append(
            ParsedFedH41Observation(
                series_name=series_name,
                series_description=series_description,
                unit=unit,
                date=date_str,
                value=value,
            )
        )

    return observations


def _parse_date(date_str: str) -> datetime:
    """Parse H.4.1 date string (YYYY-MM-DD) to datetime.

    Args:
        date_str: Date string like "2026-06-10".

    Returns:
        Datetime representing the date at midnight UTC.

    Raises:
        ValueError: If the date string is invalid.
    """
    try:
        year, month, day = map(int, date_str.split("-"))
        return datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid date format: {date_str!r}") from exc


def normalize_h41_observations(
    *,
    observations: list[ParsedFedH41Observation],
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> list[SourceItem]:
    """Normalize parsed H.4.1 observations into SourceItem objects.

    Each observation becomes a separate SourceItem with full provenance metadata.
    This allows tracking each series independently by date.

    Args:
        observations: List of parsed H.4.1 observations.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per observation.
    """
    items: list[SourceItem] = []

    for obs in observations:
        # Build external_id from series name and date
        series_slug = obs.series_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        external_id = f"h41_{series_slug}_{obs.date}"

        # Parse date for published_at
        try:
            published_at = _parse_date(obs.date)
        except ValueError:
            # If date parsing fails, skip this observation
            continue

        # Build title
        title = f"{obs.series_name}: {obs.date} - ${obs.value:,.0f}M"

        # Build summary with context
        summary = (
            f"Federal Reserve H.4.1 - {obs.series_name}: ${obs.value:,.0f} million "
            f"as of {obs.date}. Unit: {obs.unit}."
        )

        # Build metadata
        metadata: dict[str, object] = {
            "content_type": "h41_weekly_observation",
            "series_name": obs.series_name,
            "series_description": obs.series_description,
            "unit": obs.unit,
            "date": obs.date,
            "value_millions": obs.value,
            "currency": "USD",
            "frequency": "weekly",
            "frequency_difference_vs_fiscaldata_dts": FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS,
        }

        # Build provenance
        provenance = Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=fetch_url,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        )

        # Build freshness
        freshness = Freshness(
            published_at=published_at,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        )

        # Create SourceItem
        item = SourceItem(
            external_id=external_id,
            source=SOURCE_NAME,
            published_at=published_at,
            title=title,
            body=None,  # CSV data doesn't have a full body
            summary=summary,
            url=fetch_url,
            metadata=metadata,
            provenance=provenance,
            freshness=freshness,
        )

        items.append(item)

    return items


class FedH41LiquidityConnector:
    """Connector for Federal Reserve H.4.1 weekly balance sheet data.

    Fetches the official H.4.1 Data Download CSV from the Federal Reserve and
    normalizes it into SourceItem objects. The CSV contains multiple weekly
    observations for key liquidity and balance sheet series.

    Key Series Provided:
        - Total Assets: Fed's total assets (all items)
        - Securities Held Outright: Treasury securities and agency MBS
        - ON RRP: Overnight reverse repo facility usage
        - TGA: U.S. Treasury General Account balance
        - Reserve Balances: Depository institution reserves at the Fed

    Frequency:
        H.4.1 is published WEEKLY (as-of-Wednesday, released Thursdays 4:30 p.m. ET).
        This is fundamentally different from daily FiscalData DTS TGA data.
        See FREQUENCY_DIFFERENCE_VS_FISCALDATA_DTS constant for details.

    This connector follows the standard pattern:
        - Async HTTP client via injected AsyncHttpTransport
        - Pure parser functions (parse_h41_csv, normalize_h41_observations)
        - Frozen dataclasses for intermediate representations
        - Proper error handling (RecoverableConnectorError for 4xx/5xx)
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
        """Initialize the Fed H.4.1 liquidity connector.

        Args:
            transport: Async HTTP client for fetching the CSV file.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch and parse Fed H.4.1 weekly data.

        Args:
            cursor: Not used (H.4.1 doesn't support pagination).
            since: Not used (full dataset is fetched each time).

        Returns:
            PageResult containing all H.4.1 observations from the CSV file.
            The CSV contains multiple observations (by series and week),
            so this returns a list with all of them. has_more is False and
            next_cursor is None because there's no pagination.

        Raises:
            RecoverableConnectorError: For 404/5xx HTTP errors (transient).
            ValueError: For unexpected status codes or CSV parsing errors.
        """
        del since  # Not used

        # Construct the H.4.1 Data Download URL
        # In a real implementation, this would be the actual Fed URL
        # For now, we use a placeholder that tests can mock
        h41_url = "https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41"

        # Fetch the CSV file
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=h41_url,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(f"H.4.1 CSV not found at {h41_url}")
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(f"Fed returned {response.status_code} for {h41_url}")
        if response.status_code != 200:
            raise ValueError(f"Unexpected Fed status code {response.status_code} for {h41_url}")

        # Decode CSV text (Fed uses UTF-8)
        try:
            csv_text = response.text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode CSV as UTF-8: {exc}") from exc

        # Parse CSV
        try:
            observations = parse_h41_csv(csv_text)
        except ValueError as exc:
            raise ValueError(f"Failed to parse H.4.1 CSV: {exc}") from exc

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_h41_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url=response.url,
            cursor=cursor,
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "observation_count": len(observations),
            },
        )

        return PageResult(
            items=tuple(items),
            next_cursor=None,
            has_more=False,
        )