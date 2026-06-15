---
id: TASK-10.2
title: Implementar runner CLI de conectores
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-15 17:21'
labels:
  - pipeline
  - cli
  - connectors
  - model-medium
dependencies:
  - TASK-10.1
references:
  - analysis/connector_architecture.md
  - analysis/connector_quality_matrix.md
parent_task_id: TASK-10
priority: high
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una CLI local para ejecutar conectores por nombre, ventana temporal y modo offline/online, persistiendo resultados en el storage local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CLI permite listar conectores disponibles y ejecutar uno por nombre
- [x] #2 Permite dry-run/offline usando fixtures cuando el conector lo soporte
- [x] #3 Registra run summary con conteo de items, errores recuperables y ruta de salida
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Connector runner CLI. src/finance_news/cli/{runner,__main__}.py provide an argparse CLI: 'list' prints available connectors from a new registry in connectors/__init__.py (available_connectors/get_connector, additive); 'run <name>' executes a connector with --offline, --storage, --limit, --cursor, --from options. Offline mode loads fixtures via finance_news.testing.fixtures and runs the connector's parser; unsupported-offline connectors exit with a clear message. RunSummary (items_count, recoverable_errors_count, storage_path) is returned by run_connector() and printed. scripts/finance-news.sh wrapper (mirrors backlog.sh) sets PYTHONPATH=src so the CLI is invokable. 9 new unittest tests incl. 2 subprocess end-to-end CLI tests. Full suite 66 OK. Merged via feat/task-10.2-runner.
<!-- SECTION:FINAL_SUMMARY:END -->
