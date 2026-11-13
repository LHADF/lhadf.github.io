# Extracción del libro de la Liturgia de las Horas

Extracción del PDF de los cuatro tomos (`LH_completa.pdf`, que no está en el repo) por tipografía, con PyMuPDF. Sigue el documento «Extracción de la Liturgia de las Horas desde el PDF: instrucciones para una IA». La app no usa nada de esta carpeta: es material para revisar.

    pip install pymupdf
    python3 extraccion/extraer.py RUTA/LH_completa.pdf [--seccion tiempo-adviento|tiempo-navidad|tiempo-cuaresma|tiempo-semana-santa|tiempo-pascua|tiempo-ordinario|salterio|completas|ordinario|comunes|virgen] [--revision CARPETA]

- `extraer.py`: el script (lectura, clasificación, piezas, unificación de tomos, controles).
- `revision.py`: arma la página de revisión lado a lado (con `--revision`; las imágenes de las páginas no van al repo).
- `tiempo/`: paso 5, el Propio del tiempo, un archivo por tiempo litúrgico y una carpeta por tiempo: `tiempo/adviento/tiempo-adviento.json` (tomo I, 44–209), `tiempo/navidad/` (I, 210–400), `tiempo/cuaresma/` (II, 1185–1428), `tiempo/semana-santa/` (II, 1429–1516), `tiempo/pascua/` (II, 1517–1864) y `tiempo/ordinario/` (III 2880–3313 y IV 4487–5072). Cada tiempo está en un solo tomo, salvo el Tiempo ordinario, que se reparte entre el III (semanas I–XVII y las solemnidades del Señor) y el IV (semanas XVIII–XXXIV): las semanas son complementarias y no se unifica nada entre tomos.

  Estructura de cada archivo: `titulo` (el del libro, nulo si el libro no lo imprime), y `bloques`, en el orden del libro. Un bloque es un título que agrupa («I. TEXTOS COMUNES PARA EL TIEMPO DE ADVIENTO…», «SEMANA I DE CUARESMA», «SANTO TRIDUO PASCUAL…»): tiene su `titulo`, sus `rubricas`, sus `horas` propias si el libro se las da, y sus `celebraciones`. Cada celebración lleva `id` (el slug del título literal), `titulo`, y los campos que el título dice: `semana`, `dia`, `fecha` (`{dia, mes}`) y `tipo` (solo si el título dice «SOLEMNIDAD», «FIESTA» o «MEMORIA»).

  Claves nuevas de `cuando` en el paso 5: ninguna; se usan las del documento que no habían aparecido hasta ahora: `ciclo_dominical` (A, B, C), `ciclo_lecturas` (anual, bienal) y `anio` (I, II). Quedan marcadas para CRU las etiquetas de fecha («Día 17 de diciembre:»), las que señalan una de las tres Horas («TERCIA:», «Sólo para Nona:») y «Antes/Después de la Ascensión».
- `salterio/`: paso 4, el Salterio de cuatro semanas de los cuatro tomos (portada, semanas I–IV y la salmodia complementaria, que el libro imprime después de Completas): `salterio.json` (semanas → días → horas), `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `completas/`: paso 4, Completas («Oración para antes del descanso nocturno») de los cuatro tomos: `completas.json` (formularios: domingo tras las I y II Vísperas, lunes a viernes), con sus bibliotecas y controles.

  Claves nuevas de `cuando` en el paso 4: `dia` («Domingo I de Adviento:» → `{tiempo: adviento, dia: [domingo-1]}`; «Lunes santo:» → `{tiempo: semana-santa, dia: [lunes]}`; «Domingo de Ramos:» → `dia: [domingo-ramos]`) y `despues_de` (Completas: `visperas1-domingo`, `visperas1-solemnidad`, `visperas2-domingo`, `visperas2-solemnidad`). Quedan marcadas para CRU «… antes del 24 de diciembre:» (rango de fechas) y «… durante la octava de Pascua». Los tomos I y II ponen rúbricas donde los tomos III y IV traen texto: quedan como piezas aparte, con sus tomos en `fuentes`, sin condición.
- `ordinario/`: paso 3, el Ordinario de la Liturgia de las Horas de los cuatro tomos (de la portada hasta antes del Salterio): `ordinario.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/`: paso 2, todos los oficios comunes de los cuatro tomos (de la Dedicación hasta antes del Oficio de difuntos): `comunes.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/virgen/`: prueba aprobada con el Común de la Santísima Virgen María y la memoria de santa María en sábado: `virgen.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
