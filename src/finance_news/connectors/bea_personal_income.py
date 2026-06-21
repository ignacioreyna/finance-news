"""BEA NIPA Personal Income (T20600) connector for US macro economic time series.

This connector consumes official BEA (Bureau of Economic Analysis) Personal Income
monthly data from the NIPA (National Income and Product Accounts) dataset, Table T20600.

Data Source:
    BEA API - https://apps.bea.gov/api/data/
    API Documentation: https://apps.bea.gov/API/docs/index.htm

API Key:
    The BEA API requires a UserID (36-character API key). The connector reads the
    key from the BEA_API_KEY environment variable if available. For testing,
    the key is optional - tests run without a live key using a fake transport.

API Response Format:
    {
        "BEAAPI": {
            "Results": {
                "Data": [
                    {
                        "TableName": "T20600",
                        "SeriesCode": "A069RC",
                        "LineNumber": "1",
                        "LineDescription": "Personal income",
                        "TimePeriod": "2026M05",
                        "DataValue": "21500.5",
                        "CL_UNIT": "Billions of Dollars",
                        "UNIT_NUM": "3"
                    }
                ]
            }
        }
    }

Key Fields:
    - TimePeriod: Period string (YYYYMM for monthly, YYYYQX for quarterly, YYYY for annual)
    - DataValue: The observation value (as string)
    - CL_UNIT: Unit description (e.g., "Billions of Dollars")
    - UNIT_NUM: Unit multiplier code
    - LineDescription: Description of the data series

Pagination:
    This connector returns all available observations in a single page.
    The connector fetches data for a specified year or year range.

Error Handling:
    - 5xx errors: RecoverableConnectorError (retryable)
    - 4xx errors: ValueError (non-retryable, indicates client error)
    - 1xx/3xx errors: ValueError (unexpected status)
    - Malformed JSON: ValueError (invalid response format)
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

CONNECTOR_NAME = "bea_personal_income"
SOURCE_NAME = "bea"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://apps.bea.gov/api/data/"
DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days for monthly data

# BEA NIPA Table for Personal Income (Monthly)
TABLE_NAME = "T20600"
DATA_SET_NAME = "NIPA"
FREQUENCY = "M"  # Monthly


@dataclass(frozen=True)
class ParsedBeaObservation:
    """A single parsed BEA observation from the API."""

    table_name: str
    series_code: str
    line_number: str
    line_description: str
    time_period: str
    data_value: float
    cl_unit: str
    unit_num: str


def parse_bea_time_period(time_period: str) -> datetime:
    """Parse BEA TimePeriod string into a datetime.

    Args:
        time_period: BEA TimePeriod string (YYYYMM for monthly, YYYYQX for quarterly,
            YYYY for annual).

    Returns:
        A datetime object representing the start of the period.

    Raises:
        ValueError: If the period format is invalid.
    """
    if len(time_period) == 7 and time_period[4] == "M":
        # Monthly: YYYYMXX (e.g., "2026M05")
        year = int(time_period[:4])
        month = int(time_period[5:])
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month in TimePeriod: {time_period}")
        return datetime(year, month, 1, tzinfo=timezone.utc)
    elif len(time_period) == 7 and time_period[4] == "Q":
        # Quarterly: YYYYQXX (e.g., "2026Q02")
        year = int(time_period[:4])
        quarter = int(time_period[5:])
        if quarter < 1 or quarter > 4:
            raise ValueError(f"Invalid quarter in TimePeriod: {time_period}")
        month = (quarter - 1) * 3 + 1
        return datetime(year, month, 1, tzinfo=timezone.utc)
    elif len(time_period) == 4:
        # Annual: YYYY
        year = int(time_period)
        return datetime(year, 1, 1, tzinfo=timezone.utc)
    else:
        raise ValueError(f"Unsupported TimePeriod format: {time_period}")


def parse_bea_series_json(
    json_text: str,
    table_name: str,
) -> list[ParsedBeaObservation]:
    """Parse a BEA API JSON response into observations.

    Args:
        json_text: Raw JSON text from the BEA API.
        table_name: The expected table name (for validation).

    Returns:
        A list of parsed observations.

    Raises:
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    # Check for BEAAPI wrapper
    beaapi = data.get("BEAAPI")
    if not isinstance(beaapi, dict):
        raise ValueError("Missing or invalid 'BEAAPI' field in response")

    # Extract Results.Data array
    results = beaapi.get("Results")
    if not isinstance(results, dict):
        raise ValueError("Missing or invalid 'Results' field in BEAAPI")

    data_list = results.get("Data")
    if data_list is None:
        # Empty result is valid (no data available)
        return []

    if not isinstance(data_list, list):
        raise ValueError(f"Expected 'Data' to be a list, got {type(data_list)}")

    observations = []
    for point in data_list:
        # Validate required fields
        table = point.get("TableName")
        series_code = point.get("SeriesCode")
        line_number = point.get("LineNumber")
        line_description = point.get("LineDescription")
        time_period = point.get("TimePeriod")
        data_value_str = point.get("DataValue")
        cl_unit = point.get("CL_UNIT")
        unit_num = point.get("UNIT_NUM")

        # Skip if required fields are missing
        if not time_period or data_value_str is None:
            continue

        # Parse value
        try:
            data_value = float(data_value_str)
        except (ValueError, TypeError):
            continue  # Skip invalid values

        observations.append(
            ParsedBeaObservation(
                table_name=table or table_name,
                series_code=series_code or "",
                line_number=line_number or "",
                line_description=line_description or "",
                time_period=time_period,
                data_value=data_value,
                cl_unit=cl_unit or "",
                unit_num=unit_num or "",
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
    published_at = parse_bea_time_period(parsed.time_period)

    # Build external_id using series code and time period
    external_id = f"{parsed.series_code}_{parsed.time_period}"

    # Build title with description and date
    title = f"BEA {parsed.line_description}: {parsed.time_period}"

    # Build summary with context
    summary = (
        f"Series: {parsed.line_description}, Period: {parsed.time_period}, "
        f"Value: {parsed.data_value}, Units: {parsed.cl_unit}"
    )

    # Build metadata
    metadata: dict[str, Any] = {
        "content_type": "bea_nipa_observation",
        "table_name": parsed.table_name,
        "series_code": parsed.series_code,
        "line_number": parsed.line_number,
        "line_description": parsed.line_description,
        "time_period": parsed.time_period,
        "data_value": parsed.data_value,
        "cl_unit": parsed.cl_unit,
        "unit_num": parsed.unit_num,
        "frequency": "monthly" if "M" in parsed.time_period else "quarterly" if "Q" in parsed.time_period else "annual",
        "fuente": "BEA NIPA T20600",
        "source": "Bureau of Economic Analysis (BEA)",
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
            canonical_url="https://www.bea.gov/data/income-saving/personal-income",
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


class BeaPersonalIncomeConnector:
    """Fetch US Personal Income monthly data from BEA NIPA T20600.

    This connector retrieves monthly Personal Income observations from the BEA API
    for the NIPA dataset, Table T20600.

    Usage:
        The connector fetches data for a specified year or year range.
        Use the constructor's year parameter to specify the year(s) to fetch.

    API Key:
        The BEA API requires a UserID (36-character API key). If set in the
        BEA_API_KEY environment variable, it will be included in requests.
        For testing, the key is optional - tests run without a live key.

    Pagination:
        This connector returns all observations for the requested year(s) in a
        single page. No next_cursor is provided; the connector always fetches
        all available data for the specified year(s).

    Error Handling:
        - 5xx errors: RecoverableConnectorError (retryable)
        - 4xx errors: ValueError (non-retryable, indicates client error)
        - 1xx/3xx errors: ValueError (unexpected status)
        - Malformed JSON: ValueError (invalid response format)
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
        year: str | None = None,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
            year: Optional year (4-digit year, or comma-separated years). If not
                provided, fetches current year data.
        """
        self._transport = transport
        self._year = year

    def _get_api_key(self) -> str | None:
        """Get the BEA API key from environment.

        Returns:
            The API key if BEA_API_KEY is set, otherwise None.
        """
        return os.environ.get("BEA_API_KEY")

    def _build_request_params(self) -> dict[str, str]:
        """Build request parameters for the BEA API.

        Returns:
            A dictionary of request parameters.

        Raises:
            ValueError: If API key is not available.
        """
        params = {
            "method": "GetData",
            "DataSetName": DATA_SET_NAME,
            "TableName": TABLE_NAME,
            "Frequency": FREQUENCY,
        }

        # Add year parameter
        if self._year:
            params["Year"] = self._year
        else:
            # Default to current year
            params["Year"] = str(datetime.now(timezone.utc).year)

        # Add API key if available
        api_key = self._get_api_key()
        if api_key:
            params["UserID"] = api_key

        return params

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of BEA Personal Income observations.

        Args:
            cursor: Optional parameter (not used for this connector).
            since: Optional since timestamp (not used for this connector).

        Returns:
            A PageResult containing BEA Personal Income observations.

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
                headers={"Accept": "application/json"},
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
        observations = parse_bea_series_json(json_text, TABLE_NAME)

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

        # Sort items by time period for deterministic ordering
        items.sort(key=lambda x: x.published_at)

        # This connector returns all data in a single page
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)