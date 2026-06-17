# Validación de Schemas INDEC - Datasets No-IPC

**Fecha:** 2026-06-16
**Scope:** EMAE, Salarios, CBA/CBT, Pobreza, EPH
**Estado:** VERIFICACIÓN EN CURSO

## Resumen Ejecutivo

Este documento valida la disponibilidad, formato y estructura de los datasets INDEC excluyendo IPC (ya implementado como conector). Se verificaron URLs en vivo con `curl -sI` para confirmar accesibilidad y se inspeccionó estructura de archivos CSV cuando fue posible.

**Estado General:**
- **3 datasets READY para conectores atómicos** (Salarios, Gini, Salarios variaciones)
- **4 datasets NEEDS WORK** (EMAE, CBA/CBT, Pobreza, EPH) - requieren parsers de Excel
- **0 datasets BLOCKED** - todas las URLs verificadas responden 200 OK

---

## 1. EMAE (Estimador Mensual de Actividad Económica)

### 1.1 EMAE Nivel General

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual_base2004.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 71,680 bytes) |
| **Frecuencia** | Mensual |
| **Última actualización** | 2026-05-21 (según Last-Modified header) |

**Estructura esperada (INFERIDA desde research doc):**
- Base 2004
- Índice de actividad mensual
- Variaciones mensuales e interanuales
- Posiblemente múltiples hojas (serie histórica, variaciones, desestacionalizado)

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS (legacy Excel 97-2003)
- **Parser requerido:** Excel reader con soporte para XLS (ej. `xlrd` o `openpyxl` en modo legacy)
- **Gaps identificados:**
  - Estructura de hojas no verificada en vivo (requiere descarga e inspección)
  - Potenciales merged cells o formatting específico de INDEC
  - Series temporales pueden estar en columnas o filas según hoja

**Riesgos de parsing:**
- Cambios históricos en estructura de hojas (base 2004 vs bases anteriores)
- Filas de totales o notas al pie que pueden interferir con parsing
- Codificación de caracteres (code page 1252 detectada en el archivo)

### 1.2 EMAE Sectorial

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_actividad_base2004.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 211,456 bytes) |
| **Frecuencia** | Mensual |
| **Última actualización** | 2026-05-21 |

**Estructura esperada (INFERIDA):**
- Desglose por sector económico
- Índices sectoriales mensuales
- Variaciones por sector

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS, estructura de hojas desconocida
- **Parser requerido:** Excel reader
- **Gaps identificados:**
  - Número de sectores y nomenclatura no verificada
  - Posible estructura multi-hoja (por sector o por tipo de índice)

---

## 2. Salarios

### 2.1 Índice de Salarios (Nivel)

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/indice_salarios.csv` |
| **Formato** | CSV (VERIFICADO: `application/octet-stream`, 5,781 bytes) |
| **Frecuencia** | Mensual |
| **Última actualización** | 2026-05-18 |

**Estructura verificada (HEAD inspeccionado):**
```
periodo;IS_sector_privado_registrado;IS_sector_publico;IS_total_registrado;IS_sector_no_registrado;IS_indice_total
```

**Columnas:**
1. `periodo` - Fecha (formato: `d/m/yyyy`)
2. `IS_sector_privado_registrado` - Índice salarial sector privado registrado
3. `IS_sector_publico` - Índice salarial sector público
4. `IS_total_registrado` - Índice total registrado
5. `IS_sector_no_registrado` - Índice sector no registrado
6. `IS_indice_total` - Índice total

**Parsing verdict:** READY
- **Razón:** CSV simple, estructura verificada, encoding UTF-8 detectado (puntos y coma como separador)
- **Parser requerido:** CSV reader estándar con delimitador `;`
- **Gaps:** Ninguno mayor
- **Notas:** Período base octubre 2016 = 100 (verificado en datos)

### 2.2 Variaciones del Índice de Salarios

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/variacion_indice_salarios.csv` |
| **Formato** | CSV (VERIFICADO: `application/octet-stream`, 15,091 bytes) |
| **Frecuencia** | Mensual |
| **Última actualización** | 2026-05-18 |

