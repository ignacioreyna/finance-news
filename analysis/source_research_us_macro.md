# Investigacion de fuentes oficiales de EE.UU. para empleo, inflacion y actividad

Fecha de verificacion: 2026-06-14

## Objetivo

Mapear fuentes oficiales accionables para cubrir el bloque macro de EE.UU. que mas mueve la lectura semanal de Fed:

- inflacion: CPI, PPI, PCE;
- empleo: payrolls, desempleo, salarios, JOLTS;
- actividad: PBI, consumo, inversion;
- alta frecuencia complementaria: weekly claims y GDPNow.

La recomendacion operativa es usar:

1. `BLS` como fuente primaria para CPI, PPI, payrolls, unemployment y JOLTS;
2. `BEA` como fuente primaria para PCE, PIB, consumo e inversion;
3. `DOL` y `Atlanta Fed` como complemento oficial de alta frecuencia para claims y nowcast de actividad.

## Resumen ejecutivo

- `BLS` tiene dos vias utiles: `Public Data API v2` y `download.bls.gov/pub/time.series/*`. La API sirve para consumo directo; los text files sirven para metadata y validacion de series IDs.
- `BEA` tiene una API oficial con `UserID` obligatorio. Para macro conviene trabajar sobre `DataSetName=NIPA` y descubrir `TableName`/`Frequency`/`Year` via metadata antes de fijar conectores.
- `DOL` no expone una API moderna equivalente a BLS/BEA para claims, pero si publica la serie oficial semanal en `HTML`, `Spreadsheet` y `XML`.
- Para el tablero Fed semanal, el minimo viable no necesita cubrir todo el universo macro: alcanza con 10-12 indicadores que mezclen frecuencia semanal, mensual y trimestral.

## 1. BLS

### 1.1 Endpoints y formatos

| Recurso | URL oficial | Cobertura | Formato | Frecuencia | API key |
| --- | --- | --- | --- | --- | --- |
| Developer hub | https://www.bls.gov/developers/ | documentacion general | HTML | eventual | no aplica |
| API v2 signatures | https://www.bls.gov/developers/api_signature_v2.htm | requests `GET`/`POST` sobre series | HTML | eventual | opcional/condicional |
| API features / limits | https://www.bls.gov/bls/api_features.htm | limites, notas de version | HTML | eventual | opcional/condicional |
| Base API | https://api.bls.gov/publicAPI/v2/timeseries/data/ | datos historicos por series ID | JSON, XLSX | segun serie | opcional/condicional |
| Text files root | https://download.bls.gov/pub/time.series/ | catalogo por encuesta | directorios y `.txt` | segun serie | no |

### 1.2 Restricciones operativas

- La pagina `Data API` dice que el API es publica y no requiere registro.
- La misma documentacion de `Version 2.0` indica que el registro es requerido para las funciones nuevas y para usar parametros opcionales como `catalog`, `calculations`, `annualaverage` y `aspects`.
- La recomendacion practica es:
  - asumir que consultas simples de series funcionan sin key;
  - tramitar `registrationkey` si se va a usar ventana larga, metadata opcional o lotes grandes;
  - respetar los limites documentados de `50` series por request y `20` anios por request en v2.

### 1.3 Patrón de ingestion recomendado

- Query simple, ultima observacion o historico corto:
  - `GET https://api.bls.gov/publicAPI/v2/timeseries/data/{SERIES_ID}`
  - ejemplo documentado de latest:
    - `https://api.bls.gov/publicAPI/v2/timeseries/data/LAUCN040010000000005?latest=true`
- Query en lote con rango de anios:
  - `POST https://api.bls.gov/publicAPI/v2/timeseries/data/`
  - payload JSON con `seriesid`, `startyear`, `endyear` y opcionalmente `registrationkey`.
- Metadata y QA de series:
  - leer `download.bls.gov/pub/time.series/{survey}/`
  - usar `*.txt`, `*.series`, `*.item`, `*.industry`, `*.period`, etc.

