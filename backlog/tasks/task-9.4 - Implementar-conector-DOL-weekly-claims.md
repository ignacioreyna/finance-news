---
id: TASK-9.4
title: Implementar conector DOL weekly claims
status: To Do
assignee: []
created_date: '2026-06-15 02:44'
labels:
  - international
  - dol
  - labor
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_us_macro.md
parent_task_id: TASK-9
priority: medium
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir fuente oficial semanal de initial/continued claims desde DOL cuando haya XML/spreadsheet disponible, como indicador laboral de alta frecuencia.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve initial claims y continued claims con semana, valor, revision si existe y fuente
- [ ] #2 Incluye fixtures/tests offline para XML o spreadsheet convertido a fixture estable
- [ ] #3 Documenta fallback si la pagina solo publica HTML/PDF en una semana
<!-- AC:END -->
