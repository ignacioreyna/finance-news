---
id: TASK-8.10
title: Definir metodologia MEP CCL y spread soberano proxy
status: Done
assignee:
  - '@general-max'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-17 01:04'
labels:
  - argentina
  - market-data
  - methodology
  - research
  - model-large
dependencies: []
references:
  - analysis/source_research_arg_market.md
  - analysis/report_context_pack.md
parent_task_id: TASK-8
priority: medium
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Diseñar metodologia versionada para calcular MEP/CCL por especies, curva local y proxy de riesgo soberano sin depender de datos pagos no confirmados.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/arg_market_methodology.md con formulas, universo minimo de especies y supuestos
- [x] #2 Separar dato primario de precio, calculo derivado y proxy secundario
- [x] #3 Definir criterios de confianza para incluir el dato en reporte semanal
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/arg_market_methodology.md (298 lines). AC#1: MEP = Precio_ARS(bono)/Precio_USD(bono) same sovereign, C-suffix tranche settles via CI/Caja de Valores; CCL = same ratio on D-suffix tranche settles offshore (Euroclear/CB); explicitly flags CCL=MEP*(1+k) as INCORRECT (emerges from distinct-tranche prices). Sovereign-spread proxy = TIR(bono_D) - YTM(UST duration-matched), labeled proxy/no-EMBI. Minimum species: AL30/GD30 primary + AL29/GD35/GD38 cross-checks, C and D tranches, each classified primary-public vs proxy. AC#2: separates raw prices / derived computations (mep_ccl_calculated, brecha_cambiaria, sovereign_spread_proxy) / secondary proxies with a no-mixing rule. AC#3: 5 confidence filters (freshness TTL, volume/bid-acceptance w/ weak mode if no volume field, outlier rejection, dual-pair agreement 1.5%/2% flag & >5% suppress, <3% index concordance) mapped to a publish/suppress matrix. Free-source constraint respected (no BYMA paid); open risks: free-EOD volume-field dependency, calibration debt on numeric thresholds, pari-passu assumption breaks on restructure.
<!-- SECTION:FINAL_SUMMARY:END -->
