// Salmodia en español (src/salmodia.js) y modos de Laudes y Vísperas: node --test tests/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
const S = require('../src/salmodia.js');
const sil = w => S.silabasEspanol(w).map(s => (s.acc ? s.t.toUpperCase() : s.t)).join('-');

// ---------- Salmos reales de Laudes y Vísperas ----------
const ctx = { window: {} };
for (const f of ['datos/base.js', 'datos/calendario.js', 'completas.js', 'carga/laudes.js', 'carga/visperas.js', 'laudes.js'])
  vm.runInNewContext(readFileSync(new URL('../src/' + f, import.meta.url), 'utf8'), ctx);
const CP = ctx.window.Completas, X = ctx.window.Completas._, LA = ctx.window.Laudes, VI = ctx.window.Visperas;
const SALMOS = { ...ctx.window.LAUDES.salmos, ...ctx.window.VISPERAS.salmos };
const MODOS = ['1g', '2D', '3a', '4g', '5a', '6F', '7a', '8G'];

// Una mitad de verso pautada, con el acento entre corchetes y las preparatorias entre guiones bajos
const marca = h => h.pals.map((p, iw) => p.pre + p.sil.map((x, k) => {
  const r = h.res[h.sils.findIndex(s => s.iw === iw && s.k === k)];
  return r.rol === 'acc' ? `[${x.t}]` : r.rol === 'prep' ? `_${x.t}_` : x.t;
}).join('') + p.post).join(' ');
const pautar = (v, cod) => { const pv = S.pautarVerso(v, cod, 'es', false); return [pv.flex, pv.med, pv.ter].filter(Boolean).map(marca).join(' | '); };
const acentoMetro = (h, cod = '8G') => { const pv = S.pautarVerso(h + ' * y nada más.', cod, 'es', false);
  return pv.med.sils.filter((s, i) => pv.med.res[i].rol === 'acc').map(s => s.t).join(' '); };

test('silabeo español: qu y gu, Aleluia, Sión, hiatos y diptongos', () => {
  assert.equal(sil('porque'), 'POR-que');
  assert.equal(sil('aunque'), 'AUN-que');
  assert.equal(sil('exquisitos'), 'ex-qui-SI-tos');
  assert.equal(sil('distinguir'), 'dis-tin-GUIR');
  assert.equal(sil('averigüéis'), 'a-ve-ri-GÜÉIS');
  assert.equal(sil('Aleluia'), 'A-le-LU-ia');
  assert.equal(sil('Sión'), 'Si-ÓN');
  assert.equal(sil('guió'), 'gui-Ó');
  assert.equal(sil('dió'), 'DIÓ');
  assert.equal(sil('Israel'), 'Is-ra-EL');
  assert.equal(sil('Jerusalén'), 'Je-ru-sa-LÉN');
  assert.equal(sil('oído'), 'o-Í-do');
  assert.equal(sil('guía'), 'GUÍ-a');
  assert.equal(sil('reyes'), 'RE-yes');
  assert.equal(sil('Dios'), 'DIOS');
  assert.equal(sil('de'), 'de');   // átona
  assert.equal(sil('para'), 'PA-ra');   // «pa-» de «para» es fuerte
});

test('sílabas fuertes, débiles y neutras', () => {
  const tipos = t => S.clasificar(S.plano(S.palabras(t, 'es')), 'es').join('');
  assert.equal(tipos('majestad'), 'NDF');
  assert.equal(tipos('Señor'), 'DF');
  assert.equal(tipos('sinceridad'), 'NNDF');
  assert.equal(tipos('de tus pies'), 'NDF');   // neutra: átona no pegada a una acentuada, también la de una palabra átona
  assert.equal(tipos('a mi Señor'), 'NNDF');
});

