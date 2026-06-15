"""BCRA catalog connector for monetarias series metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Protocol

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

CONNECTOR_NAME = "bcra_catalogo"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
CATALOG_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for catalog metadata


@dataclass(frozen=True)
class ParsedBcraCatalogEntry:
    """Normalized BCRA series metadata entry."""

    id: int
    external_id: str
    nombre: str
    unidad: str
    frecuencia: str
    fuente: str
    categoria: str
    tipo_serie: str
    moneda: str
    primera_fecha: str | None
    ultima_fecha: str | None
    ultimo_valor: float | None


def parse_bcra_catalog_json(json_data: dict[str, object]) -> list[ParsedBcraCatalogEntry]:
    """Parse BCRA monetarias catalog JSON into normalized entries.

    This is a pure parser function with no I/O side effects.

    Args:
        json_data: The parsed JSON response from BCRA catalog endpoint.

    Returns:
        A list of normalized catalog entries.

    Raises:
        ValueError: If the JSON structure is invalid or missing required fields.
    """
    status = json_data.get("status")
    if status != 200:
        raise ValueError(f"Unexpected BCRA API status: {status}")

    results = json_data.get("results")
    if not isinstance(results, list):
        raise ValueError("BCRA catalog response missing 'results' array")

    entries: list[ParsedBcraCatalogEntry] = []
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("BCRA catalog entry must be a dict")

        id_variable = item.get("idVariable")
        if not isinstance(id_variable, int):
            raise ValueError("BCRA catalog entry missing 'idVariable' integer")

        descripcion = item.get("descripcion")
        if not isinstance(descripcion, str):
            raise ValueError("BCRA catalog entry missing 'descripcion' string")

        unidad_expresion = item.get("unidadExpresion", "")
        periodicidad = item.get("periodicidad", "")
        categoria = item.get("categoria", "")
        tipo_serie = item.get("tipoSerie", "")
        moneda = item.get("moneda", "")

        # Clean whitespace from nombre (BCRA often has trailing spaces)
        nombre = descripcion.strip()
        unidad = unidad_expresion.strip() if isinstance(unidad_expresion, str) else ""
        frecuencia = periodicidad.strip() if isinstance(periodicidad, str) else ""

        # Normalize frequency codes to Spanish
        frecuencia_map = {"D": "diaria", "M": "mensual", "T": "trimestral", "Q": "trimestral"}
        frecuencia_espanol = frecuencia_map.get(frecuencia, frecuencia)

        primera_fecha = item.get("primerFechaInformada")
        ultima_fecha = item.get("ultFechaInformada")
        ultimo_valor = item.get("ultValorInformado")

        entry = ParsedBcraCatalogEntry(
            id=id_variable,
            external_id=str(id_variable),
            nombre=nombre,
            unidad=unidad,
            frecuencia=frecuencia_espanol,
            fuente=SOURCE_NAME,
            categoria=categoria.strip() if isinstance(categoria, str) else "",
            tipo_serie=tipo_serie.strip() if isinstance(tipo_serie, str) else "",
            moneda=moneda.strip() if isinstance(moneda, str) else "",
            primera_fecha=primera_fecha if isinstance(primera_fecha, str) else None,
            ultima_fecha=ultima_fecha if isinstance(ultima_fecha, str) else None,
            ultimo_valor=ultimo_valor if isinstance(ultimo_valor, (int, float)) else None,
        )
        entries.append(entry)

    return entries


def normalize_bcra_catalog_entry(
    *,
    parsed: ParsedBcraCatalogEntry,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed BCRA catalog entry into a SourceItem.

    The catalog entry represents metadata about a time series, not a
    specific data point. We model it as a SourceItem where the body
    contains the full metadata as JSON.

    Args:
        parsed: The parsed catalog entry.
        fetched_at: When the catalog was fetched.
        fetch_url: The URL used to fetch the catalog.
        cursor: Optional pagination cursor.
        transport_metadata: Optional HTTP transport metadata.

    Returns:
        A normalized SourceItem representing the catalog entry.
    """
    import json as _json

    # Build metadata with all BCRA series fields
    metadata: dict[str, object] = {
        "catalog_entry": True,
        "bcra_id": parsed.id,
        "bcra_categoria": parsed.categoria,
        "bcra_tipo_serie": parsed.tipo_serie,
        "bcra_moneda": parsed.moneda,
        "bcra_primera_fecha": parsed.primera_fecha,
        "bcra_ultima_fecha": parsed.ultima_fecha,
        "bcra_ultimo_valor": parsed.ultimo_valor,
    }

    # Body contains structured metadata as JSON
    body_metadata = {
        "id": parsed.id,
        "nombre": parsed.nombre,
        "unidad": parsed.unidad,
        "frecuencia": parsed.frecuencia,
        "fuente": parsed.fuente,
        "categoria": parsed.categoria,
        "tipo_serie": parsed.tipo_serie,
        "moneda": parsed.moneda,
        "primera_fecha": parsed.primera_fecha,
        "ultima_fecha": parsed.ultima_fecha,
        "ultimo_valor": parsed.ultimo_valor,
    }

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=None,  # Catalog metadata has no publication date
        title=parsed.nombre,
        body=_json.dumps(body_metadata, ensure_ascii=False, indent=2),
        summary=f"Serie {parsed.nombre} ({parsed.frecuencia}, {parsed.unidad})",
        url=f"{CATALOG_URL}/{parsed.id}",
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
            published_at=None,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


