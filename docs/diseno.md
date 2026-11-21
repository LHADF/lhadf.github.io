# Reglas de diseño de Cervus

Cervus (antes Septies) es app hermana del Cantoral: comparte su sistema visual y sus gestos. Las reglas de **ortotipografía son innegociables**; las demás se aplican en la medida en que la app las necesite.

## Ortotipografía

- **En rojo:** rúbricas (además en cursiva), la letra capital inicial del gregoriano y el número de modo, los números de estrofa de los himnos, ℣, ℟, asterisco y cruz.
- **Capitular** (21/11/2026): también en las lecturas breves, los himnos en español y los cánticos evangélicos (en estos, como la del gregoriano): la primera letra, grande y roja, a lo alto de dos renglones. No va si el texto empieza con ¡ o ¿ (ni con otro signo).
- **Renglón quebrado por falta de ancho** (pantalla angosta o letra grande): lo que baja va más adentro que el renglón de la cadencia, como con dos sangrías (2,2 em; el renglón de la cadencia, 1,1 em). Sin guion ni otra marca. Vale para salmos, cánticos e himnos. El tercer renglón de una estrofa sin flexa cuyo primero termina en «:» va igual de adentro (`.v .h3`, CRU 20/11/2026).
- **Partituras de himnos:** cada estrofa y el Amén empiezan renglón nuevo; el anterior termina con el custos de la nota siguiente y el pentagrama vacío hasta el final (en el GABC, `(::Z)`).
- **Glifos propios** (fuente «Cantoral Signos»): ℣ y ℟ con trazo diagonal, cruz patada (✠) y asterisco de cinco pétalos.
- **Latín:** *i* en lugar de *j*; ligaduras æ/œ; tildes de acento. Source Serif 4 no trae «ǽ» ni «Ǽ»: van en `src/assets/ae.css` (familia propia «Septies AE», nunca «Cantoral Signos»), armadas con la «æ» y la tilde de la misma fuente (`tools/fuente_ae.py`), para que no se vean más altas.
- **Español: «aleluia», nunca «aleluya»** (para que no se pronuncie «ya»), también en la traducción del latín. La base ya está así y la prueba lo verifica.
- **Sinalefas** (21/11/2026): en los himnos en español, «‿» entre las palabras que se unen en una sílaba («descalza‿el alma‿y los pies»). Están en la base (`base/himnos/`, marcadas una vez con `tools/sinalefas.py`; un archivo ya marcado no se vuelve a tocar: las correcciones, a mano en la base); la app no muestra el arco: pone en cursiva la vocal final que se une a la palabra siguiente («descalz*a* el alm*a* y los pies», `.sin`; 21/11/2026). No se marcan donde la medida del verso pide hiato (lista en `base/informes/sinalefas.md`).
- **Himnos:** estrofas numeradas «1.», «2.», con línea en blanco entre estrofas. En un himno con estrofas numeradas, el bloque sin número es el estribillo: cursiva y con ℟. Himno sin ninguna estrofa numerada: texto normal, sin cursiva y sin ℟.
- **Polifonías:** una frase por línea, con traducción interlineal. Indicaciones entre corchetes en el original ([Coro]) y en rojo en la app.

## Traducción

- **Siempre interlineal** y en **verde** (`--glosa`).
- **Literal, palabra por palabra**, bajo cada palabra latina; por frases o con otro orden solo cuando ir una por una confundiría. Es una traducción propia, no el español de la Liturgia de las Horas.
- **El latín no se toca:** corre con espacios regulares; la traducción se acomoda. Cada traducción arranca bajo su palabra latina; si se encima con la de al lado, las del renglón se reparten en el espacio libre de los dos lados, lo menos lejos posible de su palabra (el anclaje cede), y **nunca se superponen**. Si ni así entran, el renglón se quiebra una sola vez, antes de la primera palabra cuya traducción ya no entra; la última palabra del versículo no baja sola, baja con la anterior (`colocarGlosas` / `ajustarGlosas` en `src/app.js`, que se rehacen al cargar la letra, al cambiar el ancho o el tamaño y al volver a la app).
- **Preposiciones:** la preposición latina va traducida junto con la palabra que sigue, en un solo par («ad dandam = para dar», «in terra = en la tierra»), y esas dos palabras no se separan de renglón.
- Salmos: un hemistiquio latino y debajo su traducción. Prosa (lecturas, oraciones, versículos, antífonas): grupos de palabras con su traducción debajo, que bajan juntos al cortar el renglón.

