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

// Las partes del día, capa sobre capa
function capas(L, fecha, sel, campos){
  const ref=CP.diaCal(fecha, sel), d=CP.deIso(fecha), dia=X.DIAS[d.getDay()];
  const P={}, capa=o=>{ if(o) for(const k of campos) if(o[k]!=null) P[k]=o[k]; };
  capa((L.salterio['semana_'+(ref.sal||1)]||L.salterio.semana_1)[dia]);
  const cic=window.Laudes.ciclo(fecha), T1=L.tiempo[ref.fer], T2=L.tiempo[`${ref.fer} (${cic})`];
  capa(T1); capa(T2);
  const adf=(L.adf||{})[ref.n]||{}, k=L.mapa[ref.n]||adf.como;
  const santo=k?L.santoral[k]:null; capa(santo);
  return {P, ref, dia, dom:d.getDay()===0, santo, k, tiempo:!!(T1||T2)};
}
function aviso(ref, k, L){
  if(ref.n===ref.fer || k) return (L.adf||{})[ref.n]&&(L.adf||{})[ref.n].como ? 'Celebración propia de ADF: por ahora, con los textos de otra celebración de la base.' : '';
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
  return {k:'salmo', es:true, id:sid, ant, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!SIN_GLORIA.includes(sid), rubrica:s.rubrica_final||''}; };
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
  return {dia:{titulo:ref.n, tiempo:X.TIEMPO_TXT[ref.t]||ref.t, salterio:ref.sal?`Semana ${X.ROMANO(ref.sal)} del salterio`:'', color:ref.c, grado:ref.g, nota},
          fechaTxt:`${X.DIAS_TXT[d.getDay()]} ${d.getDate()} de ${X.MESES[d.getMonth()]}`,
          versiones:{es:{n:'Liturgia de las Horas'}},
          gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']}};
}
const himno=(S, Hs, n, id)=>{ S.push({k:'sec', id:'himno', t:'Himno'});
  S.push({k:'himno', es:true, opciones:[{id, n:n||'[falta el himno]', lang:'es', est:(Hs[n]||[]).map(e=>e.split('\n')), amen:''}]}); };
const oracion=(S, t)=>{ S.push({k:'sec', id:'oracion', t:'Oración'}); S.push({k:'prosa', es:true, t:{es:t||'[falta la oración]'}, amen:{es:'Amén.'}}); };

// ---------- Oficio de lectura ----------
const CAMPOS_O=['himno','salmodia','versiculo','lectura1','resp1','lectura2','resp2','oracion'];
function armarOficio(fecha, sel){
  const L=window.OFICIO; if(!L || !CP.diaCal(fecha, sel)) return null;
  const {P, ref, dom, k}=capas(L, fecha, sel, CAMPOS_O);
  // Fiestas y solemnidades sin salmodia propia (ni en el tiempo ni en el santoral): la del domingo de la I semana
  const propia=[L.tiempo[ref.fer], L.tiempo[`${ref.fer} (${window.Laudes.ciclo(fecha)})`], k&&L.santoral[k]].some(x=>x&&x.salmodia);
  if(/^(Fiesta|Solemnidad)/.test(ref.g) && !dom && !propia) P.salmodia=L.salterio.semana_1.domingo.salmodia;
  // Te Deum: domingos fuera de Cuaresma, solemnidades, fiestas y octavas de Navidad y de Pascua
  const teDeum = (dom && ref.t!=='Cuaresma' && ref.t!=='Triduo') || ref.sol || /^Fiesta/.test(ref.g) || !!ref.oct;
  const S=[];
  invocacion(S, ref);
  himno(S, L.himnos, P.himno, 'oficio');
  salmodia(S, L, P.salmodia||[]);
  if(P.versiculo) S.push({k:'resp', es:true, l:{es:P.versiculo}});
  const lect=(id, t, x, r)=>{
    S.push({k:'sec', id, t, ref:x&&x.ref&&!/^De /.test(x.ref)?x.ref:''});
    if(!x){ S.push({k:'aviso', t:'Falta esta lectura en la base.'}); return; }
    S.push({k:'lectura_larga', ref:x.ref||'', autor:x.autor||'', titulo:x.titulo||'', t:x.texto||''});
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
  return {hora:'oficio', nombre:NOMBRES.oficio, primeras:false, ...datosDia(ref, fecha, aviso(ref, k, L)), secciones:S};
}

// ---------- Hora intermedia ----------
const ids=s=>(s||[]).map(g=>g.salmo).join(' ');
function armarMenor(hora, fecha, sel, opc){
  const L=window.INTERMEDIA; if(!L || !CP.diaCal(fecha, sel)) return null;
  const H=L.horas[hora];
  const D=capas({salterio:L.salterio, tiempo:L.tiempo, santoral:L.santoral, mapa:L.mapa, adf:L.adf}, fecha, sel, ['salmodia','salmos']);
  const {P, ref, dom, k}=capas({salterio:H.salterio, tiempo:H.tiempo, santoral:H.santoral, mapa:L.mapa, adf:L.adf}, fecha, sel, ['himno','ant','lectura','versiculo','oracion']);
  // Salmodia del día: la del salterio, o los salmos que indiquen el tiempo o la celebración (con sus antífonas solo si son los mismos)
  let sal=D.P.salmodia||[];
  if(D.P.salmos && D.P.salmos.join(' ')!==ids(sal)) sal=D.P.salmos.map(s=>({salmo:s}));
  // Complementaria: si se eligió, y siempre en las solemnidades que no caen en domingo
  const obligada=!!(ref.sol && !dom), comp=obligada || !!(opc&&opc.complementaria);
  if(comp) sal=L.complementaria[hora];
  const S=[];
  invocacion(S, ref);
  himno(S, H.himnos, P.himno, hora);
  if(!obligada) S.push({k:'salop', comp});
  salmodia(S, L, sal, P.ant || (sal.some(g=>!g.ant) ? null : null));
  S.push({k:'sec', id:'lectura', t:'Lectura breve', ref:(P.lectura||{}).ref||''});
  S.push({k:'lectura', es:true, t:{es:(P.lectura||{}).texto||'[falta la lectura]'}});
  if(P.versiculo) S.push({k:'resp', es:true, l:{es:P.versiculo}});
  oracion(S, P.oracion);
  conclusion(S, L);
  return {hora, nombre:NOMBRES[hora], primeras:false, ...datosDia(ref, fecha, aviso(ref, k, L)), secciones:S};
}

window.Oficio={armar:armarOficio};
for(const h of ['tercia','sexta','nona']) window[h[0].toUpperCase()+h.slice(1)]={armar:(f,s,o)=>armarMenor(h,f,s,o)};
})();
