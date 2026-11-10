/* ================== Armado de Laudes para cualquier fecha ==================
   Datos: window.LAUDES (src/carga/laudes.js, se carga recién al abrir Laudes), window.BASE y window.CAL.
   Capas: salterio de cuatro semanas → propio del tiempo (por feria; en domingo, con ciclo A/B/C) → santoral.
   Decisiones ADF en docs/laudes.md. */
(function(){
const CP=window.Completas, X=CP._;
const CAMPOS=['inv_ant','himno','salmodia','lectura','responsorio','ant_benedictus','preces','padrenuestro_intro','oracion','en_lugar_del_responsorio','pendiente'];
const SIN_GLORIA=['cantico-dn-3-57-88-56'];   // el cántico de Daniel 3, 57-88 no lleva Gloria

// Ciclo dominical del año litúrgico (empieza el I Domingo de Adviento)
function ciclo(fecha){
  const d=CP.deIso(fecha);
  const adv=y=>{ const n=new Date(y,11,25,12); n.setDate(n.getDate()-(n.getDay()||7)-21); return n; };
  const y = d>=adv(d.getFullYear()) ? d.getFullYear() : d.getFullYear()-1;
  return 'ABC'[(((y-2016)%3)+3)%3];
}

// Las partes del día, capa sobre capa
function propio(hoy, fecha){
  const L=window.LAUDES, d=CP.deIso(fecha), dia=X.DIAS[d.getDay()];
  const P={}, capa=o=>{ if(o) for(const k of CAMPOS) if(o[k]!=null) P[k]=o[k]; };
  capa(L.salterio['semana_'+(hoy.sal||1)][dia]);
  capa(L.tiempo[hoy.fer]);
  if(dia==='domingo') capa(L.tiempo[`${hoy.fer} (${ciclo(fecha)})`]);
  let santo=null, nota='';
  const k=L.mapa[hoy.n];
  if(k){ santo=L.santoral[k]; delete P.pendiente; capa(santo); }
  else if(hoy.n!==hoy.fer){
    nota='El propio de esta celebración todavía no está en la base: se reza el oficio del día.'; }
  // Fiestas y solemnidades sin salmodia propia: salmos y antífonas del domingo de la I semana
  if(/^(Fiesta|Solemnidad)/.test(hoy.g) && !(santo&&santo.salmodia)) P.salmodia=L.salterio.semana_1.domingo.salmodia;
  if(P.pendiente) nota='Faltan textos propios de este día (antífona del Benedictus u oración): están marcados para completar.';
  return {P, dia, nota};
}

function armar(fecha, region){
  const L=window.LAUDES; if(!L) return null;
  const hoy=CP.diaCal(fecha, region); if(!hoy) return null;
  const B=window.BASE, GR=B.completas.gregoriano, GL=L.gregoriano;
  const {P, dia, nota}=propio(hoy, fecha);
  const cuaresma=hoy.t==='Cuaresma'||hoy.t==='Triduo';
  const solemne=!!(hoy.sol||hoy.dom||hoy.t==='Triduo'||hoy.oct);
  const S=[]; const sec=(id,t,extra)=>S.push({k:'sec',id,t,...extra});
  const salmo=(sid, ant)=>{ const s=L.salmos[sid]; const v=X.versosDe(s.texto);
    return {k:'salmo', es:true, id:sid, ant, titulo:{es:s.titulo}, lema:{es:X.oracionCase(s.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:!SIN_GLORIA.includes(sid)}; };

  // Invitatorio: solo los domingos (ADF). Dómine, lábia mea; antífona y Salmo 94; después, el Deus in adiutórium.
  // Todos los días se empieza con «Dómine, lábia mea apéries»; el invitatorio (antífona y Salmo 94), solo los domingos.
  const labia={k:'vr', gabc:GL.invitatorio.gabc, glosa:GL.invitatorio.traduccion, rec:X.recitado(GL.invitatorio.traduccion, [['V','Dómine,'],['R','Et',true]])};
  if(dia==='domingo'){
    sec('invitatorio','Invitatorio');
    S.push(labia);
    S.push({k:'ant', id:'ai', es:true, n:'Ant.', t:{es:P.inv_ant}});
    const s94=L.ordinario.invitatorio.salmo, v=X.versosDe(s94.texto);
    S.push({k:'salmo', es:true, id:'salmo-94', ant:'ai', titulo:{es:s94.titulo}, lema:{es:X.oracionCase(s94.subtitulo||'')}, versos:{es:v.versos}, grupos:{es:v.grupos}, gloria:true});
    S.push({k:'ant', rep:'ai', es:true});
  }

  sec('inicio','Invocación inicial');
  if(dia!=='domingo') S.push(labia);
  const tono = solemne ? 'solemne' : /^Fiesta/.test(hoy.g) ? 'festivo' : 'ferial';
  const trInv=cuaresma ? GR.invocacion.traduccion.filter(p=>!/^Allel/.test(p[0])).concat(GR.invocacion.laus) : GR.invocacion.traduccion;
  S.push({k:'vr', tono, gabc:X.invocacionGabc(tono, !cuaresma), glosa:trInv,
          rec:X.recInvocacion(trInv)});

  sec('himno','Himno');
  const H=L.himnos[P.himno]||[];
  S.push({k:'himno', es:true, opciones:[{id:'laudes', n:P.himno, lang:'es', est:H.map(e=>e.split('\n')), amen:''}]});

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

  sec('cantico','Cántico evangélico',{ref:GL.benedictus.ref});
  const BN=GL.benedictus;
  S.push({k:'ant', id:'ab', es:true, n:'Ant.', t:{es:P.ant_benedictus}});
  S.push({k:'cantico', titulo:BN.titulo, versos:BN.versos, inter:BN.traduccion_versos});
  S.push({k:'ant', rep:'ab', es:true});

  sec('preces','Preces');
  S.push({k:'preces', es:true, ...P.preces});

  sec('padrenuestro','Padre nuestro');
  S.push({k:'pater', intro: (dia==='domingo' || /^(Fiesta|Solemnidad)/.test(hoy.g)) ? (P.padrenuestro_intro||'') : '', pares:GL.pater_noster, lineas:X.enLineas(GL.pater_noster, GL.pater_cortes)});   // monición (la del día) solo en domingos, fiestas y solemnidades

  sec('oracion','Oración');
  S.push({k:'prosa', es:true, t:{es:P.oracion}, amen:{es:'Amén.'}});

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
    hora:'laudes', nombre:'Laudes',
    versiones:{es:{n:'Liturgia de las Horas'}},
    gloria:{es:['Gloria al Padre, y al Hijo, * y al Espíritu Santo.','Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']},
    dia:{titulo:hoy.n, tiempo:X.TIEMPO_TXT[hoy.t]||hoy.t, salterio: hoy.sal?`Semana ${X.ROMANO(hoy.sal)} del salterio`:'', color:hoy.c, grado:hoy.g, nota},
    fechaTxt:`${X.DIAS_TXT[d.getDay()]} ${d.getDate()} de ${X.MESES[d.getMonth()]}`,
    secciones:S,
  };
}

window.Laudes={armar, ciclo, propio};
})();
