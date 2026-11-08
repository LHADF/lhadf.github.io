const ESP_SILABA=5, ESP_PAUSA=2.5, ESP_PAUSA_CHICA=4.5; // pausas chicas: divisio minima (,) y virgula (`)
let _fuentes=null;
const ROMANO_MODO=['','i','ii','iii','iv','v','vi','vii','viii'];
function contextoExsurge(){
  const ctxt=new exsurge.ChantContext(exsurge.TextMeasuringStrategy.Canvas);
  ctxt.condenseLineAmount=1; ctxt.setGlyphScaling(1/16);
  // Igual que Chant Tools: dibuja en el color del texto (currentColor), así el modo oscuro no requiere redibujar
  ctxt.textColor='currentColor'; ctxt.staffLineColor=ctxt.neumeLineColor=ctxt.dividerLineColor='currentColor';
  ctxt.negativeFillColor='var(--exsurge-negative-fill, #fff)';
  ctxt.setFont("'Cantoral Signos', 'Septies AE', 'Source Serif 4', Georgia, serif", 20.5);
  ctxt.spaceBetweenSystems=0; ctxt.textStyles.dropCap.size=64; ctxt.textStyles.annotation.size=12.8;
  ctxt.minLyricWordSpacing*=0.7; ctxt.interSyllabicMultiplier=ESP_SILABA; ctxt.accidentalSpaceMultiplier=1.5;
  ctxt.setRubricColor('var(--rubric, #981914)');
  ctxt.specialCharMap={"℣":"℣","℟":"℟","V":"℣","R":"℟","+":"+","*":"*"};
  ctxt.specialCharProperties["font-family"]="'Cantoral Signos', 'Source Serif 4', serif"; ctxt.specialCharProperties["font-size"]="80%";
  return ctxt;
}
function gabcParaExsurge(g){
  return g.replace(/<i>(Ps\.|Cant\.)<\/i>\s*/g,'^$1^ ')            // «Ps.» del Introito, en rojo como rúbrica
    .replace(/(^|[\s)])Ps\.\s+(?=[A-ZÁÉÍÓÚ])/gm,'$1^Ps.^ ')
    .replace(/<c>\*\*<\/c>\(([^)]*)\)/g,'\u0001($1)')                       // doble asterisco: se protege y se repone al final
    .replace(/<v>\\([VRA])bar<\/v>/g,(m,b)=>b+'/.')
    .replace(/<sp>([VRA])\/<\/sp>\.?/g,(m,b)=>b+'/.')
    .replace(/(\)\s+)([^()]*V\/\.\s*\d+\.?)(?=[ (])/g,'$1^$2^')
    .replace(/\\emph{([^(}]+)\}/g,'_$1_')
    .replace(/(v[A-Z]__[A-Z])([^_])/g,'$1_3$2')
    .replace(/([^)]\s+)([*†]|<i>i+j\.<\/i>)\(/g,'$1^$2^(')
    .replace(/\^?(<i>[^(|]*? [^(|]*?<\/i>)\^?([^(|]*)/g,'^$1^$2')
    .replace(/\*(\([:;,]+\))\s+(<i>i+j\.<\/i>)\(/g,'{*} $2$1 (')
    .replace(/(\s+)({?<i>i+j\.<\/i>}?)\(/g,'$1^$2^(')
    .replace(/\[([^\]\s-áéíóú]+)\](?=\()/g,'|$1 ')
    .replace(/\[([^\]\s-]+)-?\](?=\()/g,'|$1')
    .replace(/(?:{})?<i>\(([^)]+)\)<\/i>/g,'_{}$1_')
    .replace(/<\/?i>/g,'_')
    .replace(/(\)\s+(?:\([^)]*\))*)(\s*[^(^|]+)(?=\(\))/g,'$1^$2^')
    .replace(/\\hspace{[^}]*}/g,'')
    .replace(/(?:\(Z\)\s*)?<alt>(.*?)<\/alt>/gi,'')
    .replace(/<\/?eu>|\[[ou]ll:[01]?[{}][01]?\]/ig,'')
    .replace(/<\/?c>/g,'')
    .replace(/<sp>'?(ae|æ)<\/sp>/g,'ǽ').replace(/<sp>'?(oe|œ)<\/sp>/g,'œ')
    .replace(/(\s\^?\*\^?)(?=\s*[^(])/g,' *()')
    .replace(/(\))\s*\(\)/g,')')
    .replace(/(^|[^^])†(?!\^)/gm,'$1^†^')                          // toda cruz (†), en rojo
    .replace(/\u0001/g,'**');
}
function gabcCuerpo(g){ const i=g.indexOf('%%'); return i>=0? g.slice(i+2).replace(/^\s*\n/,'') : g; }
function espaciarSilabas(maps){
  const ns=[]; maps.forEach(m=>(m.notations||[]).forEach(n=>ns.push(n)));
  const chica=n=>(exsurge.QuarterBar&&n instanceof exsurge.QuarterBar)||(exsurge.Virgula&&n instanceof exsurge.Virgula);
  ns.forEach((n,i)=>{
    if(!n.isDivider) return;
    const f=chica(n)?ESP_PAUSA_CHICA:ESP_PAUSA, pausa=c=>c.intraNeumeSpacing*f;
    if(n.trailingSpace && n.trailingSpace.isDefault) n.trailingSpace=pausa;
    for(let k=i-1;k>=0;k--){ const a=ns[k]; if(a.isNeume||a.isDivider){ if(a.trailingSpace&&a.trailingSpace.isDefault) a.trailingSpace=pausa; break; } if(a.hasLyrics&&a.hasLyrics()) break; }
  });
}
function gabcModo(g){ const m=g.match(/^mode:\s*([1-8])/m); return m? +m[1] : 0; }
function fuentesListas(){ if(!_fuentes) _fuentes=(document.fonts&&document.fonts.load? Promise.all([document.fonts.load("400 20px 'Source Serif 4'"),document.fonts.load("italic 400 20px 'Source Serif 4'"),document.fonts.load("20px 'Cantoral Signos'","*℣℟")]).catch(()=>{}) : Promise.resolve()).then(()=>new Promise(r=>setTimeout(r,0))); return _fuentes; }
function uniformarRenglones(svg){
  if(!svg) return; const L=[...svg.querySelectorAll("g.chantLine")]; if(L.length<2) return;
  const inf=L.map(g=>{ const m=(g.getAttribute("transform")||"").match(/translate\(([-\d.e]+),([-\d.e]+)\)/); let bb; try{ bb=g.getBBox(); }catch(e){ return null; }
    return {g,x:m?+m[1]:0,y:m?+m[2]:0,top:bb.y,bot:bb.y+bb.height}; });
  if(inf.some(i=>!i)) return;
  const maxBot=Math.max(...inf.map(i=>i.bot)), minTop=Math.min(...inf.slice(1).map(i=>i.top));
  const paso=maxBot-minTop+20; let y=inf[0].y;
  inf.forEach((it,k)=>{ if(k) y+=paso; it.g.setAttribute("transform",`translate(${it.x},${y})`); });
  const vb=svg.viewBox&&svg.viewBox.baseVal; if(vb) svg.setAttribute("viewBox",`${vb.x} ${vb.y} ${vb.width} ${y+maxBot+10}`);
}
function ajustarTraducciones(svg){
  if(!svg || !svg.viewBox || !svg.viewBox.baseVal) return;
  const vb=svg.viewBox.baseVal, cr=svg.getBoundingClientRect(); if(!cr.width) return;
  const k=vb.width/cr.width;
  const ts=[...svg.querySelectorAll("text.translation")].filter(t=>t.textContent.trim());
  if(!ts.length) return;
  // Cada traducción empieza justo debajo de la palabra latina (sin el número de estrofa ni ℣/℟)
  ts.forEach(t=>{ const l=t.parentElement && t.parentElement.querySelector("text.lyric"); if(!l) return;
    let x=+l.getAttribute("x")||0; const s=l.textContent, pre=(s.match(/^\s*(?:\d+\.|[℣℟]\.?|\*|[VR]\/\.?)?\s*/)||[""])[0];
    if(pre.length && pre.length<s.length){ try{ x+=l.getSubStringLength(0,pre.length); }catch(e){} }
    t.setAttribute("x",x); t.removeAttribute("transform"); });
  const mover=(t,dx,dy)=>{ const m=(t.getAttribute("transform")||"").match(/translate\(([-\d.e]+),([-\d.e]+)\)/); t.setAttribute("transform",`translate(${(m?+m[1]:0)+dx},${(m?+m[2]:0)+dy})`); };
  const filasL=[...new Set([...svg.querySelectorAll("text.lyric")].map(t=>Math.round(t.getBoundingClientRect().top)))].sort((a,b)=>a-b);
  for(let pasada=0;pasada<2;pasada++){
    const lineasY=[...new Set(ts.map(t=>Math.round(t.getBoundingClientRect().top)))].sort((a,b)=>a-b).filter((y,i,a)=>!i||y-a[i-1]>4);
    const porLinea=new Map();
    ts.forEach(t=>{ const y=Math.round(t.getBoundingClientRect().top); const key=lineasY.reduce((a,b)=>Math.abs(b-y)<Math.abs(a-y)?b:a,lineasY[0]); if(!porLinea.has(key)) porLinea.set(key,[]); porLinea.get(key).push(t); });
    let movida=false;
    [...porLinea.keys()].sort((a,b)=>a-b).forEach(y=>{
      const xs=porLinea.get(y).sort((a,b)=>a.getBoundingClientRect().left-b.getBoundingClientRect().left);
      let fin=-Infinity;
      xs.forEach(t=>{ const r=t.getBoundingClientRect(); if(r.left<fin+8) mover(t,(fin+8-r.left)*k,0); fin=t.getBoundingClientRect().right; });
      const ult=xs[xs.length-1], r=ult.getBoundingClientRect();
      if(r.right>cr.right+2){
        const propia=filasL.filter(f=>f<y).pop(), sigL=filasL.find(f=>f>y);
        if(pasada===0 && sigL!==undefined && propia!==undefined && xs.length>1 && r.left>cr.left+cr.width*0.55){ mover(ult,(cr.left+2-r.left)*k,(sigL-propia)*k); movida=true; }
        else { const base=xs[0].getBoundingClientRect().left, esc=Math.max(.72,(cr.right-base)/(r.right-base));
          xs.forEach(t=>{ const tr=t.getBoundingClientRect(); t.style.fontSize=(esc*100)+"%"; mover(t,-(tr.left-base)*(1-esc)*k,0); }); }
      }
    });
    if(!movida) break;
  }
}
function normPal(s){ return String(s).replace(/<[^>]+>/g,"").replace(/[{}]/g,"").normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase().replace(/æ/g,"ae").replace(/œ/g,"oe").replace(/[^a-z]/g,""); }
function insertarTraduccion(gabc, pares){
  const i=gabc.indexOf("%%"); const cab=i>=0?gabc.slice(0,i+2):"", cuerpo=i>=0?gabc.slice(i+2):gabc;
  const re=/([^()]*)\(([^)]*)\)/g; const pal=[]; let cur=null, m;
  while((m=re.exec(cuerpo))){
    const fin=m.index+m[1].length;
    let t=m[1].replace(/\[[^\]]*\]/g,"").replace(/<alt>.*?<\/alt>/g,"").replace(/<[^>]+>/g,"").replace(/~/g," ");
    t.split(/(\s+)/).forEach(tr=>{ if(!tr) return; if(/^\s+$/.test(tr)){cur=null;return;} const l=normPal(tr); if(!l) return;
      if(!cur){ cur={txt:l,fin}; pal.push(cur); } else cur.txt+=l; });
    if(/\s$/.test(t)) cur=null;
  }
  const ins=[]; let p=0;
  const igual=(a,w)=>a&&(a.txt===w||a.txt.startsWith(w));
  pares.forEach(([lat,es])=>{ const ws=String(lat).trim().split(/\s+/).map(normPal).filter(Boolean), w=ws[0], w2=ws[1]; es=String(es||"").trim(); if(!w||!es) return;
    let q=-1;
    if(w2) for(let k=p;k<pal.length;k++){ if(igual(pal[k],w)&&igual(pal[k+1],w2)){ q=k; break; } }
    if(q<0) for(let k=p;k<pal.length;k++){ if(igual(pal[k],w)){ q=k; break; } }
    if(q>=0){ ins.push([pal[q].fin,es]); p=q+Math.max(1,ws.length); } });
  let out=cuerpo; ins.sort((a,b)=>b[0]-a[0]).forEach(([pos,t])=>{ if(!/\s/.test(t)) t+=" "; out=out.slice(0,pos)+"["+t.replace(/\[/g,"\u27E6").replace(/\]/g,"\u27E7")+"]"+out.slice(pos); });
  // reserva el renglón de traducción en todas las sílabas, para que el espacio sea parejo
  out=out.replace(/([^()]*)\(/g,(mm,t)=> (/[A-Za-zÀ-ÿæœǽ]/.test(t.replace(/<[^>]*>/g,"")) && !/\]\s*$/.test(t)) ? t+"[   ](" : mm);
  return cab+out;
}
