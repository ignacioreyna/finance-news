---
id: TASK-9.9
title: Implementar conector Fed H41 liquidity
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 13:19'
labels:
  - international
  - fed
  - h41
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir Federal Reserve H.4.1 Data Download para snapshot semanal de reservas, TGA, ON RRP, securities held outright y total assets.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve observaciones semanales H.4.1 normalizadas por serie clave
- [x] #2 Incluye fixtures/tests offline para CSV/XML o payload descargado
- [x] #3 Documenta diferencias de frecuencia frente a FiscalData DTS
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added Fed H41 liquidity connector (fed_h41_liquidity) consuming the Federal Reserve H.4.1 Data Download (CSV) into weekly observations keyed by series (total assets, securities held outright, ON RRP, TGA/earned remuneration, reserves). AC#3: module-level documentation of frequency difference vs FiscalData DTS (H.4.1 is weekly/as-of-Wednesday; DTS is daily) - covered by test. Hand-crafted CSV fixture + offline tests (389->415). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
