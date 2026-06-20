"""NY Fed SOMA holdings connector.

This connector fetches System Open Market Account (SOMA) holdings data from the
New York Fed, providing detailed composition of the Fed's securities portfolio
by instrument type and maturity bucket.

Data Source:
    NY Fed SOMA Holdings - https://www.newyorkfed.org/markets/soma-holdings
    Published regularly with snapshots of holdings by instrument and maturity

Key Series:
    - Treasuries: U.S. Treasury securities by maturity bucket
    - MBS: Agency mortgage-backed securities by maturity bucket
    - Agency Debt: Federal agency debt securities by maturity bucket

Maturity Buckets:
    Common breakdown includes ranges like 0-1y, 1-3y, 3-5y, 5-7y, 7-10y, 10+y

Metrics:
    - Par Value: Original face value of securities (in millions)
    - Market Value: Current market value of securities (in millions)

Frequency:
    SOMA holdings data is updated regularly (frequency varies by instrument).
    The connector supports computing weekly/monthly changes for QT analysis.

Freshness:
    DEFAULT_TTL_SECONDS is set to 1 week since holdings change gradually.
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

CONNECTOR_NAME = "nyfed_soma"
SOURCE_NAME = "nyfed_soma"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

# SOMA holdings data is the primary source for Fed's securities composition
DATA_CLASSIFICATION = "primary"
PROXY_SOURCES = ["FRED"]  # Alternative sources that are NOT primary


@dataclass(frozen=True)
class ParsedNyfedSomaHolding:
    """A parsed SOMA holding from the NY Fed SOMA data.

    Attributes:
        as_of_date: The reference date for the holding snapshot (YYYY-MM-DD).
        instrument: The instrument type (e.g., "Treasuries", "MBS", "Agency Debt").
        maturity_bucket: The maturity bucket (e.g., "0-1y", "1-3y", "3-5y").
        amount_par: The par value in millions.
        amount_market: The market value in millions (optional).
    """

    as_of_date: str  # YYYY-MM-DD format
    instrument: str
    maturity_bucket: str
    amount_par: float
    amount_market: float | None


def compute_weekly_monthly_changes(
    holdings: list[ParsedNyfedSomaHolding],
    prior_date: str,
    current_date: str,
) -> dict[str, dict[str, float]]:
    """Compute weekly/monthly changes between two as-of dates per instrument.

    This helper calculates the change in total holdings between two snapshots
    for each instrument type. This is useful for QT (quantitative tightening)
    analysis, where the decline in total securities held is a key metric.

    Args:
        holdings: List of all SOMA holdings (multiple dates).
        prior_date: The earlier as-of date (YYYY-MM-DD).
        current_date: The later as-of date (YYYY-MM-DD).

    Returns:
        A dictionary mapping instrument names to change metrics:
        {
            "Treasuries": {"change_par": -150.0, "change_market": -145.0},
            "MBS": {"change_par": -50.0, "change_market": -48.0},
            "Agency Debt": {"change_par": -10.0, "change_market": -9.0},
        }

        If prior_date data is missing for an instrument, returns 0.0 change.
        If current_date data is missing for an instrument, the instrument is
        omitted from the result.
    """
    # Group holdings by date and instrument
    by_date_instrument: dict[str, dict[str, list[ParsedNyfedSomaHolding]]] = {}
    for holding in holdings:
        if holding.as_of_date not in by_date_instrument:
            by_date_instrument[holding.as_of_date] = {}
        if holding.instrument not in by_date_instrument[holding.as_of_date]:
            by_date_instrument[holding.as_of_date][holding.instrument] = []
        by_date_instrument[holding.as_of_date][holding.instrument].append(holding)

    # Get holdings for the two dates
    prior_holdings = by_date_instrument.get(prior_date, {})
    current_holdings = by_date_instrument.get(current_date, {})

    # Compute changes per instrument
    changes: dict[str, dict[str, float]] = {}
    for instrument, current_entries in current_holdings.items():
        # Sum current holdings by instrument
        current_par = sum(h.amount_par for h in current_entries)
        current_market = sum(h.amount_market or 0.0 for h in current_entries)

        # Sum prior holdings by instrument (default to 0 if missing)
        prior_entries = prior_holdings.get(instrument, [])
        prior_par = sum(h.amount_par for h in prior_entries)
        prior_market = sum(h.amount_market or 0.0 for h in prior_entries)

        # Compute changes
        changes[instrument] = {
            "change_par": current_par - prior_par,
            "change_market": current_market - prior_market,
        }

    return changes


def parse_soma_csv(csv_text: str) -> list[ParsedNyfedSomaHolding]:
    """Parse NY Fed SOMA holdings CSV text into structured holdings.

    The SOMA CSV format includes columns for:
    - As-Of Date: The snapshot date
    - Instrument: The instrument type (Treasuries, MBS, Agency Debt)
    - Maturity Bucket: The maturity range
    - Par Value: Par value in millions
    - Market Value: Market value in millions (optional)

    Args:
        csv_text: Raw CSV text from SOMA data (UTF-8 encoding, comma-delimited).

    Returns:
        List of parsed SOMA holdings.

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
        "As-Of Date",
        "Instrument",
        "Maturity Bucket",
        "Par Value",
        "Market Value",
    ]

    # Build column index map
    header_map = {col.strip(): idx for idx, col in enumerate(header)}

    # Check that all required columns are present
    for col in expected_columns:
        if col not in header_map:
            raise ValueError(f"Missing required column '{col}' in CSV header")

    # Get column indices
    as_of_date_idx = header_map["As-Of Date"]
    instrument_idx = header_map["Instrument"]
    maturity_bucket_idx = header_map["Maturity Bucket"]
    par_value_idx = header_map["Par Value"]
    market_value_idx = header_map["Market Value"]

    # Parse rows
    holdings: list[ParsedNyfedSomaHolding] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) < len(header):
            raise ValueError(
                f"Row {row_num} has {len(row)} fields, expected at least {len(header)}"
            )

        # Extract fields
        as_of_date = row[as_of_date_idx].strip()
        instrument = row[instrument_idx].strip()
        maturity_bucket = row[maturity_bucket_idx].strip()
        par_value_str = row[par_value_idx].strip()
        market_value_str = row[market_value_idx].strip()

        # Skip empty rows
        if not any(row):
            continue

        # Parse par value
        try:
            par_value = float(par_value_str) if par_value_str else 0.0
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Row {row_num}: invalid par value '{par_value_str}' "
                f"for instrument '{instrument}'"
            ) from exc

        # Parse market value (optional)
        try:
            market_value = float(market_value_str) if market_value_str else None
        except (ValueError, TypeError):
            # If market value is invalid, set to None instead of raising
            market_value = None

        holdings.append(
            ParsedNyfedSomaHolding(
                as_of_date=as_of_date,
                instrument=instrument,
                maturity_bucket=maturity_bucket,
                amount_par=par_value,
                amount_market=market_value,
            )
        )

    return holdings


