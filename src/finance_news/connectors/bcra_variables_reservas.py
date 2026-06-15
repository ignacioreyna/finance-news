"""BCRA variables monetarias y reservas connector."""

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

CONNECTOR_NAME = "bcra_variables_reservas"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for monetarias data

# BCRA variable IDs for monetarias and reservas
RESERVAS_INTERNACIONALES_ID = 1
BASE_MONETARIA_ID = 15
CIRCULACION_MONETARIA_ID = 16
EFECTIVO_ENTIDADES_ID = 18
DEPOSITOS_CC_BCRA_ID = 19

# Series metadata for normalization
_SERIES_METADATA = {
    RESERVAS_INTERNACIONALES_ID: {
        "nombre": "Reservas internacionales",
        "unidad": "En millones de USD",
        "frecuencia": "D",
        "categoria": "Principales Variables",
        "tipo_serie": "Saldos",
        "moneda": "ME",
    },
    BASE_MONETARIA_ID: {
        "nombre": "Base monetaria",
        "unidad": "En millones de ARS",
        "frecuencia": "D",
        "categoria": "Principales Variables",
        "tipo_serie": "Saldos",
        "moneda": "ML",
    },
    CIRCULACION_MONETARIA_ID: {
        "nombre": "Circulación monetaria",
        "unidad": "En millones de ARS",
        "frecuencia": "D",
        "categoria": "Principales Variables",
        "tipo_serie": "Saldos",
        "moneda": "ML",
    },
    EFECTIVO_ENTIDADES_ID: {
        "nombre": "Efectivo en entidades financieras",
        "unidad": "En millones de ARS",
        "frecuencia": "D",
        "categoria": "Principales Variables",
        "tipo_serie": "Saldos",
        "moneda": "ML",
    },
    DEPOSITOS_CC_BCRA_ID: {
        "nombre": "Depósitos de las entidades financieras en cuenta corriente en el BCRA",
        "unidad": "En millones de ARS",
        "frecuencia": "D",
        "categoria": "Principales Variables",
        "tipo_serie": "Saldos",
        "moneda": "ML",
    },
}

# List of supported variable IDs (ordered for cursor-based pagination)
_SUPPORTED_VARIABLE_IDS = [
    RESERVAS_INTERNACIONALES_ID,
    BASE_MONETARIA_ID,
    CIRCULACION_MONETARIA_ID,
    EFECTIVO_ENTIDADES_ID,
    DEPOSITOS_CC_BCRA_ID,
]


@dataclass(frozen=True)
class ParsedBcraMonetariasObservation:
    """A parsed observation from the BCRA monetarias API."""

    fecha: str  # YYYY-MM-DD format
    valor: float
    variable_id: int
    series_name: str  # Human-readable series name


def parse_bcra_monetarias_response(
    response_data: dict[str, Any],
    series_name: str,
) -> list[ParsedBcraMonetariasObservation]:
    """Parse a BCRA monetarias API response into observations.

    Args:
        response_data: The JSON response from the BCRA API.
        series_name: The series name (e.g., "Reservas internacionales").

    Returns:
        A list of parsed observations.

    Raises:
        ValueError: If the response format is invalid.
    """
    if response_data.get("status") != 200:
        raise ValueError(f"Unexpected status code: {response_data.get('status')}")

    results = response_data.get("results", [])
    if not results:
        # Empty results - no observations available
        return []

    result = results[0]
    detalle = result.get("detalle", [])
    if not isinstance(detalle, list):
        raise ValueError(f"Expected 'detalle' to be a list, got {type(detalle)}")

    observations = []
    for entry in detalle:
        fecha = entry.get("fecha")
        valor = entry.get("valor")

        if not isinstance(fecha, str) or not isinstance(valor, (int, float)):
            raise ValueError(
                f"Invalid observation format: fecha={fecha!r}, valor={valor!r}"
            )

        observations.append(
            ParsedBcraMonetariasObservation(
                fecha=fecha,
                valor=float(valor),
                variable_id=result["idVariable"],
                series_name=series_name,
            )
        )

    return observations


