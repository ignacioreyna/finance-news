---
id: TASK-4.1
title: Implementar conector BCRA Comunicaciones A
status: To Do
assignee: []
created_date: '2026-06-14 14:51'
labels:
  - argentina
  - bcra
  - connectors
  - model-medium
dependencies:
  - TASK-3.2
references:
  - >-
    https://github.com/colossus-lab/vigia/tree/main/packages/connectors/src/vigia_connectors/bcra.py
parent_task_id: TASK-4
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Portar/adaptar el enfoque de vigia_connectors.bcra para consumir Comunicaciones A del BCRA como fuente normativa cambiaria/financiera. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Conector descarga PDFs de Comunicaciones A por numero y devuelve items normalizados
- [ ] #2 Incluye parser de titulo, fecha, url, texto extraido y external_id
- [ ] #3 Incluye fixtures/tests offline para parsing y al menos una prueba controlada de existencia/fetch documentada
<!-- AC:END -->
