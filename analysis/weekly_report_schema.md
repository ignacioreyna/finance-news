# Esquema operativo del reporte semanal

## Reglas globales

- Formato de cada sección:
  - `titulo`
  - `tesis`
  - `confianza` (`alta` | `media` | `baja`)
  - `hechos_confirmados`
  - `lectura`
  - `precio_o_variable_que_confirma`
  - `precio_o_variable_que_invalida`
  - `fuentes_usadas`
  - `faltantes`
- Criterio editorial:
  - Separar dato, expectativa y precio.
  - Explicar mecanismo antes que relato.
  - Si hubo intervención, indicar instrumento, canal, costo y límite.
  - No cerrar una lectura sin variable de validación.
- Política de fuentes:
  - Priorizar fuente primaria oficial o de mercado.
  - Si falta fuente primaria, usar proxy explícito y bajar confianza.
  - Si faltan dos o más insumos obligatorios, marcar la sección como `incompleta`.

## 1. Qué cambió esta semana

- Objetivo: abrir con los 3 a 5 cambios que movieron escenario o precios.
- Campos obligatorios:
  - `cambios_clave` (lista corta)
  - `impacto_en_escenario`
  - `activos_o_variables_afectadas`
- Campos opcionales:
  - `cambio_de_consenso`
  - `tema_que_el_mercado_ignoro`
- Fuentes requeridas:
  - Cierre semanal de activos relevantes.
  - Calendario y resultados de datos/eventos de la semana.
  - Al menos una referencia primaria por cambio listado.
- Fallback si faltan datos:
  - Si no hay cierre consolidado semanal, usar variación a 5 ruedas.
  - Si un evento no tiene documento primario disponible, citar cobertura secundaria confiable y marcar `confianza: baja`.

## 2. Argentina

- Objetivo: cubrir macro local, pesos, dólar, reservas, Tesoro y política operativa.
- Subsecciones obligatorias:
  - `inflacion_y_actividad`
  - `pesos_y_tasas`
  - `dolar_y_reservas`
  - `tesoro_y_deuda`
  - `politica_y_restricciones`
  - `senales_de_mercado`
- Campos obligatorios por subsección:
  - `dato_nuevo`
  - `por_que_importa`
  - `precio_o_variable_que_confirma`
  - `precio_o_variable_que_invalida`
- Campos opcionales por subsección:
  - `comparacion_vs_semana_previa`
  - `comparacion_vs_consenso`
  - `riesgo_de_timing`
- Fuentes requeridas:
  - Oficiales: BCRA, INDEC, Ministerio de Economía/Tesoro.
  - Mercado: MEP, CCL, oficial, futuros, curva CER, TAMAR, LECAP, bonos hard dollar, riesgo país.
  - Política/institucional: Congreso, FMI, ratings u organismos multilaterales si aplica.
- Fallback si faltan datos:
  - Inflación/actividad: usar nowcasts o privados explícitos hasta dato oficial.
  - Reservas/caja: usar última publicación oficial más precios de mercado como validación.
  - Política: si no hay documento oficial, limitarse a hecho confirmado por al menos dos medios confiables.

## 3. Internacional

- Objetivo: resumir el marco externo que condiciona a Argentina y riesgo global.
- Subsecciones obligatorias:
  - `fed_y_bancos_centrales`
  - `inflacion_empleo_y_actividad_eeuu`
  - `liquidez_y_curva`
  - `commodities`
  - `geopolitica`
  - `ia_y_mega_caps` 
- Campos obligatorios por subsección:
  - `hecho_clave`
  - `implicancia_para_mercados`
  - `implicancia_para_argentina`
  - `variable_de_confirmacion`
- Campos opcionales por subsección:
  - `cambio_vs_consenso`
  - `riesgo_de_segunda_vuelta`
- Fuentes requeridas:
  - Primarias de Fed/FOMC, BLS, BEA, Treasury y bancos centrales relevantes.
  - Mercado global: UST, DXY, oro, Brent/WTI, S&P/Nasdaq, VIX, crédito.
  - Geopolítica: comunicados oficiales o cables de referencia.
