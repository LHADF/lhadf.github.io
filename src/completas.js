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
// La base es el calendario ADF. «sel» dice qué se eligió: {cal: sigla del calendario preferido (ARG, PGY, BUE…),
// dia: {fecha: nombre de la celebración elegida a mano ese día, o '' para la del calendario ADF}}. También vale la sigla sola.
const TXT=['t','n','g','c','fer','oct','cal','nota','bio'];
function fichaDe(fila, fecha){ const T=CAL.tabla, o={fecha}; CAL.campos.forEach((c,k)=>{ o[c]=TXT.includes(c)?T[fila[k]]:fila[k]; }); return o; }
function fichaBase(fecha){ const fila=CAL.dias[Math.round((deIso(fecha)-deIso(CAL.desde))/864e5)]; return fila?fichaDe(fila,fecha):null; }
// Variantes del día: 'r', otro calendario lo celebra distinto; 'l', memoria libre (optativa)
const variantesDe=fecha=>(CAL.var[fecha]||[]).map(([tipo,sig,fila])=>({tipo, siglas:sig.split(' '), f:fichaDe(fila,fecha)}));
function diaCal(fecha, sel){
  sel=(sel&&typeof sel==='object')?sel:{cal:sel||''};
  const base=fichaBase(fecha); if(!base) return null;
  const vs=variantesDe(fecha), el=sel.dia?sel.dia[fecha]:null;
  if(el===''||el===base.n) return base;
  if(el!=null){ const v=vs.find(v=>v.f.n===el); if(v) return v.f; }
  for(let c=sel.cal; c; c=CAL.padres[c]){ const v=vs.find(v=>v.tipo==='r'&&v.siglas.includes(c)); if(v) return v.f; }   // el calendario preferido o el de su país
  return base;
}
// Ciclo dominical del año litúrgico (empieza el I Domingo de Adviento)
function ciclo(fecha){
  const d=deIso(fecha);
  const adv=y=>{ const n=new Date(y,11,25,12); n.setDate(n.getDate()-(n.getDay()||7)-21); return n; };
  const y = d>=adv(d.getFullYear()) ? d.getFullYear() : d.getFullYear()-1;
  return 'ABC'[(((y-2016)%3)+3)%3];
}

/* Imagen de la tarjeta del inicio (window.ILUS, de base/ilustraciones.yaml). Orden: propia de la celebración o del día
   (también en Cuaresma) → la del evangelio del domingo, según el ciclo → la del común (en Cuaresma, no: va la del
   tiempo) → la del tiempo → una genérica. Si hay varias, cambian con la franja horaria (0 Oficio y Laudes, 1 Tercia,
   2 Sexta, 3 Nona, 4 Vísperas, 5 Completas) y, de un día al otro, se corren seis lugares. Devuelve el índice o null. */
const TIEMPO_ILU={Adviento:'adviento', Navidad:'navidad', Cuaresma:'cuaresma', Triduo:'cuaresma', Pascua:'pascua'};
function franjaHoraria(d){ const m=d.getHours()*60+d.getMinutes();
  return m<4*60 ? 5 : m<7*60+30 ? 0 : m<10*60+30 ? 1 : m<13*60+30 ? 2 : m<16*60+30 ? 3 : m<20*60 ? 4 : 5; }
