# Investigacion de fuentes Treasury y liquidez USD

Fecha de verificacion: 2026-06-14

## Objetivo

Mapear fuentes accionables para seguir issuance/refunding del Tesoro de EE.UU., TGA, SOMA, repo/SOFR, QT/QE y liquidez USD. La prioridad operativa es usar datos primarios de U.S. Treasury, Federal Reserve y New York Fed; FRED queda como agregador/proxy para simplificar series historicas, no como fuente original.

## Resumen ejecutivo

- `U.S. Treasury / FiscalData` es la fuente primaria para Daily Treasury Statement, TGA diaria y flujos de caja del Tesoro.
- `U.S. Treasury / TreasuryDirect` es la fuente primaria para anuncios, resultados y calendario de subastas.
- `home.treasury.gov` es la fuente primaria documental para Quarterly Refunding, borrowing estimates y comunicacion de estrategia de financiamiento.
- `Federal Reserve H.4.1` es la fuente primaria semanal para balance Fed, reservas bancarias, TGA en balance Fed, ON RRP y ritmo agregado de QT/QE.
- `New York Fed` es fuente primaria para SOMA holdings, open market operations, repo/reverse repo, SOFR y otras reference rates.
- `FRED` puede usarse como proxy/agregador para series Fed/Treasury ya normalizadas, siempre guardando la fuente original y marcando `source_type=proxy`.

## 1. Treasury

### 1.1 Daily Treasury Statement, TGA y flujos de caja

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| FiscalData - Daily Treasury Statement | https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/ | DTS completo: operating cash, deposits, withdrawals, debt transactions | diaria, dias habiles federales | web, CSV, JSON API | primaria | punto de entrada oficial para caja diaria |
| FiscalData API - Operating Cash Balance | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance | `record_date`, `account_type`, `close_today_bal`, `open_today_bal`; incluye `Federal Reserve Account` | diaria | JSON | primaria, verificada | TGA diaria operativa; filtrar `account_type=Federal Reserve Account` |
| FiscalData API - Deposits and Withdrawals of Operating Cash | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash | `transaction_type`, `transaction_catg`, `transaction_today_amt`, MTD, FYTD | diaria | JSON | primaria, verificada | explicar por que sube/baja TGA: impuestos, gasto, redenciones, emisiones |

Campos minimos:

- `record_date`
- `account_type`
- `close_today_bal`
- `transaction_type`
- `transaction_catg`
- `transaction_today_amt`

Regla de lectura:

- suba de TGA drena reservas si no se compensa por ON RRP u otros pasivos Fed;
- baja de TGA inyecta liquidez al sistema bancario;
- mirar flujo neto diario y acumulado semanal, no solo nivel.

### 1.2 Issuance, auctions y refunding

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| Treasury Quarterly Refunding | https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding | refunding statement, presentation, financing estimates, borrowing needs | trimestral, con updates intra-trimestre si aplica | HTML, PDF | primaria documental | estrategia de financiamiento, guidance de cupones/bills, impacto esperado en liquidez |
| Treasury buybacks | https://home.treasury.gov/policy-issues/financing-the-government/treasury-buybacks | calendario, resultados y comunicacion de buybacks | segun calendario | HTML, CSV/PDF segun recurso | primaria | liquidez de mercado UST y composicion de duration |
| TreasuryDirect Web API - announced securities | https://www.treasurydirect.gov/TA_WS/securities/announced?format=json | subastas anunciadas: tipo, CUSIP, auction date, issue date, maturity, offering amount | por anuncio | JSON | primaria, pendiente de revalidar en implementacion | calendario operativo de issuance |
| TreasuryDirect Web API - auctioned securities | https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json | resultados de subastas ya realizadas | por subasta | JSON | primaria, pendiente de revalidar en implementacion | tails, bid-to-cover, awards, tasas |
| TreasuryDirect API docs | https://www.treasurydirect.gov/webapis/webapisecurities.htm | documentacion de endpoints de securities | eventual | HTML | primaria documental | discovery y contrato de ingestion |

