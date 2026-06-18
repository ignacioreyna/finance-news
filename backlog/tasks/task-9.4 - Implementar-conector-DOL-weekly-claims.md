---
id: TASK-9.4
title: Implementar conector DOL weekly claims
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:44'
updated_date: '2026-06-18 12:34'
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
- [x] #1 El conector devuelve initial claims y continued claims con semana, valor, revision si existe y fuente
- [x] #2 Incluye fixtures/tests offline para XML o spreadsheet convertido a fixture estable
- [x] #3 Documenta fallback si la pagina solo publica HTML/PDF en una semana
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added DOL weekly claims connector (dol_weekly_claims) parsing the DOL/ETA weekly claims feed (XML primary via stdlib xml.etree, CSV fallback) into initial+continued claims with week_ending, value, prior_week_revised (revision when published, else None) and fuente. AC#3 fallback documented via FALLBACK_BEHAVIOR_DOCUMENTED constant + connector docstring (raises RecoverableConnectorError to retry when only HTML/PDF available rather than fragile parsing). Offline XML fixture + 28 tests (303->331). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
