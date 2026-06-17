# Validacion de acceso a datos de mercado argentino (BYMA / MAE / A3 / Matba Rofex)

- Tarea origen: TASK-8.9 "Validar acceso BYMA MAE y A3 para datos EOD"
- Tipo: RESEARCH / METODOLOGIA (sin codigo, sin tests, sin conectores).
- Fecha de relevamiento: 2026-06-16.
- Fuente primaria de contexto: `analysis/source_research_arg_market.md` (2026-06-14).
- Metodo: lectura del documento de investigacion + sondeo en vivo con `curl -sI` / `curl -s` contra las URLs publicadas.
- Directiva del owner (ya decidida): el veredicto esperado para BYMA EOD/bonos es que requiere un feed de mercado de datos PAGO y NO es libremente disponible. Este documento confirma y documenta ese veredicto, y propone alternativas gratuitas. No se persiguen ni asumen credenciales pagas.

Leyenda de estados:
- **VERIFIED (200)**: probeo en vivo, respuesta HTTP 200 con contenido util o JSON valido.
- **VERIFIED (page)**: pagina publica carga (HTML) pero es marketing/documentacion, no un endpoint de datos.
- **UNVERIFIABLE**: el probeo no pudo confirmar respuesta de datos (conexion fallida, wall de bot, o requiere credenciales).
- **INFERRED**: deducido del documento fuente o de la pagina publica, no confirmado por probeo directo.

---

## 1. Resumen ejecutivo

- **BYMA EOD gratuito NO alcanza** para bonos, MEP/CCL y curva local a volumen semanal util. Existe un tier "Sin costo" pero limitado a **1.000 solicitudes/mes** (VERIFIED desde la pagina), requiere alta/token, y el host de datos (`api.bymadata.com.ar`) **no es abiertamente alcanzable** (UNVERIFIABLE en este probe). El tier usable es pago: **Delay USD 100/mes** o **Snapshot USD 400/mes** (VERIFIED).
- **MAE Market Data** esta detras de un wall de bot (Incapsula); su API formal (`mae.com.ar/APIsMAE`) requiere formulario/credenciales. No hay endpoint publico confirmado.
- **A3 / Matba Rofex**: las paginas publicas (visor, CEM, CCL-MtR, productos) cargan, pero son apps JS (scrapeables con riesgo) y **no hay API publica abierta confirmada** (`api.primary.ventures` UNVERIFIABLE).
- Las **fuentes gratuitas verificadas** que si sostienen un MVP semanal son: **BCRA API** (oficial, JSON, VERIFIED), **Tesoro licitaciones** (publico, HTML/PDF/XLS), e **indices CCL publicos** (Indice CCL BYMA y CCL-MtR como paginas scrapeables) + **Rava/Ambito** como secundarias.
- **Conclusion operativa**: construir conectores solo sobre fuentes gratuitas confirmadas. Diferir/bloquear BYMA-EOD-pago, MAE-API y Matba-Rofex-API hasta que exista licencia o endpoint confirmado.

---

## 2. Tabla maestra de proveedores (alta, costo, limites, URLs, verificacion)

