---
id: TASK-8.7
title: Validar descargas de vencimientos y cashflows Tesoro
status: Done
assignee:
  - '@general-max'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-17 01:04'
labels:
  - argentina
  - tesoro
  - debt
  - research
  - model-large
dependencies: []
references:
  - analysis/source_research_tesoro.md
parent_task_id: TASK-8
priority: high
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Antes de implementar calendario de deuda, validar los archivos oficiales de estructura financiera/cupones/vencimientos, sus URLs finales y estabilidad de columnas.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/tesoro_cashflows_schema_validation.md con fuentes, enlaces finales, formatos y columnas requeridas
- [x] #2 Definir si el primer conector debe leer XLS/XLSX, CSV, PDF o combinacion
- [x] #3 Identificar reglas para evitar doble conteo entre vencimientos, canjes y conversiones
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/tesoro_cashflows_schema_validation.md (460 lines). Verified (live 200) the cashflow endpoints on Mecon: estructura-financiera-de-titulos-publicos (estructura_financiera_*.xlsx versioned + cupones.xlsx 116-sheet unversioned) and datos-trimestrales-de-la-deuda (deuda_publica_DD-MM-YYYY.xlsx, 2026 quarters 404 = normal lag). AC#2: first connector should read XLSX via lazy openpyxl (mirroring bcra_balance_cambiario); CSV not published; PDF only as fallback. AC#3: 14 double-counting rules across 7 axes (stock vs servicio per-unit coefficients, canjes netted, conversiones tagged, partition by moneda, exclude intra-sector-publico, capitalize-don't-pay, re-baseline on each version). Flagged critical trap: cupones are per-unit coefficients (not aggregates) and CER uses the 10-business-day-pre rate. cronograma-2026 recovered (200) but out of scope (licitaciones).
<!-- SECTION:FINAL_SUMMARY:END -->
