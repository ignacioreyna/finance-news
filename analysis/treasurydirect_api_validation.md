# TreasuryDirect Auction API Validation

**Research date**: 2026-06-14  
**Validation date**: 2026-06-20  
**Research source**: `source_research_us_liquidity.md`  
**Validation scope**: Revalidate official TreasuryDirect announced/auctioned securities endpoints for auction calendar/results connector

---

## Endpoints quoted

### Announced securities endpoint

**URL (VERIFIED - quoted from research doc)**:
```
https://www.treasurydirect.gov/TA_WS/securities/announced?format=json
```

**Status**: INFERRED (endpoint documented but not verified via HTTP call)  
**Required parameters**: `format=json` (INFERRED - appears in URL)  
**Expected data**: Subastas anunciadas: tipo, CUSIP, auction date, issue date, maturity, offering amount (INFERRED - described in research doc)  
**Frequency**: Por anuncio (INFERRED - described as "por anuncio")  
**Format**: JSON (INFERRED - appears in URL as `?format=json`)

### Auctioned securities endpoint

**URL (VERIFIED - quoted from research doc)**:
```
https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json
```

**Status**: INFERRED (endpoint documented but not verified via HTTP call)  
**Required parameters**: `format=json` (INFERRED - appears in URL)  
**Expected data**: Resultados de subastas ya realizadas (INFERRED - described in research doc)  
**Frequency**: Por subasta (INFERRED - described as "por subasta")  
**Format**: JSON (INFERRED - appears in URL as `?format=json`)

### API documentation endpoint

**URL (VERIFIED - quoted from research doc)**:
```
https://www.treasurydirect.gov/webapis/webapisecurities.htm
```

**Status**: VERIFIED (documentation URL exists as reference)  
**Purpose**: Discovery y contrato de ingestion (VERIFIED - described in research doc)

---

## Campos y ejemplo de respuesta

### Announced securities - expected fields

Based on research doc description ("tipo, CUSIP, auction date, issue date, maturity, offering amount"):

**Expected fields (INFERRED)**:
- `securityType` or `type`: Tipo de seguridad (Bill, Note, Bond, TIPS, FRN)
- `cusip`: CUSIP identifier
- `auctionDate`: Fecha de subasta
- `issueDate`: Fecha de emision
- `maturityDate`: Fecha de vencimiento
- `offeringAmount`: Monto ofertado (en millones de USD)
- `securityTerm`: Duracion (ej: 2-Year, 10-Year, 30-Year)

**Reconstructed example (INFERRED - not from actual API response)**:
```json
{
  "announcedSecurities": [
    {
      "securityType": "Note",
      "cusip": "91282CAZ5",
      "auctionDate": "2026-06-22",
      "issueDate": "2026-06-30",
      "maturityDate": "2028-06-30",
      "offeringAmount": 54000,
      "securityTerm": "2-Year"
    },
    {
      "securityType": "Bill",
      "cusip": "912797KZ0",
      "auctionDate": "2026-06-23",
      "issueDate": "2026-06-26",
      "maturityDate": "2026-09-25",
      "offeringAmount": 75000,
      "securityTerm": "13-Week"
    }
  ]
}
```

### Auctioned securities - expected fields

Based on research doc description ("tails, bid-to-cover, awards, tasas"):

**Expected fields (INFERRED)**:
- `securityType` or `type`: Tipo de seguridad
- `cusip`: CUSIP identifier
- `auctionDate`: Fecha de subasta
- `issueDate`: Fecha de emision
- `maturityDate`: Fecha de vencimiento
- `offeringAmount`: Monto ofertado
- `acceptedAmount`: Monto aceptado
- `highRate`: Tasa alta de aceptacion (yield)
- `lowRate`: Tasa baja de aceptacion
- `medianRate`: Tasa media
- `bidToCoverRatio`: Ratio de cobertura
- `percentAwardsAtHigh`: Porcentaje adjudicado a tasa alta
- `securityTerm`: Duracion

