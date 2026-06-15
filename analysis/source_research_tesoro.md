# Investigacion de fuentes del Tesoro argentino y deuda

Fecha de relevamiento: 2026-06-15

## Resumen ejecutivo

- El nucleo oficial para Tesoro/deuda esta en Finanzas/Ministerio de Economia:
  - Licitaciones, cronogramas, resultados y colocaciones: `https://www.argentina.gob.ar/economia/licitaciones`
  - Datos de deuda publica: `https://www.argentina.gob.ar/economia/finanzas/datos`
  - Deuda publica: `https://www.argentina.gob.ar/economia/finanzas/deuda-publica`
  - Informe de deuda publica en pesos: `https://www.argentina.gob.ar/economia/finanzas/informe-de-deuda-publica-en-pesos`
- No encontre una API oficial unica para licitaciones del Tesoro, resultados primarios, rollover y vencimientos. La automatizacion debe combinar scraping de HTML/noticias, descarga de archivos oficiales y parsing de planillas/PDF.
- La mejor superficie machine-readable para caja fiscal y resultado primario/financiero es la API de series de datos.gob.ar, especialmente datasets de Secretaria de Hacienda y Programacion Macroeconomica.
- La mejor superficie machine-readable para cuenta/caja del Tesoro observada desde el sistema financiero/BCRA es la API monetaria del BCRA, usando "depositos del gobierno en el BCRA" y "depositos del sector publico" como proxy operativo. No reemplaza una Cuenta Unica del Tesoro detallada por jurisdiccion.
- La fuente oficial independiente mas util para contraste y vencimientos agregados es OPC: `https://opc.gob.ar/operaciones-de-deuda-publica/` y `https://opc.gob.ar/seguimiento-de-la-deuda-publica/`.
- Fuentes no oficiales solo son necesarias para precio de mercado y stress soberano cuando no haya licencia de proveedor: BYMA/MAE/A3 para precios primarios de mercado; Rava/Ambito solo como fallback secundario de riesgo pais, marcado como no licenciado.

## Clasificacion rapida

| Bloque | Fuente recomendada | Estado | Ingesta |
| --- | --- | --- | --- |
| Llamados de licitacion | Argentina.gob.ar noticias + landing licitaciones | oficial | scraping HTML/manual |
| Resultados de licitacion | Argentina.gob.ar noticias + historico + colocaciones | oficial | scraping HTML + descarga archivos |
| Rollover primario | calcular con resultados oficiales y vencimientos | derivado | pipeline propio |
| Calendario de vencimientos | estructura financiera de titulos + datos mensuales/trimestrales + OPC | oficial/organismo | XLS/PDF scraping/manual |
| Caja/cuenta Tesoro | BCRA API monetaria + datos.gob.ar base caja | oficial | JSON/CSV |
| Deuda en moneda extranjera | datos mensuales/trimestrales de deuda + OPC | oficial/organismo | XLS/PDF |
| Resultado fiscal | datos.gob.ar series IMIG/base caja + publicaciones Hacienda | oficial | JSON/CSV + manual |
| Precio/stress de deuda | BYMA/MAE/A3; Rava/Ambito como fallback | mercado/no oficial | API/credenciales/scraping |

## 1. Licitaciones del Tesoro

### 1.1 Hub oficial de licitaciones

Fuente:
- `https://www.argentina.gob.ar/economia/licitaciones`

Cobertura:
- Cronograma de llamados y licitaciones.
- Resultados de licitaciones.
- Colocaciones de deuda por ano.
- Suscripcion por correo a llamados/resultados.

Evidencia verificada:
- La pagina indica que para cada licitacion se publica "el cronograma con los proximos llamados y los resultados" y que las colocaciones muestran las operaciones por ano.
- Links internos verificados:
  - Cronograma 2026: `https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro/cronograma-2026`
  - Historico de resultados: `https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro/historico-de-resultados`
  - Colocaciones: `https://www.argentina.gob.ar/economia/finanzas/deudapublica/colocacionesdedeuda`

