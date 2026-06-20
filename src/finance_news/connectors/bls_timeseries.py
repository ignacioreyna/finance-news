"""BLS Public Data API v2 connector for US macro economic time series.

This connector consumes official BLS (Bureau of Labor Statistics) time series
data from the Public Data API v2 endpoint, covering key macro indicators:

- CPI (Consumer Price Index): CUSR0000SA0 (headline), CUSR0000SA0L1E (core)
- Payrolls (Nonfarm Payrolls): CES0000000001
- Unemployment Rate: LNS14000000
- AHE (Average Hourly Earnings): CES0500000003
- JOLTS (Job Openings and Labor Turnover Survey): JTS000000000000000JOL (openings),
  JTS000000000000000HIL (hires), JTS000000000000000QUR (quits rate)

Data Source:
    BLS Public Data API v2 - https://api.bls.gov/publicAPI/v2/timeseries/data/
    API Documentation: https://www.bls.gov/developers/api_signature_v2.htm

Registration Key:
    The BLS API registration key is optional. Simple queries work without a key,
    but using a key is recommended for production to avoid rate limits and enable
    optional parameters. The connector reads the key from the BLS_API_KEY
    environment variable if available.

API Response Format:
    {
        "status": "REQUEST_SUCCEEDED",
        "responseTime": 123,
        "message": [],
        "Results": {
            "series": [
                {
                    "seriesID": "CUSR0000SA0",
                    "data": [
                        {
                            "year": "2026",
                            "period": "M05",
                            "periodName": "May",
                            "value": "317.123",
                            "footnotes": [...]
                        }
                    ]
                }
            ]
        }
    }

Key Fields:
    - seriesID: The BLS series identifier
    - year: Four-digit year (YYYY)
    - period: Period code (M01-M12 for monthly, Q01-Q04 for quarterly, A01 for annual)
    - periodName: Human-readable period name
    - value: The observation value (as string)
    - footnotes: Array of footnote objects

Pagination:
    This connector returns all requested series observations in a single page.
    The cursor parameter should contain a comma-separated list of series IDs.

Error Handling:
    - 5xx errors: RecoverableConnectorError (retryable)
    - 4xx errors: ValueError (non-retryable, indicates client error)
    - 1xx/3xx errors: ValueError (unexpected status)
    - Malformed JSON: ValueError (invalid response format)
    - Invalid series ID: Returns empty results for that series
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

CONNECTOR_NAME = "bls_timeseries"
SOURCE_NAME = "bls"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days for monthly data

# Default minimum series set for weekly Fed dashboard (versioned list)
DEFAULT_SERIES = [
    # CPI (Consumer Price Index)
    "CUSR0000SA0",  # CPI-U All Items, Not Seasonally Adjusted (headline)
    "CUSR0000SA0L1E",  # CPI-U All Items Less Food and Energy (core)
    # Payrolls (Nonfarm Payrolls)
    "CES0000000001",  # Total Nonfarm Payrolls, Seasonally Adjusted
    # Unemployment
    "LNS14000000",  # Unemployment Rate, Seasonally Adjusted
    # AHE (Average Hourly Earnings)
    "CES0500000003",  # Average Hourly Earnings of All Employees, Total Private, Seasonally Adjusted
    # JOLTS (Job Openings and Labor Turnover Survey)
    "JTS000000000000000JOL",  # Job Openings Level, Total Nonfarm, Seasonally Adjusted
    "JTS000000000000000HIL",  # Hires Level, Total Nonfarm, Seasonally Adjusted
    "JTS000000000000000QUR",  # Quits Rate, Total Nonfarm, Seasonally Adjusted
]


@dataclass(frozen=True)
class ParsedBlsObservation:
    """A single parsed BLS observation from the API."""

    series_id: str
    year: str
    period: str
    period_name: str
    value: float
    footnotes: list[dict[str, Any]]


def parse_bls_period(year: str, period: str) -> datetime:
    """Parse BLS period code and year into a datetime.

    Args:
        year: Four-digit year string (YYYY).
        period: Period code (M01-M12 for monthly, Q01-Q04 for quarterly, A01 for annual).

    Returns:
        A datetime object representing the start of the period.

    Raises:
        ValueError: If the period code is invalid.
    """
    if period.startswith("M"):
        # Monthly: M01-M12
        month = int(period[1:])
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month period: {period}")
        return datetime(int(year), month, 1, tzinfo=timezone.utc)
    elif period.startswith("Q"):
        # Quarterly: Q01-Q04
        quarter = int(period[1:])
        if quarter < 1 or quarter > 4:
            raise ValueError(f"Invalid quarter period: {period}")
        month = (quarter - 1) * 3 + 1
        return datetime(int(year), month, 1, tzinfo=timezone.utc)
    elif period.startswith("A"):
        # Annual: A01
        return datetime(int(year), 1, 1, tzinfo=timezone.utc)
    else:
        raise ValueError(f"Unsupported period code: {period}")


def parse_bls_series_json(
    json_text: str,
    series_ids: list[str],
) -> list[ParsedBlsObservation]:
    """Parse a BLS API v2 JSON response into observations.

    Args:
        json_text: Raw JSON text from the BLS API.
        series_ids: The list of series IDs requested (for validation).

    Returns:
        A list of parsed observations across all series.

    Raises:
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    # Check overall status
    status = data.get("status")
    if status == "REQUEST_NOT_PROCESSED" or status == "REQUEST_FAILED":
        message = data.get("message", [])
        error_msg = message[0] if message else "Unknown error"
        raise ValueError(f"BLS API request failed: {error_msg}")

    # Extract Results.series array
    results = data.get("Results")
    if not isinstance(results, dict):
        raise ValueError("Missing or invalid 'Results' field in response")

    series_list = results.get("series")
    if series_list is None:
        raise ValueError("Missing 'series' field in Results")

    if not isinstance(series_list, list):
        raise ValueError(f"Expected 'series' to be a list, got {type(series_list)}")

    observations = []
    for series in series_list:
        series_id = series.get("seriesID")
        if not series_id:
            continue  # Skip series without ID

        # Check if this is one of the requested series
        if series_ids and series_id not in series_ids:
            continue  # Skip unexpected series

        data_points = series.get("data")
        if not isinstance(data_points, list):
            continue  # Skip series without valid data

        for point in data_points:
            year = point.get("year")
            period = point.get("period")
            period_name = point.get("periodName")
            value_str = point.get("value")
            footnotes = point.get("footnotes", [])

            # Validate required fields
            if not year or not period or value_str is None:
                continue  # Skip incomplete data points

            # Parse value
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue  # Skip invalid values

            observations.append(
                ParsedBlsObservation(
                    series_id=series_id,
                    year=year,
                    period=period,
                    period_name=period_name,
                    value=value,
                    footnotes=footnotes if isinstance(footnotes, list) else [],
                )
            )

    return observations


