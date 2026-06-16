---
id: TASK-8.13
title: Implementar conector calendario publicaciones INDEC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-16 01:37'
labels:
  - argentina
  - indec
  - calendar
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_indec.md
parent_task_id: TASK-8
priority: medium
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir calendario oficial INDEC para anticipar releases de IPC, EMAE, EPH, salarios, canastas y pobreza.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve eventos de publicacion con fecha, dataset, titulo y fuente
- [x] #2 Incluye fixtures/tests offline para HTML/JSON/PDF segun fuente confirmada
- [x] #3 Permite filtrar eventos relevantes al reporte semanal
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added INDEC calendario connector (indec_calendario) that extracts publication events from the INDEC calendar (HTML with embedded JSON in a script tag) and normalizes them to SourceItems with fecha/dataset/titulo/fuente. Includes a weekly-report filter (WEEKLY_REPORT_DATASETS: IPC, EMAE, EPH, Salarios, Canasta, Pobreza) plus offline HTML/JSON fixtures and error-case fixtures. 20 new tests (178->198 baseline before integration). Registered centrally in connectors/__init__.py. Risks: JSON structure inferred from research doc; may need a parser bump on first live run if INDEC's frontend differs.
<!-- SECTION:FINAL_SUMMARY:END -->