## Partitura gregoriana

- Espacio entre sílabas amplio (el equivalente a «====» de Caeciliae) y algo menos («==») antes y después de cada pausa.
- Las sílabas no se centran bajo las notas.

## Versión única

Solo Liturgia de las Horas (rito actual), sin selector de rito ni de modo. Una sola versión, que se va corrigiendo. Base: la Liturgia de las Horas en español (salmos pautados para el canto, antífonas de los salmos en español). En gregoriano latino, con traducción literal bajo los neumas: la invocación inicial, el cántico evangélico (antífona y cuerpo) y la conclusión. La traducción interlineal es literal y propia (no la del español de la Liturgia de las Horas): va palabra por palabra, bajo cada palabra latina, salvo la preposición, que va con la palabra que sigue; fuera de eso, solo se agrupan palabras o se cambia el orden cuando ir una por una confundiría. El latín corre con espacios regulares y es la traducción la que se acomoda. Un botón «Cantado | Recitado» al comienzo de la hora pasa todas esas piezas a texto (latín con traducción literal debajo), sin botones por pieza. En el modo recitado no va ninguna partitura ni pauta de canto (ni las negritas ni las cursivas de la pauta): solo el texto, con * y †; en negrita, solo lo que responde la asamblea.

- **Base:** la forma ordinaria, con cambios puntuales de la forma extraordinaria (ciertos himnos, antífonas y cánticos).
- **Nombres de las horas y de sus partes:** los de la Liturgia de las Horas en español (Completas, Invocación inicial, Salmo 15, Cántico de Simeón, Antífona final de la Santísima Virgen…), aunque el texto vaya en latín.
- **Título de la hora:** solo en la barra de arriba; no se repite en el cuerpo.
- **Barra de arriba en la hora:** se esconde al bajar y vuelve al subir; tocar el texto la muestra o la esconde (no cuenta si se está seleccionando texto ni si se toca un botón o un desplegable). Tocar dos o tres veces seguidas no selecciona palabras; arrastrar o mantener apretado, sí.
- **Modo de salmos y cánticos (Laudes y Vísperas):** uno por semana del salterio para las ferias y otro por domingo, el mismo para toda la hora y el cántico evangélico; se puede cambiar con el desplegable junto al título de cada salmo. Primer verso en partitura y los demás pautados (acento en negrita, preparatorias en cursiva). Detalle y reglas de acentuación: [salmodia.md](salmodia.md). El Breviario de 1960 sigue en los datos, pero no se muestra.

- **Cruz (✠):** solo en el texto latino; nunca en la traducción. Va pegada a la palabra que sigue, con un espacio común antes.
- **Respuestas del pueblo** (℟. Amen.) en renglón propio.

## Diseño visual

