---
id: TASK-9.7
title: Implementar conector Treasury DTS cashflows
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
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
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir FiscalData deposits_withdrawals_operating_cash para explicar movimientos de TGA por impuestos, gasto, deuda y otras categorias.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve flujos diarios por categoria con fecha, tipo, monto y fuente
- [ ] #2 Incluye fixtures/tests offline para JSON FiscalData
- [ ] #3 Permite agregado semanal por categoria sin mezclar deposits y withdrawals
<!-- AC:END -->
