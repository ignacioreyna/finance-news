---
id: TASK-6.1
title: Definir esquema del reporte semanal
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 15:28'
labels:
  - weekly-report
  - spec
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-6
priority: high
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Convertir analysis/host_profile.md en una plantilla operativa de reporte semanal con secciones, inputs y nivel de confianza. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/weekly_report_schema.md con secciones, campos obligatorios y opcionales
- [x] #2 Incluir Argentina, internacional, mercado, escenarios, riesgos y que mirar
- [x] #3 Cada seccion debe indicar fuentes requeridas y fallback si faltan datos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer analysis/host_profile.md para extraer expectativas editoriales del reporte.
2. Crear analysis/weekly_report_schema.md con secciones, campos requeridos/opcionales y fuentes/fallbacks.
3. Cubrir Argentina, internacional, mercado, escenarios, riesgos y que mirar.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Se creo analysis/weekly_report_schema.md con estructura operativa por seccion.

- Se incluyeron Argentina, internacional, mercado, escenarios, riesgos y que mirar.

- Cada bloque define campos obligatorios/opcionales, fuentes requeridas y fallback ante faltantes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Defini el esquema operativo del reporte semanal en analysis/weekly_report_schema.md a partir de analysis/host_profile.md.

El documento organiza el reporte en secciones ejecutables, con campos obligatorios y opcionales, criterios editoriales, fuentes requeridas y fallback cuando faltan datos. Tambien cubre explicitamente Argentina, internacional, mercado, escenarios, riesgos y que mirar, con validacion por precios o variables que confirman o invalidan cada lectura.
<!-- SECTION:FINAL_SUMMARY:END -->
