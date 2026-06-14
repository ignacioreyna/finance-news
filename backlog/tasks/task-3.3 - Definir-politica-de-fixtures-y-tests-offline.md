---
id: TASK-3.3
title: Definir politica de fixtures y tests offline
status: To Do
assignee: []
created_date: '2026-06-14 14:51'
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
- [ ] #1 Crear una seccion en connector_architecture.md o un doc dedicado con politica de fixtures
- [ ] #2 Definir naming, ubicacion y criterios para snapshots HTML/CSV/PDF
- [ ] #3 Incluir regla: parsers puros testeados offline antes de pruebas con red
<!-- AC:END -->