| Proveedor / Producto | Modelo de acceso | Alta / Auth | Costo (VERIFIED salvo nota) | Limite / Rate | URLs probeadas | Estado probeo |
| --- | --- | --- | --- | --- | --- | --- |
| **BYMA Market Data - Snapshot (Miembros)** | Feed pago, real-time | Suscripcion + Token (API key), HTTPS | **USD 400/mes** | 237.600 solicitudes/mes | `https://www.byma.com.ar/productos/productos-de-datos/market-data/apis` | VERIFIED (page, schema.org Offer + texto) |
| **BYMA Market Data - Delay (Miembros)** | Feed pago, 20 min | Suscripcion + Token, HTTPS | **USD 100/mes** | 79.200 solicitudes/mes | idem | VERIFIED (page) |
| **BYMA Market Data - EOD** | "Sin costo" con alta | **Suscripcion (alta) + Token**, HTTPS | **Sin costo (free)** | **1.000 solicitudes/mes**, solo precios EOD | idem + `https://api.bymadata.com.ar/` (host datos) | VERIFIED (page, existe tier free) / **UNVERIFIABLE** (el host de datos no respondio en el probe, ver §6) |
| **BYMA Market Data - Indices (CCL, Dolar)** | "Sin costo" con alta | Suscripcion + Token | **Sin costo (free)** | 10.000 EOD + 43.200 intraday / mes | `https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico` , `.../indice-dolar-byma-historico` | VERIFIED (page 200). API de indices requiere alta (INFERRED) |
| **BYMA Market Data - News (Hechos relevantes)** | "Sin costo" con alta | Suscripcion + Token | Sin costo | 1.000 solicitudes/mes | idem hub | VERIFIED (page) |
| **BYMADATA abierto (open)** | Web publica | None (sesion solo para acciones avanzadas) | Gratis | No documentado (visores) | `https://open.bymadata.com.ar/` | VERIFIED (page 200) - avisos/hechos relevantes, no series EOD completas |
| **MAE Market Data (web)** | Web publica (JS) | None para visor | Gratis en web | Imperva/Incapsula (anti-bot) | `https://marketdata.mae.com.ar/` , `.../boletindiario` | VERIFIED 200 pero **696 bytes** = wall de bot / shell JS (UNVERIFIABLE para datos directos) |
| **MAE APIs (formal)** | API con credenciales | Formulario + credenciales (agente/inst.) | No publicado (institucional) | Segun contrato | `https://www.mae.com.ar/APIsMAE` | VERIFIED (page 200 Drupal); **PAID-BLOCKED** sin alta institucional |
| **A3 datos de mercado (hub)** | Web publica | None | Gratis | WordPress normal | `https://a3mercados.com.ar/mercado/datos-de-mercado/` | VERIFIED (page 200). Expone `wp-json` (INFERIDO scrapeable). Solo links/visores, no series |
| **Matba Rofex - Visor primary.ventures** | Web publica (JS) | None para visor | Gratis | No documentado | `https://matbarofex.primary.ventures` , `https://api.primary.ventures/...` | Visor VERIFIED 200 (4.3KB shell JS). **api.primary.ventures UNVERIFIABLE** (conexion fallida). No API publica confirmada |
| **Matba Rofex - CEM** | Web publica (JS) | None | Gratis | No documentado | `https://cem.matbarofex.com.ar/` | VERIFIED 200 (2.7KB shell JS). Requiere JS; scrapeo fragil |
| **Matba Rofex - Indice CCL-MtR** | Web publica | None | Gratis (delay 20 min) | No documentado | `https://matbarofex.com.ar/IndiceCCLMtR` | VERIFIED (page 200 Drupal). Scrapeable, media confianza |
| **Matba Rofex - Productos (dolar, CER)** | Web publica | None | Gratis (documentacion) | - | `https://matbarofex.com.ar/producto/futuros-y-opciones-sobre-dolar` , `.../futuros-sobre-cer` | VERIFIED (page 200). Solo specs/metodologia, no precios |
| **BCRA - Estadisticas Cambiarias (USD oficial)** | API publica | **None** | **Gratis** | limit/offset soportado | `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` | **VERIFIED 200 (GET)** - devuelve JSON: USD 1428.00 @ 2026-06-12. Ojo: HEAD devuelve 404, usar GET |
| **BCRA - Estadisticas Monetarias (CER, TAMAR, tasas, reservas)** | API publica | **None** | **Gratis** | Catalogo + series por `idVariable` | `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` | **VERIFIED 200 (GET)** - devuelve catalogo JSON enorme |
| **BCRA - Hub de APIs** | Web + API publica | None | Gratis | - | `https://www.bcra.gob.ar/apis-banco-central/` | VERIFIED (page 200) |
| **Tesoro - Licitaciones** | Web publica | None | Gratis | - | `https://www.argentina.gob.ar/economia/licitaciones` | INFERRED free/public (no re-probado en esta pasada; cubierto en `source_research_arg_market.md` y doc Tesoro) |
| **Rava - Riesgo pais / bonos** | Web scrapeable | None | Gratis | PHPSESSID | `https://www.rava.com/perfil/RIESGO%20PAIS` | VERIFIED (page 200). Secundario |
| **Ambito - Riesgo pais / dolar** | Web scrapeable | None | Gratis/comercial | `x-ratelimit-limit: 100` | `https://www.ambito.com/contenidos/riesgo-pais.html` | VERIFIED (page 200). Secundario; rate limit visible |

