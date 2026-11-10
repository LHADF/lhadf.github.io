/* ================== Armado de Completas para cualquier fecha ==================
   Datos: window.BASE (base/ en YAML) y window.CAL (calendario ADF calculado con el Ordo).
   Devuelve un objeto con las secciones que dibuja app.js. Reglas en base/LEEME.md. */
(function(){
const B=window.BASE, CAL=window.CAL;
const DIAS=['domingo','lunes','martes','miercoles','jueves','viernes','sabado'];
const DIAS_TXT=['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
const MESES=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const TIEMPO_TXT={Ordinario:'Tiempo Ordinario',Adviento:'Adviento',Navidad:'Navidad',Cuaresma:'Cuaresma',Triduo:'Triduo pascual',Pascua:'Tiempo pascual'};
const ROMANO=n=>['','I','II','III','IV'][n]||String(n);

const iso=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const deIso=s=>{ const [y,m,d]=s.split('-').map(Number); return new Date(y,m-1,d,12); };
const masDias=(s,n)=>{ const d=deIso(s); d.setDate(d.getDate()+n); return iso(d); };

/* ---------- Calendario ---------- */
function diaCal(fecha, region){
  const T=CAL.tabla, C=CAL.campos;
  const i=Math.round((deIso(fecha)-deIso(CAL.desde))/864e5);
  const fila=(region==='PGY'&&CAL.PGY[fecha]) || CAL.ARG[i];
  if(!fila) return null;
  const o={fecha}; C.forEach((c,k)=>{ o[c]=['t','n','g','c','fer','oct'].includes(c)?T[fila[k]]:fila[k]; });
  return o;
}
const enRango=f=>f>=CAL.desde && f<=CAL.hasta;
const difiereRegion=f=>!!CAL.PGY[f];

/* ---------- Utilidades de texto ---------- */
const MAYUS=['Dios','Señor','Cristo','Jesús','Jesucristo','Israel','Padre','Hijo','Espíritu','Santo','María','Jerusalén','Sión','Iglesia','Omnipotente','Altísimo','Mesías','Redentor','Reina','Virgen','Madre'];
function oracionCase(s){ // «ACCIÓN DE GRACIAS» → «Acción de gracias», respetando nombres divinos
  const t=s.toLocaleLowerCase('es').replace(/^\p{L}/u,c=>c.toLocaleUpperCase('es'));
  return t.split(/(\s+)/).map(w=>{ const lim=w.replace(/[^\p{L}]/gu,''); const m=MAYUS.find(x=>x.toLocaleLowerCase('es')===lim); return m?w.replace(lim,m):w; }).join('').replace(/\.$/,'');
}
// Estrofas (renglones) → versos salmódicos: pares con mediante; si sobra una línea, flexa
function versosDe(estrofas){
  const versos=[], grupos=[];
  estrofas.forEach(e=>{
    const ls=e.split('\n').map(x=>x.trim()).filter(Boolean), g=[];
    let i=0;
    if(ls.length%2===1 && ls.length>=3){ versos.push(`${ls[0]} † ${ls[1]} * ${ls[2]}`); g.push(versos.length-1); i=3; }
    for(;i+1<ls.length;i+=2){ versos.push(`${ls[i]} * ${ls[i+1]}`); g.push(versos.length-1); }
    if(i<ls.length){ versos.push(ls[i]); g.push(versos.length-1); }
    grupos.push(g);
  });
  return {versos, grupos};
}
const pares=l=>l.map(e=>{ const k=Object.keys(e)[0]; return [k==='texto'?'':k, e[k]]; });

/* ---------- Gregoriano ---------- */
// tono: 'solemne' | 'festivo' | 'ferial'. En Cuaresma, en lugar del «Allelúia», el «Laus tibi, Christe» del mismo tono.
function invocacionGabc(tono, aleluya){
  const cuerpo=B.completas.gregoriano.invocacion[tono].split('%%')[1];
  const m=/(?:<b>)?Al(?:<\/b>)?\(/.exec(cuerpo);
  const laus=/(?:<b>)?Laus(?:<\/b>)?\(.*?\(::\)/s.exec(cuerpo)[0];
  const out = aleluya ? cuerpo.slice(0, cuerpo.indexOf('(::)', m.index)+4) : cuerpo.slice(0, m.index).replace(/\s*$/,' ')+laus;
  return 'name:Deus in adiutorium;\n%%'+out+'\n';
}
// Versión recitada: el texto latino con su traducción, en renglones. spec: [[rol, primera palabra latina, lo dicen todos]]
function recitado(pares, spec){
  const out=[]; let k=0;
  pares.forEach(p=>{
    if(k<spec.length && p[0]===spec[k][1]){ out.push({rol:spec[k][0], todos:!!spec[k][2], pares:[]}); k++; }
    if(!out.length) out.push({rol:'', todos:false, pares:[]});
    out[out.length-1].pares.push(p);
  });
  return out;
}
function salvaNosGabc(pascua, repeticion){
  // repetición: la canta toda la asamblea (en negrita) y sin asterisco
  let g=B.completas.gregoriano.antifona[repeticion?'repeticion':'gabc'].replace(/\s*(<b>)?<eu>.*$/s,'');
  g = pascua ? g.replace(/<i>T\. P\.<\/i>\s*/,'') : g.replace(/\s*<i>T\. P\.<\/i>.*$/s,'');
  return g;
}

/* ---------- Qué Completas corresponden ---------- */
function eleccion(hoy, man){
  const T=B.completas.tiempo[hoy.fer];
  const solemneDia=d=>d && (d.sol||d.dom);
  if(T) return {juego:T.juego, especial:T, solemne:true};
  if(hoy.oct==='navidad'){
    if(man&&man.pv) return {juego:'sabado', oracion:'solemnidad', solemne:true};
    if(hoy.dom) return {juego:'domingo', oracion:'solemnidad', solemne:true};
    return {juego: deIso(hoy.fecha).getDate()%2===0?'sabado':'domingo', oracion:'solemnidad', solemne:true};
  }
  if(man && man.pv) return {juego:'sabado', oracion: man.sol?'solemnidad':'juego', solemne:true, visperasDe:man};
  if(solemneDia(hoy)) return {juego:'domingo', oracion: hoy.sol?'solemnidad':'juego', solemne:true};
  return {juego: DIAS[deIso(hoy.fecha).getDay()], oracion:'juego', solemne:false};
}

// Himno recitado: cada estrofa se parte en sus versos (palabra latina con que empieza cada uno)
function enVersos(rec, inicios){
  return rec.map(l=>({...l, versos:l.pares.reduce((vs,p)=>{ if(!vs.length||inicios.includes(p[0].split(' ')[0])) vs.push([]); vs[vs.length-1].push(p); return vs; },[])}));
}
/* ---------- Armado ---------- */
function armar(fecha, region){
  const hoy=diaCal(fecha, region), man=diaCal(masDias(fecha,1), region);
  if(!hoy) return null;
  const C=B.completas, O=C.ordinario, GR=C.gregoriano;
  const el=eleccion(hoy, man);
  const J=C.salterio[el.juego];
  const pascua=hoy.t==='Pascua', cuaresma=hoy.t==='Cuaresma'||hoy.t==='Triduo';
  const tono=GR.tonos[el.juego]||'8G';
  const S=[]; const sec=(id,t,extra)=>S.push({k:'sec',id,t,...extra});

  sec('inicio','Invocación inicial');
  // Tono: solemne (domingos, solemnidades y sus I Vísperas, Triduo, Octavas), festivo (fiestas), ferial (ferias y memorias)
  const tonoInv = el.solemne ? 'solemne' : /^Fiesta/.test(hoy.g) ? 'festivo' : 'ferial';
  const trInv=cuaresma ? GR.invocacion.traduccion.filter(p=>!/^Allel/.test(p[0])).concat(GR.invocacion.laus) : GR.invocacion.traduccion;
  S.push({k:'vr', tono:tonoInv, gabc:invocacionGabc(tonoInv, !cuaresma), glosa:trInv,
          rec:recitado(trInv.map((p,i)=>i===1?['✠ '+p[0],p[1]]:p), [['V','Deus,'],['R','Dómine,',true],['','Glória',true]])});

  sec('examen','Examen de conciencia',{plegable:true});
  const pr=l=>l.map(x=>x.split(' = '));
  const EX=O.examen;
  S.push({k:'examen', pleg:'examen', es:true, invitacion:EX.invitacion, absolucion:pares(EX.absolucion),
    formulas:EX.formulas.map(f=>f.latin
      ? {id:f.id, titulo:f.titulo, latin:true, todos:f.todos.map(pr), absolucion:f.absolucion.map(e=>{ const k=Object.keys(e)[0]; return [k, pr(e[k])]; })}
      : {id:f.id, titulo:f.titulo, todos:f.todos||null, versos:f.versos?pares(f.versos):null})});

  sec('himno','Himno');
  const pool = pascua?'pascua': cuaresma?'cuaresma': (hoy.t==='Adviento'||hoy.t==='Navidad')?'adviento_navidad':'ordinario';
  // Domingos y solemnidades: siempre abre en el Te lucis; los demás días, el primer himno del tiempo (o el último elegido)
  S.push({k:'himno', es:true, efimera:el.solemne, def: el.solemne?'telucis':pool+'-0', opciones:[{id:'telucis', n:GR.himno.titulo, lang:'la', gabc:GR.himno.gabc, glosa:GR.himno.traduccion, rec:enVersos(recitado(GR.himno.traduccion, [['','Te'],['','Procul'],['','Præsta,']]), ['Te','Rerum','Ut','Sis','Procul','Et','Hostémque','Ne','Præsta,','Patríque','Cum','Regnans'])}].concat(C.himnos[pool].map((h,i)=>({id:pool+'-'+i, n:oracionCase(h.titulo), lang:'es', est:h.texto.map(e=>e.split('\n')), amen:''})))});

  sec('salmodia','Salmodia');
  const sal=pascua?J.salmodia_pascua:J.salmodia; let na=0;
  sal.forEach((g,gi)=>{
    const id='a'+(gi+1);
    S.push({k:'ant', id, es:true, n: sal.length>1?`Ant. ${gi+1}`:'Ant.', t:{es:g.ant}, modo:tono});
    g.salmos.forEach(sid=>{
      const s=B.salmos[sid]; const v=versosDe(s.texto);
      S.push({k:'salmo', es:true, id:sid, ant:id, titulo:{es:s.titulo}, lema:{es:oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:true});
    });
    S.push({k:'ant', rep:id, es:true});
  });

  sec('lectura','Lectura breve',{ref:J.lectura.ref});
  S.push({k:'lectura', es:true, t:{es:J.lectura.texto}});
  S.push({k:'deo', t:GR.lectura_respuesta[0][0]});   // ℟. Deo grátias (la dicen todos)

  if(el.especial){
    sec('responsorio','En lugar del responsorio breve');
    S.push({k:'ant', id:'rb', es:true, n:'Ant.', t:{es:el.especial.en_lugar_del_responsorio}});
  } else {
    sec('responsorio','Responsorio breve');
    const rg = pascua ? null : GR.responsorio.ordinario;   // cantado: por ahora, el del Tiempo Ordinario
    S.push({k:'resp', es:true, l:{es:pares(O.responsorio[pascua?'pascua':'ordinario'])}, ...(rg?{gabc:rg.gabc, glosa:rg.traduccion}:{})});
  }

  sec('cantico','Cántico evangélico');
  const tp=pascua||!!(el.especial&&/Aleluia/i.test(el.especial.antifona_cantico||''));
  const trAnt=GR.antifona.traduccion.filter(p=>tp||!/^Allel/.test(p[0])), recAnt=recitado(trAnt, [['Ant','Salva',true]]);
  S.push({k:'ant', id:'ac', gabc:salvaNosGabc(tp), modo:'3a', glosa:trAnt, rec:recAnt, t:{la:'Salva nos, Dómine'}});
  S.push({k:'cantico', titulo:'Cántico de Simeón', ref:'Lc 2, 29-32', gabc:GR.cantico.gabc, glosa:GR.cantico.traduccion,
          tono:GR.cantico.tono, versos:GR.cantico.versos, inter:GR.cantico.traduccion_versos,
          verso1:GR.cantico.primer_verso, inter1:GR.cantico.traduccion});
  S.push({k:'ant', id:'ac2', gabc:salvaNosGabc(tp, true), modo:'3a', glosa:trAnt, rec:recAnt, t:{la:'Salva nos, Dómine'}});

  sec('oracion','Oración');
  S.push({k:'oremos', es:true, t:{es:'Oremos.'}});
  const orac = el.especial ? el.especial.oracion : (el.oracion==='solemnidad' ? O.oracion_solemnidad : J.oracion);
  S.push({k:'prosa', es:true, t:{es:orac}, amen:{es:'Amén.'}});

  sec('bendicion','Conclusión');
  S.push({k:'vr', gabc:GR.conclusion.gabc, glosa:GR.conclusion.traduccion, rec:recitado(GR.conclusion.traduccion.map(p=>p[0]==='quiétam'?['✠ '+p[0],p[1]]:p), [['V','Noctem'],['R','Amen.',true]])});

  sec('mariana','Antífona final de la Santísima Virgen');
  // Domingos y solemnidades (y sus I Vísperas, Triduo y Octavas): versión solemne; los demás días, la simple.
  // Adviento y Navidad: Alma Redemptóris; de la Candelaria (2 de febrero) al fin de Cuaresma: Ave Regína cælórum;
  // Pascua: Regína cæli; Tiempo Ordinario: Salve Regína (con Sub tuum como opción en ferias, memorias y fiestas);
  // Asunción: Ave Regína cælórum, solemne o simple.
  const GM=GR.marianas, op=(k,id)=>{ const tr=(GM[k.replace('_solemne','_simple')]||GM[k]).traduccion;   // recitada: el texto completo (en la solemne del Regina cæli la melodía parte el último aleluya)
    return {id, n:GM[k].titulo, gabc:GM[k].gabc, glosa:GM[k].traduccion, rec:recitado(tr, [['',tr[0][0],true]])}; };
  const f=deIso(fecha), mes=f.getMonth()+1, dia=f.getDate();
  const vis=el.visperasDe||hoy;
  let tipo;
  if(/Asunción/.test(vis.n)) tipo='asuncion';
  else if(pascua) tipo='regina_caeli';
  else if(hoy.t==='Adviento'||hoy.t==='Navidad') tipo='alma';
  else if(hoy.t==='Cuaresma'||hoy.t==='Triduo'||(hoy.t==='Ordinario'&&(mes===2&&dia>=2||mes===3))) tipo='ave';
  else tipo='salve';
  const sol=el.solemne;
  if(el.especial && el.especial.antifona_final){   // Triduo: Ave Regína cælórum, simple o solemne
    const t=el.especial.antifona_final;
    S.push({k:'mariana', es:true, opciones:[op(t+'_simple', t+'-sim'), op(t+'_solemne', t+'-sol')]});
  }
  else if(tipo==='asuncion') S.push({k:'mariana', es:true, opciones:[op('ave_solemne','ave-sol'), op('ave_simple','ave-sim')]});
  else if(tipo==='salve' && !sol) S.push({k:'mariana', es:true, efimera:true, opciones:[op('salve_simple','salve-sim'), op('sub_tuum','subtuum')]});   // siempre abre en la Salve simple
  else S.push({k:'mariana', es:true, opciones:[op(tipo+(sol?'_solemne':'_simple'), tipo+(sol?'-sol':'-sim'))]});

  const d=deIso(fecha);
  const salterio = hoy.sal ? `Semana ${ROMANO(hoy.sal)} del salterio` : '';
  return {
    nombre:'Liturgia de las Horas',
    versiones:{es:{n:'Liturgia de las Horas'}},
    gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']},
    dia:{titulo:hoy.n, tiempo:TIEMPO_TXT[hoy.t]||hoy.t, salterio, color:hoy.c, grado:hoy.g,
         visperas: el.visperasDe ? `Completas después de las I Vísperas de: ${el.visperasDe.n}` : ''},
    fechaTxt:`${DIAS_TXT[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]}`,
    juego:el.juego,
    secciones:S,
  };
}

window.Completas={armar, diaCal, enRango, difiereRegion, iso, deIso, masDias, regiones:CAL.regiones};
})();
