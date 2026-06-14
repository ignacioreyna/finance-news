# Contrato comun de conectores

## Alcance

Este documento define el contrato minimo para conectores de fuentes financieras del proyecto. El objetivo es desacoplar adquisicion, parseo y normalizacion para que cada fuente entregue items comparables, trazables y reintentables.

Supuesto de trabajo: la referencia externa de `vigia_connectors` no estuvo accesible desde este entorno al momento de redactar este documento el 2026-06-14, por lo que el contrato se define con base en la tarea y en [analysis/host_profile.md](/Users/ignacioreyna/PERSONAL/finance-news/analysis/host_profile.md).

## Principios

- Cliente async para adquisicion I/O bound.
- Parser puro: transforma payload crudo en items normalizados sin efectos secundarios.
- Normalizacion comun para ranking, deduplicacion, resumen y citacion.
- Provenance explicita para reconstruir origen, fetch y version de parseo.
- Freshness separada de fecha editorial para distinguir novedad real de recirculacion.
- Errores recuperables modelados como parte del contrato operativo.

## Flujo de ingesta

1. Scheduler o runner invoca `fetch_page` del conector con un cursor opcional y una ventana temporal.
2. El cliente async resuelve autenticacion, headers, timeouts, rate limit y retries de red.
3. El conector devuelve una o mas respuestas crudas con metadata de transporte.
4. Un parser puro convierte cada respuesta en `SourceItem`.
5. Un normalizador valida campos requeridos, completa `provenance` y calcula `freshness`.
6. El pipeline deduplica por `source + external_id` y opcionalmente por `canonical_url`.
7. Si hay mas paginas, el conector emite `next_cursor`.
8. Los errores recuperables se registran con contexto y permiten retry o reanudacion desde cursor.

## Interfaces propuestas

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    base_delay_seconds: float
    max_delay_seconds: float
    jitter: bool = True


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_minute: int | None = None
    concurrency: int = 1
    burst: int = 1


@dataclass(frozen=True)
class Freshness:
    published_at: datetime | None
    first_seen_at: datetime
    fetched_at: datetime
    is_stale: bool
    ttl_seconds: int | None


@dataclass(frozen=True)
class Provenance:
    connector: str
    source: str
    fetch_url: str
    canonical_url: str
    cursor: str | None
    fetched_at: datetime
    parser_version: str
    transport_metadata: Mapping[str, Any]


@dataclass(frozen=True)
class SourceItem:
    external_id: str
    source: str
    published_at: datetime | None
    title: str
    body: str | None
    summary: str | None
    url: str
    metadata: Mapping[str, Any]
    provenance: Provenance
    freshness: Freshness


@dataclass(frozen=True)
class PageResult:
    items: Sequence[SourceItem]
    next_cursor: str | None
    has_more: bool


class RecoverableConnectorError(Exception):
    pass


class Connector(Protocol):
    name: str
    source: str
    retry_policy: RetryPolicy
    rate_limit_policy: RateLimitPolicy

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult: ...
```

## Modelo normalizado: `SourceItem`

Campos minimos obligatorios:

- `external_id`: identificador estable de la fuente original.
- `source`: nombre canonico de la fuente, por ejemplo `bloomberg`, `bcra`, `fomc`.
- `published_at`: fecha editorial original si existe.
- `title`: titulo canonico del item.
- `body` o `summary`: cuerpo completo o resumen utilizable si el cuerpo no esta disponible.
- `url`: URL canonical del item.
- `metadata`: mapa flexible para campos de dominio.

Campos recomendados para operacion:

- `provenance`: datos de fetch, parser y cursor.
- `freshness`: estado temporal del item respecto del pipeline.

Convenciones:

- `external_id` debe ser estable dentro de una misma fuente; no usar hashes del contenido salvo que la fuente no exponga id.
- `source` debe ser corto, estable y reusable en deduplicacion y filtros.
- `body` y `summary` pueden coexistir; si solo hay uno, el otro puede ser `None`.
- `metadata` debe reservar claves estructurales de bajo cambio, por ejemplo `tickers`, `language`, `authors`, `section`, `region`, `content_type`, `raw_timestamp`, `http_etag`.
- El item normalizado no debe incluir el payload crudo completo; eso pertenece a fixtures o storage de raw responses.

## Provenance

`Provenance` resuelve trazabilidad y auditoria minima:

- `connector`: implementacion concreta, por ejemplo `fomc_press_releases`.
- `source`: familia editorial o institucional.
- `fetch_url`: URL efectiva usada para la adquisicion.
- `canonical_url`: URL final del item.
- `cursor`: cursor o pagina desde la cual se obtuvo el item.
- `fetched_at`: timestamp UTC del fetch.
- `parser_version`: version del parser para detectar cambios de extraccion.
- `transport_metadata`: status code, headers relevantes, etag, last-modified y latencia.

## Freshness

`Freshness` distingue tres tiempos:

- `published_at`: cuando la fuente dice haber publicado.
- `first_seen_at`: primera vez que el pipeline vio el item.
- `fetched_at`: fetch actual.

Reglas:

- Un item puede ser viejo en `published_at` y nuevo en `first_seen_at` si el conector se incorpora tarde o si la fuente reprocesa historicos.
- `ttl_seconds` depende del tipo de fuente: breaking news bajo, series institucionales alto.
- `is_stale` se calcula contra `fetched_at` y el TTL operativo del conector.

## Parser puro

El parser debe ser una funcion determinista sobre el payload crudo y su contexto:

```python
def parse_items(raw_payload: bytes | str, *, fetched_at: datetime, cursor: str | None) -> list[SourceItem]:
    ...