Nota operativa:

- En esta pasada el endpoint TreasuryDirect con `?format=json` no se pudo verificar por expansion de `zsh` en el comando local; tratarlo como oficial pero revalidar con URL quoted o cliente HTTP en el conector.
- El endpoint FiscalData `accounting/od/auction_query` devolvio 404 y no debe usarse hasta encontrar dataset correcto.
- Para refunding, no alcanza con datos de subasta: guardar tambien el texto del `Quarterly Refunding Statement`, porque ahi aparece el cambio de estrategia que mueve term premium.

### 1.3 Debt outstanding y composicion

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| FiscalData - Monthly Statement of the Public Debt | https://fiscaldata.treasury.gov/datasets/monthly-statement-public-debt/ | outstanding por tipo de security, vencimientos y deuda total | mensual | web, CSV, JSON API | primaria | composicion de stock, vencimientos y duration aproximada |
| FiscalData - Debt to the Penny | https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/ | deuda publica total diaria | diaria | web, CSV, JSON API | primaria | contexto de stock, no sustituye issuance por instrumento |

## 2. New York Fed

### 2.1 SOFR y repo/reference rates

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| NY Fed SOFR page | https://www.newyorkfed.org/markets/reference-rates/sofr | SOFR, percentiles, volumen, metodologia | diaria | HTML, CSV/API links | primaria | costo de fondeo secured overnight |
| NY Fed Markets API - SOFR last | https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json | `effectiveDate`, `percentRate`, percentiles 1/25/75/99, `volumeInBillions` | diaria | JSON | primaria, verificada | ingestion directa de ultima observacion |
| NY Fed Markets API docs | https://markets.newyorkfed.org/read?productCode=50&eventCodes=500&limit=25&startPosition=0 | discovery de rates y operaciones | diaria | JSON/HTML | primaria documental | ajustar queries historicas |

Campos minimos:

- `effectiveDate`
- `percentRate`
- `volumeInBillions`
- percentiles 1, 25, 75 y 99

Uso editorial:

- SOFR estable con volumen normal implica funding ordenado;
- salto de SOFR vs IORB/rango Fed Funds o percentiles altos tensionados implica stress de repo;
- siempre cruzar con Treasury settlements, TGA, reservas y ON RRP.

### 2.2 Repo, reverse repo y Standing Repo Facility

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| NY Fed Reverse Repo Operations | https://www.newyorkfed.org/markets/desk-operations/reverse-repo | resultados ON RRP, tasa, monto aceptado, contrapartes | diaria | HTML, archivos historicos/API segun pagina | primaria | drenaje de liquidez no bancaria y piso de tasas |
| NY Fed Repo Operations | https://www.newyorkfed.org/markets/desk-operations/repo | repo operations y Standing Repo Facility | diaria/eventual | HTML, archivos historicos/API segun pagina | primaria | stress de colateral/funding, backstop de liquidez |
| NY Fed Open Market Operations | https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation | marco operativo del Desk | eventual | HTML | primaria documental | interpretar herramientas y cambios de regimen |

Series clave:

- ON RRP amount accepted;
- ON RRP rate;
- number of counterparties, si disponible;
- repo/SRF submitted y accepted amounts;
- spread SOFR - IORB;
- spread SOFR - upper/lower bound del target range.

### 2.3 SOMA y QT/QE operativo

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| NY Fed SOMA Holdings | https://www.newyorkfed.org/markets/soma-holdings | holdings SOMA por Treasury, MBS, agency debt; composicion y vencimientos | regular | HTML, CSV/descargas segun recurso | primaria | ver QT por instrumento y maturity profile |
| NY Fed Treasury Securities Operations | https://www.newyorkfed.org/markets/treasury-securities/treasury-securities-operational-details | compras/ventas/reinversiones de Treasuries | por operacion | HTML, CSV/descargas segun recurso | primaria | QE/QT operativo y reinversion |
| NY Fed Agency MBS Operations | https://www.newyorkfed.org/markets/ambs/agency-mbs-operational-details | compras/ventas/reinversiones MBS | por operacion | HTML, CSV/descargas segun recurso | primaria | componente MBS de QT/QE |

