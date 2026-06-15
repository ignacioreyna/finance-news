---
id: TASK-9.5
title: Validar BEA API key y metadata NIPA
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
labels:
  - international
  - bea
  - macro
  - research
  - credentials
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_macro.md
parent_task_id: TASK-9
priority: high
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Antes de implementar conectores BEA, validar UserID, discovery de metadata y mapeo de tablas NIPA para PCE, core PCE, ingreso, consumo y GDP.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear analysis/bea_nipa_schema_validation.md con endpoints, parametros, tablas, frecuencia y series objetivo
- [ ] #2 Definir estrategia de configuracion segura para BEA UserID
- [ ] #3 Crear tareas atomicas posteriores solo para tablas confirmadas
<!-- AC:END -->