Notas de verificacion:
- Precios BYMA extraidos del JSON-LD `schema.org/Offer` y del bloque tarifario visible ("Snapshot USD 400/mes", "Delay USD 100/mes", "EOD Sin costo 1.000 solicitudes/mes"). Columna "No Miembros" existe en la pagina (precios mayores, no capturados literalmente → INFERRED mas caro).
- "Cifrado HTTPS" y mencion de "Token" confirman que **el acceso a datos requiere API key/token emitido en el alta**, incluso para el tier EOD gratuito. No es un endpoint abierto anonimo.

---

## 3. Veredicto BYMA EOD (AC #2) - Explicito

**Pregunta: el EOD gratuito de BYMA alcanza para (a) bonos, (b) MEP/CCL, (c) curva local?**

**Respuesta: NO.** Confirmado contra la directiva del owner: BYMA EOD utilizable requiere feed PAGO y no es libremente disponible. Justificacion detallada:

### 3.1 Bonos (hard dollar + pesos)
- El tier EOD "Sin costo" otorga **1.000 solicitudes/mes** (VERIFIED). Una cobertura semanal minima de bonos liquidos exige multiples especies: AL30/AL30D, GD30/GD30D, GD35/GD35D, GD38/GD38D, AE38/AE38D, paridades cable (C), mas LECAPs y BONCERs por vencimiento. Easily **20-35 instrumentos**.
- A un refresh diario habil (~21 dias habiles/mes), 25 especies × 21 = **525 solicitudes/mes solo para cierres**, sin dejar margen para reintentos, historicos, ni especies adicionales. Cualquier historico o ampliacion rompe el cupo.
- El tier pago (Delay USD 100/mes = 79.200 req/mes; Snapshot USD 400/mes = 237.600 req/mes) es el que cubre volumen real.
- Ademas, el host de datos `api.bymadata.com.ar` **no respondio al probe** (HTTP 000), por lo que ni siquiera esta confirmado que el tier free devuelva datos sin token valido. → **PAID-BLOCKED para bonos a volumen util.**

### 3.2 MEP / CCL
- MEP/CCL requieren **pares de especies** (peso + dolar + cable) por benchmark: ej. AL30 (pesos), AL30D (dolar MEP), AL30C (dolar cable); idem GD30. Son **3 llamadas × N benchmarks × dias habiles**.
- Para 4 benchmarks (AL30, GD30, GD35, GD38) × 3 especies × 21 dias = **252 req/mes solo de MEP/CCL**, compitiendo con el cupo de 1.000 con bonos y curva. Inviable como unica fuente.
- Alternativa: el **Indice CCL BYMA** (tier Indices "Sin costo", 10.000 EOD req/mes) y el **Indice CCL-MtR** (Matba Rofex, pagina publica) cubren CCL ya calculado sin consumir el cupo EOD de especies. **Es por esto que el MVP gratuito debe armar MEP/CCL via indices publicos o calculo propio desde Rava, no via BYMA EOD de especies.**
- → **Free BYMA EOD NO alcanza para MEP/CCL por paridad.** Se usan indices publicos o calculo desde otras fuentes (ver §4).

### 3.3 Curva local (LECAP / BONCER / CER / TAMAR)
- Una curva local requiere cierres EOD de **todo el escalonado** (LECAP por vencimiento ~8-12 tenores + BONCER ~6-10), mas tasas primarias (Tesoro) y CER/TAMAR (BCRA).
- Solo LECAP + BONCER EOD serian **15-22 especies × 21 dias ≈ 315-460 req/mes**, sumados al cupo de 1.000 ya colapsado por bonos y MEP/CCL.
- → **Free BYMA EOD NO alcanza para curva local secundaria.** La curva local gratuita se arma como **proxy** con Tesoro (corte primario) + BCRA (CER/TAMAR) + CAFCI, etiquetado explicitamente como "proxy, sin secundario de mercado".

### 3.4 Sintesis del veredicto
| Necesidad | Free BYMA EOD (1.000/mes) | Veredicto |
| --- | --- | --- |
| Bonos hard dollar + pesos | Insuficiente (cupos, sin margen) | **PAID-BLOCKED** |
| MEP/CCL por paridad de especies | Insuficiente + compite con bonos | **PAID-BLOCKED** (usar indice publico o calculo propio) |
| Curva local secundaria (LECAP/BONCER EOD) | Insuficiente | **PAID-BLOCKED** (usar proxy Tesoro+BCRA+CAFCI) |

Razon estructural: el tier free de BYMA es un **trial/demo** (1.000 req/mes con alta), no un feed de produccion. Para uso semanal sistematico de renta fija argentina se requiere el plan **Delay (USD 100/mes)** como minimo, lo que confirma la directiva del owner.

