# Metodologia: dolar MEP, dolar CCL y proxy de spread soberano (Argentina)

Fecha de redaccion: 2026-06-16
Rama: `research/task-8.10-mep-ccl-methodology`
Tarea origen: TASK-8.10 (`Definir metodologia MEP CCL y spread soberano proxy`)
Documentos base: [analysis/source_research_arg_market.md](./source_research_arg_market.md) y [analysis/report_context_pack.md](./report_context_pack.md).

---

## 1. Objetivo y alcance

Definir, con fuentes publicas y gratuitas unicamente, como se calculan y validan para el reporte semanal tres bloques del tablero de mercado:

1. **Dolar MEP** (Mercado Electronico de Pagos / Contado Inmediato).
2. **Dolar CCL** (Contado Con Liquidacion).
3. **Proxy de spread soberano** que reemplaza al EMBI/EMBIG de J.P. Morgan (propietario, no licenciado).

Restriccion dura (ver veredicto paralelo TASK-8.9): el feed pago de BYMA no esta disponible. La metodologia debe ser **computable sin credenciales pagas**, usando el plan EOD gratuito de BYMA (1.000 solicitudes/mes segun pagina), visores/scraping de MAE/Matba Rofex como respaldo, y APIs oficiales (BCRA, Tesoro, Treasury/FRED). Cualquier numero que no pueda sostenerse con estas fuentes debe marcarse como `open_gap` y no publicarse como hecho.

Esta metodologia **no** reimplementa el EMBI, no mezcla blue con MEP/CCL, y no publica TIR/paridad sin cashflows verificables.

---

## 2. Definiciones y formulas  (AC #1)

### 2.1 Principio comun: paridad de un bono en dos tramos de moneda

MEP y CCL son dos lecturas del mismo principio: el dolar implicito que surge de comparar el precio en pesos y en dolares del **mismo** instrumento de deuda soberana argentina. La diferencia estructural entre ambos **no es un factor de ajuste** que se aplica a una unica cifra; es el **canal de liquidacion de la pata en dolares**, que determina que tramo (ticker) se usa y por lo tanto que precio se obtiene.

```
dolar_implicito(ARS por USD) = Precio_ARS(bono) / Precio_USD(bono)
```

donde `Precio_ARS` y `Precio_USD` son precios de cierre/ajuste del mismo bono en sus dos tramos de moneda, tomados al mismo timestamp y misma fecha de liquidacion operativa.

### 2.2 Dolar MEP (liquidacion CI / domestica)

```
MEP = P_ARS(bono_base) / P_USD(bono_C)
```

- `bono_base`: tramo en pesos, ley argentina (ej. AL30, GD30, AL29, GD35, GD38).
- `bono_C`: **mismo** bono, denominado en USD bajo ley argentina, liquidable por **CI (Caja de Valores)**. Ticker con sufijo `C` (ej. AL30C, GD30C).
- La pata USD queda depositada en cuenta comitente local (CI). No hay envio de fondos al exterior.
- Resultado: tipo de cambio ARS/USD operable en plaza local, sin pasar por el cepo/cambio exterior.

### 2.3 Dolar CCL (liquidacion offshore / contado con liquidacion)

```
CCL = P_ARS(bono_base) / P_USD(bono_D)
```

- `bono_base`: mismo tramo en pesos que en MEP.
- `bono_D`: **mismo** bono, denominado en USD bajo ley extranjera (Nueva York), depositable en **Euroclear/CB** y por lo tanto envieable al exterior via swap de contado con liquidacion. Ticker con sufijo `D` (ej. AL30D, GD30D).
- La pata USD se liquida offshore; el ratio refleja el costo/friccion de sacar dolares del pais.
- Por eso, estructuralmente, **CCL >= MEP** (el canal offshore incorpora la prima por la restriccion cambiaria).

### 2.4 Supuestos de liquidacion y moneda (explicitos)

