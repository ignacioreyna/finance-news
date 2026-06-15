---
id: TASK-11.2
title: Crear helpers de fixtures y snapshots
status: Done
assignee:
  - '@general-air'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-15 17:07'
labels:
  - ops
  - testing
  - fixtures
  - model-small
dependencies: []
references:
  - analysis/connector_fixtures_policy.md
parent_task_id: TASK-11
priority: medium
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Estandarizar carga de fixtures, snapshots normalizados y metadata de origen para nuevos conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Helper carga fixtures desde tests/fixtures o ruta configurada sin red
- [x] #2 Helper compara snapshots normalizados de SourceItem de forma deterministica
- [x] #3 Incluye documentacion breve de naming y uso en tests
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Reusable test helpers. src/finance_news/testing/{fixtures,snapshots}.py: fixture loaders resolve tests/fixtures/<connector>/ offline (base via arg or FINANCE_NEWS_FIXTURES_BASE env); snapshots produce deterministic SourceItem normalization (sorted-key JSON) with readable diff on mismatch. README documents naming (YYYY-MM-DD__source__case.ext) and usage. Stdlib only. 14 new unittest tests. Full suite 57 OK. Merged via feat/task-11.2-fixtures.
<!-- SECTION:FINAL_SUMMARY:END -->
