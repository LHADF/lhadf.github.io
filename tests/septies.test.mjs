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
  assert.equal(sil(S.silabasLatin, 'requiéscet'), 're-qui-É-scet');
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

test('pautado español: en la cadencia, la última sílaba no se acentúa', () => {
  const pv = S.pautarVerso('yo digo al Señor * «Tú eres mi bien.»', '8G', 'es', false);
  const ult = pv.ter.res[pv.ter.res.length - 1];
  assert.equal(ult.rol, 'fin');
  assert.equal(ult.nota, 'g.');
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
    { assert.ok(!/[jJ]/.test(letra(g)), letra(g).slice(0, 40)); assert.ok(!/ë/.test(letra(g)), 'sin diéresis'); }
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

// Latín de las partituras: tilde en las palabras de tres sílabas o más («Ísrael», con tilde: sin diéresis)
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
    if (n >= 3 && !/[áéíóúýǽÁÉÍÓÚÝǼ́]/.test(w)) faltan.push(w);
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
  assert.equal(inv[0].pares[1][0], '✠ in adiutórium');   // la preposición va con la palabra que sigue
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
  // los pares van palabra por palabra salvo pocas frases hechas; la preposición va siempre con la palabra que sigue
  const PREP = /^(a|ab|ad|ante|apud|contra|cum|de|e|ex|in|inter|ob|per|post|pro|propter|sine|sub|super|secúndum)$/i;
  const todos = casos.flatMap(c => c[1]).concat(G.cantico.traduccion_versos.flat());
  assert.ok(todos.filter(p => /\s/.test(String(p[0]).trim()) && !PREP.test(String(p[0]).trim().replace(/^[✠*]\s*/, '').split(/\s+/)[0])).length <= 3);
  assert.ok(!todos.some(p => PREP.test(String(p[0]).trim())), 'preposición suelta');
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
  assert.equal(ids('2026-11-08')[0], 'invitatorio'); assert.equal(secL('2026-11-08', 'salmoinv')[0].id, 'salmo-94');
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
  assert.equal(pn.pares[0][0], 'Pater'); assert.equal(pn.pares[2][0], '* qui'); assert.equal(pn.pares.at(-1)[0], 'a malo.'); assert.equal(pn.pares.at(-1)[1], 'del mal.');
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
  assert.equal(ln(secc('2026-11-05', 'vr')[0].rec[2].versos).join(' / '), 'Glória Patri, et Fílio, / et Spirítui Sancto. / Sicut erat in princípio, / et nunc, et semper, / et in sǽcula sæculórum. / Amen. Allelúia.');
  assert.equal(ln(secc('2027-02-17', 'vr')[0].rec[2].versos).at(-1), 'Amen. Laus tibi, Christe, Rex ætérnæ glóriæ.');
  // invocación: la cruz después de «Deus», cantada y recitada
  for (const g of Object.values(B.completas.gregoriano.invocacion).filter(x => typeof x === 'string')) assert.match(g, /DE\([^)]*\)us\([^)]*\) ✠\([,;]\) in/)   // la cruz, bajo la pausa: la pausa queda en medio de las notas;
  assert.equal(secc('2026-11-05', 'vr')[0].rec[0].pares[1][0], '✠ in adiutórium');
  const salve = ln(secc('2026-11-05', 'mariana')[0].opciones[0].rec[0].versos);
  assert.equal(salve.length, 10); assert.equal(salve[4], 'in hac lacrimárum valle.'); assert.equal(salve.at(-1), 'O clemens: O pia: O dulcis Virgo María.');
  const pn = ln(secL('2026-11-10', 'pater')[0].lineas);
  assert.equal(pn.length, 12); assert.equal(pn[4], 'sicut in cælo, et in terra.'); assert.equal(pn[9], 'debitóribus nostris;'); assert.equal(pn[0], 'Pater noster, * qui es in cælis,'); assert.equal(pn.at(-1), 'sed líbera nos a malo.');
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
  assert.match(r.dia.nota, /para un mártir/); assert.match(r.secciones.find(s => s.k === 'prosa').t.es, /Blas/);   // oración del común, con el nombre
  const um = LD.comunes['un-martir'], op = (k) => [um[k], ...((um.opciones || {})[k] || [])];   // las «O bien» se alternan
  assert.ok(op('himno').includes(r.secciones.find(s => s.k === 'himno').opciones[0].n));
  assert.ok(op('ant_benedictus').includes(r.secciones.find(s => s.id === 'ab').t.es));
  assert.equal(LD.mapa['Divino Niño Jesús'], undefined);                         // no se confunde con santa Teresa del Niño Jesús
  for (const [n, a] of Object.entries(LD.adf)) assert.ok((a.comun && LD.comunes[a.comun]) || (a.como && LD.santoral[a.como]) || (a.es && LD.mapa[n] === a.es)
    || (a.de && LD.mapa[a.de]) || (a.propio_libro && a.propio) || a.pendiente, n);
  // «de»: lo que falte sale de otra celebración, y la nota dice qué es propio (San José obrero, del 19 de marzo)
  const jo = LA.armar('2026-05-01', ''), jv = VI.armar('2026-05-01', '');
  assert.match(jo.dia.nota, /^Himno, lectura breve, .* y oración propios; lo demás, de San José, esposo de la bienaventurada Virgen María \(19 de marzo\)\.$/);
  assert.equal(jo.secciones.find(s => s.k === 'salmo').ant, 'a1');
  assert.match(jo.secciones.find(s => s.id === 'a1').t.es, /^Los pastores vinieron/);                       // antífonas del 19 de marzo
  assert.match(jv.dia.nota, /^Oración propia; lo demás, de San José/);
  assert.match(jv.secciones.find(s => s.k === 'prosa' && /creador del universo/.test(s.t.es)).t.es, /^Dios nuestro, creador/);
  assert.match(LA.armar('2026-03-21', '').dia.nota, /^Textos de San Benito de Nursia, abad \(11 de julio\)\.$/);   // «como»
  assert.match(LA.armar('2026-05-06', '').dia.nota, /lo demás, de San Juan, apóstol y evangelista \(27 de diciembre\)/);
  assert.equal(LA.armar('2026-07-20', '').dia.nota, '');                                                    // Divino Niño: todo propio
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
  assert.equal(JSON.stringify(nombres('2026-11-13', '')), JSON.stringify(['ESP ADF*', 'ARG', 'Feria']));   // con memoria libre, también la feria
  assert.equal(CP.diaCal('2026-11-13', '').n, 'San Leandro de Sevilla, obispo');
  assert.equal(CP.diaCal('2026-11-13', 'ARG').n, 'San Artémides Zatti, religioso');
  assert.equal(CP.diaCal('2026-11-13', 'BUE').n, 'San Artémides Zatti, religioso');
  assert.match(LA.armar('2026-11-13', 'ARG').dia.nota, /Común de santos varones/);
  assert.equal(CP.diaCal('2026-11-25', '').n, 'Santa Catalina de Alejandría, virgen y mártir');
  assert.equal(CP.opcionesDia('2026-11-25', '').length, 2);       // santa Catalina (memoria libre) o la feria
  assert.equal(CP.opcionesDia('2026-11-15', '').length, 1);        // Roque González (Fiesta en PGY) no le gana al domingo
  for (const sg of Object.keys(ctx.window.CAL.var).flatMap(k => ctx.window.CAL.var[k].flatMap(v => v[1].split(' ')))) assert.ok(sg === 'Feria' || ctx.window.CAL.calendarios[sg], sg);   // «Feria»: la opción de la feria
});

