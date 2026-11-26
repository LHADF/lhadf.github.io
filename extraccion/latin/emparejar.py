"""Empareja los salmos y cánticos latinos de la extracción (extraccion/latin/dias/) con las claves de base/salmos: por fecha,
hora y orden, comparando con lo que arma la app (salmos_app.mjs). Sale en extraccion/latin/:
  salmos.json   — por clave de la base: cita latina, título, epígrafe y texto en estrofas (con * y † como en el libro),
                  cuántas veces se emparejó y, si hubo, otras citas (días en que la app reza otra cosa: calendario ADF distinto);
  controles.txt — horas que no se pudieron emparejar y claves con más de una cita.
Uso: python3 tools/armar.py && python3 extraccion/latin/emparejar.py"""
import json, re, collections, unicodedata, glob, os, subprocess, tempfile
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
L = [d for f in sorted(glob.glob(os.path.join(AQUI, 'dias', '*.json'))) for d in json.load(open(f, encoding='utf-8'))['dias']]
tmp = os.path.join(tempfile.mkdtemp(), 'app.json')
subprocess.run(['node', os.path.join(AQUI, 'salmos_app.mjs'), L[0]['fecha'], L[-1]['fecha'], tmp], check=True)
E = json.load(open(tmp))

def es_salmo(b, hora):
    s = b.get('sub') or []
    if b.get('alternativa') == 'lastblock' and hora in ('tercia', 'sexta', 'nona'): return False   # salmodia complementaria
    if s and re.match(r'(Ps|Psalmus) \d', s[0]): return True
    return b.get('titulo') == 'Canticum' and bool(b.get('ref'))   # cántico del AT o del NT (no el evangélico)

def partir(b):
    ls = [l for l in b['lineas'] if not l.get('p')]
    if ls and ls[0].get('cursiva'): ls = ls[1:]     # antífona
    if ls and ls[-1].get('cursiva'): ls = ls[:-1]   # antífona repetida
    g = next((i for i, l in enumerate(ls) if l['t'].startswith('Glória Patri')), None)
    if g is not None: ls = ls[:g]
    est = []
    for l in ls:
        if l.get('estrofa') or not est: est.append([])
        est[-1].append(l['t'])
    return est

def norm(t): return re.sub(r'\W+', '', unicodedata.normalize('NFD', t.lower()).encode('ascii', 'ignore').decode())

def vale(k, x):   # la cita latina tiene que ser del mismo salmo (o del mismo capítulo, en los cánticos)
    m = re.match(r'salmo-(\d+)', k)
    if m: return bool(re.match(r'Ps ' + m.group(1) + r'(?![0-9])', x['ref']))
    c = re.match(r'cantico-(\d?[a-z]+)-(\d+)', k)
    if c:
        cap = re.search(r'(\d+)\s*[:,]', x['ref'] or '')
        return bool(cap and cap.group(1) == c.group(2))
    return True

salmos = collections.defaultdict(list); ctl = []
for d in L:
    f = d['fecha']
    for h, bl in d['horas'].items():
        la = [b for b in bl if es_salmo(b, h)]
        es = (E.get(f, {}).get(h) or {}).get('sal') or []
        if len(la) != len(es):
            ctl.append(f'{f} {h}: {len(la)} salmos en latín y {len(es)} en la app ({d["celebracion"]})'); continue
        for b, s in zip(la, es):
            cant = b.get('titulo') == 'Canticum'; sb = b.get('sub') or []
            salmos[s['id']].append({'ref': b.get('ref', '') if cant else (sb[0] if sb else ''),
                                    'titulo': (sb[0] if sb else '') if cant else (sb[1] if len(sb) > 1 else ''),
                                    'epigrafe': b.get('epigrafe', ''), 'est': partir(b), 'f': f, 'h': h})
out = {}
for k in sorted(salmos):
    v = [x for x in salmos[k] if vale(k, x)] or salmos[k]
    txt = collections.Counter(norm(' '.join(sum(x['est'], []))) for x in v)
    x = next(y for y in v if norm(' '.join(sum(y['est'], []))) == txt.most_common(1)[0][0])
    refs = collections.Counter(y['ref'] for y in salmos[k])
    out[k] = {'ref': x['ref'], 'titulo': x['titulo'], 'epigrafe': x['epigrafe'], 'texto': ['\n'.join(e) for e in x['est']], 'veces': len(salmos[k])}
    if len(refs) > 1:
        otros = [f"{y['f']} {y['h']} ({y['ref']})" for y in salmos[k] if y['ref'] != x['ref']]
        out[k]['otras_citas'] = otros
        ctl.append(f'{k}: {x["ref"]} ({refs[x["ref"]]} veces); otras: ' + '; '.join(otros))
base = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(RAIZ, 'base', 'salmos', '*.yaml'))}
ctl.insert(0, f'{len(out)} claves de base/salmos con texto latino; sin latín en este período: ' + ', '.join(sorted(base - set(out))))
json.dump(out, open(os.path.join(AQUI, 'salmos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(AQUI, 'controles.txt'), 'w', encoding='utf-8').write('\n'.join(ctl) + '\n')
print(ctl[0])