test('reglas de CRU para el acento del metro (modos de un acento)', () => {
  assert.equal(acentoMetro('Señor, no me corrijas con ira'), 'i');                    // …fd
  assert.equal(acentoMetro('En la sentencia tendrás razón'), 'drás');                  // fdf: esdrújula
  assert.equal(acentoMetro('En su boca no hay sinceridad'), 'ce');                     // ndf: esdrújula suave
  assert.equal(acentoMetro('en el trono que ha colocado para juzgar'), 'gar');         // ddf con dos débiles: aguda suave
  assert.equal(acentoMetro('no tengo miedo a Dios'), 'Dios');                          // ddf: sustantivo, siempre fuerte: aguda (CRU, 22/11/2026)
  assert.equal(acentoMetro('a cantar sus cánticos'), 'cán');                           // esdrújula
  for (const cod of ['2D', '4g', '5a', '8G']) assert.equal(acentoMetro('En su boca no hay sinceridad', cod), 'ce');
});

test('dos fuertes seguidas: las dos fuertes, acentuación grave (CRU, 22/11/2026)', () => {
  const tipos = t => S.clasificar(S.plano(S.palabras(t, 'es')), 'es').join('');
  assert.equal(tipos('Señor Dios'), 'DFF');
  assert.equal(pautar('Señor Dios, * te alabamos.', '8G').split(' | ')[0], 'Se[ñor] Dios,');
  assert.equal(pautar('Te alabamos, * Señor Dios.', '8G').split(' | ')[1], '_Se_[ñor] Dios.');   // también en la cadencia
  assert.deepEqual(S.clasificar(S.plano(S.palabras('mar, oh Deus', 'la')), 'la'), ['F', 'D', 'F', 'D']);   // en latín manda la segunda
});

test('agudas en la mediante (CRU, 22/11/2026): un acento, la aguda sin juntar notas; dos acentos, −2; pronombre tónico como neutro', () => {
  const ac = (v, cod) => { const h = S.pautarVerso(v, cod, 'es', false).med; return h.sils.filter((x, i) => h.res[i].rol === 'acc').map(x => x.t).join(' '); };
  for (const cod of ['1g', '2D', '3a', '4g', '5a', '6F', '7a', '8G']) {
    const T = S.tono(cod), um = S.pautarVerso('para juzgar * y nada más.', cod, 'es', false).med.res.at(-1);
    if (T.med.acc.length > 1) { assert.equal(ac('para juzgar * y nada más.', cod), 'pa juz', cod); continue; }   // dos acentos: −2
    assert.equal(um.rol, 'acc'); assert.equal(um.nota, T.med.acc.at(-1).n, cod);   // un acento: la última, con la nota del acento, sola
  }
  assert.equal(ac('servid al Señor con temor, * y nada más.', '8G'), 'mor');
  assert.equal(ac('servid al Señor con temor, * y nada más.', '3a'), 'ñor te');
  assert.equal(ac('confío en ti, * y nada más.', '8G'), 'en');                 // pronombre tónico tomado como neutro
  assert.equal(ac('el camino que has de seguir, * y nada más.', '8G'), 'de');
  assert.equal(ac('Mi alma tiene ansia de ti, * mi carne tiene sed.', '3a'), 'an de');      // dos acentos: «[an]sia [de] ti»
  assert.equal(ac('Mi alma tiene ansia de ti, * mi carne tiene sed.', '8G'), 'de');
  assert.equal(ac('¿No fui yo, el Señor? * ¡No hay otro Dios fuera de mí!', '8G'), 'el');
});

test('cadencia: nunca acento en la última sílaba (CRU)', () => {
  const cad = v => { const h = S.pautarVerso('Y dije: * ' + v, '8G', 'es', false).ter; return h.sils.filter((x, i) => h.res[i].rol === 'acc').map(x => x.t).join(' '); };
  assert.equal(cad('¿a quién temeré?'), 'te');
  assert.equal(cad('bendecid al Señor.'), 'al');                 // antepenúltima
  assert.equal(cad('la luz del Señor.'), 'del');
  assert.equal(cad('mi alma está sedienta de ti;'), 'de');       // la antepenúltima sigue al acento de su palabra: la penúltima
  assert.equal(cad('se exalta por Dios;'), 'por');
  assert.equal(cad('para juzgar.'), 'juz');
  // termina en la nota final del modo
  for (const cod of ['1g', '2D', '3a', '4g', '5a', '6F', '7a', '8G']) {
    const ut = S.pautarVerso('Y dije: * ¿a quién temeré?', cod, 'es', false).ter.res.at(-1);
    assert.notEqual(ut.rol, 'acc', cod); assert.equal(ut.nota, S.tono(cod).ter.acc.at(-1).fijas.at(-1), cod);
  }
});

