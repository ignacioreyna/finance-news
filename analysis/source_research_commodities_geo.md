# Investigacion de fuentes commodities y geoeconomia

Fecha de verificacion: 2026-06-14

## Objetivo

Mapear fuentes accionables para seguir Brent/WTI, oro, DXY, breakevens, energia, OPEP y eventos geoeconomicos relevantes al reporte semanal. La regla editorial es separar:

1. precios de mercado;
2. datos oficiales de energia;
3. tracking de eventos geoeconomicos.

Prioridad: fuentes oficiales y gratuitas. Cuando no hay fuente oficial gratuita y usable para mercado, usar proxies gratuitos marcados como `proxy`.

## Resumen ejecutivo

- Para WTI y Brent spot, la mejor fuente gratuita es EIA/FRED: EIA es fuente original; FRED da CSV simple y estable para `DCOILWTICO` y `DCOILBRENTEU`.
- Para oro, LBMA es benchmark oficial pero el historico tabulado requiere portal/licencia segun uso. Para un MVP gratis conviene usar CME Gold futures como pagina oficial de mercado o Stooq/Yahoo como proxy de precio spot/futuros.
- Para DXY, ICE es el benchmark propietario. Para serie gratis, usar Stooq `DX.F` como proxy de DXY/futuro y complementar con el indice broad dollar oficial de la Fed/FRED `DTWEXBGS`.
- Para breakevens, FRED es suficientemente operativo: `T5YIE`, `T10YIE`, `T5YIFR` y tasas reales TIPS (`DFII5`, `DFII10`) con frecuencia diaria.
- Para energia fisica, el nucleo semanal debe ser EIA Weekly Petroleum Status Report; el nucleo mensual, EIA STEO y OPEC MOMR. IEA Oil Market Report sirve como contraste, pero el contenido completo es pago; usar solo pagina/resumen publico si aplica.
- Para geoeconomia, no automatizar titulares genericos. Incluir solo eventos con canal macro verificable: energia/transporte, aranceles, sanciones, export controls, chips/tierras raras, guerra, nuclear, puertos/chokepoints.

## 1. Precios de mercado

### 1.1 Brent y WTI

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| EIA spot prices browser | https://www.eia.gov/opendata/browser/petroleum/pri/spt | diaria | HTML/API | primaria | fuente original para spot WTI Cushing y Brent Europe | API puede requerir key gratuita; discovery por browser puede cambiar |
| EIA API v2 WTI | `https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RWTC&sort[0][column]=period&sort[0][direction]=desc&length=30` | diaria | JSON | primaria | ultimo WTI spot y ventana corta | validar key/rate limit al implementar |
| EIA API v2 Brent | `https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&length=30` | diaria | JSON | primaria | ultimo Brent spot y ventana corta | validar key/rate limit al implementar |
| FRED WTI `DCOILWTICO` | https://fred.stlouisfed.org/series/DCOILWTICO / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO | diaria | HTML/CSV | proxy/agregador de EIA | ingestion simple sin API key | retraso y revisiones EIA; no es intradia |
| FRED Brent `DCOILBRENTEU` | https://fred.stlouisfed.org/series/DCOILBRENTEU / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU | diaria | HTML/CSV | proxy/agregador de EIA | ingestion simple sin API key | retraso y revisiones EIA; no es intradia |
| CME WTI futures | https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html | intradia/delayed | HTML | mercado oficial | confirmacion de precio futuro front-month | historico estructurado suele ser pago; usar solo quote/check manual o conector HTML fragil |
| CME Brent futures | https://www.cmegroup.com/markets/energy/crude-oil/brent-crude-oil.html | intradia/delayed | HTML | mercado oficial/proxy de Brent futures | confirmacion de curva/futuro Brent | ICE Brent es benchmark central; CME Brent es proxy financiero |
| Stooq WTI/Brent proxies | WTI futures: https://stooq.com/q/d/l/?s=cl.f&i=d ; Brent futures: https://stooq.com/q/d/l/?s=br.f&i=d | diaria | CSV | proxy mercado | fallback gratis para variacion semanal | simbolos y continuidad de contrato deben validarse; no fuente oficial |

