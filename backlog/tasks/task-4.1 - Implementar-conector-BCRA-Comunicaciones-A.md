---
id: TASK-4.1
title: Implementar conector BCRA Comunicaciones A
status: Done
assignee: []
created_date: '2026-06-14 14:51'
updated_date: '2026-06-14 22:21'
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
- [x] #1 Conector descarga PDFs de Comunicaciones A por numero y devuelve items normalizados
- [x] #2 Incluye parser de titulo, fecha, url, texto extraido y external_id
- [x] #3 Incluye fixtures/tests offline para parsing y al menos una prueba controlada de existencia/fetch documentada
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar scaffold de conectores, politica de fixtures y research BCRA.
2. Implementar conector BCRA Comunicaciones A con fetch por numero y parser normalizado.
3. Agregar fixtures/tests offline para parsing y documentar una prueba controlada de existencia/fetch.
4. Ejecutar tests y actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Implementado BcraComunicacionesAConnector con fetch por numero sobre la URL oficial https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A{numero}.pdf.
- Agregado parser puro para external_id, fecha, titulo, texto extraido y referencia de circular a partir de texto offline derivado del PDF.
- Sumados fixtures A8060 y A8083, tests offline de parseo/normalizacion/fetch y documento de verificacion controlada del patron de URL oficial.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementé el conector acotado de BCRA Comunicaciones A sobre el scaffold comun de conectores.

Cambios principales:
- agregué BcraComunicacionesAConnector con fetch por número usando la URL oficial https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A{numero}.pdf;
- incorporé un parser puro que normaliza external_id, published_at, title, url, body y metadata de circular;
- dejé la extracción PDF detrás de la interfaz PdfTextExtractor, con backend opcional pypdf cuando esté disponible;
- sumé fixtures offline y tests para parseo, normalización y comportamiento de fetch/errores.

Verificación:
- python3 -m unittest discover -s tests
- documento de fetch controlado en docs/TASK-4.1-bcra-fetch-check.md.

Limitación conocida:
- si el entorno no tiene una librería PDF instalada, el conector necesita inyección explícita de extractor o instalar pypdf para extracción en runtime.
<!-- SECTION:FINAL_SUMMARY:END -->