**Reconstructed example (INFERRED - not from actual API response)**:
```json
{
  "auctionedSecurities": [
    {
      "securityType": "Note",
      "cusip": "91282CAX8",
      "auctionDate": "2026-06-15",
      "issueDate": "2026-06-22",
      "maturityDate": "2028-06-30",
      "offeringAmount": 54000,
      "acceptedAmount": 54000,
      "highRate": 4.650,
      "lowRate": 4.620,
      "medianRate": 4.635,
      "bidToCoverRatio": 2.45,
      "percentAwardsAtHigh": 18.5,
      "securityTerm": "2-Year"
    }
  ]
}
```

---

## Cobertura announced vs auctioned

### Announced securities endpoint

**Coverage (INFERRED - based on description)**:
- Proporciona: Calendario operativo de issuance
- Incluye: Todas las subastas anunciadas por el Tesoro
- Tipo de datos: Forward-looking (futuro)
- Periodo cubierto: Desde fecha actual hasta varios meses adelante
- Instrumentos: Bills, Notes, Bonds, TIPS, FRN (segun se anuncien)
- Valor agregado: Planificacion de liquidez, calendar settlements

**Limitaciones (INFERRED)**:
- No incluye resultados de subastas pasadas
- No confirma montos definitivos (pueden cambiar hasta la subasta)
- No provee bid-to-cover ni tasas reales
- Puede tener cambios si se modifican programas de emision

### Auctioned securities endpoint

**Coverage (INFERRED - based on description)**:
- Proporciona: Resultados de subastas ya realizadas
- Incluye: tails, bid-to-cover, awards, tasas
- Tipo de datos: Historical (pasado)
- Periodo cubierto: Historial completo de subastas
- Instrumentos: Bills, Notes, Bonds, TIPS, FRN (segun se hayan realizado)
- Valor agregado: Analisis de demanda de Treasury, term premium, liquidez post-settlement

**Limitaciones (INFERRED)**:
- No incluye subastas futuras (calendar)
- Puede no tener data en tiempo real para subastas muy recientes
- No refleja cambios de politica de emision

### Refunding pages

**Refunding statement (VERIFIED - URL quoted from research doc)**:
```
https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding
```

**Coverage (INFERRED - based on description)**:
- Proporciona: Refunding statement, presentation, financing estimates, borrowing needs
- Frecuencia: Trimestral, con updates intra-trimestre si aplica
- Formato: HTML, PDF
- Tipo: Documental (no estructurado)
- Valor agregado: Estrategia de financiamiento, guidance de cupones/bills, impacto esperado en liquidez
- Diferencia clave: Incluye contexto cualitativo y cambios de estrategia que no estan en los endpoints JSON

**Gap identificado (INFERRED)**:
- Los endpoints TreasuryDirect no reemplazan la necesidad de guardar el texto del `Quarterly Refunding Statement`
- El refunding statement contiene cambios de estrategia que afectan term premium y no estan estructurados en el API
- Necesario conectar scraping/document processing para capturar guidance cualitativo

### Gaps de cobertura

**1. Timing gap (INFERRED)**:
- `announced`: Subastas futuras pero sin resultados
- `auctioned`: Resultados pasados pero sin calendar
- Gap: Subastas recientes que ya ocurrieron pero cuyos resultados aun no estan disponibles en `auctioned`

**2. Strategy gap (INFERRED)**:
- `announced`/`auctioned`: Datos numericos de subastas
- `quarterly-refunding`: Estrategia de financiamiento y borrowing estimates
- Gap: Faltan datos cualitativos de politica y guidance de emision

**3. Operational gap (INFERRED)**:
- `announced`/`auctioned`: No informan sobre cambios de metodologia
- `quarterly-refunding`: Puede incluir cambios en cupones, bills composition, etc.
- Gap: Sin cruzar ambos sources, no se detectan cambios estructurales en el programa de emision

---

## Implementacion

### GO/NO-GO verdict

**DECISION**: NO-GO - DEFER UNTIL VERIFICATION