Variables minimas:

- `WTI spot` ultimo y variacion semanal;
- `Brent spot` ultimo y variacion semanal;
- `Brent-WTI spread`;
- si hay shock, mirar futures front-month y pendiente 1m/6m con CME/Stooq como proxy.

### 1.2 Oro

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| LBMA precious metal prices | https://www.lbma.org.uk/prices-and-data/precious-metal-prices | dos fixes diarios para oro | HTML/portal | benchmark oficial | referencia institucional del precio LBMA Gold AM/PM | historico tabulado movido a MyLBMA Portal; licencias segun uso comercial/no educativo |
| CME Gold futures | https://www.cmegroup.com/markets/metals/precious/gold.html | intradia/delayed | HTML | mercado oficial | precio de confirmacion para refugio/tasas reales | historico estructurado Datamine suele ser pago; conector HTML no ideal |
| Stooq XAUUSD proxy | https://stooq.com/q/d/l/?s=xauusd&i=d | diaria | CSV | proxy mercado | MVP gratis de oro spot | no es benchmark oficial; validar cambios de simbolo |
| Stooq Gold futures proxy | https://stooq.com/q/d/l/?s=gc.f&i=d | diaria | CSV | proxy mercado | variacion semanal de futuros | continuidad de contrato puede generar saltos |
| Yahoo Finance GC=F | https://finance.yahoo.com/quote/GC=F | diaria/intradia delayed | HTML/CSV no oficial | proxy mercado | fallback visual/manual | descarga historica puede romper por cookies/crumb; no usar como fuente unica automatica |

Lectura editorial:

- Oro subiendo junto con tasas reales cayendo puede ser lectura monetaria.
- Oro subiendo junto con DXY fuerte y tasas reales estables/subiendo suele ser stress/geopolitica.
- No usar oro solo como prueba de conflicto; exigir confirmacion en DXY, UST, VIX, Brent o noticias oficiales.

### 1.3 DXY y dolar global

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| ICE U.S. Dollar Index futures | https://www.ice.com/products/194/US-Dollar-Index-Futures | intradia/delayed | HTML | mercado oficial/benchmark | referencia conceptual de DXY | datos historicos/licencias propietarios; no asumir API gratis |
| Stooq DXY futures proxy | https://stooq.com/q/d/l/?s=dx.f&i=d | diaria | CSV | proxy mercado | MVP semanal de DXY | proxy, no fuente oficial; revisar continuidad |
| Fed/FRED broad dollar `DTWEXBGS` | https://fred.stlouisfed.org/series/DTWEXBGS / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS | diaria | HTML/CSV | oficial/proxy macro | dolar amplio ponderado por comercio | no es DXY; menor sensibilidad a EUR que DXY |
| Fed H.10 release | https://www.federalreserve.gov/releases/h10/ | diaria/semanal segun serie | HTML/data download | oficial | FX oficiales y trade-weighted dollar indexes | usar para marco oficial, no para DXY propietario |

Regla:

- Para "DXY" en reporte, etiquetar como `DXY proxy` si se usa Stooq.
- Para lectura macro de dolar, preferir `DTWEXBGS` porque es oficial y broad.
- Si ambos divergen, explicitar composicion: DXY es canasta vieja con mucho EUR; broad dollar captura mas comercio global.

