# Septies — instrucciones para trabajar en este repositorio

- Antes de tocar la interfaz o los textos, seguí [docs/diseno.md](docs/diseno.md). Las reglas de ortotipografía son innegociables.
- La app es un solo HTML armado por `tools/armar.py` desde `src/`. No hay paso de compilación con npm.
- **Base de textos:** `base/` (ver `base/LEEME.md`), cargada una vez desde `sync` con `tools/importar/`. La base es la fuente: se corrige ahí, no en `sync`, y el importador no se vuelve a correr (pisaría correcciones). `python3 tools/verificar_base.py` la revisa.
- **Gregoriano:** `base/gregoriano/` (archivos `.gabc` con i y æ, y `completas.yaml` con cuándo va cada uno y su traducción «latín = español»). Todo texto latino lleva traducción literal debajo; la prueba falla si falta.
- **Calendario:** el motor del Ordo ADF (`lucasfelixjhs/ordo-telegram`). `tools/calendario.py` genera `src/datos/calendario.js`: la base es el calendario ADF sin país; los demás calendarios (ARG, PGY, BRS del Ordo; locales como BUE en `base/calendario/locales.yaml`) y las memorias libres van como variantes del día, que se eligen en el inicio. La publicación lo recalcula y corre cada lunes.
- **Armado:** `tools/base_js.py` pasa la base a `src/datos/base.js` (Completas) y a `src/carga/laudes.js` y `visperas.js` (se cargan al abrir la hora); `src/completas.js` arma Completas y `src/laudes.js` arma Laudes y Vísperas; `app.js` las dibuja. Decisiones: `docs/laudes.md`, `docs/visperas.md`.
- Antes de proponer cambios: `node --test tests/*.test.mjs` y `python3 tools/armar.py`.
- Hablale al usuario en español rioplatense.
