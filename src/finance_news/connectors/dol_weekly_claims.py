"""DOL Weekly Claims connector.

This connector fetches official weekly unemployment claims data from the U.S. Department
of Labor (DOL) Employment and Training Administration (ETA). The data includes:

- Initial claims: New unemployment insurance claims filed during the week
- Continued claims: Total number of unemployed persons claiming benefits

The DOL publishes weekly claims data in HTML, Spreadsheet, and XML formats. This connector
prioritizes XML format when available, as it provides the most structured and parseable data.

FALLBACK BEHAVIOR:
==================
If DOL only publishes HTML/PDF for a given week (i.e., XML/spreadsheet format is not available),
this connector will raise a RecoverableConnectorError. The fallback strategy is to retry later
when the structured format becomes available. This is intentional because:

1. HTML parsing is fragile and breaks easily with minor markup changes
2. PDF parsing requires external dependencies (pypdf) and is error-prone for tabular data
3. The source typically publishes XML/spreadsheet within 24-48 hours of the HTML release
4. Losing one week of data is preferable to introducing parse errors that corrupt the pipeline

In production, the orchestrator should implement a delayed retry strategy for this connector
to handle the temporary unavailability of structured formats.

Source URL: https://oui.doleta.gov/unemploy/claims.asp
"""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
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

CONNECTOR_NAME = "dol_weekly_claims"
SOURCE_NAME = "dol"
PARSER_VERSION = "0.1.0"
DOL_CLAIMS_URL = "https://oui.doleta.gov/unemploy/claims.asp"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for weekly data

# Fallback documentation constant (used in tests to verify AC#3)
FALLBACK_BEHAVIOR_DOCUMENTED = """
FALLBACK BEHAVIOR FOR HTML/PDF-ONLY WEEKS:
When DOL only publishes HTML/PDF and XML/spreadsheet is unavailable, this connector
raises RecoverableConnectorError. The intended fallback strategy is delayed retry,
not attempting to parse HTML/PDF formats which are fragile and error-prone.
"""


@dataclass(frozen=True)
class ParsedDolWeeklyClaimsObservation:
    """A single DOL weekly claims observation.

    Attributes:
        series_type: Type of claims series ("initial" or "continued").
        week_ending: ISO week ending date (YYYY-MM-DD).
        value: Claims count for the week (integer).
        prior_week_revised: Revised value from the prior week, if available (None if not).
        seasonally_adjusted: Whether the data is seasonally adjusted (boolean).
    """

    series_type: str
    week_ending: str
    value: str
    prior_week_revised: str | None
    seasonally_adjusted: bool


