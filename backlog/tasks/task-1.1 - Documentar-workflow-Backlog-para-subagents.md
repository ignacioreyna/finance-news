---
id: TASK-1.1
title: Documentar workflow Backlog para subagents
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:53'
updated_date: '2026-06-14 15:27'
labels:
  - workflow
  - backlog
  - subagents
  - model-small
dependencies: []
references:
  - AGENTS.md
parent_task_id: TASK-1
priority: high
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una guia breve para que futuras sesiones/subagents tomen una tarea, la pongan In Progress, documenten plan/notas y cierren con resumen. Modelo recomendado: small.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/backlog_workflow.md o backlog doc equivalente con comandos principales
- [x] #2 Incluir convencion de modelo recomendado usando labels model-small/model-medium/model-large
- [x] #3 Incluir regla de una tarea atomica por subagent/sesion
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar AGENTS.md y el estado actual del backlog.
2. Crear una guia corta en analysis/backlog_workflow.md con comandos CLI y convenciones de subagents.
3. Verificar que cubra labels de modelo y aislamiento de una tarea por subagent.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Creado analysis/backlog_workflow.md con comandos base, convencion de labels de modelo y regla de una sola tarea atomica por sesion.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego analysis/backlog_workflow.md como guia breve para subagents. Incluye comandos de inicio/cierre con ./scripts/backlog.sh, convencion de labels model-small/model-medium/model-large y regla de una tarea atomica por sesion. La tarea queda cerrada sin tocar otros archivos del backlog.
<!-- SECTION:FINAL_SUMMARY:END -->
