# Validacion de descargas de vencimientos y cashflows del Tesoro

Tarea: TASK-8.7 — Validar descargas de vencimientos y cashflows Tesoro
Tipo: INVESTIGACION / METODOLOGIA (sin codigo, sin conectores, sin tests).
Fecha de verificacion en vivo: 2026-06-16.
Worktree: `/Users/ignacioreyna/PERSONAL/finance-news-worktrees/task-8.7`.
Fuente primaria de referencia: `analysis/source_research_tesoro.md`.
Base de evidencia: probing con `curl -sI`/`curl -s` contra URLs reales + inspeccion
de la estructura de los archivos XLSX descargados (ZIP/XML, sin Python).
Convencion: **VERIFIED** = probado en vivo el 2026-06-16. **INFERRED** = deducido
de la doc de referencia o del contenido pero no reprobadado en vivo.

> NOTA DE ALCANCE: este documento cubre la **estructura financiera de la deuda,
> cupones y calendario de vencimientos por instrumento** (stock + cashflows). NO
> cubre llamados/resultados de licitaciones, que son dominio del conector
> `tesoro_licitaciones` ya existente. Ver seccion "Limite de alcance vs
> tesoro_licitaciones".

---

## Resumen ejecutivo

- Las 8 paginas de deuda de Argentina.gob.ar y las 3 paginas de OPC responden
  **200 OK en vivo** (no son soft-404; contenido real verificado por titulo y
  marcadores).
- El endpoint real de cashflows es la pagina **"Estructura financiera de Titulos
  Publicos"**, que publica **dos archivos XLSX estables**:
  - `estructura_financiera_titulos_publicos_31-5-26_vf.xlsx` (descriptores +
    estructura del stock por instrumento, 14 hojas, versionado por fecha).
  - `cupones.xlsx` (calendario de servicios por instrumento, 116 hojas, una por
    instrumento/serie/ISIN). **URL estable pero nombre SIN version** -> hay que
    hashear para detectar actualizaciones silenciosas.
- Adicionalmente, la pagina **"Datos trimestrales de la deuda"** expone enlaces
  profundos predecibles `deuda_publica_DD-MM-YYYY[_n].xlsx` (stock por moneda,
  acreedor y legislacion), verificados para 2019-Q1 .. 2025-Q3. Los trimestres
  2026 aun **no publicados** (404, rezago esperado).
- **Recomendacion AC#2**: el primer conector debe leer **XLSX con openpyxl
  (modo lazy/read_only)** como formato unico primario (estructura + cupones +
  trimestral). CSV no se publica para estos datasets. PDF solo como fallback de
  reconciliacion (informes mensuales / OPC), nunca como fuente de cashflows.
- **Recomendacion AC#3**: las reglas anti doble conteo giran en torno a (a)
  separar STOCK vs SERVICIO, (b) recordar que cupones son coeficientes por
  denominacion minima (no nominales agregados), (c) netear canjes/conversiones
  por `operation_type`, (d) nunca mezclar monedas sin FX explicito, (e)
  excluir intra-sector-publico (BCRA/Organismos) cuando se reporta deuda con el
  sector privado.

---

## 1. Fuentes y enlaces finales (AC#1)

### 1.1 Paginas HTML de entrada (todas VERIFIED 200 el 2026-06-16)

