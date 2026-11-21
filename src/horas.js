/* ================== Oficio de lectura y Hora intermedia (Tercia, Sexta, Nona) ==================
   Datos: window.OFICIO (src/carga/oficio.js) y window.INTERMEDIA (src/carga/intermedia.js), que se cargan al abrir la hora.
   Capas, como Laudes: salterio de cuatro semanas → propio del tiempo (por feria; en domingo, con ciclo A/B/C) → santoral.
   Hora intermedia: una salmodia del día para las tres horas (o la complementaria de cada hora: se elige, y es la de las
   solemnidades que no caen en domingo); himno, antífona propia (en los tiempos que la tienen), lectura, versículo y oración, por hora.
   Decisiones en docs/horas.md. */
(function(){
const CP=window.Completas, X=CP._;
const NOMBRES={oficio:'Oficio de lectura', tercia:'Tercia', sexta:'Sexta', nona:'Nona'};
const SIN_GLORIA=['cantico-dn-3-57-88-56'];
let PAS=false;   // tiempo de pasión (X.pasion): los salmos, sin Gloria y con la rúbrica

// Las partes del día, capa sobre capa
const mayor=ref=>/^(Fiesta|Solemnidad)/.test(ref.g);
function capas(L, fecha, sel, campos, hora){
  const DIF=!!X.modo.difuntos, ref0=CP.diaCal(fecha, sel), d=CP.deIso(fecha), dia=X.DIAS[d.getDay()];
  const COM=!DIF && X.modo.comun;   // Comunes de los santos (botón del inicio)
  const ref=DIF ? {...ref0, n:'Oficio de difuntos', g:'Oficio de difuntos', sol:false}   // Oficio de difuntos (botón del inicio)
    : COM ? {...ref0, n:COM.nombre, g:COM.grado, sol:COM.grado==='Solemnidad', c:COM.color, oct:''} : ref0;
  const P={}, capa=o=>{ if(o) for(const k of campos) if(o[k]!=null) P[k]=o[k]; };
  capa((L.salterio['semana_'+(ref.sal||1)]||L.salterio.semana_1)[dia]);
  const cic=window.Laudes.ciclo(fecha), T1=L.tiempo[ref.fer], T2=L.tiempo[`${ref.fer} (${cic})`];
  capa(T1); capa(T2);
  const TD=d.getDay()!==0 ? L.tiempo[X.fechaClave(fecha)] : null;   // días con fecha propia en el tiempo (17 al 24 de diciembre, 7 al 12 de enero), nunca en domingo
  capa(TD);
  // Ciclo bienal de la primera lectura del Oficio: la entrada del tiempo dice de qué año es la suya («anio») y trae la del otro
  const TB=[TD, T2, T1].find(x=>x && x.otro_anio);
  if(TB && P.lectura1===TB.lectura1 && TB.anio!==X.anioBienal(fecha, ref)){ P.lectura1=TB.otro_anio.lectura1; if(TB.otro_anio.resp1) P.resp1=TB.otro_anio.resp1; }
  const adf=DIF ? {comun:'difuntos'} : COM ? {comun:COM.id} : (L.adf||{})[ref.n]||{}, k=(DIF||COM) ? null : (L.mapa[ref.n]||adf.como);
  // «de»: celebración (nombre del calendario) de la que se toma lo que falte (San José obrero, del 19 de marzo)
  // (en la Hora intermedia, solo si es fiesta o solemnidad: en las memorias, todo de la feria)
  const kd=(!DIF && !COM && adf.de && !adf.como && (!hora || hora==='oficio' || mayor(ref))) ? (L.mapa[adf.de] || (L.santoral[adf.de] ? adf.de : null)) : null;
  const DE=kd ? (ref.t==='Pascua' ? X.textosPascua(L.santoral[kd]) : L.santoral[kd]) : null;   // tiempo pascual: con «Aleluia»
  capa(DE);
  const santo0=k?L.santoral[k]:null; capa(santo0);
  const santo=DE ? {...DE, ...(santo0||{})} : santo0;
  const deTxt=adf.de ? X.deCelebracion(adf.de, L.santoral[kd]||(window.LAUDES&&window.LAUDES.santoral[(window.LAUDES.mapa||{})[adf.de]])) : '';
  // Sin propio en la base: el común que corresponde (base/santoral/adf.yaml), del libro
  const n=COM ? 0 : X.turno(L.adf, adf.comun, fecha, sel);   // las «O bien» del común se alternan entre celebraciones (en el modo común, se eligen)
  const C=(!k && adf.comun && L.comunes) ? X.comun(L.comunes, adf.comun, ref.n, ref.t==='Pascua', n) : null;
  const PR=!k ? (ref.t==='Pascua' ? X.textosPascua(X.enPascua(adf.propio)) : adf.propio)||null : null;   // propio del libro (base/santoral/libro.yaml)
  // Fiesta o solemnidad con propio en la base pero sin todas sus partes (p. ej. una memoria que un calendario eleva):
  // lo que falte, del común que indica el santoral. M: datos de Laudes para la Hora intermedia.
  const M=mayor(ref) ? (L.mayores||{})[ref.n] : null;
  const CS=(mayor(ref) && (k||M) && L.comunes) ? X.comun(L.comunes, (X.esDoctor(ref.n)&&(adf.comun||'doctores')) || X.comunDe((santo&&santo.comun) || (M&&M.comun)) || adf.comun, ref.n, ref.t==='Pascua') : null;
  // Nota: qué es propio y de dónde sale lo demás (otra celebración, el común o el día)
  const PRh = PR && (hora && hora!=='oficio' ? {...(PR[hora]||{}), oracion:PR.oracion} : PR);
  const nota = DE ? X.notaPropios(k ? santo0 : PRh, deTxt) : (adf.como && deTxt) ? `Textos ${deTxt}.` : null;
  return {P, ref, dia, dom:d.getDay()===0, santo, k, C, PR, CS, M, n, nota, tiempo:!!(T1||T2), comun:adf.comun};
}
function aviso(ref, k, L, C, hora, PR, nota){
  if(X.modo.difuntos || X.modo.comun) return '';
  if(nota!=null) return nota;
  if(ref.n===ref.fer || k) return (L.adf||{})[ref.n]&&(L.adf||{})[ref.n].como ? 'Celebración propia de ADF: por ahora, con los textos de otra celebración de la base.' : '';
  if(hora!=='oficio' && /^Memoria/.test(ref.g)) return '';   // Hora intermedia de una memoria: todo de la feria
  if(PR && PR.oracion) return X.notaPropios(hora==='oficio' ? PR : {...(PR[hora]||{}), oracion:PR.oracion}, C ? `del ${C.nombre}` : 'del día');
  if(C) return /^Memoria de santa María/.test(C.nombre) ? '' : `Textos del ${C.nombre}`+(C.oraciones?', con su oración (falta la propia).':'.');
  if(/^Memoria/.test(ref.g)) return 'Memoria: se toma de la feria. Falta en la base la oración propia.';
  return 'El propio de esta celebración todavía no está en la base: se reza el oficio del día.';
}

// Comunes a las dos: invocación, salmo, conclusión y datos del día
function invocacion(S, ref){
  const GR=window.BASE.completas.gregoriano, cuaresma=ref.t==='Cuaresma'||ref.t==='Triduo';
  const tono = (ref.sol||ref.dom||ref.t==='Triduo'||ref.oct) ? 'solemne' : /^Fiesta/.test(ref.g) ? 'festivo' : 'ferial';
  const tr=cuaresma ? GR.invocacion.traduccion.filter(p=>!/^Allel/.test(p[0])).concat(GR.invocacion.laus) : GR.invocacion.traduccion;
  S.push({k:'sec', id:'inicio', t:'Invocación inicial'});
  S.push({k:'vr', tono, gabc:X.invocacionGabc(tono, !cuaresma), glosa:tr, rec:X.recInvocacion(tr)});
}
const salmo=(L, sid, ant)=>{ const s=L.salmos[sid]; if(!s) return {k:'aviso', t:`Falta el texto de ${sid}.`};
  const v=X.versosDe(s.texto);
  return {k:'salmo', es:true, id:sid, ant, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!PAS && !SIN_GLORIA.includes(sid), rubrica:[s.rubrica_final||'', PAS && !SIN_GLORIA.includes(sid) ? X.NO_GLORIA : ''].filter(Boolean).join(' ')}; };
function salmodia(S, L, sal, unica){
  S.push({k:'sec', id:'salmodia', t:'Salmodia'});
  if(unica){   // una antífona para los tres salmos: antes del primero y después del último
    S.push({k:'ant', id:'a1', es:true, n:'Ant.', t:{es:unica}});
    sal.forEach(g=>S.push(salmo(L, g.salmo, 'a1')));
    S.push({k:'ant', rep:'a1', es:true});
    return;
  }
  sal.forEach((g,gi)=>{
    const id='a'+(gi+1);
    if(g.ant) S.push({k:'ant', id, es:true, n:`Ant. ${gi+1}`, t:{es:g.ant}});
    S.push(salmo(L, g.salmo, g.ant?id:null));
    if(g.ant_fin) S.push({k:'ant', id:id+'f', es:true, n:`Ant. ${gi+1}`, t:{es:g.ant_fin}});
    else if(g.ant) S.push({k:'ant', rep:id, es:true});
  });
}
function conclusion(S, L){
  S.push({k:'sec', id:'conclusion', t:'Conclusión'});
  S.push({k:'vr', rec:X.recitado(L.gregoriano.benedicamus, [['V','Benedicámus'],['R','Deo',true]])});
}
function datosDia(ref, fecha, nota){
  const d=CP.deIso(fecha);
  return {dia:{titulo:ref.n+(ref.n===ref.fer && CP.deIso(fecha).getDay()!==0 && /( de diciembre| de enero)$/.test(X.fechaClave(fecha)) && /privilegiada|Epifanía/.test(ref.n) ? ` · ${X.fechaClave(fecha)}`:''), tiempo:X.TIEMPO_TXT[ref.t]||ref.t, salterio:ref.sal?`Semana ${X.ROMANO(ref.sal)} del salterio`:'', color:ref.c, grado:ref.g, nota},
          fechaTxt:`${X.DIAS_TXT[d.getDay()]} ${d.getDate()} de ${X.MESES[d.getMonth()]}`,
          versiones:{es:{n:'Liturgia de las Horas'}},
          gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']}};
}
// otros: los demás himnos del común (opciones en la hora; la elección vale mientras se mira ese día)
const himno=(S, Hs, n, id, otros)=>{ S.push({k:'sec', id:'himno', t:'Himno'});
  const op=(x,i)=>({id:i?id+'~'+i:id, n:x||'[falta el himno]', lang:'es', est:(Hs[x]||[]).map(e=>e.split('\n')), amen:''});
  S.push({k:'himno', es:true, efimera:!!(otros&&otros.length), opciones:[n, ...(otros||[])].map(op)}); };
const oracion=(S, t)=>{ S.push({k:'sec', id:'oracion', t:'Oración'}); S.push({k:'prosa', es:true, t:{es:t||'[falta la oración]'}, amen:{es:'Amén.'}}); };

// ---------- Oficio de lectura ----------
const CAMPOS_O=['himno','salmodia','versiculo','lectura1','resp1','lectura2','resp2','oracion'];
function armarOficio(fecha, sel){
  const L=window.OFICIO; if(!L || !CP.diaCal(fecha, sel)) return null;
  PAS=X.pasion(fecha, (CP.diaCal(fecha, sel)||{}).sol);
  const {P, ref, dom, k, C, PR, CS, santo, n, nota, comun}=capas(L, fecha, sel, CAMPOS_O, 'oficio');
  if(CS) for(const c of ['himno','salmodia','versiculo','lectura1','resp1','lectura2','resp2']) if(!(santo&&santo[c]!=null) && CS[c]!=null) P[c]=CS[c];
  if(C){   // Común: memorias, himno y segunda lectura (la primera, de la feria); fiestas y solemnidades, todo
    const cs=(mayor(ref) || C.salmodia_propia) ? ['himno','salmodia','versiculo','lectura1','resp1','lectura2','resp2'] : ['himno','lectura2','resp2'];
    for(const c of cs) if(C[c]!=null) P[c]=C[c];
    X.elegirComun(P, cs.filter(c=>c!=='salmodia' && c!=='himno' && !(PR&&PR[c]!=null)), L.comunes, comun, ref.n, ref.t==='Pascua', null, 'oficio');
    const o=(PR&&PR.oracion) ? null : X.oracionElegida(C.oraciones, ref.n, 'oficio', ref.t, n); if(o) P.oracion=o;
  }
  // Celebración con propio en la base que toma del común (el santoral dice cuál): lo que es texto del común, con sus otras opciones
  if(k && !C && L.comunes){ const cid=X.comunDe((L.santoral[k]||{}).comun); if(cid && L.comunes[cid]) X.elegirComun(P, ['versiculo','lectura2','resp2'], L.comunes, cid, ref.n, ref.t==='Pascua', null, 'oficio'); }
  if(PR) for(const c of [...CAMPOS_O]) if(PR[c]!=null) P[c]=PR[c];   // lo propio del libro: segunda lectura, oración…
  const otros=(C && !(PR&&PR.himno) && P.himno===C.himno) ? X.himnosComun(L.comunes, comun, ref.n, null, P.himno, L.himnos) : [];   // los otros himnos del común
  // Fiestas y solemnidades sin salmodia propia (ni en el tiempo, ni en el santoral, ni en el propio del libro, ni en el común): la del domingo de la I semana
  const propia=[L.tiempo[ref.fer], L.tiempo[`${ref.fer} (${window.Laudes.ciclo(fecha)})`], k&&L.santoral[k], C&&mayor(ref)&&C, CS, PR].some(x=>x&&x.salmodia);
  if(/^(Fiesta|Solemnidad)/.test(ref.g) && !dom && !propia) P.salmodia=L.salterio.semana_1.domingo.salmodia;
  // Te Deum: domingos fuera de Cuaresma, solemnidades, fiestas y octavas de Navidad y de Pascua
  const teDeum = !X.modo.difuntos && ((dom && ref.t!=='Cuaresma' && ref.t!=='Triduo') || ref.sol || /^Fiesta/.test(ref.g) || !!ref.oct);
  const S=[];
  invocacion(S, ref);
  himno(S, L.himnos, P.himno, 'oficio', otros);
  salmodia(S, L, P.salmodia||[]);
  if(P.versiculo) S.push({k:'resp', es:true, l:{es:P.versiculo}});
  const lect=(id, t, x, r)=>{
    // La cita bíblica va junto al título de la sección (una sola vez); la obra («De los Sermones…»), arriba del texto
    const enTitulo=!!(x && x.ref && !/^De /.test(x.ref));
    S.push({k:'sec', id, t, ref:enTitulo?x.ref:''});
    if(!x){ S.push({k:'aviso', t:'Falta esta lectura en la base.'}); return; }
    S.push({k:'lectura_larga', ref:enTitulo?'':(x.ref||''), autor:x.autor||'', titulo:x.titulo||'', t:x.texto||''});
    if(r){ S.push({k:'sec', id:id+'-r', t:'Responsorio', ref:r.ref||'', menor:true}); S.push({k:'resp', es:true, l:{es:r.vr}}); }
  };
  lect('lectura1', 'Primera lectura', P.lectura1, P.resp1);
  lect('lectura2', 'Segunda lectura', P.lectura2, P.resp2);
  if(teDeum){
    const TD=L.ordinario.te_deum;
    S.push({k:'sec', id:'tedeum', t:'Te Deum'});
    S.push({k:'himno', es:true, opciones:[{id:'tedeum', n:'Te Deum', lang:'es', est:TD.texto.map(e=>e.split('\n')), amen:''}]});
    S.push({k:'rub', t:TD.rubrica_final});
    S.push({k:'himno', es:true, opciones:[{id:'tedeum2', n:'Te Deum', lang:'es', est:TD.final.map(e=>e.split('\n')), amen:''}]});
  }
  oracion(S, P.oracion);
  conclusion(S, L);
  return {hora:'oficio', nombre:NOMBRES.oficio, primeras:false, ...datosDia(ref, fecha, aviso(ref, k, L, C, 'oficio', PR, nota)), secciones:S};
}

// ---------- Hora intermedia ----------
const ids=s=>(s||[]).map(g=>g.salmo).join(' ');
function armarMenor(hora, fecha, sel, opc){
  const L=window.INTERMEDIA; if(!L || !CP.diaCal(fecha, sel)) return null;
  PAS=X.pasion(fecha, (CP.diaCal(fecha, sel)||{}).sol);
  const H=L.horas[hora];
  const D=capas({salterio:L.salterio, tiempo:L.tiempo, santoral:L.santoral, mapa:L.mapa, adf:L.adf}, fecha, sel, ['salmodia','salmos']);
  const {P, ref, dom, k, C, PR, CS, M, santo, n, nota, comun}=capas({salterio:H.salterio, tiempo:H.tiempo, santoral:H.santoral, mapa:L.mapa, adf:L.adf, comunes:L.comunes, mayores:L.mayores}, fecha, sel, ['himno','ant','lectura','versiculo','oracion'], hora);
  if(CS && CS[hora]) for(const c of ['ant','lectura','versiculo']) if(!(santo&&santo[c]!=null) && CS[hora][c]!=null) P[c]=CS[hora][c];
  if(M && M.oracion && !(santo&&santo.oracion)) P.oracion=M.oracion;
  if((C || PR) && (mayor(ref) || (C && C.salmodia_propia))){   // fiestas y solemnidades (y el Oficio de difuntos) sin propio en la base: del libro (propio y común); la oración, la de Laudes
    for(const c of ['himno','ant','lectura','versiculo']){ if(C && C[hora] && C[hora][c]!=null) P[c]=C[hora][c]; if(PR && PR[hora] && PR[hora][c]!=null) P[c]=PR[hora][c]; }
    if(C) X.elegirComun(P, ['ant','lectura','versiculo'], L.comunes, comun, ref.n, ref.t==='Pascua', hora, hora);
    const o=(PR&&PR.oracion) || (C&&X.oracionElegida(C.oraciones, ref.n, hora, ref.t, n)); if(o) P.oracion=o;
  }
  // Salmodia del día: la del salterio, o los salmos que indiquen el tiempo o la celebración (con sus antífonas solo si son los mismos)
  let sal=D.P.salmodia||[];
  if(D.P.salmos && D.P.salmos.join(' ')!==ids(sal)) sal=D.P.salmos.map(s=>({salmo:s}));
  if(C && C.salmodia_propia && C.salmos) sal=C.salmos.map(s=>({salmo:s}));   // Oficio de difuntos: sus salmos (69, 84, 85)
  // Complementaria: si se eligió, y siempre en las solemnidades que no caen en domingo
  const obligada=!!(ref.sol && !dom), comp=obligada || !!(opc&&opc.complementaria);
  if(comp) sal=L.complementaria[hora];
  const S=[];
  invocacion(S, ref);
  const otrosH=(C && C[hora] && !(PR&&PR[hora]&&PR[hora].himno) && P.himno===C[hora].himno) ? X.himnosComun(L.comunes, comun, ref.n, hora, P.himno, H.himnos) : [];
  himno(S, H.himnos, P.himno, hora, otrosH);
  if(!obligada) S.push({k:'salop', comp});
  salmodia(S, L, sal, P.ant || (sal.some(g=>!g.ant) ? null : null));
  S.push({k:'sec', id:'lectura', t:'Lectura breve', ref:(P.lectura||{}).ref||''});
  S.push({k:'lectura', es:true, t:{es:(P.lectura||{}).texto||'[falta la lectura]'}});
  if(P.versiculo) S.push({k:'resp', es:true, l:{es:P.versiculo}});
  oracion(S, P.oracion);
  conclusion(S, L);
  return {hora, nombre:NOMBRES[hora], primeras:false, ...datosDia(ref, fecha, (M&&!k&&nota==null) ? '' : aviso(ref, k, L, C&&(mayor(ref)||C.salmodia_propia)?C:null, hora, (mayor(ref)||(C&&C.salmodia_propia))?PR:null, nota)), secciones:S};
}

window.Oficio={armar:armarOficio};
for(const h of ['tercia','sexta','nona']) window[h[0].toUpperCase()+h.slice(1)]={armar:(f,s,o)=>armarMenor(h,f,s,o)};
})();
