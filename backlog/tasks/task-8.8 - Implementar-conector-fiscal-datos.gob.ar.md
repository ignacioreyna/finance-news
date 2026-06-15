---
id: TASK-8.8
title: Implementar conector fiscal datos.gob.ar
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
labels:
  - argentina
  - fiscal
  - tesoro
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_tesoro.md
parent_task_id: TASK-8
priority: medium
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir series fiscales oficiales desde datos.gob.ar/Mecon para resultado primario, financiero y componentes mensuales relevantes al reporte.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones fiscales mensuales normalizadas con periodo, concepto, valor, unidad y fuente
- [ ] #2 Incluye fixtures/tests offline para JSON/CSV de datos.gob.ar
- [ ] #3 Documenta base caja/devengado segun la fuente usada
<!-- AC:END -->
