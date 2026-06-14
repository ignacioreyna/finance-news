---
id: TASK-6.3
title: Prototipar context pack para generacion del reporte
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 19:58'
labels:
  - weekly-report
  - prompting
  - agent
  - model-medium
dependencies:
  - TASK-6.1
  - TASK-6.2
references:
  - analysis/host_profile.md
parent_task_id: TASK-6
priority: medium
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Definir el paquete de contexto que recibira el modelo generador: datos normalizados, cambios semanales, perfil del host, scoring y fuentes. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/report_context_pack.md con estructura JSON/Markdown sugerida
- [x] #2 Incluir reglas de estilo: dato, mecanismo, precio, riesgo, confianza
- [x] #3 Definir limites para citas, links y trazabilidad de fuente
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer analysis/weekly_report_schema.md, analysis/weekly_signal_scoring.md, analysis/source_catalog.md y analysis/report_evaluation_rubric.md.
2. Crear analysis/report_context_pack.md con estructura JSON/Markdown sugerida para el modelo generador.
3. Incluir reglas de estilo, limites de citas/links y trazabilidad de fuente.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Cree analysis/report_context_pack.md con una plantilla Markdown + JSON para el modelo generador.

- Inclui reglas editoriales obligatorias para dato, mecanismo, precio, riesgo y confianza.

- Defini limites de citas, links y trazabilidad mediante source_index, fuente_ids y open_gaps.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se prototipo un context pack operativo para la generacion del reporte semanal en analysis/report_context_pack.md.

Cambios principales:
- Se definio una estructura compacta Markdown + JSON con bloques para ventana de reporte, perfil del generador, reglas editoriales, seleccion de senales, secciones del reporte, indice de fuentes y gaps abiertos.
- Se incorporaron reglas de estilo alineadas al host para separar dato, mecanismo, precio, riesgo y confianza.
- Se fijaron limites de citas, links y trazabilidad para que cada afirmacion material quede auditada con source_ids y un source_index reutilizable.

Impacto:
- El modelo generador ya tiene un contrato de entrada estable y compacto para producir borradores trazables y consistentes con el esquema editorial.

Verificacion:
- Revision manual contra analysis/weekly_report_schema.md, analysis/weekly_signal_scoring.md, analysis/source_catalog.md, analysis/report_evaluation_rubric.md y analysis/host_profile.md.
<!-- SECTION:FINAL_SUMMARY:END -->