test('invitatorio gregoriano de los domingos del Tiempo Ordinario, con traducción palabra por palabra', () => {
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  const pal = g => g.split('%%')[1].replace(/\([^)]*\)/g, '').replace(/<[^>]+>|[{}]/g, '').split(/\s+/).map(norm).filter(Boolean).join(' ');
  const pp = ps => ps.flatMap(p => String(p[0]).split(/\s+/)).map(norm).filter(Boolean).join(' ');
  // (la opción de cantarlo en latín está oculta: el invitatorio va en español, en estrofas y sin asteriscos)
  const S = LA.armar('2026-11-15', '').secciones, inv = S.find(s => s.k === 'salmoinv');
  assert.ok(!S.some(s => s.k === 'invgreg' || s.k === 'invop'));
  assert.equal(inv.estrofas.length, 6); assert.ok(!inv.estrofas.flat().some(l => /[*†]/.test(l)));
  assert.equal(inv.estrofas.map(e => e[e.length - 1].split(' ').pop()).join(' '), 'cantos. manos. guía. obras. descanso». Amén.');
  const IG = ctx.window.LAUDES.gregoriano.invitatorio_to;   // los textos en latín siguen en la base
  for (const x of [IG.ant, ...IG.estrofas]) { assert.equal(pp(x.traduccion), pal(x.gabc)); assert.ok(!/[jJ]/.test(x.gabc.split('%%')[1].replace(/\([^)]*\)/g, ''))); }
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
  // San Blas: memoria obligatoria en ADF (notas 2 y 3 del Calendario ADF), solemnidad solo en Ciudad del Este
  assert.equal(CP.diaCal('2027-02-03', '').g, 'Memoria obligatoria'); assert.equal(CP.diaCal('2027-02-03', 'PGY').g, 'Memoria obligatoria');
  assert.equal(CP.diaCal('2027-02-03', 'CDE').g, 'Solemnidad'); assert.equal(CP.diaCal('2027-02-03', '').cal, 'ADF');
  // Feria como opción cuando se celebra una memoria libre; Sancta María in sábbato con su nota
  assert.ok(CP.opcionesDia('2026-11-17', '').some(o => o.f.g === 'Feria' && o.siglas[0] === 'Feria'));
  assert.match(CP.diaCal('2026-11-14', {cal: '', dia: {'2026-11-14': 'Sancta María in sábbato'}}).nota, /^CRG\tMemoria de Santa María en sábado\. En los sábados feriales/);
  for (const f of ctx.window.CAL.dias) { const n = ctx.window.CAL.tabla[f[12]]; if (n) for (const l of n.split('\n')) assert.match(l, /^[A-Z]{3}\t\S/); }
});

test('calendarios: las siglas de la celebración base dicen de dónde la asume ADF; solo las variantes son lugares', () => {
  // San Leandro: «ESP · ADF» (ADF asume la celebración de España, para todos menos ARG); el único lugar es ARG (San Artémides Zatti)
  const o = CP.opcionesDia('2027-11-13', '');
  assert.equal(o[0].tipo, 'b'); assert.deepEqual([...o[0].siglas], ['ESP', 'ADF']);
  assert.equal(JSON.stringify(o.filter(x => x.tipo === 'r').flatMap(x => [...x.siglas])), '["ARG"]');
  // ninguna variante de lugar es de ADF ni de los calendarios que ADF solo asume (ESP, CHL, FRC)
  const lugares = new Set(Object.values(ctx.window.CAL.var).flatMap(v => v.filter(x => x[0] === 'r').flatMap(x => x[1].split(' '))));
  for (const sg of ['ADF', 'CRG', 'ESP', 'CHL', 'FRC']) assert.ok(!lugares.has(sg), sg);
});

