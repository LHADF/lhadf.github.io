# La base de la app frente al libro

Comparación automática entre `base/` —los textos que usa la app, cargados una sola vez del repositorio `sync`— y la extracción del libro impreso (`extraccion/`). La hace `extraccion/comparar_base.py`; el detalle está en `informes/textos.csv` (una fila por texto que no coincide) y en `informes/faltantes.csv`.

Las dos fuentes no están armadas igual, y eso explica buena parte de las diferencias: `sync` guarda **cada día ya resuelto** (el salterio y el propio juntos, con una sola opción elegida), mientras que el libro imprime **solo lo que cambia** y deja varias opciones. Por eso la comparación separa seis resultados:

- **iguales**: el mismo texto.
- **solo en la forma**: tildes, comillas, guiones, mayúsculas, puntuación; las normas de ADF que la base ya aplicó («aleluia» por «Aleluya»); el «Padre nuestro.» con que el libro cierra la monición y la base no copia; y la conclusión de las oraciones, que la base escribe entera y el libro abrevia.
- **cortado distinto**: el mismo texto repartido en otras estrofas o partes (el libro parte varios salmos en I, II y III).
- **la base lo resuelve**: la base trae un texto donde el libro remite al Salterio o a un Común.
- **difieren**: cambian las palabras. Acá está lo que hay que revisar.
- **solo en el libro**: el libro trae algo que la base no tiene.

| Ámbito | Comparados | Iguales | Solo en la forma | Cortado distinto | La base lo resuelve | Difieren | Solo en el libro |
|---|---|---|---|---|---|---|---|
| Salmos y cánticos | 416 | 168 | 47 | 40 | 2 | 136 | 23 |
| Himnos | 247 | 115 | 54 | 16 | 0 | 62 | 0 |
| Completas | 53 | 26 | 10 | 1 | 0 | 16 | 0 |
| Salterio | 1040 | 659 | 171 | 11 | 0 | 199 | 0 |
| Oficios comunes | 361 | 235 | 82 | 5 | 15 | 23 | 1 |
| Propio de los santos | 1961 | 945 | 248 | 15 | 149 | 604 | 0 |
| Propio del tiempo | 5190 | 2478 | 1142 | 31 | 432 | 1098 | 9 |
| **Total** | **9268** | **4626** | **1754** | **119** | **598** | **2138** | **33** |

Detalle de «solo en la forma»: 657 tildes, comillas, guiones, mayúsculas o puntuación, 586 normas de ADF que la base ya aplicó («aleluia»), 341 la base no copia el «Padre nuestro.» final, 167 la conclusión de la oración, entera o abreviada, 3 los mismos textos en otro orden.

Además, en 451 casos la base trae una hora entera que el libro no imprime en ese lugar porque la toma del Salterio o de un Común: Propio del tiempo tercia (94), Propio del tiempo nona (86), Propio del tiempo sexta (84), Propio de los santos sexta (49), Propio de los santos nona (47), Propio de los santos laudes (35), Propio de los santos visperas (32), Propio de los santos tercia (20).

## Qué cubre cada fuente

| Sección del libro | Extraída | En la base | Archivos de la base |
|---|---|---|---|
| Ordinario | sí | sí | ordinario/laudes, ordinario/oficio, ordinario/intermedia, ordinario/antifonas-marianas, ordinario/oraciones-oficio |
| Salterio | sí | sí | salterio/laudes, salterio/visperas, salterio/oficio, salterio/tercia, salterio/sexta, salterio/nona |
| Completas | sí | sí | salterio/completas, ordinario/completas, tiempo/completas-triduo-octava |
| Propio del tiempo | sí | sí | tiempo/laudes, tiempo/visperas, tiempo/oficio, tiempo/tercia, tiempo/sexta, tiempo/nona, tiempo/intermedia |
| Propio de los santos | sí | sí | santoral/laudes, santoral/visperas, santoral/oficio, santoral/tercia, santoral/sexta, santoral/nona, santoral/intermedia, santoral/libro, santoral/adf |
| Oficios comunes | sí | sí | comunes/laudes, comunes/visperas, comunes/oficio, comunes/intermedia |
| Oficio de difuntos | sí | no |  |
| Apéndices | sí | no |  |
| Salmos y cánticos | sí | sí | salmos/ (313 archivos) |
| Himnos | sí | sí | himnos/ (7 archivos) |

## Dónde difieren

