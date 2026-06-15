# Investigacion de fuentes de mercado local Argentina

Fecha de relevamiento: 2026-06-14

## Resumen ejecutivo

- No hay una unica fuente oficial gratuita que cubra todo el set local. El nucleo sin pago debe combinar BCRA, Tesoro, CAFCI y fuentes de mercado con acceso gratuito o scrapeable.
- Para dolar oficial, CER y TAMAR, la fuente primaria debe ser BCRA. Es oficial, gratuita y mayormente machine-readable.
- Para MEP/CCL, futuros, curva de pesos y bonos hard dollar, la fuente mas confiable es la infraestructura de mercado: BYMA, A3/Matba Rofex y MAE. Parte del acceso es gratis con alta de API o visor web; tiempo real y baja latencia son pagos o con credenciales.
- Riesgo pais EMBI Argentina es un dato propietario de J.P. Morgan. Sin licencia, usar Rava/Ambito como fuente secundaria scrapeable o construir un proxy propio de spread soberano, siempre marcado como "no EMBI oficial".
- Minimo viable semanal sin datos pagos: BCRA oficial + Tesoro + BYMA/A3 EOD o visores + CAFCI + Rava/Ambito para riesgo pais como proxy secundario.

## Clasificacion de fuentes

### Gratis / oficiales o de mercado primario

| Fuente | URL | Cobertura | Formato | Frecuencia | Costo | Confiabilidad | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BCRA API | https://www.bcra.gob.ar/apis-banco-central/ | estadisticas cambiarias, monetarias, tasas y series oficiales | JSON | diaria / mensual | gratis | alta | Base para dolar oficial, A3500, TAMAR, CER y tasas. |
| BCRA estadisticas cambiarias | https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD | cotizacion USD oficial y monedas | JSON | diaria habil | gratis | alta | Usar con parametros `fechadesde`, `fechahasta`, `limit`, `offset` cuando aplique. |
| BCRA estadisticas monetarias | https://api.bcra.gob.ar/estadisticas/v4.0/monetarias | catalogo de variables monetarias, tasas y reservas | JSON | mixta | gratis | alta | Descubrir IDs de variables y consultar series por `idVariable`. |
| BCRA tasas de interes | https://www.bcra.gob.ar/tasas-de-interes/ | TAMAR, BADLAR, TM20, BAIBAR, CER, UVA, UVI | XLS/XLSX desde pagina | diaria / mensual | gratis | alta | Fuente oficial para TAMAR y CER cuando no convenga resolver IDs de API. |
| Tesoro licitaciones | https://www.argentina.gob.ar/economia/licitaciones | llamados, cronogramas, resultados y colocaciones | HTML/PDF/XLS segun publicacion | por licitacion | gratis | alta | Base para LECAP/LECER/BONCER primario, tasas de corte y rollover. |
| Tesoro deuda en pesos | https://www.argentina.gob.ar/economia/finanzas/informe-de-deuda-publica-en-pesos | informes mensuales de deuda en moneda local | PDF/XLS segun archivo | mensual | gratis | alta | Complementa stock, composicion y estrategia. |
| BYMA APIs Market Data | https://www.byma.com.ar/productos/productos-de-datos/market-data/apis | renta fija, futuros, indices, EOD, instrumentos | API con suscripcion | intradiaria / EOD | EOD e indices sin costo; delay/real-time pago | alta | EOD permite 1.000 solicitudes/mes sin costo; delay USD 100/mes; snapshot real-time USD 400/mes segun pagina. |
| BYMA Indice CCL | https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico | indice CCL BYMA | pagina/API indices | intradiaria / historica | sin costo segun plan indices | media-alta | Bueno para CCL de mercado con metodologia BYMA; validar acceso API. |
| BYMA Indice Dolar | https://www.byma.com.ar/productos/productos-de-datos/indice-dolar-byma-historico | indice dolar BYMA | pagina/API indices | intradiaria / historica | sin costo segun plan indices | media-alta | Util como complemento al oficial, no reemplaza BCRA. |
| A3 datos de mercado | https://a3mercados.com.ar/mercado/datos-de-mercado/ | links a MAE, Matba Rofex, CEM, informes y visores | HTML / dashboards | diaria / semanal / mensual | gratis en visores; APIs con credenciales | media-alta | Hub operativo para descubrir productos y publicaciones. |
| CAFCI | https://www.cafci.org.ar/ | planilla diaria y resumen mensual de FCIs | descarga diaria / informes | diaria / mensual | gratis | media-alta | Util para flujos y posicionamiento de fondos T+0, CER, money market; no es curva de mercado directa. |

