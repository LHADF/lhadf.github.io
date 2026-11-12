# LH ADF (Septies) — instrucciones para Copilot

Respondé en español rioplatense. Antes de cambiar la interfaz o los textos, leé [docs/diseno.md](../docs/diseno.md): las reglas de ortotipografía son innegociables.

## Qué es

**LH ADF** (nombre interno: *Septies*) es una app web de **Liturgia de las Horas** con canto gregoriano, publicada en <https://lhadf.github.io/>. Es de ADF (Ad Fontes, Movimiento de renovación cultural) y sigue su **calendario litúrgico propio**, distinto del general y del de Argentina.

- **Una sola versión**, que se va corrigiendo: sin selector de rito, de versión ni de texto.
- **Base:** la forma ordinaria (nombres de las horas y de sus partes como en la Liturgia de las Horas en español), con cambios puntuales de la forma extraordinaria (ciertos himnos, antífonas y cánticos) que indica el equipo.
- Salmos y lecturas en español; invocación, cántico evangélico, conclusión y otras piezas en latín con traducción interlineal literal. Un botón «Cantado | Recitado» al comienzo de la hora decide todas las piezas gregorianas.
- Es app hermana del **Cantoral Laudibus**: comparten sistema visual (colores, modo oscuro, tipografías, partituras).

## Cómo está organizado

| Ruta | Qué hay |
| --- | --- |
| `base/` | **La fuente de los textos** (YAML editable a mano). Ver `base/LEEME.md`. `ordinario/`, `salterio/`, `tiempo/`, `santoral/`, `comunes/`, `himnos/`, `salmos/` (un archivo por salmo o cántico), `gregoriano/` (`.gabc` y cuándo va cada uno), `calendario/` (calendarios locales y notas). |
| `src/app.js`, `src/app.css` | Interfaz: portada «Hoy», lectura de la hora, menú «⋯». |
| `src/completas.js` | Arma Completas. |
| `src/laudes.js` | Arma Laudes y Vísperas. |
| `src/horas.js` | Arma el Oficio de lectura y la Hora intermedia. |
| `src/salmodia.js` | Silabeo, acentos, tonos salmódicos y pautado. |
| `src/cantoral.js` | Dibujo de partituras compartido con el Cantoral. |
| `src/assets/` | Fuentes propias («Cantoral Signos», «Septies AE») e ilustraciones. |
| `tools/calendario.py` | Genera `src/datos/calendario.js` con el motor del Ordo ADF (`lucasfelixjhs/ordo-telegram`). |
| `tools/base_js.py` | Pasa `base/` a `src/datos/base.js` y a `src/carga/*.js`. |
| `tools/verificar_base.py` | Revisa la base (falta algo, salmo inexistente, etc.). |
| `tools/normalizar_gabc.py` | Normaliza GABC nuevos (i, æ, œ, negrita de la asamblea). |
| `tools/armar.py` | Une todo en un único `dist/index.html`. |
| `tests/` | Pruebas con `node --test`. |
| `docs/` | Decisiones: `diseno.md`, `laudes.md`, `visperas.md`, `horas.md`. |

No hay npm ni paso de compilación: solo Python 3 y Node.js.

```sh
python3 tools/verificar_base.py   # revisa la base
python3 tools/base_js.py          # base → src/datos y src/carga
node --test tests/*.test.mjs      # pruebas
python3 tools/armar.py            # genera dist/index.html
```

Cada push a `main` corre todo esto y publica en GitHub Pages (`.github/workflows/deploy.yml`). El calendario se recalcula además cada lunes.

Si `README.md` o `docs/fuentes.md` contradicen a `CLAUDE.md`, vale `CLAUDE.md` (el README describe el prototipo inicial).

## Qué no tocar

- **No edites a mano archivos generados:** `src/datos/calendario.js`, `src/datos/base.js`, `src/carga/` y `dist/`. Cambiá la fuente (`base/`, `tools/`) y regenerá.
- **No vuelvas a correr `tools/importar/`** ni corrijas textos en `sync`: la base ya se cargó una vez y desde entonces `base/` es la fuente. El importador pisaría correcciones hechas a mano.
- **No toques `src/vendor/exsurge.js`** (librería de terceros, MIT) ni `public/licenses/` / `THIRD_PARTY_NOTICES.md` salvo para sumar una licencia.
- **No inventes textos litúrgicos** (antífonas, oraciones, propios ADF, melodías). Si falta algo, dejalo marcado y avisá; los propios ADF se revisan a mano y las decisiones de fondo las define el revisor del equipo.
- **No agregues** selectores de versión, barras inferiores, índices ni dependencias de compilación.
- **No cambies `deploy.yml`** sin que se pida.

## Reglas que más se rompen

- **«aleluia»**, nunca «aleluya» (también en las traducciones). En Cuaresma y el Triduo, «Laus tibi, Christe, Rex ætérnæ glóriæ» en lugar del aleluia. Las pruebas lo verifican.
- **Latín:** *i* en vez de *j*, ligaduras æ/œ, tildes de acento. La ✠ solo en el latín, nunca en la traducción.
- **Traducción interlineal literal, palabra por palabra**, bajo cada palabra latina (propia, no el español de la Liturgia de las Horas). El latín corre con espacios regulares; la traducción se acomoda. Todo texto latino lleva traducción: la prueba falla si falta.
- **En rojo:** rúbricas (en cursiva), ℣, ℟, asterisco, cruz, números de estrofa, capital inicial del gregoriano. **Traducción en verde** (`--glosa`).
- **Lo que responde la asamblea, en negrita** (en GABC, `<b>…</b>` sílaba por sílaba).
- **Preces:** † en el corte y * al final.
- **Citas bíblicas** en texto nuevo: «Dn 3: 26-27» (capítulo, dos puntos, espacio, versículos). La base heredada usa coma; no la cambies en bloque sin que se pida.
- **Tipografía:** Source Serif 4 (textos y latín) y Source Sans 3 (interfaz), solo pesos 400 y 600. Radios de 8 y 16 px. Modo claro por defecto; oscuro con fondo `#000` solo si se elige en Opciones.
- **Accesibilidad:** zonas táctiles de 44 × 44 pt, «Deshacer» en lugar de confirmaciones.

## Usos ADF en las horas (resumen)

- **Calendario:** base ADF sin país; Argentina, Paraguay y otros como variantes del día.
- **Laudes:** «Dómine, lábia mea apéries» siempre antes del «Deus in adiutórium»; invitatorio (antífona y Salmo 94) solo los domingos. Himno en gregoriano en domingos y solemnidades; solo texto en ferias, memorias y fiestas. Cánticos evangélicos en latín de la Neovulgata. Pater noster en latín, con monición solo en fiestas y solemnidades.
- **Invocación en gregoriano:** tono solemne (domingos, solemnidades y sus I Vísperas, Triduo, Octavas), festivo (fiestas), ferial (ferias y memorias).
- Reglas detalladas de Completas: `base/LEEME.md`. Laudes, Vísperas y otras horas: `docs/`.

## Antes de proponer cambios

Corré `node --test tests/*.test.mjs` y `python3 tools/armar.py`; si tocaste `base/`, también `python3 tools/verificar_base.py`. Commits en español, breves, que digan qué cambia para quien usa la app.