### Salmos y cánticos (136)

Por campo: texto (93), subtitulo (43).

- **salmo-118-105-112 · subtitulo**
  - base: HIMNO A LA LEY DIVINA
  - libro: XIV (Nun)
- **salmo-118-145-152 · subtitulo**
  - base: TE INVOCO DE TODO CORAZÓN
  - libro: XIX (KOF)
- **cantico-1cro-29-10-13 = cantico-i-1-cro-29-10-13 · subtitulo**
  - base: SÓLO A DIOS HONOR Y GLORIA
  - libro: BENDITO ERES, SEÑOR
- **salmo-146 · subtitulo**
  - base: PODER Y BONDAD DEL SEÑOR
  - libro: PODER Y BONDAD DE DIOS
- **salmo-79 · subtitulo**
  - base: VEN A VISITAR TU VIÑA
  - libro: VEN, SEÑOR, A VISITAR TU VIÑA
- **salmo-50 · subtitulo**
  - base: CONFESIÓN DEL PECADOR ARREPENTIDO
  - libro: MISERICORDIA, DIOS MÍO
- **cantico-ef-1-3-10 · subtitulo**
  - base: EL PLAN DIVINO DE SALVACIÓN
  - libro: EL PLAN DIVINO DE LA SALVACIÓN
- **cantico-simeon = cantico-lc-2-29-32 · subtitulo**
  - base: Lc 2, 29-32
  - libro: CRISTO, LUZ DE LAS NACIONES Y GLORIA DE ISRAEL
- **salmo-2 · subtitulo**
  - base: EL MESÍAS, REY VENCEDOR
  - libro: ¿POR QUÉ SE AMOTINAN LAS NACIONES?
- **salmo-112 · subtitulo**
  - base: ALABADO SEA EL NOMBRE DEL SEÑOR
  - libro: ALABADO SEA EL NOMBRE DE DIOS
- … y 126 más en `informes/textos.csv`.

### Himnos (62)

Por campo: estrofas (62).

- **Ayer, en leve centella · estrofas**
  - base: Ayer, en leve centella,
te vio Moisés sobre el monte;
hoy no basta el horizonte
para contener tu estrella. ¶ Los magos preguntan; y ella
de un Dios infante responde
que en duras pajas se acuesta
y más se nos manifiesta
cuanto más hondo se esconde. Amén.
  - libro: Ayer, en leve centella,
te vio Moisés sobre el monte;
hoy no basta el horizonte
para contener tu estrella. ¶ Los magos preguntan; y ella
de un Dios infante responde
que en duras pajas se acuesta
y más se nos manifiesta
cuando más hondo se esconde. Amén.
- **Lucero del alba · estrofas**
  - base: Lucero del alba,
aurora estremecida,
luz de mi alma,
Santa María. ¶ Hija del Padre,
doncella en gracia concebida,
virgen y madre,
Santa María. ¶ Flor del Espíritu,
ave, blancura, caricia,
madre del Hijo,
Santa María. ¶ Llena de ternura,
bendita entre las bendi
  - libro: Lucero del alba,
luz de mi alma,
santa María. ¶ Virgen y Madre,
hija del Padre,
santa María. ¶ Flor del Espíritu,
Madre del Hijo,
santa María. ¶ Amor maternal
del Cristo total,
santa María. Amén.
- **Quien entrega su vida por amor · estrofas**
  - base: Quien entrega su vida por amor
la gana para siempre
dice el Señor. ¶ Aquí el bautismo proclama
su voz de gloria y de muerte.
Aquí la unción se hace fuerte
contra el cuchillo y la llama.
Mirad cómo se derrama
mi sangre por cada herida.
Si Cristo fue mi comida,

  - libro: "Quien entrega su vida por amor,
la gana para siempre",
dice el Señor. ¶ Aquí el bautismo proclama
su voz de gloria y de muerte.
Aquí la unción se hace fuerte
contra el cuchillo y la llama.
Mirad cómo se derrama
mi sangre por cada herida.
Si Cristo fue mi comi
- **Hoy grande gozo en el cielo · estrofas**
  - base: Hoy grande gozo en el cielo
todos tienen,
porque en un barrio del suelo
nace Dios.
¡Qué gran gozo y alegría
tengo yo! ¶ Mas no nace solamente
en Belén,
nace donde hay un caliente
corazón.
¡Qué gran gozo y alegría
tengo yo! ¶ Nace en mí, nace en cualquiera
si h
  - libro: Hoy grande gozo en el cielo