test('inicio: Sancta María in sábbato como opción, biografías y nombre de las Vísperas', () => {
  const o = CP.opcionesDia('2026-11-14', '');
  assert.equal(o.length, 2); assert.equal(o[1].f.n, 'Sancta María in sábbato'); assert.ok(o[0].actual);
  const sms = LA.armar('2026-11-14', {cal: '', dia: {'2026-11-14': 'Sancta María in sábbato'}});
  assert.equal(sms.secciones.find(s => s.k === 'himno').opciones[0].n, 'Salve, Madre, en la tierra de mis amores');   // sus elementos propios
  assert.match(sms.secciones.find(s => s.id === 'ab').t.es, /Virgen María/);
  assert.match(sms.secciones.find(s => s.k === 'prosa').t.es, /intercesión de santa María/);
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

test('comunes: las «O bien» se alternan entre celebraciones del mismo común (el himno no: va el de sync y los otros como opción), y en Pascua va lo pascual', () => {
  const X = ctx.window.Completas._, C = { a: { himno: 'H1', lectura: 'L1', opciones: { himno: ['H2'], lectura: ['L2'] }, pascua: { ant: 'A, aleluia' }, ant: 'A' } };
  assert.equal(X.comun(C, 'a', 'San X', false, 0).lectura, 'L1');
  assert.equal(X.comun(C, 'a', 'San X', false, 1).lectura, 'L2');
  assert.equal(X.comun(C, 'a', 'San X', false, 2).lectura, 'L1');
  for (const n of [0, 1, 2]) assert.equal(X.comun(C, 'a', 'San X', false, n).himno, 'H1');
  assert.equal(JSON.stringify(X.himnosComun(C, 'a', 'San X', null, 'H1', { H1: [], H2: [] })), '["H2"]');
  assert.equal(X.comun(C, 'a', 'San X', true, 0).ant, 'A, aleluia');
  const fidel = LA.armar('2027-04-24', '');   // memoria en Pascua, del común de un mártir: responsorio pascual
  assert.match(JSON.stringify(fidel.secciones.find(s => s.k === 'resp').l.es), /[Aa]leluia/);
});

test('ferias de fecha fija (17 al 24 de diciembre, 7 al 12 de enero) y las antífonas «Oh»', () => {
  const W = ctx.window, l17 = LA.armar('2026-12-17', ''), l18 = LA.armar('2026-12-18', '');
  assert.notEqual(l17.secciones.find(s => s.id === 'ab').t.es, l18.secciones.find(s => s.id === 'ab').t.es);
  assert.match(VI.armar('2026-12-17', '').secciones.find(s => s.id === 'ab').t.es, /^Oh Sabiduría/);
  assert.match(VI.armar('2026-12-19', '').secciones.find(s => s.id === 'ab').t.es, /^Oh renuevo/);   // sábado: I Vísperas del domingo
  assert.match(LA.armar('2026-12-24', '').secciones.find(s => s.id === 'a1').t.es, /Belén/);
  assert.notEqual(LA.armar('2026-12-20', '').secciones.find(s => s.id === 'ab').t.es, LA.armar('2026-12-21', '').secciones.find(s => s.id === 'ab').t.es);   // domingo IV: lo del domingo
  // 7 de enero (ADF celebra la Epifanía el 6): lo del 7 de enero del libro, aunque el Ordo lo llame por el día de la semana
  assert.match(LA.armar('2027-01-08', '').secciones.find(s => s.id === 'ab').t.es, /^Tres son los regalos/);
  assert.notEqual(W.Oficio.armar('2026-12-17', '').secciones.filter(s => s.k === 'prosa').pop().t.es,
                  W.Oficio.armar('2026-12-18', '').secciones.filter(s => s.k === 'prosa').pop().t.es);
});

test('Oficio de lectura: ciclo bienal (años impares, I; pares, II; el año litúrgico empieza en Adviento)', () => {
  const W = ctx.window, X = W.Completas._, pl = f => W.Oficio.armar(f, '').secciones.find(s => s.k === 'lectura_larga').titulo;
  assert.equal(X.anioBienal('2026-12-17', { t: 'Adviento' }), 'I'); assert.equal(X.anioBienal('2026-06-10', { t: 'Ordinario' }), 'II');
  assert.match(pl('2026-12-18'), /^GRANDEZA DEL SEÑOR/);                    // 2026-27, año I: Isaías 40
  assert.match(pl('2027-12-18'), /^EL SEÑOR CONTRA LOS DIOSES DE BABILONIA/);  // 2027-28, año II: Isaías 46
});

test('2 de noviembre: Oficio de difuntos, con sus salmos, y la oración propia', () => {
  const W = ctx.window, l = LA.armar('2027-11-02', ''), o = W.Oficio.armar('2027-11-02', ''), t = W.Tercia.armar('2027-11-02', '');
  assert.equal(l.secciones.filter(s => s.k === 'salmo').map(s => s.id).slice(0, 2).join(' '), ['salmo-50', 'cantico-is-38-10-14-17-20'].join(' '));
  assert.match(l.secciones.filter(s => s.k === 'prosa').pop().t.es, /resurrección de Jesucristo/);
  assert.equal(o.secciones.filter(s => s.k === 'salmo').map(s => s.id).join(' '), ['salmo-39-2-14-17-18-i', 'salmo-39-2-14-17-18-ii', 'salmo-41'].join(' '));
  assert.match(o.secciones.filter(s => s.k === 'lectura_larga').pop().titulo, /MURAMOS CON CRISTO/);
  assert.equal(t.secciones.filter(s => s.k === 'salmo').map(s => s.id).join(' '), ['salmo-69', 'salmo-84', 'salmo-85'].join(' '));
  assert.ok(!o.secciones.some(s => s.k === 'tedeum'));
  assert.match(t.secciones.find(s => s.k === 'himno').opciones[0].n, /Dejad que el grano|Camino del sepulcro/);   // himno del Oficio de difuntos
});

test('Oficio de difuntos (botón del inicio) e invitatorio a elección', () => {
  const W = ctx.window, M = W.Completas._.modo;
  M.difuntos = true;
  const l = LA.armar('2027-03-10', ''), o = W.Oficio.armar('2027-03-10', ''), v = VI.armar('2027-03-13', '');   // (un sábado: no pasa a las I Vísperas)
  M.difuntos = false;
  assert.equal(l.secciones.filter(s => s.k === 'salmo').map(s => s.id).slice(0, 2).join(' '), 'salmo-50 cantico-is-38-10-14-17-20');
  assert.equal(o.secciones.filter(s => s.k === 'salmo').map(s => s.id).join(' '), 'salmo-39-2-14-17-18-i salmo-39-2-14-17-18-ii salmo-41');
  assert.ok(!v.primeras && !o.secciones.some(s => s.k === 'tedeum'));
  M.inv = false; assert.ok(!LA.armar('2026-11-15', '').secciones.some(s => s.k === 'salmoinv')); M.inv = undefined;   // domingo sin invitatorio
  M.inv = true; assert.ok(LA.armar('2026-11-17', '').secciones.some(s => s.k === 'salmoinv')); M.inv = undefined;     // para el Oficio, cualquier día
  assert.ok(LA.armar('2026-11-15', '').secciones.some(s => s.k === 'salmoinv') && !LA.armar('2026-11-17', '').secciones.some(s => s.k === 'salmoinv'));
});

test('Cántico Ap 19: sus «Aleluia» van aparte (la app los muestra según se cante o se recite)', () => {
  const c = VI.armar('2026-11-15', '').secciones.find(s => s.id === 'cantico-ap-19-1-2-5-7');
  assert.equal(c.aleluyas.length, 4); assert.ok(c.aleluyas.every(e => e.length === 2 && e.every(l => !/aleluia/i.test(l))));
});

test('salmos en español: asterisco y flexa (de a dos; sobra uno: los tres últimos, o los tres primeros si un punto los cierra)', () => {
  const X = ctx.window.Completas._, v = t => X.versosDe([t]).versos.join(' | ');
  assert.equal(v('a,\nb,\nc,\nd,\ne.'), 'a, * b, | c, † d, * e.');
  assert.equal(v('a,\nb,\nc.\nd,\ne.'), 'a, † b, * c. | d, * e.');
  assert.equal(v('a:\nb,\nc.'), 'a: * b, ¶ c.');
  assert.equal(v('a,\nb:\nc.'), 'a, † b: * c.');
  assert.equal(v('Anuncien todos los pueblos sus maravillas\nb,\nc;\nd,\ne\nf.'), 'Anuncien todos los pueblos sus maravillas † b, * c; | d, † e * f.');
  // marcados a mano en la base: manda lo marcado (renglón sin signo antes del metro: aparte, sin flexa)
  assert.equal(v('a, *\nb,\nc,\nd, *\ne.'), 'a, * b, | c, ¶ d, * e.');
  assert.equal(v('a †\nb *\nc:\nd, *\ne.'), 'a † b * c: | d, * e.');
  const ef = ctx.window.VISPERAS.salmos['cantico-ef-1-3-10'], vs = X.versosDe(ef.texto).versos;
  assert.ok(vs.includes('que tan generosamente nos ha concedido ¶ en su querido Hijo, * redunde en alabanza suya.'));
  assert.ok(vs.includes('Éste es el plan † que había proyectado realizar por Cristo * cuando llegase el momento culminante:'));
  assert.equal(X.versosDe(ctx.window.LAUDES.salmos['salmo-150'].texto).versos.at(-1), 'Todo ser que alienta, * alabe al Señor.');
});

test('comunes y propio del libro: oración propia, segunda lectura y oficio entero cuando lo hay', () => {
  const W = ctx.window;
  const blas = LA.armar('2027-02-03', '');
  assert.match(blas.secciones.filter(s => s.k === 'prosa').pop().t.es, /^Escucha, Señor, las súplicas de tu pueblo/);   // oración propia
  assert.match(blas.dia.nota, /Oración propia/);
  assert.match(W.Oficio.armar('2027-02-03', '').secciones.find(s => s.k === 'lectura_larga' && s.autor).autor, /san Agustín/);
  // Jesucristo, Sumo y Eterno Sacerdote: oficio propio entero
  const ses = W.Oficio.armar('2026-05-28', '');
  assert.match(ses.dia.titulo, /Sumo y Eterno Sacerdote/); assert.equal(ses.secciones.filter(s => s.k === 'salmo').length, 3);
  // oración del común con el nombre, sin «N.»
  const agata = LA.armar('2027-02-05', '');   // ahora con oración propia del libro (allí, «santa Águeda»)
  assert.match(agata.secciones.filter(s => s.k === 'prosa').pop().t.es, /santa Águeda/);
  const eduardo = LA.armar('2027-10-13', ''), o = eduardo.secciones.filter(s => s.k === 'prosa').pop().t.es;   // ADF, sin oración propia
  assert.match(o, /san Eduardo de Inglaterra/);
  // colecta del Misal cargada como oración propia (CRU, 19/11/2026)
  assert.match(LA.armar('2027-07-17', '').secciones.filter(s => s.k === 'prosa').pop().t.es, /^Dios nuestro, que con la abundancia de tu gracia ayudaste a san Enrique/); assert.ok(!/\bN\./.test(o) && !/\[/.test(o));
  // Santa María en sábado: Oficio con su himno y su segunda lectura
  const smo = W.Oficio.armar('2026-11-14', {cal: '', dia: {'2026-11-14': 'Sancta María in sábbato'}});
  assert.equal(smo.secciones.find(s => s.k === 'himno').opciones[0].n, 'Rosa entre rosas');
});

test('imágenes de la tarjeta del inicio', () => {
  vm.runInNewContext(readFileSync(new URL('../src/datos/ilustraciones.js', import.meta.url), 'utf8'), ctx);
  const I = ctx.window.ILUS, C = ctx.window.CAL;
  // cada imagen tiene su archivo, y no sobra ninguno
  const archivos = readdirSync(new URL('../src/assets/ilu/', import.meta.url)).filter(f => f.endsWith('.webp')).map(f => f.slice(0, -5)).sort();
  assert.deepEqual(archivos, [...I.img].sort());
  // las celebraciones, domingos, comunes y tiempos que nombra existen
  const nombres = new Set([...C.dias.map(d => C.tabla[d[3]]), ...Object.values(C.var).flatMap(vs => vs.map(v => C.tabla[v[2][3]]))]);
  for (const n of [...Object.keys(I.propias), ...Object.keys(I.domingos)]) assert.ok(nombres.has(n), n);
  for (const k of Object.keys(I.comunes)) assert.ok(['dedicacion','virgen-maria','apostoles','varios-martires','un-martir','pastores','doctores','virgenes','santos-varones','santas-mujeres','religiosos','caridad','educadores'].includes(k), k);
  for (const k of Object.keys(I.tiempos)) assert.ok(['adviento','navidad','cuaresma','pascua'].includes(k), k);
  // todos los días tienen imagen
  for (let f = C.desde; f <= C.hasta; f = CP.masDias(f, 1)) assert.ok(CP.ilustracion(f, '', 0) != null, f);
  const en = (f, h) => CP.ilustracion(f, '', h), seis = f => new Set([0, 1, 2, 3, 4, 5].map(h => en(f, h)));
  // propia del día, que cambia en cada hora: Viernes Santo
  assert.ok(I.propias['Viernes Santo de la Pasión del Señor'].includes(en('2027-03-26', 2)));
  assert.ok(seis('2027-03-26').size > 1);
  // domingo, según el ciclo: IV de Adviento de 2026 (ciclo B) → la Anunciación
  assert.equal(CP.ciclo('2026-12-20'), 'B');
  assert.ok(I.domingos['IV Domingo de Adviento'].B.includes(en('2026-12-20', 0)));
  // en Cuaresma, una memoria con imagen propia la conserva; sin propia, va la de Cuaresma y no la del común
  assert.ok(I.propias['San Blas, obispo y mártir'].includes(en('2027-02-03', 0)));   // 2027: San Blas cae fuera de Cuaresma
  const cua = []; for (let f = '2027-02-10'; f <= '2027-03-20'; f = CP.masDias(f, 1)) { const r = CP.diaCal(f, ''); if (r.t === 'Cuaresma' && !I.propias[r.n] && !I.domingos[r.n]) cua.push(f); }
  assert.ok(cua.length > 20);
  for (const f of cua) assert.ok(I.tiempos.cuaresma.includes(en(f, 0)), f);
  // fuera de Cuaresma, una memoria sin propia toma la de su común
  let memorias = 0;
  for (let f = '2027-06-01'; f <= '2027-10-31'; f = CP.masDias(f, 1)) {
    const r = CP.diaCal(f, ''), c = I.comunDe[r.n];
    if (r.t === 'Ordinario' && c && I.comunes[c] && !I.propias[r.n] && !I.domingos[r.n]) { assert.ok(I.comunes[c].includes(en(f, 0)), r.n); memorias++; }
  }
  assert.ok(memorias > 10, memorias);
  // las dedicaciones sin común propio toman la imagen de la dedicación de una iglesia
  assert.equal(CP.diaCal('2026-11-18', '').n, 'Dedicación de las Basílicas de San Pedro y San Pablo');
  for (const h of [0, 1, 2, 3, 4, 5]) assert.ok(I.comunes.dedicacion.includes(en('2026-11-18', h)));
  assert.ok(!I.img.includes('camello'));
  // franjas del reloj
  const a = h => CP.franjaHoraria(new Date(2027, 0, 1, h, 0));
  assert.deepEqual([2, 6, 9, 12, 15, 18, 22].map(a), [5, 0, 1, 2, 3, 4, 5]);
});

// ---------- Himnos en gregoriano de Laudes y Vísperas (base/gregoriano/himnos.yaml) ----------
test('himnos gregorianos de Laudes y Vísperas: opción después del himno en español, en sus días', () => {
  const hg = (A, f) => { const o = A.armar(f, 'ARG').secciones.find(s => s.k === 'himno').opciones; assert.equal(o[0].lang, 'es'); const g = o.find(x => x.lang === 'la' && x.gabc); return g ? g.n : ''; };
  assert.equal(hg(VI, '2026-11-14'), 'Deus, Creátor ómnium');          // I Vísperas, domingo de la semana I
  assert.equal(hg(LA, '2026-11-15'), 'Ætérne rerum Cónditor');
  assert.equal(hg(VI, '2026-11-15'), 'Lucis Creátor óptime');
  assert.equal(hg(VI, '2026-11-07'), 'Rerum Deus fons ómnium');         // semana IV
  assert.equal(hg(LA, '2026-11-08'), 'Ecce iam noctis');
  assert.equal(hg(VI, '2026-11-08'), 'O lux beáta Trínitas');
  assert.equal(hg(VI, '2026-11-21'), 'Te sæculórum Príncipem');         // Cristo Rey: I y II Vísperas
  assert.equal(hg(VI, '2026-11-22'), 'Te sæculórum Príncipem');
  assert.equal(hg(LA, '2026-11-22'), '');
  assert.equal(hg(VI, '2026-11-28'), 'Creátor alme síderum');           // Adviento
  assert.equal(hg(LA, '2026-12-06'), 'En clara vox redárguit');
  assert.equal(hg(VI, '2026-12-24'), 'Iesu, Redémptor ómnium');         // Navidad
  assert.equal(hg(VI, '2026-12-25'), 'Iesu, Redémptor ómnium');
  assert.equal(hg(VI, '2027-05-15'), 'Veni Creátor Spíritus');          // Pentecostés
  assert.equal(hg(VI, '2027-05-16'), 'Veni Creátor Spíritus');
  assert.equal(hg(LA, '2026-11-10'), '');                               // ferias: solo el himno en español
  assert.equal(hg(LA, '2027-01-24'), 'O gloriósa Vírginum');            // domingo reemplazado por una solemnidad de la Virgen
  // Fiestas y solemnidades de la Virgen María: O gloriósa Vírginum en Laudes, Ave maris stella en Vísperas (también las I)
  assert.equal(hg(LA, '2026-12-08'), 'O gloriósa Vírginum');            // Inmaculada (con himno propio en español)
  assert.equal(hg(VI, '2026-12-07'), 'Ave maris stella');               // I Vísperas de la Inmaculada
  assert.equal(hg(VI, '2026-12-08'), 'Ave maris stella');
  assert.equal(hg(VI, '2027-05-31'), 'Ave maris stella');               // Visitación (fiesta)
  assert.equal(hg(LA, '2027-08-15'), 'O gloriósa Vírginum');            // Asunción
  assert.equal(hg(VI, '2026-03-25'), 'Ave maris stella');               // Anunciación: II Vísperas
  assert.equal(hg(LA, '2026-03-25'), '');
  assert.equal(hg(LA, '2027-02-02'), '');                               // Presentación del Señor: no
});

test('himnos gregorianos: latín con i y tildes; la traducción por frases cubre la partitura', () => {
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  const pal = g => g.split('%%')[1].replace(/\([^)]*\)/g, '').replace(/<[^>]+>|\[[^\]]*\]|[{}]/g, '').split(/\s+/).map(norm).filter(Boolean).join(' ');
  const H = { ...LD.gregoriano.himnos.himnos, ...ctx.window.VISPERAS.gregoriano.himnos.himnos };
  assert.equal(Object.keys(H).length, 13);
  for (const [k, h] of Object.entries(H)) {
    const pares = h.estrofas.flat(2).concat([h.amen]);
    assert.equal(pares.flatMap(p => p[0].split(/\s+/)).map(norm).join(' '), pal(h.gabc), k);
    assert.ok(pares.every(p => p[0] && p[1]), k);
    assert.ok(!/[jJ]/.test(letra(h.gabc)), k);
    assert.ok(!/aleluya/i.test(JSON.stringify(h)), k);
    const sinTilde = palabrasGabc(h.gabc).filter(([w, n]) => n >= 3 && !/[áéíóúýǽÁÉÍÓÚÝǼ́]/.test(w)).map(x => x[0]);
    assert.deepEqual(sinTilde, [], k);
    assert.ok(h.estrofas.every(e => e.length === 4), k);                 // cuatro versos por estrofa (la versión recitada)
  }
  const o = ctx.window.Visperas.armar('2026-11-15', 'ARG').secciones.find(s => s.k === 'himno').opciones[1];
  assert.equal(o.rec.length, 5); assert.equal(o.rec.at(-1).versos.at(-1)[0][0], 'Amen.');
  assert.equal(o.glosa.length, o.rec.flatMap(l => l.pares).length);
});

test('comunes: se elige la variante que indica la rúbrica, por el nombre de la celebración', () => {
  const X = ctx.window.Completas._;
  const antEv = (A, f) => { const s = A.armar(f, '').secciones, i = s.findIndex(x => x.k === 'cantico'); return s[i - 1].t.es; };
  // santa Gertrudis, virgen (no mártir): no la antífona de una virgen mártir
  assert.match(antEv(VI, '2026-11-16'), /^Ven, esposa de Cristo/);
  assert.match(antEv(LA, '2026-11-16'), /^Ésta es la virgen prudente/);
  assert.equal(X.rubricaVale('Para una santa virgen:', 'Santa Inés, virgen y mártir'), false);
  assert.equal(X.rubricaVale('Para varios santos:', 'Santos Mauro y Plácido, religiosos'), true);
  assert.equal(X.rubricaVale('Para un santo presbítero:', 'San Cayetano, presbítero'), true);
  assert.equal(X.rubricaVale('En tiempo de cuaresma Para un solo mártir:', 'San Blas, obispo y mártir'), false);
  assert.equal(X.rubricaVale('opcion: 2', 'San Blas, obispo y mártir'), false);
  // todo doctor toma del común de doctores; el nombre va en lugar de «N.» también fuera de la oración
  const bel = JSON.stringify(VI.armar('2027-09-17', '').secciones);
  assert.match(bel, /Oh doctor admirable, luz de la Iglesia santa, san Roberto, fiel/);
  assert.ok(!/\bN\./.test(bel) && !/\bN\./.test(JSON.stringify(LA.armar('2026-11-16', '').secciones)));
  assert.match(JSON.stringify(VI.armar('2026-11-16', '').secciones), /la fiesta de santa Gertrudis, virgen,/);
  assert.match(LA.armar('2027-09-18', '').dia.nota || '', /vírgenes/i);   // santa Hildegarda: solo del común de vírgenes
  // doctores varones (y san Bernardo, «abad» en el calendario ADF): del común de doctores; las doctoras vírgenes, del de vírgenes (25/11/2026)
  assert.ok(X.esDoctor('San Agustín, obispo y doctor de la Iglesia') && X.esDoctor('San Bernardo, abad') && !X.esDoctor('Santa Teresa de Jesús, virgen y doctora de la Iglesia') && !X.esDoctor('San Blas, obispo y mártir'));
  assert.match(LA.armar('2025-08-20', '').dia.nota, /del Común de doctores de la Iglesia\.$/);
  for (const f of ['2025-08-20', '2025-06-13', '2025-10-15', '2025-10-01', '2026-04-29', '2025-08-11']) assert.ok(!(LA.armar(f, '').dos || { ops: [] }).ops.some((o, i) => i > 0), f);   // sin elección
  // en Pascua, lo que no es propio conserva su «Aleluia» (santa Catalina de Siena, del común de vírgenes)
  const cat = ctx.window.Oficio.armar('2027-04-29', '').secciones.find(s => s.k === 'ant' && s.id === 'a1');
  assert.match(cat.t.es, /Aleluia\.$/);
  // Basílicas de san Pedro y san Pablo: del común de apóstoles, no los textos del 29 de junio
  const bas = VI.armar('2026-11-18', '');
  assert.match(bas.dia.nota || '', /apóstoles/i);
  assert.ok(!JSON.stringify(bas.secciones).includes('Yo he rogado por ti, Pedro'));
  assert.match(bas.secciones.filter(s => s.k === 'prosa').pop().t.es, /^Defiende a tu Iglesia, Señor, con la protección de los apóstoles/);
  // y lo propio del libro: antífonas del Benedictus y del Magnificat
  const antEvB = (A, f) => { const s = A.armar(f, '').secciones, i = s.findIndex(x => x.k === 'cantico'); return s[i - 1].t.es; };
  assert.match(antEvB(LA, '2026-11-18'), /^Pedro, apóstol, y Pablo, maestro de los gentiles/);
  assert.match(antEvB(VI, '2026-11-18'), /^Los cuerpos de los santos fueron sepultados en paz/);
  // preces: la respuesta va una vez, con ℟, y no pegada al final de cada intención
  for (const [A, f] of [[LA, '2026-11-18'], [VI, '2027-01-20']]) {
    const p = A.armar(f, '').secciones.find(s => s.k === 'preces');
    assert.ok(p.preces.every(x => !x.filter(Boolean).at(-1).includes(p.respuesta.replace(/\.$/, ''))), f);
    assert.ok(!JSON.stringify(p).includes('Salkvador'));
  }
  // san Alberto Magno: del común de doctores, completado por el de pastores
  const alberto = VI.armar('2027-11-17', '');
  assert.match(alberto.dia.nota || '', /doctores/i);
});

test('Comunes de los santos (botón del inicio): común, caso y grado; cualquier opción de cada elemento', () => {
  const W = ctx.window, X = W.Completas._, M = X.modo;
  const H = { laudes: LA, visperas: VI, oficio: W.Oficio, tercia: W.Tercia, sexta: W.Sexta, nona: W.Nona };
  const ora = r => r.secciones.filter(s => s.k === 'prosa').pop().t.es;
  const con = (sel, f, h, elige = {}) => { M.comun = { ...X.comunSantos(sel), elige, alts: {} }; const r = H[h].armar(f, ''); const a = M.comun.alts; M.comun = null; return [r, a]; };
  // todos los comunes y casos, en tres grados y en cuatro tiempos: se arma, sin «[falta», sin nota y con «N.»
  X.COMUNES_SANTOS.forEach((G, g) => G.casos.forEach((C, c) => {
    for (const grado of ['Memoria', 'Fiesta', 'Solemnidad']) for (const f of ['2026-11-24', '2026-12-09', '2027-03-10', '2027-04-20']) for (const h of Object.keys(H)) {
      const [r] = con({ g, c, grado }, f, h);
      assert.ok(r && !JSON.stringify(r.secciones).includes('[falta'), `${G.n} · ${C.n} · ${grado} · ${f} · ${h}`);
      assert.equal(r.dia.nota, '');
    }
  }));
  // pastores, un obispo: su oración; las demás, a elección (cualquiera, sin rotar)
  const [l, al] = con({ g: 4, c: 1, grado: 'Memoria' }, '2026-11-24', 'laudes');
  assert.match(ora(l), /^Señor, tú que colocaste a san N\. en el número de los santos pastores/);
  const ops = al['laudes|oracion'].ops; assert.ok(ops.length >= 5 && ops[al['laudes|oracion'].i].n === 'Para un santo obispo');
  const [l2] = con({ g: 4, c: 1, grado: 'Memoria' }, '2026-11-24', 'laudes', { 'laudes|oracion': 0 });
  assert.match(ora(l2), /^Dios todopoderoso y eterno, que quisiste que san N\., papa/);
  // varias vírgenes: la antífona del Benedictus y la oración en plural; en femenino, «santa N.»
  const [v, av] = con({ g: 6, c: 1, grado: 'Fiesta' }, '2026-11-24', 'laudes');
  assert.equal(av['laudes|ant_benedictus'].ops[av['laudes|ant_benedictus'].i].n, 'Para varias santas vírgenes');
  assert.match(ora(v), /santas vírgenes N\. y N\./);
  const [o] = con({ g: 8, c: 2, grado: 'Fiesta' }, '2026-11-24', 'oficio');
  assert.match(ora(o), /santa N\./); assert.ok(o.secciones.some(s => s.id === 'tedeum'));
  // grado: memoria, salmos de la feria; fiesta, los del común; solemnidad, también I Vísperas
  const sal = r => r.secciones.filter(s => s.k === 'salmo').map(s => s.id).join(' ');
  assert.notEqual(sal(con({ g: 4, c: 1, grado: 'Memoria' }, '2026-11-24', 'laudes')[0]), sal(con({ g: 4, c: 1, grado: 'Fiesta' }, '2026-11-24', 'laudes')[0]));
  const [i1] = con({ g: 4, c: 1, grado: 'Solemnidad', primeras: true }, '2026-11-24', 'visperas');
  assert.ok(i1.primeras);
  // tiempo pascual: con «Aleluia»; Virgen María en Adviento: la oración de Adviento
  assert.match(con({ g: 4, c: 1, grado: 'Fiesta' }, '2027-04-20', 'laudes')[0].secciones.find(s => s.k === 'ant' && s.t).t.es, /Aleluia/);
  assert.match(ora(con({ g: 1, c: 0, grado: 'Memoria' }, '2026-12-05', 'laudes')[0]), /Verbo inefable/);
  // sin el modo, nada cambia
  assert.ok(!M.comun && LA.armar('2026-11-24', '').dia.titulo !== 'San N., obispo');
});

test('himnos de los comunes: el de sync primero y los otros como opción en la hora; San Juan XXIII, del común de pastores', () => {
  const W = ctx.window, ops = r => r.secciones.find(s => s.k === 'himno').opciones.filter(o => o.lang === 'es').map(o => o.n);
  // Santa Isabel de Hungría (19 de noviembre): Vísperas del común de santas mujeres
  assert.equal(ops(VI.armar('2026-11-19', '')).join(' | '), 'Un amor casto y puro | Finísimo fue el lino con que ella');
  const j = ['laudes', 'visperas'].map(h => ({ laudes: LA, visperas: VI }[h].armar('2027-10-11', '')));
  assert.equal(j[0].dia.titulo, 'San Juan XXIII, papa');
  assert.equal(ops(j[0])[0], 'Cristo, cabeza, rey de los pastores');
  assert.equal(ops(j[1])[0], 'Cantemos al Señor con alegría');
});

test('Santa María Magdalena: himnos propios (del libro en Laudes y Vísperas; la secuencia pascual en el Oficio)', () => {
  const W = ctx.window, h = H => H.armar('2027-07-22', '').secciones.find(s => s.k === 'himno').opciones[0];
  assert.equal(h(LA).n, 'Al levantarse la aurora');
  assert.equal(h(VI).n, '«¿Qué viste en el huerto?');
  assert.equal(h(W.Oficio).n, '«¿Qué has visto de camino');
  for (const H of [LA, VI, W.Oficio]) assert.ok(h(H).est.length > 3);
});

// ---------- Himnos latinos recitados (base/himnos/latinos.yaml y latinos_cuando.yaml) ----------
test('himnos latinos: opción recitada después del español y del gregoriano, del tiempo o del común, con el caso', () => {
  const W = ctx.window, X = CP._;
  const lat = (A, f) => A.armar(f, '').secciones.find(s => s.k === 'himno').opciones.filter(o => o.lat);
  const n = (A, f) => lat(A, f).map(o => o.n).join(' / ');
  assert.equal(n(LA, '2026-12-02'), 'Vox clara ecce íntonat');                          // Adviento, hasta el 16
  assert.equal(n(VI, '2026-12-18'), 'Verbum salútis ómnium');                           // desde el 17
  assert.equal(n(VI, '2026-11-28'), 'Cónditor alme síderum');                           // I Vísperas: queda también el gregoriano
  assert.ok(VI.armar('2026-11-28', '').secciones.find(s => s.k === 'himno').opciones.some(o => o.id === 'greg'));
  assert.equal(n(VI, '2027-01-05'), 'Hostis Heródes ímpie');                            // I Vísperas de la Epifanía
  assert.equal(n(LA, '2027-03-15'), 'Iam, Christe, sol iustítiæ / En acétum, fel, arúndo');   // V semana: también los de Semana Santa
  assert.equal(n(W.Tercia, '2027-03-26'), 'Salva, Redémptor, plasma tuum nóbile');
  assert.equal(n(VI, '2027-04-06'), 'Ad cenam Agni próvidi / O rex ætérne, Dómine');    // ferias de Pascua: «si se prefiere»
  assert.equal(n(VI, '2027-04-01'), 'Ad cenam Agni próvidi');                           // Octava
  assert.equal(n(LA, '2027-05-08'), 'Optátus votis ómnium');                            // después de la Ascensión
  assert.equal(n(VI, '2027-05-15'), 'Veni, creátor Spíritus (recitado)');               // I Vísperas de Pentecostés, con el gregoriano
  // segunda etapa: Tiempo Ordinario (semana del salterio y día), solemnidades del Señor y propios de santos
  assert.equal(n(LA, '2026-11-20'), 'Ætérna cæli glória');                              // viernes, semana I/III
  assert.equal(n(W.Oficio, '2027-06-27'), 'Dies ætásque céteris (de día) / Primo diérum ómnium (de noche)');
  assert.equal(n(VI, '2027-06-28'), 'Aurea luce et decóre róseo');                        // I Vísperas de san Pedro y san Pablo
  assert.equal(n(LA, '2026-11-30'), 'Captátor olim píscium');                             // san Andrés: el mismo himno en las tres Horas
  assert.equal(n(VI, '2028-06-11'), 'Imménsa et una, Trínitas');
  // Te Deum en latín: opción en las dos partes, con la misma clave de elección y traducción en cada renglón
  const td = W.Oficio.armar('2027-06-27', '').secciones.filter(x => x.k === 'himno' && x.opciones[0].id === 'tedeum');
  assert.equal(td.length, 2); assert.ok(td.every(x => x.opciones.some(o => o.id === 'lat' && o.lit.flat().every(Boolean))));
  assert.equal(n(LA, '2026-11-10'), 'Doctor ætérnus cóleris piúsque');                 // San León Magno: del común de doctores
  // Completas: del tiempo (Cuaresma, según la semana)
  const nc = f => CP.armar(f, '').secciones.find(s => s.k === 'himno').opciones.filter(o => o.lat).map(o => o.n).join(' / ');
  assert.equal(nc('2027-02-15'), 'Te lucis ante términum (recitado)');
  assert.equal(nc('2027-02-22'), 'Christe, qui, splendor et dies');
  // comunes: pastores (papa), mártir (una santa), difuntos (una difunta o varios)
  const p = lat(VI, '2027-10-11')[0];
  assert.equal(p.n, 'Vir celse, forma fúlgida'); assert.equal(p.est[3][0], 'Tu Petri ovíle cǽlitus');
  assert.equal(p.est.length, p.lit.length); assert.ok(p.est.every((e, i) => e.length === p.lit[i].length && p.lit[i].every(Boolean)));
  assert.equal(p.amen, 'Amen.');
  // una virgen mártir: solo los del común elegido (vírgenes, por defecto; o el de un mártir, en femenino)
  assert.equal(n(LA, '2027-11-22'), 'Aptáta, virgo, lámpade');
  X.modo.comunDia = { f: '2027-11-22', id: 'un-martir' };
  try {
    assert.equal(n(LA, '2027-11-22'), 'O castitátis sígnifer / Martyr Dei, quæ únicum');
    assert.equal(lat(LA, '2027-11-22')[1].est[0][3], 'victrix fruens cæléstibus,');
  } finally { X.modo.comunDia = null; }
  assert.equal(n(VI, '2027-11-02'), 'Imménsæ rex poténtiæ (varios difuntos)');
  X.modo.difuntos = true;
  try {
    assert.equal(n(LA, '2027-06-15'), 'Spes, Christe, nostræ véniæ / Spes, Christe, nostræ véniæ (una difunta) / Spes, Christe, nostræ véniæ (varios difuntos)');
    assert.ok(/Tercia, estrofas 1, 4 y 5/.test(lat(W.Tercia, '2027-06-15')[0].rub));
  } finally { X.modo.difuntos = false; }
});

// ---------- Antífonas propias en gregoriano (base/gregoriano/propios.yaml) ----------
test('antífonas «Oh» y en lugar del responsorio: en gregoriano si se canta, con traducción y latín con i', () => {
  const sec = (A, f, id) => A.armar(f, 'ARG').secciones.find(s => s.id === id);
  const oh = { '2026-12-17': 'o-sapientia', '2026-12-18': 'o-adonai', '2026-12-19': 'o-radix-iesse', '2026-12-20': 'o-clavis-david',
    '2026-12-21': 'o-oriens', '2026-12-22': 'o-rex-gentium', '2026-12-23': 'o-emmanuel' };
  for (const [f, k] of Object.entries(oh)) {
    const a = sec(VI, f, 'ab'), c = VI.armar(f, 'ARG').secciones.find(s => s.k === 'cantico');
    assert.equal(a.greg, k, f); assert.ok(/^Oh /.test(a.t.es), f);              // el español sigue para el recitado
    if (k) { assert.ok(a.soloCanto && a.glosa.length && /\(::\)\s*$/.test(a.gabc) && !/<eu>/.test(a.gabc)); assert.equal(c.modo, '2D', f);
             assert.ok(/<b>/.test(a.gabc.split('*')[1]) && !/<b>/.test(a.gabc.split('*')[0].split('%%')[1]), 'negrita desde el asterisco');
             assert.ok(!/\*/.test(letra(a.gabcRep)) && /<b>Sa<\/b>|<b>/.test(a.gabcRep), 'repetición sin asterisco'); }
  }
  assert.equal(sec(LA, '2026-12-17', 'ab').greg, undefined);                  // Laudes: el Benedictus, en español
  const rb = { 'VI:2027-03-25': 'christus-factus-est-1', 'LA:2027-03-26': 'christus-factus-est-2', 'VI:2027-03-26': 'christus-factus-est-2',
    'LA:2027-03-27': 'christus-factus-est-3', 'VI:2027-03-27': 'christus-factus-est-3', 'LA:2027-03-29': 'haec-dies', 'VI:2027-04-03': 'haec-dies' };
  for (const [hf, k] of Object.entries(rb)) { const [h, f] = hf.split(':'); assert.equal(sec(h === 'LA' ? LA : VI, f, 'rb').greg, k, hf); }
  for (const [f, k] of [['2027-03-25', 'christus-factus-est-1'], ['2027-03-26', 'christus-factus-est-2'], ['2027-03-27', 'christus-factus-est-3'], ['2027-03-30', 'haec-dies']])
    assert.equal(CP.armar(f, 'ARG').secciones.find(s => s.id === 'rb').greg, k, 'Completas ' + f);
  assert.ok(!/Confit/.test(sec(LA, '2027-03-29', 'rb').gabc));                // Hæc dies sin el versículo
  // la traducción cubre la partitura, palabra por palabra
  const norm = w => w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-zæœ]/g, '');
  const pal = g => g.split('%%')[1].replace(/\([^)]*\)/g, '').replace(/<[^>]+>|\[[^\]]*\]|[{}*]/g, '').replace(/[VR]\/\./g, '').split(/\s+/).map(norm).filter(Boolean).join(' ');
  const P = B.gregoriano_propios;
  for (const p of [...P.magnificat, ...P.responsorio]) {
    assert.equal(p.traduccion.flatMap(x => x[0].split(/\s+/)).map(norm).filter(Boolean).join(' '), pal(p.gabc), p.id);
    assert.ok(!/[jJ]/.test(letra(p.gabc)), p.id);
    assert.ok(!/ë/.test(letra(p.gabc)), p.id);                                // «Ísrael», sin diéresis
    const sinTilde = palabrasGabc(p.gabc).filter(([w, n]) => n >= 3 && !/[áéíóúýǽÁÉÍÓÚÝǼ́]/.test(w)).map(x => x[0]);
    assert.deepEqual(sinTilde, [], p.id);
  }
});