**Rationale**:
1. **Endpoint contract NOT verified**: El research doc explicitamente states "no se pudo verificar por expansion de `zsh` en el comando local; tratarlo como oficial pero revalidar con URL quoted o cliente HTTP en el conector"
2. **No actual API response samples**: Todos los ejemplos de respuesta son RECONSTRUCTED/INFERRED, no de llamadas reales
3. **Field names INFERRED**: Los nombres de campos (`cusip`, `auctionDate`, etc.) son deducidos de la descripcion, no verificados en el API
4. **Format uncertainty**: Aunque la URL incluye `?format=json`, no hay confirmacion de que el JSON sea parseable o estable

**Required for GO**:
1. Verificar que `https://www.treasurydirect.gov/TA_WS/securities/announced?format=json` devuelve JSON parseable
2. Verificar que `https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json` devuelve JSON parseable
3. Documentar nombres exactos de campos (case-sensitive) desde una respuesta real
4. Confirmar que no requiere autenticacion o headers especiales
5. Validar que la frecuencia y cobertura descritas coinciden con datos reales

### Proposed implementation task (DEFERRED)

**Task name (provisional)**: `treasury_auction_calendar_connector`

**Proposed scope** (ONLY after verification):
- Fuente: TreasuryDirect announced/auctioned securities API
- Output: auction date, settlement, maturity, CUSIP, amount, result metrics (tails, bid-to-cover, awards, tasas)
- Tipo: primario
- Integration: Cruzar con quarterly refunding pages para contexto cualitativo

**Pre-requisites**:
1. Verification task completed with actual HTTP responses
2. Schema definition basada en campos reales del API
3. Error handling documentado para casos de cambio de formato

**NOTA**: No crear esta tarea hasta completar verificacion con llamadas HTTP reales fuera del sandbox del agente.

---

## Verificacion

### Items VERIFIED

| Item | Status | Evidence |
| --- | --- | --- |
| URL announced endpoint | VERIFIED | Quoted from research doc: `https://www.treasurydirect.gov/TA_WS/securities/announced?format=json` |
| URL auctioned endpoint | VERIFIED | Quoted from research doc: `https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json` |
| URL API docs | VERIFIED | Quoted from research doc: `https://www.treasurydirect.gov/webapis/webapisecurities.htm` |
| URL quarterly refunding | VERIFIED | Quoted from research doc: `https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding` |
| Research note on verification failure | VERIFIED | Research doc line 55: "En esta pasada el endpoint TreasuryDirect con `?format=json` no se pudo verificar por expansion de `zsh` en el comando local" |
| Need for HTTP client verification | VERIFIED | Research doc line 55: "tratarlo como oficial pero revalidar con URL quoted o cliente HTTP en el conector" |
| Refunding statement importance | VERIFIED | Research doc line 57: "Para refunding, no alcanza con datos de subasta: guardar tambien el texto del `Quarterly Refunding Statement`" |

### Items INFERRED

| Item | Status | Evidence |
| --- | --- | --- |
| Endpoint works with `?format=json` | INFERRED | URL includes parameter, but not tested via HTTP call |
| Endpoint returns JSON | INFERRED | URL implies JSON format, but not verified |
| Field: `securityType` | INFERRED | Described as "tipo" in research doc, field name deduced |
| Field: `cusip` | INFERRED | Described as "CUSIP" in research doc, field name deduced |
| Field: `auctionDate` | INFERRED | Described as "auction date" in research doc, field name deduced |
| Field: `issueDate` | INFERRED | Described as "issue date" in research doc, field name deduced |
| Field: `maturityDate` | INFERRED | Described as "maturity" in research doc, field name deduced |
| Field: `offeringAmount` | INFERRED | Described as "offering amount" in research doc, field name deduced |
| Field: `highRate` | INFERRED | Described as "tasas" in research doc, field name deduced |
| Field: `bidToCoverRatio` | INFERRED | Described as "bid-to-cover" in research doc, field name deduced |
| Announced covers forward-looking auctions | INFERRED | Described as "subastas anunciadas" in research doc |
| Auctioned covers historical results | INFERRED | Described as "resultados de subastas ya realizadas" in research doc |
| Frequency: por anuncio / por subasta | INFERRED | Described in research doc |
| No authentication required | INFERRED | Research doc does not mention auth, but not verified |
| API response format stability | INFERRED | No historical data available to confirm |

