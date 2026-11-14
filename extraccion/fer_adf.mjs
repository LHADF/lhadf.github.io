// Los nombres de feria del Ordo (ref.fer) de 2025 a 2028, con el ciclo dominical: lo que la app busca en base/tiempo/.
// Hace falta haber corrido tools/armar.py. Sale en extraccion/informes/ferias-adf.json.
//     node extraccion/fer_adf.mjs
import { readFileSync, readdirSync, writeFileSync } from 'node:fs'; import vm from 'node:vm';
const R=new URL('../src/', import.meta.url).pathname; const ctx={window:{}};
for (const f of readdirSync(R+'datos')) vm.runInNewContext(readFileSync(R+'datos/'+f,'utf8'),ctx);
vm.runInNewContext(readFileSync(R+'completas.js','utf8'),ctx);
for (const f of ['carga/laudes.js','laudes.js']) vm.runInNewContext(readFileSync(R+f,'utf8'),ctx);
const W=ctx.window, CP=W.Completas; let f=W.CAL.desde; const out={};
while(f<=W.CAL.hasta){ const r=CP.diaCal(f,''); const e=out[r.fer]||(out[r.fer]={fer:r.fer, t:r.t, ciclos:[], dom:false});
  const c=W.Laudes.ciclo(f); if(!e.ciclos.includes(c)) e.ciclos.push(c); if(CP.deIso(f).getDay()===0) e.dom=true; f=CP.masDias(f,1); }
writeFileSync(new URL('informes/ferias-adf.json', import.meta.url), JSON.stringify(Object.values(out)));
console.log(Object.keys(out).length, 'ferias');
