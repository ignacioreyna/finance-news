"""EIA WPSR (Weekly Petroleum Status Report) connector.

This connector consumes the EIA Weekly Petroleum Status Report data,
providing weekly observations for U.S. petroleum inventories, production,
and supply/demand metrics.

Data Source:
    EIA Weekly Petroleum Status Report - https://www.eia.gov/petroleum/supply/weekly/
    Published weekly, typically Wednesdays at 10:30 a.m. ET

Key Series:
    - crude_stocks_mmbbl: U.S. commercial crude oil stocks (million barrels)
    - cushing_stocks_mmbbl: Cushing, OK crude oil stocks (million barrels)
    - gasoline_stocks_mmbbl: U.S. gasoline stocks (million barrels)
    - distillate_stocks_mmbbl: U.S. distillate fuel oil stocks (million barrels)
    - production_thousand_bpd: U.S. crude oil production (thousand barrels per day)
    - refinery_utilization_pct: U.S. refinery utilization (percent)
    - product_supplied_total_thousand_bpd: Total products supplied (thousand barrels per day)

Weekly Variation:
    The connector provides a helper function to compute weekly variation (delta)
    for the 5 key series: crude stocks, Cushing, gasoline, distillates, and production.
    The variation is calculated as current_week_value - prior_week_value.

Freshness:
    Weekly DEFAULT_TTL_SECONDS is used since WPSR is published once per week.
    Data is considered fresh for 7 days after publication.
"""

from __future__ import annotations

import csv
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

CONNECTOR_NAME = "eia_wpsr"
SOURCE_NAME = "eia_wpsr"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for weekly WPSR data

# WPSR series that should have weekly variation calculated
SERIES_FOR_VARIATION = [
    "crude_stocks_mmbbl",
    "cushing_stocks_mmbbl",
    "gasoline_stocks_mmbbl",
    "distillate_stocks_mmbbl",
    "production_thousand_bpd",
]

# Series units mapping
SERIES_UNITS: dict[str, str] = {
    "crude_stocks_mmbbl": "million barrels",
    "cushing_stocks_mmbbl": "million barrels",
    "gasoline_stocks_mmbbl": "million barrels",
    "distillate_stocks_mmbbl": "million barrels",
    "production_thousand_bpd": "thousand barrels per day",
    "refinery_utilization_pct": "percent",
    "product_supplied_total_thousand_bpd": "thousand barrels per day",
}


@dataclass(frozen=True)
class ParsedEiaWpsrObservation:
    """A single WPSR weekly observation from the CSV.

    Attributes:
        week_ending: The week-ending date (YYYY-MM-DD format)
        release_date: The date the report was released (YYYY-MM-DD format)
        series_name: The name of the WPSR series (e.g., "crude_stocks_mmbbl")
        value: The numeric value for the series on that week
        unit: Unit of measurement for the series
    """

    week_ending: str  # YYYY-MM-DD format
    release_date: str  # YYYY-MM-DD format
    series_name: str
    value: float
    unit: str


