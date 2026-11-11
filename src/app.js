/* ================== LH ADF — Completas ================== */
const SAL=window.Salmodia, CP=window.Completas;
let D=null; // Completas del día elegido (src/completas.js)
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------- Estado ---------- */
const DEF={vista:'hoy', rito:'novus', modo:'canto', salmos:'primer', trad:true,
  lec:1.2, esc:'n', theme:'light', tonos:{}, himno:{}, mariana:{}, examen:false, region:'ARG', cantado:true};
let S=DEF;
try{ const g=JSON.parse(localStorage.getItem('septies')||'null'); if(g){ S=Object.assign({},DEF,g); delete S.ves; if(!g.modo) S.modo=g.canto?'canto':(g.lengua==='es'?'es':'la'); } }catch(e){}
if(S.salmos==='texto') S.salmos='primer';
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
function guardar(){ try{ const {lengua,canto,antGreg,fecha,_marDia,...g}=S; localStorage.setItem('septies',JSON.stringify(g)); }catch(e){} }
let DH=null; // la hora abierta cuando no es Completas (Laudes o Vísperas)
const MAYORES={laudes:'Laudes', visperas:'Visperas'};
const R=()=> (S.vista==='hora' && MAYORES[S.hora] && DH) || D;
// Los datos de Laudes y de Vísperas van en archivos aparte: se cargan recién al abrir la hora
const _carga={};
function cargarHora(h){
  if(window[h.toUpperCase()]) return Promise.resolve();
  if(!_carga[h]) _carga[h]=new Promise((ok,mal)=>{ const sc=document.createElement('script'); sc.src=(window.HORAS_URL||{})[h]||h+'.js'; sc.onload=ok; sc.onerror=()=>{ _carga[h]=null; mal(); }; document.head.appendChild(sc); });
  return _carga[h];
}
const VES=()=>'es';
// Día litúrgico de hoy: antes de las 5 de la mañana, todavía son las Completas de ayer
function fechaHoy(){ const d=new Date(); if(d.getHours()<5) d.setDate(d.getDate()-1); return CP.iso(d); }
S.fecha=fechaHoy();
function cargarDia(){
  if(!CP.enRango(S.fecha)) S.fecha=fechaHoy();
  if(!CP.difiereRegion(S.fecha) && !['ARG','PGY'].includes(S.region)) S.region='ARG';
  D=CP.armar(S.fecha, S.region);
  DH = (MAYORES[S.hora] && window[S.hora.toUpperCase()]) ? window[MAYORES[S.hora]].armar(S.fecha, S.region) : null;
  S._marDia={}; // la antífona mariana elegida a mano vale solo para ese día
}
cargarDia();
// S.trad (glosa bajo la partitura) lo usan las funciones heredadas del Cantoral
function aplicarTema(){ const r=document.documentElement; r.dataset.theme=S.theme==='dark'?'dark':'light'; const mt=document.querySelector('meta[name=theme-color]'); if(mt) mt.content=S.theme==='dark'?'#1c1a17':'#ffffff'; r.style.setProperty('--lec',S.lec); if(S.esc==='n') delete r.dataset.esc; else r.dataset.esc=S.esc; }

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
function marcas(s){ // ℣ ℟ * † ✠ en rojo
  return esc(s).replace(/✠/g,'<span class="cruz">✠</span>').replace(/ \* /g,' <span class="k">*</span> ').replace(/ † /g,' <span class="k">†</span> ');
}