todos hacen,
porque en un barrio del suelo
nace Dios.
¡Qué gran gozo y alegría
tengo yo! ¶ Mas no nace solamente
en Belén,
nace donde hay un caliente
corazón.
¡Qué gran gozo y alegría
tengo yo! ¶ Nace en mí, nace en cualquiera
si ha
- **Aplaudan a esta Rosa · estrofas**
  - base: Aplaudan a esta Rosa
las rosas de la tierra;
resuene su alabanza
del sol a las estrellas. ¶ Una Rosa de gracia
en un rosal de penas;
por las culpas del mundo
hirió su carne tierna. ¶ Roja Rosa del cielo,
virgen Rosa limeña:
un puñado de gozo
y un haz de penite
  - libro: Aplaudan a esta Rosa
las rosas de la tierra;
resuene su alabanza
del sol a las estrellas. ¶ Una Rosa de gracia
en un rosal de penas;
por las culpas del mundo
hirió su carne tierna. ¶ Roja Rosa del cielo,
virgen Rosa limeña:
un puñado de gozo
un haz de penitenc
- **Alegría de nieve · estrofas**
  - base: Alegría de nieve
por los caminos.
Todo espera la gracia
del Bien Nacido. ¶ Miserables los hombres,
dura la tierra.
Cuanta más nieve cae,
más cielo cerca. ¶ La tierra tan dormida
ya se despierta.
Y hasta el hombre más muerto
se despereza. ¶ Ya los montes se all
  - libro: Alegría de nieve
por los caminos.
Todo espera la gracia
del Bien Nacido. ¶ En desgracia los hombres,
dura la tierra.
Cuanta más nieve cae,
más cielo cerca. ¶ La tierra tan dormida
ya se despierta.
Y hasta el hombre más muerto
se despereza. ¶ Ya los montes se a
- **Hora de la tarde · estrofas**
  - base: Hora de la tarde,
fin de las labores.
Amo de las viñas,
paga los trabajos
de tus viñadores. ¶ Al romper el día
nos apalabraste.
Cuidamos tu viña
del alba a la tarde. ¶ Ahora que nos pagas,
nos lo das de balde,
que a jornal de gloria
no hay trabajo grande. ¶ Da
  - libro: Hora de la tarde,
fin de las labores.
Amo de las viñas,
paga los trabajos de tus viñadores. ¶ Al romper el día,
nos apalabraste.
Cuidamos tu viña
del alba a la tarde.
Ahora que nos pagas,
nos lo das de balde,
que a jornal de gloria
no hay trabajo grande. ¶ Das
- **A la orilla del Jordán · estrofas**
  - base: A la orilla del Jordán,
descalza el alma y los pies,
bajan buscando pureza
doce tribus de Israel. ¶ Piensan que a la puerta está
el Mesías del Señor
y que para recibirle
gran limpieza es menester. ¶ Bajan hombres y mujeres,
pobres y ricos también,
y Juan, sobr
  - libro: A la orilla del Jordán,
descalza el alma y los pies,
bajan buscando pureza
doce tribus de Israel. ¶ Piensan que a la puerta está
el Mesías del Señor
y que para recibirle
gran limpieza es menester. ¶ Bajan hombres y mujeres,
pobres y ricos también,
y Juan, sobr
- **Santa unidad y Trinidad beata · estrofas**
  - base: Santa unidad y Trinidad beata:
con los destellos de tu brillo eterno,
infunde amor en nuestros corazones,
mientras se va alejando el sol de fuego. ¶ Por la mañana te cantamos loas
y por la tarde te elevamos ruegos,
pidiéndote que estemos algún día
entre los qu
  - libro: Santa Unidad y Trinidad beata:
con los destellos de tu brillo eterno,
infunde amor en nuestros corazones,
mientras se va alejando el sol de fuego. ¶ Por la mañana te cantamos loas
y por la tarde te elevamos ruegos,
pidiéndote que estemos algún día
entre los qu
- **Asidos de tu falda, con los ojos · estrofas**
  - base: Asidos de tu falda, con los ojos
agrandados de asombro, con las manos
apretadas de miedos y de enojos... ¶ ¡Pobres manos vacías de tus hijos!
Ojos que alzan del suelo su vergüenza
para quedar en tu mirada fijos; ¶ ojos que te confían nuestros sueños,
manos que
  - libro: Asidos de tu falda, con los ojos