def parse_eia_wpsr_csv(csv_text: str) -> list[ParsedEiaWpsrObservation]:
    """Parse EIA WPSR CSV text into structured observations.

    The WPSR CSV format includes columns for:
    - week_ending: The week-ending date
    - release_date: The report release date
    - Multiple series columns with their values

    Args:
        csv_text: Raw CSV text from WPSR data source (UTF-8 encoding,
            comma-delimited).

    Returns:
        List of parsed WPSR observations, excluding the header row.
        Each observation represents a single series value for a specific week.

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

    # Expected required columns
    required_columns = ["week_ending", "release_date"]

    # Build column index map
    header_map = {col.strip(): idx for idx, col in enumerate(header)}

    # Check that all required columns are present
    for col in required_columns:
        if col not in header_map:
            raise ValueError(f"Missing required column '{col}' in CSV header")

    # Get column indices for required columns
    week_ending_idx = header_map["week_ending"]
    release_date_idx = header_map["release_date"]

    # Identify series columns (everything except week_ending and release_date)
    series_columns = [col for col in header if col not in required_columns]

    # Parse rows
    observations: list[ParsedEiaWpsrObservation] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) < len(header):
            raise ValueError(
                f"Row {row_num} has {len(row)} fields, expected at least {len(header)}"
            )

        # Extract required fields
        week_ending = row[week_ending_idx].strip()
        release_date = row[release_date_idx].strip()

        # Skip empty rows
        if not any(row):
            continue

        # Parse each series column
        for series_name in series_columns:
            series_idx = header_map[series_name]
            value_str = row[series_idx].strip()

            # Get unit for this series
            unit = SERIES_UNITS.get(series_name, "")

            # Parse value
            try:
                value = float(value_str) if value_str else 0.0
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Row {row_num}: invalid value '{value_str}' for series '{series_name}'"
                ) from exc

            observations.append(
                ParsedEiaWpsrObservation(
                    week_ending=week_ending,
                    release_date=release_date,
                    series_name=series_name,
                    value=value,
                    unit=unit,
                )
            )

    return observations


def compute_weekly_variation(
    observations: list[ParsedEiaWpsrObservation],
) -> dict[str, dict[str, float | None]]:
    """Compute weekly variation (delta) for key series.

    This helper function calculates the week-over-week change for each
    of the 5 key series: crude stocks, Cushing, gasoline, distillates,
    and production. The variation is calculated as:

        delta = current_week_value - prior_week_value

    Args:
        observations: List of parsed WPSR observations.

    Returns:
        A dictionary mapping series_name to a dict containing:
            - "delta": The weekly variation (current - prior week)
            - "week_ending": The week_ending date for this observation
        For the earliest week (no prior week), delta is None.

    Example:
        >>> observations = parse_eia_wpsr_csv(csv_text)
        >>> variations = compute_weekly_variation(observations)
        >>> variations["crude_stocks_mmbbl"]["delta"]
        2.5  # crude stocks increased by 2.5 million barrels this week
    """
    # Group observations by series and sort by week_ending
    series_data: dict[str, list[tuple[str, float]]] = {}
    for obs in observations:
        if obs.series_name not in SERIES_FOR_VARIATION:
            continue
        if obs.series_name not in series_data:
            series_data[obs.series_name] = []
        series_data[obs.series_name].append((obs.week_ending, obs.value))

    # Sort each series by week_ending (ascending)
    for series_name in series_data:
        series_data[series_name].sort(key=lambda x: x[0])

    # Compute variations
    variations: dict[str, dict[str, float | None]] = {}
    for series_name, data_points in series_data.items():
        for i, (week_ending, value) in enumerate(data_points):
            delta: float | None
            if i == 0:
                # No prior week for the earliest observation
                delta = None
            else:
                # Compute delta vs prior week
                prior_week_value = data_points[i - 1][1]
                delta = value - prior_week_value

            variations[f"{series_name}_{week_ending}"] = {
                "delta": delta,
                "week_ending": week_ending,
            }

    return variations


def _parse_date(date_str: str) -> datetime:
    """Parse WPSR date string (YYYY-MM-DD) to datetime.

    Args:
        date_str: Date string like "2024-05-31".

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


