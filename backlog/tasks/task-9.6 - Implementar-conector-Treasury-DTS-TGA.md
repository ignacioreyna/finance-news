---
id: TASK-9.6
title: Implementar conector Treasury DTS TGA
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
labels:
  - international
  - treasury
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir FiscalData Daily Treasury Statement operating_cash_balance para TGA diaria y cambios diario/semanal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve TGA Federal Reserve Account con fecha, open/close balance y cambio diario
- [ ] #2 Incluye fixtures/tests offline para JSON FiscalData
- [ ] #3 Define freshness diaria y manejo de dias no habiles federales
<!-- AC:END -->
