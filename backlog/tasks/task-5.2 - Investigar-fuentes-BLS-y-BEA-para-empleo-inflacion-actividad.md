---
id: TASK-5.2
title: Investigar fuentes BLS y BEA para empleo inflacion actividad
status: Done
assignee: []
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 22:14'
labels:
  - international
  - bls
  - bea
  - research
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-5
priority: high
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapear APIs y descargas oficiales para CPI, PPI, payrolls, JOLTS, claims si aplica, PCE y PBI/consumo/inversion. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_us_macro.md con series, endpoints, frecuencia y claves/API requeridas
- [x] #2 Separar BLS, BEA y otras fuentes oficiales necesarias
- [x] #3 Definir minimo viable para tablero Fed semanal
<!-- AC:END -->



## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar analysis/host_profile.md, analysis/source_catalog.md y analysis/source_research_fed.md.
2. Investigar fuentes oficiales BLS, BEA y complementarias oficiales para empleo, inflacion, actividad y claims si aplica.
3. Crear analysis/source_research_us_macro.md con series, endpoints, frecuencia, claves/API y minimo viable Fed semanal.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Revise analysis/host_profile.md, analysis/source_catalog.md, analysis/source_research_fed.md y analysis/weekly_signal_scoring.md para alinear estructura y prioridades.

- Verifique fuentes oficiales de BLS, BEA, DOL/ETA y Atlanta Fed para CPI, PPI, payrolls, unemployment, JOLTS, claims, PCE, GDP, consumo e inversion.

- Cree analysis/source_research_us_macro.md con endpoints, frecuencias, formatos, requisitos de API key y MVP para tablero Fed semanal.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documente las fuentes oficiales de EE.UU. para empleo, inflacion y actividad en analysis/source_research_us_macro.md.

Inclui:
- separacion operativa entre BLS, BEA y otras fuentes oficiales necesarias;
- endpoints, formatos, frecuencias y requisitos de API key para cada bloque;
- series candidatas para CPI, payrolls, unemployment, JOLTS y rutas de trabajo para PPI, PCE, GDP, consumo e inversion;
- minimo viable para tablero Fed semanal con prioridad de implementacion.

Fuentes oficiales verificadas:
- BLS Public Data API y text files por encuesta;
- BEA API, GDP y PCE pages;
- DOL/ETA weekly claims;
- Atlanta Fed GDPNow.
<!-- SECTION:FINAL_SUMMARY:END -->