- **Mismo bono, misma fecha de cierre**: las dos patas deben corresponder al mismo ajuste/cierre del mismo dia habil. No mezclar precio intradiario de una pata con cierre de la otra.
- **Misma especie subyacente**: el tramo en pesos y el tramo en USD deben ser pari passu (mismo emisor, mismo flujo de fondos, misma moneda de referencia tras el clone). Esto vale para los bonos del canje 2020 y posteriores; **se rompe** si un tramo se reestructura, cede o paga amortizaciones distintas (ver 6).
- **Sin factor de ajuste CI extra**: la brecha MEP-vs-CCL surge de que `P_USD(bono_C)` y `P_USD(bono_D)` son precios de mercado distintos (tramos distintos con liquidez y base inversor distintas), no de multiplicar MEP por un escalar. Documentar esto evita el error de modelar CCL como `MEP * (1 + k)`.
- **Precio a usar**: preferir **ajuste/cierre operado** (con volumen). Si solo hay ultimo precio sin volumen, bajar confianza (ver 5).
- **Calendario**: fecha de operacion = fecha de cierre BYMA. Dia habil Buenos Aires.

### 2.5 Brecha cambiaria (derivado sobre el oficial)

```
brecha_MEP = (MEP - USD_oficial_BCRA) / USD_oficial_BCRA
brecha_CCL = (CCL - USD_oficial_BCRA) / USD_oficial_BCRA
```

`USD_oficial_BCRA` viene de `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (primaria oficial, gratuita). La brecha es lectura derivada, no dato primario.

### 2.6 Proxy de spread soberano (NO EMBI)

El EMBI/EMBIG de J.P. Morgan es propietario y requiere licencia. Sin licencia se construye un **proxy propio de spread soberano**, claramente etiquetado como `proxy, no EMBI`.

```
spread_soberano_proxy = TIR(bono_D_AR) - YTM(UST_comparable)
```

- `bono_D_AR`: bono soberano argentino en USD ley extranjera (tramo `D`), cuyo precio de cierre se observa en BYMA EOD / MAE. Se usa la **TIR (yield to maturity)** calculada con el cashflow publicado del bono y el precio limpio de cierre.
- `UST_comparable`: Treasury (EE.UU.) de tenor/vencimiento comparable, **duration-match por vencimiento** (ej. GD30D ~ UST 10Y; GD38D/GD41D ~ UST 30Y). La curva de UST constant-maturity se toma de Treasury Direct / FRED (publico y gratuito).
- Resultado en puntos basicos (bps). Es un spread de **un bono** (o mediana de 2-3 bonos liquidos), no un basket equal-weighted como EMBIG; por eso **no es comparable 1:1 en nivel** con EMBI, solo direccionalmente.

**Alternativa secundaria del spread (cuando no hay cashflow verificable para TIR propia):**

```
spread_secundario = riesgo_pais_publicado(Rava | Ambito)
```

- Rava: `https://www.rava.com/perfil/RIESGO%20PAIS`
- Ambito: `https://www.ambito.com/contenidos/riesgo-pais.html`

Estas paginas atribuyen el numero a EMBI/JPM pero el dato se obtiene por scraping comercial; tratar como **proxy secundario scrapeable**, nunca como EMBI licenciado, y nunca mezclar niveles entre fuentes.

### 2.7 Indices publicados (referencia, no calculo propio)

Existen dos indices publicos gratuitos con metodologia explicita que se usan **solo como validacion cruzada** del calculo propio, no como fuente primaria del numero publicado en el reporte (para no acoplar la lectura a la metodologia/basket de un tercero):

- **BYMA Indice CCL**: `https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico` — basket definido por BYMA, intradiario con delay.
- **Matba Rofex Indice CCL-MtR**: `https://matbarofex.com.ar/IndiceCCLMtR` — consulta diaria con delay ~20 min, metodologia publica.

Regla: si el calculo propio y el indice publicado difieren mas de la tolerancia definida en 5, se investiga antes de publicar.

---

## 3. Universo minimo de especies  (AC #1)

Convencion de ticker (publica, estandar de mercado AR): **base = pesos ley AR**; **sufijo `C` = USD ley AR liquidable por CI**; **sufijo `D` = USD ley extranjera (Euroclear/CB)**.

### 3.1 Set minimo para MEP y CCL

| Par | Pata pesos | Pata MEP (C / CI) | Pata CCL (D / offshore) | Liquidez historica | Rol |
| --- | --- | --- | --- | --- | --- |
| AL30 | AL30 | AL30C | AL30D | alta | **Principal MEP+CCL** |
| GD30 | GD30 | GD30C | GD30D | alta | **Principal MEP+CCL** |
| AL29 | AL29 | AL29C | AL29D | media-alta | Secundario / cross-check |
| GD35 | GD35 | GD35C | GD35D | media | Cross-check tenor largo |
| GD38 | GD38 | GD38C | GD38D | media | Cross-check tenor largo |

