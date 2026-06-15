---
id: TASK-4.4
title: Investigar fuentes del Tesoro argentino y deuda
status: To Do
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-15 02:14'
labels:
  - argentina
  - tesoro
  - debt
  - research
  - model-large
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-4
priority: high
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapear fuentes para licitaciones, vencimientos, rollover, cuenta del Tesoro, deuda en moneda extranjera y reportes fiscales. Modelo recomendado: large por dispersion de fuentes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear analysis/source_research_tesoro.md con fuentes oficiales y no oficiales necesarias
- [ ] #2 Cubrir licitaciones, resultados, calendario de vencimientos, caja/cuenta y deuda
- [ ] #3 Indicar si cada fuente es machine-readable o requiere scraping/manual
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar host_profile, source_catalog y research Argentina existente.
2. Investigar fuentes para licitaciones, resultados, vencimientos, caja/cuenta, deuda y fiscal.
3. Crear analysis/source_research_tesoro.md clasificando oficial/no oficial y machine-readable/scraping/manual.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Intento de research delegado interrumpido: el subagent no entrego analysis/source_research_tesoro.md ni pudo cerrar ACs. Queda pendiente para una nueva tanda.
<!-- SECTION:NOTES:END -->