// ---------- Correcciones del 25/11/2026 ----------
test('antífonas de salmos y cánticos: asterisco de la entonación (primera palabra o frase con sentido)', () => {
  const A = CP._.asteriscoAnt, corte = t => { const p = A(t); return p < 0 ? null : t.slice(0, p); };
  const casos = {
    'No temáis, yo he vencido al mundo.': 'No temáis,', 'No seréis vosotros los que habléis.': 'No seréis', 'No, Señor.': 'No,',
    'En una sola víctima celebramos un doble triunfo.': 'En una sola víctima', 'El buen Pastor dio la vida.': 'El buen Pastor', 'Dichosos vosotros, los pobres.': 'Dichosos', 'En mi angustia te busco, Señor, y extiendo las manos sin descanso.': 'En mi angustia',
    'Mi corazón está firme, Dios mío, mi corazón está firme.': 'Mi corazón', 'El Señor reina, la tierra goza.': 'El Señor',
    'El que se aborrece a sí mismo en este mundo se guardará para la vida eterna.': 'El que se aborrece',
    'Yo soy pobre, pero el Señor cuida de mí.': 'Yo', 'Me asalta el temor y el terror: hazme caso y respóndeme, Señor.': 'Me asalta',
    'He examinado mi camino, para enderezar mis pies a tus preceptos.': 'He examinado',
    'Que Dios ilumine su rostro sobre nosotros y nos bendiga.': 'Que Dios', 'Señor, Dios mío, a ti grité, y tú me sanaste.': 'Señor,',
    'De noche, Dios mío, mi alma te desea.': 'De noche,', 'Yo mismo apacentaré mis ovejas.': 'Yo', 'Mi corazón está firme, Dios mío.': 'Mi corazón', 'Dios mío, ven en mi auxilio.': 'Dios mío,',
    'El ángel Gabriel saludó a María.': 'El ángel', 'Todos los pueblos te alaben.': 'Todos', 'Santa María, madre de Dios, ruega por nosotros.': 'Santa María,',
    'Alégrate, María, llena de gracia, el Señor está contigo.': 'Alégrate,', 'En medio de la tempestad, Jesús dormía.': 'En medio',
    'Padre justo, si es verdad que el mundo no te ha conocido.': 'Padre', '¿Quién subirá al monte del Señor?': '¿Quién',
    'En tu juicio, Señor, acuérdate de la misericordia.': 'En tu juicio,',
  };
  for (const [t, c] of Object.entries(casos)) assert.equal(corte(t), c, t);
  // la primera vez lleva asterisco; la repetición final, no (toda en negrita)
  const S = VI.armar('2026-11-25', 'ARG').secciones.filter(s => s.k === 'ant');
  assert.ok(S.filter(s => s.id).every(s => s.ast) && S.filter(s => s.rep).every(s => !s.ast));
  assert.ok(!LA.armar('2026-11-08', 'ARG').secciones.find(s => s.id === 'ai').ast);   // invitatorio: sin asterisco
});