**Minimo viable semanal**: computar MEP y CCL con **al menos dos pares liquidos** (AL30 + GD30). El reporte publica el par principal y valida contra el secundario (regla de acuerdo multi-especie, seccion 5). Si solo un par pasa el filtro de confianza, publicar ese con confianza `media` y abrir `open_gap`.

### 3.2 Set para proxy de spread soberano

| Bono hard dollar | Tenor aprox. | UST comparable | Fuente UST |
| --- | --- | --- | --- |
| GD30D | 2030 | UST 10Y | FRED/Treasury |
| GD35D | 2035 | UST 10Y/30Y interp. | FRED/Treasury |
| GD38D / GD41D | 2038/2041 | UST 30Y | FRED/Treasury |

Minimo: **un** bono D liquido (preferencia GD30D o GD38D) contra UST comparable. Publicar la mediana de 2-3 bonos si hay volumen.

### 3.3 Clasificacion primaria-publico vs proxy (riesgo de volverse pago)

| Especie / serie | Tipo | Fuente publica gratuita | Riesgo de ser pago |
| --- | --- | --- | --- |
| Precio ARS de AL30/GD30/AL29/GD35/GD38 | **Primario-publico** | BYMA EOD (1.000 req/mes); respaldo MAE web/Rava | Bajo (EOD gratuito) |
| Precio USD (C) de AL30C/GD30C/... | **Primario-publico** | BYMA EOD; MAE/Rava | **Medio** (tramo C suele tener menos volumen que D; en planes ajustados podria quedar fuera del tier gratuito) |
| Precio USD (D) de AL30D/GD30D/... | **Primario-publico** | BYMA EOD; MAE/Rava | Bajo |
| USD oficial BCRA | **Primario-oficial** | BCRA API cambiaria | Nulo |
| UST yields | **Primario-oficial** | FRED / Treasury Direct | Nulo |
| Cashflows de bonos (para TIR propia) | **Primario-publico** | Prospectos / paginas de Tesoro AR / open.bymadata | Medio (formato variable) |
| Indice CCL BYMA | **Proxy secundario** | Pagina/plan indices | Medio (plan indices puede cambiar) |
| Indice CCL-MtR | **Proxy secundario** | Matba Rofex web (delay 20 min) | Bajo-medio |
| Riesgo pais Rava/Ambito | **Proxy secundario scrapeable** | HTML comercial | **Alto** (DOM comercial inestable, no automatizar sin alerta) |
| Volumen operado por especie | **Primario-publico** (en EOD) / pago (real-time) | BYMA EOD si incluye volumen | Medio (el campo puede no venir en tier gratuito; si falta, degrada el filtro de volumen de 5) |

> **Decision operativa**: si el tier gratuito de BYMA EOD no entrega volumen por especie, el filtro de confianza (5.2) queda en su version debil (solo precios frescos + acuerdo multi-especie), y la confianza del MEP/CCL baja a `media` sistematicamente. Documentar en `open_gaps` del context pack.

---

## 4. Separacion de datos: primario, derivado, proxy  (AC #2)

La regla editorial del context pack (separar `dato`, `lectura`, `precio`) exige distinguir tres capas. Aqui se mapea cada capa a los conectores del proyecto (ver [analysis/connector_architecture.md](./connector_architecture.md)).

### 4.1 (a) Dato primario de precio (raw)

Precios/series observados, sin calculo, publicados por la fuente.

| Dato primario | Conector | Fuente | Frecuencia | Confianza fuente |
| --- | --- | --- | --- | --- |
| Precio cierre ARS de bonos base | `byma_eod` | BYMA EOD | diaria habil | alta |
| Precio cierre USD (C y D) | `byma_eod` | BYMA EOD | diaria habil | alta |
| Precio cierre renta fija (respaldo) | `mae_marketdata_scrape` | MAE web | diaria habil | media |
| USD oficial | `bcra_fx` | BCRA cambiaria | diaria habil | alta |
| UST yields | `ust_treasury` / `fred` | Treasury / FRED | diaria EE.UU. | alta |
| Volumen operado por especie | `byma_eod` (si disponible) | BYMA EOD | diaria habil | alta (o N/A si no viene) |
| Dolar futuro (contexto, no insumo MEP/CCL) | `matbarofex_visor` / `cem` | A3/Matba Rofex | intradiaria/cierre | media |