def normalize_bcra_monetarias_observation(
    *,
    parsed: ParsedBcraMonetariasObservation,
    metadata: dict[str, Any],
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed BCRA monetarias observation into a SourceItem.

    Args:
        parsed: The parsed observation.
        metadata: Series metadata (nombre, unidad, frecuencia, categoria, etc.).
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the observation.
    """
    # Parse the fecha (assume BCRA returns dates in YYYY-MM-DD format)
    # BCRA dates are in local time, but we treat them as midnight UTC
    try:
        year, month, day = map(int, parsed.fecha.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid fecha format: {parsed.fecha!r}") from exc

    # Build title with series name and date
    title = f"{parsed.series_name}: {parsed.fecha} - {parsed.valor} {metadata['unidad']}"

    # Build summary with context
    summary = (
        f"{parsed.series_name}: {parsed.valor} {metadata['unidad']} "
        f"({metadata['frecuencia']}, {metadata['categoria']}) on {parsed.fecha}"
    )

    # Build metadata
    item_metadata: dict[str, Any] = {
        "content_type": "monetarias_observation",
        "series_name": parsed.series_name,
        "variable_id": parsed.variable_id,
        "frequency": metadata["frecuencia"],
        "unit": metadata["unidad"],
        "category": metadata["categoria"],
        "series_type": metadata["tipo_serie"],
        "currency": metadata["moneda"],
    }

    return SourceItem(
        external_id=f"{parsed.series_name}_{parsed.fecha}",
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


class BcraVariablesReservasConnector:
    """Fetch monetarias and reservas variables from the BCRA API.

    This connector fetches key monetary aggregates and reserves data:
    - Reservas internacionales (idVariable=1)
    - Base monetaria (idVariable=15)
    - Circulación monetaria (idVariable=16)
    - Efectivo en entidades financieras (idVariable=18)
    - Depósitos de las entidades financieras en cuenta corriente en el BCRA (idVariable=19)

    Daily net intervention (intervención diaria neta) is NOT included because:
    - No official daily API endpoint was identified in source_research_bcra.md
    - The closest official source is monthly: "mercado de cambios y balance cambiario"
    - See analysis/source_research_bcra.md lines 217-218, 335

    Pagination:
        Uses cursor-based pagination over variable IDs. Call with no cursor to
        start from the first series (reservas), or with a variable ID (int or str)
        to fetch that specific series.
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
        limit: int = 1000,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The async HTTP transport for making requests.
            limit: Maximum number of observations to fetch per series.
        """
        self._transport = transport
        self._limit = limit

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of monetarias and reservas observations.

        The cursor should be a variable ID (e.g., "1" or 1) to specify which series
        to fetch. If no cursor is provided, starts from the first series (reservas).

        Args:
            cursor: Optional cursor to specify which series to fetch by variable ID.
            since: Optional start date (not currently used for BCRA API).

        Returns:
            A PageResult containing the monetarias observations.

        Raises:
            ValueError: If cursor is invalid or API returns unexpected status.
            RecoverableConnectorError: For recoverable HTTP errors (4xx/5xx).
        """
        del since  # BCRA API doesn't support date filtering in this pattern

        # Determine which variable ID to fetch
        if cursor is None:
            # Start from the first series
            variable_id = _SUPPORTED_VARIABLE_IDS[0]
            current_index = 0
        else:
            try:
                variable_id = int(cursor)
                current_index = _SUPPORTED_VARIABLE_IDS.index(variable_id)
            except (ValueError, IndexError) as exc:
                raise ValueError(
                    f"Invalid cursor: {cursor!r}. Expected variable ID "
                    f"(one of {', '.join(map(str, _SUPPORTED_VARIABLE_IDS))})."
                ) from exc

        # Determine next cursor
        if current_index + 1 < len(_SUPPORTED_VARIABLE_IDS):
            next_cursor = str(_SUPPORTED_VARIABLE_IDS[current_index + 1])
            has_more = True
        else:
            next_cursor = None
            has_more = False

        # Get series metadata
        if variable_id not in _SERIES_METADATA:
            raise ValueError(f"Unsupported variable ID: {variable_id}")

        metadata = _SERIES_METADATA[variable_id]

        # Build the API URL
        url = f"{BASE_URL}/{variable_id}?limit={self._limit}"

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
                f"BCRA API returned {response.status_code} for {url}"
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected BCRA status code {response.status_code} for {url}")

        # Parse the JSON response
        import json

        try:
            response_data = json.loads(response.text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from {url}") from exc

        # Parse the observations
        try:
            observations = parse_bcra_monetarias_response(response_data, metadata["nombre"])
        except ValueError as exc:
            raise ValueError(f"Failed to parse BCRA response from {url}") from exc

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_bcra_monetarias_observation(
                parsed=obs,
                metadata=metadata,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        return PageResult(items=tuple(items), next_cursor=next_cursor, has_more=has_more)