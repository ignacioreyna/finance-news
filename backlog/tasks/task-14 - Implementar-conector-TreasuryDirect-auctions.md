---
id: TASK-14
title: Implementar conector TreasuryDirect auctions
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-21 15:54'
updated_date: '2026-06-21 23:47'
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
- [x] #1 El conector devuelve securities announced y auctioned con CUSIP, tipo, fechas (announcement/auction/maturity), high rate/price cuando aplica, y URL
- [x] #2 Incluye fixtures/tests offline para JSON/HTML de TreasuryDirect
- [x] #3 Distingue announced vs auctioned y cubre refunding pages
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added TreasuryDirect auctions connector (treasurydirect_auctions) consuming the public TreasuryDirect TA_WS endpoints (announced + auctioned securities, no key). Parses JSON into normalized auction records with status (announced/auctioned), CUSIP, security_type, announcement/auction/maturity dates, high_rate (None until auctioned), amount, url. AC#3: status field distinguishes announced vs auctioned; is_refunding flag covers refunding/reopening auctions (with [REFUNDING/REOPENING] marker + metadata note). Hand-crafted fixture (3 announced + 4 auctioned incl. 1 refunding) + recoverable-error tests. 21 offline tests (833->854). Endpoints INFERRED from research doc (not live-probed). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
