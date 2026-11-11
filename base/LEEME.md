# Base de textos de la LH ADF

Textos de la Liturgia de las Horas en español, ordenados como en los libros. Se cargaron una sola vez desde
el repositorio `sync` (2015–2026) con `tools/importar/`; desde entonces **la base es la fuente**: las
correcciones se hacen acá y la app no depende de `sync`. El importador no se vuelve a correr: pisaría las correcciones
(por ejemplo, las Completas del Domingo de Pascua, agregadas a mano).

Cada archivo es texto YAML y se puede editar directamente en GitHub. Reglas de escritura:

- Los textos de varios renglones van después de `|-`, con sangría de dos espacios. Cada renglón del texto es un renglón del archivo.
- Las estrofas de los salmos e himnos son elementos de una lista (`- |-`).
- Versículo y respuesta: `- V: …` y `- R: …`.
- Si un texto empieza con comillas, lleva dos puntos seguidos de espacio («: ») o empieza con un signo raro, conviene encerrarlo entre comillas simples `'…'`.
- Al publicar, `tools/verificar_base.py` revisa que no falte nada y que cada salmo citado exista. Si algo está mal, la publicación se detiene y dice qué arreglar.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `ordinario/` | Lo que no cambia con el día: invocación, examen, responsorio, cántico evangélico, conclusión, antífonas finales de la Virgen |
| `salterio/` | El salterio de cada hora. Completas: un juego por día de la semana. Laudes: las cuatro semanas (`semana_1`…`semana_4`, de domingo a sábado) |
| `tiempo/` | Propio del tiempo. Completas: Triduo pascual y Octava de Pascua. Laudes: por feria, con el nombre del Ordo (en los domingos, `(A)`, `(B)` o `(C)` cuando cambia con el ciclo); solo lo que cambia respecto del salterio |
| `santoral/` | Laudes de las celebraciones, por nombre (calendario de `sync`, a revisar con el ADF): solo lo que cambia respecto del salterio y del tiempo; `fecha: variable` = movible |
| `himnos/` | Himnos por hora y por tiempo; en cada tiempo se puede elegir cualquiera de la lista |
| `salmos/` | Cada salmo y cántico una sola vez, por su clave (`salmo-30-2-6` = Salmo 30, 2-6) |
| `gregoriano/` | Partituras GABC y cuándo va cada una (`completas.yaml`): invocación solemne/festiva/ferial, Salva nos y Nunc dimittis, Noctem quietam; traducción interlineal propia, literal y palabra por palabra (no la del sync, que sirve solo para lo que se canta en español); tono de los salmos |
| `informes/` | Lo que encontró la carga: versiones distintas de un mismo texto en `sync` y la verificación |

Laudes y Vísperas: cargadas y armadas en la app (11/2026); falta revisar los propios ADF (ver `docs/laudes.md` y `docs/visperas.md`). Faltan todavía: Oficio de lectura, hora intermedia y lo propio de ADF.

## Reglas de Completas (las aplica la app)

- **Juego de salmos:** el del día de la semana. En la noche del sábado y la víspera de una solemnidad, el del sábado
  (después de las I Vísperas); el domingo y el día de una solemnidad, el del domingo (después de las II Vísperas).
- **Oración:** la del juego; en las solemnidades, `oracion_solemnidad` («Visita, Señor, esta habitación…»).
- **Tiempo pascual:** `salmodia_pascua`, responsorio y antífona del cántico con aleluya, antífona «Reina del cielo».
- **Triduo y Octava de Pascua:** todo lo de `tiempo/completas-triduo-octava.yaml`, día por día. En la Octava se alternan los juegos del sábado y del domingo.
- **Aleluia** (así, con i, en español; nunca «aleluya») después del Gloria de la invocación: siempre, salvo en Cuaresma y el Triduo, en que va «Laus tibi, Christe, Rex ætérnæ glóriæ» (texto ADF) con la melodía del tono del día.
- **Octava de Navidad:** se alternan los juegos del sábado y del domingo, con la oración de las solemnidades.
- **Himno:** primera opción, *Te lucis ante términum* en gregoriano; después, los himnos en español del tiempo. Domingos y
  solemnidades: siempre abre en el Te lucis. Los demás días: el primer himno en español del tiempo, o el último elegido.
- **Lectura breve:** ℟. *Deo grátias*.
- **Cantado o recitado:** un solo botón al comienzo de la hora decide todas las piezas gregorianas (invocación, himno *Te lucis*, responsorio, cántico evangélico con su antífona, conclusión y antífona final). Recitado: el mismo texto latino con su traducción literal debajo; el responsorio recitado va en español (cantado: *In manus tuas*, fuera de Pascua). La elección se recuerda.
- **Antífona final de la Virgen:** solemne en domingos y solemnidades (y sus I Vísperas, Triduo y Octavas); simple los demás días.
  Adviento y Navidad: *Alma Redemptóris*; de la Candelaria (2 de febrero) al fin de Cuaresma: *Ave Regína cælórum*;
  Pascua: *Regína cæli* (sin versículo); Tiempo Ordinario: *Salve Regína*, con *Sub tuum præsídium* como opción en ferias, memorias
  y fiestas (siempre abre en la Salve); Asunción: *Ave Regína cælórum*, solemne o simple. Triduo: *Ave Regína cælórum*, simple o solemne
  (`antifona_final` en `tiempo/completas-triduo-octava.yaml`; ahí están las fuentes). Desde el Domingo de Pascua, *Regína cæli*.
- **Lo que responde la asamblea va en negrita:** en las partituras (desde el ℟ de la invocación y de la conclusión, desde el asterisco
  en las antífonas, las repeticiones del responsorio), la repetición del Salva nos (toda, sin asterisco), *Deo grátias*, los Amén
  que responden a una oración, el *Yo confieso* y el *Confíteor*. En los GABC se marca con `<b>…</b>` sílaba por sílaba;
  `negrita()` de `tools/normalizar_gabc.py` lo hace.
- **Examen de conciencia:** cuatro fórmulas a elegir (*Yo confieso*, otras dos de la Liturgia de las Horas y el *Confíteor* latino con su
  traducción); la elección se recuerda.
- **Salmos en español:** sin partitura y sin pautas, con * y †. Sus antífonas, en negrita (las dice toda la asamblea).
- **Nunc dimittis:** desde el 2.º versículo, marcas escritas a mano como en el libro de Completas ADF (`**negrita**` acento, `_cursiva_` preparación).
- **Cántico evangélico:** primer versículo del Nunc dimittis en partitura; el resto pautado en latín (tono 3 a), con traducción.
- **GABC nuevos:** `python3 tools/normalizar_gabc.py ORIGEN.gabc destino.gabc` pasa el latín a i, æ y œ y avisa las palabras
  de tres sílabas o más sin tilde (hay que agregarla a mano). Los cortes de renglón forzados se marcan con `(Z)`.
- **Invocación en gregoriano:** tono solemne los domingos y solemnidades (y sus I Vísperas), el Triduo y las Octavas; tono festivo en las fiestas; tono ferial en ferias y memorias.
- **Himnos:** Tiempo Ordinario, Adviento y Navidad, Cuaresma (y Triduo), Pascua: cada uno con su lista.