| # | URL | Titulo verificado | Publicador | Frecuencia | Estabilidad del enlace |
|---|-----|-------------------|------------|------------|------------------------|
| P1 | `https://www.argentina.gob.ar/economia/finanzas/estructura-financiera-de-titulos-publicos` | "Estructura financiera de Titulos Publicos" | Secretaria de Finanzas / Mecon | Eventual (ante reaperturas, canjes, nuevos instrumentos) | Estable; resuelve enlaces XLSX directamente (P=a) |
| P2 | `https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda` | "Datos trimestrales de la deuda" | Mecon | Trimestral | Estable; enlaces XLSX predecibles y profundos (1.3) |
| P3 | `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda` | "Datos mensuales de la deuda" | Mecon | Mensual | Requiere resolucion de pagina (solo expone `calendario_de_publicaciones_2026.pdf` en la landing; el XLSX mensual esta anidado) |
| P4 | `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales` | "Datos mensuales" | Mecon | Mensual | Landing de serie mensual; requiere resolucion |
| P5 | `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda/informes-mensuales` | informes mensuales | Mecon | Mensual | Estable; informes PDF narrativos |
| P6 | `https://www.argentina.gob.ar/economia/finanzas/deuda-publica` | "Deuda publica" | Mecon | Eventual | Hub de seccion |
| P7 | `https://www.argentina.gob.ar/economia/finanzas/datos` | "Datos" | Mecon | Eventual | Hub de seccion |
| P8 | `https://www.argentina.gob.ar/economia/finanzas/informe-de-deuda-publica-en-pesos` | informe deuda publica en pesos | Mecon | Mensual/trim. | Estable |
| P9 | `https://opc.gob.ar/operaciones-de-deuda-publica/` | Operaciones de deuda publica | OPC (Congreso) | Mensual/eventual | Estable; HTML + PDF en subpaginas por mes |
| P10 | `https://opc.gob.ar/seguimiento-de-la-deuda-publica/` | Seguimiento de la deuda publica | OPC | Eventual | Estable |
| P11 | `https://opc.gob.ar/operaciones-de-deuda-publica/operaciones-de-deuda-publica-abril-2026/` | Operaciones abril 2026 | OPC | Mensual | Estable; subpagina mensual verificada |

Notas:
- La pagina P1 ("Estructura financiera") es **la fuente primaria de cashflows**.
- P2 ("Datos trimestrales") es la **fuente primaria de stock/composicion**.
- P9/P10/P11 (OPC) son **fuente independiente de contraste/reconciliacion**
  (organismo tecnico del Congreso). Marcadores de contenido verificados en P9
  (32 hits de `vencimiento|canje|conversi[o]n|deuda|stock|moneda extranjera`).

### 1.2 Archivos de descarga directa (VERIFIED en vivo: HTTP, content-type, size)

| # | URL | Formato | content-type | Tamano | last-modified | Rol |
|---|-----|---------|--------------|--------|---------------|-----|
| F1 | `https://www.argentina.gob.ar/sites/default/files/estructura_financiera_titulos_publicos_31-5-26_vf.xlsx` | XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 305 KB | **2026-06-08** (fresco) | Descriptor + estructura del stock por instrumento |
| F2 | `https://www.argentina.gob.ar/sites/default/files/cupones.xlsx` | XLSX | idem | 844 KB | 2019-08-08 (fecha de archivo; URL estable, contenido se actualiza sin renombrar) | Calendario de servicios (capital + interes) por instrumento |
| F3 | `https://www.argentina.gob.ar/sites/default/files/coeficientes_de_pago_de_pg_-_desde_enero_de_2019_en_adelante_25.xls` | XLS | `application/vnd.ms-excel` | 886 KB | **2026-05-28** (fresco) | Coeficientes de pago Prestamos Garantizados (deuda historica) |
| F4 | `https://www.argentina.gob.ar/sites/default/files/coeficientes_de_pago_de_pg_-_desde_enero_de_2018_hasta_enero_de_2019.xls` | XLS | `application/vnd.ms-excel` | 44 MB | 2019-07-25 (congelado) | PG historico 2018-2019 |
| F5 | `https://www.argentina.gob.ar/sites/default/files/deuda_publica_<DD-MM-YYYY>[_n].xlsx` | XLSX | idem openxml | ~1.5 MB | por trimestre | Stock trimestral por moneda/acreedor/legislacion |

Patron F5 VERIFIED para las fechas: `31-03-2019_1`, `30-06-2019_2`, `30-09-2019_1`,
`31-12-...`, ... hasta `30-09-2025`. Sufijo `_n` inconsistente entre años
(a veces `_0`, `_1`, `_2`, a veces sin sufijo) -> el conector debe **listar la
pagina P2 y resolver el href exacto**, no construir la URL a ciegas.

**STALE / NO DISPONIBLE (verificado 2026-06-16):**
- `deuda_publica_31-03-2026.xlsx`, `_0`, y `30-06-2026.xlsx` -> **404**. Los
  trimestres 2026 no estan publicados todavia (rezago normal). El conector debe
  tomar el ultimo trimestre disponible y marcar `as_of_date`.
- Trimestre 2025-Q4 (`31-12-2025`) **no verificado** en este probe (INFERIDO del
  patron; confirmar al implementar).

### 1.3 Enlace marcado como STALE en TASK-8.6

