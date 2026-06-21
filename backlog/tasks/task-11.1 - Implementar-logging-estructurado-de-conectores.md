---
id: TASK-11.1
title: Implementar logging estructurado de conectores
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-21 14:56'
labels:
  - ops
  - logging
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_quality_matrix.md
  - analysis/connector_architecture.md
parent_task_id: TASK-11
priority: medium
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agregar helpers para logs de partial_failure y run_summary alineados con la matriz de calidad de conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Los conectores pueden emitir eventos connector.partial_failure y connector.run_summary con campos requeridos
- [x] #2 Incluye tests unitarios del formato de log/evento
- [x] #3 Runner o helper no imprime secretos ni payloads crudos completos
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added structured connector logging (src/finance_news/connector_logging.py). Frozen PartialFailureEvent and RunSummaryEvent dataclasses (to_dict/from_dict) emitting connector.partial_failure and connector.run_summary events with the required fields from connector_quality_matrix.md. AC#3: _redact() recursively strips 13 secret keys (api_key/token/password/authorization/userid etc, case-insensitive) and truncates raw_body/payload/body/content to 256 bytes with a size+hash marker; emit_event returns a dict (never prints), log_event routes JSON to stdlib logging. 33 unit tests (765->798).
<!-- SECTION:FINAL_SUMMARY:END -->
