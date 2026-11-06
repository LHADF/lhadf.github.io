/* ================== Septies — prototipo de Completas ================== */
const D=window.DATA, SAL=window.Salmodia;
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------- Estado ---------- */
const DEF={vista:'hoy', rito:'novus', modo:'canto', salmos:'primer', trad:true,
  lec:1.2, esc:'n', theme:'light', tonos:{}, himno:{}, mariana:{}, examen:false};
let S=DEF;
try{ const g=JSON.parse(localStorage.getItem('septies')||'null'); if(g){ S=Object.assign({},DEF,g); delete S.ves; if(!g.modo) S.modo=g.canto?'canto':(g.lengua==='es'?'es':'la'); } }catch(e){}
if(S.salmos==='texto') S.salmos='primer';
if(S.theme!=='dark') S.theme='light'; // claro por defecto; oscuro solo si se elige
S.antGreg=true;
/* Una sola versión: Liturgia de las Horas en modo canto (salmos y lecturas en español pautado, lo demás en latín) */
S.rito='novus'; S.modo='canto';
function aplicarModo(kind, sec){
  S.canto = S.modo==='canto';
  if(S.modo==='es') S.lengua='es';
  else if(S.modo==='la') S.lengua='bi';
  // salmos y lecturas en español; el cántico evangélico, todo en latín
  else S.lengua = ((kind==='salmo'&&!(sec&&sec.cantico))||kind==='lectura') ? 'es' : (S.trad?'bi':'la');
}
aplicarModo();
function guardar(){ try{ const {lengua,canto,antGreg,...g}=S; localStorage.setItem('septies',JSON.stringify(g)); }catch(e){} }
const R=()=>D.ritos[S.rito];
const VES=()=>Object.keys(R().versiones).find(k=>k!=='la'); // una sola versión en español por rito
// S.trad (glosa bajo la partitura) lo usan las funciones heredadas del Cantoral
function aplicarTema(){ const r=document.documentElement; r.dataset.theme=S.theme==='dark'?'dark':'light'; r.style.setProperty('--lec',S.lec); if(S.esc==='n') delete r.dataset.esc; else r.dataset.esc=S.esc; }

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
function svgDe(id, ancho){
  const it=GAB.get(id); if(!it) return Promise.reject();
  const conGlosa=S.trad && it.glosa && it.glosa.length;
  const clave=(it.drop?'d':'n')+it.gabc.length+'|'+it.gabc.slice(-60)+'|'+ancho+'|'+(conGlosa?1:0)+'|'+it.gabc.slice(0,80);
  if(cacheSvg.has(clave)) return Promise.resolve(cacheSvg.get(clave));
  return fuentesListas().then(()=>new Promise((ok,mal)=>{
    try{
      let g=it.gabc; if(conGlosa) g=insertarTraduccion(g,it.glosa);
      const ctxt=contextoExsurge();
      const maps=exsurge.Gabc.createMappingsFromSource(ctxt, gabcParaExsurge(gabcCuerpo(g))); espaciarSilabas(maps);
      const score=new exsurge.ChantScore(ctxt, maps, it.drop && !/initial-style:\s*0/.test(g));
      const modo=gabcModo(g); if(modo) score.annotation=new exsurge.Annotations(ctxt,'%'+ROMANO_MODO[modo]+'%');
      score.performLayoutAsync(ctxt,()=>score.layoutChantLines(ctxt,ancho,()=>{
        const svg=score.createSvgNode(ctxt);
        const w=parseFloat(svg.getAttribute('width')), h=parseFloat(svg.getAttribute('height'));
        if(!svg.getAttribute('viewBox')&&w&&h) svg.setAttribute('viewBox','0 0 '+w+' '+h);
        svg.removeAttribute('width'); svg.removeAttribute('height');
        const html=svg.outerHTML; cacheSvg.set(clave,html); ok(html);
      }));
    }catch(e){ mal(e); }
  }));
}
function pintar(raiz){
  const els=[...(raiz||document).querySelectorAll('.partitura[data-g]')];
  const zoom=S.lec/1.15;
  return els.reduce((p,el)=>p.then(()=>{
    const ancho=Math.max(260, Math.round((el.clientWidth||600)/zoom/10)*10); el.dataset.w=ancho;
    return svgDe(el.dataset.g, ancho).then(html=>{ if(!el.isConnected) return; el.innerHTML=html; const svg=el.querySelector('svg'); uniformarRenglones(svg); if(S.trad) ajustarTraducciones(svg); })
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
  let h=`<div class="salmo-h"><span class="t">${esc(t.p)}</span>${sal.ref?`<span class="ref">${esc(sal.ref)}</span>`:''}${lema&&lema.p?`<span class="lema">${esc(lema.p)}</span>`:''}`;
  h+='</div>';
  // partitura
  let todos=vP.concat(sal.gloria?glP:[]);
  const inter = S.lengua==='bi' && sal.inter ? sal.inter : null;
  const interTodos = inter ? inter.concat(sal.gloria?(r.gloriaInter||[]):[]) : null;
  if(S.canto && (modo==='primer'||modo==='todos')){
    const lista=modo==='todos'?todos:todos.slice(0,1);
    const g=SAL.gabcSalmo(lista,cod,L,true);
    h+=partituraHTML(`name:salmo;\n%%\n${g}`, null, false);
    // traducción de los versos que van en partitura, debajo de ella
    if(interTodos) h+=`<div class="versos inter gl-part">${lista.map((v,i)=>`<p class="v">${glosaVerso(v,interTodos[i]).map((x,k)=>x?`<span class="gl ${k?'h2':'h1'}">${esc(x)}</span>`:'').join('')}</p>`).join('')}</div>`;
    if(modo==='todos') return h;
  }
  const inicio=(S.canto&&modo==='primer')?1:0;
  const modoTxt=(S.canto&&modo!=='texto')?'pautado':'texto';
  const resto=todos.slice(inicio);
  h+=`<div class="versos${inter?' inter':''}">${versosHTML(resto,modoTxt,cod,L,inicio,interTodos?interTodos.slice(inicio):null)}</div>`;
  return h;
}

/* ---------- Secciones ---------- */
// Interlineal por segmentos: cada grupo de palabras latinas con su traducción literal debajo
const BI=()=>S.lengua==='bi';
function interHTML(pares){
  const seg=(a,b)=>`<span class="ilseg"><span class="sl">${marcas(a)}</span><span class="se">${marcas(b)}</span></span>`;
  return pares.map(([a,b])=>{ // ✠ o * al comienzo del latín: segmento propio, sin traducción, para centrarlo entre los textos
    const m=/^([✠*])\s+(.*)$/.exec(a);
    return m ? `<span class="ilseg signo" aria-hidden="true"><span class="sl">${m[1]}</span><span class="se"></span></span> `+seg(m[2],b.replace(/^[✠*]\s*/,'')) : seg(a,b);
  }).join(' ');
}
// Centra cada signo en el hueco que queda entre el final del texto anterior y el comienzo del siguiente
function anchoTexto(el){ const r=document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); }
function centrarSignos(raiz){
  (raiz||document).querySelectorAll('.ilseg.signo').forEach(s=>{
    s.style.transform='';
    const prev=s.previousElementSibling, next=s.nextElementSibling;
    if(!prev||!next||!prev.classList.contains('ilseg')||!next.classList.contains('ilseg')) return;
    const a=anchoTexto(prev.querySelector('.sl')), c=anchoTexto(next.querySelector('.sl')), b=anchoTexto(s.querySelector('.sl'));
    const mismo=(x,y)=>Math.abs((x.top+x.bottom)/2-(y.top+y.bottom)/2)<b.height/2;
    if(!mismo(a,b)||!mismo(c,b)) return; // signo al comienzo o al final del renglón
    const centro=(a.right+c.left)/2; s.style.transform=`translateX(${centro-(b.left+b.width/2)}px)`;
  });
}
function vrHTML(sec){
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
  h+=`<p>${extra||''}${marcas(t.p)}${amen?` <span class="amen"><span class="k">℟.</span> ${esc(txt(amen).p)}</span>`:''}</p>`;
  if(t.s) h+=`<p class="gl">${marcas(t.s)}${amen?' '+esc(txt(amen).s||''):''}</p>`;
  return h;
}
function antHTML(sec){
  const a=sec.rep?antDe(sec.rep):sec; if(!a) return '';
  if(S.canto && S.antGreg && a.gabc) return `<div class="ant-greg">${partituraHTML(a.gabc, a.glosa)}</div>`;
  if(BI() && a.il) return `<div class="ant il"><p><span class="n">${esc(a.n||'Ant.')}</span> ${interHTML(a.il)}</p></div>`;
  const t=txt(a.t);
  return `<div class="ant"><p><span class="n">${esc(a.n||'Ant.')}</span>${marcas(t.p.replace(/ \* /,' '))}</p>${t.s?`<span class="gl">${esc(t.s.replace(/ \* /,' '))}</span>`:''}</div>`;
}
function elegida(sec, clave, def){ const id=S[clave][sec.opciones[0].id]; return sec.opciones.find(o=>o.id===id)||def; }
function himnoHTML(sec){
  const ops=sec.opciones;
  const def= ops.find(o=>o.lang===(S.lengua==='es'?VES():'la')) || ops.find(o=>o.lang==='es79'&&S.lengua==='es') || ops[0];
  const o=elegida(sec,'himno',def);
  let h='';
  if(ops.length>1) h+=`<div class="opciones" role="group" aria-label="Himno">${ops.map(x=>`<button data-act="himno" data-k="${ops[0].id}" data-v="${x.id}" aria-pressed="${x===o}">${esc(x.n)}</button>`).join('')}</div>`;
  if(S.canto && o.gabc) return h+partituraHTML(o.gabc, (S.lengua!=='la'||S.trad)?o.glosa:null);
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
function respHTML(sec){
  if(S.canto && S.antGreg && sec.gabc) return partituraHTML(sec.gabc, (S.lengua!=='la'||S.trad)?sec.glosa:null);
  const es=VES(); const la=sec.l.la, sp=sec.l[es]||sec.l.es79||sec.l.es;
  const P= S.lengua==='es'? sp : la; const Sx= S.lengua==='bi'? (sec.lit? sec.lit.map((x,i)=>[la[i][0],x]) : sp) : null;
  return `<div class="vr">${P.map((x,i)=>`<p><span class="k">${x[0]==='V'?'℣':'℟'}.</span> ${marcas(x[1])}${Sx&&Sx[i]?`<span class="gl">${marcas(Sx[i][1])}</span>`:''}</p>`).join('')}</div>`;
}
function marianaHTML(sec){
  const ops=sec.opciones; const o=elegida(sec,'mariana',ops[0]);
  let h=`<div class="opciones" role="group" aria-label="Antífona">${ops.map(x=>`<button data-act="mariana" data-k="${ops[0].id}" data-v="${x.id}" aria-pressed="${x===o}">${esc(x.n)}</button>`).join('')}</div>`;
  if(S.canto && S.antGreg && o.gabc) return h+partituraHTML(o.gabc,(S.lengua!=='la'||S.trad)?o.glosa:null);
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
  h+=`<p class="dia-h">${esc(r.dia.titulo)} · ${esc(r.dia.tiempo)}<br>${esc(r.nombre)}</p>`;
  let pleg=null;
  r.secciones.forEach(sec=>{
    if(sec.k==='sec'){
      pleg=sec.plegable?sec.id:null;
      h+=`<h2 class="sec" id="s-${sec.id}">${esc(sec.t)}${sec.plegable?` <button data-act="examen" aria-expanded="${S.examen}">${S.examen?'Ocultar':'Mostrar'}</button>`:''}</h2>`;
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
      case 'lectura': { const t=txt(sec.t); const ref=txt(sec.ref).p; if(BI()&&sec.il){ h+=`<p class="il"><span class="lec-ref">${esc(ref)}</span>${interHTML(sec.il)}</p>`+(sec.aviso?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; } h+=`<p><span class="lec-ref">${esc(ref)}</span>${esc(t.p)}</p>`+(t.s?`<p class="gl">${esc(t.s)}</p>`:'')+(sec.aviso&&S.lengua!=='es'?`<p class="aviso">${esc(sec.aviso.txt)}</p>`:''); break; }
      case 'himno': h+=himnoHTML(sec); break;
      case 'ant': h+=antHTML(sec); break;
      case 'salmo': h+=salmoHTML(sec); break;
      case 'resp': h+=respHTML(sec); break;
      case 'mariana': h+=marianaHTML(sec); break;
    }
  });
  aplicarModo();
  h+=`<p class="fin">✠</p>`;
  return h;
}

/* ---------- Portada ---------- */
function horaActual(){ const d=new Date(); const m=d.getHours()*60+d.getMinutes();
  if(m<5*60) return 'completas'; if(m<9*60) return 'laudes'; if(m<11*60) return 'tercia'; if(m<14*60) return 'sexta'; if(m<17*60) return 'nona'; if(m<21*60) return 'visperas'; return 'completas'; }
function portadaHTML(){
  const r=R(); const ahora=horaActual();
  return `<div class="portada">
    <div class="dia">
      <div class="txt">
        <div><div class="hoy">Hoy, ${esc(D.fechaTxt.toLowerCase())}</div><h2>${esc(r.dia.titulo)}</h2></div>
        <div class="meta"><span class="color">${esc(r.dia.tiempo)}</span><span>${esc(r.dia.salterio)}</span></div>
      </div>
      <div class="arco"><span class="ilu" style="--ilu:url(${window.ILU})"></span></div>
    </div>
    <p class="lbl">Las horas de hoy</p>
    <ul class="horas">${D.horas.map(([id,n,hh])=>{
      const ok=id==='completas';
      return `<li class="${ok?'sel':''}"><button ${ok?'data-act="abrir"':'disabled'}><span class="n">${esc(n)}</span><span class="h">${ok?'':(id===ahora?'<span class="pronto">ahora · </span>':'')+'<span class="pronto">en preparación</span>'}${ok?esc(hh):''}</span><span class="chev">${ok?'›':''}</span></button></li>`; }).join('')}</ul>
    <p class="nota-proto">Prototipo: solo Completas de hoy está armada. Los textos latinos de la Liturgia de las Horas se tomaron de la Nova Vulgata y deben cotejarse con la edición típica.</p>
  </div>`;
}

/* ---------- Render ---------- */
function render(){
  aplicarTema();
  const enHora=S.vista==='hora';
  $('#atras').hidden=!enHora;
  $('#brand').innerHTML= enHora? `Completas<small>${esc(D.fechaTxt)}</small>` : '<span class="vh">Liturgia de las Horas</span>';
  $('#main').innerHTML= enHora? `<article class="hora" lang="la">${horaHTML()}</article>` : portadaHTML();
  if(enHora){ centrarSignos($('#main')); if(document.fonts&&document.fonts.ready) document.fonts.ready.then(()=>centrarSignos($('#main'))); pintar($('#main')); }
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
    <div class="grupo"><h3>Canto</h3>
      ${sw('trad',S.trad,'Traducción del latín','Interlineal en el texto y glosa bajo los neumas')}
      <p class="hint" style="margin-top:12px">Salmos</p>${seg('salmos',[['pautado','Pautados'],['primer','1.er verso en partitura'],['todos','Todo en partitura']],S.salmos)}
      <div class="leyenda">Prot<b>é</b>geme, Dios mío, que me re<i>fu</i><b>gio</b> en ti <span class="sg">*</span><small>Negrita: acento · cursiva: preparación · <u>subrayado</u>: entonación · <span class="sg">*</span> mediante · <span class="sg">†</span> flexa. El tono sigue a la antífona.</small></div></div>`);
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
    case 'deshacer': if(_undo){ S=JSON.parse(_undo); aplicarModo(); _undo=null; guardar(); refrescarHoja(reabrir); toast('Cambio deshecho'); } break;
    case 'abrir': S.vista='hora'; empujar('hora'); guardar(); render(); window.scrollTo(0,0); break;
    case 'atras': if(history.state&&history.state.hora){ history.back(); } else { S.vista='hoy'; guardar(); render(); window.scrollTo(0,0); } break;
    case 'opciones': hojaOpciones(); break;
    case 'trad': S.trad=!S.trad; cambio('Traducción del latín: '+(S.trad?'sí':'no')); break;
    case 'salmos': if(S.salmos===v) break; S.salmos=v; cambio('Salmos: '+{pautado:'pautados',primer:'primer verso en partitura',todos:'todo en partitura'}[v]); break;
    case 'himno': S.himno[b.dataset.k]=v; cambio('Himno cambiado'); break;
    case 'mariana': S.mariana[b.dataset.k]=v; cambio('Antífona cambiada'); break;
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
let _rz; window.addEventListener('resize',()=>{ clearTimeout(_rz); _rz=setTimeout(()=>{ if(S.vista==='hora'){ centrarSignos($('#main')); pintar($('#main')); } },250); });

render();
