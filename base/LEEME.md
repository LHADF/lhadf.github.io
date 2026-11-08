# Base de textos de la LH ADF

Textos de la Liturgia de las Horas en español, ordenados como en los libros. Se cargaron una sola vez desde
el repositorio `sync` (2015–2026) con `tools/importar/`; desde entonces **la base es la fuente**: las
correcciones se hacen acá y la app no depende de `sync`.

Cada archivo es texto YAML y se puede editar directamente en GitHub. Reglas de escritura:

- Los textos de varios renglones van después de `|-`, con sangría de dos espacios. Cada renglón del texto es un renglón del archivo.
- Las estrofas de los salmos e himnos son elementos de una lista (`- |-`).
- Versículo y respuesta: `- V: …` y `- R: …`.
- Si un texto empieza con comillas, lleva dos puntos seguidos de espacio («: ») o empieza con un signo raro, conviene encerrarlo entre comillas simples `'…'`.
- Al publicar, `tools/verificar_base.py` revisa que no falte nada y que cada salmo citado exista. Si algo está mal, la publicación se detiene y dice qué arreglar.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `ordinario/` | Lo que no cambia con el día: invocación, examen, responsorio, cántico evangélico, bendición, antífonas finales de la Virgen |
| `salterio/` | El salterio de cada hora. Completas: un juego por día de la semana |
| `tiempo/` | Propio del tiempo. Por ahora, Completas del Triduo pascual y de la Octava de Pascua |
| `himnos/` | Himnos por hora y por tiempo; en cada tiempo se puede elegir cualquiera de la lista |
| `salmos/` | Cada salmo y cántico una sola vez, por su clave (`salmo-30-2-6` = Salmo 30, 2-6) |
| `informes/` | Lo que encontró la carga: versiones distintas de un mismo texto en `sync` y la verificación |

Faltan todavía: Laudes, Vísperas, Oficio de lectura, hora intermedia, santoral, comunes y lo propio de ADF.

## Reglas de Completas (las aplica la app)

- **Juego de salmos:** el del día de la semana. En la noche del sábado y la víspera de una solemnidad, el del sábado
  (después de las I Vísperas); el domingo y el día de una solemnidad, el del domingo (después de las II Vísperas).
- **Oración:** la del juego; en las solemnidades, `oracion_solemnidad` («Visita, Señor, esta habitación…»).
- **Tiempo pascual:** `salmodia_pascua`, responsorio y antífona del cántico con aleluya, antífona «Reina del cielo».
- **Triduo y Octava de Pascua:** todo lo de `tiempo/completas-triduo-octava.yaml`, día por día. En la Octava se alternan los juegos del sábado y del domingo.
- **Aleluya** después del Gloria de la invocación: siempre, salvo en Cuaresma.
- **Himnos:** Tiempo Ordinario, Adviento y Navidad, Cuaresma (y Triduo), Pascua: cada uno con su lista.
