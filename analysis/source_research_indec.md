# Fuentes INDEC para tablero Argentina

Fecha de verificación: 2026-06-14.

## Resumen ejecutivo

- INDEC sí ofrece fuentes oficiales verificables para `inflación`, `actividad`, `empleo/ingresos` y `pobreza/canastas`.
- El patrón dominante no es una API homogénea: prevalecen `XLS`, `CSV`, `XLSX`, `PDF` y páginas HTML con links a archivos en `/ftp` o `/uploads`.
- El `calendario de difusión` sí es automatizable desde fuente oficial porque combina:
  - HTML: https://www.indec.gob.ar/Calendario/Fecha/0
  - PDFs semestrales: https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_1sem2026.pdf y https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf
  - JSON embebido en el HTML del calendario.

## Fuentes recomendadas

| Tema | Dataset / indicador | URL oficial | Formato usable | Frecuencia | Uso en tablero | Notas operativas |
| --- | --- | --- | --- | --- | --- | --- |
| Inflación | IPC nacional | https://www.indec.gob.ar/Nivel4/Tema/3/5/31 | HTML + PDF + XLS + CSV | mensual | headline de inflación | Página principal del IPC con series históricas y próximo release. |
| Inflación | IPC divisiones / bienes y servicios | https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv | CSV | mensual | aperturas por división | Serie nacional machine-readable. |
| Inflación | IPC aperturas principales | https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.csv | CSV | mensual | aperturas más finas | Útil para alimentos, regulados, etc. |
| Inflación | Precios promedio IPC | https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_precios_promedio.xls | XLS | mensual | validación de precios puntuales | No reemplaza al índice; sirve para inspección. |
| Inflación | Metodología inflación núcleo | https://www.indec.gob.ar/ftp/cuadros/economia/ipc_metodologia_17_07_16.pdf | PDF | eventual | documentación metodológica | Ver gap sobre serie núcleo. |
| Inflación | Visualizador oficial de precios | https://shiny.indec.gob.ar/vip/ | web app | mensual | exploración manual | Útil para chequeos; no la trataría como fuente primaria de pipeline sin scraping controlado. |
| Actividad | EMAE | https://www.indec.gob.ar/Nivel4/Tema/3/9/48 | HTML + PDF + XLS | mensual | proxy oficial de actividad | La página publica el próximo release y los cuadros históricos. |
| Actividad | EMAE nivel general | https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual_base2004.xls | XLS | mensual | serie principal de actividad | Base 2004, índice y variaciones. |
| Actividad | EMAE por sector | https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_actividad_base2004.xls | XLS | mensual | desglose sectorial | Sin CSV visible en la página verificada. |
| Empleo | EPH mercado de trabajo | https://www.indec.gob.ar/Nivel4/Tema/4/31/58 | HTML + PDF + XLS + XLSX | trimestral | empleo, desempleo, actividad | Cobertura 31 aglomerados; incluye informalidad laboral. |
| Empleo | Cuadros tasas e indicadores EPH | https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_tasas_indicadores_eph_03_26.xls | XLS | trimestral | tasa de actividad, empleo, desempleo | Serie 2017-2025 en el archivo verificado. |
| Empleo | Principales tasas mercado laboral EPH | https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_eph_informe_03_26.xls | XLS | trimestral | tablero sintético de mercado laboral | |
| Empleo | Coeficientes de variación EPH | https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_mdt_03_26.xlsx | XLSX | trimestral | calidad/intervalos | Útil para auditar robustez. |
| Empleo | Tabulados EPH online | https://www.indec.gob.ar/indec/web/Institucional-Indec-bases_EPH_tabulado_continua | sistema web | continua | consultas ad hoc | Requiere navegación, no simple descarga. |
| Ingresos | EPH distribución del ingreso | https://www.indec.gob.ar/Nivel4/Tema/4/31/60 | HTML + PDF + XLS + XLSX + ZIP | trimestral | deciles, Gini, ingresos familiares | Fuente oficial para distribución. |
| Ingresos | Indicadores ingreso total urbano | https://www.indec.gob.ar/ftp/cuadros/sociedad/indicadores_eph_total_urbano_ingresos_3t_2025.xls | XLS | trimestral | TNU de ingresos | Publican por trimestre; no serie única consolidada visible. |
| Ingresos | Gini | https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_coeficiente_gini.xlsx | XLSX | trimestral | desigualdad | Serie larga 1996-2025. |
| Salarios | Índice de salarios | https://www.indec.gob.ar/Nivel4/Tema/4/31/61 | HTML + PDF + XLS + CSV | mensual | salarios nominales | Incluye registrado, público y no registrado estimado. |
| Salarios | Serie índice de salarios | https://www.indec.gob.ar/ftp/cuadros/sociedad/indice_salarios.csv | CSV | mensual | nivel del índice | Machine-readable. |
| Salarios | Variaciones del índice de salarios | https://www.indec.gob.ar/ftp/cuadros/sociedad/variacion_indice_salarios.csv | CSV | mensual | m/m, acumulada | Machine-readable. |
| Salarios | Variaciones por sector | https://www.indec.gob.ar/ftp/cuadros/sociedad/variaciones_salarios_05_26.xls | XLS | mensual | sector público/privado | Archivo mensual rotativo. |
| Salarios | CVS diario | https://www.indec.gob.ar/ftp/cuadros/sociedad/sh_cvs_diarios_2026.xls | XLS | diaria/publicación periódica | contratos indexados/CVS | Más útil como complemento que como headline macro. |
| Canastas | CBA y CBT | https://www.indec.gob.ar/Nivel4/Tema/4/43/149 | HTML + PDF + XLS | mensual | línea de indigencia/pobreza monetaria | Fuente mensual oficial para canastas. |
| Canastas | Serie CBA/CBT | https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_cba_cbt.xls | XLS | mensual | canastas por adulto equivalente | No vi CSV en la página verificada. |
| Pobreza | Línea de pobreza / indigencia | https://www.indec.gob.ar/Nivel4/Tema/4/46/152 | HTML + PDF + XLS + XLSX | semestral | tasa de pobreza e indigencia | Combina EPH + CBT/CBA. |
| Pobreza | Cuadros pobreza 31 aglomerados | https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_informe_pobreza_03_26.xls | XLS | semestral | pobreza/indigencia headline | Serie 2016-2025 según archivo verificado. |
| Pobreza | Coeficientes de variación pobreza | https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_pobreza_03_26.xlsx | XLSX | semestral | precisión estadística | |
| Calendario | Calendario de difusión | https://www.indec.gob.ar/Calendario/Fecha/0 | HTML + JSON embebido + PDF | continuo / semestral | agenda de publicaciones | Incluye categorías como IPC, EMAE, salarios, pobreza, EPH. |

