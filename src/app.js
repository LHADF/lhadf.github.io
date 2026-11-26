/* ================== Cervus (LH ADF) ================== */
const SAL=window.Salmodia, CP=window.Completas;
let D=null; // Completas del día elegido (src/completas.js)
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------- Estado ---------- */
const DEF={vista:'hoy', rito:'novus', modo:'canto', salmos:'primer', trad:true,
  zoom:1, theme:'light', tonos:{}, himno:{}, mariana:{}, examen:false, cal:'', cantado:true};
let S=DEF;
try{ const g=JSON.parse(localStorage.getItem('septies')||'null'); if(g){ S=Object.assign({},DEF,g); delete S.ves; if(!g.modo) S.modo=g.canto?'canto':(g.lengua==='es'?'es':'la');
  if(g.cal==null) S.cal=g.region==='PGY'?'PGY':''; delete S.region;   // antes se elegía país en Opciones; ahora, calendario en el inicio
  if(g.zoom==null) S.zoom=(g.lec||1.2)/1.2*({g:1.15,mg:1.3,max:1.5}[g.esc]||1);   // antes había dos controles (texto y aplicación): se unifican
  S.zoom=Math.min(2,Math.max(.8,Math.round(S.zoom*10)/10)); delete S.lec; delete S.esc; } }catch(e){}
if(S.salmos!=='primer') S.salmos='primer';   // ya no hay opción para cambiarlo: un valor viejo guardado («sin partitura») dejaba los salmos sin partitura
if(S.theme!=='dark') S.theme='light'; // claro por defecto; oscuro solo si se elige
// Reinicio único (como en el Cantoral): todos vuelven a claro una vez; si después eligen oscuro, se respeta
try{ if(!localStorage.getItem('temaClaro2026')){ S.theme='light'; localStorage.setItem('temaClaro2026','1'); guardar(); } }catch(e){}
S.antGreg=true; delete S.respCanto;
/* Una sola versión: Liturgia de las Horas en modo canto (salmos y lecturas en español pautado, lo demás en latín) */
S.rito='novus'; S.modo='canto';
function aplicarModo(kind, sec){
  S.canto = S.modo==='canto';
  if(sec && sec.es){ S.lengua='es'; return; } // textos de la base en español
  if(S.modo==='es') S.lengua='es';
  else if(S.modo==='la') S.lengua='bi';
  // salmos y lecturas en español; el cántico evangélico, todo en latín
  else S.lengua = ((kind==='salmo'&&!(sec&&sec.cantico))||kind==='lectura') ? 'es' : (S.trad?'bi':'la');
}
aplicarModo();
function guardar(){ try{ const {lengua,canto,antGreg,fecha,_marDia,_varDia,_prep,_elige,difuntos,comunOn,comunPrim,comunElige,...g}=S; localStorage.setItem('septies',JSON.stringify(g)); }catch(e){} }
let DH=null; // la hora abierta cuando no es Completas (Laudes o Vísperas)
const MAYORES={laudes:'Laudes', visperas:'Visperas', oficio:'Oficio', tercia:'Tercia', sexta:'Sexta', nona:'Nona'};
// Archivo de datos de cada hora (Tercia, Sexta y Nona comparten el de la Hora intermedia)
const ARCHIVO={laudes:'laudes', visperas:'visperas', oficio:'oficio', tercia:'intermedia', sexta:'intermedia', nona:'intermedia'};
const cargada=h=>!!window[(ARCHIVO[h]||h).toUpperCase()];
const R=()=> (S.vista==='hora' && MAYORES[S.hora] && DH) || D;
// Los datos de Laudes y de Vísperas van en archivos aparte: se cargan recién al abrir la hora
const _carga={};
function cargarHora(h){
  const a=ARCHIVO[h]||h;
  if(window[a.toUpperCase()]) return Promise.resolve();
  if(!_carga[a]) _carga[a]=new Promise((ok,mal)=>{ const sc=document.createElement('script'); sc.src=(window.HORAS_URL||{})[a]||a+'.js'; sc.onload=ok; sc.onerror=()=>{ _carga[a]=null; mal(); }; document.head.appendChild(sc); });
  return _carga[a];
}
const VES=()=>'es';
// Día litúrgico de hoy: antes de las 5 de la mañana, todavía son las Completas de ayer
function fechaHoy(){ const d=new Date(); if(d.getHours()<5) d.setDate(d.getDate()-1); return CP.iso(d); }
S.fecha=fechaHoy();
// Qué calendario se sigue (S.cal, se recuerda) y qué celebración optativa se eligió a mano cada día (S._varDia, no se guarda)
function SEL(){ return {cal:S.cal||'', dia:S._varDia||(S._varDia={})}; }
const linaje=c=>{ const l=[]; for(;c;c=window.CAL.padres[c]) l.push(c); return l; };
// Fichas de calendario del día: la del calendario ADF, una por cada calendario que difiere y una por cada memoria libre
function fichasCal(){
  const ops=CP.opcionesDia(S.fecha, SEL()), mio=linaje(S.cal), out=[];
  ops.forEach((o,i)=>{
    if(o.tipo==='r') o.siglas.forEach(sg=>out.push({i, sg, txt:sg, on:o.actual&&(mio.includes(sg)||!o.siglas.some(x=>mio.includes(x))), o}));
    else out.push({i, sg:'', txt:o.f.n==='Sancta María in sábbato'?'Sancta María in sábbato':o.siglas.join(' · '), on:o.actual, o});
  });
  return out;
}
const claveElige=()=>S.fecha+(S.difuntos?'|dif':'');
function cargarDia(){
  if(!CP.enRango(S.fecha)) S.fecha=fechaHoy();
  const MODO=CP._.modo;
  MODO.difuntos=false; MODO.comun=null; MODO.inv=undefined;
  D=CP.armar(S.fecha, SEL());
  // Oficio de difuntos (botón del inicio): las horas, con todo del Oficio de difuntos. Invitatorio de Laudes: se puede quitar.
  MODO.difuntos=!!S.difuntos;
  // Comunes de los santos (botón del inicio): las horas como la celebración de un santo, con todo del común elegido.
  // Lo elegido en «Otras opciones» (S.comunElige) vale mientras se reza; MODO.comun.alts junta las opciones de cada elemento.
  MODO.comun = (S.comunOn && !S.difuntos) ? {...CP._.comunSantos({...(S.comunSel||{}), primeras:S.hora==='visperas' && !!S.comunPrim}), elige:S.comunElige||{}, alts:{}} : null;
  // Fuera del modo común, las «O bien» que rotan (y las demás opciones del común) también se pueden elegir: lo elegido
  // (S._elige, por día y hora; no se guarda) vale mientras se mira ese día.
  MODO.opc = MODO.comun ? null : {elige:(S._elige||{})[claveElige()]||{}, alts:{}};
  MODO.inv = (S.hora==='laudes' && S.invLaudes===false) ? false : undefined;
  // Celebraciones que pueden tomar de dos comunes (virgen mártir): el común elegido al comienzo de la hora, que vale
  // para todas las horas de ese día (S.comunDia = {f: fecha de la celebración, id}; se guarda)
  MODO.comunDia = S.comunDia || null;
  DH = (MAYORES[S.hora] && cargada(S.hora)) ? window[MAYORES[S.hora]].armar(S.fecha, SEL(), {complementaria:!!S.compl}) : null;
  // Oficio de lectura unido a Laudes: después de las lecturas (y del Te Deum) siguen las Laudes desde la salmodia,
  // sin su invocación inicial ni su himno; el Oficio no tiene oración ni conclusión propias.
  // Oficio de lectura como primera oración del día: empieza con el invitatorio (el de Laudes de ese día)
  if(DH && S.hora==='oficio' && S.invOficio && window.LAUDES){
    MODO.inv=true; const Li=window.Laudes.armar(S.fecha, SEL()); MODO.inv=undefined;
    const a=Li.secciones.findIndex(s=>s.k==='sec'&&s.id==='invitatorio'), b=Li.secciones.findIndex(s=>s.k==='sec'&&s.id==='inicio');
    if(a>=0 && b>a) DH={...DH, secciones:[...Li.secciones.slice(a,b), ...DH.secciones]};
  }
  if(DH && S.hora==='oficio' && S.unirLaudes && window.LAUDES){
    const O=DH.secciones, corte=O.findIndex(s=>s.k==='sec'&&s.id==='oracion'), Lh=window.Laudes.armar(S.fecha, SEL());
    if(Lh){ const i=Lh.secciones.findIndex(s=>s.k==='sec'&&s.id==='salmodia');
      // El Oficio pasa a ser la primera hora del día: empieza como Laudes (Dómine, lábia mea e invitatorio), no con «Deus in adiutórium»
      const iniL=S.invOficio ? O.slice(0, O.findIndex(s=>s.k==='sec'&&s.id==='himno')) : Lh.secciones.slice(0, Lh.secciones.findIndex(s=>s.k==='sec'&&s.id==='himno')), iniO=O.findIndex(s=>s.k==='sec'&&s.id==='himno');
      DH={...DH, unidas:true, secciones:[...iniL, ...O.slice(iniO,corte), {k:'sec', id:'l-laudes', t:'Laudes', titulo:true}, ...Lh.secciones.slice(i).map(s=>s.k==='sec'?{...s,id:'l-'+s.id}:s)]}; }
  }
  // Uso ADF: Vísperas y Completas juntas. Después de la oración de Vísperas se omite su conclusión y siguen, de Completas:
  // examen de conciencia, cántico evangélico, oración, conclusión y antífona de la Virgen.
  if(DH && S.hora==='visperas' && S.unirCompletas && D){
    const V=DH.secciones, corte=V.findIndex(s=>s.k==='sec'&&s.id==='bendicion');
    const C=[]; let toma=false;
    for(const s of D.secciones){ if(s.k==='sec') toma=['examen','cantico','oracion','bendicion','mariana'].includes(s.id); if(toma) C.push(s.k==='sec'?{...s,id:'c-'+s.id,plegable:false}:{...s,pleg:false}); }
    DH={...DH, unidas:true, secciones:[...V.slice(0,corte), ...C]};
  }
  if(DH && MODO.difuntos) DH={...DH, difuntos:true, dia:{...DH.dia, titulo:'Oficio de difuntos', grado:'', nota:''}};
  if(DH && MODO.opc) DH={...DH, alts:MODO.opc.alts};
  if(DH && MODO.comun) DH={...DH, comun:true, alts:MODO.comun.alts, dia:{...DH.dia, titulo:MODO.comun.titulo, grado:MODO.comun.grado, nota:''}};
  S._marDia={}; // la antífona mariana elegida a mano vale solo para ese día
}
cargarDia();
// S.trad (glosa bajo la partitura) lo usan las funciones heredadas del Cantoral
function aplicarTema(){ const r=document.documentElement; r.dataset.theme=S.theme==='dark'?'dark':'light'; const mt=document.querySelector('meta[name=theme-color]'); if(mt) mt.content=S.theme==='dark'?'#000000':'#ffffff'; r.style.setProperty('--esc',ESC()); r.style.setProperty('--lec',LEC()); }
// Un solo tamaño (S.zoom, de 80 % a 200 % de a 10 %): el texto de la hora crece todo eso; botones y títulos, la mitad (hasta 150 %).
function ESC(){ return S.zoom<=1 ? 1 : Math.min(1.5, 1+(S.zoom-1)/2); }
function LEC(){ return 1.2*S.zoom/ESC(); }

/* ---------- Texto según lengua ---------- */
// Devuelve {p: principal, s: secundario (solo en bilingüe), falta: aviso}
function txt(o){
  if(!o) return {p:''};
  const es=VES();
  const esTxt=o[es]!=null?o[es]:null;
  if(S.lengua==='la'){ if(o.la!=null) return {p:o.la}; return {p:esTxt||'', falta:'la'}; }
  if(S.lengua==='es'){ if(esTxt!=null) return {p:esTxt}; return {p:o.la||'', falta:'es'}; }
  // bilingüe
  if(o.la!=null) return {p:o.la, s:esTxt};
  return {p:esTxt||'', falta:'la'};
}
const langPrincipal=()=>S.lengua==='es'?'es':'la';
function nombreVersion(){
  const v=R().versiones; const es=v[VES()]||{};
  if(S.lengua==='la') return '<b>Latín</b>';
  if(S.lengua==='es') return '<b>'+esc(es.n)+'</b>';
  return '<b>Latín</b> · '+esc(es.n);
}
// Capitular (docs/diseno.md): la primera letra, grande y roja, a lo alto de dos renglones, como la del gregoriano.
// Lecturas breves, himnos en español y cánticos evangélicos. No va si el texto empieza con ¡, ¿ u otro signo.
// Sinalefas de los himnos en español (base/himnos: «‿» entre las palabras que se unen; tools/sinalefas.py): la vocal
// final que se une a la palabra siguiente va en cursiva, y entre las palabras, un espacio común
const sinalefas=h=>h.replace(/(\p{L})([^\p{L}\s<]*)‿/gu,'<i class="sin">$1</i>$2 ').replace(/‿/g,' ');
const capiHTML=ch=>`<span class="capi">${esc(ch)}</span>`;
function capiTxt(t){ const s=String(t||''), m=/^\p{L}/u.exec(s); return m ? capiHTML(m[0])+esc(s.slice(m[0].length)) : esc(s); }
// Lectura breve con capitular y con la flexa (†) y el metro (*) para salmodiarla (CP._.marcarLectura)
function lecturaMarcada(p){
  return CP._.marcarLectura(p).map((x,i)=>(i?esc(x.t):capiTxt(x.t))+(x.sg?`&nbsp;<span class="sg">${x.sg}</span>`:'')).join(' ');
}
function marcas(s){ // ℣ ℟ * † ✠ en rojo
  return esc(s).replace(/✠/g,'<span class="cruz">✠</span>').replace(/ \* /g,' <span class="k">*</span> ').replace(/ † /g,' <span class="k">†</span> ');
}