/* ---------- Partituras (Exsurge, igual que el Cantoral) ---------- */
let _id=0; const GAB=new Map();
function partituraHTML(gabc, glosa, drop=true){ const id='g'+(++_id); GAB.set(id,{gabc,glosa,drop}); return `<div class="partitura" data-g="${id}"><p class="cargando">Preparando la partitura…</p></div>`; }
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
  const zoom=S.lec/1.15;
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
function tonoDe(sal){ const a=antDe(sal.ant); return (a&&a.modo)||'8G'; } // el tono sigue siempre a la antífona
// Devuelve las líneas (hemistiquios) de un verso, ya marcadas
function lineasVerso(v, modo, cod, lang, intonar){
  v=v.replace(/✠\s*/g,'');
  if(modo==='texto'){
    const d=SAL.dividirVerso(v); const out=[];
    if(d.flex) out.push(`${esc(d.flex)}&nbsp;<span class="sg">†</span>`);
    if(d.ter!=null){ out.push(`${esc(d.med)}&nbsp;<span class="sg">*</span>`); out.push(esc(d.ter)); }
    else out.push(esc(d.med));
    return out;
  }
  return SAL.htmlVerso(SAL.pautarVerso(v,cod,lang,intonar)).split('<br>');
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
function versosHTML(versos, modo, cod, lang, desde, glosas){
  return versos.map((v,i)=>{
    const ls=lineasVerso(v,modo,cod,lang,(desde+i)===0);
    const gs=glosas?glosaVerso(v,glosas[i]):null;
    return `<p class="v">${ls.map((l,k)=>`<span class="${k?'h2':'h1'}">${l}</span>${gs&&gs[k]?`<span class="gl ${k?'h2':'h1'}">${esc(gs[k])}</span>`:''}`).join('')}</p>`;
  }).join('');
}
// Versos con marcas escritas a mano: **negrita** (acento) y _cursiva_ (preparación); * mediante, † flexa.
// glosas: por versículo, pares «latín → español» palabra por palabra, en el orden del texto (el * y la † no llevan par)
function versosMarcados(versos, glosas){
  const m=t=>esc(t).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/_(.+?)_/g,'<i>$1</i>');
  return versos.map((v,i)=>{
    const pares=glosas&&glosas[i]||null; let k=0, resto=0;
    const mitades=v.split(/ \* /);
    const hs=mitades.map((h,hi)=>h.trim().split(/\s+/).map(w=>{
        if(w==='†') return `<span class="sg">†</span>`;
        if(!pares) return m(w);
        let tr='';
        if(resto===0 && k<pares.length){ const p=pares[k++]; resto=String(p[0]).trim().split(/\s+/).length; tr=p[1]; }
        if(resto>0) resto--;
        return `<span class="w">${m(w)}${tr?`<span class="tr">${marcas(tr)}</span>`:''}</span>`;
      }));
    const hs2=hs.map((ws,hi)=>{ // el asterisco no baja solo de renglón: va pegado a la última palabra
      if(hi<mitades.length-1 && ws.length){ const u=ws.pop(); ws.push(`<span class="nw">${u}&nbsp;<span class="sg">*</span></span>`); }
      return ws.join(' '); });
    return `<p class="v${pares?' il':''}">${hs2.map((h,n)=>`<span class="${n?'h2':'h1'}">${h}</span>`).join('')}</p>`;
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
  const modo=S.canto? S.salmos : 'texto';
  let h=`<div class="salmo-h"><span class="t">${esc(cita(t.p))}</span>${sal.ref?`<span class="ref">${esc(sal.ref)}</span>`:''}${lema&&lema.p?`<span class="lema">${esc(lema.p)}</span>`:''}`;
  h+='</div>';
  // partitura
  let todos=vP.concat(sal.gloria?glP:[]);
  const inter = S.lengua==='bi' && sal.inter ? sal.inter : null;
  const interTodos = inter ? inter.concat(sal.gloria?(r.gloriaInter||[]):[]) : null;
  if(S.canto && !sal.es && (modo==='primer'||modo==='todos')){ // los salmos en español van sin partitura
    const lista=modo==='todos'?todos:todos.slice(0,1);
    let g=SAL.gabcSalmo(lista,cod,L,true);
    if(sal.es) g=g.replace(/<\/?[bi]>/g,''); // salmos en español: sin pautas también en la partitura
    h+=partituraHTML(`name:salmo;\n%%\n${g}`, null, false);
    // traducción de los versos que van en partitura, debajo de ella
    if(interTodos) h+=`<div class="versos inter gl-part">${lista.map((v,i)=>`<p class="v">${glosaVerso(v,interTodos[i]).map((x,k)=>x?`<span class="gl ${k?'h2':'h1'}">${esc(x)}</span>`:'').join('')}</p>`).join('')}</div>`;
    if(modo==='todos') return h;
  }
  const inicio=(S.canto&&!sal.es&&modo==='primer')?1:0;
  const modoTxt=(S.canto&&modo!=='texto'&&!sal.es)?'pautado':'texto'; // salmos en español: sin pautas, con * y †
  const resto=todos.slice(inicio);
  h+=`<div class="versos${inter?' inter':''}">${versosHTML(resto,modoTxt,cod,L,inicio,interTodos?interTodos.slice(inicio):null)}</div>`;
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
    if(sg) pal[0]=`<span class="nw">${marcas(sg)} ${pal[0]}</span>`;   // el signo no queda solo al final del renglón
    return pal.join(' ');
  }).join(' ');
}
// Ubica las traducciones: cada una empieza bajo su palabra; si la anterior es más larga, se corre a la derecha;
// si el renglón se pasa del margen, se recorren hacia la izquierda. Solo si aun así no entran, la última palabra
// latina con traducción pasa al renglón siguiente (el latín nunca se estira ni se abre).
function ajustarGlosas(raiz){
  raiz=raiz||document;
  raiz.querySelectorAll('br.ajuste').forEach(b=>b.remove());
  for(let vuelta=0; vuelta<40; vuelta++){
    const trs=[...raiz.querySelectorAll('.il .tr')];
    trs.forEach(t=>{ t.style.left=''; });
    const grupos=[]; let g=null;
    trs.forEach(t=>{
      let caja=t.parentElement.parentElement; while(caja.parentElement&&/^inline/.test(getComputedStyle(caja).display)) caja=caja.parentElement;   // la caja de bloque que lo contiene
      const top=t.parentElement.getBoundingClientRect().top;
      if(!g||g.caja!==caja||Math.abs(top-g.top)>2){ g={caja,top,it:[]}; grupos.push(g); }
      g.it.push(t);
    });
    let quebrar=null;
    for(const g of grupos){
      const cs=getComputedStyle(g.caja), cr=g.caja.getBoundingClientRect();
      const izq=cr.left+parseFloat(cs.paddingLeft), der=cr.right-parseFloat(cs.paddingRight);
      const gap=.45*parseFloat(getComputedStyle(g.it[0]).fontSize);
      const m=g.it.map(t=>{ const r=t.getBoundingClientRect(); return {t,base:r.left,w:r.width}; });
      let x=-Infinity; m.forEach(o=>{ o.l=Math.max(o.base,x); x=o.l+o.w+gap; });
      let lim=der; for(let k=m.length-1;k>=0;k--){ const o=m[k]; if(o.l+o.w>lim) o.l=lim-o.w; lim=o.l-gap; }
      if(m[0].l<izq-1){
        if(m.length>1){ quebrar=m[m.length-1].t.parentElement; break; }
        m[0].l=m[0].base;   // una sola traducción más larga que el renglón: se deja correr
      }
      m.forEach(o=>{ if(Math.abs(o.l-o.base)>.5) o.t.style.left=(o.l-o.base)+'px'; });
    }
    if(!quebrar) return;
    const w=quebrar.parentElement.classList.contains('nw')?quebrar.parentElement:quebrar;
    const br=document.createElement('br'); br.className='ajuste'; w.parentNode.insertBefore(br,w);
  }
}
/* Cantado o recitado: un solo botón al comienzo decide todas las piezas gregorianas.
   Recitado: el texto latino de la pieza, con su traducción literal debajo (si está activa). */