test('Santa Catalina de Alejandría: común de vírgenes (virgen mártir); San Clemente: responsorio de Vísperas del común', () => {
  const v = VI.armar('2026-11-25', 'ARG');
  assert.match(v.dia.nota, /del Común de vírgenes: para una virgen mártir\.$/);
  for (const f of ['2027-05-28', '2027-07-06', '2027-11-22', '2027-12-13', '2027-02-05'])   // toda virgen mártir, del común de vírgenes
    assert.match(VI.armar(f, 'ARG').secciones.find(s => s.id === 'ab').t.es, /^En una sola víctima|.{0,400}/, f);
  const CC = CP._.comunConCaso;
  assert.equal(CC('Común de pastores', 'San Ildefonso, obispo'), 'Común de pastores: para un santo obispo');
  assert.equal(CC('Común de santos varones o de santas mujeres: para religiosos', 'Santa Rita de Cascia, religiosa'), 'Común de santas mujeres: para una santa religiosa');
  assert.equal(CC('Común de mártires: para un mártir', 'San Blas, obispo y mártir'), 'Común de mártires: para un mártir');
  assert.match(v.secciones.find(s => s.id === 'ab').t.es, /^En una sola víctima/);           // la de una virgen mártir
  assert.match(VI.armar('2026-11-23', 'ARG').secciones.find(s => s.k === 'resp').l.es[0][1], /^Oh Dios, nos pusiste a prueba/);
});

