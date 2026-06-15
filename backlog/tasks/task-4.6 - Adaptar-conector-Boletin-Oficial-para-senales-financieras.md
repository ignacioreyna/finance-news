---
id: TASK-4.6
title: Adaptar conector Boletin Oficial para senales financieras
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-15 02:26'
labels:
  - argentina
  - bora
  - connectors
  - model-medium
dependencies:
  - TASK-3.2
references:
  - >-
    https://github.com/colossus-lab/vigia/tree/main/packages/connectors/src/vigia_connectors/bora.py
parent_task_id: TASK-4
priority: medium
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Definir y luego implementar un filtro de Boletin Oficial enfocado en normas economicas/financieras relevantes para el agente. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Usar el patron de vigia_connectors.bora para listado/detalle por fecha
- [x] #2 Filtrar organismos y keywords economicas: BCRA, Economia, ARCA, CNV, deuda, cambios, energia, mineria, agro
- [x] #3 Incluir fixtures/tests offline de parsing y clasificacion
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar scaffold de conectores, politica de fixtures y referencia/patron BORA si esta disponible.
2. Implementar conector/filtro Boletin Oficial para listado/detalle por fecha con clasificacion economica.
3. Agregar fixtures/tests offline de parsing y clasificacion para organismos y keywords relevantes.
4. Ejecutar tests y actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado el conector bora_financial para la Primera Sección del Boletín Oficial con fetch por fecha, resolución de detalle por aviso y filtrado orientado a señales financieras.

Cambios:
- Añadido parser de listado por fecha y parser de detalle para normalizar entradas BORA a SourceItem.
- Incorporada clasificación por organismos objetivo (BCRA, Economía, ARCA, CNV) y keywords económicas (deuda, cambios, energía, minería, agro).
- Exportado el conector desde connectors.__init__.
- Agregados fixtures HTML offline y tests para parseo, clasificación y flujo completo del conector.

Tests:
- python3 -m unittest discover -s tests
<!-- SECTION:FINAL_SUMMARY:END -->
