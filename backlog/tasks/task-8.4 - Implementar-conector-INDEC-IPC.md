---
id: TASK-8.4
title: Implementar conector INDEC IPC
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
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
- [ ] #1 El conector devuelve IPC headline y categorias disponibles con periodo, valor, frecuencia y fuente oficial
- [ ] #2 Incluye fixtures/tests offline para parsing CSV y normalizacion
- [ ] #3 Documenta si IPC nucleo no esta disponible como serie descargable clara
<!-- AC:END -->
