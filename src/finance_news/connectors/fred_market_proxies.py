"""FRED market proxies connector.

This connector fetches economic and financial market proxy series from FRED
(Federal Reserve Economic Data) via the fredgraph.csv endpoint.

Series are classified as:
- primary: Official Fed data or original sources (e.g., DFII10, DTWEXBGS)
- proxy: Aggregators or derived series (e.g., DCOILWTICO, T10YIE, T5YIFR)

Based on source research:
- source_research_us_liquidity.md: Fed balance, liquidity proxy series
- source_research_commodities_geo.md: Oil prices, breakevens, real rates, broad dollar

Data Source:
    FRED fredgraph.csv API - https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES_ID

Key Series:
    - DCOILWTICO: WTI Crude Oil Spot Price (proxy of EIA)
    - DCOILBRENTEU: Brent Crude Oil Spot Price (proxy of EIA)
    - DFII10: 10-Year Treasury Inflation-Indexed Security Constant Maturity (primary)
    - DFII5: 5-Year Treasury Inflation-Indexed Security Constant Maturity (primary)
    - DTWEXBGS: Trade Weighted U.S. Dollar Index: Broad (primary)
    - T5YIE: 5-Year Breakeven Inflation Rate (proxy, derived)
    - T10YIE: 10-Year Breakeven Inflation Rate (proxy, derived)
    - T5YIFR: 5-Year Forward Inflation Expectation Rate (proxy, derived)
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

CONNECTOR_NAME = "fred_market_proxies"
SOURCE_NAME = "fred"
PARSER_VERSION = "0.1.0"
BASE_FREDGRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
DEFAULT_TTL_SECONDS = 24 * 60 * 60


# Series classification and metadata based on source research
# "primary" = official Fed/Treasury source
# "proxy" = aggregator or derived series
DEFAULT_SERIES: dict[str, dict[str, str]] = {
    # Oil prices (proxy - FRED aggregates EIA data)
    "DCOILWTICO": {
        "label": "WTI Crude Oil Spot Price",
        "classification": "proxy",
        "description": "Cushing, OK WTI Spot Price FOB (Dollars per Barrel)",
    },
    "DCOILBRENTEU": {
        "label": "Brent Crude Oil Spot Price",
        "classification": "proxy",
        "description": "Brent Crude Oil Spot Price FOB (Dollars per Barrel)",
    },
    # Real rates (primary - official Fed/TIPS data)
    "DFII10": {
        "label": "10-Year Treasury Real Interest Rate",
        "classification": "primary",
        "description": "10-Year Treasury Inflation-Indexed Security Constant Maturity",
    },
    "DFII5": {
        "label": "5-Year Treasury Real Interest Rate",
        "classification": "primary",
        "description": "5-Year Treasury Inflation-Indexed Security Constant Maturity",
    },
    # Broad dollar (primary - official Fed index)
    "DTWEXBGS": {
        "label": "Trade Weighted U.S. Dollar Index: Broad",
        "classification": "primary",
        "description": "Trade Weighted U.S. Dollar Index: Broad, Index Mar 1973=100",
    },
    # Breakevens (proxy - derived from Treasury/TIPS)
    "T5YIE": {
        "label": "5-Year Breakeven Inflation Rate",
        "classification": "proxy",
        "description": "5-Year Breakeven Inflation Rate (T5YIE)",
    },
    "T10YIE": {
        "label": "10-Year Breakeven Inflation Rate",
        "classification": "proxy",
        "description": "10-Year Breakeven Inflation Rate (T10YIE)",
    },
    # Forward rates (proxy - derived)
    "T5YIFR": {
        "label": "5-Year Forward Inflation Expectation Rate",
        "classification": "proxy",
        "description": "5-Year Forward Inflation Expectation Rate (T5YIFR)",
    },
}


@dataclass(frozen=True)
class ParsedFredObservation:
    """A single FRED observation from the fredgraph CSV.

    Attributes:
        series_id: FRED series ID (e.g., "DCOILWTICO", "DFII10")
        observation_date: The observation date in YYYY-MM-DD format
        value: The numeric value (may be "." for missing data)
    """

    series_id: str
    observation_date: str
    value: str


def parse_fred_csv(csv_text: str, series_id: str) -> list[ParsedFredObservation]:
    """Parse FRED fredgraph CSV text into structured observations.

    Args:
        csv_text: Raw CSV text from FRED fredgraph endpoint.
        series_id: The FRED series ID being parsed.

    Returns:
        List of parsed FRED observations, excluding the header row.

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

    # FRED CSV format: "observation_date, VALUE" or with series name
    # We validate it has at least 2 columns
    if len(header) < 2:
        raise ValueError(f"Unexpected CSV header: {header}")

    # Parse rows
    observations: list[ParsedFredObservation] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) < 2:
            raise ValueError(f"Row {row_num} has {len(row)} fields, expected at least 2")

        observation_date, value = row[0], row[1]

        # Skip empty rows
        if not any(row):
            continue

        observations.append(
            ParsedFredObservation(
                series_id=series_id,
                observation_date=observation_date,
                value=value,
            )
        )

    return observations


def _parse_observation_date(date_str: str) -> datetime:
    """Parse FRED observation date (YYYY-MM-DD) to datetime.

    Args:
        date_str: Date string like "2024-01-02".

    Returns:
        Datetime representing the date at midnight UTC.

    Raises:
        ValueError: If the date string is invalid.
    """
    if len(date_str) != 10:
        raise ValueError(f"Invalid date format: {date_str}")

    try:
        year = int(date_str[0:4])
        month = int(date_str[5:7])
        day = int(date_str[8:10])
    except ValueError as exc:
        raise ValueError(f"Invalid date components in {date_str}: {exc}") from exc

    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month in date: {date_str}")
    if not (1 <= day <= 31):
        raise ValueError(f"Invalid day in date: {date_str}")

    return datetime(year, month, day, tzinfo=timezone.utc)


