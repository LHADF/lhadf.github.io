# Vísperas — estado (11/11/2026)

Igual que Laudes (ver `docs/laudes.md`): mismas decisiones ADF (citas, Pater noster, preces, conclusión con o sin ministro ordenado). Sin «Dómine, lábia mea». Cántico evangélico: Magníficat en latín (PDF «NVG» de ADF) con interlineal palabra por palabra (`base/gregoriano/magnificat.yaml`), recitado por ahora.

## Base

`tools/importar/importar_visperas.py` leyó 5298 Vísperas de sync (2015–2025): `base/salterio/visperas.yaml` (cuatro semanas; `domingo_1` = I Vísperas del domingo; no hay «sábado»), `base/tiempo/visperas.yaml`, `base/santoral/visperas.yaml` (las primeras vísperas llevan «· I Vísperas» en el nombre), `base/himnos/visperas.yaml` y 61 salmos y cánticos nuevos (los salmos partidos: `salmo-44-i`, `salmo-44-ii`…). Variantes: `base/informes/visperas.md`.

- Toda tarde de sábado es I Vísperas del domingo (sync no siempre lo rotula), salvo el Sábado Santo y las solemnidades en sábado.

## Armado (`src/laudes.js`, que arma las dos horas)

- **I Vísperas:** si mañana tiene primeras vísperas en el calendario ADF (`pv`) y hoy no es una solemnidad de mayor rango, se rezan las de mañana (salterio `domingo_1`, propio «· I Vísperas»).
- **Sin textos para lo elegido:** se toma la otra posibilidad (las del día, o las I Vísperas de mañana) y la app lo avisa. Pasa en las vísperas de solemnidades ADF que sync no tiene (San Blas, María Auxiliadora, Sumo y Eterno Sacerdote, Corredentora…) y de la Ascensión en jueves (sync la trae en domingo).
- **Pendientes** (sync no los trae; siempre cayeron bajo Trinidad o Corpus): IX y X Domingo del Tiempo Ordinario, antífona del Magníficat y oración (30/5/2027, 7/6/2026 y sus I Vísperas).
- Himnos: por ahora los de sync en español.