function ilustracion(fecha, sel, franja){
  const I=window.ILUS, r=diaCal(fecha, sel); if(!I || !r) return null;
  const cuaresma=r.t==='Cuaresma', com=I.comunDe[r.n]==='santa-maria-sabado' ? 'virgen-maria' : I.comunDe[r.n];
  const l=I.propias[r.n] || (I.domingos[r.n]||{})[ciclo(fecha)] || (!cuaresma && com && I.comunes[com]) || I.tiempos[TIEMPO_ILU[r.t]] || I.genericas;
  if(!l || !l.length) return null;
  const dia=Math.round((deIso(fecha)-deIso('2000-01-01'))/864e5);
  return l[(dia*6+(franja||0))%l.length];
}
// Para el inicio: todas las celebraciones posibles del día (la primera, la del calendario ADF) y cuál está elegida
function opcionesDia(fecha, sel){
  const base=fichaBase(fecha); if(!base) return [];
  const act=diaCal(fecha, sel);
  const sig=f=>f.cal?f.cal.split(/,\s*/):['ADF'];
  return [{tipo:'b', siglas:sig(base), f:base}, ...variantesDe(fecha)].map(o=>({...o, actual:o.f.n===act.n&&o.f.g===act.g}));
}
const enRango=f=>f>=CAL.desde && f<=CAL.hasta;
// La entrada de la base para una fecha fija del Propio del tiempo («17 de diciembre»)
// Año del ciclo bienal (Oficio de lectura): años impares, el I; pares, el II. Cuenta el año litúrgico, que empieza en
// Adviento: el Adviento y la Navidad de 2026 son del año 2027 (año I).
const anioBienal=(f, ref)=>{ const y=+f.slice(0,4)+((f.slice(5,7)==='12' || (f.slice(5,7)==='11' && ref && ref.t==='Adviento')) ? 1 : 0); return y%2 ? 'I' : 'II'; };
const fechaClave=f=>`${+f.slice(8,10)} de ${MESES[+f.slice(5,7)-1]}`;

/* ---------- Oración del común, con el nombre de la celebración ----------
   Los comunes traen varias oraciones «para» distintos casos (un santo obispo, varios mártires, una virgen…), con N. en
   lugar del nombre. Se elige la que mejor cuadra con el título y se pone el nombre: «San Blas, obispo y mártir» → «Blas». */
const PALABRAS=['papa','obispo','presbítero','sacerdote','abad','religios','virgen','mártir','misioner','fundador','doctor','rey','reina','educador','caridad','pastor','monje','abadesa','madre','viuda'];
// El común que indica el santoral de la base («Del Común de pastores: para un santo obispo.») → su clave en base/comunes/.
// Si nombra dos («de pastores… y del de doctores»), el primero.
const COMUN_DE=[[/dedicaci/,'dedicacion'],[/virgen mar/,'virgen-maria'],[/ap[óo]stol/,'apostoles'],[/para un m[áa]rt|un m[áa]rt/,'un-martir'],
  [/varios m[áa]rt/,'varios-martires'],[/pastores/,'pastores'],[/doctores/,'doctores'],[/v[íi]rgenes/,'virgenes'],[/santos varones/,'santos-varones'],[/santas mujeres/,'santas-mujeres'],[/religios/,'religiosos'],[/caritativ/,'caridad'],[/educador/,'educadores']];
