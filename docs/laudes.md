# Laudes — decisiones (10/11/2026)

Orden de trabajo: 1) carga única desde sync a `base/` (salterio de cuatro semanas, propio del tiempo, santoral) con su verificador; 2) armado para cualquier fecha con el calendario ADF y elección de la hora en la portada; 3) piezas en latín y gregoriano con interlineal palabra por palabra; 4) revisión a mano de los propios ADF.

## Partes

- **Invitatorio: solo los domingos.** Primero *Dómine, lábia mea apéries* (gregoriano, `base/gregoriano/domine-labia-mea-aperies.gabc`), luego el Salmo 94 con su antífona, y después el *Deus in adiutórium*. Los demás días, solo el *Deus in adiutórium*.
- **Himno.** Ferias, memorias y fiestas: texto, en español y en latín, sin canto. Domingos y solemnidades: con melodía gregoriana, con la opción de solo texto o español. Falta: una fuente de los textos latinos de los himnos y los GABC de domingos y solemnidades (a veces de la forma extraordinaria, a veces de la ordinaria en los domingos del Tiempo Ordinario).
- **Cántico evangélico (Benedictus):** Neovulgata, en latín, con traducción interlineal.
- **Preces:** flexa (†) en el corte del medio de cada prece (el que trae sync; si no hay, en la invocación clara) y asterisco de metro (*) al final de la prece.
- **Padre nuestro:** *Pater noster* en latín.
- **Conclusión:** *Dóminus nos benedícat*. No hay GABC de un libro: `base/gregoriano/dominus-nos-benedicat.gabc` lleva la melodía del *Noctem quiétam* (mediante sol–fa antes del acento en «deféndat»; final con el acento en la y caída al re en «ætérnam»; ℟ Amen la–la). Aprobada el 10/11/2026.

## Estado

- **Paso 1 hecho (10/11/2026):** `tools/importar/importar_laudes.py` leyó 5152 Laudes de sync (2015–2025) y escribió `base/salterio/laudes.yaml`, `base/tiempo/laudes.yaml` (289 días con propio), `base/santoral/laudes.yaml` (130 celebraciones), `base/himnos/laudes.yaml` (118 himnos), `base/ordinario/laudes.yaml` y 73 salmos y cánticos nuevos. Variantes de la fuente: `base/informes/laudes.md`. `tools/verificar_base.py` comprueba que todos los días del calendario tengan Laudes completas.
- **Pendiente:** IX Domingo del Tiempo Ordinario (30/5/2027): sync no lo trae (antífona del Benedictus y oración).
- **Santoral:** es el de sync; en el paso 2 hay que vincularlo con las celebraciones del calendario ADF (nombres distintos, santos propios de ADF y de Argentina/Paraguay) y completar desde los comunes lo que falte.
- **Paso 2 hecho (10/11/2026):** `src/laudes.js` arma Laudes para cualquier fecha (salterio → tiempo → santoral). Los datos van en `dist/laudes.js` (aparte del HTML; la app los carga al abrir la hora). Partes en latín en `base/gregoriano/laudes.yaml`: invitatorio, Benedictus (Neovulgata, recitado, con interlineal), Pater noster y conclusión. Himnos: por ahora, los de sync en español.
- **Santoral ↔ calendario ADF:** `tools/base_js.py` vincula cada celebración del calendario con su entrada del santoral por fecha y nombre (118 vinculadas). Quedan 44 celebraciones ADF sin propio en la base (lista en `LAUDES.sin_vincular`): esos días la app reza el oficio del día y lo avisa. Fiestas y solemnidades sin salmodia propia toman los salmos del domingo I.
- **Himnos latinos:** texto base, el ePub de Universalis (Liturgia Horarum); cotejo palabra por palabra con GregoBase (Liber Hymnarius); las diferencias se revisan en el libro impreso. Falta el tomo de Pentecostés a Adviento.

## Usos ADF (10/11/2026; valen también para las otras horas)

- **Citas bíblicas** al modo «capítulo: versículos» (Dn 3: 26-27). La base guarda la coma; la app la convierte al mostrar (`cita()` en app.js).
- **Cántico evangélico:** la referencia va al final del renglón del título de la sección, como en la lectura breve. Texto y versículos del Benedictus y del Magníficat: los PDF «NVG» de ADF (`base/gregoriano/laudes.yaml`, `magnificat.yaml`).
- **Comienzo de Laudes:** siempre *Dómine, lábia mea apéries* y después el *Deus in adiutórium*; entre ambos, el invitatorio (antífona y Salmo 94) solo los domingos.
- **Padre nuestro:** la monición (la propia del día) se dice solo en domingos, fiestas y solemnidades. *Pater noster* con asterisco después de «noster»: hasta ahí, normal; desde ahí, negrita. Traducción: literal, palabra por palabra.
- **Preces:** † y * en rojo.
- **Conclusión:** cruz después de «Dóminus» (en la bendición del ministro, después de «Pater,»; «[esté] con vosotros» con corchetes). Opción «Con ministro ordenado»: *Dóminus vobíscum… Benedícat vos* (Graduale Romanum 1974, p. 817: tono A en ferias, memorias y fiestas; tono B en domingos y solemnidades; el libro no trae un tercer tono), seguido de *Ite in pace. ℟. Deo grátias.* (por ahora en texto: falta el GABC).

## Celebraciones propias de ADF (11/11/2026)

