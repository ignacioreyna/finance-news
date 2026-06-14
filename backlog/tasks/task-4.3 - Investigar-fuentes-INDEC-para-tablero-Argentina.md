---
id: TASK-4.3
title: Investigar fuentes INDEC para tablero Argentina
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-14 22:16'
labels:
  - argentina
  - indec
  - research
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-4
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapear fuentes oficiales INDEC para IPC, IPC nucleo si aplica, EMAE, EPH, salarios/canastas y calendarios de publicacion. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_indec.md con datasets, URLs/API, formato y frecuencia
- [x] #2 Indicar cuales alimentan inflacion, actividad, empleo/ingresos y pobreza/canastas
- [x] #3 Identificar gaps donde se requieran fuentes complementarias
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar analysis/host_profile.md y catalogo de fuentes existente.
2. Investigar fuentes oficiales INDEC para IPC, actividad, empleo/ingresos, canastas y calendario.
3. Crear analysis/source_research_indec.md con datasets, URLs/API, formato, frecuencia y gaps.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiqué rutas oficiales INDEC y confirmé el patrón de publicación real: páginas HTML con enlaces a XLS/CSV/XLSX/PDF y calendario oficial con JSON embebido + PDFs semestrales.

Documenté fuentes para IPC, EMAE, EPH mercado de trabajo, distribución del ingreso, índice de salarios, CBA/CBT, pobreza y calendario en analysis/source_research_indec.md.

Identifiqué gaps para IPC núcleo, ausencia de API homogénea y necesidad de normalización adicional en EPH/ingresos y canastas.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Relevé y documenté fuentes oficiales actuales de INDEC para el tablero Argentina en analysis/source_research_indec.md. El documento incluye URLs verificadas, formatos disponibles (CSV/XLS/XLSX/PDF/HTML), frecuencia de publicación, mapeo a inflación, actividad, empleo/ingresos y pobreza/canastas, y una sección de gaps para los casos donde INDEC no expone una serie/API homogénea o donde conviene sumar una capa complementaria de parsing o validación.
<!-- SECTION:FINAL_SUMMARY:END -->
