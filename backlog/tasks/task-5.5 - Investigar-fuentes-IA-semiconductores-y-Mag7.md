---
id: TASK-5.5
title: Investigar fuentes IA semiconductores y Mag7
status: Done
assignee: []
created_date: '2026-06-14 14:52'
updated_date: '2026-06-15 02:18'
labels:
  - international
  - ai
  - semiconductors
  - research
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-5
priority: low
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapear fuentes para seguir IA/capex/productividad/chips/Mag7 cuando impactan mercado, sin convertir el agente en stock picker. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_ai_markets.md con fuentes y señales a monitorear
- [x] #2 Separar earnings/SEC, noticias regulatorias, restricciones comerciales y datos de mercado
- [x] #3 Definir criterios de relevancia para incluir en reporte semanal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar host_profile, source_catalog y research internacional existente.
2. Investigar fuentes para IA/capex/productividad/chips/Mag7 sin enfoque stock picker.
3. Crear analysis/source_research_ai_markets.md separando earnings/SEC, regulacion/comercio y datos de mercado.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Revise host_profile, source_catalog, source_research_fed, source_research_us_macro y weekly_signal_scoring para mantener el mismo marco editorial.

Cree analysis/source_research_ai_markets.md con fuentes primarias para SEC/earnings, productividad/capex macro, regulacion, restricciones comerciales y proxies de mercado.

Defini criterios de relevancia y workflow semanal para cubrir IA/chips/Mag7 sin enfoque stock picker.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego analysis/source_research_ai_markets.md como guia accionable para seguir IA, semiconductores, capex y Mag7 cuando el tema escala de historia sectorial a señal de mercado.

Incluye:
- Fuentes primarias de SEC/EDGAR e investor relations para hyperscalers, NVIDIA, AMD, Broadcom, TSMC y ASML.
- Separacion explicita entre noticias regulatorias, restricciones comerciales/export controls y proxies de mercado.
- Fuentes macro oficiales de BLS, BEA y Census para validar productividad, inversion e infraestructura.
- Criterios de relevancia, score editorial y workflow semanal para decidir que entra al reporte.

La pieza evita stock picking y deja a los precios de mercado como confirmacion o contradiccion, no como fuente causal primaria.
<!-- SECTION:FINAL_SUMMARY:END -->
