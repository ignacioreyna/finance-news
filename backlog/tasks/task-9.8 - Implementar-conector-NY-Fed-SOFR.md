---
id: TASK-9.8
title: Implementar conector NY Fed SOFR
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-18 12:34'
labels:
  - international
  - nyfed
  - sofr
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir NY Fed Markets API para SOFR, volumen y percentiles como indicador de funding secured.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve SOFR, volumen y percentiles con effectiveDate y source_url
- [x] #2 Incluye fixtures/tests offline para JSON de NY Fed
- [x] #3 Marca SOFR como dato primario y FRED SOFR solo como proxy/fallback
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added NY Fed SOFR connector (nyfed_sofr) consuming the NY Fed Markets API for SOFR rate, total volume, and percentiles (1st/25th/75th/99th) with effectiveDate and source_url in provenance/metadata. AC#3: marks NY Fed SOFR as DATA_CLASSIFICATION='primary' and documents FRED SOFR as proxy/fallback only, surfaced into item metadata; covered by test. JSON fixture + offline tests (303->325 in worktree). Registered centrally. NOTE: an initial parallel-suite verification falsely showed a CLI test failure; root cause was a pre-existing cross-worktree race on fixed /tmp/test_storage_cli* paths (not a connector defect) — passes reliably when run sequentially (3x OK).
<!-- SECTION:FINAL_SUMMARY:END -->
