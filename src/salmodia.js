/* Salmodia: silabeo, acentos y pautado de salmos en tonos gregorianos (latín y español).
   Tonos tomados de jgabc (B. Bloomfield, dominio público). */
(function(root){
"use strict";

/* ---------- Tonos ---------- */
// ' marca la nota del acento; r marca nota de recitación (cuerda) que absorbe sílabas.
const TONOS={
 '1':{clef:'c4',med:"f gh hr 'ixi hr 'g hr h.",ter:{'D':"hr g f 'gh gr gvFED.",'D2':"hr g f gr 'gf d.",'f':"hr g f 'gh gr gf..",'g':"hr g f 'gh gr g.",'g2':"hr g f 'g gr ghg.",'g3':"hr g f 'g gr g.",'a':"hr g f 'g hr h.",'a2':"hr g f 'g gr gh..",'a3':"hr g f 'gh gr gh.."}},
 '2':{clef:'f3',med:"e f hr 'i hr h.",ter:{'D':"hr g 'e fr f."}},
 '3':{clef:'c4',med:"g hj jr 'k jr jr 'ih j.",ter:{'b':"jr h 'j jr i.",'a':"jr h 'j jr ih..",'a2':"jr ji hi 'h gr gh..",'g':"jr ji hi 'h gr g.",'g2':"jr h j i 'h gr g."}},
 '4':{clef:'c4',med:"h gh hr g h 'i hr h.",ter:{'g':"hr 'h gr g.",'E':"hr g h ih gr 'gf e."}},
 '4alt':{clef:'c3',med:"i hi ir h i 'j ir i.",ter:{'c':"ir 'i hr h.",'A':"ir h i j 'h fr f.",'d':"ir h i j 'h ir i."}},
 '5':{clef:'c3',med:"d f hr 'i hr h.",ter:{'a':"hr 'i gr 'h fr f."}},
 '6':{clef:'c4',med:"f gh hr 'ixi hr 'g hr h.",ter:{'F':"hr f gh 'g fr f."}},
 '7':{clef:'c3',med:"hg hi ir 'k jr 'i jr j.",ter:{'a':"ir 'j ir 'h hr gf..",'b':"ir 'j ir 'h hr g.",'c':"ir 'j ir 'h hr gh..",'c2':"ir 'j ir 'h hr ih..",'d':"ir 'j ir 'h hr gi.."}},
 '8':{clef:'c4',med:"g h jr 'k jr j.",ter:{'G':"jr i j 'h gr g.",'G*':"jr i j 'h gr gh..",'c':"jr h j 'k jr j."}},
 'per':{clef:'c4',med:"ixhi hr g ixi h 'g fr f.",ter:{'':"gr d 'f fr ed.."}}
};
const NOMBRE_TONO={'1':'1','2':'2','3':'3','4':'4','4alt':'4 alt.','5':'5','6':'6','7':'7','8':'8','per':'peregrino'};
const ROMANO=['','I','II','III','IV','V','VI','VII','VIII'];

function partes(cod){ // "8G" -> {tono:'8', fin:'G'}
  cod=String(cod||'').replace(/\s|\./g,'');
  if(/^per/i.test(cod)) return {tono:'per',fin:''};
  const m=cod.match(/^(4alt|[1-8])(.*)$/); if(!m) return null;
  let t=m[1], f=m[2]||'';
  const def=TONOS[t]; if(!def) return null;
  if(!(f in def.ter)){ const k=Object.keys(def.ter).find(k=>k.toLowerCase()===f.toLowerCase()); f=k!==undefined?k:Object.keys(def.ter)[0]; }
  return {tono:t,fin:f};
}
function etiquetaTono(cod){ const p=partes(cod); if(!p) return ''; return (p.tono==='per'?'Tono peregrino':'Tono '+NOMBRE_TONO[p.tono])+(p.fin?' '+p.fin:''); }

function parseParte(s){
  const toks=s.trim().split(/\s+/).map(x=>{ const acc=x[0]==="'"; if(acc) x=x.slice(1); const rep=/r$/.test(x); if(rep) x=x.slice(0,-1); return {n:x,acc,rep}; });
  const iT=toks.findIndex(t=>t.rep);
  return {inton:toks.slice(0,iT).map(t=>t.n), tenor:toks[iT].n, cad:toks.slice(iT+1)};
}
function tono(cod){
  const p=partes(cod); if(!p) return null; const d=TONOS[p.tono];
  const med=parseParte(d.med), ter=parseParte(d.ter[p.fin]);
  const notaBase=x=>x.replace(/[^a-m]/g,'').slice(-1)||x;
  return {cod:p.tono+p.fin, clef:d.clef, med, ter, tenor:med.tenor, flex:flexDe(med.tenor, d.clef)};
}
function flexDe(tenor, clef){ // la flexa baja un tono (o semitono hasta la nota inferior)
  const L='abcdefghijklm'; const i=L.indexOf(tenor[tenor.length-1]);
  return L[Math.max(0,i-1)];
}

/* ---------- Silabeo latino ---------- */
const VOC_LA='aeiouyáéíóúýæœǽëäöü';
const ACENTO_LA=/[áéíóúýǽ]/;
const esVocLa=c=>VOC_LA.includes(c);
function silabasLatin(pal){
  const w=pal, low=w.toLowerCase();
  const n=low.length; const tipo=[]; // V o C por posición
  for(let i=0;i<n;i++){
    const c=low[i];
    if(!/[a-zæœǽáéíóúýëäöü]/.test(c)){ tipo.push('X'); continue; }
    if(c==='j'){ tipo.push('C'); continue; }
    if(c==='u' && i>0 && (low[i-1]==='q' || (low[i-1]==='g' && i>1 && low[i-2]==='n')) && i+1<n && esVocLa(low[i+1])){ tipo.push('C'); continue; }
    if(c==='i'||c==='í'){
      const prev=i>0?low[i-1]:'', next=i+1<n?low[i+1]:'';
      const ini=(i===0 || !/[a-zæœǽáéíóúý]/.test(prev));
      if(ini && next && esVocLa(next) && c==='i'){ tipo.push('C'); continue; }        // Iesus, iam, iustitia
      if(c==='i' && tipo[i-1]==='V' && next && esVocLa(next)){ tipo.push('C'); continue; } // eius, maior
      if(c==='i' && next && esVocLa(next) && /^(ad|ab|ob|sub|in|con|dis|per)$/.test(low.slice(0,i).replace(/[áéíóú]/g,m=>'aeiou'['áéíóú'.indexOf(m)]))){ tipo.push('C'); continue; } // ad-iu-va, in-iu-stus, con-iu-gi-um
    }
    tipo.push(esVocLa(c)?'V':'C');
  }
  // núcleos: agrupar diptongos
  const nucleos=[]; let i=0;
  while(i<n){
    if(tipo[i]==='V'){
      let j=i+1; const a=low[i], b=low[j]||'';
      if(tipo[j]==='V' && ((a==='a'&&b==='u')||(a==='á'&&b==='u')||(a==='a'&&b==='ú')||(a==='e'&&b==='u'&&i===0))) j++;
      nucleos.push([i,j]); i=j;
    } else i++;
  }
  if(!nucleos.length) return [{t:w,acc:0}];
  const cortes=[];
  for(let k=0;k<nucleos.length-1;k++){
    const fin=nucleos[k][1], ini=nucleos[k+1][0];
    const cons=[]; for(let p=fin;p<ini;p++) if(tipo[p]==='C') cons.push(p);
    const s=low.slice(fin,ini).replace(/[^a-z]/g,'');
    let corte;
    // qu y gu consonántica forman una sola consonante con la q/g
    if(cons.length>=2 && low[cons[cons.length-1]]==='u' && /[qg]/.test(low[cons[cons.length-2]])){ const u=cons.pop(); }
    if(cons.length===0) corte=ini;
    else if(cons.length===1){ corte = low[cons[0]]==='x' ? cons[0]+1 : cons[0]; }
    else {
      // pares que no se separan: muda + líquida, ch, ph, th, qu, gu
      const last2=low[cons[cons.length-2]]+low[cons[cons.length-1]];
      if(/^([bcdgptf][lr]|ch|ph|th|rh)$/.test(last2) && !(last2[1]==='h' && false)) corte=cons[cons.length-2];
      else if(low[cons[cons.length-1]]==='h' && cons.length>=2) corte=cons[cons.length-2];
      else corte=cons[cons.length-1];
      if(low[cons[0]]==='x') corte=cons[0]+1;
    }
    cortes.push(corte);
  }
  const sil=[]; let ant=0; cortes.forEach(c=>{ sil.push(w.slice(ant,c)); ant=c; }); sil.push(w.slice(ant));
  // acento
  let acc=sil.findIndex(s=>ACENTO_LA.test(s));
  const nS=sil.filter(s=>/[a-zæœǽáéíóúýëäöü]/i.test(s)).length;
  if(acc<0){ if(sil.length===2) acc=0; else if(sil.length>=3) acc=sil.length-2; }
  return sil.map((t,k)=>({t,acc:k===acc&&sil.length>1?1:0}));
}

/* ---------- Silabeo español ---------- */
const VOC_ES='aeiouáéíóúü';
const FUERTE=/[aeoáéóíú]/;
const INSEP=/^(bl|br|cl|cr|dr|fl|fr|gl|gr|kl|kr|pl|pr|tr|tl)$/;
const ATONOS=new Set(['el','la','lo','los','las','le','les','un','de','del','a','al','en','con','por','sin','so','tras','y','e','o','u','ni','que','si','me','te','se','nos','os','mi','mis','tu','tus','su','sus','cual','como','pues','mas']);
function silabasEspanol(pal){
  const w=pal, low=w.toLowerCase(); const n=low.length;
  const tipo=[];
  for(let i=0;i<n;i++){
    const c=low[i];
    if(!/[a-zñáéíóúü]/.test(c)){ tipo.push('X'); continue; }
    if(c==='u' && i>0 && (low[i-1]==='q'||low[i-1]==='g') && /[eiéí]/.test(low[i+1]||'')){ tipo.push('C'); continue; } // que, gui
    if(c==='y'){ const fin=(i===n-1)||!/[a-zñáéíóúü]/.test(low[i+1]||''); tipo.push(fin && i>0 ? 'V' : (n===1?'V':'C')); continue; }
    tipo.push(VOC_ES.includes(c)?'V':'C');
  }
  const debil=c=>/[iuüy]/.test(c);
  const nucleos=[]; let i=0;
  while(i<n){
    if(tipo[i]==='V'){
      let j=i+1;
      while(j<n && tipo[j]==='V'){ const a=low[j-1], b=low[j]; if(debil(a)||debil(b)) j++; else break; }
      // la h intercalada no rompe el diptongo: se ignora
      nucleos.push([i,j]); i=j;
    } else i++;
  }
  if(!nucleos.length) return [{t:w,acc:0}];
  const cortes=[];
  for(let k=0;k<nucleos.length-1;k++){
    const fin=nucleos[k][1], ini=nucleos[k+1][0];
    let cons=[]; for(let p=fin;p<ini;p++) if(tipo[p]==='C') cons.push(p);
    // dígrafos ch, ll, rr cuentan como una consonante
    const unid=[]; for(let q=0;q<cons.length;q++){ const a=low[cons[q]], b=low[cons[q+1]]; if(q+1<cons.length && ((a==='c'&&b==='h')||(a==='l'&&b==='l')||(a==='r'&&b==='r'))){ unid.push([cons[q],a+b]); q++; } else unid.push([cons[q],a]); }
    let corte;
    if(unid.length===0) corte=ini;
    else if(unid.length===1) corte=unid[0][0];
    else if(unid.length===2) corte= INSEP.test(unid[0][1]+unid[1][1]) ? unid[0][0] : unid[1][0];
    else if(unid.length===3) corte= INSEP.test(unid[1][1]+unid[2][1]) ? unid[1][0] : unid[2][0];
    else corte=unid[2][0];
    cortes.push(corte);
  }
  const sil=[]; let ant=0; cortes.forEach(c=>{ sil.push(w.slice(ant,c)); ant=c; }); sil.push(w.slice(ant));
  let acc=sil.findIndex(s=>/[áéíóú]/i.test(s));
  if(acc<0){
    const letras=low.replace(/[^a-zñáéíóúü]/g,'');
    if(sil.length===1) acc= ATONOS.has(letras)? -1 : 0;
    else acc= /[aeiouns]$/.test(letras) ? sil.length-2 : sil.length-1;
  }
  return sil.map((t,k)=>({t,acc:k===acc?1:0}));
}

/* ---------- Texto a palabras/sílabas ---------- */
function palabras(texto, lang){
  const out=[];
  const re=/(\S+)/g; let m;
  while((m=re.exec(texto))){
    const tok=m[1];
    const mm=tok.match(/^([^A-Za-zÀ-ÿæœǽÆŒ]*)([A-Za-zÀ-ÿæœǽÆŒ'’]+(?:-[A-Za-zÀ-ÿæœǽ]+)*)?(.*)$/);
    if(!mm || !mm[2]){ if(out.length) out[out.length-1].post+=' '+tok; else out.push({pre:tok,sil:[],post:''}); continue; }
    const sil=(lang==='es'?silabasEspanol:silabasLatin)(mm[2]);
    out.push({pre:mm[1],sil,post:mm[3]});
  }
  // acentos secundarios (para tonos de dos acentos)
  out.forEach(p=>{ const a=p.sil.findIndex(s=>s.acc===1); if(a>=2) for(let k=a-2;k>=0;k-=2) p.sil[k].acc2=1; });
  return out;
}
// Lista plana de sílabas con referencia a su palabra
function plano(pals){
  const s=[]; pals.forEach((p,iw)=>p.sil.forEach((x,k)=>s.push({t:x.t,acc:x.acc,acc2:x.acc2||0,iw,k,ult:k===p.sil.length-1,mono:p.sil.length===1})));
  return s;
}

/* ---------- Pautado ---------- */
// Asigna notas a las sílabas de un hemistiquio. Devuelve [{nota, rol}] alineado con las sílabas.
function puntear(sils, parte, intonar, lat){
  const n=sils.length; const res=new Array(n).fill(null);
  // acento efectivo: monosílabo final -> el acento pasa a la sílaba anterior
  const acc=sils.map(s=>s.acc===1);
  // Latín: monosílabo final. Si la palabra anterior es esdrújula o monosílaba, el acento pasa a la sílaba anterior
  if(lat && n>=2 && sils[n-1].mono){
    const prev=sils[n-2];
    if(prev.mono){ acc[n-2]=true; }
    else if(prev.ult && prev.k>=2 && sils[n-2-2] && sils[n-2-2].acc===1 && sils[n-2-2].iw===prev.iw){ acc[n-4]=false; acc[n-2]=true; }
  }
  const acc2=sils.map((s,i)=>acc[i]||s.acc2===1);
  let pos=n-1; let ultimoRep=null; let primerAcento=true;
  const cad=parte.cad;
  for(let t=cad.length-1;t>=0;t--){
    const tk=cad[t];
    if(tk.rep){ ultimoRep=tk; continue; }
    if(tk.acc){
      let q=pos; const ok=primerAcento?acc:acc2;
      while(q>=0 && !ok[q]) q--;
      if(q<0){ q=pos; }
      // sílabas entre el acento y lo ya asignado: van a la nota de relleno posterior
      for(let r=q+1;r<=pos;r++) res[r]={nota:ultimoRep?ultimoRep.n:tk.n.replace(/[^a-m]/g,'').slice(-1), rol:'post'};
      if(q===pos && pos===n-1 && t===cad.length-1){ /* acento en la última sílaba */ }
      res[q]={nota:tk.n, rol:'acc'}; pos=q-1; ultimoRep=null; primerAcento=false;
    } else {
      if(pos<0) break;
      // nota final sin sílaba propia (aguda): se une a la sílaba acentuada anterior
      res[pos]={nota:tk.n, rol: t===cad.length-1?'fin':'prep'}; pos--;
    }
  }
  // Agudas: si la última nota cayó en una sílaba acentuada y la siguiente nota de acento quedó antes, se corrige
  // Entonación y cuerda
  let ini=0;
  if(intonar){ parte.inton.forEach((nt,k)=>{ if(ini<=pos){ res[ini]={nota:nt,rol:'int'}; ini++; } }); }
  for(let k=ini;k<=pos;k++) res[k]={nota:parte.tenor,rol:'ten'};
  return res;
}
// Corrige agudas: si la sílaba final es acentuada y recibió la nota 'fin', le damos acento+final juntos
function corregirAgudas(sils, res, parte, lat){
  const n=sils.length; if(n<2) return res;
  const last=sils[n-1];
  if(last.acc===1 && (!last.mono || !lat)){
    // buscar la nota del último acento del tono y la final
    const cad=parte.cad; const fin=cad[cad.length-1]; let ia=-1; for(let t=cad.length-1;t>=0;t--) if(cad[t].acc){ ia=t; break; }
    if(ia<0) return res;
    // reasignar: rehacer el punteo considerando la última sílaba como acento + final
    const copia=sils.slice(0,n-1).concat([{...last}]);
    const fake=copia.concat([{t:'',acc:0,mono:false,fantasma:true}]);
    const r2=puntear(fake, parte, false, lat);
    const fn=r2.pop();
    r2[n-1]={nota:limpiaNota(r2[n-1].nota)+limpiaNota(fn.nota), rol:'acc'};
    // conservar entonación si la había
    for(let k=0;k<n;k++) if(res[k] && res[k].rol==='int') r2[k]=res[k];
    return r2;
  }
  return res;
}
function limpiaNota(x){ return String(x).replace(/\.+$/,''); }

/* Divide un verso en hemistiquios por † y * */
function dividirVerso(v){
  const flexI=v.indexOf('†'), medI=v.indexOf('*');
  let flex=null, a, b;
  if(medI<0) return {flex:null, med:v.replace(/[†*]/g,'').trim(), ter:null};
  if(flexI>=0 && flexI<medI){ flex=v.slice(0,flexI).trim(); a=v.slice(flexI+1,medI).trim(); }
  else a=v.slice(0,medI).trim();
  b=v.slice(medI+1).replace(/†/g,'').trim();
  return {flex, med:a, ter:b};
}

/* Pautar un verso completo: devuelve estructura con sílabas y notas por hemistiquio */
function pautarVerso(verso, cod, lang, intonar){
  const T=tono(cod); if(!T) return null;
  const d=dividirVerso(verso);
  const hemi=(txt, parte, into, esFlex)=>{
    if(txt==null) return null;
    const pals=palabras(txt.replace(/\+/g,'').trim(), lang); const s=plano(pals);
    let res;
    if(esFlex){
      // flexa: cuerda ... 'cuerda flexa
      const P={inton:[],tenor:T.tenor,cad:[{n:T.tenor,acc:true,rep:false},{n:T.flex,acc:false,rep:true},{n:T.flex+'.',acc:false,rep:false}]};
      res=puntear(s,P,false,lang!=='es'); res=corregirAgudas(s,res,P,lang!=='es');
    } else { res=puntear(s,parte,into,lang!=='es'); res=corregirAgudas(s,res,parte,lang!=='es'); }
    return {pals, sils:s, res};
  };
  return {
    tono:T,
    flex: d.flex!=null? hemi(d.flex,null,false,true):null,
    med: d.ter!=null? hemi(d.med, T.med, intonar && d.flex==null) : null,
    ter: d.ter!=null? hemi(d.ter, T.ter, false) : hemi(d.med, T.ter, false),
    intonFlex: intonar && d.flex!=null
  };
}

/* HTML del texto pautado: acento en negrita, preparatorias en cursiva */
function esc(s){ return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function htmlHemi(h){
  if(!h) return '';
  let out=''; let k=0;
  h.pals.forEach((p,iw)=>{
    out+=esc(p.pre);
    p.sil.forEach(sy=>{ const r=h.res[k++]||{rol:'ten'}; let t=esc(sy.t);
      if(r.rol==='acc') t='<b>'+t+'</b>'; else if(r.rol==='prep') t='<i>'+t+'</i>'; else if(r.rol==='int') t='<u>'+t+'</u>';
      out+=t; });
    out+=esc(p.post); if(iw<h.pals.length-1) out+=' ';
  });
  return out;
}
function htmlVerso(pv){
  if(!pv) return '';
  let s='';
  if(pv.flex) s+=htmlHemi(pv.flex)+'&nbsp;<span class="sg fx">†</span><br>';
  if(pv.med) s+=htmlHemi(pv.med)+'&nbsp;<span class="sg md">*</span><br>';
  s+=htmlHemi(pv.ter);
  return s;
}

/* GABC de un verso (para dibujar la partitura) */
function gabcHemi(h, sepFinal){
  let out=''; let k=0;
  h.pals.forEach((p,iw)=>{
    p.sil.forEach((sy,j)=>{
      const r=h.res[k++]||{nota:'h'};
      let txt=(j===0?p.pre:'')+sy.t+(j===p.sil.length-1?p.post:'');
      txt=txt.replace(/[()\[\]{}]/g,'');
      if(r.rol==='acc') txt='<b>'+txt+'</b>'; else if(r.rol==='prep') txt='<i>'+txt+'</i>';
      let nota=String(r.nota).replace(/r$/,'');
      out+=txt+'('+nota+')';
    });
    out+=' ';
  });
  return out.trim();
}
function gabcVerso(pv, num){
  if(!pv) return '';
  let s='';
  if(pv.flex) s+=gabcHemi(pv.flex)+' †(,) ';
  if(pv.med) s+=gabcHemi(pv.med)+' *(:) ';
  s+=gabcHemi(pv.ter)+' (::)';
  return s;
}
function gabcSalmo(versos, cod, lang, todos){
  const T=tono(cod); if(!T) return '';
  let g='('+T.clef+') ';
  const lista=todos?versos:versos.slice(0,1);
  lista.forEach((v,i)=>{ const pv=pautarVerso(v,cod,lang,i===0); g+=(i?' ':'')+gabcVerso(pv); });
  return g;
}

const API={TONOS,ROMANO,partes,tono,etiquetaTono,silabasLatin,silabasEspanol,palabras,plano,puntear,pautarVerso,htmlVerso,gabcSalmo,dividirVerso,listaTonos};
function listaTonos(){ const l=[]; Object.keys(TONOS).forEach(t=>Object.keys(TONOS[t].ter).forEach(f=>l.push({cod:t+f, et:etiquetaTono(t+f)}))); return l; }
if(typeof module!=='undefined') module.exports=API; else root.Salmodia=API;
})(this);
