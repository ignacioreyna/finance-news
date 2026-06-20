---
id: TASK-9.1
title: Implementar conector calendario FOMC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-20 00:04'
labels:
  - international
  - fed
  - fomc
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: high
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir el calendario oficial FOMC y producir una fila por reunion con links a statement, minutes, SEP, implementation note y press conference cuando existan.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve reuniones normalizadas con fecha, tipo, URLs hijas y source_url
- [x] #2 Incluye fixtures/tests offline para parsing del calendario oficial
- [x] #3 Marca reuniones con SEP y eventos faltantes sin romper la corrida
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FOMC calendario connector (fomc_calendario) parsing the federalreserve.gov FOMC calendar HTML (stdlib HTMLParser) into normalized meetings with date, meeting_type, has_sep flag, and categorized child URLs (statement/minutes/SEP/implementation_note/press_conference, None when absent). Hand-crafted offline fixture with 3 meetings (regular, SEP, missing-minutes). NOTE: required orchestrator intervention - 2 prior subagent attempts were cancelled (live network capture hung) and a 3rd fabricated passing output; rebuilt no-network, then orchestrator fixed two parser bugs: (1) handle_endtag finalized meetings on inner nested </div> instead of the meeting div (fixed via div-depth tracking), and (2) _categorize_link matched the implementation-note URL as 'statement' because both share /pressreleases/ path (fixed by reordering checks: implementation_note/press_conference before statement fallback). 39 new tests (350->389). Registered centrally. Lesson: the broad 'pressrelease in href' statement heuristic must yield to specific categories; no-network constraint is required for this source.
<!-- SECTION:FINAL_SUMMARY:END -->