/* ---------- Partituras (Exsurge, igual que el Cantoral) ---------- */
let _id=0; const GAB=new Map();
// sal: partitura de la salmodia (los acentos del modo van en 700, docs/diseno.md)
function partituraHTML(gabc, glosa, drop=true, sal=false){ const id='g'+(++_id); GAB.set(id,{gabc,glosa,drop}); return `<div class="partitura${sal?' sal-p':''}" data-g="${id}"><p class="cargando">Preparando la partitura…</p></div>`; }
const cacheSvg=new Map();
function svgDe(id, ancho, tam){ // tam: tamaño de la letra y de la traducción, en unidades de la partitura
  const it=GAB.get(id); if(!it) return Promise.reject();
  const conGlosa=S.trad && it.glosa && it.glosa.length;
  const clave=(it.drop?'d':'n')+it.gabc.length+'|'+it.gabc.slice(-60)+'|'+ancho+'|'+(conGlosa?1:0)+'|'+(tam?tam.letra.toFixed(2)+'/'+tam.trad.toFixed(2):'')+'|'+it.gabc.slice(0,80);
  if(cacheSvg.has(clave)) return Promise.resolve(cacheSvg.get(clave));
  return fuentesListas().then(()=>new Promise((ok,mal)=>{
    try{
      let g=it.gabc; if(conGlosa) g=insertarTraduccion(g,it.glosa);
      const ctxt=contextoExsurge();
      if(tam){ ctxt.textStyles.lyric.size=tam.letra; ctxt.textStyles.translation.size=tam.trad; }   // mismo tamaño que el texto en español
      const maps=exsurge.Gabc.createMappingsFromSource(ctxt, gabcParaExsurge(gabcCuerpo(g))); espaciarSilabas(maps);
      const score=new exsurge.ChantScore(ctxt, maps, it.drop && !/initial-style:\s*0/.test(g));
      const modo=gabcModo(g); if(modo) score.annotation=new exsurge.Annotations(ctxt,'%'+ROMANO_MODO[modo]+'%');
      score.performLayoutAsync(ctxt,()=>score.layoutChantLines(ctxt,ancho,()=>{
        const svg=score.createSvgNode(ctxt);
        const w=parseFloat(svg.getAttribute('width')), h=parseFloat(svg.getAttribute('height'));
        if(!svg.getAttribute('viewBox')&&w&&h) svg.setAttribute('viewBox','0 0 '+w+' '+h);
        svg.removeAttribute('width'); svg.removeAttribute('height');
        // Las reglas de estilo de Exsurge valen para toda la página: se limitan a esta partitura (y a su tamaño de letra)
        const marca=tam?tam.letra.toFixed(2)+'-'+tam.trad.toFixed(2):'base'; svg.setAttribute('data-t',marca);
        svg.querySelectorAll('style').forEach(st=>{ st.textContent=st.textContent.replace(/svg\.Exsurge(?=[ .{:])/g,`svg.Exsurge[data-t="${marca}"]`); });
        const html=svg.outerHTML.replace(/\u27E6/g,'[').replace(/\u27E7/g,']'); cacheSvg.set(clave,html); ok(html);
      }));
    }catch(e){ mal(e); }
  }));
}
function pintar(raiz){
  const els=[...(raiz||document).querySelectorAll('.partitura[data-g]')];
  const zoom=LEC()/1.15;
  return els.reduce((p,el)=>p.then(()=>{
    const ancho=Math.max(260, Math.round((el.clientWidth||600)/zoom/10)*10); el.dataset.w=ancho;
    // La partitura se dibuja con ancho «ancho» y se escala al ancho real: la letra se calcula para que, ya escalada,
    // mida lo mismo que el texto en español (y la traducción, lo mismo que la glosa: .84 em)
    const cuerpo=parseFloat(getComputedStyle(el).fontSize)||16, escala=(el.clientWidth||ancho)/ancho;
    const tam={letra:cuerpo/escala, trad:cuerpo*.84/escala};
    return svgDe(el.dataset.g, ancho, tam).then(html=>{ if(!el.isConnected) return; el.innerHTML=html; const svg=el.querySelector('svg'); uniformarRenglones(svg); if(S.trad) ajustarTraducciones(svg); })
      .catch(()=>{ if(el.isConnected) el.innerHTML='<p class="cargando">No se pudo dibujar la partitura.</p>'; });
  }), Promise.resolve());
}

/* ---------- Salmos ---------- */
function antDe(id){ return R().secciones.find(s=>s.k==='ant'&&s.id===id); }
// Modo de un salmo o cántico. En Laudes y Vísperas (sal.modo, de laudes.js): el de la semana del salterio, o el que se
// eligió a mano en el desplegable para esta hora (S.tonos). En lo demás, el de la antífona.
const claveTono=sec=>`${S.fecha}|${R().hora||R().nombre||''}|${sec.id}`;
function tonoDe(sal){ if(sal.modo) return (S.tonos||{})[claveTono(sal)] || sal.modo; const a=antDe(sal.ant); return (a&&a.modo)||'8G'; }
// Indicación del modo, en rojo, con un desplegable para cambiarlo
function selectorModo(sec){
  const cod=SAL.tono(tonoDe(sec)).cod, def=SAL.tono(sec.modo).cod;
  const op=t=>`<option value="${t.cod}"${t.cod===cod?' selected':''}>${esc(t.corta)}</option>`, L=SAL.listaTonos();
  // arriba, los modos que se cantan en el salterio (por semana y domingo); los demás, en «Más modos» (CRU, 20/11/2026)
  const USADOS=['1g','2D','3a','4g','5a','6F','7a','8G'], usados=USADOS.map(c=>L.find(t=>t.cod===c)).filter(Boolean);
  return `<label class="modo">Modo <select data-chg="tono" data-k="${esc(claveTono(sec))}" data-def="${def}" aria-label="Modo de la salmodia"><optgroup label="Modos">${usados.map(op).join('')}</optgroup><optgroup label="Más modos">${L.filter(t=>!USADOS.includes(t.cod)).map(op).join('')}</optgroup></select></label>`;
}
// Devuelve las líneas (hemistiquios) de un verso, ya marcadas
const ESTRIBILLO=/^R\.\s/;
const CRUZ_ANT=SAL.CRUZ_ANT, omitirAnt=SAL.omitirAnt;   // antífona con † (salmodia.js)
// La antífona lleva † (en rojo) si el salmo que la usa empieza con ella
function cruzVale(antSec){
  const t=antSec && antSec.t && antSec.t.es; if(!t) return false;
  const sal=R().secciones.find(s=>s.k==='salmo' && s.ant===antSec.id);
  return !!(sal && sal.es && sal.versos.es && omitirAnt(sal.versos.es, t));
}
// Renglones de una mitad recitada: el que sigue en la misma mitad (« ¶ ») lleva la marca SAL.SIGUE (va más adentro)
const renglonesT=t=>t.split(' ¶ ').map((x,i)=>(i?SAL.SIGUE:'')+esc(x));
// Clase del renglón: h1 el primero, h2 los demás, h3 el que sigue en la misma mitad
const claseRenglon=(l,k)=>String(l).startsWith(SAL.SIGUE)?'h3':(k?'h2':'h1');
const sinSigue=l=>String(l).replace(SAL.SIGUE,'');
function lineasVerso(v, modo, cod, lang, intonar){
  v=v.replace(/✠\s*/g,'');
  if(modo==='texto' || ESTRIBILLO.test(v)){
    const d=SAL.dividirVerso(v); const out=[];
    if(d.flex) out.push(`${esc(d.flex)}&nbsp;<span class="sg">†</span>`);
    if(d.ter!=null && !d.med) out.push(...renglonesT(d.ter));   // solo la segunda mitad (antífona con †)
    else if(d.ter!=null){ const m=renglonesT(d.med); m[m.length-1]+='&nbsp;<span class="sg">*</span>'; out.push(...m, ...renglonesT(d.ter)); }   // « ¶ »: dos renglones en la misma mitad
    else out.push(...renglonesT(d.med));
    return out;
  }
  return SAL.renglonesVerso(SAL.pautarVerso(v,cod,lang,intonar));
}
// Traducción de un verso repartida en las mismas líneas que el latín
function glosaVerso(latV, glV){
  const a=SAL.dividirVerso(latV.replace(/✠\s*/g,'')), b=SAL.dividirVerso(String(glV||'').replace(/✠\s*/g,''));
  const out=[];
  if(a.flex!=null) out.push(b.flex!=null?b.flex:'');
  if(a.ter!=null){ out.push(b.ter!=null?(b.flex!=null||a.flex!=null?b.med:b.med):(b.med||'')); out.push(b.ter!=null?b.ter:''); }
  else out.push(b.ter!=null?b.med+' '+b.ter:(b.med||''));
  // si el español no tiene flexa y el latín sí, la primera mitad va bajo la flexa y la mediante
  if(a.flex!=null && b.flex==null && b.ter!=null){ out[0]=b.med; out[1]=''; }
  return out;
}
// cruz: el primer verso es lo que queda del que empezó la antífona (antífona con †): lleva la † al comienzo, como guía de
// dónde sigue el canto (26/11/2026)
function versosHTML(versos, modo, cod, lang, desde, glosas, ent, cruz){
  return versos.map((v,i)=>{
    const ls=lineasVerso(v,modo,cod,lang,(desde+i)===(ent||0));
    if(cruz && desde+i===0 && ls.length) ls[0]=`<span class="sg">†</span>&nbsp;`+ls[0];
    const gs=glosas?glosaVerso(v,glosas[i]):null;
    return `<p class="v">${ls.map((l,k)=>`<span class="${claseRenglon(l,k)}">${sinSigue(l)}</span>${gs&&gs[k]?`<span class="gl ${k?'h2':'h1'}">${esc(gs[k])}</span>`:''}`).join('')}</p>`;
  }).join('');
}
// Frases en versalitas dentro de un verso (25/11/2026): «sanctum nomen eius» del Magníficat. La versalita conserva las marcas
// de la pauta (negrita del acento, cursiva de la preparación). Devuelve los índices de las palabras que van en versalitas.
const VERSALITAS=[['sanctum','nomen','eius']];
function versalitas(ws){
  const n=ws.map(w=>w.replace(/\*\*|_/g,'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-zæœ]/g,'')), out=new Set();
  for(const f of VERSALITAS) for(let i=0;i+f.length<=n.length;i++) if(f.every((x,j)=>n[i+j]===x)) f.forEach((x,j)=>out.add(i+j));
  return out;
}
// Lo mismo en la letra de una partitura (GABC): cada sílaba de esas palabras, entre <sc> y </sc> (Exsurge las dibuja en
// versalitas, también dentro de <b> o <i>)
function versalitasGabc(g){
  const i0=g.indexOf('%%')+2, cuerpo=g.slice(i0), toks=[]; let m; const re=/([^()]*)(\([^)]*\))/g;
  while((m=re.exec(cuerpo))) toks.push({t:m[1], n:m[2]});
  const pal=[]; toks.forEach((x,i)=>{ if(!pal.length || /^\s/.test(x.t) || !x.t) pal.push([]); pal[pal.length-1].push(i); });
  const vs=versalitas(pal.map(p=>p.map(i=>toks[i].t.replace(/<[^>]+>/g,'')).join('').trim()));
  if(!vs.size) return g;
  pal.forEach((p,k)=>{ if(vs.has(k)) p.forEach(i=>{ const t=toks[i].t, ini=t.match(/^\s*/)[0]; if(t.trim()) toks[i].t=`${ini}<sc>${t.trim()}</sc>`; }); });
  return g.slice(0,i0)+toks.map(x=>x.t+x.n).join('')+cuerpo.slice(cuerpo.lastIndexOf(')')+1);
}
// Versos con marcas escritas a mano: **negrita** (acento) y _cursiva_ (preparación); * mediante, † flexa.
// glosas: por versículo, pares «latín → español» palabra por palabra, en el orden del texto (el * y la † no llevan par)
function versosMarcados(versos, glosas, capi){   // capi: capitular en el primer verso (cántico evangélico sin partitura)
  // las marcas de la pauta de canto (**negrita**, _cursiva_) solo en el modo cantado; recitado, texto llano
  const m0=t=>CANTA() ? esc(t).replace(/\*\*(.+?)\*\*/g,'<b class="ac">$1</b>').replace(/_(.+?)_/g,'<i>$1</i>') : esc(t.replace(/\*\*(.+?)\*\*/g,'$1').replace(/_(.+?)_/g,'$1'));
  return versos.map((v,i)=>{
    const pares=glosas&&glosas[i]||null; let k=0, resto=0;
    const mitades=v.split(/ \* /);
    const hs=mitades.map((h,hi)=>{ const ws=h.trim().split(/\s+/), vs=versalitas(ws); return ws.map((w,wi)=>{
        if(w==='†') return `<span class="sg">†</span>`;
        const m=t=>vs.has(wi) ? `<span class="vers">${m0(t)}</span>` : m0(t);
        if(!pares) return m(w);
        let tr='', ini=false;
        if(resto===0 && k<pares.length){ const p=pares[k++]; resto=String(p[0]).trim().split(/\s+/).length; tr=p[1]; ini=resto>1; }
        if(resto>0) resto--;
        const h=`<span class="w">${m(w)}${tr?`<span class="tr">${marcas(tr)}</span>`:''}</span>`;
        return ini ? {ini:h} : h;
      }); }).map(l=>l.reduce((a,x)=>{ // las dos primeras palabras de un par («ad dandam») no se separan de renglón
        const u=a[a.length-1]; if(u && typeof u==='object'){ a[a.length-1]=`<span class="nw">${u.ini} ${x}</span>`; } else a.push(x); return a; },[])
        .map(x=>typeof x==='object'?x.ini:x));
    const hs2=hs.map((ws,hi)=>{ // el asterisco no baja solo de renglón: va pegado a la última palabra
      if(hi<mitades.length-1 && ws.length){ const u=ws.pop(); ws.push(`<span class="nw">${u}&nbsp;<span class="sg">*</span></span>`); }
      return ws.join(' '); });
    let cap='';
    if(capi && i===0 && !pares) hs2[0]=hs2[0].replace(/^((?:<[^>]+>)*)(\p{L})/u, (x,tags,ch)=>{ cap=ch; return tags; });
    return `<p class="v${pares?' il':''}${cap?' capi-on':''}">${cap?capiHTML(cap):''}${hs2.map((h,n)=>`<span class="${n?'h2':'h1'}">${h}</span>`).join('')}</p>`;
  }).join('');
}
function salmoHTML(sal){
  const r=R(); const es=VES();
  // nombres de las partes como en la Liturgia de las Horas en español, aunque el texto vaya en latín
  const nombre=o=>({p:o[es]!=null?o[es]:(o.es!=null?o.es:o.la)});
  const t=nombre(sal.titulo); const lema=sal.lema?nombre(sal.lema):null;
  const L=langPrincipal();
  const keyP = S.lengua==='es' ? es : 'la';
  const keyS = S.lengua==='bi' ? (sal.versos[es]?es:'es79') : null;
  const vP=sal.versos[keyP]||sal.versos.la, gP=sal.grupos[keyP]||sal.grupos.la;
  const glP=(r.gloria[keyP]||r.gloria.la), glS=keyS?(r.gloria[keyS]):null;
  const cod=tonoDe(sal);
  // Se canta pautado y con partitura: en latín, siempre; en español, en Laudes y Vísperas (los que traen modo), si se canta
  const canta = sal.es ? !!sal.modo && CANTA() : S.canto;
  const modo=canta? S.salmos : 'texto';
  let h=`<div class="salmo-h"><div class="cab"><span class="t">${esc(cita(t.p))}</span>${sal.ref?`<span class="ref">${esc(sal.ref)}</span>`:''}${sal.modo&&canta?selectorModo(sal):''}</div>${lema&&lema.p?`<span class="lema">${esc(lema.p)}</span>`:''}</div>`;
  // Cántico Ap 19: «Aleluia» al principio y al final de cada estrofa; cantado, también en medio y doble al final. En negrita (todos).
  if(sal.aleluyas){
    const al=t=>`<p class="v todos"><b>${t}</b></p>`, R_=t=>`<p class="v todos"><span class="k">℟.</span> <b>${t}</b></p>`, c=CANTA();
    if(canta && sal.aleluyas.every(e=>e.length===2)){
      // Cantado, cada estrofa son dos versos del modo: «Aleluia» (flexa), primer renglón (mediante), «℟. Aleluia» (terminación);
      // segundo renglón (mediante), «℟. Aleluia, aleluia» (terminación). En negrita, solo los acentos del modo.
      const vs=sal.aleluyas.flatMap(e=>[`Aleluia. † ${e[0]} * Aleluia.`, `${e[1]} * Aleluia, aleluia.`]);
      const lin=(v,i)=>{ const ls=SAL.renglonesVerso(SAL.pautarVerso(v,cod,'es',i===0));
        return ls.map((l,k)=>`<p class="v">${k===ls.length-1?'<span class="k">℟.</span> ':''}${sinSigue(l)}</p>`).join(''); };
      if(modo==='primer'||modo==='todos') h+=partituraHTML(`name:salmo;\n%%\n${SAL.gabcSalmo(modo==='todos'?vs:vs.slice(0,1),cod,'es',{marcas:true})}`, null, false, true);
      const desde=(modo==='primer'||modo==='todos')?(modo==='todos'?vs.length:1):0;
      h+=`<div class="versos al19">${sal.aleluyas.map((e,k)=>{ const par=[2*k,2*k+1].filter(i=>i>=desde); return par.length?`<div class="est">${par.map(i=>lin(vs[i],i)).join('')}</div>`:''; }).join('')}</div>`;
    } else {
      h+=`<div class="versos al19">${sal.aleluyas.map(e=>`<div class="est">${al('Aleluia.')}${e.map((l,i)=>`<p class="v">${esc(l)}</p>`+(c && i<e.length-1?R_('Aleluia.'):'')).join('')}${R_(c?'Aleluia, aleluia.':'Aleluia.')}</div>`).join('')}</div>`;
    }
    if(sal.gloria) h+=`<div class="versos">${versosHTML(glP,canta?'pautado':'texto',cod,L,1,null)}</div>`;
    return h;
  }
  // antífona con †: lo que repite la antífona, en gris y sin cantar; la entonación, en el primer verso entero que sigue
  const aS=sal.es && keyP==='es' && antDe(sal.ant), om=aS ? omitirAnt(vP, txt(aS.t).p) : null;
  // la entonación: en el primer verso; sin entonación si la base lo dice (Ef 1, «Bendito sea Dios», CRU).
  // Si la antífona repite el comienzo del primer verso (hasta la flexa o el metro), lo que queda va solo en la partitura,
  // sin entonación (directo a la cuerda), y el verso siguiente tampoco la lleva (CRU, 24/11/2026)
  const ent=om ? (om.ent ? -1 : 0) : (sal.sinEnt ? -1 : 0), np=1;
  const cruzIni=!!(om && om.ent);   // la antífona dijo parte del verso: lo que sigue empieza con la †
  if(om) h+=`<div class="versos omit" title="Lo dice la antífona">${om.gris.map(v=>`<p class="v">${lineasVerso(v,'texto').map((l,k)=>`<span class="${claseRenglon(l,k)}">${sinSigue(l)}</span>`).join('')}</p>`).join('')}</div>`;
  // partitura
  let todos=(om?om.versos:vP).concat(sal.gloria?glP:[]);
  const inter = S.lengua==='bi' && sal.inter ? sal.inter : null;
  const interTodos = inter ? inter.concat(sal.gloria?(r.gloriaInter||[]):[]) : null;
  // estribillo («R. …», cántico de 1 Tm 3, 16): no va en la partitura; si está antes del primer verso, va antes de ella
  const i0=Math.max(0, todos.findIndex(v=>!ESTRIBILLO.test(v)));
  if(canta && modo==='primer' && i0>0){ h+=`<div class="versos">${versosHTML(todos.slice(0,i0),'pautado',cod,L,1,null)}</div>`; todos=todos.slice(i0); }
  if(canta && (modo==='primer'||modo==='todos')){ // el primer verso (o todos) en partitura, con la entonación
    const lista=modo==='todos'?todos.filter(v=>!ESTRIBILLO.test(v)):todos.slice(0,np);
    let g=SAL.gabcSalmo(lista,cod,L,{marcas:true, entonarEn:ent});   // acento en negrita y preparatorias en cursiva, como en el pautado
    if(cruzIni) g=g.replace(/^(\([^)]*\)\s*)/,'$1†() ');   // la † al comienzo de lo que sigue de la antífona
    h+=partituraHTML(`name:salmo;\n%%\n${g}`, null, false, true);
    // traducción de los versos que van en partitura, debajo de ella
    if(interTodos) h+=`<div class="versos inter gl-part">${lista.map((v,i)=>`<p class="v">${glosaVerso(v,interTodos[i]).map((x,k)=>x?`<span class="gl ${k?'h2':'h1'}">${esc(x)}</span>`:'').join('')}</p>`).join('')}</div>`;
    if(modo==='todos') return h;
  }
  const inicio=(canta&&modo==='primer')?np:0;
  const modoTxt=(canta&&modo!=='texto')?'pautado':'texto'; // sin canto: con * y †, sin pautas
  const resto=todos.slice(inicio);
  h+=`<div class="versos${inter?' inter':''}">${versosHTML(resto,modoTxt,cod,L,inicio,interTodos?interTodos.slice(inicio):null,ent,cruzIni)}</div>`;
  return h;
}

/* ---------- Secciones ---------- */
// Interlineal: el latín corre como texto común (espacios regulares, corta en cualquier palabra);
// la traducción de cada grupo cuelga debajo de su primera palabra y es la que se acomoda (ajustarGlosas).
const BI=()=>S.lengua==='bi';
function interHTML(pares){
  return pares.map(([a,b])=>{
    const m=/^([✠*†])\s+(.*)$/.exec(a); let sg='';
    if(m){ sg=m[1]; a=m[2]; b=String(b||'').replace(/^[✠*†]\s*/,''); }
    const ws=String(a).trim().split(/\s+/);
    const pal=ws.map((w,i)=>`<span class="w">${marcas(w)}${i===0&&b?`<span class="tr">${marcas(b)}</span>`:''}</span>`);
    if(pal.length>1) pal.splice(0,2,`<span class="nw">${pal[0]} ${pal[1]}</span>`);   // las dos primeras palabras del par («ad dandam») no se separan
    if(sg) pal[0]=`<span class="nw">${sg==='✠'?marcas(sg):`<span class="sg">${sg}</span>`} ${pal[0]}</span>`;   // el signo no queda solo al final del renglón
    return pal.join(' ');
  }).join(' ');
}
// Traducción interlineal: cada traducción arranca bajo su palabra latina; si se encima con la de al lado, se reparten
// las del renglón en el espacio libre de ambos lados (lo menos lejos posible de su palabra: el anclaje cede) y nunca se
// superponen. Si ni así entran en el ancho, el renglón se quiebra antes de la última palabra. El latín no se toca.
function colocarGlosas(m, izq, der, gap){
  // m: [{base,w}] en orden. Posiciones l con l[i] ≥ l[i-1]+w[i-1]+gap, izq ≤ l[0], l[n-1]+w[n-1] ≤ der, lo más cerca de base.
  const off=[]; let o=0; m.forEach((x,i)=>{ off.push(o); o+=x.w+gap; });
  const n=m.length, hi=der-off[n-1]-m[n-1].w; if(hi<izq-1) return false;
  const bl=[];   // regresión isótona (bloques que se juntan): y = l - off, no decreciente
  m.forEach((x,i)=>{ bl.push({s:x.base-off[i], c:1}); while(bl.length>1 && bl[bl.length-2].s/bl[bl.length-2].c > bl[bl.length-1].s/bl[bl.length-1].c){ const z=bl.pop(); bl[bl.length-1].s+=z.s; bl[bl.length-1].c+=z.c; } });
  let i=0; bl.forEach(z=>{ const y=Math.min(hi, Math.max(izq, z.s/z.c)); for(let k=0;k<z.c;k++,i++) m[i].l=y+off[i]; });
  return true;
}
function ajustarGlosas(raiz){
  raiz=raiz||document;
  raiz.querySelectorAll('br.ajuste').forEach(b=>b.remove());
  const todas=[...raiz.querySelectorAll('.il .tr')]; todas.forEach(t=>{ t.style.left=''; });
  if(!todas.length) return true;
  const cajaDe=t=>{ let c=t.parentElement.parentElement; while(c.parentElement&&/^inline/.test(getComputedStyle(c).display)) c=c.parentElement; return c; };   // la caja de bloque
  const cajas=new Map(); todas.forEach(t=>{ const c=cajaDe(t); if(!cajas.has(c)) cajas.set(c,[]); cajas.get(c).push(t); });
  let listo=true;
  for(const [caja,trs] of cajas){
    for(let vuelta=0; vuelta<60; vuelta++){
      trs.forEach(t=>{ t.style.left=''; });
      const cs=getComputedStyle(caja), cr=caja.getBoundingClientRect();
      if(!cr.width){ listo=false; break; }   // sin dibujar todavía: se rehace después
      const grupos=[]; let g=null;
      trs.forEach(t=>{ const top=t.parentElement.getBoundingClientRect().top; if(!g||Math.abs(top-g.top)>2){ g={top,it:[]}; grupos.push(g); } g.it.push(t); });
      let quebrar=null;
      grupos.forEach((g,gi)=>{
        if(quebrar) return;
        // el primer renglón empieza donde dice la sangría francesa (text-indent negativo); los que bajan, en el padding
        const izq=cr.left+parseFloat(cs.paddingLeft)+(gi===0?Math.min(0,parseFloat(cs.textIndent)||0):0), der=cr.right-parseFloat(cs.paddingRight);
        const gap=.45*parseFloat(getComputedStyle(g.it[0]).fontSize);
        const m=g.it.map(t=>{ const r=t.getBoundingClientRect(); return {t,base:r.left,w:r.width,l:r.left}; });
        if(!colocarGlosas(m, izq, der, gap)){
          // se quiebra una sola vez, antes de la primera palabra que ya no entra (no de a una desde el final:
          // los saltos se acumularían y dejarían palabras solas en renglones con lugar)
          let j=m.length-1; while(j>1 && !colocarGlosas(m.slice(0,j).map(o=>({base:o.base,w:o.w})), izq, der, gap)) j--;
          if(gi===grupos.length-1 && j===m.length-1 && j>1) j--;   // la última palabra no baja sola: baja con la anterior
          if(m.length>1){
            const w=m[j].t.parentElement, nw=w.parentElement.classList.contains('nw')?w.parentElement:null;
            if(!(nw && nw.contains(m[0].t))){ quebrar=nw||w; return; }
          }
          colocarGlosas(m, izq, Infinity, gap);   // no hay dónde quebrar (traducción más larga que el renglón): se deja correr sin encimarse
        }
        m.forEach(o=>{ if(Math.abs(o.l-o.base)>.5) o.t.style.left=(o.l-o.base)+'px'; });
      });
      if(!quebrar) break;
      const br=document.createElement('br'); br.className='ajuste'; quebrar.parentNode.insertBefore(br,quebrar);
    }
  }
  return listo;
}
// Se rehace cuando cambia lo que mide: la letra (al cargar), el ancho, el tamaño, o al volver a la app.
let _glosaPend=0;
function reajustarGlosas(){ cancelAnimationFrame(_glosaPend); _glosaPend=requestAnimationFrame(()=>{ if(S.vista==='hora' && $('#main') && !ajustarGlosas($('#main'))) setTimeout(reajustarGlosas,300); }); }
if(document.fonts&&document.fonts.addEventListener) document.fonts.addEventListener('loadingdone', reajustarGlosas);
window.addEventListener('pageshow', reajustarGlosas);
document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) reajustarGlosas(); });
if(window.ResizeObserver){ let _anchoMain=0; new ResizeObserver(es=>{ const w=Math.round(es[0].contentRect.width); if(w!==_anchoMain){ _anchoMain=w; reajustarGlosas(); } }).observe(document.documentElement); }
/* Cantado o recitado: un solo botón al comienzo decide todas las piezas gregorianas.
   Recitado: el texto latino de la pieza, con su traducción literal debajo (si está activa). */
