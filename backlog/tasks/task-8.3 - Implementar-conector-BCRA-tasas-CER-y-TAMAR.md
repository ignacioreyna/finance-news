---
id: TASK-8.3
title: Implementar conector BCRA tasas CER y TAMAR
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-15 18:29'
labels:
  - argentina
  - bcra
  - rates
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-8
priority: high
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir fuentes oficiales BCRA para CER, TAMAR y tasas relacionadas que alimentan lectura de curva local y condiciones monetarias.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve observaciones normalizadas de CER y TAMAR con fecha, valor, fuente y frecuencia
- [x] #2 Incluye fixtures/tests offline para CSV/XLS/API segun fuente elegida
- [x] #3 Separa datos de tasas de normas BCRA sobre encajes o liquidez
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
BCRA CER/TAMAR rates connector. connectors/bcra_tasas_cer_tamar.py: BcraTasasCerTamarConnector + pure parser parse_bcra_monetarias_response(); public BCRA monetarias endpoint, variable IDs 30 (CER) and 44 (TAMAR) (no key). Normalized rate observations (fecha, valor, fuente, frecuencia) with rate_name. AC#3: rates kept separate from BCRA normas via content_type metadata + distinct fields. Live-captured fixtures. 21 new unittest tests; registered as bcra_tasas_cer_tamar. Full suite 129 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
