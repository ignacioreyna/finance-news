---
id: TASK-7.2
title: Definir evaluacion del reporte contra perfil del host
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:53'
updated_date: '2026-06-14 15:31'
labels:
  - quality
  - weekly-report
  - evaluation
  - model-medium
dependencies:
  - TASK-6.1
references:
  - analysis/host_profile.md
parent_task_id: TASK-7
priority: medium
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Diseñar una checklist para evaluar si un reporte semanal respeta criterios del host: dato/mecanismo/precio/riesgo, anti-narrativa y trazabilidad. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/report_evaluation_rubric.md con criterios y escala
- [x] #2 Incluir ejemplos de fallas: sobreinterpretar un dato, omitir precio de mercado, confundir BCRA/Tesoro
- [x] #3 La rubrica debe poder usarse por un subagent reviewer
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer analysis/host_profile.md y analysis/weekly_report_schema.md para extraer criterios de evaluacion.
2. Crear analysis/report_evaluation_rubric.md con escala usable por subagent reviewer.
3. Incluir fallas tipicas y checks de dato, mecanismo, precio, riesgo, anti-narrativa y trazabilidad.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Revise analysis/host_profile.md y analysis/weekly_report_schema.md para extraer criterios de dato, mecanismo, precio, riesgo y trazabilidad.

- Cree analysis/report_evaluation_rubric.md con escala 0/1/2, criterios criticos, regla de decision y salida sugerida para subagent reviewer.

- Inclui ejemplos concretos de fallas: sobreinterpretar un dato, omitir precio de mercado y confundir BCRA/Tesoro.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Defini la rubrica de evaluacion del reporte semanal en analysis/report_evaluation_rubric.md.

La rubrica condensa el perfil del host y el esquema operativo existente en una escala 0/1/2, criterios criticos, regla de aprobacion y formato de salida para un subagent reviewer.

Tambien incluye fallas tipicas y como penalizarlas cuando el reporte sobreinterpreta un dato, omite precio de mercado o confunde roles entre BCRA y Tesoro.
<!-- SECTION:FINAL_SUMMARY:END -->
