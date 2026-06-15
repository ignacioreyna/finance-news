"""BCRA Dólar Oficial (A3500/REF) connector."""

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

CONNECTOR_NAME = "bcra_dolar_oficial"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/REF"
DEFAULT_TTL_SECONDS = 86400  # 1 day


@dataclass(frozen=True)
class ParsedBcraDolarOficial:
    """Parsed BCRA official dollar (A3500/REF) observation."""

    fecha: str
    valor: float
    codigo_moneda: str
    descripcion: str


def parse_bcra_dolar_oficial_response(data: dict[str, Any]) -> list[ParsedBcraDolarOficial]:
    """Parse BCRA exchange rate API response for REF currency.

    Args:
        data: Raw JSON response from BCRA API.

    Returns:
        List of parsed observations, one per date.

    Raises:
        ValueError: If the response structure is invalid or empty.
    """
    if not isinstance(data, dict):
        raise ValueError("Response must be a dictionary")

    if data.get("status") != 200:
        raise ValueError(f"API returned status {data.get('status')}")

    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("No results found in response")

    observations: list[ParsedBcraDolarOficial] = []
    for entry in results:
        if not isinstance(entry, dict):
            raise ValueError("Each result entry must be a dictionary")

        fecha = entry.get("fecha")
        if not isinstance(fecha, str):
            raise ValueError(f"Missing or invalid fecha in entry: {entry}")

        detalle = entry.get("detalle")
        if not isinstance(detalle, list) or not detalle:
            continue  # Skip entries without detail

        for item in detalle:
            if not isinstance(item, dict):
                continue

            codigo_moneda = item.get("codigoMoneda")
            if codigo_moneda != "REF":
                continue  # Only process REF currency

            descripcion = item.get("descripcion")
            tipo_cotizacion = item.get("tipoCotizacion")

            if not isinstance(descripcion, str):
                continue
            if not isinstance(tipo_cotizacion, (int, float)):
                continue

            observations.append(
                ParsedBcraDolarOficial(
                    fecha=fecha,
                    valor=float(tipo_cotizacion),
                    codigo_moneda=codigo_moneda,
                    descripcion=descripcion,
                )
            )

    if not observations:
        raise ValueError("No REF currency observations found in response")

    return observations


def normalize_bcra_dolar_oficial(
    *,
    parsed: ParsedBcraDolarOficial,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed BCRA official dollar observation to SourceItem.

    Args:
        parsed: The parsed observation.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: The cursor used for pagination (if any).
        transport_metadata: Additional transport metadata.

    Returns:
        A normalized SourceItem.
    """
    # Parse the fecha field (YYYY-MM-DD) to datetime
    published_at = datetime.strptime(parsed.fecha, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )

    metadata: dict[str, object] = {
        "currency_code": parsed.codigo_moneda,
        "currency_description": parsed.descripcion,
        "value": parsed.valor,
        "value_type": "exchange_rate",
    }

    # Create a descriptive title
    title = f"Dólar Oficial (A3500): {parsed.valor:.2f} ARS/USD - {parsed.fecha}"

    # Create a brief summary
    summary = f"BCRA official dollar rate (Comunicación A3500): {parsed.valor:.2f} ARS per USD as of {parsed.fecha}"

    return SourceItem(
        external_id=f"{parsed.codigo_moneda}_{parsed.fecha}",
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
            cursor=cursor,
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


class BcraDolarOficialConnector:
    """Fetch BCRA official dollar (A3500/REF) exchange rate observations."""

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
        """Initialize the connector.

        Args:
            transport: The async HTTP transport to use for requests.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of BCRA official dollar observations.

        Args:
            cursor: Optional cursor for pagination (not currently used).
            since: Optional datetime to filter results (not currently used).

        Returns:
            A PageResult containing the fetched observations.

        Raises:
            RecoverableConnectorError: For transient API failures.
            ValueError: For permanent API failures or invalid responses.
        """
        # Currently, we fetch the latest available data without date filtering
        # The connector can be extended to use cursor/since for incremental updates

        request = HttpRequest(
            method="GET",
            url=BASE_URL,
            headers={"Accept": "application/json"},
            params={"limit": "1000"},
        )

        response = await self._transport.send(request)

        # Handle errors
        if response.status_code == 404:
            # No data available - this is recoverable (temporary outage)
            raise RecoverableConnectorError(
                f"BCRA API returned 404 - endpoint may be temporarily unavailable: {response.url}"
            )

        if 500 <= response.status_code <= 599:
            # Server error - recoverable
            raise RecoverableConnectorError(
                f"BCRA API returned {response.status_code} - server error: {response.url}"
            )

        if 400 <= response.status_code <= 499:
            # Client error (rate limit, bad request, etc.) - treat as recoverable for retry
            raise RecoverableConnectorError(
                f"BCRA API returned {response.status_code} - client error: {response.url}"
            )

        if response.status_code != 200:
            # Other status codes - permanent error
            raise ValueError(
                f"BCRA API returned unexpected status {response.status_code}: {response.url}"
            )

        # Parse response
        try:
            response_data = response.text()
            import json

            data = json.loads(response_data)
            parsed_observations = parse_bcra_dolar_oficial_response(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from BCRA API: {response.url}") from exc
        except ValueError as exc:
            raise ValueError(f"Failed to parse BCRA API response: {response.url}: {exc}") from exc

        # Normalize observations
        fetched_at = datetime.now(timezone.utc)
        items = [
            normalize_bcra_dolar_oficial(
                parsed=obs,
                fetched_at=fetched_at,
                fetch_url=response.url,
                cursor=cursor,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            for obs in parsed_observations
        ]

        # This connector returns all available observations in a single page
        # No pagination support from the API for the REF endpoint
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)