### 1.4 Breakevens y tasas reales

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| FRED 5y breakeven `T5YIE` | https://fred.stlouisfed.org/series/T5YIE / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=T5YIE | diaria | HTML/CSV | oficial/proxy Fed St. Louis | expectativas inflacion 5y | derivado de Treasury/TIPS; no es encuesta |
| FRED 10y breakeven `T10YIE` | https://fred.stlouisfed.org/series/T10YIE / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE | diaria | HTML/CSV | oficial/proxy Fed St. Louis | expectativas inflacion 10y | incorpora prima de liquidez/riesgo TIPS |
| FRED 5y5y forward `T5YIFR` | https://fred.stlouisfed.org/series/T5YIFR / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=T5YIFR | diaria | HTML/CSV | oficial/proxy Fed St. Louis | ancla inflacionaria forward | derivado; puede moverse por primas |
| FRED real 5y `DFII5` | https://fred.stlouisfed.org/series/DFII5 / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII5 | diaria | HTML/CSV | oficial/proxy Fed St. Louis | tasas reales TIPS | no mezclar con nominales sin fecha alineada |
| FRED real 10y `DFII10` | https://fred.stlouisfed.org/series/DFII10 / CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10 | diaria | HTML/CSV | oficial/proxy Fed St. Louis | tasas reales 10y | idem |

Uso minimo:

- `T10YIE` y `DFII10` para separar shock de inflacion esperada vs tasa real.
- Si sube Brent y suben breakevens, canal inflacion energia.
- Si sube oro pero tambien suben reales, mirar geopolitica o compras oficiales, no solo Fed.

## 2. Datos oficiales de energia

### 2.1 EIA semanal y mensual

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| Weekly Petroleum Status Report | https://www.eia.gov/petroleum/supply/weekly/ | semanal, normalmente miercoles 10:30 ET | HTML, PDF, CSV, XLS | primaria oficial | inventarios, produccion, import/export, demanda implicita, Cushing | datos semanales son estimaciones; feriados mueven release |
| WPSR Table 1/9 balance | desde links CSV/XLS en la pagina WPSR | semanal | CSV/XLS | primaria oficial | balance petrolero rapido | URLs de tablas pueden cambiar; hacer discovery desde pagina |
| EIA Short-Term Energy Outlook | https://www.eia.gov/outlooks/steo/ | mensual | HTML, PDF, tables, data browser | primaria oficial | forecast de Brent, WTI, produccion, consumo, inventarios, LNG | forecast dependiente de supuestos; comparar con precio de mercado |
| STEO data browser | https://www.eia.gov/outlooks/steo/data/browser/ | mensual | browser/API/CSV segun tabla | primaria oficial | series historicas y forecast descargables | validar codigos de series al implementar |
| EIA International data | https://www.eia.gov/international/data/world | mensual/anual segun serie | HTML/API | primaria oficial | produccion/consumo/importaciones por pais | rezagos mayores que WPSR |
| EIA energy disruptions | https://www.eia.gov/special/disruptions/ | eventual | HTML/maps | primaria oficial | huracanes, infraestructura, outages | cobertura centrada en EE.UU. |
| EIA World Oil Transit Chokepoints | https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints | estructural/eventual | HTML | primaria oficial | contexto de Hormuz, Suez, Bab el-Mandeb, etc. | no es tracker diario de flujos |

Variables minimas WPSR:

- crude oil commercial stocks;
- Cushing stocks;
- gasoline stocks;
- distillate stocks;
- refinery utilization;
- U.S. crude production;
- crude imports/exports y net imports;
- product supplied total/gasoline/distillates;
- SPR si hay liberaciones o compras.

### 2.2 OPEC/OPEC+

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| OPEC homepage / research links | https://www.opec.org/ | mensual/eventual | HTML/PDF | primaria cartel | discovery de MOMR, ORB, comunicados | sitio redirige URLs antiguas; discovery puede requerir parsing |
| Monthly Oil Market Report | https://www.opec.org/opec_web/en/publications/338.htm | mensual | PDF/HTML segun sitio | primaria cartel | oferta/demanda global, produccion OPEC, revisions | puede redirigir; tratar la URL final y PDF como fuente por edicion |
| OPEC press releases | https://www.opec.org/opec_web/en/press_room/28.htm | eventual | HTML | primaria cartel | decisiones OPEC+, JMMC, cuotas/voluntary cuts | lenguaje politico; contrastar con produccion observada y precio |
| OPEC Reference Basket | https://www.opec.org/opec_web/en/data_graphs/40.htm | diaria/semanal | HTML | primaria cartel | precio ORB | no reemplaza Brent/WTI para mercado global |

