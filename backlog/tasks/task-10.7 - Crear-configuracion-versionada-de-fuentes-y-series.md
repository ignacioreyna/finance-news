---
id: TASK-10.7
title: Crear configuracion versionada de fuentes y series
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-15 17:07'
labels:
  - pipeline
  - config
  - sources
  - model-medium
dependencies: []
references:
  - analysis/source_catalog.md
  - analysis/connector_quality_matrix.md
parent_task_id: TASK-10
priority: high
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Definir archivos de configuracion versionados para series, conectores habilitados, frecuencias, freshness y prioridad editorial, usando los source research docs como base.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Config incluye identificadores de fuente, conector, frecuencia, freshness TTL y prioridad
- [x] #2 Separa fuentes primarias, proxies y fuentes manuales
- [x] #3 Incluye validacion/tests de schema de configuracion
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Versioned sources/series config. src/finance_news/config/{schema,loader}.py define frozen SourceConfig/SeriesConfig/FreshnessSpec (to_dict/from_dict) with primary/proxy/manual categories, frequency, freshness TTL, priority (alta/media/baja). Loader parses config/sources.toml via stdlib tomllib (no deps, no secrets; env-var placeholders) with clear validation errors; seeded from analysis/source_catalog.md (Argentina + international). 18 new unittest tests incl. negative schema cases; pyproject deps remain []. Full suite 57 OK. Merged via feat/task-10.7-config.
<!-- SECTION:FINAL_SUMMARY:END -->
