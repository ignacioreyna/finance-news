# Investigación de fuentes BCRA: reservas y variables monetarias

Fecha de relevamiento: 2026-06-14

## Resumen ejecutivo

- El BCRA hoy expone dos superficies programables relevantes para esta tarea:
  - API pública de estadísticas monetarias: `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias`
  - API pública de estadísticas cambiarias: `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/...`
- Para reservas, base monetaria, agregados, tasas y series del Informe Monetario Diario, la mejor entrada es la API monetaria v4 más sus archivos XLSX/XLS/PDF de respaldo.
- Para compras/ventas de divisas no encontré un endpoint diario oficial equivalente a "intervención neta del BCRA". La fuente oficial más cercana y actual es mensual: anexo del mercado de cambios y balance cambiario.
- Para encajes/efectivo mínimo hay datos estadísticos mensuales en la página de reservas/base monetaria y el marco regulatorio vive en comunicaciones/circulares del BCRA; conviene separar datos y norma.
- El sitio oficial ya advierte deprecación de `Principales Variables v3.0` el 2026-02-28; para desarrollo nuevo conviene evitarla y usar `Estadísticas Monetarias v4.0`.

## 1. Fuentes estadísticas y endpoints utilizables

### 1.1 API monetaria principal

Fuente oficial:
- API hub: https://www.bcra.gob.ar/apis-banco-central/
- Manual técnico PDF: https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf

Cobertura relevante:
- reservas internacionales
- base monetaria
- circulación monetaria
- efectivo en entidades financieras
- depósitos en cuenta corriente en pesos en el BCRA
- depósitos
- agregados monetarios
- tasas
- series del Informe Monetario Diario

Endpoints:
- Catálogo/listado de variables:
  - `GET https://api.bcra.gob.ar/estadisticas/v4.0/monetarias`
- Serie histórica por variable:
  - `GET https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{idVariable}`
  - `GET https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{idVariable}?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`
- Metodologías:
  - `GET https://api.bcra.gob.ar/estadisticas/v4.0/metodologia`

Formato:
- JSON

Frecuencia:
- mixta por variable: diaria (`D`), mensual (`M`) y trimestral (`T`/`Q`)

Límites y notas operativas:
- sin autenticación
- control de tráfico por IP, pero el manual no publica umbral numérico
- `limit` por catálogo: default `1000`
- `limit` por serie histórica: default `1000`, máximo `3000`
- `limit` por metodologías: default `250`
- útil para descubrimiento porque devuelve `idVariable`, `categoria`, `tipoSerie`, `periodicidad`, `unidadExpresion`, primera y última fecha informada

Clasificación de ingestión:
- `machine-readable`

### 1.2 Página de datos monetarios diarios

Fuente oficial:
- https://www.bcra.gob.ar/datos-monetarios-diarios/

Artefactos publicados:
- Informe Monetario Diario PDF
- Informe Monetario Diario XLS
- series XLSX
- metodología PDF
- listados API en XLSX

Uso recomendado:
- respaldo humano y validación de la API monetaria
- recuperación rápida cuando cambie algún `idVariable`
- fuente secundaria para series del IMD si una variable no queda clara en la API

Formato:
- PDF, XLS, XLSX

Frecuencia:
- diaria

Clasificación de ingestión:
- `machine-readable` para XLS/XLSX
- `manual` para PDF

### 1.3 Reservas internacionales y base monetaria

Fuente oficial:
- https://www.bcra.gob.ar/reservas-internacionales-y-base-monetaria/

Cobertura:
- series diarias por año
- serie mensual
- regulación de liquidez / efectivo mínimo

Formato:
- archivos descargables por año + serie mensual; el sitio no expone el nombre amigable completo en HTML, pero la navegación es directa desde la página

Frecuencia:
- diaria para reservas/base monetaria
- mensual para series consolidadas y efectivo mínimo

Uso recomendado:
- reconciliación contra API monetaria
- fallback cuando cambie la estructura de la API
- insumo mensual específico para efectivo mínimo

Clasificación de ingestión:
- `machine-readable` para descargas tabulares
- `scraping` solo si hubiera que automatizar la selección del archivo anual desde la UI