| URL | Estado TASK-8.6 | Estado 2026-06-16 | Accion |
|-----|-----------------|-------------------|--------|
| `https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro/cronograma-2026` | 404 (stale) | **200 OK con contenido real** (titulo "Cronograma 2026", 48 marcadores de contenido, sin marcadores "no encontrado") -> **RECUPERADO** | **FUERA DE ALCANCE**: es una pagina de LICITACIONES (cronograma de llamados), no de cashflows/vencimientos. Pertenece al conector `tesoro_licitaciones`. No usar para el conector de cashflows. |

### 1.4 Frecuencias y estabilidad (resumen)

- **F1 estructura_financiera**: eventual; nombre **versionado por fecha**
  (`_31-5-26_vf`). El conector debe descubrir el nombre actual en P1 porque el
  sufijo cambia (`_vf`, fecha de corte). Es el "punto en el tiempo" del stock.
- **F2 cupones**: URL fija `cupones.xlsx` **sin versionado** -> hay que
  **hashear (sha256) + comparar last-modified/etag** en cada poll. Riesgo de
  actualizacion silenciosa alto.
- **F3 coeficientes PG**: nombre incluye rango ("desde 2019 en adelante") y
  sufijo `_25` (anio de edicion); cambia con cada actualizacion. Resolver desde
  P1.
- **F5 deuda_publica trimestral**: enlaces profundos estables por fecha de
  corte; rezago de publicacion de ~1 trimestre.

---

## 2. Columnas requeridas (AC#1)

### 2.1 Esquema de `cupones.xlsx` (calendario de servicios — fuente primaria de cashflows)

Estructura: **116 hojas** = `Indice` + agregadas (`A 1.1`, `A 1.3`, `A 1.4`,
`A 1.5`, `A 1.8`, `A.1.10`, `A. 1.11`, `A.1.12`) + **una hoja por
instrumento/serie**. Las hojas por instrumento se nombran por:
- Codigo de especie argentina: `2426`, `5428`, `5311`, `5475`, `8713`...
- ISIN internacional: `XS1715303779`, `XS1503160225`, `US040114HP86` (en titulos),
  `CH0361824458`.
- Familia: `Par U$S`, `Par $`, `Par €`, `Par ¥`, `Discount U$S`, `Discount $`,
  `Discount €`, `Discount ¥`, `Cuasipar $`, `Global 2017`, `BIRAD 2019..2048`,
  `BIRAE 2022..2028`, `BIRAF 2020`, `Unidades Ligadas a PBI`.

Columnas/encabezados VERIFIED dentro de cada hoja por instrumento:

| Campo (string en el archivo) | Significado | Tipo esperado |
|------------------------------|-------------|---------------|
| `CÓDIGO / ESPECIE`, `ESPECIE`, `CODIGO CVSA` | Especie/serie local (BYMA/CVSA) | string |
| `CODIGO ISIN` (en titulos internacionales, ej. BIRAD/BIRAE) | ISIN | string(12) |
| Bloque `SERVICIOS` / `SERVICIOS (*)` | Encabezado del bloque de flujo | header |
| `CUPÓN N°` (1, 2, 3 ...) | Numero de cupon/servicio | int |
| `CUPÓN VIGENTE` / `CUPÓN VIGENTE (*)` | Cupon corriente (los CER usan el cupon previo, ver nota `*`) | pct |
| Fecha del servicio (filas) | Fecha de pago de capital + interes | date |
| `AMORTIZACIÓN A PAGAR` | Capital a pagar en la fecha | coeficiente/unidad |
| `INTERÉS A PAGAR` (con variantes "Mínima denominación 5.000/100.000/150.000") | Interes a pagar en la fecha | coeficiente/unidad |
| `VALOR DEL CUPÓN`, `VALOR TÉCNICO` | Valor del cupon / valor tecnico | coeficiente |
| `TASA ANUAL`, `TASA MENSUAL`, `TASA ANUAL + SPREAD` | Tasa aplicable | pct |
| `CAPITALIZACIÓN` | Marca de periodo de capitalizacion | flag |
| Bloque `Cupones Históricos` vs `Cupones Corrientes` | Pasados vs futuros | seccion |

**CRITICO**: las notas internas dicen textualmente *"Coeficientes expresados por
mínima denominación sobre valores nominales originales"* y *"En el caso de los
bonos cuyos cupones se calculan en base al CER, los mismos no son los corrientes
sino el cupón previo ... CER de 10 días hábiles anteriores al pago."*. O sea:
- Los valores de `AMORTIZACIÓN A PAGAR` e `INTERÉS A PAGAR` **NO son nominales
  agregados**: son coeficientes por unidad de denominacion minima sobre el VN
  original. Para obtener el cashflow total en ARS/USD hay que multiplicar por el
  **saldo nominal circulante** del instrumento (que viene de F1/F5).
