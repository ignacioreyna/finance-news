# Context pack operativo para generacion del reporte semanal

## Objetivo

Definir un paquete de contexto compacto y usable para un modelo generador de nivel `medium`, alineado con el esquema semanal, el scoring de senales y el perfil editorial del host. El pack debe permitir producir un borrador trazable, con mecanismo causal, precio de validacion y riesgos claros, sin obligar al modelo a reconstruir reglas desde cero.

## Principios editoriales que gobiernan el pack

- Separar siempre `dato`, `lectura` y `precio`.
- Explicar `mecanismo` antes que narrativa.
- Marcar `riesgo`, `invalidador` y `senal temprana` de forma observable.
- Declarar `confianza` segun calidad de evidencia y limpieza de fuentes.
- Si un precio esta intervenido o administrado, explicitarlo y bajar confianza.
- Si faltan dos o mas insumos obligatorios de una seccion, marcarla `incompleta`.

## Estructura sugerida del context pack

Usar un documento Markdown con un bloque JSON central. Markdown sirve para instrucciones estables; JSON sirve para datos normalizados y validables.

### Plantilla de alto nivel

```md
# Weekly Report Context Pack

## Instructions
- Reglas editoriales estables
- Restricciones de citas, links y trazabilidad
- Criterios de inclusion por score

## Input Payload
```json
{
  "reporting_window": {
    "week_end_date": "YYYY-MM-DD",
    "timezone": "America/Argentina/Buenos_Aires"
  },
  "generator_profile": {
    "target_model": "medium",
    "language": "es-AR",
    "audience": "inversor/macroeconomico",
    "host_style": {
      "tone": "tecnico, directo, coloquial",
      "bias": "liberal-institucional pragmatica",
      "priority": [
        "mecanismo antes que relato",
        "dato vs expectativa vs precio",
        "riesgo e invalidador",
        "trazabilidad auditable"
      ]
    }
  },
  "editorial_rules": {
    "must_separate_fact_and_interpretation": true,
    "must_include_confirmation_variable": true,
    "must_include_invalidation_variable": true,
    "must_flag_intervention_cost_limit": true,
    "must_declare_confidence": true
  },
  "source_policy": {
    "primary_required_when_available": true,
    "secondary_allowed_as_proxy": true,
    "secondary_requires_lower_confidence": true,
    "max_unverified_claims_per_section": 0
  },
  "signal_selection": {
    "include_threshold": 2,
    "lead_threshold": 3,
    "scenario_break_threshold": 4
  },
  "sections": {
    "que_cambio": [],
    "argentina": {},
    "internacional": {},
    "mercado": {},
    "escenarios": {},
    "riesgos": [],
    "que_mirar": []
  },
  "source_index": [],
  "open_gaps": []
}
```
```

## Payload operativo detallado

### 1. `reporting_window`

Define semana analizada y zona horaria de corte.

```json
{
  "week_end_date": "2026-06-12",
  "timezone": "America/Argentina/Buenos_Aires",
  "calendar_mode": "weekly_close"
}
```

### 2. `generator_profile`

Fija estilo del host y restricciones del modelo.

```json
{
  "target_model": "medium",
  "language": "es-AR",
  "audience": "inversor/macroeconomico",
  "host_style": {
    "tone": "tecnico, directo, coloquial",
    "priority": [
      "mecanismo antes que relato",
      "separar dato, expectativa y precio",
      "explicitar quien absorbe el costo",
      "cerrar con variable de seguimiento"
    ],
    "anti_patterns": [
      "epica politica",
      "opinion presentada como hecho",
      "causalidad fuerte sin precio",
      "certeza alta con evidencia incompleta"
    ]
  }
}
```

### 3. `signal_selection`

Resume el scoring semanal para decidir inclusion.

```json
{
  "include_threshold": 2,
  "lead_threshold": 3,
  "scenario_break_threshold": 4,
  "rules": [
    "Subir un punto si contradice consenso y el precio confirma",
    "Bajar un punto si la fuente es secundaria o el precio es administrado",
    "Excluir score 0-1 salvo que aporte contexto a otra senal"
  ]
}
```

