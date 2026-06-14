# Scoring operativo de senales semanales

## Objetivo

Priorizar que entra al reporte semanal segun stress, novedad y capacidad de romper el escenario base. El score no reemplaza el juicio editorial: ordena los temas que requieren explicacion, precio de validacion y seguimiento.

## Escala comun

| Score | Interpretacion | Uso editorial |
| --- | --- | --- |
| 0 | Sin senal nueva o ruido normal | No incluir, salvo contexto breve |
| 1 | Senal leve, esperada o ya priceada | Mencionar solo si ayuda a explicar otra seccion |
| 2 | Senal relevante pero contenida | Incluir en subseccion correspondiente |
| 3 | Stress alto o cambio de tendencia | Abrir seccion o destacarlo en "Que cambio" |
| 4 | Ruptura potencial de escenario base | Incluir como riesgo central y gatillo de seguimiento |

Reglas:
- Puntuar `stress` y `relevancia` por separado cuando sea posible. Prioridad final = mayor de ambos scores.
- Subir un punto si el dato contradice consenso y el precio confirma.
- Bajar un punto si la fuente es secundaria, el precio esta administrado o faltan dos insumos obligatorios.
- No cerrar lectura sin `precio_o_variable_que_confirma` y `precio_o_variable_que_invalida`.

## Argentina

### Tesoro y deuda en pesos

| Campo | Guia operativa |
| --- | --- |
| Inputs | Vencimientos semanales/mensuales, licitaciones, rollover, tasas de corte, duration, mix CER/LECAP/TAMAR/dollar-linked, cuenta del Tesoro, puts/encajes si aplican, riesgo pais y bonos hard dollar. |
| Score 0-1 | Rollover alto, tasas alineadas con curva, caja estable, sin concentracion de vencimientos. |
| Score 2 | Rollover aceptable pero con premio de tasa, menor duration o demanda concentrada en instrumentos muy cortos/indexados. |
| Score 3 | Rollover debil, fuerte suba de tasas de corte, vencimientos grandes sin financiamiento claro o presion visible sobre bancos. |
| Score 4 | Fallo de licitacion, canje defensivo, riesgo de monetizacion/represion financiera o perdida de acceso local. |
| Interpretacion | Separar caja del Tesoro, absorcion de bancos y senal de mercado. Un rollover alto con tasa forzada no es una senal limpia de confianza. |
| Umbrales iniciales | Incluir si rollover < 110%, tasa de corte sube mas de 300 pb vs curva comparable, duration cae de forma marcada, o riesgo pais mueve > 100 pb semanal. |

### BCRA, reservas y pesos

| Campo | Guia operativa |
| --- | --- |
| Inputs | Reservas brutas/netas, compras/ventas MULC, intervencion en bonos/futuros si se infiere, encajes, pases/repos, base monetaria, tasas de politica, balance BCRA, metas FMI. |
| Score 0-1 | Reservas y compras dentro de lo esperado; tasas y liquidez estables. |
| Score 2 | Acumulacion menor a la necesaria, ventas puntuales o aumento de esterilizacion sin cambio de regimen. |
| Score 3 | Perdida persistente de reservas, intervencion creciente, suba de encajes/tasas defensiva o incumplimiento probable de meta. |
| Score 4 | Perdida abrupta de reservas liquidas, cambio de regla cambiaria/monetaria, asistencia extraordinaria o senal de dominancia fiscal. |
| Interpretacion | Aclarar instrumento, canal, costo y limite de toda intervencion. Distinguir reservas contables de poder de fuego usable. |
| Umbrales iniciales | Incluir si reservas netas caen por 3 ruedas, ventas semanales son materialmente negativas, brecha sube > 5 pp, o futuros implican devaluacion acelerada. |

### Cambiario

