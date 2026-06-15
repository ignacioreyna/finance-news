---
id: TASK-8.1
title: Implementar conector BCRA catalogo de series
status: Done
assignee:
  - '@general-mid'
created_date: '2026-06-15 02:43'
updated_date: '2026-06-15 18:29'
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
- [x] #1 El conector devuelve un catalogo normalizado de series BCRA relevantes con id, nombre, unidad, frecuencia y fuente
- [x] #2 Incluye fixtures/tests offline para parsing de metadata o respuesta API
- [x] #3 Documenta fallback cuando una serie requerida no aparece en el catalogo
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Confirmado via analysis/source_research_bcra.md: las APIs publicas BCRA NO requieren API key (sin autenticacion). Solo control de trafico por IP sin cuota publica.

- Hub de APIs: https://www.bcra.gob.ar/apis-banco-central/

- API monetaria v4 (sin auth): https://api.bcra.gob.ar/estadisticas/v4.0/monetarias

- API cambiaria v1 (sin auth): https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones

- Principales Variables v3.0 esta deprecado (2026-02-28); usar v4.0.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
BCRA series catalog connector. connectors/bcra_catalogo.py: BcraCatalogoConnector + pure parser parse_bcra_catalog_json(); public BCRA monetarias endpoint (no key). Normalized catalog entries (id, nombre, unidad, frecuencia, fuente). Missing-series fallback documented + tested. Live-captured fixture. 22 new unittest tests; registered as bcra_catalogo. Full suite 129 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
