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
function invocacionGabc(solemne, aleluya){
  const g=B.completas.gregoriano.invocacion[solemne?'solemne':'ferial'];
  const [cab,cuerpo]=g.split('%%');
  const ls=cuerpo.split('\n'); const ia=ls.findIndex(l=>/^Al\(/.test(l.trim()));
  let out;
  if(aleluya) out=ls.slice(0,ia+1).map(l=>l.replace(/\s*\(Z-\)\s*$/,''));
  else { out=ls.slice(0,ia); out[out.length-1]=out[out.length-1].replace(/\(;\)\s*$/,'(::)'); }
  return 'name:Deus in adiutorium;\n%%'+out.join('\n');
}
function salvaNosGabc(pascua){
  let g=B.completas.gregoriano.antifona.gabc.replace(/\s*<eu>.*$/s,'');
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
  S.push({k:'vr', gabc:invocacionGabc(el.solemne, !cuaresma), glosa:GR.invocacion.traduccion.filter(p=>cuaresma?!/^Allel/.test(p[0]):true)});

  sec('examen','Examen de conciencia',{plegable:true});
  O.examen.forEach(p=>{
    const m=/^V\. (.*)\nR\. (.*)$/s.exec(p);
    if(m) S.push({k:'vr', pleg:'examen', es:true, v:{es:m[1]}, r:{es:m[2]}});
    else S.push({k:'prosa', pleg:'examen', es:true, t:{es:p.replace(/\n/g,' ')}});
  });

  sec('himno','Himno');
  const pool = pascua?'pascua': cuaresma?'cuaresma': (hoy.t==='Adviento'||hoy.t==='Navidad')?'adviento_navidad':'ordinario';
  S.push({k:'himno', es:true, opciones:C.himnos[pool].map((h,i)=>({id:pool+'-'+i, n:oracionCase(h.titulo), lang:'es', est:h.texto.map(e=>e.split('\n')), amen:''}))});

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

  sec('lectura','Lectura breve');
  S.push({k:'lectura', es:true, ref:{es:J.lectura.ref}, t:{es:J.lectura.texto}});

  if(el.especial){
    sec('responsorio','En lugar del responsorio breve');
    S.push({k:'ant', id:'rb', es:true, n:'Ant.', t:{es:el.especial.en_lugar_del_responsorio}});
  } else {
    sec('responsorio','Responsorio breve');
    S.push({k:'resp', es:true, l:{es:pares(O.responsorio[pascua?'pascua':'ordinario'])}});
  }

  sec('cantico','Cántico evangélico');
  const tp=pascua||!!(el.especial&&/Aleluya/.test(el.especial.antifona_cantico||''));
  S.push({k:'ant', id:'ac', gabc:salvaNosGabc(tp), modo:'3a', glosa:GR.antifona.traduccion.filter(p=>tp||!/^Allel/.test(p[0])), t:{la:'Salva nos, Dómine'}});
  S.push({k:'greg', titulo:'Cántico de Simeón', ref:'Lc 2, 29-32', gabc:GR.cantico.gabc, glosa:GR.cantico.traduccion});
  S.push({k:'ant', rep:'ac'});

  sec('oracion','Oración');
  S.push({k:'oremos', es:true, t:{es:'Oremos.'}});
  const orac = el.especial ? el.especial.oracion : (el.oracion==='solemnidad' ? O.oracion_solemnidad : J.oracion);
  S.push({k:'prosa', es:true, t:{es:orac}, amen:{es:'Amén.'}});

  sec('bendicion','Bendición');
  S.push({k:'vr', gabc:GR.conclusion.gabc, glosa:GR.conclusion.traduccion});

  sec('mariana','Antífona final de la Santísima Virgen');
  const mar=B.marianas[pascua?'pascua':'año'];
  S.push({k:'mariana', es:true, opciones:mar.map((m,i)=>({id:(pascua?'p':'a')+i, n:oracionCase(m.titulo.replace(/[,;:.]$/,'')), l:{es:m.texto.flatMap(e=>e.split('\n'))}}))});

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
