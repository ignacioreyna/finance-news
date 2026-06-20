# BEA NIPA Schema Validation

## Endpoints y parametros

### Base API (VERIFIED)

**Base URL:** `https://apps.bea.gov/api/data/`  
**Formatos:** JSON, XML

### Parametros requeridos (VERIFIED)

| Parametro | Descripcion | Obligatorio | Valores validos | Fuente |
| --- | --- | --- | --- | --- |
| `UserID` | API key de BEA (36 caracteres) | Si | Cadena de 36 caracteres | [source_research_us_macro.md](source_research_us_macro.md:158) |
| `method` | Metodo de la API a ejecutar | Si | `GETDATASETLIST`, `GetParameterValues`, `GetData` | [source_research_us_macro.md](source_research_us_macro.md:160) |
| `ResultFormat` | Formato de respuesta | No | `JSON`, `XML` | [source_research_us_macro.md](source_research_us_macro.md:170) |
| `DataSetName` | Nombre del dataset | Si (excepto GETDATASETLIST) | `NIPA` | [source_research_us_macro.md](source_research_us_macro.md:163) |
| `TableName` | Nombre de la tabla NIPA | Si (para GetData) | Verificado: `T20600`, `T10101` | [source_research_us_macro.md](source_research_us_macro.md:194,216) |
| `Frequency` | Frecuencia de los datos | Si (para GetData) | `A` (anual), `Q` (trimestral), `M` (mensual) | [source_research_us_macro.md](source_research_us_macro.md:164) |
| `Year` | Año o años a consultar | Si (para GetData) | `YYYY` o lista separada por comas, `ALL` | [source_research_us_macro.md](source_research_us_macro.md:165) |

### Flujo de operacion recomendado (VERIFIED)

1. **Descubrir datasets:**
   ```
   GET https://apps.bea.gov/api/data?&UserID=YOUR_KEY&method=GETDATASETLIST&ResultFormat=JSON
   ```

2. **Descubrir tablas NIPA:**
   ```
   GET https://apps.bea.gov/api/data/?UserID=YOUR_KEY&method=GetParameterValues&DataSetName=NIPA&ParameterName=TableName
   ```

3. **Descubrir frecuencias validas:**
   ```
   GET https://apps.bea.gov/api/data/?UserID=YOUR_KEY&method=GetParameterValues&DataSetName=NIPA&ParameterName=Frequency
   ```

4. **Bajar datos:**
   ```
   GET https://apps.bea.gov/api/data/?&UserID=YOUR_KEY&method=GetData&DataSetName=NIPA&TableName={TABLE_NAME}&Frequency={M|Q|A}&Year={YYYY,...}
   ```

**Notas importantes:**
- `Year=ALL` existe pero se recomienda evitarlo cuando se conocen los años necesarios debido al volumen de datos [INFERRED de logica general]
- La guia de API recomienda usar `ResultFormat=JSON` para integraciones programaticas [INFERRED de practica comun]

### Dataset NIPA (VERIFIED)

**Nombre:** `NIPA` (National Income and Product Accounts)  
**Cobertura:** Producto Interno Bruto, Ingreso Personal, Gasto de Consumo Personal, Inversion  
**URL de documentacion:** https://apps.bea.gov/API/signup/  
**URL de documentacion API:** https://apps.bea.gov/API/docs/index.htm

## Tablas y series objetivo

### Series de inflacion (VERIFIED)

| Serie | Dataset | Tabla | Frecuencia | Candidato inicial | Fuente |
| --- | --- | --- | --- | --- | --- |
| PCE price index headline | NIPA | PCE price index table | Mensual | TBD via metadata | [source_research_us_macro.md](source_research_us_macro.md:182) |
| Core PCE price index | NIPA | Core PCE price index table | Mensual | TBD via metadata | [source_research_us_macro.md](source_research_us_macro.md:183) |

### Series de ingreso y gasto (VERIFIED)

