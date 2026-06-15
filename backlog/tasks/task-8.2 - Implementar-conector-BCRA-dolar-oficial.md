---
id: TASK-8.2
title: Implementar conector BCRA dolar oficial
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
labels:
  - argentina
  - bcra
  - fx
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-8
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir la fuente oficial BCRA para dolar oficial/A3500 y entregar serie normalizada para el reporte semanal y calculos cambiarios.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones normalizadas de dolar oficial/A3500 con fecha, valor, source_url y metadata
- [ ] #2 Incluye fixtures/tests offline para parsing y serializacion
- [ ] #3 Define freshness diaria y fallback si la API oficial no responde
<!-- AC:END -->