### 1.4 CPI

| Item | Fuente BLS | Encuesta / carpeta | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| CPI headline | API + text files | `cu` | mensual | `CUSR0000SA0` |
| CPI core | API + text files | `cu` | mensual | `CUSR0000SA0L1E` |

URLs utiles:

- CPI survey files: https://download.bls.gov/pub/time.series/cu/
- formato de series CPI: https://download.bls.gov/pub/time.series/cu/cu.txt
- catalogo de series CPI: https://download.bls.gov/pub/time.series/cu/cu.series

Notas:

- `cu.txt` confirma que la carpeta `cu` corresponde a `Consumer Price Index-All Urban Consumers`.
- `cu.series` lista series con `series_id`, `seasonal`, `area_code`, `item_code` y `series_title`.
- Para el tablero semanal basta con headline y core desestacionalizados; despues se puede agregar shelter, servicios ex shelter y bienes.

### 1.5 PPI

| Item | Fuente BLS | Encuesta / carpeta | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| PPI final demand | API + release tables + text files | `pc` para catalogo; release mensual para headline | mensual | headline final demand |
| PPI core operativa | release tables + series mapping | `pc` | mensual | final demand ex alimentos/energia/comercio |

URLs utiles:

- PPI subject page: https://www.bls.gov/ppi/
- PPI survey files: https://download.bls.gov/pub/time.series/pc/
- formato de series PPI: https://download.bls.gov/pub/time.series/pc/pc.txt

Nota importante:

- La automatizacion de `PPI final demand` conviene arrancarla desde la publicacion mensual y luego fijar series ID exactos con metadata BLS.
- En esta investigacion no cierro un `series_id` unico de PPI headline porque la estructura `pc` mezcla niveles de clasificacion y el riesgo de enganchar la serie equivocada es real.
- Supuesto de trabajo razonable: para MVP editorial alcanza con `headline final demand` y una medida `core` de la propia release.

### 1.6 Payrolls y Employment Situation

| Item | Fuente BLS | Encuesta / carpeta | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| Nonfarm payrolls | API + text files | `ce` | mensual | `CES0000000001` |
| Avg hourly earnings total private | API + text files | `ce` | mensual | `CES0500000003` |
| Unemployment rate | API + text files | `ln` | mensual | `LNS14000000` |
| Labor force participation rate | API + text files | `ln` | mensual | `LNS11300000` |

URLs utiles:

- CES survey files: https://download.bls.gov/pub/time.series/ce/
- CES format: https://download.bls.gov/pub/time.series/ce/ce.txt
- CPS/LN survey files: https://download.bls.gov/pub/time.series/ln/
- CPS/LN format: https://download.bls.gov/pub/time.series/ln/ln.txt

Notas:

- `ce.txt` confirma que `ce` es `Current Employment Statistics - CES (National)`, o sea la fuente primaria de payrolls.
- `ln.txt` confirma que `ln` es `Current Population Survey (Household Data)`, fuente primaria de desempleo, participacion y ratio empleo/poblacion.
- Para lectura Fed semanal, el combo minimo es:
  - cambio mensual de payrolls;
  - unemployment rate;
  - average hourly earnings.

### 1.7 JOLTS

| Item | Fuente BLS | Encuesta / carpeta | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| Job openings level | API + text files | `jt` | mensual | `JTS000000000000000JOL` |
| Hires level | API + text files | `jt` | mensual | `JTS000000000000000HIL` |
| Quits rate | API + text files | `jt` | mensual | `JTS000000000000000QUR` |

URLs utiles:

- JOLTS survey files: https://download.bls.gov/pub/time.series/jt/
- JOLTS format: https://download.bls.gov/pub/time.series/jt/jt.txt
- JOLTS catalogo de series: https://download.bls.gov/pub/time.series/jt/jt.series

