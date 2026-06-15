---
id: TASK-9.18
title: Implementar conector NY Fed repo y reverse repo
status: To Do
assignee: []
created_date: '2026-06-15 02:49'
labels:
  - international
  - nyfed
  - repo
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: medium
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir operaciones repo/reverse repo de NY Fed para montos aceptados, tasas y participantes cuando esten disponibles.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve operaciones normalizadas con fecha, tipo, monto, tasa, participantes si existen y fuente
- [ ] #2 Incluye fixtures/tests offline para pagina/API/archivo historico
- [ ] #3 Distingue ON RRP de repo/SRF y marca fuente primaria
<!-- AC:END -->
