# Septies — instrucciones para trabajar en este repositorio

- Antes de tocar la interfaz o los textos, seguí [docs/diseno.md](docs/diseno.md). Las reglas de ortotipografía son innegociables.
- La app es un solo HTML armado por `tools/armar.py` desde `src/`. No hay paso de compilación con npm.
- Los textos viven en `src/datos/`, generados por `tools/datos.py`. Si cambiás un texto, cambialo en `tools/datos.py` y regenerá; no edites el `.js` generado a mano.
- Todo texto latino lleva traducción interlineal literal (en `tools/datos.py`: `IL_NOVUS`, `IL_VETUS`, `INTER_*`). La prueba `tests/septies.test.mjs` falla si falta alguna.
- Antes de proponer cambios: `node --test tests/*.test.mjs` y `python3 tools/armar.py`.
- Hablale al usuario en español rioplatense.