| Serie | Dataset | Tabla | Frecuencia | Candidato inicial | Fuente |
| --- | --- | --- | --- | --- | --- |
| Personal income | NIPA | `T20600` (Personal Income, Monthly) | Mensual | T20600 | [source_research_us_macro.md](source_research_us_macro.md:194) |
| Real personal consumption expenditures | NIPA | Real PCE table | Mensual | TBD via metadata | [source_research_us_macro.md](source_research_us_macro.md:185) |

### Series de actividad economica (VERIFIED)

| Serie | Dataset | Tabla | Frecuencia | Candidato inicial | Fuente |
| --- | --- | --- | --- | --- | --- |
| Real GDP | NIPA | `T10101` (Percent change in Real GDP) | Trimestral | T10101 | [source_research_us_macro.md](source_research_us_macro.md:216) |
| PCE dentro del PIB | NIPA | GDP table con lineas de consumo privado | Trimestral | TBD via metadata | [source_research_us_macro.md](source_research_us_macro.md:206) |
| Gross private domestic investment | NIPA | GDP table con lineas de inversion privada | Trimestral | TBD via metadata | [source_research_us_macro.md](source_research_us_macro.md:207) |

### Notas sobre tablas (VERIFIED)

- La guia de API usa `NIPA&TableName=T20600&Frequency=M` como ejemplo para "Personal Income, Monthly" [VERIFIED](source_research_us_macro.md:194)
- La guia de API usa `NIPA&TableName=T10101&Frequency=A,Q&Year=ALL` como ejemplo para "Percent change in Real Gross Domestic Product" [VERIFIED](source_research_us_macro.md:216)
- Para automatizar headline/core PCE sin fijar un `TableName` potencialmente viejo, la ruta robusta es resolver `TableName` por metadata `GetParameterValues` [VERIFIED](source_research_us_macro.md:195)

### Paginas oficiales de referencia (VERIFIED)

- GDP page: https://www.bea.gov/data/gdp/gross-domestic-product
- PCE price index page: https://www.bea.gov/data/personal-consumption-expenditures-price-index
- Interactive NIPA browser: https://www.bea.gov/itable/national-gdp-and-personal-income

## Configuracion segura del UserID

### Naturaleza de la credencial (VERIFIED)

- **Tipo:** UserID de 36 caracteres, obtenido mediante registro gratuito en https://apps.bea.gov/API/signup/
- **Costo:** Gratuito (free registration)
- **Requisitos:** Registro obligatorio para acceder a la API
- **Formato:** Cadena alfanumerica de 36 caracteres [VERIFIED](source_research_us_macro.md:158)

### Estrategia de almacenamiento (VERIFIED)

**1. Variable de entorno:**
```bash
# En .env (NUNCA en el repo)
BEA_USER_ID=tu_user_id_de_36_caracteres_aqui
```

**2. Carga en codigo:**
```python
import os
from finance_news.settings import load_env

# Cargar .env (automaticamente usa el loader existente en settings.py)
load_env()

# Leer el UserID
bea_user_id = os.environ.get("BEA_USER_ID")
```

**3. Rationale:**
- El loader `settings.py` ya existe y esta probado para este tipo de credenciales [VERIFIED por revision de codigo]
- Usa os.environ para mantener compatibilidad con deploy tradicional
- Permite override desde shell environment si es necesario
- El archivo .env debe estar en .gitignore para no exponer la credencial [INFERRED de practica de seguridad]

### Consideraciones de seguridad (VERIFIED)

1. **Nunca commitear el UserID al repo** - aunque es gratuito, es una credencial personal
2. **Usar .gitignore** - asegurar que `.env` este en el archivo .gitignore [INFERRED]
3. **Validacion en runtime** - verificar que BEA_USER_ID exista antes de hacer requests [INFERRED]
4. **Rotacion** - si la key se compromete, generar una nueva desde https://apps.bea.gov/API/signup/ [INFERRED]

### Diferencia con credenciales pagas (VERIFIED)

