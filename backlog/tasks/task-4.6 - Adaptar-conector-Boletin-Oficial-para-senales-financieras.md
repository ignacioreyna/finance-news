---
id: TASK-4.6
title: Adaptar conector Boletin Oficial para senales financieras
status: To Do
assignee: []
created_date: '2026-06-14 14:51'
labels:
  - argentina
  - bora
  - connectors
  - model-medium
dependencies:
  - TASK-3.2
references:
  - >-
    https://github.com/colossus-lab/vigia/tree/main/packages/connectors/src/vigia_connectors/bora.py
parent_task_id: TASK-4
priority: medium
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Definir y luego implementar un filtro de Boletin Oficial enfocado en normas economicas/financieras relevantes para el agente. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Usar el patron de vigia_connectors.bora para listado/detalle por fecha
- [ ] #2 Filtrar organismos y keywords economicas: BCRA, Economia, ARCA, CNV, deuda, cambios, energia, mineria, agro
- [ ] #3 Incluir fixtures/tests offline de parsing y clasificacion
<!-- AC:END -->
