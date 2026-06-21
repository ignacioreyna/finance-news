---
id: TASK-12
title: Implementar conector BEA NIPA Personal Income (T20600)
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-21 15:54'
updated_date: '2026-06-21 23:47'
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
- [x] #1 El conector devuelve observaciones mensuales de Personal Income con periodo, valor, unidades y fuente
- [x] #2 Incluye fixtures/tests offline para JSON BEA y errores recuperables
- [x] #3 Soporta BEA_API_KEY opcional sin exigirla en tests
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added BEA NIPA Personal Income connector (bea_personal_income) consuming the BEA API (apps.bea.gov/api/data/, DataSetName=NIPA, TableName=T20600, Frequency=M). Parses {BEAAPI:{Results:{Data:[{TimePeriod,DataValue,CL_UNIT}]}}} into monthly observations (period, value, units, fuente='BEA NIPA T20600'). AC#2: hand-crafted success/empty JSON fixtures + recoverable-error tests (5xx->Recoverable, 4xx->ValueError, malformed JSON->ValueError). AC#3: BEA_API_KEY optional (read via os.environ in live fetch only; default tests run with NO key; one test sets a key and asserts inclusion in request params). 28 offline tests (833->861). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
