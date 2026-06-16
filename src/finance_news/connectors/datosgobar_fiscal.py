"""datos.gob.ar Fiscal connector for Ministerio de Economía fiscal series.

This connector consumes official fiscal series from the datos.gob.ar API,
specifically the series from Secretaria de Hacienda / Ministerio de Economía.

Base Methodology:
    This connector uses series on a "base caja" (cash basis) methodology,
    not "devengado" (accrual basis). The datos.gob.ar fiscal series from
    Secretaria de Hacienda measure actual cash flows for income and expenditures.

Data Source:
    datos.gob.ar series API - https://apis.datos.gob.ar/series/api/
    Series are published by Secretaria de Hacienda, Ministerio de Economía.

Key Series:
    - 452.3_RESULTADO_RIO_0_M_18_54: IMIG Resultado primario mensual
    - 379.9_RESULTADO_017__18_38: Resultado financiero SPNF base caja mensual
    - 373.9_RESULTADO_017__18_45: Resultado financiero Tesoro Nacional base caja mensual
"""

from __future__ import annotations

import json
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

CONNECTOR_NAME = "datosgobar_fiscal"
SOURCE_NAME = "datosgobar"
PARSER_VERSION = "0.1.0"
BASE_SERIES_URL = "https://apis.datos.gob.ar/series/api/series/"
DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60


# Module-level constants documenting the methodology
METHODOLOGY = "base_caja"
METHODOLOGY_DESCRIPTION = "Series published by Secretaria de Hacienda use cash basis (base caja) methodology, measuring actual cash flows for income and expenditures."


@dataclass(frozen=True)
class ParsedFiscalObservation:
    """A single parsed fiscal observation from datos.gob.ar series API."""

    external_id: str
    period: datetime
    concepto: str
    valor: float
    unidad: str
    fuente: str
    series_id: str


def parse_datosgobar_fiscal_json(
    json_text: str,
    series_id: str,
) -> ParsedFiscalObservation:
    """Parse a datos.gob.ar series API JSON response.

    Args:
        json_text: Raw JSON text from the series API.
        series_id: The series ID used in the request.

    Returns:
        A parsed fiscal observation with normalized data.

    Raises:
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    # Extract the main data points
    observations = data.get("data")
    if observations is None or not isinstance(observations, list):
        raise ValueError("Missing or invalid 'data' field in response")

    # Use the most recent observation (last item in the array)
    if not observations:
        raise ValueError("No observations found in response")

    latest = observations[-1]
    if not isinstance(latest, list) or len(latest) < 2:
        raise ValueError(f"Invalid observation format: {latest}")

    date_str = latest[0]
    value = latest[1]

    # Parse the period (format: YYYY-MM-DD)
    try:
        period = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Invalid date format {date_str}: {exc}") from exc

    # Extract metadata
    meta_list = data.get("meta")
    if not meta_list or not isinstance(meta_list, list):
        raise ValueError("Missing or invalid 'meta' field in response")

    meta = meta_list[0]
    field = meta.get("field")
    if not field:
        # Fall back to checking if this is the simplified format
        # where metadata might be at the top level
        field = data.get("field")
        if not field:
            raise ValueError("Missing 'field' in metadata")

    concepto = field.get("description", "Unknown")
    unidad = field.get("units", "Unknown")
    series_id_check = field.get("id", "")

    # Extract source from catalog or dataset
    catalog = meta.get("catalog", {})
    fuente = catalog.get("title")
    if not fuente:
        # Fall back to dataset title
        dataset = meta.get("dataset", {})
        fuente = dataset.get("title", "datos.gob.ar")

    # Verify series ID matches (only if field has an id)
    series_id_check = field.get("id", "")
    if series_id_check and series_id_check != series_id:
        raise ValueError(f"Series ID mismatch: requested {series_id}, got {series_id_check}")

    external_id = f"{series_id}_{period.strftime('%Y-%m')}"

    return ParsedFiscalObservation(
        external_id=external_id,
        period=period,
        concepto=concepto,
        valor=value,
        unidad=unidad,
        fuente=fuente,
        series_id=series_id,
    )


def normalize_datosgobar_fiscal(
    *,
    parsed: ParsedFiscalObservation,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed fiscal observation into a SourceItem.

    Args:
        parsed: The parsed fiscal observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: The cursor used for pagination.
        transport_metadata: Additional metadata from the HTTP transport.

    Returns:
        A normalized SourceItem.
    """
    metadata: dict[str, object] = {
        "period": parsed.period.isoformat(),
        "concepto": parsed.concepto,
        "valor": parsed.valor,
        "unidad": parsed.unidad,
        "fuente": parsed.fuente,
        "series_id": parsed.series_id,
        "metodologia": METHODOLOGY,
        "metodologia_descripcion": METHODOLOGY_DESCRIPTION,
    }

    # Build a descriptive title
    title = f"{parsed.concepto} - {parsed.period.strftime('%Y-%m')}"

    # Create a summary
    summary = f"{parsed.valor} {parsed.unidad}"

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.period,
        title=title,
        body=json.dumps(metadata, ensure_ascii=False, indent=2),
        summary=summary,
        url=fetch_url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=fetch_url,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=parsed.period,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class DatosgobarFiscalConnector:
    """Fetch fiscal data series from datos.gob.ar API.

    This connector retrieves monthly fiscal observations from the
    datos.gob.ar series API, specifically from Secretaria de Hacienda.
    The series are on a cash basis (base caja) methodology.

    Usage:
        The cursor should be a series ID (e.g., "452.3_RESULTADO_RIO_0_M_18_54").

        Example series IDs:
            - 452.3_RESULTADO_RIO_0_M_18_54: IMIG Resultado primario mensual
            - 379.9_RESULTADO_017__18_38: Resultado financiero SPNF base caja mensual
            - 373.9_RESULTADO_017__18_45: Resultado financiero Tesoro Nacional base caja mensual
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
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of fiscal observations from datos.gob.ar.

        Args:
            cursor: The series ID to fetch (e.g., "452.3_RESULTADO_RIO_0_M_18_54").
            since: Optional since timestamp (not used for this connector).

        Returns:
            A PageResult containing the latest fiscal observation.

        Raises:
            ValueError: If no cursor is provided or if the response is malformed.
            RecoverableConnectorError: If the server returns a 5xx error.
        """
        del since

        if cursor is None:
            raise ValueError("datosgobar_fiscal connector requires a series ID cursor.")

        # Build the request URL with the series ID
        params = {
            "ids": cursor,
            "format": "json",
            "limit": "1",  # Only fetch the most recent observation
        }

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_SERIES_URL,
                params=params,
                headers={"Accept": "application/json"},
            )
        )

        # Handle error responses
        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 400 <= response.status_code <= 499:
            raise ValueError(f"datos.gob.ar returned {response.status_code} for {response.url}")
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"datos.gob.ar returned {response.status_code} for {response.url}"
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected status code {response.status_code} for {response.url}")

        # Parse the response
        fetched_at = datetime.now(timezone.utc)
        json_text = response.text()

        parsed = parse_datosgobar_fiscal_json(json_text, cursor)
        item = normalize_datosgobar_fiscal(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=response.url,
            cursor=cursor,
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
            },
        )

        return PageResult(items=(item,), next_cursor=None, has_more=False)