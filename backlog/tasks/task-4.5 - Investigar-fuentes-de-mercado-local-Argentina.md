---
id: TASK-4.5
title: Investigar fuentes de mercado local Argentina
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-14 23:51'
labels:
  - argentina
  - market-data
  - research
  - model-large
dependencies: []
references:
  - analysis/host_profile.md
modified_files:
  - analysis/source_research_arg_market.md
parent_task_id: TASK-4
priority: medium
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Identificar proveedores o endpoints para dolar oficial/MEP/CCL, futuros, curva CER/TAMAR/LECAP, bonos hard dollar y riesgo pais. Modelo recomendado: large por mezcla de fuentes oficiales, mercado y posibles restricciones.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_arg_market.md con opciones por serie y costo/confiabilidad
- [x] #2 Separar fuentes gratis/oficiales, fuentes scrapeables y fuentes pagas/manuales
- [x] #3 Proponer minimo viable para un reporte semanal sin datos pagos
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Releve fuentes oficiales/gratuitas, scrapeables y pagas/manuales para dolar oficial, MEP/CCL, futuros, curva CER/TAMAR/LECAP, bonos hard dollar y riesgo pais.
- Cree analysis/source_research_arg_market.md con URLs concretas, formato, frecuencia, costo/confiabilidad y recomendacion de MVP semanal sin datos pagos.
- Marque JPM EMBI como fuente licenciada y propuse Rava/Ambito/proxy propio como fallback secundario no oficial.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Investigue fuentes de mercado local Argentina y documente una matriz accionable en analysis/source_research_arg_market.md.

Incluye:
- Opciones por serie para dolar oficial, MEP/CCL, futuros, curva CER/TAMAR/LECAP, bonos hard dollar y riesgo pais.
- Separacion entre fuentes gratis/oficiales, scrapeables y pagas/manuales, con URLs, formato, frecuencia, costo y confiabilidad.
- MVP semanal sin datos pagos basado en BCRA, Tesoro, BYMA/A3/MAE cuando haya acceso EOD o visor, CAFCI y fallback secundario para riesgo pais.

Riesgos/seguimiento:
- Riesgo pais EMBI oficial requiere licencia JPM; el MVP debe etiquetar Rava/Ambito o proxy propio como dato no licenciado.
- Conviene confirmar credenciales BYMA EOD/Indices sin costo antes de implementar conectores productivos.
<!-- SECTION:FINAL_SUMMARY:END -->