test('Gloria: «Amén» sin acento en «-mén» (como llana)', () => {
  for (const cod of ['1g', '2D', '3a', '4g', '5a', '6F', '7a', '8G']) {
    const h = S.pautarVerso('Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.', cod, 'es', false).ter;
    assert.equal(h.res.at(-1).rol, 'fin', cod); assert.equal(h.res.at(-2).rol, 'acc', cod); assert.equal(h.sils.at(-2).t, 'A');
  }
  // fuera del Gloria, «amén» sigue siendo aguda
  assert.equal(sil('Amén'), 'A-MÉN');
});

test('flexa: baja un tono, o una tercera menor desde do o fa; nunca acentúa la última (como la cadencia)', () => {
  assert.equal(S.tono('8G').flex, 'h');   // cuerda do (c4: j) → la
  assert.equal(S.tono('2D').flex, 'f');   // cuerda fa (f3: h) → re
  assert.equal(S.tono('4g').flex, 'g');   // cuerda la → sol
  assert.equal(S.tono('5a').flex, 'f');   // cuerda do (c3: h) → la
  assert.equal(S.tono('7a').flex, 'h');   // cuerda re → do
  const pv = S.pautarVerso('Desde Sión extenderá el Señor † el poder de tu cetro: * somete en la batalla a tus enemigos.', '8G', 'es', false);
  // ddf: acento en la antepenúltima («extenderá el Señor»: «el»), y bajan las que siguen (CRU, 19/11/2026)
  assert.equal(pv.flex.sils.map((x, i) => x.t + '(' + pv.flex.res[i].nota + ')').slice(-3).join(' '), 'el(j) Se(h) ñor(h)');
  assert.equal(pv.flex.res.at(-3).rol, 'acc');
});

test('modos de dos acentos: período de 2 sílabas, 3 como máximo (como Chant Tools en latín)', () => {
  // fuerte a 2 o a 3
  assert.equal(pautar('No tengo miedo a Dios, * ni en su presencia.', '1g').split(' | ')[0], 'No tengo [mie]do [a] Dios,');
  assert.equal(pautar('El Señor da la muerte y la vida, * hunde en el abismo y levanta.', '7a').split(' | ')[0], 'El Señor da la muerte [y] la [vi]da,');
  // sin fuerte ni neutra a 2 o a 3: acento a 2 aunque sea débil (Chant Tools: «in progénies et progénies»)
  assert.equal(pautar('Gloria al Padre, y al Hijo, * y al Espíritu Santo.', '1g'), 'Gloria al Padre, [y] al [Hi]jo, | y al Espí_ri__tu_ [San]to.');
  assert.equal(pautar('Gloria al Padre, y al Hijo, * y al Espíritu Santo.', '7a'), 'Gloria al Padre, [y] al [Hi]jo, | y al Es[pí]ritu [San]to.');
  // nunca a más de 3 sílabas, en ningún salmo
  for (const [id, s] of Object.entries(SALMOS)) for (const v of X.versosDe(s.texto).versos) for (const cod of ['1g', '3a', '6F', '7a', '5a']) {
    const pv = S.pautarVerso(v, cod, 'es', false);
    for (const h of [pv.med, pv.ter].filter(Boolean)) { const a = h.res.map((r, i) => r.rol === 'acc' ? i : -1).filter(i => i >= 0);
      for (let k = 1; k < a.length; k++) assert.ok(a[k] - a[k - 1] <= 3, `${id} ${cod}: ${v}`); }
  }
});

