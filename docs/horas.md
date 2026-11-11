# Oficio de lectura y Hora intermedia (Tercia, Sexta, Nona)

## Fuente y base

- Cargadas una sola vez desde sync con `tools/importar/importar_horas.py` (parser: `horas_sync.py`). Como en Laudes, cada parte se reparte en tres capas: `base/salterio/` (cuatro semanas, de las ferias del Tiempo Ordinario), `base/tiempo/` (por feria; en domingo, con ciclo A/B/C) y `base/santoral/` (por celebración, solo lo que cambia). Para cada texto quedó la versión más frecuente; las demás, en `base/informes/`.
- Oficio de lectura: `base/{salterio,tiempo,santoral}/oficio.yaml`, himnos en `base/himnos/oficio.yaml`, Te Deum en `base/ordinario/oficio.yaml`. Las lecturas, sus responsorios y la oración nunca van en el salterio (cambian cada semana). Ciclo de lecturas: el de un año de sync (no el bienal del libro).
- Hora intermedia: la salmodia del día es una para las tres horas (`base/*/intermedia.yaml`); himno, antífona propia, lectura breve, versículo y oración, por hora (`base/*/tercia|sexta|nona.yaml`). La salmodia complementaria (salmos graduales) está en `base/ordinario/intermedia.yaml`.
- `tools/base_js.py` las pasa a `src/carga/oficio.js` e `intermedia.js` (se cargan al abrir la hora); `src/horas.js` las arma.

## Decisiones

- **Invocación:** «Deus in adiutórium» con el tono del día (solemne, festivo, ferial; «Laus tibi, Christe» en Cuaresma). Conclusión: «Benedicámus Dómino» / «Deo grátias».
- **Te Deum:** domingos fuera de Cuaresma, solemnidades, fiestas y octavas de Navidad y de Pascua.
- **Fiestas y solemnidades sin salmodia propia:** en el Oficio, la del domingo de la I semana.
- **Hora intermedia:** se puede elegir la salmodia complementaria (para quien reza más de una hora); en las solemnidades que no caen en domingo va siempre.
- **Memorias:** la Hora intermedia y el Oficio se toman de la feria; falta en la base la oración propia de muchas (la app lo avisa).
- **Oficio unido a Laudes** («Seguir con Laudes»): el Oficio pasa a ser la primera hora del día y empieza como Laudes (Dómine, lábia mea e invitatorio); después de las lecturas (y del Te Deum) siguen las Laudes desde la salmodia, sin su invocación ni su himno. El Oficio no tiene oración ni conclusión propias.

## Pendiente

- Comunes para las celebraciones propias de ADF (como en Laudes y Vísperas): hoy toman el oficio del día.
- Faltan en la base: el Oficio del IX Domingo del T. O. (lecturas; la oración ya está) y la segunda lectura del jueves de la semana XXXIII.
- Himnos latinos de las horas menores y Te Deum en gregoriano.