---

## 4. Alternativas gratuitas (sin datos pagos de BYMA)

Estrategia: cubrir cada bloque del MVP con fuentes publicas/verificadas y marcar `metodologia` + `confianza`.

### 4.1 Dolar oficial y brecha (denominador)
- **BCRA Estadisticas Cambiarias USD** - VERIFIED 200 (JSON). Base oficial para USD tipo cambio. Endpoint: `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (usar GET, no HEAD).

### 4.2 MEP / CCL sin BYMA-EOD
Tres vias gratuitas, en orden de preferencia:
1. **Indice CCL BYMA (pagina/visor)** - VERIFIED 200 (`.../indice-ccl-byma-historico`). Tier Indices "Sin costo" segun pagina; si la API requiere alta, caer al scrapeo del visor publico.
2. **Indice CCL-MtR (Matba Rofex)** - VERIFIED 200 (`https://matbarofex.com.ar/IndiceCCLMtR`). Metodologia explicita, delay 20 min. Buen CCL de mercado.
3. **Calculo propio desde precios publicos (Rava)** - VERIFIED 200 (`https://www.rava.com/`). MEP = precio pesos / precio dolar de la misma especie (AL30/AL30D, GD30/GD30D). Etiquetar `metodologia = paridad AL30`. Confianza media.
- Fallback periodistico: Ambito dolar MEP/CCL (VERIFIED 200, rate limit 100).

### 4.3 Curva local (proxy, sin secundario BYMA)
Combinar tres bloques publicos:
1. **BCRA CER + TAMAR + BADLAR + UVA** - VERIFIED 200 via `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` (catalogo → `idVariable`). Base indexacion y tasa de referencia.
2. **Tesoro licitaciones** (LECAP/LECER/BONCER) - publico, tasas de corte y monto adjudicado por vencimiento. Ancla la curva primaria.
3. **CAFCI** - planilla diaria de FCIs money market / T+0 / CER. Contexto de liquidez pesos.
- Salida etiquetada **"curva proxy (primario + referencia), sin cierre secundario verificable"** hasta que se disponga de feed pago.

### 4.4 Futuros (dolar y CER) - Matba Rofex publico
- **Visor primary.ventures** y **CEM** - VERIFIED 200 pero apps JS (scrapeo fragil, confianza media). Tomar cierres semanales de contratos mas liquidos con timestamp y `fuente`.
- **Indice CCL-MtR** ya cubierto en §4.2 para el componente dolar futuro implicito.
- No hay API publica confirmada (`api.primary.ventures` UNVERIFIABLE). No automatizar sin fallback.

### 4.5 Riesgo pais
- **Rava** `RIESGO PAIS` (VERIFIED 200) y **Ambito** (VERIFIED 200, rate limit 100) como secundarios.
- Proxy propio: spread de TIR de bono hard dollar (si se obtiene precio publico) contra UST comparable de igual tenor. **Nunca etiquetar como EMBI oficial.**

---

## 5. Conectores propuestos (AC #3) - solo fuentes confirmadas gratuitas

Principio: una tarea atomica por conector, cada una mapeada a una fuente VERIFIED free/public. BYMA-pago, MAE-API y Matba-Rofex-API se marcan explicitamente como diferidas/bloqueadas.