agrandados de asombro, con las manos
apretadas de miedos y de enojos... ¶ ¡Abres manos vacías de tus hijos!
Ojos que alzan del suelo su vergüenza
para quedar en tu mirada fijos; ¶ ojos que te confían nuestros sueños,
manos que 
- … y 52 más en `informes/textos.csv`.

### Completas (16)

Por campo: oración (6), lectura (5), lectura: cita (3), salmodia_pascua: antífonas (1), responsorio breve (1).

- **completas/jueves · lectura: cita**
  - base: 1Ts 5, 23
  - libro: 1 Ts 5, 23
- **completas/martes · lectura: cita**
  - base: 1Pe 5, 8-9
  - libro: 1 Pe 5, 8-9
- **completas/lunes · lectura: cita**
  - base: 1Ts 5, 9-10
  - libro: 1 Ts 5, 9-10
- **completas/sabado · salmodia_pascua: antífonas**
  - base: Aleluia, aleluia, aleluia.
  - libro: Aleluya, aleluya, aleluya. ¶ Aleluya, aleluya, aleluya.
- **completas/miercoles · lectura**
  - base: No lleguéis a pecar; que la puesta del sol no os sorprenda en vuestro enojo. No dejéis lugar al diablo.
  - libro: No lleguéis a pecar; que la puesta del sol no os sorprenda en vuestro enojo. No dejéis resquicio al diablo.
- **completas/martes · lectura**
  - base: Sed sobrios, estad despiertos: vuestro enemigo, el diablo, como león rugiente, ronda buscando a quien devorar; resistidle, firmes en la fe.
  - libro: Sed sobrios, estad alerta, que vuestro enemigo, el diablo, como león rugiente, ronda buscando a quien devorar; resistidle firmes en la fe.
- **completas/lunes · lectura**
  - base: Dios nos ha puesto para obtener la salvación por nuestro Señor Jesucristo, que murió por nosotros, para que, velando o durmiendo, vivamos junto con él.
  - libro: Dios nos ha destinado a obtener la salvación por medio de nuestro Señor Jesucristo; él murió por nosotros, para que, despiertos o dormidos, vivamos con él.
- **completas/jueves · lectura**
  - base: Que el mismo Dios de la paz os consagre totalmente y que todo vuestro ser, alma y cuerpo, sea custodiado sin reproche hasta la Parusía de nuestro Señor Jesucristo.
  - libro: Que el mismo Dios de la paz os consagre totalmente, y que todo vuestro espíritu, alma y cuerpo, sea custodiado sin reproche hasta la venida de nuestro Señor Jesucristo.
- **ordinario · responsorio breve**
  - base: En tus manos, Señor, encomiendo mi espíritu. ¶ En tus manos, Señor, encomiendo mi espíritu. ¶ Tú, el Dios leal, nos librarás. ¶ Te encomiendo mi espíritu. ¶ Gloria al Padre, y al Hijo, y al Espíritu Santo. ¶ En tus manos, Señor, encomiendo mi espíritu.
  - libro: A tus manos, Señor, encomiendo mi espíritu. ¶ A tus manos, Señor, encomiendo mi espíritu. ¶ Tú, el Dios leal, nos librarás. ¶ Encomiendo mi espíritu.
- **completas/domingo · lectura**
  - base: Verán el rostro del Señor, y tendrán su nombre en la frente. Y no habrá más noche, y no necesitarán luz de lámpara ni de sol, porque el Señor Dios alumbrará sobre ellos, y reinarán por los siglos de los siglos.
  - libro: Verán al Señor cara a cara y llevarán su nombre en la frente. Ya no habrá más noche, ni necesitarán luz de lámpara o del sol, porque el Señor Dios irradiará luz sobre ellos, y reinarán por los siglos de los siglos.
- … y 6 más en `informes/textos.csv`.

### Salterio (199)

Por campo: salmodia: salmos (44), salmodia: antífonas (39), lectura (24), preces: intenciones (23), himno (título) (15), lectura: cita (10), oración (9), monición del Padre nuestro (7), responsorio breve (7), preces: introducción (6), preces: respuesta (6), antífona del Magníficat (4), versículo (3), antífona del invitatorio (1), antífona del Benedictus (1).

- **semana 3/sabado/tercia · lectura: cita**
  - base: 1S 15, 22
  - libro: Is 15, 22
