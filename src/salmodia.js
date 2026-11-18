/* Salmodia: silabeo, acentos y pautado de salmos y cánticos en tonos gregorianos (español y latín).
   Tonos tomados de jgabc (B. Bloomfield). Reglas de acentuación de CRU (docs/salmodia.md):
   - Cada sílaba es F (fuerte: la acentuada de su palabra), D (débil: pegada a una fuerte) o N (neutra).
   - Se mira desde el final. El acento va en la penúltima o en la antepenúltima; nunca más atrás; en la última,
     solo si no se puede en otra. No se acentúa una débil. Período de 2 a 3 sílabas por acento.
   - …fd: normal. …fdf y …ndf: en la antepenúltima. …ddf: en la última (aguda suave).
   - Sin sinalefa: cada sílaba lleva su nota. No se juntan en una sílaba notas que irían en sílabas distintas
     (con acento en la última, se omiten las notas que seguían al acento). */
(function(root){
"use strict";

/* ---------- Tonos ---------- */
// ' marca la nota del acento; r, la nota de recitación (cuerda) o la de relleno que absorbe sílabas.
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
function etiquetaTono(cod){ const p=partes(cod); if(!p) return ''; return (p.tono==='per'?'Tono peregrino':'Modo '+NOMBRE_TONO[p.tono])+(p.fin?' '+p.fin:''); }
function etiquetaCorta(cod){ const p=partes(cod); if(!p) return ''; return p.tono==='per'?'Peregrino':NOMBRE_TONO[p.tono]+(p.fin?' '+p.fin:''); }

// Una mitad del tono: entonación, cuerda y cadencia. La cadencia queda en grupos de acento:
// prep (preparatorias antes del primer acento) y, por cada acento, su nota, la de relleno (rep) y las fijas que siguen.
function parseParte(s){
  const toks=s.trim().split(/\s+/).map(x=>{ const acc=x[0]==="'"; if(acc) x=x.slice(1); const rep=/r$/.test(x); if(rep) x=x.slice(0,-1); return {n:x,acc,rep}; });
  const iT=toks.findIndex(t=>t.rep);
  const E={inton:toks.slice(0,iT).map(t=>t.n), tenor:toks[iT].n, prep:[], acc:[]};
  let cur=null;
  for(const t of toks.slice(iT+1)){
    if(t.acc){ cur={n:t.n, rep:null, fijas:[]}; E.acc.push(cur); }
    else if(!cur) E.prep.push(t.n);
    else if(t.rep){ if(cur.rep==null) cur.rep=t.n; }   // (tono 3: dos notas de relleno iguales entre los acentos)
    else cur.fijas.push(t.n);
  }
  return E;
}
// La flexa baja un grado desde la cuerda; si ese grado es de semitono (desde do o desde fa), baja una tercera menor.
function flexDe(tenor, clef){
  const L='abcdefghijklm', i=L.indexOf(tenor[tenor.length-1]);
  const linea=+clef[1], base=L.indexOf('dfhj'[linea-1]);   // letra de la línea de la clave
  const ESC=clef[0]==='c'?['do','re','mi','fa','sol','la','si']:['fa','sol','la','si','do','re','mi'];
  const nombre=ESC[((i-base)%7+7)%7];
  return L[Math.max(0, i-((nombre==='do'||nombre==='fa')?2:1))];
}
function tono(cod){
  const p=partes(cod); if(!p) return null; const d=TONOS[p.tono];
  const med=parseParte(d.med), ter=parseParte(d.ter[p.fin]);
  const flex=flexDe(med.tenor, d.clef);
  return {cod:p.tono+p.fin, clef:d.clef, med, ter, tenor:med.tenor, flex,
          flexa:{inton:[], tenor:med.tenor, prep:[], acc:[{n:med.tenor, rep:flex, fijas:[flex]}]}};
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
const INSEP=/^(bl|br|cl|cr|dr|fl|fr|gl|gr|kl|kr|pl|pr|tr|tl)$/;
// Monosílabos átonos (artículos, preposiciones, conjunciones, pronombres átonos, posesivos antepuestos).
// Las palabras de dos o más sílabas llevan siempre su acento («pa-» de «para» es fuerte).
const ATONOS=new Set(['el','la','lo','los','las','le','les','un','de','del','a','al','en','con','por','sin','so','tras','y','e','o','u','ni','que','si','me','te','se','nos','os','mi','mis','tu','tus','su','sus','cual','quien','cuan','pues','mas','aun','san']);
// Palabras que se dividen distinto de lo que da la regla. «Sión» es aguda de dos sílabas (Si-ón), y «guió», gui-ó;
// en cambio «dió» (grafía antigua) es una sola sílaba, así que no hay una regla general para la tilde en el diptongo.
const EXCEPCIONES={'sión':{cortes:[2],acc:1}, 'sion':{cortes:[2],acc:1}, 'guió':{cortes:[3],acc:1}, 'guio':{cortes:[3],acc:1}};
function silabasEspanol(pal){
  const w=pal, low=w.toLowerCase(); const n=low.length;
  const exc=EXCEPCIONES[low];
  if(exc){ const sil=[]; let a=0; exc.cortes.concat([n]).forEach(c=>{ sil.push(w.slice(a,c)); a=c; }); return sil.map((t,k)=>({t,acc:k===exc.acc?1:0})); }
  const esVoc=c=>VOC_ES.includes(c)||c==='y';
  const tipo=[];
  for(let i=0;i<n;i++){
    const c=low[i], prev=low[i-1]||'', next=low[i+1]||'';
    if(!/[a-zñáéíóúü]/.test(c)){ tipo.push('X'); continue; }
    if(c==='u' && (prev==='q'||prev==='g') && /[eiéí]/.test(next)){ tipo.push('C'); continue; }   // que, qui, gue, gui: la u no suena
    if(c==='y'){ tipo.push(VOC_ES.includes(next)?'C':'V'); continue; }                            // ya, rayo / rey, y
    if(c==='i' && tipo[i-1]==='V' && VOC_ES.includes(next)){ tipo.push('C'); continue; }          // Aleluia: a-le-lu-ia
    tipo.push(VOC_ES.includes(c)?'V':'C');
  }
  const debil=c=>/[iuüy]/.test(c);
  const nucleos=[]; let i=0;
  while(i<n){
    if(tipo[i]==='V'){
      let j=i+1;
      while(j<n && tipo[j]==='V'){ const a=low[j-1], b=low[j]; if(debil(a)||debil(b)) j++; else break; }   // diptongo; hiato entre fuertes o con débil acentuada
      nucleos.push([i,j]); i=j;
    } else i++;
  }
  if(!nucleos.length) return [{t:w,acc:0}];
  const cortes=[];
  for(let k=0;k<nucleos.length-1;k++){
    const fin=nucleos[k][1], ini=nucleos[k+1][0];
    const cons=[]; for(let p=fin;p<ini;p++) if(tipo[p]==='C') cons.push(p);
    // unidades: ch, ll, rr, qu, gu (con u muda) cuentan como una consonante
    const unid=[];
    for(let q=0;q<cons.length;q++){
      const a=low[cons[q]], b=low[cons[q+1]];
      if(q+1<cons.length && cons[q+1]===cons[q]+1 && ((a==='c'&&b==='h')||(a==='l'&&b==='l')||(a==='r'&&b==='r')||((a==='q'||a==='g')&&b==='u'))){ unid.push([cons[q],a+b]); q++; }
      else unid.push([cons[q],a]);
    }
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
    else acc= /[aeiouns]$/.test(letras) ? sil.length-2 : sil.length-1;   // llana si termina en vocal, n o s; si no, aguda
  }
  return sil.map((t,k)=>({t,acc:k===acc?1:0}));
}
// Monosílabos latinos átonos (preposiciones, conjunciones, relativos, pronombres enclíticos)
const ATONOS_LA=new Set(['et','in','ad','ab','a','e','ex','de','cum','per','pro','sub','ob','qui','quæ','quod','ut','ne','nec','sed','si','me','te','se','nos','vos','mi','est']);

/* ---------- Texto a palabras y sílabas ---------- */
// « ¶ » dentro de una mitad: el renglón sigue aparte (dos renglones en la misma mitad)
function palabras(texto, lang){
  const out=[]; let br=false;
  const re=/(\S+)/g; let m;
  while((m=re.exec(texto))){
    const tok=m[1];
    if(tok==='¶'){ br=true; continue; }
    const mm=tok.match(/^([^A-Za-zÀ-ÿæœǽÆŒ]*)([A-Za-zÀ-ÿæœǽÆŒ'’]+(?:-[A-Za-zÀ-ÿæœǽ]+)*)?(.*)$/);
    if(!mm || !mm[2]){ if(out.length) out[out.length-1].post+=' '+tok; else { out.push({pre:tok,sil:[],post:'',br}); br=false; } continue; }
    const sil=(lang==='es'?silabasEspanol:silabasLatin)(mm[2]);
    const mono=sil.length===1, w=mm[2].toLowerCase();
    sil.forEach(s=>{ s.f = s.acc===1 || (mono && lang!=='es' && !ATONOS_LA.has(w)); });
    const atona=!sil.some(s=>s.f); sil.forEach(s=>{ s.atona=atona; });   // palabra sin acento (artículo, preposición…)
    out.push({pre:mm[1],sil,post:mm[3],br}); br=false;
  }
  return out;
}
// Lista plana de sílabas con referencia a su palabra
function plano(pals){
  const s=[]; pals.forEach((p,iw)=>p.sil.forEach((x,k)=>s.push({t:x.t,f:!!x.f,atona:!!x.atona,iw,k,ult:k===p.sil.length-1,mono:p.sil.length===1})));
  return s;
}

/* ---------- Acentuación (reglas de CRU) ---------- */
// F: acentuada; D: inmediatamente antes o después de una acentuada; N: sin acento, en una palabra que lo tiene («ma-» de
// «majestad»). Las palabras átonas (artículos, preposiciones, posesivos: «de», «la», «mi») cuentan como débiles.
// (CONFIG.atonasDebiles=false: la lectura literal, en la que una átona lejos del acento es neutra; para comparar)
const CONFIG={atonasDebiles:true};
function clasificar(s){
  return s.map((x,i)=> x.f ? 'F' : ((CONFIG.atonasDebiles && x.atona) || (s[i-1]&&s[i-1].f) || (s[i+1]&&s[i+1].f)) ? 'D' : 'N');
}
// Último acento de la cadencia, mirando desde el final
function acentoFinal(t){
  const n=t.length; if(n===0) return {p:-1,regla:''}; if(n===1) return {p:0,regla:'f'};
  if(t[n-1]==='F'){
    if(t[n-2]==='F') return {p:n-2, regla:'ff'};
    if(n<3) return {p:n-1, regla:'df'};
    if(t[n-3]==='F') return {p:n-3, regla:'fdf'};   // esdrújula: «tendrás razón»
    if(t[n-3]==='N') return {p:n-3, regla:'ndf'};   // esdrújula suave: «sinceridad»
    return {p:n-1, regla:'ddf'};                    // aguda suave: «para juzgar»
  }
  if(t[n-2]==='F') return {p:n-2, regla:'fd'};      // normal: «con ira»
  if(n>=3 && t[n-3]==='F') return {p:n-3, regla:'f··'};   // esdrújula: «cánticos»
  // sin acentuada en las tres últimas: la penúltima o la antepenúltima que no sea débil
  if(t[n-2]!=='D') return {p:n-2, regla:'sin F'};
  if(n>=3 && t[n-3]!=='D') return {p:n-3, regla:'sin F'};
  return {p:n-2, regla:'sin F'};
}
// Acento anterior (tonos de dos acentos): a 2 o 3 sílabas del siguiente, mejor fuerte y si no neutra. Si las dos son débiles,
// antes que acentuar una débil se alarga el período: a 4 sílabas una fuerte o neutra («Gloria al Padre, y al Hijo»: Pa…Hi),
// a 5 una fuerte («la grandeza y el poder»: de…der); si tampoco, la débil.
function acentoPrevio(t, a){
  const c=[a-2,a-3].filter(i=>i>=0); if(!c.length) return -1;
  for(const k of ['F','N']) for(const i of c) if(t[i]===k) return i;
  if(a-4>=0 && t[a-4]!=='D') return a-4;
  if(a-5>=0 && t[a-5]==='F') return a-5;
  return c[0];
}

/* ---------- Pautado ---------- */
const nota0=x=>String(x).replace(/[^a-mA-M]/g,'').slice(-1).toLowerCase();
// Asigna notas a las sílabas de una mitad. E: parte del tono (parseParte). Devuelve {res:[{nota,rol}], regla}.
// rol: 'int' (entonación), 'ten' (cuerda), 'prep' (preparatoria), 'acc' (acento), 'post' (después del acento), 'fin'
function puntear(s, E, intonar, flexa){
  const n=s.length, res=new Array(n).fill(null); if(!n) return {res, regla:''};
  const t=clasificar(s);
  const ult=acentoFinal(t);
  const pos=new Array(E.acc.length).fill(-1);
  pos[E.acc.length-1]=ult.p;
  for(let k=E.acc.length-2;k>=0;k--) pos[k]= pos[k+1]>=0 ? acentoPrevio(t,pos[k+1]) : -1;
  let fin=n-1, primero=-1;
  for(let k=E.acc.length-1;k>=0;k--){
    const p=pos[k], A=E.acc[k]; if(p<0) break;
    const rep=A.rep!=null?A.rep:nota0(A.fijas[0]||A.n);
    const post=fin-p, nf=A.fijas.length, esUlt=k===E.acc.length-1;
    if(post>=nf){
      for(let j=0;j<nf;j++) res[fin-nf+1+j]={nota:A.fijas[j], rol:(esUlt&&j===nf-1)?'fin':'post'};
      for(let i=p+1;i<=fin-nf;i++) res[i]={nota:rep, rol:'post'};
      res[p]={nota:A.n, rol:'acc'};
    } else if(flexa && post===0){
      res[p]={nota:A.fijas[nf-1], rol:'acc'};   // flexa con acento en la última: baja en esa sílaba
    } else {
      // menos sílabas que notas: no se juntan en una sílaba notas de sílabas distintas; se omiten las que sobran
      for(let j=0;j<post;j++) res[p+1+j]={nota:A.fijas[nf-post+j], rol:(esUlt&&j===post-1)?'fin':'post'};
      res[p]={nota:A.n, rol:'acc'};
    }
    primero=p; fin=p-1;
  }
  if(primero>=0){
    E.prep.forEach((nt,j)=>{ const i=primero-E.prep.length+j; if(i>=0) res[i]={nota:nt, rol:'prep'}; });
    fin=Math.min(fin, primero-E.prep.length-1);
  }
  let i=0;
  if(intonar) E.inton.forEach(nt=>{ if(i<=fin){ res[i]={nota:nt, rol:'int'}; i++; } });
  for(;i<=fin;i++) res[i]={nota:E.tenor, rol:'ten'};
  return {res, regla:ult.regla};
}

/* Divide un verso en mitades por † y * */
function dividirVerso(v){
  const flexI=v.indexOf('†'), medI=v.indexOf('*');
  let flex=null, a, b;
  if(medI<0) return {flex:null, med:v.replace(/[†*]/g,'').trim(), ter:null};
  if(flexI>=0 && flexI<medI){ flex=v.slice(0,flexI).trim(); a=v.slice(flexI+1,medI).trim(); }
  else a=v.slice(0,medI).trim();
  b=v.slice(medI+1).replace(/†/g,'').trim();
  return {flex, med:a, ter:b};
}

/* Pauta un verso: estructura con sílabas y notas por mitad. intonar: la entonación al comienzo del verso. */
function pautarVerso(verso, cod, lang, intonar){
  const T=tono(cod); if(!T) return null;
  const d=dividirVerso(String(verso).replace(/✠\s*/g,''));
  const mitad=(txt, E, into, flexa)=>{
    if(txt==null) return null;
    const pals=palabras(txt.replace(/\+/g,'').trim(), lang); const s=plano(pals);
    // la flexa con entonación: la entonación del tono, y la cuerda hasta la flexa
    const r=puntear(s, into&&flexa?{...E, inton:T.med.inton}:E, into, flexa);
    return {pals, sils:s, res:r.res, regla:r.regla};
  };
  if(d.ter==null) return {tono:T, flex:null, med:null, ter:mitad(d.med, T.ter, intonar, false)};
  return {
    tono:T,
    flex: d.flex!=null? mitad(d.flex, T.flexa, intonar, true) : null,
    med: mitad(d.med, T.med, intonar && d.flex==null, false),
    ter: mitad(d.ter, T.ter, false, false)
  };
}

/* ---------- Salidas ---------- */
function esc(s){ return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
// Renglones (HTML) de una mitad: acento en negrita, preparatorias en cursiva
function renglonesMitad(h){
  const out=[]; let cur=''; let k=0;
  h.pals.forEach((p,iw)=>{
    if(p.br && cur){ out.push(cur.trim()); cur=''; }
    cur+=esc(p.pre);
    p.sil.forEach(sy=>{ const r=h.res[k++]||{rol:'ten'}; let t=esc(sy.t);
      if(r.rol==='acc') t='<b>'+t+'</b>'; else if(r.rol==='prep') t='<i>'+t+'</i>';
      cur+=t; });
    cur+=esc(p.post)+' ';
  });
  out.push(cur.trim());
  return out;
}
// Renglones de un verso pautado, con † y * en rojo al final de su mitad
function renglonesVerso(pv){
  if(!pv) return [];
  const L=[], sg=c=>'&nbsp;<span class="sg">'+c+'</span>';
  if(pv.flex){ const r=renglonesMitad(pv.flex); r[r.length-1]+=sg('†'); L.push(...r); }
  if(pv.med){ const r=renglonesMitad(pv.med); r[r.length-1]+=sg('*'); L.push(...r); }
  L.push(...renglonesMitad(pv.ter));
  return L;
}
function htmlVerso(pv){ return renglonesVerso(pv).join('<br>'); }
// El verso con marcas de texto (**acento**, _preparatoria_), para los versos con interlineal
function marcadoMitad(h){
  let out=[]; let k=0;
  h.pals.forEach(p=>{ let w=p.pre;
    p.sil.forEach(sy=>{ const r=h.res[k++]||{rol:'ten'}; w+= r.rol==='acc'?'**'+sy.t+'**' : r.rol==='prep'?'_'+sy.t+'_' : sy.t; });
    out.push((w+p.post).replace(/\*\*\*\*/g,'')); });
  return out.join(' ');
}
function marcadoVerso(pv){
  if(!pv) return '';
  let s='';
  if(pv.flex) s+=marcadoMitad(pv.flex)+' † ';
  if(pv.med) s+=marcadoMitad(pv.med)+' * ';
  return s+marcadoMitad(pv.ter);
}

/* GABC de un verso (para dibujar la partitura) */
function gabcMitad(h, marcas){
  let out=''; let k=0;
  h.pals.forEach(p=>{
    p.sil.forEach((sy,j)=>{
      const r=h.res[k++]||{nota:'h',rol:'ten'};
      let txt=(j===0?p.pre:'')+sy.t+(j===p.sil.length-1?p.post:'');
      txt=txt.replace(/[()\[\]{}<>|]/g,'');
      if(marcas){ if(r.rol==='acc') txt='<b>'+txt+'</b>'; else if(r.rol==='prep') txt='<i>'+txt+'</i>'; }
      out+=txt+'('+String(r.nota).replace(/r$/,'')+')';
    });
    out+=' ';
  });
  return out.trim();
}
function gabcVerso(pv, marcas){
  if(!pv) return '';
  let s='';
  if(pv.flex) s+=gabcMitad(pv.flex,marcas)+' †(,) ';
  if(pv.med) s+=gabcMitad(pv.med,marcas)+' *(:) ';
  return s+gabcMitad(pv.ter,marcas)+' (::)';
}
// versos: los que van en la partitura. op: {entonarTodos: entonación en cada verso (cánticos evangélicos),
// marcas: negrita y cursiva en la letra, desde: índice del primer verso (la entonación va solo en el verso 0)}
function gabcSalmo(versos, cod, lang, op){
  op=op||{};
  const T=tono(cod); if(!T) return '';
  let g='('+T.clef+') ';
  versos.forEach((v,i)=>{ const pv=pautarVerso(v,cod,lang, op.entonarTodos || (op.desde||0)+i===0); g+=(i?' ':'')+gabcVerso(pv, !!op.marcas); });
  return g;
}

function listaTonos(){ const l=[]; Object.keys(TONOS).forEach(t=>Object.keys(TONOS[t].ter).forEach(f=>l.push({cod:t+f, et:etiquetaTono(t+f), corta:etiquetaCorta(t+f)}))); return l; }
const API={CONFIG,TONOS,ROMANO,partes,tono,etiquetaTono,etiquetaCorta,silabasLatin,silabasEspanol,palabras,plano,clasificar,acentoFinal,acentoPrevio,
           puntear,pautarVerso,renglonesVerso,htmlVerso,marcadoVerso,gabcVerso,gabcSalmo,dividirVerso,listaTonos,flexDe};
if(typeof module!=='undefined') module.exports=API; else root.Salmodia=API;
})(this);