### Fuentes scrapeables gratuitas

| Fuente | URL | Cobertura | Formato | Frecuencia | Costo | Confiabilidad | Uso recomendado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MAE Market Data | https://marketdata.mae.com.ar/ | renta fija, forex, repo, boletin, informe diario | web app | diaria / intradiaria | gratis en web | media | Scraping liviano de cierre/boletin si no hay API; validar cambios de frontend. |
| MAE boletin diario | https://marketdata.mae.com.ar/boletindiario | boletin diario MAE | web app / descarga si disponible | diaria | gratis | media | Respaldo para renta fija y operaciones MAE. |
| MAE informe diario | https://marketdata.mae.com.ar/informediario | informe diario MAE | web app / descarga si disponible | diaria | gratis | media | Respaldo manual o scraping controlado. |
| A3/Matba Rofex visor | https://matbarofex.primary.ventures | precios de futuros y opciones | web app | intradiaria | gratis | media | Usar para dolar futuro y CER si no hay API; riesgo de cambios de DOM. |
| Matba Rofex CEM | https://cem.matbarofex.com.ar/ | centro de estadisticas de mercado | web app | diaria | gratis | media | Requiere JS; mejor como fuente visual/manual hasta probar endpoints. |
| Matba Rofex Indice CCL-MtR | https://matbarofex.com.ar/IndiceCCLMtR | CCL-MtR con consultas diarias y delay | HTML | intradiaria / cierre | gratis | media-alta | Buen CCL alternativo; metodologia explicita con delay de 20 minutos. |
| Rava riesgo pais | https://www.rava.com/perfil/RIESGO%20PAIS | riesgo pais Argentina y serie historica visible | HTML | diaria / intradiaria | gratis | media | Dato secundario; no usar como EMBI oficial licenciado. |
| Ambito riesgo pais | https://www.ambito.com/contenidos/riesgo-pais.html | riesgo pais argentino atribuido a EMBI/JPM | HTML | diaria / intradiaria | gratis / sitio comercial | media | Fuente de contraste y fallback, no fuente primaria. |
| BYMADATA abierto | https://open.bymadata.com.ar/ | avisos, hechos relevantes, informacion visible al inversor | web | diaria / eventual | gratis | media | Util para metadata, avisos y chequeos, no para toda serie historica de precios. |

### Fuentes pagas, con credenciales o manuales

| Fuente | URL | Cobertura | Costo / restriccion | Confiabilidad | Uso recomendado |
| --- | --- | --- | --- | --- | --- |
| BYMA Snapshot / Delay | https://www.byma.com.ar/productos/productos-de-datos/market-data/apis | cotizaciones BYMA real-time o delay | Snapshot USD 400/mes; Delay USD 100/mes segun BYMA | alta | Produccion si se necesita latencia o volumen mayor que EOD gratis. |
| MAE APIs Market Data | https://www.mae.com.ar/APIsMAE | titulos, indices, resumen final de renta fija | requiere formulario y credenciales; precio no publicado | alta | Alternativa institucional para precios de cierre de renta fija y A3500/CER/UVA segun catalogo. |
| MAE TRD / Back Office APIs | https://www.mae.com.ar/APIsMAE | operaciones, cauciones, comitentes, auditoria de ofertas | exclusivo agentes MAE | alta | No aplica al MVP salvo que el usuario tenga acceso de agente. |
| Bloomberg / Refinitiv / FactSet | sitios comerciales | bonos hard dollar, curvas, riesgo pais, precios globales | pago | alta | Ideal para cobertura robusta; fuera del MVP sin datos pagos. |
| J.P. Morgan EMBI | proveedor JPM | EMBI/EMBIG Argentina oficial | pago/licencia | alta | Riesgo pais oficial. Sin licencia, usar proxy o fuentes secundarias claramente marcadas. |
| Reportes de brokers/ALyCs | sitios o mails privados | curvas CER/TAMAR/LECAP, MEP/CCL, bonos | manual / registro / pago | media-alta | Contexto cualitativo; no automatizar sin permiso y trazabilidad. |

