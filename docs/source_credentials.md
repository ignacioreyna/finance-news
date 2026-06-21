# Credenciales de Fuentes de Datos

Este documento documenta todas las variables de entorno, su obligatoriedad y qué conectores las utilizan.

## Resumen del Landscape de Credenciales

| Categoría | Estado | Descripción |
|-----------|--------|-------------|
| **Opcionales** | ✅ Libre registro | BLS, FRED, EIA, BEA - conectores funcionan sin claves pero con rate-limits más bajos |
| **Obligatorias** | ❌ Ninguna actualmente | Todos los conectores trabajan offline/sin claves por diseño |
| **Pendientes Validación** | ⚠️ Pago/Bloqueadas | BYMA, MAE - feeds pagos, requieren suscripción institucional |
| **Públicas sin credenciales** | ✅ Acceso abierto | Argentina (BCRA), FOMC, Treasury, NY Fed - ninguna clave requerida |

---

## Tabla de Variables de Entorno

| Variable | Obligatoriedad | Fuentes que la usan | Cómo obtener |
|----------|---------------|---------------------|---------------|
| `BLS_API_KEY` | Opcional | `bls_timeseries.py` (BLS Public Data API v2) | Registro gratuito en https://www.bls.gov/developers/ |
| `FRED_API_KEY` | Opcional | `fred_market_proxies.py` (FRED fredgraph.csv) | Registro gratuito en https://fred.stlouisfed.org/docs/api/api_key.html |
| `EIA_API_KEY` | Opcional | `eia_wpsr.py` (EIA Weekly Petroleum Status Report) | Registro gratuito en https://www.eia.gov/opendata/register.php |
| `BEA_USER_ID` | Opcional* | Connector BEA pendiente (Validado en `analysis/bea_nipa_schema_validation.md`) | Registro gratuito en https://apps.bea.gov/API/signup/ |

*Note: El conector BEA aún no existe, pero se validó en análisis que requiere `UserID` obligatorio de 36 caracteres.

---

## Categorías Detalladas

### 1. CREDENCIALES OPCIONALES (Free Registration)

Estas variables son opcionales pero recomendadas para evitar rate-limits y habilitar parámetros opcionales. Los conectores funcionan sin ellas pero con límites más estrictos.

#### BLS_API_KEY
- **Fuente**: Bureau of Labor Statistics (BLS) - Public Data API v2
- **Conector**: `bls_timeseries.py`
- **URL API**: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- **Registro**: https://www.bls.gov/developers/
- **Límites sin clave**: Consultas simples funcionan, pero hay restricciones en ventanas largas, metadatos opcionales y lotes grandes
- **Límites con clave**: Habilita parámetros como `catalog`, `calculations`, `annualaverage`, `aspects`
- **Series cubiertas**: CPI (headline/core), payrolls, unemployment, AHE, JOLTS
- **Uso**: Se añade al parámetro `registrationkey` en el POST request

#### FRED_API_KEY
- **Fuente**: Federal Reserve Economic Data (FRED) - St. Louis Fed
- **Conector**: `fred_market_proxies.py`
- **URL API**: `https://fred.stlouisfed.org/graph/fredgraph.csv`
- **Registro**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Límites sin clave**: El endpoint `fredgraph.csv` es público, pero sin clave puede haber límites de frecuencia
- **Series cubiertas**: WTI/Brent crude oil, Treasury real rates (DFII10, DFII5), Broad dollar index (DTWEXBGS), breakevens (T5YIE, T10YIE), forward inflation (T5YIFR)
- **Uso**: Se añade como query parameter `api_key` al GET request

#### EIA_API_KEY
- **Fuente**: U.S. Energy Information Administration (EIA)
- **Conector**: `eia_wpsr.py`
- **URL API**: `https://www.eia.gov/petroleum/supply/weekly/csv_data.csv`
- **Registro**: https://www.eia.gov/opendata/register.php
- **Límites sin clave**: CSV público, pero puede requerir API key para rate-limits más altos
- **Series cubiertas**: Weekly Petroleum Status Report (crude stocks, Cushing, gasoline, distillates, production, refinery utilization)
- **Uso**: Se añade como header o query parameter según especificación EIA

#### BEA_USER_ID
- **Fuente**: U.S. Bureau of Economic Analysis (BEA)
- **Conector**: Pendiente de implementación
- **URL API**: `https://apps.bea.gov/api/data/`
- **Registro**: https://apps.bea.gov/API/signup/
- **Límites**: Obligatorio - 36 caracteres, requerido para todas las llamadas
- **Series cubiertas**: PCE, PIB, personal income, personal spending
- **Validación**: Confirmado en `analysis/bea_nipa_schema_validation.md`
- **Uso**: Se añade como parámetro `UserID` en todas las llamadas al API