- **semana 2/miercoles/visperas · lectura: cita**
  - base: 1Pe 5, 5b-7
  - libro: 1 Pe 5, 5-7
- **semana 3/miercoles/visperas · lectura: cita**
  - base: Ef 3, 20-21
  - libro: Ef 3, 29-21
- **semana 1/sabado/tercia · lectura: cita**
  - base: 1R 8, 60-61
  - libro: Jr 8, 60-61
- **semana 2/sabado/sexta · lectura: cita**
  - base: 1R 2, 2b-3
  - libro: 1 Re 5, 16-17
- **semana 4/sabado/tercia · lectura: cita**
  - base: Dn 6, 26b-27
  - libro: Dn 6, 26b-97
- **semana 4/viernes/laudes · lectura: cita**
  - base: Ga 2, 19b-20
  - libro: Gal 2, 19b-20
- **semana 4/lunes/visperas · lectura: cita**
  - base: 1Ts 3, 12-13
  - libro: 1 Tes 3, 12-13
- **semana 3/viernes/sexta · lectura: cita**
  - base: Rm 3, 21-22a
  - libro: Rm 3, 21-2-2,1
- **semana 3/viernes/laudes · lectura: cita**
  - base: 2Co 12, 9b-10
  - libro: 2 Cor 12, 9b-10
- … y 189 más en `informes/textos.csv`.

### Oficios comunes (23)

Por campo: salmodia: salmos (6), salmodia: antífonas (4), himno (título) (3), oración 1 (2), preces: intenciones (2), antífona del Benedictus (2), antífona del Magníficat (2), lectura (1), responsorio breve (1).

- **doctores/oficio · himno (título)**
  - base: vosotros-sois-la-luz-del-mundo
  - libro: vosotros-sois-luz-del-mundo
- **varios-martires/oficio · salmodia: salmos**
  - base: salmo-2 ¶ salmo-32-i ¶ salmo-32-ii
  - libro: salmo-32 ¶ salmo-32 ¶ salmo-2
- **santas-mujeres/visperas · himno (título)**
  - base: finisimo-fue-el-lino-con-que-ella
  - libro: finisimo-fue-el-lino-con-que-ella-2
- **virgenes/oficio · salmodia: salmos**
  - base: salmo-18-a ¶ salmo-44-i ¶ salmo-44-ii
  - libro: salmo-18-a ¶ salmo-44 ¶ salmo-44
- **santas-mujeres/oficio · salmodia: salmos**
  - base: salmo-18-a ¶ salmo-44-i ¶ salmo-44-ii
  - libro: salmo-18-a ¶ salmo-44 ¶ salmo-44
- **pastores/oficio · salmodia: salmos**
  - base: salmo-20-2-8-14 ¶ salmo-91-i ¶ salmo-91-ii
  - libro: salmo-20-2-8-14 ¶ salmo-91 ¶ salmo-91
- **santos-varones/oficio · salmodia: salmos**
  - base: salmo-20-2-8-14 ¶ salmo-91-i ¶ salmo-91-ii
  - libro: salmo-20-2-8-14 ¶ salmo-91 ¶ salmo-91
- **un-martir/oficio · himno (título)**
  - base: pleyade-santa-y-noble-de-martires-insignes
  - libro: pleyade-santa-y-noble-de-martires-insignes-2
- **dedicacion/visperas · salmodia: salmos**
  - base: salmo-45 ¶ salmo-121 ¶ cantico-ap-19-1-2-5-7
  - libro: salmo-45 ¶ salmo-121 ¶ cantico-cf-ap-19-1-7 ¶ cantico-cf-ap-19-1-7 ¶ cantico-ap-15-3-4
- **santas-mujeres/visperas · responsorio breve**
  - base: Dios la eligió y la predestinó. ¶ Dios la eligió y la predestinó. ¶ Le hizo morar en su templo santo. ¶ Y la predestinó.
  - libro: Dios la eligió y la predestinó. ¶ Dios la eligió y la predestinó. ¶ La hizo morar en su templo santo. ¶ Y la predestinó.
- … y 13 más en `informes/textos.csv`.

### Propio de los santos (604)

Por campo: oración (180), lectura (64), salmodia: antífonas (53), preces: intenciones (40), antífona del Benedictus (39), himno (título) (37), antífona del Magníficat (32), versículo (25), antífona (25), preces: introducción (19), preces: respuesta (19), responsorio breve (19), monición del Padre nuestro (18), lectura: cita (15), antífona del invitatorio (13), salmodia: salmos (4), grado (2).

