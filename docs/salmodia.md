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

**Desplegable:** junto al título de cada salmo y del cántico evangélico, «Modo …» en rojo con un desplegable (el del día primero; después, en «Modos», los que se cantan: 1g, 2, 3a, 4g, 5, 6, 7a, 8G; el resto, en «Más modos»). El cambio vale para esa pieza en esa hora de ese día (`S.tonos`, se guardan los de la última semana).

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

Finales: …fd, acento normal («con ira»); …fdf, esdrújula («tendrás razón»); …ndf, esdrújula suave («sinceridad»); …ddf: en la mediante, si la antepenúltima o la penúltima es de una palabra átona (neutra: ni acentuada ni claramente débil, como «de», «el», «a»), se acentúa esa («ansia **de** ti», «yo, **el** Señor», «miedo **a** Dios»); si las dos son claramente débiles (de la misma palabra que un acento), aguda suave («para juz**gar**») (CRU, 20/11/2026). En la cadencia y la flexa, nunca la aguda (ver abajo). Dos fuertes seguidas: la segunda manda y la primera es débil (CRU): «¡oh Dios!» tiene fuerte «Dios» y débil «oh»; «mar, ¡oh Dios!» queda F D F. Monosílabo fuerte al final: igual que cualquier aguda.

**Nunca en la última sílaba: en la cadencia (CRU, 18/11/2026) y en la flexa (19/11/2026).** Donde caería en una aguda (…ddf), se acentúa la antepenúltima («a quién **te**meré», «bendecid **al** Señor»), salvo que sea la sílaba que sigue al acento de su propia palabra: entonces la penúltima («sedienta **de** ti», «se exalta **por** Dios»). Así la cadencia termina siempre en la nota final del modo. En los modos de dos acentos (1, 3, 6, 7), con la neutra de la mediante el primer acento va en su lugar de siempre: «[**an**]sia [**de**] ti». En el Gloria, «Amén» se canta como llana: «de los *si*glos. **A**mén».

- **Agudas:** en la mediante (español y latín), cuando la aguda lleva el acento, no se juntan en una sílaba notas que irían en sílabas distintas: la última lleva la nota del acento y se omiten las que seguían (forma B del Liber). En la cadencia y la flexa en español la última nunca lleva el acento (ver arriba). En la flexa latina, si el acento cae en la última, esa sílaba baja.
- **Modos de dos acentos** (1, 3, 6 y 7 en la mediante; 5 y 7 en la terminación): período de 2 sílabas, 3 como máximo, como en el gregoriano latino y en Chant Tools (jgabc). El primer acento va en una fuerte a 2 sílabas, si no a 3; si el intervalo entre acentos es mayor, como último recurso en una neutra a 2 o a 3; si tampoco hay, a 2 aunque sea débil (acento ficticio, como hace Chant Tools: «in progénies **et** pro**gé**nies»).
- **Flexa:** baja un grado desde la cuerda; desde do o desde fa (semitono), una tercera menor.
- **Entonación:** en el primer verso de cada salmo; en el cántico evangélico, en cada verso.
- **Antífona igual al comienzo del salmo** (en el libro, con † al final; CRU, 19/11/2026: también cuando el libro no la pone, si coinciden de verdad): el salmo empieza después de lo que la antífona ya dijo. Lo repetido se muestra en gris y no se canta, y la antífona lleva la † en rojo (no al repetirse). Si del verso queda una parte, va sin entonación: después de la flexa, con el metro y la terminación; después del asterisco, solo con la terminación. La entonación pasa al verso siguiente, y la partitura del primer verso abarca los dos (`omitirAnt` en `src/salmodia.js`). En la base, las antífonas que en el libro llevan † la tienen al final (« †»): Sal 26 I, 47, 116, 118, 105-112, 64, 96, 80, 147, 144 III, 148, Is 42, 10-16 (lunes antes del 24 de diciembre), 127 (Nona complementaria), 83 (dedicación y Letrán), 129 y 87 (Completas). Sin † en el libro y con la regla igual: Sal 17 I, 41, 67 III, 92, 109, 116 (San Basilio y San Gregorio), 144 III (III domingo de Cuaresma), Is 45.
- **Flexa:** como en la cadencia, nunca se acentúa la última: en el caso ddf, la antepenúltima («extenderá **el** Señor †»), o la penúltima si la antepenúltima sigue al acento de su propia palabra («tus obras, **Se**ñor †», «camino **de** Dios †») (CRU, 19/11/2026). Las sílabas que siguen al acento bajan a la nota de la flexa.
- **Sin entonación:** un salmo o cántico puede llevar `sin_entonacion: true` en `base/salmos/`; cantado, su primer verso empieza directo en la cuerda y hace el metro, en todos los modos. Así está Ef 1, 3-10 («Bendito sea Dios», CRU, 19/11/2026).
- **Mitad corta** (no alcanza para entonación y mediante): en español no se entona; empieza directo en la cuerda y hace la mediante. En latín, como Chant Tools: entonación corta del modo (2: `e fe eh`; 8: `g hg gj`; en los demás, la normal) y la última sílaba en la cuerda, sin cadencia («Magníficat»).
- **Latín (cántico evangélico):** igual que Chant Tools (jgabc), comprobado con los 416 hemistiquios del Benedictus y el Magníficat en los 8 modos. El acento sale de las tildes (también en mayúscula: «Ísrael»); los monosílabos átonos están en `ATONOS_LA`. Silabeo de Solesmes: «gn», «sc» y «sp» van juntos y «st» no (Ma-gní-fi-cat, ví-sce-ra); la x va con la vocal siguiente, salvo el prefijo «ex-»; «eu» es diptongo solo al principio de palabra ante consonante que no sea m ni n, y en heu, ceu, seu, neu (e-um, e-ré-xit); las excepciones (red-emp-ti-ó-nem, in-i-mí-cis…) están en `EXCEPCIONES_LA`. «Óriens ex alto», con tilde.