const CANTA=()=>S.cantado!==false;
function lineaRec(l, extra){
  const uno=ps=> S.trad ? interHTML(ps) : marcas(ps.map(x=>x[0]).join(' '));
  // desde: antífona entonada (Salva nos): hasta ahí uno, con el asterisco; desde ahí todos, en negrita
  const ent = l.desde>0 && !l.versos ? (()=>{ const a=l.pares.slice(0,l.desde), b=l.pares.slice(l.desde);
    return S.trad ? `${uno(a)} <span class="todos">${interHTML([['* '+b[0][0], b[0][1]], ...b.slice(1)])}</span>`
      : `${uno(a)}&nbsp;<span class="k">*</span> <span class="todos">${uno(b)}</span>`; })() : null;
  const cuerpo = ent || (l.versos ? l.versos.map(v=>`<span class="ln">${uno(v)}</span>`).join('') : uno(l.pares));   // renglones con sentido (base)
  return `<span class="segs${l.todos?' todos':''}">${extra||''}${cuerpo}</span>`;
}
function recitadoHTML(rec, tipo){
  const il=S.trad?' il':'';
  if(tipo==='ant') return `<div class="ant rec${il}">${rec.map(l=>`<p><span class="n">Ant.</span> ${lineaRec(l)}</p>`).join('')}</div>`;
  if(tipo==='estrofas') return `<div class="himno rec${il}${rec.length>1?'':' sin-num'}">${rec.map((l,i)=>`<p class="est">${rec.length>1?`<span class="num">${i+1}.</span>`:''}${
      (l.versos||[l.pares]).map(v=>`<span class="ln">${lineaRec({...l,pares:v,versos:null})}</span>`).join('')}</p>`).join('')}</div>`;
  if(tipo==='prosa') return rec.map(l=>`<p class="rec${il}">${lineaRec(l)}</p>`).join('');
  return `<div class="vr rec${il}">${rec.map(l=>`<p${l.rol!=='R'?' class="pv"':''}>${l.rol?`<span class="k">${l.rol==='R'?'℟':'℣'}.</span> `:''}${lineaRec(l)}</p>`).join('')}</div>`;
}
// Citas bíblicas al modo «capítulo: versículos» (Dn 3: 26-27), más preciso que la coma
function cita(t){ return String(t||'').replace(/(^|[;—–]\s*|\p{L}\.?\s+)(\d+), (?=\d)/gu,'$1$2: '); }
function vrHTML(sec){
  if((!CANTA() || !sec.gabc) && sec.rec) return recitadoHTML(sec.rec);   // sin partitura: siempre recitado
  if(S.canto && S.antGreg && sec.gabc) return partituraHTML(sec.gabc, sec.glosa);
  if(BI() && sec.ilv) return `<div class="vr il"><p><span class="k">℣.</span> <span class="segs">${interHTML(sec.ilv)}</span></p><p><span class="k">℟.</span> <span class="segs">${interHTML(sec.ilr)}</span></p></div>`;
  const v=txt(sec.v), r=txt(sec.r);
  const ln=(k,o)=>`<p><span class="k">${k}.</span> ${marcas(o.p)}${o.s?`<span class="gl">${marcas(o.s)}</span>`:''}</p>`;
  return `<div class="vr">${ln('℣',v)}${ln('℟',r)}</div>`;
}
function prosaHTML(o, amen, extra, il){
  if(BI() && il) return `<p class="il">${extra||''}${interHTML(il)}</p>`;
  const t=txt(o); let h='';
  if(t.falta==='la') h+=`<p class="aviso">Este texto todavía no tiene versión latina en el prototipo. Se muestra en español.</p>`;
  h+=`<p>${extra||''}${marcas(t.p)}${amen?` <span class="amen"><span class="k">℟.</span> <b>${esc(txt(amen).p)}</b></span>`:''}</p>`;
  if(t.s) h+=`<p class="gl">${marcas(t.s)}${amen?' '+esc(txt(amen).s||''):''}</p>`;
  return h;
}
function antHTML(sec){
  const a=sec.rep?antDe(sec.rep):sec; if(!a) return '';
  if(!CANTA() && a.rec) return recitadoHTML(a.rec,'ant');
  // soloCanto: antífona propia en gregoriano (propios.yaml) que va si se canta; recitado, el texto español. Repetida: la de toda la asamblea
  if(S.canto && S.antGreg && a.gabc && (CANTA() || !a.soloCanto)) return `<div class="ant-greg">${partituraHTML(sec.rep && a.gabcRep ? a.gabcRep : a.gabc, a.glosa)}</div>`;
  if(BI() && a.il) return `<div class="ant il"><p><span class="n">${esc(a.n||'Ant.')}</span> ${interHTML(a.il)}</p></div>`;
  const t=txt(a.t), cruz=!sec.rep && cruzVale(a), tp=t.p.replace(CRUZ_ANT,'');   // la † solo la primera vez, si vale
  // Antífona de un salmo o cántico, la primera vez: hasta el asterisco la entona uno (texto normal), desde ahí siguen todos
  // (negrita). Al repetirla al final, toda en negrita y sin asterisco (25/11/2026; el corte, CP._.asteriscoAnt)
  const sin=tp.replace(/ \* /,' '), ka=a.es && sec.ast ? CP._.asteriscoAnt(sin) : -1;
  const cuerpo= ka>=0 ? `${marcas(sin.slice(0,ka))}&nbsp;<span class="sg">*</span> <b>${marcas(sin.slice(ka+1))}</b>`
    : `${a.es?'<b>':''}${marcas(sin)}${a.es?'</b>':''}`;
  return `<div class="ant"><p><span class="n">${esc(a.n||'Ant.')}</span>${cuerpo}${cruz?'&nbsp;<span class="sg">†</span>':''}</p>${t.s?`<span class="gl">${esc(t.s.replace(/ \* /,' '))}</span>`:''}</div>`;
}
// Título corto para los botones: hasta ~24 letras, sin cortar en un artículo o preposición; «(solemne)» se conserva
function corto(n){
  const m=/^(.*?)(\s*\([^)]*\))?$/.exec(n), base=m[1], par=m[2]||'';
  if(base.length<=26) return n;
  let out=''; for(const w of base.split(' ')){ if((out+' '+w).trim().length>24) break; out=(out+' '+w).trim(); }
  out=out.replace(/(\s+(?:de|del|la|las|el|los|y|que|es|ya|en|a|mi|tu|su|con|por|para|nuestras?|nuestros?))+$/i,'').replace(/[,;:]$/,'');
  return out+par;
}
function botonesHTML(act, k, ops, o, efimera, label){
  return `<div class="opciones desliza" role="group" aria-label="${label}">${ops.map(x=>`<button data-act="${act}" data-k="${k}" data-v="${x.id}"${efimera?' data-e="1"':''} aria-pressed="${x===o}" title="${esc(x.n)}">${esc(corto(x.n))}</button>`).join('')}</div>`;
}
// En las filas deslizables, la opción elegida queda a la vista
function deslizarElegidos(raiz){
  (raiz||document).querySelectorAll('.opciones.desliza').forEach(f=>{
    const b=f.querySelector('[aria-pressed="true"]'); if(!b) return;
    const fr=f.getBoundingClientRect(), br=b.getBoundingClientRect();
    if(br.left<fr.left||br.right>fr.right) f.scrollLeft+= br.left-fr.left-(fr.width-br.width)/2;
    f.classList.toggle('mas', f.scrollWidth>f.clientWidth+1);
  });
}
function elegida(sec, clave, def){ const id=S[clave][sec.opciones[0].id]; return sec.opciones.find(o=>o.id===id)||def; }
function himnoHTML(sec){
  const ops=sec.opciones;
  const def= sec.def ? (ops.find(o=>o.id===sec.def)||ops[0]) : sec.es ? ops[0] : (ops.find(o=>o.lang===(S.lengua==='es'?VES():'la')) || ops[0]);
  // efímera (domingos y solemnidades): la elección vale solo mientras se mira ese día
  // El latín (recitado, «lat…») y el gregoriano («greg») se recuerdan para todos los días que los tienen, también en los
  // que la elección es efímera; si el día no tiene el segundo latino elegido, el primero.
  const mem=S.himno[ops[0].id], recordada=/^(lat|greg)/.test(mem||'') && (ops.find(x=>x.id===mem) || (/^lat/.test(mem) && ops.find(x=>x.id==='lat')));
  const o= sec.efimera ? (ops.find(x=>x.id===(S._marDia||{})['h:'+ops[0].id])||recordada||def) : (recordada||elegida(sec,'himno',def));
  let h='';
  if(ops.length>1 && !sec.sinBotones) h+=botonesHTML('himno', ops[0].id, ops, o, sec.efimera, 'Himno');
  // Himno latino recitado: cada verso con su traducción literal debajo (si la traducción está activa)
  if(o.lat){
    const gl=t=>S.trad?`<span class="gl">${esc(t)}</span>`:'', num=o.est.length>1 && o.num!==false;
    return h+`<div class="himno lat${num?'':' sin-num'}">`+o.est.map((e,ie)=>`<p class="est">${num?`<span class="num">${ie+1}.</span>`:''}${e.map((l,il)=>`<span class="ln">${esc(l)}</span>${gl(o.lit[ie][il])}`).join('')}</p>`).join('')
      +(o.amen?`<p class="est amen-fin"><b>${esc(o.amen)}</b>${gl('Amén.')}</p>`:'')+'</div>'+(o.rub?`<p class="rub">${esc(o.rub)}</p>`:'');
  }
  // rubGreg: rúbrica del himno gregoriano (Ave maris stella: «Aquí se arrodilla.»); cantado, arriba de la primera nota
  if(!CANTA() && o.rec) return h+(o.rubGreg?`<p class="rub">${esc(o.rubGreg)}</p>`:'')+recitadoHTML(o.rec,'estrofas');
  if(S.canto && o.gabc) return h+partituraHTML(o.rubGreg ? o.gabc.replace(/(%%[\s\S]*?\)\s*)(\S)/, (m,a,b)=>a+'<alt>¶'+o.rubGreg+'</alt>'+b) : o.gabc, S.trad?o.glosa:null);
  // Traducción anclada: cada par se ubica en la línea donde aparece su primera palabra latina, en orden
  const glosaLineas=(est,pares)=>{
    const pos=[]; est.forEach((e,ie)=>e.forEach((l,il)=>l.split(/\s+/).forEach(w=>{ const n=normPal(w); if(n) pos.push({n,ie,il}); })));
    const out=est.map(e=>e.map(()=>[])); let p=0;
    (pares||[]).forEach(([la,es])=>{ const ws=la.split(/\s+/).map(normPal).filter(Boolean); if(!ws.length) return;
      let q=-1; for(let k=p;k<pos.length;k++){ if(pos[k].n===ws[0] && (ws.length<2 || (pos[k+1]&&pos[k+1].n===ws[1]))){ q=k; break; } }
      if(q<0) return; out[pos[q].ie][pos[q].il].push(es); p=q+ws.length; });
    return out.map(e=>e.map(x=>x.join(' ')));
  };
  const bi=S.lengua==='bi' && o.lang==='la';
  const usarTrad=S.lengua==='es' && o.lang==='la' && o.trad;
  let est=usarTrad?o.trad.es:o.est, amen=usarTrad?(o.trad.amen||'Amén.'):(o.amen||'');
  // El Amén final va fuera de la última estrofa y en negrita (lo dicen todos). Si viene pegado al último verso, se separa.
  if(!amen && est.length){ const u=est[est.length-1], l=u[u.length-1]||'', m=/^(.*?)\s*((?:am[eé]n[,.]?\s*)+)$/i.exec(l);
    if(m){ amen='Amén.'; const resto=m[1].trim(); est=est.slice(0,-1).concat([resto?u.slice(0,-1).concat([resto]):u.slice(0,-1)]).filter(e=>e.length); } }
  const numerar=est.length>1; const GL=(bi&&!usarTrad)?glosaLineas(est,o.glosa):null;
  // himno en español: capitular en la primera estrofa (no en la continuación del Te Deum)
  const capi=o.lang==='es' && !GL && o.id!=='tedeum2' && est.length && /^\p{L}/u.test(est[0][0]||'') && (est[0][0]||'').length>1;
  h+=`<div class="himno${numerar?'':' sin-num'}">`+est.map((e,ie)=>{
    const c=capi && ie===0;
    return `<p class="est${c?' capi-on':''}">${numerar&&!c?`<span class="num">${ie+1}.</span>`:''}${c?capiHTML([...e[0]][0]):''}${e.map((l,il)=>`<span class="ln${c&&il<2?' c':''}">${sinalefas(esc(c&&!il?l.slice([...l][0].length):l))}</span>${GL?`<span class="gl">${esc(GL[ie][il])}</span>`:''}`).join('')}</p>`; }).join('')+(amen?`<p class="est amen-fin"><b>${esc(amen)}</b></p>`:'')+'</div>';
  return h;
}
// Invitatorio de los domingos del Tiempo Ordinario: gregoriano si se canta (salvo que se elija en español)
const INV=()=>(CANTA() && S.invit!=='es') ? 'greg' : 'es';
// Oraciones antes y después del oficio (base/ordinario/oraciones-oficio.yaml): latín y, debajo de cada renglón, la traducción de ADF
function oracionOficioHTML(k){
  const O=window.BASE.oraciones[k];
  const ln=(ps,pre)=>`<p class="orof">${ps.map(([a,b],k)=>`<span class="ln">${k?'':(pre||'')}${esc(a)}${S.trad?`<span class="gl">${esc(b)}</span>`:''}</span>`).join('')}</p>`;
  let h=`<p class="rub">${esc(O.rubrica)}</p>`+ln(O.texto);
  if(O.pausa) h+=`<p class="rub">${esc(O.pausa)}</p>`+ln(O.final);
  if(O.respuesta) h+=ln(O.respuesta,'<span class="k">℟.</span> ')+ln(O.versiculo,'<span class="k">℣.</span> ')+ln(O.respuesta_versiculo,'<span class="k">℟.</span> ')+ln(O.despues);
  return h;
}
// Lecturas del Oficio: referencia u obra («Del libro…», «De las Catequesis…»), título y texto en párrafos
function lecturaLargaHTML(sec){
  const ps=String(sec.t).split(/\n+/).filter(Boolean);
  return `<div class="lec-larga">${sec.ref?`<p class="lec-obra">${esc(sec.ref)}</p>`:''}${sec.autor?`<p class="lec-obra">${esc(sec.autor).replace(/\n/g,'<br>')}</p>`:''}`
    +(sec.titulo?`<p class="lec-tit">${esc(CP._.oracionCase(sec.titulo))}</p>`:'')+ps.map(p=>`<p>${marcas(p)}</p>`).join('')+`</div>`;
}
function examenHTML(sec){
  const f=sec.formulas.find(x=>x.id===S.examenF)||sec.formulas[0];
  const br=t=>esc(t).replace(/\n/g,'<br>');
  const vr=(k,t)=>`<p${k==='V'?' class="pv"':''}><span class="k">${k==='V'?'℣':'℟'}.</span> ${k==='R'?`<b>${br(t)}</b>`:br(t)}</p>`;
  let h=`<div class="opciones desliza" role="group" aria-label="Fórmula">${sec.formulas.map(x=>`<button data-act="examenF" data-v="${x.id}" aria-pressed="${x===f}">${esc(x.titulo)}</button>`).join('')}</div>`;
  h+=`<p>${br(sec.invitacion)}</p>`;
  if(f.latin){ // Confíteor latino, con traducción literal debajo; lo dicen todos
    // un renglón por grupo de la base (cortes de ADF), en un solo párrafo
    h+=`<p class="todos confiteor${S.trad?' il':''}">${f.todos.map(g=>`<span class="ln">${S.trad?interHTML(g):esc(g.map(x=>x[0]).join(' '))}</span>`).join('')}</p>`;
    h+=`<div class="vr${S.trad?' il':''}">`+f.absolucion.map(([k,p])=>S.trad
      ? `<p><span class="k">${k==='V'?'℣':'℟'}.</span> <span class="segs${k==='R'?' todos':''}">${interHTML(p)}</span></p>`
      : vr(k,p.map(x=>x[0]).join(' '))).join('')+'</div>';
    return h;
  }
  if(f.todos) h+=f.todos.map(p=>`<p class="todos">${br(p)}</p>`).join('');
  if(f.versos) h+=`<div class="vr">${f.versos.map(([k,t])=>vr(k,t)).join('')}</div>`;
  return h+`<div class="vr">${sec.absolucion.map(([k,t])=>vr(k,t)).join('')}</div>`;
}
function respHTML(sec){
  // Cantado: en gregoriano (si hay melodía para el tiempo); recitado: en español
  if(CANTA() && sec.gabc) return partituraHTML(sec.gabc, S.trad?sec.glosa:null)+(sec.rub?`<p class="rub">${esc(sec.rub)}</p>`:'');
  const es=VES(); const la=sec.l.la, sp=sec.l[es]||sec.l.es79||sec.l.es;
  const P= S.lengua==='es'? sp : la; const Sx= S.lengua==='bi'? (sec.lit? sec.lit.map((x,i)=>[la[i][0],x]) : sp) : null;
  return `<div class="vr">${P.map((x,i)=>x[0]==='rub' ? `<p class="rub">${esc(x[1])}</p>` : `<p${x[0]==='V'?' class="pv"':''}><span class="k">${x[0]==='V'?'℣':'℟'}.</span> ${x[0]==='R'?'<b>'+marcas(x[1])+'</b>':marcas(x[1])}${Sx&&Sx[i]?`<span class="gl">${marcas(Sx[i][1])}</span>`:''}</p>`).join('')}</div>`;
}
function marianaHTML(sec){
  const ops=sec.opciones;
  // efímera: la elección vale solo mientras se mira ese día (al volver a abrir, la primera opción)
  const o= sec.efimera ? (ops.find(x=>x.id===(S._marDia||{})[ops[0].id])||ops[0]) : elegida(sec,'mariana',ops[0]);
  let h= ops.length>1 ? botonesHTML('mariana', ops[0].id, ops, o, sec.efimera, 'Antífona') : '';
  if(!CANTA() && o.rec) return h+recitadoHTML(o.rec,'prosa');
  if(S.canto && S.antGreg && o.gabc) return h+partituraHTML(o.gabc, S.trad?o.glosa:null);
  const es=VES(); const la=o.l.la, sp=o.l[es]||o.l.es79||o.l.es;
  let P=S.lengua==='es'?sp:(la||sp); const Sx=S.lengua==='bi'&&la?sp:null;
  if(!la && S.lengua!=='es') h+=`<p class="aviso">Esta antífona está cargada solo en español en el prototipo.</p>`;
  const LIT=BI()&&la&&o.lit?o.lit:null;
  h+= LIT ? `<div class="himno sin-num"><p class="est">${P.map((l,i)=>`<span class="ln">${esc(l)}</span><span class="gl">${esc(LIT[i]||'')}</span>`).join('')}</p></div>`
     : `<div class="himno sin-num"><p class="est">${P.map(l=>`<span class="ln">${esc(l)}</span>`).join('')}</p>${Sx?`<p class="est gl">${Sx.map(l=>`<span class="ln">${esc(l)}</span>`).join('')}</p>`:''}</div>`;
  return h;
}

