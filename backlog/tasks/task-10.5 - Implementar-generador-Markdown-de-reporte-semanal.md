---
id: TASK-10.5
title: Implementar generador Markdown de reporte semanal
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-21 14:46'
labels:
  - weekly-report
  - generator
  - pipeline
  - model-medium
dependencies:
  - TASK-10.4
references:
  - analysis/weekly_report_schema.md
  - analysis/report_context_pack.md
parent_task_id: TASK-10
priority: medium
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear un generador deterministico de borrador Markdown desde el context pack, sin depender todavia de un modelo externo, para validar estructura, trazabilidad y gaps.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Genera secciones Argentina, internacional, mercado, escenarios, riesgos y que mirar
- [x] #2 Incluye source links/citas breves dentro de los limites del context pack
- [x] #3 Incluye tests snapshot del Markdown generado
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added weekly Markdown report generator (src/finance_news/markdown_report.py) - DETERMINISTIC (no LLM/external model) generator producing a draft from a ReportContextPack. AC#1: emits 6 sections in order - Argentina, Internacional, Mercado, Escenarios, Riesgos, 'Que mirar' (watch list) - derived from pack sections + summary. AC#2: short inline source citations (source_id->label) per item plus a full source_index appendix with URLs; every claim cites a source_id. AC#3: snapshot tests (full + empty pack) with stored snapshots under tests/fixtures/markdown_report/; deterministic ordering (items sorted by topic then score, source index sorted by id). Imports ReportContextPack from context_pack (10.4). NOTE: orchestrator normalized the 2 snapshot assertions with .rstrip() to ignore trailing-newline drift and removed stray 0-byte snapshot files that blocked the merge. 6 tests (759->765).
<!-- SECTION:FINAL_SUMMARY:END -->