def _parse_value(value_str: str) -> float | None:
    """Parse FRED value string to float.

    Args:
        value_str: Value string like "72.50" or "." for missing.

    Returns:
        Parsed float value, or None if the value is "." (missing) or whitespace.
    """
    # Strip whitespace first
    stripped = value_str.strip()

    if stripped == "." or not stripped:
        return None

    try:
        return float(stripped)
    except ValueError as exc:
        raise ValueError(f"Invalid value format: {value_str}") from exc


def normalize_fred_observations(
    *,
    observations: list[ParsedFredObservation],
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> list[SourceItem]:
    """Normalize parsed FRED observations into SourceItem objects.

    Each observation becomes a separate SourceItem with full provenance metadata.

    Args:
        observations: List of parsed FRED observations.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value (series ID in this case).
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per observation.
    """
    items: list[SourceItem] = []

    for obs in observations:
        # Get series metadata
        series_meta = DEFAULT_SERIES.get(obs.series_id, {})
        label = series_meta.get("label", obs.series_id)
        classification = series_meta.get("classification", "unknown")
        description = series_meta.get("description", "")

        # Build external_id
        external_id = f"fred_{obs.series_id}_{obs.observation_date}"

        # Parse observation date for published_at
        try:
            published_at = _parse_observation_date(obs.observation_date)
        except ValueError:
            # If date parsing fails, skip this observation
            continue

        # Parse numeric value
        value = _parse_value(obs.value)

        # Build title
        title = f"{label} - {obs.observation_date}"

        # Build summary with available data
        if value is not None:
            summary = f"{label}: {value} on {obs.observation_date}"
        else:
            summary = f"{label}: No data on {obs.observation_date}"

        # Build metadata
        metadata: dict[str, object] = {
            "series_id": obs.series_id,
            "series_label": label,
            "series_classification": classification,
            "series_description": description,
            "observation_date": obs.observation_date,
            "value": value,
        }

        # Build provenance
        provenance = Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=f"{BASE_FREDGRAPH_URL}?id={obs.series_id}",
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
            body=None,
            summary=summary,
            url=f"{BASE_FREDGRAPH_URL}?id={obs.series_id}",
            metadata=metadata,
            provenance=provenance,
            freshness=freshness,
        )

        items.append(item)

    return items


class FredMarketProxiesConnector:
    """Connector for FRED market proxy data series.

    Fetches economic and financial market proxy series from FRED via the
    fredgraph.csv endpoint. Series are classified as "primary" (official
    Fed/Treasury data) or "proxy" (aggregators or derived series).

    Usage:
        The cursor should be a FRED series ID (e.g., "DCOILWTICO", "DFII10").

        Example series IDs:
            - DCOILWTICO: WTI Crude Oil Spot Price (proxy)
            - DCOILBRENTEU: Brent Crude Oil Spot Price (proxy)
            - DFII10: 10-Year Treasury Real Interest Rate (primary)
            - DFII5: 5-Year Treasury Real Interest Rate (primary)
            - DTWEXBGS: Trade Weighted U.S. Dollar Index: Broad (primary)
            - T5YIE: 5-Year Breakeven Inflation Rate (proxy)
            - T10YIE: 10-Year Breakeven Inflation Rate (proxy)
            - T5YIFR: 5-Year Forward Inflation Expectation Rate (proxy)

    This connector follows the standard pattern:
    - Async HTTP client via injected AsyncHttpTransport
    - Pure parser functions (parse_fred_csv, normalize_fred_observations)
    - Frozen dataclasses for intermediate representations
    - Proper error handling (RecoverableConnectorError for 4xx/5xx)
    - Series classification (primary vs proxy) in metadata
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
        """Initialize the FRED market proxies connector.

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
        """Fetch and parse FRED series data.

        Args:
            cursor: The FRED series ID to fetch (e.g., "DCOILWTICO").
            since: Optional since timestamp (not used for this connector).

        Returns:
            PageResult containing all observations from the FRED CSV file.
            The CSV contains multiple observations by date, so this returns
            a list with all of them. has_more is False and next_cursor is None
            because there's no pagination.

        Raises:
            ValueError: If no cursor is provided, if the series ID is not in
                DEFAULT_SERIES, or if CSV parsing fails.
            RecoverableConnectorError: For 4xx/5xx HTTP errors (transient).
        """
        del since

        if cursor is None:
            raise ValueError("fred_market_proxies connector requires a series ID cursor.")

        # Validate series ID is known
        if cursor not in DEFAULT_SERIES:
            raise ValueError(f"Unknown FRED series ID: {cursor}")

        # Build the request URL with the series ID
        params = {"id": cursor}

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_FREDGRAPH_URL,
                params=params,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(
                f"FRED series not found: {cursor}"
            )
        if 400 <= response.status_code <= 499:
            raise ValueError(
                f"FRED returned {response.status_code} for series {cursor}"
            )
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"FRED returned {response.status_code} for series {cursor}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected FRED status code {response.status_code} for series {cursor}"
            )

        # Decode CSV text (FRED uses UTF-8)
        try:
            csv_text = response.text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode CSV as UTF-8: {exc}") from exc

        # Parse CSV
        try:
            observations = parse_fred_csv(csv_text, cursor)
        except ValueError as exc:
            raise ValueError(f"Failed to parse FRED CSV for series {cursor}: {exc}") from exc

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_fred_observations(
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