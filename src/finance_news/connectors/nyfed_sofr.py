"""NY Fed SOFR connector."""

from __future__ import annotations

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

CONNECTOR_NAME = "nyfed_sofr"
SOURCE_NAME = "nyfed"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for SOFR data

# NY Fed SOFR is the primary source for SOFR data
# FRED SOFR series (https://fred.stlouisfed.org/series/SOFR) is a proxy/fallback only
DATA_CLASSIFICATION = "primary"
PROXY_SOURCES = ["FRED"]  # Alternative sources that are NOT primary


@dataclass(frozen=True)
class ParsedNyfedSofrObservation:
    """A parsed SOFR observation from the NY Fed Markets API."""

    effective_date: str  # YYYY-MM-DD format
    percent_rate: float
    volume_in_billions: float
    percentile_1: float
    percentile_25: float
    percentile_75: float
    percentile_99: float


def parse_nyfed_sofr_response(
    response_data: dict[str, Any],
) -> list[ParsedNyfedSofrObservation]:
    """Parse a NY Fed SOFR API response into observations.

    Args:
        response_data: The JSON response from the NY Fed Markets API.

    Returns:
        A list of parsed SOFR observations.

    Raises:
        ValueError: If the response format is invalid.
    """
    ref_rates = response_data.get("refRates", [])
    if not isinstance(ref_rates, list):
        raise ValueError(f"Expected 'refRates' to be a list, got {type(ref_rates)}")

    observations = []
    for entry in ref_rates:
        effective_date = entry.get("effectiveDate")
        percent_rate = entry.get("percentRate")
        volume_in_billions = entry.get("volumeInBillions")
        percentile_1 = entry.get("percentPercentile1")
        percentile_25 = entry.get("percentPercentile25")
        percentile_75 = entry.get("percentPercentile75")
        percentile_99 = entry.get("percentPercentile99")

        if not isinstance(effective_date, str):
            raise ValueError(f"Invalid effectiveDate: {effective_date!r}")

        if not isinstance(percent_rate, (int, float)):
            raise ValueError(f"Invalid percentRate: {percent_rate!r}")

        if not isinstance(volume_in_billions, (int, float)):
            raise ValueError(f"Invalid volumeInBillions: {volume_in_billions!r}")

        if not isinstance(percentile_1, (int, float)):
            raise ValueError(f"Invalid percentPercentile1: {percentile_1!r}")

        if not isinstance(percentile_25, (int, float)):
            raise ValueError(f"Invalid percentPercentile25: {percentile_25!r}")

        if not isinstance(percentile_75, (int, float)):
            raise ValueError(f"Invalid percentPercentile75: {percentile_75!r}")

        if not isinstance(percentile_99, (int, float)):
            raise ValueError(f"Invalid percentPercentile99: {percentile_99!r}")

        observations.append(
            ParsedNyfedSofrObservation(
                effective_date=effective_date,
                percent_rate=float(percent_rate),
                volume_in_billions=float(volume_in_billions),
                percentile_1=float(percentile_1),
                percentile_25=float(percentile_25),
                percentile_75=float(percentile_75),
                percentile_99=float(percentile_99),
            )
        )

    return observations


def normalize_nyfed_sofr_observation(
    *,
    parsed: ParsedNyfedSofrObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed NY Fed SOFR observation into a SourceItem.

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the SOFR observation.
    """
    # Parse the effective_date (assume NY Fed returns dates in YYYY-MM-DD format)
    # NY Fed dates are in local time, but we treat them as midnight UTC
    try:
        year, month, day = map(int, parsed.effective_date.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid effective_date format: {parsed.effective_date!r}") from exc

    # Build title with SOFR rate, volume, and date
    title = (
        f"SOFR: {parsed.percent_rate}% on {parsed.effective_date} "
        f"(Volume: ${parsed.volume_in_billions:.0f}B)"
    )

    # Build summary with context including percentiles
    summary = (
        f"SOFR rate: {parsed.percent_rate}% on {parsed.effective_date}, "
        f"volume: ${parsed.volume_in_billions:.0f}B, "
        f"percentiles: 1st={parsed.percentile_1}%, 25th={parsed.percentile_25}%, "
        f"75th={parsed.percentile_75}%, 99th={parsed.percentile_99}%"
    )

    # Build metadata including data classification
    item_metadata: dict[str, Any] = {
        "content_type": "sofr_observation",
        "rate": parsed.percent_rate,
        "volume_in_billions": parsed.volume_in_billions,
        "percentile_1": parsed.percentile_1,
        "percentile_25": parsed.percentile_25,
        "percentile_75": parsed.percentile_75,
        "percentile_99": parsed.percentile_99,
        "data_classification": DATA_CLASSIFICATION,
        "proxy_sources": PROXY_SOURCES,
    }

    return SourceItem(
        external_id=f"SOFR_{parsed.effective_date}",
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


class NyfedSofrConnector:
    """Fetch SOFR rates from the NY Fed Markets API.

    This connector fetches Secured Overnight Financing Rate (SOFR) data:
    - SOFR rate (percentRate)
    - Volume in billions (volumeInBillions)
    - Percentiles: 1st, 25th, 75th, 99th

    The NY Fed Markets API is the primary source for SOFR data.
    FRED SOFR series (https://fred.stlouisfed.org/series/SOFR) should only
    be used as a proxy/fallback when the NY Fed API is unavailable.

    Pagination:
        Simple connector - fetches all available observations in a single page.
        No cursor-based pagination is needed for this source.
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
            limit: Maximum number of observations to fetch.
        """
        self._transport = transport
        self._limit = limit

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of SOFR observations.

        Args:
            cursor: Not used for SOFR connector (included for protocol compatibility).
            since: Not used for SOFR connector (included for protocol compatibility).

        Returns:
            A PageResult containing the SOFR observations.

        Raises:
            ValueError: If API returns unexpected status or invalid response.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del cursor, since  # Not used for this connector

        # Build the API URL to fetch the last N observations
        url = f"{BASE_URL}/last/{self._limit}.json"

        # Make the HTTP request
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=url,
                headers={"Accept": "application/json"},
            )
        )

        # Handle response status codes
        if 500 <= response.status_code < 600:
            raise RecoverableConnectorError(
                f"NY Fed API returned {response.status_code} for {url}"
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected NY Fed status code {response.status_code} for {url}")

        # Parse the JSON response
        import json

        try:
            response_data = json.loads(response.text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from {url}") from exc

        # Parse the observations
        try:
            observations = parse_nyfed_sofr_response(response_data)
        except ValueError as exc:
            raise ValueError(f"Failed to parse NY Fed SOFR response from {url}") from exc

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_nyfed_sofr_observation(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        # No pagination for this connector
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)