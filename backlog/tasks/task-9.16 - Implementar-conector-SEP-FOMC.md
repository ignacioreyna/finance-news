---
id: TASK-9.16
title: Implementar conector SEP FOMC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:48'
updated_date: '2026-06-20 18:50'
labels:
  - international
  - fed
  - fomc
  - sep
  - connectors
  - model-medium
dependencies:
  - TASK-9.1
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: medium
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir projection materials en reuniones FOMC con SEP y extraer medianas de GDP, unemployment, PCE, core PCE y fed funds cuando el formato lo permita.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector identifica reuniones con SEP y devuelve proyecciones normalizadas por variable/horizonte
- [x] #2 Incluye fixtures/tests offline para material SEP representativo
- [x] #3 Marca limitaciones si dots/dispersión requieren parsing manual o PDF complejo
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FOMC SEP connector (fomc_sep) parsing SEP projection materials (CSV medians table for reliability) into normalized projections keyed by variable (GDP/unemployment/PCE/core PCE/fed funds) x horizon (current year/+1/+2/longer-run): 20 projections per SEP meeting, grouped into one SourceItem per meeting with has_sep flag. AC#3: DOTS_LIMITATION module constant documents that individual participant dots/dispersion (dot plot) require manual/complex PDF parsing and are NOT extracted here - only the medians table; covered by test. Hand-crafted CSV fixture + 31 offline tests (486->517). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