def normalize_eia_wpsr_observations(
    *,
    observations: list[ParsedEiaWpsrObservation],
    variations: dict[str, dict[str, float | None]],
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, Any] | None = None,
) -> list[SourceItem]:
    """Normalize parsed WPSR observations into SourceItem objects.

    Each observation becomes a separate SourceItem with full provenance metadata.
    Weekly variation is included in metadata for the 5 key series.

    Args:
        observations: List of parsed WPSR observations.
        variations: Weekly variation data from compute_weekly_variation().
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per observation.
    """
    items: list[SourceItem] = []

    for obs in observations:
        # Build external_id from series name and week_ending
        series_slug = obs.series_name.lower()
        external_id = f"eia_wpsr_{series_slug}_{obs.week_ending}"

        # Parse dates for published_at
        try:
            week_ending_dt = _parse_date(obs.week_ending)
            release_date_dt = _parse_date(obs.release_date)
        except ValueError:
            # If date parsing fails, skip this observation
            continue

        # Get weekly variation for this series/week if applicable
        variation_key = f"{obs.series_name}_{obs.week_ending}"
        variation = variations.get(variation_key, {})
        delta = variation.get("delta")

        # Build title
        title = f"EIA WPSR {obs.series_name}: week ending {obs.week_ending} - {obs.value:,.1f} {obs.unit}"
        if delta is not None:
            direction = "+" if delta > 0 else ""
            title += f" ({direction}{delta:,.1f})"

        # Build summary with context
        summary = (
            f"EIA Weekly Petroleum Status Report - {obs.series_name}: "
            f"{obs.value:,.1f} {obs.unit} for week ending {obs.week_ending}. "
            f"Released on {obs.release_date}."
        )
        if delta is not None:
            direction = "+" if delta > 0 else ""
            summary += f" Weekly change: {direction}{delta:,.1f} {obs.unit}."

        # Build metadata
        metadata: dict[str, Any] = {
            "content_type": "eia_wpsr_weekly_observation",
            "week_ending": obs.week_ending,
            "release_date": obs.release_date,
            "series_name": obs.series_name,
            "value": obs.value,
            "unit": obs.unit,
            "frequency": "weekly",
        }

        # Add weekly variation to metadata if available
        if delta is not None:
            metadata["weekly_variation"] = delta

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
        # Use the release date as published_at since that's when data becomes available
        freshness = Freshness(
            published_at=release_date_dt,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        )

        # Create SourceItem
        item = SourceItem(
            external_id=external_id,
            source=SOURCE_NAME,
            published_at=release_date_dt,
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


class EiaWpsrConnector:
    """Connector for EIA Weekly Petroleum Status Report data.

    Fetches weekly U.S. petroleum data from the EIA WPSR and normalizes it
    into SourceItem objects. The CSV contains multiple weekly observations
    for key inventory, production, and supply/demand series.

    Key Series Provided:
        - crude_stocks_mmbbl: U.S. commercial crude oil stocks
        - cushing_stocks_mmbbl: Cushing, OK crude oil stocks
        - gasoline_stocks_mmbbl: U.S. gasoline stocks
        - distillate_stocks_mmbbl: U.S. distillate fuel oil stocks
        - production_thousand_bpd: U.S. crude oil production
        - refinery_utilization_pct: U.S. refinery utilization
        - product_supplied_total_thousand_bpd: Total products supplied

    Weekly Variation:
        The compute_weekly_variation() helper calculates week-over-week
        deltas for the 5 key series (crude stocks, Cushing, gasoline,
        distillates, production). The earliest week has no delta.

    This connector follows the standard pattern:
        - Async HTTP client via injected AsyncHttpTransport
        - Pure parser functions (parse_eia_wpsr_csv, normalize_eia_wpsr_observations)
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
        """Initialize the EIA WPSR connector.

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
        """Fetch and parse EIA WPSR weekly data.

        Args:
            cursor: Not used (WPSR doesn't support pagination).
            since: Not used (full dataset is fetched each time).

        Returns:
            PageResult containing all WPSR observations from the CSV file.
            The CSV contains multiple observations (by series and week),
            so this returns a list with all of them. has_more is False and
            next_cursor is None because there's no pagination.

        Raises:
            RecoverableConnectorError: For 404/5xx HTTP errors (transient).
            ValueError: For unexpected status codes or CSV parsing errors.
        """
        del since  # Not used

        # Construct the WPSR data URL
        # In a real implementation, this would be the actual EIA WPSR CSV URL
        # For now, we use a placeholder that tests can mock
        wpsr_url = "https://www.eia.gov/petroleum/supply/weekly/csv_data.csv"

        # Fetch the CSV file
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=wpsr_url,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(f"WPSR CSV not found at {wpsr_url}")
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(f"EIA returned {response.status_code} for {wpsr_url}")
        if response.status_code != 200:
            raise ValueError(f"Unexpected EIA status code {response.status_code} for {wpsr_url}")

        # Decode CSV text (EIA uses UTF-8)
        try:
            csv_text = response.text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode CSV as UTF-8: {exc}") from exc

        # Parse CSV
        try:
            observations = parse_eia_wpsr_csv(csv_text)
        except ValueError as exc:
            raise ValueError(f"Failed to parse WPSR CSV: {exc}") from exc

        # Compute weekly variations for key series
        variations = compute_weekly_variation(observations)

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_eia_wpsr_observations(
            observations=observations,
            variations=variations,
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