- Fallback si faltan datos:
  - Si falta publicación oficial intraperiodo, usar discurso/comunicado más reciente y mercado en tiempo real.
  - Si falta dato sectorial, reemplazar por activo proxy y explicitar limitación.

## 4. Mercado

- Objetivo: integrar precios en una lectura transversal de posicionamiento y estrés.
- Subbloques obligatorios:
  - `tasas_y_curvas`
  - `fx`
  - `equity`
  - `credito_y_spreads`
  - `commodities_clave`
- Campos obligatorios:
  - `nivel_actual`
  - `variacion_semanal`
  - `driver_principal`
  - `lectura_de_flujos_vs_fundamentals`
- Campos opcionales:
  - `posicionamiento_extremo`
  - `distorsion_por_intervencion`
- Fuentes requeridas:
  - Precios de cierre o series comparables de la semana.
  - Una referencia de flujo, licitación o posicionamiento cuando aplique.
- Fallback si faltan datos:
  - Si falta cierre formal, usar último dato líquido disponible.
  - Si no hay dato de flujos, mantener lectura descriptiva y no inferir causalidad fuerte.

## 5. Escenarios

- Objetivo: ordenar lectura en `base`, `alcista` y `bajista`.
- Escenarios obligatorios:
  - `escenario_base`
  - `escenario_positivo`
  - `escenario_negativo`
- Campos obligatorios por escenario:
  - `disparadores`
  - `mecanismo`
  - `activos_mas_sensibles`
  - `probabilidad_cualitativa`
  - `hito_que_lo_valida`
  - `hito_que_lo_descarta`
- Campos opcionales:
  - `ventana_temporal`
  - `implicancia_politica`
- Fuentes requeridas:
  - Síntesis de secciones Argentina, internacional y mercado.
  - Al menos un dato o precio de validación por escenario.
- Fallback si faltan datos:
  - Reducir a `base + riesgos` si no hay evidencia suficiente para escenarios alternativos robustos.
  - Bajar confianza si la validación depende de precios intervenidos.

## 6. Riesgos que rompen el escenario

- Objetivo: listar riesgos discretos o acumulativos que invalidan la tesis central.
- Campos obligatorios:
  - `riesgo`
  - `tipo` (`macro` | `mercado` | `politico` | `externo`)
  - `canal_de_transmision`
  - `senal_temprana`
  - `impacto_probable`
- Campos opcionales:
  - `cobertura_o_hedge`
  - `precedente_relevante`
- Fuentes requeridas:
  - Fuente primaria o precio observable para cada riesgo.
  - Si es riesgo político, al menos un hecho institucional confirmado.
- Fallback si faltan datos:
  - Mantener el riesgo en formato condicional y no asignar probabilidad fuerte.
  - Si no hay señal temprana observable, moverlo a watchlist en lugar de riesgo central.

## 7. Qué mirar la semana próxima

- Objetivo: cerrar con agenda accionable y gatillos de seguimiento.
- Campos obligatorios:
  - `evento_o_dato`
  - `fecha_esperada`
  - `por_que_importa`
  - `resultado_positivo`
  - `resultado_negativo`
  - `mercado_o_variable_a_mirar`
- Campos opcionales:
  - `expectativa_de_consenso`
  - `dependencia_con_otro_evento`
- Fuentes requeridas:
  - Calendario oficial o agenda pública verificable.
  - Variable de mercado asociada a cada evento.
- Fallback si faltan datos:
  - Si no hay fecha cerrada, marcar `fecha_a_confirmar`.
  - Si no hay consenso disponible, definir solo umbrales de reacción.

## Salida mínima esperada

- Extensión objetivo:
  - `Qué cambió`: 5 a 8 bullets.
  - `Argentina`: 4 a 6 subsecciones cortas.
  - `Internacional`: 4 a 6 subsecciones cortas.
  - `Mercado`: tablero resumido más lectura.
  - `Escenarios`: 3 escenarios máximo.
  - `Riesgos`: 3 a 5 riesgos.
  - `Qué mirar`: 5 a 10 eventos.
- Control final:
  - Todas las secciones con `confianza`.
  - Todas las secciones con `fuentes_usadas` o `faltantes`.
  - Ninguna conclusión sin variable de confirmación o invalidación.
