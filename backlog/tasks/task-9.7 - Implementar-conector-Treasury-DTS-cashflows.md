---
id: TASK-9.7
title: Implementar conector Treasury DTS cashflows
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 13:19'
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
- [x] #1 El conector devuelve flujos diarios por categoria con fecha, tipo, monto y fuente
- [x] #2 Incluye fixtures/tests offline para JSON FiscalData
- [x] #3 Permite agregado semanal por categoria sin mezclar deposits y withdrawals
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added Treasury DTS cashflows connector (treasury_dts_cashflows) consuming FiscalData deposits_withdrawals_operating_cash into daily flows per category (record_date, transaction_type deposits/withdrawals, transaction_catg, amount_millions, fuente). AC#3: aggregate_cashflows_weekly_by_category() groups by ISO week and category keeping deposits and withdrawals SEPARATE (never netted) - covered by test. Hand-crafted FiscalData JSON fixture (10 obs) + offline tests (389->410). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