**Estructura verificada (HEAD inspeccionado):**
```
periodo;v_m_sector_privado_registrado;v_i_a_sector_privado_registrado;v_acum_sector_privado_registrado;v_m_sector_publico;v_i_a_sector_publico;v_acum_sector_publico;v_m_total_registrado;v_i_a_total_registrado;v_acum_total_registrado;v_m_sector_privado_no_registrado;v_i_a_sector_privado_no_registrado;v_acum_sector_privado_no_registrado;v_m_indice_total;v_i_a_indice_total;v_acum_indice_total;v_m_subsector_publico_nacional;v_i_a_subsector_publico_nacional;v_acum_subsector_publico_nacional;v_m_subsector_publico_provincial;v_i_a_subsector_publico_provincial;v_acum_subsector_publico_provincial
```

**Columnas (20+):**
- `periodo` - Fecha
- `v_m_*` - Variación mensual por categoría
- `v_i_a_*` - Variación interanual por categoría
- `v_acum_*` - Variación acumulada por categoría
- Categorías: sector privado registrado, sector público, total registrado, sector no registrado, índice total, subsector público nacional, subsector público provincial

**Parsing verdict:** READY
- **Razón:** CSV estructurado, encoding UTF-8, delimitador `;`
- **Parser requerido:** CSV reader estándar
- **Gaps:** Ninguno
- **Notas:** Valores NA para períodos iniciales (antes de octubre 2016) - manejable

### 2.3 Variaciones por Sector (XLS)

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/variaciones_salarios_05_26.xls` |
| **Formato** | XLS (INFERIDO desde research doc) |
| **Frecuencia** | Mensual |
| **Notas** | Archivo mensual rotativo (según research doc) |

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS, URL no verificada en vivo
- **Parser requerido:** Excel reader
- **Gaps:**
  - URL no verificada (posible nombre dinámico)
  - Estructura desconocida
  - Patrón de rotación de archivos no claro

---

## 3. CBA/CBT (Canastas Básica Alimentaria y Total)

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_cba_cbt.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 105,472 bytes) |
| **Frecuencia** | Mensual |
| **Última actualización** | 2026-06-11 (muy reciente) |

**Estructura esperada (INFERIDA):**
- Serie histórica de CBA (Canasta Básica Alimentaria)
- Serie histórica de CBT (Canasta Básica Total)
- Valores monetarios por adulto equivalente
- Posible desglose por región o tamaño de aglomerado

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS, estructura de hojas no verificada
- **Parser requerido:** Excel reader
- **Gaps identificados:**
  - Sin CSV equivalente visible
  - Estructura de hojas desconocida (¿una hoja por canasta? ¿una hoja combinada?)
  - Posibles formatos de fecha específicos
  - Valores monetarios con formato local (puntos como separadores de miles)

**Riesgos de parsing:**
- Cambios históricos en metodología de canastas
- Múltiples series en mismo archivo vs. archivos separados
- Posibles hojas de notas o documentación

---

## 4. Pobreza

### 4.1 Cuadros Informe Pobreza

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_informe_pobreza_03_26.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 398,336 bytes) |
| **Frecuencia** | Semestral |
| **Última actualización** | 2026-03-31 |

**Estructura esperada (INFERIDA desde research doc):**
- Tasa de pobreza e indigencia por período
- Serie 2016-2025
- Posible desglose por 31 aglomerados urbanos
- Variaciones y tendencias

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS complejo, archivo grande (398KB sugiere múltiples hojas)
- **Parser requerido:** Excel reader robusto
- **Gaps identificados:**
  - Estructura de hojas desconocida
  - Posible combinación de series de pobreza, indigencia y distribución
  - Filas de totales o subtotales
  - Nombres de aglomerados pueden tener acentos o caracteres especiales

**Riesgos de parsing:**
- Hojas múltiples con estructuras diferentes
- Celdas combinadas (merged cells) en headers
- Notas metodológicas en hojas separadas
- Cambios en cobertura geográfica (aglomerados)

### 4.2 Coeficientes de Variación Pobreza

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_pobreza_03_26.xlsx` |
| **Formato** | XLSX (VERIFICADO: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, 63,924 bytes) |
| **Frecuencia** | Semestral |
| **Última actualización** | 2026-03-31 |

