---
id: TASK-8.5
title: Validar schemas descargables INDEC no-IPC
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
labels:
  - argentina
  - indec
  - research
  - schemas
  - model-medium
dependencies: []
references:
  - analysis/source_research_indec.md
parent_task_id: TASK-8
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigar y fijar schemas locales para EMAE, salarios, CBA/CBT, pobreza y EPH antes de crear conectores atomicos, porque las fuentes usan XLS/XLSX heterogeneos.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear analysis/indec_schema_validation.md con URLs, formato, columnas esperadas y frecuencia por dataset
- [ ] #2 Identificar cuales datasets ya pueden convertirse en conectores atomicos
- [ ] #3 Marcar gaps de parsing, hojas multiples o cambios historicos de formato
<!-- AC:END -->