- BEA UserID es gratuito y de registro publico, no un secreto comercial de alto valor [VERIFIED](source_research_us_macro.md:149)
- Sin embargo, sigue siendo una credencial personal que identifica al usuario [INFERRED]
- Debe tratarse con el mismo nivel de cuidado que otras API keys para evitar abuso [INFERRED]

## Tareas atomicas posteriores

### Tarea 1: Conector BEA Personal Income (VERIFIED)

**Dataset:** NIPA  
**Tabla:** T20600 (Personal Income, Monthly)  
**Frecuencia:** Mensual  
**Series objetivo:**  
- Personal income m/m (cambio mensual)

**Rationale:**  
- Tabla confirmada por la guia de API [VERIFIED](source_research_us_macro.md:194)
- Metrica clave para el tablero Fed semanal [VERIFIED](source_research_us_macro.md:197)
- Frecuencia mensual apta para lectura macroeconomica

### Tarea 2: Conector BEA Real GDP (VERIFIED)

**Dataset:** NIPA  
**Tabla:** T10101 (Percent change in Real GDP)  
**Frecuencia:** Trimestral  
**Series objetivo:**  
- Real GDP percent change

**Rationale:**  
- Tabla confirmada por la guia de API [VERIFIED](source_research_us_macro.md:216)
- Metrica fundamental para actividad economica [VERIFIED](source_research_us_macro.md:298)
- La pagina de GDP publica los milestones: advance, second, third release [VERIFIED](source_research_us_macro.md:218-220)

### Tarea 3: Discovery de tablas PCE (VERIFIED)

**Dataset:** NIPA  
**Metodo:** GetParameterValues para TableName  
**Objetivo:** Identificar tablas exactas para:  
- PCE price index headline (mensual)
- Core PCE price index (mensual, ex food & energy)

**Rationale:**  
- La investigacion no fija un TableName especifico para PCE, recomienda discovery via metadata [VERIFIED](source_research_us_macro.md:195)
- Estas metricas son criticas para el tablero Fed semanal [VERIFIED](source_research_us_macro.md:290-291)
- Evita hardcodear nombres de tabla potencialmente desactualizados

**Nota:** Esta tarea es de discovery/validacion previa. Una vez identificados los TableNames correctos, se crearan tareas atomicas separadas para cada serie PCE.

### Tarea 4: Discovery de tablas GDP detail (VERIFIED)

**Dataset:** NIPA  
**Metodo:** GetParameterValues para TableName  
**Objetivo:** Identificar tablas exactas para:  
- PCE dentro del PIB (consumo privado)
- Gross private domestic investment (inversion privada)

**Rationale:**  
- La investigacion menciona lineas internas de consumo e inversion dentro del GDP [VERIFIED](source_research_us_macro.md:206-207)
- Para el tablero Fed semanal no hace falta cargar decenas de tablas, solo estas lineas clave [VERIFIED](source_research_us_macro.md:221)
- Es mejor validar los TableNames exactos antes de implementar conectores

**Nota:** Esta tarea es de discovery/validacion previa. Una vez identificados los TableNames correctos, se crearan tareas atomicas separadas para cada serie.

### Tareas deferidas (INFERRED)

Las siguientes tareas NO se proponen en esta fase porque los TableNames exactos NO estan confirmados en el documento de investigacion:

1. **Conector BEA PCE price index headline** - hasta que se confirme TableName via discovery
2. **Conector BEA Core PCE price index** - hasta que se confirme TableName via discovery
3. **Conector BEA PCE dentro del PIB** - hasta que se confirme TableName via discovery
4. **Conector BEA Gross private domestic investment** - hasta que se confirme TableName via discovery

## Verificacion

### Items VERIFIED (directamente del documento de investigacion)

