---
id: TASK-10.2
title: Implementar runner CLI de conectores
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - pipeline
  - cli
  - connectors
  - model-medium
dependencies:
  - TASK-10.1
references:
  - analysis/connector_architecture.md
  - analysis/connector_quality_matrix.md
parent_task_id: TASK-10
priority: high
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una CLI local para ejecutar conectores por nombre, ventana temporal y modo offline/online, persistiendo resultados en el storage local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CLI permite listar conectores disponibles y ejecutar uno por nombre
- [ ] #2 Permite dry-run/offline usando fixtures cuando el conector lo soporte
- [ ] #3 Registra run summary con conteo de items, errores recuperables y ruta de salida
<!-- AC:END -->