test('Liber Usualis: en la cadencia dactílica, la nota adicional se anticipa en la sílaba acentuada (modo 3, 1 D², 4 E)', () => {
  const notas = (v, cod, l) => { const h = S.pautarVerso(v + ' * y nada más.', cod, l, false).med; return h.sils.slice(-4).map((x, i) => x.t + '(' + h.res[h.res.length - 4 + i].nota + ')').join(' '); };
  // como Chant Tools: «et Fí(j) li(ih) o(j.)»
  assert.equal(notas('Glória Patri, et Fílio,', '3a', 'la'), 'et(j) Fí(j) li(ih) o(j.)');
  assert.deepEqual(S.pautarVerso('cantad al Señor un cántico, * bendecid su nombre.', '3a', 'es', false).med.res.slice(-3).map(r => r.nota), ['j', 'ih', 'j.']);
  // llana: la clivis sigue en la sílaba acentuada
  assert.deepEqual(S.pautarVerso('Dad gracias al Señor porque es bueno, * porque es eterna su misericordia.', '3a', 'es', false).med.res.slice(-2).map(r => r.nota), ['ih', 'j.']);
  assert.deepEqual(S.tono('1D2').ter.acc[0].antic, 'g');
  assert.deepEqual(S.tono('4E').ter.acc[0].antic, 'g');
});

test('modo 6: también la otra fórmula del Liber (mediante de un acento con una preparatoria)', () => {
  assert.equal(S.etiquetaTono('6altF'), 'Modo 6 alt. F');
  assert.equal(S.tono('6altF').med.acc.length, 1);
  assert.equal(S.tono('6altF').med.prep.length, 1);
});

test('latín: la tilde vale también en mayúscula inicial', () => {
  assert.deepEqual(S.silabasLatin('Ísrael').map(x => x.acc), [1, 0, 0]);
  assert.deepEqual(S.silabasLatin('Ábraham').map(x => x.acc), [1, 0, 0]);
});

test('latín como Chant Tools: silabeo de Solesmes', () => {
  const sl = w => S.silabasLatin(w).map(x => x.t).join('-');
  assert.equal(sl('Magníficat'), 'Ma-gní-fi-cat');      // gn juntas
  assert.equal(sl('eum'), 'e-um');                      // eu: dos sílabas
  assert.equal(sl('Deus'), 'De-us');
  assert.equal(sl('Eucharistía'), 'Eu-cha-ris-tí-a');
  assert.equal(sl('eréxit'), 'e-ré-xit');               // x con la vocal que sigue
  assert.equal(sl('exaltávit'), 'ex-al-tá-vit');        // salvo el prefijo ex-
  assert.equal(sl('víscera'), 'ví-sce-ra');             // sc y sp juntas
  assert.equal(sl('dispérsit'), 'di-spér-sit');
  assert.equal(sl('testaménti'), 'tes-ta-mén-ti');      // st no
  assert.equal(sl('iusiurándum'), 'ius-iu-rán-dum');
  assert.equal(sl('redemptiónem'), 'red-emp-ti-ó-nem');
  assert.equal(sl('Óriens'), 'Ó-ri-ens');
});

test('mitad corta con entonación, como Chant Tools («Magníficat»)', () => {
  const g = cod => S.gabcSalmo(['Magníficat * ánima mea Dóminum.'], cod, 'la', { entonarTodos: true }).split(' *(:)')[0];
  assert.equal(g('2D'), '(f3) Ma(e)gní(fe)fi(eh)cat(h.)');   // entonación corta del modo 2
  assert.equal(g('8G'), '(c4) Ma(g)gní(hg)fi(gj)cat(j.)');   // y del 8
  assert.equal(g('1g'), '(c4) Ma(f)gní(gh)fi(h)cat(h.)');
  assert.equal(g('7a'), '(c3) Ma(hg)gní(hi)fi(i)cat(i.)');
  // «timéntibus eum»: e-um, acento en e- (Chant Tools)
  const h = S.pautarVerso('Et misericórdia eius in progénies et progénies * timéntibus eum.', '2D', 'la', true).ter;
  assert.equal(h.sils.map((x, i) => x.t + '(' + h.res[i].nota + ')').join(' '), 'ti(h) mén(h) ti(h) bus(g) e(e) um(f.)');
});

