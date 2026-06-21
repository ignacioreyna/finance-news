---
id: TASK-10.3
title: Implementar motor de scoring semanal
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-21 13:57'
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
- [x] #1 El scorer devuelve score, rationale, inputs usados y gatillos de ruptura si aplican
- [x] #2 Separa scoring Argentina e internacional
- [x] #3 Incluye tests unitarios con señales fixture para score 0 a 4
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added weekly scoring engine (src/finance_news/scoring.py) implementing analysis/weekly_signal_scoring.md: a 0-4 scale (0 noise, 1 light/priced, 2 relevant contained, 3 high stress/trend change, 4 base-scenario break). Frozen NormalizedSignal (input: domain/name/value/unit/period/region) and ScoredSignal (output: score 0-4, rationale, inputs_used, breakout_triggers) with to_dict/from_dict. ScoringEngine.score_signals() with SEPARATE ARG_THRESHOLDS and INTL_THRESHOLDS tables (AC#2) covering AR (tesoro_y_deuda, bcra_reservas, cambiario, inflacion, actividad_empleo) and international (fed_bancos_centrales, liquidez_global_curva, geopolitica_commodities) domains; breakout triggers fire at score 4. 28 unit tests covering scores 0-4 across all domains (691->719).
<!-- SECTION:FINAL_SUMMARY:END -->