### 2. CREDENCIALES OBLIGATORIAS

**Actualmente no hay credenciales obligatorias.** Todos los conectores están diseñados para funcionar sin claves:

- Los conectores US (BLS/FRED/EIA/BEA) trabajan en modo "degraded" sin claves
- Los conectores de Argentina usan endpoints públicos sin autenticación
- FOMC, Treasury, NY Fed son completamente públicos

### 3. CREDENCIALES PENDIENTES VALIDACIÓN (Pago/Bloqueadas)

Estas fuentes requieren suscripción de pago y están bloqueadas para el MVP gratuito.

#### BYMA (Bolsas y Mercados Argentinos)
- **Estado**: **PAID-BLOCKED** - Requiere suscripción
- **Tiers disponibles**:
  - **EOD Sin costo**: 1.000 solicitudes/mes (insuficiente para MVP semanal)
  - **Delay**: USD 100/mes (79.200 req/mes)
  - **Snapshot**: USD 400/mes (237.600 req/mes)
- **Host de datos**: `api.bymadata.com.ar` (no respondió en probe, requiere token)
- **Documentación**: https://www.byma.com.ar/productos/productos-de-datos/market-data/apis
- **Validación**: Confirmado en `analysis/arg_market_access_validation.md` - NO alcanza para bonos/MEP/CCL/curva local
- **Uso en MVP**: Diferido - usar alternativas gratuitas (BCRA, índices públicos, Rava/Ambito)

#### MAE (Mercado Abierto Electrónico)
- **Estado**: **PAID-BLOCKED** - Requiere formulario + credenciales institucionales
- **Web pública**: Bloqueada por Incapsula (wall de bot)
- **API formal**: https://www.mae.com.ar/APIsMAE (requiere contrato)
- **Documentación**: https://marketdata.mae.com.ar/
- **Validación**: Confirmado en `analysis/arg_market_access_validation.md` - wall de bot sin datos directos
- **Uso en MVP**: Diferido - usar visor web o scraping controlado

#### Matba Rofex (A3)
- **Estado**: **BLOCKED/UNVERIFIABLE** - No hay API pública confirmada
- **Visores públicos**: `https://matbarofex.primary.ventures`, `https://cem.matbarofex.com.ar`
- **API**: `https://api.primary.ventures/` (no respondió en probe)
- **Índice CCL**: `https://matbarofex.com.ar/IndiceCCLMtR` (público, delay 20 min)
- **Documentación**: https://matbarofex.com.ar/
- **Validación**: Confirmado en `analysis/arg_market_access_validation.md` - solo visores scrapeables
- **Uso en MVP**: Solo índice CCL-MtR público; API diferida

### 4. FUENTES PÚBLICAS SIN CREDENCIALES

Estas fuentes no requieren ninguna credencial y son completamente abiertas:

#### Argentina
- **BCRA**: `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD` (USD oficial)
- **BCRA**: `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` (CER, TAMAR, tasas, reservas)
- **Tesoro**: `https://www.argentina.gob.ar/economia/licitaciones` (LECAP/LECER/BONCER)
- **BYMA Índice CCL**: `https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico` (público)
- **Matba Rofex CCL-MtR**: `https://matbarofex.com.ar/IndiceCCLMtR` (público, delay 20 min)
- **Rava**: `https://www.rava.com/` (bonos, riesgo país - scrapeable)
- **Ambito**: `https://www.ambito.com/` (riesgo país - scrapeable)

#### Estados Unidos
- **FOMC**: https://www.federalreserve.gov/monetarypolicy/fomc.htm (comunicados, proyecciones)
- **Treasury**: https://home.treasury.gov/ (deuda, yield curve, H.4.1)
- **NY Fed**: https://www.newyorkfed.org/ (reformas, sistema de pagos)

---

## Cómo Cargar las Credenciales

### Archivo `.env`

Crea un archivo `.env` en la raíz del repositorio con las credenciales deseadas:

```bash
# Credenciales opcionales para fuentes de EE.UU.
BLS_API_KEY=tu_bls_api_key_aqui
FRED_API_KEY=tu_fred_api_key_aqui
EIA_API_KEY=tu_eia_api_key_aqui
BEA_USER_ID=tu_bea_user_id_aqui
```

### Carga Automática

El archivo `.env` se carga automáticamente vía `src/finance_news/settings.py`:

```python
from finance_news.settings import load_env

# Carga .env desde la raíz del repo (o path especificado)
env_vars = load_env()  # No requiere override, respeta shell env
```

