---
id: TASK-10.3
title: Implementar motor de scoring semanal
status: To Do
assignee: []
created_date: '2026-06-15 02:46'
labels:
  - weekly-report
  - scoring
  - pipeline
  - model-medium
dependencies: []
references:
  - analysis/weekly_signal_scoring.md
parent_task_id: TASK-10
priority: high
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Convertir analysis/weekly_signal_scoring.md en codigo que puntue señales normalizadas por dominio, con umbrales iniciales y explicacion de score.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El scorer devuelve score, rationale, inputs usados y gatillos de ruptura si aplican
- [ ] #2 Separa scoring Argentina e internacional
- [ ] #3 Incluye tests unitarios con señales fixture para score 0 a 4
<!-- AC:END -->
