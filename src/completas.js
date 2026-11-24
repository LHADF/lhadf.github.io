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
// Lectura breve para salmodiar (docs/horas.md): «*» (metro) y «†» (flexa), como en los salmos.
// Metro: en un punto fuerte (. ; : ! ?) lo más cerca de la mitad; si no hay ninguno cerca, en una coma (donde se cierra
// una idea). Flexa: igual, en la primera parte, lo más cerca de su mitad, pero nunca en dos puntos; si la primera parte
// es muy breve o no tiene dónde, sin flexa. Si la base ya trae « * » o « † », manda lo marcado.
// Devuelve [{t, sg}] (los trozos y el signo que va después de cada uno, '' en el último).
function marcarLectura(texto){
  const t=String(texto||'').trim();
  if(/ [*†] /.test(t)) return t.split(/ ([*†]) /).reduce((a,x,i)=>{ if(i%2) a[a.length-1].sg=x; else a.push({t:x, sg:''}); return a; }, []);
  // cortes posibles: después de un signo (y de comillas o paréntesis que cierran), antes de un espacio, fuera de paréntesis
  const cortes=[]; let par=0, cita=0;
  const atona=/(?:^|[\s«(—])(?:que|de|del|y|e|o|u|a|al|el|la|lo|los|las|en|con|por|para|si|ni|se|su|sus|mi|tu)$/i;
  for(let i=0;i<t.length;i++){
    const c=t[i]; if(c==='(') par++; else if(c===')') par=Math.max(0,par-1);
    if(c==='«') cita++; else if(c==='»') cita=Math.max(0,cita-1);
    if(par || !/[.;:!?,]/.test(c)) continue;
    if(c===',' && (cita || atona.test(t.slice(Math.max(0,i-8),i)))) continue;   // ni comas dentro de una cita ni detrás de «que», «de», «e»…
    let j=i+1; while(j<t.length && /[»”"’)]/.test(t[j])) j++;
    if(t[j]!==' ' || j>=t.length-1) continue;
    if(c==='.' && /\b(?:[A-Z]|cf|Sr|Mt|Mc|Lc|Jn|vv?)\.$/.test(t.slice(Math.max(0,i-3),i+1))) continue;   // abreviaturas
    cortes.push({p:j, fuerte:c!==',', dos:c===':'});
  }
  const elegir=(a,b,sinDos)=>{   // el corte más cercano a la mitad de [a,b): fuerte en el tramo central; si no, coma; si no, fuerte
    const m=(a+b)/2, L=b-a, en=c=>c.p>a+L*0.25 && c.p<b-L*0.25, cs=cortes.filter(c=>c.p>a && c.p<b && !(sinDos&&c.dos));
    const cerca=(xs)=>xs.sort((x,y)=>Math.abs(x.p-m)-Math.abs(y.p-m))[0];
    return cerca(cs.filter(c=>c.fuerte&&en(c))) || cerca(cs.filter(c=>!c.fuerte&&en(c))) || cerca(cs.filter(c=>c.fuerte && c.p>a+L*0.15 && c.p<b-L*0.15));
  };
  const met=t.length>=50 && elegir(0,t.length,false);
  if(!met) return [{t, sg:''}];
  const fl=met.p>=70 && elegir(0,met.p,true);
  const trozos=fl ? [{t:t.slice(0,fl.p), sg:'†'},{t:t.slice(fl.p+1,met.p), sg:'*'}] : [{t:t.slice(0,met.p), sg:'*'}];
  return [...trozos, {t:t.slice(met.p+1), sg:''}];
}

// Flexa de una prece (docs/laudes.md): en lo posible, después de la invocación o el título conmemorativo y antes del
// pedido («Tú que subiste a Jerusalén…, † conduce a tu Iglesia…»). Si no hay esa estructura clara (o la invocación es muy
// breve: «Señor,»), lo más cerca de la mitad, donde se divide una idea (coma, punto y coma, dos puntos); si no, como
// viene de la base. Recibe y devuelve [antes de la flexa, después].
const PEDIDOS=new Set(('haz concede da dales danos ayuda ayúdanos guarda libra protege conduce atrae ilumina purifica santifica recibe acoge '
  +'perdona enseña mira escucha envía infunde aumenta fortalece renueva socorre consuela sostén sana bendice derrama llena colma mantén une '
  +'reúne dirige ten muestra despierta inspira otorga aleja defiende visita acuérdate acompaña glorifica admite introduce lleva abre enciende '
  +'transforma cuida preserva salva multiplica suscita no que asiste ampara favorece sé fortifica levanta perfecciona robustece custodia '
  +'atiende vela confirma inflama libera consagra purifícanos santifícanos prepara dispón dígnate permite haced trae otorga reconforta alienta '
  +'derrama infunde revístenos viste aparta apártanos desata rompe hazlos haznos hazles conserva guía orienta reanima').split(' '));
const esPedido=w=>{ const x=w.toLowerCase().replace(/[^a-záéíóúüñ]/g,''); return PEDIDOS.has(x) || /^[a-zñ]*[áéíóú][a-zñ]*(nos|les|los|las|lo|la|le|me|te|se)$/.test(x) && x.length>5 && !/[aá]ndo|[ie][eé]ndo|éndo/.test(x); };   // (no los gerundios: «resucitándolo»)
function marcarPrece(par){
  const [a,b]=par; if(!b) return par;
  const t=a+' '+b, ws=t.split(' ');
  // 1) invocación + pedido: la primera coma seguida de un verbo de pedido
  let pos=0;
  for(let i=0;i<ws.length-1;i++){
    pos+=ws[i].length+1;
    if(/,$/.test(ws[i]) && esPedido(ws[i+1]) && !/^(no|que)$/i.test(ws[i+1].replace(/[^\p{L}]/gu,''))){
      let ini=t.slice(0,pos-1), fin=t.slice(pos);
      // «…, por intercesión de san José, ayúdanos…»: la intercesión va con el pedido (la flexa, antes)
      const pi=ini.search(/,\s+por (?:la )?intercesi[oó]n\b[^,]*,$/i);
      if(pi>=14){ fin=ini.slice(pi+1).trim()+' '+fin; ini=ini.slice(0,pi+1); }
      if(ini.length>=14 && fin.length>=20) return [ini, fin];
      break;
    }
  }
  // 2) empieza con el pedido y sigue otro coordinado («Haz, Señor, que recordemos…, recibida en el bautismo, † y que
  //    vivamos…»): la flexa, antes del segundo pedido
  if(esPedido(ws[0])){
    const k=t.search(/,\s+y (?:que\b|\S+)/);
    if(k>=20){ const sig=t.slice(k+1).trim().split(' ')[1]||''; if(/^que$/i.test(sig) || esPedido(sig)) return [t.slice(0,k+1), t.slice(k+2)]; }
  }
  // 3) sin esa estructura: la división de la base, si está cerca de la mitad; si no, la coma (o ; :) más cercana a la mitad
  const m=t.length/2, cerca=x=>Math.abs(x-m)<t.length*0.2;
  if(cerca(a.length)) return par;
  let mejor=-1;
  for(let i=0;i<t.length;i++) if(/[,;:]/.test(t[i]) && t[i+1]===' ' && !/(?:^|\s)(?:que|de|del|y|e|o|a|al|el|la|los|las|en|con|por|para)$/i.test(t.slice(Math.max(0,i-8),i))
    && (mejor<0 || Math.abs(i-m)<Math.abs(mejor-m))) mejor=i;
  return mejor>0 && Math.abs(mejor-m)<Math.abs(a.length-m) ? [t.slice(0,mejor+1), t.slice(mejor+2)] : par;
}

// Domingo de Pascua (cómputo gregoriano)
function domPascua(y){
  const a=y%19, b=Math.floor(y/100), c=y%100, d=Math.floor(b/4), e=b%4, f=Math.floor((b+8)/25), g=Math.floor((b-f+1)/3);
  const h=(19*a+b-d-g+15)%30, i=Math.floor(c/4), k=c%4, l=(32+2*e+2*i-h-k)%7, m=Math.floor((a+11*h+22*l)/451);
  const mes=Math.floor((h+l-7*m+114)/31), dia=(h+l-7*m+114)%31+1;
  return iso(new Date(y, mes-1, dia, 12));
}
// Tiempo de pasión: desde las I Vísperas del V domingo de Cuaresma hasta el Sábado Santo (el domingo de Pascua, ya no).
// No se dice el Gloria al Padre al final de los salmos y cánticos (va la rúbrica) ni en el responsorio breve (de la
// respuesta corta se pasa a la repetición final). f: el día del oficio (en las I Vísperas, el domingo).
function pasion(f, sol){
  if(!f || modo.difuntos || sol) return false;   // en las solemnidades se dice el Gloria
  const p=domPascua(+f.slice(0,4));
  return f>=masDias(p,-14) && f<masDias(p,0);
}
const NO_GLORIA='No se dice Gloria.';
// Responsorio breve sin el «Gloria al Padre» (pares [V|R, texto])
// (en su lugar, la rúbrica: ['rub', «No se dice Gloria.»])
const sinGloriaResp=r=>Array.isArray(r) ? r.map(x=>(Array.isArray(x) && /^Gloria al Padre/.test(x[1]||'')) ? ['rub', NO_GLORIA] : x) : r;
// Versos de un cántico sin el Glória Patri y el Sicut erat (y su traducción, verso por verso)
const esGloriaLa=v=>/^Gl[óo]ria Patri|^Sicut erat/.test(String(v).replace(/\*\*|_/g,''));
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
// El himno no: va siempre el primero (el de sync) y los demás se ofrecen como opciones en la hora (himnosComun).
function rotar(o, n){
  if(!o || typeof o!=='object') return o;
  const out={...o};
  for(const [k,alt] of Object.entries(o.opciones||{})){ if(k==='himno') continue; const l=[o[k], ...alt].filter(x=>x!=null); if(l.length) out[k]=l[(n||0)%l.length]; }
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
// Antífona propia en gregoriano (base/gregoriano/propios.yaml) para un texto español de la base: la de «cuando» más larga
// con que empieza el texto. tipo: 'magnificat' (antífonas «Oh») o 'responsorio' (en lugar del responsorio breve).
// Va solo cantada (soloCanto): recitado, el texto español. Devuelve los campos para la sección {k:'ant'}.
function gregPropio(tipo, texto){
  const L=(B.gregoriano_propios||{})[tipo]||[], t=String(texto||'').trim();
  const p=L.filter(x=>t.startsWith(x.cuando)).sort((a,b)=>b.cuando.length-a.cuando.length)[0];
  return p ? {gabc:p.gabc, gabcRep:p.repeticion||null, glosa:p.traduccion, soloCanto:true, modoGreg:p.modo, greg:p.id} : null;
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
  // La oración propia de las solemnidades, solo si no caen en domingo (Cristo Rey, Trinidad…: la del domingo)
  const esDom=d=>d.dom || deIso(d.fecha).getDay()===0;
  if(man && man.pv) return {juego:'sabado', oracion: man.sol && !esDom(man) ? 'solemnidad' : 'juego', solemne:true, visperasDe:man};
  if(solemneDia(hoy)) return {juego:'domingo', oracion: hoy.sol && !esDom(hoy) ? 'solemnidad' : 'juego', solemne:true};
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
  // (las del sábado anterior al V domingo de Cuaresma, después de sus I Vísperas; no las de una solemnidad ni las que siguen a sus I Vísperas)
  const pas=el.visperasDe ? pasion(masDias(fecha,1), el.visperasDe.sol) : pasion(fecha, hoy.sol);
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
  S.push({k:'himno', es:true, efimera:el.solemne, def: el.solemne?'telucis':pool+'-0', opciones:[{id:'telucis', n:GR.himno.titulo, lang:'la', gabc:GR.himno.gabc, glosa:GR.himno.traduccion, rec:enVersos(recitado(GR.himno.traduccion, [['','Te'],['','Procul'],['','Præsta,']]), ['Te','Rerum','Ut','Sis','Procul','Et','Hostémque','Ne','Præsta,','Patríque','Cum','Regnans'])}].concat(C.himnos[pool].map((h,i)=>({id:pool+'-'+i, n:oracionCase(h.titulo), lang:'es', est:h.texto.map(e=>e.split('\n')), amen:''})),
    himnosLatinos('completas', el.visperasDe||hoy, {hs:C.latinos, tiempo:true, greg:GR.himno.titulo}))});

  sec('salmodia','Salmodia');
  const sal=pascua?J.salmodia_pascua:J.salmodia; let na=0;
  sal.forEach((g,gi)=>{
    const id='a'+(gi+1);
    S.push({k:'ant', id, es:true, n: sal.length>1?`Ant. ${gi+1}`:'Ant.', t:{es:g.ant}, modo:tono});
    g.salmos.forEach(sid=>{
      const s=B.salmos[sid]; const v=versosDe(s.texto);
      S.push({k:'salmo', es:true, id:sid, ant:id, titulo:{es:s.titulo}, lema:{es:oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!pas, rubrica:pas?NO_GLORIA:''});
    });
    S.push({k:'ant', rep:id, es:true});
  });

  sec('lectura','Lectura breve',{ref:J.lectura.ref});
  S.push({k:'lectura', es:true, t:{es:J.lectura.texto}});
  S.push({k:'deo', t:GR.lectura_respuesta[0][0], il:GR.lectura_respuesta_glosa, tr:GR.lectura_respuesta[0][1]});   // ℟. Deo grátias (la dicen todos)

  if(el.especial){
    sec('responsorio','En lugar del responsorio breve');
    S.push({k:'ant', id:'rb', es:true, n:'Ant.', t:{es:el.especial.en_lugar_del_responsorio}, ...(gregPropio('responsorio', el.especial.en_lugar_del_responsorio)||{})});
  } else {
    sec('responsorio','Responsorio breve');
    const rg = pascua ? null : GR.responsorio.ordinario;   // cantado: por ahora, el del Tiempo Ordinario
    const rl=pares(O.responsorio[pascua?'pascua':'ordinario']);
    // tiempo de pasión: sin el Gloria (en la partitura, el versículo «Glória Patri» y su traducción)
    const rgg=rg && (pas ? {gabc:rg.gabc.replace(/<sp>V\/<\/sp>\.\s*Gl[óo]\([^]*?\(::\)\s*/, ''),
      glosa:rg.traduccion.filter((p,i,a)=>{ const g=a.findIndex(x=>/^Gl[óo]ria$/.test(x[0])), s=a.findIndex((x,j)=>j>g && /^Sancto\.$/.test(x[0])); return g<0 || s<0 || i<g || i>s; })}
      : {gabc:rg.gabc, glosa:rg.traduccion});
    S.push({k:'resp', es:true, l:{es:pas?sinGloriaResp(rl):rl}, ...(rgg||{}), ...(pas?{rub:NO_GLORIA}:{})});
  }

  sec('cantico','Cántico evangélico',{ref:'Lc 2, 29-32'});
  const tp=pascua||!!(el.especial&&/Aleluia/i.test(el.especial.antifona_cantico||''));
  const trAnt=GR.antifona.traduccion.filter(p=>tp||!/^Allel/.test(p[0])), recAnt=recitado(trAnt, [['Ant','Salva',true]]);
  S.push({k:'ant', id:'ac', gabc:salvaNosGabc(tp), modo:'3a', glosa:trAnt, rec:recAnt, t:{la:'Salva nos, Dómine'}});
  S.push({k:'cantico', titulo:'Cántico de Simeón', gabc:GR.cantico.gabc, glosa:GR.cantico.traduccion,
          tono:GR.cantico.tono, versos:pas?GR.cantico.versos.filter(v=>!esGloriaLa(v)):GR.cantico.versos,
          inter:pas&&GR.cantico.traduccion_versos?GR.cantico.traduccion_versos.filter((x,i)=>!esGloriaLa(GR.cantico.versos[i])):GR.cantico.traduccion_versos,
          verso1:GR.cantico.primer_verso, inter1:GR.cantico.traduccion});
  if(pas) S.push({k:'rub', t:NO_GLORIA});
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

// Tiempo pascual: las antífonas y el responsorio breve de lo que no trae su versión pascual (propios de ADF, lo que se
// toma de otra celebración, lo propio del libro) llevan «Aleluia», como en el libro («T.P.»)
const tieneAleluia=t=>/aleluia/i.test(String(t||''));
function respPascua(r){   // [[V,a],[R,a],[V,b],[R,c],[V,Gloria],[R,a]] → a con «Aleluia, aleluia.»; c = «Aleluia, aleluia.»
  if(!Array.isArray(r) || r.length<4 || r.some(x=>tieneAleluia(x[1]))) return r;
  const a=r[0][1], a2=a.replace(/\s*$/,'').replace(/([^.!?»])$/,'$1.')+' Aleluia, aleluia.';
  return r.map((x,i)=> (x[1]===a) ? [x[0], a2] : (i===3 && x[0]==='R') ? ['R','Aleluia, aleluia.'] : x);
}
function textosPascua(o){
  if(!o || typeof o!=='object') return o;
  const out={...o};
  if(Array.isArray(o.salmodia)) out.salmodia=o.salmodia.map(g=>g && g.ant && !tieneAleluia(g.ant) ? {...g, ant:conAleluia(g.ant)} : g);
  for(const k of ['ant_benedictus','ant_magnificat','inv_ant','ant']) if(typeof o[k]==='string' && !tieneAleluia(o[k])) out[k]=conAleluia(o[k]);
  if(o.responsorio) out.responsorio=respPascua(o.responsorio);
  for(const k of ['primeras','tercia','sexta','nona','invitatorio']) if(o[k] && typeof o[k]==='object' && !Array.isArray(o[k])) out[k]=textosPascua(o[k]);
  return out;
}
// Nota al comienzo de la hora: qué es propio y de dónde sale lo demás («Himno, lectura breve y oración propios; lo
// demás, de San José, esposo de la bienaventurada Virgen María (19 de marzo).»). o: lo propio; resto: «de …», «del día»…
const CAMPO_NOTA=[['himno','himno','m'],['salmodia','antífonas','fp'],['lectura1','primera lectura','f'],['lectura2','segunda lectura','f'],
  ['lectura','lectura breve','f'],['responsorio','responsorio','m'],['ant','antífona','f'],['ant_benedictus','antífona del Benedictus','f'],
  ['ant_magnificat','antífona del Magníficat','f'],['preces','preces','fp'],['oracion','oración','f']];
function notaPropios(o, resto){
  const cs=CAMPO_NOTA.filter(c=>o && o[c[0]]!=null);
  if(!cs.length) return resto ? `Textos ${resto}.` : '';
  const ns=cs.map(c=>c[1]), lista=ns.length>1 ? ns.slice(0,-1).join(', ')+' y '+ns[ns.length-1] : ns[0];
  const m=cs.some(c=>c[2]==='m'), pl=cs.length>1 || cs[0][2]==='fp';
  const adj='propi'+(m?'o':'a')+(pl?'s':'');
  return lista[0].toUpperCase()+lista.slice(1)+' '+adj+(resto ? `; lo demás, ${resto}.` : '.');
}
// «de San José, esposo de la bienaventurada Virgen María (19 de marzo)»: la celebración de la que se toma lo que falta
function deCelebracion(nombre, e){
  const f=/^(\d\d)-(\d\d)$/.exec((e&&e.fecha)||'');
  return 'de '+nombre+(f ? ` (${+f[2]} de ${MESES[+f[1]-1]})` : '');
}
/* ---------- Comunes de los santos (botón del inicio) ----------
   Para celebrar a un santo que no está en el calendario: el común y el caso se eligen en dos desplegables; el grado, en
   otro. Cada caso lleva un nombre genérico («San N., obispo») con el que el motor elige solo, como para cualquier
   celebración, las variantes con rúbrica, el masculino o femenino y el singular o plural; en los textos queda «N.».
   «or»: qué oración del común va primero (por su «para»). Las demás opciones de cada elemento se eligen en la hora. */
const modo={};   // modos del inicio: difuntos, comun (y el invitatorio a elección)
const COMUNES_SANTOS=[
  {n:'Común de la dedicación de una iglesia', c:'Blanco', casos:[
    {n:'En la iglesia dedicada', id:'dedicacion', nombre:'Dedicación de una iglesia', or:/misma iglesia/i},
    {n:'Fuera de la iglesia dedicada', id:'dedicacion', nombre:'Dedicación de una iglesia', or:/fuera de la iglesia/i}]},
  {n:'Común de la Santísima Virgen María', c:'Blanco', casos:[{n:'', id:'virgen-maria', nombre:'Santa María Virgen'}]},
  {n:'Común de apóstoles', c:'Rojo', casos:[{n:'Un apóstol', id:'apostoles', nombre:'San N., apóstol'}, {n:'Varios apóstoles', id:'apostoles', nombre:'Santos N. y N., apóstoles'}]},
  {n:'Común de mártires', c:'Rojo', casos:[
    {n:'Un mártir', id:'un-martir', nombre:'San N., mártir'},
    {n:'Una mártir', id:'un-martir', nombre:'Santa N., mártir', or:/mujer mártir/i},
    {n:'Una virgen mártir', id:'un-martir', nombre:'Santa N., virgen y mártir', or:/mártir virgen/i},
    {n:'Varios mártires', id:'varios-martires', nombre:'Santos N. y N., mártires'},
    {n:'Varias vírgenes mártires', id:'varios-martires', nombre:'Santas N. y N., vírgenes y mártires', or:/mártires vírgenes/i},
    {n:'Varias santas mujeres mártires', id:'varios-martires', nombre:'Santas N. y N., mártires', or:/santas mujeres/i}]},
  {n:'Común de pastores', c:'Blanco', casos:[
    {n:'Un papa', id:'pastores', nombre:'San N., papa', or:/papa/i},
    {n:'Un obispo', id:'pastores', nombre:'San N., obispo', or:/obispo/i},
    {n:'Un presbítero', id:'pastores', nombre:'San N., presbítero', or:/santo pastor/i},
    {n:'Un fundador de una Iglesia', id:'pastores', nombre:'San N., obispo', or:/fundador/i},
    {n:'Un misionero', id:'pastores', nombre:'San N., misionero', or:/misionero/i}]},
  {n:'Común de doctores de la Iglesia', c:'Blanco', casos:[
    {n:'Un doctor', id:'doctores', nombre:'San N., doctor de la Iglesia'},
    {n:'Una doctora', id:'doctores', nombre:'Santa N., doctora de la Iglesia'}]},
  {n:'Común de vírgenes', c:'Blanco', casos:[
    {n:'Una virgen', id:'virgenes', nombre:'Santa N., virgen'},
    {n:'Varias vírgenes', id:'virgenes', nombre:'Santas N. y N., vírgenes', or:/varias/i}]},
  {n:'Común de santos varones', c:'Blanco', casos:[
    {n:'Un santo', id:'santos-varones', nombre:'San N.'},
    {n:'Varios santos', id:'santos-varones', nombre:'Santos N. y N.', or:/varios santos/i},
    {n:'Un religioso', id:'religiosos', nombre:'San N., religioso', or:/religioso/i},
    {n:'Un abad', id:'religiosos', nombre:'San N., abad', or:/abad/i},
    {n:'Obras de misericordia', id:'caridad', nombre:'San N.', or:/misericordia|caritativ/i},
    {n:'Un educador', id:'educadores', nombre:'San N., educador', or:/educador/i}]},
  {n:'Común de santas mujeres', c:'Blanco', casos:[
    {n:'Una santa', id:'santas-mujeres', nombre:'Santa N.'},
    {n:'Varias santas', id:'santas-mujeres', nombre:'Santas N. y N.', or:/varias santas/i},
    {n:'Una religiosa', id:'religiosos', nombre:'Santa N., religiosa', or:/religios/i},
    {n:'Obras de misericordia', id:'caridad', nombre:'Santa N.', or:/misericordia|caritativ/i},
    {n:'Una educadora', id:'educadores', nombre:'Santa N., educadora', or:/educador/i}]},
];
// Lo que pide el modo «común»: {g: índice del común, c: índice del caso, grado, primeras} → datos para el motor
function comunSantos(sel){
  const G=COMUNES_SANTOS[sel.g]||COMUNES_SANTOS[0], C=G.casos[sel.c]||G.casos[0];
  return {...C, grupo:G.n, color:G.c, titulo:G.n+(C.n?': '+C.n.toLowerCase():''), grado:sel.grado||'Memoria', primeras:!!sel.primeras};
}
// «salmo-62-2-9» → «Sal 62»; «cantico-is-38-10-14-17-20» → «Is 38»
function citaSalmo(k){
  const m=/^salmo-(\d+)(?:-([a-z]+))?/.exec(k||''); if(m) return 'Sal '+m[1]+(m[2]&&m[2].length<3?' '+m[2].toUpperCase():'');
  const c=/^cantico-(\d?[a-z]+)-(\d+)/.exec(k||''); if(c) return c[1][0].toUpperCase()+c[1].slice(1)+' '+c[2];
  return k||''; }
// Vista previa breve de un texto (para la lista de opciones)
function vista(t){
  const corta=s=>{ s=String(s||'').replace(/\s+/g,' ').trim(); if(s.length<=110) return s; const c=s.slice(0,110); return c.slice(0, c.lastIndexOf(' '))+'…'; };
  if(t==null) return '';
  if(typeof t==='string') return corta(t);
  if(Array.isArray(t) && t[0] && t[0].salmo) return corta(t.map(g=>citaSalmo(g.salmo)).join(' · '));   // salmodia: sus salmos
  if(Array.isArray(t)) return vista(Array.isArray(t[0]) ? t[0][1] : t[0]);
  if(t.preces && t.preces[0]) return corta(t.preces[0][0]);   // preces: la primera (la introducción suele ser la misma)
  if(t.titulo) return corta((t.ref?t.ref+' · ':'')+oracionCase(t.titulo));
  if(t.vr) return vista(t.vr);
  if(t.intro) return corta(t.intro+' '+(t.respuesta||''));
  if(t.texto) return corta((t.ref?t.ref+' · ':'')+t.texto);
  return '';
}
// Todas las opciones de un elemento del común (el texto principal, las «O bien» y las variantes del libro), con su rótulo.
// sub: 'primeras' (si no lo trae, lo de siempre) o la hora menor ('tercia'…). Si el común no lo trae, el común del que hereda.
function opcionesComun(comunes, id, nombre, pascua, campo, sub){
  const c0=comunes && comunes[id]; if(!c0) return [];
  const fem=/^(Santa|Santas|Beata|Beatas)\b/.test(String(nombre||''));
  const de=src=>{ const L=[], tiene=src && (src[campo]!=null || (src.opciones||{})[campo] || (src.variantes||{})[campo]);
    if(!tiene) return L;
    if(src[campo]!=null) L.push({n:'', t:src[campo], p:(src.pascua||{})[campo]});
    for(const t of (src.opciones||{})[campo]||[]) L.push({n:'', t});
    for(const v of (src.variantes||{})[campo]||[]){ const e=String(v.etiqueta||'').trim();
      L.push({n:/^opcion/i.test(e) ? '' : e.replace(/:\s*$/,'').replace(/^O bien,?\s*/i,'').replace(/^./,x=>x.toUpperCase()), t:v.texto}); }
    return L; };
  let L=de(sub ? c0[sub] : c0);
  if(!L.length && sub==='primeras') L=de(c0);
  if(!L.length){ const h=(fem && c0.hereda_mujeres) || c0.hereda; return h ? opcionesComun(comunes, h, nombre, pascua, campo, sub) : []; }
  // Las «opciones» que son el mismo texto en otra traducción (diferencias entre tomos: la misma cita, o casi las mismas
  // palabras) no se ofrecen aparte, salvo que tengan rúbrica propia
  const pals=x=>new Set(String(typeof x==='string' ? x : vista(x)).toLowerCase().match(/\p{L}+/gu)||[]);
  const igual=(a,b)=>{ if(a.t&&b.t&&a.t.ref&&a.t.ref===b.t.ref) return true;
    const A=pals(a.t), B=pals(b.t); let c=0; for(const w of A) if(B.has(w)) c++; return A.size && B.size && c/Math.max(A.size,B.size)>=0.6; };
  const vistos=new Set(), out=[];
  L.forEach(a=>{
    const raw=conNombre({[campo]:a.t}, nombre)[campo];
    const t=!pascua ? raw : a.p!=null ? conNombre({[campo]:a.p}, nombre)[campo] : textosPascua({[campo]:raw})[campo];
    const k=JSON.stringify(t); if(vistos.has(k)) return; vistos.add(k);
    if(!a.n && campo!=='himno' && campo!=='salmodia' && out.some(b=>igual(b,a))) return;
    out.push({n:a.n, t, raw});
  });
  let i=0; return out.map(a=>({...a, n:a.n || 'Opción '+(++i)}));
}
// Parecido entre dos textos (0 a 1): palabras en común sobre las del más largo
function parecido(a, b){
  const pals=x=>new Set(JSON.stringify(x).toLowerCase().match(/\p{L}{3,}/gu)||[]);
  const A=pals(a), B=pals(b); if(!A.size || !B.size) return 0;
  let c=0; for(const w of A) if(B.has(w)) c++; return c/Math.max(A.size, B.size);
}
// Deja en P lo elegido para cada elemento del común que tiene opciones y anota las opciones para la app
// (alts[hora|campo] = {i, ops}): en el modo «común» (modo.comun) y también en las celebraciones y el Oficio de difuntos
// que toman del común, donde las «O bien» rotan (modo.opc: lo que eligió el motor, con el botón «Otras opciones»).
// Sin elección, queda lo que el motor eligió solo.
function elegirComun(P, campos, comunes, id, nombre, pascua, sub, hora){
  const M=modo.comun||modo.opc; if(!M || !id) return;
  M.alts=M.alts||{};
  for(const c of campos){
    if(P[c]==null) continue;
    const L=opcionesComun(comunes, id, nombre, pascua, c, sub), j=JSON.stringify(P[c]);
    let i=L.findIndex(a=>JSON.stringify(a.t)===j || JSON.stringify(a.raw)===j);
    // el texto de la celebración (sync) puede ser el del común con otra traducción o pequeñas diferencias: el más parecido
    if(i<0){ let m=0; L.forEach((a,k)=>{ const x=parecido(a.t, P[c]); if(x>m){ m=x; i=k; } }); if(m<0.75) i=-1; }
    if(i<0 || L.length<2) continue;
    L[i]={...L[i], t:P[c]};
    const k=hora+'|'+c, e=(M.elige||{})[k];
    if(e!=null && L[e]){ P[c]=L[e].t; i=e; }
    // salmodia: las opciones difieren en algún salmo; el botón va debajo de la antífona de ese salmo
    if(c==='salmodia'){ const dif=P[c].map((g,gi)=>gi).filter(gi=>L.some(a=>JSON.stringify((a.t||[])[gi])!==JSON.stringify(L[0].t[gi])));
      M.alts[k]={i, dif, ops:L.map(a=>({n:a.n, ver:dif.map(gi=>{ const g=(a.t||[])[gi]||{}; return citaSalmo(g.salmo)+(g.ant?' · '+g.ant:''); }).join(' / ')}))};
    } else M.alts[k]={i, ops:L.map(a=>({n:a.n, ver:vista(a.t)}))};
  }
}
// La oración del común en el modo «común»: la del caso («or») o, si no hay, la que elige el motor (sin las de otro
// tiempo: en el común de la Virgen, la de Adviento o la de Navidad solo en su tiempo); las demás, a elección.
// Fuera del modo «común» (modo.opc), la que elige el motor en su turno (n) y las demás, en «Otras opciones».
function oracionElegida(oraciones, nombre, hora, t, n){
  const M=modo.comun||modo.opc; if(!M || !oraciones || !oraciones.length) return oracionComun(oraciones, nombre, n||0);
  const ok=oraciones.filter(o=>o.texto && o.texto.length>40 && !/^\p{Ll}/u.test(o.texto));   // (no las truncas ni los restos de otra)
  if(!ok.length) return oracionComun(oraciones, nombre, n||0);
  const tdo=o=>(/^tiempo de (\S+)/i.exec(o.para||'')||[])[1], ajena=o=>tdo(o) && tdo(o).toLowerCase()!==String(t||'').toLowerCase();
  const propia=ok.find(o=>tdo(o) && !ajena(o)), porCaso=M.or && ok.find(o=>M.or.test(o.para||''));
  const pre=propia || porCaso || null;
  const ops=ok.map(o=>({n:!o.para ? '' : /^(tiempo|cuando)/i.test(o.para) ? o.para : 'Para '+o.para, t:oracionComun([o], nombre, 0)}))
    .filter((o,i,a)=>a.findIndex(x=>x.t===o.t)===i);   // (el libro repite alguna)
  const def=!modo.comun ? oracionComun(oraciones, nombre, n||0) : pre ? oracionComun([pre], nombre, 0) : oracionComun(ok.filter(o=>!ajena(o)), nombre, 0);
  let i=ops.findIndex(o=>o.t===def), j=0; ops.forEach(o=>{ if(!o.n) o.n='Opción '+(++j); });
  if(ops.length<2 || i<0) return def;
  const k=hora+'|oracion', e=(M.elige||{})[k]; if(e!=null && ops[e]) i=e;
  M.alts=M.alts||{}; M.alts[k]={i, ops:ops.map(o=>({n:o.n, ver:vista(o.t)}))};
  return ops[i<0?0:i].t;
}
// Himnos latinos recitados (base/himnos/latinos.yaml; cuándo va cada uno: latinos_cuando.yaml), como opciones después del
// himno en español y del gregoriano. ref: el día del oficio (en las I Vísperas, mañana). o: {hs: himnos latinos de la hora,
// comun: clave del común si el himno en español es del común, primeras, tiempo: true/false si la hora sabe si su himno es
// del tiempo (si no, por el nombre de la celebración), greg: título del gregoriano del día}. Devuelve las opciones (ids
// «lat», «lat2»…), con las estrofas del caso (papa, obispo, presbítero; una santa o varias; una difunta o varios).
// El común (de cids, en orden) que trae este himno en español, en cualquier hora o variante: para las celebraciones con
// propio en la base cuyo himno es el del común que indica su santoral (el himno latino, entonces, también del común)
function comunDelHimno(comunes, himno, cids){
  const tiene=o=>o && typeof o==='object' && Object.entries(o).some(([k,v])=> (k==='himno' && [].concat(v).includes(himno)) || (typeof v==='object' && tiene(v)));
  return (cids||[]).find(c=>c && comunes && tiene(comunes[c])) || null;
}
const RUB_LAZARO='Si se rezan las tres Horas: Tercia, estrofas 1, 4 y 5; Sexta, 2, 4 y 5; Nona, 3, 4 y 5.';
function himnosLatinos(hora, ref, o){
  const C=B.latinos_cuando, hs=(o&&o.hs)||{}; o=o||{};
  if(!C || !ref) return [];
  const de=t=>{ if(!t) return null; const v=(o.primeras && t[hora+'1']) || t[hora]; return v==null ? null : [].concat(v); };
  const nombre=String(ref.n||''), plural=/^(santos|santas|beatos|beatas)\b|y compañer/i.test(nombre), fem=/^(Santa|Santas|Beata|Beatas)\b/.test(nombre);
  let lista=null, casos=[''];
  // Propios del santo o de la solemnidad (segunda etapa): mandan sobre el común y el tiempo en las horas que traen
  const pr=(C.propios||{})[nombre];
  if(pr && de(pr) && hora!=='completas') lista=de(pr);
  else if(o.comun){
    let c=o.comun;
    if(c==='difuntos') casos = ref.n==='Todos los Fieles Difuntos' ? ['varios'] : ['', 'una', 'varios'];
    if(c==='caridad' || c==='educadores' || (c==='religiosos' && plural)) c = fem ? 'santas-mujeres' : 'santos-varones';
    if(c==='doctores' && fem) c='virgenes';   // doctoras: los de vírgenes (el de doctores habla de un varón)
    if(c==='un-martir' && fem) c='una-martir';
    if(c==='apostoles' && ref.t==='Pascua') c='apostoles_pascua';
    lista = (plural && de(C.comunes[c+(fem?'_varias':'_varios')])) || de(C.comunes[c]);
    if(c!=='difuntos') casos=[ /\bpapa\b/i.test(nombre) ? 'papa' : /\bobispo/i.test(nombre) ? 'obispo' : /presbítero|sacerdote/i.test(nombre) ? 'presbitero'
      : fem ? (plural ? 'mujeres' : 'mujer') : '' ];
  } else {
    const delTiempo = o.tiempo!=null ? o.tiempo : (ref.n===ref.fer || ref.t==='Triduo' || (C.del_tiempo||[]).includes(ref.n));
    if(!delTiempo) return [];
    const f=ref.fecha||'', md=f.slice(5), y=+f.slice(0,4);
    let t=null;
    if(ref.t==='Adviento') t = md>='12-17' ? 'adviento_17' : 'adviento';
    else if(ref.t==='Navidad') t = (md>='12-01' || md<='01-05') ? 'navidad' : 'epifania';
    else if(ref.t==='Cuaresma') t = ref.sem>=6 ? 'semana_santa' : hora==='completas' ? ((ref.sal||1)%2 ? 'cuaresma_completas_impar' : 'cuaresma_completas_par')
      : ref.dom ? 'cuaresma_domingo' : ref.sem===5 ? 'cuaresma_semana_5' : 'cuaresma_feria';
    else if(ref.t==='Triduo') t='semana_santa';
    else if(ref.t==='Ordinario'){   // por la semana del salterio (I y III, II y IV) y el día
      const par=!((ref.sal||1)%2) ? 'par' : 'impar', dia=new Date(f+'T12:00:00Z').getUTCDay();
      t = C.tiempo['ordinario_'+par+'_'+dia] && de(C.tiempo['ordinario_'+par+'_'+dia]) ? 'ordinario_'+par+'_'+dia : 'ordinario_'+par; }
    else if(ref.t==='Pascua'){ const asc=masDias(domPascua(y), 39);
      t = ref.n==='Ascensión del Señor' ? 'ascension' : f>asc ? (ref.dom ? 'ascension' : 'ascension_ferias') : (ref.oct || ref.dom) ? 'pascua' : 'pascua_ferias'; }
    lista = de(C.celebraciones[ref.n]) || de(C.tiempo[t]);
  }
  const out=[], norm=x=>String(x||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-zæœ ]/g,'').trim();
  const SUF={una:' (una difunta)', varios:' (varios difuntos)'};
  for(const k of lista||[]) for(const c of casos){
    const h=hs[k]; if(!h) continue;
    const v=(c && h.variantes && h.variantes[c]) || {};
    const est=h.estrofas.map((e,i)=>v[i]||e);
    const tit = v[0] ? v[0][0][0].replace(/[,;:.]+$/,'') : h.titulo;   // si cambia la primera estrofa («Beáta martyr»), su primer verso
    const rot = hora==='oficio' && Object.keys(C.rotulos||{}).find(r=>(C.rotulos[r]||[]).includes(k));
    out.push({id:'lat'+(out.length?out.length+1:''), n:tit+(rot?' ('+rot+')':'')+(SUF[c]||'')+(o.greg && norm(o.greg)===norm(tit) ? ' (recitado)' : ''), lang:'la', lat:true,
              est:est.map(e=>e.map(p=>p[0])), lit:est.map(e=>e.map(p=>p[1])), amen:h.amen?'Amen.':'', rub:k==='qui-lacrimatus-lazarum'?RUB_LAZARO:''});
  }
  return out;
}
// Los himnos de un común para una hora: el primero (el de sync) y las otras opciones, que la hora ofrece como botones.
// hs: los himnos de la hora (por título); sin el que ya va, ni los que la hora no tiene.
function himnosComun(comunes, id, nombre, sub, actual, hs){
  const l=opcionesComun(comunes, id, nombre, false, 'himno', sub).map(a=>a.t).filter(x=>typeof x==='string' && hs && hs[x]);
  return l.includes(actual) ? l.filter(x=>x!==actual) : [];
}
window.Completas={armar, diaCal, opcionesDia, enRango, iso, deIso, masDias, ciclo, ilustracion, franjaHoraria, calendarios:CAL.calendarios,
  _:{modo, marcarLectura, marcarPrece, pasion, parecido, NO_GLORIA, sinGloriaResp, esGloriaLa, domPascua, COMUNES_SANTOS, comunSantos, opcionesComun, elegirComun, himnosComun, himnosLatinos, comunDelHimno, oracionElegida, textosPascua, notaPropios, deCelebracion, oracionComun, comunDe, esDoctor, comun, rubricaVale, enPascua, turno, alternativas, fechaClave, anioBienal, invocacionGabc, recInvocacion, gregPropio, enLineas, recitado, versosDe, oracionCase, pares, enVersos, DIAS, DIAS_TXT, MESES, TIEMPO_TXT, ROMANO}};   // para las otras horas (laudes.js)
})();