| Campo | Guia operativa |
| --- | --- |
| Inputs | Oficial, crawling/banda si aplica, MEP, CCL, blue como contexto, brecha, futuros A3/Rofex, volumen, liquidacion agro/exportadores, pagos importadores, intervencion. |
| Score 0-1 | Brecha y futuros estables; movimiento explicado por estacionalidad. |
| Score 2 | Suba de brecha o futuros sin traslado claro a reservas o tasas. |
| Score 3 | Presion simultanea en brecha, futuros y reservas; mercado pricea cambio de regla. |
| Score 4 | Salto discreto, ruptura de banda, cepo/regla nueva o perdida de ancla cambiaria. |
| Interpretacion | Separar precio genuino de precio administrado. Mirar si la presion se paga con reservas, tasa, deuda o restricciones. |
| Umbrales iniciales | Incluir si MEP/CCL suben > 5% semanal, brecha aumenta > 5 pp, futuros suben > 500 pb anualizados, o oficial se aparta de la regla comunicada. |

### Inflacion

| Campo | Guia operativa |
| --- | --- |
| Inputs | IPC INDEC, IPC nucleo, regulados/estacionales, IPC CABA, alimentos alta frecuencia, REM/consultoras, salarios, tipo de cambio y tarifas. |
| Score 0-1 | Dato cerca de consenso, nucleo estable o desacelerando, sin shock de precios relativos. |
| Score 2 | Desvio moderado vs consenso o nucleo pegajosa, pero sin cambio de expectativas. |
| Score 3 | Aceleracion de nucleo, difusion alta o pass-through visible desde FX/tarifas. |
| Score 4 | Reaceleracion que invalida la desinflacion base o fuerza cambio de tasa/crawling. |
| Interpretacion | Separar headline de nucleo, nivel de velocidad y persistencia. Un dato aislado no cambia regimen sin expectativas/precios. |
| Umbrales iniciales | Incluir si IPC difiere > 0,5 pp del consenso, nucleo acelera por 2 meses, alimentos alta frecuencia cambia > 1 pp semanal, o REM sube fuerte. |

### Actividad y empleo

| Campo | Guia operativa |
| --- | --- |
| Inputs | EMAE, industria/construccion, recaudacion real, consumo, credito, empleo SIPA, salarios reales, indicadores privados, confianza UTDT. |
| Score 0-1 | Datos mixtos dentro del sendero base. |
| Score 2 | Rebote o caida sectorial relevante pero no generalizada. |
| Score 3 | Cambio transversal en actividad/empleo que altera recaudacion, apoyo politico o sostenibilidad fiscal. |
| Score 4 | Recesion/rebote fuera de escenario que fuerza redisenar fiscal, tasas o riesgo politico. |
| Interpretacion | Distinguir rebote estadistico de traccion genuina. Conectar actividad con recaudacion, empleo, politica y credito. |
| Umbrales iniciales | Incluir si EMAE/industria difiere > 1 pp vs consenso, empleo privado cae/sube de forma persistente, o recaudacion real rompe tendencia. |

## Internacional

### Fed y bancos centrales

| Campo | Guia operativa |
| --- | --- |
| Inputs | FOMC, SEP/dot plot, Powell y gobernadores, minutas, FedWatch/OIS, CPI/PCE/payrolls/JOLTS/claims, BCE/BoJ/BoE si mueven condiciones globales. |
| Score 0-1 | Guidance y pricing de tasas estables. |
| Score 2 | Dato o discurso mueve expectativas, pero sin cambio de funcion de reaccion. |
| Score 3 | Repricing relevante de cuts/hikes, cambio de sesgo Fed o sorpresa en inflacion/empleo. |
| Score 4 | Shock de mandato dual que cambia escenario global de tasas y dolar. |
| Interpretacion | Separar dato, consenso y precio. La pregunta central es si cambia la funcion de reaccion o solo el timing. |
| Umbrales iniciales | Incluir si 2y UST mueve > 15 pb semanal, FedWatch/OIS cambia > 25 pb para la reunion relevante, o CPI/PCE/payrolls sorprenden de forma material. |

### Liquidez global y curva

