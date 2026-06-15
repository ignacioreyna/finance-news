# Investigacion de fuentes para IA, semiconductores, capex y Mag7

Fecha de verificacion: 2026-06-14

## Objetivo

Mapear fuentes primarias y proxies de mercado para seguir:

- IA como driver de capex corporativo y multiples;
- semiconductores como cuello de botella, instrumento geopolitico y beta de mercado;
- productividad y monetizacion como filtro para separar narrativa de impacto real;
- Mag7 e infraestructura AI solo cuando cambian la lectura macro, de liquidez o de apetito por riesgo.

La meta no es hacer stock picking. La meta es detectar cuando IA/chips/Mag7 pasan de ser historia sectorial a ser señal relevante para el reporte semanal.

## Resumen ejecutivo

- El bloque central debe arrancar en `SEC/EDGAR` y `investor relations` oficiales de hyperscalers y fabricantes clave. Ahi aparecen capex, guidance, backlog, inventarios, restricciones de oferta, depreciacion, margenes y lenguaje de demanda real.
- Para productividad y capex macro, las fuentes primarias son `BLS`, `BEA` y, cuando haga falta confirmar construccion/infraestructura, `Census`. Sirven para validar si la narrativa de IA ya sale del relato corporativo y entra en datos agregados.
- Para regulacion, separar dos carriles: `regulacion de negocio/competencia/AI policy` por un lado y `restricciones comerciales/export controls` por otro.
- Los precios de `Nasdaq`, `SOX`, `Mag7`, `NVDA`, `AMD`, `TSM`, `ASML`, `UST`, `DXY` y energia sirven como confirmacion o contradiccion. No son fuente causal primaria.

## Principios editoriales

1. Priorizar documentos primarios sobre notas de mercado.
2. No incluir una noticia sectorial si no tiene canal claro hacia:
   - capex;
   - productividad;
   - liquidez/earnings del equity index;
   - restricciones de oferta/comercio;
   - regulacion con impacto material.
3. No abrir una seccion por un movimiento de una accion aislada salvo que:
   - arrastre al complejo AI/chips;
   - mueva indices amplios;
   - cambie guidance agregado de capex o demanda.
4. Separar siempre:
   - narrativa corporativa;
   - dato oficial;
   - precio de mercado.

## 1. Earnings, SEC y investor relations

### 1.1 Fuente primaria base

| Fuente | URL oficial | Cobertura | Uso principal | Prioridad |
| --- | --- | --- | --- | --- |
| SEC EDGAR company filings | https://www.sec.gov/search-filings | 10-K, 10-Q, 8-K, 6-K, proxies, exhibits | fuente canonica para guidance, riesgos, capex, segmentos, inventory, legal/regulatory risk | alta |
| SEC Company Facts API | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | XBRL y facts por emisor | seguimiento estructurado de capex, revenue, margins y segmentos cuando el tagging ayuda | media |
| Earnings releases via 8-K / IR | pagina IR de cada empresa | comunicado trimestral, slides, webcast, transcript oficial si existe | primera lectura rapida del quarter | alta |
| Annual reports / shareholder letters | pagina IR de cada empresa | estrategia, vida util de activos, AI monetization, capex framework | contexto estructural | media |

### 1.2 Universe minimo a cubrir

#### A. Hyperscalers y plataformas donde IA mueve capex

| Empresa | IR oficial | Que mirar primero |
| --- | --- | --- |
| Microsoft | https://www.microsoft.com/en-us/Investor | capex total, cloud/AI capacity, Azure growth, backlog, useful life, comments sobre demanda superando oferta |
| Amazon | https://ir.aboutamazon.com/ | capex y finance leases, AWS growth, AI infra, comentarios sobre capacidad y retorno esperado |
| Alphabet | https://abc.xyz/investor/ | capex guidance, cloud growth, TPU/data center spend, monetizacion AI en Search/Cloud |
| Meta | https://investor.atmeta.com/ | capex range, infra AI, efficiency/productivity claims, monetizacion de ads con AI |

#### B. Compute, networking y supply chain AI

| Empresa | IR oficial | Que mirar primero |
| --- | --- | --- |
| NVIDIA | https://investor.nvidia.com/ | Data Center revenue, networking, gross margin, inventory, supply constraints, export restrictions |
| AMD | https://ir.amd.com/ | Data Center/GPU AI ramp, enterprise demand, margin mix, customer concentration |
| Broadcom | https://investors.broadcom.com/ | AI networking/custom silicon, hyperscaler concentration, backlog, capex de clientes |
| TSMC | https://investor.tsmc.com/english | node demand, AI accelerators, advanced packaging, monthly revenue, capex discipline |
| ASML | https://www.asml.com/en/investors | bookings, EUV demand, China exposure, shipment timing, export license risk |