Formato:
- HTML de navegacion.
- Descargas oficiales por cronograma y colocaciones; la extension puede variar por publicacion, por lo que el conector debe descubrir el link final.
- Noticias HTML para llamados/resultados recientes.

Frecuencia:
- Por evento de licitacion.
- Cronograma anual, actualizado cuando Finanzas modifica fechas.
- Colocaciones: acumulado anual con cortes periodicos.

Confiabilidad:
- Alta para dato oficial primario.
- Media para automatizacion, porque no hay API estable publicada y varios enlaces "Descargar" se resuelven desde el CMS.

Ingesta:
- `scraping` para HTML/noticias/listados.
- `machine-readable` si el enlace final es XLS/XLSX/CSV.
- `manual` si el enlace final es PDF o tabla HTML irregular.

Conector sugerido:
- `tesoro_licitaciones_index`
  - Poll diario del hub y de Finanzas noticias.
  - Extraer URLs con patrones `llamado-licitacion`, `resultado-de-la-licitacion`, `segunda-vuelta`, `conversion`.
  - Guardar HTML crudo, fecha de publicacion, titulo, instrumentos, moneda, VNO/VE ofertado, VNO/VE adjudicado, precio de corte, TNA/TIREA y nuevo VNO en circulacion.

### 1.2 Noticias oficiales de llamados y resultados

Fuentes recientes verificadas:
- Resultado segunda vuelta BONAR 2028: `https://www.argentina.gob.ar/noticias/resultado-de-la-segunda-vuelta-de-la-licitacion-de-bonar-2028-en-dolares-estadounidenses`
- Resultado licitacion pesos, dolar linked, dolares y conversion TZX26/TTJ26: `https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-4`
- Llamado a licitacion pesos/dolares y conversion: `https://www.argentina.gob.ar/noticias/llamado-licitacion-de-instrumentos-del-tesoro-nacional-denominados-en-pesos-y-en-dolares-5`

Cobertura:
- Llamados: instrumentos ofrecidos, condiciones, fechas, integracion, segunda vuelta cuando aplica.
- Resultados: ofertas recibidas, montos ofertados/adjudicados, precios de corte, TNA/TIREA, prorrateo, conversiones/canjes, instrucciones operativas CRYL cuando aplica.

Formato:
- HTML con tablas renderizadas como texto.

Frecuencia:
- Por licitacion, usualmente el dia del llamado y el dia del resultado.

Confiabilidad:
- Alta como comunicacion oficial de Secretaria de Finanzas.
- Riesgo de parsing medio por tablas HTML no normalizadas.

Ingesta:
- `scraping`.

Conector sugerido:
- `tesoro_news_scraper`
  - Buscar en `https://www.argentina.gob.ar/economia/finanzas` y en `/noticias/` por titulos con `licitacion`, `resultado`, `conversion`, `canje`, `BONAR`, `BONCER`, `LECAP`, `dolar linked`.
  - Parser flexible por bloques: resumen total, tabla por moneda, tabla por instrumento, notas.
  - Versionar el esquema por publicacion porque las licitaciones mixtas cambian columnas.

### 1.3 Historico y colocaciones

Fuentes:
- Historico de resultados: `https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro/historico-de-resultados`
- Colocaciones de deuda: `https://www.argentina.gob.ar/economia/finanzas/deudapublica/colocacionesdedeuda`

Cobertura:
- Historico de llamados/resultados desde 2017 en adelante, organizado por ano hasta 2024 inclusive en la pagina verificada.
- Colocaciones compila resultados de licitaciones, estructura financiera de instrumentos, canjes/conversiones y suscripciones directas por ano.

Formato:
- HTML + descargas por ano.
- Los archivos deben inspeccionarse por ano; pueden ser XLS/XLSX/PDF segun publicacion.

