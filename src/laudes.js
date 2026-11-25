/* ================== Armado de Laudes para cualquier fecha ==================
   Datos: window.LAUDES (src/carga/laudes.js, se carga recién al abrir Laudes), window.BASE y window.CAL.
   Capas: salterio de cuatro semanas → propio del tiempo (por feria; en domingo, con ciclo A/B/C) → santoral.
   Decisiones ADF en docs/laudes.md. */
(function(){
const CP=window.Completas, X=CP._;
const CAMPOS=['inv_ant','himno','salmodia','lectura','responsorio','ant_benedictus','ant_magnificat','preces','padrenuestro_intro','oracion','en_lugar_del_responsorio','pendiente'];
const SIN_GLORIA=['cantico-dn-3-57-88-56'];   // el cántico de Daniel 3, 57-88 no lleva Gloria

const ciclo=CP.ciclo;   // ciclo dominical A/B/C (completas.js)

// Modo de la salmodia (docs/laudes.md, docs/salmodia.md): uno por semana del salterio para las ferias y otro para cada
// domingo; el mismo para todos los salmos y cánticos de la hora y para el cántico evangélico. Las solemnidades siguen el
// ritmo de la semana en que caen (CRU): un martes de la semana II, el modo de las ferias de la II.
// Días que el calendario deja sin semana del salterio (CRU):
//  - Ascensión y Pentecostés: la semana en que caen (de domingo a sábado): en domingo, el modo de ese domingo; la Ascensión
//    en jueves, el de las ferias de esa semana;
//  - Navidad (tiempo de Navidad) y Pascua (domingo y octava): modo 1 g;
//  - Viernes y Sábado Santo: modo 4 g.
const MODOS={domingo:{1:'1g',2:'3a',3:'6F',4:'7a'}, feria:{1:'2D',2:'4g',3:'5a',4:'8G'}};
function semanaDe(ref, fRef){
  if(ref.sal) return ref.sal;
  const dom=CP.masDias(fRef, -CP.deIso(fRef).getDay());   // domingo de esa semana
  for(let k=0;k<7;k++){ const f=CP.masDias(dom,k); if(f===fRef || !CP.enRango(f)) continue; const d=CP.diaCal(f,''); if(d && d.sal) return d.sal; }
  return 1;
}
function modoDe(ref, fRef){
  if(!ref.sal && !/Ascensi[oó]n|Pentecost[eé]s/i.test(ref.n||'')){
    if(ref.t==='Triduo') return '4g';
    if(ref.t==='Navidad' || ref.t==='Pascua') return '1g';
  }
  const dom = CP.deIso(fRef).getDay()===0;
  return MODOS[dom?'domingo':'feria'][semanaDe(ref,fRef)] || MODOS[dom?'domingo':'feria'][1];
}

// Las partes del día, capa sobre capa. hora: 'laudes' | 'visperas'.
// Vísperas: si mañana tiene I Vísperas (domingo o solemnidad) y hoy no es de mayor rango, se rezan las primeras de mañana.
function propio(hora, fecha, region){
  const L=window[hora.toUpperCase()], hoyC=CP.diaCal(fecha, region), CE=hora==='laudes'?'ant_benedictus':'ant_magnificat';
  const fm=CP.masDias(fecha,1), man=(hora==='visperas' && CP.enRango(fm)) ? CP.diaCal(fm, region) : null;
  const calc=primeras=>{
    // Oficio de difuntos (botón del inicio): el día cualquiera, con todo del Oficio de difuntos (base/comunes/, «difuntos»)
    // Comunes de los santos (botón del inicio): el día cualquiera, como la celebración de un santo con todo del común elegido
    // (también sus I Vísperas, si se eligen, el mismo día)
    const DIF=!!X.modo.difuntos, COM=!DIF && X.modo.comun, ref0=(primeras&&!COM)?man:hoyC, fRef=(primeras&&!COM)?fm:fecha;
    const ref=DIF?{...ref0, n:'Oficio de difuntos', g:'Oficio de difuntos', sol:false}
      : COM?{...ref0, n:COM.nombre, g:COM.grado, sol:COM.grado==='Solemnidad', c:COM.color, oct:''} : ref0;
    const d=CP.deIso(fRef), dom=d.getDay()===0, dia=X.DIAS[d.getDay()];
    const P={}, capa=o=>{ if(o) for(const k of CAMPOS) if(o[k]!=null) P[k]=o[k]; };
    const I=primeras?' · I Vísperas':'';
    const semana=L.salterio['semana_'+(ref.sal||1)];
    // (Vísperas no tiene «sábado» en el salterio: esa tarde es del domingo; una solemnidad en sábado toma lo del domingo I)
    capa(primeras ? (dom ? semana.domingo_1 : L.salterio.semana_1.domingo_1) : (semana[dia] || L.salterio.semana_1.domingo));
    const S0=P.salmodia;   // la del Salterio
    const T1=L.tiempo[ref.fer+I], T2=L.tiempo[`${ref.fer} (${ciclo(fRef)})${I}`];
    capa(T1); capa(T2);   // (con ciclo: los domingos y las solemnidades que alguna vez cayeron en domingo)
    // Días con fecha propia dentro del tiempo (del 17 al 24 de diciembre): lo de ese día. Los salmos, los de la feria del
    // Salterio; las antífonas, las del día de la semana («Lunes antes del 24 de diciembre») o las propias del día (24).
    // (Del 7 al 12 de enero, igual: lo de la fecha, porque ADF celebra la Epifanía el 6.) Nunca en domingo.
    const TD=!primeras && !dom && L.tiempo[X.fechaClave(fRef)];
    if(TD){ capa(TD);
      const AS=TD.antifonas ? TD : (/diciembre$/.test(X.fechaClave(fRef)) && L.tiempo[`${X.DIAS_TXT[d.getDay()]} antes del 24 de diciembre`]);
      if(!TD.salmodia && S0 && AS && AS.antifonas) P.salmodia = S0.map((g,i)=>({...g, ant: AS.antifonas[i]||g.ant}));
    }
    const salmodiaPropia=!!((T1&&T1.salmodia)||(T2&&T2.salmodia)||(TD&&TD.salmodia));
    let santo=null, nota='';
    const adf=DIF ? {comun:'difuntos'} : COM ? {comun:COM.id} : (L.adf||{})[ref.n]||{};
    const k=(DIF||COM) ? null : (L.mapa[ref.n] || adf.como);   // «como»: celebración propia de ADF que toma todo de otra de la base
    // «de»: celebración (nombre del calendario) de la que se toma lo que falte (San José obrero, del 19 de marzo)
    const kd=(!DIF && !COM && adf.de && !adf.como) ? (L.mapa[adf.de] || (L.santoral[adf.de] ? adf.de : null)) : null;
    const pas=o=>ref.t==='Pascua' ? X.textosPascua(o) : o;   // tiempo pascual: con «Aleluia»
    const DE=kd ? pas(L.santoral[kd+I] || (primeras ? null : L.santoral[kd])) : null;
    const deTxt=adf.de ? X.deCelebracion(adf.de, L.santoral[kd]||L.santoral[k]) : '';
    const PR0=(ref.t==='Pascua' ? X.textosPascua(X.enPascua(adf.propio)) : adf.propio)||{}, PR=(primeras&&PR0.primeras)?{...PR0,...PR0.primeras}:PR0;
    if(k){ santo=L.santoral[k+I]||(primeras?null:L.santoral[k]);
           if(DE) capa(DE);
           if(santo){ delete P.pendiente; capa(santo); }
           else if(primeras && !DE){ capa(L.santoral[k]); delete P.salmodia; }   // I Vísperas sin propio: lo de la celebración, con otros salmos
           if(DE){ nota=X.notaPropios(santo, deTxt); santo={...DE, ...(santo||{})}; }
           else if(adf.como) nota=deTxt ? `Textos ${deTxt}.` : 'Celebración propia de ADF: por ahora, con los textos de otra celebración de la base (falta la oración propia).';
    } else if(DE){   // sin propio en la base para esta hora: lo propio que haya (libro u oración de Laudes) y lo demás, de la otra celebración
      capa(DE); capa(PR); delete P.pendiente;
      santo={...DE, ...PR};
      nota=X.notaPropios(PR, deTxt);
    } else if((adf.comun && L.comunes && L.comunes[adf.comun]) || adf.propio){
      const n=COM ? 0 : X.turno(L.adf, adf.comun, fRef, region);   // las «O bien» del común se alternan entre celebraciones (en el modo común, se eligen)
      // Sin textos propios en la base: lo propio del libro (base/santoral/libro.yaml) y el resto del común (libro).
      // Memorias: salmos de la feria; fiestas y solemnidades, también los del común. En las I Vísperas, lo de las I Vísperas.
      // Oración: la propia; si no hay, la del común «en su defecto», con el nombre.
      const C0=X.comun(L.comunes, adf.comun, ref.n, ref.t==='Pascua', n)||{nombre:''}, C=(primeras&&C0.primeras)?{...C0,...C0.primeras}:C0, mayor=/^(Fiesta|Solemnidad)/.test(ref.g);
      const CAMPOS=['himno','lectura','responsorio','ant_benedictus','ant_magnificat','preces','padrenuestro_intro','inv_ant'];
      for(const c of CAMPOS) if(C[c]!=null) P[c]=C[c];
      if((mayor || C.salmodia_propia) && C.salmodia){ P.salmodia=C.salmodia; santo={salmodia:C.salmodia}; }   // (el Oficio de difuntos, siempre con sus salmos)
      for(const c of CAMPOS) if(PR[c]!=null) P[c]=PR[c];
      if(PR.salmodia){ P.salmodia=PR.salmodia; santo={salmodia:PR.salmodia}; }
      const HK=hora+(primeras?'1':'');   // clave de la hora para las elecciones del modo común
      // las opciones de cada elemento (en el modo común, a elegir; si no, lo que tocó en la rotación y las demás en «Otras opciones»)
      X.elegirComun(P, [...CAMPOS.filter(c=>c!=='himno' && PR[c]==null), ...(P.salmodia===C.salmodia && !PR.salmodia ? ['salmodia'] : [])], L.comunes, adf.comun, ref.n, ref.t==='Pascua', primeras?'primeras':null, HK);
      // el himno del común: los otros, como opción en la hora (no rotan)
      if(!PR.himno && P.himno===C.himno) P._himnos=X.himnosComun(L.comunes, adf.comun, ref.n, primeras?'primeras':null, P.himno, L.himnos);
      if(!PR.himno && P.himno===C.himno) P._comunLat=adf.comun;   // el himno latino, también del común
      const o=PR.oracion || X.oracionElegida(C.oraciones||C0.oraciones, ref.n, HK, ref.t, n);
      if(o) P.oracion=o;
      delete P.pendiente;
      // lo que falta (sin común): del día. Si está todo, sin nota.
      const todo=['himno','salmodia','lectura','responsorio',CE,'preces','oracion'].every(c=>PR[c]!=null);
      nota = (adf.comun==='santa-maria-sabado' || DIF || COM) ? ''
        : PR.oracion ? (todo ? '' : X.notaPropios(PR, C0.nombre ? `del ${C0.nombre}` : 'del día'))
        : `Textos del ${C0.nombre}`+(o?', con su oración (falta la propia).':'. Falta la oración propia: va la del día.');
    } else if(ref.n!==ref.fer){
      nota='El propio de esta celebración todavía no está en la base: se reza el oficio del día.'; }
    // Celebración con propio en la base que toma textos del común (el santoral dice cuál): donde lo que trae es un texto del
    // común (igual o casi), las otras opciones del común también se pueden elegir («Otras opciones»); lo propio de verdad, no
    if(k && !DE && L.comunes && P.himno && !P._comunLat) P._comunLat=X.comunDelHimno(L.comunes, P.himno, [X.comunDe((L.santoral[k]||{}).comun), X.esDoctor(ref.n)&&'doctores']);
    if(k && !DE && L.comunes){ const cid=X.comunDe((L.santoral[k]||{}).comun);
      if(cid && L.comunes[cid]) X.elegirComun(P, ['lectura','responsorio','ant_benedictus','ant_magnificat','preces','padrenuestro_intro','inv_ant'], L.comunes, cid, ref.n, ref.t==='Pascua', primeras?'primeras':null, hora+(primeras?'1':'')); }
    // Fiestas y solemnidades sin salmodia propia: la del común que indica el santoral (en las I Vísperas, la de sus I Vísperas);
    // si no hay común, salmos y antífonas del domingo de la I semana
    if(/^(Fiesta|Solemnidad)/.test(ref.g) && !(santo&&santo.salmodia) && !salmodiaPropia && !(dom && !k)){
      const CS=k && L.comunes && X.comun(L.comunes, (X.esDoctor(ref.n)&&(adf.comun||'doctores')) || X.comunDe((L.santoral[k]||{}).comun) || adf.comun, ref.n, ref.t==='Pascua'), SC=CS && (primeras ? (CS.primeras||{}).salmodia : CS.salmodia);
      P.salmodia=SC || L.salterio.semana_1[primeras?'domingo_1':'domingo'].salmodia;
    }
    if(!P.salmodia) P.salmodia=(semana[dia]||L.salterio.semana_1.domingo).salmodia;
    // Antífonas «Oh» (del 17 al 23 de diciembre): se dicen todas las tardes, también en las I Vísperas del domingo
    if(hora==='visperas'){ const O=L.tiempo[X.fechaClave(fecha)]; if(O && O.ant_magnificat && /^Oh /.test(O.ant_magnificat)) P.ant_magnificat=O.ant_magnificat; }
    return {P, dia, nota, hoy:ref, fRef, primeras, completo:!!(P[CE] && P.oracion && !P.pendiente)};
  };
  // Vísperas: si mañana tiene I Vísperas (domingo o solemnidad) y hoy no es de mayor rango, se rezan las primeras de mañana.
  const quiere = X.modo.comun ? !!X.modo.comun.primeras : !X.modo.difuntos && !!(man && man.pv && !(hoyC.sol && !man.sol) && hoyC.t!=='Triduo');
  let r=calc(quiere);
  if(!r.completo && man && hoyC.t!=='Triduo' && !X.modo.comun){   // sin textos para lo elegido: la otra posibilidad (hoy, o las I Vísperas de mañana si es domingo o solemnidad)
    const otra = quiere ? calc(false) : ((man.dom||man.sol) ? calc(true) : null);
    if(otra && otra.completo){ if(quiere) otra.nota='Las I Vísperas de mañana todavía no tienen propio en la base: se rezan las del día.'; r=otra; }
  }
  if(!r.completo) r.nota='Faltan textos propios de este día (antífona del cántico evangélico u oración): están marcados para completar.';
  return r;
}

// Himno en gregoriano (base/gregoriano/himnos.yaml), como opción después del himno en español: domingos del Tiempo
// Ordinario y de Adviento sin otra celebración (en el Ordinario, según la semana del salterio: I Vísperas, Laudes y
// II Vísperas) y algunas celebraciones por nombre (Vísperas: también las I). ref: el día del oficio (en las I Vísperas, mañana).
function himnoGregoriano(hora, ref, primeras, GH){
  if(!GH || !ref) return null;
  const C=GH.cuando, dom=ref.dom && ref.n===ref.fer;
  // Fiestas y solemnidades de la Virgen María: O gloriósa Vírginum (Laudes) y Ave maris stella (Vísperas, también las I)
  const mariana = C.marianas && /^(Fiesta|Solemnidad)/.test(ref.g||'') && C.marianas.nombres.some(x=>String(ref.n||'').startsWith(x));
  const t = C.celebraciones[ref.n]
    || (mariana ? C.marianas : null)
    || (dom && ref.t==='Ordinario' && ref.sal ? C.ordinario[ref.sal%2 ? 'semanas_1_3' : 'semanas_2_4'] : null)
    || (dom && ref.t==='Adviento' ? C.adviento : null);
  if(!t) return null;
  const k = hora==='laudes' ? t.laudes : (t[primeras?'visperas1':'visperas2'] || t.visperas);
  const H = k && GH.himnos[k]; if(!H) return null;
  const ult=H.estrofas.length-1;
  return {id:'greg', n:H.titulo, lang:'la', gabc:H.gabc, glosa:H.estrofas.flat(2).concat([H.amen]), ...(H.rubrica?{rubGreg:H.rubrica}:{}),
          rec:H.estrofas.map((e,i)=>{ const vs=i===ult?e.concat([[H.amen]]):e; return {rol:'', todos:false, pares:vs.flat(), versos:vs}; })};
}

function armar(hora, fecha, region){
  const L=window[hora.toUpperCase()]; if(!L) return null;
  if(!CP.diaCal(fecha, region)) return null;
  const B=window.BASE, GR=B.completas.gregoriano, GL=L.gregoriano, LAU=hora==='laudes';
  const {P, dia, nota, hoy, fRef, primeras}=propio(hora, fecha, region);
  const cuaresma=hoy.t==='Cuaresma'||hoy.t==='Triduo';
  const solemne=!!(hoy.sol||hoy.dom||hoy.t==='Triduo'||hoy.oct);
  const S=[]; const sec=(id,t,extra)=>S.push({k:'sec',id,t,...extra});
  // Cántico Ap 19 (Vísperas del domingo): sus «Aleluia» van aparte; la app los muestra todos si el oficio se canta,
  // y si se recita, solo al principio y al final de cada estrofa (rúbrica del libro)
  const aleluyas=t=>t.filter(e=>/\n/.test(e)).map(e=>e.split('\n').map(x=>x.trim()).filter(x=>x && !/aleluia/i.test(x)));
  const modo=modoDe(hoy, fRef);
  const pas=X.pasion(fRef, hoy.sol);   // tiempo de pasión: sin Gloria al final de salmos y cánticos ni en el responsorio breve
  const salmo=(sid, ant)=>{ const s=L.salmos[sid]; const v=X.versosDe(s.texto);
    if(/^cantico-ap-19-/.test(sid)) return {k:'salmo', es:true, id:sid, ant, modo, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:[]}, grupos:{es:[]}, aleluyas:aleluyas(s.texto), gloria:!pas, rubrica:pas?X.NO_GLORIA:''};
    return {k:'salmo', es:true, id:sid, ant, modo, sinEnt:!!s.sin_entonacion, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!pas && !SIN_GLORIA.includes(sid), rubrica:[s.rubrica_final||'', pas && !SIN_GLORIA.includes(sid) ? X.NO_GLORIA : ''].filter(Boolean).join(' ')}; };

  // Invitatorio: solo los domingos (ADF). Dómine, lábia mea; antífona y Salmo 94; después, el Deus in adiutórium.
  // Todos los días se empieza con «Dómine, lábia mea apéries»; el invitatorio (antífona y Salmo 94), solo los domingos.
  const labia=LAU && {k:'vr', gabc:GL.invitatorio.gabc, glosa:GL.invitatorio.traduccion, rec:X.recitado(GL.invitatorio.traduccion, [['V','Dómine,'],['R','Et',true]])};
  // Invitatorio: en Laudes, los domingos, si Laudes es la primera oración del día (botón en la hora; X.modo.inv: true o false
  // lo fuerza, p. ej. para el Oficio de lectura cuando es la primera oración)
  const conInv = LAU && (X.modo.inv!=null ? X.modo.inv : (CP.deIso(fecha).getDay()===0 && !X.modo.difuntos));
  if(conInv){
    sec('invitatorio','Invitatorio');
    S.push(labia);
    // Domingos del Tiempo Ordinario: se puede cantar en gregoriano («Veníte, exsultémus Dómino» y Salmo 94). inv: 'greg' o 'es', según se elija.
    // (Oculto por ahora: el invitatorio se reza solo en español. Para volver a ofrecerlo, quitar «false &&».)
    const IG=false && hoy.t==='Ordinario' && hoy.dom && !hoy.sol && GL.invitatorio_to, inv=IG?{inv:'es'}:{};
    if(IG){ S.push({k:'invop'});
      S.push({k:'invgreg', inv:'greg', ant:{gabc:IG.ant.gabc, glosa:IG.ant.traduccion}, estrofas:IG.estrofas.map(e=>({gabc:e.gabc, glosa:e.traduccion}))}); }
    S.push({k:'ant', id:'ai', es:true, n:'Ant.', t:{es:P.inv_ant}, ...inv});
    // Salmo 94 en estrofas, sin asteriscos ni cruces (no se salmodia): las cinco del salmo y el Gloria
    const s94=L.ordinario.invitatorio.salmo;
    S.push({k:'salmoinv', id:'salmo-94', titulo:s94.titulo, lema:X.oracionCase(s94.subtitulo||''), ant:P.inv_ant,
            estrofas:s94.texto.map(e=>e.split('\n').map(x=>x.trim()).filter(Boolean))
              .concat(pas ? [] : [['Gloria al Padre, y al Hijo, y al Espíritu Santo.', 'Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén.']]), ...inv});
    if(pas) S.push({k:'rub', t:X.NO_GLORIA, ...inv});
    S.push({k:'ant', rep:'ai', es:true, ...inv});
  }

  sec('inicio','Invocación inicial');
  if(LAU && !conInv) S.push(labia);
  const tono = solemne ? 'solemne' : /^Fiesta/.test(hoy.g) ? 'festivo' : 'ferial';
  const trInv=cuaresma ? GR.invocacion.traduccion.filter(p=>!/^Allel/.test(p[0])).concat(GR.invocacion.laus) : GR.invocacion.traduccion;
  S.push({k:'vr', tono, gabc:X.invocacionGabc(tono, !cuaresma), glosa:trInv,
          rec:X.recInvocacion(trInv)});

  sec('himno','Himno');
  const H=L.himnos[P.himno]||[];
  // El himno en español va primero; el gregoriano del día, como opción (la elección se recuerda: «greg» vale para todos los días que lo tienen)
  const HG=himnoGregoriano(hora, hoy, primeras, GL.himnos);
  // Himno de un común: los otros del común, como opciones (la elección vale mientras se mira ese día)
  const OH=(P._himnos||[]).map((n,i)=>({id:hora+'~'+(i+1), n, lang:'es', est:(L.himnos[n]||[]).map(e=>e.split('\n')), amen:''}));
  // Himno latino recitado (base/himnos/latinos.yaml): del común, si el himno en español es del común; si no, del tiempo
  const HL=X.himnosLatinos(hora, hoy, {hs:L.latinos, comun:P._comunLat, primeras, greg:HG&&HG.n});
  S.push({k:'himno', es:true, efimera:OH.length>0, opciones:[{id:hora, n:P.himno, lang:'es', est:H.map(e=>e.split('\n')), amen:''}].concat(OH, HG?[HG]:[], HL)});

  sec('salmodia','Salmodia');
  (P.salmodia||[]).forEach((g,gi)=>{
    const id='a'+(gi+1);
    S.push({k:'ant', id, es:true, ast:true, n:`Ant. ${gi+1}`, t:{es:g.ant}, modo});
    S.push(salmo(g.salmo, id));
    S.push(g.ant_fin ? {k:'ant', id:id+'f', es:true, n:`Ant. ${gi+1}`, t:{es:g.ant_fin}} : {k:'ant', rep:id, es:true});
  });

  sec('lectura','Lectura breve',{ref:P.lectura.ref});
  S.push({k:'lectura', es:true, t:{es:P.lectura.texto}});
  S.push({k:'deo', t:GR.lectura_respuesta[0][0], il:GR.lectura_respuesta_glosa, tr:GR.lectura_respuesta[0][1]});

  if(P.en_lugar_del_responsorio){
    sec('responsorio','En lugar del responsorio breve');
    S.push({k:'ant', id:'rb', es:true, n:'Ant.', t:{es:P.en_lugar_del_responsorio}, ...(X.gregPropio('responsorio', P.en_lugar_del_responsorio)||{})});
  } else {
    sec('responsorio','Responsorio breve');
    S.push({k:'resp', es:true, l:{es:pas ? X.sinGloriaResp(P.responsorio) : P.responsorio}});
  }

  sec('cantico','Cántico evangélico',{ref:GL.cantico.ref});
  const BN=GL.cantico;
  // Antífonas «Oh» (Vísperas, 17 al 23 de diciembre): cantadas, en gregoriano (modo 2), y el Magníficat en 2 D
  const AG=!LAU && X.gregPropio('magnificat', P.ant_magnificat);
  S.push({k:'ant', id:'ab', es:true, ast:true, n:'Ant.', t:{es:(LAU?P.ant_benedictus:P.ant_magnificat)||'[falta la antífona]'}, ...(AG||{})});
  const bnv=pas ? BN.versos.filter(v=>!X.esGloriaLa(v)) : BN.versos, bni=pas&&BN.traduccion_versos ? BN.traduccion_versos.filter((x,i)=>!X.esGloriaLa(BN.versos[i])) : BN.traduccion_versos;
  S.push({k:'cantico', id:LAU?'benedictus':'magnificat', modo:AG&&AG.modoGreg===2 ? '2D' : modo, titulo:BN.titulo, versos:bnv, inter:bni});
  if(pas) S.push({k:'rub', t:X.NO_GLORIA});
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
    dia:{titulo:hoy.n+(!primeras && hoy.n===hoy.fer && CP.deIso(fRef).getDay()!==0 && window[hora.toUpperCase()].tiempo[X.fechaClave(fRef)] ? ` · ${X.fechaClave(fRef)}`:'')+(primeras?' · I Vísperas':''), tiempo:X.TIEMPO_TXT[hoy.t]||hoy.t, salterio: hoy.sal?`Semana ${X.ROMANO(hoy.sal)} del salterio`:'', color:hoy.c, grado:hoy.g, nota},
    fechaTxt:`${X.DIAS_TXT[d.getDay()]} ${d.getDate()} de ${X.MESES[d.getMonth()]}`,
    secciones:S,
  };
}

window.Laudes={armar:(f,r)=>armar('laudes',f,r), ciclo, propio, himnoGregoriano, modoDe, MODOS};
window.Visperas={armar:(f,r)=>armar('visperas',f,r), propio};
})();