test('mitad corta en español: sin entonación, directo a la cuerda y la mediante (CRU, «Bendito sea Dios»)', () => {
  const g = cod => S.gabcSalmo(['Bendito sea Dios, * Padre de nuestro Señor Jesucristo,'], cod, 'es', {}).split(' *(:)')[0];
  assert.equal(g('1g'), '(c4) Ben(h)di(ixi)to(h) se(g)a(h) Dios,(h.)');
  assert.equal(g('3a'), '(c4) Ben(j)di(k)to(j) se(j)a(ih) Dios,(j.)');
  assert.equal(g('4g'), '(c4) Ben(h)di(g)to(h) se(i)a(h) Dios,(h.)');
  assert.equal(g('7a'), '(c3) Ben(i)di(k)to(j) se(i)a(j) Dios,(j.)');
  // con lugar para la entonación, la entonación sigue
  assert.equal(g('2D'), '(f3) Ben(e)di(f)to(h) se(i)a(h) Dios,(h.)');
});

test('entonación: en el primer verso de los salmos; en todos los del cántico evangélico', () => {
  const g1 = S.gabcSalmo(['Señor, tú eres mi Dios, * por ti madrugo.', 'Mi alma está sedienta de ti, * mi carne tiene ansia de ti.'], '8G', 'es', { todos: true });
  const versos = g1.split('(::)');
  assert.match(versos[0], /^\(c4\) Se\(g\)ñor,\(h\)/);
  assert.match(versos[1], /^ Mi\(j\)/);
  const g2 = S.gabcSalmo(['Benedíctus Dóminus Deus Ísrael, * quia visitávit', 'et eréxit cornu salútis nobis, * in domo David'], '8G', 'la', { entonarTodos: true });
  assert.match(g2.split('(::)')[1], /^ et\(g\) e\(h\)/);
});

test('todos los salmos y cánticos de Laudes y Vísperas, en los ocho modos', () => {
  const mal = []; let n = 0;
  for (const [id, s] of Object.entries(SALMOS)) {
    if (/^cantico-ap-19-/.test(id)) continue;
    const vs = X.versosDe(s.texto).versos.filter(v => !/^R\.\s/.test(v));
    for (const cod of MODOS) vs.forEach((v, i) => {
      const pv = S.pautarVerso(v, cod, 'es', i === 0); n++;
      for (const h of [pv.flex, pv.med, pv.ter].filter(Boolean)) {
        const k = h.res.length, t = S.clasificar(h.sils, 'es');
        if (h.res.some(r => !r || !r.nota)) mal.push(`${id} ${cod}: sílaba sin nota: ${v}`);
        const acc = h.res.map((r, i) => r.rol === 'acc' ? i : -1).filter(i => i >= 0);
        if (k >= 3 && h.regla !== 'corta' && (!acc.length || acc.at(-1) < k - 3)) mal.push(`${id} ${cod}: acento fuera de las tres últimas: ${v}`);
        if (acc.length && t[acc.at(-1)] === 'D' && h.regla !== 'sin F' && !/^ddf[· ]/.test(h.regla)) mal.push(`${id} ${cod}: acento en débil: ${v}`);
        if (h === pv.ter && k >= 2 && h.res[k - 1].rol === 'acc') mal.push(`${id} ${cod}: cadencia con acento en la última: ${v}`);
        if (h.sils.some(x => !/[aeiouáéíóúüy]/i.test(x.t))) mal.push(`${id}: sílaba sin vocal: ${v}`);
      }
      const g = S.gabcVerso(pv);
      if ((g.match(/\(/g) || []).length !== (g.match(/\)/g) || []).length) mal.push(`${id} ${cod}: GABC mal formado`);
    });
  }
  assert.ok(n > 10000, String(n));
  assert.deepEqual(mal, []);
});