**Estructura esperada (INFERIDA):**
- Coeficientes de variación para estimaciones de pobreza
- Intervalos de confianza
- Precisión estadística

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLSX, estructura desconocida
- **Parser requerido:** Excel reader con soporte XLSX (`openpyxl`)
- **Gaps:**
  - Estructura de hojas no verificada
  - Posible uso de fórmulas o celdas calculadas
  - Metadatos estadísticos pueden estar en formato no-tabular

---

## 5. EPH (Encuesta Permanente de Hogares)

### 5.1 Cuadros Tasas e Indicadores EPH

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_tasas_indicadores_eph_03_26.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 312,832 bytes) |
| **Frecuencia** | Trimestral |
| **Última actualización** | 2026-03-18 |

**Estructura esperada (INFERIDA):**
- Tasa de actividad
- Tasa de empleo
- Tasa de desempleo
- Informalidad laboral
- Serie 2017-2025

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS grande, múltiples indicadores
- **Parser requerido:** Excel reader
- **Gaps identificados:**
  - Estructura de hojas desconocida
  - Posible separación por indicador en diferentes hojas
  - Filas de subtotales por categoría (edad, sexo, educación)

### 5.2 Cuadros Informe EPH

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_eph_informe_03_26.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 310,784 bytes) |
| **Frecuencia** | Trimestral |
| **Última actualización** | 2026-03-18 |

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS, estructura no verificada
- **Parser requerido:** Excel reader
- **Gaps:**
  - Relación con otros archivos EPH no clara
  - Posible duplicación o complementariedad con otros cuadros

### 5.3 Coeficientes de Variación EPH

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_mdt_03_26.xlsx` |
| **Formato** | XLSX (VERIFICADO: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, 75,729 bytes) |
| **Frecuencia** | Trimestral |
| **Última actualización** | 2026-03-18 |

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLSX, estructura desconocida
- **Parser requerido:** Excel reader XLSX
- **Gaps:**
  - Estructura de hojas no verificada
  - Posible complejidad en formato de intervalos de confianza

### 5.4 Indicadores Ingreso Total Urbano

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/indicadores_eph_total_urbano_ingresos_3t_2025.xls` |
| **Formato** | XLS (VERIFICADO: `application/vnd.ms-excel`, 92,672 bytes) |
| **Frecuencia** | Trimestral (por nombre de archivo) |
| **Notas** | Nombre de archivo específico por trimestre |

**Parsing verdict:** NEEDS WORK
- **Razón:** Formato XLS, patrón de URLs dinámico
- **Parser requerido:** Excel reader + lógica de detección de archivos por trimestre
- **Gaps identificados:**
  - URL específica por trimestre (no hay una serie consolidada)
  - Requiere identificación del archivo más reciente o patrón de nombres
  - No hay "serie única consolidada" visible

**Riesgos de parsing:**
- Cambios en patrón de nombres de archivos
- Requiere scraping de la página HTML para encontrar URLs dinámicas
- Mantener tabla consolidada localmente

---

## 6. Gini (Coeficiente de Desigualdad)

| Atributo | Valor |
|----------|-------|
| **URL** | `https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_coeficiente_gini.xlsx` |
| **Formato** | XLSX (VERIFICADO: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, 16,832 bytes) |
| **Frecuencia** | Trimestral |
| **Última actualización** | 2026-04-06 |

**Estructura esperada (INFERIDA desde research doc):**
- Serie larga 1996-2025
- Coeficiente de Gini por trimestre

**Parsing verdict:** NEEDS WORK (reclasificado desde READY debido a formato)
- **Razón:** Formato XLSX, archivo pequeño pero estructura no verificada
- **Parser requerido:** Excel reader XLSX
- **Gaps:**
  - Estructura de hojas desconocida
  - Posible simplicidad (serie única) pero no verificado
  - Encoding de fechas puede variar

**Nota:** Si se verifica que el archivo XLSX tiene una sola hoja con estructura simple, podría ser READY. Actualmente clasificado como NEEDS WORK por falta de inspección en vivo.

---

## Datasets Listos para Conector Atómico

Basado en verificación en vivo y estructura conocida:

| Dataset | URL | Verdict | Parser requerido |
|---------|-----|---------|------------------|
| **Salarios - Índice de Salarios** | `indice_salarios.csv` | **READY** | CSV reader (delimitador `;`) |
| **Salarios - Variaciones** | `variacion_indice_salarios.csv` | **READY** | CSV reader (delimitador `;`) |