### 4.2 (b) Calculo derivado (a partir de precios primarios)

Transformaciones deterministas sobre datos primarios. Reproducibles, versionadas, sin nueva fuente.

| Calculo derivado | Componente | Formula | Insumos primarios |
| --- | --- | --- | --- |
| `mep_ccl_calculated` | MEP por par | `P_ARS / P_USD_C` (2.2) | precios ARS + precios C |
| `mep_ccl_calculated` | CCL por par | `P_ARS / P_USD_D` (2.3) | precios ARS + precios D |
| `mep_ccl_calculated` | MEP/CCL de tablero | mediana/ponderada por volumen de los pares que pasan filtro (5) | ratios por par + volumen |
| `brecha_cambiaria` | brecha MEP, brecha CCL | `(implicito - oficial)/oficial` (2.5) | MEP/CCL + USD oficial BCRA |
| `sovereign_spread_proxy` | spread por bono | `TIR(bono_D) - YTM(UST)` (2.6) | precio D + cashflow + UST |
| `sovereign_spread_proxy` | spread de tablero | mediana de bonos D liquidos | spreads por bono |

### 4.3 (c) Proxy secundario (suplencia de dato no disponible)

Numeros que reemplazan algo que no podemos computar/observar como primario. Siempre etiquetados y con `confidence_impact` negativo en el `source_index` del context pack.

| Proxy secundario | Reemplaza a | Fuente | Condicion de uso |
| --- | --- | --- | --- |
| Indice CCL BYMA | calculo propio de CCL (cuando faltan precios D) | BYMA indices | solo si faltan >=2 pares primarios |
| Indice CCL-MtR | calculo propio de CCL | Matba Rofex | idem; util como segundo proxy |
| Riesgo pais Rava/Ambito | EMBI JPM (no licenciado) | scraping comercial | solo lectura de nivel; marcar `no EMBI` |
| `spread_soberano_proxy` propio | EMBI JPM | TIR propia + UST | proxy primario; no igualar a EMBI en nivel |
| Rava/Ambito dolar MEP/CCL | calculo propio | scraping comercial | solo cuando BYMA EOD no responde; confianza `baja` |

### 4.4 Regla de no mezcla

- No mezclar capa primaria con proxy en el mismo numero publicado (ej. no promediar CCL propio con indice BYMA).
- No mezclar precios intradiarios con cierres EOD en la misma variacion semanal (ya en `source_research_arg_market.md`).
- Todo proxy baja al menos un nivel la confianza (`alta` -> `media`, `media` -> `baja`) segun `report_context_pack.md`.

---

## 5. Criterios de confianza para el reporte semanal  (AC #3)

Un numero (MEP, CCL, spread) se publica solo si supera los filtros siguientes. Los umbrales son **defaults operativos recomendados** (INFERRED como numeros; revisar/calibrar con historia propia). Se alinean con los tiers de freshness de `connector_quality_matrix.md`.

### 5.1 Freshness / staleness (TTL)

| Dato | TTL saludable | Degradado (bajar confianza) | Critico (suppress) |
| --- | --- | --- | --- |
| Precio de cierre ARS/USD de bonos | cierre del ultimo dia habil <= 1 dia habil | 2-3 dias habiles | > 3 dias habiles o sin cierre en la semana |
| USD oficial BCRA | <= 1 dia habil | 2 dias habiles | > 2 dias habiles |
| UST yields | <= 1 dia habil EE.UU. | 2-3 dias | > 3 dias |

Regla: el cierre semanal debe corresponder al **ultimo dia habil con sesion completa** en Buenos Aires. Feriados sin sesion se reportan como `open_gap`, no se rellenan con cierre anterior disfrazado de vigente.

### 5.2 Filtro de volumen / bid-acceptance

