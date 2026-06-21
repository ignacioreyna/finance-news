---
id: TASK-11.4
title: Documentar configuracion y credenciales de fuentes
status: Done
assignee:
  - '@general-air'
created_date: '2026-06-15 02:47'
updated_date: '2026-06-21 14:56'
labels:
  - ops
  - docs
  - credentials
  - model-small
dependencies: []
references:
  - analysis/source_research_us_macro.md
  - analysis/source_research_arg_market.md
parent_task_id: TASK-11
priority: medium
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Crear una guia de variables de entorno, credenciales opcionales y politicas de secretos para APIs como BLS, BEA, BYMA/MAE y futuros conectores.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Crear docs/source_credentials.md con variables, obligatoriedad y fuentes que las usan
- [x] #2 Distinguir credenciales opcionales, obligatorias y pendientes de validacion
- [x] #3 Incluir reglas para no commitear secretos ni fixtures con tokens
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added docs/source_credentials.md. AC#1: table of env vars (BLS_API_KEY/FRED_API_KEY/EIA_API_KEY/BEA_USER_ID) with required/optional status, sources that use them, and how to obtain; notes all AR + FOMC/Treasury/NY-Fed connectors are NO-KEY public. AC#2: separates OPTIONAL (BLS/FRED/EIA/BEA - free registration, rate-limited without), REQUIRED (none - all connectors work keyless by design), and PENDING VALIDATION (BYMA/MAE paid feeds - blocked per arg_market_access_validation.md). AC#3: rules - secrets in .env (gitignored, confirmed untracked), loaded via settings.py load_env(); never hardcode; never commit .env; fixtures must not contain real tokens (FakeTransport pattern); connectors never log secrets. Includes a .env.example template.
<!-- SECTION:FINAL_SUMMARY:END -->