def parse_dol_weekly_claims_xml(xml_text: str) -> list[ParsedDolWeeklyClaimsObservation]:
    """Parse DOL weekly claims XML text into structured observations.

    The XML format from DOL ETA contains weekly claims data with the following structure:
    - Root element with weekly claims data
    - Separate entries for initial and continued claims
    - Week ending dates and values
    - Prior week revisions when applicable

    Args:
        xml_text: Raw XML text from DOL weekly claims data source.

    Returns:
        List of parsed weekly claims observations, typically including both initial
        and continued claims for the most recent week(s).

    Raises:
        ValueError: If the XML format is invalid or required fields are missing.
    """
    # Try to parse the XML
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML format: {exc}") from exc

    observations: list[ParsedDolWeeklyClaimsObservation] = []

    # Try to find <observation> elements first (most common structure)
    for obs_element in root.iter("observation"):
        # Extract data from child elements
        series_type_elem = obs_element.find("series_type")
        week_ending_elem = obs_element.find("week_ending")
        value_elem = obs_element.find("value")
        prior_week_elem = obs_element.find("prior_week_revised")
        seasonal_elem = obs_element.find("seasonally_adjusted")

        if (
            series_type_elem is None
            or week_ending_elem is None
            or value_elem is None
            or series_type_elem.text is None
            or week_ending_elem.text is None
            or value_elem.text is None
        ):
            continue

        series_type = series_type_elem.text.strip().lower()
        week_ending = week_ending_elem.text.strip()
        value = value_elem.text.strip()
        prior_week_revised = prior_week_elem.text.strip() if prior_week_elem is not None and prior_week_elem.text else None
        seasonally_adjusted = (
            seasonal_elem is not None
            and seasonal_elem.text is not None
            and seasonal_elem.text.strip().lower() == "true"
        )

        # Validate series_type
        if series_type not in ("initial", "continued"):
            continue

        # Create observation
        observations.append(
            ParsedDolWeeklyClaimsObservation(
                series_type=series_type,
                week_ending=week_ending,
                value=value,
                prior_week_revised=prior_week_revised,
                seasonally_adjusted=seasonally_adjusted,
            )
        )

    # If we didn't find observations using <observation> elements,
    # try a more generic approach
    if not observations:
        # Look for any element with "series" or "type" in its tag or attributes
        for element in root.iter():
            # Check for data in attributes
            series_type = element.get("series_type") or element.get("type")
            week_ending = element.get("week_ending") or element.get("week") or element.get("date")
            value = element.get("value") or element.get("claims") or element.text
            prior_week_revised = element.get("prior_week_revised") or element.get("revised")
            seasonally_adjusted = element.get("seasonally_adjusted", "true").lower() == "true"

            # Skip if we don't have the minimum required fields
            if not all([series_type, week_ending, value]):
                continue

            # Validate series_type
            if series_type not in ("initial", "continued"):
                continue

            # Create observation
            observations.append(
                ParsedDolWeeklyClaimsObservation(
                    series_type=series_type,
                    week_ending=week_ending,
                    value=value,
                    prior_week_revised=prior_week_revised,
                    seasonally_adjusted=seasonally_adjusted,
                )
            )

    # If still no observations, raise an error
    if not observations:
        raise ValueError(
            "No weekly claims observations found in XML. "
            "The XML format may have changed or is not supported."
        )

    return observations


