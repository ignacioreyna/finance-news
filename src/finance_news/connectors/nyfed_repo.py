"""NY Fed repo/reverse repo connector."""

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

CONNECTOR_NAME = "nyfed_repo"
SOURCE_NAME = "nyfed"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://markets.newyorkfed.org/api"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for repo operations

# NY Fed is the primary source for repo/reverse repo operations
# FRED RRPONTSYD series is a proxy/fallback only
DATA_CLASSIFICATION = "primary"
PROXY_SOURCES = ["FRED"]


@dataclass(frozen=True)
class ParsedNyfedRepoOperation:
    """A parsed repo/reverse repo operation from the NY Fed Markets API."""

    operation_date: str  # YYYY-MM-DD format
    operation_type: str  # "ON_RRP" or "SRF_REPO"
    amount_submitted: float
    amount_accepted: float
    award_rate: float
    number_counterparties: int | None


def parse_nyfed_repo_response(
    response_data: dict[str, Any],
) -> list[ParsedNyfedRepoOperation]:
    """Parse a NY Fed repo/reverse repo API response into operations.

    Args:
        response_data: The JSON response from the NY Fed Markets API.

    Returns:
        A list of parsed repo/reverse repo operations.

    Raises:
        ValueError: If the response format is invalid.
    """
    operations = response_data.get("repoOperations", [])
    if not isinstance(operations, list):
        raise ValueError(f"Expected 'repoOperations' to be a list, got {type(operations)}")

    parsed_ops = []
    for entry in operations:
        operation_date = entry.get("operationDate")
        operation_type = entry.get("operationType")
        amount_submitted = entry.get("amountSubmitted")
        amount_accepted = entry.get("amountAccepted")
        award_rate = entry.get("awardRate")
        number_counterparties = entry.get("numberCounterparties")

        if not isinstance(operation_date, str):
            raise ValueError(f"Invalid operationDate: {operation_date!r}")

        if not isinstance(operation_type, str):
            raise ValueError(f"Invalid operationType: {operation_type!r}")

        if not isinstance(amount_accepted, (int, float)):
            raise ValueError(f"Invalid amountAccepted: {amount_accepted!r}")

        if not isinstance(award_rate, (int, float)):
            raise ValueError(f"Invalid awardRate: {award_rate!r}")

        if not isinstance(amount_submitted, (int, float)):
            raise ValueError(f"Invalid amountSubmitted: {amount_submitted!r}")

        if number_counterparties is not None and not isinstance(number_counterparties, (int, float)):
            raise ValueError(f"Invalid numberCounterparties: {number_counterparties!r}")

        parsed_ops.append(
            ParsedNyfedRepoOperation(
                operation_date=operation_date,
                operation_type=operation_type,
                amount_submitted=float(amount_submitted),
                amount_accepted=float(amount_accepted),
                award_rate=float(award_rate),
                number_counterparties=int(number_counterparties) if number_counterparties is not None else None,
            )
        )

    return parsed_ops


def normalize_nyfed_repo_operation(
    *,
    parsed: ParsedNyfedRepoOperation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed NY Fed repo/reverse repo operation into a SourceItem.

    Args:
        parsed: The parsed operation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the repo/reverse repo operation.
    """
    # Parse the operation_date (assume NY Fed returns dates in YYYY-MM-DD format)
    # NY Fed dates are in local time, but we treat them as midnight UTC
    try:
        year, month, day = map(int, parsed.operation_date.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid operation_date format: {parsed.operation_date!r}") from exc

    # Map operation_type to normalized type field
    if parsed.operation_type == "ON_RRP":
        normalized_type = "on_rrp"
        operation_name = "ON RRP"
    elif parsed.operation_type == "SRF_REPO":
        normalized_type = "srf_repo"
        operation_name = "Standing Repo Facility"
    else:
        normalized_type = parsed.operation_type.lower()
        operation_name = parsed.operation_type

    # Build title with key information
    counterparties_str = f", {parsed.number_counterparties} counterparties" if parsed.number_counterparties is not None else ""
    title = (
        f"NY Fed {operation_name}: ${parsed.amount_accepted:.1f}B accepted at {parsed.award_rate:.2f}% "
        f"on {parsed.operation_date}{counterparties_str}"
    )

    # Build summary with context
    summary = (
        f"NY Fed {operation_name} on {parsed.operation_date}: "
        f"${parsed.amount_accepted:.1f}B accepted at {parsed.award_rate:.2f}%, "
        f"${parsed.amount_submitted:.1f}B submitted"
    )
    if parsed.number_counterparties is not None:
        summary += f", {parsed.number_counterparties} counterparties"

    # Build metadata including data classification
    item_metadata: dict[str, Any] = {
        "content_type": "repo_operation",
        "operation_date": parsed.operation_date,
        "type": normalized_type,
        "amount_accepted": parsed.amount_accepted,
        "amount_submitted": parsed.amount_submitted,
        "award_rate": parsed.award_rate,
        "number_counterparties": parsed.number_counterparties,
        "data_classification": DATA_CLASSIFICATION,
        "proxy_sources": PROXY_SOURCES,
    }

    # Build external_id from operation type and date
    external_id = f"{normalized_type}_{parsed.operation_date}"

    return SourceItem(
        external_id=external_id,
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


class NyfedRepoConnector:
    """Fetch repo/reverse repo operations from the NY Fed Markets API.

    This connector fetches operations from:
    - ON RRP (Overnight Reverse Repo Facility)
    - SRF (Standing Repo Facility)

    Key data points:
    - operation date
    - operation type (ON RRP / SRF repo)
    - amount accepted and submitted
    - award rate
    - number of counterparties/participants (when available)

    The NY Fed Markets API is the primary source for repo/reverse repo operations.
    FRED RRPONTSYD series should only be used as a proxy/fallback when the NY Fed
    API is unavailable.

    Pagination:
        Simple connector - fetches all available operations in a single page.
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
            limit: Maximum number of operations to fetch.
        """
        self._transport = transport
        self._limit = limit

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of repo/reverse repo operations.

        Args:
            cursor: Not used for repo connector (included for protocol compatibility).
            since: Not used for repo connector (included for protocol compatibility).

        Returns:
            A PageResult containing the repo/reverse repo operations.

        Raises:
            ValueError: If API returns unexpected status or invalid response.
            RecoverableConnectorError: For recoverable HTTP errors (5xx).
        """
        del cursor, since  # Not used for this connector

        # Build the API URL to fetch repo operations
        url = f"{BASE_URL}/repo/operations/last/{self._limit}.json"

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

        # Parse the operations
        try:
            operations = parse_nyfed_repo_response(response_data)
        except ValueError as exc:
            raise ValueError(f"Failed to parse NY Fed repo response from {url}") from exc

        # Normalize each operation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for op in operations:
            item = normalize_nyfed_repo_operation(
                parsed=op,
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