Frecuencia:
- Historico: archivo estable, baja frecuencia.
- Colocaciones: anual con actualizaciones durante el ano corriente.

Confiabilidad:
- Alta para backfill oficial.

Ingesta:
- `machine-readable` cuando el archivo sea XLS/XLSX/CSV.
- `manual` o `scraping` cuando el archivo sea PDF.

Conector sugerido:
- `tesoro_colocaciones_backfill`
  - Resolver links de descarga por ano.
  - Fingerprint de archivo por fecha/hash.
  - Normalizar por operacion: fecha, instrumento, tipo de operacion, moneda, VNO, VE, precio, tasa, nuevo circulante.

## 2. Rollover, vencimientos y calendario de pagos

### 2.1 Calculo de rollover

No encontre una serie oficial unica "rollover" por licitacion. Debe calcularse.

Insumos recomendados:
- Resultados de licitacion oficiales: adjudicado por moneda/instrumento.
- Vencimientos inmediatos:
  - Estructura financiera de titulos publicos: `https://www.argentina.gob.ar/economia/finanzas/estructura-financiera-de-titulos-publicos`
  - Datos mensuales de deuda: `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales`
  - Datos trimestrales de deuda: `https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda`
  - OPC operaciones de deuda publica: `https://opc.gob.ar/operaciones-de-deuda-publica/`

Formula operativa:
- `rollover_bruto = valor_efectivo_adjudicado / vencimientos_elegibles_del_periodo`
- Calcular separado por:
  - moneda: ARS, USD, dolar linked, dual/CER/TAMAR
  - mercado: efectivo, conversion/canje, segunda vuelta
  - inclusion/exclusion de intra-sector publico si la fuente lo permite

Frecuencia:
- Por licitacion y cierre semanal/mensual.

Ingesta:
- `derived` desde fuentes oficiales.

Conector sugerido:
- `tesoro_rollover_calculator`
  - Une `tesoro_news_scraper` + `deuda_cashflows`.
  - Guarda metodologia explicita: fechas de vencimiento incluidas, moneda, tratamiento de canjes, tipo de cambio si corresponde.

### 2.2 Estructura financiera de titulos publicos

Fuente:
- `https://www.argentina.gob.ar/economia/finanzas/estructura-financiera-de-titulos-publicos`

Cobertura:
- Detalle de bonos y letras vigentes emitidos por el Estado Nacional.
- Cupones de renta y amortizacion de titulos publicos nacionales corrientes e historicos.
- Coeficientes de pago de prestamos garantizados.

Formato:
- Descargas oficiales desde la pagina; el conector debe resolver los links finales.

Frecuencia:
- Eventual, ante nuevos instrumentos, reaperturas, canjes o actualizaciones de cashflows.

Confiabilidad:
- Alta para cashflows oficiales y calendario de vencimientos por instrumento.

Ingesta:
- `machine-readable` si descarga en XLS/XLSX/CSV.
- `manual` si PDF o estructura no tabular.
- `scraping` para descubrir links.

Conector sugerido:
- `deuda_cashflows`
  - Descargar "Estructura financiera" y "Cupones Titulos Publicos Nacionales".
  - Normalizar ISIN/especie/ticker, fecha emision, vencimiento, moneda, indice, tasa/cupon, amortizaciones y renta.
  - Generar calendario semanal/mensual de vencimientos de capital e intereses.

### 2.3 Datos mensuales y trimestrales de deuda

Fuentes:
- Datos mensuales de la deuda: `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda`
- Serie mensual: `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales`
- Informes mensuales: `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda/informes-mensuales`
- Datos trimestrales: `https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda`

Cobertura:
- Deuda publica bruta: nivel, composicion, flujos, variaciones e indicadores.
- Serie mensual 2019-ultimo dato disponible en la pagina verificada.
- Bases trimestrales por acreedor/residencia, moneda, legislacion y otros indicadores.
- Informes ejecutivos mensuales en PDF.

