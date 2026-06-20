---
id: TASK-9.11
title: Implementar conector FRED market proxies
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 23:51'
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
- [x] #1 El conector acepta una lista versionada de series FRED y devuelve observaciones normalizadas
- [x] #2 Incluye fixtures/tests offline para CSV fredgraph
- [x] #3 Cada serie queda marcada como primario o proxy segun el source research
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FRED market proxies connector (fred_market_proxies) - a generic FRED fredgraph CSV connector for market proxies (WTI/Brent crude, breakevens, real rates, broad dollar, liquidity proxy). AC#1: versioned DEFAULT_SERIES map of seriesID->{label,classification} + normalized observations (date, value, series_id, label). AC#2: hand-crafted fredgraph CSV fixtures (observation_date,VALUE) + recoverable-error tests. AC#3: each series classified primary vs proxy per source research (real rates/broad dollar=primary; WTI/Brent/breakevens/forward inflation=proxy), surfaced into item metadata. FRED_API_KEY optional (offline tests use FakeTransport). 29 offline tests (591->620). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
