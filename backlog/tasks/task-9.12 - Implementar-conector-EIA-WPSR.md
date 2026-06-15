---
id: TASK-9.12
title: Implementar conector EIA WPSR
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
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
- [ ] #1 El conector devuelve datos semanales normalizados con week ending, release date, serie y valor
- [ ] #2 Incluye fixtures/tests offline para tablas CSV/HTML de EIA WPSR
- [ ] #3 Calcula variacion semanal para crude stocks, Cushing, gasoline, distillates y produccion
<!-- AC:END -->