Formato:
- Serie mensual descargable.
- Bases trimestrales en Excel.
- Informes PDF.

Frecuencia:
- Mensual y trimestral.

Confiabilidad:
- Alta para stock y composicion oficial.
- Para lectura semanal, puede estar rezagada frente a licitaciones recientes.

Ingesta:
- `machine-readable` para Excel/CSV.
- `manual` para PDF si se requiere narrativa.
- `scraping` para descubrir el ultimo archivo disponible.

Conector sugerido:
- `deuda_monthly_stock`
  - Poll semanal de pagina de datos mensuales.
  - Descargar serie mensual e informe nuevo.
  - Extraer stock total, moneda, acreedor, legislacion, vida promedio/duration si figura.
- `deuda_quarterly_stock`
  - Batch trimestral para bases Excel.

### 2.4 OPC como fuente oficial independiente de vencimientos y deuda

Fuentes:
- Operaciones de deuda publica: `https://opc.gob.ar/operaciones-de-deuda-publica/`
- Ejemplo verificado abril 2026: `https://opc.gob.ar/operaciones-de-deuda-publica/operaciones-de-deuda-publica-abril-2026/`
- Seguimiento de deuda publica: `https://opc.gob.ar/seguimiento-de-la-deuda-publica/`

Cobertura:
- Operaciones mensuales de deuda.
- Deuda en pesos y moneda extranjera.
- Canjes adicionales, rescates y vencimientos estimados.
- Monitores: novedades normativas, deuda flotante, indicadores de deuda.

Formato:
- HTML de resumen.
- PDF descargable por publicacion.
- Algunas herramientas interactivas pueden estar temporalmente fuera de servicio, segun aviso de OPC.

Frecuencia:
- Mensual/eventual.

Confiabilidad:
- Alta como organismo tecnico del Congreso.
- No reemplaza la fuente primaria de Secretaria de Finanzas para licitaciones, pero es excelente contraste.

Ingesta:
- `scraping` para resumen HTML.
- `manual` o parser PDF para reportes.

Conector sugerido:
- `opc_deuda_monitor`
  - Poll mensual.
  - Extraer vencimientos estimados, stock por moneda, resumen de canjes y comentarios metodologicos.
  - Usar como reconciliacion contra Ministerio de Economia.

## 3. Cuenta, caja y posicion del Tesoro

### 3.1 BCRA API monetaria: depositos del gobierno y sector publico

Fuentes:
- API hub BCRA: `https://www.bcra.gob.ar/apis-banco-central/`
- Catalogo monetario: `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias`
- Serie por variable: `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{idVariable}?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`

Variables BCRA utiles verificadas:
- `1264` - Depositos del gobierno en el BCRA.
- `1265` - Depositos del gobierno en el BCRA en pesos.
- `1266` - Depositos del gobierno en el BCRA en moneda extranjera.
- `1268` - Adelantos transitorios del BCRA al gobierno nacional.
- `1225` - Adelantos transitorios del BCRA al Gobierno Nacional, categoria Informe Monetario Diario.
- `1229` - Depositos del sector publico.
- `1230` - Depositos a la vista del sector publico.
- `1231` - Depositos a plazo del sector publico.
- `1455` - Depositos totales del sector publico.
- `1457` - Cuentas corrientes del sector publico no financiero.
- `1463` - Plazo fijo del sector publico no financiero.
- `1487` - Utilizacion de fondos unificados (FUCO) del sector publico no financiero.
- `1497` - Cuentas a la vista del sector publico no financiero en moneda extranjera.
- `1499` - Cajas de ahorro del sector publico no financiero en moneda extranjera.
- `1501` - Plazo fijo del sector publico no financiero en moneda extranjera.