- **SAN FELIPE DE JESÚS, protomártir mexicano/laudes · grado**
  - base: Fiesta
  - libro: Memoria
- **SAN FELIPE DE JESÚS, protomártir mexicano/oficio · grado**
  - base: Fiesta
  - libro: Memoria
- **LA NATIVIDAD DE LA SANTÍSIMA VIRGEN MARÍA/tercia · lectura: cita**
  - base: Ct 6, 9
  - libro: Ct 6, 10
- **SANTA TERESA DE JESÚS, virgen y doctora de la Iglesia/laudes · lectura: cita**
  - base: Ct 8, 7
  - libro: Sb 7, 7-8
- **NUESTRA SEÑORA DEL PILAR/visperas · lectura: cita**
  - base: Ga 4, 4-5
  - libro: Ga 4, 4-7
- **SAN MARTÍN DE TOURS, obispo/visperas · lectura: cita**
  - base: 1Pe 5, 1-4
  - libro: 1 P 5, 1-4
- **NUESTRA SEÑORA DEL ROSARIO/laudes · lectura: cita**
  - base: Is 61,10
  - libro: Cf. Is 61, 10
- **NUESTRA SEÑORA DEL PILAR/laudes · lectura: cita**
  - base: Is 61,10
  - libro: 2 Cro 7, 15-16
- **LA ANUNCIACIÓN DEL SEÑOR · I Vísperas/visperas · lectura: cita**
  - base: 1Jn 1, 1-3a
  - libro: 1 Jn 1, 1-2
- **LA ANUNCIACIÓN DEL SEÑOR/visperas · lectura: cita**
  - base: 1Jn 1, 1-3a
  - libro: 1 Jn 1, 1-2
- … y 594 más en `informes/textos.csv`.

### Propio del tiempo (1098)

Por campo: oración (517), lectura (98), lectura: cita (84), himno (título) (65), antífona del Magníficat (56), preces: intenciones (48), versículo (41), antífona del Benedictus (40), preces: introducción (37), monición del Padre nuestro (32), preces: respuesta (24), antífona del invitatorio (16), salmodia: salmos (13), responsorio breve (12), salmodia: antífonas (11), antífona (4).

- **Jueves de la I semana de Adviento/nona · lectura: cita**
  - base: Ml 4, 2
  - libro: Mi 4, 2
- **II Domingo después de Navidad (A)/sexta · lectura: cita**
  - base: 1Jn 4, 9
  - libro: Jn 4, 9
- **II Domingo después de Navidad (B)/sexta · lectura: cita**
  - base: 1Jn 4, 9
  - libro: Jn 4, 9
- **II Domingo después de Navidad (C)/sexta · lectura: cita**
  - base: 1Jn 4, 9
  - libro: Jn 4, 9
- **Viernes después de la Epifanía/nona · lectura: cita**
  - base: Is 65, 1
  - libro: St 1, 27
- **Jueves después de la Epifanía/tercia · lectura: cita**
  - base: Dt 4, 7
  - libro: Is 55, 6-7
- **Viernes después de la Epifanía/tercia · lectura: cita**
  - base: Is 45, 13
  - libro: Is 55, 3
- **VII Domingo de Pascua (A)/nona · lectura: cita**
  - base: Col 3, 1-2
  - libro: Rm 6, 4
- **VII Domingo de Pascua (B)/nona · lectura: cita**
  - base: Col 3, 1-2
  - libro: Rm 6, 4
- **VII Domingo de Pascua (C)/nona · lectura: cita**
  - base: Col 3, 1-2
  - libro: Rm 6, 4
- … y 1088 más en `informes/textos.csv`.

## Lo que tiene una fuente y no la otra

| Ámbito | Dónde | Cuántos |
|---|---|--:|
| Oficios comunes | solo en el libro | 3 |
| Himnos | solo en el libro | 224 |
| Himnos | solo en la base | 132 |
| Salmos y cánticos | solo en el libro | 80 |
| Salmos y cánticos | solo en la base | 105 |
| Propio de los santos | no se pudo emparejar | 66 |
| Propio del tiempo | no se pudo emparejar | 65 |

El detalle está en `informes/faltantes.csv`. «No se pudo emparejar» son claves de la base que no encontraron su celebración en el libro (fiestas móviles, nombres muy distintos): no quiere decir que falten.

