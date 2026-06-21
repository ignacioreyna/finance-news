---
id: TASK-13
title: Implementar conector BEA NIPA Real GDP (T10101)
status: To Do
assignee:
  - '@general-mid'
created_date: '2026-06-21 15:54'
labels:
  - international
  - bea
  - macro
  - connectors
  - model-medium
dependencies: []
priority: high
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir BEA API NIPA T10101 (Real GDP, percent change) trimestral. Lee BEA_API_KEY desde os.environ (opcional en tests). Validado en analysis/bea_nipa_schema_validation.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones trimestrales de Real GDP con periodo, valor, unidades y fuente
- [ ] #2 Incluye fixtures/tests offline para JSON BEA y errores recuperables
- [ ] #3 Soporta BEA_API_KEY opcional sin exigirla en tests
<!-- AC:END -->