test('preces de Vísperas: cada intención por separado (no dos pegadas en una)', () => {
  for (const f of ['2026-11-12', '2026-11-24', '2027-02-06', '2026-09-16', '2026-09-29', '2026-12-12', '2027-01-04']) {
    const p = VI.armar(f, 'ARG').secciones.find(s => s.k === 'preces');
    for (const [a, b] of p.preces) assert.ok(!(b && /[.!?]$/.test(a) && /^\p{Lu}/u.test(b)) && b !== p.respuesta && b !== '', f + ': ' + a);
  }
});

test('virgen mártir: el común (vírgenes o mártires) se elige al comienzo de la hora y vale para todo el día; lo propio queda', () => {
  const W = ctx.window, X = CP._;
  const de = (r, id) => r.secciones[r.secciones.findIndex(s => s.k === 'sec' && s.id === id) + 1];
  // Santa Catalina de Alejandría (toma del común): por defecto, vírgenes; la nota dice el común elegido
  let r = W.Laudes.armar('2026-11-25', '');
  assert.equal(r.dos.actual, 'virgenes');
  assert.equal(r.dos.ops.map(o => o.id).join(' '), 'virgenes un-martir');
  assert.match(r.dia.nota, /del Común de vírgenes: para una virgen mártir\.$/);
  X.modo.comunDia = { f: '2026-11-25', id: 'un-martir' };
  try {
    for (const A of [W.Laudes, W.Visperas, W.Oficio]) {
      r = A.armar('2026-11-25', '');
      assert.equal(r.dos.actual, 'un-martir');
      assert.match(r.dia.nota, /del Común de mártires: para una virgen mártir\.$/);
    }
    assert.equal(W.Laudes.armar('2026-11-26', '').dos.actual, 'pastores');   // la elección es de ese día (San Columbano: pastores, por defecto)
  } finally { X.modo.comunDia = null; }
  // Santa Águeda (propio de sync): lo que era del común de mártires pasa al elegido; la antífona del Benedictus y la oración, propias
  const L1 = W.Laudes.armar('2026-02-05', '');
  X.modo.comunDia = { f: '2026-02-05', id: 'un-martir' };
  let L2;
  try { L2 = W.Laudes.armar('2026-02-05', ''); } finally { X.modo.comunDia = null; }
  assert.equal(L1.dos.actual, 'virgenes'); assert.equal(L2.dos.actual, 'un-martir');
  assert.notEqual(JSON.stringify(de(L1, 'lectura')), JSON.stringify(de(L2, 'lectura')));
  assert.equal(JSON.stringify(de(L1, 'oracion')), JSON.stringify(de(L2, 'oracion')));
  assert.match(L1.dia.nota, /^Antífona del Benedictus y oración propias; lo demás, del Común de vírgenes/);
  // otras celebraciones: sin elección (también los doctores: «pastores o doctores» es un común que completa al otro)
  assert.equal(W.Laudes.armar('2026-11-24', '').dos, null);
  assert.equal(W.Laudes.armar('2026-11-17', '').dos, null);   // San Alberto Magno
  // pastores mártires (San Blas): sin elección; San Leandro: pastores o religiosos
  assert.equal(W.Laudes.armar('2026-02-03', '').dos, null);
  assert.equal(W.Laudes.armar('2025-11-13', '').dos.ops.map(o => o.id).join(' '), 'pastores religiosos');
  // presbítero educador con propio de sync (San Juan Bosco): por defecto, pastores; la nota, con el caso
  r = W.Laudes.armar('2025-01-31', '');
  assert.equal(r.dos.ops.map(o => o.n).join(' | '), 'Común de pastores | Común de santos varones: para educadores');
  assert.match(r.dia.nota, /del Común de pastores: para un santo presbítero\.$/);
  X.modo.comunDia = { f: '2025-01-31', id: 'educadores' };
  try { assert.match(W.Laudes.armar('2025-01-31', '').dia.nota, /del Común de santos varones: para un santo educador\.$/); } finally { X.modo.comunDia = null; }
  // Hora intermedia: religiosos, educadores y caridad toman sus textos de santos varones (o de santas mujeres)
  const CI = W.INTERMEDIA.comunes;
  for (const c of ['religiosos', 'educadores', 'caridad']) {
    assert.equal(JSON.stringify(X.comun(CI, c, 'San N., religioso').tercia), JSON.stringify(X.comun(CI, 'santos-varones', 'San N., religioso').tercia), c);
    assert.equal(JSON.stringify(X.comun(CI, c, 'Santa N., religiosa').nona), JSON.stringify(X.comun(CI, 'santas-mujeres', 'Santa N., religiosa').nona), c);
  }
  // presbítero religioso con propio de sync (San Ignacio de Loyola): con su común, el texto de sync queda; con el otro, cambia
  const I1 = W.Laudes.armar('2026-07-31', '');
  assert.equal(I1.dos.ops.map(o => o.n).join(' | '), 'Común de pastores | Común de santos varones: para religiosos');
  X.modo.comunDia = { f: '2026-07-31', id: 'religiosos' };
  let I2; try { I2 = W.Laudes.armar('2026-07-31', ''); } finally { X.modo.comunDia = null; }
  assert.notEqual(JSON.stringify(de(I1, 'preces')), JSON.stringify(de(I2, 'preces')));
  assert.match(I2.dia.nota, /del Común de santos varones: para un santo religioso\.$/);
});

