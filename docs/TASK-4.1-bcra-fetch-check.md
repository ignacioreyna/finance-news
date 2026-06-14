# TASK-4.1 - BCRA Comunicaciones A fetch check

Fecha de verificación: 2026-06-14

## Objetivo

Dejar documentada una verificación controlada del patrón de fetch usado por el conector `BcraComunicacionesAConnector`.

## Patrón asumido

El conector arma la URL oficial del PDF con el patrón:

`https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A{numero}.pdf`

## Verificación controlada

Se verificó contra URLs oficiales del BCRA, sin depender del buscador HTML:

- `https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8060.pdf`
- `https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8083.pdf`
- `https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8190.pdf`

Observaciones registradas:

- El recurso responde como `application/pdf`.
- `A8060.pdf` existe y expone el encabezado `COMUNICACIÓN “A” 8060 11/07/2024`.
- `A8083.pdf` existe y expone el encabezado `COMUNICACIÓN “A” 8083 05/08/2024`.
- `A8190.pdf` existe y expone el encabezado `COMUNICACIÓN “A” 8190 30/01/2025`.

## Limitación conocida

El proyecto no declara hoy una dependencia de extracción de texto PDF. El conector deja la extracción detrás de la interfaz `PdfTextExtractor` y usa `pypdf` sólo si está disponible en el entorno. Los tests del parser se ejecutan offline con fixtures textuales derivados de PDFs reales del BCRA.