test('versos reales, pautados', () => {
  // Salmo 62 (domingo I, Laudes): modo 1 g
  assert.equal(pautar("¡Oh Dios!, tú eres mi Dios, por ti madrugo, * mi alma está sedienta de ti;", '1g'),
    '¡Oh Dios!, tú eres mi Dios, por [ti] ma[dru]go, | mi alma está se_dien__ta_ [de] ti;');
  // Salmo 35 (miércoles I, Laudes): modo 2
  assert.equal(pautar('«No tengo miedo a Dios, * ni en su presencia.»', '2D'), '«No tengo miedo a [Dios], | ni en su _pre_[sen]cia.»');
  assert.equal(pautar('acostado medita el crimen, † se obstina en el mal camino, * no rechaza la maldad.', '2D'),
    'acostado medita el [cri]men, | se obstina en el mal ca[mi]no, | no recha_za_ [la] maldad.');
  // Salmo 109 (domingos, Vísperas): modo 3 a
  assert.equal(pautar('y haré de tus enemigos * estrado de tus pies.»', '3a'), 'y haré de tus [e]ne[mi]gos | estra_do_ [de] tus pies.»');
});

test('modo de la salmodia: uno por semana del salterio y otro por domingo', () => {
  const m = (f, h = LA) => { const r = h.armar(f, 'ARG').secciones; return [...new Set(r.filter(s => s.k === 'salmo' || s.k === 'cantico').map(s => s.modo))].join(','); };
  // Noviembre de 2026: el 15 es domingo de la semana I; el 18, miércoles de la I; el 22 (Cristo Rey), domingo de la II
  assert.equal(LA.modoDe({ sal: 1, dom: 1 }, '2026-11-15'), '1g');
  assert.equal(LA.modoDe({ sal: 2 }, '2026-11-22'), '3a');
  assert.equal(LA.modoDe({ sal: 3 }, '2026-11-29'), '6F');
  assert.equal(LA.modoDe({ sal: 4 }, '2026-12-06'), '7a');
  assert.equal(LA.modoDe({ sal: 1 }, '2026-11-18'), '2D');
  assert.equal(LA.modoDe({ sal: 2 }, '2026-11-24'), '4g');
  assert.equal(LA.modoDe({ sal: 3 }, '2026-12-01'), '5a');
  assert.equal(LA.modoDe({ sal: 4 }, '2026-11-12'), '8G');
  assert.equal(LA.modoDe({ sal: 2, sol: 1 }, '2026-11-24'), '4g');   // solemnidad en martes de la II: el modo de la semana (CRU)
  // días sin semana del salterio (CRU)
  const dia = f => CP.diaCal(f, '');
  assert.equal(LA.modoDe(dia('2026-12-25'), '2026-12-25'), '1g');   // Navidad
  assert.equal(LA.modoDe(dia('2027-01-06'), '2027-01-06'), '1g');   // tiempo de Navidad (Epifanía)
  assert.equal(LA.modoDe(dia('2027-03-28'), '2027-03-28'), '1g');   // Domingo de Pascua
  assert.equal(LA.modoDe(dia('2027-03-31'), '2027-03-31'), '1g');   // octava de Pascua
  assert.equal(LA.modoDe(dia('2027-03-26'), '2027-03-26'), '4g');   // Viernes Santo
  assert.equal(LA.modoDe(dia('2027-03-27'), '2027-03-27'), '4g');   // Sábado Santo
  assert.equal(LA.modoDe(dia('2027-05-06'), '2027-05-06'), '4g');   // Ascensión en jueves: feria de su semana (II)
  assert.equal(LA.modoDe(dia('2027-05-16'), '2027-05-16'), '6F');   // Pentecostés: domingo de su semana (III)
  // en las horas: el mismo modo para todos los salmos, los cánticos y el cántico evangélico
  assert.equal(m('2026-11-18'), '2D');
  assert.equal(m('2026-11-15'), '1g');
  assert.equal(m('2026-11-15', VI), '1g');
  assert.equal(m('2026-11-12', VI), '8G');
  // sábado por la tarde: las I Vísperas del domingo, con el modo del domingo
  assert.equal(m('2026-11-14', VI), '1g');
});

test('Completas no cambia: el Nunc dimíttis sigue en el modo 3 a y los salmos sin modo de la semana', () => {
  const C = ctx.window.Completas.armar('2026-11-18', 'ARG').secciones;
  assert.ok(C.filter(s => s.k === 'salmo').every(s => !s.modo));
  assert.equal(C.find(s => s.id === 'ac').modo, '3a');
});

