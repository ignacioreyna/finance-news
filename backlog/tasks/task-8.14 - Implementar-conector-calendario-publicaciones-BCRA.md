---
id: TASK-8.14
title: Implementar conector calendario publicaciones BCRA
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:48'
updated_date: '2026-06-16 01:37'
labels:
  - argentina
  - bcra
  - calendar
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: medium
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir calendario oficial de informes BCRA para programar expectativas de Informe Monetario Diario/Mensual, Boletin Estadistico, Balance Cambiario, REM e IPOM.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve eventos de publicacion BCRA con fecha, informe, frecuencia y fuente
- [x] #2 Incluye fixtures/tests offline para parsing del calendario
- [x] #3 Se integra con metadata de freshness para scheduling posterior
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added BCRA calendario connector (bcra_calendario) that parses the official BCRA calendar HTML table (div#tabla-rowcolspan-events) into publication events with fecha/informe/frecuencia/fuente, using a stdlib HTMLParser. Frequency is inferred from report-name keywords and freshness metadata (DEFAULT_TTL_SECONDS=86400) is exposed for scheduling. Fixture captured live (82 events for 2026); 12 new offline tests. Registered centrally. Risks: HTML table structure and Spanish month abbreviations are hard-coded; brittle to a BCRA site redesign.
<!-- SECTION:FINAL_SUMMARY:END -->
