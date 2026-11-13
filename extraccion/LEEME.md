# Extracción del libro de la Liturgia de las Horas

Extracción del PDF de los cuatro tomos (`LH_completa.pdf`, que no está en el repo) por tipografía, con PyMuPDF. Sigue el documento «Extracción de la Liturgia de las Horas desde el PDF: instrucciones para una IA». La app no usa nada de esta carpeta: es material para revisar.

    pip install pymupdf
    python3 extraccion/extraer.py RUTA/LH_completa.pdf [--seccion ordinario|comunes|virgen] [--revision CARPETA]

- `extraer.py`: el script (lectura, clasificación, piezas, unificación de tomos, controles).
- `revision.py`: arma la página de revisión lado a lado (con `--revision`; las imágenes de las páginas no van al repo).
- `ordinario/`: paso 3, el Ordinario de la Liturgia de las Horas de los cuatro tomos (de la portada hasta antes del Salterio): `ordinario.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/`: paso 2, todos los oficios comunes de los cuatro tomos (de la Dedicación hasta antes del Oficio de difuntos): `comunes.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
- `comunes/virgen/`: prueba aprobada con el Común de la Santísima Virgen María y la memoria de santa María en sábado: `virgen.json`, `salmos.json`, `himnos.json`, `dudas.csv`, `diferencias.csv` y `controles.txt`.
