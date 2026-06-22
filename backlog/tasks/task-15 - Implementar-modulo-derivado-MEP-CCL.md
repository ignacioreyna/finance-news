---
id: TASK-15
title: Implementar modulo derivado MEP/CCL
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-22 12:11'
updated_date: '2026-06-22 12:27'
labels:
  - argentina
  - market-data
  - mep
  - ccl
  - connectors
  - model-medium
dependencies: []
priority: high
ordinal: 83000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Calcular MEP y CCL a partir de precios ARS/USD del mismo soberano (tramos C y D) segun analysis/arg_market_methodology.md. Modulo puro de calculo (no scrapea).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Computa MEP y CCL desde pares de precios ARS/USD del mismo soberano (sufijo C para MEP via CI, sufijo D para CCL offshore) y devuelve valor, paridad, decision de publicacion/supresion
- [x] #2 Separa dato primario (precios) de calculo derivado (MEP/CCL) y marca el resultado como derivado
- [x] #3 Aplica filtros de confianza del metodograma (acuerdo dual-pair 1.5%/2% flag, >5% suprime; outlier/stale) con tests fixture
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added MEP/CCL derived calculation module (src/finance_news/mep_ccl.py) implementing analysis/arg_market_methodology.md. Pure-logic (no scraping). frozen BondPrice (input: isin/specie, currency ARS|USD, tranche C|D, price, as_of_date, source_classification) and MepCclResult (output: mep, ccl, brecha, data_classification='derived', inputs_used, publish_decision publish|flag|suppress, confidence alta|media|baja, rationale). compute_mep_ccl(): MEP = ARS/USD on C-suffix tranche (CI/Caja de Valores), CCL = ARS/USD on D-suffix tranche (offshore) - does NOT model CCL=MEP*(1+k) (flagged incorrect in the doc). AC#2: results marked derived, primary prices listed separately in inputs_used. AC#3: confidence filters - dual-pair agreement >1.5% flag, >2% lower confidence, MEP/CCL cross-pair >5% SUPPRESS; outlier/stale rejection. 44 tests (912->956).
<!-- SECTION:FINAL_SUMMARY:END -->