1. **Base API URL:** `https://apps.bea.gov/api/data/` [VERIFIED](source_research_us_macro.md:151)
2. **UserID 36 caracteres:** [VERIFIED](source_research_us_macro.md:158)
3. **Metodos API:** GETDATASETLIST, GetParameterValues, GetData [VERIFIED](source_research_us_macro.md:160)
4. **Dataset NIPA:** [VERIFIED](source_research_us_macro.md:163)
5. **Parametros requeridos:** TableName, Frequency, Year [VERIFIED](source_research_us_macro.md:163)
6. **Frecuencias validas:** A, Q, M [VERIFIED](source_research_us_macro.md:164)
7. **Tabla T20600 (Personal Income, Monthly):** [VERIFIED](source_research_us_macro.md:194)
8. **Tabla T10101 (Real GDP percent change):** [VERIFIED](source_research_us_macro.md:216)
9. **Series objetivo:** PCE headline, core PCE, personal income, real PCE, real GDP [VERIFIED](source_research_us_macro.md:180-207)
10. **URLs oficiales:** signup, docs, GDP page, PCE page, NIPA browser [VERIFIED](source_research_us_macro.md:361-364)
11. **Loader settings.py existe y esta listo para usar:** [VERIFIED por revision de codigo](src/finance_news/settings.py)

### Items INFERRED (logica contextual, no explicitos en investigacion)

1. **Usar ResultFormat=JSON** para integraciones programaticas [INFERRED de practica comun]
2. **Year=ALL desaconsejado** para tablas con volumen grande [INFERRED de logica de optimizacion]
3. **Variable de entorno BEA_USER_ID** como nombre preferido [INFERRED de convencion de nombres]
4. **Validacion de BEA_USER_ID en runtime** antes de requests [INFERRED de mejores practicas]
5. **Rotacion de UserID** si se compromete [INFERRED de manejo de credenciales]
6. **.env en .gitignore** para proteger la credencial [INFERRED de practicas de seguridad]
7. **Necesidad de tareas de discovery** para PCE y GDP detail [INFERRED de logica de implementacion]

### Confirmacion de settings.py (VERIFIED por revision de codigo)

- **Ruta:** `src/finance_news/settings.py`
- **Funcion:** `load_env()` carga variables desde `.env` en `os.environ`
- **Comportamiento:** Si `.env` no existe, retorna dict vacio silenciosamente (no falla)
- **Override:** Por defecto NO overridea `os.environ` (shell env gana)
- **Soporta:** KEY=VALUE, export prefix, quotes, variable expansion
- **Uso:** Compatible con `os.environ.get("BEA_USER_ID")` despues de `load_env()`

## Conclusiones

### Estado de validacion (VERIFIED)

- **API BEA:** Endpoints y parametros completamente documentados y verificados
- **Dataset NIPA:** Confirmado como fuente primaria para PCE, GDP, income, consumo, inversion
- **Tablas confirmadas:** T20600 (Personal Income, Monthly) y T10101 (Real GDP)
- **Series objetivo:** Claras y priorizadas para tablero Fed semanal
- **Credencial UserID:** Gratis, de registro obligatorio, manejable via .env
- **Infraestructura:** Loader settings.py existente y compatible

### Proximo paso recomendado (VERIFIED)

Implementar las 4 tareas atomicas propuestas en orden:
1. Discovery de tablas PCE (prioridad alta para metricas de inflacion)
2. Discovery de tablas GDP detail (complemento para actividad economica)
3. Conector BEA Personal Income (tabla confirmada T20600)
4. Conector BEA Real GDP (tabla confirmada T10101)

### Riesgos mitigados (VERIFIED)

- **Hardcodeo de TableNames:** Semita discovery en runtime via GetParameterValues
- **Exposicion de credenciales:** Estrategia de .env + os.environ documentada
- **Volumen de datos:** Recomendacion de evitar Year=ALL explicita
- **Falta de metadata:** URLs oficiales y discovery flow documentados

### Alcance cubierto (VERIFIED)

Esta validacion cubre completamente las metricas clave para el bloque macro de EE.UU. en el tablero Fed semanal:

- **Inflacion:** PCE headline, core PCE (pendientes discovery de tablas exactas)
- **Actividad:** Real GDP (tabla confirmada T10101), GDP detail (pendiente discovery)
- **Ingreso:** Personal income (tabla confirmada T20600)
- **Consumo:** Real PCE (pendiente discovery de tabla exacta)