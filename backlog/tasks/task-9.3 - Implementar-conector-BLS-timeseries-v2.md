---
id: TASK-9.3
title: Implementar conector BLS timeseries v2
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
labels:
  - international
  - bls
  - macro
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_macro.md
parent_task_id: TASK-9
priority: high
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear cliente/conector para BLS Public Data API v2 que cubra el set minimo semanal: CPI, payrolls, unemployment, AHE y JOLTS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector acepta una lista versionada de series IDs y devuelve observaciones normalizadas
- [ ] #2 Incluye fixtures/tests offline para respuesta JSON BLS y errores recuperables
- [ ] #3 Soporta registrationkey opcional sin exigirla en tests
<!-- AC:END -->