// ---------- Correcciones del 26/11/2026 ----------
test('base: sin «¡» en lugar de «i» (errata de la extracción del libro)', () => {
  const dir = new URL('../base/', import.meta.url), malos = [];
  const recorrer = d => { for (const e of readdirSync(d, { withFileTypes: true })) {
    const u = new URL(e.name + (e.isDirectory() ? '/' : ''), d);
    if (e.isDirectory()) recorrer(u);
    else if (e.name.endsWith('.yaml')) readFileSync(u, 'utf8').split('\n').forEach((l, i) => {
      // pegado a una letra («m¡», «de¡») o palabras que empiezan con «i» («¡mitad», «¡mito», «¡da»)
      if (/\p{L}¡|¡(?:mit|da\b|nclus|nmens|gual|glesia\b)/u.test(l)) malos.push(e.name + ':' + (i + 1));
    }); } };
  recorrer(dir);
  assert.deepEqual(malos, []);
});

test('Completas después de las I Vísperas del I domingo de Adviento: Alma Redemptóris', () => {
  const m = f => CP.armar(f, 'ARG').secciones.find(s => s.k === 'mariana').opciones[0].id;
  assert.equal(m('2026-11-28'), 'alma-sol');
  assert.equal(m('2026-11-27'), 'salve-sim');
});