const CANTA=()=>S.cantado!==false;
function lineaRec(l, extra){
  const uno=ps=> S.trad ? interHTML(ps) : marcas(ps.map(x=>x[0]).join(' '));
  const cuerpo = l.versos ? l.versos.map(v=>`<span class="ln">${uno(v)}</span>`).join('') : uno(l.pares);   // renglones con sentido (base)
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
  if(!CANTA() && sec.rec) return recitadoHTML(sec.rec);
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
  if(S.canto && S.antGreg && a.gabc) return `<div class="ant-greg">${partituraHTML(a.gabc, a.glosa)}</div>`;
  if(BI() && a.il) return `<div class="ant il"><p><span class="n">${esc(a.n||'Ant.')}</span> ${interHTML(a.il)}</p></div>`;
  const t=txt(a.t);
  return `<div class="ant"><p><span class="n">${esc(a.n||'Ant.')}</span>${a.es?'<b>':''}${marcas(t.p.replace(/ \* /,' '))}${a.es?'</b>':''}</p>${t.s?`<span class="gl">${esc(t.s.replace(/ \* /,' '))}</span>`:''}</div>`;
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
  const o= sec.efimera ? (ops.find(x=>x.id===(S._marDia||{})['h:'+ops[0].id])||def) : elegida(sec,'himno',def);
  let h='';
  if(ops.length>1) h+=botonesHTML('himno', ops[0].id, ops, o, sec.efimera, 'Himno');
  if(!CANTA() && o.rec) return h+recitadoHTML(o.rec,'estrofas');
  if(S.canto && o.gabc) return h+partituraHTML(o.gabc, S.trad?o.glosa:null);
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
  const est=usarTrad?o.trad.es:o.est, amen=usarTrad?(o.trad.amen||'Amén.'):(o.amen||'');
  const numerar=est.length>1; const GL=(bi&&!usarTrad)?glosaLineas(est,o.glosa):null;
  h+=`<div class="himno${numerar?'':' sin-num'}">`+est.map((e,ie)=>{
    const ult=ie===est.length-1;
    return `<p class="est">${numerar?`<span class="num">${ie+1}.</span>`:''}${e.map((l,il)=>`<span class="ln">${esc(l)}${ult&&il===e.length-1&&amen?' '+esc(amen):''}</span>${GL?`<span class="gl">${esc(GL[ie][il])}</span>`:''}`).join('')}</p>`; }).join('')+'</div>';
  return h;
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
  if(CANTA() && sec.gabc) return partituraHTML(sec.gabc, S.trad?sec.glosa:null);
  const es=VES(); const la=sec.l.la, sp=sec.l[es]||sec.l.es79||sec.l.es;
  const P= S.lengua==='es'? sp : la; const Sx= S.lengua==='bi'? (sec.lit? sec.lit.map((x,i)=>[la[i][0],x]) : sp) : null;
  return `<div class="vr">${P.map((x,i)=>`<p${x[0]==='V'?' class="pv"':''}><span class="k">${x[0]==='V'?'℣':'℟'}.</span> ${x[0]==='R'?'<b>'+marcas(x[1])+'</b>':marcas(x[1])}${Sx&&Sx[i]?`<span class="gl">${marcas(Sx[i][1])}</span>`:''}</p>`).join('')}</div>`;
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

function horaHTML(){
  _id=0; GAB.clear();
  const r=R(); let h='';
  h+=`<p class="dia-h">${esc(r.dia.titulo)} · ${esc(r.dia.tiempo)}${r.dia.visperas?`<br>${esc(r.dia.visperas)}`:''}${CP.difiereRegion(S.fecha)?`<br>Calendario de ${esc(CP.regiones[S.region])}`:''}</p>`;
  if(r.dia.nota) h+=`<p class="aviso">${esc(r.dia.nota)}</p>`;
  h+=`<div class="opciones modo-canto" role="group" aria-label="Cantado o recitado">${[[true,'Cantado'],[false,'Recitado']].map(([v,n])=>`<button data-act="cantado" data-v="${v?'si':'no'}" aria-pressed="${CANTA()===v}">${n}</button>`).join('')}</div>`;
  let pleg=null;
  r.secciones.forEach(sec=>{
    if(sec.k==='sec'){
      pleg=sec.plegable?sec.id:null;
      h+=`<h2 class="sec" id="s-${sec.id}">${esc(sec.t)}${sec.plegable?` <button data-act="examen" aria-expanded="${S.examen}">${S.examen?'Ocultar':'Mostrar'}</button>`:''}${sec.ref?`<span class="sref">${esc(cita(sec.ref))}</span>`:''}</h2>`;
      return;
    }
    aplicarModo(sec.k, sec);
    if(sec.pleg && !S.examen) return;
    if(sec.k==='rub' && pleg && !S.examen) return;
    switch(sec.k){
      case 'rub': h+=`<p class="rub">${esc(sec.t)}</p>`; break;
      case 'vr': h+=vrHTML(sec); break;
      case 'vr1': { if(BI()&&sec.il){ h+=`<div class="vr il"><p><span class="k">${/^R\./.test(sec.t.la)?'℟':'℣'}.</span> <span class="segs">${interHTML(sec.il)}</span></p></div>`; break; } const t=txt(sec.t); h+=`<div class="vr"><p><span class="k">℣.</span> ${marcas(t.p.replace(/^R\. /,''))}${t.s?`<span class="gl">${marcas(t.s.replace(/^R\. /,''))}</span>`:''}</p></div>`; break; }
      case 'doxo': h+=prosaHTML(sec.t,null,'',sec.il); break;
      case 'prosa': h+=(sec.n?`<p class="rub">${esc(sec.n)}</p>`:'')+prosaHTML(sec.t, sec.amen, '', sec.il); break;
      case 'oremos': h+= BI()&&sec.il ? `<p class="il"><b>${interHTML(sec.il)}</b></p>` : `<p><b>${esc(txt(sec.t).p)}</b></p>`; break;
      case 'lectura': { const t=txt(sec.t); const ref=sec.ref?txt(sec.ref).p:''; if(BI()&&sec.il){ h+=`<p class="il"><span class="lec-ref">${esc(cita(ref))}</span>${interHTML(sec.il)}</p>`+(sec.aviso?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; } h+=`<p>${ref?`<span class="lec-ref">${esc(cita(ref))}</span>`:''}${esc(t.p)}</p>`+(t.s?`<p class="gl">${esc(t.s)}</p>`:'')+(sec.aviso&&S.lengua!=='es'?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; }
      case 'himno': h+=himnoHTML(sec); break;
      case 'ant': h+=antHTML(sec); break;
      case 'salmo': h+=salmoHTML(sec); break;
      case 'resp': h+=respHTML(sec); break;
      case 'mariana': h+=marianaHTML(sec); break;
      case 'deo': h+=`<div class="vr"><p><span class="k">℟.</span> <b>${esc(sec.t)}</b></p></div>`; break;
      case 'examen': h+=examenHTML(sec); break;
      case 'cantico':
        h+=`<div class="salmo-h"><span class="t">${esc(sec.titulo)}</span></div>`
          +(!sec.gabc ? `<div class="versos${S.trad?' inter':''}">${versosMarcados(sec.versos,S.trad?sec.inter:null)}</div>`   // sin partitura (Benedictus): todo pautado
            : CANTA() ? partituraHTML(sec.gabc, S.trad?sec.glosa:null, false)
              +`<div class="versos${S.trad?' inter':''}">${versosMarcados(sec.versos,S.trad?sec.inter:null)}</div>`
            : `<div class="versos${S.trad?' inter':''}">${versosMarcados([sec.verso1,...sec.versos],S.trad?[sec.inter1,...sec.inter]:null)}</div>`); break;
      case 'preces': {
        // Cada prece: flexa (†) en el corte del medio y asterisco (*) al final; la respuesta la dicen todos
        if(sec.renglones){ h+=sec.renglones.map(t=>`<p>${esc(t)}</p>`).join(''); break; }
        h+=`<p>${esc(sec.intro)}</p><p class="todos">${esc(sec.respuesta)}</p>`
          +`<div class="preces">${sec.preces.map(([a,b])=>`<p><span class="pa">${esc(a)}&nbsp;<span class="sg">†</span></span><span class="pb">${esc(b)}&nbsp;<span class="sg">*</span></span></p>`).join('')}</div>`
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
function horaActual(){ const d=new Date(); const m=d.getHours()*60+d.getMinutes();
  if(m<5*60) return 'completas'; if(m<9*60) return 'laudes'; if(m<11*60) return 'tercia'; if(m<14*60) return 'sexta'; if(m<17*60) return 'nona'; if(m<21*60) return 'visperas'; return 'completas'; }
const HORAS=[['oficio','Oficio de lectura'],['laudes','Laudes'],['tercia','Tercia'],['sexta','Sexta'],['nona','Nona'],['visperas','Vísperas'],['completas','Completas']];
const COLORES={Verde:'var(--verde)',Morado:'#6b3f8a',Rojo:'#b0302a',Blanco:'#d9d2c3',Rosa:'#d58aa0',Negro:'#333','Azul o blanco':'#4f7fbf'};
function portadaHTML(){
  const r=R(); const ahora=horaActual(); const esHoy=S.fecha===fechaHoy();
  const reg=CP.difiereRegion(S.fecha) ? `<div class="region"><span>Este día el calendario difiere:</span>${seg('region',Object.entries(CP.regiones),S.region)}</div>` : '';
  return `<div class="portada">
    <div class="navdia">
      <button class="iconbtn" data-act="dia" data-v="-1" aria-label="Día anterior">${'‹'}</button>
      <span class="fecha">${esHoy?'Hoy, ':''}${esc(esHoy?r.fechaTxt.toLowerCase():r.fechaTxt)}</span>
      <button class="iconbtn" data-act="dia" data-v="1" aria-label="Día siguiente">${'›'}</button>
      ${esHoy?'':'<button class="hoybtn" data-act="hoy">Hoy</button>'}
    </div>
    <div class="dia">
      <div class="txt">
        <div><div class="hoy">${esc(r.dia.grado)}</div><h2>${esc(r.dia.titulo)}</h2></div>
        <div class="meta"><span class="color" style="--col:${COLORES[r.dia.color]||'var(--verde)'}">${esc(r.dia.tiempo)}</span>${r.dia.salterio?`<span>${esc(r.dia.salterio)}</span>`:''}</div>
      </div>
      <div class="arco"><span class="ilu" style="--ilu:url(${window.ILU})"></span></div>
    </div>
    ${reg}
    <p class="lbl">${esHoy?'Las horas de hoy':'Las horas del día'}</p>
    <ul class="horas">${HORAS.map(([id,n])=>{
      const ok=id==='completas'||id==='laudes'||id==='visperas';
      return `<li class="${ok?'sel':''}"><button ${ok?`data-act="abrir" data-v="${id}"`:'disabled'}><span class="n">${esc(n)}</span><span class="h">${ok?esc(id==='completas'&&r.dia.visperas?'tras las I Vísperas':''):(esHoy&&id===ahora?'<span class="pronto">ahora · </span>':'')+'<span class="pronto">en preparación</span>'}</span><span class="chev">${ok?'›':''}</span></button></li>`; }).join('')}</ul>
    <p class="nota-proto">Prototipo: Laudes, Vísperas y Completas están armadas para cualquier día, con el calendario ADF. Textos de la Liturgia de las Horas en español; invocación, cántico evangélico y conclusión en latín. En Laudes y Vísperas, los himnos van por ahora solo en español y el santoral está en revisión.</p>
  </div>`;
}

/* ---------- Render ---------- */
function render(){
  aplicarTema();
  const enHora=S.vista==='hora';
  $('#atras').hidden=!enHora;
  $('#brand').innerHTML= enHora? `${esc(R().nombre||'Completas')}<small>${esc(D.fechaTxt)}</small>` : '<span class="vh">Liturgia de las Horas</span>';
  $('#main').innerHTML= enHora? `<article class="hora" lang="es">${horaHTML()}</article>` : portadaHTML();
  if(enHora){ ajustarGlosas($('#main')); deslizarElegidos($('#main')); if(document.fonts&&document.fonts.ready) document.fonts.ready.then(()=>ajustarGlosas($('#main'))); pintar($('#main')); }
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
    <div class="grupo"><h3>Lectura</h3><div class="tam"><button data-act="menos" aria-label="Achicar el texto">A−</button><span>Texto ${Math.round(S.lec/1.2*100)} %</span><button data-act="mas" aria-label="Agrandar el texto">A+</button></div>
      <p class="hint" style="margin-top:12px">Tamaño de toda la aplicación</p>${seg('esc',[['n','Normal'],['g','Grande'],['mg','Muy grande'],['max','Máxima']],S.esc)}</div>
    <div class="grupo"><h3>Aspecto</h3>${seg('theme',[['light','Claro'],['dark','Oscuro']],S.theme)}</div>
    <div class="grupo"><h3>Calendario</h3>${seg('region',Object.entries(CP.regiones),S.region)}<p class="hint" style="margin-top:8px">Calendario ADF. Paraguay cambia solo los días en que su calendario difiere.</p></div>
    <div class="grupo"><h3>Canto</h3>
      ${sw('trad',S.trad,'Traducción del latín','Interlineal en el texto y glosa bajo los neumas')}
      <div class="leyenda">quia vidérunt óculi <b>me</b>i <span class="sg">*</span> salutá<i>re</i> <b>tu</b>um<small><span class="sg">*</span> mediante · <span class="sg">†</span> flexa. En el Nunc dimittis: negrita, acento; cursiva, preparación.</small></div></div>`);
}
let _toast, _undo=null;
function toast(m, snap){
  clearTimeout(_toast); let t=$('#toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; t.className='toast'; t.setAttribute('role','status'); t.setAttribute('aria-live','polite'); document.body.appendChild(t); }
  _undo=snap||null;
  t.innerHTML=`<span>${esc(m)}</span>${snap?'<button data-act="deshacer">Deshacer</button>':''}`; t.hidden=false;
  _toast=setTimeout(()=>{ t.hidden=true; _undo=null; },snap?4500:2200);
}

/* ---------- Acciones ---------- */
function refrescarHoja(f){ const y=$('#main')?window.scrollY:0; render(); window.scrollTo(0,y); if(f) f(); }
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
    case 'abrir': { const abrir=()=>{ S._marDia={}; S.hora=v||'completas'; cargarDia(); S.vista='hora'; empujar('hora'); guardar(); render(); window.scrollTo(0,0); };
      if(MAYORES[v] && !window[v.toUpperCase()]){ toast('Cargando…'); cargarHora(v).then(abrir, ()=>toast('No se pudo cargar la hora. Revisá la conexión.')); } else abrir();
      break; }
    case 'atras': if(history.state&&history.state.hora){ history.back(); } else { S.vista='hoy'; guardar(); render(); window.scrollTo(0,0); } break;
    case 'opciones': hojaOpciones(); break;
    case 'dia': { const n=CP.masDias(S.fecha,+v); if(CP.enRango(n)){ S.fecha=n; cargarDia(); render(); } else toast('Fuera del calendario cargado'); break; }
    case 'hoy': S.fecha=fechaHoy(); cargarDia(); render(); break;
    case 'region': if(S.region===v) break; S.region=v; cargarDia(); cambio('Calendario de '+CP.regiones[v]); break;
    case 'trad': S.trad=!S.trad; cambio('Traducción del latín: '+(S.trad?'sí':'no')); break;
    case 'salmos': if(S.salmos===v) break; S.salmos=v; cambio('Salmos: '+{pautado:'sin partitura',primer:'primer verso en partitura',todos:'todo en partitura'}[v]); break;
    case 'examenF': S.examenF=v; cambio('Examen: '+b.textContent); break;
    case 'himno': if(b.dataset.e){ S._marDia['h:'+b.dataset.k]=v; refrescarHoja(); } else { S.himno[b.dataset.k]=v; cambio('Himno cambiado'); } break;
    case 'mariana': if(b.dataset.e){ S._marDia[b.dataset.k]=v; refrescarHoja(); } else { S.mariana[b.dataset.k]=v; cambio('Antífona cambiada'); } break;
    case 'concl': if(S.concl===v) break; S.concl=v; cambio('Conclusión: '+b.textContent.toLowerCase()); break;
    case 'cantado': { const c=v==='si'; if(CANTA()===c) break; S.cantado=c; cambio(c?'Completas cantadas':'Completas recitadas'); break; }
    case 'examen': S.examen=!S.examen; guardar(); refrescarHoja(); toast(S.examen?'Examen de conciencia visible':'Examen de conciencia oculto'); break;
    case 'menos': S.lec=Math.max(.9,Math.round((S.lec-.1)*10)/10); cambio('Texto al '+Math.round(S.lec/1.2*100)+' %',false); break;
    case 'mas': S.lec=Math.min(2,Math.round((S.lec+.1)*10)/10); cambio('Texto al '+Math.round(S.lec/1.2*100)+' %',false); break;
    case 'esc': if(S.esc===v) break; S.esc=v; cambio('Tamaño: '+{n:'normal',g:'grande',mg:'muy grande',max:'máximo'}[v]); break;
    case 'theme': if(S.theme===v) break; S.theme=v; guardar(); aplicarTema(); reabrir(); toast({light:'Modo claro',dark:'Modo oscuro'}[v], snap); break;
  }
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape') cerrar(); });
// Barras que se esconden al bajar y vuelven al subir
let yAnt=0; window.addEventListener('scroll',()=>{ const y=window.scrollY; const bajar=y>yAnt && y>120; if(S.vista==='hora'){ $('#top').classList.toggle('oculta',bajar); } yAnt=y; },{passive:true});
document.addEventListener('scroll',e=>{ const f=e.target; if(f.classList&&f.classList.contains('desliza')) f.classList.toggle('mas', f.scrollLeft+f.clientWidth<f.scrollWidth-2); },true);
let _rz; window.addEventListener('resize',()=>{ clearTimeout(_rz); _rz=setTimeout(()=>{ if(S.vista==='hora'){ ajustarGlosas($('#main')); pintar($('#main')); } },250); });

// Si se recarga con Laudes abierta, primero se cargan sus datos
if(S.vista==='hora' && MAYORES[S.hora] && !window[S.hora.toUpperCase()]){ S.vista='hoy'; cargarHora(S.hora).then(()=>{ S.vista='hora'; cargarDia(); render(); }, ()=>{}); }
render();
