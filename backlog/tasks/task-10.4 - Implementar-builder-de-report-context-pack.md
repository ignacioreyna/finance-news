---
id: TASK-10.4
title: Implementar builder de report context pack
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-21 14:23'
labels:
  - weekly-report
  - context-pack
  - pipeline
  - model-medium
dependencies:
  - TASK-10.1
  - TASK-10.3
references:
  - analysis/report_context_pack.md
  - analysis/weekly_report_schema.md
parent_task_id: TASK-10
priority: high
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Construir el paquete de contexto semanal desde SourceItems, scores, fuentes y gaps abiertos, respetando la estructura Markdown/JSON definida.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Builder genera report_context_pack en JSON y Markdown con source_index y open_gaps
- [x] #2 Aplica reglas de inclusion por score y confianza
- [x] #3 Incluye tests offline con items y scores fixture
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added report context pack builder (src/finance_news/context_pack.py) implementing analysis/report_context_pack.md + weekly_report_schema.md. Frozen dataclasses (to_dict/from_dict): ContextPackItem, SourceIndexEntry, OpenGap, ReportContextPack (week metadata + argentina/international/market sections + source_index + open_gaps + summary_stats). ContextPackBuilder.build(items, scored_signals, score_threshold=2, confidence_threshold='media') applies AC#2 inclusion rules (score>=threshold AND confidence>=threshold; excluded items recorded in open_gaps with reason; confidence derived from score+source classification). AC#1: to_json() and to_markdown() serializers emit the pack in both formats with source_index and open_gaps. Imports ScoredSignal from scoring (10.3). 19 offline tests with fixture items+scores (740->759).
<!-- SECTION:FINAL_SUMMARY:END -->
