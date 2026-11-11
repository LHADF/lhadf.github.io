/* ================== Armado de Laudes para cualquier fecha ==================
   Datos: window.LAUDES (src/carga/laudes.js, se carga recién al abrir Laudes), window.BASE y window.CAL.
   Capas: salterio de cuatro semanas → propio del tiempo (por feria; en domingo, con ciclo A/B/C) → santoral.
   Decisiones ADF en docs/laudes.md. */
(function(){
const CP=window.Completas, X=CP._;
const CAMPOS=['inv_ant','himno','salmodia','lectura','responsorio','ant_benedictus','ant_magnificat','preces','padrenuestro_intro','oracion','en_lugar_del_responsorio','pendiente'];
const SIN_GLORIA=['cantico-dn-3-57-88-56'];   // el cántico de Daniel 3, 57-88 no lleva Gloria

// Ciclo dominical del año litúrgico (empieza el I Domingo de Adviento)
function ciclo(fecha){
  const d=CP.deIso(fecha);
  const adv=y=>{ const n=new Date(y,11,25,12); n.setDate(n.getDate()-(n.getDay()||7)-21); return n; };
  const y = d>=adv(d.getFullYear()) ? d.getFullYear() : d.getFullYear()-1;
  return 'ABC'[(((y-2016)%3)+3)%3];
}

// Las partes del día, capa sobre capa. hora: 'laudes' | 'visperas'.
// Vísperas: si mañana tiene I Vísperas (domingo o solemnidad) y hoy no es de mayor rango, se rezan las primeras de mañana.
function propio(hora, fecha, region){
  const L=window[hora.toUpperCase()], hoyC=CP.diaCal(fecha, region), CE=hora==='laudes'?'ant_benedictus':'ant_magnificat';
  const fm=CP.masDias(fecha,1), man=(hora==='visperas' && CP.enRango(fm)) ? CP.diaCal(fm, region) : null;
  const calc=primeras=>{
    const ref=primeras?man:hoyC, fRef=primeras?fm:fecha;
    const d=CP.deIso(fRef), dom=d.getDay()===0, dia=X.DIAS[d.getDay()];
    const P={}, capa=o=>{ if(o) for(const k of CAMPOS) if(o[k]!=null) P[k]=o[k]; };
    const I=primeras?' · I Vísperas':'';
    const semana=L.salterio['semana_'+(ref.sal||1)];
    // (Vísperas no tiene «sábado» en el salterio: esa tarde es del domingo; una solemnidad en sábado toma lo del domingo I)
    capa(primeras ? (dom ? semana.domingo_1 : L.salterio.semana_1.domingo_1) : (semana[dia] || L.salterio.semana_1.domingo));
    const T1=L.tiempo[ref.fer+I], T2=L.tiempo[`${ref.fer} (${ciclo(fRef)})${I}`];
    capa(T1); capa(T2);   // (con ciclo: los domingos y las solemnidades que alguna vez cayeron en domingo)
    const salmodiaPropia=!!((T1&&T1.salmodia)||(T2&&T2.salmodia));
    let santo=null, nota='';
    const k=L.mapa[ref.n];
    if(k){ santo=L.santoral[k+I]||(primeras?null:L.santoral[k]); if(santo){ delete P.pendiente; capa(santo); }
           else if(primeras){ capa(L.santoral[k]); delete P.salmodia; }   // I Vísperas sin propio: lo de la celebración, con otros salmos
    } else if(ref.n!==ref.fer){
      nota='El propio de esta celebración todavía no está en la base: se reza el oficio del día.'; }
    // Fiestas y solemnidades sin salmodia propia: salmos y antífonas del domingo de la I semana
    if(/^(Fiesta|Solemnidad)/.test(ref.g) && !(santo&&santo.salmodia) && !salmodiaPropia && !(dom && !k)) P.salmodia=L.salterio.semana_1[primeras?'domingo_1':'domingo'].salmodia;
    if(!P.salmodia) P.salmodia=(semana[dia]||L.salterio.semana_1.domingo).salmodia;
    return {P, dia, nota, hoy:ref, fRef, primeras, completo:!!(P[CE] && P.oracion && !P.pendiente)};
  };
  // Vísperas: si mañana tiene I Vísperas (domingo o solemnidad) y hoy no es de mayor rango, se rezan las primeras de mañana.
  const quiere = !!(man && man.pv && !(hoyC.sol && !man.sol) && hoyC.t!=='Triduo');
  let r=calc(quiere);
  if(!r.completo && man && hoyC.t!=='Triduo'){   // sin textos para lo elegido: la otra posibilidad (hoy, o las I Vísperas de mañana si es domingo o solemnidad)
    const otra = quiere ? calc(false) : ((man.dom||man.sol) ? calc(true) : null);
    if(otra && otra.completo){ if(quiere) otra.nota='Las I Vísperas de mañana todavía no tienen propio en la base: se rezan las del día.'; r=otra; }
  }
  if(!r.completo) r.nota='Faltan textos propios de este día (antífona del cántico evangélico u oración): están marcados para completar.';
  return r;
}

function armar(hora, fecha, region){
  const L=window[hora.toUpperCase()]; if(!L) return null;
  if(!CP.diaCal(fecha, region)) return null;
  const B=window.BASE, GR=B.completas.gregoriano, GL=L.gregoriano, LAU=hora==='laudes';
  const {P, dia, nota, hoy, fRef, primeras}=propio(hora, fecha, region);
  const cuaresma=hoy.t==='Cuaresma'||hoy.t==='Triduo';
  const solemne=!!(hoy.sol||hoy.dom||hoy.t==='Triduo'||hoy.oct);
  const S=[]; const sec=(id,t,extra)=>S.push({k:'sec',id,t,...extra});
  const salmo=(sid, ant)=>{ const s=L.salmos[sid]; const v=X.versosDe(s.texto);
    return {k:'salmo', es:true, id:sid, ant, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!SIN_GLORIA.includes(sid)}; };

  // Invitatorio: solo los domingos (ADF). Dómine, lábia mea; antífona y Salmo 94; después, el Deus in adiutórium.
  // Todos los días se empieza con «Dómine, lábia mea apéries»; el invitatorio (antífona y Salmo 94), solo los domingos.
  const labia=LAU && {k:'vr', gabc:GL.invitatorio.gabc, glosa:GL.invitatorio.traduccion, rec:X.recitado(GL.invitatorio.traduccion, [['V','Dómine,'],['R','Et',true]])};
  if(LAU && CP.deIso(fecha).getDay()===0){
    sec('invitatorio','Invitatorio');
    S.push(labia);
    S.push({k:'ant', id:'ai', es:true, n:'Ant.', t:{es:P.inv_ant}});
    const s94=L.ordinario.invitatorio.salmo, v=X.versosDe(s94.texto);
    S.push({k:'salmo', es:true, id:'salmo-94', ant:'ai', titulo:{es:s94.titulo}, lema:{es:X.oracionCase(s94.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:true});
    S.push({k:'ant', rep:'ai', es:true});
  }

  sec('inicio','Invocación inicial');
  if(LAU && CP.deIso(fecha).getDay()!==0) S.push(labia);
  const tono = solemne ? 'solemne' : /^Fiesta/.test(hoy.g) ? 'festivo' : 'ferial';
  const trInv=cuaresma ? GR.invocacion.traduccion.filter(p=>!/^Allel/.test(p[0])).concat(GR.invocacion.laus) : GR.invocacion.traduccion;
  S.push({k:'vr', tono, gabc:X.invocacionGabc(tono, !cuaresma), glosa:trInv,
          rec:X.recInvocacion(trInv)});

  sec('himno','Himno');
  const H=L.himnos[P.himno]||[];
  S.push({k:'himno', es:true, opciones:[{id:hora, n:P.himno, lang:'es', est:H.map(e=>e.split('\n')), amen:''}]});

  sec('salmodia','Salmodia');
  (P.salmodia||[]).forEach((g,gi)=>{
    const id='a'+(gi+1);
    S.push({k:'ant', id, es:true, n:`Ant. ${gi+1}`, t:{es:g.ant}, modo:'8G'});
    S.push(salmo(g.salmo, id));
    S.push(g.ant_fin ? {k:'ant', id:id+'f', es:true, n:`Ant. ${gi+1}`, t:{es:g.ant_fin}} : {k:'ant', rep:id, es:true});
  });

  sec('lectura','Lectura breve',{ref:P.lectura.ref});
  S.push({k:'lectura', es:true, t:{es:P.lectura.texto}});
  S.push({k:'deo', t:GR.lectura_respuesta[0][0]});

  if(P.en_lugar_del_responsorio){
    sec('responsorio','En lugar del responsorio breve');
    S.push({k:'ant', id:'rb', es:true, n:'Ant.', t:{es:P.en_lugar_del_responsorio}});
  } else {
    sec('responsorio','Responsorio breve');
    S.push({k:'resp', es:true, l:{es:P.responsorio}});
  }

  sec('cantico','Cántico evangélico',{ref:GL.cantico.ref});
  const BN=GL.cantico;
  S.push({k:'ant', id:'ab', es:true, n:'Ant.', t:{es:(LAU?P.ant_benedictus:P.ant_magnificat)||'[falta la antífona]'}});
  S.push({k:'cantico', titulo:BN.titulo, versos:BN.versos, inter:BN.traduccion_versos});
  S.push({k:'ant', rep:'ab', es:true});

  sec('preces','Preces');
  S.push({k:'preces', es:true, ...P.preces});

  sec('padrenuestro','Padre nuestro');
  S.push({k:'pater', intro: (dia==='domingo' || /^(Fiesta|Solemnidad)/.test(hoy.g) || primeras) ? (P.padrenuestro_intro||'') : '', pares:GL.pater_noster, lineas:X.enLineas(GL.pater_noster, GL.pater_cortes)});   // monición (la del día) solo en domingos, fiestas y solemnidades

  sec('oracion','Oración');
  S.push({k:'prosa', es:true, t:{es:P.oracion||'[falta la oración]'}, amen:{es:'Amén.'}});

  sec('bendicion','Conclusión');
  // Sin ministro ordenado: «Dóminus nos benedícat»; con ministro ordenado: «Dóminus vobíscum… Benedícat vos» (tono B en domingos y solemnidades)
  const cruz=(tr,pal)=>tr.map(p=>p[0]===pal?['✠ '+p[0],p[1]]:p), TB=GL.bendicion.traduccion, iEt=TB.map(p=>p[0]).indexOf('et');
  S.push({k:'conclusion', opciones:[
    {id:'laico', n:'Sin ministro ordenado', gabc:GL.conclusion.gabc, glosa:GL.conclusion.traduccion, rec:X.recitado(cruz(GL.conclusion.traduccion,'nos'), [['V','Dóminus'],['R','Amen.',true]])},
    {id:'ministro', n:'Con ministro ordenado', gabc:GL.bendicion[solemne?'solemne':'simple'], glosa:TB,
     rec:X.recitado(TB.map((p,i)=>i===iEt?['✠ '+p[0],p[1]]:p), [['V','Dóminus'],['R','Et',true],['V','Benedícat'],['R','Amen.',true]]),
     despues:X.recitado(GL.bendicion.despedida, [['V','Ite'],['R','Deo',true]])}]});   // «Ite in pace»: sin partitura por ahora

  const d=CP.deIso(fecha);
  return {
    hora, nombre:LAU?'Laudes':'Vísperas', primeras,
    versiones:{es:{n:'Liturgia de las Horas'}},
    gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']},
    dia:{titulo:hoy.n+(primeras?' · I Vísperas':''), tiempo:X.TIEMPO_TXT[hoy.t]||hoy.t, salterio: hoy.sal?`Semana ${X.ROMANO(hoy.sal)} del salterio`:'', color:hoy.c, grado:hoy.g, nota},
    fechaTxt:`${X.DIAS_TXT[d.getDay()]} ${d.getDate()} de ${X.MESES[d.getMonth()]}`,
    secciones:S,
  };
}

window.Laudes={armar:(f,r)=>armar('laudes',f,r), ciclo, propio};
window.Visperas={armar:(f,r)=>armar('visperas',f,r), propio};
})();
