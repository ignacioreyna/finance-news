---
id: TASK-9.14
title: Validar universo SEC IA semiconductores Mag7
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:45'
updated_date: '2026-06-20 23:57'
labels:
  - international
  - ai
  - sec
  - semiconductors
  - research
  - model-medium
dependencies: []
references:
  - analysis/source_research_ai_markets.md
parent_task_id: TASK-9
priority: low
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Antes de automatizar filings de IA/Mag7, fijar universo minimo, CIKs, formularios y campos duros de capex/data center/productividad que no conviertan el agente en stock picker.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/sec_ai_universe_validation.md con CIKs, tickers, fuentes oficiales y campos a monitorear
- [x] #2 Separar señales macro/sectoriales de métricas puramente idiosincraticas
- [x] #3 Proponer conectores atomicos posteriores solo para filings/campos confirmados
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/sec_ai_universe_validation.md. AC#1: minimum universe of 11 names (MSFT/AMZN/GOOGL/META/NVDA/AMD/AVGO/TSM/ASML/AAPL/TSLA) with forms (10-K/10-Q/8-K, 20-F/6-K for foreign) and 16 hard fields (capex, data-center revenue, AI revenue, GPU/accelerator, productivity, export controls, etc.). CRITICAL: no CIKs are verified in the research doc - all marked TO-VERIFY (must be fetched from EDGAR before implementation). AC#2: explicitly separated 13 macro/sector signals (aggregate capex, data-center buildout, export controls) from 7 idiosyncratic stock-specific metrics to avoid becoming a stock picker. AC#3: 5 atomic connectors proposed only for confirmed sources (EDGAR full-text search, EDGAR XBRL facts, 8-K parsing, BIS/Federal Register, BLS/BEA/Census macro validation).
<!-- SECTION:FINAL_SUMMARY:END -->