### 1.4 Balances y agregados monetarios

Fuente oficial:
- https://www.bcra.gob.ar/balances-y-agregados-monetarios/

Cobertura:
- balance consolidado del sistema financiero
- balance del BCRA con fines analíticos
- balance consolidado de entidades financieras
- agregados monetarios
- billetes y monedas en circulación

Formato:
- descargas tabulares desde la página

Frecuencia:
- mensual

Uso recomendado:
- series estructurales para base, M1, M2, M3 y composición del balance
- mejor conector batch mensual que polling diario

Clasificación de ingestión:
- `machine-readable`

### 1.5 Tasas de interés

Fuente oficial:
- https://www.bcra.gob.ar/tasas-de-interes/

Cobertura:
- TAMAR, BADLAR, TM20
- adelantos en cuenta corriente
- préstamos personales
- BAIBAR
- tasas por obligaciones con el exterior
- CER y tasas de uso judicial

Formato:
- archivos diarios y mensuales descargables

Frecuencia:
- mayormente diaria; algunos cuadros mensuales o trimestrales

Uso recomendado:
- conector diario separado de monetarias, porque cambia la familia de datos y suele alimentar lecturas semanales de liquidez/precio del peso

Clasificación de ingestión:
- `machine-readable`

### 1.6 Estadísticas cambiarias API

Fuentes oficiales:
- API hub: https://www.bcra.gob.ar/apis-banco-central/
- Manual técnico PDF: https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/estadisticascambiarias-v1.pdf

Endpoints:
- maestro de monedas:
  - `GET https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Maestros/Divisas`
- cotizaciones por fecha:
  - `GET https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones`
  - `GET https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones?fecha=YYYY-MM-DD`
- evolución por moneda:
  - `GET https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/{MONEDA}`
  - `GET https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/{MONEDA}?fechadesde=YYYY-MM-DD&fechahasta=YYYY-MM-DD&limit=n&offset=n`

Formato:
- JSON

Frecuencia:
- diaria hábil

Límites y notas operativas:
- sin autenticación
- control de tráfico por IP, sin cuota pública explícita
- `limit` en evolución por moneda: debe ser mayor a `10` y menor a `1000`; default `1000`
- si una fecha no tiene cotización, la API devuelve `fecha: null` o lista vacía según endpoint

Cobertura útil para esta tarea:
- no sirve para reservas ni agregados
- sí sirve para contextualizar tipo de cambio oficial y cruces por moneda

Clasificación de ingestión:
- `machine-readable`

### 1.7 Mercado de cambios y balance cambiario

Fuente oficial:
- https://www.bcra.gob.ar/estadisticas-estandarizadas-sobre-la-evolucion-del-mercado-de-cambios/

Artefactos:
- anexo estadístico del mercado de cambios y balance cambiario (XLSX)
- anexo sectorial CLANAE (XLSX)
- ranking de entidades por volumen operado (XLSX)
- histórico completo del informe

Frecuencia:
- mensual

Cobertura útil:
- compras/ventas del mercado de cambios por rubro y sector
- vínculo con balance cambiario

Límite importante:
- no reemplaza un dato diario de intervención neta del BCRA
- es la mejor fuente oficial actual identificada para compras/ventas agregadas

Clasificación de ingestión:
- `machine-readable`

### 1.8 Calendario oficial de publicación

Fuente oficial:
- https://www.bcra.gob.ar/calendario-de-informes/

Uso:
- control de expectativa y scheduling de conectores
- confirma que el BCRA publica:
  - Informe Monetario Diario: actualización diaria
  - Informe Monetario Mensual: mensual
  - Boletín Estadístico: mensual
  - Evolución del Mercado de Cambios y Balance Cambiario: mensual
  - REM: mensual
  - IPOM: periódico

Clasificación de ingestión:
- `scraping` liviano o `manual`

## 2. Fuentes normativas

### 2.1 Buscador de comunicaciones

Fuente oficial:
- https://www.bcra.gob.ar/buscador-de-comunicaciones/