#### C. Mag7 de seguimiento contextual, no automatico

| Empresa | IR oficial | Condicion para entrar al reporte |
| --- | --- | --- |
| Apple | https://investor.apple.com/ | solo si guidance, device cycle o regulation conectan con AI demand o cadena de semis |
| Tesla | https://ir.tesla.com/ | solo si AI/Dojo/robotaxi/capex cambia lectura de riesgo amplio, no por ruido idiosincratico |

### 1.3 Documentos y campos que importan

| Documento | Senales a extraer |
| --- | --- |
| 10-Q / 10-K | capex, useful life, depreciation, inventory, customer concentration, risk factors, legal/regulatory exposure, geographic revenue |
| 8-K earnings release | revenue por segmento, guidance, capex actualizado, margin commentary, supply/demand imbalance |
| earnings slides | backlog, data center growth, AI bookings, unit economics, infra build-out |
| prepared remarks / transcript oficial | lenguaje sobre demanda real vs pilot projects, monetizacion, productividad interna, timing de retorno |
| shareholder letter | cambios de estrategia y disciplina de inversion |

### 1.4 Senales semanales que si valen

- cambio de guidance de capex en hyperscalers;
- comentario repetido de `demand exceeds supply` o, al reves, normalizacion de oferta;
- aceleracion o freno de revenue de data center / cloud que cambie multiples del indice;
- extension de vida util de servidores o cambio contable que altere lectura de flujo de caja;
- inventarios, lead times o packaging constraints en chips avanzados;
- menciones materiales a `export controls`, licencias, China exposure o customer concentration.

### 1.5 Senales que no alcanzan solas

- demo de producto sin guidance asociado;
- titulares de partnership sin monto, volumen o efecto en capex;
- mejora marginal de un solo nombre sin confirmacion en peers o en indices.

## 2. Productividad y capex macro

### 2.1 Fuentes primarias

| Fuente | URL oficial | Cobertura | Uso principal | Prioridad |
| --- | --- | --- | --- | --- |
| BLS Labor Productivity and Costs | https://www.bls.gov/productivity/ | productividad laboral, output por hora, costos laborales unitarios | verificar si la narrativa de AI ya aparece en productividad agregada | media |
| BEA GDP / NIPA | https://www.bea.gov/data/gdp/gross-domestic-product | PIB y composicion, incluyendo private fixed investment | medir si capex privado acompania la historia AI | alta |
| BEA Fixed Assets / IP investment context | https://www.bea.gov/data/investment-saving/fixed-assets | stock de capital e inversion por tipo de activo | contexto estructural de software, IP y equipo | media |
| BEA Personal income and outlays / PCE | https://www.bea.gov/data/income-saving/personal-income | sirve como contexto macro para monetizacion y consumo, no como fuente AI directa | baja-media |
| Census Construction Spending | https://www.census.gov/construction/c30/current/index.html | construccion privada no residencial, incluida infraestructura relevante | confirmar boom de data centers e infra fisica | media |
| Census Manufacturers' Shipments, Inventories, and Orders | https://www.census.gov/manufacturing/m3/index.html | ordenes e inventarios manufactureros | chequear si el ciclo de equipo/capex se amplifica o enfria | media |

### 2.2 Variables que mas importan

| Bloque | Variable | Lectura editorial |
| --- | --- | --- |
| productividad | output per hour, unit labor costs | si la productividad mejora, la narrativa de AI gana sustento macro; si no, sigue siendo promesa/capex adelantado |
| capex agregado | private fixed investment, equipment, intellectual property products | confirma si el boom de AI ya escala a cuentas nacionales |
| infraestructura | construction spending no residencial / data-center-linked proxies | valida si el capex de hyperscalers se traduce en obra fisica |
| ciclo manufacturero | new orders, shipments, inventories | ayuda a detectar si chips y equipo son expansion genuina o solo restocking |

### 2.3 Regla de lectura

- `BLS` y `BEA` son confirmacion lenta pero robusta.
- Un quarter fuerte de hyperscalers no alcanza para hablar de ganancia de productividad agregada.
- La narrativa pasa a ser de alta prioridad cuando:
  - el capex corporativo sube en filings;
  - la inversion agregada en `BEA` acompania;
  - algun dato de `BLS` o costos laborales sugiere mejora real de eficiencia.

