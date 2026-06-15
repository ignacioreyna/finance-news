---
id: TASK-8.6
title: Implementar scraper Tesoro licitaciones y resultados
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
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
- [ ] #1 El conector entrega eventos normalizados de llamado y resultado por instrumento con fecha, moneda, monto y URL
- [ ] #2 Incluye fixtures/tests offline para HTML/listados y casos de links de descarga
- [ ] #3 Distingue dato oficial de calculo derivado y conserva source_url/retrieved_at/raw_hash
<!-- AC:END -->
