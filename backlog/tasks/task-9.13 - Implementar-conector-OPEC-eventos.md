---
id: TASK-9.13
title: Implementar conector OPEC eventos
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 18:49'
labels:
  - international
  - opec
  - energy
  - geopolitics
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_commodities_geo.md
parent_task_id: TASK-9
priority: medium
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir press releases/MOMR publicos de OPEC para decisiones, cuotas, recortes o aumentos relevantes al reporte semanal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve eventos OPEC con meeting_date, decision, paises afectados, effective_date y URL
- [x] #2 Incluye fixtures/tests offline para press release y/o tabla publica
- [x] #3 Marca limitaciones si MOMR completo no esta disponible gratis
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added OPEC eventos connector (opec_eventos) parsing OPEC press releases (opec.org HTML via stdlib HTMLParser with div-depth tracking) into events with meeting_date, decision, affected_countries, effective_date, event_url. AC#3: module docstring documents the full MOMR (Monthly Oil Market Report) is NOT freely available (paid/restricted) - only press releases/public tables are processed; covered by test. Hand-crafted HTML fixture (3 events) + offline tests (486->502). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