Qué aporta:
- búsqueda por tipo, número, fecha o circular asociada
- distinción oficial entre comunicaciones `A`, `B`, `C` y comunicados de prensa `P`
- explicación del ordenamiento normativo y actualización por circular

Uso recomendado:
- fuente raíz para trazabilidad normativa
- clave para encajes/efectivo mínimo, regulaciones monetarias, operaciones cambiarias y operatoria de liquidez

Clasificación de ingestión:
- `scraping` o `manual`

### 2.2 Ejemplos normativos directamente vinculados a regulación monetaria

Fuentes oficiales:
- Comunicación A 8060: https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8060.pdf
- Comunicación A 8083: https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8083.pdf
- Comunicación A 8190: https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8190.pdf
- Página de operaciones de regulación monetaria: https://www.bcra.gob.ar/operaciones-pases-subastas-letras/

Cobertura:
- suspensión de pases pasivos y migración operativa a LEFI
- adecuaciones horarias
- liquidación compensada de pases activos

Uso recomendado:
- no como feed de datos primario
- sí como conector normativo/event-driven para detectar cambios de régimen, instrumentos o reglas operativas que alteran la lectura de reservas, encajes o liquidez

Clasificación de ingestión:
- `manual` o `scraping` PDF por evento

### 2.3 Efectivo mínimo / regulación de liquidez

Fuente oficial base:
- https://www.bcra.gob.ar/reservas-internacionales-y-base-monetaria/

Observación:
- la página publica un enlace específico de "Información relacionada con la normativa de regulación de liquidez del BCRA (serie mensual)" para efectivo mínimo.
- No identifiqué en este relevamiento un endpoint JSON dedicado a encajes/efectivo mínimo; la vía oficial visible es descarga tabular desde la página estadística más búsqueda normativa por comunicaciones/circulares.

Conclusión operativa:
- tratar encajes como dataset estadístico mensual más overlay normativo.

## 3. Fuentes de comunicados e informes

### 3.1 Últimos informes y calendario

Fuentes oficiales:
- Últimos informes: https://www.bcra.gob.ar/ultimos-informes/
- Calendario: https://www.bcra.gob.ar/calendario-de-informes/

Uso:
- detección de nuevos PDFs/XLS
- armado de agenda semanal
- contraste entre dato de alta frecuencia y narrativa oficial

Clasificación de ingestión:
- `scraping`

### 3.2 Comunicados de prensa y comunicados normativos

Fuente oficial:
- https://www.bcra.gob.ar/buscador-de-comunicaciones/

Uso:
- seguimiento de comunicados `P` para cambios de política o aclaraciones
- separación explícita frente a normas `A/B/C`

Clasificación de ingestión:
- `scraping` o `manual`

## 4. Mapa por necesidad analítica

| Necesidad | Mejor fuente primaria | Formato | Frecuencia | Modo |
| --- | --- | --- | --- | --- |
| Reservas internacionales diarias | API monetaria v4 + página de reservas | JSON + XLS/XLSX | diaria | machine-readable |
| Base monetaria diaria | API monetaria v4 + página de reservas | JSON + XLS/XLSX | diaria | machine-readable |
| Agregados monetarios M1/M2/M3 | balances y agregados monetarios | XLS/XLSX | mensual | machine-readable |
| Tasas BADLAR/TAMAR/TM20/BAIBAR | tasas de interés | XLS/XLSX | diaria | machine-readable |
| Encajes / efectivo mínimo | reservas y base monetaria + comunicaciones | XLS/XLSX + PDF | mensual + event-driven | mixed |
| Compras/ventas de divisas | mercado de cambios y balance cambiario | XLSX | mensual | machine-readable |
| Tipo de cambio oficial y cruces | API cambiaria v1 | JSON | diaria | machine-readable |
| Cambios de régimen monetario/liquidez | buscador de comunicaciones + operaciones de regulación monetaria | HTML + PDF | eventual | scraping/manual |

## 5. Limitaciones detectadas

