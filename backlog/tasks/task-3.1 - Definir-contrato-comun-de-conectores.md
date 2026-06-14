---
id: TASK-3.1
title: Definir contrato comun de conectores
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:50'
updated_date: '2026-06-14 15:29'
labels:
  - connectors
  - architecture
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
  - >-
    https://github.com/colossus-lab/vigia/tree/main/packages/connectors/src/vigia_connectors
parent_task_id: TASK-3
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Diseñar el contrato minimo para conectores financieros inspirado en vigia: cliente async, item normalizado, provenance, freshness, parser puro y errores recuperables. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear docs o analysis/connector_architecture.md con interfaz propuesta y flujo de ingesta
- [x] #2 Definir un modelo SourceItem o equivalente con id externo, fuente, fecha, titulo, body/resumen, url y metadata
- [x] #3 Incluir convenciones de retries, rate limits, fixtures, paginado y cursores
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar analysis/host_profile.md y la referencia vigia si esta disponible.
2. Crear analysis/connector_architecture.md con contrato minimo de conectores, SourceItem y flujo de ingesta.
3. Definir convenciones de retries, rate limits, fixtures, paginado, cursores, freshness y errores recuperables.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Redactado analysis/connector_architecture.md con contrato minimo de conectores: cliente async, parser puro, SourceItem, Provenance, Freshness y errores recuperables.

- Documentadas convenciones de retries, rate limits, fixtures, paginado y cursores, incluyendo el supuesto de referencia externa inaccesible.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se definio el contrato comun de conectores en analysis/connector_architecture.md para desacoplar adquisicion, parseo y normalizacion de fuentes financieras.

Incluye:
- Interfaz minima de conector async con PageResult, RetryPolicy y RateLimitPolicy.
- Modelo SourceItem con external_id, source, published_at, title, body/summary, url, metadata, provenance y freshness.
- Convenciones operativas para retries, rate limits, fixtures, paginado, cursores y manejo de errores recuperables.

Tambien se explicito el supuesto de trabajo por falta de acceso a la referencia externa de vigia en este entorno.
<!-- SECTION:FINAL_SUMMARY:END -->
