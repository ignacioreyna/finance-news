---
id: TASK-5.3
title: Investigar fuentes Treasury y liquidez USD
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:52'
updated_date: '2026-06-14 23:41'
labels:
  - international
  - treasury
  - liquidity
  - research
  - model-large
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-5
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapear fuentes para Treasury issuance/refunding, TGA, SOMA, repo/SOFR, QT/QE y liquidez que el host usa para leer condiciones financieras. Modelo recomendado: large.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_us_liquidity.md con fuentes, endpoints, series y frecuencia
- [x] #2 Separar Treasury, NY Fed, FRED u otros agregadores si aplican
- [x] #3 Indicar cuales son datos primarios y cuales son proxies
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar analysis/host_profile.md, source_catalog, source_research_fed y source_research_us_macro.
2. Investigar fuentes oficiales Treasury, NY Fed, Fed/FRED para issuance/refunding, TGA, SOMA, repo/SOFR, QT/QE y liquidez.
3. Crear analysis/source_research_us_liquidity.md separando fuentes primarias y proxies/agregadores.
4. Actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Cree analysis/source_research_us_liquidity.md con mapa de fuentes Treasury, NY Fed, Federal Reserve y FRED para TGA, issuance/refunding, SOMA, repo/SOFR, QT/QE y liquidez USD.

- Verifique via curl los endpoints oficiales FiscalData de DTS operating cash balance y deposits/withdrawals; verifique NY Fed SOFR last JSON.

- Marque TreasuryDirect API como fuente oficial pendiente de revalidar en implementacion por falla local de shell con ?format=json; documente el supuesto y evite usar el endpoint FiscalData auction_query que devolvio 404.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Investigue y documente fuentes oficiales y proxies para Treasury y liquidez USD.

Cambios:
- Agregue analysis/source_research_us_liquidity.md con fuentes, URLs/endpoints, frecuencia, formato, tipo primario/proxy y uso operativo.
- Separe Treasury/FiscalData/TreasuryDirect, New York Fed, Federal Reserve Board y FRED/agregadores.
- Propuse conectores atomicos para TGA/DTS, cashflows, auctions/refunding, H.4.1, SOFR, repo/RRP, SOMA y FRED fallback.

Verificacion:
- ./scripts/backlog.sh task 5.3 --plain
- curl FiscalData DTS operating_cash_balance
- curl FiscalData DTS deposits_withdrawals_operating_cash
- curl NY Fed SOFR last JSON
- sed/wc sanity check sobre analysis/source_research_us_liquidity.md

Riesgo:
- TreasuryDirect API queda marcada para revalidacion quoted en implementacion; la URL es oficial, pero la prueba local fallo por expansion de ? en zsh.
<!-- SECTION:FINAL_SUMMARY:END -->
