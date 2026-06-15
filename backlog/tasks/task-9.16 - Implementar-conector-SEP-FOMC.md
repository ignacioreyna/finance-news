---
id: TASK-9.16
title: Implementar conector SEP FOMC
status: To Do
assignee: []
created_date: '2026-06-15 02:48'
labels:
  - international
  - fed
  - fomc
  - sep
  - connectors
  - model-medium
dependencies:
  - TASK-9.1
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: medium
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir projection materials en reuniones FOMC con SEP y extraer medianas de GDP, unemployment, PCE, core PCE y fed funds cuando el formato lo permita.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector identifica reuniones con SEP y devuelve proyecciones normalizadas por variable/horizonte
- [ ] #2 Incluye fixtures/tests offline para material SEP representativo
- [ ] #3 Marca limitaciones si dots/dispersión requieren parsing manual o PDF complejo
<!-- AC:END -->
