# Salmodia en español: modos, pautado y partitura (11/2026)

Motor: `src/salmodia.js` (tonos de jgabc, de B. Bloomfield). Pruebas: `tests/salmodia.test.mjs`.

## Dónde y cómo

- **Laudes y Vísperas, cuando el oficio se canta:** cada salmo y cántico lleva el primer verso en partitura (con la entonación) y los demás pautados: el acento en negrita y las preparatorias en cursiva. Recitado: texto con * y †, sin pautas. Las antífonas van en recto tono (texto, sin partitura).
- **Cántico evangélico** (Benedictus y Magníficat, en latín): el mismo modo, con la entonación en cada verso; primer verso en partitura con la traducción bajo los neumas, los demás pautados con interlineal.
- **Cántico Ap 19** (domingos en Vísperas): cada estrofa se pauta como un verso (primer renglón, mediante; segundo, terminación), entre los Aleluia. El estribillo «R. …» (1 Tm 3, 16) no se pauta ni va en la partitura.
- **Completas, Oficio de lectura e Intermedia: sin cambios.** El Salva nos y el Nunc dimíttis siguen en el modo 3 a.

## Modos (`MODOS` en `src/laudes.js`)

| Semana del salterio | Domingo | Ferias |
|---|---|---|
| I | 1 g | 2 D |
| II | 3 a | 4 g |
| III | 6 F | 5 a |
| IV | 7 a | 8 G |

El mismo modo para todos los salmos y cánticos de la hora y para el cántico evangélico. Las I Vísperas llevan el del domingo. Para confirmar con CRU: las solemnidades llevan el del domingo de su semana; los días sin semana del salterio (Navidad, octava de Pascua, Pentecostés), la semana I.

**Desplegable:** junto al título de cada salmo y del cántico evangélico, «Modo …» en rojo con un desplegable (el del día primero, después los demás). El cambio vale para esa pieza en esa hora de ese día (`S.tonos`, se guardan los de la última semana).

## Silabeo

- Sin sinalefa ni elisiones: cada sílaba lleva su nota.
- qu y gu (con u muda) son una consonante: POR-que, ex-qui-SI-tos. ch, ll y rr, también.
- «Aleluia»: a-le-LU-ia (la i entre vocales es consonante). «Sión»: Si-ÓN, aguda de dos sílabas; «guió»: gui-Ó (lista `EXCEPCIONES`: «dió», grafía antigua, sigue siendo una sílaba).
- Monosílabos átonos: los de `ATONOS` (artículos, preposiciones, conjunciones, pronombres átonos, posesivos antepuestos). Las palabras de dos o más sílabas llevan siempre su acento («pa-» de «para» es fuerte).

## Acento (reglas de CRU)

Tipos de sílaba: **F** (fuerte: la acentuada de su palabra), **D** (débil: inmediatamente antes o después de una fuerte), **N** (neutra: sin acento, en una palabra que lo tiene: «ma-» de majestad). Las palabras átonas cuentan como débiles (lectura nuestra, para confirmar: con la otra, «estrado de tus pies» se acentuaría en «de»).

1. Mirar del final hacia el comienzo.
2. El acento, en la penúltima o en la antepenúltima; nunca más atrás; en la última solo si no se puede en otra.
3. No acentuar sílabas débiles.
4. Evitar en lo posible acentuar la última.
5. Período de 2 a 3 sílabas por acento.

Finales: …fd, acento normal («con ira»); …fdf, esdrújula («tendrás razón»); …ndf, esdrújula suave («sinceridad»); …ddf, aguda suave («para juzgar»). Agregado nuestro: …ff, la penúltima («Señor Dios»). Monosílabos fuertes: «no tengo miedo a Dios» va en «Dios».

- **Agudas:** no se juntan en una sílaba notas que irían en sílabas distintas: la última lleva la nota del acento y se omiten las que seguían (también en la terminación, que entonces acaba en la nota del acento). En la flexa, si el acento cae en la última, esa sílaba baja.
- **Modos de dos acentos** (1, 3, 6 y 7 en la mediante; 5 y 7 en la terminación): el primero, a 2 o 3 sílabas del segundo, en una fuerte o si no en una neutra; si las dos son débiles, a 4 sílabas (fuerte o neutra) o a 5 (fuerte); solo si no hay nada de eso, en la débil. Pendiente de estudio con CRU.
- **Flexa:** baja un grado desde la cuerda; desde do o desde fa (semitono), una tercera menor.
- **Entonación:** en el primer verso de cada salmo; en el cántico evangélico, en cada verso. Si la mitad es corta, la cadencia tiene prioridad.
- **Latín (cántico evangélico):** las mismas reglas; el acento sale de las tildes y los monosílabos átonos están en `ATONOS_LA`.