- `base/santoral/adf.yaml`: para cada celebración del calendario ADF que la base no trae, de dónde toma los textos hasta tener los propios: `comun` (de `base/comunes/`), `como` (otra celebración de la base) o `pendiente` (oficio propio sin textos). La asignación inicial es automática, por el nombre (`tools/adf_santoral.py`); se corrige a mano en ese archivo.
- `base/comunes/laudes.yaml` y `visperas.yaml`: comunes **provisorios**, deducidos del santoral de sync (`tools/importar/comunes.py`): de cada parte, el texto que más celebraciones de ese común comparten. Hay que cotejarlos con el libro.
- Del común se toman himno, lectura, responsorio, antífona del cántico evangélico y preces; en fiestas y solemnidades, también los salmos si el común los trae. La oración queda la del día (falta la propia) y la app lo avisa.
- Lista de diferencias entre el calendario ADF y el general: `docs/calendario-adf-diferencias.json` (la genera `tools/adf_santoral.py`).

## Calendarios, oraciones e invitatorio gregoriano (11/11/2026)

- **Calendarios.** La app sigue el calendario ADF. Cuando un día tiene variantes, el inicio muestra las siglas en lugar de «Las horas de hoy»: en gris, lo que se está celebrando; encendidas, las otras opciones. Tocar la sigla de otro calendario (ARG, PGY, BUE…) cambia a ese calendario y se recuerda; tocar una memoria libre vale solo para ese día. Si la celebración tiene nota, aparece el signo (!) que la abre.
- Los calendarios locales se cargan en `base/calendario/locales.yaml` (sigla, fecha, celebración, grado y nota); el motor del Ordo recalcula precedencias y I Vísperas. Las siglas y sus nombres están en ese mismo archivo.
- Las memorias libres que la base no trae toman el común que indica el Ordo (`base/santoral/adf.yaml`), con la oración del día.
- **Oraciones antes y después del oficio:** `base/ordinario/oraciones-oficio.yaml` (texto y traducción de ADF, renglón por renglón). Botón discreto al pie del inicio; la preparatoria se ofrece además antes de las I Vísperas del domingo.
- **Invitatorio gregoriano** (domingos del Tiempo Ordinario): antífona «Veníte, exsultémus Dómino» y Salmo 94 (`venite-exsultemus-*.gabc`, clave `invitatorio_per_annum` de `gregoriano/laudes.yaml`). Si se canta, va en gregoriano salvo que se elija «En español»; recitado, va en español.

### Notas y variaciones del Calendario litúrgico ADF (PDF 2026)

- `base/calendario/notas.yaml`: las notas al pie del calendario, unidas a cada celebración del Ordo y con la sigla del calendario al que se refieren (la de san Martín sobre Buenos Aires va como BUE). Se importaron una vez con `tools/importar/notas_calendario.py`; se corrigen ahí. Se omitieron los aniversarios de ordenación de personas y se corrigieron erratas evidentes.
- Grados y fechas del santoral: el Ordo coincide con el PDF en las 258 celebraciones con grado. Lo que el PDF dice solo en notas va en `base/calendario/locales.yaml`: san Martín, Solemnidad en BUE; Roque González y compañeros, Fiesta en PGY. Un calendario local hereda los cambios de su país (CDE de PGY). Si un calendario solo cambia la sigla, no se muestra como variante.
- En el inicio la sigla encendida (roja) es la que se está celebrando.

### Inicio y calendario (11/11/2026, tarde)

- En día ferial con memoria libre, ADF celebra la memoria libre (la del calendario más propio: local, país, ADF, general). Ya no se ofrece la feria.
- Sábados del Tiempo Ordinario sin memoria: opción «Santa María» (Santa María en sábado, común de la Virgen; falta la oración propia).
- Biografías: las del Ordo (columna «biografia» del santoral), con el enlace «Biografía» en la tarjeta del día.
- Lista de horas: la que toca según el reloj (1:30 antes y después de su hora; el Oficio de lectura con Laudes) va resaltada en rojo. Vísperas se llama «I Vísperas» o «II Vísperas» cuando corresponde.
- El inicio no tiene barra superior: los tres puntos van en la fila de la fecha.
- En Completas y en las I Vísperas, la línea del día no repite el nombre de la celebración.

## Comunes y propio del libro (11/11/2026, noche)

- **Comunes** (`base/comunes/laudes|visperas|oficio|intermedia.yaml`): tomados del libro (Liturgia de las Horas, tomo III) con `tools/importar/comunes_libro.py` (lector: `libro_lh.py`). Reemplazan a los provisorios deducidos de sync. Incluyen invitatorio, I Vísperas (`primeras`), Tercia/Sexta/Nona y las oraciones «en su defecto», con N. en lugar del nombre y una indicación de a quién corresponde cada una (un obispo, varios mártires, una virgen…). El común de doctores trae pocas partes: el resto se copió del de pastores.
- La app elige la oración del común según el título de la celebración (papa, obispo, presbítero, virgen, mártir, religioso…, y si es santo o santa, uno o varios) y pone el nombre: «San Blas, obispo y mártir» → «san Blas».
- **Propio del libro** (`base/santoral/libro.yaml`, con `tools/importar/propio_libro.py`): para 77 de las celebraciones que la base no traía, la oración propia y lo que el libro tenga de propio (casi siempre la segunda lectura del Oficio; a veces antífonas, himnos o el oficio entero, como Jesucristo, Sumo y Eterno Sacerdote). Lo propio va encima del común.
- Memorias sin propio: salmos de la feria y lo demás del común. Fiestas y solemnidades: también la salmodia del común (en Laudes, salmos del domingo I con las antífonas del común) y sus I Vísperas.
- **Santa María en sábado**: sus elementos propios del libro (invitatorio, himnos, lectura breve, responsorio, antífona del Benedictus, preces, seis oraciones; en el Oficio, himno y segunda lectura); lo demás, de la feria.
- Tres comunes corregidos según el libro: san Camilo de Lelis y san Jerónimo Emiliani (santos varones), san Efrén (doctores).
