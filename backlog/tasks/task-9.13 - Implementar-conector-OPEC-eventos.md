---
id: TASK-9.13
title: Implementar conector OPEC eventos
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
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
- [ ] #1 El conector devuelve eventos OPEC con meeting_date, decision, paises afectados, effective_date y URL
- [ ] #2 Incluye fixtures/tests offline para press release y/o tabla publica
- [ ] #3 Marca limitaciones si MOMR completo no esta disponible gratis
<!-- AC:END -->
