---
id: TASK-8.13
title: Implementar conector calendario publicaciones INDEC
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
labels:
  - argentina
  - indec
  - calendar
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_indec.md
parent_task_id: TASK-8
priority: medium
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir calendario oficial INDEC para anticipar releases de IPC, EMAE, EPH, salarios, canastas y pobreza.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve eventos de publicacion con fecha, dataset, titulo y fuente
- [ ] #2 Incluye fixtures/tests offline para HTML/JSON/PDF segun fuente confirmada
- [ ] #3 Permite filtrar eventos relevantes al reporte semanal
<!-- AC:END -->