## 3. Noticias regulatorias

Separar regulacion de negocio/competencia de comercio exterior. Esta seccion cubre solo la primera.

| Fuente | URL oficial | Cobertura | Uso principal | Prioridad |
| --- | --- | --- | --- | --- |
| DOJ Antitrust | https://www.justice.gov/atr | casos y comunicados de competencia | seguir acciones que afecten estructura, distribucion o monetizacion de Mag7/AI | media |
| FTC News | https://www.ftc.gov/news-events/news | investigaciones y policy signals sobre plataformas, datos y competencia | filtro regulatorio para big tech | media |
| White House Briefing Room | https://www.whitehouse.gov/briefing-room/ | executive orders, fact sheets, AI policy general | detectar cambios de politica con impacto en investment mood o compliance | media |
| NIST AI | https://www.nist.gov/artificial-intelligence | marcos, estandares y guidance | contexto de cumplimiento, no gatillo semanal por si solo | baja-media |
| European Commission Competition / Digital | https://competition-policy.ec.europa.eu/ | decisiones sobre plataformas y competencia en UE | relevante solo si cambia economics o riesgo legal de Mag7 | baja-media |

### Senales regulatorias que si entran

- demanda, settlement o injunction que afecte distribucion, bundling, App Store, ads o cloud economics;
- reglas de AI safety/compliance con costo material para despliegue o monetizacion;
- anuncios oficiales que cambien permisos, reporting o acceso a datos/modelos para grandes plataformas.

### Senales regulatorias que quedan fuera

- speech politico sin accion concreta;
- consulta publica sin calendario, enforcement ni impacto economico visible;
- titulares de lobbying o opinion sin documento oficial.

## 4. Restricciones comerciales y export controls

Esta seccion es distinta de regulacion de negocio. El foco es comercio, seguridad nacional y oferta global de chips.

| Fuente | URL oficial | Cobertura | Uso principal | Prioridad |
| --- | --- | --- | --- | --- |
| BIS home / news and updates | https://www.bis.gov/ | export administration regulations, press releases, guidance | punto de entrada principal para export controls de advanced computing y semiconductor manufacturing | alta |
| BIS Entity List / regulatory actions | https://www.bis.gov/entity-list | altas/bajas y restricciones por entidad | detectar shocks a supply chain, clientes chinos y licencias | alta |
| Federal Register | https://www.federalregister.gov/ | texto legal y effective dates de nuevas reglas | confirmar vigencia exacta y alcance de la restriccion | alta |
| U.S. Department of Commerce News | https://www.commerce.gov/news | comunicados politicos y de implementacion | contexto oficial alrededor de BIS | media |
| USTR | https://ustr.gov/ | aranceles, investigaciones y cambios de politica comercial | relevante si afecta hardware, insumos o retaliacion | media |
| Treasury OFAC | https://ofac.treasury.gov/ | sanciones financieras | usar cuando la restriccion sea via sancion y no via EAR | media |
| White House Briefing Room | https://www.whitehouse.gov/briefing-room/ | fact sheets o executive framing de seguridad nacional | contexto politico de cambios en chips/China | media |

### Senales de restricciones comerciales que mas mueven mercado

- nueva regla BIS para `advanced computing`, `AI models`, `semiconductor manufacturing items` o licencias a China;
- cambios en `Entity List` que toquen clientes, foundries, packaging o tooling;
- ampliacion o relajacion de licencias con efecto en revenue de NVIDIA, AMD, ASML, TSMC o proveedores de equipamiento;
- retaliacion oficial de China en minerales criticos, gallium/germanium, tierras raras o insumos de cadena;
- aranceles o controles que eleven costo de hardware, atrasen despliegue de capacity o peguen en margenes.

### Regla operativa

- no publicar la noticia solo por la geopolítica;
- exigir canal economico visible: revenue, shipments, bookings, capacity, costos o multiples;
- confirmar `effective date`, jurisdiccion y producto afectado antes de elevar relevancia.

## 5. Datos de mercado y proxies

Estas fuentes sirven como confirmacion o contradiccion. Son `secundarias/proxy`, no fuentes primarias de causalidad.

