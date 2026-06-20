---
id: TASK-9.17
title: Implementar conector discursos Fed
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:49'
updated_date: '2026-06-20 18:50'
labels:
  - international
  - fed
  - speeches
  - connectors
  - model-medium
dependencies: []
references:
  - analysis/source_research_fed.md
parent_task_id: TASK-9
priority: medium
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consumir pagina oficial anual de speeches Fed y clasificar discursos por speaker, titulo, fecha y tags editoriales relevantes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector devuelve speeches normalizados con fecha, speaker, titulo, URL y tags
- [x] #2 Incluye fixtures/tests offline para listado anual y detalle
- [x] #3 Permite priorizar discursos por speaker o tema sin resumir extensivamente
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added Fed speeches connector (fed_speeches) parsing the Fed annual speeches listing (HTML via stdlib HTMLParser with div-depth tracking) into speeches with date, speaker, title, URL, and editorial tags (monetary_policy/banking/financial_stability/economy/regulation via keyword classification). AC#3: filter_speeches() helper prioritizes by speaker and/or tag WITHOUT summarizing body text (just selects items); covered by test. Hand-crafted listing fixture (5 speeches) + 39 offline tests (486->525). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
