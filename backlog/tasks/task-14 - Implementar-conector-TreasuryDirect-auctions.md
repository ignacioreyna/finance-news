---
id: TASK-14
title: Implementar conector TreasuryDirect auctions
status: To Do
assignee:
  - '@general-mid'
created_date: '2026-06-21 15:54'
labels:
  - international
  - treasury
  - auctions
  - connectors
  - model-medium
dependencies: []
priority: high
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir endpoints publicos de TreasuryDirect announced/auctioned securities para calendario y resultados de subastas. Validado en analysis/treasurydirect_api_validation.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve securities announced y auctioned con CUSIP, tipo, fechas (announcement/auction/maturity), high rate/price cuando aplica, y URL
- [ ] #2 Incluye fixtures/tests offline para JSON/HTML de TreasuryDirect
- [ ] #3 Distingue announced vs auctioned y cubre refunding pages
<!-- AC:END -->
