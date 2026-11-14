# Clasificación del libro contra la base

Una fila por pieza del libro en `clasificacion.csv`. **Regla:** el texto de `sync` manda; el libro llena lo que falta, suma variantes y reemplaza lo que se había cargado a mano del libro (`comunes/`, `santoral/libro.yaml`). La arma `extraccion/clasificar.py` sobre los emparejamientos de `comparar_base.py`. No toca ni `base/` ni la app.

## Qué quiere decir cada grupo

| Grupo | Qué se hace |
|---|---|
| **Queda la de sync** (6691) | El libro no cambia nada: se descarta la pieza del libro. |
| **Sync + variantes del libro** (1193) | Se mantiene el texto de sync y se suman las variantes por tiempo o día que trae el libro. |
| **Sync con error de estructura** (57) | Se mantiene el texto de sync y se corrige el corte o el orden mirando el libro. |
| **Reemplazar lo cargado a mano** (437) | Vino del libro sin la extracción limpia: se reemplaza por la extracción. |
| **Falta en la base** (3388) | Se agrega desde el libro (en su traducción). |
| **Sin cotejar** (755) | Está en una hora que la base tiene, pero la comparación no mira esa parte: hay que ver si falta. |
| **Rúbricas** (2394) | Indicaciones del libro: no son texto para rezar; sirven para las reglas. |
| **Ordinario** (325) | Lo que la app tiene fijo: se coteja aparte, a mano. |

## Por sección

| Sección | Queda la de sync | Sync + variantes del libro | Sync con error de estructura | Reemplazar lo cargado a mano | Falta en la base | Sin cotejar | Rúbricas | Ordinario | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ordinario |  |  |  |  |  |  |  | 325 | 325 |
| salterio | 1358 | 261 | 27 |  | 18 | 235 | 510 |  | 2409 |
| completas | 19 | 15 | 1 |  |  | 73 | 75 |  | 183 |
| santoral | 1434 | 76 | 7 | 87 | 849 | 290 | 570 |  | 3313 |
| comunes |  |  |  | 350 | 218 | 9 | 186 |  | 763 |
| difuntos |  |  |  |  | 81 |  |  |  | 81 |
| apendices |  |  |  |  | 1420 |  |  |  | 1420 |
| tiempo | 3880 | 841 | 22 |  | 498 | 148 | 1053 |  | 6442 |
| biblioteca de salmos |  |  |  |  | 80 |  |  |  | 80 |
| biblioteca de himnos |  |  |  |  | 224 |  |  |  | 224 |
| **Total** | **6691** | **1193** | **57** | **437** | **3388** | **755** | **2394** | **325** | **15240** |

## Lo que falta, por qué

| Sección | Motivo | Piezas |
|---|---|---:|
| apendices | sección que la base no tiene | 1420 |
| biblioteca de himnos | himno que la base no tiene | 224 |
| biblioteca de salmos | salmo o cántico sin par por clave (puede ser el mismo con otro nombre) | 80 |
| comunes | celebración o día que la base no tiene | 31 |
| comunes | hora que la base no tiene | 187 |
| difuntos | sección que la base no tiene | 81 |
| salterio | celebración o día que la base no tiene | 18 |
| santoral | celebración o día que la base no tiene | 716 |
| santoral | hora que la base no tiene | 133 |
| tiempo | celebración o día que la base no tiene | 326 |
| tiempo | hora que la base no tiene | 172 |

Celebraciones o días enteros que faltan: **112**.

