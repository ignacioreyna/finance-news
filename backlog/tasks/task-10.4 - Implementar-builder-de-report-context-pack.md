---
id: TASK-10.4
title: Implementar builder de report context pack
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - weekly-report
  - context-pack
  - pipeline
  - model-medium
dependencies:
  - TASK-10.1
  - TASK-10.3
references:
  - analysis/report_context_pack.md
  - analysis/weekly_report_schema.md
parent_task_id: TASK-10
priority: high
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Construir el paquete de contexto semanal desde SourceItems, scores, fuentes y gaps abiertos, respetando la estructura Markdown/JSON definida.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Builder genera report_context_pack en JSON y Markdown con source_index y open_gaps
- [ ] #2 Aplica reglas de inclusion por score y confianza
- [ ] #3 Incluye tests offline con items y scores fixture
<!-- AC:END -->