Lectura:

- Separar decision anunciada, cumplimiento observado y reaccion de precio.
- Si OPEC+ anuncia recorte/aumento, chequear si cambia balances EIA/STEO y si Brent confirma.
- El "voluntary cut" tiene riesgo de compliance; no tratar como barriles efectivos hasta ver produccion/exportaciones.

### 2.3 IEA

| Fuente | URL / endpoint | Frecuencia | Formato | Tipo | Uso | Limitaciones |
| --- | --- | --- | --- | --- | --- | --- |
| IEA Oil Market Report | https://www.iea.org/reports/oil-market-report | mensual | HTML/resumen; full report usualmente suscripcion | organismo internacional | contraste de demanda/oferta global contra EIA/OPEC | no depender del full report si requiere pago |
| IEA reports search | https://www.iea.org/reports | eventual/mensual | HTML/PDF segun reporte | organismo internacional | energia, gas, clean energy, security | cobertura amplia; filtrar por impacto macro |

Uso recomendado:

- Usar IEA como tercera mirada cuando EIA y OPEC divergen en demanda/oferta.
- No incluir datos IEA pagos en el pipeline MVP.
- Guardar solo resumen publico y URL, salvo que exista acceso licenciado.

## 3. Tracking de eventos geoeconomicos

### 3.1 Energia, seguridad y chokepoints

| Fuente | URL | Frecuencia | Formato | Tipo | Canal macro |
| --- | --- | --- | --- | --- | --- |
| EIA disruptions | https://www.eia.gov/special/disruptions/ | eventual | HTML/maps | oficial | oferta energia, infraestructura, huracanes |
| EIA chokepoints | https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints | estructural/eventual | HTML | oficial | Hormuz, Suez, Bab el-Mandeb, Turkish Straits |
| IAEA press releases | https://www.iaea.org/newscenter/pressreleases | eventual | HTML | organismo internacional | nuclear Iran/Ucrania, riesgo de escalada |
| IAEA Iran topic | https://www.iaea.org/topics/iran | eventual | HTML | organismo internacional | monitoreo y verificacion nuclear |
| IMF PortWatch | https://portwatch.imf.org/ | diaria/alta frecuencia | web/API segun disponibilidad | organismo/proxy de flujos | puertos, comercio maritimo, disrupciones logisticas |

### 3.2 Aranceles, sanciones y export controls

| Fuente | URL | Frecuencia | Formato | Tipo | Canal macro |
| --- | --- | --- | --- | --- | --- |
| USTR press releases | https://ustr.gov/about-us/policy-offices/press-office/press-releases | eventual | HTML | oficial | aranceles, Section 301, acuerdos comerciales |
| USTR Federal Register | https://www.federalregister.gov/agencies/office-of-the-united-states-trade-representative | eventual | HTML/API | oficial/legal | texto normativo de acciones comerciales |
| White House presidential actions | https://www.whitehouse.gov/presidential-actions/ | eventual | HTML | oficial | executive orders, proclamations, tariff actions |
| Treasury OFAC recent actions | https://ofac.treasury.gov/recent-actions | eventual | HTML/XML/CSV en listas | oficial | sanciones financieras, energia, shipping, Rusia/Iran |
| Treasury press releases | https://home.treasury.gov/news/press-releases | eventual | HTML | oficial | sanciones, G7, debt/financial policy |
| Commerce/BIS Federal Register | https://www.federalregister.gov/agencies/industry-and-security-bureau | eventual | HTML/API | oficial/legal | export controls, entity list, chips/AI |
| WTO news | https://www.wto.org/english/news_e/news_e.htm | eventual | HTML | organismo internacional | disputas comerciales, aranceles, retaliacion |

### 3.3 Eventos a incluir y excluir

Incluir solo si hay al menos uno de estos canales:

