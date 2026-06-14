# Politica de fixtures y tests offline

Este documento complementa [analysis/connector_architecture.md](/Users/ignacioreyna/PERSONAL/finance-news/analysis/connector_architecture.md) y fija la politica operativa para fixtures, snapshots y pruebas de conectores.

## Objetivo

- Hacer reproducible el parseo de cada fuente sin depender de red.
- Separar claramente payload crudo, snapshot normalizado y prueba de integracion con red.
- Mantener fixtures estables, pequenos y faciles de revisar.

## Regla de orden

1. Primero se prueba el parser puro con fixtures locales.
2. Luego se agregan pruebas de integracion con red solo para validar adquisicion, headers, auth y rate limits.
3. Si un parser no puede cubrirse offline, la fuente debe tratarse como deuda tecnica y no como excepcion por defecto.

## Estructura recomendada

- `analysis/fixtures/<connector>/raw/` para payloads crudos.
- `analysis/fixtures/<connector>/normalized/` para snapshots de salida del parser.
- `analysis/fixtures/<connector>/meta/` para notas de origen, fecha de captura y supuestos.

Ejemplo:

```text
analysis/fixtures/fomc_press_releases/raw/
analysis/fixtures/fomc_press_releases/normalized/
analysis/fixtures/fomc_press_releases/meta/
```

## Naming

Usar nombres estables, descriptivos y ordenables:

- `YYYY-MM-DD__source__case.ext` para fixtures puntuales.
- `source__case__variant.ext` cuando la fecha no sea el mejor discriminator.
- `page-01`, `page-02` para secuencias paginadas.
- `empty`, `schema-drift`, `missing-field`, `redirected`, `rate-limited` para escenarios funcionales.

Reglas:

- El nombre debe indicar fuente y escenario sin depender de ids efimeros.
- Evitar hashes como nombre principal; si se necesitan, deben ir en metadata o comentarios del fixture.
- Si un fixture cambia por schema, versionarlo con sufijo de revision, por ejemplo `...__v2.html`.

## Formato por tipo de snapshot

### HTML

- Guardar el HTML bruto minimizado solo cuando el parser dependa del markup.
- Preservar el DOM suficiente para reproducir selectores, links y textos relevantes.
- El snapshot normalizado debe comparar items, no el documento entero, salvo que el layout sea el contrato.
- Si la fuente cambia mucho, preferir un fixture HTML reducido y anotado sobre una pagina completa ruidosa.

### CSV

- Guardar con encabezados exactos y separadores literales.
- Normalizar saltos de linea y encoding para evitar falsos positivos.
- Ordenar filas de forma estable segun la semantica de la fuente o el cursor original.
- Incluir un snapshot normalizado por fila o por lote, segun el conector.

### PDF

- Guardar el PDF original solo si el parser extrae tablas, texto o metadata desde el documento.
- Cuando sea posible, agregar una extraccion textual intermedia para tests unitarios.
- Si el parser depende de pagina, anotar pagina y region de interes en `meta/`.
- Evitar fixtures PDF enormes; preferir recortes representativos cuando la cobertura sea equivalente.

## Criterios de estabilidad

- El fixture debe ser minimo pero suficiente para cubrir el comportamiento observado.
- No debe depender de reloj del sistema, red, cookies de sesion ni orden no determinista.
- Cualquier dato variable debe quedar fijado en metadata o parametrizacion del test.
- Si el parser cambia de version, el snapshot normalizado debe revisarse junto con el fixture bruto.

## Criterios de reproduccion

- El test debe poder correr sin red ni credenciales externas.
- El fixture debe contener todo lo necesario para ejecutar el parser de forma determinista.
- Si falta contexto para reproducir el caso, ese contexto pertenece al fixture o a un helper local, no a la red.
- Los casos de error deben ser reproducibles offline con muestras de payload incompleto, vacio o alterado.

## Regla de uso en tests

- Los tests de parser deben consumir fixtures locales y comparar estructuras normalizadas.
- Las pruebas con red se limitan a adaptadores, autenticacion, paginado real y resiliencia de transporte.
- No se introduce una prueba con red para validar una transformacion que ya puede ejercitarse offline.
- El orden de implementacion es siempre parser puro, fixture, snapshot, integracion con red.

## Mantenimiento

- Cuando cambie un contrato de parseo, actualizar fixture crudo y snapshot normalizado en la misma revison.
- Si el cambio es solo de presentacion o metadata no estructural, evitar tocar el fixture crudo.
- Si un fixture deja de representar la fuente real, archivarlo o reemplazarlo en lugar de acumular variantes ambiguas.

