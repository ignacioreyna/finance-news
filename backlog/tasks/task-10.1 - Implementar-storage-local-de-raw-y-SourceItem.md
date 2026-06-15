---
id: TASK-10.1
title: Implementar storage local de raw y SourceItem
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:46'
updated_date: '2026-06-15 17:07'
labels:
  - pipeline
  - storage
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/connector_architecture.md
  - analysis/connector_fixtures_policy.md
parent_task_id: TASK-10
priority: high
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agregar una capa local simple para guardar payloads crudos, snapshots normalizados y metadata de provenance por conector, siguiendo el contrato de conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Storage persiste raw payload, SourceItem normalizado y run metadata en rutas deterministicas
- [x] #2 Incluye tests offline de round-trip y hash/provenance
- [x] #3 No requiere base de datos externa para el MVP
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Local filesystem storage for connector payloads. src/finance_news/storage/local.py adds LocalStorage with deterministic paths (storage/<connector>/YYYY-MM/<external_id>/) persisting raw bytes (raw.bin), normalized SourceItem (normalized.json via to_dict/from_dict) and run metadata incl. SHA-256 (metadata.json). Atomic writes via temp+os.replace; stdlib only, no DB. 10 new unittest tests cover round-trip, hash/provenance, deterministic paths, atomic writes. Full suite 57 OK. Merged via feat/task-10.1-storage.
<!-- SECTION:FINAL_SUMMARY:END -->
