---
id: TASK-3.2
title: Scaffold inicial del paquete de conectores
status: Done
assignee: []
created_date: '2026-06-14 14:50'
updated_date: '2026-06-14 19:55'
labels:
  - connectors
  - scaffold
  - python
  - model-medium
dependencies:
  - TASK-3.1
parent_task_id: TASK-3
priority: high
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear la estructura de codigo del paquete de conectores siguiendo el patron de vigia, sin implementar fuentes complejas todavia. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear estructura src o package equivalente con _http, models y modulo de tests
- [x] #2 Agregar pyproject o configuracion minima segun el stack elegido en el repo
- [x] #3 Incluir un test trivial/offline que valide serializacion del item normalizado
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar README.md, analysis/connector_architecture.md y la estructura actual del repo.
2. Crear scaffold Python minimo para conectores con _http, models y tests offline.
3. Agregar pyproject/configuracion minima coherente con el repo.
4. Ejecutar test trivial de serializacion y actualizar tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Se creo el scaffold Python inicial en src/finance_news/connectors con contratos compartidos en models.py.

- Se agrego _http.py con request/response y protocolo async de transporte sin dependencias externas.

- Se sumo pyproject.toml minimo con setuptools y un test offline de round-trip para SourceItem via unittest.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego el scaffold inicial del paquete de conectores en Python siguiendo el contrato comun definido en analysis/connector_architecture.md.

Cambios:
- Cree el paquete src/finance_news/connectors con modelos normalizados serializables, export surface minima y un modulo _http para transporte async.
- Agregue pyproject.toml con configuracion minima de empaquetado basada en setuptools.
- Incorpore un test offline con unittest que valida el round-trip de serializacion de SourceItem, Provenance y Freshness sin depender de red.

Tests:
- python3 -m unittest tests/test_connectors_models.py
<!-- SECTION:FINAL_SUMMARY:END -->
