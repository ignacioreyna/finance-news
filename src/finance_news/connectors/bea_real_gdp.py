"""BEA NIPA Real GDP connector for US macro economic data.

This connector consumes official BEA (Bureau of Economic Analysis) Real GDP data
from the NIPA (National Income and Product Accounts) dataset, specifically table
T10101 which contains percent change in Real Gross Domestic Product.

Data Source:
    BEA API - https://apps.bea.gov/api/data/
    API Documentation: https://apps.bea.gov/API/docs/index.htm

API Key:
    The BEA API requires a UserID (36-character API key) for all requests.
    This can be obtained for free at https://apps.bea.gov/API/signup/.
    The connector reads the key from the BEA_API_KEY environment variable if available.
    However, tests work without a key by using FakeTransport.

API Parameters:
    - UserID: 36-character API key (from BEA_API_KEY env var)
    - method: GetData
    - DataSetName: NIPA
    - TableName: T10101 (Percent change in Real Gross Domestic Product)
    - Frequency: Q (Quarterly)
    - Year: YYYY or comma-separated years

API Response Format:
    {
        "BEAAPI": {
            "Results": {
                "Data": [
                    {
                        "TimePeriod": "2025Q1",
                        "DataValue": "2.1",
                        "CL_UNIT": "Percent",
                        "LineNumber": "1",
                        "LineDescription": "Gross domestic product...",
                        "NoteRef": "0"
                    }
                ],
                "Notes": [
                    {
                        "NoteRef": "0",
                        "NoteText": "Seasonally adjusted annual rates"
                    }
                ]
            }
        }
    }

Key Fields:
    - TimePeriod: Quarter identifier (e.g., "2025Q1", "2024Q4")
    - DataValue: The observation value (as string)
    - CL_UNIT: Unit of measurement (e.g., "Percent")
    - LineNumber: Line number in the table
    - LineDescription: Description of the data series
    - NoteRef: Reference to notes array

Pagination:
    This connector returns all requested Real GDP observations in a single page.
    The connector always fetches quarterly data for the T10101 table.

Error Handling:
    - 5xx errors: RecoverableConnectorError (retryable)
    - 4xx errors: ValueError (non-retryable, indicates client error)
    - 1xx/3xx errors: ValueError (unexpected status)
    - Malformed JSON: ValueError (invalid response format)
    - API errors: ValueError (BEA API error codes)
"""

from __future__ import annotations

import json
import os
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

CONNECTOR_NAME = "bea_real_gdp"
SOURCE_NAME = "bea"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://apps.bea.gov/api/data/"
DEFAULT_TTL_SECONDS = 90 * 24 * 60 * 60  # 90 days for quarterly data

# BEA NIPA T10101 table parameters
DATASET_NAME = "NIPA"
TABLE_NAME = "T10101"
FREQUENCY = "Q"  # Quarterly
DEFAULT_YEARS = "2024,2025"  # Default to recent years


@dataclass(frozen=True)
class ParsedBeaObservation:
    """A single parsed BEA observation from the API."""

    time_period: str
    data_value: float
    unit: str
    line_number: str
    line_description: str
    note_ref: str


