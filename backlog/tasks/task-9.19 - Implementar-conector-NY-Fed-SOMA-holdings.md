---
id: TASK-9.19
title: Implementar conector NY Fed SOMA holdings
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:49'
updated_date: '2026-06-20 23:51'
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
- [x] #1 El conector devuelve holdings normalizados por fecha, instrumento, vencimiento/bucket y monto
- [x] #2 Incluye fixtures/tests offline para archivo/API SOMA
- [x] #3 Permite calcular cambios semanales o mensuales para reporte de QT
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added NY Fed SOMA holdings connector (nyfed_soma) consuming SOMA holdings (CSV) into normalized holdings by as_of_date, instrument (Treasuries/MBS/Agency Debt), maturity_bucket, amount_par, amount_market. AC#3: compute_weekly_monthly_changes() helper computes per-instrument delta (change_par/change_market) between two as-of dates for the QT report (QT=decline in total securities held); handles missing prior/current dates gracefully. Hand-crafted CSV fixture (2 dates x 3 instruments x 6 buckets, showing QT runoff) + recoverable-error tests. 16 offline tests (591->607). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
