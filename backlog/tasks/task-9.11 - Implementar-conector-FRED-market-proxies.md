---
id: TASK-9.11
title: Implementar conector FRED market proxies
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
labels:
  - international
  - fred
  - market-data
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
  - analysis/source_research_commodities_geo.md
parent_task_id: TASK-9
priority: medium
ordinal: 55000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear conector generico FRED CSV para proxies de mercado usados en liquidez, commodities y reporte semanal: WTI, Brent, breakevens, tasas reales, broad dollar y liquidez proxy.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector acepta una lista versionada de series FRED y devuelve observaciones normalizadas
- [ ] #2 Incluye fixtures/tests offline para CSV fredgraph
- [ ] #3 Cada serie queda marcada como primario o proxy segun el source research
<!-- AC:END -->