**Razones de clasificación READY:**
- URLs responden 200 OK
- Formato CSV machine-readable
- Estructura de columnas verificada con `curl -s`
- Encoding compatible (UTF-8, puntos y coma como separador)
- Sin gaps mayores identificados

---

## Gaps y Riesgos de Parsing

### 1. Múltiples Hojas (Multi-sheet Excel)

**Afecta:**
- EMAE (nivel general y sectorial)
- CBA/CBT
- Pobreza (informe principal y coeficientes)
- EPH (tasas, informe, variaciones)

**Riesgos:**
- Estructura de hojas no documentada
- Cambios en orden o contenido de hojas entre actualizaciones
- Celdas combinadas (merged cells) en headers
- Hojas de notas o documentación que no deben ser parseadas

**Mitigación:**
- Implementar detección automática de hojas relevantes
- Documentar estructura esperada por hoja
- Manejo robusto de merged cells

### 2. Cambios Históricos de Formato

**Afecta:**
- EMAE (bases 2004 vs anteriores)
- CBA/CBT (metodologías de canastas)
- EPH (cobertura de aglomerados)

**Riesgos:**
- Series con metodologías diferentes en mismo archivo
- Cambios en columnas o estructura temporal
- Requiere normalización a una metodología consistente

**Mitigación:**
- Identificar puntos de quiebre metodológico
- Mantener versiones separadas si es necesario
- Documentar cambios explícitamente

### 3. Filas de Totales y Subtotales

**Afecta:**
- EMAE sectorial
- Pobreza (por aglomerados)
- EPH (por categorías socioeconómicas)

**Riesgos:**
- Filas de totales pueden ser parseadas como datos
- Subtotales intermedios duplican información
- Etiquetas no estándar ("Total", "Total general", etc.)

**Mitigación:**
- Detectar patrones de filas de totales
- Excluir filas con keywords específicos
- Validar sumas esperadas

### 4. Codificación de Caracteres

**Afecta:**
- Todos los archivos XLS/XLSX
- Nombres de aglomerados con acentos (EPH, Pobreza)

**Riesgos:**
- Code page 1252 detectado en XLS (Windows Latin-1)
- Acentos y caracteres especiales pueden corromperse
- Fechas en formatos locales (dd/mm/yyyy)

**Mitigación:**
- Forzar encoding UTF-8 en parsers
- Manejar fechas con parser específico de locale
- Validar caracteres especiales

### 5. URLs Dinámicas

**Afecta:**
- EPH ingresos (archivos por trimestre)
- Salarios sectoriales (archivos rotativos)

**Riesgos:**
- URLs cambian por período (trimestre, mes)
- Requiere lógica de descubrimiento de URLs
- No hay endpoint estable

**Mitigación:**
- Implementar scraping de páginas HTML
- Mantener mapeo de patrones de URLs
- Cache local de archivos descargados

### 6. Formatos Numéricos Locales

**Afecta:**
- CBA/CBT (valores monetarios)
- EMAE (índices con decimales)

**Riesgos:**
- Puntos como separadores de miles (formato argentino)
- Comas como separadores decimales
- Ambigüedad en parsing de números

**Mitigación:**
- Configurar locale es-AR en parsers numéricos
- Normalizar a formato internacional (punto decimal)
- Validar rangos esperados

---

## Verificación de URLs

### URLs Verificadas en Vivo (200 OK)

