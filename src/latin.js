/* ================== «Solo latín» (26/11/2026) ==================
   La hora latina de Universalis (src/carga/latin-AAAA-MM.js, de extraccion/latin/) sobre el armado de la app: la hora
   que arma la app (con el calendario ADF) da el esqueleto y las piezas que ya están en latín con su traducción literal
   (invocación, Dómine, lábia mea, himnos gregorianos y latinos, cántico evangélico, Pater noster, conclusión, Completas);
   lo que la app tiene en español (salmodia, lecturas, responsorios, preces, oración) se cambia por el latín del día.
   Lo que viene de Universalis va sin traducción por ahora (Juana, 26/11/2026: el texto oficial en español debajo quedó
   para revisar antes); lo que ya estaba en latín en la app conserva su traducción literal. El latín sigue el calendario
   general: si ese día celebra otra cosa que ADF, se reza lo del calendario general. */
(function(){
const CP=window.Completas, X=CP._;
const norm=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/æ/g,'ae').replace(/œ/g,'oe').replace(/[^a-z0-9]+/g,' ').trim();
const INGLES=/\b(the|you|use|other|Hour|Invitatory)\b/;
const GLORIA_LA=['Glória Patri, et Fílio, * et Spirítui Sancto.','Sicut erat in princípio, et nunc et semper, * et in sǽcula sæculórum. Amen.'];

const mesDe=f=>f.slice(0,7);
function hay(fecha){ return (window.BASE.latin_meses||[]).includes(mesDe(fecha)); }
function cargado(fecha){ return !!(window.LATIN && window.LATIN[mesDe(fecha)]); }
function dia(fecha){ const M=window.LATIN && window.LATIN[mesDe(fecha)]; return M ? M.dias[fecha] : null; }
// Renglones de un bloque: [{t, sang, est, cur, neg, p}]
function lineas(M, b){ return (b.l || M.T[b.n] || []).map(([t,f])=>({t, sang:!!(f&1), est:!!(f&2), cur:!!(f&4), neg:!!(f&8), p:!!(f&16)})); }

// La hora latina, por papeles
function papeles(fecha, hora, compl){
  const M=window.LATIN[mesDe(fecha)], D=M.dias[fecha]; if(!D) return null;
  const bl=D.h[hora==='tercia'||hora==='sexta'||hora==='nona'?hora:hora]; if(!bl) return null;
  const P={cel:D.c, salmos:[], lecturas:[], resps:[], vrs:[]};
  let vigilias=false, previo=null;
  for(const b of bl){
    const ls=lineas(M,b), s=b.s||[], t=b.t||'';
    if(s[0]==='Pro vigiliis'){ vigilias=true; continue; }
    if(vigilias){ if(t==='Canticum' && !b.r){ vigilias=false; } else continue; }   // cánticos y evangelio de las vigilias: no van
    if(/^PSALMODIA|^CONTINUATIO/.test(s[0]||'')) continue;
    if(b.a==='lastblock' && /^(tercia|sexta|nona)$/.test(hora) && !compl && (s[0]||'').startsWith('Ps')) continue;
    if(b.a==='firstblock' && /^(tercia|sexta|nona)$/.test(hora) && compl && (s[0]||'').startsWith('Ps')) continue;
    if(/^Introductio \(cum/.test(t)){ P.labia=ls; continue; }
    if(/^Ps 94/.test(t)){ P.inv=ls; continue; }
    if(/^Introductio|^INTRODUCTIO/.test(t)) continue;
    if(t==='Hymnus'){ P.himno=ls; continue; }
    if(/^(Ps|Psalmus) \d/.test(s[0]||'') || (t==='Canticum' && b.r)){
      P.salmos.push({ref: t==='Canticum' ? b.r : s[0], titulo: t==='Canticum' ? (s[0]||'') : (s[1]||''), ls}); continue; }
    if(t==='Lectio brevis'){ P.lectura={ref:b.r||'', t:ls.map(l=>l.t).join(' ')}; previo='lectura'; continue; }
    if(t==='Responsorium breve'){ P.resp=ls; continue; }
    if(/^Lectio /.test(t)){ P.lecturas.push({tit:t, ref:b.r||'', sub:s[0]||'', ls}); previo='lectio'; continue; }
    if(t==='Responsorium'){ P.resps.push({ref:b.r||'', ls}); continue; }
    if(t==='Canticum' && !b.r){ if(/^Te Deum/.test((ls[0]||{}).t)) P.tedeum=ls; else P.cantico=ls; continue; }
    if(t==='Preces'){ P.preces=ls; continue; }
    if(t==='Conscientiæ discussio') continue;
    if(/^Antiphona finalis/.test(s[0]||'')) continue;
    const l0=(ls[0]||{}).t||'';
    if(/^Pater noster/.test(l0)) continue;
    if(/^[℣℟]\./.test(l0)){ P.vrs.push(ls); continue; }   // versículo (después de la salmodia o de la lectura breve)
    if(/^Or[ée]mus\.?$/.test(l0) || (ls.length && ls[0].p && !/^(Benedic|Dóminus|Noctem)/.test(l0))){ P.oracion=ls; continue; }
    if(/^(Benedicámus|Dóminus nos|Noctem)/.test(l0)) continue;   // conclusión: la de la app (gregoriano, con traducción)
  }
  return P;
}

// Un salmo latino → sección «salmo» (versos con * y †, para el pautado latino) y sus antífonas
function salmoLatino(x, id, modo, esSalmos){
  let ls=x.ls.slice(); let ant=null, antFin=null;
  if(ls[0] && ls[0].cur){ ant=ls[0].t; ls=ls.slice(1); }
  if(ls.length && ls[ls.length-1].cur){ antFin=ls[ls.length-1].t; ls=ls.slice(0,-1); }
  const g=ls.findIndex(l=>/^Glória Patri/.test(l.t)), gloria=g>=0; if(gloria) ls=ls.slice(0,g);
  const est=[]; ls.forEach(l=>{ if(l.est || !est.length) est.push([]); est[est.length-1].push(l.t.replace(/\s*\*$/,' *').replace(/\s*†$/,' †')); });
  const v=X.versosDe(est.map(e=>e.join('\n')));
  const R=window.LATIN[Object.keys(window.LATIN)[0]].R||{}, clave=R[x.ref];
  const S=clave && esSalmos && esSalmos[clave];
  return {ant, antFin, sec:{k:'salmo', la:true, id:clave||('la:'+x.ref), ant:id, modo, titulo:{la:S?S.titulo:x.ref.replace(/^Ps /,'Salmo ').replace(/:/,', ')},
    lema:{la:x.titulo||''}, versos:{la:v.versos}, grupos:{la:v.grupos}, gloria}};
}

// Himno latino: el gregoriano o el del Apéndice IV de la app (con su traducción literal), si es el mismo; si no, solo el latín
function himnoLatino(ls, ops, latinos){
  if(!ls || !ls.length) return null;
  const c=norm(ls[0].t).split(' ').slice(0,3).join(' ');
  const o=(ops||[]).find(o=>(o.gabc||o.lat) && (norm(o.n).startsWith(c) || norm((o.est&&o.est[0]&&o.est[0][0])||'').startsWith(c)));
  if(o) return [o];
  const h=Object.values(latinos||{}).find(h=>norm(h.estrofas[0][0][0]).startsWith(c));
  if(h) return [{id:'lat', n:h.titulo, lang:'la', lat:true, est:h.estrofas.map(e=>e.map(p=>p[0])), lit:h.estrofas.map(e=>e.map(p=>p[1]||'')), amen:h.amen?'Amen.':''}];
  const est=[]; ls.forEach(l=>{ if(l.est || !est.length) est.push([]); est[est.length-1].push(l.t); });
  let amen=''; const u=est[est.length-1], m=/^(.*?)\s*Amen\.$/.exec(u[u.length-1]); if(m){ amen='Amen.'; if(m[1]) u[u.length-1]=m[1]; else u.pop(); }
  return [{id:'lat', n:ls[0].t.replace(/[,;:.]$/,''), lang:'la', lat:true, est, lit:est.map(e=>e.map(()=>'')), amen}];
}

// Versículos y responsorios latinos («℣. … ℟. …») → [[V|R|'', texto]]
const vr=ls=>ls.map(l=>{ const m=/^([℣℟])\.\s*(.*)$/.exec(l.t), t=(m?m[2]:l.t.replace(/^–\s*/,'')).replace(/\s*\*\s*/g,' * '); return [m ? (m[1]==='℣'?'V':'R') : '', t]; });
// Responsorio breve: el libro lo imprime abreviado («℣. A,* B. A.» / «℟. C.* B. Glória Patri. A.»); se despliega como en
// el libro en español: ℣ A * B / ℟ A * B / ℣ C / ℟ B / ℣ Glória Patri… / ℟ A * B. Si no tiene esa forma, tal cual.
function respBreve(ls){
  const x=vr(ls).map(([k,t])=>[k,t.replace(/\s*\*\s*/g,' * ').trim()]);
  if(x.length!==2 || !/ \* /.test(x[0][1]) || !/ \* /.test(x[1][1])) return x;
  const [a,r1]=x[0][1].split(' * '), [c,r2]=x[1][1].split(' * ');
  const p1=a.split(/\s+/)[0].replace(/[,.;:]$/,'');
  const corta=t=>t.replace(new RegExp('\\s*'+p1.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'[^.]*\\.$'),'').trim();
  const b=corta(r1), gl=/Glória Patri/.test(r2), A=`${a} * ${b}`;
  return [['V',A],['R',A],['V',c],['R',b]].concat(gl?[['V','Glória Patri, et Fílio, et Spirítui Sancto.'],['R',A]]:[]);
}
// Oración: «Oremus.», el texto y la conclusión, sin el «Amen.» (lo pone la sección)
function oracion(ls){
  const t=ls.filter(l=>!/^Or[ée]mus\.?$/.test(l.t) && !/^Amen\.?$/.test(l.t)).map(l=>l.t).join(' ').replace(/\s+/g,' ').trim();
  return {oremus:ls.some(l=>/^Or[ée]mus\.?$/.test(l.t)), t};
}

function armar(r, fecha, hora, opc){
  if(!r || !hay(fecha) || !cargado(fecha)) return r;
  const P=papeles(fecha, hora, opc&&opc.complementaria); if(!P) return r;
  const W=window, Lh=W[{laudes:'LAUDES',visperas:'VISPERAS',oficio:'OFICIO',tercia:'INTERMEDIA',sexta:'INTERMEDIA',nona:'INTERMEDIA'}[hora]];
  const esSalmos=hora==='completas' ? W.BASE.salmos : (Lh&&Lh.salmos)||{};
  const latinos=hora==='completas' ? W.BASE.completas.latinos : (Lh&&Lh.latinos)||{};
  const S0=r.secciones;
  const esSal=S0.filter(s=>s.k==='salmo').map(s=>s.id);
  const R=window.LATIN[mesDe(fecha)].R||{};
  // ¿El mismo oficio? Los mismos salmos (por su clave). Si no, el español solo donde es el mismo texto
  const mismo=P.salmos.length===esSal.length && P.salmos.every((x,i)=>R[x.ref]===esSal[i]);
  const modo=(S0.find(s=>s.k==='salmo'&&s.modo)||{}).modo || (hora==='completas' ? (W.BASE.completas.gregoriano.tonos[r.juego]||'8G') : '8G');
  // Sin el español debajo de lo que viene de Universalis (Juana, 26/11/2026: hay que revisarlo antes); quedan solo
  // las traducciones literales que la app ya tenía (invocación, himnos, cántico evangélico, Pater noster, conclusión…)
  const es=()=>null;
  const out=[], igualLect=[]; let sec=null, salmodiaHecha=false, lect=0, resp=0, vrs=0;
  const antEs=[]; S0.forEach(s=>{ if(s.k==='ant' && !s.rep && /^a\d/.test(s.id||'')) antEs.push(s.t&&s.t.es); });
  for(let i=0;i<S0.length;i++){
    const s=S0[i];
    if(s.k==='sec'){ sec=s.id; out.push(s); continue; }
    // invitatorio
    if(sec==='invitatorio' && P.inv){
      if(s.k==='ant' && !s.rep){ const a=P.inv.find(l=>l.cur); out.push({k:'antla', id:'ai', la:a?a.t:'', es:es(s.t&&s.t.es)}); continue; }
      if(s.k==='salmoinv'){ const ls=P.inv.filter(l=>!l.cur), est=[]; ls.forEach(l=>{ if(l.est||!est.length) est.push([]); est[est.length-1].push(l.t.replace(/\s*\*$/,'')); });
        out.push({...s, titulo:'Salmo 94', ant:(P.inv.find(l=>l.cur)||{}).t||s.ant, estrofas:est, la:true, lema:''}); continue; }
      if(s.k==='ant' && s.rep){ out.push({k:'antla', la:(P.inv.find(l=>l.cur)||{}).t||'', es:null}); continue; }
      if(s.k==='rub') continue;
    }
    if(s.k==='himno' && sec==='himno'){ const ops=himnoLatino(P.himno, s.opciones, latinos); out.push(ops ? {...s, opciones:ops, sinBotones:true, efimera:false} : s); continue; }
    if(sec==='tedeum' && s.k==='himno'){ const ops=s.opciones.filter(o=>o.lat); if(!P.tedeum) continue; out.push(ops.length?{...s, opciones:ops, sinBotones:true}:s); continue; }
    if(sec==='tedeum' && s.k==='rub' && !P.tedeum) continue;
    // salmodia: toda la latina, una sola vez
    if(sec==='salmodia' && (s.k==='ant' || s.k==='salmo' || s.k==='aviso' || (s.k==='rub' && S0[i-1] && S0[i-1].k==='salmo'))){
      if(salmodiaHecha) continue; salmodiaHecha=true;
      P.salmos.forEach((x,j)=>{ const id='la'+(j+1), q=salmoLatino(x, id, modo, esSalmos);
        if(q.ant) out.push({k:'antla', id, la:q.ant, es:es(antEs[j]), ast:true});
        out.push(q.sec);
        const fin=q.antFin||(!P.salmos[j+1] || (P.salmos[j+1].ls[0]||{}).cur ? q.ant : null);
        if(fin) out.push({k:'antla', la:fin, es:es(antEs[j])}); });
      continue; }
    if(s.k==='resp' && sec==='salmodia'){ const l=P.vrs[vrs++]; out.push(l ? {k:'vrla', l:vr(l), es:es(s.l&&s.l.es)} : s); continue; }   // versículo del Oficio
    if(s.k==='lectura'){ if(!P.lectura){ out.push(s); continue; }
      const h=out[out.length-1]; if(h && h.k==='sec' && P.lectura.ref) out[out.length-1]={...h, ref:P.lectura.ref.replace(/:/,', ')};
      out.push({k:'lectura', la:true, t:{la:P.lectura.t, es:es(s.t&&s.t.es)}}); continue; }
    if(s.k==='resp' && sec==='lectura'){ const l=P.vrs[vrs++]; out.push(l ? {k:'vrla', l:vr(l), es:es(s.l&&s.l.es)} : s); continue; }   // versículo de la Hora intermedia
    if(s.k==='resp' && sec==='responsorio'){
      if(s.gabc && hora==='completas'){ out.push({...s, la:true, l:{...s.l, la:P.resp?respBreve(P.resp):null}}); continue; }
      out.push(P.resp ? {k:'vrla', l:respBreve(P.resp), es:es(s.l&&s.l.es)} : s); continue; }
    if(s.k==='ant' && s.id==='ab'){ const a=P.cantico && P.cantico.find(l=>l.cur); out.push(a ? {...s, k:s.gabc?'ant':'antla', la:a.t, es:es(s.t&&s.t.es), t:{la:a.t}} : s); continue; }
    if(s.k==='ant' && s.rep==='ab'){ const a=P.cantico && P.cantico.find(l=>l.cur); out.push(a && !S0.find(x=>x.id==='ab').gabc ? {k:'antla', la:a.t, es:es((S0.find(x=>x.id==='ab').t||{}).es)} : s); continue; }
    if(s.k==='preces'){ out.push(P.preces ? {k:'precesla', l:P.preces.reduce((a,l)=>{ if(l.sang && a.length) a[a.length-1]+='\n'+l.t; else a.push(l.t); return a; },[]), es:es(s)} : s); continue; }
    if(s.k==='pater'){ out.push({...s, intro:''}); continue; }
    if(s.k==='oremos'){ out.push({k:'oremos', la:true, t:{la:'Orémus.'}}); continue; }
    if(s.k==='prosa' && sec==='oracion'){ if(!P.oracion){ out.push(s); continue; } const o=oracion(P.oracion);
      if(o.oremus && hora!=='completas' && !out.some(x=>x.k==='oremos')) out.push({k:'oremos', la:true, t:{la:'Orémus.'}});
      out.push({k:'prosa', la:true, t:{la:o.t, es:es(s.t&&s.t.es)}, amen:{la:'Amen.'}}); continue; }
    // Lecturas del Oficio: la cita va arriba del texto (la del encabezado era la del español). La primera lectura sigue en
    // latín el ciclo de un año y en español el bienal: el español va solo si es la misma (los mismos capítulo y versículos)
    if(s.k==='lectura_larga'){ const x=P.lecturas[lect++]; if(!x){ out.push(s); continue; }
      const h=out[out.length-1], refEs=(h && h.k==='sec' && h.ref) || s.ref || ''; if(h && h.k==='sec') out[out.length-1]={...h, ref:''};
      const nums=t=>{ const m=/(\d+)\s*[,:]\s*(\d+)/.exec(String(t||'')); return m ? m[1]+':'+m[2] : String(t||''); }, bib=/\d/.test(x.ref) && /\d/.test(refEs);
      const igual=!bib || nums(x.ref)===nums(refEs);
      igualLect[lect-1]=igual;
      out.push({k:'lecturala', ref:x.ref, sub:x.sub, verso:!x.ls.some(l=>l.p), ls:x.ls.map(l=>l.t), es:igual?es(s):null}); continue; }
    if(s.k==='resp' && /^lectura\d-r$/.test(sec||'')){ const x=P.resps[resp++]; const h=out[out.length-1]; if(h && h.k==='sec' && x) out[out.length-1]={...h, ref:x.ref||h.ref};
      out.push(x ? {k:'vrla', l:vr(x.ls), es:igualLect[resp-1]===false?null:es(s.l&&s.l.es)} : s); continue; }
    if(s.k==='examen'){ out.push({...s, formulas:s.formulas.filter(f=>f.latin).concat(s.formulas.filter(f=>!f.latin))}); continue; }
    out.push(s);
  }
  // secciones que quedaron vacías (Te Deum que el latín no trae)
  const limpio=out.filter((s,i)=>!(s.k==='sec' && s.id==='tedeum' && !(out[i+1] && out[i+1].k!=='sec')));
  return {...r, latin:true, mismo, secciones:limpio, gloria:{...r.gloria, la:GLORIA_LA},
    dia:{...r.dia, titulo:P.cel||r.dia.titulo, nota: mismo ? '' : `En latín se reza lo del calendario general: ${P.cel}.`}};
}

window.Latin={hay, cargado, armar, mesDe};
})();
