---
id: TASK-11.1
title: Implementar logging estructurado de conectores
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - ops
  - logging
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_quality_matrix.md
  - analysis/connector_architecture.md
parent_task_id: TASK-11
priority: medium
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agregar helpers para logs de partial_failure y run_summary alineados con la matriz de calidad de conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Los conectores pueden emitir eventos connector.partial_failure y connector.run_summary con campos requeridos
- [ ] #2 Incluye tests unitarios del formato de log/evento
- [ ] #3 Runner o helper no imprime secretos ni payloads crudos completos
<!-- AC:END -->
