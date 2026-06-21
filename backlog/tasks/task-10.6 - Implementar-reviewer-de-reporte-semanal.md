---
id: TASK-10.6
title: Implementar reviewer de reporte semanal
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-21 13:58'
labels:
  - weekly-report
  - evaluation
  - reviewer
  - model-medium
dependencies: []
references:
  - analysis/report_evaluation_rubric.md
parent_task_id: TASK-10
priority: medium
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una herramienta local que evalúe un reporte semanal contra la rubrica del perfil del host y devuelva score, fallas criticas y recomendaciones.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reviewer consume Markdown de reporte y produce evaluacion estructurada con escala 0/1/2
- [x] #2 Detecta fallas tipicas: sobreinterpretar dato, omitir precio, confundir BCRA/Tesoro
- [x] #3 Incluye tests con reportes fixture aprobados y rechazados
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added weekly report reviewer (src/finance_news/report_reviewer.py) implementing analysis/report_evaluation_rubric.md + host_profile.md: review_report(markdown)->ReviewResult with 10 rubric criteria scored 0/1/2 (AC#1), overall_score, per_criterion, critical_failures, recommendations, approved flag. AC#2: three heuristic failure detectors - over-interpretation (structural claims without cited figures), missing market/price data (credibility/risk claims without market variables), and BCRA-vs-Tesoro confusion (cross-attributing fiscal to BCRA or monetary to Tesoro). Accent-normalized keyword/regex matching, stdlib only. AC#3: approved + rejected fixture reports under tests/fixtures/report_reviewer/ with classification tests. 21 tests (691->712).
<!-- SECTION:FINAL_SUMMARY:END -->
