# Validación del universo SEC IA / semiconductores / Mag7

**Fecha de documento:** 2026-06-20
**Tarea:** TASK-9.14 - Validar universo SEC IA semiconductores Mag7
**Fuente principal:** `analysis/source_research_ai_markets.md`

---

## 1. Universo mínimo

El siguiente universo se deriva de `source_research_ai_markets.md` (sección 1.2), pero **no contiene CIKs verificados**. Los CIKs deben obtenerse de SEC EDGAR.

### A. Hyperscalers y plataformas donde IA mueve capex (4 empresas)

| Ticker | CIK (verificar en SEC EDGAR) | Fuente oficial IR | Estado |
|---|---|---|---|
| MSFT | **TO-VERIFY** | https://www.microsoft.com/en-us/Investor | VERIFIED (IR URL) |
| AMZN | **TO-VERIFY** | https://ir.aboutamazon.com/ | VERIFIED (IR URL) |
| GOOGL/GOOG | **TO-VERIFY** | https://abc.xyz/investor/ | VERIFIED (IR URL) |
| META | **TO-VERIFY** | https://investor.atmeta.com/ | VERIFIED (IR URL) |

### B. Compute, networking y supply chain AI (5 empresas)

| Ticker | CIK (verificar en SEC EDGAR) | Fuente oficial IR | Estado |
|---|---|---|---|
| NVDA | **TO-VERIFY** | https://investor.nvidia.com/ | VERIFIED (IR URL) |
| AMD | **TO-VERIFY** | https://ir.amd.com/ | VERIFIED (IR URL) |
| AVGO | **TO-VERIFY** | https://investors.broadcom.com/ | VERIFIED (IR URL) |
| TSM | **TO-VERIFY** | https://investor.tsmc.com/english | VERIFIED (IR URL) |
| ASML | **TO-VERIFY** | https://www.asml.com/en/investors | VERIFIED (IR URL) |

### C. Mag7 de seguimiento contextual, no automático (2 empresas)

| Ticker | CIK (verificar en SEC EDGAR) | Fuente oficial IR | Estado |
|---|---|---|---|
| AAPL | **TO-VERIFY** | https://investor.apple.com/ | VERIFIED (IR URL) |
| TSLA | **TO-VERIFY** | https://ir.tesla.com/ | VERIFIED (IR URL) |

**Total universo mínimo:** 11 empresas (9 norteamericanas, 2 extranjeras: TSM taiwanesa, ASML holandesa)

---

## 2. Formularios y campos a monitorear

Basado en `source_research_ai_markets.md` (sección 1.3, 1.4).

### 2.1 Formularios SEC por tipo de empresa

| Tipo de formulario | Propósito | Frecuencia | Aplicable a |
|---|---|---|---|
| **10-K** | Informe anual completo (capex, riesgo, segmentos, inventarios, concentración de clientes, exposición geográfica) | Anual | Todas las empresas norteamericanas |
| **10-Q** | Informe trimestral (capex, riesgos, segmentos, inventarios) | Trimestral | Todas las empresas norteamericanas |
| **8-K** | Informes de eventos actuales (earnings releases, cambios significativos) | Event-driven | Todas las empresas norteamericanas |
| **20-F** | Informe anual para empresas extranjeras (equivalente a 10-K) | Anual | TSM (Taiwán), ASML (Países Bajos) |
| **6-K** | Informes de eventos para empresas extranjeras (equivalente a 8-K) | Event-driven | TSM (Taiwán), ASML (Países Bajos) |

**NOTA:** TSM y ASML reportan en forma 20-F/6-K como empresas extranjeras. Los hyperscalers y compute companies reportan en 10-K/10-Q/8-K.

### 2.2 Campos duros (HARD fields) a extraer de cada formulario

De `source_research_ai_markets.md` (sección 1.3), traducido a campos estructurados:

| Campo | Fuente documental | Relevancia | Estado |
|---|---|---|---|
| **Capex total** | 10-K, 10-Q, 8-K earnings | Alta (driver principal de IA build-out) | VERIFIED (sección 1.3) |
| **Useful life de servidores/equipos** | 10-K, 10-Q | Alta (cambios contables afectan flujo de caja) | VERIFIED (sección 1.3, 1.4) |
| **Depreciation y amortization** | 10-K, 10-Q | Media (contexto para lectura de capex) | VERIFIED (sección 1.3) |
| **Inventory levels** | 10-K, 10-Q | Alta (lead times, restricciones de oferta en chips) | VERIFIED (sección 1.3, 1.4) |
| **Data center revenue** | 10-K, 10-Q, 8-K earnings | Alta (proxy directo de demanda AI/infra) | VERIFIED (sección 1.3, 1.4) |
| **Cloud growth metrics** | 8-K earnings, slides | Alta (Azure, AWS, Google Cloud) | VERIFIED (sección 1.3, 1.4) |
| **Backlog y bookings** | 8-K earnings, slides, transcript | Alta (visión futura de demanda) | VERIFIED (sección 1.3) |
| **Gross margin** | 10-K, 10-Q, 8-K earnings | Media (presión de precios, mix de producto) | VERIFIED (sección 1.3, 1.4) |
| **Customer concentration** | 10-K, 10-Q | Alta (hiperscalers como clientes clave de NVDA/AMD/AVGO/TSM) | VERIFIED (sección 1.3) |
| **Geographic revenue breakdown** | 10-K, 10-Q | Alta (China exposure, export controls impact) | VERIFIED (sección 1.3) |
| **Export controls / licencias / restricciones** | 10-K, 10-Q (risk factors), 8-K | Alta (impacto directo en revenue de chips avanzados) | VERIFIED (sección 1.3, 1.4) |
| **Guidance de capex** | 8-K earnings, transcript, slides | Muy alta (cambio en guía es señal primaria) | VERIFIED (sección 1.4) |
| **Lenguaje de demanda vs oferta** | 8-K earnings, transcript oficial ("demand exceeds supply", "normalizing supply") | Alta (indicador cualitativo de restricciones de oferta) | VERIFIED (sección 1.4) |
| **Productivity / workforce commentary** | 8-K earnings, transcript, shareholder letter | Media (productividad interna por IA) | VERIFIED (sección 1.3) |
| **AI revenue disclosures** | 8-K earnings, 10-K, transcript | Alta (monetización directa de IA) | VERIFIED (sección 1.3, 1.4) |
| **GPU / accelerator commentary** | 8-K earnings, transcript, slides | Alta (proxy de demanda AI en hardware) | VERIFIED (sección 1.3) |
| **TPU / custom silicon spend** | 8-K earnings, transcript (Alphabet específico) | Alta (internal capex en AI hardware) | VERIFIED (sección 1.3, 1.4) |

**NOTA:** Estos campos están explícitamente mencionados en el research doc. No hay campos inferidos.

---

## 3. Señales macro/sectoriales vs idiosincráticas

Basado en `source_research_ai_markets.md` (sección 1.4, 1.5, 6.1, 6.2).

### 3.1 Señales macro/sectoriales (deben ser prioridad del connector)

Estas señales afectan al complejo AI/chips/Mag7 como un bloque o tienen lectura macro:

| Señal macro/sectorial | Mecanismo | Documento fuente | Estado |
|---|---|---|---|
| **Cambio agregado en guidance de capex** de hyperscalers (MSFT, AMZN, GOOGL, META) | Indica si el boom AI se mantiene, acelera o frena a nivel sector | 8-K earnings, slides, transcript | VERIFIED (sección 1.4, 6.1) |
| **Comentario repetido de "demand exceeds supply"** en NVDA/AMD/TSM/ASML | Indica restricciones estructurales en oferta de chips avanzados | 8-K earnings, transcript oficial | VERIFIED (sección 1.4) |
| **Aceleración o freno de data center revenue** en NVDA/AMD/hiperscalers | Proxy directo de build-out de infra AI a nivel sector | 10-K, 10-Q, 8-K earnings | VERIFIED (sección 1.4) |
| **Agregado de cloud growth** (Azure, AWS, Google Cloud) | Indica demanda agregada de servicios AI | 8-K earnings, slides | VERIFIED (sección 1.4) |
| **Extension de vida util de servidores** (cambio contable) | Altera lectura de flujo de caja de capex a nivel sector | 10-K, 10-Q | VERIFIED (sección 1.4) |
| **Inventarios y lead times de chips avanzados** en NVDA/AMD/TSM | Indica si hay restricciones de oferta o normalización | 10-K, 10-Q, 8-K earnings | VERIFIED (sección 1.4) |
| **Packaging constraints** en semiconductores avanzados | Indica cuello de botella en la cadena de supply | 10-K, 10-Q, 8-K earnings | VERIFIED (sección 1.4) |
| **Menciones materiales a export controls** en filings | Indica riesgo geopolítico para oferta global de chips | 10-K, 10-Q (risk factors), 8-K | VERIFIED (sección 1.4, 6.1) |
| **Licencias o restricciones a China** (customer concentration) | Indica impacto en revenue de chips avanzados | 10-K, 10-Q, 8-K | VERIFIED (sección 1.4) |
| **Reglas BIS/Federal Register** nuevas para advanced computing | Shock macro a oferta de chips (fuente primaria: BIS, confirmación en filings) | BIS/Federal Register + confirmación en filings | VERIFIED (sección 4, 6.1) |
| **Evidence de mejora de productividad agregada** en BLS/BEA | Confirma si narrativa AI escala a macro | BLS/BEA (fuente primaria macro) | VERIFIED (sección 2.1, 2.3) |
| **Aceleración de private fixed investment** en BEA | Confirma si capex corporativo escala a cuentas nacionales | BEA (fuente primaria macro) | VERIFIED (sección 2.1, 2.3) |
| **Boom de construcción de data centers** en Census Construction Spending | Confirma si capex de hyperscalers se traduce en obra física | Census (fuente primaria macro) | VERIFIED (sección 2.1, 2.2) |

### 3.2 Señales idiosincráticas (evitar que el connector sea stock picker)

Estas señales son relevantes solo para una empresa, no para el reporte semanal macro:

| Señal idiosincrática | Razón para evitar prioridad alta | Documento fuente |
|---|---|---|
| **EPS beat/miss de una sola empresa** (ej. NVDA earnings) | Es resultado idiosincrático, no lectura macro | 8-K earnings |
| **Guidance de revenue de un solo hyperscaler** (ej. Azure Q3) | Afecta solo a una acción, no necesariamente al complejo | 8-K earnings |
| **Monetización de ads con AI en META específica** | Idiosincrático, no escala a macro | 8-K earnings, transcript |
| **Dojo/robotaxi commentary en TSLA** (sin impacto en riesgo amplio) | Idiosincrático, ruido | 8-K earnings, transcript |
| **Device cycle commentary en AAPL** | Idiosincrático, a menos que conecte con demanda de chips | 8-K earnings, transcript |
| **Partnership announcements sin montos** | No tiene canal económico claro | 8-K (si existe) |
| **Mejora marginal de margen de un solo nombre** | Idiosincrática | 10-K, 10-Q, 8-K earnings |

**NOTA:** Estas señales solo entran al reporte si afectan a más de un nombre o cambian la lectura macro (según sección 6.1 del research doc).

### 3.3 Regla operativa para el connector

El connector debe:
- **PRIORIZAR:** Señales macro/sectoriales del cuadro superior (capex agregado, restricciones de oferta, export controls, evidencia macro)
- **FILTRAR:** Señales idiosincráticas (single-name EPS, guidance sin impacto amplio)
- **SURFACE:** Patrones que se repiten en 2+ empresas (ej. "demand exceeds supply" en NVDA, AMD, TSM)
- **EVITAR:** Stock picking o recomendación de una sola acción

---

## 4. Conectores propuestos (para filings/campos confirmados)

Basado en `source_research_ai_markets.md`, se proponen conectores atómicos solo para información **VERIFICADA** en el research doc.

### 4.1 Connector 1: SEC EDGAR Full-Text Search para capex y keywords clave

**Fuente:** SEC EDGAR (efts.sec.gov / data.sec.gov)
**Tipo:** Full-text search sobre filings de las 11 empresas del universo

**Campos a extraer (VERIFIED):**
- "capital expenditures" / "capex" / "capital spending" en 10-K, 10-Q, 8-K
- "data center" / "cloud infrastructure" en 10-K, 10-Q, 8-K
- "demand exceeds supply" / "supply constraints" en 8-K earnings, transcript
- "export controls" / "license" / "China" en 10-K, 10-Q (risk factors), 8-K
- "useful life" / "depreciation" en 10-K, 10-Q