**Comportamiento:**
- Si `.env` no existe, retorna `{}` (sin error)
- Por defecto, NO sobrescribe variables ya definidas en `os.environ`
- Solo establece claves que no existen en el entorno del shell

### Validación de Carga

Para verificar que las credenciales están cargadas:

```python
import os

print(f"BLS_API_KEY: {bool(os.environ.get('BLS_API_KEY'))}")
print(f"FRED_API_KEY: {bool(os.environ.get('FRED_API_KEY'))}")
print(f"EIA_API_KEY: {bool(os.environ.get('EIA_API_KEY'))}")
print(f"BEA_USER_ID: {bool(os.environ.get('BEA_USER_ID'))}")
```

---

## Reglas de Seguridad

### 1. Nunca Commitear Secretos

- ❌ **Nunca** agregar `.env` al control de versiones
- ✅ El archivo `.env` debe estar en `.gitignore`
- ✅ Las claves deben vivir solo en el entorno local o en CI/CD secrets

### 2. No Hardcodear Claves en Conectores

- ❌ **Nunca** escribir claves directamente en código Python
- ✅ Leer credenciales desde `os.environ` (ej: `os.environ.get("BLS_API_KEY")`)
- ✅ Usar `None` como fallback para credenciales opcionales

### 3. Nunca Commitear Fixtures con Tokens

- ❌ **Nunca** incluir archivos JSON/CSV de prueba con claves reales
- ✅ Usar `FakeTransport` + hand-crafted fixtures en tests
- ✅ Reemplazar cualquier token real con `"test_key"` o similar

Ejemplo de fixture seguro:

```json
{
  "status": "REQUEST_SUCCEEDED",
  "Results": {
    "series": [
      {
        "seriesID": "CUSR0000SA0",
        "data": [
          {
            "year": "2026",
            "period": "M05",
            "value": "317.123"
          }
        ]
      }
    ]
  }
}
```

### 4. No Loggear Secrets

- ❌ **Nunca** imprimir claves en logs o stdout
- ✅ Redactar credenciales en logs de transporte HTTP
- ✅ Usar el sistema de redacción del conector cuando sea relevante

---

## Variables por Conector

| Conector | Variable de Entorno | Uso |
|----------|---------------------|-----|
| `bls_timeseries.py` | `BLS_API_KEY` | Parámetro `registrationkey` para evitar rate-limits |
| `fred_market_proxies.py` | `FRED_API_KEY` | Query parameter `api_key` para llamadas `fredgraph.csv` |
| `eia_wpsr.py` | `EIA_API_KEY` | Header/query parameter para datos de petróleo semanal |
| `bea_nipa.py` (pendiente) | `BEA_USER_ID` | Parámetro obligatorio `UserID` para datos BEA |
| `bcra_fx.py` | Ninguna | BCRA API pública, sin autenticación |
| `tesoro_licitaciones.py` | Ninguna | Tesoro público, sin autenticación |
| `fomc_statements.py` | Ninguna | FOMC público, sin autenticación |
| `treasury_h41.py` | Ninguna | Treasury público, sin autenticación |
| `ny_fed_reforms.py` | Ninguna | NY Fed público, sin autenticación |

---

## Resumen de Validación

### AC #1: Tabla de Variables de Entorno ✅
- Documentado: BLS_API_KEY, FRED_API_KEY, EIA_API_KEY, BEA_USER_ID
- Incluye: obligatoriedad, fuentes que las usan, cómo obtenerlas
- Cubre: conectores existentes (BLS, FRED, EIA) y pendientes (BEA)

### AC #2: Categorización de Credenciales ✅
- **Opcionales**: BLS, FRED, EIA, BEA - libre registro, funcionan sin claves pero rate-limited
- **Obligatorias**: Ninguna actualmente - todos los conectores trabajan offline/sin claves
- **Pendientes Validación**: BYMA, MAE, Matba Rofex - pago/bloqueadas, requieren suscripción

### AC #3: Reglas de Seguridad ✅
- `.env` es el único lugar para secretos (gitignored)
- Conectores leen desde `os.environ`, nunca hardcodean
- Nunca commitear `.env`
- Fixtures NO contienen tokens reales (usar FakeTransport + fixtures crafteds)
- Conectores no loggearán secretos (redacción implementada)

---

## Referencias

- **Loader**: `src/finance_news/settings.py` - `load_env()` function
- **Investigación US Macro**: `analysis/source_research_us_macro.md`
- **Investigación Argentina Mercado**: `analysis/source_research_arg_market.md`
- **Validación Argentina Acceso**: `analysis/arg_market_access_validation.md`
- **Validación BEA Schema**: `analysis/bea_nipa_schema_validation.md`

---

**Última actualización**: 2026-06-21