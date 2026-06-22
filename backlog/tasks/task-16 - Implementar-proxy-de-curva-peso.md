---
id: TASK-16
title: Implementar proxy de curva peso
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-22 12:11'
updated_date: '2026-06-22 12:27'
labels:
  - argentina
  - market-data
  - curve
  - proxy
  - connectors
  - model-medium
dependencies: []
priority: medium
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Construir proxy de curva peso desde cutoff Tesoro + CER/TAMAR BCRA (y CAFCI si aplica) segun analysis/arg_market_methodology.md. Modulo puro de calculo.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Construye una curva peso proxy por horizonte desde inputs de tasas Tesoro/BCRA/CAFCI
- [x] #2 Marca el resultado como proxy (no primario) y documenta supuestos
- [x] #3 Incluye tests con fixtures de inputs de tasas
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added peso curve proxy module (src/finance_news/peso_curve.py) implementing analysis/arg_market_methodology.md. Pure-logic. frozen RateInput (source tesoro_corte|bcra_cer|bcra_tamar|cafci, horizon_days, rate, classification), CurvePoint (horizon_days, rate, contributing_sources, classification='proxy'), PesoCurveProxy (points, assumptions, data_classification='proxy'). build_peso_curve_proxy(): buckets rates by horizon, anchors fixed tenors with Tesoro cutoff (primary), fills gaps with BCRA CER (short)/TAMAR (floating)/CAFCI (fund). AC#2: result + every point carry classification='proxy' with a non-empty assumptions list documenting the no-liquid-curve proxy nature. 23 tests (912->935).
<!-- SECTION:FINAL_SUMMARY:END -->
