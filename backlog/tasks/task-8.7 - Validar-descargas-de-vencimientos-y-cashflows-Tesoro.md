---
id: TASK-8.7
title: Validar descargas de vencimientos y cashflows Tesoro
status: To Do
assignee: []
created_date: '2026-06-15 02:43'
labels:
  - argentina
  - tesoro
  - debt
  - research
  - model-large
dependencies: []
references:
  - analysis/source_research_tesoro.md
parent_task_id: TASK-8
priority: high
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Antes de implementar calendario de deuda, validar los archivos oficiales de estructura financiera/cupones/vencimientos, sus URLs finales y estabilidad de columnas.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear analysis/tesoro_cashflows_schema_validation.md con fuentes, enlaces finales, formatos y columnas requeridas
- [ ] #2 Definir si el primer conector debe leer XLS/XLSX, CSV, PDF o combinacion
- [ ] #3 Identificar reglas para evitar doble conteo entre vencimientos, canjes y conversiones
<!-- AC:END -->
