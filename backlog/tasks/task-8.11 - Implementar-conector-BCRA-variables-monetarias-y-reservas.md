---
id: TASK-8.11
title: Implementar conector BCRA variables monetarias y reservas
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-15 19:04'
labels:
  - argentina
  - bcra
  - reserves
  - monetary
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: high
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir fuentes oficiales BCRA para reservas, base monetaria, agregados y variables monetarias relevantes al tablero Argentina.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve series normalizadas con fecha, valor, unidad, frecuencia y fuente
- [x] #2 Incluye fixtures/tests offline para payload API/descarga oficial
- [x] #3 Excluye intervencion diaria neta si no hay fuente oficial diaria identificada
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
BCRA variables monetarias y reservas connector. connectors/bcra_variables_reservas.py: BcraVariablesReservasConnector + pure parser parse_bcra_monetarias_response(); public BCRA monetarias endpoint (no key); variables: reservas(1), base monetaria(15), circulacion(16), efectivo entidades(18), depositos cc BCRA(19). Normalized series (fecha, valor, unidad, frecuencia, fuente). AC#3: daily net intervention excluded (no official daily source); documented + tested. Live-captured fixtures. 25 new unittest tests; registered as bcra_variables_reservas. Full suite 178 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
