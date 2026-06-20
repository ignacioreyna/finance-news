---
id: TASK-9.12
title: Implementar conector EIA WPSR
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 23:51'
labels:
  - international
  - eia
  - energy
  - commodities
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_commodities_geo.md
parent_task_id: TASK-9
priority: medium
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir Weekly Petroleum Status Report de EIA para stocks, Cushing, productos, produccion e import/export de energia.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve datos semanales normalizados con week ending, release date, serie y valor
- [x] #2 Incluye fixtures/tests offline para tablas CSV/HTML de EIA WPSR
- [x] #3 Calcula variacion semanal para crude stocks, Cushing, gasoline, distillates y produccion
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added EIA WPSR connector (eia_wpsr) consuming the EIA Weekly Petroleum Status Report (CSV) into weekly observations with week_ending, release_date, series_name, value (crude stocks, Cushing, gasoline, distillates, production, refinery utilization, product supplied). AC#3: compute_weekly_variation() computes delta vs prior week for the 5 key series (crude, Cushing, gasoline, distillates, production), first week delta=None, surfaced into item metadata.weekly_variation. Hand-crafted CSV fixture (5 weeks x 7 series) + recoverable-error tests. EIA_API_KEY optional (offline FakeTransport). 22 offline tests (591->613). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