## Qué alimenta cada bloque del tablero

### Inflación

Fuente primaria recomendada:

- IPC headline: `serie_ipc_divisiones.csv`
- Aperturas: `serie_ipc_aperturas.csv`
- Validación metodológica: página IPC + PDF metodológico

Cobertura:

- `headline mensual`
- `interanual`
- `aperturas por división`
- `precios promedio seleccionados` si se necesita inspección puntual

### Actividad

Fuente primaria recomendada:

- EMAE nivel general: `sh_emae_mensual_base2004.xls`
- EMAE sectorial: `sh_emae_actividad_base2004.xls`

Cobertura:

- `nivel de actividad mensual`
- `variación m/m`
- `variación interanual`
- `lectura sectorial`

### Empleo / ingresos

Fuentes primarias recomendadas:

- Mercado de trabajo EPH: `cuadros_tasas_indicadores_eph_03_26.xls`, `cuadros_eph_informe_03_26.xls`
- Distribución del ingreso EPH: página 4/31/60 + archivos trimestrales de ingreso
- Salarios: `indice_salarios.csv`, `variacion_indice_salarios.csv`

Cobertura:

- `tasa de actividad`
- `tasa de empleo`
- `desempleo`
- `informalidad laboral`
- `distribución del ingreso`
- `coeficiente de Gini`
- `salarios nominales`

### Pobreza / canastas

Fuentes primarias recomendadas:

- Canastas: `serie_cba_cbt.xls`
- Pobreza: `cuadros_informe_pobreza_03_26.xls`

Cobertura:

- `CBA`
- `CBT`
- `pobreza`
- `indigencia`
- `apertura por grupos de edad` si se usa el XLSX de coeficientes y cuadros complementarios

## Gaps y fuentes complementarias necesarias

### 1. IPC núcleo

Gap:

- En la página verificada del IPC encontré la `metodología` de inflación núcleo, pero no una `serie dedicada, descargable y estable` en CSV/XLS visible desde esa página.

Implicancia:

- Para un tablero automatizado no conviene asumir que la serie de núcleo está lista para consumir desde INDEC con el mismo nivel de facilidad que el IPC headline.

Complemento sugerido:

- Primero intentar una segunda pasada dentro de INDEC o `shiny.indec.gob.ar/vip/`.
- Si no aparece un archivo estable, dejar `IPC núcleo` como campo complementario/manual o usar scraping controlado del visualizador oficial.

### 2. Falta de API homogénea

Gap:

- No vi una API REST uniforme expuesta en las páginas relevadas; la publicación oficial opera sobre archivos `XLS/CSV/XLSX/PDF` y HTML.

Implicancia:

- El pipeline debe contemplar `descarga de archivos` y no asumir JSON/API para todo.

Complemento sugerido:

- Implementar un fetcher por tipo de archivo.
- Mantener una capa de normalización local.

### 3. EPH e ingresos no vienen como una sola serie consolidada simple

Gap:

- En EPH mercado de trabajo y distribución del ingreso aparecen múltiples archivos por corte, más anexos, coeficientes y tabulados.

Implicancia:

- Hay más trabajo de modelado que en IPC o salarios.

Complemento sugerido:

- Construir una tabla curada interna con columnas estables por trimestre.
- Para microdatos o cruces a medida, usar además el sistema de bases/tabulados EPH del propio INDEC.

### 4. Canastas en XLS, no CSV visible

Gap:

- Para CBA/CBT verifiqué `serie_cba_cbt.xls`, pero no un CSV equivalente visible en la página.

Implicancia:

- Requiere parser de Excel.

Complemento sugerido:

- Ingesta directa de XLS.

### 5. Calendario oficial: mejor usar PDF semestral + HTML/JSON

Gap:

- El calendario es oficial y rico, pero el JSON está embebido en la página HTML, no documentado como endpoint separado.

Implicancia:

- Si cambia el frontend puede romper un scraper ingenuo.

Complemento sugerido:

- Tomar como base estable los PDFs semestrales.
- Usar el HTML/JSON embebido para validación fina de fechas y horas.

## Recomendación de implementación

Prioridad alta para pipeline:

1. IPC (`CSV`)
2. Salarios (`CSV`)
3. EMAE (`XLS`)
4. CBA/CBT (`XLS`)
5. Pobreza (`XLS/XLSX`)
6. EPH mercado de trabajo e ingresos (`XLS/XLSX`)
7. Calendario (`PDF + HTML/JSON`)

Prioridad de diseño:

- Preferir `CSV` cuando exista.
- Donde sólo haya `XLS/XLSX`, parsear y versionar esquema local.
- Usar los `PDF` sólo como respaldo editorial o validación de publicación, no como fuente primaria si existe tabla descargable.
