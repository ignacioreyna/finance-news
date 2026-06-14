---
id: TASK-6.2
title: Definir scoring de senales semanales
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 19:56'
labels:
  - weekly-report
  - scoring
  - model-large
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-6
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Diseñar rubricas de stress y relevancia para priorizar que entra al reporte: Tesoro, BCRA, cambiario, inflacion, actividad, Fed, liquidez y geopolítica. Modelo recomendado: large.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/weekly_signal_scoring.md con score, input, interpretacion y umbrales iniciales
- [x] #2 Separar scores Argentina e internacional
- [x] #3 Incluir ejemplos de gatillos que rompen escenario base
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Creado analysis/weekly_signal_scoring.md con escala 0-4, inputs, interpretacion, umbrales iniciales y reglas de priorizacion para el reporte semanal.

Separados los scores de Argentina e internacional, cubriendo Tesoro, BCRA, cambiario, inflacion, actividad, Fed, liquidez y geopolitica.

Agregados gatillos concretos que rompen el escenario base local e internacional.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Definido el scoring operativo de senales semanales en analysis/weekly_signal_scoring.md.

Cambios:
- Agregada escala comun 0-4 con reglas de uso editorial y priorizacion.
- Separados tableros de Argentina e internacional con inputs, interpretacion y umbrales iniciales.
- Cubiertos Tesoro, BCRA, cambiario, inflacion, actividad, Fed, liquidez global y geopolitica/commodities.
- Incluidos gatillos locales e internacionales que rompen el escenario base.

Tests/verificacion:
- Revision manual del archivo creado contra los AC de TASK-6.2.
<!-- SECTION:FINAL_SUMMARY:END -->
