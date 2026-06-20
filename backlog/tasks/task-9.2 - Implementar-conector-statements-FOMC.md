---
id: TASK-9.2
title: Implementar conector statements FOMC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-20 13:19'
labels:
  - international
  - fed
  - fomc
  - connectors
  - model-medium
dependencies:
  - TASK-9.1
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: high
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir statements oficiales FOMC por reunion y extraer decision, rango objetivo, votos, cuerpo limpio y flags de cambio de lenguaje.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector normaliza statement FOMC con fecha, decision, target range, votos, texto y URL
- [x] #2 Incluye fixtures/tests offline para HTML/PDF o texto representativo
- [x] #3 Puede consumir URLs provistas por el calendario FOMC sin hacer discovery duplicado
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FOMC statements connector (fomc_statements) that consumes a single FOMC statement URL (passed as cursor, supplied by fomc_calendario - no duplicate calendar discovery per AC#3) and parses the press-release HTML via stdlib HTMLParser into date, decision (raise/cut/hold via keyword classification), target range (fraction-range regex), votes (for/against regex), clean body text, and source_url. Hand-crafted HTML fixture + offline tests (389->411). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