Notas:

- `jt.txt` confirma la descomposicion del series ID por `state`, `industry`, `size class`, `data element`, `rate/level` y `seasonal`.
- Para tablero Fed semanal no hace falta toda la matriz JOLTS: openings, hires y quits alcanzan para medir enfriamiento o recalentamiento del mercado laboral.

## 2. BEA

### 2.1 Endpoints y formatos

| Recurso | URL oficial | Cobertura | Formato | Frecuencia | API key |
| --- | --- | --- | --- | --- | --- |
| API signup | https://apps.bea.gov/API/signup/ | alta de `UserID` | HTML | eventual | si |
| API docs | https://apps.bea.gov/API/docs/index.htm | guia y PDF oficial | HTML, PDF | eventual | si |
| Base API | https://apps.bea.gov/api/data/ | datasets, metadata y datos | JSON, XML | segun tabla | si |
| GDP page | https://www.bea.gov/data/gdp/gross-domestic-product | pagina editorial PIB | HTML | trimestral | no |
| PCE price index page | https://www.bea.gov/data/personal-consumption-expenditures-price-index | pagina editorial PCE / core PCE | HTML | mensual | no |
| Personal income and outlays | https://www.bea.gov/news/2026/personal-income-and-outlays-april-2026 | release mensual actual | HTML | mensual | no |

### 2.2 Restricciones operativas

- La API de BEA usa `UserID` de 36 caracteres.
- El flujo correcto es:
  1. `GetDataSetList`
  2. `GetParameterValues`
  3. `GetData`
- Para `DataSetName=NIPA`, `TableName`, `Frequency` y `Year` son parametros requeridos.
- `Frequency` acepta `A`, `Q` y `M` segun disponibilidad de la tabla.
- `Year=ALL` existe, pero la propia guia recomienda evitarlo cuando se conocen los anios necesarios porque devuelve mucho volumen.

### 2.3 Patrón de ingestion recomendado

1. Descubrir datasets:
   - `https://apps.bea.gov/api/data?&UserID=YOUR_KEY&method=GETDATASETLIST&ResultFormat=JSON`
2. Descubrir tablas NIPA:
   - `https://apps.bea.gov/api/data/?UserID=YOUR_KEY&method=GetParameterValues&DataSetName=NIPA&ParameterName=TableName`
3. Descubrir frecuencias validas:
   - `https://apps.bea.gov/api/data/?UserID=YOUR_KEY&method=GetParameterValues&DataSetName=NIPA&ParameterName=Frequency`
4. Bajar datos:
   - `https://apps.bea.gov/api/data/?&UserID=YOUR_KEY&method=GetData&DataSetName=NIPA&TableName={TABLE_NAME}&Frequency={M|Q|A}&Year={YYYY,...}`

### 2.4 PCE, ingreso y gasto

| Item | Fuente BEA | Dataset | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| PCE price index headline | API + pagina editorial | `NIPA` | mensual | tabla de PCE price index |
| Core PCE price index | API + pagina editorial | `NIPA` | mensual | tabla de core PCE price index |
| Personal income | API + release mensual | `NIPA` | mensual | tabla de personal income |
| Real personal consumption expenditures | API + release mensual | `NIPA` | mensual | tabla de real PCE |

URLs utiles:

- PCE page: https://www.bea.gov/data/personal-consumption-expenditures-price-index
- Personal income & outlays release: https://www.bea.gov/news/2026/personal-income-and-outlays-april-2026

Notas:

- La guia de API usa como ejemplo `NIPA&TableName=T20600&Frequency=M`, que corresponde a `Personal Income, Monthly`.
- Para automatizar headline/core PCE sin fijar hoy un `TableName` potencialmente viejo, la ruta robusta es resolver `TableName` por metadata `GetParameterValues`.
- Para tablero Fed semanal, el set minimo de BEA mensual es:
  - personal income m/m;
  - personal spending m/m;
  - headline PCE y core PCE m/m e y/y.

