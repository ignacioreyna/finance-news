---
id: TASK-2.2
title: Normalizar glosario tecnico de transcripciones
status: Done
assignee:
  - '@codex-orchestrator'
created_date: '2026-06-14 14:50'
updated_date: '2026-06-14 15:27'
labels:
  - research
  - transcripts
  - glossary
  - model-small
dependencies: []
references:
  - analysis/host_profile.md
  - data/transcripts
parent_task_id: TASK-2
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Revisar errores frecuentes de Whisper en nombres financieros y crear un glosario de normalizacion para futuras extracciones. Modelo recomendado: small.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear analysis/transcript_glossary.md con terminos correctos, variantes mal transcriptas y contexto
- [x] #2 Cubrir al menos Fed/FOMC/PCE/JOLTS/BLS/TGA/SOMA/Rofex/A3/Bessent/Waller/INDEC/BCRA/TAMAR/LECAP
- [x] #3 Indicar reglas que puedan automatizarse y casos que requieran revision humana
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar analysis/host_profile.md y transcriptos disponibles para detectar terminos financieros con riesgo de mala transcripcion.
2. Crear analysis/transcript_glossary.md con termino canonico, variantes, contexto y regla de normalizacion.
3. Separar reglas automatizables de casos que requieren revision humana.
4. Actualizar la tarea por CLI con notas, ACs y resumen final.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Revisado analysis/host_profile.md y los lotes analysis/subagents para extraer terminologia recurrente.
- Creado analysis/transcript_glossary.md con canonicos, variantes mal transcriptas, contexto y reglas de normalizacion.
- Separadas reglas automatizables de casos que requieren revision humana.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se normalizo el glosario tecnico de transcripciones en analysis/transcript_glossary.md.

Incluye terminos canonicos, variantes ASR frecuentes y contexto para Fed, FOMC, PCE, JOLTS, BLS, TGA, SOMA, Rofex, A3, Bessent, Waller, INDEC, BCRA, TAMAR y LECAP.

Tambien agrega reglas automatizables de normalizacion y una lista de casos que requieren revision humana para evitar reemplazos ambiguos.
<!-- SECTION:FINAL_SUMMARY:END -->