- **Texto negro: dos pesos, como en el Cantoral Laudibus.** Normal 400 y negrita 600, también en la letra de las partituras. **Excepción (18/11/2026):** los acentos del modo en la salmodia (pautado y letra de la partitura de salmos, cánticos y cántico evangélico) van en bold 700, para que se vean más; por eso Source Serif 4 se carga también en 700 (solo redonda) y «Septies AE» trae ǽ/Ǽ en 400, 600 y 700. La letra bajo los neumas mide lo mismo que el texto en español y la traducción, lo mismo que la glosa (app.js lo calcula al dibujar cada partitura); solo se achica la traducción de un renglón que no entra (hasta 72 %).
- **Tipografías:** Source Serif 4 para textos, títulos y latín; Source Sans 3 para la interfaz y los datos. Etiquetas en mayúsculas con espaciado (no hay versalitas reales).
- **Cuatro tamaños:** título, ítem, interfaz y dato. El mínimo es el dato (unos 14 px) y toda la interfaz se puede agrandar.
- **Radios:** dos, de 8 px y 16 px.
- **Modo claro:** papel blanco, tinta negra, pergamino `#f4eee4` para tarjetas, arco `#e7ddcc`, tinta de ilustración `#2a201a`. Nada de tonos pastel.
- **Modo oscuro:** fondo negro puro (`#000`) y superficies en gris neutro (`#161616`, `#111`). Las ilustraciones no se invierten.
- **Ilustraciones:** grabado y mosaico antiguo, en línea, dentro de arcos de pergamino, sin imágenes pixeladas.
- **Tarjeta del día (inicio):** altura fija y arco de forma fija (ancho = 0,72 del alto). Si el título no entra, se achica la letra hasta 1,05 rem; solo si ni así entra, la tarjeta crece.
- **Título del día:** el nombre arriba, en negrita; debajo, muy junto y en letra más fina y cursiva, los títulos del santo («obispo y doctor de la Iglesia», «papa y mártir», «reina»). Si estaban intercalados se juntan: «Santos Andrés Dung-Lac y compañeros» / «presbítero y mártires». Una rayita suave separa el título de los datos del día (tiempo, semana del salterio, síntesis biográfica), que van juntos al pie.
- **Inicio:** sin el rótulo «Las horas de hoy»; «Oraciones antes y después del oficio» va centrado entre la tarjeta (o los calendarios) y la lista de horas.
- **Calendario:** al tocar la fecha del inicio se abre el mes (la semana empieza el domingo): cada día con su número y, debajo, un globito del color litúrgico; domingos y solemnidades en negrita, hoy en rojo, el día elegido sobre pergamino. Los colores dobles («Rojo o color del Tiempo litúrgico») toman el primero.
- **Imagen de la tarjeta del inicio:** grabados de una sola tinta del álbum «Liturgical Cliparts», pintados con la tinta de ilustración sobre el pergamino del arco; entran enteros, apoyados abajo. Cuál va cada día lo dice `base/ilustraciones.yaml`: propia de la celebración o del día (también en Cuaresma) → la del evangelio del domingo, según el ciclo → la del común (en Cuaresma, la del tiempo) → la del tiempo → una genérica. Si el día tiene varias, cambian en cada hora. Las figuras muy angostas llevan una guarda del álbum a cada costado. Nada de escenas modernas ni de textos que contradigan estas reglas (por ejemplo, «Aleluya» con y).
- **Controles:** escondidos. Nada de barras inferiores ni índice: todo está en el menú «⋯» (lectura, aspecto, canto).
- **Modo claro por defecto;** el oscuro solo si la persona lo elige.
- **Una sola versión de cada texto.** No hay selector de versiones.
- **Lectura aireada:** amplio espacio entre las partes del oficio.

## Accesibilidad (guías de Apple)

- Zonas táctiles de 44 × 44 pt.
- «Deshacer» en lugar de pedir confirmación.
- Aviso breve tras cada acción.
- El botón o gesto de volver cierra capas sin salir de la app.

## Modo oscuro

Como en el Cantoral Laudibus: no sigue al dispositivo; solo se aplica si se elige en Opciones (`:root[data-theme="dark"]`). Fondo negro puro (`#000`, pedido en noviembre de 2026); superficies y líneas en gris neutro algo más claro; texto blanco roto y acentos aclarados (contraste ≥ 4,5:1). En noviembre de 2026 todos volvieron a claro una vez (`temaClaro2026`).