Cobertura:
- Posicion de depositos del gobierno en BCRA.
- Depositos del sector publico en el sistema financiero.
- Proxies de caja liquida y fondos inmovilizados/plazo.
- No identifica por si sola la Cuenta Unica del Tesoro con detalle presupuestario.

Formato:
- JSON.

Frecuencia:
- Diaria habil para la mayoria de estas variables.

Confiabilidad:
- Alta para series BCRA.
- Media para interpretar "caja del Tesoro" porque incluye agregados de gobierno/sector publico que pueden diferir de la CUT del Tesoro Nacional.

Ingesta:
- `machine-readable`.

Conector sugerido:
- `bcra_tesoro_cash_proxy`
  - Pull diario de IDs 1264, 1265, 1266, 1229, 1230, 1231, 1455, 1457, 1463, 1487.
  - Calcular variacion semanal de caja en BCRA y depositos del sector publico.
  - Mostrar advertencia metodologica: proxy, no CUT detallada.

### 3.2 Series fiscales de datos.gob.ar: base caja e IMIG

Fuentes:
- Busqueda de series: `https://apis.datos.gob.ar/series/api/search/?q=resultado%20primario`
- Consulta de serie: `https://apis.datos.gob.ar/series/api/series/?ids=452.3_RESULTADO_RIO_0_M_18_54&limit=3&format=json`
- CSV IMIG mensual indicado por metadata: `https://infra.datos.gob.ar/catalog/sspm/dataset/452/distribution/452.3/download/imig-mensual.csv`

Series verificadas:
- `452.3_RESULTADO_RIO_0_M_18_54` - IMIG. Resultado primario, mensual.
- `452.2_RESULTADO_RIO_0_T_18_21` - IMIG. Resultado primario, trimestral.
- `378.9_RESULTADO_017_0_M_18_90` - Resultado financiero metodologia 2017, EEPP/PAMI/fondos fiduciarios/otros, mensual.
- `379.9_RESULTADO_017__18_38` - Resultado financiero metodologia 2017, Sector Publico Nacional base caja, mensual.
- `373.9_RESULTADO_017__18_45` - Resultado financiero metodologia 2017, Tesoro Nacional base caja, mensual.

Cobertura:
- Resultado primario y financiero.
- Ingresos/gastos del SPNF y Tesoro Nacional base caja en datasets asociados.
- Sirve para evaluar consistencia fiscal y caja, no para vencimientos diarios.

Formato:
- JSON API de series.
- CSV descargable.

Frecuencia:
- Mensual/trimestral/anual segun campo.

Confiabilidad:
- Alta para series oficiales publicadas por Secretaria de Hacienda/Ministerio de Economia.

Ingesta:
- `machine-readable`.

Conector sugerido:
- `mecon_fiscal_series`
  - Usar API de series para resultado primario/financiero.
  - Descargar CSV completo para backfill y control de cambios.
  - Mantener lista de IDs versionada porque los datasets tienen series por metodologia.

### 3.3 Gaps sobre Cuenta Unica del Tesoro

Gap:
- No encontre una API publica estable y actual de la Cuenta Unica del Tesoro con saldos diarios por cuenta/jurisdiccion.

Mitigacion:
- Usar BCRA depositos del gobierno/sector publico como proxy diario.
- Usar series de Hacienda base caja como cierre mensual.
- Marcar en reporte: "caja Tesoro proxy BCRA" vs "resultado fiscal base caja Hacienda".

## 4. Deuda en moneda extranjera

### 4.1 Datos oficiales de deuda

Fuentes:
- Deuda publica: `https://www.argentina.gob.ar/economia/finanzas/deuda-publica`
- Datos: `https://www.argentina.gob.ar/economia/finanzas/datos`
- Datos mensuales: `https://www.argentina.gob.ar/economia/finanzas/datos-mensuales`
- Datos trimestrales: `https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda`
- Estructura financiera de titulos: `https://www.argentina.gob.ar/economia/finanzas/estructura-financiera-de-titulos-publicos`

