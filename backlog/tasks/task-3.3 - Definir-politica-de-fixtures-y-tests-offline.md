---
id: TASK-3.3
title: Definir politica de fixtures y tests offline
status: Done
assignee: []
created_date: '2026-06-14 14:51'
updated_date: '2026-06-14 15:30'
labels:
  - connectors
  - tests
  - fixtures
  - model-small
dependencies:
  - TASK-3.1
parent_task_id: TASK-3
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Documentar como cada conector debe testear parsing sin red usando fixtures, siguiendo el enfoque observado en vigia. Modelo recomendado: small.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear una seccion en connector_architecture.md o un doc dedicado con politica de fixtures
- [x] #2 Definir naming, ubicacion y criterios para snapshots HTML/CSV/PDF
- [x] #3 Incluir regla: parsers puros testeados offline antes de pruebas con red
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer analysis/connector_architecture.md para alinear la politica de fixtures al contrato de conectores.
2. Crear analysis/connector_fixtures_policy.md con naming, ubicacion, snapshots y reglas offline.
3. Cubrir HTML, CSV, PDF y criterios de estabilidad/reproduccion.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Created analysis/connector_fixtures_policy.md with offline-first fixture rules, naming, locations, and snapshot criteria for HTML/CSV/PDF.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a dedicated fixtures policy document to codify offline-first parser testing, fixture layout, naming conventions, and snapshot rules for HTML, CSV, and PDF sources. This keeps connector parser coverage reproducible without network access and leaves integration tests focused on transport and auth behavior.
<!-- SECTION:FINAL_SUMMARY:END -->
