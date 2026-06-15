---
id: TASK-9.19
title: Implementar conector NY Fed SOMA holdings
status: To Do
assignee: []
created_date: '2026-06-15 02:49'
labels:
  - international
  - nyfed
  - soma
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: medium
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir holdings SOMA de NY Fed para composicion por instrumento, maturity buckets y cambios relevantes para QT.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve holdings normalizados por fecha, instrumento, vencimiento/bucket y monto
- [ ] #2 Incluye fixtures/tests offline para archivo/API SOMA
- [ ] #3 Permite calcular cambios semanales o mensuales para reporte de QT
<!-- AC:END -->
