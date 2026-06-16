---
id: TASK-8.6
title: Implementar scraper Tesoro licitaciones y resultados
status: Done
assignee:
  - '@general-max'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-16 01:37'
labels:
  - argentina
  - tesoro
  - debt
  - connectors
  - model-large
dependencies: []
references:
  - analysis/source_research_tesoro.md
parent_task_id: TASK-8
priority: high
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear conector para llamadas y resultados oficiales de licitaciones del Tesoro argentino, resolviendo noticias/listados y links finales cuando esten publicados.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El conector entrega eventos normalizados de llamado y resultado por instrumento con fecha, moneda, monto y URL
- [x] #2 Incluye fixtures/tests offline para HTML/listados y casos de links de descarga
- [x] #3 Distingue dato oficial de calculo derivado y conserva source_url/retrieved_at/raw_hash
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added Tesoro licitaciones scraper (tesoro_licitaciones) that scrapes Argentine Tesoro licitation notices (argentina.gob.ar) using stdlib HTMLParser, emitting per-instrument llamado/resultado events with fecha/moneda/monto/source_url. Distinguishes official data from derived calculations (metadata.official vs metadata.derived with is_derived flags) and always carries Provenance source_url/retrieved_at/raw_hash. Includes link/listing resolution + download-link filtering. 3 live-captured HTML fixtures + 1 crafted cronograma (the research doc's cronograma-2026 URL now 404s; default URL points to a live resultado notice). 24 new offline tests. Registered centrally. Risk: HTML columns vary across auctions; header-regex mapping may need a parser bump (PARSER_VERSION 0.1.0). No FX cross-currency derivation (respects 'no mezclar monedas').
<!-- SECTION:FINAL_SUMMARY:END -->