### 4. `sections`

Contiene el material que el modelo debe transformar en reporte.

#### 4.1 `que_cambio`

Lista corta de 3 a 5 cambios que movieron escenario o precios.

```json
[
  {
    "tema": "string",
    "score": 3,
    "dato": "hecho confirmado",
    "lectura": "que implica",
    "mecanismo": "canal causal concreto",
    "precio_o_variable_que_confirma": "string",
    "precio_o_variable_que_invalida": "string",
    "confianza": "alta",
    "fuente_ids": ["src_1", "src_2"]
  }
]
```

#### 4.2 `argentina` e `internacional`

Usar subsecciones del esquema semanal y mantener campos fijos por item.

```json
{
  "inflacion_y_actividad": [
    {
      "tema": "IPC nucleo",
      "score": 2,
      "dato": "string",
      "lectura": "string",
      "mecanismo": "string",
      "comparacion_vs_semana_previa": "string",
      "comparacion_vs_consenso": "string",
      "precio_o_variable_que_confirma": "string",
      "precio_o_variable_que_invalida": "string",
      "riesgo": "string",
      "confianza": "media",
      "fuente_ids": ["src_3"]
    }
  ]
}
```

#### 4.3 `mercado`

Tablero resumido mas lectura.

```json
{
  "fx": [
    {
      "activo": "MEP",
      "nivel_actual": "numeric/string",
      "variacion_semanal": "numeric/string",
      "driver_principal": "string",
      "lectura_de_flujos_vs_fundamentals": "string",
      "distorsion_por_intervencion": "string|null",
      "confianza": "media",
      "fuente_ids": ["src_4"]
    }
  ]
}
```

#### 4.4 `escenarios`

Debe quedar listo para que el modelo narre `base`, `positivo` y `negativo`.

```json
{
  "escenario_base": {
    "disparadores": ["string"],
    "mecanismo": "string",
    "activos_mas_sensibles": ["string"],
    "probabilidad_cualitativa": "media",
    "hito_que_lo_valida": "string",
    "hito_que_lo_descarta": "string",
    "confianza": "media",
    "fuente_ids": ["src_1", "src_4"]
  }
}
```

#### 4.5 `riesgos`

Lista 3 a 5 riesgos que rompen escenario.

```json
[
  {
    "riesgo": "string",
    "tipo": "macro",
    "canal_de_transmision": "string",
    "senal_temprana": "string",
    "impacto_probable": "string",
    "cobertura_o_hedge": "string|null",
    "confianza": "media",
    "fuente_ids": ["src_5"]
  }
]
```

#### 4.6 `que_mirar`

Agenda accionable para la semana siguiente.

```json
[
  {
    "evento_o_dato": "string",
    "fecha_esperada": "YYYY-MM-DD|fecha_a_confirmar",
    "por_que_importa": "string",
    "resultado_positivo": "string",
    "resultado_negativo": "string",
    "mercado_o_variable_a_mirar": "string",
    "expectativa_de_consenso": "string|null",
    "fuente_ids": ["src_6"]
  }
]
```

### 5. `source_index`

Indice normalizado para trazabilidad sin repetir URLs en el cuerpo.

```json
[
  {
    "id": "src_1",
    "label": "BCRA - Reservas internacionales",
    "type": "primaria_oficial",
    "region": "AR",
    "url": "https://...",
    "published_at": "YYYY-MM-DD",
    "accessed_at": "YYYY-MM-DD",
    "supports": [
      "argentina.dolar_y_reservas[0]",
      "que_cambio[1]"
    ],
    "confidence_impact": "none"
  }
]
```

### 6. `open_gaps`

Campo explicito para faltantes y supuestos.

```json
[
  {
    "section": "internacional.geopolitica",
    "missing_input": "comunicado oficial",
    "fallback_used": "medio confiable",
    "confidence_adjustment": "baja",
    "note": "mantener lectura condicional"
  }
]
```