- energia: Brent/WTI, gas, inventarios, produccion, transporte o seguros maritimos;
- inflacion: breakevens, combustibles, alimentos/commodities, shipping;
- comercio: arancel oficial, Section 301, WTO, acuerdo bilateral relevante;
- sanciones: OFAC/UE/UK sobre energia, bancos, shipping, tecnologia o commodities;
- tecnologia: export controls, chips, AI, tierras raras, minerales criticos;
- riesgo global: DXY, oro, UST reales, VIX, spreads EM.

Excluir o dejar en watchlist:

- titulares belicos sin fuente primaria y sin precio;
- rumores de prensa no confirmados por precio o comunicado oficial;
- declaraciones politicas sin instrumento operativo;
- eventos humanitarios sin canal macro directo para este reporte.

## 4. Conectores propuestos

### Prioridad alta

1. `market_prices_weekly_proxy_connector`
   - Fuentes: FRED CSV (`DCOILWTICO`, `DCOILBRENTEU`, `T10YIE`, `T5YIE`, `T5YIFR`, `DFII10`, `DTWEXBGS`) + Stooq (`dx.f`, `xauusd` o `gc.f`).
   - Output: ultimo dato, fecha, variacion 1w, variacion 4w, fuente, tipo (`primary`, `proxy`).

2. `eia_wpsr_connector`
   - Fuente: https://www.eia.gov/petroleum/supply/weekly/
   - Output: release_date, week_ending, crude stocks, Cushing, gasoline, distillates, refinery utilization, production, imports/exports, product supplied.

3. `eia_steo_connector`
   - Fuente: https://www.eia.gov/outlooks/steo/
   - Output: release_date, Brent/WTI forecast, world liquids consumption/production, OPEC+ production, inventories, key forecast changes.

4. `opec_event_connector`
   - Fuentes: OPEC press releases + MOMR.
   - Output: meeting_date, decision, quota/cut/addition, countries, effective_date, stated rationale, URL.

5. `geo_event_watch_connector`
   - Fuentes: USTR, OFAC, White House, Federal Register USTR/BIS, IAEA, EIA disruptions.
   - Output: event_date, source, event_type, instrument, affected countries/commodities, macro_channel, URL, confidence.

### Prioridad media

6. `iea_public_oil_connector`
   - Solo resumen publico de IEA OMR; no asumir full report.

7. `portwatch_shipping_connector`
   - Puerto/chokepoint changes si hay API o export estable.

8. `cme_manual_quote_check`
   - Check de paginas CME para WTI/Brent/Gold cuando hay shock intradia; no base historica inicial.

## 5. Minimo viable semanal sin proveedores pagos

### Insumos fijos

| Bloque | Fuente gratis | Dia sugerido | Salida |
| --- | --- | --- | --- |
| Precios crudo | FRED `DCOILWTICO`, `DCOILBRENTEU`; fallback Stooq `cl.f`, `br.f` | viernes/cierre semanal | WTI, Brent, spread, % semanal |
| Oro | Stooq `xauusd` o `gc.f`; check CME Gold | viernes/cierre semanal | oro spot/futuro proxy, % semanal |
| Dolar | Stooq `dx.f` + FRED `DTWEXBGS` | viernes/cierre semanal | DXY proxy, broad dollar oficial |
| Inflacion implicita | FRED `T5YIE`, `T10YIE`, `T5YIFR`, `DFII10` | viernes/cierre semanal | breakevens, reales, lectura inflacion vs tasa real |
| Energia fisica | EIA WPSR | miercoles despues de release | stocks, Cushing, productos, produccion, exports |
| Outlook energia | EIA STEO | mensual | forecast y cambios vs mes anterior |
| OPEP | OPEC press/MOMR | mensual/eventual | decision, cumplimiento esperado, cambio de balance |
| Eventos | USTR, OFAC, White House, Federal Register, IAEA, EIA disruptions | diario ligero / viernes consolidado | eventos con canal macro |

### Workflow semanal

1. Descargar precios viernes o ultimo dato disponible:
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=T5YIE`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS`
   - `https://stooq.com/q/d/l/?s=dx.f&i=d`
   - `https://stooq.com/q/d/l/?s=xauusd&i=d`
