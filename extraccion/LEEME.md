# Extracción del libro de la Liturgia de las Horas

Extracción del PDF de los cuatro tomos (`LH_completa.pdf`, que no está en el repo) por tipografía, con PyMuPDF. Sigue el documento «Extracción de la Liturgia de las Horas desde el PDF: instrucciones para una IA». La app no usa nada de esta carpeta: es material para revisar.

    pip install pymupdf
    python3 extraccion/extraer.py RUTA/LH_completa.pdf [--seccion salterio|completas|ordinario|comunes|virgen] [--revision CARPETA]

- `extraer.py`: el script (lectura, clasificación, piezas, unificación de tomos, controles).
- `revision.py`: arma la página de revisión lado a lado (con `--revision`; las imágenes de las páginas no van al repo).
- `salterio/`: paso 4, el Salterio de cuatro semanas de los cuatro tomos (portada, semanas I–IV y la salmodia complementaria, que el libro imprime después de Completas): `salterio.json` (semanas → días → horas), `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `completas/`: paso 4, Completas («Oración para antes del descanso nocturno») de los cuatro tomos: `completas.json` (formularios: domingo tras las I y II Vísperas, lunes a viernes), con sus bibliotecas y controles.

  Claves nuevas de `cuando` en el paso 4: `dia` («Domingo I de Adviento:» → `{tiempo: adviento, dia: [domingo-1]}`; «Lunes santo:» → `{tiempo: semana-santa, dia: [lunes]}`; «Domingo de Ramos:» → `dia: [domingo-ramos]`) y `despues_de` (Completas: `visperas1-domingo`, `visperas1-solemnidad`, `visperas2-domingo`, `visperas2-solemnidad`). Quedan marcadas para CRU «… antes del 24 de diciembre:» (rango de fechas) y «… durante la octava de Pascua». Los tomos I y II ponen rúbricas donde los tomos III y IV traen texto: quedan como piezas aparte, con sus tomos en `fuentes`, sin condición.
- `ordinario/`: paso 3, el Ordinario de la Liturgia de las Horas de los cuatro tomos (de la portada hasta antes del Salterio): `ordinario.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/`: paso 2, todos los oficios comunes de los cuatro tomos (de la Dedicación hasta antes del Oficio de difuntos): `comunes.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/virgen/`: prueba aprobada con el Común de la Santísima Virgen María y la memoria de santa María en sábado: `virgen.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