- Para instrumentos CER hay un desfasaje de 10 dias habiles en el coeficiente.

### 2.2 Esquema de `estructura_financiera_titulos_publicos_*.xlsx` (descriptores + estructura del stock)

Estructura: **14 hojas** = `INDICE` + `A.1..A.7` (tablas por familia/tipo) +
`B`, `C`, `D`, `E` + `PL` + `OL`. Columnas descriptoras por instrumento VERIFIED:

| Campo (string en el archivo) | Significado |
|------------------------------|-------------|
| `INSTRUMENTO FINANCIERO` / `Instrumento financiero` | Descripcion del instrumento (ej. "BONOS CON AJUSTE POR C.E.R. 0% VTO. 30 de Junio de 2026") |
| `Tipo de bono` / `Tipo de Letra` | Familia (Bonos CER, BONARES, BONTE, Bono Capitalizable Tasa Cero/TAMAR, Letras, etc.) |
| `FECHA DE EMISIÓN` | Fecha de emision |
| `VENCIMIENTO` / `Vencimiento Original` | Vencimiento final |
| `Plazo original en años` / `Plazo original en dias` | Plazo |
| `TASA DE INTERÉS` | Tasa (fija, CER+spread, TAMAR TEM, BADLAR+spread, etc.) |
| `Ley aplicable` | Legislacion (Argentina / Nueva York / etc.) |
| `Denominación mínima` | Denominacion minima (clave para casar con cupones) |
| `Amortización` / `Capitalización` / `Cupón cero` | Condiciones de pago (texto) |
| Moneda | Implicita por familia: `$` pesos, `U$S` dolares, `€` euros, `¥` yenes, CER (pesos ajustables), dolar linked, PBI |

> La moneda **no** aparece siempre como columna literal; se infiere del
> descriptor y de la familia (INFERRED salvo donde es explicita). El conector
> debe normalizar moneda a partir del texto del instrumento.

### 2.3 Esquema de `deuda_publica_DD-MM-YYYY.xlsx` (stock/composicion trimestral)

Estructura: ~30 hojas = `INDICE` + `A.1.x` (stock por moneda) + `A.2.x` +
`A.3.x` (por acreedor/sector) + `A.4.x` (por legislacion/jurisdiccion).
Columnas/encabezados VERIFIED:

| Campo (string en el archivo) | Significado |
|------------------------------|-------------|
| `INSTRUMENTO` (`BONOS`, `LETRAS DEL TESORO`, `PRÉSTAMOS`, `TÍTULOS PÚBLICOS`, `Bonos de Consolidación`, `Préstamos Garantizados`, `Letras Intransferibles`, `Letras en Garantía`, etc.) | Tipo de instrumento |
| `Moneda` / `Moneda de origen` / `Moneda local` / `Moneda extranjera` / `EN MONEDA NACIONAL AJUSTABLE POR CER` | Trinchero por moneda |
| `Saldo al <fecha>` (ej. `Saldo al 31/03/2025`) | Stock nominal a la fecha de corte |
| `Saldo Bruto` / `Total Deuda` / `TOTAL` | Totales |
| `Capital` / `CAPITAL NETO` / `CAPITAL REEMBOLSADO` / `TOTAL DESEMBOLSOS (I)` | Capital |
| `Intereses` / `INTERESES PAGADOS` / `Intereses Totales Pagados` / `Intereses Compensatorios` | Intereses |
| `Tipo de Cambio (excluye deudas ajustables por CER)` | TC aplicado para convertir moneda extranjera (excluye CER) |
| Acreedor / Tenedor: `ORGANISMOS INTERNACIONALES`, `Préstamos Organismos Multilaterales`, `Préstamos Organismos Oficiales`, `LETRAS ADQUIRIDAS POR EL BCRA`, `Letras del Tesoro - Organismos Públicos`, `Organismos Oficiales` | Desglose por acreedor (clave para excluir intra-sector-publico) |

### 2.4 Columnas requeridas para el calendario de vencimientos normalizado (salida del conector)

Schema objetivo sugerido (1 fila = 1 servicio de 1 instrumento en 1 fecha):

