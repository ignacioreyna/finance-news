---
id: TASK-11.5
title: Implementar reporte de calidad de conectores
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
labels:
  - ops
  - quality
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_quality_matrix.md
parent_task_id: TASK-11
priority: medium
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una herramienta que recorra conectores/resultados y produzca un reporte de freshness, completitud, provenance, errores y cobertura de tests.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reporte muestra estado por conector con severidad S0/S1/S2/S3
- [ ] #2 Incluye freshness por tipo de fuente diaria/semanal/mensual/evento
- [ ] #3 Incluye tests con conectores/resultados fixture
<!-- AC:END -->