test('antífona con † (como en el libro): lo que repite la antífona se omite y la entonación pasa al verso siguiente', () => {
  const v26 = ['El Señor es mi luz y mi salvación, * ¿a quién temeré?', 'El Señor es la defensa de mi vida, * ¿quién me hará temblar?', 'Cuando me asaltan los malvados * para devorar mi carne,'];
  assert.deepEqual(S.omitirAnt(v26, 'El Señor es mi luz y mi salvación, ¿a quién temeré? †'),
    { gris: ['El Señor es mi luz y mi salvación, * ¿a quién temeré?'], versos: v26.slice(1), ent: 0 });
  // queda solo la segunda mitad: va con la terminación, sin entonación; la entonación, en el verso siguiente
  const v96 = ['El Señor reina, la tierra goza, * se alegran las islas innumerables.', 'Tiniebla y nube lo rodean, * justicia y derecho sostienen su trono.'];
  const o = S.omitirAnt(v96, 'El Señor reina, la tierra goza. †');
  assert.deepEqual(o, { gris: ['El Señor reina, la tierra goza,'], versos: ['* se alegran las islas innumerables.', v96[1]], ent: 1 });
  const pv = S.pautarVerso(o.versos[0], '4g', 'es', true);
  assert.equal(pv.med, null); assert.ok(pv.ter.res.length);
  assert.ok(/^\(c4\) se\(h\)/.test(S.gabcSalmo(o.versos, '4g', 'es', { entonarEn: 1 })));
  // después de la flexa: queda un verso entero; con «Aleluia» en la antífona
  const v64 = ['¡Oh Dios!, tú mereces un himno en Sión, † y a ti se te cumplen los votos, * porque tú escuchas las súplicas.'];
  // después de la flexa: queda el metro y la terminación, sin entonación; la entonación, en el verso siguiente
  const o64 = S.omitirAnt(v64.concat(['A ti acude todo mortal * a causa de sus culpas;']), '¡Oh Dios!, tú mereces un himno en Sión. Aleluia. †');
  assert.deepEqual(o64, { gris: ['¡Oh Dios!, tú mereces un himno en Sión,'], versos: ['y a ti se te cumplen los votos, * porque tú escuchas las súplicas.', 'A ti acude todo mortal * a causa de sus culpas;'], ent: 1 });
  assert.ok(/^\(c4\) y\(h\) a\(h\)/.test(S.gabcSalmo(o64.versos, '4g', 'es', { entonarEn: 1 })));   // sin entonación (4 g: h g h)
  // sin † en el libro, pero igual al comienzo del salmo: también (CRU)
  assert.equal(S.omitirAnt(v26, 'El Señor es mi luz y mi salvación, ¿a quién temeré?').versos[0], v26[1]);
  assert.equal(S.omitirAnt(v26, 'El Señor es mi luz. †'), null);                                // no coincide con un corte del verso
});

test('las antífonas con † de la base (las del libro) coinciden con el comienzo de su salmo', () => {
  const comp = ctx.window.BASE.salmos, mal = [];
  const ver = (ant, sid, donde) => { const s = SALMOS[sid] || comp[sid]; if (s && !S.omitirAnt(X.versosDe(s.texto).versos, ant)) mal.push(`${donde}: ${sid}`); };
  for (const L of [ctx.window.LAUDES, ctx.window.VISPERAS])
    for (const [sem, dias] of Object.entries(L.salterio)) for (const [d, e] of Object.entries(dias)) for (const g of (e && e.salmodia) || [])
      if (/†\s*$/.test(g.ant)) ver(g.ant, g.salmo, `${sem} ${d}`);
  for (const [d, e] of Object.entries(ctx.window.BASE.completas.salterio || {})) for (const g of (e && e.salmodia) || [])
    if (/†\s*$/.test(g.ant)) ver(g.ant, g.salmos[0], `Completas ${d}`);
  assert.deepEqual(mal, []);
});