- **salterio** (1): `salmodia-complementaria`
- **santoral** (85): `beata-ana-de-los-angeles-monteagudo`, `beata-josefa-naval-girbes-virgen-seglar`, `beata-mariana-de-jesus-navarro-virgen`, `beatas-angeles-de-san-jose-maria-del-sufragio-virgenes-y-companeras-ma`, `beato-francisco-de-paula-castello-aleu-martir`, `beato-jose-aparicio-sanz-y-ccxxxii-companeros-martires`, `beato-juan-pablo-ii-papa`, `beato-juan-xxiii-papa`, `beato-nicolas-factor-presbitero`, `beatos-antonio-perulles-presbitero-y-companeros-martires`, `beatos-juan-de-perusa-presbitero-y-pedro-de-saxoferrato-religioso-mart`, `bienaventurada-virgen-maria-de-los-angeles-del-puig`, `el-senor-de-los-milagros`, `la-dedicacion-de-las-basilicas-de-los-apostoles-san-pedro-y-san-pablo`, `la-natividad-de-la-santisima-virgen-maria-nuestra-senora-de-monserrate`, `la-santa-faz-de-nuestro-senor-jesucristo`, `martires-de-espana-del-siglo-xx`, `nuestra-senora-de-coromoto`, `nuestra-senora-de-la-paz`, `nuestra-senora-de-los-desamparados`, `nuestra-senora-del-remedio-patrona-de-la-ciudad-de-alicante`, `sab-gregorio-vii-papa`, `san-adalberto-obispo-y-martir`, `san-alberto-magno-obispo-y-doctor-de-la-iglesia`, `san-cirilo-de-alejandria-obispo-y-doctor-de-la-iglesia`, `san-cirilo-de-jerusalen-obispo-y-doctor-de-la-iglesia`, `san-columbano-abad`, `san-emigdio-obispo-y-martir`, `san-enrique`, `san-esteban-de-hungria`, `san-eulogio-de-cordoba-presbitero-y-martir`, `san-ezequiel-moreno-obispo`, `san-francisco-de-borja-presbitero`, `san-francisco-de-paula-ermitano`, `san-fructuoso-obispo-y-martir-y-sus-diaconos-santos-augurio-y-eulogio`, `san-isidoro-de-sevilla-obispo-y-doctor-de-la-iglesia`, `san-isidoro-obispo-y-doctor-de-la-iglesia`, `san-jenaro-obispo-y-martir`, `san-juan-de-brebeuf-y-san-isaac-jogues-presbiteros-y-companeros-martir`, `san-juan-de-dios-religioso`, `san-juan-de-kety-presbitero`, `san-juan-i-papa-y-martir`, `san-juan-leonardi-presbitero`, `san-juan-macias-religioso`, `san-juan-macias-religioso-2`, `san-lorenzo-ruiz-y-companeros-martires`, `san-luis-beltran-presbitero`, `san-luis-bertran-presbitero`, `san-luis-obispo`, `san-marcelino-champagnat-presbitero`, `san-martin-de-porres-religioso`, `san-martin-i-papa-y-martir`, `san-nereo-y-san-aquiles-martires`, `san-oscar-obispo`, `san-pascual-bailon-religioso`, `san-patricio-obispo`, `san-paulino-de-nola-obispo`, `san-pedro-canisio-presbitero-y-doctor-de-la-iglesia`, `san-pedro-chanel-presbitero-y-martir`, `san-pedro-de-alcantara-presbitero`, `san-pelayo-martir`, `san-pio-v-papa`, `san-roque`, `san-sarbelio-charbel-maklluf-presbitero`, `san-sebastian-martir`, `san-silvestre-i-papa`, `san-sixto-ii-papa-y-companeros-martires`, `san-vicente-ferrer-presbitero`, `san-vicente-ferrer-presbitero-patrono-de-la-archidiocesis-de-valencia`, `santa-eduvigis-religiosa`, `santa-eulalia-de-merida-virgen-y-martir`, `santa-francisca-romana-religiosa`, `santa-joaquina-vedruna-religiosa`, `santa-joserfina-bakhita-virgen`, `santa-margarita-de-escocia`, `santa-maria-magdalena-de-pazzi-virgen`, `santa-maria-micaela-del-santisimo-sacramento`, `santa-perpetua-y-santa-felicidad-martires`, `santa-rosa-de-lima-virgen-patrona-de-lima-del-peru-y-de-america-latina`, `santa-soledad-torres-acosta-virgen`, `santa-teresa-de-jesus-jornet-e-ibars-virgen-patrona-de-la-ancianidad`, `santa-vicenta-maria-lopez-vicuna-virgen`, `santo-tomas-becket-obispo-y-martir`, `santo-tomas-de-villanueva-obispo`, `temporas-de-accion-de-gracias-y-de-peticion`
- **comunes** (3): `caridad`, `educadores`, `religiosos`
- **tiempo** (23): `10-de-enero-o-jueves-despues-del-domingo-de-epifania`, `11-de-enero-o-viernes-despues-del-domingo-de-epifania`, `12-de-enero-o-sabado-despues-del-domingo-de-epifania`, `17-de-diciembre`, `18-de-diciembre`, `19-de-diciembre`, `20-de-diciembre`, `21-de-diciembre`, `22-de-diciembre`, `23-de-diciembre`, `24-de-diciembre`, `26-de-diciembre`, `27-de-diciembre`, `28-de-diciembre`, `6-de-enero`, `7-de-enero`, `jueves-santo-de-la-cena-del-senor`, `jueves-vi-semana-de-pascua`, `jueves-xv-semana-del-tiempo-ordinario`, `semana-7`, `solemnidades-del-senor-durante-el-tiempo-ordinario`, `textos-comunes-1`, `textos-comunes-2`

