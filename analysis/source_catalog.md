# Catalogo de fuentes del host

Estado:
- `explicita`: mencionada de forma directa en `analysis/host_profile.md` o `analysis/subagents/*.md`
- `inferida`: no siempre nombrada, pero el uso se deduce con alta confianza por indicadores o documentos citados
- `pendiente de verificacion`: aparece con nombre confuso, genérico o indirecto; no conviene automatizarla sin chequeo extra

Prioridad semanal:
- `alta`: suele mover escenario o precios
- `media`: agrega contexto frecuente
- `baja`: util, pero no estructural todas las semanas

## Argentina

| Fuente | Tipo | Estado | Periodicidad esperada | Prioridad semanal | Uso principal |
| --- | --- | --- | --- | --- | --- |
| BCRA | oficial | explicita | diaria / semanal / mensual | alta | reservas, compras/ventas, encajes, tasas, balance, IPOM |
| Tesoro / Ministerio de Economia | oficial | explicita | semanal / por licitacion / mensual | alta | licitaciones, rollover, vencimientos, caja, deuda, RIGI |
| INDEC | oficial | explicita | semanal / mensual / trimestral | alta | IPC, EMAE, actividad, empleo, pobreza, canastas |
| IPC CABA | oficial subnacional | explicita | mensual | alta | anticipo de inflacion nacional |
| FMI / staff reports | organismo | explicita | por revision / eventual | alta | metas, reservas, fiscal, programa financiero |
| OPC | organismo tecnico | explicita | mensual / eventual | media | contraste caja vs devengado, deuda flotante |
| Ferreres | privada | explicita | mensual / alta frecuencia | media | actividad e inflacion de seguimiento |
| EcoGo | privada | explicita | semanal / mensual | media | nowcast de inflacion |
| REM BCRA | encuesta | explicita | mensual | media | expectativas de consultoras, no precio de mercado |
| UTDT / Di Tella | academia | explicita | mensual | media | confianza, imagen, clima politico |
| SIPA | oficial | explicita | mensual | media | empleo privado registrado |
| Riesgo pais JP Morgan / EMBI | mercado | inferida | diaria | alta | stress soberano y cambio de regimen |
| MAE / BYMA / A3-Rofex | mercado | inferida | diaria | alta | dolar oficial/MEP/CCL, futuros, curvas CER/TAMAR/LECAP/dollar-linked |
| Ratings S&P / Fitch / Moody's | calificadoras | explicita | eventual | media | acceso a mercado y senal institucional |
| BID / Banco Mundial / CAF / BIRF | multilaterales | explicita | eventual | media | desembolsos, vencimientos, financiamiento |
| Encuestas electorales / analisis mesa por mesa | politica | inferida | semanal / eventual | media | riesgo politico, probabilidad implicita en activos |

## Internacional

| Fuente | Tipo | Estado | Periodicidad esperada | Prioridad semanal | Uso principal |
| --- | --- | --- | --- | --- | --- |
| Fed / FOMC / Powell / minutas / SEP | banco central | explicita | diaria / por reunion / quincenal | alta | tasas, dot plot, guidance, mandato dual |
| Treasury de EE.UU. | oficial | explicita | diaria / semanal / trimestral | alta | TGA, issuance, refunding, bills/notes/bonds |
| BLS | oficial | inferida | semanal / mensual | alta | payrolls, CPI, JOLTS, desempleo, participacion |
| BEA | oficial | inferida | mensual / trimestral | alta | PCE, PIB, GDI, ingreso y consumo real |
| Cleveland Fed nowcasts | regional Fed | explicita | diaria / semanal | media | nowcast de inflacion USA |
| GDPNow Atlanta Fed / Nowcast NY Fed | regional Fed | explicita | semanal | media | seguimiento de actividad USA |
| BCE | banco central | explicita | por reunion / eventual | media | tasa y tono europeo |
| BoE | banco central | explicita | por reunion / eventual | media | tasa y mercado britanico |
| BoJ | banco central | explicita | por reunion / eventual | media | yen, carry, normalizacion monetaria |
| BoC / RBNZ / RBA | bancos centrales | explicita | por reunion / eventual | baja-media | comparacion de shock inflacionario global |
| FMI | organismo | explicita | eventual | media | geoeconomia, conflictos, gasto militar |
| BLS-ADP-JOLTS set privado/oficial | mixto | explicita | semanal / mensual | media | chequeos cruzados del mercado laboral |