| Proxy | Tipo | Uso principal | Nota operativa |
| --- | --- | --- | --- |
| Nasdaq 100 | mercado | beta broad de growth/AI | util para medir si la historia sale del nicho |
| Philadelphia Semiconductor Index (SOX) | mercado | termometro sectorial de chips | mejor lectura sectorial que una accion aislada |
| Mag7 basket | mercado | concentracion de leadership en mega caps | usar como amplitud limitada, no como tesis |
| NVDA / AMD / AVGO / TSM / ASML | mercado | confirmacion de shocks de earnings o export controls | no abrir reporte por movimiento aislado sin fuente primaria |
| UST 2y/10y y tasas reales | macro mercado | sensibilidad de duration y multiples | IA funciona distinto si suben tasas reales |
| DXY | macro mercado | condicion financiera global | clave para separar earnings buenos de compresion de multiples |
| Brent / WTI / power/nat gas proxies | commodities | costo energetico e inflacion para build-out de data centers | contexto, no driver principal salvo shock fuerte |

### Regla de uso para proxies

- si el documento primario no aparece, el proxy solo va a watchlist;
- si hay documento primario y el precio lo confirma, la señal sube de prioridad;
- si el precio contradice la narrativa, el reporte debe explicarlo en vez de forzar la historia.

## 6. Criterios de relevancia para el reporte semanal

### 6.1 Filtro base

Una senal entra al reporte solo si cumple al menos dos de estos cuatro puntos:

1. proviene de fuente primaria o corporate filing oficial;
2. tiene canal claro hacia capex, productividad, oferta de chips, regulacion material o multiples amplios;
3. afecta mas de un nombre o un indice/segmento relevante;
4. cambia el escenario base o el calendario de seguimiento de la semana.

### 6.2 Score editorial sugerido

| Score | Cuando usarlo |
| --- | --- |
| 0 | titular sin dato, sin precio y sin canal macro claro |
| 1 | señal menor o idiosincratica; sirve solo como contexto |
| 2 | dato o filing relevante pero contenido; entra en subseccion |
| 3 | guidance, regulacion o restriccion comercial que cambia lectura de capex/earnings del complejo AI |
| 4 | shock que mueve indices, multiples amplios o expectativa macro de productividad/inversion |

### 6.3 Gatillos concretos para incluir

| Bloque | Gatillo inicial |
| --- | --- |
| hyperscaler capex | cambio de guidance, commentary de capacidad o capex mucho mayor/menor a lo esperado |
| chips | sorpresa fuerte en data center revenue, bookings, packaging constraints o China exposure |
| productividad | cambio visible en BLS productivity o unit labor costs que respalde o contradiga la narrativa AI |
| capex macro | BEA/Census muestran aceleracion o frenazo que salga del rango normal |
| regulacion | accion oficial con enforcement, multa, injunction o cambio material de economics |
| comercio | regla BIS/Federal Register con effective date y alcance claro sobre chips, tooling o AI compute |
| mercado | SOX/Nasdaq/Mag7 confirman en bloque un shock primario; solos no alcanzan |

### 6.4 Preguntas obligatorias antes de incluir

1. Que cambio exactamente: guidance, dato, regla o precio.
2. Cual es el mecanismo: oferta de chips, capex, productividad, margen, multiple o liquidez.
3. Quien absorbe el costo: proveedor, hyperscaler, cliente final o mercado.
4. Que precio o dato confirma la lectura.
5. Que dato la invalida la semana siguiente.

## 7. Workflow semanal recomendado

### Durante earnings season

1. Leer `8-K`, slides y prepared remarks oficiales.
2. Confirmar campos duros en `10-Q` o `10-K`.
3. Clasificar la señal:
   - capex;
   - demanda AI;
   - supply chain;
   - productividad/eficiencia;
   - regulacion/comercio.
4. Recién después mirar precio e indices.

### Fuera de earnings

1. Escanear `BIS`, `Federal Register`, `DOJ`, `FTC`, `White House`.
2. Revisar `BLS`, `BEA` y `Census` para evidencia agregada.
3. Usar mercado como capa de confirmacion.

## 8. Recomendacion final

Para el agente semanal, el orden correcto es:

1. `SEC/EDGAR` y `IR` de hyperscalers/fabricantes para descubrir shocks reales.
2. `BIS/Federal Register` para restricciones comerciales.
3. `DOJ/FTC/White House` para regulacion de negocio.
4. `BLS/BEA/Census` para validar si el tema escala de corporate story a macro story.
5. `Nasdaq/SOX/Mag7/UST/DXY` como filtro de confirmacion de mercado.

Si falta una fuente primaria, la señal no deberia pasar de watchlist salvo que el precio muestre ruptura amplia y el mecanismo sea obvio.
