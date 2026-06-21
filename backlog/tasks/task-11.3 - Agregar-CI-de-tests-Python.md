---
id: TASK-11.3
title: Agregar CI de tests Python
status: Done
assignee:
  - '@general-air'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-21 14:56'
labels:
  - ops
  - ci
  - testing
  - model-small
dependencies: []
references:
  - pyproject.toml
parent_task_id: TASK-11
priority: medium
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Configurar GitHub Actions o equivalente para ejecutar la suite Python en cada push/PR y evitar regresiones de conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CI instala el paquete local sin dependencias innecesarias
- [x] #2 CI ejecuta python -m unittest discover -s tests
- [x] #3 Documenta como correr la misma verificacion localmente
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added .github/workflows/python-tests.yml: runs on push/PR to main, ubuntu-latest, Python 3.11 via setup-python@v5, executes PYTHONPATH=src python -m unittest discover -s tests. AC#1: no pip install step (project is stdlib-only; uses PYTHONPATH=src to avoid unnecessary deps). AC#3: local-run instructions documented in a comment block at the top of the workflow (PYTHONPATH=src python -m unittest discover -s tests). Validated the command locally (765 tests OK).
<!-- SECTION:FINAL_SUMMARY:END -->
