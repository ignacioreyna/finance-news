"""FOMC SEP (Summary of Economic Projections) connector.

This connector parses the Summary of Economic Projections (SEP) from FOMC meetings
that include projection materials. The SEP contains the "dot plot" showing FOMC
participants' projections for key economic variables.

Data Source:
    Federal Reserve FOMC SEP Projection Materials - https://www.federalreserve.gov/monetarypolicy/fomcprojtabl.htm
    Published quarterly in March, June, September, and December (meetings marked with *)

Key Variables Extracted:
    - GDP Growth: Median projection for real GDP growth rate
    - Unemployment Rate: Median projection for unemployment rate
    - PCE Inflation: Median projection for overall PCE inflation rate
    - Core PCE Inflation: Median projection for core PCE inflation rate
    - Federal Funds Rate: Median projection for the federal funds rate

Horizons:
    - Current Year: Projection for the current calendar year
    - Year +1: Projection for the next calendar year
    - Year +2: Projection for two years ahead
    - Longer Run: Longer-run normal rate estimate

DOTS_LIMITATION:
    IMPORTANT: This connector extracts ONLY the median projections from the SEP table.
    The full "dot plot" showing individual participant projections (the dispersion/dots)
    requires manual parsing or complex PDF extraction and is NOT extracted here.
    Only the central tendency medians are parsed from the structured table.

    For detailed participant-by-participant projections, manual review of the PDF
    or more advanced PDF parsing would be required.

Frequency:
    Published quarterly in March, June, September, and December (4 times per year).

Freshness:
    DEFAULT_TTL_SECONDS is used since SEP is published only 4 times per year.
    Data is considered fresh for 90 days after publication.
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

CONNECTOR_NAME = "fomc_sep"
SOURCE_NAME = "fed"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 90 * 24 * 60 * 60  # 90 days for quarterly SEP

# Dots/dispersion limitation documentation
DOTS_LIMITATION = (
    "This connector extracts ONLY median projections from the SEP table. "
    "The full 'dot plot' showing individual participant projections (dispersion/dots) "
    "requires manual parsing or complex PDF extraction and is NOT extracted here. "
    "Only the central tendency medians are parsed from the structured table. "
    "For detailed participant-by-participant projections, manual review of the PDF "
    "or more advanced PDF parsing would be required."
)


@dataclass(frozen=True)
class ParsedSepProjection:
    """A single SEP projection for a variable and horizon.

    Attributes:
        variable: The economic variable (e.g., "GDP Growth", "Unemployment Rate")
        horizon: The projection horizon (e.g., "Current Year", "Year +1", "Year +2", "Longer Run")
        value: The median projection value (percentage or rate)
    """

    variable: str
    horizon: str
    value: float

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "variable": self.variable,
            "horizon": self.horizon,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedSepProjection":
        """Create from dictionary for deserialization."""
        return cls(
            variable=str(data["variable"]),
            horizon=str(data["horizon"]),
            value=float(data["value"]),
        )


def parse_sep_csv(csv_text: str) -> list[ParsedSepProjection]:
    """Parse SEP CSV text into structured projections.

    The SEP CSV format has variables as rows and horizons as columns.
    Expected format:
        Variable,Current Year,Year +1,Year +2,Longer Run
        GDP Growth,2.1,1.9,1.8,1.8
        Unemployment Rate,4.0,4.1,4.2,4.0
        ...

    Args:
        csv_text: Raw CSV text from SEP projection materials (UTF-8 encoding,
            comma-delimited).

    Returns:
        List of parsed SEP projections, one per variable-horizon combination.

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

    # Expected header columns
    expected_columns = [
        "Variable",
        "Current Year",
        "Year +1",
        "Year +2",
        "Longer Run",
    ]

    # Check header length
    if len(header) != len(expected_columns):
        raise ValueError(f"Expected {len(expected_columns)} columns, got {len(header)}")

    # Validate column names
    header_map = {col.strip(): idx for idx, col in enumerate(header)}
    for col in expected_columns:
        if col not in header_map:
            raise ValueError(f"Missing required column '{col}' in CSV header")

    # Get column indices
    variable_idx = header_map["Variable"]
    current_year_idx = header_map["Current Year"]
    year_plus_1_idx = header_map["Year +1"]
    year_plus_2_idx = header_map["Year +2"]
    longer_run_idx = header_map["Longer Run"]

    # Parse rows
    projections: list[ParsedSepProjection] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) != len(header):
            raise ValueError(f"Row {row_num} has {len(row)} fields, expected {len(header)}")

        # Extract variable name
        variable = row[variable_idx].strip()

        # Skip empty rows
        if not variable:
            continue

        # Extract horizon values
        current_year_str = row[current_year_idx].strip()
        year_plus_1_str = row[year_plus_1_idx].strip()
        year_plus_2_str = row[year_plus_2_idx].strip()
        longer_run_str = row[longer_run_idx].strip()

        # Parse and add projections for each horizon
        for horizon_idx, horizon_name, value_str in [
            (current_year_idx, "Current Year", current_year_str),
            (year_plus_1_idx, "Year +1", year_plus_1_str),
            (year_plus_2_idx, "Year +2", year_plus_2_str),
            (longer_run_idx, "Longer Run", longer_run_str),
        ]:
            if not value_str:
                continue  # Skip empty values

            try:
                value = float(value_str)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Row {row_num}, column '{horizon_name}': invalid value '{value_str}' for variable '{variable}'"
                ) from exc

            projections.append(
                ParsedSepProjection(
                    variable=variable,
                    horizon=horizon_name,
                    value=value,
                )
            )

    return projections


