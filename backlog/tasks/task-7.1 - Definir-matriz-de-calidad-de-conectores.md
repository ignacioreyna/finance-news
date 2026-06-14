---
id: TASK-7.1
title: Definir matriz de calidad de conectores
status: Done
assignee: []
created_date: '2026-06-14 14:53'
updated_date: '2026-06-14 15:30'
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
- [x] #1 Crear analysis/connector_quality_matrix.md con dimensiones, checks y severidad
- [x] #2 Incluir criterios de freshness por tipo de fuente: diaria, semanal, mensual, evento
- [x] #3 Definir que debe loguear un conector ante fallo parcial
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer analysis/connector_architecture.md para tomar el contrato base de conectores.
2. Crear analysis/connector_quality_matrix.md con dimensiones, checks y severidad.
3. Definir freshness por frecuencia de fuente y logging ante fallos parciales.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Se definio analysis/connector_quality_matrix.md con dimensiones operativas, checks accionables y severidades S0-S3.

Se agregaron umbrales de freshness para fuentes diarias, semanales, mensuales y por evento, alineados con published_at, first_seen_at y fetched_at.

Se documento el contrato de logging ante fallo parcial, incluyendo evento estructurado y resumen de corrida.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego la matriz de calidad de conectores en analysis/connector_quality_matrix.md como complemento del contrato comun definido en analysis/connector_architecture.md. El documento establece dimensiones de evaluacion, severidades S0-S3, reglas de aprobacion, umbrales de freshness por frecuencia de fuente y el contrato minimo de logging estructurado ante fallos parciales y cierres degradados de corrida.
<!-- SECTION:FINAL_SUMMARY:END -->
