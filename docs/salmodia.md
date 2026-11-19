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

El mismo modo para todos los salmos y cánticos de la hora y para el cántico evangélico. Las I Vísperas llevan el del domingo. Las solemnidades siguen el ritmo de la semana en que caen (CRU): en martes de la semana II, el de las ferias de la II. Días que el calendario deja sin semana del salterio (CRU): la Ascensión y Pentecostés, la semana en que caen, contada de domingo a sábado (en domingo, el modo de ese domingo; la Ascensión en jueves, el de las ferias); el tiempo de Navidad (de Navidad al Bautismo) y Pascua con su octava, modo 1 g; Viernes y Sábado Santo, modo 4 g.

**Desplegable:** junto al título de cada salmo y del cántico evangélico, «Modo …» en rojo con un desplegable (el del día primero, después los demás). El cambio vale para esa pieza en esa hora de ese día (`S.tonos`, se guardan los de la última semana).

## Silabeo

- Sin sinalefa ni elisiones: cada sílaba lleva su nota.
- qu y gu (con u muda) son una consonante: POR-que, ex-qui-SI-tos. ch, ll y rr, también.
- «Aleluia»: a-le-LU-ia (la i entre vocales es consonante). «Sión»: Si-ÓN, aguda de dos sílabas; «guió»: gui-Ó (lista `EXCEPCIONES`: «dió», grafía antigua, sigue siendo una sílaba).
- Monosílabos átonos: los de `ATONOS` (artículos, preposiciones, conjunciones, pronombres átonos, posesivos antepuestos). Las palabras de dos o más sílabas llevan siempre su acento («pa-» de «para» es fuerte).

## Acento (reglas de CRU)

Tipos de sílaba: **F** (fuerte: la acentuada de su palabra), **D** (débil: inmediatamente antes o después de una fuerte), **N** (neutra: átona no pegada a una acentuada, también la de una palabra átona: «ma-» de majestad, «de» en «estrado de tus pies»). Las neutras se acentúan como último recurso (CRU, 18/11/2026).

1. Mirar del final hacia el comienzo.
2. El acento, en la penúltima o en la antepenúltima; nunca más atrás; en la última solo si no se puede en otra.
3. No acentuar sílabas débiles.
4. Evitar en lo posible acentuar la última.
5. Período de 2 a 3 sílabas por acento.

Finales: …fd, acento normal («con ira»); …fdf, esdrújula («tendrás razón»); …ndf, esdrújula suave («sinceridad»); …ddf, aguda suave («para juzgar»). Dos fuertes seguidas: la segunda manda y la primera es débil (CRU): «¡oh Dios!» tiene fuerte «Dios» y débil «oh»; «mar, ¡oh Dios!» queda F D F. Monosílabos fuertes: «no tengo miedo a Dios» va en «Dios».

**En la cadencia (terminación), nunca en la última sílaba** (CRU, 18/11/2026): donde la mediante haría aguda suave (…ddf), la cadencia acentúa la antepenúltima («a quién **te**meré», «bendecid **al** Señor»), salvo que sea la sílaba que sigue al acento de su propia palabra: entonces la penúltima («sedienta **de** ti», «se exalta **por** Dios»). Así la cadencia termina siempre en la nota final del modo. En el Gloria, «Amén» se canta como llana: «de los *si*glos. **A**mén».

- **Agudas:** en la mediante (y la flexa) no se juntan en una sílaba notas que irían en sílabas distintas: la última lleva la nota del acento y se omiten las que seguían (forma B del Liber). En la cadencia la última nunca lleva el acento (ver arriba). En la flexa, si el acento cae en la última, esa sílaba baja.
- **Modos de dos acentos** (1, 3, 6 y 7 en la mediante; 5 y 7 en la terminación): período de 2 sílabas, 3 como máximo, como en el gregoriano latino y en Chant Tools (jgabc). El primer acento va en una fuerte a 2 sílabas, si no a 3; si el intervalo entre acentos es mayor, como último recurso en una neutra a 2 o a 3; si tampoco hay, a 2 aunque sea débil (acento ficticio, como hace Chant Tools: «in progénies **et** pro**gé**nies»).
- **Flexa:** baja un grado desde la cuerda; desde do o desde fa (semitono), una tercera menor.
- **Entonación:** en el primer verso de cada salmo; en el cántico evangélico, en cada verso.
- **Mitad corta** (no alcanza para entonación y mediante), como Chant Tools: entonación corta del modo (2: `e fe eh`; 8: `g hg gj`; en los demás, la normal) y la última sílaba en la cuerda, sin cadencia. En español pasa solo con Ef 1, 3-10 «Bendito sea Dios, *» en los modos 1, 3, 4, 6 y 7 (a confirmar).
- **Latín (cántico evangélico):** igual que Chant Tools (jgabc), comprobado con los 416 hemistiquios del Benedictus y el Magníficat en los 8 modos. El acento sale de las tildes (también en mayúscula: «Ísrael»); los monosílabos átonos están en `ATONOS_LA`. Silabeo de Solesmes: «gn», «sc» y «sp» van juntos y «st» no (Ma-gní-fi-cat, ví-sce-ra); la x va con la vocal siguiente, salvo el prefijo «ex-»; «eu» es diptongo solo al principio de palabra ante consonante que no sea m ni n, y en heu, ceu, seu, neu (e-um, e-ré-xit); las excepciones (red-emp-ti-ó-nem, in-i-mí-cis…) están en `EXCEPCIONES_LA`. «Óriens ex alto», con tilde.

## Lo que dice el Liber Usualis (1961, pp. 112-117)

- **Período:** en las fórmulas de dos acentos, entre un acento y el otro hay una nota fija y otra hueca, que se canta solo si la palabra es esdrújula: 2 sílabas, o 3 como máximo. El caso sin acento a 2 o 3 no está en estas páginas (estaría en las reglas del comienzo del Liber).
- **Cadencia dactílica** en la mediante del modo 3 y en las terminaciones 1 D² y 4 E: la nota adicional se anticipa en la sílaba acentuada y la clivis pasa a la siguiente (Fí(j) li(ih) o(j)). Aplicado (`antic` en `parseParte`).
- **Monosílabo o palabra hebrea en la mediante** de los modos de un acento (2, 4, 5, 6 alt., 8): se puede usar la forma B (termina en la nota del acento) o la modulación ordinaria A. Coincide con la regla de CRU para las agudas. Para las terminaciones y las mediantes de dos acentos el Liber no trae forma B: ahí la terminación aguda es extensión nuestra, por decidir.
- **Flexa:** baja una segunda o una tercera según el tono, en la última sílaba antes de la †, o también en la penúltima si no está acentuada; vale también para monosílabos y palabras hebreas.
- **Entonación:** en el primer verso de cada salmo con su Gloria; en el Benedictus, el Magníficat y el Nunc dimíttis, en cada verso.
- **Modo 6:** también «otra fórmula», con mediante de un acento con una preparatoria: «6 alt. F» en el desplegable.
