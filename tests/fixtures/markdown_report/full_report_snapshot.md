# Reporte Semanal

**Semana finaliza:** 2026-06-12
**Zona horaria:** America/Argentina/Buenos_Aires
**Generado:** 2026-06-13T10:00:00

**Estadísticas:** 4 señales totales, 4 incluidas, 4 fuentes

## Argentina

### Inflación y Actividad

**IPC Núcleo** (score: 3, confianza: alta)

- **Dato:** 3.5% mensual
- **Lectura:** Aceleración respecto al mes anterior
- **Mecanismo:** Canal: inflacion
- **Confirma:** IPC < 3.0% confirma desaceleración
- **Invalida:** IPC > 4.0% invalida tesis de desinflación
- **Fuente(s):** src_1
- **Extracto:** El IPC núcleo mostró un incremento...

**Reservas Netas** (score: 4, confianza: alta)

- **Dato:** -USD 2.1B
- **Lectura:** Pérdida significativa de reservas
- **Mecanismo:** Canal: bcra_reservas
- **Confirma:** Estabilidad de reservas confirma
- **Invalida:** Pérdida > USD 1B/semana invalida
- **Fuente(s):** src_2
- **Extracto:** El BCRA reportó...


## Internacional

### Geopolítica

**Fed Policy** (score: 2, confianza: media)

- **Dato:** Tasa 5.25-5.50%
- **Lectura:** Mantención de tasa
- **Mecanismo:** Canal: fed_bancos_centrales
- **Confirma:** Tasa estable confirma
- **Invalida:** Corte agresivo invalida
- **Fuente(s):** src_3
- **Extracto:** El FOMC decidió...


## Mercado

### FX

**MEP** (score: 3, confianza: alta)

- **Dato:** 1,050 ARS/USD
- **Lectura:** Estabilidad relativa
- **Mecanismo:** Canal: cambiario
- **Confirma:** MEP < 1,100 confirma
- **Invalida:** MEP > 1,200 invalida
- **Fuente(s):** src_4
- **Extracto:** El tipo de cambio MEP...


## Escenarios

### Escenario Base

**Disparadores:**
- Estabilización de las variables principales observadas.

**Mecanismo:**
- Los datos de inflación y actividad se mantienen en rangos esperados.
- No hay rupturas en el mercado cambiario ni de tasas.

**Activos más sensibles:**
- Bonos soberanos en pesos y dólares.
- Tipo de cambio paralelo (MEP/CCL).

**Probabilidad cualitativa:** Media

**Hito que lo valida:**
- Estabilidad en precios de mercado por 2 semanas consecutivas.

**Hito que lo descarta:**
- Salto discreto en tipo de cambio o tasas > 15%.

### Escenario Positivo

**Disparadores:**
- Mejora en indicadores de actividad menor a la esperada.

**Mecanismo:**
- Recuperación más rápida de la economía.
- Mayor liquidez y menor presión cambiaria.

**Activos más sensibles:**
- Acciones locales.
- Riesgo país.

**Probabilidad cualitativa:** Baja

**Hito que lo valida:**
- Serie de datos positivos consecutivos.

**Hito que lo descarta:**
- Deterioro de reservas o brecha cambiaria.

### Escenario Negativo

**Disparadores:**
- Aceleración de inflación o devaluación.

**Mecanismo:**
- Pérdida de reservas y presión sobre el tipo de cambio.
- Ajuste monetario más agresivo.

**Activos más sensibles:**
- Dólar oficial y paralelo.
- Tasa Badlar y pases.

**Probabilidad cualitativa:** Media

**Hito que lo valida:**
- Salto en tipo de cambio o pérdida de reservas > USD 1B/semana.

**Hito que lo descarta:**
- Estabilidad de reservas por 3 semanas.


## Riesgos que rompen el escenario

### Riesgos Observables

### Gaps de Información

**Sección:** tesoro_y_deuda
- **Faltante:** Rollover mensual
- **Fallback:** Estimación de mercado
- **Ajuste de confianza:** media
- **Nota:** Falta dato oficial de licitación


## Qué mirar la semana próxima

### Eventos y Datos a Monitorear

**Evento/dato:** Fed Policy
- **Fecha esperada:** Próxima semana (a confirmar)
- **Por qué importa:** Mantención de tasa
- **Resultado positivo:** Tasa estable confirma
- **Resultado negativo:** Corte agresivo invalida
- **Mercado/variable a mirar:** Canal: fed_bancos_centrales
- **Fuente:** [Fed - FOMC](https://federalreserve.gov/monetarypolicy/fomccalendars.htm)

**Evento/dato:** IPC Núcleo
- **Fecha esperada:** Próxima semana (a confirmar)
- **Por qué importa:** Aceleración respecto al mes anterior
- **Resultado positivo:** IPC < 3.0% confirma desaceleración
- **Resultado negativo:** IPC > 4.0% invalida tesis de desinflación
- **Mercado/variable a mirar:** Canal: inflacion
- **Fuente:** [INDEC - IPC](https://indec.gob.ar/ipc)

**Evento/dato:** MEP
- **Fecha esperada:** Próxima semana (a confirmar)
- **Por qué importa:** Estabilidad relativa
- **Resultado positivo:** MEP < 1,100 confirma
- **Resultado negativo:** MEP > 1,200 invalida
- **Mercado/variable a mirar:** Canal: cambiario
- **Fuente:** [Mercado - MEP](https://mercado.com.ar/mep)

**Evento/dato:** Reservas Netas
- **Fecha esperada:** Próxima semana (a confirmar)
- **Por qué importa:** Pérdida significativa de reservas
- **Resultado positivo:** Estabilidad de reservas confirma
- **Resultado negativo:** Pérdida > USD 1B/semana invalida
- **Mercado/variable a mirar:** Canal: bcra_reservas
- **Fuente:** [BCRA - Reservas](https://bcra.gob.ar/reservas)


## Índice de Fuentes

**src_1**: INDEC - IPC
- URL: https://indec.gob.ar/ipc
- Tipo: primaria_oficial, Región: AR
- Publicado: 2026-06-12
- Accedido: 2026-06-13T10:00:00
- Soporta: argentina.inflacion_y_actividad[0]

**src_2**: BCRA - Reservas
- URL: https://bcra.gob.ar/reservas
- Tipo: primaria_oficial, Región: AR
- Publicado: 2026-06-12
- Accedido: 2026-06-13T10:00:00
- Soporta: argentina.dolar_y_reservas[0]

**src_3**: Fed - FOMC
- URL: https://federalreserve.gov/monetarypolicy/fomccalendars.htm
- Tipo: primaria_oficial, Región: US
- Publicado: 2026-06-12
- Accedido: 2026-06-13T10:00:00
- Soporta: internacional.fed_bancos_centrales[0]

**src_4**: Mercado - MEP
- URL: https://mercado.com.ar/mep
- Tipo: mercado, Región: AR
- Publicado: 2026-06-12
- Accedido: 2026-06-13T10:00:00
- Soporta: mercado.fx[0]