def normalize_sep_projections(
    *,
    projections: list[ParsedSepProjection],
    meeting_date: str,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize parsed SEP projections into a SourceItem.

    All projections from a single FOMC meeting are grouped into one SourceItem.
    The projections are stored in metadata as a structured list.

    Args:
        projections: List of parsed SEP projections.
        meeting_date: The meeting date (YYYY-MM-DD format).
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value (typically the SEP URL).
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        A normalized SourceItem containing all projections from the meeting.
    """
    # Parse meeting date for published_at
    try:
        year, month, day = map(int, meeting_date.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid meeting date format: {meeting_date!r}") from exc

    # Build external_id from meeting date
    external_id = f"fomc_sep_{meeting_date}"

    # Build title
    title = f"FOMC SEP Projections - {meeting_date}"

    # Build summary
    variable_count = len(set(proj.variable for proj in projections))
    horizon_count = len(set(proj.horizon for proj in projections))
    summary = (
        f"FOMC Summary of Economic Projections from {meeting_date}. "
        f"Contains median projections for {variable_count} variables "
        f"across {horizon_count} horizons (GDP, unemployment, PCE, core PCE, fed funds). "
        f"{DOTS_LIMITATION}"
    )

    # Build projections list for metadata
    projections_list = [proj.to_dict() for proj in projections]

    # Build metadata
    metadata: dict[str, object] = {
        "content_type": "fomc_sep_projections",
        "meeting_date": meeting_date,
        "projections": projections_list,
        "variable_count": variable_count,
        "horizon_count": horizon_count,
        "dots_limitation": DOTS_LIMITATION,
        "has_sep": True,  # Flag indicating this meeting has SEP
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
        body=None,  # SEP data doesn't have a full body
        summary=summary,
        url=fetch_url,
        metadata=metadata,
        provenance=provenance,
        freshness=freshness,
    )

    return item


class FomcSepConnector:
    """Connector for FOMC Summary of Economic Projections (SEP).

    Fetches and parses SEP projection materials from FOMC meetings that include
    projections (typically March, June, September, December meetings marked with *).

    The connector extracts median projections for:
        - GDP Growth (real GDP growth rate)
        - Unemployment Rate
        - PCE Inflation (overall)
        - Core PCE Inflation
        - Federal Funds Rate

    Across horizons:
        - Current Year
        - Year +1
        - Year +2
        - Longer Run

    DOT_PLOT_LIMITATION:
        This connector extracts ONLY the median projections from the SEP table.
        The full "dot plot" showing individual participant projections (dispersion/dots)
        requires manual parsing or complex PDF extraction and is NOT extracted here.
        Only the central tendency medians are parsed from the structured table.

    This connector follows the standard pattern:
        - Async HTTP client via injected AsyncHttpTransport
        - Pure parser functions (parse_sep_csv, normalize_sep_projections)
        - Frozen dataclasses for intermediate representations
        - Proper error handling (RecoverableConnectorError for 4xx/5xx)

    Usage:
        The cursor should be the SEP URL for a specific FOMC meeting.
        Only meetings with SEP (marked with * in the calendar) should have projections.
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
        """Initialize the FOMC SEP connector.

        Args:
            transport: Async HTTP client for fetching the SEP file.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch and parse SEP projections from an FOMC meeting.

        Args:
            cursor: The SEP URL for a specific FOMC meeting (required).
            since: Not used (full dataset is fetched each time).

        Returns:
            PageResult containing all SEP projections from the meeting.
            All projections are grouped into a single SourceItem.
            has_more is False and next_cursor is None because there's no pagination.

        Raises:
            ValueError: If cursor is not provided or if status code is unexpected.
            RecoverableConnectorError: For 404/5xx HTTP errors (transient).
        """
        del since  # Not used

        if not cursor:
            raise ValueError("cursor (SEP URL) is required for FOMC SEP connector")

        sep_url = cursor

        # Fetch the SEP file
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=sep_url,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(f"SEP projections not found at {sep_url}")
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(f"Fed returned {response.status_code} for {sep_url}")
        if response.status_code != 200:
            raise ValueError(f"Unexpected Fed status code {response.status_code} for {sep_url}")

        # Decode CSV text (Fed uses UTF-8)
        try:
            csv_text = response.text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode SEP CSV as UTF-8: {exc}") from exc

        # Parse CSV
        try:
            projections = parse_sep_csv(csv_text)
        except ValueError as exc:
            raise ValueError(f"Failed to parse SEP CSV: {exc}") from exc

        # Extract meeting date from URL (format: fomcprojtablYYYYMMDD.htm)
        import re

        url_match = re.search(r"fomcprojtabl(\d{8})\.htm", sep_url)
        if not url_match:
            raise ValueError(f"Cannot extract meeting date from SEP URL: {sep_url}")

        date_suffix = url_match.group(1)
        meeting_date = f"{date_suffix[:4]}-{date_suffix[4:6]}-{date_suffix[6:8]}"

        # Normalize to SourceItem
        fetched_at = datetime.now(timezone.utc)
        item = normalize_sep_projections(
            projections=projections,
            meeting_date=meeting_date,
            fetched_at=fetched_at,
            fetch_url=response.url,
            cursor=cursor,
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "projection_count": len(projections),
            },
        )

        return PageResult(
            items=(item,),
            next_cursor=None,
            has_more=False,
        )