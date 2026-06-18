---
id: TASK-9.6
title: Implementar conector Treasury DTS TGA
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-18 12:34'
labels:
  - international
  - treasury
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir FiscalData Daily Treasury Statement operating_cash_balance para TGA diaria y cambios diario/semanal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve TGA Federal Reserve Account con fecha, open/close balance y cambio diario
- [x] #2 Incluye fixtures/tests offline para JSON FiscalData
- [x] #3 Define freshness diaria y manejo de dias no habiles federales
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added Treasury DTS TGA connector (treasury_dts_tga) consuming the FiscalData Daily Treasury Statement API (operating_cash_balance, account_type=Federal Reserve Account) into TGA observations with record_date, open_today_bal, close_today_bal, daily_change (close-open), in USD millions. AC#3: DEFAULT_TTL_SECONDS=24h (daily freshness); federal holiday/weekend handling returns empty PageResult (no error) since FiscalData DTS only publishes on business days, documented in docstring + metadata.holiday_handling. Real FiscalData JSON fixture + empty-response fixture + 19 offline tests (303->322). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
