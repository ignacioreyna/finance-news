---
id: TASK-8.3
title: Implementar conector BCRA tasas CER y TAMAR
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
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
- [ ] #1 El conector devuelve observaciones normalizadas de CER y TAMAR con fecha, valor, fuente y frecuencia
- [ ] #2 Incluye fixtures/tests offline para CSV/XLS/API segun fuente elegida
- [ ] #3 Separa datos de tasas de normas BCRA sobre encajes o liquidez
<!-- AC:END -->
