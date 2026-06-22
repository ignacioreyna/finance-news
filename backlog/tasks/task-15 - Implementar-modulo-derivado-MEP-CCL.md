---
id: TASK-15
title: Implementar modulo derivado MEP/CCL
status: To Do
assignee:
  - '@general-mid'
created_date: '2026-06-22 12:11'
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
- [ ] #1 Computa MEP y CCL desde pares de precios ARS/USD del mismo soberano (sufijo C para MEP via CI, sufijo D para CCL offshore) y devuelve valor, paridad, decision de publicacion/supresion
- [ ] #2 Separa dato primario (precios) de calculo derivado (MEP/CCL) y marca el resultado como derivado
- [ ] #3 Aplica filtros de confianza del metodograma (acuerdo dual-pair 1.5%/2% flag, >5% suprime; outlier/stale) con tests fixture
<!-- AC:END -->