test('Completas recitado: «Salva nos, *» lo entona uno y desde «Dómine» siguen todos; la repetición, sin asterisco', () => {
  const S = CP.armar('2026-11-26', 'ARG').secciones, a = S.find(s => s.id === 'ac'), b = S.find(s => s.id === 'ac2');
  assert.equal(a.rec.length, 1); assert.equal(a.rec[0].pares[a.rec[0].desde][0], 'Dómine,'); assert.ok(!a.rec[0].todos);
  assert.ok(b.rec[0].todos && b.rec[0].desde == null);
  assert.ok(!/\*/.test(B.completas.gregoriano.conclusion.gabc.split('%%')[1]));   // Noctem quiétam: sin asterisco
});

test('Oficio de lectura y Hora intermedia: salmodia cantada en el modo del día, como Laudes', () => {
  const modoLA = LA.armar('2026-11-26', 'ARG').secciones.find(s => s.k === 'salmo').modo;
  const salmos = r => r.secciones.filter(s => s.k === 'salmo');
  const of = salmos(ctx.window.Oficio.armar('2026-11-26', 'ARG'));
  assert.ok(of.length && of.every(s => s.modo === modoLA));
  const ih = salmos(ctx.window.Sexta.armar('2026-11-26', 'ARG'));
  assert.ok(ih.length && ih.every(s => s.modo === modoLA));
});

// 26/11/2026: un mismo salmo puede ir cortado distinto en el Oficio de lectura y en Vísperas (o en la Hora intermedia).
// El importador guardaba cada salmo por su título («Salmo 144 I») y, si la clave ya existía, se salteaba el texto de la otra
// hora: el Oficio rezaba dos veces los vv. 13-21 del 144 (y lo mismo con el 135 y el 54), y el sábado IV empezaba el 77
// por el comienzo. En una misma salmodia, las partes de un salmo no pueden repetir texto y van seguidas (II después de I…).
test('salmodias: las partes de un mismo salmo no se repiten y van en orden', () => {
  for (const f of ['carga/oficio.js', 'carga/intermedia.js']) if (!ctx.window[f.slice(6, -3).toUpperCase()]) vm.runInNewContext(readFileSync(new URL('../src/' + f, import.meta.url), 'utf8'), ctx);
  const W = ctx.window, malos = [];
  const ROM = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6 };
  for (const [hora, D] of [['laudes', W.LAUDES], ['visperas', W.VISPERAS], ['oficio', W.OFICIO], ['intermedia', W.INTERMEDIA]]) {
    const listas = [];
    const buscar = (o, donde) => { if (!o || typeof o !== 'object') return;
      for (const [k, v] of Object.entries(o)) {
        if ((k === 'salmodia' || k === 'complementaria') && Array.isArray(v) && v.every(g => g && g.salmo)) listas.push([donde, v.map(g => g.salmo)]);
        else buscar(v, donde + '/' + k); } };
    buscar({ salterio: D.salterio, tiempo: D.tiempo, santoral: D.santoral, comunes: D.comunes }, hora);
    for (const [donde, l] of listas) {
      const pr = l.map(id => { const s = D.salmos[id]; return s ? String(s.texto[0]).split('\n').slice(0, 2).join(' ') : id; });   // dos renglones: el 95 y el 97 empiezan igual
      if (new Set(pr).size !== pr.length) malos.push(donde + ': texto repetido ' + l.join(' '));
      for (let i = 1; i < l.length; i++) {
        const n = id => (/^salmo-(\d+)/.exec(id) || [])[1], a = D.salmos[l[i - 1]], b = D.salmos[l[i]];
        if (!a || !b || n(l[i - 1]) !== n(l[i])) continue;
        const r = s => ROM[(/ ([IV]+)$/.exec(s.titulo) || [])[1]] || 1;
        if (r(b) !== r(a) + 1) malos.push(donde + ': partes fuera de orden ' + l[i - 1] + ' → ' + l[i]);
      }
    }
  }
  assert.deepEqual(malos, []);
});
