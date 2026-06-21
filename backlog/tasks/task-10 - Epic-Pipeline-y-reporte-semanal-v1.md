---
id: TASK-10
title: 'Epic: Pipeline y reporte semanal v1'
status: Done
assignee: []
created_date: '2026-06-15 02:42'
updated_date: '2026-06-21 14:56'
labels:
  - epic
  - weekly-report
  - pipeline
  - phase-2
  - model-medium
dependencies: []
priority: high
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Convertir conectores normalizados, scoring y context pack en un flujo reproducible para generar el reporte semanal: storage local, runner, scoring, armado de contexto y revision automatizable.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Epic complete: weekly pipeline built. Scoring engine (10.3, 0-4 scale, AR/INTL split) -> report context pack builder (10.4, JSON+Markdown, score/confidence inclusion rules, open_gaps) -> deterministic Markdown report generator (10.5, 6 sections + citations, snapshot tests) -> report reviewer (10.6, 0/1/2 rubric + failure detectors for over-interpretation/missing-price/BCRA-Tesoro confusion). 833 tests green on main.
<!-- SECTION:FINAL_SUMMARY:END -->