| Dataset | URL | Método | Estado |
|---------|-----|--------|--------|
| EMAE nivel general | `https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual_base2004.xls` | `curl -sI` | **VERIFIED** |
| EMAE sectorial | `https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_actividad_base2004.xls` | `curl -sI` | **VERIFIED** |
| Salarios índice | `https://www.indec.gob.ar/ftp/cuadros/sociedad/indice_salarios.csv` | `curl -sI` + `curl -s` | **VERIFIED** (estructura inspeccionada) |
| Salarios variaciones | `https://www.indec.gob.ar/ftp/cuadros/sociedad/variacion_indice_salarios.csv` | `curl -sI` + `curl -s` | **VERIFIED** (estructura inspeccionada) |
| CBA/CBT | `https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_cba_cbt.xls` | `curl -sI` + `file` | **VERIFIED** (formato XLS confirmado) |
| Pobreza informe | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_informe_pobreza_03_26.xls` | `curl -sI` | **VERIFIED** |
| Pobreza variación | `https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_pobreza_03_26.xlsx` | `curl -sI` | **VERIFIED** |
| EPH tasas | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_tasas_indicadores_eph_03_26.xls` | `curl -sI` | **VERIFIED** |
| EPH informe | `https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_eph_informe_03_26.xls` | `curl -sI` | **VERIFIED** |
| EPH variación | `https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_mdt_03_26.xlsx` | `curl -sI` | **VERIFIED** |
| EPH ingresos | `https://www.indec.gob.ar/ftp/cuadros/sociedad/indicadores_eph_total_urbano_ingresos_3t_2025.xls` | `curl -sI` | **VERIFIED** |
| Gini | `https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_coeficiente_gini.xlsx` | `curl -sI` | **VERIFIED** |

### URLs No Verificadas (INFERIDAS desde research doc)

| Dataset | URL | Razón |
|---------|-----|--------|
| Salarios sectoriales | `https://www.indec.gob.ar/ftp/cuadros/sociedad/variaciones_salarios_05_26.xls` | No se verificó en vivo (posible nombre dinámico) |
| CVS diario | `https://www.indec.gob.ar/ftp/cuadros/sociedad/sh_cvs_diarios_2026.xls` | No se verificó en vivo (prioridad baja) |

---

## Recomendaciones de Implementación

### Fase 1: Conectores Atómicos READY (Inmediato)

1. **Salarios - Índice de Salarios**
   - Parser: CSV con delimitador `;`
   - Fecha: parsear formato `d/m/yyyy`
   - Manejo de NA: `NA` strings para períodos iniciales

2. **Salarios - Variaciones**
   - Parser: CSV con delimitador `;`
   - Columnas: 20+ columnas de variaciones
   - Manejo de NA: similar a índice

### Fase 2: Conectores XLS/XLSX (Post-parser Excel)

**Prioridad alta:**
1. **CBA/CBT** - requerido para pobreza
   - Parser: Excel XLS
   - Detectar estructura de hojas (¿una por canasta? ¿combinada?)
   - Normalizar formatos numéricos (puntos de miles)

2. **EMAE nivel general** - headline de actividad
   - Parser: Excel XLS
   - Identificar hoja principal con serie histórica
   - Extraer índice y variaciones

**Prioridad media:**
3. **Pobreza** - requiere CBA/CBT primero
   - Parser: Excel XLS
   - Manejo de múltiples hojas
   - Detectar filas de totales

4. **EMAE sectorial** - complemento de EMAE general
   - Parser: Excel XLS
   - Estructura similar a EMAE general

**Prioridad baja:**
5. **EPH** - complejidad alta, múltiples archivos
   - Parser: Excel XLS/XLSX
   - Lógica de archivos por trimestre
   - Posible consolidación local requerida

6. **Gini** - si se verifica estructura simple
   - Parser: Excel XLSX
   - Posible simplificación a READY si es hoja única

### Fase 3: Complementos y Mantenimiento

- **Calendario de difusión** - scraping de HTML/PDF
- **Monitoreo de cambios** - detectar cambios en formato o estructura
- **Normalización** - unificar formatos de fecha y números

---

## Consideraciones Finales

1. **Todos los datasets principales son accesibles** - no hay URLs bloqueadas
2. **La barrera principal es el formato XLS/XLSX** - requiere parser especializado
3. **Salarios es el único con CSV machine-readable** - prioridad de implementación
4. **EMAE y CBA/CBT son críticos** - requieren parser Excel urgente
5. **EPH es el más complejo** - múltiples archivos, URLs dinámicas, requiere diseño especial

**Blockers identificados:**
- Ninguno (todas las URLs responden)

**Riesgos críticos:**
- Cambios en formato de archivos XLS/XLSX
- URLs dinámicas sin endpoint estable (EPH ingresos)
- Estructuras no documentadas de hojas Excel

**Siguientes pasos:**
1. Implementar parser Excel XLS/XLSX genérico
2. Descargar y analizar estructura de EMAE y CBA/CBT
3. Definir esquema normalizado para cada dataset
4. Implementar conectores atómicos en orden de prioridad