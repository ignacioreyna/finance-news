# Glosario tecnico para normalizacion de transcripciones

Base de trabajo: `analysis/host_profile.md`, `analysis/subagents/*.md` y transcriptos locales en `data/transcripts/`.

## Canonicos y variantes frecuentes

| Canonico | Variantes mal transcriptas o abreviadas | Contexto de uso | Normalizar a |
|---|---|---|---|
| Fed | fe, la fed, reserva federal | Tasa, balance, comunicacion, Powell, QT/QE | `Fed` |
| FOMC | fomc, fomsi, comite, directorio | Decision de politica monetaria, votos, statement, dot plot | `FOMC` |
| PCE | pci, pce core, inflacion preferida | Inflacion EE.UU., core, servicios, pass-through | `PCE` |
| JOLTS | shelds, jolts, jobs openings | Vacantes, hires, quits, mercado laboral | `JOLTS` |
| BLS | beeles, bls, bureau laboral | NFP, desempleo, participacion, CPI/empleo | `BLS` |
| TGA | cuenta 2020, treasury general account, cuenta del tesoro | Liquidez del Tesoro de EE.UU., cash balance en Fed | `TGA` |
| SOMA | soma, cartera soma, balance soma | Reinvenciones, runoff, QT/QE, auctions no competitivas | `SOMA` |
| Rofex | rofex, ro-fex, rofecs | Futuros de dolar/tasas en Argentina | `Rofex` |
| A3 | a3, mercado a3, matba rofex, bolsa a3 | Futuros y derivados, pantalla local | `A3` |
| Bessent | besent, bezen, bessen, bessett | Scott Bessent, Tesoro de EE.UU. | `Bessent` |
| Waller | waller, hualler, valer, walles | Gobernador de la Fed, comentarios de tasa/balance | `Waller` |
| INDEC | indec, indesk, índice nacional | IPC, canastas, actividad, salarios | `INDEC` |
| BCRA | bcra, banco central, banco central de la republica argentina | Reservas, tasa, encajes, comunicacion, balance | `BCRA` |
| TAMAR | tamar, tama, tasa tamar | Costo de fondeo bancario, curva pesos | `TAMAR` |
| LECAP | lecap, lecaps, le cap, letras capitalizables | Curva pesos, licitaciones, rollover | `LECAP` |

## Reglas automatizables

1. Normalizar mayusculas de acronimos canonicos: `Fed`, `FOMC`, `PCE`, `JOLTS`, `BLS`, `TGA`, `SOMA`, `Rofex`, `A3`, `Bessent`, `Waller`, `INDEC`, `BCRA`, `TAMAR`, `LECAP`.
2. Unificar variantes foneticas obvias cuando el contexto sea consistente:
   - `la fe` -> `Fed`
   - `shelds` -> `JOLTS`
   - `bezen/bessen` -> `Bessent`
   - `cuenta 2020` o `cuenta del tesoro` en contexto de liquidez EE.UU. -> `TGA`
   - `carta soma`, `balance soma`, `reinvenciones soma` -> `SOMA`
3. Mantener la sigla en el idioma de uso local:
   - Argentina: `INDEC`, `BCRA`, `TAMAR`, `LECAP`, `Rofex`, `A3`
   - EE.UU.: `Fed`, `FOMC`, `PCE`, `JOLTS`, `BLS`, `TGA`, `SOMA`
4. No expandir siglas en la capa de transcript normalizada salvo que el entorno de salida lo pida. La sigla canonica alcanza para busqueda y alineacion.

## Casos que requieren revision humana

1. Cuando la misma forma ASR puede mapear a dos entidades posibles segun el episodio.
   - Ejemplo: `cuenta 2020` puede ser TGA, pero si el contexto es argentino puede referir a la cuenta del Tesoro en BCRA.
2. Cuando el reconocimiento audibiliza nombres propios y no siglas.
   - Ejemplo: `Waller` puede confundirse con un apellido similar; revisar si el contexto es un gobernador de la Fed o una referencia distinta.
3. Cuando el episodio mezcla siglas con marcas o pantallas de mercado.
   - Ejemplo: `A3`, `Rofex`, `Matba Rofex`, o menciones a futuros sin pantalla explicita.
4. Cuando la transcripcion parece una hipotesis semantica y no un error mecanico.
   - Ejemplo: si `la fe` aparece en una frase religiosa o generica, no forzar `Fed`.
5. Cuando el nombre propio es central para la tesis del episodio pero no queda claro.
   - Ejemplo: `Bessent`, `Waller`, `Powell`, `Ueda`, `Warsh`.

## Criterio operativo

- Priorizar el contexto economico-financiero inmediato sobre la coincidencia literal.
- Si hay sigla canonica y contexto suficiente, normalizar.
- Si la duda cambia el sentido del pasaje o afecta una etiqueta de busqueda, dejar marca para revision humana antes de reemplazar.