## Reglas de estilo obligatorias para el modelo generador

### 1. Dato

- Cada parrafo debe apoyarse primero en un `dato` o hecho confirmado.
- No presentar inferencias como hechos.
- Si el dato contradice el consenso, decirlo de forma explicita.

### 2. Mecanismo

- Despues del dato, explicar el canal causal: flujos, caja, reservas, tasa, curva, dolar, actividad o posicionamiento.
- Si hay intervencion, precisar `instrumento`, `canal`, `costo` y `limite`.
- No usar geopolítica o politica local como adorno: exigir canal economico observable.

### 3. Precio

- Toda lectura relevante debe incluir `precio_o_variable_que_confirma`.
- Toda tesis debe incluir `precio_o_variable_que_invalida`.
- Si el precio es administrado, decir por que pierde capacidad informativa.

### 4. Riesgo

- Explicitar que rompe la tesis central y cual es la `senal_temprana`.
- Evitar riesgos abstractos sin variable observable.
- Si no hay evidencia suficiente, mover el punto a watchlist o bajar confianza.

### 5. Confianza

- `alta`: fuente primaria o precio observable suficiente, sin faltantes materiales.
- `media`: evidencia razonable, pero con alguna pieza proxy o validacion parcial.
- `baja`: fuente secundaria, precio intervenido, dato incompleto o lectura aun condicional.
- Ninguna seccion puede omitir `confianza`.

## Limites de citas, links y trazabilidad

### Citas

- No usar citas textuales largas salvo que el documento fuente las haga necesarias.
- Limite sugerido: maximo `1` cita textual corta por subseccion, de hasta `20` palabras.
- Priorizar parafrasis tecnica sobre reproduccion literal.

### Links

- No incrustar URLs en el cuerpo narrativo del reporte.
- Usar `fuente_ids` en el cuerpo de datos y resolver URLs solo en `source_index`.
- Limite sugerido: `1` a `3` `fuente_ids` por item y `6` fuentes maximas por seccion.
- Si varias afirmaciones dependen de la misma fuente, reutilizar el mismo `id`.

### Trazabilidad

- Toda afirmacion material debe mapear a al menos un `source_id`.
- Toda seccion debe poder auditarse con fuente primaria o proxy explicitado.
- Cuando se use proxy, marcar `confidence_impact`.
- Si una afirmacion no puede trazarse, no debe entrar al resumen final.
- El reviewer deberia poder reconstruir:
  - que dato se uso
  - desde que fuente salio
  - que lectura genero
  - con que precio se valido o invalido

## Reglas de compacidad para modelo `medium`

- Mantener nombres de campos estables y cortos.
- No duplicar el mismo contexto en multiples secciones.
- Incluir solo senales con `score >= 2`, salvo contexto minimo imprescindible.
- Resumir series o tablas extensas en una lectura mas nivel/variacion.
- Mover evidencia secundaria o faltantes a `open_gaps` en lugar de inflar el cuerpo principal.

## Secuencia sugerida de uso

1. Cargar `generator_profile`, `editorial_rules` y `source_policy`.
2. Filtrar senales por `signal_selection`.
3. Poblar `sections` con datos normalizados y `source_ids`.
4. Completar `open_gaps` antes de generar texto.
5. Generar borrador respetando:
   - dato
   - mecanismo
   - precio de confirmacion
   - precio de invalidacion
   - riesgo
   - confianza
6. Revisar el borrador contra la rubrica de evaluacion antes de publicarlo.

## Checklist minimo antes de generar

- Hay 3 a 5 cambios en `que_cambio`.
- Cada item incluido tiene `score`, `dato`, `mecanismo`, `confianza` y `fuente_ids`.
- Ninguna conclusion carece de confirmacion o invalidacion.
- Las fuentes estan indexadas y sin links sueltos en el cuerpo.
- Los faltantes quedaron expuestos en `open_gaps`.