// Comunes de los santos: debajo de cada elemento que tiene varias opciones (las «O bien» y variantes del libro), un botón
// discreto para elegir cualquiera. Sección de la hora → elementos (claves de la base) que muestra.
const CAMPOS_SEC={invitatorio:['inv_ant'], himno:['himno'], salmodia:['salmodia','ant','versiculo'], lectura:['lectura','versiculo'], responsorio:['responsorio'],
  cantico:['ant_benedictus','ant_magnificat'], preces:['preces'], padrenuestro:['padrenuestro_intro'], oracion:['oracion'],
  lectura1:['lectura1'], 'lectura1-r':['resp1'], lectura2:['lectura2'], 'lectura2-r':['resp2']};
const NOMBRE_CAMPO={inv_ant:'Antífona del invitatorio', himno:'Himno', salmodia:'Salmodia', ant:'Antífona', versiculo:'Versículo', lectura:'Lectura breve', responsorio:'Responsorio breve',
  ant_benedictus:'Antífona del Benedictus', ant_magnificat:'Antífona del Magníficat', preces:'Preces', padrenuestro_intro:'Monición del Padre nuestro',
  oracion:'Oración', lectura1:'Primera lectura', resp1:'Responsorio', lectura2:'Segunda lectura', resp2:'Responsorio'};
