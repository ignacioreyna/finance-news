---
id: TASK-10.5
title: Implementar generador Markdown de reporte semanal
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - weekly-report
  - generator
  - pipeline
  - model-medium
dependencies:
  - TASK-10.4
references:
  - analysis/weekly_report_schema.md
  - analysis/report_context_pack.md
parent_task_id: TASK-10
priority: medium
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear un generador deterministico de borrador Markdown desde el context pack, sin depender todavia de un modelo externo, para validar estructura, trazabilidad y gaps.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Genera secciones Argentina, internacional, mercado, escenarios, riesgos y que mirar
- [ ] #2 Incluye source links/citas breves dentro de los limites del context pack
- [ ] #3 Incluye tests snapshot del Markdown generado
<!-- AC:END -->