| Columna | Origen | Notas |
|---------|--------|-------|
| `instrumento_id` | sintetico | hash(especie|isin|emision) |
| `especie` | F2 `CÓDIGO / ESPECIE` / `ESPECIE` | codigo local |
| `isin` | F2 `CODIGO ISIN` (si existe) | para titulos internacionales |
| `descripcion` | F1 `INSTRUMENTO FINANCIERO` | texto oficial |
| `familia` | F1 `Tipo de bono/Letra` | CER/BONARES/BONTE/... |
| `moneda` | F1 descriptor + F3 trichero | `$`,`U$S`,`€`,`¥`,`CER`,`DL`,`PBI` |
| `fecha_emision` | F1 `FECHA DE EMISIÓN` | |
| `fecha_vencimiento` | F1 `VENCIMIENTO` | |
| `ley_aplicable` | F1 `Ley aplicable` | AR/NY/... |
| `tasa` | F1/F2 `TASA...` | normalizada a pct anual |
| `fecha_servicio` | F2 fila (fecha) | fecha de pago |
| `nro_cupon` | F2 `CUPÓN N°` | |
| `amortizacion_coef` | F2 `AMORTIZACIÓN A PAGAR` | coeficiente por unidad |
| `interes_coef` | F2 `INTERÉS A PAGAR` | coeficiente por unidad |
| `saldo_nominal` | F1/F5 al `as_of_date` | nominal circulante |
| `capital_pago` = `amortizacion_coef` x `saldo_nominal` | derivado | cashflow capital |
| `interes_pago` = `interes_coef` x `saldo_nominal` | derivado | cashflow interes |
| `as_of_date` | F1 fecha de corte del archivo | version del stock |
| `source_url`, `raw_hash`, `retrieved_at`, `parser_version` | metadata | trazabilidad |
| `operation_type` | derivado (regular/canje/conversion/reapertura) | anti doble conteo |

---

## 3. Formato del primer conector (AC#2)

**Recomendacion: XLSX unicamente como primario, con openpyxl en modo
lazy/read_only, + PDF solo como fallback de reconciliacion.**

### 3.1 Justificacion