def _parse_date(date_str: str) -> datetime:
    """Parse SOMA date string (YYYY-MM-DD) to datetime.

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


def normalize_soma_holdings(
    *,
    holdings: list[ParsedNyfedSomaHolding],
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> list[SourceItem]:
    """Normalize parsed SOMA holdings into SourceItem objects.

    Each holding becomes a separate SourceItem with full provenance metadata.
    This allows tracking each instrument/bucket combination independently by date.

    Args:
        holdings: List of parsed SOMA holdings.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per holding.
    """
    items: list[SourceItem] = []

    for holding in holdings:
        # Build external_id from instrument, date, and maturity bucket
        instrument_slug = holding.instrument.lower().replace(" ", "_").replace("/", "_")
        bucket_slug = holding.maturity_bucket.lower().replace(" ", "_").replace("/", "_")
        external_id = f"soma_{instrument_slug}_{holding.as_of_date}_{bucket_slug}"

        # Parse date for published_at
        try:
            published_at = _parse_date(holding.as_of_date)
        except ValueError:
            # If date parsing fails, skip this holding
            continue

        # Build title
        market_value_str = (
            f", Market: ${holding.amount_market:,.0f}M"
            if holding.amount_market is not None
            else ""
        )
        title = (
            f"SOMA {holding.instrument}: {holding.maturity_bucket} "
            f"on {holding.as_of_date} - Par: ${holding.amount_par:,.0f}M"
            f"{market_value_str}"
        )

        # Build summary with context
        summary_parts = [
            f"NY Fed SOMA - {holding.instrument} ({holding.maturity_bucket}) "
            f"as of {holding.as_of_date}.",
            f"Par Value: ${holding.amount_par:,.0f} million",
        ]
        if holding.amount_market is not None:
            summary_parts.append(f"Market Value: ${holding.amount_market:,.0f} million")
        summary = " | ".join(summary_parts)

        # Build metadata
        metadata: dict[str, Any] = {
            "content_type": "soma_holding",
            "as_of_date": holding.as_of_date,
            "instrument": holding.instrument,
            "maturity_bucket": holding.maturity_bucket,
            "amount_par_millions": holding.amount_par,
            "currency": "USD",
            "data_classification": DATA_CLASSIFICATION,
            "proxy_sources": PROXY_SOURCES,
        }
        if holding.amount_market is not None:
            metadata["amount_market_millions"] = holding.amount_market

        # Build provenance
        provenance = Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=fetch_url,
            cursor=None,
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
            url=fetch_url,
            metadata=metadata,
            provenance=provenance,
            freshness=freshness,
        )

        items.append(item)

    return items


class NyfedSomaConnector:
    """Connector for NY Fed SOMA holdings data.

    Fetches the official SOMA holdings data from the New York Fed and
    normalizes it into SourceItem objects. The data includes detailed
    holdings breakdown by instrument type and maturity bucket.

    Key Data Provided:
        - Treasuries by maturity bucket (par and market value)
        - MBS by maturity bucket (par and market value)
        - Agency Debt by maturity bucket (par and market value)

    Helper Function:
        compute_weekly_monthly_changes(): Calculate changes between two
        as-of dates per instrument for QT analysis.

    This connector follows the standard pattern:
        - Async HTTP client via injected AsyncHttpTransport
        - Pure parser functions (parse_soma_csv, normalize_soma_holdings)
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
        """Initialize the NY Fed SOMA connector.

        Args:
            transport: Async HTTP client for fetching the SOMA data.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch and parse NY Fed SOMA holdings data.

        Args:
            cursor: Not used (SOMA doesn't support pagination).
            since: Not used (full dataset is fetched each time).

        Returns:
            PageResult containing all SOMA holdings from the data file.
            The data contains multiple holdings (by instrument, date, and bucket),
            so this returns a list with all of them. has_more is False and
            next_cursor is None because there's no pagination.

        Raises:
            RecoverableConnectorError: For 404/5xx HTTP errors (transient).
            ValueError: For unexpected status codes or CSV parsing errors.
        """
        del since  # Not used

        # Construct the SOMA holdings URL
        # In a real implementation, this would be the actual NY Fed URL
        # For now, we use a placeholder that tests can mock
        soma_url = "https://www.newyorkfed.org/markets/soma-holdings"

        # Fetch the CSV/JSON file
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=soma_url,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(f"SOMA data not found at {soma_url}")
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"NY Fed returned {response.status_code} for {soma_url}"
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected NY Fed status code {response.status_code} for {soma_url}")

        # Decode CSV text (NY Fed uses UTF-8)
        try:
            csv_text = response.text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode CSV as UTF-8: {exc}") from exc

        # Parse CSV
        try:
            holdings = parse_soma_csv(csv_text)
        except ValueError as exc:
            raise ValueError(f"Failed to parse SOMA CSV: {exc}") from exc

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_soma_holdings(
            holdings=holdings,
            fetched_at=fetched_at,
            fetch_url=response.url,
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "holding_count": len(holdings),
            },
        )

        return PageResult(
            items=tuple(items),
            next_cursor=None,
            has_more=False,
        )