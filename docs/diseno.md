# Reglas de diseño de Septies

Septies es app hermana del Cantoral: comparte su sistema visual y sus gestos. Las reglas de **ortotipografía son innegociables**; las demás se aplican en la medida en que la app las necesite.

## Ortotipografía

- **En rojo:** rúbricas (además en cursiva), la letra capital inicial del gregoriano y el número de modo, los números de estrofa de los himnos, ℣, ℟, asterisco y cruz.
- **Glifos propios** (fuente «Cantoral Signos»): ℣ y ℟ con trazo diagonal, cruz patada (✠) y asterisco de cinco pétalos.
- **Latín:** *i* en lugar de *j*; ligaduras æ/œ; tildes de acento.
- **Himnos:** estrofas numeradas «1.», «2.», con línea en blanco entre estrofas. En un himno con estrofas numeradas, el bloque sin número es el estribillo: cursiva y con ℟. Himno sin ninguna estrofa numerada: texto normal, sin cursiva y sin ℟.
- **Polifonías:** una frase por línea, con traducción interlineal. Indicaciones entre corchetes en el original ([Coro]) y en rojo en la app.

## Traducción

- **Siempre interlineal** y en **verde** (`--glosa`).
- **Anclada por palabras** en la medida de lo posible; por frases solo cuando el orden no queda bien en español. Así no se desfasa del latín ni se superponen partes.
- Salmos: un hemistiquio latino y debajo su traducción. Prosa (lecturas, oraciones, versículos, antífonas): grupos de palabras con su traducción debajo, que bajan juntos al cortar el renglón.

## Partitura gregoriana

- Espacio entre sílabas amplio (el equivalente a «====» de Caeciliae) y algo menos («==») antes y después de cada pausa.
- Las sílabas no se centran bajo las notas.

## Modos de rezo

Tres modos, arriba y discretos: **Español** (todo en español), **Latín** (latín con interlineal) y **Canto** (salmos y lecturas en español, pautados para el canto; lo demás en latín, con antífonas, himno, responsorio y antífona mariana en gregoriano).

## Diseño visual

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
