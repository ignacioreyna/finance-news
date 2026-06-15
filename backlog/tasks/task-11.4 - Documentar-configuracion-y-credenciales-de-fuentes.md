---
id: TASK-11.4
title: Documentar configuracion y credenciales de fuentes
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
labels:
  - ops
  - docs
  - credentials
  - model-small
dependencies: []
references:
  - analysis/source_research_us_macro.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-11
priority: medium
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una guia de variables de entorno, credenciales opcionales y politicas de secretos para APIs como BLS, BEA, BYMA/MAE y futuros conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear docs/source_credentials.md con variables, obligatoriedad y fuentes que las usan
- [ ] #2 Distinguir credenciales opcionales, obligatorias y pendientes de validacion
- [ ] #3 Incluir reglas para no commitear secretos ni fixtures con tokens
<!-- AC:END -->
