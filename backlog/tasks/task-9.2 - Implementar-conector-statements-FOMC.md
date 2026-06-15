---
id: TASK-9.2
title: Implementar conector statements FOMC
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
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
- [ ] #1 El conector normaliza statement FOMC con fecha, decision, target range, votos, texto y URL
- [ ] #2 Incluye fixtures/tests offline para HTML/PDF o texto representativo
- [ ] #3 Puede consumir URLs provistas por el calendario FOMC sin hacer discovery duplicado
<!-- AC:END -->
