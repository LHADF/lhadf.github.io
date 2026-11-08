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

// Datos: base y calendario; armado de Completas
const ctx = { window: {} };
for (const f of ['base.js', 'calendario.js'])
  vm.runInNewContext(readFileSync(new URL('../src/datos/' + f, import.meta.url), 'utf8'), ctx);
vm.runInNewContext(readFileSync(new URL('../src/completas.js', import.meta.url), 'utf8'), ctx);
const B = ctx.window.BASE, CP = ctx.window.Completas;
const letra = g => g.split('%%')[1].replace(/\([^)]*\)/g, '').replace(/<[^>]+>/g, '').replace(/\[[^\]]*\]/g, '');

test('latín de las partituras: i, no j', () => {
  const G = B.completas.gregoriano;
  for (const g of [G.invocacion.solemne, G.invocacion.ferial, G.antifona.gabc, G.cantico.gabc, G.conclusion.gabc])
    assert.ok(!/[jJ]/.test(letra(g)), letra(g).slice(0, 40));
});

test('toda partitura latina lleva traducción', () => {
  for (const f of ['2026-11-05', '2026-11-08', '2027-03-28', '2027-12-25']) {
    const r = CP.armar(f, 'ARG');
    for (const s of r.secciones) if (s.gabc) assert.ok(Array.isArray(s.glosa) && s.glosa.length, f + ' ' + s.k);
  }
});

const juego = (f, reg = 'ARG') => CP.armar(f, reg).juego;
const secc = (f, k) => CP.armar(f, 'ARG').secciones.filter(s => s.k === k);
test('Completas: juego de salmos según el día', () => {
  assert.equal(juego('2026-11-05'), 'jueves');                  // feria
  assert.equal(juego('2026-11-07'), 'sabado');                  // sábado: I Vísperas del domingo
  assert.equal(juego('2026-11-08'), 'domingo');                 // domingo
  assert.equal(juego('2026-12-07'), 'sabado');                  // víspera de la Inmaculada (solemnidad)
  assert.equal(juego('2026-12-08'), 'domingo');                 // Inmaculada
  assert.equal(juego('2027-03-29'), 'sabado');                  // lunes de la Octava de Pascua
  assert.equal(juego('2027-03-30'), 'domingo');                 // martes de la Octava de Pascua
});

test('Completas: oración de solemnidad, Cuaresma sin aleluya, Pascua con aleluya', () => {
  const orac = f => secc(f, 'prosa').at(-1).t.es;
  assert.match(orac('2026-12-08'), /^Visita, Señor/);
  assert.match(orac('2026-11-08'), /^Humildemente/);
  assert.match(orac('2026-11-05'), /^Señor, Dios nuestro, concédenos/);
  const inv = f => secc(f, 'vr')[0].gabc;
  assert.ok(!/Al\(/.test(inv('2027-02-17')), 'Miércoles de Ceniza sin aleluya');
  assert.ok(/Al\(/.test(inv('2026-11-05')));
  assert.ok(/deus|DE\(f\)us/i.test(inv('2026-11-08')) && /\(c4\)/.test(inv('2026-11-08')), 'domingo: tono solemne (clave de do en 4.ª)');
  assert.ok(/\(c3\)/.test(inv('2026-11-05')), 'feria: tono festivo (clave de do en 3.ª)');
  const ant = f => secc(f, 'ant').find(s => s.id === 'ac').gabc;
  assert.ok(/Al\(g\)le/.test(ant('2027-04-15')) && !/Al\(g\)le/.test(ant('2026-11-05')));
});