### 2.5 PIB, consumo e inversion

| Item | Fuente BEA | Dataset | Frecuencia | Candidato inicial |
| --- | --- | --- | --- | --- |
| Real GDP | API + GDP page | `NIPA` | trimestral | tabla real GDP / percent change |
| PCE dentro del PIB | API | `NIPA` | trimestral | lineas de consumo privado |
| Gross private domestic investment | API | `NIPA` | trimestral | lineas de inversion privada |

URLs utiles:

- GDP page: https://www.bea.gov/data/gdp/gross-domestic-product
- interactive NIPA browser: https://www.bea.gov/itable/national-gdp-and-personal-income

Notas:

- La guia de API usa como ejemplo `NIPA&TableName=T10101&Frequency=A,Q&Year=ALL` para `Percent change in Real Gross Domestic Product`.
- La pagina de GDP publica los siguientes hitos editoriales utiles:
  - `advance`,
  - `second`,
  - `third`.
- Para tablero Fed semanal no hace falta cargar decenas de tablas: alcanza con una tabla de GDP headline y las lineas internas de `PCE` y `gross private domestic investment`.

## 3. Otras fuentes oficiales necesarias

### 3.1 DOL / ETA para weekly claims

| Recurso | URL oficial | Cobertura | Formato | Frecuencia | API key |
| --- | --- | --- | --- | --- | --- |
| Weekly claims page | https://oui.doleta.gov/unemploy/claims.asp | initial y continued claims, nacional y estados | HTML, Spreadsheet, XML | semanal | no |
| Current release PDF | https://www.dol.gov/ui/data.pdf | comunicado semanal | PDF | semanal | no |

Notas:

- Esta es la fuente oficial correcta para claims; no depende de BLS.
- La pagina de ETA permite extraer historico por anio y devuelve `Spreadsheet` o `XML`, suficiente para ingestion automatizable.
- Claims es el mejor termometro semanal del mercado laboral porque llega antes que payrolls y antes que JOLTS.

### 3.2 Atlanta Fed GDPNow

| Recurso | URL oficial | Cobertura | Formato | Frecuencia | API key |
| --- | --- | --- | --- | --- | --- |
| GDPNow page | https://www.atlantafed.org/research-and-data/data/gdpnow | nowcast de PIB real corriente | HTML | 6-7 veces por mes, segun releases | no |

Notas:

- No es una fuente oficial de BEA ni del Board, pero si es una fuente oficial Fed regional y sirve como nowcast de actividad.
- La propia pagina aclara que el modelo se actualiza alrededor de `6 o 7 veces por mes` y que incorpora releases como retail trade, trade, housing starts y personal income and outlays.
- Para el weekly dashboard funciona como puente entre el ultimo GDP BEA publicado y el flujo mensual/trimestral de datos.

## 4. Separacion recomendada por dominio

### BLS

Usar para:

- CPI;
- PPI;
- payrolls;
- unemployment rate;
- average hourly earnings;
- JOLTS.

### BEA

Usar para:

- headline PCE;
- core PCE;
- personal income;
- personal spending;
- GDP headline;
- consumo e inversion dentro del PIB.

### Otras fuentes oficiales necesarias

Usar para:

- `DOL/ETA`: weekly initial claims y continued claims;
- `Atlanta Fed GDPNow`: nowcast de actividad entre publicaciones de BEA.

## 5. Minimo viable para tablero Fed semanal

### 5.1 Indicadores minimos