Cobertura:
- Stock de deuda bruta total.
- Deuda por moneda, acreedor/residencia, legislacion.
- Titulos vigentes, cupones y amortizaciones.
- Base mensual/trimestral e informes ejecutivos.

Formato:
- Excel/CSV/PDF segun pagina y periodo.

Frecuencia:
- Mensual/trimestral para stock.
- Eventual para estructura financiera.

Confiabilidad:
- Alta.

Ingesta:
- `machine-readable` para bases Excel/CSV.
- `manual` o parser PDF para informes.
- `scraping` para descubrir links nuevos.

Conector sugerido:
- `deuda_fx_stock_and_service`
  - Combinar base mensual/trimestral con cashflows de estructura financiera.
  - Separar deuda pagadera en moneda extranjera, deuda dollar-linked y deuda local indexada.
  - Reconciliar contra OPC.

### 4.2 OPC deuda en moneda extranjera y vencimientos

Fuente:
- `https://opc.gob.ar/operaciones-de-deuda-publica/`

Uso recomendado:
- Contraste mensual de stock y vencimientos en moneda extranjera.
- Identificar meses con concentracion de pagos y canjes defensivos.

Ingesta:
- `scraping` HTML para resumen.
- `manual` o parser PDF para detalle.

## 5. Reportes fiscales y presupuesto

### 5.1 datos.gob.ar / Programacion Macroeconomica

Fuentes:
- `https://apis.datos.gob.ar/series/api/search/?q=resultado%20primario`
- `https://apis.datos.gob.ar/series/api/search/?q=resultado%20financiero`
- `https://apis.datos.gob.ar/series/api/series/?ids=452.3_RESULTADO_RIO_0_M_18_54&format=json`

Cobertura:
- Informe Mensual de Ingresos y Gastos del Sector Publico Nacional No Financiero (IMIG).
- Esquema Ahorro-Inversion-Financiamiento base caja.
- Resultado primario/financiero y componentes de ingresos/gastos segun dataset.

Formato:
- JSON API.
- CSV en `infra.datos.gob.ar`.

Frecuencia:
- Mensual, trimestral y anual segun serie.

Confiabilidad:
- Alta.

Ingesta:
- `machine-readable`.

### 5.2 OPC ejecucion presupuestaria

Fuente:
- `https://opc.gob.ar/ejecucion-presupuestaria-2/`

Cobertura:
- Ejecucion mensual base devengado.
- Modificaciones presupuestarias.
- Subsidios, transferencias, inversion publica y otros informes.

Formato:
- HTML + PDF.

Frecuencia:
- Mensual/eventual.

Confiabilidad:
- Alta como fuente tecnica de contraste, no primaria de caja.

Ingesta:
- `manual`/`scraping`.

Conector sugerido:
- `opc_budget_monitor`
  - Poll mensual para alertas de gasto devengado y deuda flotante.
  - No mezclar devengado OPC con base caja Hacienda sin etiqueta metodologica.

## 6. Fuentes de mercado y no oficiales necesarias

Estas fuentes no deben reemplazar datos oficiales de Tesoro. Sirven para precio de validacion: si una licitacion "sale bien" pero la curva secundaria, bonos hard dollar o riesgo pais empeoran, el reporte debe reflejar la contradiccion.

### 6.1 Mercado primario/secundario institucional

Fuentes:
- BYMA Market Data APIs: `https://www.byma.com.ar/productos/productos-de-datos/market-data/apis`
- MAE Market Data: `https://marketdata.mae.com.ar/`
- MAE APIs: `https://www.mae.com.ar/APIsMAE`
- A3/Matba Rofex datos: `https://a3mercados.com.ar/mercado/datos-de-mercado/`

Cobertura:
- Bonos hard dollar.
- Letras/bonos en pesos.
- Curvas secundarias.
- Futuros y dolares financieros segun acceso.