def _parse_week_ending(date_str: str) -> datetime:
    """Parse week ending date string to datetime.

    Args:
        date_str: Date string in various formats (e.g., "2025-06-14", "06/14/2025").

    Returns:
        Datetime representing the week ending date at midnight UTC.

    Raises:
        ValueError: If the date string is invalid.
    """
    # Try common date formats
    formats = [
        "%Y-%m-%d",  # ISO format
        "%m/%d/%Y",  # US format
        "%d/%m/%Y",  # European format
        "%Y%m%d",  # Compact format
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date string: {date_str}")


def _parse_value(value_str: str) -> int | None:
    """Parse claims value string to integer.

    Args:
        value_str: Numeric value string (e.g., "233000", "233,000").

    Returns:
        Parsed integer value, or None if the value is empty or invalid.
    """
    if not value_str or not value_str.strip():
        return None

    # Remove commas and other formatting
    cleaned = value_str.strip().replace(",", "").replace(" ", "")

    try:
        return int(cleaned)
    except ValueError:
        return None


def normalize_dol_weekly_claims_observations(
    *,
    observations: list[ParsedDolWeeklyClaimsObservation],
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> list[SourceItem]:
    """Normalize parsed DOL weekly claims observations into SourceItem objects.

    Each observation becomes a separate SourceItem with full provenance metadata.
    The metadata distinguishes between initial and continued claims series.

    Args:
        observations: List of parsed weekly claims observations.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per observation.
    """
    items: list[SourceItem] = []

    for obs in observations:
        # Build external_id
        external_id = f"dol_weekly_claims_{obs.series_type}_{obs.week_ending}"

        # Parse week ending for published_at
        try:
            published_at = _parse_week_ending(obs.week_ending)
        except ValueError:
            # If date parsing fails, skip this observation
            continue

        # Parse numeric values
        value = _parse_value(obs.value)
        prior_week_revised = _parse_value(obs.prior_week_revised) if obs.prior_week_revised else None

        # Build title
        if obs.series_type == "initial":
            title = f"Initial Unemployment Claims - Week Ending {obs.week_ending}"
        else:
            title = f"Continued Unemployment Claims - Week Ending {obs.week_ending}"

        # Build summary with available data
        summary_parts = [f"DOL weekly {obs.series_type} claims for week ending {obs.week_ending}"]
        if value is not None:
            summary_parts.append(f"Value: {value:,}")
        if prior_week_revised is not None:
            summary_parts.append(f"Prior week revised: {prior_week_revised:,}")
        if obs.seasonally_adjusted:
            summary_parts.append("(Seasonally Adjusted)")

        summary = ". ".join(summary_parts) + "."

        # Build metadata
        metadata: dict[str, object] = {
            "series_type": obs.series_type,
            "week_ending": obs.week_ending,
            "value": value,
            "prior_week_revised": prior_week_revised,
            "seasonally_adjusted": obs.seasonally_adjusted,
            "fuente": "DOL/ETA",
        }

        # Build provenance
        provenance = Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=DOL_CLAIMS_URL,
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
            body=None,  # XML data doesn't have a full body
            summary=summary,
            url=DOL_CLAIMS_URL,
            metadata=metadata,
            provenance=provenance,
            freshness=freshness,
        )

        items.append(item)

    return items


class DolWeeklyClaimsConnector:
    """Connector for DOL Weekly Unemployment Claims data.

    Fetches official weekly unemployment claims data from the U.S. Department of Labor
    (DOL) Employment and Training Administration (ETA). The data includes both initial
    and continued claims at the national level.

    This connector prioritizes XML format when available, as it provides the most
    structured and parseable data. When only HTML/PDF is available, it raises
    RecoverableConnectorError to trigger a delayed retry rather than attempting
    fragile HTML/PDF parsing.

    This connector follows the standard pattern:
    - Async HTTP client via injected AsyncHttpTransport
    - Pure parser functions (parse_dol_weekly_claims_xml, normalize_dol_weekly_claims_observations)
    - Frozen dataclasses for intermediate representations
    - Proper error handling (RecoverableConnectorError for 4xx/5xx)
    - Documented fallback behavior for HTML/PDF-only weeks
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
        """Initialize the DOL weekly claims connector.

        Args:
            transport: Async HTTP client for fetching the data.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch and parse DOL weekly claims data.

        Args:
            cursor: Not used (DOL weekly claims doesn't support pagination).
            since: Not used (latest weekly data is fetched each time).

        Returns:
            PageResult containing weekly claims observations from the XML data.
            The XML typically contains both initial and continued claims for the
            most recent week(s). has_more is False and next_cursor is None because
            there's no pagination.

        Raises:
            RecoverableConnectorError: For 4xx/5xx HTTP errors (transient) or when
                only HTML/PDF is available (fallback to retry later).
            ValueError: For unexpected status codes or XML parsing errors.
        """
        del since  # Not used

        # Fetch the weekly claims data
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=DOL_CLAIMS_URL,
                headers={"Accept": "application/xml, text/xml, text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(
                f"DOL weekly claims page not found at {DOL_CLAIMS_URL}"
            )
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"DOL returned {response.status_code} for {DOL_CLAIMS_URL}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected DOL status code {response.status_code} for {DOL_CLAIMS_URL}"
            )

        # Check content type - if HTML only, trigger fallback
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type.lower() and "xml" not in content_type.lower():
            # This indicates only HTML is available - trigger fallback
            raise RecoverableConnectorError(
                f"DOL only published HTML format for weekly claims (XML/spreadsheet unavailable). "
                f"Fallback: retry later when structured format becomes available. "
                f"URL: {DOL_CLAIMS_URL}"
            )

        # Try to decode as XML or CSV
        xml_text = None
        csv_text = None

        if "xml" in content_type.lower():
            # Try XML
            try:
                xml_text = response.text(encoding="utf-8")
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    xml_text = response.text(encoding="iso-8859-1")
                except UnicodeDecodeError as exc:
                    raise ValueError(f"Failed to decode response as UTF-8 or ISO-8859-1: {exc}") from exc
        elif "csv" in content_type.lower():
            # Try CSV
            try:
                csv_text = response.text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    csv_text = response.text(encoding="iso-8859-1")
                except UnicodeDecodeError as exc:
                    raise ValueError(f"Failed to decode response as UTF-8 or ISO-8859-1: {exc}") from exc
        else:
            # Try XML first (most common for DOL)
            try:
                xml_text = response.text(encoding="utf-8")
            except UnicodeDecodeError:
                # Try CSV
                try:
                    csv_text = response.text(encoding="utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError(f"Failed to decode response as UTF-8: {exc}") from exc

        # Parse data
        observations: list[ParsedDolWeeklyClaimsObservation] = []

        if xml_text:
            try:
                observations = parse_dol_weekly_claims_xml(xml_text)
            except ValueError as exc:
                raise ValueError(f"Failed to parse DOL weekly claims XML: {exc}") from exc
        elif csv_text:
            # If CSV, convert to observation format
            try:
                observations = _parse_dol_weekly_claims_csv(csv_text)
            except ValueError as exc:
                raise ValueError(f"Failed to parse DOL weekly claims CSV: {exc}") from exc
        else:
            # Neither XML nor CSV - trigger fallback
            raise RecoverableConnectorError(
                f"DOL weekly claims data is not in XML or CSV format (likely HTML/PDF only). "
                f"Fallback: retry later when structured format becomes available. "
                f"Content-Type: {content_type}"
            )

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_dol_weekly_claims_observations(
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


def _parse_dol_weekly_claims_csv(csv_text: str) -> list[ParsedDolWeeklyClaimsObservation]:
    """Parse DOL weekly claims CSV text into structured observations.

    This is a fallback parser for when data is available as CSV instead of XML.

    Args:
        csv_text: Raw CSV text from DOL weekly claims data source.

    Returns:
        List of parsed weekly claims observations.

    Raises:
        ValueError: If the CSV format is invalid or required fields are missing.
    """
    # Normalize line endings
    normalized_text = csv_text.replace("\r\n", "\n").replace("\r", "\n")

    # Parse CSV
    reader = csv.reader(normalized_text.splitlines())

    # Read header
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("Empty CSV file")

    # Convert header to lowercase for matching
    header_lower = [h.lower() for h in header]

    # Try to identify columns - more specific matching first
    series_idx = None
    week_idx = None
    value_idx = None
    revised_idx = None

    for i, h in enumerate(header_lower):
        # Most specific matches first
        if "series_type" in h or h == "series_type":
            series_idx = i
        elif "week_ending" in h or h == "week_ending":
            week_idx = i
        elif "prior_week_revised" in h or "prior_week" in h:
            revised_idx = i
        # Fallback to partial matches
        elif series_idx is None and ("series" in h or "type" in h):
            series_idx = i
        elif week_idx is None and ("week" in h or "date" in h or "ending" in h):
            week_idx = i
        elif value_idx is None and ("value" in h or "claims" in h):
            value_idx = i
        elif revised_idx is None and ("prior" in h or "revised" in h):
            revised_idx = i

    if series_idx is None or week_idx is None or value_idx is None:
        raise ValueError(
            f"CSV header missing required columns. Header: {header}"
        )

    # Parse rows
    observations: list[ParsedDolWeeklyClaimsObservation] = []
    for row_num, row in enumerate(reader, start=2):
        if len(row) < max(series_idx, week_idx, value_idx) + 1:
            continue

        series_type = row[series_idx].strip().lower()
        week_ending = row[week_idx].strip()
        value = row[value_idx].strip()
        prior_week_revised = row[revised_idx].strip() if revised_idx is not None else None

        # Validate series_type
        if series_type not in ("initial", "continued"):
            continue

        observations.append(
            ParsedDolWeeklyClaimsObservation(
                series_type=series_type,
                week_ending=week_ending,
                value=value,
                prior_week_revised=prior_week_revised if prior_week_revised else None,
                seasonally_adjusted=True,  # Default assumption
            )
        )

    if not observations:
        raise ValueError("No valid weekly claims observations found in CSV")

    return observations