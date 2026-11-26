// Para cada fecha y hora del período de la extracción latina, los salmos (claves de base/salmos) que arma la app, en orden,
// con su antífona. Calendario general ADF (sin país). Necesita src/carga/ (correr antes python3 tools/armar.py).
// Uso: node extraccion/latin/salmos_app.mjs DESDE HASTA SALIDA.json
import { readFileSync, writeFileSync } from 'node:fs';
import vm from 'node:vm';
const [desde, hasta, salida] = process.argv.slice(2);
const R = new URL('../../src/', import.meta.url);
const ctx = { window: {}, console }; ctx.window.window = ctx.window;
for (const f of ['datos/base.js', 'datos/calendario.js', 'completas.js', 'carga/laudes.js', 'carga/visperas.js', 'carga/oficio.js', 'carga/intermedia.js', 'laudes.js', 'horas.js'])
  vm.runInNewContext(readFileSync(new URL(f, R), 'utf8'), ctx);
const W = ctx.window, CP = W.Completas, out = {}, sel = { cal: '', dia: {} };
for (let f = desde; f <= hasta; f = CP.masDias(f, 1)) {
  out[f] = {};
  const arm = { completas: () => CP.armar(f, sel), laudes: () => W.Laudes.armar(f, sel), visperas: () => W.Visperas.armar(f, sel), oficio: () => W.Oficio.armar(f, sel),
    tercia: () => W.Tercia.armar(f, sel, {}), sexta: () => W.Sexta.armar(f, sel, {}), nona: () => W.Nona.armar(f, sel, {}) };
  for (const [h, fn] of Object.entries(arm)) {
    try { const r = fn(); if (!r) { out[f][h] = null; continue; }
      const sal = []; let ant = null;
      for (const s of r.secciones) { if (s.k === 'ant' && !s.rep && s.t && s.t.es) ant = s.t.es; if (s.k === 'salmo') sal.push({ id: s.id, ant }); }
      out[f][h] = { cel: r.dia.titulo, primeras: !!r.primeras, sal };
    } catch (e) { out[f][h] = { error: String(e) }; }
  }
}
writeFileSync(salida, JSON.stringify(out));
