---
id: TASK-8.11
title: Implementar conector BCRA variables monetarias y reservas
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
labels:
  - argentina
  - bcra
  - reserves
  - monetary
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: high
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir fuentes oficiales BCRA para reservas, base monetaria, agregados y variables monetarias relevantes al tablero Argentina.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve series normalizadas con fecha, valor, unidad, frecuencia y fuente
- [ ] #2 Incluye fixtures/tests offline para payload API/descarga oficial
- [ ] #3 Excluye intervencion diaria neta si no hay fuente oficial diaria identificada
<!-- AC:END -->
