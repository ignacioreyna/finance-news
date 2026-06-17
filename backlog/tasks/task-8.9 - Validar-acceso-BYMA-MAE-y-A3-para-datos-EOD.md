---
id: TASK-8.9
title: Validar acceso BYMA MAE y A3 para datos EOD
status: Done
assignee:
  - '@general-max'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-17 01:04'
labels:
  - argentina
  - market-data
  - research
  - credentials
  - model-large
dependencies: []
references:
  - analysis/source_research_arg_market.md
parent_task_id: TASK-8
priority: high
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigar acceso real, costos, credenciales y endpoints disponibles para BYMA EOD/indices, MAE market data y A3/Matba Rofex antes de crear conectores de mercado local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/arg_market_access_validation.md con requisitos de alta, costo, limites y URLs por proveedor
- [x] #2 Determinar si BYMA EOD/indices gratis alcanza para bonos, MEP/CCL y curva local
- [x] #3 Proponer tareas atomicas de conectores solo para fuentes confirmadas
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/arg_market_access_validation.md (198 lines). RESEARCH-ONLY VERDICT (no paid credentials pursued). AC#1: per-provider table of alta/costo/limites/URLs (BYMA Snapshot USD400/mes, Delay USD100/mes, EOD free 1000 req/mes + alta/token; MAE web/API; A3; Matba Rofex visor/CEM/CCL-MtR; BCRA; Tesoro; Rava; Ambito rate-limit 100). AC#2: free BYMA EOD does NOT suffice for bonos/MEP-CCL/curva (1000 req/mo blown by bonds+parities+ladder; api.bymadata.com.ar unreachable HTTP 000). AC#3: proposed ONLY free/public atomic connectors (bcra_fx_usd, bcra_monetary_rates, tesoro_licitaciones, matbarofex_ccl_mtr_scrape, byma_ccl_indice_scrape (visor, not paid API), rava_bonds_and_rp_scrape, mep_ccl_derived, peso_curve_proxy); BYMA-paid, MAE-API, Matba-Rofex-API deferred/blocked. Verified-live vs inferred URLs listed.
<!-- SECTION:FINAL_SUMMARY:END -->
