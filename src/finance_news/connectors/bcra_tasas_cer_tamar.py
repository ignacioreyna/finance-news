"""BCRA CER and TAMAR rates connector."""

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

CONNECTOR_NAME = "bcra_tasas_cer_tamar"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for rate data

# BCRA variable IDs
CER_VARIABLE_ID = 30
TAMAR_VARIABLE_ID = 44

# Rate metadata for normalization
_CER_METADATA = {
    "idVariable": 30,
    "descripcion": "Coeficiente de estabilización de referencia (base 2.2.02=1)",
    "categoria": "Principales Variables",
    "tipoSerie": "Índice",
    "periodicidad": "D",
    "unidadExpresion": "Índice base 2.2.02=1",
}

_TAMAR_METADATA = {
    "idVariable": 44,
    "descripcion": "Tasa de interes TAMAR de bancos privados",
    "categoria": "Principales Variables",
    "tipoSerie": "Tasa de interés",
    "periodicidad": "D",
    "unidadExpresion": "En porcentaje nominal anual",
}


@dataclass(frozen=True)
class ParsedBcraRateObservation:
    """A parsed observation from the BCRA monetarias API."""

    fecha: str  # YYYY-MM-DD format
    valor: float
    variable_id: int
    rate_name: str  # "CER" or "TAMAR"


def parse_bcra_monetarias_response(
    response_data: dict[str, Any],
    rate_name: str,
) -> list[ParsedBcraRateObservation]:
    """Parse a BCRA monetarias API response into rate observations.

    Args:
        response_data: The JSON response from the BCRA API.
        rate_name: The rate name ("CER" or "TAMAR").

    Returns:
        A list of parsed rate observations.

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
            ParsedBcraRateObservation(
                fecha=fecha,
                valor=float(valor),
                variable_id=result["idVariable"],
                rate_name=rate_name,
            )
        )

    return observations


def normalize_bcra_rate_observation(
    *,
    parsed: ParsedBcraRateObservation,
    fetched_at: datetime,
    fetch_url: str,
    transport_metadata: dict[str, Any] | None = None,
) -> SourceItem:
    """Normalize a parsed BCRA rate observation into a SourceItem.

    This separates rate observations (CER/TAMAR) from BCRA norms about
    encajes or liquidez by:
    1. Using metadata["content_type"] = "rate_observation" for all items
    2. Excluding normative communication fields (document_type, circular_reference)
    3. Including rate-specific metadata (rate_name, variable_id, frequency)

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        transport_metadata: HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the rate observation.
    """
    # Determine rate-specific metadata
    if parsed.rate_name == "CER":
        rate_metadata = _CER_METADATA.copy()
    elif parsed.rate_name == "TAMAR":
        rate_metadata = _TAMAR_METADATA.copy()
    else:
        raise ValueError(f"Unknown rate name: {parsed.rate_name!r}")

    # Parse the fecha (assume BCRA returns dates in YYYY-MM-DD format)
    # BCRA dates are in local time, but we treat them as midnight UTC
    try:
        year, month, day = map(int, parsed.fecha.split("-"))
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid fecha format: {parsed.fecha!r}") from exc

    # Build title with rate name and date
    title = f"{parsed.rate_name}: {parsed.fecha} - {parsed.valor}"

    # Build summary with rate context
    summary = (
        f"{parsed.rate_name} ({rate_metadata['descripcion']}): "
        f"{parsed.valor} {rate_metadata['unidadExpresion']} on {parsed.fecha}"
    )

    # Build metadata - note content_type distinguishes rate data from norms
    metadata: dict[str, Any] = {
        "content_type": "rate_observation",  # Distinguishes from BCRA norms
        "rate_name": parsed.rate_name,
        "variable_id": parsed.variable_id,
        "frequency": rate_metadata["periodicidad"],
        "unit": rate_metadata["unidadExpresion"],
        "category": rate_metadata["categoria"],
        "series_type": rate_metadata["tipoSerie"],
    }

    return SourceItem(
        external_id=f"{parsed.rate_name}_{parsed.fecha}",  # Unique ID per rate and date
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


class BcraTasasCerTamarConnector:
    """Fetch CER and TAMAR rates from the BCRA monetarias API.

    This connector fetches rate observations (time series data) and
    explicitly separates them from BCRA normative communications about
    encajes or liquidez. Rate observations use metadata["content_type"] =
    "rate_observation", while normative items would use different types.
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
            limit: Maximum number of observations to fetch per rate.
        """
        self._transport = transport
        self._limit = limit

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of CER and TAMAR rate observations.

        The cursor should be "CER" or "TAMAR" to specify which rate to fetch.
        If no cursor is provided, fetches both rates (CER first, then TAMAR).

        Args:
            cursor: Optional cursor to specify which rate to fetch ("CER" or "TAMAR").
            since: Optional start date (not currently used for BCRA API).

        Returns:
            A PageResult containing the rate observations.

        Raises:
            ValueError: If cursor is invalid or API returns unexpected status.
            RecoverableConnectorError: For recoverable HTTP errors (4xx/5xx).
        """
        del since  # BCRA API doesn't support date filtering in this pattern

        # Determine which rate(s) to fetch
        if cursor is None:
            # Fetch both rates - return CER observations and set cursor to TAMAR
            return await self._fetch_rate("CER", next_cursor="TAMAR", has_more=True)
        elif cursor == "CER":
            return await self._fetch_rate("CER", next_cursor="TAMAR", has_more=True)
        elif cursor == "TAMAR":
            return await self._fetch_rate("TAMAR", next_cursor=None, has_more=False)
        else:
            raise ValueError(f"Invalid cursor: {cursor!r}. Expected 'CER', 'TAMAR', or None.")

    async def _fetch_rate(
        self,
        rate_name: str,
        *,
        next_cursor: str | None,
        has_more: bool,
    ) -> PageResult:
        """Fetch observations for a specific rate.

        Args:
            rate_name: The rate name ("CER" or "TAMAR").
            next_cursor: The cursor value to set in the result.
            has_more: Whether there are more pages.

        Returns:
            A PageResult with the rate observations.

        Raises:
            ValueError: If API returns unexpected status.
            RecoverableConnectorError: For recoverable HTTP errors.
        """
        # Get the variable ID for the rate
        if rate_name == "CER":
            variable_id = CER_VARIABLE_ID
        elif rate_name == "TAMAR":
            variable_id = TAMAR_VARIABLE_ID
        else:
            raise ValueError(f"Unknown rate name: {rate_name!r}")

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
        if response.status_code == 404:
            # Variable not found - return empty results
            return PageResult(items=(), next_cursor=next_cursor, has_more=has_more)
        if 400 <= response.status_code < 500:
            raise RecoverableConnectorError(
                f"BCRA API returned {response.status_code} for {url}"
            )
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
            observations = parse_bcra_monetarias_response(response_data, rate_name)
        except ValueError as exc:
            raise ValueError(f"Failed to parse BCRA response from {url}") from exc

        # Normalize each observation
        fetched_at = datetime.now(timezone.utc)
        items = []
        for obs in observations:
            item = normalize_bcra_rate_observation(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        return PageResult(items=tuple(items), next_cursor=next_cursor, has_more=has_more)