- **Volumen minimo por pata y por dia** (recomendado, INFERRED): excluir un par del calculo de tablero si cualquiera de las dos patas opero por debajo de un piso (sugerencia inicial: volumen diario < percentil 10 historico de la propia especie, o umbral absoluto a calibrar). Si el conector `byma_eod` no entrega volumen, pasar a la **version debil**: sin filtro de volumen, confianza maxima del MEP/CCL = `media`.
- **Tipo de precio**: priorizar **ajuste/cierre operado**. Si solo se dispone de `ultimo precio` o `indicativo` sin volumen, bajar confianza un nivel.
- **Bid-acceptance**: si la fuente marca la operacion como indirecta/cruzada o sin profundidad de libro, no usar como par principal.

### 5.3 Filtro de outliers y reinicios

- **Sanity absoluto**: descartar ratio si `MEP` o `CCL` cae fuera de bandas operativas razonables (ej. < USD oficial o > 3x CCL historico reciente); son sintomas de precio sucio/stale/ajuste tecnico.
- **Reinicio/precio stale**: si el precio de una pata es identico al de N sesiones previas (sin variacion) y el resto del mercado se movio, sospechar congelamiento de ultima cotizacion sin operacion; excluir el par.

### 5.4 Acuerdo multi-especie (dual-pair agreement)

- Computar MEP y CCL con **>=2 pares liquidos** (minimo AL30 + GD30).
- **Tolerancia de dispersion** (INFERRED, calibrar): si la dispersion entre pares (max/min - 1) supera **1.5%** para MEP o **2.0%** para CCL, flag de investigacion; publicar la **mediana** y confidence `media`.
- Si la dispersion supera **5%**, suppress del numero de tablero; publicar solo el par principal con etiqueta `lectura condicional, dispersion alta` y abrir `open_gap`.

### 5.5 Concordancia con indices publicados

- Comparar el CCL propio contra **Indice CCL BYMA** y **CCL-MtR**. Diferencia esperada < ~1.5% (cada indice usa basket y horario propios). Si la diferencia supera **3%**, investigar antes de publicar; si persiste, confidence `baja` y nota en `open_gaps`.

### 5.6 Regla publicar / suprimir (resumen)

| Estado | Condicion | Accion en el reporte |
| --- | --- | --- |
| **Publicar `alta`** | primario fresco + volumen OK + >=2 pares + acuerdo dentro de tol + concordancia con indices | numero de tablero + lectura + cita primaria |
| **Publicar `media`** | una condicion degradada (sin volumen, o solo 1 par, o proxy secundario) | numero + etiqueta de metodo + nota de proxy |
| **Publicar `baja`** | dos o mas condiciones degradadas, o divergencia > tol sin resolucion | numero entre parentesis / "aproximado" + lectura condicional |
| **Suppress** | precio stale critico, dispersion > 5%, o falta de >=1 pata primaria y sin proxy confiable | no publicar numero; registrar `open_gap` con causa |

Estos estados se mapean 1:1 al campo `confianza` (`alta`/`media`/`baja`) y a `source_policy`/`open_gaps` del context pack, y al score de `weekly_signal_scoring`.

---

## 6. Supuestos y limitaciones

1. **Pari passu de los tramos**: la formula de paridad supone que el tramo en pesos y el tramo en USD (C o D) corresponden al mismo flujo de fondos. **Se rompe** si un tramo se reestructura, se cede, paga amortizaciones distintas, o entra en default selectivo. Mitigacion: chequear avisos de hechos relevantes en `open.bymadata.com.ar` antes de publicar.
2. **MEP y CCL no son `MEP * (1+k)`**: la brecha entre ambos emerge de precios de mercado de tramos distintos (C vs D), no de un escalar. Modelar CCL como ajuste de MEP es metodologicamente incorrecto.
3. **Disponibilidad del tier gratuito BYMA EOD**: 1.000 solicitudes/mes es suficiente para cierre semanal (~25 especies x 4-5 semanas), pero **no** para intradia. Si BYMA elimina el tier gratuito o cambia el campo de volumen, la confianza sistematica del MEP/CCL baja a `media` y se activa el respaldo MAE/Rava (mas frágil).
4. **Tramo C (MEP) menos liquido que D (CCL)**: el filtro de volumen suele ser el cuello de botella del MEP; en periodos de baja liquidez puede no haber par C usable y el MEP queda con par unico o sin par.
5. **Proxy de spread != EMBI**: metodologia distinta (un bono o mediana vs basket equal-weighted EMBIG). Correlacion direccional alta, pero niveles no comparables. Nunca etiquetar como EMBI ni comparar punto a punto con series licenciadas.
6. **Duration match aproximado**: emparejar GD30D con UST 10Y es una aproximacion por vencimiento, no por duration efectiva. Para mayor precision usar duration modificada y curva UST interpolada.
7. **Cashflows de TIR propia**: si no se obtienen cashflows oficiales limpios, no publicar TIR/spread propio; caer al proxy secundario Rava/Ambito con etiqueta `no licenciado`.
8. **Calendario y feriados**: feriados AR sin sesion producen ausencia de cierre; no rellenar. Feriados EE.UU. producen ausencia de UST; spread del dia anterior se marca stale.
9. **Scraping comercial (Rava/Ambito/Matba Rofex visor)**: inestabilidad de DOM; no usar como unica fuente para numero publicado; siempre con alerta de cambio de selector (`parser_version`) segun `connector_quality_matrix.md`.
10. **No automatizar broker reports**: curvas/lecturas de brokers/ALyCs son contexto cualitativo, no insumo numerico sin trazabilidad y permiso.

