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
  const AL = /Al(<\/b>)?\(/;
  assert.ok(!AL.test(inv('2027-02-17')), 'Cuaresma sin aleluya');
  assert.ok(AL.test(inv('2026-11-05')));
  assert.ok(/deus|DE\(f\)us/i.test(inv('2026-11-08')) && /\(c4\)/.test(inv('2026-11-08')), 'domingo: tono solemne (clave de do en 4.ª)');
  assert.ok(/\(c3\)/.test(inv('2026-11-05')), 'feria: tono festivo (clave de do en 3.ª)');
  const ant = f => secc(f, 'ant').find(s => s.id === 'ac').gabc;
  const ALS = /Al(<\/b>)?\(g\)(<b>)?le/;
  assert.ok(ALS.test(ant('2027-04-15')) && !ALS.test(ant('2026-11-05')));
});

// Latín de las partituras: tilde en las palabras de tres sílabas o más (salvo nombres con diéresis, como Israël)
const palabrasGabc = g => {
  const c = g.split('%%')[1].replace(/<alt>.*?<\/alt>|<eu>.*?<\/eu>/gs, '').replace(/<[^>]+>|\[[^\]]*\]|[{}]/g, '');
  const out = []; let cur = '', n = 0;
  for (const m of c.matchAll(/([^()]*)\(([^)]*)\)/g)) {
    const t = m[1];
    if (/^\s/.test(t) || !t.trim()) { if (cur) out.push([cur, n]); cur = ''; n = 0; }
    if (/[A-Za-zÀ-ÿæœǽ]/.test(t)) { cur += t.trim(); n++; }
  }
  if (cur) out.push([cur, n]);
  return out;
};
test('latín de las partituras: tildes en palabras de 3 sílabas o más', () => {
  const G = B.completas.gregoriano;
  const todas = [G.invocacion.solemne, G.invocacion.ferial, G.antifona.gabc, G.cantico.gabc, G.conclusion.gabc, G.himno.gabc,
    ...Object.values(G.responsorio).map(x => x.gabc), ...Object.values(G.marianas).map(x => x.gabc)];
  const faltan = [];
  for (const g of todas) for (const [w, n] of palabrasGabc(g))
    if (n >= 3 && !/[áéíóúýǽÁÉÍÓÚÝǼ́ë]/.test(w)) faltan.push(w);
  assert.deepEqual(faltan, []);
});

test('Completas: antífona final de la Virgen según el día', () => {
  const mar = f => { const m = secc(f, 'mariana')[0]; return m.opciones.map(o => o.id).join(' ') + (m.efimera ? ' (efímera)' : ''); };
  assert.equal(mar('2026-11-05'), 'salve-sim subtuum (efímera)');     // feria del Tiempo Ordinario
  assert.equal(mar('2026-11-08'), 'salve-sol');                        // domingo
  assert.equal(mar('2026-11-07'), 'salve-sol');                        // I Vísperas del domingo
  assert.equal(mar('2027-08-15'), 'ave-sol ave-sim');                  // Asunción
  assert.equal(mar('2026-12-02'), 'alma-sim');                         // Adviento, feria
  assert.equal(mar('2026-12-06'), 'alma-sol');                         // Adviento, domingo
  assert.equal(mar('2027-01-20'), 'salve-sim subtuum (efímera)');     // Tiempo Ordinario antes de la Candelaria
  assert.equal(mar('2027-02-04'), 'ave-sim');                          // después de la Candelaria (feria)
  assert.equal(mar('2027-03-03'), 'ave-sim');                          // Cuaresma
  assert.equal(mar('2027-04-15'), 'regina_caeli-sim');                 // Pascua, feria
  assert.equal(mar('2027-04-18'), 'regina_caeli-sol');                 // Pascua, domingo
});

test('Completas: invocación con cortes y doble barra; Nunc con un solo versículo en partitura; bendición sin acentos', () => {
  const inv = secc('2026-11-05', 'vr')[0].gabc;
  assert.match(inv, /na\.(<\/b>)?\([^)]*\) \(::\) \(Z\)\s*\n(<b>)?Gló/); // doble barra y renglón nuevo antes del Gloria
  assert.match(inv, /\(Z\)\s*\n<sp>R\/<\/sp>/);                       // Dómine en renglón nuevo
  const c = secc('2026-11-05', 'cantico')[0];
  assert.equal((c.gabc.match(/\(::\)/g) || []).length, 1);
  assert.ok(!/\d+\.\s*Nunc/.test(c.gabc));
  assert.equal(c.versos.length, c.inter.length);
  assert.ok(!/r1/.test(B.completas.gregoriano.conclusion.gabc));
});

test('Completas: lo que responde la asamblea va en negrita', () => {
  const r = CP.armar('2026-11-05', 'ARG').secciones;
  const inv = r.find(s => s.k === 'vr').gabc;
  assert.match(inv, /<b>Dó<\/b>\(h\)<b>mi<\/b>/);                            // ℟. Dómine…
  assert.ok(!/<b>DE<\/b>|<b>us<\/b>/.test(inv));                               // el «Deus» lo entona el que preside
  const [a1, a2] = r.filter(s => s.id === 'ac' || s.id === 'ac2');
  assert.match(a1.gabc, /nos,\(j\) \*\(\) <b>Dó<\/b>/);                     // Salva nos: desde el asterisco
  assert.match(a2.gabc, /<b>SAl<\/b>/); assert.ok(!/\*\(/.test(a2.gabc));    // repetición: toda en negrita, sin asterisco
  assert.equal(r.find(s => s.k === 'deo').t, 'Deo grátias.');
});

test('Completas: Triduo como sync, himno según el día, Nunc con marcas a mano', () => {
  const mar = f => secc(f, 'mariana')[0].opciones.map(o => o.id).join(' ');
  assert.equal(mar('2027-03-25'), 'alma-sol');     // Jueves Santo
  assert.equal(mar('2027-03-26'), 'ave-sol');      // Viernes Santo
  assert.equal(mar('2027-03-27'), 'salve-sol');    // Sábado Santo
  const h = f => secc(f, 'himno')[0];
  assert.equal(h('2026-11-08').def, 'telucis'); assert.ok(h('2026-11-08').efimera);   // domingo: siempre el Te lucis
  assert.equal(h('2026-11-05').def, 'ordinario-0'); assert.ok(!h('2026-11-05').efimera);
  const c = secc('2026-11-05', 'cantico')[0];
  assert.ok(c.versos.every(v => / \* /.test(v))); assert.match(c.versos[0], /\*\*me\*\*i/);
});