Horas que faltan dentro de lo que la base sí tiene:

| Sección | Hora | Piezas |
|---|---|---:|
| comunes | nona | 27 |
| comunes | sexta | 27 |
| comunes | tercia | 27 |
| comunes | visperas1 | 106 |
| santoral | intermedia | 10 |
| santoral | invitatorio | 1 |
| santoral | laudes | 8 |
| santoral | nona | 12 |
| santoral | oficio | 13 |
| santoral | sexta | 3 |
| santoral | tercia | 12 |
| santoral | visperas | 13 |
| santoral | visperas1 | 61 |
| tiempo | intermedia | 62 |
| tiempo | laudes | 2 |
| tiempo | nona | 6 |
| tiempo | oficio | 1 |
| tiempo | sexta | 6 |
| tiempo | tercia | 6 |
| tiempo | visperas | 10 |
| tiempo | visperas1 | 21 |
| tiempo | visperas2 | 58 |

## Sin cotejar, por tipo

Están en horas que la base tiene, pero `comparar_base.py` no compara ese campo o esa opción. Antes de agregarlas hay que ver si la base ya las tiene con otra forma.

| Sección | Tipo | Piezas |
|---|---|---:|
| salterio | versiculo | 112 |
| santoral | responsorio | 101 |
| salterio | oracion | 83 |
| santoral | lectura | 78 |
| santoral | antifona | 68 |
| tiempo | lectura | 67 |
| salterio | himno | 28 |
| completas | versiculo | 26 |
| tiempo | antifona | 26 |
| tiempo | responsorio | 25 |
| completas | texto | 14 |
| completas | antifona | 13 |
| salterio | antifona | 12 |
| santoral | salmo | 12 |
| tiempo | salmo | 11 |
| santoral | versiculo | 9 |
| comunes | versiculo | 9 |
| tiempo | versiculo | 9 |
| tiempo | texto | 9 |
| completas | himno | 7 |
| completas | salmo | 7 |
| santoral | himno | 7 |
| completas | responsorio_breve | 6 |
| santoral | lectura_breve | 5 |
| santoral | texto | 4 |
| santoral | responsorio_breve | 3 |
| santoral | preces | 3 |
| tiempo | responsorio_breve | 1 |

## Sync con error de estructura

| Sección | Tipo | Piezas |
|---|---|---:|
| completas | oracion | 1 |
| salterio | antifona | 9 |
| salterio | rubrica | 9 |
| salterio | salmo | 9 |
| santoral | antifona | 5 |
| santoral | rubrica | 2 |
| tiempo | antifona | 9 |
| tiempo | responsorio | 4 |
| tiempo | salmo | 9 |

## Claves de la base que siguen sin par en el libro

No quiere decir que falten en el libro: son fiestas propias, móviles o nombradas de otro modo. Las piezas del libro que les corresponderían pueden figurar arriba como «falta».

- santoral: 20 — MARÍA, MADRE DE LA IGLESIA, NUESTRA SEÑORA DE ITATÍ, NUESTRA SEÑORA DE LUJÁN, Patrona de la República Argentina, NUESTRA SEÑORA DE LUJÁN, Patrona de la República Argentina · I Vísperas, SANTA MARÍA VIRGEN, MADRE DE LA DIVINA PROVIDENCIA
- tiempo: 11 — Día II de la Octava de la Natividad (C) · I Vísperas, Día III de la Octava de la Natividad (B) · I Vísperas, Día III de la Octava de la Natividad (C) · I Vísperas, Día IV de la Octava de la Natividad (A) · I Vísperas, Día VII de la Octava de la Natividad (B) · I Vísperas, Feria privilegiada de Adviento

## Límites

- El emparejamiento es el de `comparar_base.py` (por semana y día, o por parecido del nombre), más los arreglos de este script. Algunas claves pueden quedar mal emparejadas: en la lista de días que faltan, `jueves-santo-de-la-cena-del-senor`, `jueves-xv-semana-del-tiempo-ordinario` y `10-de-enero-o-jueves-…` hay que mirarlos a mano antes de agregar nada.
- La base no tiene las ferias del 17 al 24 de diciembre: `sync` las juntó en una sola «Feria privilegiada de Adviento». Faltan, entonces, las antífonas «O» y los textos de cada día.
- Una pieza «sin cotejar» puede estar ya en la base con otra forma: es lo primero que hay que revisar.
- Las rúbricas no se cuentan como texto: sirven para escribir las reglas de la app.
