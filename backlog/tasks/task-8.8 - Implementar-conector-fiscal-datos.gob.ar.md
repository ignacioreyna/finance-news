---
id: TASK-8.8
title: Implementar conector fiscal datos.gob.ar
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-16 01:37'
labels:
  - argentina
  - fiscal
  - tesoro
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_tesoro.md
parent_task_id: TASK-8
priority: medium
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir series fiscales oficiales desde datos.gob.ar/Mecon para resultado primario, financiero y componentes mensuales relevantes al reporte.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve observaciones fiscales mensuales normalizadas con periodo, concepto, valor, unidad y fuente
- [x] #2 Incluye fixtures/tests offline para JSON/CSV de datos.gob.ar
- [x] #3 Documenta base caja/devengado segun la fuente usada
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added datos.gob.ar fiscal connector (datosgobar_fiscal) that fetches monthly fiscal series (resultado primario/financiero) from the apis.datos.gob.ar series API and normalizes to SourceItems with periodo/concepto/valor/unidad/fuente. Documents base-caja methodology via module constants (METHODOLOGY/METHODOLOGY_DESCRIPTION) reflected into item metadata. Fixture modeled on the real API JSON; 17 new offline tests. Registered centrally. Risk: fetches the latest observation only (limit=1); backfill/range queries are a follow-up.
<!-- SECTION:FINAL_SUMMARY:END -->
