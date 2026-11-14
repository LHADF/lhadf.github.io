// Todas las celebraciones del calendario ADF (y sus variantes por país) de 2026 a 2028, con lo que la app tiene para cada una.
// Hace falta haber corrido tools/armar.py. Sale en extraccion/informes/calendario-adf.json.
//     node extraccion/calendario_adf.mjs
import { readFileSync, readdirSync, writeFileSync } from 'node:fs'; import vm from 'node:vm';
const R=new URL("../src/", import.meta.url).pathname;
const ctx={window:{}};
for (const f of readdirSync(R+'datos')) vm.runInNewContext(readFileSync(R+'datos/'+f,'utf8'),ctx);
vm.runInNewContext(readFileSync(R+'completas.js','utf8'),ctx);
for (const f of ['carga/laudes.js','carga/visperas.js','laudes.js']) vm.runInNewContext(readFileSync(R+f,'utf8'),ctx);
const W=ctx.window, CP=W.Completas, LD=W.LAUDES;
const out={};
for (const y of [2026,2027,2028]) { let f=`${y}-01-01`;
  while (f<=`${y}-12-31`) {
    for (const o of CP.opcionesDia(f,'')) { const x=o.f; if(!x || x.n===x.fer) continue;
      const k=x.n; const e=out[k]||(out[k]={n:k, fechas:new Set(), g:new Set(), cal:new Set(), t:new Set(), base:o.tipo==='b'});
      e.fechas.add(f.slice(5)); e.g.add(x.g); (x.cal||'ADF').split(/,\s*/).forEach(s=>e.cal.add(s)); for(const s of o.siglas||[]) e.cal.add(s); e.t.add(x.t); if(o.tipo==='b') e.base=true; }
    f=CP.masDias(f,1); } }
const arr=Object.values(out).map(e=>({n:e.n, fechas:[...e.fechas].sort(), g:[...e.g], cal:[...e.cal], t:[...e.t], base:e.base, mapa:LD.mapa[e.n]||null, adf:LD.adf[e.n]||null}));
writeFileSync('/home/claude/lhadf.github.io/extraccion/informes/calendario-adf.json', JSON.stringify(arr,null,0));
console.log(arr.length, arr.filter(a=>a.mapa).length, arr.filter(a=>a.adf).length, arr.filter(a=>!a.mapa&&!a.adf).length);