Formato:
- API con credenciales/suscripcion o web app scrapeable.

Frecuencia:
- Diaria/intradiaria.

Confiabilidad:
- Alta si hay feed/API contratado o acceso EOD oficial de mercado.
- Media si se scrapea web.

Ingesta:
- `machine-readable` con API/credenciales.
- `scraping` si solo visor web.

### 6.2 Riesgo pais sin licencia

Fuentes secundarias:
- Rava: `https://www.rava.com/perfil/RIESGO%20PAIS`
- Ambito: `https://www.ambito.com/contenidos/riesgo-pais.html`

Cobertura:
- Riesgo pais Argentina reportado por medio/plataforma.

Formato:
- HTML.

Frecuencia:
- Diaria/intradiaria.

Confiabilidad:
- Media. No es el proveedor licenciado original.

Ingesta:
- `scraping`.

Regla:
- Etiquetar como "fuente secundaria, no EMBI licenciado".
- Si se calcula proxy propio, llamarlo `sovereign_spread_proxy`, nunca `EMBI oficial`.

## 7. Arquitectura de conectores sugerida

Orden recomendado para MVP:

1. `tesoro_news_scraper`
   - Llamados/resultados oficiales de licitaciones.
   - Output: eventos normalizados por instrumento.

2. `deuda_cashflows`
   - Estructura financiera y cupones.
   - Output: calendario de vencimientos por instrumento, moneda y tipo de flujo.

3. `tesoro_rollover_calculator`
   - Combina resultados + vencimientos.
   - Output: rollover por licitacion/semana/mes, con metodologia.

4. `bcra_tesoro_cash_proxy`
   - Depositos del gobierno/sector publico y FUCO desde BCRA.
   - Output: proxy diario de caja/cuenta.

5. `mecon_fiscal_series`
   - Resultado primario/financiero y componentes fiscales desde datos.gob.ar.
   - Output: cierre mensual fiscal, base caja.

6. `deuda_monthly_stock`
   - Stock y composicion oficial de deuda.
   - Output: deuda por moneda, acreedor, legislacion, variacion mensual.

7. `opc_deuda_monitor`
   - Contraste de vencimientos y deuda.
   - Output: alertas, reconciliacion y gaps.

8. `market_debt_prices`
   - BYMA/MAE/A3 o fallback Rava/Ambito.
   - Output: precios secundarios, hard dollar, riesgo/spread proxy.

## 8. Reglas de calidad para el agente semanal

- Separar siempre:
  - dato oficial de licitacion
  - calculo derivado de rollover
  - proxy de caja
  - precio de mercado
- Guardar `source_url`, `published_at`, `retrieved_at`, `raw_hash`, `parser_version` y `methodology_note`.
- No comparar rollover en ARS contra vencimientos en USD sin explicitar tipo de cambio y universo.
- No mezclar canjes/conversiones con efectivo sin doble conteo claro.
- Para cuenta/caja, escribir "proxy BCRA" cuando se use depositos del gobierno/sector publico.
- Para fiscal, escribir "base caja" o "devengado" segun fuente.
- Para riesgo pais, distinguir JPM/licenciado, fuente secundaria y proxy propio.

## 9. Gaps no bloqueantes

- No encontre API oficial de Secretaria de Finanzas para licitaciones/resultados.
- No encontre endpoint publico estable de Cuenta Unica del Tesoro con saldo diario desagregado.
- Los enlaces "Descargar" de Argentina.gob.ar deben resolverse por crawler; el HTML publico no siempre expone extension/URL en la vista textual.
- Para curva secundaria confiable se necesita acceso BYMA/MAE/A3. Sin credenciales, el MVP debe usar scraping/fallback marcado con menor confianza.
- El historico de resultados en la pagina verificada llega hasta 2024 inclusive; para 2025/2026 conviene usar noticias recientes y colocaciones de deuda anual.
