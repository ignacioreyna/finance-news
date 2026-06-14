# Rubrica de evaluacion del reporte semanal

## Objetivo

Dar a un subagent reviewer una forma compacta de evaluar si el reporte semanal respeta el perfil del host: mecanismo antes que relato, separacion entre dato y precio, foco en riesgo e invalidador, y trazabilidad suficiente para auditar la lectura.

## Escala

- `2 = cumple`: el criterio esta resuelto de forma explicita, correcta y usable.
- `1 = parcial`: aparece, pero con ambiguedad, cobertura incompleta o validacion debil.
- `0 = falla`: falta, contradice el perfil del host o induce una lectura engañosa.

## Regla de uso para reviewer

1. Revisar cada seccion del reporte contra los criterios.
2. Asignar `0`, `1` o `2` por criterio.
3. Marcar el reporte como `aprobado` solo si no hay ningun `0` en criterios criticos.
4. Criterios criticos: `dato vs lectura`, `mecanismo`, `precio de confirmacion`, `riesgo/invalidador`, `trazabilidad`.
5. Si una seccion esta `incompleta` o sin fuente primaria, el maximo puntaje de esa seccion es `1`.

## Criterios

| Criterio | Que debe verificar el reviewer | 2 | 1 | 0 |
| --- | --- | --- | --- | --- |
| Dato vs lectura | Separa hechos confirmados de interpretacion | Hechos y lectura claramente separados | Mezcla parcial entre hecho e interpretacion | Presenta opinion como hecho |
| Mecanismo causal | Explica por que el dato mueve flujos, caja, reservas, tasas o posicionamiento | Mecanismo explicito y consistente | Hay intuicion, pero no canal completo | Relato sin mecanismo |
| Precio de mercado | Incluye el precio o variable que confirma o contradice la tesis | Confirma e invalida con precios/variables concretas | Solo una de las dos o demasiado vaga | Omite precio de mercado |
| Riesgo e invalidador | Expone que rompe la tesis y por que | Riesgo, señal temprana e invalidador claros | Riesgo generico sin disparador observable | No hay riesgo o se presenta certeza excesiva |
| Intervencion y costo | Si hubo intervencion, aclara instrumento, canal, costo y limite | Los cuatro puntos estan explicitados | Falta uno de los cuatro puntos | Trata precio administrado como genuino |
| Distincion institucional | Distingue funciones y costos entre BCRA, Tesoro, bancos y mercado | Roles y costos correctamente asignados | Hay simplificacion tolerable | Confunde actores o balances |
| Anti-narrativa | Evita épica politica o sesgo tribal; prioriza restricciones operativas | Lenguaje sobrio y tecnico | Hay algo de narrativa, pero no domina la lectura | La narrativa reemplaza al analisis |
| Confianza y faltantes | Declara confianza y faltantes cuando la evidencia es incompleta | Confianza y faltantes bien marcados | Solo uno de los dos | No reconoce limites de evidencia |
| Trazabilidad | Permite rastrear de donde sale cada afirmacion relevante | Usa fuentes primarias o proxies explicitados | Algunas afirmaciones quedan sin respaldo directo | No se puede auditar la lectura |
| Utilidad accionable | Cierra con que mirar o que variable seguir | Hay gatillos concretos de seguimiento | Recomendacion generica | No deja agenda verificable |

## Fallas tipicas a detectar

### 1. Sobreinterpretar un dato

- Falla: un IPC o payroll aislado se usa para concluir cambio de regimen sin mirar consenso, persistencia ni precio.
- Como marcarlo:
  - `0` en `dato vs lectura` si la conclusion se presenta como hecho.
  - `0` o `1` en `mecanismo causal` si no explica canal.
  - `0` en `precio de mercado` si no muestra que activo confirmo la lectura.

### 2. Omitir precio de mercado

- Falla: el texto dice que "mejora la credibilidad" o "sube el riesgo" sin mostrar MEP, CCL, curva, bonos, riesgo pais, UST, DXY u otra variable relevante.
- Como marcarlo:
  - `0` en `precio de mercado`.
  - `1` maximo en `utilidad accionable` porque no deja validacion observable.

### 3. Confundir BCRA y Tesoro

- Falla: atribuye al BCRA costos, deuda o caja que corresponden al Tesoro, o viceversa, sin separar balance, instrumento ni restriccion.
- Como marcarlo:
  - `0` en `distincion institucional`.
  - `0` en `intervencion y costo` si ademas trata coordinacion o absorcion de pesos como si fuera una sola caja.

## Regla de decision

- `Aprobado`: todos los criterios criticos con `2` o, como excepcion, un solo `1` justificado.
- `A revisar`: cualquier criterio critico en `1`, o dos no criticos en `0`.
- `Rechazado`: cualquier criterio critico en `0`.

## Salida sugerida del reviewer

Usar este formato breve:

- `veredicto`: `aprobado` | `a revisar` | `rechazado`
- `score_critico`: resumen de los 5 criterios criticos
- `hallazgos`: 3 a 5 bullets con fallas o fortalezas
- `faltantes_obligatorios`: lista corta
- `siguiente_correccion`: una accion concreta para mejorar el reporte
