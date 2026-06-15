---
id: TASK-10.6
title: Implementar reviewer de reporte semanal
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - weekly-report
  - evaluation
  - reviewer
  - model-medium
dependencies: []
references:
  - analysis/report_evaluation_rubric.md
parent_task_id: TASK-10
priority: medium
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una herramienta local que evalúe un reporte semanal contra la rubrica del perfil del host y devuelva score, fallas criticas y recomendaciones.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reviewer consume Markdown de reporte y produce evaluacion estructurada con escala 0/1/2
- [ ] #2 Detecta fallas tipicas: sobreinterpretar dato, omitir precio, confundir BCRA/Tesoro
- [ ] #3 Incluye tests con reportes fixture aprobados y rechazados
<!-- AC:END -->
