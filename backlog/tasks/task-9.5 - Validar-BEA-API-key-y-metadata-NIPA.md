---
id: TASK-9.5
title: Validar BEA API key y metadata NIPA
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-20 23:57'
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
- [x] #1 Crear analysis/bea_nipa_schema_validation.md con endpoints, parametros, tablas, frecuencia y series objetivo
- [x] #2 Definir estrategia de configuracion segura para BEA UserID
- [x] #3 Crear tareas atomicas posteriores solo para tablas confirmadas
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/bea_nipa_schema_validation.md. VERIFIED endpoints/params (apps.bea.gov/api/data, UserID 36-char, DataSetName=NIPA, methods GETDATASETLIST/GetParameterValues/GetData). Confirmed NIPA tables: T20600 (Personal Income, monthly), T10101 (Real GDP, quarterly); PCE/core-PCE/consumption tables need TableName discovery. AC#2: BEA UserID stored as BEA_USER_ID in .env, loaded via existing settings.py, read via os.environ (free registration, not paid). AC#3: atomic tasks proposed only for confirmed tables (BEA Personal Income T20600, BEA Real GDP T10101); PCE/GDP-detail deferred pending metadata discovery.
<!-- SECTION:FINAL_SUMMARY:END -->
