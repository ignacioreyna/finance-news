---
id: TASK-8.12
title: Implementar conector BCRA balance cambiario mensual
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
labels:
  - argentina
  - bcra
  - fx
  - balance-cambiario
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: medium
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir Evolucion del Mercado de Cambios y Balance Cambiario del BCRA para compras/ventas agregadas y rubros cambiarios mensuales.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones mensuales por rubro con periodo, monto, unidad y fuente
- [ ] #2 Incluye fixtures/tests offline para descarga machine-readable identificada
- [ ] #3 Documenta explicitamente que no reemplaza intervencion diaria neta
<!-- AC:END -->
