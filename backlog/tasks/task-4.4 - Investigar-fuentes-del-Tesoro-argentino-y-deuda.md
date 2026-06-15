---
id: TASK-4.4
title: Investigar fuentes del Tesoro argentino y deuda
status: Done
assignee:
  - '@codex-worker'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-15 02:20'
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
- [x] #1 Crear analysis/source_research_tesoro.md con fuentes oficiales y no oficiales necesarias
- [x] #2 Cubrir licitaciones, resultados, calendario de vencimientos, caja/cuenta y deuda
- [x] #3 Indicar si cada fuente es machine-readable o requiere scraping/manual
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

- Cree analysis/source_research_tesoro.md con inventario de fuentes oficiales, fuentes de mercado/no oficiales necesarias, gaps y conectores sugeridos.

- Verifique fuentes de Argentina.gob.ar/Finanzas para licitaciones, resultados, colocaciones, datos mensuales/trimestrales, estructura financiera y deuda en pesos.

- Contraste con BCRA API monetaria para proxy de cuenta/caja del Tesoro, datos.gob.ar series fiscales IMIG/base caja, y OPC para deuda/vencimientos.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Cree analysis/source_research_tesoro.md como inventario accionable de fuentes para Tesoro argentino y deuda.

Incluye fuentes oficiales de Argentina.gob.ar/Finanzas para licitaciones, resultados, colocaciones, estructura financiera, datos mensuales/trimestrales y deuda en pesos; BCRA API monetaria como proxy de cuenta/caja del Tesoro; datos.gob.ar para series fiscales IMIG/base caja; y OPC como contraste tecnico de deuda/vencimientos.

Tambien clasifica cada fuente por frecuencia, formato, confiabilidad e ingesta machine-readable/scraping/manual, y propone conectores para licitaciones, cashflows, rollover, caja, deuda y precios de mercado. Los gaps quedan explicitados: no se encontro API oficial unica para licitaciones/resultados ni endpoint publico estable de Cuenta Unica del Tesoro diaria desagregada.
<!-- SECTION:FINAL_SUMMARY:END -->
