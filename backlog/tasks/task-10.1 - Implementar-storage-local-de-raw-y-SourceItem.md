---
id: TASK-10.1
title: Implementar storage local de raw y SourceItem
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - pipeline
  - storage
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_architecture.md
  - analysis/connector_fixtures_policy.md
parent_task_id: TASK-10
priority: high
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agregar una capa local simple para guardar payloads crudos, snapshots normalizados y metadata de provenance por conector, siguiendo el contrato de conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Storage persiste raw payload, SourceItem normalizado y run metadata en rutas deterministicas
- [ ] #2 Incluye tests offline de round-trip y hash/provenance
- [ ] #3 No requiere base de datos externa para el MVP
<!-- AC:END -->
