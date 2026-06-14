---
id: TASK-4.2
title: Investigar endpoints BCRA de reservas y variables monetarias
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:51'
updated_date: '2026-06-14 20:02'
labels:
  - argentina
  - bcra
  - research
  - model-medium
dependencies: []
references:
  - analysis/host_profile.md
parent_task_id: TASK-4
priority: high
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Identificar fuentes oficiales BCRA para reservas, compras/ventas, agregados, tasas, encajes y series monetarias relevantes al criterio del host. Modelo recomendado: medium.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/source_research_bcra.md con endpoints, formatos, frecuencia y limites
- [x] #2 Separar fuentes normativas, estadisticas y comunicados
- [x] #3 Proponer conectores atomicos posteriores con prioridad
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Relevadas superficies oficiales BCRA: API monetaria v4, API cambiaria v1, páginas de estadísticas, calendario y buscador de comunicaciones.

- Documentadas fuentes para reservas, base monetaria, agregados, tasas, encajes y mercado de cambios con clasificación machine-readable/scraping/manual.

- Concluido que no se identificó un endpoint público diario específico para compras/ventas netas del BCRA; se dejó como fuente oficial más cercana el anexo mensual de mercado de cambios y balance cambiario.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se creó analysis/source_research_bcra.md con un relevamiento accionable de fuentes oficiales BCRA para reservas y variables monetarias. El documento separa fuentes estadísticas, normativas y de comunicados; identifica endpoints y artefactos descargables, sus formatos, frecuencias y límites operativos; y propone una secuencia de conectores atómicos priorizados. También deja explícito el principal gap detectado: no apareció un endpoint público diario y específico para compras/ventas netas del BCRA, por lo que la mejor fuente oficial identificada para ese frente sigue siendo el anexo mensual del mercado de cambios y balance cambiario.
<!-- SECTION:FINAL_SUMMARY:END -->
