---
id: TASK-5.4
title: Investigar fuentes commodities y geoeconomia
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 23:46'
labels:
  - international
  - commodities
  - geopolitics
  - research
  - model-large
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-5
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Identificar fuentes para Brent/WTI, oro, DXY, breakevens, energia, OPEP y eventos geoeconomicos relevantes al criterio del host. Modelo recomendado: large.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_commodities_geo.md con fuentes disponibles y limitaciones
- [x] #2 Separar datos de precio, datos oficiales de energia y tracking de eventos
- [x] #3 Proponer un minimo viable semanal sin proveedores pagos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar host_profile, source_catalog y research internacional existente.
2. Investigar fuentes para Brent/WTI, oro, DXY, breakevens, energia, OPEP y eventos geoeconomicos.
3. Crear analysis/source_research_commodities_geo.md separando precios, datos oficiales de energia y tracking de eventos.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Created analysis/source_research_commodities_geo.md with a sourced catalog for Brent/WTI, gold, DXY, breakevens, official energy data, OPEC/IEA context, and geoeconomic event tracking.

- Separated market price data, official energy data, and event tracking into independent sections, with source type and limitations for each.

- Added a no-paid-provider weekly MVP using FRED, EIA, OPEC public pages, Stooq proxies, and official event sources.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created a commodities and geoeconomics source research note for the weekly finance-news pipeline.

Changes:
- Added analysis/source_research_commodities_geo.md with concrete URLs, frequency, format, source type, usage, and limitations.
- Separated market prices, official energy data, OPEC/IEA context, and geoeconomic event tracking.
- Proposed a minimum viable weekly workflow using free sources only, with clear proxy labeling for DXY and gold.

Verification:
- Reviewed TASK-5.4 and local reference files.
- Checked the resulting markdown for the required acceptance criteria.
<!-- SECTION:FINAL_SUMMARY:END -->