## Mercado global

| Fuente | Tipo | Estado | Periodicidad esperada | Prioridad semanal | Uso principal |
| --- | --- | --- | --- | --- | --- |
| UST 2y/10y/30y | mercado | explicita | diaria | alta | curva, tasas reales, condiciones financieras |
| DXY | mercado | explicita | diaria | alta | fortaleza global del dolar |
| Oro | mercado | explicita | diaria | media | refugio, geopolítica, tasas reales |
| Brent / WTI | mercado | explicita | diaria | alta | energia, inflacion, geopolítica |
| Breakevens / TIPS | mercado | explicita | diaria | alta | expectativa de inflacion implicita |
| S&P 500 / Nasdaq / Mag7 | mercado | explicita | diaria | media | apetito por riesgo, IA, liquidez |
| VIX | mercado | explicita | diaria | media | stress cuantificable |
| Riesgo pais argentino / bonos hard dollar | mercado | explicita | diaria | alta | lectura de Argentina desde precios |
| Curvas soberanas y tasas locales | mercado | explicita | diaria | alta | rollover, precios genuinos vs forzados |
| Bloomberg terminal / calendarios de mercado | mercado | inferida | diaria | media | escenarios, consensos, timing de eventos |
| CME FedWatch / OIS / pricing de tasas | mercado | inferida | diaria | media | probabilidades implicitas de Fed |

## Geopolitica

| Fuente | Tipo | Estado | Periodicidad esperada | Prioridad semanal | Uso principal |
| --- | --- | --- | --- | --- | --- |
| Axios | medio | explicita | eventual | media | primicias Medio Oriente |
| Bloomberg / CNBC | medio | explicita | eventual | media | Japon, Fed, energia, escenarios de mercado |
| Corte Suprema / tribunal federal de comercio EE.UU. | judicial | explicita | eventual | media | aranceles, legalidad comercial |
| OMC | organismo | explicita | eventual | baja-media | reglas comerciales y dumping |
| Agencia Internacional de Energia | organismo | explicita | eventual / mensual | alta | reservas estrategicas, oferta petrolera |
| EIA | oficial | inferida | semanal / mensual | media | crudo, gasolina, inventarios, energia USA |
| OPEP | organismo/cartel | explicita | eventual / mensual | media | oferta petrolera global |
| Casa Blanca / Tesoro EE.UU. | oficial | explicita | eventual | media | aranceles, acuerdos, asistencia financiera |
| China / India / Rusia / Ucrania / Iran / Israel / Japon | actores estatales | explicita | eventual | media | shocks geoeconomicos y de energia |
| Organismo nuclear internacional (nombre a confirmar) | organismo | pendiente de verificacion | eventual | baja | capacidad nuclear iran y escalada |

## Notas operativas

- Para el agente semanal, el nucleo minimo deberia salir de: `BCRA`, `Tesoro`, `INDEC`, `FMI`, `Fed`, `Treasury`, `BLS/BEA`, `Brent/WTI`, `DXY`, `UST`, `riesgo pais` y `curvas locales`.
- `REM`, consultoras, ratings y medios sirven como contexto o anticipo, pero no deben reemplazar precios ni datos oficiales.
- Las fuentes `inferidas` conviene incorporarlas al pipeline solo si luego se valida el documento o proveedor exacto.
- Las fuentes `pendiente de verificacion` deben quedar fuera de automatizaciones hasta limpiar nombres y origen.
