# Vísperas — estado (11/11/2026)

Igual que Laudes (ver `docs/laudes.md`): mismas decisiones ADF (citas, Pater noster, preces, conclusión con o sin ministro ordenado). Sin «Dómine, lábia mea». Cántico evangélico: Magníficat en latín (PDF «NVG» de ADF) con interlineal palabra por palabra (`base/gregoriano/magnificat.yaml`), recitado por ahora.

## Base

`tools/importar/importar_visperas.py` leyó 5298 Vísperas de sync (2015–2025): `base/salterio/visperas.yaml` (cuatro semanas; `domingo_1` = I Vísperas del domingo; no hay «sábado»), `base/tiempo/visperas.yaml`, `base/santoral/visperas.yaml` (las primeras vísperas llevan «· I Vísperas» en el nombre), `base/himnos/visperas.yaml` y 61 salmos y cánticos nuevos (los salmos partidos: `salmo-44-i`, `salmo-44-ii`…). Variantes: `base/informes/visperas.md`.

- Toda tarde de sábado es I Vísperas del domingo (sync no siempre lo rotula), salvo el Sábado Santo y las solemnidades en sábado.

## Armado (`src/laudes.js`, que arma las dos horas)

- **I Vísperas:** si mañana tiene primeras vísperas en el calendario ADF (`pv`) y hoy no es una solemnidad de mayor rango, se rezan las de mañana (salterio `domingo_1`, propio «· I Vísperas»).
- **Sin textos para lo elegido:** se toma la otra posibilidad (las del día, o las I Vísperas de mañana) y la app lo avisa. Pasa en las vísperas de solemnidades ADF que sync no tiene (San Blas, María Auxiliadora, Sumo y Eterno Sacerdote, Corredentora…) y de la Ascensión en jueves (sync la trae en domingo).
- **Memorias con propio en Laudes y sin Vísperas en la base** (el libro manda tomar las Vísperas del común: Santa Isabel de Hungría, Inmaculado Corazón de María, Nuestra Señora del Valle, San José obrero): `tools/base_js.py` les da el común que dice su santoral de Laudes (o `santoral/adf.yaml`, o el libro) y la oración de Laudes. Antes se rezaba la feria sin aviso. San José obrero tiene Vísperas propias en el libro que faltan en la base: por ahora, del común de santos varones (19/11/2026).
- **Pendientes** (sync no los trae; siempre cayeron bajo Trinidad o Corpus): IX y X Domingo del Tiempo Ordinario, antífona del Magníficat y oración (30/5/2027, 7/6/2026 y sus I Vísperas).
- Himnos: los de sync en español. Himnos en gregoriano (11/2026): `base/gregoriano/himnos.yaml` (partituras `.gabc` de la misma carpeta). Son una opción después del himno en español, que sigue primero; elegir «gregoriano» se recuerda para los días que lo tienen. Domingos del Tiempo Ordinario sin otra celebración, según la semana del salterio: semanas I y III, *Deus, Creátor ómnium* (I Vísperas), *Ætérne rerum Cónditor* (Laudes) y *Lucis Creátor óptime* (II Vísperas); semanas II y IV, *Rerum Deus fons ómnium*, *Ecce iam noctis* y *O lux beáta Trínitas*. Domingos de Adviento: *Creátor alme síderum* (Vísperas) y *En clara vox* (Laudes). Vísperas (I y II) de Cristo Rey, *Te sæculórum Príncipem*; de Pentecostés, *Veni Creátor Spíritus*; de Navidad, *Iesu, Redémptor ómnium*. Traducción interlineal por frases breves (no palabra por palabra), tomada en lo posible de la *Liturgia de las Horas Dominical* de ADF y de sus hojas del Veni Creator y del Creator alme; recitado: latín con la traducción debajo, verso por verso.
