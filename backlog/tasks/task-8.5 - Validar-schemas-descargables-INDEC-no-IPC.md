---
id: TASK-8.5
title: Validar schemas descargables INDEC no-IPC
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-17 01:04'
labels:
  - argentina
  - indec
  - research
  - schemas
  - model-medium
dependencies: []
references:
  - analysis/source_research_indec.md
parent_task_id: TASK-8
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigar y fijar schemas locales para EMAE, salarios, CBA/CBT, pobreza y EPH antes de crear conectores atomicos, porque las fuentes usan XLS/XLSX heterogeneos.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/indec_schema_validation.md con URLs, formato, columnas esperadas y frecuencia por dataset
- [x] #2 Identificar cuales datasets ya pueden convertirse en conectores atomicos
- [x] #3 Marcar gaps de parsing, hojas multiples o cambios historicos de formato
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Produced analysis/indec_schema_validation.md (566 lines) validating INDEC non-IPC datasets: EMAE (nivel general + sectorial), Salarios (nivel/variaciones/sector), CBA/CBT, Pobreza, EPH (tasas/informe/coef/ingreso), and Gini. For each: URLs, format (XLS/XLSX/CSV), expected columns/sheets, frequency. AC#2 ready-for-atomic-connector section identifies which datasets can become connectors now (CSV-based ones) vs need an Excel parser. AC#3 gaps section documents multi-sheet, historical format drift, totals rows, encoding, dynamic URLs, local numeric formats. URLs probed live where possible (200 OK listed) vs inferred.
<!-- SECTION:FINAL_SUMMARY:END -->
