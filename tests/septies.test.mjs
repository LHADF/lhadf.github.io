// Pruebas sin dependencias: node --test tests/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync, readdirSync } from 'node:fs';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
const S = require('../src/salmodia.js');
const sil = (f, w) => f(w).map(s => (s.acc ? s.t.toUpperCase() : s.t)).join('-');

test('silabeo latino', () => {
  assert.equal(sil(S.silabasLatin, 'requiéscet'), 're-qui-ÉS-cet');
  assert.equal(sil(S.silabasLatin, 'lingua'), 'LIN-gua');
  assert.equal(sil(S.silabasLatin, 'Iesum'), 'IE-sum');
  assert.equal(sil(S.silabasLatin, 'eius'), 'E-ius');
  assert.equal(sil(S.silabasLatin, 'Dómine'), 'DÓ-mi-ne');
});

test('silabeo y acento en español', () => {
  assert.equal(sil(S.silabasEspanol, 'refugio'), 're-FU-gio');
  assert.equal(sil(S.silabasEspanol, 'Señor'), 'Se-ÑOR');
  assert.equal(sil(S.silabasEspanol, 'corazón'), 'co-ra-ZÓN');
  assert.equal(sil(S.silabasEspanol, 'Espíritu'), 'Es-PÍ-ri-tu');
  assert.equal(sil(S.silabasEspanol, 'satisfacen'), 'sa-tis-FA-cen');
});

const roles = (verso, tono, lang) => {
  const pv = S.pautarVerso(verso, tono, lang, false);
  const f = h => h.res.map(r => r.rol === 'acc' ? 'B' : r.rol === 'prep' ? 'I' : '.').join('');
  return [pv.med && f(pv.med), f(pv.ter)];
};

test('pautado latino, tono 8 G', () => {
  // mediante: un acento; terminación: dos preparatorias y un acento
  assert.deepEqual(roles('Deus, in adiutórium meum inténde: * Dómine, ad adiuvándum me festína.', '8G', 'la'),
    ['...........B.', '........IIB.']);
  // monosílabo final tras esdrújula: el acento pasa a la sílaba anterior
  assert.deepEqual(roles('Ego vero egénus et pauper sum: * Deus, ádiuva me.', '8G', 'la')[1], '..IIB.');
});

test('pautado español: aguda al final del verso', () => {
  const pv = S.pautarVerso('yo digo al Señor * «Tú eres mi bien.»', '8G', 'es', false);
  const ult = pv.ter.res[pv.ter.res.length - 1];
  assert.equal(ult.rol, 'acc');
  assert.equal(ult.nota, 'hg');
});

// Datos: todo el latín sigue las normas (i, no j) y lleva traducción interlineal en el modo Latín
const ctx = { window: {} };
for (const f of readdirSync(new URL('../src/datos/', import.meta.url)).filter(f => f.endsWith('.js')))
  vm.runInNewContext(readFileSync(new URL('../src/datos/' + f, import.meta.url), 'utf8'), ctx);
const D = ctx.window.DATA;

test('latín sin j', () => {
  const malos = [];
  const ver = (o, enLatin) => {
    if (typeof o === 'string') { if (enLatin && /[jJ]/.test(o.replace(/\([^)]*\)/g, '').replace(/^[^%]*%%/s, ''))) malos.push(o.slice(0, 50)); return; }
    if (Array.isArray(o)) return o.forEach(x => ver(x, enLatin));
    if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) ver(v, enLatin || k === 'la');
  };
  ver(D, false);
  assert.deepEqual(malos, []);
});

test('interlineal en todos los textos latinos', () => {
  const faltan = [];
  for (const [nombre, rito] of Object.entries(D.ritos))
    for (const s of rito.secciones) {
      if (s.rep || !['vr', 'vr1', 'prosa', 'doxo', 'lectura', 'ant', 'oremos', 'salmo'].includes(s.k)) continue;
      const tieneLatin = s.k === 'salmo' ? true : (s.v || s.t || {}).la != null;
      if (!tieneLatin) continue;
      const ok = s.k === 'salmo' ? Array.isArray(s.inter) && s.inter.length === s.versos.la.length
        : s.k === 'vr' ? s.ilv && s.ilr : !!s.il;
      if (!ok) faltan.push(`${nombre}: ${s.k} ${((s.v || s.t || {}).la || s.id || '').slice(0, 30)}`);
    }
  assert.deepEqual(faltan, []);
});