function otrasHTML(r, id, vistas){
  if(!r.alts || !id || /^c-/.test(id)) return '';
  let hk=r.hora+(r.primeras?'1':'');
  if(/^l-/.test(id)){ hk='laudes'; id=id.slice(2); }   // Oficio unido a Laudes
  const ks=(CAMPOS_SEC[id]||[]).filter(c=>c!=='salmodia').map(c=>hk+'|'+c).filter(k=>r.alts[k] && !vistas.has(k));   // (la salmodia: debajo de la antífona del salmo que cambia)
  ks.forEach(k=>vistas.add(k));
  return ks.map(k=>`<div class="otras"><button class="discreto" data-act="otras" data-v="${esc(k)}">Otras opciones${ks.length>1?' · '+esc(NOMBRE_CAMPO[k.split('|')[1]].toLowerCase()):''}</button></div>`).join('');
}
// Salmodia con opciones (último salmo de Laudes de difuntos…): «Otras opciones» debajo de la antífona del salmo que cambia
function otrasSalmoHTML(r, secId, sec){
  if(!r.alts || !secId || !/^(l-)?salmodia$/.test(secId) || sec.rep) return '';
  const m=/^a(\d+)$/.exec(sec.id||''); if(!m) return '';
  const hk=/^l-/.test(secId) ? 'laudes' : r.hora+(r.primeras?'1':''), k=hk+'|salmodia', a=r.alts[k];
  return a && (a.dif||[]).includes(+m[1]-1) ? `<div class="otras"><button class="discreto" data-act="otras" data-v="${esc(k)}">Otras opciones</button></div>` : '';
}
function hojaOtras(k){
  const a=(R().alts||{})[k]; if(!a) return;
  hoja(NOMBRE_CAMPO[k.split('|')[1]]||'Opciones', `<ul class="opc-lista">${a.ops.map((o,i)=>`<li><button data-act="eligeop" data-k="${esc(k)}" data-v="${i}" aria-pressed="${i===a.i}"><span class="n">${esc(o.n)}</span>${o.ver?`<span class="v">${esc(o.ver)}</span>`:''}</button></li>`).join('')}</ul>`);
}
// Hoja del botón del inicio: el común, el caso y el grado (desplegables) y las horas
function hojaComunes(){
  const L=CP._.COMUNES_SANTOS, sel=S.comunSel=Object.assign({g:0, c:0, grado:'Memoria'}, S.comunSel||{}), G=L[sel.g]||L[0];
  const opt=(v,n,on)=>`<option value="${esc(String(v))}"${on?' selected':''}>${esc(n)}</option>`;
  const nom=n=>{ const x=n.replace(/^Común de (la )?/,''); return x[0].toUpperCase()+x.slice(1); };
  const sol=sel.grado==='Solemnidad';
  const hs=[['oficio','Oficio de lectura'],['laudes','Laudes'],['tercia','Tercia'],['sexta','Sexta'],['nona','Nona'], ...(sol?[['visperas1','I Vísperas']]:[]), ['visperas', sol?'II Vísperas':'Vísperas']];
  hoja('Comunes de los santos', `<p class="rub">Para celebrar a un santo que no está en el calendario, con los textos del común. Donde dice «N.», se dice el nombre.</p>
    <div class="elige-comun">
      <label><span>Común</span><select data-chg="comun" data-k="g">${L.map((x,i)=>opt(i, nom(x.n), i===sel.g)).join('')}</select></label>
      ${G.casos.length>1?`<label><span>Para</span><select data-chg="comun" data-k="c">${G.casos.map((x,i)=>opt(i, x.n, i===sel.c)).join('')}</select></label>`:''}
      <label><span>Grado</span><select data-chg="comun" data-k="grado">${['Memoria','Fiesta','Solemnidad'].map(x=>opt(x, x, x===sel.grado)).join('')}</select></label>
    </div>
    <ul class="horas">${hs.map(([id,n])=>`<li class="disp"><button data-act="abrircom" data-v="${id}"><span class="n">${n}</span><span class="h"></span><span class="chev">›</span></button></li>`).join('')}</ul>`);
}
document.addEventListener('change',e=>{
  const sel=e.target.closest('select[data-chg="comun"]'); if(!sel) return;
  const c=S.comunSel=Object.assign({g:0, c:0, grado:'Memoria'}, S.comunSel||{}), k=sel.dataset.k;
  if(k==='g'){ c.g=+sel.value; c.c=0; } else if(k==='c') c.c=+sel.value; else c.grado=sel.value;
  guardar(); hojaComunes();
  const f=$(`#capa select[data-k="${k}"]`); if(f) f.focus({preventScroll:true});
});

