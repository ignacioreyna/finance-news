---
id: TASK-11.5
title: Implementar reporte de calidad de conectores
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-21 14:56'
labels:
  - ops
  - quality
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_quality_matrix.md
parent_task_id: TASK-11
priority: medium
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una herramienta que recorra conectores/resultados y produzca un reporte de freshness, completitud, provenance, errores y cobertura de tests.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reporte muestra estado por conector con severidad S0/S1/S2/S3
- [x] #2 Incluye freshness por tipo de fuente diaria/semanal/mensual/evento
- [x] #3 Incluye tests con conectores/resultados fixture
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added connector quality report (src/finance_news/quality_report.py) implementing connector_quality_matrix.md. Frozen dataclasses (to_dict/from_dict): ConnectorQuality (severity S0/S1/S2/S3, freshness_status, completeness, provenance_present, last_error, test_coverage), QualityReport, FreshnessEvaluation. Enums: Severity, SourceFrequency (daily/weekly/monthly/event), FreshnessStatus. QualityReporter.build_report(connector_results). AC#1: S0(bloqueante)/S1(critico)/S2(mayor)/S3(menor). AC#2: freshness thresholds per frequency (daily<=6h/24h, weekly<=48h/168h, monthly<=72h/240h, event<=1h/6h). 35 tests covering all severities, frequencies, provenance, summary aggregation (765->800).
<!-- SECTION:FINAL_SUMMARY:END -->
