---
id: TASK-9.9
title: Implementar conector Fed H41 liquidity
status: To Do
assignee: []
created_date: '2026-06-15 02:45'
labels:
  - international
  - fed
  - h41
  - liquidity
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
  - analysis/source_research_us_liquidity.md
parent_task_id: TASK-9
priority: high
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir Federal Reserve H.4.1 Data Download para snapshot semanal de reservas, TGA, ON RRP, securities held outright y total assets.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve observaciones semanales H.4.1 normalizadas por serie clave
- [ ] #2 Incluye fixtures/tests offline para CSV/XML o payload descargado
- [ ] #3 Documenta diferencias de frecuencia frente a FiscalData DTS
<!-- AC:END -->