def find_series_by_id(
    entries: list[ParsedBcraCatalogEntry], series_id: int | str
) -> ParsedBcraCatalogEntry | None:
    """Find a series entry by its BCRA ID.

    This is a pure lookup function used by callers to check if a required
    series exists in the catalog. If the series is not found, the caller
    can implement fallback behavior (e.g., raise an error, use alternative
    series, log a warning, etc.).

    Args:
        entries: The list of parsed catalog entries.
        series_id: The BCRA series ID to find (int or string).

    Returns:
        The matching entry, or None if not found.

    Fallback behavior:
        When a required series is not found in the catalog, callers should:
        1. Log a clear warning that the series is missing
        2. Consider whether the series ID is correct (typo, deprecated)
        3. Decide on application-specific fallback:
           - Raise an error if the series is critical
           - Use an alternative series if available
           - Skip the data point if non-critical
        4. Monitor for series additions/changes in future catalog updates

    Example:
        >>> entries = parse_bcra_catalog_json(catalog_json)
        >>> reserves = find_series_by_id(entries, 1)  # Reservas internacionales
        >>> if reserves is None:
        ...     raise ValueError("Critical series 'Reservas internacionales' not found in catalog")
    """
    normalized_id = int(series_id)
    for entry in entries:
        if entry.id == normalized_id:
            return entry
    return None


class BcraCatalogoConnector:
    """Fetch and normalize the BCRA monetarias series catalog.

    This connector fetches the catalog of all available time series from
    the BCRA monetarias API and returns each series as a normalized SourceItem.

    The catalog provides metadata (name, unit, frequency, etc.) but not the
    actual time series data. Use bcra_monetarias (future connector) for fetching
    series data points.

    Pagination:
        The BCRA API supports offset/limit pagination. By default, this connector
        fetches all series in a single request (limit=3000, the API maximum).
        For large catalogs, use the cursor parameter with offset values like
        "offset=0&limit=1000" to paginate.
    """

    name = CONNECTOR_NAME
    source = SOURCE_NAME
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=8.0,
    )
    rate_limit_policy = RateLimitPolicy(concurrency=1, burst=1)

    def __init__(self, *, transport: AsyncHttpTransport) -> None:
        """Initialize the BCRA catalog connector.

        Args:
            transport: The async HTTP transport to use for API requests.
        """
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of BCRA series catalog entries.

        Args:
            cursor: Optional pagination cursor. Use format "offset=N&limit=M"
                or None for all entries (up to API max 3000).
            since: Not supported for catalog (metadata has no temporal filter).

        Returns:
            A PageResult containing catalog entries as SourceItems.

        Raises:
            ValueError: If the cursor format is invalid.
            RecoverableConnectorError: For transient API errors (5xx, timeouts).
            ValueError: For persistent API errors (4xx, invalid JSON).
        """
        del since  # Catalog doesn't support temporal filtering

        # Build URL with pagination parameters
        url = CATALOG_URL
        params: dict[str, str] = {}
        next_cursor: str | None = None
        has_more = False

        if cursor is None:
            # Fetch all entries in one request (up to API max)
            params["limit"] = "3000"
        else:
            # Parse cursor format: "offset=N&limit=M"
            try:
                for pair in cursor.split("&"):
                    key, value = pair.split("=", 1)
                    params[key.strip()] = value.strip()
            except ValueError as exc:
                raise ValueError(
                    f"Invalid cursor format: {cursor!r}. Expected 'offset=N&limit=M'."
                ) from exc

            # Determine if there are more pages
            offset = int(params.get("offset", 0))
            limit = int(params.get("limit", 1000))
            next_offset = offset + limit
            next_cursor = f"offset={next_offset}&limit={limit}"
            has_more = True  # Assume more pages; API will return empty results if done

        # Make HTTP request
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=url,
                params=params,
                headers={"Accept": "application/json"},
            )
        )

        # Handle response
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"BCRA returned {response.status_code} for {url}."
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected BCRA status code {response.status_code} for {url}.")

        # Parse JSON response
        import json as _json

        try:
            json_data = _json.loads(response.text())
        except _json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from BCRA catalog: {exc}") from exc

        # Parse catalog entries
        fetched_at = datetime.now(timezone.utc)
        entries = parse_bcra_catalog_json(json_data)

        # Check if this is the last page
        if entries:
            metadata = json_data.get("metadata", {})
            resultset = metadata.get("resultset", {})
            total_count = resultset.get("count", 0)
            offset = int(params.get("offset", 0))
            limit = int(params.get("limit", 1000))

            if offset + len(entries) >= total_count:
                has_more = False
                next_cursor = None
        else:
            has_more = False
            next_cursor = None

        # Normalize entries to SourceItems
        items = [
            normalize_bcra_catalog_entry(
                parsed=entry,
                fetched_at=fetched_at,
                fetch_url=response.url,
                cursor=cursor,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            for entry in entries
        ]

        return PageResult(items=items, next_cursor=next_cursor, has_more=has_more)