| Campo | Guia operativa |
| --- | --- |
| Inputs | UST 2y/10y/30y, pendiente, TGA, RRP, reservas bancarias, Treasury issuance/refunding, SOMA/QT, repo, credito, VIX, DXY. |
| Score 0-1 | Curva, dolar y liquidez sin cambio relevante. |
| Score 2 | Movimiento de tasas o dolar con impacto acotado en riesgo. |
| Score 3 | Tightening de condiciones financieras: suben tasas reales/DXY/VIX o se tensiona funding. |
| Score 4 | Stress de liquidez o curva que fuerza risk-off global y cierre de financiamiento para emergentes. |
| Interpretacion | Distinguir shock de tasa real, prima de plazo, dolar y liquidez. Para Argentina importa por riesgo pais, commodities y acceso a mercado. |
| Umbrales iniciales | Incluir si 10y UST mueve > 20 pb semanal, DXY > 2%, VIX > 20 o +5 pts, Brent > 7%, o spreads EM se amplian de forma visible. |

### Geopolitica y commodities

| Campo | Guia operativa |
| --- | --- |
| Inputs | Conflictos con energia/transporte, aranceles EE.UU./China, sanciones, OPEP/EIA/IEA, Brent/WTI, oro, semiconductores, tierras raras, comunicados oficiales. |
| Score 0-1 | Titulares sin precio ni canal macro claro. |
| Score 2 | Evento relevante con impacto localizado o todavia condicional. |
| Score 3 | Shock con precio confirmado en energia, dolar, oro, tasas o cadenas de suministro. |
| Score 4 | Escalada que cambia inflacion global, comercio, energia o riesgo soberano. |
| Interpretacion | No incluir geopolitica por dramatismo. Exigir canal: energia, inflacion, comercio, tasas, dolar, commodities o financiamiento. |
| Umbrales iniciales | Incluir si Brent/WTI mueve > 7% semanal, oro marca stress junto con DXY/tasas, hay sancion/arancel oficial nuevo, o se afecta oferta de energia/chips. |

## Priorizacion para el reporte

| Prioridad | Condicion |
| --- | --- |
| Abrir "Que cambio" | Cualquier score 4, o dos scores 3 conectados por el mismo mecanismo. |
| Seccion principal | Score 3 con precio de confirmacion o dato primario. |
| Subseccion breve | Score 2 con fuente primaria o precio observable. |
| Watchlist | Score 2 sin confirmacion de precio, o riesgo condicional sin fuente primaria. |
| Excluir | Score 0-1 sin conexion con escenario, precio o agenda proxima. |

## Gatillos que rompen escenario base

### Argentina

- Tesoro no logra rollover suficiente y debe convalidar tasa muy superior a curva, canje defensivo o asistencia indirecta.
- BCRA pierde reservas liquidas de forma persistente mientras suben brecha y futuros.
- La regla cambiaria se modifica o el mercado pricea salto discreto pese a intervencion.
- IPC nucleo reacelera por mas de un dato y obliga a endurecer tasa/crawling.
- Actividad o empleo se deterioran lo suficiente para afectar recaudacion, gobernabilidad o apoyo legislativo.
- Riesgo pais y bonos hard dollar contradicen la narrativa de normalizacion aunque los datos fiscales luzcan ordenados.

### Internacional

- Fed pasa de discusion de timing a cambio de funcion de reaccion por inflacion persistente o empleo quebrado.
- Suba de UST reales, DXY y VIX al mismo tiempo cierra apetito por emergentes.
- Shock petrolero o de transporte cambia el sendero de inflacion global.
- Aranceles, sanciones o restricciones de chips/tierras raras afectan comercio, energia o expectativas de crecimiento.
- Stress de liquidez por Treasury/QT/repo fuerza ventas de riesgo y ampliacion de spreads.

## Salida minima por senal incluida

Para cada senal que entre al reporte, completar:

- `score`: 0 a 4.
- `input`: dato, evento o precio observado.
- `lectura`: mecanismo causal en una frase.
- `confirma`: precio o variable que valida la lectura.
- `invalida`: precio o variable que la contradice.
- `umbral_proximo`: dato/precio que decide si escala, se mantiene o sale del reporte.