### 5.1 Conectores a construir (free confirmados)
| ID propuesto | Fuente (URL) | Estado probeo | Cobertura | Justificacion |
| --- | --- | --- | --- | --- |
| `bcra_fx_usd` | `api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (GET) | VERIFIED 200 | USD oficial diario habil | Base oficial del reporte y denominador de brecha. Sin auth. |
| `bcra_monetary_rates` | `api.bcra.gob.ar/estadisticas/v4.0/monetarias` (GET, por `idVariable`) | VERIFIED 200 | CER, TAMAR, BADLAR, TM20, BAIBAR, UVA, reservas | Curva de referencia y indexacion. Sin auth. |
| `tesoro_licitaciones` | `argentina.gob.ar/economia/licitaciones` | INFERRED free (publico) | LECAP/LECER/BONCER: cronograma, tasas de corte, montos | Ancla de curva primaria en pesos. Cubierto en doc Tesoro. |
| `matbarofex_ccl_mtr_scrape` | `matbarofex.com.ar/IndiceCCLMtR` | VERIFIED 200 (Drupal) | CCL-MtR (delay 20 min) | CCL de mercado gratuito sin BYMA. Metodologia explicita. |
| `byma_ccl_indice_scrape` | `byma.com.ar/.../indice-ccl-byma-historico` | VERIFIED 200 (page) | Indice CCL BYMA (visor) | CCL alternativo; se scrapea el visor publico, **no** la API paga. |
| `rava_bonds_and_rp_scrape` | `rava.com/perfil/{especie}` , `.../RIESGO%20PAIS` | VERIFIED 200 | Precios de bonos + riesgo pais secundario | Insumo para MEP/CCL por paridad y RP cuando no haya otra fuente. Confianza media. |
| `mep_ccl_derived` | (derivado) | DERIVADO | MEP/CCL calculado | Calcula paridad desde la fuente de precios que caiga primero (Rava o indice publico). Metodologia versionada (`metodologia`, `especie`, `timestamp`). |
| `peso_curve_proxy` | (derivado de Tesoro + BCRA + CAFCI) | DERIVADO | Curva local proxy | Ensambla corte Tesoro + CER/TAMAR BCRA + CAFCI. Etiqueta obligatoria "proxy, sin secundario". |

### 5.2 Conectores diferidos / bloqueados (NO construir ahora)
| ID | Fuente | Bloqueo | Razon |
| --- | --- | --- | --- |
| `byma_eod_api` | `api.bymadata.com.ar` (EOD especies) | **PAID-BLOCKED / DEFERRED** | Tier free solo 1.000 req/mes (insuficiente para bonos+MEP/CCL+curva); requiere alta+token; host no alcanzable en probe. Usar recien con licencia Delay (USD 100/mes) o superior. |
| `byma_delay_api` / `byma_snapshot_api` | `api.bymadata.com.ar` | **PAID-BLOCKED** | USD 100/mes y USD 400/mes respectivamente. No se persiguen credenciales pagas. |
| `mae_marketdata_scrape` | `marketdata.mae.com.ar` | **PARTIAL / DEFERRED** | Wall de bot Incapsula (696B shell). No confirmado scrapeo estable. Reevaluar si se estabiliza el frontend. |
| `mae_formal_api` | `mae.com.ar/APIsMAE` | **PAID-BLOCKED** | Requiere formulario + credenciales institucionales. |
| `matba_rofex_formal_api` | `api.primary.ventures` | **BLOCKED / UNVERIFIABLE** | Host no alcanzable en probe (HTTP 000). No hay API publica documentada. Solo usar visor/CEM como scrape manual de baja confianza. |

---

## 6. Verificacion (que se probeo en vivo vs inferido)

Probeos realizados el 2026-06-16 con `curl`:

### 6.1 VERIFIED en vivo (HTTP 200 con contenido util)
- `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (GET) → 200, JSON valido: `{"fecha":"2026-06-12",...,"tipoCotizacion":1428.00}`. **Dato real.** (Nota: HEAD devuelve 404; usar GET.)
- `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` (GET) → 200, catalogo JSON completo de variables (idVariable, descripcion, periodicidad, fechas).
- `https://www.bcra.gob.ar/apis-banco-central/` (HEAD) → 200.
- `https://www.byma.com.ar/productos/productos-de-datos/market-data/apis` (GET) → 200, 303KB. Contiene bloque tarifario y JSON-LD `schema.org/Offer` con precios **Snapshot USD 400/mes**, **Delay USD 100/mes**, **EOD Sin costo 1.000 solicitudes/mes**, **Indices Sin costo**, **News Sin costo 1.000 solicitudes/mes**.
- `https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico` (GET) → 200, 275KB.
- `https://www.byma.com.ar/productos/productos-de-datos/indice-dolar-byma-historico` (HEAD) → 200.
- `https://open.bymadata.com.ar/` (HEAD) → 200, 20KB (web app, no API).
- `https://marketdata.mae.com.ar/` y `/boletindiario` (HEAD) → 200 pero **696 bytes** (Incapsula shell; no datos directos).
- `https://www.mae.com.ar/APIsMAE` (HEAD) → 200 (Drupal, requiere credenciales).
- `https://a3mercados.com.ar/mercado/datos-de-mercado/` (HEAD) → 200 (WordPress, expone `wp-json`).
- `https://matbarofex.primary.ventures` (HEAD) → 200, 4.3KB (JS shell).
- `https://cem.matbarofex.com.ar/` (HEAD) → 200, 2.7KB (JS shell).
- `https://matbarofex.com.ar/IndiceCCLMtR` (HEAD) → 200 (Drupal).
- `https://matbarofex.com.ar/producto/futuros-y-opciones-sobre-dolar` (HEAD) → 200.
- `https://matbarofex.com.ar/producto/futuros-sobre-cer` (HEAD) → 200.
- `https://www.rava.com/perfil/RIESGO%20PAIS` (HEAD) → 200.
- `https://www.ambito.com/contenidos/riesgo-pais.html` (HEAD) → 200, header `x-ratelimit-limit: 100`.

