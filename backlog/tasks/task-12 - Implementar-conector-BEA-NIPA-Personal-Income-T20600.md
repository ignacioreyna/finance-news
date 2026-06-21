---
id: TASK-12
title: Implementar conector BEA NIPA Personal Income (T20600)
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
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir BEA API NIPA T20600 (Personal Income) mensual. Lee BEA_API_KEY desde os.environ (opcional en tests). Validado en analysis/bea_nipa_schema_validation.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones mensuales de Personal Income con periodo, valor, unidades y fuente
- [ ] #2 Incluye fixtures/tests offline para JSON BEA y errores recuperables
- [ ] #3 Soporta BEA_API_KEY opcional sin exigirla en tests
<!-- AC:END -->
