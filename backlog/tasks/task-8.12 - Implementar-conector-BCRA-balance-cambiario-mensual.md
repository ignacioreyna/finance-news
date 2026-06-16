---
id: TASK-8.12
title: Implementar conector BCRA balance cambiario mensual
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-16 06:31'
labels:
  - argentina
  - bcra
  - fx
  - balance-cambiario
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
parent_task_id: TASK-8
priority: medium
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir Evolucion del Mercado de Cambios y Balance Cambiario del BCRA para compras/ventas agregadas y rubros cambiarios mensuales.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve observaciones mensuales por rubro con periodo, monto, unidad y fuente
- [x] #2 Incluye fixtures/tests offline para descarga machine-readable identificada
- [x] #3 Documenta explicitamente que no reemplaza intervencion diaria neta
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Deferred after first attempt: live source is XLSX-only (needs openpyxl). Retry approach: lazy-import openpyxl in fetch_page (mirror the pypdf lazy-import pattern in bcra_comunicaciones_a), do NOT add openpyxl to pyproject; keep a CSV parser for offline tests; ensure parser matches its own fixture and actually run the suite.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added BCRA balance cambiario connector (bcra_balance_cambiario) for the monthly FX market balance, parsing rows into per-rubro observations (period/rubro/compras/ventas/saldo, USD unit) via a deterministic header-based column mapper. Lazy openpyxl import (OpenpyxlRowExtractor instantiated only inside fetch_page; module imports with stdlib only, connector instantiates without openpyxl) mirroring the pypdf pattern; missing-extractor path raises MissingXlsxExtractorError. CSV fixture + offline tests (FakeTransport + injected CSV row extractor) cover the 200/404/5xx/other status matrix, decimal parsing (incl. thousands+decimal '1,000.5'), NA handling, and the openpyxl-absent path. AC#3: DOES_NOT_REPLACE_NET_INTERVENTION=True surfaced into item metadata. 25 new tests (251->276). Registered centrally. NOTE: a prior attempt fabricated passing output and shipped an eager openpyxl __init__ import + a placeholder fetch_page; that was scrapped and rebuilt cleanly. Known limitation: DEFAULT_XLSX_URL points at the stats page (research doc lacks a stable direct XLSX link); live XLSX URL resolution is an operational follow-up.
<!-- SECTION:FINAL_SUMMARY:END -->
