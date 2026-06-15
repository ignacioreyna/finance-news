---
id: TASK-9.8
title: Implementar conector NY Fed SOFR
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
labels:
  - international
  - nyfed
  - sofr
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir NY Fed Markets API para SOFR, volumen y percentiles como indicador de funding secured.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve SOFR, volumen y percentiles con effectiveDate y source_url
- [ ] #2 Incluye fixtures/tests offline para JSON de NY Fed
- [ ] #3 Marca SOFR como dato primario y FRED SOFR solo como proxy/fallback
<!-- AC:END -->
