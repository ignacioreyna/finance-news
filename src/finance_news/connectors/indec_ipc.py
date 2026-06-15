"""INDEC IPC connector.

This connector fetches Argentina's official Consumer Price Index (IPC) data from INDEC.
The IPC data is published as a CSV file containing the headline index and various
category breakdowns (COICOP divisions and special categories like core, seasonal,
and regulated).

Note on IPC Núcleo: According to INDEC's official methodology (PDF documentation),
IPC núcleo has a defined methodology but is NOT published as a dedicated, downloadable
series in CSV/XLS format from the main IPC page. The CSV file only includes general
categories (Estacional, Regulados, B, S) but not the specific "Núcleo" series that
would match the methodology document. This is a known gap in INDEC's data publishing.
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

CONNECTOR_NAME = "indec_ipc"
SOURCE_NAME = "indec"
PARSER_VERSION = "0.1.0"
IPC_CSV_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours


@dataclass(frozen=True)
class ParsedIpcObservation:
    """A single IPC observation from the CSV.

    Attributes:
        code: Category code (e.g., "0" for general, "01" for divisions, empty for special)
        description: Category description (e.g., "NIVEL GENERAL", "Alimentos y bebidas no alcohólicas")
        classifier: Classification type (e.g., "Nivel general y divisiones COICOP", "Categorias")
        period: Period as YYYYMM string (e.g., "201612", "202601")
        index_value: IPC index value (decimal with comma separator)
        monthly_variation: Monthly variation percentage (may be "NA")
        annual_variation: Annual variation percentage (may be "NA")
        region: Geographic region (e.g., "GBA", "Nacional", "Pampeana")
    """

    code: str
    description: str
    classifier: str
    period: str
    index_value: str
    monthly_variation: str
    annual_variation: str
    region: str


def parse_ipc_csv(csv_text: str) -> list[ParsedIpcObservation]:
    """Parse INDEC IPC CSV text into structured observations.

    Args:
        csv_text: Raw CSV text from INDEC (ISO-8859-1 encoding, semicolon-delimited,
            CRLF line endings, decimal comma).

    Returns:
        List of parsed IPC observations, excluding the header row.

    Raises:
        ValueError: If the CSV format is invalid or required fields are missing.
    """
    # Normalize line endings
    normalized_text = csv_text.replace("\r\n", "\n").replace("\r", "\n")

    # Parse CSV with semicolon delimiter
    reader = csv.reader(normalized_text.splitlines(), delimiter=";")

    # Read and validate header
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("Empty CSV file")

    expected_header = [
        "Codigo",
        "Descripcion",
        "Clasificador",
        "Periodo",
        "Indice_IPC",
        "v_m_IPC",
        "v_i_a_IPC",
        "Region",
    ]
    if header != expected_header:
        raise ValueError(f"Unexpected CSV header: {header}")

    # Parse rows
    observations: list[ParsedIpcObservation] = []
    for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
        if len(row) != 8:
            raise ValueError(f"Row {row_num} has {len(row)} fields, expected 8")

        code, description, classifier, period, index_value, monthly_variation, annual_variation, region = row

        # Skip empty rows
        if not any(row):
            continue

        observations.append(
            ParsedIpcObservation(
                code=code,
                description=description,
                classifier=classifier,
                period=period,
                index_value=index_value,
                monthly_variation=monthly_variation,
                annual_variation=annual_variation,
                region=region,
            )
        )

    return observations


def _parse_period(period_str: str) -> datetime:
    """Parse INDEC period string (YYYYMM) to datetime.

    Args:
        period_str: Period string like "201612" or "202601".

    Returns:
        Datetime representing the first day of the period at midnight UTC.

    Raises:
        ValueError: If the period string is invalid.
    """
    if len(period_str) != 6 or not period_str.isdigit():
        raise ValueError(f"Invalid period format: {period_str}")

    year = int(period_str[:4])
    month = int(period_str[4:6])

    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month in period: {period_str}")

    return datetime(year, month, 1, tzinfo=timezone.utc)


def _parse_decimal_value(value_str: str) -> float | None:
    """Parse INDEC decimal value (comma separator) to float.

    Args:
        value_str: Decimal value like "11594,5499" or "NA".

    Returns:
        Parsed float value, or None if the value is "NA" or empty.
    """
    if not value_str or value_str.upper() == "NA":
        return None

    # Replace comma with dot for float parsing
    return float(value_str.replace(",", "."))


def normalize_ipc_observations(
    *,
    observations: list[ParsedIpcObservation],
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> list[SourceItem]:
    """Normalize parsed IPC observations into SourceItem objects.

    Each observation becomes a separate SourceItem with full provenance metadata.

    Args:
        observations: List of parsed IPC observations.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor value.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        List of normalized SourceItem objects, one per observation.
    """
    items: list[SourceItem] = []

    for obs in observations:
        # Build external_id from period, region, and code/description
        # For special categories (empty code), use description to distinguish
        if obs.code:
            code_part = obs.code
        else:
            # Use description for special categories (Estacional, Regulados, B, S)
            code_part = obs.description.lower().replace(" ", "_")

        external_id = f"ipc_{code_part}_{obs.period}_{obs.region}"

        # Parse period for published_at
        try:
            published_at = _parse_period(obs.period)
        except ValueError:
            # If period parsing fails, skip this observation
            continue

        # Parse numeric values
        index_value = _parse_decimal_value(obs.index_value)
        monthly_variation = _parse_decimal_value(obs.monthly_variation)
        annual_variation = _parse_decimal_value(obs.annual_variation)

        # Build title
        if obs.code == "0":
            title = f"IPC Nacional - {obs.period}"
        elif obs.code:
            title = f"IPC {obs.description} - {obs.period}"
        else:
            title = f"IPC {obs.description} - {obs.period}"

        # Build summary with available data
        summary_parts = [f"INDEC IPC para {obs.period}"]
        if index_value is not None:
            summary_parts.append(f"Índice: {index_value:.2f}")
        if monthly_variation is not None:
            summary_parts.append(f"Var. mensual: {monthly_variation:.1f}%")
        if annual_variation is not None:
            summary_parts.append(f"Var. interanual: {annual_variation:.1f}%")
        summary = ", ".join(summary_parts) + f". Región: {obs.region}"

        # Build metadata
        metadata: dict[str, object] = {
            "category_code": obs.code if obs.code else None,
            "category_description": obs.description,
            "classifier": obs.classifier,
            "period": obs.period,
            "region": obs.region,
            "index_value": index_value,
            "monthly_variation_pct": monthly_variation,
            "annual_variation_pct": annual_variation,
        }

        # Build provenance
        provenance = Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=IPC_CSV_URL,
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
            body=None,  # CSV data doesn't have a full body
            summary=summary,
            url=IPC_CSV_URL,
            metadata=metadata,
            provenance=provenance,
            freshness=freshness,
        )

        items.append(item)

    return items


class IndecIpcConnector:
    """Connector for INDEC IPC (Consumer Price Index) data.

    Fetches the official IPC CSV from INDEC and normalizes it into SourceItem objects.
    The CSV contains the headline IPC index and various category breakdowns by region
    and period.

    Note on IPC Núcleo: This connector does NOT provide IPC núcleo as a separate
    downloadable series because INDEC does not publish it as a stable CSV/XLS file.
    The methodology exists (PDF), but the time series itself is not available in
    machine-readable format from the main IPC page. Only general categories
    (Estacional, Regulados, B, S) are included in the CSV.

    This connector follows the standard pattern:
    - Async HTTP client via injected AsyncHttpTransport
    - Pure parser functions (parse_ipc_csv, normalize_ipc_observations)
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
        """Initialize the INDEC IPC connector.

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
        """Fetch and parse INDEC IPC data.

        Args:
            cursor: Not used (INDEC IPC doesn't support pagination).
            since: Not used (full dataset is fetched each time).

        Returns:
            PageResult containing all IPC observations from the CSV file.
            The CSV contains multiple observations (by period, region, category),
            so this returns a list with all of them. has_more is False and
            next_cursor is None because there's no pagination.

        Raises:
            RecoverableConnectorError: For 4xx/5xx HTTP errors (transient).
            ValueError: For unexpected status codes or CSV parsing errors.
        """
        del since  # Not used

        # Fetch the CSV file
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=IPC_CSV_URL,
                headers={"Accept": "text/csv"},
            )
        )

        # Handle HTTP status codes
        if response.status_code == 404:
            raise RecoverableConnectorError(
                f"INDEC IPC CSV not found at {IPC_CSV_URL}"
            )
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"INDEC returned {response.status_code} for {IPC_CSV_URL}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected INDEC status code {response.status_code} for {IPC_CSV_URL}"
            )

        # Decode CSV text (INDEC uses ISO-8859-1/Latin-1)
        try:
            csv_text = response.text(encoding="iso-8859-1")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode CSV as ISO-8859-1: {exc}") from exc

        # Parse CSV
        try:
            observations = parse_ipc_csv(csv_text)
        except ValueError as exc:
            raise ValueError(f"Failed to parse INDEC IPC CSV: {exc}") from exc

        # Normalize to SourceItems
        fetched_at = datetime.now(timezone.utc)
        items = normalize_ipc_observations(
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