## Lo que dice el Liber Usualis (1961, pp. 112-117)

- **Período:** en las fórmulas de dos acentos, entre un acento y el otro hay una nota fija y otra hueca, que se canta solo si la palabra es esdrújula: 2 sílabas, o 3 como máximo. El caso sin acento a 2 o 3 no está en estas páginas (estaría en las reglas del comienzo del Liber).
- **Cadencia dactílica** en la mediante del modo 3 y en las terminaciones 1 D² y 4 E: la nota adicional se anticipa en la sílaba acentuada y la clivis pasa a la siguiente (Fí(j) li(ih) o(j)). Aplicado (`antic` en `parseParte`).
- **Monosílabo o palabra hebrea en la mediante** de los modos de un acento (2, 4, 5, 6 alt., 8): se puede usar la forma B (termina en la nota del acento) o la modulación ordinaria A. Coincide con la regla de CRU para las agudas. Para las terminaciones y las mediantes de dos acentos el Liber no trae forma B: ahí la terminación aguda es extensión nuestra, por decidir.
- **Flexa:** baja una segunda o una tercera según el tono, en la última sílaba antes de la †, o también en la penúltima si no está acentuada; vale también para monosílabos y palabras hebreas.
- **Entonación:** en el primer verso de cada salmo con su Gloria; en el Benedictus, el Magníficat y el Nunc dimíttis, en cada verso.
- **Modo 6:** también «otra fórmula», con mediante de un acento con una preparatoria: «6 alt. F» en el desplegable.

## Cortes de renglón dentro de una estrofa

- **Tres renglones con «:» al final del primero y sin flexa:** el primero es el metro y los otros dos son la cadencia; el tercero va más adentro, como renglón quebrado (CRU, 20/11/2026; ej. Sal 99: «Sabed que el Señor es Dios: * / que él nos hizo y somos suyos, / su pueblo y ovejas de su rebaño.»). En la base, ` ¶ ` dentro de la mitad marca el corte; en la app, clase `h3`.
- **Is 45,15-25:** «Yo juro por mi nombre, †» es la flexa, «de mi boca sale una sentencia, *» el metro y «una palabra irrevocable» la cadencia; el resto, metro y cadencia de a dos renglones.

## Cántico de Simeón

El Nunc dimíttis va en modo 3, de mediante con dos acentos: las dos sílabas en negrita, como en Chant Tools («vidérunt **ó**culi **me**i *»).