## Opciones por serie

### 1. Dolar oficial

Opcion recomendada:
- BCRA Estadisticas Cambiarias USD: `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD`
- Formato: JSON.
- Frecuencia: diaria habil.
- Costo/confiabilidad: gratis, oficial, alta.

Alternativas:
- BCRA API hub y manuales: https://www.bcra.gob.ar/apis-banco-central/
- MAE FOREX desde A3/MAE: https://a3mercados.com.ar/mercado/datos-de-mercado/ y https://marketdata.mae.com.ar/
- BYMA Indice Dolar: https://www.byma.com.ar/productos/productos-de-datos/indice-dolar-byma-historico

Decision operativa:
- Usar BCRA para el oficial del reporte.
- Usar MAE/BYMA solo como contraste de mercado o si se necesita precio operado/indice no oficial.

### 2. Dolar MEP y CCL

Opcion recomendada sin pago:
- BYMA API EOD gratis para precios de bonos y especies en pesos/dolares, si se obtiene suscripcion sin costo: https://www.byma.com.ar/productos/productos-de-datos/market-data/apis
- Calcular MEP/CCL por paridad de especies liquidas: por ejemplo AL30/AL30D, GD30/GD30D, AL30C/GD30C cuando esten disponibles.
- Complementar con indice CCL BYMA: https://www.byma.com.ar/productos/productos-de-datos/indice-ccl-byma-historico
- Complementar con Indice CCL-MtR: https://matbarofex.com.ar/IndiceCCLMtR

Scrapeable:
- Rava dolares/bonos y calculos implicitos desde precios visibles: https://www.rava.com/
- Ambito dolar MEP/CCL como dato periodistico: https://www.ambito.com/contenidos/dolar.html

Costo/confiabilidad:
- BYMA/A3 indices: gratis o plan gratuito con alta, confiabilidad media-alta/alta segun acceso.
- Calculo propio con EOD: gratis con limite, confiabilidad media-alta si se documenta especie, plaza y horario.
- Scraping de medios: gratis, confiabilidad media/baja para automatizacion.

Decision operativa:
- Publicar MEP/CCL como "calculado con especie X al cierre" o "indice BYMA/A3" para no mezclar metodologias.
- No mezclar blue con MEP/CCL salvo contexto.

### 3. Futuros de dolar y futuros CER

Opcion recomendada:
- A3/Matba Rofex productos de dolar: https://matbarofex.com.ar/producto/futuros-y-opciones-sobre-dolar
- A3/Matba Rofex futuros CER: https://matbarofex.com.ar/producto/futuros-sobre-cer
- Visor de precios: https://matbarofex.primary.ventures
- CEM: https://cem.matbarofex.com.ar/

Alternativas:
- BYMA API Market Data si los contratos estan cubiertos por el plan disponible: https://www.byma.com.ar/productos/productos-de-datos/market-data/apis
- A3 Sintesis Semanal / Informes Mensuales desde hub: https://a3mercados.com.ar/mercado/datos-de-mercado/

Costo/confiabilidad:
- Visor/CEM: gratis, scrapeable, confiabilidad media por dependencia de frontend.
- API BYMA/A3/MAE: alta, pero puede requerir credenciales o pago segun producto.

Decision operativa:
- Para MVP, tomar cierres semanales por visor/CEM o informe semanal y guardar timestamp/fuente.
- Para produccion, pedir API o feed institucional de A3/BYMA.

### 4. Curva CER, TAMAR y LECAP

