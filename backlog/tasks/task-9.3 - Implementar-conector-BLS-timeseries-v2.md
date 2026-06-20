---
id: TASK-9.3
title: Implementar conector BLS timeseries v2
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-20 23:51'
labels:
  - international
  - bls
  - macro
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_macro.md
parent_task_id: TASK-9
priority: high
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear cliente/conector para BLS Public Data API v2 que cubra el set minimo semanal: CPI, payrolls, unemployment, AHE y JOLTS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector acepta una lista versionada de series IDs y devuelve observaciones normalizadas
- [x] #2 Incluye fixtures/tests offline para respuesta JSON BLS y errores recuperables
- [x] #3 Soporta registrationkey opcional sin exigirla en tests
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added BLS timeseries v2 connector (bls_timeseries) for the BLS Public Data API v2 covering the minimum weekly set (CPI, payrolls, unemployment, AHE, JOLTS) via a versioned DEFAULT_SERIES list + cursor selection. Parses BLS v2 JSON ({Results:{series:[{seriesID,data:[{year,period,periodName,value}]}]}}) into normalized observations (date from year+period, value, periodName). AC#2: hand-crafted success/not_found/empty JSON fixtures + recoverable-error tests (5xx→RecoverableConnectorError, 4xx→ValueError, NOT_FOUND status handled). AC#3: registration key OPTIONAL (read from os.environ BLS_API_KEY only in live fetch; tests run with NO key; one test sets a key and asserts it is included in the request). 33 offline tests (591->624). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
