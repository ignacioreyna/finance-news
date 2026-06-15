---
id: TASK-8.2
title: Implementar conector BCRA dolar oficial
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-15 18:29'
labels:
  - argentina
  - bcra
  - fx
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-8
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir la fuente oficial BCRA para dolar oficial/A3500 y entregar serie normalizada para el reporte semanal y calculos cambiarios.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve observaciones normalizadas de dolar oficial/A3500 con fecha, valor, source_url y metadata
- [x] #2 Incluye fixtures/tests offline para parsing y serializacion
- [x] #3 Define freshness diaria y fallback si la API oficial no responde
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
BCRA dolar oficial (A3500) connector. connectors/bcra_dolar_oficial.py: BcraDolarOficialConnector + pure parser parse_bcra_dolar_oficial_response(); public BCRA Cotizaciones/REF endpoint (no key). Normalized observations (fecha, valor, source_url, metadata). Daily freshness TTL 86400; 404/4xx/5xx -> RecoverableConnectorError, unexpected (3xx) -> ValueError (two contradicting tests reconciled). Live-captured fixture. 20 new unittest tests; registered as bcra_dolar_oficial. Full suite 129 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
