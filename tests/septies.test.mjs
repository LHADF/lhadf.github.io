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
  for (const g of [G.invocacion.solemne, G.invocacion.festivo, G.invocacion.ferial, G.antifona.gabc, G.cantico.gabc, G.conclusion.gabc])
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
  assert.ok(/\(c3\)/.test(inv('2026-11-05')), 'feria: tono ferial (clave de do en 3.ª)');
  const tono = f => secc(f, 'vr')[0].tono;
  assert.equal(tono('2026-11-05'), 'ferial');                    // feria
  assert.equal(tono('2026-11-09'), 'festivo');                   // fiesta (Dedicación de Letrán)
  assert.equal(tono('2026-11-08'), 'solemne');                   // domingo
  assert.equal(tono('2026-12-08'), 'solemne');                   // solemnidad
  assert.match(inv('2026-11-09'), /tó\(hi\)ri/); assert.match(inv('2026-11-05'), /tó\(i\)ri/);
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
  const todas = [G.invocacion.solemne, G.invocacion.festivo, G.invocacion.ferial, G.antifona.gabc, G.cantico.gabc, G.conclusion.gabc, G.himno.gabc,
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

test('Completas: Triduo, himno según el día, Nunc con marcas a mano', () => {
  const mar = f => secc(f, 'mariana')[0].opciones.map(o => o.id).join(' ');
  for (const f of ['2027-03-25', '2027-03-26', '2027-03-27'])   // Triduo: Ave Regína cælórum, simple o solemne
    assert.equal(mar(f), 'ave-sim ave-sol');
  assert.equal(mar('2027-03-28'), 'regina_caeli-sol');            // Domingo de Pascua
  const h = f => secc(f, 'himno')[0];
  assert.equal(h('2026-11-08').def, 'telucis'); assert.ok(h('2026-11-08').efimera);   // domingo: siempre el Te lucis
  assert.equal(h('2026-11-05').def, 'ordinario-0'); assert.ok(!h('2026-11-05').efimera);
  const c = secc('2026-11-05', 'cantico')[0];
  assert.ok(c.versos.every(v => / \* /.test(v))); assert.match(c.versos[0], /\*\*me\*\*i/);
});

test('Completas: las antífonas de los salmos se marcan como de la asamblea', () => {
  assert.ok(secc('2026-11-05', 'ant').filter(a => a.t && a.t.es).every(a => a.es));
});

test('Completas: cada pieza cantada tiene su versión recitada (latín con traducción)', () => {
  for (const f of ['2026-11-05', '2026-11-08', '2027-02-17', '2027-04-15', '2027-03-26']) {
    const r = CP.armar(f, 'ARG').secciones;
    const rec = [...r.filter(s => s.k === 'vr' || s.id === 'ac' || s.id === 'ac2').map(s => s.rec),
      ...r.filter(s => s.k === 'mariana' || s.k === 'himno').flatMap(s => s.opciones.filter(o => o.gabc).map(o => o.rec))];
    assert.ok(rec.length >= 6 && rec.every(x => x && x.length && x.every(l => l.pares.every(p => p[0] && p[1]))), f);
    const c = r.find(s => s.k === 'cantico');
    assert.ok(c.verso1 && c.inter1);
  }
  const inv = secc('2026-11-05', 'vr')[0].rec;
  assert.equal(JSON.stringify(inv.map(l => [l.rol, l.todos])), JSON.stringify([['V', false], ['R', true], ['', true]]));
  assert.equal(inv[0].pares[1][0], '✠ in');
  assert.ok(!secc('2027-02-17', 'vr')[0].rec.flatMap(l => l.pares).some(p => /^Allel/.test(p[0])));
  // Cuaresma: «Laus tibi, Christe» en lugar del aleluya, en partitura y en el texto, con su traducción palabra por palabra
  for (const f of ['2027-02-17', '2027-02-21', '2027-03-25']) {
    const v = secc(f, 'vr')[0];
    assert.match(v.gabc, /<b>Laus<\/b>\(h\) <b>ti<\/b>\(h\)<b>bi,<\/b>\(h\) <b>Chri<\/b>/); assert.ok(!/Dó<\/b>\(h\)<b>mi<\/b>\(h\)<b>ne<\/b>\(h'_\) <b>Rex/.test(v.gabc));
    assert.ok(!/Allel|<alt>/.test(v.gabc)); assert.match(v.gabc, /\(::\)\s*$/);
    assert.equal(v.glosa.map(p => p[0]).slice(-6).join(' '), 'Laus tibi, Christe, Rex ætérnæ glóriæ.');
  }
  assert.ok(!/Laus/.test(secc('2026-11-05', 'vr')[0].gabc));
});

// El interlineal es palabra por palabra: las palabras latinas de los pares, en orden, son exactamente las del texto
test('interlineal: los pares cubren el texto latino palabra por palabra', () => {
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  const palGabc = g => g.split('%%')[1].replace(/<alt>.*$/s, '').replace(/<eu>.*?<\/eu>/gs, '').replace(/<sp>[^<]*<\/sp>|<i>T\. ?P\.<\/i>|T\. P\./g, '')
    .replace(/\([^)]*\)/g, '').replace(/<[^>]+>|\[[^\]]*\]|[{}]/g, '').split(/\s+/).map(norm).filter(Boolean).join(' ').replace(/alle luia$/, 'alle');
  const palPares = ps => ps.flatMap(p => String(p[0]).split(/\s+/)).map(norm).filter(Boolean).join(' ');
  const G = B.completas.gregoriano;
  const casos = [[G.invocacion.solemne, G.invocacion.traduccion], [G.invocacion.festivo, G.invocacion.traduccion], [G.invocacion.ferial, G.invocacion.traduccion],
    [G.antifona.gabc, G.antifona.traduccion], [G.cantico.gabc, G.cantico.traduccion], [G.conclusion.gabc, G.conclusion.traduccion], [G.himno.gabc, G.himno.traduccion],
    ...Object.values(G.responsorio).map(x => [x.gabc, x.traduccion]), ...Object.values(G.marianas).map(x => [x.gabc, x.traduccion])];
  for (const [g, ps] of casos) assert.equal(palPares(ps), palGabc(g), g.split('\n')[0]);
  const plano = v => v.replace(/\*\*|_/g, '').split(/\s+/).filter(w => w !== '*' && w !== '†').map(norm).filter(Boolean).join(' ');
  G.cantico.versos.forEach((v, i) => assert.equal(palPares(G.cantico.traduccion_versos[i]), plano(v)));
  assert.equal(palPares(G.cantico.traduccion), plano(G.cantico.primer_verso));
  // los pares van palabra por palabra salvo pocas frases hechas
  const todos = casos.flatMap(c => c[1]).concat(G.cantico.traduccion_versos.flat());
  assert.ok(todos.filter(p => /\s/.test(String(p[0]).trim())).length <= 3);
});

test('español: «aleluia», nunca «aleluya»', () => {
  assert.ok(!/aleluya/i.test(JSON.stringify(B)));
});

// ---------- Laudes ----------
for (const f of ['../src/carga/laudes.js', '../src/carga/visperas.js', '../src/laudes.js']) vm.runInNewContext(readFileSync(new URL(f, import.meta.url), 'utf8'), ctx);
const LA = ctx.window.Laudes, LD = ctx.window.LAUDES;
const secL = (f, k) => LA.armar(f, 'ARG').secciones.filter(s => s.k === k);

test('Laudes: se arman completas para todos los días del calendario', () => {
  let f = ctx.window.CAL.desde; const mal = [];
  while (f <= ctx.window.CAL.hasta) {
    const r = LA.armar(f, 'ARG'), S = r.secciones;
    const ok = S.filter(s => s.k === 'salmo').length >= 3 && S.find(s => s.k === 'himno').opciones[0].est.length && S.find(s => s.k === 'lectura').t.es
      && S.find(s => s.k === 'preces') && S.find(s => s.id === 'ab').t.es && S.find(s => s.k === 'prosa').t.es;
    if (!ok && !r.dia.nota) mal.push(f);
    f = CP.masDias(f, 1);
  }
  assert.deepEqual(mal, []);
});

test('Laudes: invitatorio solo los domingos; tono de la invocación; ciclo dominical', () => {
  const ids = f => LA.armar(f, 'ARG').secciones.filter(s => s.k === 'sec').map(s => s.id);
  assert.equal(ids('2026-11-08')[0], 'invitatorio'); assert.equal(secL('2026-11-08', 'salmo')[0].id, 'salmo-94');
  assert.equal(ids('2026-11-10')[0], 'inicio');
  assert.equal(secL('2026-11-08', 'vr')[1].tono, 'solemne'); assert.equal(secL('2026-11-10', 'vr')[1].tono, 'ferial'); assert.equal(secL('2026-11-09', 'vr')[1].tono, 'festivo');
  assert.equal(LA.ciclo('2026-11-08'), 'A'); assert.equal(LA.ciclo('2026-11-29'), 'B'); assert.equal(LA.ciclo('2025-06-01'), 'C');
});

test('Laudes: capas (salterio, tiempo, santoral) y partes en latín', () => {
  assert.equal(secL('2026-11-12', 'salmo')[0].id, LD.salterio.semana_4.jueves.salmodia[0].salmo);          // feria: salterio
  assert.match(secL('2026-11-10', 'prosa')[0].t.es, /san León Magno/);                                       // memoria: oración propia
  assert.equal(secL('2026-12-08', 'salmo')[0].id, 'salmo-62-2-9');                                           // solemnidad: salmos del domingo I
  assert.ok(!secL('2026-12-08', 'salmo').find(s => s.id === 'cantico-dn-3-57-88-56').gloria);                // Daniel 3, 57-88: sin Gloria
  const c = secL('2026-11-10', 'cantico')[0];
  assert.equal(c.versos.length, 14); assert.equal(c.versos.length, c.inter.length);
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  c.versos.forEach((v, i) => assert.equal(c.inter[i].flatMap(p => p[0].split(/\s+/)).map(norm).join(' '), v.split(/\s+/).filter(w => w !== '*').map(norm).join(' ')));
  const pn = secL('2026-11-10', 'pater')[0];
  assert.equal(pn.pares[0][0], 'Pater'); assert.equal(pn.pares[2][0], '* qui'); assert.equal(pn.pares.at(-1)[1], 'mal.');
  assert.equal(pn.intro, ''); assert.ok(secL('2026-11-09', 'pater')[0].intro && secL('2026-11-08', 'pater')[0].intro);   // monición: solo domingos, fiestas y solemnidades
  assert.equal(LA.armar('2026-11-10', 'ARG').secciones.filter(x => x.k === 'vr').length, 2);                          // Dómine, lábia mea + Deus in adiutórium
  const co = secL('2026-11-10', 'conclusion')[0].opciones;
  assert.match(co[0].gabc, /nus\(h\) ✠\(\) nos/); assert.match(co[1].gabc, /\(c3\)/); assert.match(secL('2026-11-08', 'conclusion')[0].opciones[1].gabc, /\(c4\)/);
  assert.equal(co[1].rec.length, 4); assert.equal(co[1].despues.map(l => l.pares.map(x => x[0]).join(' ')).join(' | '), 'Ite in pace. | Deo grátias.');
  const p = secL('2026-11-10', 'preces')[0]; assert.ok(p.respuesta && p.preces.every(x => x.length === 2));
  assert.ok(!/aleluya/i.test(JSON.stringify(LD)));
});

test('texto recitado: renglones con sentido (Gloria, Salve, Pater noster)', () => {
  const ln = vs => vs.map(v => v.map(p => p[0]).join(' '));
  assert.equal(ln(secc('2026-11-05', 'vr')[0].rec[2].versos).join(' / '), 'Glória Patri, et Fílio, et Spirítui Sancto. / Sicut erat in princípio, et nunc, et semper, / et in sǽcula sæculórum. Amen. Allelúia.');
  assert.equal(ln(secc('2027-02-17', 'vr')[0].rec[2].versos).at(-1), 'Laus tibi, Christe, Rex ætérnæ glóriæ.');
  const salve = ln(secc('2026-11-05', 'mariana')[0].opciones[0].rec[0].versos);
  assert.equal(salve.length, 10); assert.equal(salve[4], 'in hac lacrimárum valle.'); assert.equal(salve.at(-1), 'O clemens: O pia: O dulcis Virgo María.');
  const pn = ln(secL('2026-11-10', 'pater')[0].lineas);
  assert.equal(pn.length, 9); assert.equal(pn[0], 'Pater noster, * qui es in cælis,'); assert.equal(pn.at(-1), 'sed líbera nos a malo.');
  for (const m of Object.values(B.completas.gregoriano.marianas))   // los cortes cubren todo el texto
    assert.ok(Math.abs(m.cortes.reduce((a, b) => a + b, 0) - m.traduccion.flatMap(p => p[0].split(/\s+/)).length) <= 1);
});

// ---------- Vísperas ----------
const VI = ctx.window.Visperas, VD = ctx.window.VISPERAS;
test('Vísperas: se arman para todos los días; I Vísperas la tarde anterior a domingos y solemnidades', () => {
  let f = ctx.window.CAL.desde; const mal = [];
  while (f <= ctx.window.CAL.hasta) {
    const r = VI.armar(f, 'ARG'), S = r.secciones;
    const ok = S.filter(s => s.k === 'salmo').length === 3 && S.find(s => s.k === 'himno').opciones[0].est.length && S.find(s => s.k === 'lectura').t.es && S.find(s => s.k === 'preces');
    if (!ok) mal.push(f);
    f = CP.masDias(f, 1);
  }
  assert.deepEqual(mal, []);
  const sab = VI.armar('2026-11-14', 'ARG');                                   // sábado: I Vísperas del domingo
  assert.ok(sab.primeras); assert.match(sab.dia.titulo, /Domingo.*I Vísperas$/);
  assert.equal(sab.secciones.find(s => s.k === 'salmo').id, VD.salterio['semana_' + CP.diaCal('2026-11-15', 'ARG').sal].domingo_1.salmodia[0].salmo);
  assert.ok(VI.armar('2026-12-07', 'ARG').primeras);                             // víspera de la Inmaculada
  assert.ok(!VI.armar('2026-11-11', 'ARG').primeras);
  assert.ok(!VI.armar('2027-03-27', 'ARG').primeras);                            // Sábado Santo: vísperas propias
  assert.equal(VI.armar('2026-11-11', 'ARG').secciones[0].id, 'inicio');         // sin «Dómine, lábia mea»
});

test('Vísperas: Magníficat en latín con interlineal palabra por palabra', () => {
  const c = VI.armar('2026-11-11', 'ARG').secciones.find(s => s.k === 'cantico');
  assert.equal(c.versos.length, 12); assert.match(c.versos[0], /^Magníficat \* ánima mea Dóminum\./);
  const norm = w => w.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  c.versos.forEach((v, i) => assert.equal(c.inter[i].flatMap(p => p[0].split(/\s+/)).map(norm).join(' '), v.split(/\s+/).filter(w => w !== '*').map(norm).join(' ')));
  assert.ok(!/aleluya/i.test(JSON.stringify(VD)));
});

test('celebraciones propias de ADF: toman del común (o de otra celebración) hasta tener textos propios', () => {
  const r = LA.armar('2027-02-03', 'ARG');                                       // San Blas (solemnidad ADF): común de un mártir
  assert.match(r.dia.nota, /Común de un mártir/);
  assert.equal(r.secciones.find(s => s.k === 'himno').opciones[0].n, LD.comunes['un-martir'].himno);
  assert.equal(r.secciones.find(s => s.id === 'ab').t.es, LD.comunes['un-martir'].ant_benedictus);
  assert.equal(LD.mapa['Divino Niño Jesús'], undefined);                         // no se confunde con santa Teresa del Niño Jesús
  for (const [n, a] of Object.entries(LD.adf)) assert.ok((a.comun && LD.comunes[a.comun]) || (a.como && LD.santoral[a.como]) || (a.es && LD.mapa[n] === a.es) || a.pendiente, n);
});

test('cántico de Daniel 3, 57-88: «No se dice Gloria al Padre» va como rúbrica, no como verso', () => {
  const s = LA.armar('2026-11-15', 'ARG').secciones.find(x => x.k === 'salmo' && x.id === 'cantico-dn-3-57-88-56');
  assert.equal(s.rubrica, 'No se dice Gloria al Padre.');
  assert.equal(s.gloria, false);
  assert.ok(!s.versos.es.some(v => /No se dice/.test(v)));
});

test('calendarios: la base es ADF; otros calendarios y memorias libres son variantes del día', () => {
  const nombres = (f, sel) => CP.opcionesDia(f, sel).map(o => o.siglas.join(' ') + (o.actual ? '*' : ''));
  assert.deepEqual(JSON.stringify(nombres('2026-11-11', '')), JSON.stringify(['CRG ADF*', 'BUE']));       // San Martín: memoria; solemnidad en Buenos Aires
  assert.equal(CP.diaCal('2026-11-11', '').g, 'Memoria obligatoria');
  const bue = CP.diaCal('2026-11-11', 'BUE');
  assert.equal(bue.g, 'Solemnidad'); assert.match(bue.nota, /Patrono principal de la Ciudad de Buenos Aires/);
  assert.ok(VI.armar('2026-11-10', 'BUE').primeras && !VI.armar('2026-11-10', '').primeras);                // con sus I Vísperas
  assert.equal(CP.diaCal('2027-05-08', 'BUE').n, 'Bienaventurada Virgen María de Luján');                  // lo de Argentina vale para Buenos Aires
  assert.equal(CP.diaCal('2027-05-08', '').g, 'Feria');
  // Día ferial con memoria libre: se celebra la memoria (no la feria). 13 de noviembre: san Leandro en ADF, san Artémides en ARG
  assert.equal(JSON.stringify(nombres('2026-11-13', '')), JSON.stringify(['ESP ADF*', 'ARG']));
  assert.equal(CP.diaCal('2026-11-13', '').n, 'San Leandro de Sevilla, obispo');
  assert.equal(CP.diaCal('2026-11-13', 'ARG').n, 'San Artémides Zatti, religioso');
  assert.equal(CP.diaCal('2026-11-13', 'BUE').n, 'San Artémides Zatti, religioso');
  assert.match(LA.armar('2026-11-13', 'ARG').dia.nota, /Común de santos varones/);
  assert.equal(CP.diaCal('2026-11-25', '').n, 'Santa Catalina de Alejandría, virgen y mártir');
  assert.equal(CP.opcionesDia('2026-11-25', '').length, 1);
  assert.equal(CP.opcionesDia('2026-11-15', '').length, 1);        // Roque González (Fiesta en PGY) no le gana al domingo
  for (const sg of Object.keys(ctx.window.CAL.var).flatMap(k => ctx.window.CAL.var[k].flatMap(v => v[1].split(' ')))) assert.ok(ctx.window.CAL.calendarios[sg], sg);
});

test('invitatorio gregoriano de los domingos del Tiempo Ordinario, con traducción palabra por palabra', () => {
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  const pal = g => g.split('%%')[1].replace(/\([^)]*\)/g, '').replace(/<[^>]+>|[{}]/g, '').split(/\s+/).map(norm).filter(Boolean).join(' ');
  const pp = ps => ps.flatMap(p => String(p[0]).split(/\s+/)).map(norm).filter(Boolean).join(' ');
  const S = LA.armar('2026-11-15', '').secciones, g = S.find(s => s.k === 'invgreg');
  assert.ok(g && S.some(s => s.k === 'invop') && S.some(s => s.k === 'salmo' && s.inv === 'es'));
  assert.equal(g.estrofas.length, 6);
  for (const x of [g.ant, ...g.estrofas]) { assert.equal(pp(x.glosa), pal(x.gabc)); assert.ok(!/[jJ]/.test(x.gabc.split('%%')[1].replace(/\([^)]*\)/g, ''))); }
  assert.ok(!LA.armar('2026-12-06', '').secciones.some(s => s.k === 'invgreg'));   // Adviento: todavía no
  assert.ok(B.oraciones.preparatoria.texto.length > 6 && B.oraciones.conclusiva.texto.length > 7);
  for (const k of ['preparatoria', 'conclusiva']) for (const [la] of B.oraciones[k].texto) assert.ok(la.length <= 52, la);   // renglones cortos
});