2. Procesar EIA WPSR:
   - abrir `https://www.eia.gov/petroleum/supply/weekly/`;
   - tomar `week ending`, `release date`, tablas CSV de balance, stocks e import/export;
   - calcular variacion semanal de crude stocks, Cushing, gasoline, distillates y produccion.
3. Si hay release mensual:
   - EIA STEO: registrar cambios de forecast Brent/WTI, demanda, oferta, inventarios.
   - OPEC MOMR: registrar cambios de demanda, non-OPEC supply, OPEC production y narrativa.
4. Revisar eventos oficiales:
   - OFAC si hay sanciones a energia/shipping/bancos;
   - USTR/Federal Register si hay aranceles o Section 301;
   - BIS/Federal Register si hay export controls;
   - IAEA si hay Iran/Ucrania nuclear;
   - EIA disruptions si hay huracanes/outages/chokepoints.
5. Incluir en reporte solo senales con precio o fuente primaria:
   - Brent/WTI > 7% semanal;
   - DXY proxy > 2% semanal o broad dollar confirma;
   - oro > 3% semanal con DXY/tasas reales;
   - T10YIE > 15 pb semanal o DFII10 > 20 pb semanal;
   - WPSR crude/Cushing/product stocks fuera de rango reciente;
   - sancion/arancel/export control oficial con commodity, energia o tech afectado.

### Salida recomendada para el reporte

Para cada senal incluida:

```yaml
signal:
  source_url:
  source_type: primary|official|proxy
  frequency:
  observed_date:
  input:
  market_confirmation:
  macro_channel:
  reading:
  invalidation:
  next_watch:
```

Ejemplo de lectura:

- `Brent +9% semanal, WTI +8%, T10YIE +12 pb, DXY estable`: shock de energia con canal inflacionario; mirar WPSR/OPEC/EIA STEO y si gasolina/distillates validan.
- `Oro +4%, DXY +2%, DFII10 sin caer`: refugio/geopolitica mas que Fed dovish; exigir evento oficial o stress en VIX/UST.
- `OPEC anuncia recorte pero Brent no sube y spreads calendario no se tensionan`: el mercado no compra compliance o demanda domina.

## 6. Limitaciones y decisiones

- Brent/WTI spot de EIA/FRED es diario pero no intradia. Para shocks durante el dia, usar futures CME/ICE/Stooq como confirmacion de mercado y luego reconciliar con spot.
- DXY oficial es propietario de ICE. En automatizacion gratis, `dx.f` de Stooq es proxy; `DTWEXBGS` es oficial pero no DXY.
- Oro oficial LBMA tiene restricciones/licencia para historico; Stooq/CME/Yahoo deben rotularse como proxies de mercado.
- IEA OMR completo puede requerir suscripcion. No disenar el MVP alrededor de datos pagos.
- OPEC comunica intencion y cuotas; EIA/STEO, precios y eventualmente datos de produccion/exportacion validan ejecucion.
- Eventos geoeconomicos necesitan una fuente primaria o precio de confirmacion. Medios como Axios/Bloomberg/CNBC pueden alertar, pero no deben ser fuente unica del dato.
- Federal Register es la fuente legal para reglas; press releases son mas rapidos pero pueden omitir detalles de vigencia, HS codes o excepciones.

## 7. Recomendacion final

Implementar primero un pipeline semanal gratuito con:

1. FRED CSV para crudo spot, breakevens, tasas reales y broad dollar.
2. Stooq CSV para DXY proxy y oro proxy.
3. EIA WPSR semanal como dato fisico central.
4. EIA STEO mensual y OPEC MOMR/press releases como contexto de balance/oferta.
5. Watchlist oficial de eventos: OFAC, USTR, White House, Federal Register USTR/BIS, IAEA y EIA disruptions.

Con eso alcanza para responder las preguntas del host sin proveedor pago: que hizo el precio, que dice el dato fisico, que evento oficial explica el shock, que precio confirma o invalida la lectura, y que mirar la semana siguiente.