// Todo doctor de la Iglesia toma del común de doctores (completado por el de pastores; las doctoras, por el de vírgenes),
// salvo sus elementos propios, aunque la rúbrica del libro nombre primero otro común. Lo que asigne adf.yaml manda
// (santa Hildegarda: solo del común de vírgenes).
const esDoctor=nombre=>/\bdoctor(a|es)?\b/i.test(String(nombre||''));
function comunDe(texto){
  const t=String(texto||'').toLowerCase(); let mejor=null, pos=1e9;
  for(const [re,id] of COMUN_DE){ const m=t.match(re); if(m && m.index<pos){ pos=m.index; mejor=id; } }
  return mejor;
}
// «San Roberto Belarmino, presbítero…» → «Roberto Belarmino» (lo que va en lugar de «N.»)
function nucleoDe(n){
  n=String(n||'');
  return n.split(',')[0].replace(/^(San|Santa|Santo|Santos|Santas|Beato|Beata|Beatos|Beatas)\s+/,'').trim()
    + (/y compañer/i.test(n) && !/y compañer/i.test(n.split(',')[0]) ? ' y compañeros' : '');
}
// En los textos del común (fuera de las oraciones, que arma oracionComun): «san N.» / «santa N.» → el primer nombre del santo
function conNombre(o, nombre){
  const n=String(nombre||''), m=/^(San|Santa|Santo|Beato|Beata)\s/.exec(n); if(!m) return o;
  const fem=/^(Santa|Beata)$/.test(m[1]), nom=m[1].toLowerCase()+' '+nucleoDe(n).split(/\s+/)[0];   // solo el primer nombre: «san Roberto»
  const f=x=> typeof x==='string' ? x.replace(/\b(san|santa|santo)\s+N\./gi, (t,a)=>(/^[A-Z]/.test(a)?nom[0].toUpperCase()+nom.slice(1):nom)).replace(/\bdoctor admirable/g, fem?'doctora admirable':'doctor admirable')
    : Array.isArray(x) ? x.map(f) : (x && typeof x==='object') ? Object.fromEntries(Object.entries(x).map(([k,v])=>[k, k==='oraciones'?v:f(v)])) : x;
  return f(o);
}
function oracionComun(oraciones, nombre, turnoN){
  if(!oraciones || !oraciones.length) return null;
  const n=String(nombre||''), tit=n.toLowerCase(), plural=/^(santos|santas|beatos|beatas)\b|y compañer/i.test(n);
  const fem=/^(Santa|Santas|Beata|Beatas)\b/.test(n);
  const pts=o=>{ const p=o.para.toLowerCase(); let x=0;
    const t=tit+(/presbítero|sacerdote/.test(tit)?' pastor':'');   // un presbítero: «un santo pastor»
    for(const w of PALABRAS) if(p.includes(w)) x+= t.includes(w) ? 2 : (/papa|obispo|abad|misioner|fundador|religios|educador|caridad|virgen/.test(w) ? -3 : 0);
    if(/varios|varias|las |los /.test(p)) x+=plural?3:-3; else if(plural && p) x-=1;
    // que no le toque a un santo la oración de una santa, ni al revés
    const pf=/\b(una|las|santa|santas|mujer|mujeres|virgen|vírgenes|religiosa|educadora)\b/.test(p), pm=/\b(un|los|santo|santos|varios)\b/.test(p);
    if(fem ? (pm && !pf) : pf) x-=10;
    if(fem ? /\bsan N\./.test(o.texto) : /\bsanta N\./.test(o.texto)) x-=5;
    return x; };
  // Entre las que cuadran igual de bien (las «O bien»), se alternan de una celebración a la siguiente (n: turno del común)
  const max=Math.max(...oraciones.map(pts)), empate=oraciones.filter(o=>pts(o)===max), o=empate[(turnoN||0)%empate.length];
  const nucleo=nucleoDe(n);
  return alternativas(o.texto, fem).replace(/\bsan N\./g, fem?'santa N.':'san N.').replace(/\bN\.(\s*y\s*N\.)?/g, nucleo).replace(/\s*[([](obispo|presbítero|papa|abad|abadesa)[)\]]/g, '');
}
// El libro marca la forma femenina entre corchetes: «san [santa] N.», «este santo [esta santa]». Se queda una.
function alternativas(texto, fem){
  return String(texto).replace(/((?:\p{L}+ ){0,3}\p{L}+) \[([^\]]+)\]/gu, (m, antes, alt)=>{
    const n=alt.trim().split(/\s+/).length, pal=antes.split(' '), masc=pal.slice(-n).join(' '), resto=pal.slice(0,-n).join(' ');
    if(/^(obispo|presbítero|papa|abad|abadesa)$/.test(alt)) return m;   // se quita aparte
    return (resto?resto+' ':'')+(fem?alt:masc);
  });
}
// Un común del libro (base/comunes/), con lo que hereda: «hereda» (o «hereda_mujeres», para las santas) es el común del que
// se toma lo que este no trae (religiosos, caridad y educadores, de santos varones o santas mujeres; doctores, de pastores).
// En el tiempo pascual, lo que el común (o el propio del libro) trae para Pascua reemplaza a lo de siempre: las antífonas
// con «Aleluia», los responsorios breves pascuales… (también en sus I Vísperas y en Tercia, Sexta y Nona).
function enPascua(o){
  if(!o) return o;
  const out=o.pascua ? {...o, ...o.pascua} : {...o};
  if(o.primeras) out.primeras=enPascua(o.primeras);
  for(const k of ['tercia','sexta','nona','invitatorio']) if(o[k] && typeof o[k]==='object' && o[k].pascua) out[k]={...o[k], ...o[k].pascua};
  return out;
}
// Las «opciones» de un común («O bien:») se alternan: la celebración n.º n del año que toma de ese común usa la opción n.
function rotar(o, n){
  if(!o || typeof o!=='object') return o;
  const out={...o};
  for(const [k,alt] of Object.entries(o.opciones||{})){ const l=[o[k], ...alt].filter(x=>x!=null); if(l.length) out[k]=l[(n||0)%l.length]; }
  for(const k of ['primeras','tercia','sexta','nona']) if(o[k] && typeof o[k]==='object') out[k]=rotar(o[k], n);
  return out;
}
// Cuántas celebraciones del año, antes de esta fecha, toman del mismo común (según base/santoral/adf.yaml): el turno.
const TURNOS={};
function turno(adf, id, fecha, sel){
  if(!adf || !id || !fecha) return 0;
  const clave=fecha.slice(0,4)+'|'+id+'|'+JSON.stringify(sel||'');
  if(!TURNOS[clave]){ const l=[]; for(let f=fecha.slice(0,4)+'-01-01'; f.slice(0,4)===fecha.slice(0,4) && enRango(f); f=masDias(f,1)){
      const r=diaCal(f, sel); if(r && adf[r.n] && adf[r.n].comun===id) l.push(f); }
    TURNOS[clave]=l; }
  return TURNOS[clave].filter(f=>f<fecha).length;
}
// Las «variantes» de un común llevan rúbrica («Para una santa virgen:», «Para varios santos:»…): se toma la que corresponde
// a la celebración, por su nombre (número, sexo, mártir, presbítero). Sin rúbrica que corresponda, queda el texto principal
// (en el común de vírgenes, el de una virgen mártir). Las de un tiempo, las «O bien» y las demás no se eligen solas.
function rubricaVale(et, nombre){
  const e=String(et||'').toLowerCase(), n=String(nombre||'');
  if(/opcion|o bien|latinoamericana|tiempo|cuaresma|pascual|matrimonio|fundador|misionero|^ii |difunto|si se trata/.test(e)) return false;
  const varios=/^(Santos|Santas|Beatos|Beatas)\b/.test(n), fem=/^(Santa|Santas|Beata|Beatas)\b/.test(n), martir=/mártir/i.test(n);
  if(/\bvari[oa]s\b/.test(e)) return varios;
  if(varios) return false;
  if(/santa virgen/.test(e)) return !martir;
  if(/una mártir/.test(e)) return fem;
  if(/un mártir/.test(e)) return !fem;
  if(/presbítero/.test(e)) return /presbítero/i.test(n);
  return false;
}
const conAleluia=t=>{ const c=/\s*†\s*$/.test(t); t=t.replace(/\s*†?\s*$/,''); return t.replace(/([^.!?»])$/,'$1.')+' Aleluia.'+(c?' †':''); };   // la † de la antífona, al final
function conVariantes(o, nombre){
  if(!o || typeof o!=='object') return o;
  const out={...o};
  if(o.variantes){
    const pas=o.pascua?{...o.pascua}:null;
    for(const [k,vs] of Object.entries(o.variantes)){
      const ok=(vs||[]).filter(v=>rubricaVale(v.etiqueta, nombre)); if(!ok.length) continue;
      const tieneA=v=>/aleluia/i.test(JSON.stringify(v.texto));
      const sin=ok.find(v=>!tieneA(v)), con=ok.find(tieneA);
      if(sin) out[k]=sin.texto;
      if(pas && pas[k]!=null) pas[k] = con ? con.texto : (sin && typeof sin.texto==='string' ? conAleluia(sin.texto) : pas[k]);
    }
    if(pas) out.pascua=pas;
  }
  for(const k of ['primeras','tercia','sexta','nona']) if(o[k] && typeof o[k]==='object') out[k]=conVariantes(o[k], nombre);
  return out;
}
function comun(comunes, id, nombre, pascua, n){
  if(pascua) { const c=comun(comunes, id, nombre, false, n); return c && enPascua(c); }
  const c0=comunes && comunes[id]; if(!c0) return null;
  const c=conNombre(conVariantes(rotar(c0, n), nombre), nombre);
  const fem=/^(Santa|Santas|Beata|Beatas)\b/.test(String(nombre||''));
  const h=comunes[(fem && c.hereda_mujeres) || c.hereda];
  if(!h) return c;
  const b=comun(comunes, (fem && c.hereda_mujeres) || c.hereda, nombre, false, n);
  // lo heredado se completa también en su versión de Pascua (si no, se perdería el «Aleluia» de lo que trae el otro común)
  const mezclar=(x,y)=>{ const o={...(x||{}), ...(y||{})}; if((x&&x.pascua) || (y&&y.pascua)) o.pascua={...((x&&x.pascua)||{}), ...((y&&y.pascua)||{})}; return o; };
  const out={...mezclar(b, c), nombre:c.nombre};
  if(b.primeras || c.primeras) out.primeras=mezclar(b.primeras, c.primeras);
  for(const k of ['tercia','sexta','nona']) if(b[k] || c[k]) out[k]=mezclar(b[k], c[k]);
  return out;
}

