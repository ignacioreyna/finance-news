---
id: TASK-9.15
title: Implementar conector minutes FOMC
status: To Do
assignee: []
created_date: '2026-06-15 02:48'
labels:
  - international
  - fed
  - fomc
  - connectors
  - model-medium
dependencies:
  - TASK-9.1
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: medium
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir minutes oficiales FOMC desde URLs de reunion y extraer texto limpio con secciones de actividad, inflacion, empleo, riesgos, balance y directive operativa.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector normaliza minutes con fecha, URL, texto limpio y secciones principales
- [ ] #2 Incluye fixtures/tests offline para HTML/PDF o texto representativo
- [ ] #3 Puede operar sobre URLs descubiertas por el calendario FOMC
<!-- AC:END -->
