---
id: TASK-7.1
title: Definir matriz de calidad de conectores
status: To Do
assignee: []
created_date: '2026-06-14 14:53'
labels:
  - quality
  - connectors
  - testing
  - model-medium
dependencies:
  - TASK-3.1
parent_task_id: TASK-7
priority: medium
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Especificar como evaluar freshness, completitud, errores de fuente, trazabilidad y tests de cada conector. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear analysis/connector_quality_matrix.md con dimensiones, checks y severidad
- [ ] #2 Incluir criterios de freshness por tipo de fuente: diaria, semanal, mensual, evento
- [ ] #3 Definir que debe loguear un conector ante fallo parcial
<!-- AC:END -->