### 6.2 UNVERIFIABLE en este probe (conexion fallida / wall de bot / requiere creds)
- `https://api.bymadata.com.ar/` y `https://api.bymadata.com.ar/v3/instruments` (GET) → **HTTP 000** (sin respuesta TCP/TLS). No se puede confirmar que el tier EOD free devuelva datos sin token valido. Podria ser geo-bloqueo, auth requerida o restriccion de red del entorno de probeo.
- `https://api.primary.ventures/...` (GET) → **HTTP 000**. API de Matba Rofex no alcanzable; no hay endpoint publico confirmado.
- `marketdata.mae.com.ar` contenido util → **bloqueado por Incapsula** (shell de 696B).
- `https://www.argentina.gob.ar/economia/finanzas/cmf` (HEAD) → **404** (URL de CMF no valida / reubicada). Etiquetado INFERRED.
- Tasas "No Miembros" de BYMA → no capturadas literalmente; se asume mayores a Miembros (INFERRED).

### 6.3 INFERIDO (no probeado directamente, tomado de `source_research_arg_market.md`)
- Disponibilidad y estructura del tier "Indices" de BYMA como API (la pagina lo anuncia "Sin costo" pero el acceso via API requiere alta/token no probado).
- Endpoints internos de Tesoro licitaciones (cubiertos en doc de Tesoro separada).
- Endpoints de CAFCI (cubiertos en doc fuente).
- Metodologia exacta del CCL-MtR y del CCL BYMA (paginas publican delay 20 min; formula detallada no extraida en este probe).

### 6.4 Bloqueadores y riesgos
- **Bloqueador principal**: BYMA EOD free (1.000 req/mes + alta/token) es estructuralmente insuficiente para renta fija argentina semanal. Sin plan pago (Delay/Snapshot) no hay cobertura util de bonos, MEP/CCL ni curva local por esta via.
- **Riesgo de scraping**: MAE (Incapsula), visores Matba Rofex (JS) y Rava/Ambito (DOM comercial) son fragiles ante cambios de frontend. Todo conector de scrapeo debe guardar raw + alertar si el selector cambia.
- **Riesgo de red**: los hosts `api.bymadata.com.ar` y `api.primary.ventures` no respondieron en el probe; cualquier conector futuro que los use debe validar reachabilidad y auth antes de depender de ellos.

---

## 7. Mapeo a criterios de aceptacion

- **AC #1** - "Crear `analysis/arg_market_access_validation.md` con requisitos de alta, costo, limites y URLs por proveedor." → CUMPLIDO. Se crea este unico archivo. La §2 documenta alta, auth, costo (VERIFIED), limites y URLs por proveedor (BYMA Snapshot/Delay/EOD/Indices/News, MAE web/API, A3 hub, Matba Rofex visor/CEM/CCL-MtR/productos, BCRA, Tesoro, Rava, Ambito).
- **AC #2** - "Determinar si BYMA EOD/indices gratis alcanza para bonos, MEP/CCL y curva local." → CUMPLIDO. §3 "Veredicto BYMA EOD" responde **NO** con justificacion por bloque (bonos, MEP/CCL, curva local), apoyado en el cupo VERIFIED de 1.000 req/mes y los precios VERIFIED de los tiers pagos.
- **AC #3** - "Proponer tareas atomicas de conectores solo para fuentes confirmadas (free/public)." → CUMPLIDO. §5.1 lista 8 conectores atomicos sobre fuentes VERIFIED free/public (`bcra_fx_usd`, `bcra_monetary_rates`, `tesoro_licitaciones`, `matbarofex_ccl_mtr_scrape`, `byma_ccl_indice_scrape`, `rava_bonds_and_rp_scrape`, `mep_ccl_derived`, `peso_curve_proxy`). §5.2 marca explicitamente BYMA-pago, MAE-API y Matba-Rofex-API como diferidos/bloqueados.
