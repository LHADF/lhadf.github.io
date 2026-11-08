"""Reconstruye cada Completas de sync desde la base y cuenta coincidencias por parte.
Uso: después de importar_completas.py (usa /tmp/completas_sync.json)."""
import json, collections, sys, re
import os
AQUI=os.path.dirname(os.path.abspath(__file__)); RAIZ=os.path.abspath(os.path.join(AQUI,'..','..')); sys.path.insert(0,AQUI)
from yaml_base import leer
B=os.path.join(RAIZ,'base')+'/'
O=leer(B+'ordinario/completas.yaml'); S=leer(B+'salterio/completas.yaml'); T=leer(B+'tiempo/completas-triduo-octava.yaml')
H=leer(B+'himnos/completas.yaml'); M=leer(B+'ordinario/antifonas-marianas.yaml')
import glob,os
SAL={os.path.basename(f)[:-5]:leer(f) for f in glob.glob(B+'salmos/*.yaml')}
todos=json.load(open('/tmp/completas_sync.json'))
ok=collections.Counter(); mal=collections.defaultdict(list)
def chk(campo, a, b, f):
    if a==b: ok[campo]+=1
    else: mal[campo].append(f)
for d in todos:
    f=d['fecha']; esp=T.get(d['dia']) if (d.get('ant_en_lugar_del_resp') or d['tiempo']=='Triduo') else None
    j = esp['juego'] if esp else d['juego']
    J=S[j]; pas = d['tiempo']=='Pascua'
    # salmodia
    sal = J['salmodia_pascua' if pas else 'salmodia']
    chk('antifonas', [g['ant'] for g in sal], [g['ant'] for g in d['salmodia']], f)
    for g in sal:
        for sid in g['salmos']:
            got=[s for gg in d['salmodia'] for s in gg['salmos'] if s['titulo'].startswith(SAL[sid]['titulo'].replace('Salmo','Salmo'))]
            chk('texto salmos', SAL[sid]['texto'], [e for e in got[0]['texto'] if not e.startswith('Gloria')] if got else None, f)
    chk('lectura', J['lectura'], d.get('lectura'), f)
    if esp:
        chk('ant. en lugar del resp.', esp['en_lugar_del_responsorio'], d['ant_en_lugar_del_resp'], f)
        chk('oración', esp['oracion'], d['oracion'], f)
        chk('ant. cántico', esp['antifona_cantico'], d.get('ant_cantico'), f)
    else:
        r = O['responsorio']['pascua' if pas else 'ordinario']
        chk('responsorio', [[k+'.',v] for e in r for k,v in e.items()], [[a,b] for a,b in d['responsorio']], f)
        chk('ant. cántico', O['cantico_evangelico']['antifona']['pascua' if pas else 'ordinario'], d.get('ant_cantico'), f)
        orac = d['oracion']
        chk('oración', O['oracion_solemnidad'] if orac.startswith('Visita') else J['oracion'], orac, f)
    pool={'Pascua':'pascua','Triduo':'cuaresma','Cuaresma':'cuaresma','Adviento':'adviento_navidad','Navidad':'adviento_navidad'}.get(d['tiempo'],'ordinario')
    chk('himno', any(h['titulo']==d['himno']['titulo'] and h['texto']==d['himno']['texto'] for h in H[pool]), True, f)
    mp = 'pascua' if pas else 'año'
    chk('antífona mariana', any(m['texto']==d.get('mariana') for m in M[mp]), True, f)
    chk('cántico de Simeón', SAL['cantico-simeon']['texto'], d.get('cantico_texto'), f)
    chk('bendición', [[k+'.',v] for e in O['bendicion'] for k,v in e.items()], [[a,b] for a,b in d['bendicion']], f)
L=['', '## Verificación', '', 'Cada Completas de sync se reconstruyó desde la base y se comparó parte por parte.', '', '| Parte | Coincide | Difiere | Fechas que difieren |', '|---|---|---|---|']
for k in sorted(ok.keys()|mal.keys()):
    L.append(f'| {k} | {ok[k]} | {len(mal[k])} | {", ".join(mal[k][:6])}{"…" if len(mal[k])>6 else ""} |')
print('\n'.join(L))
if '--informe' in sys.argv:
    p=os.path.join(RAIZ,'base','informes','completas.md'); t=open(p,encoding='utf-8').read().split('\n## Verificación')[0]
    open(p,'w',encoding='utf-8').write(t.rstrip()+'\n'+'\n'.join(L)+'\n')
