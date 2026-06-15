---
id: TASK-8.14
title: Implementar conector calendario publicaciones BCRA
status: To Do
assignee: []
created_date: '2026-06-15 02:48'
labels:
  - argentina
  - bcra
  - calendar
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: medium
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir calendario oficial de informes BCRA para programar expectativas de Informe Monetario Diario/Mensual, Boletin Estadistico, Balance Cambiario, REM e IPOM.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve eventos de publicacion BCRA con fecha, informe, frecuencia y fuente
- [ ] #2 Incluye fixtures/tests offline para parsing del calendario
- [ ] #3 Se integra con metadata de freshness para scheduling posterior
<!-- AC:END -->
