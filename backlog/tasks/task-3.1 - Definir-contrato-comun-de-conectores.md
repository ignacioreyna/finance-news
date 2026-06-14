---
id: TASK-3.1
title: Definir contrato comun de conectores
status: To Do
assignee: []
created_date: '2026-06-14 14:50'
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
- [ ] #1 Crear docs o analysis/connector_architecture.md con interfaz propuesta y flujo de ingesta
- [ ] #2 Definir un modelo SourceItem o equivalente con id externo, fuente, fecha, titulo, body/resumen, url y metadata
- [ ] #3 Incluir convenciones de retries, rate limits, fixtures, paginado y cursores
<!-- AC:END -->