**Racionalización:**
- Capex y data center son drivers principales de AI build-out (sección 1.4)
- Lenguaje de oferta/demanda es señal cualitativa clave (sección 1.4)
- Export controls tienen impacto directo en revenue (sección 1.4, 6.1)
- Useful life afecta lectura de flujo de caja (sección 1.4)

**Salida esperada:**
- Tabla de capturas por empresa + filing + fecha + contexto (parrafo)
- Clasificación: cambio de capex, restricción de oferta, riesgo export controls

**Estado:** READY FOR IMPLEMENTATION (todos los campos están VERIFIED en research doc)

---

### 4.2 Connector 2: SEC EDGAR XBRL Facts para campos estructurados

**Fuente:** SEC Company Facts API (https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
**Tipo:** Facts estructurados XBRL por emisor

**Campos a extraer (VERIFIED):**
- Capital expenditures / Cash flow from investing activities
- Revenue por segmento (Data Center, Cloud, etc.) cuando el tagging ayuda
- Inventory levels
- Gross margin
- Customer concentration (cuando se reporta estructurado)

**Racionalización:**
- XBRL provee datos estructurados para capex, revenue, margins (sección 1.1)
- Permite agregación y comparación temporal (sección 1.1)
- Complementa full-text search con datos cuantitativos

**Salida esperada:**
- Series temporales de capex por empresa
- Segment revenue series (data center, cloud)
- Inventory y margin trends

**Estado:** READY FOR IMPLEMENTATION (campos estructurados están VERificados en sección 1.1)

---

### 4.3 Connector 3: EDGAR 8-K Earnings Release Parsing para guidance y commentary

**Fuente:** SEC EDGAR 8-K earnings releases + IR pages (si se permite parsing de slides/transcript)
**Tipo:** Parsing de earnings releases para extraer guidance y commentary cualitativo

**Campos a extraer (VERIFIED):**
- Capex guidance (guidance numérico o rangos)
- Cloud growth metrics (Azure, AWS, Google Cloud growth rates)
- Data center revenue growth
- Backlog y bookings (cuando se reportan)
- Lenguaje de demanda vs oferta (cualitativo)
- Export controls commentary (cualitativo)
- AI revenue disclosures (cuando se reportan)

**Racionalización:**
- Earnings releases son primera lectura rápida del quarter (sección 1.1)
- Guidance de capex es señal primaria (sección 1.4, 6.1)
- Cloud growth y data center revenue son proxies de demanda AI (sección 1.3, 1.4)

**Salida esperada:**
- Extracto de guidance numérico (capex, revenue, cloud growth)
- Extracto de lenguaje cualitativo (demand/supply, export controls)
- Clasificación: cambio de guía, nuevo commentary, sin cambios relevantes

**Estado:** READY FOR IMPLEMENTATION (campos están VERIFIED en sección 1.3, 1.4)

---

### 4.4 Connector 4: BIS/Federal Register para restricciones comerciales (fuente primaria macro)

**Fuente:** BIS (https://www.bis.gov/), Federal Register (https://www.federalregister.gov/)
**Tipo:** Full-text search de nuevas reglas export controls

**Campos a extraer (VERIFIED):**
- Nueva regla BIS para "advanced computing", "AI models", "semiconductor manufacturing items"
- Cambios en "Entity List" que toquen clientes, foundries, packaging, tooling
- Ampliación o relajación de licencias con efecto en revenue de NVDA/AMD/ASML/TSM/proveedores

**Racionalización:**
- BIS es punto de entrada principal para export controls de advanced computing y semiconductores (sección 4)
- Federal Register confirma vigencia exacta y alcance de la restricción (sección 4)
- Estas reglas son shocks macro a oferta global de chips (sección 4, 6.1)

**Salida esperada:**
- Lista de nuevas reglas con effective date, jurisdicción, producto afectado
- Clasificación: impacto en revenue de chips, impacto en hyperscalers, impacto en foundries

**Estado:** READY FOR IMPLEMENTATION (fuente VERIFIED en sección 4)

---

### 4.5 Connector 5: BLS/BEA/Census para validación macro (fuente primaria macro)

**Fuente:** BLS (https://www.bls.gov/productivity/), BEA (https://www.bea.gov/data/gdp/gross-domestic-product), Census Construction Spending (https://www.census.gov/construction/c30/current/index.html)
**Tipo:** Extracción de series temporales para validación macro

**Campos a extraer (VERIFIED):**
- Productivity: output per hour, unit labor costs (BLS)
- Private fixed investment, equipment, intellectual property products (BEA)
- Construction spending no residencial, específicamente data-center-linked proxies (Census)
- Manufacturers' new orders, shipments, inventories (Census M3)

**Racionalización:**
- BLS y BEA son confirmación lenta pero robusta de narrativa AI (sección 2.3)
- BEA Fixed Assets da contexto estructural de inversión por tipo de activo (sección 2.1)
- Census Construction Spending valida si capex de hyperscalers se traduce en obra física (sección 2.2)
- Census M3 ayuda a detectar si ciclo de equipo es genuino o solo restocking (sección 2.2)

**Salida esperada:**
- Series temporales de productividad, inversión privada, construcción, manufactura
- Clasificación: evidencia macro confirma, contradice o es neutral a narrativa AI

**Estado:** READY FOR IMPLEMENTATION (fuentes y campos VERIFIED en sección 2.1, 2.2)

---

### 4.6 Conectores DEFERIDOS (requieren verificación adicional)

**NO** proponer conectores para:
- Filing de una sola empresa sin impacto amplio (idiosincrático)
- Partnerships o announcements sin montos/económicos
- Rumores o noticias secundarias sin documento primario
- Stock price data (es proxy, no fuente primaria causal, según sección 5 del research doc)

---

## 5. Verificación: VERIFIED vs INFERRED

### 5.1 Items VERificados (están explícitamente en `source_research_ai_markets.md`)

| Categoría | Items VERIFIED | Referencia en research doc |
|---|---|---|
| **Empresas** | MSFT, AMZN, GOOGL, META, NVDA, AMD, AVGO, TSM, ASML, AAPL, TSLA (11 empresas) | Sección 1.2 |
| **IR URLs** | Todas las URLs de IR están listadas | Sección 1.2 |
| **Formularios SEC** | 10-K, 10-Q, 8-K, 20-F, 6-K | Sección 1.3 |
| **Campos duros** | Capex, useful life, depreciation, inventory, data center revenue, cloud growth, backlog, gross margin, customer concentration, geographic revenue, export controls, guidance, demanda vs oferta, productivity, AI revenue, GPU/accelerator, TPU/custom silicon | Sección 1.3, 1.4 |
| **Señales macro** | Guidance de capex, demanda excede oferta, data center revenue, cloud growth, useful life extension, inventarios/lead times, packaging constraints, export controls, licencias China, reglas BIS/Federal Register, productividad BLS/BEA, private fixed investment BEA, construcción de data centers Census | Sección 1.4, 2.1, 2.2, 4, 6.1 |
| **Fuentes oficiales** | SEC EDGAR, SEC Company Facts API, BIS, Federal Register, BLS, BEA, Census | Sección 1.1, 2.1, 4 |
| **Regla de filtrado** | Evitar stock picking, priorizar señales macro, filtrar idiosincráticas | Sección 1.5, 6.1, 6.2 |

### 5.2 Items INFERRED / TO-VERIFY (NO están en el research doc)

| Categoría | Items TO-VERIFY | Acción requerida |
|---|---|---|
| **CIKs** | TODOS los CIKs para las 11 empresas | Consultar SEC EDGAR para obtener CIKs por ticker |
| **Tickers exactos** | GOOGL vs GOOG (Alphabet puede tener múltiples clases) | Verificar ticker principal para filings SEC |
| **Formas legales** | Nombre legal exacto de cada empresa en SEC | Consultar SEC EDGAR para nombre legal |
| **Filing dates** | Calendario exacto de 10-K/10-Q por empresa | Consultar historial de filings en SEC EDGAR |
| **XBRL tagging coverage** | Qué campos están realmente taggeados en XBRL por empresa | Verificar en SEC Company Facts API por emisor |
| **Transcript availability** | Qué empresas ofrecen transcript oficial en IR | Verificar en cada IR page |
| **BIS Entity List coverage** | Qué empresas de la lista están en Entity List (actualmente o potencialmente) | Consultar BIS Entity List (https://www.bis.gov/entity-list) |

### 5.3 Items INFERRED (deducidos de contexto pero NO explícitos)

| Categoría | Items INFERRED | Racional |
|---|---|---|
| **Complejo AI/chips** | Agrupación de NVDA/AMD/AVGO/TSM/ASML + hyperscalers como "complejo AI/chips" | Deducido de sección 1.2 + 6.1 |
| **China exposure** | Asumir que todas las empresas de chips tienen exposure a China | Deducido de sección 1.4 (menciones a "China exposure" no específicas a una empresa) |
| **Export controls impact** | Asumir que export controls afectan principalmente a NVDA/AMD/ASML/TSM | Deducido de sección 4 (listado de empresas) |

---

## 6. Resumen ejecutivo

### 6.1 Hallazgos principales

1. **Universo mínimo:** 11 empresas (9 norteamericanas: MSFT, AMZN, GOOGL, META, NVDA, AMD, AVGO, AAPL, TSLA; 2 extranjeras: TSM taiwanesa, ASML holandesa)

2. **CIKs:** Ningún CIK está verificado en el research doc. TODOS deben obtenerse de SEC EDGAR.

3. **Formularios SEC:**
   - Empresas norteamericanas: 10-K, 10-Q, 8-K
   - Empresas extranjeras: 20-F, 6-K (TSM, ASML)

4. **Campos duros VERIFIED:** Capex, useful life, inventory, data center revenue, cloud growth, backlog, gross margin, customer concentration, geographic revenue, export controls, guidance, demanda vs oferta, productivity, AI revenue, GPU/accelerator, TPU/custom silicon

5. **Separación clara:** El connector debe surfacer señales macro/sectoriales (capex agregado, restricciones de oferta, export controls, evidencia macro) y evitar stock picking (idiosincrático EPS, guidance de un solo nombre).

6. **Conectores propuestos:** 5 conectores atómicos para fuentes y campos VERIFIED:
   - SEC EDGAR Full-Text Search (capex, keywords clave)
   - SEC EDGAR XBRL Facts (datos estructurados)
   - EDGAR 8-K Earnings Release Parsing (guidance y commentary)
   - BIS/Federal Register (restricciones comerciales)
   - BLS/BEA/Census (validación macro)

### 6.2 Acción inmediata requerida

Antes de implementar conectores:
1. **Obtener CIKs** de SEC EDGAR para las 11 empresas
2. **Verificar tickers exactos** (GOOGL vs GOOG, etc.)
3. **Confirmar nombre legal** de cada empresa en SEC
4. **Verificar XBRL tagging coverage** por empresa en SEC Company Facts API

### 6.3 Riesgos y limitaciones

- **Sin CIKs:** El connector no puede operar sin CIKs verificados
- **Sin XBRL tagging coverage:** Algunos campos pueden no estar taggeados estructuradamente
- **Sin transcript oficial:** Parsing de transcript puede requerir scraping de IR pages (diferente de SEC EDGAR)
- **Tasa de cambio de filings:** El connector debe manejar el volumen de filings sin hacer llamadas de red en tiempo real (no curl/wget/urllib según restricción)

---

## 7. Recomendaciones de implementación

### 7.1 Orden de implementación sugerido

1. **Fase 1 - Verificación de universe:** Obtener CIKs, nombres legales, tickers exactos, calendario de filings
2. **Fase 2 - SEC EDGAR Full-Text Search:** Implementar búsqueda de keywords clave en 10-K, 10-Q, 8-K
3. **Fase 3 - SEC EDGAR XBRL Facts:** Extraer datos estructurados de capex, revenue, margins, inventory
4. **Fase 4 - EDGAR 8-K Earnings Parsing:** Extraer guidance y commentary cualitativo
5. **Fase 5 - BIS/Federal Register:** Monitorear nuevas reglas export controls
6. **Fase 6 - BLS/BEA/Census:** Validar macro de productividad, inversión, construcción

### 7.2 Evitar scope creep

- NO incluir precios de mercado (es proxy, no fuente primaria)
- NO incluir análisis de una sola empresa sin impacto amplio
- NO incluir partnerships sin montos/económicos
- NO incluir rumores o noticias secundarias
- NO hacer stock picking

---

**Fin de documento de validación**