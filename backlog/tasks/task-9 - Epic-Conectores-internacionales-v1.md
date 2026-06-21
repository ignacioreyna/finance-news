---
id: TASK-9
title: 'Epic: Conectores internacionales v1'
status: Done
assignee: []
created_date: '2026-06-15 02:42'
updated_date: '2026-06-20 23:57'
labels:
  - epic
  - international
  - connectors
  - phase-2
  - model-medium
dependencies: []
priority: high
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implementar la primera capa productiva de conectores internacionales a partir de los research docs: Fed/FOMC, BLS/BEA/DOL, Treasury/liquidez USD, commodities/geoeconomia e IA/semiconductores. Priorizar fuentes oficiales machine-readable y marcar proxies.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Epic complete: 16 international connectors registered (fomc_calendario/statements/minutes/sep, fed_speeches, fed_h41_liquidity, dol_weekly_claims, bls_timeseries, fred_market_proxies, eia_wpsr, opec_eventos, treasury_dts_tga/cashflows, nyfed_sofr/repo/soma) + 3 validation docs (BEA NIPA, TreasuryDirect, SEC AI). Optional API keys wired via settings.py .env loader (BLS/FRED/EIA/BEA).
<!-- SECTION:FINAL_SUMMARY:END -->
