# Septies

*Septies in die laudem dixi tibi* (Sal 118, 164).

Liturgia de las Horas con varias versiones de texto y canto gregoriano: rito actual y Breviario Romano de 1960; español, latín con traducción interlineal y modo canto con antífonas en notación cuadrada y salmos pautados en cualquier tono.

**Estado:** prototipo. Solo está armada **Completas del jueves 5 de noviembre de 2026**, en los dos ritos.

## Cómo funciona

| Carpeta | Contenido |
| --- | --- |
| `src/app.js`, `src/app.css` | Interfaz: portada «Hoy», lectura de la hora, modos, menú de opciones. |
| `src/salmodia.js` | Silabeo latino y español, acentos, tonos salmódicos 1–8 y peregrino, pautado y GABC de los salmos. |
| `src/cantoral.js` | Funciones de dibujo de partituras compartidas con el Cantoral (espaciado, glosa bajo los neumas). |
| `src/vendor/exsurge.js` | Exsurge, motor de notación gregoriana (MIT). |
| `src/assets/` | Fuente «Cantoral Signos» (℣, ℟, cruz patada, asterisco) e ilustración de la portada. |
| `src/datos/` | Los textos y partituras de cada hora, generados por `tools/datos.py`. |
| `tools/datos.py` | Arma los datos a partir de las fuentes (ver [docs/fuentes.md](docs/fuentes.md)). |
| `tools/armar.py` | Une todo en un solo `dist/index.html`. |
| `tests/` | Pruebas del silabeo, el pautado y los datos. |

La app es un único archivo HTML sin dependencias de compilación: solo Python 3 para armarla y Node.js para las pruebas.

```sh
node --test tests/*.test.mjs   # pruebas
python3 tools/armar.py         # genera dist/index.html
```

Para regenerar los datos hacen falta los clones de las fuentes en una carpeta hermana `../fuentes` (o en la que indique `SEPTIES_FUENTES`); los datos generados ya están en el repositorio.

## Publicación

Cada cambio en `main` ejecuta las pruebas, arma la app y la publica en GitHub Pages (**Settings → Pages → Source → GitHub Actions**). Dirección: <https://lhadf.github.io/>.

## Reglas

Las decisiones de diseño, ortotipografía y accesibilidad están en [docs/diseno.md](docs/diseno.md). Las de ortotipografía son innegociables.

## Historia

La primera versión (React + TypeScript, Completas de 1960 del 7 de julio de 2026 contrastadas con Divinum Officium) sigue en la rama `feat/1960-compline`.