function horaHTML(){
  _id=0; GAB.clear();
  const r=R(); let h='', secAct=null; const vistas=new Set();
  const sinNombre=S.hora==='completas' || r.primeras;   // Completas y I Vísperas: sin el nombre de la celebración
  h+=`<p class="dia-h">${sinNombre?(r.primeras?'I Vísperas · ':''):esc(r.dia.titulo)+' · '}${esc(r.dia.tiempo)}${r.dia.visperas&&!sinNombre?`<br>${esc(r.dia.visperas)}`:''}${(f=>f.length>1?`<br>Calendario: ${esc((f.find(x=>x.on)||f[0]).txt)}`:'')(fichasCal())}</p>`;
  // dos comunes: primero los botones para elegirlo y, debajo, la nota de dónde se toma cada cosa
  if(r.dos && r.dos.ops.length>1) h+=`<div class="opciones desliza dos-comunes" role="group" aria-label="Común">${r.dos.ops.map(x=>`<button data-act="comundia" data-k="${r.dos.f}" data-v="${x.id}" aria-pressed="${x.id===r.dos.actual}" title="${esc(x.n)}">${esc(x.n)}</button>`).join('')}</div>`;   // en una línea que se desliza, como los himnos (26/11/2026)
  if(r.dia.nota) h+=`<p class="aviso">${esc(r.dia.nota)}</p>`;
  // I Vísperas del domingo: en ADF, antes de empezar, la oración preparatoria (introduce el oficio de toda la semana)
  if(r.hora==='visperas' && r.primeras && CP.deIso(S.fecha).getDay()===6)
    h+=`<div class="prep"><button class="discreto" data-act="prep" aria-expanded="${!!S._prep}">Oración preparatoria</button></div>`+(S._prep?`<div class="orof-b">${oracionOficioHTML('preparatoria')}</div>`:'');
  // Cantado | Recitado: interruptor deslizante, distinto de los botones de opciones (26/11/2026)
  h+=`<div class="modo-canto${CANTA()?'':' rec'}" role="group" aria-label="Cantado o recitado">${[[true,'Cantado'],[false,'Recitado']].map(([v,n])=>`<button data-act="cantado" data-v="${v?'si':'no'}" aria-pressed="${CANTA()===v}">${n}</button>`).join('')}</div>`;
  // Invitatorio: en Laudes (los domingos) y en el Oficio de lectura, si es la primera oración del día
  const invL = r.hora==='laudes' && CP.deIso(S.fecha).getDay()===0 && !r.difuntos, invO = r.hora==='oficio';
  if(invL || invO){ const on = invL ? S.invLaudes!==false : !!S.invOficio;
    h+=`<div class="opciones unir"><button data-act="invtog" aria-pressed="${on}">Invitatorio</button></div><p class="rub nota-inv">Si ${invL?'Laudes es':'el Oficio de lectura es'} la primera oración, se hace el Invitatorio.</p>`; }
  let pleg=null;
  r.secciones.forEach(sec=>{
    if(sec.k==='sec'){
      secAct=sec.id;
      // Vísperas: antes de la conclusión (o del examen, si ya están unidas), el botón para seguir con Completas
      if(r.hora==='visperas' && (sec.id==='bendicion'||sec.id==='c-examen')) h+=`<div class="opciones unir"><button data-act="unir" aria-pressed="${!!r.unidas}">Conclusión de Completas</button></div>`;
      if(r.hora==='oficio' && (sec.id==='oracion'||sec.id==='l-laudes')) h+=`<div class="opciones unir"><button data-act="unirl" aria-pressed="${!!r.unidas}">Seguir con Laudes</button></div>`;
      pleg=sec.plegable?sec.id:null;
      h+=`<h2 class="sec" id="s-${sec.id}">${esc(sec.t)}${sec.plegable?` <button data-act="examen" aria-expanded="${S.examen}">${S.examen?'Ocultar':'Mostrar'}</button>`:''}${sec.ref?`<span class="sref">${esc(cita(sec.ref))}</span>`:''}</h2>`;
      h+=otrasHTML(r, sec.id, vistas);   // «Otras opciones», justo debajo del título del elemento
      return;
    }
    if(sec.inv && sec.inv!==INV()) return;   // invitatorio: gregoriano o en español, según se eligió
    aplicarModo(sec.k, sec);
    if(sec.pleg && !S.examen) return;
    if(sec.k==='rub' && pleg && !S.examen) return;
    switch(sec.k){
      case 'rub': h+=`<p class="rub">${esc(sec.t)}</p>`; break;
      case 'aviso': h+=`<p class="aviso">${esc(sec.t)}</p>`; break;
      case 'lectura_larga': h+=lecturaLargaHTML(sec); break;
      case 'salop': h+=`<div class="opciones" role="group" aria-label="Salmodia">${[['dia','Salmodia del día'],['comp','Complementaria']].map(([v,n])=>`<button data-act="salop" data-v="${v}" aria-pressed="${(v==='comp')===sec.comp}">${n}</button>`).join('')}</div>`; break;
      case 'vr': h+=vrHTML(sec); break;
      case 'vr1': { if(BI()&&sec.il){ h+=`<div class="vr il"><p><span class="k">${/^R\./.test(sec.t.la)?'℟':'℣'}.</span> <span class="segs">${interHTML(sec.il)}</span></p></div>`; break; } const t=txt(sec.t); h+=`<div class="vr"><p><span class="k">℣.</span> ${marcas(t.p.replace(/^R\. /,''))}${t.s?`<span class="gl">${marcas(t.s.replace(/^R\. /,''))}</span>`:''}</p></div>`; break; }
      case 'doxo': h+=prosaHTML(sec.t,null,'',sec.il); break;
      case 'prosa': h+=(sec.n?`<p class="rub">${esc(sec.n)}</p>`:'')+prosaHTML(sec.t, sec.amen, '', sec.il); break;
      case 'oremos': h+= BI()&&sec.il ? `<p class="il"><b>${interHTML(sec.il)}</b></p>` : `<p><b>${esc(txt(sec.t).p)}</b></p>`; break;
      case 'lectura': { const t=txt(sec.t); const ref=sec.ref?txt(sec.ref).p:''; if(BI()&&sec.il){ h+=`<p class="il"><span class="lec-ref">${esc(cita(ref))}</span>${interHTML(sec.il)}</p>`+(sec.aviso?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; } h+=`<p class="lec-b">${ref?`<span class="lec-ref">${esc(cita(ref))}</span>`:''}${lecturaMarcada(t.p)}</p>`+(t.s?`<p class="gl">${esc(t.s)}</p>`:'')+(sec.aviso&&S.lengua!=='es'?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; }
      case 'himno': h+=himnoHTML(sec); break;
      case 'invop': if(CANTA()) h+=`<div class="opciones" role="group" aria-label="Invitatorio">${[['greg','Gregoriano'],['es','En español']].map(([v,n])=>`<button data-act="invit" data-v="${v}" aria-pressed="${INV()===v}">${n}</button>`).join('')}</div>`; break;
      case 'invgreg': h+=`<div class="ant-greg">${partituraHTML(sec.ant.gabc, S.trad?sec.ant.glosa:null)}</div><p class="rub">La antífona se repite después de cada estrofa.</p>`
        +sec.estrofas.map(e=>partituraHTML(e.gabc, S.trad?e.glosa:null, false)).join(''); break;
      case 'ant': h+=antHTML(sec)+otrasSalmoHTML(r, secAct, sec); break;
      case 'salmoinv': {   // Salmo 94 del invitatorio: en estrofas, con capitular, «Venid, postrémonos por tierra» en versalitas
        // y la antífona repetida después de cada estrofa (después de la última, la repetición que sigue al salmo)
        const antRep=sec.ant ? `<div class="ant"><p><span class="n">Ant.</span><b>${marcas(sec.ant.replace(/ \* /,' '))}</b></p></div>` : '';
        const ln=(l,c)=>`<span class="ln${c?' c':''}">${esc(l).replace(/^(Venid, postrémonos por tierra)/i,'<span class="vers">$1</span>')}</span>`;
        h+=`<div class="salmo-h"><span class="t">${esc(cita(sec.titulo))}</span>${sec.lema?`<span class="lema">${esc(sec.lema)}</span>`:''}</div>`
          +`<div class="himno sin-num">${sec.estrofas.map((e,ie)=>{
              const cap=ie===0 && /^\p{L}/u.test(e[0]||'') ? [...e[0]][0] : '';
              return `<p class="est${cap?' capi-on':''}">${cap?capiHTML(cap):''}${e.map((l,il)=>ln(cap&&!il?l.slice(cap.length):l, cap&&il<2)).join('')}</p>`
                +(ie<sec.estrofas.length-1?antRep:''); }).join('')}</div>`; break; }
      case 'salmo': h+=salmoHTML(sec)+(sec.rubrica?`<p class="rub">${esc(sec.rubrica)}</p>`:''); break;
      case 'resp': h+=respHTML(sec); break;
      case 'mariana': h+=marianaHTML(sec); break;
      case 'deo':   // ℟. Deo grátias, con su traducción (interlineal, palabra por palabra; si no, debajo)
        h+= S.trad&&sec.il ? `<div class="vr il"><p><span class="k">℟.</span> <b class="segs">${interHTML(sec.il)}</b></p></div>`
          : `<div class="vr"><p><span class="k">℟.</span> <b>${esc(sec.t)}</b>${sec.tr?`<span class="gl">${esc(sec.tr)}</span>`:''}</p></div>`; break;
      case 'examen': h+=examenHTML(sec); break;
      case 'cantico':
        // Laudes y Vísperas, cantado: el Benedictus o el Magníficat en el modo del día, con la entonación en cada verso
        if(sec.modo && !sec.gabc && CANTA()){
          const cod=tonoDe(sec), lista=S.salmos==='todos'?sec.versos:S.salmos==='pautado'?[]:sec.versos.slice(0,1);
          h+=`<div class="salmo-h"><div class="cab"><span class="t">${esc(sec.titulo)}</span>${selectorModo(sec)}</div></div>`;
          // con la capitular del gregoriano (en la partitura) o, si no hay partitura, en el primer verso
          if(lista.length) h+=partituraHTML(versalitasGabc(`name:cantico;\n%%\n${SAL.gabcSalmo(lista,cod,'la',{entonarTodos:true, marcas:true})}`), S.trad&&sec.inter?lista.flatMap((v,i)=>sec.inter[i]||[]):null, true, true);
          const resto=sec.versos.slice(lista.length);
          if(resto.length) h+=`<div class="versos${S.trad?' inter':''}">${versosMarcados(resto.map(v=>SAL.marcadoVerso(SAL.pautarVerso(v,cod,'la',true))),S.trad&&sec.inter?sec.inter.slice(lista.length):null, !lista.length)}</div>`;
          break;
        }
        h+=`<div class="salmo-h"><span class="t">${esc(sec.titulo)}</span></div>`
          +(!sec.gabc ? `<div class="versos${S.trad?' inter':''}">${versosMarcados(sec.versos,S.trad?sec.inter:null,true)}</div>`   // sin partitura (Benedictus): todo pautado
            : CANTA() ? partituraHTML(sec.gabc.replace(/initial-style:\s*0;?\n?/,''), S.trad?sec.glosa:null, true, true)   // Nunc dimíttis: acentos del modo en 700, como el pautado; capitular del gregoriano
              +`<div class="versos${S.trad?' inter':''}">${versosMarcados(sec.versos,S.trad?sec.inter:null)}</div>`
            : `<div class="versos${S.trad?' inter':''}">${versosMarcados([sec.verso1,...sec.versos],S.trad?[sec.inter1,...sec.inter]:null,true)}</div>`); break;
      case 'preces': {
        // Cada prece: flexa (†) en el corte del medio y asterisco (*) al final; la respuesta la dicen todos
        if(sec.renglones){ h+=sec.renglones.map(t=>`<p>${esc(t)}</p>`).join(''); break; }
        h+=`<p>${esc(sec.intro)}</p><div class="vr"><p class="todos"><span class="k">℟.</span> ${esc(sec.respuesta)}</p></div>`
          // después de cada prece, la respuesta (la dicen todos)
          +`<div class="preces">${sec.preces.map(pr=>CP._.marcarPrece(pr)).map(([a,b])=>(b ? `<p><span class="pa">${esc(a)}&nbsp;<span class="sg">†</span></span><span class="pb">${esc(b)}&nbsp;<span class="sg">*</span></span></p>`
              : `<p><span class="pa">${esc(a)}&nbsp;<span class="sg">*</span></span></p>`)   // prece sin corte
              +`<div class="vr"><p class="todos"><span class="k">℟.</span> ${esc(sec.respuesta)}</p></div>`).join('')}</div>`
; break; }
      case 'pater':
        { // hasta el asterisco lo entona el que preside; desde ahí, todos (negrita). Un renglón por frase.
          const uno=ps=> S.trad ? interHTML(ps) : marcas(ps.map(x=>x[0]).join(' '));
          const ls=(sec.lineas||[sec.pares]).map(l=>{
            const k=l.findIndex(x=>/^\*/.test(x[0]));
            if(k<0) return `<span class="ln todos">${uno(l)}</span>`;
            const a=l.slice(0,k), b=l.slice(k).map((x,i)=>i?x:[x[0].replace(/^\*\s*/,''),x[1]]);
            return `<span class="ln">${uno(a)} <span class="sg">*</span> <span class="todos">${uno(b)}</span></span>`; });
          h+=(sec.intro?`<p>${esc(sec.intro)}</p>`:'')+`<p class="rec renglones${S.trad?' il':''}">${ls.join('')}</p>`; break; }
      case 'conclusion': {
        const o=sec.opciones.find(x=>x.id===S.concl)||sec.opciones[0];
        h+=`<div class="opciones desliza" role="group" aria-label="Conclusión">${sec.opciones.map(x=>`<button data-act="concl" data-v="${x.id}" aria-pressed="${x===o}">${esc(x.n)}</button>`).join('')}</div>`+vrHTML(o)+(o.despues?recitadoHTML(o.despues):''); break; }
      case 'greg': h+=`<div class="salmo-h"><span class="t">${esc(sec.titulo)}</span>${sec.ref?`<span class="ref">${esc(sec.ref)}</span>`:''}</div>`+partituraHTML(sec.gabc, sec.glosa, false); break;
    }
  });
  aplicarModo();
  h+=`<p class="fin">✠</p>`;
  return h;
}

/* ---------- Portada ---------- */
// La hora que toca según el reloj: hasta 1:30 antes y después de su hora (Laudes 6, Tercia 9, Sexta 12, Nona 15, Vísperas 18, Completas 21).
// El Oficio de lectura se marca junto con Laudes.
function horasAhora(){ const d=new Date(), m=d.getHours()*60+d.getMinutes();
  const h=[['laudes',6],['tercia',9],['sexta',12],['nona',15],['visperas',18],['completas',21]].find(([id,x])=>id==='visperas' ? (m>=16*60+30 && m<=20*60+30) : Math.abs(m-x*60)<=90);
  return !h ? [] : h[0]==='laudes' ? ['oficio','laudes'] : [h[0]]; }
const HORAS=[['oficio','Oficio de lectura'],['laudes','Laudes'],['tercia','Tercia'],['sexta','Sexta'],['nona','Nona'],['visperas','Vísperas'],['completas','Completas']];
const COLORES={Verde:'#3f9142','Rosa o morado':'#d58aa0',Morado:'#6b3f8a',Rojo:'#b0302a',Blanco:'#fff',Rosa:'#d58aa0',Negro:'#333','Azul o blanco':'#4f7fbf'};
// «Rojo o color del Tiempo litúrgico» → rojo: el primero que nombra
const colorLit=c=>COLORES[c]||COLORES[(c||'').split(' ')[0]]||'#3f9142';
/* Calendario del mes (al tocar la fecha en el inicio): cada día con un globito de su color litúrgico */
let _calMes=null;
function hojaCalendario(){
  const M=CP._.MESES, hoy=fechaHoy();
  const [y,m]=(_calMes||S.fecha).slice(0,7).split('-').map(Number);
  const pad=n=>String(n).padStart(2,'0'), mes=`${y}-${pad(m)}`;
  const primero=new Date(y,m-1,1), dias=new Date(y,m,0).getDate(), hueco=primero.getDay();   // la semana empieza el domingo
  let celdas='<span></span>'.repeat(hueco);
  for(let d=1; d<=dias; d++){
    const f=`${mes}-${pad(d)}`, ok=CP.enRango(f), r=ok?CP.diaCal(f, SEL()):null;
    const cls=[f===S.fecha?'sel':'', f===hoy?'hoy':'', r&&/^(Domingo|Solemnidad)$/.test(r.g)?'mayor':''].join(' ').trim();
    celdas+= ok ? `<button class="${cls}" data-act="irdia" data-v="${f}" aria-label="${esc(d+' de '+M[m-1]+': '+r.n+' ('+r.c.toLowerCase()+')')}" ${f===S.fecha?'aria-current="date"':''}><span class="num">${d}</span><span class="globo" style="--col:${colorLit(r.c)}"></span></button>`
               : `<button disabled aria-label="${d}"><span class="num">${d}</span></button>`;
  }
  const antes=CP.enRango(CP.masDias(`${mes}-01`,-1)), despues=CP.enRango(`${m===12?y+1:y}-${pad(m===12?1:m+1)}-01`);
  const cuerpo=`<div class="calmes">
    <div class="calmes-h"><button class="iconbtn" data-act="calmes" data-v="-1" aria-label="Mes anterior" ${antes?'':'disabled'}>‹</button><h3>${M[m-1][0].toUpperCase()+M[m-1].slice(1)} ${y}</h3><button class="iconbtn" data-act="calmes" data-v="1" aria-label="Mes siguiente" ${despues?'':'disabled'}>›</button></div>
    <div class="calmes-s" aria-hidden="true"><span>D</span><span>L</span><span>M</span><span>M</span><span>J</span><span>V</span><span>S</span></div>
    <div class="calmes-g">${celdas}</div>
    ${mes!==hoy.slice(0,7)?'<button class="discreto" data-act="calhoy">Volver a este mes</button>':''}
  </div>`;
  // ya abierto: se cambia solo el mes, sin volver a abrir la hoja
  const b=$('#capa .sheet-b'); if(b && b.querySelector('.calmes')) b.innerHTML=cuerpo; else hoja('Calendario', cuerpo);
}
// Vísperas del día: I Vísperas (sábados y vísperas de solemnidad), II Vísperas (domingos y solemnidades) o Vísperas
function nombreVisperas(){
  const hoy=CP.diaCal(S.fecha, SEL()), fm=CP.masDias(S.fecha,1), man=CP.enRango(fm)?CP.diaCal(fm, SEL()):null;
  if(!hoy) return 'Vísperas';
  if(man && man.pv && !(hoy.sol && !man.sol) && hoy.t!=='Triduo') return 'I Vísperas';
  return (hoy.dom || hoy.sol) ? 'II Vísperas' : 'Vísperas';
}
// Imagen de la tarjeta: la que toca al día y a la franja horaria (completas.js); si no hay, el coro
function iluHTML(){
  const i=window.ILU_DIR && window.ILUS ? CP.ilustracion(S.fecha, SEL(), CP.franjaHoraria(new Date())) : null;
  const url=i==null ? window.ILU : window.ILU_DIR+window.ILUS.img[i]+'.webp', alt=i==null ? 'Coro cantando' : window.ILUS.d[i];
  return `<span class="ilu" role="img" aria-label="${esc(alt)}" style="--ilu:url(${url})"></span>`;
}
// Título del día: el nombre arriba y, en un renglón aparte, los títulos del santo («obispo y doctor de la Iglesia»,
// «papa y mártir», «reina»), en letra más fina. Se parte por las comas: lo que empieza en minúscula es título, salvo
// lo que empieza con «y» («y Metodio», «y compañeros»), que sigue al nombre. Si los títulos estaban intercalados
// («Andrés Dung-Lac, presbítero, y compañeros, mártires»), se juntan: «Andrés Dung-Lac y compañeros» / «presbítero y mártires».
function partesTitulo(t){
  const nombre=[], titulos=[];
  t.split(', ').forEach((x,i)=>{
    if(i>0 && /^[a-záéíóúñ]/.test(x) && !/^(y|e) /.test(x)) titulos.push(x);
    else if(i>0 && /^(y|e) /.test(x)) nombre.push(nombre.pop()+' '+x);
    else nombre.push(x);
  });
  // dos títulos: «presbítero y mártires»; tres o más: los de cada uno con «y», y el común al final: «papa y obispo, mártires»
  const tit=titulos.length>2 ? titulos.slice(0,-1).join(' y ')+', '+titulos[titulos.length-1] : titulos.join(' y ');
  return {nombre:nombre.join(', '), titulos:tit};
}
function tituloHTML(t){
  const p=partesTitulo(t);
  return esc(p.nombre)+(p.titulos?`<span class="tit">${esc(p.titulos)}</span>`:'');
}
// El título del día se achica hasta entrar en la tarjeta, que no cambia de proporción. Solo si ni al mínimo entra, la tarjeta crece.
function ajustarTitulo(){
  const dia=$('.dia'), txt=dia&&dia.querySelector('.txt'), h=txt&&txt.querySelector('h2'); if(!h) return;
  dia.classList.remove('crece'); h.style.fontSize='';
  const raiz=parseFloat(getComputedStyle(document.documentElement).fontSize)||16, min=raiz*1.05;
  let t=parseFloat(getComputedStyle(h).fontSize);
  while(txt.scrollHeight>txt.clientHeight+1 && t>min){ t=Math.max(min,t-1); h.style.fontSize=t+'px'; h.style.lineHeight=t<raiz*1.2?'1.2':''; }
  if(txt.scrollHeight>txt.clientHeight+1) dia.classList.add('crece');
}
let vigiaTitulo=null;
function vigilarTitulo(){
  ajustarTitulo();
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(ajustarTitulo);
  if(!vigiaTitulo && window.ResizeObserver){ let ancho=0; vigiaTitulo=new ResizeObserver(e=>{ const w=Math.round(e[0].contentRect.width); if(w!==ancho){ ancho=w; ajustarTitulo(); } }); }
  const d=$('.dia'); if(vigiaTitulo&&d){ vigiaTitulo.disconnect(); vigiaTitulo.observe(d); }
}
function portadaHTML(){
  const r=R(); const esHoy=S.fecha===fechaHoy(), ahora=esHoy?horasAhora():[];
  // Calendarios: solo cuando el día tiene variantes o nota. La ficha gris es lo que se está celebrando; las encendidas, las otras opciones.
  const fc=fichasCal(), nota=(CP.diaCal(S.fecha, SEL())||{}).nota;
  const cals=(fc.length>1||nota) ? `<div class="cals" role="group" aria-label="Calendarios de este día">${fc.map(c=>`<button class="cal" data-act="cal" data-v="${c.i}" data-s="${c.sg}" aria-pressed="${c.on}" aria-label="${esc(c.txt+': '+c.o.f.n+' ('+c.o.f.g+')')}">${esc(c.txt)}</button>`).join('')}${nota?'<button class="cal nota" data-act="nota" aria-label="Ver la nota de este día">!</button>':''}</div>` : '';
  return `<div class="portada"><h1 class="vh">Liturgia de las Horas</h1>
    <div class="navdia">
      <button class="iconbtn" data-act="dia" data-v="-1" aria-label="Día anterior">${'‹'}</button>
      <button class="fecha" data-act="calendario" aria-label="Abrir el calendario">${esHoy?'Hoy, ':''}${esc(esHoy?r.fechaTxt.toLowerCase():r.fechaTxt)}</button>
      <button class="iconbtn" data-act="dia" data-v="1" aria-label="Día siguiente">${'›'}</button>
      ${esHoy?'':'<button class="hoybtn" data-act="hoy">Hoy</button>'}
      <button class="iconbtn mas" data-act="opciones" aria-label="Opciones"><svg class="ico" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg></button>
    </div>
    <div class="dia">
      <div class="txt">
        <div><div class="hoy">${esc(r.dia.grado)}</div><h2>${tituloHTML(r.dia.titulo)}</h2></div>
        <div class="meta"><span class="color" style="--col:${colorLit(r.dia.color)}">${esc(r.dia.tiempo)}</span>${r.dia.salterio?`<span>${esc(r.dia.salterio)}</span>`:''}${(CP.diaCal(S.fecha, SEL())||{}).bio?'<button class="bio" data-act="bio">Síntesis biográfica</button>':''}</div>
      </div>
      <div class="arco">${iluHTML()}</div>
    </div>
    ${cals}
    <button class="discreto arriba" data-act="oraciones">Oraciones antes y después del oficio</button>
    <ul class="horas">${HORAS.map(([id,n])=>{
      const ok=true, ya=ahora.includes(id);
      if(id==='visperas') n=nombreVisperas();
      return `<li class="${[ok?'disp':'',ya?'ahora':''].join(' ').trim()}"><button ${ok?`data-act="abrir" data-v="${id}"`:'disabled'} ${ya?'aria-current="time"':''}><span class="n">${esc(n)}</span><span class="h">${ok?esc(id==='completas'&&r.dia.visperas?'tras las I Vísperas':''):'<span class="pronto">en preparación</span>'}</span><span class="chev">${ok?'›':''}</span></button></li>`; }).join('')}</ul>
    <button class="discreto" data-act="difuntos">Oficio de difuntos</button>
    <button class="discreto" data-act="comunes">Comunes de los santos</button>
    <p class="nota-proto">Versión de prueba: todas las horas, con el calendario ADF. Los textos y el santoral están en revisión; puede haber errores.</p>
  </div>`;
}

/* ---------- Render ---------- */
function render(){
  aplicarTema();
  const enHora=S.vista==='hora';
  $('#atras').hidden=!enHora; $('#top').hidden=!enHora;   // en el inicio no hay barra: los tres puntos van junto a la fecha
  $('#brand').innerHTML= enHora? `${esc(R().nombre||'Completas')}<small>${esc(D.fechaTxt)}</small>` : '<span class="vh">Liturgia de las Horas</span>';
  $('#main').innerHTML= enHora? `<article class="hora" lang="es">${horaHTML()}</article>` : portadaHTML();
  if(!enHora) vigilarTitulo();
  if(enHora){ if(!ajustarGlosas($('#main'))) reajustarGlosas(); deslizarElegidos($('#main')); if(document.fonts&&document.fonts.ready) document.fonts.ready.then(reajustarGlosas); pintar($('#main')); }
}

/* ---------- Hojas ---------- */
function hoja(titulo, cuerpo){
  const habia=!!$('#capa'); quitarCapa(); if(!habia) empujar('capa');
  const c=document.createElement('div'); c.className='capa'; c.id='capa';
  c.innerHTML=`<div class="sheet" role="dialog" aria-modal="true" aria-label="${esc(titulo)}"><div class="sheet-h"><h2>${esc(titulo)}</h2><button class="iconbtn" data-act="cerrar" aria-label="Cerrar"><svg class="ico" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div><div class="sheet-b">${cuerpo}</div></div>`;
  c.addEventListener('click',e=>{ if(e.target===c) cerrar(); });
  document.body.appendChild(c);
  const f=c.querySelector('.sheet-b button'); if(f) f.focus({preventScroll:true});
}
function quitarCapa(){ const c=$('#capa'); if(c) c.remove(); }
function cerrar(){ if(!$('#capa')) return; if(history.state&&history.state.capa){ history.back(); } else quitarCapa(); }
function empujar(tipo){ try{ history.pushState({capa:tipo==='capa', hora:S.vista==='hora'||tipo==='hora'},'',location.href); }catch(e){} }
window.addEventListener('popstate',()=>{
  if($('#capa')){ quitarCapa(); return; }
  if(S.vista==='hora'){ S.vista='hoy'; guardar(); render(); window.scrollTo(0,0); }
});
const seg=(act,vals,cur)=>`<div class="seg" role="group">${vals.map(([v,n])=>`<button data-act="${act}" data-v="${v}" aria-pressed="${cur===v}">${n}</button>`).join('')}</div>`;
const sw=(act,on,t,d)=>`<div class="fila"><span><span class="tt">${t}</span>${d?`<span class="dd">${d}</span>`:''}</span><button class="sw" role="switch" data-act="${act}" aria-checked="${on}" aria-label="${t}"></button></div>`;
function hojaOpciones(){
  hoja('Opciones',`
    <div class="grupo"><h3>Tamaño</h3><div class="tam"><button data-act="menos" aria-label="Achicar" ${S.zoom<=.8?'disabled':''}>A−</button><span>${Math.round(S.zoom*100)} %</span><button data-act="mas" aria-label="Agrandar" ${S.zoom>=2?'disabled':''}>A+</button></div></div>
    <div class="grupo"><h3>Aspecto</h3>${seg('theme',[['light','Claro'],['dark','Oscuro']],S.theme)}</div>
    <div class="grupo"><h3>Canto</h3>
      ${sw('trad',S.trad,'Traducción del latín','Interlineal en el texto y glosa bajo los neumas')}</div>
    ${_instalar?`<div class="grupo"><h3>App</h3><p class="hint">Cervus queda como una app más, con su ícono, y abre sin conexión.</p><button class="btn" data-act="instalar">Instalar Cervus</button></div>`:''}`);
}
let _toast, _toastFin, _undo=null;
// Aviso breve: aparece y se desvanece (clases «entra» y «sale» de app.css)
function toast(m, snap){
  clearTimeout(_toast); clearTimeout(_toastFin); let t=$('#toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; t.className='toast'; t.setAttribute('role','status'); t.setAttribute('aria-live','polite'); document.body.appendChild(t); }
  _undo=snap||null;
  t.innerHTML=`<span>${esc(m)}</span>${snap?'<button data-act="deshacer">Deshacer</button>':''}`;
  if(t.hidden){ t.classList.add('entra'); t.hidden=false; void t.offsetWidth; }
  t.classList.remove('entra','sale');
  _toast=setTimeout(()=>{ t.classList.add('sale'); _undo=null; _toastFin=setTimeout(()=>{ t.hidden=true; t.classList.remove('sale'); },500); },snap?4500:2200);
}

/* ---------- Acciones ---------- */
function refrescarHoja(f){ const y=$('#main')?window.scrollY:0; render(); window.scrollTo(0,y); if(f) f(); }
// Desplegable del modo (salmos y cántico evangélico de Laudes y Vísperas): vale para esta hora de este día
document.addEventListener('change',e=>{
  const sel=e.target.closest('select[data-chg="tono"]'); if(!sel) return;
  const k=sel.dataset.k, v=sel.value; S.tonos=S.tonos||{};
  if(v===sel.dataset.def) delete S.tonos[k]; else S.tonos[k]=v;
  // se guardan solo los de los últimos días
  const lim=CP.masDias(fechaHoy(),-7); for(const c of Object.keys(S.tonos)) if(c.slice(0,10)<lim) delete S.tonos[c];
  guardar(); refrescarHoja(); toast(SAL.etiquetaTono(v)+(v===sel.dataset.def?' (el del día)':''));
});
/* Deslizar el dedo: sobre la tarjeta del día, al día anterior o siguiente; en el calendario, al mes anterior o siguiente
   (como las flechas). Hacia la izquierda, el siguiente. Solo gestos claramente horizontales: el desplazamiento vertical sigue igual. */
function moverDia(n){
  const f=CP.masDias(S.fecha,n);
  if(!CP.enRango(f)){ toast('Fuera del calendario cargado'); return false; }
  S.fecha=f; cargarDia(); render(); return true;
}
function moverMes(n){
  const b=$(`#capa [data-act="calmes"][data-v="${n}"]`); if(b && b.disabled) return false;
  const [y,m]=_calMes.slice(0,7).split('-').map(Number), d=new Date(y,m-1+n,1);
  _calMes=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-01`; hojaCalendario(); return true;
}
function entrar(el, n){
  if(!el || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  el.classList.remove('entra-sig','entra-ant'); void el.offsetWidth; el.classList.add(n>0?'entra-sig':'entra-ant');
}
let _toque=null, _deslizo=0;
document.addEventListener('touchstart',e=>{
  _toque=null;
  if(e.touches.length!==1) return;
  const z=e.target.closest('.portada .dia, #capa .calmes'); if(!z) return;
  const t=e.touches[0]; _toque={x:t.clientX, y:t.clientY, t:Date.now(), mes:z.classList.contains('calmes')};
},{passive:true});
document.addEventListener('touchend',e=>{
  const q=_toque; _toque=null; if(!q) return;
  const t=e.changedTouches[0], dx=t.clientX-q.x, dy=t.clientY-q.y;
  if(Math.abs(dx)<50 || Math.abs(dx)<1.5*Math.abs(dy) || Date.now()-q.t>800) return;
  const n=dx<0?1:-1; _deslizo=Date.now();
  if(q.mes){ if(moverMes(n)) entrar($('#capa .calmes-g'), n); }
  else if(moverDia(n)) entrar($('.portada .dia'), n);
},{passive:true});
document.addEventListener('touchcancel',()=>{ _toque=null; },{passive:true});
// el toque con que termina un deslizamiento no abre lo que había debajo (un día del calendario, la síntesis biográfica)
document.addEventListener('click',e=>{ if(Date.now()-_deslizo<400){ e.preventDefault(); e.stopPropagation(); } },true);

document.addEventListener('click',e=>{
  const b=e.target.closest('[data-act]'); if(!b) return;
  const a=b.dataset.act, v=b.dataset.v;
  const abierta=$('#capa .sheet-h h2'); const enHoja=abierta?abierta.textContent:null;
  const reabrir=()=>{ if(enHoja==='Opciones') hojaOpciones(); };
  const snap=JSON.stringify(S);
  const cambio=(msg, conDeshacer=true)=>{ guardar(); refrescarHoja(reabrir); toast(msg, conDeshacer?snap:null); };
  const nV=k=>(R().versiones[k]||{}).n||k;
  const onOff=x=>x?'activado':'desactivado';
  switch(a){
    case 'cerrar': cerrar(); break;
    case 'deshacer': if(_undo){ S=JSON.parse(_undo); cargarDia(); aplicarModo(); _undo=null; guardar(); refrescarHoja(reabrir); toast('Cambio deshecho'); } break;
    case 'difuntos': hoja('Oficio de difuntos', `<p class="rub">Con todos los textos del Oficio de difuntos, en lugar de los del día.</p><ul class="horas">${[['oficio','Oficio de lectura'],['laudes','Laudes'],['tercia','Tercia'],['sexta','Sexta'],['nona','Nona'],['visperas','Vísperas']].map(([id,n])=>`<li class="disp"><button data-act="abrirdif" data-v="${id}"><span class="n">${n}</span><span class="h"></span><span class="chev">›</span></button></li>`).join('')}</ul>`); break;
    case 'invtog': if(S.hora==='laudes') S.invLaudes=(S.invLaudes===false); else S.invOficio=!S.invOficio;
      { const sigue=()=>{ cargarDia(); guardar(); render(); };
        if(S.hora==='oficio' && S.invOficio && !cargada('laudes')) cargarHora('laudes').then(sigue, ()=>toast('No se pudo cargar el invitatorio.')); else sigue(); } break;
    case 'comunes': hojaComunes(); break;
    case 'otras': hojaOtras(v); break;
    case 'eligeop': {
      if(CP._.modo.comun) S.comunElige={...(S.comunElige||{}), [b.dataset.k]:+v};
      else { const c=claveElige(); S._elige={...(S._elige||{}), [c]:{...((S._elige||{})[c]||{}), [b.dataset.k]:+v}}; }
      cerrar(); cargarDia(); refrescarHoja(); break; }
    case 'abrircom': case 'abrirdif': case 'abrir': {
      S.difuntos=a==='abrirdif'; S.comunOn=a==='abrircom'; S.comunPrim=v==='visperas1'; S.comunElige={};
      if(a!=='abrir') quitarCapa();
      const hv=v==='visperas1' ? 'visperas' : v;
      const abrir=()=>{ S._marDia={}; S.hora=hv||'completas'; cargarDia(); S.vista='hora'; empujar('hora'); guardar(); render(); window.scrollTo(0,0); };
      const faltan=[hv, ...(hv==='oficio'&&(S.unirLaudes||S.invOficio)?['laudes']:[])].filter(h=>MAYORES[h]&&!cargada(h));   // Oficio unido a Laudes (o con invitatorio): también Laudes
      if(faltan.length){ toast('Cargando…'); Promise.all(faltan.map(cargarHora)).then(abrir, ()=>toast('No se pudo cargar la hora. Revisá la conexión.')); } else abrir();
      break; }
    case 'atras': if(history.state&&history.state.hora){ history.back(); } else { S.vista='hoy'; guardar(); render(); window.scrollTo(0,0); } break;
    case 'opciones': hojaOpciones(); break;
    case 'calendario': _calMes=S.fecha; hojaCalendario(); break;
    case 'calmes': if(moverMes(+v)){ const f=$(`#capa [data-act="calmes"][data-v="${v}"]`); if(f && !f.disabled) f.focus({preventScroll:true}); } break;
    case 'calhoy': _calMes=fechaHoy(); hojaCalendario(); break;
    case 'irdia': if(CP.enRango(v)){ S.fecha=v; cargarDia(); cerrar(); render(); } break;
    case 'dia': moverDia(+v); break;
    case 'hoy': S.fecha=fechaHoy(); cargarDia(); render(); break;
    case 'cal': { const c=fichasCal().find(x=>String(x.i)===v && x.sg===(b.dataset.s||'')); if(!c||c.on) break;
      const d=SEL().dia;
      if(c.o.tipo==='r'){ S.cal=c.sg; delete d[S.fecha]; }                      // otro calendario: se recuerda
      else if(c.o.tipo==='l'){ d[S.fecha]=c.o.f.n; }                             // memoria libre: solo ese día
      else { if(fichasCal().some(x=>x.on&&x.o.tipo==='r')) S.cal=''; delete d[S.fecha]; }   // volver al calendario ADF
      cargarDia(); cambio(c.o.f.n+' ('+c.txt+')'); break; }
    case 'bio': { const f=CP.diaCal(S.fecha, SEL()); hoja(f.n, f.bio.split(/\n+/).map(p=>`<p class="nota-dia">${esc(p)}</p>`).join('')); break; }
    case 'nota': { const f=CP.diaCal(S.fecha, SEL()), fc=fichasCal();
      // notas del Calendario litúrgico ADF, una por renglón: «SIGLA<tab>texto»
      const ns=String(f.nota||'').split('\n').filter(Boolean).map(l=>{ const i=l.indexOf('\t'); return i<0?['',l]:[l.slice(0,i),l.slice(i+1)]; });
      const sg=[...new Set(fc.flatMap(c=>c.o.siglas).concat(ns.map(n=>n[0])).filter(x=>x&&CP.calendarios[x]))];
      hoja(f.n, ns.map(([x,t])=>`<p class="nota-dia">${x?`<span class="sig">${esc(x)}</span>`:''}${esc(t)}</p>`).join('')
        +`<dl class="siglas">${sg.map(x=>`<div><dt>${esc(x)}</dt><dd>${esc(CP.calendarios[x]||'')}</dd></div>`).join('')}</dl>`); break; }
    case 'trad': S.trad=!S.trad; guardar(); refrescarHoja(reabrir); break;   // el cambio se ve al instante: sin aviso
    case 'salmos': if(S.salmos===v) break; S.salmos=v; cambio('Salmos: '+{pautado:'sin partitura',primer:'primer verso en partitura',todos:'todo en partitura'}[v]); break;
    case 'examenF': S.examenF=v; cambio('Examen: '+b.textContent); break;
    case 'himno': if(b.dataset.e){ S._marDia['h:'+b.dataset.k]=v;
        // el latín y el gregoriano se recuerdan también desde un día con la elección efímera; otro himno lo olvida
        if(/^(lat|greg)/.test(v)) S.himno[b.dataset.k]=v; else if(/^(lat|greg)/.test(S.himno[b.dataset.k]||'')) delete S.himno[b.dataset.k];
        guardar(); refrescarHoja(); } else { S.himno[b.dataset.k]=v; cambio('Himno cambiado'); } break;
    case 'mariana': if(b.dataset.e){ S._marDia[b.dataset.k]=v; refrescarHoja(); } else { S.mariana[b.dataset.k]=v; cambio('Antífona cambiada'); } break;
    case 'concl': if(S.concl===v) break; S.concl=v; cambio('Conclusión: '+b.textContent.toLowerCase()); break;
    case 'invit': if(INV()===v) break; S.invit=v; cambio('Invitatorio: '+(v==='greg'?'gregoriano':'en español')); break;
    case 'prep': S._prep=!S._prep; refrescarHoja(); break;
    case 'oraciones': { const O=window.BASE.oraciones; hoja(O.titulo, `<div class="orof-b">${['preparatoria','conclusiva'].map(k=>`<h3>${esc(O[k].titulo)}</h3>${oracionOficioHTML(k)}`).join('')}</div>`); break; }
    case 'unirl': { const sigue=()=>{ S.unirLaudes=!S.unirLaudes; cargarDia(); cambio(S.unirLaudes?'Oficio con Laudes':'Oficio solo'); };
      if(!S.unirLaudes && !window.LAUDES){ toast('Cargando…'); cargarHora('laudes').then(sigue, ()=>toast('No se pudo cargar Laudes. Revisá la conexión.')); } else sigue(); break; }
    case 'comundia': { if(S.comunDia && S.comunDia.f===b.dataset.k && S.comunDia.id===v) break;
      if(!S.comunDia && v==='virgenes') break;
      S.comunDia={f:b.dataset.k, id:v}; if(S._elige) delete S._elige[claveElige()];   // las «Otras opciones» elegidas eran del otro común
      cargarDia(); cambio('Textos del '+b.textContent); break; }
    case 'salop': { const c=v==='comp'; if(!!S.compl===c) break; S.compl=c; cargarDia(); cambio(c?'Salmodia complementaria':'Salmodia del día'); break; }
    case 'unir': S.unirCompletas=!S.unirCompletas; cargarDia(); cambio(S.unirCompletas?'Vísperas con Completas':'Vísperas solas'); break;
    case 'cantado': { const c=v==='si'; if(CANTA()===c) break; S.cantado=c; { const n=R().nombre||'Completas'; cambio(n+(c?' cantadas':' recitadas')); } break; }
    case 'examen': S.examen=!S.examen; guardar(); refrescarHoja(); toast(S.examen?'Examen de conciencia visible':'Examen de conciencia oculto'); break;
    case 'menos': case 'mas': { const z=Math.min(2,Math.max(.8,Math.round((S.zoom+(a==='mas'?.1:-.1))*10)/10)); if(z===S.zoom) break; S.zoom=z; cambio('Tamaño: '+Math.round(z*100)+' %',false); break; }
    case 'instalar': if(_instalar){ const p=_instalar; _instalar=null; cerrar(); p.prompt(); } break;
    case 'theme': if(S.theme===v) break; S.theme=v; guardar(); aplicarTema(); reabrir(); break;   // sin aviso
  }
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape') cerrar(); });
// Barras que se esconden al bajar y vuelven al subir
let yAnt=0; window.addEventListener('scroll',()=>{ const y=window.scrollY; const bajar=y>yAnt && y>120; if(S.vista==='hora'){ $('#top').classList.toggle('oculta',bajar); } yAnt=y; },{passive:true});
// En la hora, tocar el texto muestra u oculta la barra. No cuenta si se está seleccionando texto
// ni si se toca algo que hace otra cosa (botones, enlaces, desplegables, hojas).
$('#main').addEventListener('click',e=>{
  if(S.vista!=='hora' || e.target.closest('a,button,select,input,label,summary,[data-act],[data-chg]')) return;
  const sel=window.getSelection&&window.getSelection(); if(sel && !sel.isCollapsed) return;
  $('#top').classList.toggle('oculta');
});
// Tocar dos o tres veces seguidas no selecciona palabras ni párrafos (arrastrar o mantener apretado sí selecciona).
$('#main').addEventListener('mousedown',e=>{ if(e.detail>1 && S.vista==='hora') e.preventDefault(); });
document.addEventListener('scroll',e=>{ const f=e.target; if(f.classList&&f.classList.contains('desliza')) f.classList.toggle('mas', f.scrollLeft+f.clientWidth<f.scrollWidth-2); },true);
let _rz; window.addEventListener('resize',()=>{ clearTimeout(_rz); _rz=setTimeout(()=>{ if(S.vista==='hora'){ ajustarGlosas($('#main')); pintar($('#main')); } },250); });

// App instalable: el service worker (sw.js, de armar.py) guarda la app para abrirla sin conexión.
// No en el Artifact (sin ILU_DIR) ni abierta como archivo.
if(window.ILU_DIR && 'serviceWorker' in navigator && (location.protocol==='https:'||location.hostname==='localhost'))
  window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js')
    .then(()=>navigator.serviceWorker.ready).then(()=>{
      // la imagen del día se pidió antes de que el service worker tomara el control: se guarda ahora
      const m=getComputedStyle(document.querySelector('.ilu')||document.body).getPropertyValue('--ilu').match(/url\(["']?([^"')]+)/);
      if(m) caches.open('cervus-ilu').then(c=>c.match(m[1]).then(g=>g||c.add(m[1])));
    }).catch(()=>{}));
// Chrome avisa cuando se puede instalar: entonces «Instalar Cervus» aparece en Opciones
let _instalar=null;
window.addEventListener('beforeinstallprompt',e=>{ _instalar=e; });
window.addEventListener('appinstalled',()=>{ _instalar=null; toast('Cervus instalada'); });

// Si se recarga con Laudes abierta, primero se cargan sus datos
if(S.vista==='hora' && MAYORES[S.hora] && !cargada(S.hora)){ S.vista='hoy'; Promise.all([S.hora, ...(S.hora==='oficio'&&S.unirLaudes?['laudes']:[])].map(cargarHora)).then(()=>{ S.vista='hora'; cargarDia(); render(); }, ()=>{}); }
render();