1. **XLSX es la unica superficie machine-readable autoritativa**. Los archivos
   F1 (estructura), F2 (cupones) y F5 (trimestral) son todos `.xlsx`. Sus
   content-types fueron verificados
   (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Las
   hojas estan estructuradas (no son imagenes).
2. **CSV no se publica para estos datasets**. La unica oferta CSV del Mecon/
   datos.gob.ar es para series fiscales (IMIG/base caja), que **no** son
   cashflows de deuda. Usar CSV obligaria a generar un derivado manual que se
   desincroniza. (INFERRED de `source_research_tesoro.md` sec. 5.)
3. **PDF es solo narrativo**. Los informes mensuales (P5) y los reportes OPC
   (P9/P11) son PDF de texto; no tienen tablas estables ni permiten armar un
   calendario de vencimientos por instrumento sin OCR/parsing fragil. Su rol es
   **reconciliacion y alertas cualitativas**, no fuente de cashflows.
4. **Patron recomendado**: replicar el patron "lazy openpyxl" del conector
   `bcra_balance_cambiario` (referenciado en el contexto del proyecto):
   `openpyxl.load_workbook(path, read_only=True, data_only=True)` y stream por
   hoja, para no cargar los 116 sheets de cupones ni los 44 MB del PG historico
   en memoria.

### 3.2 Decision combinatoria

| Formato | Rol en v1 | Por que |
|---------|-----------|---------|
| XLSX (openpyxl) | **Primario unico** | F1+F2+F5 cubren estructura + cupones + stock |
| XLS (legacy PG) | Soporte secundario | F3/F4 son `.xls` (formato antiguo); openpyxl no los lee -> requieren `xlrd` o conversion. Solo si se quiere el bucket PG historico. Postergar a v2. |
| CSV | **No** | No publicado por el publicador para estos datos |
| PDF | Fallback de reconciliacion | Solo para cruce con OPC/informes mensuales; parsing fuera del MVP |

**Conclusion AC#2**: el primer conector de cashflows/vencimientos debe leer
**XLSX** (y opcionalmente XLS legacy para PG en una fase posterior). **No** debe
incorporar CSV ni PDF como fuentes de datos estructurados en v1.

### 3.3 Manejo de enlaces (resolucion vs profundo)

- **F1 estructura_financiera**: nombre versionado por fecha -> **scrapear P1**
  para descubrir el href actual (no hardcodear `_31-5-26_vf`).
- **F2 cupones**: URL fija `cupones.xlsx` -> poll directo + **sha256 + etag +
  last-modified** para detectar cambios sin version.
- **F5 trimestral**: enlaces profundos predecibles pero sufijo `_n` inconsistente
  -> **scrapear P2** y resolver el href exacto por fecha de corte; nunca
  construir a ciegas.
- **P3 mensual**: la landing solo muestra `calendario_de_publicaciones_2026.pdf`;
  el XLSX mensual de stock esta anidado -> requiere crawl mas profundo o
  posponer (el trimestral F5 cubre el stock en v1).

---

## 4. Reglas anti doble conteo (AC#3)

Las reglas se agrupan en cinco ejes. Cada una incluye **que evitar** y
**como implementarlo**.

### 4.1 Stock vs servicio (el mas importante)

- **Regla 1**: nunca sumar STOCK (saldo nominal) + SERVICIO (cashflow del
  periodo). F1/F5 dan stock a una fecha de corte; F2 da el cronograma de
  servicios por unidad. El cashflow total en una fecha `d` es:
  `cashflow(d) = Σ_instr  coef(d, instr) × saldo_nominal(instr, as_of)`
  donde `coef` viene de F2 y `saldo_nominal` de F1/F5 al `as_of_date` mas
  cercano anterior. No sumar el saldo al cashflow.
- **Regla 2**: los valores de F2 (`AMORTIZACIÓN A PAGAR`, `INTERÉS A PAGAR`,
  `VALOR DEL CUPÓN`) son **coeficientes por denominacion minima sobre VN
  original** (lo dice el propio archivo). Nunca tratarlos como nominales
  agregados. Siempre multiplicar por `saldo_nominal` circulante.

### 4.2 Canjes y conversiones

- **Regla 3**: un **canje** retira el instrumento viejo y emite el nuevo. En la
  fecha del canje: (a) reducir `saldo_nominal` del viejo, (b) marcar sus cupones
  futuros como `cancelados` (no contarlos como vencimientos pagados), (c)
  agregar `saldo_nominal` del nuevo con sus cupones. Nunca conservar ambos
  nominales pre+post en el mismo bucket de fecha -> eso duplica el stock.
- **Regla 4**: una **conversion** (ej. conversión de `TZX26`/`TTJ26` en una
  licitacion) **no es un vencimiento pagado en efectivo**. Etiquetar
  `operation_type = conversion` y excluirla de los totales de "vencimientos
  pagados en efectivo". Aparece como movimiento de composicion, no como flujo de
  caja.
- **Regla 5**: para que un mismo pago no se cuente dos veces en un bucket de
  fecha (una como vencimiento del viejo y otra como emision del nuevo), usar
  clave unica `(fecha_servicio, instrumento_id, nro_cupon)` y campo
  `operation_type`. Si dos registros colisionan en la misma fecha para el mismo
  tenedor, uno es canje y otro es nuevo -> conservar el nuevo y registrar el
  viejo como cancelado.

### 4.3 Reapertura vs instrumento nuevo

- **Regla 6**: **reapertura** = mismo ISIN + nuevo tramo de emision -> sumar al
  `saldo_nominal` del instrumento existente (no crear fila nueva de
  instrumento). Clave de instrumento = `(isin|especie, fecha_emision_original)`.
- **Regla 7**: **nuevo instrumento** (nuevo ISIN/especie) -> crear fila nueva.
  Distinguir por ISIN/especie, no por descripcion textual (que cambia entre
  archivos).

### 4.4 Moneda y tipo de cambio

- **Regla 8**: nunca sumar ni comparar cashflows en monedas distintas sin FX
  explicito. Mantener el calendario **particionado por moneda**: `$` pesos
  corrientes, `CER` pesos ajustables, `U$S` dolares, `€` euros, `¥` yenes,
  `DL` dolar linked, `PBI` unidades ligadas al PBI. Solo agregar a un total
  unico tras aplicar un `Tipo de Cambio` declarado (F5 publica
  `Tipo de Cambio (excluye deudas ajustables por CER)`).
- **Regla 9**: la deuda ajustable por CER es un bucket aparte: su nominal cambia
  con el coeficiente CER y los cupones del archivo usan el CER de **10 dias
  habiles anteriores** al pago (ver nota `(*)` de F2). No mezclar nominal
  "original" con nominal "actualizado por CER" sin etiquetar.

### 4.5 Intra-sector-publico

- **Regla 10**: el stock F5 incluye `LETRAS ADQUIRIDAS POR EL BCRA` y
  `Letras del Tesoro - Organismos Públicos`. Para reportar deuda con el sector
  **privado/no financiero**, **excluir** las tenencias de BCRA y Organismos
  Publicos; etiquetar `tenedor`. Una misma Letra no debe figurar a la vez como
  deuda del Tesoro y como activo del BCRA en el mismo agregado.
- **Regla 11**: los Prestamos Garantizados (F3/F4) son un bucket **historico y
  separado**; aparecen tambien en F5 como `Préstamos Garantizados`. Para evitar
  doble conteo, casar por **especie** y mantener una sola fuente de verdad por
  especie (preferir F5 para stock, F3 para el coeficiente de pago).

### 4.6 Capitalizacion de intereses

- **Regla 12**: en periodos de `CAPITALIZACIÓN` / `Cupón cero`, el interes se
  suma al nominal y **no se paga en efectivo**. No contar el interes capitalizado
  como `interés pagado` en el calendario de caja; marcar el periodo como
  `capitaliza` y reflejarlo como aumento de `saldo_nominal`.

### 4.7 Versionado y re-baseline

- **Regla 13**: F1 cambia de nombre con cada fecha de corte (`_31-5-26_vf`,
  ...). Cuando aparece una version nueva, **re-baselinear** el
  `saldo_nominal` y **recalcular** los cashflows hacia adelante; **no**
  acumular old+new (sumaria stock de dos fechas distintas).
- **Regla 14**: F2 (`cupones.xlsx`) no versionada -> comparar `raw_hash` cada
  poll. Si cambia, re-leer todas las hojas de instrumento y reemplazar; nunca
  append por fecha.

---

## 5. Limite de alcance vs `tesoro_licitaciones`

| Dimension | `tesoro_licitaciones` (existente) | Conector de cashflows (este task) |
|-----------|-----------------------------------|-----------------------------------|
| Objeto | Llamados + resultados de licitacion | Stock + cronograma de servicios de instrumentos en circulacion |
| Flujo que captura | ** Nuevas colocaciones** (VNO ofertado/adjudicado, precio de corte, TNA/TIREA, prorrateo) | **Vencimientos futuros y corrientes** de capital e intereses de lo ya emitido |
| Fuentes | Noticias `/noticias/`, hub `/economia/licitaciones`, historico, colocaciones | F1 estructura_financiera + F2 cupones + F5 deuda_publica trimestral + OPC (contraste) |
| Riesgo de solape | Una licitacion que **reabre** un instrumento cambia su `saldo_nominal` | El conector de cashflows debe consumir el nuevo saldo desde F1/F5, **no** recalcularlo desde resultados de licitacion |
| Regla de separacion | Resultados de licitacion -> solo al conector de licitaciones | Cambios de stock -> solo al conector de cashflows via F1/F5 |

---

## 6. Verificacion (probes en vivo 2026-06-16)

### 6.1 Marcados VERIFIED (probed)

Paginas HTTP 200 con contenido real (titulo + marcadores):
- P1 estructura-financiera, P2 trimestral, P3 mensual-deuda, P4 datos-mensuales,
  P5 informes-mensuales, P6 deuda-publica, P7 datos, P8 informe-pesos,
  P9/P10/P11 OPC (todas 200).

Archivos (HEAD: HTTP 200 + content-type + content-length + last-modified):
- F1 `estructura_financiera_titulos_publicos_31-5-26_vf.xlsx` (XLSX, 305 KB,
  2026-06-08).
- F2 `cupones.xlsx` (XLSX, 844 KB, 2019-08-08 fecha de archivo; URL estable).
- F3 `coeficientes_de_pago_de_pg_-_desde_enero_de_2019_en_adelante_25.xls`
  (XLS, 886 KB, 2026-05-28).
- F4 `coeficientes_de_pago_de_pg_-_desde_enero_de_2018_hasta_enero_de_2019.xls`
  (XLS, 44 MB, 2019-07-25).
- F5 `deuda_publica_31-03-2025.xlsx` bajado y abierto (XLSX, 1.5 MB, ~30 hojas).

Estructura interna de XLSX inspeccionada por ZIP/XML (sin Python):
- F1: 14 hojas (`INDICE`, `A.1..A.7`, `B`, `C`, `D`, `E`, `PL`, `OL`).
- F2: 116 hojas (Indice + agregadas + una por instrumento/serie/ISIN).
- F5: ~30 hojas (`INDICE`, `A.1.x`, `A.2.x`, `A.3.x`, `A.4.x`).
- Vocabulario de encabezados confirmado por sharedStrings (ver sec. 2).

Enlaces profundos en F5: patron `deuda_publica_<DD-MM-YYYY>[_n].xlsx` verificado
para 2019-Q1 .. 2025-Q3 directamente desde el HTML de P2.

### 6.2 Marcados STALE / NO DISPONIBLE

- `cronograma-2026` (licitaciones): **RECUPERADO** (200 OK con contenido real)
  pero **FUERA DE ALCANCE** para cashflows. Es la pagina que fallo en TASK-8.6;
  re-verificada ahora y vive, pero pertenece al conector `tesoro_licitaciones`.
- `deuda_publica_31-03-2026.xlsx`, `_0`, `30-06-2026.xlsx`: **404** (trimestres
  2026 no publicados; rezago esperado). Tomar el ultimo trimestre disponible y
  etiquetar `as_of_date`.
- `cupones.xlsx`: nombre **no versionado** -> riesgo de actualizacion silenciosa.
  No es 404, pero requiere hash-fingerprinting.

### 6.3 Marcados INFERRED (no reprobadados en vivo)

- Trimestre `31-12-2025` (Q4-2025): patron sugiere que existe pero no fue
  probeado en esta sesion.
- Moneda explicita como columna en F1: se infiere del descriptor/familia; en
  algunos casos no aparece como columna literal.
- Frecuencia "eventual" de F1: deducida del tipo de publicacion, no de un
  calendario confirmado.
- Disponibilidad real de CSV para estos datasets: INFERIDO como **no publicado**
  a partir de la doc de referencia (sec. 5) y de la inspeccion de las paginas
  (no se encontraron enlaces CSV en P1/P2/P3).

### 6.4 Posibles blockers

- **Resolucion de enlaces**: F1 y F5 requieren scrapear la pagina (P1/P2) para
  obtener el href exacto (sufijos cambian). No es bloqueante pero implica un
  paso de crawling HTML ademas de la descarga.
- **`cupones.xlsx` no versionado**: si Mecon actualiza el archivo sin cambiar el
  nombre (como ya pasa), solo un hash detecta el cambio. Bloqueador suave: el
  conector debe implementar fingerprinting desde v1.
- **Coeficientes por denominacion minima**: si el conector asume que los valores
  de cupones son nominales agregados, subestimara/overestimara los cashflows por
  ordenes de magnitud. Es la trampa metodologica mas importante.
- **CER desfasaje 10 dias habiles**: para instrumentos CER el coeficiente del
  archivo no es el corriente sino el previo; el conector debe respetar la nota
  `(*)` o los cashflows CER quedaran mal.
- **XLS legacy (PG)**: openpyxl no lee `.xls`; si se quiere el bucket PG
  historico se necesita `xlrd` o conversion previa. Postergar a v2.

---

## 7. Mapeo a criterios de aceptacion

| AC | Seccion donde se cumple | Estado |
|----|-------------------------|--------|
| #1 Crear `analysis/tesoro_cashflows_schema_validation.md` con fuentes, enlaces finales, formatos y columnas requeridas | Sec. 1 (fuentes + enlaces finales, 1.1-1.4), Sec. 2 (columnas requeridas, 2.1-2.4). Archivo creado en `analysis/tesoro_cashflows_schema_validation.md`. | CUMPLIDO |
| #2 Definir si el primer conector debe leer XLS/XLSX, CSV, PDF o combinacion | Sec. 3 (Formato del primer conector): **XLSX primario unico (openpyxl lazy/read_only)**; XLS legacy solo para PG en v2; CSV no publicado; PDF solo reconciliacion. | CUMPLIDO |
| #3 Identificar reglas para evitar doble conteo entre vencimientos, canjes y conversiones | Sec. 4 (Reglas anti doble conteo): 14 reglas en 7 ejes (stock vs servicio, canjes/conversiones, reapertura, moneda/FX, intra-sector-publico, capitalizacion, versionado). | CUMPLIDO |
