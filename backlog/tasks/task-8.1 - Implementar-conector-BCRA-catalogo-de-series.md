---
id: TASK-8.1
title: Implementar conector BCRA catalogo de series
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
labels:
  - argentina
  - bcra
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_bcra.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-8
priority: high
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear un conector/helper que descubra y exponga metadatos de series BCRA necesarias para los conectores de datos oficiales, evitando hardcodear IDs cuando el hub/API lo permita.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El conector devuelve un catalogo normalizado de series BCRA relevantes con id, nombre, unidad, frecuencia y fuente
- [ ] #2 Incluye fixtures/tests offline para parsing de metadata o respuesta API
- [ ] #3 Documenta fallback cuando una serie requerida no aparece en el catalogo
<!-- AC:END -->
