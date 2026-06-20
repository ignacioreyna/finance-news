---
id: TASK-9.15
title: Implementar conector minutes FOMC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:48'
updated_date: '2026-06-20 18:50'
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
- [x] #1 El conector normaliza minutes con fecha, URL, texto limpio y secciones principales
- [x] #2 Incluye fixtures/tests offline para HTML/PDF o texto representativo
- [x] #3 Puede operar sobre URLs descubiertas por el calendario FOMC
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added FOMC minutes connector (fomc_minutes) consuming a single FOMC minutes URL (passed as cursor from fomc_calendario, no calendar re-discovery per AC#3) and parsing the HTML via stdlib HTMLParser into date, clean full text, and a dict of normalized main sections (financial_markets, economic_outlook, staff_outlook, policy_discussion, financial_review, policy_action). Tolerant: missing sections yield empty text, never crash. Hand-crafted HTML fixture + 19 offline tests (486->505). Registered centrally.
<!-- SECTION:FINAL_SUMMARY:END -->