def normalize_bls_observation(
    *,
    parsed: ParsedBlsObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed BLS observation into a SourceItem.

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the observation.
    """
    # Parse the period into a datetime
    published_at = parse_bls_period(parsed.year, parsed.period)

    # Build external_id
    external_id = f"{parsed.series_id}_{parsed.year}_{parsed.period}"

    # Build title with series ID and date
    title = f"BLS {parsed.series_id}: {parsed.period_name} {parsed.year}"

    # Build summary with context
    summary = f"Series: {parsed.series_id}, Period: {parsed.period_name} {parsed.year}, Value: {parsed.value}"

    # Build metadata
    metadata: dict[str, Any] = {
        "content_type": "bls_timeseries_observation",
        "series_id": parsed.series_id,
        "year": parsed.year,
        "period": parsed.period,
        "period_name": parsed.period_name,
        "value": parsed.value,
        "footnotes": parsed.footnotes,
        "frequency": "monthly" if parsed.period.startswith("M") else "quarterly" if parsed.period.startswith("Q") else "annual",
        "source": "Bureau of Labor Statistics (BLS)",
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
            canonical_url=f"https://www.bls.gov/data/",
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


class BlsTimeseriesConnector:
    """Fetch US macro time series data from BLS Public Data API v2.

    This connector retrieves time series observations from the BLS Public Data
    API v2 endpoint, covering key macro indicators like CPI, payrolls, unemployment,
    average hourly earnings, and JOLTS.

    Usage:
        The cursor should contain a comma-separated list of series IDs.
        If no cursor is provided, the connector uses DEFAULT_SERIES.

        Example series IDs:
            - CUSR0000SA0: CPI headline
            - CUSR0000SA0L1E: CPI core
            - CES0000000001: Nonfarm payrolls
            - LNS14000000: Unemployment rate
            - CES0500000003: Average hourly earnings
            - JTS000000000000000JOL: JOLTS job openings
            - JTS000000000000000HIL: JOLTS hires
            - JTS000000000000000QUR: JOLTS quits rate

    Registration Key:
        The BLS API registration key is optional. If set in the BLS_API_KEY
        environment variable, it will be included in requests to avoid rate limits.

    Pagination:
        This connector returns all observations for the requested series in a
        single page. No next_cursor is provided; the connector always fetches
        the latest available data for the requested series.

    API Limits:
        - Maximum 50 series per request (BLS v2 limit)
        - Maximum 20 years per request (BLS v2 limit)
        - The connector enforces the 50-series limit.
    """

    name = CONNECTOR_NAME
    source = SOURCE_NAME
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=8.0,
    )
    rate_limit_policy = RateLimitPolicy(concurrency=1, burst=1)

    # Maximum series per request (BLS v2 limit)
    MAX_SERIES_PER_REQUEST = 50

    def __init__(
        self,
        *,
        transport: AsyncHttpTransport,
        startyear: str | None = None,
        endyear: str | None = None,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
            startyear: Optional start year (4-digit year). If not provided,
                fetches all available data.
            endyear: Optional end year (4-digit year). If not provided,
                fetches all available data.
        """
        self._transport = transport
        self._startyear = startyear
        self._endyear = endyear

    def _get_api_key(self) -> str | None:
        """Get the BLS API registration key from environment.

        Returns:
            The API key if BLS_API_KEY is set, otherwise None.
        """
        return os.environ.get("BLS_API_KEY")

    def _build_request_params(self, series_ids: list[str]) -> dict[str, str]:
        """Build request parameters for the BLS API.

        Args:
            series_ids: List of series IDs to fetch.

        Returns:
            A dictionary of request parameters.

        Raises:
            ValueError: If more than MAX_SERIES_PER_REQUEST are provided.
        """
        if len(series_ids) > self.MAX_SERIES_PER_REQUEST:
            raise ValueError(
                f"Cannot request more than {self.MAX_SERIES_PER_REQUEST} series "
                f"in a single request (got {len(series_ids)})"
            )

        params = {
            "seriesid": ",".join(series_ids),
        }

        # Add optional year range
        if self._startyear:
            params["startyear"] = self._startyear
        if self._endyear:
            params["endyear"] = self._endyear

        # Add registration key if available
        api_key = self._get_api_key()
        if api_key:
            params["registrationkey"] = api_key

        return params

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of BLS time series observations.

        Args:
            cursor: Optional comma-separated list of series IDs. If not provided,
                uses DEFAULT_SERIES.
            since: Optional since timestamp (not used for this connector).

        Returns:
            A PageResult containing BLS observations for the requested series.

        Raises:
            ValueError: If API returns unexpected status or invalid format.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del since  # Not used for this connector

        # Parse cursor for series IDs
        if cursor:
            series_ids = [s.strip() for s in cursor.split(",") if s.strip()]
        else:
            series_ids = list(DEFAULT_SERIES)

        if not series_ids:
            raise ValueError("No series IDs provided in cursor and DEFAULT_SERIES is empty")

        # Build request parameters
        params = self._build_request_params(series_ids)

        # Make the request
        response = await self._transport.send(
            HttpRequest(
                method="POST",
                url=BASE_URL,
                params=params,
                headers={"Content-Type": "application/json"},
            )
        )

        # Handle response status codes
        if 500 <= response.status_code < 600:
            raise RecoverableConnectorError(
                f"BLS API returned {response.status_code} for {response.url}"
            )
        if 400 <= response.status_code < 500:
            raise ValueError(
                f"BLS API returned {response.status_code} for {response.url}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected BLS API status code {response.status_code} for {response.url}"
            )

        # Parse the JSON response
        json_text = response.text()

        # Parse observations
        observations = parse_bls_series_json(json_text, series_ids)

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_bls_observation(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        # Sort items by series_id and date for deterministic ordering
        items.sort(key=lambda x: (x.metadata["series_id"], x.published_at))

        # This connector returns all data in a single page
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)