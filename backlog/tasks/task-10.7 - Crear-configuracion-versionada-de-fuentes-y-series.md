---
id: TASK-10.7
title: Crear configuracion versionada de fuentes y series
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
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
- [ ] #1 Config incluye identificadores de fuente, conector, frecuencia, freshness TTL y prioridad
- [ ] #2 Separa fuentes primarias, proxies y fuentes manuales
- [ ] #3 Incluye validacion/tests de schema de configuracion
<!-- AC:END -->