| Bloque | Indicador | Fuente | Frecuencia |
| --- | --- | --- | --- |
| Inflacion | CPI headline | BLS | mensual |
| Inflacion | CPI core | BLS | mensual |
| Inflacion | PPI final demand | BLS | mensual |
| Inflacion | PCE headline | BEA | mensual |
| Inflacion | Core PCE | BEA | mensual |
| Empleo | Nonfarm payrolls | BLS | mensual |
| Empleo | Unemployment rate | BLS | mensual |
| Empleo | Average hourly earnings | BLS | mensual |
| Empleo | JOLTS job openings | BLS | mensual |
| Empleo | JOLTS quits rate | BLS | mensual |
| Empleo alta frecuencia | Initial claims / continued claims | DOL | semanal |
| Actividad | Real GDP | BEA | trimestral |
| Actividad | Personal income | BEA | mensual |
| Actividad | Real personal spending / PCE | BEA | mensual |
| Actividad nowcast | GDPNow | Atlanta Fed | intra-mensual |

### 5.2 Lectura editorial minima

Cada actualizacion semanal deberia responder cuatro preguntas:

1. La desinflacion sigue viva o se estanco.
2. El mercado laboral se enfria de forma ordenada o abrupta.
3. La actividad aguanta o se deteriora.
4. Eso cambia la funcion de reaccion de la Fed o solo el timing.

### 5.3 Prioridad de implementacion

#### Fase 1

- BLS API para `CPI`, `payrolls`, `unemployment`, `AHE`, `JOLTS`.
- DOL claims desde `Spreadsheet` o `XML`.
- BEA API para `PCE`, `core PCE`, `personal income`, `personal spending`, `GDP`.

#### Fase 2

- PPI con series ID exactos y/o release table robusta.
- GDP line-item detail para `consumo` e `inversion`.
- GDPNow como serie de nowcast complementaria.

## 6. Riesgos y supuestos

- `BLS API`: la documentacion de registro no es completamente consistente. Supuesto razonable: operar con v2 y provisionar `registrationkey` desde el inicio para evitar sorpresas.
- `PPI`: el headline exacto requiere cerrar series mapping con metadata BLS antes de automatizarlo como conector definitivo.
- `BEA`: los `TableName` historicos existen, pero la via mas robusta es descubrirlos por metadata en tiempo de implementacion en vez de hardcodearlos todos desde este memo.

## 7. Recomendacion final

El tablero Fed semanal deberia arrancar con este nucleo:

- `CPI headline/core`
- `PCE headline/core`
- `payrolls`
- `unemployment rate`
- `average hourly earnings`
- `JOLTS openings/quits`
- `initial claims`
- `real GDP`
- `personal income / personal spending`
- `GDPNow`

Con eso ya se cubren, con fuentes oficiales, las tres patas que importan para la lectura Fed: inflacion, empleo y actividad.

## 8. Fuentes oficiales verificadas

- BLS Data API: https://www.bls.gov/bls/api_features.htm
- BLS API signatures v2: https://www.bls.gov/developers/api_signature_v2.htm
- BLS text files root: https://download.bls.gov/pub/time.series/
- BLS CPI files: https://download.bls.gov/pub/time.series/cu/
- BLS CES files: https://download.bls.gov/pub/time.series/ce/
- BLS CPS household files: https://download.bls.gov/pub/time.series/ln/
- BLS JOLTS files: https://download.bls.gov/pub/time.series/jt/
- BLS PPI files: https://download.bls.gov/pub/time.series/pc/
- BEA API signup: https://apps.bea.gov/API/signup/
- BEA API docs: https://apps.bea.gov/API/docs/index.htm
- BEA API data endpoint: https://apps.bea.gov/api/data/
- BEA GDP page: https://www.bea.gov/data/gdp/gross-domestic-product
- BEA PCE page: https://www.bea.gov/data/personal-consumption-expenditures-price-index
- BEA interactive NIPA tables: https://www.bea.gov/itable/national-gdp-and-personal-income
- DOL weekly claims: https://oui.doleta.gov/unemploy/claims.asp
- DOL current weekly claims release: https://www.dol.gov/ui/data.pdf
- Atlanta Fed GDPNow: https://www.atlantafed.org/research-and-data/data/gdpnow