Componentes oficiales:
- CER: BCRA tasas de interes, seccion CER: https://www.bcra.gob.ar/tasas-de-interes/
- TAMAR: BCRA tasas de interes, seccion depositos/TAMAR: https://www.bcra.gob.ar/tasas-de-interes/
- LECAP y otros instrumentos primarios: Tesoro licitaciones: https://www.argentina.gob.ar/economia/licitaciones
- Informes de deuda en pesos: https://www.argentina.gob.ar/economia/finanzas/informe-de-deuda-publica-en-pesos

Precios secundarios:
- BYMA API EOD/Delay/Snapshot para renta fija: https://www.byma.com.ar/productos/productos-de-datos/market-data/apis
- MAE Market Data y APIs: https://marketdata.mae.com.ar/ y https://www.mae.com.ar/APIsMAE
- Futuros sobre titulos publicos A3: https://matbarofex.com.ar/producto/futuros-sobre-titulos-publicos

Costo/confiabilidad:
- BCRA/Tesoro: gratis, oficial, alta, pero no dan curva secundaria completa.
- BYMA/MAE/A3: alta para mercado secundario; EOD puede ser gratis en BYMA con limite; delay/real-time pago o credenciales.
- Curva de brokers: media-alta, usualmente manual/paga, no fuente primaria.

Decision operativa:
- Para MVP semanal, construir tres bloques:
  1. CER y TAMAR oficiales desde BCRA.
  2. Tasas de corte y rollover desde Tesoro.
  3. Cierre secundario de LECAP/BONCER desde BYMA EOD o MAE scrapeable.
- Si falta BYMA/MAE, reportar "primario oficial + falta precio secundario verificable" antes que inventar curva.

### 5. Bonos hard dollar

Opcion recomendada:
- BYMA API EOD gratis o paga para AL30/GD30/AE38/GD35/GD38/AL35 y especies D/C: https://www.byma.com.ar/productos/productos-de-datos/market-data/apis
- MAE Market Data/boletin/informe diario: https://marketdata.mae.com.ar/boletindiario y https://marketdata.mae.com.ar/informediario
- MAE APIs Market Data para resumen final de renta fija: https://www.mae.com.ar/APIsMAE

Scrapeable:
- Rava perfiles de bonos: https://www.rava.com/
- BYMADATA abierto para informacion visible y avisos: https://open.bymadata.com.ar/

Costo/confiabilidad:
- BYMA/MAE: alta, con limitaciones de plan/credenciales.
- Rava/BYMADATA web: media para automatizacion, buena como fallback humano.

Decision operativa:
- Usar AL30D/GD30D y GD35D/GD38D como set minimo de hard dollar.
- Guardar precio, variacion semanal, paridad/TIR si se puede calcular con cashflows propios; no depender de TIR scrapeada sin validar supuestos.

### 6. Riesgo pais

Opcion oficial/licenciada:
- J.P. Morgan EMBI/EMBIG Argentina. Es propietario y requiere licencia o proveedor de datos.

Fallback gratuito:
- Rava: https://www.rava.com/perfil/RIESGO%20PAIS
- Ambito: https://www.ambito.com/contenidos/riesgo-pais.html

Proxy propio:
- Calcular spread aproximado con TIR de bonos hard dollar argentinos liquidos contra UST comparable.
- Fuentes de insumo: BYMA/MAE para bonos locales; Treasury/FRED u otra fuente oficial USA para UST.

Costo/confiabilidad:
- JPM/licencia: pago, alta, dato oficial de mercado.
- Rava/Ambito: gratis, media, secundario.
- Proxy propio: gratis, media si se documenta metodologia; no comparable 1:1 con EMBI.

Decision operativa:
- En MVP, mostrar "riesgo pais reportado por fuente secundaria" y/o "proxy soberano propio".
- No etiquetar el proxy como EMBI.

## Minimo viable semanal sin datos pagos

### Ingesta semanal propuesta

1. Dolar oficial:
   - BCRA `estadisticascambiarias` USD.
   - Salida: cierre semanal, variacion semanal, brecha contra MEP/CCL.

