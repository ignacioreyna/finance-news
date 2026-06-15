---
id: TASK-8.4
title: Implementar conector INDEC IPC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-15 19:04'
labels:
  - argentina
  - indec
  - inflation
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_indec.md
parent_task_id: TASK-8
priority: high
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear el primer conector INDEC de inflacion usando la fuente oficial descargable de IPC, priorizando CSV cuando exista.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve IPC headline y categorias disponibles con periodo, valor, frecuencia y fuente oficial
- [x] #2 Incluye fixtures/tests offline para parsing CSV y normalizacion
- [x] #3 Documenta si IPC nucleo no esta disponible como serie descargable clara
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
INDEC IPC connector. connectors/indec_ipc.py: IndecIpcConnector + pure CSV parser parse_ipc_csv(); public INDEC CSV (serie_ipc_divisiones.csv, no key; ISO-8859-1, semicolon-delimited). Returns IPC headline (NIVEL GENERAL) + categorias (periodo, valor, frecuencia, fuente). AC#3: IPC nucleo documented as NOT available as a machine-readable downloadable series. Hand-crafted CSV fixture (35 rows). 24 new unittest tests; registered as indec_ipc. Full suite 178 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