---

## 7. Fuentes y verificacion (VERIFIED vs INFERRED)

### VERIFIED (citados en `source_research_arg_market.md` y publicos)

- BCRA Estadisticas Cambiarias USD — `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (USD oficial primario).
- BYMA Market Data APIs (EOD gratuito, 1.000 req/mes) — `https://www.byma.com.ar/productos/productos-de-datos/market-data/apis` (precios de bonos ARS/C/D y volumen si el tier lo entrega).
- BYMA Indice CCL (metodologia y basket propios) — `https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico` (proxy de validacion).
- BYMA Indice Dolar — `https://www.byma.com.ar/productos/productos-de-datos/indice-dolar-byma-historico` (contraste).
- Matba Rofex Indice CCL-MtR (delay 20 min, metodologia publica) — `https://matbarofex.com.ar/IndiceCCLMtR` (segundo proxy de validacion).
- MAE Market Data / boletin / informe diario — `https://marketdata.mae.com.ar/` y subpaginas (respaldo de precios de renta fija).
- Rava (riesgo pais y precios de bonos) — `https://www.rava.com/perfil/RIESGO%20PAIS` y `https://www.rava.com/` (proxy secundario).
- Ambito (riesgo pais, dolar MEP/CCL) — `https://www.ambito.com/contenidos/riesgo-pais.html` y `https://www.ambito.com/contenidos/dolar.html` (proxy secundario periodistico).
- BYMADATA abierto (avisos, hechos relevantes) — `https://open.bymadata.com.ar/` (chequeo de reestructuras/cedencias).
- UST constant-maturity yields — Treasury Direct / FRED (baseline del spread soberano).

### VERIFIED como definicion publica estandar

- Las formulas de MEP (pata C / CI) y CCL (pata D / Euroclear) y la convencion de sufijos `C`/`D` son conocimiento publico estandar, consistente con lo que publican BYMA, Matba Rofex, Rava y Ambito. La estructura `CCL >= MEP` por canal de liquidacion es mecanica de mercado publica.

### INFERRED (no proviene de un spec citado; calibrar)

- Umbrales numericos de la seccion 5 (volumen minimo, dispersion 1.5%/2%/5%, concordancia con indices <1.5%/<3%, percentil 10 de volumen). Son **valores operativos recomendados** para arranque; deben calibrarse con historia propia del proyecto.
- Emparejamientos bono AR vs UST por vencimiento (GD30D~10Y, GD38D/GD41D~30Y) como duration-match aproximado.
- Disponibilidad efectiva del campo volumen en el tier EOD gratuito de BYMA (confirmar al implementar el conector; si no viene, activar 5.2 version debil).

### Riesgos metodologicos abiertos

- **R1**: confirmar que el tier gratuito BYMA EOD entrega volumen; sino, el filtro de volumen es no operativo y el MEP baja sistematicamente a `media`.
- **R2**: el tramo C (MEP) puede no tener par liquido en semanas de stress; definir protocolo de fallback a indice BYMA/MtR con etiqueta explicita.
- **R3**: la calibracion de umbrales (5) requiere 3-6 meses de historia propia; hasta entonces, publicar con tolerancias holgadas y confidence conservador.
- **R4**: sin licencia EMBI, el spread soberano nunca sera nivel-comparable con consenso de mercado; gestionar expectativa editorial y no titular sobre niveles absolutos de spread.