2. MEP/CCL:
   - Preferido: BYMA EOD gratuito con especies AL30/GD30 en pesos y dolares.
   - Alternativo: Indice CCL BYMA o CCL-MtR.
   - Fallback: Rava/Ambito, marcado como scrapeable/secundario.

3. Futuros:
   - A3/Matba Rofex visor/CEM o sintesis semanal.
   - Salida: contratos mas liquidos, variacion semanal, tasa implicita anualizada aproximada.

4. CER/TAMAR/LECAP:
   - BCRA CER y TAMAR.
   - Tesoro licitaciones para tasas de corte, monto y rollover.
   - BYMA EOD o MAE para precios secundarios si hay acceso; si no, reportar primario y agenda.

5. Bonos hard dollar:
   - BYMA EOD gratuito o MAE/Rava como fallback.
   - Salida: AL30D, GD30D, GD35D/GD38D, variacion semanal, paridad/TIR calculada si hay cashflows.

6. Riesgo pais:
   - Rava o Ambito como dato secundario.
   - Proxy propio de spread soberano si hay precios y UST comparable.

### Reglas de calidad del MVP

- Etiquetar cada dato con `fuente`, `timestamp`, `metodologia` y `confianza`.
- Separar "precio oficial", "precio de mercado" y "proxy calculado".
- Usar fuentes oficiales para niveles regulatorios o estadisticos; usar mercado para stress y validacion.
- Si hay contradiccion entre fuentes, priorizar:
  1. BCRA/Tesoro para oficial.
  2. BYMA/MAE/A3 para precio negociado.
  3. Rava/Ambito solo como respaldo o alerta.
- No mezclar datos intradiarios con cierres EOD en la misma variacion semanal.

### Salida semanal minima

| Bloque | Dato minimo | Fuente sin pago | Confianza |
| --- | --- | --- | --- |
| Cambiario oficial | USD oficial BCRA | BCRA API cambiaria | alta |
| Brecha | MEP/CCL calculado o indice | BYMA EOD/Indice CCL o CCL-MtR | media-alta |
| Futuros | primer y segundo contrato dolar | A3/Matba Rofex visor/CEM | media |
| Pesos | CER, TAMAR, tasas de corte Tesoro | BCRA + Tesoro | alta |
| Curva secundaria | LECAP/BONCER cierres | BYMA EOD gratis o MAE web | media |
| Hard dollar | AL30D/GD30D y GD35D/GD38D | BYMA EOD o MAE/Rava | media |
| Riesgo pais | EMBI reportado por secundario o proxy | Rava/Ambito/proxy propio | media |

## Recomendacion de implementacion

1. Crear conectores oficiales primero:
   - `bcra_fx`: USD oficial.
   - `bcra_rates`: CER y TAMAR.
   - `tesoro_licitaciones`: cronograma/resultados.

2. Crear conectores de mercado EOD:
   - `byma_eod`: bonos hard dollar, letras/bonos en pesos, especies D/C para MEP/CCL.
   - Si BYMA EOD no queda disponible, usar `mae_marketdata_scrape` como fallback.

3. Crear indicadores derivados:
   - `mep_ccl_calculated`: paridad por especie y metodologia versionada.
   - `peso_curve_snapshot`: LECAP/BONCER/TAMAR/CER por vencimiento.
   - `sovereign_spread_proxy`: spread de hard dollar contra UST, no EMBI.

4. Mantener scrapeos con bajo acoplamiento:
   - Guardar HTML o JSON crudo cuando sea legal/razonable.
   - Alertar si el selector cambia.
   - No usar scraping como unica fuente para decisiones criticas si existe API o archivo oficial.

## Gaps y preguntas no bloqueantes

- Confirmar si el proyecto tendra credenciales BYMA EOD/Indices sin costo. Supuesto para MVP: se puede solicitar suscripcion gratuita y, mientras tanto, usar visores/scraping.
- Confirmar si se acepta riesgo pais de Rava/Ambito como dato secundario. Supuesto para MVP: si, siempre marcado como no licenciado.
- Confirmar si se quiere curva completa con TIR/paridad calculada. Supuesto para MVP: basta cierre, variacion semanal y tasa/paridad cuando haya insumos confiables.