test('notas del Calendario ADF y calendarios locales que heredan de su país', () => {
  const sm = CP.diaCal('2026-11-11', '');
  assert.match(sm.nota, /^BUE\tPatrono principal de la Ciudad de Buenos Aires/m);
  assert.match(sm.nota, /^ADF\tPatrono secundario de ADF/m);
  assert.equal(CP.diaCal('2027-11-15', 'PGY').g, 'Fiesta');           // Roque González: Fiesta en Paraguay
  assert.equal(CP.diaCal('2027-11-15', 'CDE').g, 'Fiesta');           // Ciudad del Este hereda lo de Paraguay
  assert.equal(CP.diaCal('2027-11-15', '').g, 'Memoria obligatoria');
  assert.equal(CP.opcionesDia('2027-02-03', '').length, 1);           // San Blas: CDE no cambia nada, no hay sigla de más
  for (const f of ctx.window.CAL.dias) { const n = ctx.window.CAL.tabla[f[12]]; if (n) for (const l of n.split('\n')) assert.match(l, /^[A-Z]{3}\t\S/); }
});

test('inicio: Santa María en sábado como opción, biografías y nombre de las Vísperas', () => {
  const o = CP.opcionesDia('2026-11-14', '');
  assert.equal(o.length, 2); assert.equal(o[1].f.n, 'Santa María en sábado'); assert.ok(o[0].actual);
  assert.match(LA.armar('2026-11-14', {cal: '', dia: {'2026-11-14': 'Santa María en sábado'}}).dia.nota, /Común de la Santísima Virgen María/);
  assert.ok(CP.diaCal('2026-11-11', '').bio.length > 100);
  assert.ok(VI.armar('2026-11-14', '').primeras);
});