Regla de lectura:

- H.4.1 da el agregado semanal del balance;
- SOMA da la composicion fina y vencimientos;
- operations pages explican el flujo operativo entre dos snapshots.

## 3. Federal Reserve Board

| Fuente | URL / endpoint | Datos | Frecuencia | Formato | Tipo | Uso |
| --- | --- | --- | --- | --- | --- | --- |
| H.4.1 Factors Affecting Reserve Balances | https://www.federalreserve.gov/releases/h41/ | balance Fed, assets, liabilities, reserve balances, ON RRP, TGA, securities held outright | semanal, jueves 4:30 p.m. ET salvo feriados | HTML, PDF, Data Download, RSS | primaria | base semanal de liquidez USD |
| H.4.1 Data Download | https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H41 | series descargables H.4.1 | semanal | CSV/XML | primaria | conector estructurado sin scraping HTML |
| Recent balance sheet trends | https://www.federalreserve.gov/monetarypolicy/bst_recenttrends.htm | visual oficial de balance y drivers | semanal | HTML | primaria explicativa | QA y resumen, no fuente numerica principal |
| FOMC calendars | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | statement, implementation note, minutes, SEP | por reunion | HTML/PDF | primaria documental | cambios de caps QT/QE, reinversion e implementacion |

Series/variables minimas:

- total assets;
- securities held outright;
- U.S. Treasury securities held outright;
- agency MBS held outright;
- reserve balances with Federal Reserve Banks;
- U.S. Treasury General Account;
- overnight reverse repurchase agreements;
- central bank liquidity swaps;
- discount window / loans si reaparecen.

## 4. FRED y otros agregadores/proxies

FRED es util por estabilidad historica, transformaciones y series IDs, pero no reemplaza fuentes primarias. En el pipeline debe marcarse como `proxy` o `aggregator`.

| Agregador | URL / serie | Fuente original | Frecuencia | Tipo | Uso |
| --- | --- | --- | --- | --- | --- |
| FRED `WALCL` | https://fred.stlouisfed.org/series/WALCL | Federal Reserve H.4.1 | semanal | proxy/agregador | total assets Fed |
| FRED `WRESBAL` | https://fred.stlouisfed.org/series/WRESBAL | Federal Reserve H.4.1 | semanal | proxy/agregador | reservas bancarias |
| FRED `WTREGEN` | https://fred.stlouisfed.org/series/WTREGEN | Federal Reserve H.4.1 | semanal | proxy/agregador | TGA semanal en balance Fed |
| FRED `RRPONTSYD` | https://fred.stlouisfed.org/series/RRPONTSYD | New York Fed / H.4.1 | diaria | proxy/agregador | ON RRP amount |
| FRED `SOFR` | https://fred.stlouisfed.org/series/SOFR | New York Fed | diaria | proxy/agregador | SOFR historico simple |
| FRED `DGS2`, `DGS10`, `DGS30` | https://fred.stlouisfed.org/series/DGS10 | Treasury market rates | diaria | proxy/agregador | curva UST para condiciones financieras |

Uso permitido:

- backfill rapido y QA de series;
- charts historicos;
- fallback si el endpoint primario cambia.

Uso no permitido:

- presentar FRED como fuente original;
- mezclar frecuencia diaria FRED con H.4.1 semanal sin marcar frecuencia;
- inferir composicion de issuance desde FRED.

## 5. Conectores sugeridos

### Prioridad alta

1. `treasury_dts_tga_connector`
   - Fuente: FiscalData `operating_cash_balance`.
   - Output: TGA diaria, cambio diario, cambio semanal, tipo de cuenta.
   - Tipo: primario.