def parse_bea_period(time_period: str) -> datetime:
    """Parse BEA TimePeriod into a datetime.

    Args:
        time_period: BEA TimePeriod string (e.g., "2025Q1", "2024Q4").

    Returns:
        A datetime object representing the start of the quarter.

    Raises:
        ValueError: If the time_period is invalid.
    """
    if not time_period:
        raise ValueError("Empty time_period")

    if "Q" not in time_period:
        raise ValueError(f"Invalid time_period format: {time_period}")

    try:
        year_str, quarter_str = time_period.split("Q")
        year = int(year_str)
        quarter = int(quarter_str)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid time_period format: {time_period}") from exc

    if quarter < 1 or quarter > 4:
        raise ValueError(f"Invalid quarter: {quarter}")

    # Convert quarter to starting month
    month = (quarter - 1) * 3 + 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def parse_bea_gdp_json(json_text: str) -> list[ParsedBeaObservation]:
    """Parse a BEA API JSON response into observations.

    Args:
        json_text: Raw JSON text from the BEA API.

    Returns:
        A list of parsed observations.

    Raises:
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    # Check for BEAAPI structure
    beaapi = data.get("BEAAPI")
    if not isinstance(beaapi, dict):
        raise ValueError("Missing or invalid 'BEAAPI' field in response")

    # Check for API errors
    results = beaapi.get("Results")
    if not isinstance(results, dict):
        raise ValueError("Missing or invalid 'Results' field in BEAAPI")

    if "Error" in results:
        error = results["Error"]
        error_code = error.get("APIErrorCode", "UNKNOWN")
        error_desc = error.get("APIErrorDescription", "Unknown error")
        raise ValueError(f"BEA API error {error_code}: {error_desc}")

    # Extract Data array
    data_points = results.get("Data")
    if data_points is None:
        raise ValueError("Missing 'Data' field in Results")

    if not isinstance(data_points, list):
        raise ValueError(f"Expected 'Data' to be a list, got {type(data_points)}")

    observations = []
    for point in data_points:
        time_period = point.get("TimePeriod")
        data_value_str = point.get("DataValue")
        unit = point.get("CL_UNIT", "")
        line_number = point.get("LineNumber", "")
        line_description = point.get("LineDescription", "")
        note_ref = point.get("NoteRef", "")

        # Validate required fields
        if not time_period or data_value_str is None:
            continue  # Skip incomplete data points

        # Parse value
        try:
            data_value = float(data_value_str)
        except (ValueError, TypeError):
            continue  # Skip invalid values

        observations.append(
            ParsedBeaObservation(
                time_period=time_period,
                data_value=data_value,
                unit=unit,
                line_number=line_number,
                line_description=line_description,
                note_ref=note_ref,
            )
        )

    return observations


def normalize_bea_observation(
    *,
    parsed: ParsedBeaObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed BEA observation into a SourceItem.

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the observation.
    """
    # Parse the period into a datetime
    published_at = parse_bea_period(parsed.time_period)

    # Build external_id
    external_id = f"bea_gdp_{parsed.time_period}"

    # Build title
    title = f"BEA Real GDP: {parsed.time_period}"

    # Build summary
    summary = (
        f"Period: {parsed.time_period}, "
        f"Value: {parsed.data_value} {parsed.unit}, "
        f"Source: BEA NIPA T10101"
    )

    # Build metadata
    metadata: dict[str, Any] = {
        "content_type": "bea_real_gdp_observation",
        "time_period": parsed.time_period,
        "value": parsed.data_value,
        "units": parsed.unit,
        "fuente": "BEA NIPA T10101",
        "line_number": parsed.line_number,
        "line_description": parsed.line_description,
        "frequency": "quarterly",
        "source": "Bureau of Economic Analysis (BEA)",
        "dataset": DATASET_NAME,
        "table": TABLE_NAME,
    }

    return SourceItem(
        external_id=external_id,
        source=SOURCE_NAME,
        published_at=published_at,
        title=title,
        body=None,
        summary=summary,
        url=fetch_url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url="https://www.bea.gov/data/gdp/gross-domestic-product",
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


class BeaRealGdpConnector:
    """Fetch Real GDP data from BEA NIPA T10101 table.

    This connector retrieves quarterly Real GDP percent change data from the
    BEA NIPA dataset, specifically table T10101.

    Usage:
        The connector always fetches quarterly Real GDP data for the T10101 table.
        No cursor is needed; the connector fetches data for a default year range
        (2024-2025) or for a custom year range if specified in __init__.

    API Key:
        The BEA API requires a UserID (API key). If set in the BEA_API_KEY
        environment variable, it will be included in requests. Tests work without
        a key by using FakeTransport.

    Pagination:
        This connector returns all observations in a single page. No next_cursor
        is provided; the connector always fetches the latest available data for
        the requested year range.
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
        years: str = DEFAULT_YEARS,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
            years: Comma-separated list of years to fetch (e.g., "2024,2025").
                Defaults to "2024,2025".
        """
        self._transport = transport
        self._years = years

    def _get_api_key(self) -> str | None:
        """Get the BEA API UserID from environment.

        Returns:
            The API key if BEA_API_KEY is set, otherwise None.
        """
        return os.environ.get("BEA_API_KEY")

    def _build_request_params(self) -> dict[str, str]:
        """Build request parameters for the BEA API.

        Returns:
            A dictionary of request parameters.
        """
        params = {
            "UserID": self._get_api_key() or "",
            "method": "GetData",
            "DataSetName": DATASET_NAME,
            "TableName": TABLE_NAME,
            "Frequency": FREQUENCY,
            "Year": self._years,
            "ResultFormat": "JSON",
        }

        return params

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of BEA Real GDP observations.

        Args:
            cursor: Not used for this connector.
            since: Not used for this connector.

        Returns:
            A PageResult containing Real GDP observations for the requested years.

        Raises:
            ValueError: If API returns unexpected status or invalid format.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del cursor  # Not used for this connector
        del since  # Not used for this connector

        # Build request parameters
        params = self._build_request_params()

        # Make the request
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_URL,
                params=params,
                headers={"Content-Type": "application/json"},
            )
        )

        # Handle response status codes
        if 500 <= response.status_code < 600:
            raise RecoverableConnectorError(
                f"BEA API returned {response.status_code} for {response.url}"
            )

        if 400 <= response.status_code < 500:
            raise ValueError(
                f"BEA API returned {response.status_code} for {response.url}"
            )

        if response.status_code != 200:
            raise ValueError(
                f"Unexpected BEA API status code {response.status_code} for {response.url}"
            )

        # Parse the JSON response
        json_text = response.text()

        # Parse observations
        observations = parse_bea_gdp_json(json_text)

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_bea_observation(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        # Sort items by time_period for deterministic ordering
        items.sort(key=lambda x: x.published_at)

        # This connector returns all data in a single page
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)