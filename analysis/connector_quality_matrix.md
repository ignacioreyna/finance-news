# Matriz de calidad de conectores

## Objetivo

Este documento define una matriz accionable para evaluar conectores de fuentes financieras antes de habilitarlos en produccion y durante su operacion continua. Complementa el contrato de [analysis/connector_architecture.md](/Users/ignacioreyna/PERSONAL/finance-news/analysis/connector_architecture.md) con criterios verificables, severidad operativa y expectativas de logging.

## Escala de severidad

- `S0 Bloqueante`: impide usar el conector o compromete la trazabilidad minima. El conector no debe promoverse a produccion.
- `S1 Critico`: produce perdida material de cobertura, duplicacion grave o datos temporalmente enganiosos. Requiere correccion prioritaria y alerta.
- `S2 Mayor`: degrada calidad o auditabilidad sin romper por completo la ingesta. Permite operar con seguimiento abierto.
- `S3 Menor`: desviacion cosmetica o mejora de robustez. No bloquea rollout.

## Reglas de aprobacion

- Un conector candidato a produccion no debe tener fallos `S0`.
- No debe tener mas de un fallo `S1` abierto con mitigacion manual.
- Debe pasar todos los checks marcados como `Gate`.
- Los checks `Monitor` pueden abrir seguimiento sin bloquear despliegue si la degradacion es acotada.

## Matriz

| Dimension | Objetivo | Checks accionables | Severidad si falla | Tipo |
| --- | --- | --- | --- | --- |
| Contrato del item | Garantizar que cada item cumple el modelo comun | Verificar `external_id`, `source`, `title`, `url`, `provenance`, `freshness`; rechazar items sin identificador estable | `S0` si faltan campos obligatorios; `S1` si el id no es estable | Gate |
| Parseo determinista | Asegurar reproducibilidad sobre fixtures | El mismo payload debe producir los mismos items y metadatos; parser sin reloj ni red | `S1` si cambia salida con mismo fixture; `S2` si solo cambian metadatos no criticos | Gate |
| Cobertura de fuente | Medir si la fuente se captura con amplitud suficiente | Comparar cantidad de items contra muestra manual o feed de referencia; revisar paginado y `next_cursor` | `S1` si faltan items recientes; `S2` si faltan historicos no prioritarios | Gate |
| Freshness | Detectar atraso operativo frente a la frecuencia de la fuente | Evaluar `published_at`, `first_seen_at`, `fetched_at` y TTL por tipo de fuente; marcar `is_stale` cuando excede umbral | `S1` si oculta datos vencidos como vigentes; `S2` si el atraso es acotado y visible | Gate |
| Completitud de contenido | Preservar datos utiles para ranking, resumen y citacion | Validar presencia de `body` o `summary`, metadatos clave (`tickers`, `authors`, `section`, `content_type`) cuando existan en la fuente | `S1` si no hay texto utilizable; `S2` si faltan metadatos secundarios | Gate |
| Dedupe y canonizacion | Evitar duplicados y URLs inconsistentes | Confirmar dedupe por `source + external_id`; revisar normalizacion de `canonical_url` y redirects | `S1` si duplica items en una corrida; `S2` si la URL final no queda canonizada | Gate |
| Provenance y trazabilidad | Permitir auditoria de origen y reproduccion | Registrar `connector`, `fetch_url`, `canonical_url`, `cursor`, `parser_version`, headers relevantes y latencia | `S0` si falta provenance; `S2` si faltan detalles de transporte no esenciales | Gate |
| Resiliencia operativa | Tolerar fallos transitorios sin perder estado | Probar retries, backoff, manejo de `429`, `5xx`, timeout y reanudacion desde cursor | `S1` si reintenta mal o pierde cursor; `S2` si la politica existe pero no respeta `Retry-After` | Gate |
| Fallo parcial | Aislar errores sin descartar el resto de la pagina o corrida | Confirmar que items validos se emiten aunque una pagina o subset falle; registrar conteos de procesados, descartados y reintentables | `S1` si aborta toda la corrida por error parcial recuperable; `S2` si degrada visibilidad del fallo | Gate |
| Observabilidad | Hacer visible calidad, latencia y degradacion | Exponer logs estructurados y metricas de items, errores, latencia y staleness | `S1` si no hay señal para diagnostico; `S3` si falta una metrica secundaria | Monitor |
| Tests | Cubrir contrato y regresiones de schema | Requerir fixtures estables, tests de parser, tests de paginado y tests de errores recuperables | `S1` si no hay cobertura minima del parser; `S2` si faltan tests de escenarios raros | Gate |

## Checks minimos por dimension

### 1. Contrato del item

