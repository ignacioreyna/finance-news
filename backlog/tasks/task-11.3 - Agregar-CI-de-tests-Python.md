---
id: TASK-11.3
title: Agregar CI de tests Python
status: To Do
assignee: []
created_date: '2026-06-15 02:47'
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
- [ ] #1 CI instala el paquete local sin dependencias innecesarias
- [ ] #2 CI ejecuta python -m unittest discover -s tests
- [ ] #3 Documenta como correr la misma verificacion localmente
<!-- AC:END -->