/* ---------- Utilidades de texto ---------- */
const MAYUS=['Dios','Señor','Cristo','Jesús','Jesucristo','Israel','Padre','Hijo','Espíritu','Santo','María','Jerusalén','Sión','Iglesia','Omnipotente','Altísimo','Mesías','Redentor','Reina','Virgen','Madre'];
function oracionCase(s){ // «ACCIÓN DE GRACIAS» → «Acción de gracias», respetando nombres divinos
  const t=s.toLocaleLowerCase('es').replace(/^\p{L}/u,c=>c.toLocaleUpperCase('es'));
  return t.split(/(\s+)/).map(w=>{ const lim=w.replace(/[^\p{L}]/gu,''); const m=MAYUS.find(x=>x.toLocaleLowerCase('es')===lim); return m?w.replace(lim,m):w; }).join('').replace(/\.$/,'');
}
// Estrofas (renglones) → versos salmódicos: pares con mediante; si sobra una línea, flexa
// Estrofas → versos (con * mediante y † flexa). De a dos renglones; si sobra uno, los tres últimos van juntos con flexa en
// el primero, salvo que un punto fuerte (. ! ?) al final del tercer renglón cierre claramente los tres primeros: entonces
// van juntos los tres primeros. En un grupo de tres, si el primer renglón termina en dos puntos, no hay flexa: mediante
// ahí, y los otros dos seguidos (en renglones separados: « ¶ »). Si los dos puntos están en el segundo, flexa y mediante.
const FUERTE=/[.!?][»”’)]*$/;
const TRES_PRIMEROS=[/^Anuncien todos los pueblos sus maravillas/];   // (Tb 13: los tres primeros juntos, y los tres últimos)
function gruposDe(ls){
  const n=ls.length;
  if(n<3) return [n];
  if(n===6 && TRES_PRIMEROS.some(r=>r.test(ls[0]))) return [3,3];
  if(n%2===0) return Array(n/2).fill(2);
  const pares=Array((n-3)/2).fill(2);
  if(n>=5 && FUERTE.test(ls[2]) && !FUERTE.test(ls[n-4])) return [3, ...pares];
  return [...pares, 3];
}
function verso(g){
  if(g.length===1) return g[0];
  if(g.length===2) return `${g[0]} * ${g[1]}`;
  return /:$/.test(g[0]) ? `${g[0]} * ${g[1]} ¶ ${g[2]}` : `${g[0]} † ${g[1]} * ${g[2]}`;
}
// Estrofa marcada a mano en la base (algún renglón termina en « *» o « †»): manda lo marcado. Cada verso: los renglones
// hasta el que termina en « *» (los que terminan en « †» llevan flexa; los demás, sin signo, van en renglón aparte: « ¶ »)
// y, después, un renglón (al final de la estrofa, todos los que queden).
const MARCA=/\s+[*†]$/;
function versosMarcados(ls){
  const out=[]; let i=0;
  while(i<ls.length){
    let j=i; while(j<ls.length && !/\s\*$/.test(ls[j])) j++;
    if(j>=ls.length){ out.push(ls.slice(i).map(l=>l.replace(MARCA,'')).join(' ¶ ')); break; }
    const prim=ls.slice(i,j+1).map((l,k,a)=>{ const t=l.replace(MARCA,''); return k===a.length-1 ? t+' * ' : t+(/\s†$/.test(l)?' † ':' ¶ '); }).join('');
    const resto = ls.slice(j+1).some(l=>MARCA.test(l)) ? ls.slice(j+1, j+2) : ls.slice(j+1);
    out.push(prim+resto.join(' ¶ ')); i=j+1+resto.length;
  }
  return out;
}
function versosDe(estrofas){
  const versos=[], grupos=[];
  estrofas.forEach(e=>{
    const ls=e.split('\n').map(x=>x.trim()).filter(Boolean), g=[];
    if(ls.some(l=>MARCA.test(l))){ for(const v of versosMarcados(ls)){ versos.push(v); g.push(versos.length-1); } grupos.push(g); return; }
    let i=0;
    for(const t of gruposDe(ls)){ versos.push(verso(ls.slice(i, i+t))); g.push(versos.length-1); i+=t; }
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
function recInvocacion(trInv){
  const rec=recitado(trInv.map((p,i)=>i===1?['✠ '+p[0],p[1]]:p), [['V','Deus,'],['R','Dómine,',true],['','Glória',true]]);
  rec[2].versos=enLineas(rec[2].pares, B.completas.gregoriano.invocacion.cortes_gloria);
  return rec;
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
  // Todos los Fieles Difuntos: «Completas del domingo, después de las II Vísperas» (libro, 2 de noviembre)
  if(hoy.n==='Todos los Fieles Difuntos' && !hoy.dom) return {juego:'domingo', oracion:'juego', solemne:false};
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
// Parte los pares en renglones según la cantidad de palabras latinas de cada uno (cortes con sentido, de la base).
// Lo que sobra: si es una sola palabra (Allelúia), sigue en el último renglón; si no, renglón propio.
function enLineas(pares, cortes){
  if(!cortes) return null;
  const out=[]; let i=0;
  for(const n of cortes){ const l=[]; let w=0; while(i<pares.length && w<n){ w+=pares[i][0].replace(/^[✠*†]\s+/,'').split(/\s+/).length; l.push(pares[i++]); } if(l.length) out.push(l); }
  const resto=pares.slice(i);
  if(resto.length){ if(resto.length===1 && out.length) out[out.length-1].push(resto[0]); else out.push(resto); }
  return out;
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
  S.push({k:'vr', tono:tonoInv, gabc:invocacionGabc(tonoInv, !cuaresma), glosa:trInv, rec:recInvocacion(trInv)});

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

  sec('cantico','Cántico evangélico',{ref:'Lc 2, 29-32'});
  const tp=pascua||!!(el.especial&&/Aleluia/i.test(el.especial.antifona_cantico||''));
  const trAnt=GR.antifona.traduccion.filter(p=>tp||!/^Allel/.test(p[0])), recAnt=recitado(trAnt, [['Ant','Salva',true]]);
  S.push({k:'ant', id:'ac', gabc:salvaNosGabc(tp), modo:'3a', glosa:trAnt, rec:recAnt, t:{la:'Salva nos, Dómine'}});
  S.push({k:'cantico', titulo:'Cántico de Simeón', gabc:GR.cantico.gabc, glosa:GR.cantico.traduccion,
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
    return {id, n:GM[k].titulo, gabc:GM[k].gabc, glosa:GM[k].traduccion, rec:[{rol:'', todos:true, pares:tr, versos:enLineas(tr, GM[k].cortes)}]}; };
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
    nombre:'Completas',
    versiones:{es:{n:'Liturgia de las Horas'}},
    gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']},
    dia:{titulo:hoy.n, tiempo:TIEMPO_TXT[hoy.t]||hoy.t, salterio, color:hoy.c, grado:hoy.g,
         visperas: el.visperasDe ? `Completas después de las I Vísperas de: ${el.visperasDe.n}` : ''},
    fechaTxt:`${DIAS_TXT[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]}`,
    juego:el.juego,
    secciones:S,
  };
}

window.Completas={armar, diaCal, opcionesDia, enRango, iso, deIso, masDias, ciclo, ilustracion, franjaHoraria, calendarios:CAL.calendarios,
  _:{modo:{}, oracionComun, comunDe, esDoctor, comun, rubricaVale, enPascua, turno, alternativas, fechaClave, anioBienal, invocacionGabc, recInvocacion, enLineas, recitado, versosDe, oracionCase, pares, enVersos, DIAS, DIAS_TXT, MESES, TIEMPO_TXT, ROMANO}};   // para las otras horas (laudes.js)
})();