1. No encontré un endpoint público oficial diario y explícito para "compras/ventas del BCRA" comparable a la conversación de mercado sobre intervención spot. La salida oficial actual más clara es mensual.
2. La documentación web del API usa un visor no compatible con este navegador, pero el PDF técnico sí es accesible y suficiente para implementar.
3. La familia `Principales Variables` sigue visible en el hub, pero con deprecación anunciada. No conviene diseñar conectores nuevos sobre esa superficie.
4. Para algunas descargas XLS/XLSX el HTML no expone un nombre de archivo estable visible; la automatización puede requerir resolver el link final o usar la API monetaria cuando exista equivalente.

## 6. Propuesta de conectores atómicos posteriores

### Prioridad 1

1. `bcra_monetarias_catalog`
- objetivo: traer y versionar el catálogo de variables desde `estadisticas/v4.0/monetarias`
- salida: tabla de metadatos por `idVariable`
- razón: desbloquea todos los conectores de series sin hardcodear ids

2. `bcra_reservas_base_diarias`
- objetivo: descargar reservas internacionales, base monetaria, circulación monetaria, efectivo en entidades y depósitos en c/c BCRA desde la API monetaria
- salida: snapshot diario normalizado
- razón: cubre el núcleo semanal del host

3. `bcra_tasas_diarias`
- objetivo: ingerir BADLAR, TAMAR, TM20, BAIBAR y tasa de depósitos/préstamos más usadas
- fuente: API monetaria si existe cada serie; fallback página de tasas
- razón: lectura semanal de pesos y liquidez

### Prioridad 2

4. `bcra_agregados_mensuales`
- objetivo: M1, M2, M3 y balances analíticos
- fuente: balances y agregados monetarios
- razón: contexto monetario estructural

5. `bcra_mercado_cambios_mensual`
- objetivo: anexo estadístico del mercado de cambios y balance cambiario
- salida: compras/ventas por rubro/sector y series del balance cambiario
- razón: mejor aproximación oficial para flujos FX

6. `bcra_encajes_mensuales`
- objetivo: serie de efectivo mínimo / regulación de liquidez
- fuente: página de reservas/base monetaria
- razón: detectar compresión o relajación de liquidez bancaria

### Prioridad 3

7. `bcra_normativa_monetaria_watch`
- objetivo: vigilar nuevas comunicaciones `A/B/C` en `REMON`, `LISOL`, `CAMEX` y temas afines
- fuente: buscador de comunicaciones
- razón: cambios de regla que invalidan comparaciones históricas

8. `bcra_comunicados_prensa_watch`
- objetivo: seguir comunicados `P` y nuevos informes del calendario
- razón: capa narrativa y de evento, no core dataset

## 7. Recomendación de implementación

- Diseñar el pipeline principal sobre la API monetaria v4.
- Mantener las páginas de estadísticas como respaldo y como fuente de series que todavía no tengan endpoint claro.
- Tratar compras/ventas del BCRA como problema de dos capas:
  - capa oficial mensual: mercado de cambios y balance cambiario
  - capa interpretativa diaria: no automatizar con fuente no oficial dentro de este task
- Separar siempre:
  - `estadística` = series y anexos
  - `normativa` = comunicaciones/circulares
  - `comunicados` = anuncios y contexto institucional

## URLs citadas

- https://www.bcra.gob.ar/apis-banco-central/
- https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf
- https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/estadisticascambiarias-v1.pdf
- https://api.bcra.gob.ar/estadisticas/v4.0/monetarias
- https://api.bcra.gob.ar/estadisticas/v4.0/metodologia
- https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Maestros/Divisas
- https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones
- https://www.bcra.gob.ar/datos-monetarios-diarios/
- https://www.bcra.gob.ar/reservas-internacionales-y-base-monetaria/
- https://www.bcra.gob.ar/balances-y-agregados-monetarios/
- https://www.bcra.gob.ar/tasas-de-interes/
- https://www.bcra.gob.ar/estadisticas-estandarizadas-sobre-la-evolucion-del-mercado-de-cambios/
- https://www.bcra.gob.ar/calendario-de-informes/
- https://www.bcra.gob.ar/ultimos-informes/
- https://www.bcra.gob.ar/buscador-de-comunicaciones/
- https://www.bcra.gob.ar/operaciones-pases-subastas-letras/
- https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8060.pdf
- https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8083.pdf
- https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8190.pdf
