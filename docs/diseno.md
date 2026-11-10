# Reglas de diseño de Septies

Septies es app hermana del Cantoral: comparte su sistema visual y sus gestos. Las reglas de **ortotipografía son innegociables**; las demás se aplican en la medida en que la app las necesite.

## Ortotipografía

- **En rojo:** rúbricas (además en cursiva), la letra capital inicial del gregoriano y el número de modo, los números de estrofa de los himnos, ℣, ℟, asterisco y cruz.
- **Glifos propios** (fuente «Cantoral Signos»): ℣ y ℟ con trazo diagonal, cruz patada (✠) y asterisco de cinco pétalos.
- **Latín:** *i* en lugar de *j*; ligaduras æ/œ; tildes de acento. Source Serif 4 no trae «ǽ» ni «Ǽ»: van en `src/assets/ae.css` (familia propia «Septies AE», nunca «Cantoral Signos»), armadas con la «æ» y la tilde de la misma fuente (`tools/fuente_ae.py`), para que no se vean más altas.
- **Himnos:** estrofas numeradas «1.», «2.», con línea en blanco entre estrofas. En un himno con estrofas numeradas, el bloque sin número es el estribillo: cursiva y con ℟. Himno sin ninguna estrofa numerada: texto normal, sin cursiva y sin ℟.
- **Polifonías:** una frase por línea, con traducción interlineal. Indicaciones entre corchetes en el original ([Coro]) y en rojo en la app.

## Traducción

- **Siempre interlineal** y en **verde** (`--glosa`).
- **Anclada por palabras** en la medida de lo posible; por frases solo cuando el orden no queda bien en español. Así no se desfasa del latín ni se superponen partes.
- Salmos: un hemistiquio latino y debajo su traducción. Prosa (lecturas, oraciones, versículos, antífonas): grupos de palabras con su traducción debajo, que bajan juntos al cortar el renglón.

## Partitura gregoriana

- Espacio entre sílabas amplio (el equivalente a «====» de Caeciliae) y algo menos («==») antes y después de cada pausa.
- Las sílabas no se centran bajo las notas.

## Versión única

Solo Liturgia de las Horas (rito actual), sin selector de rito ni de modo. Una sola versión, que se va corrigiendo. Base: la Liturgia de las Horas en español (salmos pautados para el canto, antífonas de los salmos en español). En gregoriano latino, con traducción literal bajo los neumas: la invocación inicial, el cántico evangélico (antífona y cuerpo) y la bendición final. Un botón «Cantado | Recitado» al comienzo de la hora pasa todas esas piezas a texto (latín con traducción literal debajo), sin botones por pieza.

- **Base:** la forma ordinaria, con cambios puntuales de la forma extraordinaria (ciertos himnos, antífonas y cánticos).
- **Nombres de las horas y de sus partes:** los de la Liturgia de las Horas en español (Completas, Invocación inicial, Salmo 15, Cántico de Simeón, Antífona final de la Santísima Virgen…), aunque el texto vaya en latín.
- **Título de la hora:** solo en la barra de arriba; no se repite en el cuerpo.
- **Tono de salmos y cánticos:** sigue siempre a la antífona; no hay opción para cambiarlo. El Breviario de 1960 sigue en los datos, pero no se muestra.

- **Cruz (✠):** solo en el texto latino; nunca en la traducción. La cruz y el asterisco quedan centrados entre los textos, con el mismo espacio a cada lado.
- **Respuestas del pueblo** (℟. Amen.) en renglón propio.

## Diseño visual

- **Texto negro: dos pesos, como en el Cantoral Laudibus.** Normal 400 y negrita 600 (la tipografía se carga solo en esos dos pesos), también en la letra de las partituras. La letra bajo los neumas mide lo mismo que el texto en español y la traducción, lo mismo que la glosa (app.js lo calcula al dibujar cada partitura); solo se achica la traducción de un renglón que no entra (hasta 72 %).
- **Tipografías:** Source Serif 4 para textos, títulos y latín; Source Sans 3 para la interfaz y los datos. Etiquetas en mayúsculas con espaciado (no hay versalitas reales).
- **Cuatro tamaños:** título, ítem, interfaz y dato. El mínimo es el dato (unos 14 px) y toda la interfaz se puede agrandar.
- **Radios:** dos, de 8 px y 16 px.
- **Modo claro:** papel blanco, tinta negra, pergamino `#f4eee4` para tarjetas, arco `#e7ddcc`, tinta de ilustración `#2a201a`. Nada de tonos pastel.
- **Modo oscuro:** negro puro (`#000`) y superficies `#141312`. Las ilustraciones no se invierten.
- **Ilustraciones:** grabado y mosaico antiguo, en línea, dentro de arcos de pergamino, sin imágenes pixeladas.
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

Como en el Cantoral Laudibus: no sigue al dispositivo; solo se aplica si se elige en Opciones (`:root[data-theme="dark"]`). Fondo carbón cálido (`#1c1a17`, alrededor del 10 % de luminosidad), superficies, líneas y tintes aclarados en la misma proporción; textos, rojo y acentos sin cambios. En noviembre de 2026 todos volvieron a claro una vez (`temaClaro2026`).
