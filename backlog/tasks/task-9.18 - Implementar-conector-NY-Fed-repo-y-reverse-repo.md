---
id: TASK-9.18
title: Implementar conector NY Fed repo y reverse repo
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:49'
updated_date: '2026-06-20 13:19'
labels:
  - international
  - nyfed
  - repo
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: medium
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir operaciones repo/reverse repo de NY Fed para montos aceptados, tasas y participantes cuando esten disponibles.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve operaciones normalizadas con fecha, tipo, monto, tasa, participantes si existen y fuente
- [x] #2 Incluye fixtures/tests offline para pagina/API/archivo historico
- [x] #3 Distingue ON RRP de repo/SRF y marca fuente primaria
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added NY Fed repo connector (nyfed_repo) consuming NY Fed Markets operations for ON RRP and SRF (standing repo facility) into normalized operations with operation_date, type (on_rrp/srf_repo), total amount accepted, award rate, counterparty count when published, fuente. AC#3: distinguishes on_rrp vs srf_repo via operation_type field and marks NY Fed as DATA_CLASSIFICATION=primary - covered by test. Hand-crafted JSON fixture (both op types) + offline tests (389->417). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
