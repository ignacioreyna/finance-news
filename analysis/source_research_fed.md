# Investigacion de fuentes oficiales Fed y FOMC

Fecha de verificacion: 2026-06-14

## Objetivo

Mapear fuentes oficiales de la Reserva Federal para cubrir:

- decisiones de politica monetaria;
- comunicacion FOMC/Fed;
- balance, liquidez e implementacion operativa.

La prioridad es usar paginas oficiales de `federalreserve.gov` y, cuando la operacion la ejecuta el Desk, complementar con `newyorkfed.org`.

## Resumen ejecutivo

- La pagina madre para politica monetaria es [FOMC meeting calendars and information](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm). Consolida calendario, statement, implementation note, press conference, projection materials y minutes por reunion.
- Las reuniones con asterisco publican `SEP / dot plot` en marzo, junio, septiembre y diciembre. La pagina oficial lo explicita en el calendario.
- Los `minutes` salen con rezago de aproximadamente tres semanas sobre la reunion, visibles en el mismo calendario y en el archivo dedicado.
- Para comunicacion continua, la fuente primaria mas estable es [Speeches](https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm) y su equivalente anual.
- Para balance/liquidez, la pieza estructural es [H.4.1](https://www.federalreserve.gov/releases/h41/), que se publica semanalmente los jueves a las 4:30 p.m. ET. Se complementa con [Recent balance sheet trends](https://www.federalreserve.gov/monetarypolicy/bst_recenttrends.htm), [SOMA holdings](https://www.newyorkfed.org/markets/soma-holdings) y [Reverse Repo Operations](https://www.newyorkfed.org/markets/desk-operations/reverse-repo).

## 1. Politica monetaria

| Fuente | URL oficial | Cobertura | Periodicidad | Formatos | Uso principal | Nota operativa |
| --- | --- | --- | --- | --- | --- | --- |
| Calendario FOMC + paquete por reunion | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | calendario anual, statement, implementation note, press conference, projection materials, minutes | 8 reuniones regulares por anio; actualizacion por evento | HTML, PDF, links salientes a video | indice canonico por reunion | Punto de entrada recomendado para discovery y linking |
| Statement FOMC | https://www.federalreserve.gov/newsevents/pressreleases/monetary20250618a.htm | decision de tasa, voto, balance de riesgos, guidance | por reunion, tipicamente 2:00 p.m. ET | HTML; ademas PDF vinculado desde calendario | gatillo principal del weekly report | Conviene persistir `meeting_date`, `release_time_et`, `title`, `body`, `votes` |
| Implementation Note | misma reunion dentro de `fomccalendars.htm` | parametros operativos: rango fed funds, IORB, ON RRP, standing repo, reinversion/QT | por reunion | HTML/PDF | traduce decision a implementacion | Es clave para liquidez aunque viva junto al statement |
| Minutes | https://www.federalreserve.gov/monetarypolicy/fomcminutes.htm | discusion, riesgos, sesgo interno, detalle de balance e implementacion | por reunion, con rezago aproximado de 3 semanas | HTML y PDF | contexto cualitativo y cambio de tono | Extraer tambien directive y detalles de QT/QE |
| SEP / dot plot / projection materials | ejemplo: https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm | PIB, desempleo, PCE, core PCE, fed funds path y dispersion de dots | trimestral: marzo, junio, septiembre, diciembre | HTML accesible y PDF | escenario base Fed y distribucion del sendero de tasas | Solo en reuniones marcadas con `*` |
| Longer-Run Goals and Monetary Policy Strategy | incluido en algunas reuniones del calendario, p.ej. enero 2026 | marco de objetivos y estrategia | eventual, no en cada reunion | HTML/PDF | referencia de regimen | No es flujo semanal, si de contexto estructural |

### Hechos operativos confirmados

- El calendario oficial muestra para 2026 las ocho reuniones y marca con `*` las asociadas a `SEP`: marzo, junio, septiembre y diciembre.
- La misma pagina concentra `Statement`, `Implementation Note`, `Press Conference`, `Projection Materials` y `Minutes` por reunion.
- En la muestra oficial 2025/2026, los `minutes` se publican tres semanas despues de la reunion.

### Endpoint/documento minimo por reunion

1. `statement_html_url`
2. `statement_pdf_url`
3. `implementation_note_url`
4. `press_conference_url`
5. `minutes_html_url`
6. `minutes_pdf_url`
7. `sep_html_url` y `sep_pdf_url` cuando exista

## 2. Comunicacion

| Fuente | URL oficial | Cobertura | Periodicidad | Formatos | Uso principal | Nota operativa |
| --- | --- | --- | --- | --- | --- | --- |
| Speeches by year | https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm | discursos de Powell, gobernadores y vice chairs; a veces incluye video o live link | irregular, varias veces por semana en periodos activos | HTML; links a video externos | seguimiento de tono fuera de reuniones | El patron es anual: `/newsevents/speech/YYYY-speeches.htm` |
| Testimony | https://www.federalreserve.gov/newsevents/testimony.htm | comparecencias ante Congreso | eventual | HTML/PDF/video segun evento | señal institucional y politica | Complementa speeches cuando el mensaje se mueve por Congreso |
| Press releases (monetary) | https://www.federalreserve.gov/newsevents/pressreleases.htm | comunicados monetarios y de facilidades | eventual, por evento | HTML | alertas de cambios extraordinarios | Filtrar por categoria `monetary` |
| Press conference video/transcript | linkeado desde `fomccalendars.htm` por reunion | conferencia posterior al statement | por reunion | video / HTML segun recurso | matiz de guidance y reaccion a preguntas | Fuente util para citas, no siempre para parsing automatizado inicial |

### Prioridad editorial dentro de comunicacion

1. Powell
2. Vice Chair y Vice Chair for Supervision
3. Governors con sesgo de politica monetaria activo
4. Testimony al Congreso
5. Resto de speeches

### Señales que vale extraer

- frases sobre inflacion, empleo, crecimiento y riesgos bilaterales;
- menciones a `uncertainty`, `data dependent`, `restrictive`, `balance sheet`, `repo`, `liquidity`;
- cambios respecto del ultimo statement o del ultimo discurso de Powell.

## 3. Balance, liquidez e implementacion

| Fuente | URL oficial | Cobertura | Periodicidad | Formatos | Uso principal | Nota operativa |
| --- | --- | --- | --- | --- | --- | --- |
| H.4.1 Factors Affecting Reserve Balances | https://www.federalreserve.gov/releases/h41/ | activos/pasivos Fed, reserve balances, ON RRP, Treasury General Account, securities held outright, loans y facilidades | semanal; jueves 4:30 p.m. ET, salvo feriados | HTML, PDF, RSS, Data Download, FRED | fuente estructural para balance semanal | Debe ser la base del conector de balance |
| Recent balance sheet trends | https://www.federalreserve.gov/monetarypolicy/bst_recenttrends.htm | visualizacion oficial y lectura resumida de tendencias de balance | actualizado tras H.4.1 | HTML accesible | contexto y QA visual | No reemplaza H.4.1; sirve como validacion y resumen |
| SOMA holdings | https://www.newyorkfed.org/markets/soma-holdings | detalle de holdings de Treasuries y MBS del SOMA | regular, ligado a operaciones del Desk | HTML, archivos descargables segun pagina | composicion fina del portfolio y QT | Util para profundidad que H.4.1 no da por titulo |
| Reverse Repo Operations | https://www.newyorkfed.org/markets/desk-operations/reverse-repo | resultados de operaciones repo y reverse repo, historico y APIs del mercado | diaria | HTML, historico, APIs | drenaje/inyecion de liquidez de muy corto plazo | Relevante para piso de tasas y uso ON RRP |
| H.3 Aggregate Reserves of Depository Institutions and the Monetary Base | https://www.federalreserve.gov/releases/h3/ | reservas agregadas y base monetaria | semanal | HTML, PDF, Data Download | serie de apoyo para reservas | Complemento a H.4.1, no sustituto |
| Open market operations / policy implementation background | https://www.federalreserve.gov/monetarypolicy/policytools.htm | descripcion de herramientas operativas y facilidadades | eventual | HTML | contexto de regimen operativo | Util para documentacion de conectores |

### Variables minimas a seguir en balance/liquidez

- total assets;
- securities held outright;
- reserve balances with Federal Reserve Banks;
- overnight reverse repurchase agreements;
- Treasury General Account;
- central bank liquidity swaps y otros loans si reaparecen;
- caps y reglas de reinversion/QT desde `Implementation Note` y `Minutes`.

## 4. Separacion recomendada por dominio

### A. Politica monetaria

Incluye:

- calendario FOMC;
- statement;
- implementation note;
- minutes;
- SEP / dot plot;
- longer-run goals.

Preguntas que responde:

- que decidio la Fed hoy;
- como cambio el sendero esperado de tasas;
- cambia QT/QE o solo la tasa;
- que tan dividido fue el comite.

### B. Comunicacion

Incluye:

- speeches;
- testimony;
- press releases monetarios fuera de reunion;
- press conference.

Preguntas que responde:

- cambia el tono entre reuniones;
- Powell o gobernadores estan preparando al mercado para un cambio;
- hay divergencias publicas relevantes dentro del Board.

### C. Balance y liquidez

Incluye:

- H.4.1;
- recent balance sheet trends;
- SOMA holdings;
- reverse repo operations;
- H.3;
- tools/policy implementation background.

Preguntas que responde:

- sigue QT y a que ritmo;
- donde esta drenando o acumulando liquidez el sistema;
- cae el ON RRP, suben reservas, cambia TGA, reaparecen facilidades;
- hay señal de stress de fondeo o cambio operativo.

## 5. Conectores atomicos propuestos

### Prioridad alta

1. `fed_fomc_calendar_connector`
   - Descubre reuniones y URLs hijas desde `fomccalendars.htm`.
   - Output: una fila por reunion con links a statement, minutes, SEP, implementation note, press conference.

2. `fed_fomc_statement_connector`
   - Consume el statement HTML/PDF de una reunion.
   - Output: fecha, decision, rango objetivo, votos, cuerpo limpio, flags de cambio de lenguaje.

3. `fed_fomc_minutes_connector`
   - Consume minutes HTML/PDF.
   - Output: resumen estructurado de actividad, inflacion, empleo, riesgos, balance, directive operativa.

4. `fed_sep_connector`
   - Consume projection materials solo en reuniones con `*`.
   - Output: medianas de GDP, unemployment, PCE, core PCE, fed funds; dispersion de dots si se puede capturar.

5. `fed_h41_connector`
   - Consume release semanal H.4.1.
   - Output: snapshot semanal de variables clave de balance/liquidez.

### Prioridad media

6. `fed_speeches_connector`
   - Consume pagina anual de speeches.
   - Output: fecha, speaker, titulo, URL, tags por tema y prioridad editorial.

7. `nyfed_soma_holdings_connector`
   - Consume holdings SOMA.
   - Output: composicion por tipo de titulo, vencimiento y cambios relevantes para QT.

8. `nyfed_rrp_repo_connector`
   - Consume resultados diarios de repo/RRP.
   - Output: uso diario, contrapartes si aplica, tasa operativa y serie historica corta.

### Prioridad baja pero util

9. `fed_h3_reserves_connector`
   - Serie de apoyo para reservas agregadas y base monetaria.

10. `fed_policy_tools_reference_connector`
   - No para reporte semanal, si para documentar reglas y mapping semantico.

## 6. Reglas de ingestión recomendadas

- Priorizar HTML cuando exista y usar PDF como respaldo o QA.
- Tratar `fomccalendars.htm` como indice oficial, no duplicar discovery con scraping suelto de press releases.
- Versionar por `meeting_date` y `release_timestamp_et`.
- Guardar URL fuente exacta en cada registro para trazabilidad editorial.
- Separar `documento primario` de `resumen derivado`.
- En speeches, asignar score de importancia por speaker antes de resumir contenido.
- En balance, no mezclar datos semanales de H.4.1 con resultados diarios de repo/RRP sin marcar frecuencia.

## 7. Riesgos y supuestos

- Algunas URLs de speeches son anuales; el conector debe derivar el anio en curso y conservar historico.
- Los recursos de New York Fed pueden exponer tablas o APIs distintas segun producto; conviene desacoplar `SOMA` de `RRP/repo`.
- `Recent balance sheet trends` sirve mas como capa explicativa que como fuente primaria numerica.

## 8. URLs oficiales verificadas

- FOMC calendars and information: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- FOMC minutes archive: https://www.federalreserve.gov/monetarypolicy/fomcminutes.htm
- SEP example, 2025-03-19: https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20250319.htm
- Statement example, 2025-06-18: https://www.federalreserve.gov/newsevents/pressreleases/monetary20250618a.htm
- Speeches 2025: https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm
- Testimony: https://www.federalreserve.gov/newsevents/testimony.htm
- Press releases: https://www.federalreserve.gov/newsevents/pressreleases.htm
- H.4.1 release page: https://www.federalreserve.gov/releases/h41/
- Recent balance sheet trends: https://www.federalreserve.gov/monetarypolicy/bst_recenttrends.htm
- H.3 release page: https://www.federalreserve.gov/releases/h3/
- SOMA holdings: https://www.newyorkfed.org/markets/soma-holdings
- Reverse repo operations: https://www.newyorkfed.org/markets/desk-operations/reverse-repo
- Policy tools / implementation background: https://www.federalreserve.gov/monetarypolicy/policytools.htm

## 9. Recomendacion final

Para el pipeline semanal, el orden correcto es:

1. `fed_fomc_calendar_connector` como discovery;
2. `fed_fomc_statement_connector` y `fed_sep_connector` para shock de reunion;
3. `fed_fomc_minutes_connector` para tono con rezago;
4. `fed_speeches_connector` para comunicacion intermeeting;
5. `fed_h41_connector` y `nyfed_rrp_repo_connector` para balance/liquidez;
6. `nyfed_soma_holdings_connector` cuando se necesite profundidad de QT o composicion por vencimiento.