```

Reglas:

- Sin llamadas de red ni acceso a filesystem.
- Sin lectura de reloj del sistema fuera de parametros inyectados.
- Con salida estable para un fixture estable.
- Debe fallar con errores tipados cuando cambie el shape de la fuente.

## Errores recuperables

Errores recuperables:

- timeout de red
- DNS/transient connection reset
- 429 rate limited
- 5xx upstream
- payload parcial o pagina vacia con cursor valido

Errores no recuperables:

- credenciales invalidas
- 4xx semantico persistente
- contrato roto del parser despues de confirmar cambio de schema

Convenciones:

- Usar `RecoverableConnectorError` o subclases equivalentes para reintentos automaticos.
- Incluir `connector`, `source`, `cursor`, `attempt`, `status_code` y `fetch_url` en el log estructurado.
- Cortar reintentos cuando el error sea deterministico o cuando se alcance `max_attempts`.

## Retries y rate limits

Retries recomendados:

- `max_attempts = 3`
- backoff exponencial con jitter
- respetar `Retry-After` si existe
- no reintentar errores de parseo salvo evidencia de truncamiento de payload

Rate limits recomendados:

- politicas declarativas por conector
- `concurrency = 1` por fuente hasta medir tolerancia
- token bucket simple o sleep cooperativo entre requests
- si la fuente publica limites explicitos, el conector debe modelarlos de forma literal

## Paginado y cursores

Contrato minimo:

- `cursor` es opaco para el scheduler y solo interpretable por el conector
- `next_cursor` debe ser `None` al finalizar
- `has_more` evita depender solo de la presencia de cursor

Reglas:

- Preferir cursores estables de API sobre offsets numericos.
- Si solo existe paginado por pagina, serializarlo como cursor opaco, por ejemplo `page=3`.
- Guardar el cursor exitoso mas reciente para reanudar sin duplicar todo el barrido.
- Si una fuente soporta `since` o `updated_after`, combinarlo con cursor para ventanas incrementales.

## Fixtures

Fixtures minimos por conector:

- un caso feliz con payload real anonimizado si hace falta
- un caso vacio
- un caso de paginado
- un caso de schema drift o campo faltante

Convenciones:

- Guardar fixtures crudos separados de snapshots normalizados.
- Los tests del parser deben comparar `SourceItem` normalizados, no strings completos de HTML salvo necesidad puntual.
- Versionar fixtures cuando cambie `parser_version`.

## Recomendaciones para este proyecto

Para el dominio de finanzas y macro del proyecto:

- Priorizar `source` y `metadata` orientados a comparacion entre Argentina y contexto global.
- Incluir en `metadata` campos opcionales como `country`, `asset_class`, `macro_topic`, `speaker`, `institution`.
- Exigir UTC en todos los timestamps normalizados.
- Mantener el contrato chico: fetch async, parse puro, `SourceItem`, `Provenance`, `Freshness`, `PageResult` y errores recuperables cubren la base comun.