- Cada item debe tener `external_id` estable dentro de la fuente.
- `url` debe ser resoluble y representar el item canonical.
- `provenance.source` debe coincidir con `source`.
- `freshness.first_seen_at` y `freshness.fetched_at` deben estar en UTC.

### 2. Freshness por tipo de fuente

Los umbrales definen cuando un item o una corrida pasa de saludable a degradada. Si una fuente publica su propio SLA mas estricto, ese SLA reemplaza estos defaults.

| Tipo de fuente | Ejemplos | Esperado saludable | Degradado `S2` | Critico `S1` |
| --- | --- | --- | --- | --- |
| Diaria | diarios economicos, newsletters de mercado, resumenes de cierre | `fetched_at - published_at <= 6h` y ultima corrida exitosa <= 24h | atraso > 6h y <= 24h, o sin corrida exitosa por > 24h y <= 48h | atraso > 24h, o sin corrida exitosa por > 48h |
| Semanal | informes semanales, outlooks de estrategia | `fetched_at - published_at <= 2d` y ultima corrida exitosa <= 7d | atraso > 2d y <= 7d, o sin corrida exitosa por > 7d y <= 14d | atraso > 7d, o sin corrida exitosa por > 14d |
| Mensual | IPC, empleo, balances mensuales, reportes regulatorios | `fetched_at - published_at <= 3d` y ultima corrida exitosa <= 31d | atraso > 3d y <= 10d, o sin corrida exitosa por > 31d y <= 45d | atraso > 10d, o sin corrida exitosa por > 45d |
| Evento | FOMC, comunicados urgentes, conferencias, filings extraordinarios | `fetched_at - published_at <= 1h` y polling acorde a ventana del evento | atraso > 1h y <= 6h | atraso > 6h o evento perdido en la ventana esperada |

Reglas adicionales:

- Si `published_at` no existe, usar `first_seen_at` para SLA operativo y marcar el item como de menor confianza temporal.
- Un item historico incorporado por bootstrap puede quedar fuera de SLA sin ser error si se etiqueta como backfill.
- `is_stale` debe calcularse contra el TTL operativo del conector, no solo contra la fecha editorial.

## Logging requerido ante fallo parcial

Cuando una corrida obtiene una respuesta parcial, una pagina vacia inesperada, un subset de items invalido o un error recuperable que no invalida toda la ejecucion, el conector debe emitir un log estructurado por evento de fallo y un resumen por corrida.

### Evento de fallo parcial

Campos obligatorios:

- `event`: `connector.partial_failure`
- `connector`
- `source`
- `run_id`
- `cursor`
- `fetch_url`
- `attempt`
- `error_type`
- `error_message`
- `recoverable`
- `status_code` cuando exista
- `items_received`
- `items_emitted`
- `items_dropped`
- `has_more`
- `next_cursor`
- `latency_ms`
- `fetched_at`
- `parser_version`

Campos recomendados:

- `retry_after_seconds`
- `response_bytes`
- `content_type`
- `trace_id`
- `sample_external_ids` de items descartados o sospechosos

### Resumen de corrida

Al cerrar la corrida, incluso si termina en estado degradado, debe existir un log de resumen con:

- `event`: `connector.run_summary`
- `connector`
- `source`
- `run_id`
- `started_at`
- `finished_at`
- `pages_fetched`
- `items_received_total`
- `items_emitted_total`
- `items_dropped_total`
- `recoverable_errors_total`
- `non_recoverable_errors_total`
- `stale_items_total`
- `status`: `success`, `partial_success` o `failed`

### Reglas operativas

- Un fallo parcial no debe borrar el cursor exitoso anterior.
- Si una pagina trae mezcla de items validos e invalidos, se emiten los validos y se loguean los invalidos con causa.
- Si la fuente responde vacio de forma inesperada pero `has_more` era probable, registrar el cursor y cortar la corrida como `partial_success`.
- Si se agotaron retries en un tramo del paginado, el resumen debe dejar claro hasta que cursor hubo cobertura confirmada.

## Suite minima de validacion

- Fixture estable para parseo base.
- Caso con item incompleto para validar rechazo y logging.
- Caso con `429` y respeto de `Retry-After`.
- Caso con pagina parcial para verificar `items_emitted` parcial y resumen degradado.
- Caso de freshness por cada tipo de fuente usado por el proyecto.

## Uso recomendado

1. Completar la matriz durante onboarding de cada conector.
2. Marcar severidad real observada por check.
3. Bloquear rollout si existe cualquier `S0` o una combinacion de `S1` sin mitigacion.
4. Reusar los campos de logging como contrato comun entre conectores y pipeline.
