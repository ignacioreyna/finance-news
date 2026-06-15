---
id: TASK-9.1
title: Implementar conector calendario FOMC
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
labels:
  - international
  - fed
  - fomc
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: high
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir el calendario oficial FOMC y producir una fila por reunion con links a statement, minutes, SEP, implementation note y press conference cuando existan.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve reuniones normalizadas con fecha, tipo, URLs hijas y source_url
- [ ] #2 Incluye fixtures/tests offline para parsing del calendario oficial
- [ ] #3 Marca reuniones con SEP y eventos faltantes sin romper la corrida
<!-- AC:END -->