### Items NOT DOCUMENTED

| Item | Status | Gap |
| --- | --- | --- |
| Actual JSON response structure | NOT VERIFIED | No real response sample available |
| Exact field names (case-sensitive) | NOT VERIFIED | Names are guessed/inferred |
| Array structure (top-level key?) | NOT VERIFIED | Unknown if response has wrapper key |
| Pagination/limit parameters | NOT VERIFIED | Not mentioned in research doc |
| Date formats (YYYY-MM-DD, etc.) | NOT VERIFIED | Assumed format not confirmed |
| Currency units for amounts | NOT VERIFIED | Assumed millions of USD |
| Error response format | NOT VERIFIED | Not documented |
| Rate availability for all auctions | NOT VERIFIED | Not clear if all fields always present |
| CUSIP format validation | NOT VERIFIED | Not documented |
| Security type values enum | NOT VERIFIED | Unknown exact values (Bill vs bill, etc.) |

### Risk assessment

**High risk items**:
1. Field name accuracy: Si los nombres reales difieren de los inferidos, el parser fallara
2. JSON structure: Si el response tiene un wrapper desconocido, el parser fallara
3. Availability: No se puede confirmar que los endpoints esten activos hoy

**Medium risk items**:
1. Frequency updates: No se sabe con que frecuencia se actualizan los endpoints
2. Coverage gaps: No se puede confirmar que cubran todas las subastas
3. Rate limiting: No se menciona, pero podria existir

**Low risk items**:
1. Documentation: La URL de docs existe y puede consultarse
2. Refunding integration: La estrategia esta clara en el research doc

---

## Recomendaciones

### Para proxima fase (verification)

1. **Ejecutar verificacion fuera del sandbox**:
   - Usar `curl` o HTTP client con URLs quoted para evitar expansion de shell
   - Capturar respuestas reales de ambos endpoints
   - Documentar respuesta exitosa y errores potenciales

2. **Validar contrato del API**:
   - Confirmar estructura JSON exacta (wrapper keys, array paths)
   - Listar todos los campos presentes en una respuesta real
   - Verificar tipos de datos (string, number, date formats)
   - Casos borde: auctions con datos faltantes, cambios de programa

3. **Revisar documentacion oficial**:
   - Navegar a `https://www.treasurydirect.gov/webapis/webapisecurities.htm`
   - Buscar cambios de version o deprecation notices
   - Documentar cualquier parametro adicional no mencionado en el research doc

4. **Crear task de implementacion**:
   - Solo despues de verificar endpoints con HTTP calls exitosos
   - Usar nombres de campos exactos del API real (no inferidos)
   - Incluir schema validation en el conector
   - Considerar fallback a FiscalData API si TreasuryDirect falla

### Para arquitectura del conector

1. **Schema-driven parsing**: Definir schema explicito basado en campos reales
2. **Error handling**: Capturar y loguear respuestas inesperadas del API
3. **Monitoring**: Verificar disponibilidad de endpoints y alertar sobre cambios
4. **Cross-reference**: Integrar con quarterly refunding para detectar cambios de estrategia
5. **Data quality**: Validar CUSIPs, fechas y montos antes de ingestar

---

## Conclusion

El research doc proporciona URLs bien definidas y contexto de uso claro para los endpoints de TreasuryDirect. Sin embargo, la falta de verificacion HTTP (debido a un problema tecnico local) significa que el contrato exacto del API (nombres de campos, estructura JSON, etc.) permanece INFERRED y no VERIFIED.

Recomendacion: NO proceder con implementacion hasta completar verificacion con llamadas HTTP reales. El endpoint contract debe ser confirmado con respuestas reales antes de crear la tarea de implementacion `treasury_auction_calendar_connector`.