2. `treasury_dts_cashflows_connector`
   - Fuente: FiscalData `deposits_withdrawals_operating_cash`.
   - Output: deposits/withdrawals por categoria, flujos de deuda publica, impuestos y gasto.
   - Tipo: primario.

3. `treasury_auction_calendar_connector`
   - Fuente: TreasuryDirect announced/auctioned securities API y Treasury refunding pages.
   - Output: auction date, settlement, maturity, CUSIP, amount, result metrics.
   - Tipo: primario.

4. `fed_h41_liquidity_connector`
   - Fuente: Federal Reserve H.4.1 Data Download.
   - Output: reservas, TGA, ON RRP, securities held outright, total assets.
   - Tipo: primario.

5. `nyfed_sofr_connector`
   - Fuente: NY Fed Markets API SOFR.
   - Output: SOFR, volumen y percentiles.
   - Tipo: primario.

### Prioridad media

6. `nyfed_repo_rrp_connector`
   - Fuente: NY Fed repo/reverse repo operations.
   - Output: monto aceptado, tasa, participantes si disponible.
   - Tipo: primario.

7. `nyfed_soma_connector`
   - Fuente: NY Fed SOMA holdings.
   - Output: holdings por instrumento, maturity buckets, cambios semanales/mensuales.
   - Tipo: primario.

8. `treasury_refunding_connector`
   - Fuente: Quarterly Refunding statement/presentation/financing estimates.
   - Output: borrowing estimates, cambios de cupones/bills, guidance cualitativo.
   - Tipo: primario documental.

### Prioridad baja / fallback

9. `fred_liquidity_proxy_connector`
   - Fuente: FRED series IDs.
   - Output: WALCL, WRESBAL, WTREGEN, RRPONTSYD, SOFR, DGS10.
   - Tipo: proxy/agregador.

## 6. Salida minima para el reporte semanal

Para cada semana:

- cambio de TGA diaria y semanal;
- cambio de reservas bancarias;
- cambio de ON RRP;
- settlement neto esperado de Treasury issuance/redemptions;
- SOFR, volumen y spread vs IORB;
- total assets Fed y securities held outright;
- novedad de refunding o cambio de guidance Treasury;
- SOMA/QT: runoff esperado vs observado si hay dato disponible;
- precio de confirmacion: UST 2y/10y/30y, curva, DXY, VIX, spreads EM.

## 7. Primario vs proxy

| Dominio | Primario | Proxy/agregador |
| --- | --- | --- |
| TGA diaria | FiscalData Daily Treasury Statement | FRED `WTREGEN` solo como TGA semanal H.4.1 |
| Treasury cashflows | FiscalData DTS deposits/withdrawals | ninguno recomendado |
| Issuance/subastas | TreasuryDirect API, home.treasury.gov refunding | calendarios privados/Bloomberg si se agregan despues |
| Balance Fed/QT | Federal Reserve H.4.1, NY Fed SOMA | FRED `WALCL`, `WRESBAL` |
| ON RRP/repo | NY Fed Desk operations | FRED `RRPONTSYD` |
| SOFR | NY Fed reference rates API | FRED `SOFR` |
| Curva UST | Treasury market data / mercado | FRED `DGS*` como historico simple |

## 8. Riesgos y supuestos

- TreasuryDirect API debe revalidarse con cliente HTTP quoted porque la prueba local fallo por expansion de `?` en `zsh`.
- Los recursos de NY Fed cambian entre paginas HTML, CSV y JSON; el conector debe empezar por discovery/documentacion oficial y guardar URL exacta por observacion.
- H.4.1 y FiscalData miden TGA con frecuencias distintas; no comparar nivel diario vs semanal sin alinear fecha.
- La lectura de liquidez debe separar tres canales: balance Fed/QT, pasivos Fed (TGA/ON RRP/reservas) y issuance/settlements del Tesoro.
