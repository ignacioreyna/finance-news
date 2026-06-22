---
id: TASK-16
title: Implementar proxy de curva peso
status: To Do
assignee:
  - '@general-mid'
created_date: '2026-06-22 12:11'
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
- [ ] #1 Construye una curva peso proxy por horizonte desde inputs de tasas Tesoro/BCRA/CAFCI
- [ ] #2 Marca el resultado como proxy (no primario) y documenta supuestos
- [ ] #3 Incluye tests con fixtures de inputs de tasas
<!-- AC:END -->