test('Oficio de lectura y Hora intermedia', () => {
  for (const f of ['carga/oficio.js', 'carga/intermedia.js', 'horas.js']) vm.runInNewContext(readFileSync(new URL('../src/' + f, import.meta.url), 'utf8'), ctx);
  const W = ctx.window, ids = r => r.secciones.filter(s => s.k === 'sec').map(s => s.id);
  const dom = W.Oficio.armar('2026-11-15', ''), fer = W.Oficio.armar('2026-11-12', '');
  assert.ok(ids(dom).includes('tedeum') && !ids(fer).includes('tedeum'));                   // Te Deum: domingo sí, feria no
  for (const r of [dom, fer]) { assert.equal(r.secciones.filter(s => s.k === 'lectura_larga').length, 2); assert.ok(!JSON.stringify(r).includes('[falta')); }
  const t = W.Tercia.armar('2026-11-12', '');
  assert.equal(t.secciones.filter(s => s.k === 'salmo').length, 3);
  assert.ok(t.secciones.some(s => s.k === 'salop'));                                        // se puede elegir la complementaria
  const c = W.Tercia.armar('2026-11-12', '', {complementaria: true}).secciones.filter(s => s.k === 'salmo').map(s => s.id);
  assert.notEqual(c.join(), t.secciones.filter(s => s.k === 'salmo').map(s => s.id).join());
  const sol = W.Sexta.armar('2026-12-08', '');                                              // solemnidad entre semana: complementaria, sin elegir
  assert.ok(!sol.secciones.some(s => s.k === 'salop'));
  for (const h of ['Tercia', 'Sexta', 'Nona']) assert.ok(W[h].armar('2026-11-12', '').secciones.some(s => s.k === 'lectura'));
});
