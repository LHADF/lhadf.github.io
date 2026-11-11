"""Carga única de Vísperas desde sync a la base propia (base/). Igual que importar_laudes.py, con una diferencia:
las I Vísperas (sábados y vísperas de solemnidad; sync las rotula «I VÍSPERAS») pertenecen al día siguiente.

  CACHE=1 SEPTIES_FUENTES=… ORDO=… python3 tools/importar/importar_visperas.py

Capas: salterio (cuatro semanas; `domingo_1` = I Vísperas del domingo), tiempo (por feria; «· I Vísperas» para las primeras),
santoral (por celebración de sync; «· I Vísperas»). Variantes: base/informes/visperas.md.
"""
import collections, json, os, re, sys, tomllib
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import laudes_sync as L
import importar_laudes as IL
from importar_laudes import Votos, sin_gloria, id_salmo, ciclo, dia_semana, preces, escribir, _aleluia, DIAS, BASE, SYNC, ORDO

CAMPOS = ['himno', 'salmodia', 'lectura', 'responsorio', 'ant_magnificat', 'preces', 'padrenuestro_intro', 'oracion']
EXTRA = CAMPOS + ['en_lugar_del_responsorio']


def cargar():
    sys.path.insert(0, ORDO)
    from ordo.calendario import Ordo
    O = Ordo(ORDO, tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb')))
    out = []
    for fecha, var, f, idx in L.archivos(SYNC, 'visperas'):
        d = L.estructura(f); d['celebracion'] = L.celebracion(idx)
        f0 = date.fromisoformat(fecha)
        D, M = O.dia(f0), O.dia(f0 + timedelta(days=1))
        d.update(fecha=fecha, var=var, tiempo=D.tiempo, salterio=D.salterio, feria=D.feria.nombre,
                 m_tiempo=M.tiempo, m_salterio=M.salterio, m_feria=M.feria.nombre)
        d.pop('benedictus_texto', None)
        out.append(d)
    return out


def id_v(h):
    """Como id_salmo, y además los salmos partidos: «Salmo 44 I» → salmo-44-i."""
    h = re.sub(r'(?i)\bcf\.\s*', '', h)
    m = re.match(r'(?i)(salmo\s+\d+)\s+(I{1,3})(?=\s*[-.]|\s*$)\s*\.?(.*)$', h.strip())
    if m:
        ident, nombre, sub = id_salmo(m.group(1) + ' ' + (m.group(3).strip() or '-'))
        return ident + '-' + m.group(2).lower(), nombre + ' ' + m.group(2).upper(), sub
    return id_salmo(h)


def partes(d, S):
    p = {}
    if d.get('himno') and d['himno'].get('texto'):
        pr = d['himno']['texto'][0].split('\n')[0].strip().rstrip('.,;:').strip()
        p['himno'] = pr; S('himno/' + pr, d['himno']['texto'], d['fecha'])
    if len(d['salmodia']) == 3:
        sal = []
        for g in d['salmodia']:
            ident, nombre, sub = id_v(g['salmo'] or '')
            if not ident: sal = None; break
            est, _ = sin_gloria(g['texto'])
            S('salmo/' + ident, {'titulo': nombre, 'subtitulo': sub, 'texto': est}, d['fecha'])
            x = {'ant': g['ant'], 'salmo': ident}
            if g.get('ant_fin') and g['ant_fin'] != g['ant']: x['ant_fin'] = g['ant_fin']
            sal.append(x)
        if sal: p['salmodia'] = sal
    for k in ('lectura', 'responsorio', 'padrenuestro_intro', 'oracion'):
        if d.get(k): p[k] = d[k]
    if d.get('ant_benedictus'): p['ant_magnificat'] = d['ant_benedictus']
    if d.get('preces'): p['preces'] = preces(d['preces'])
    for h, ls in d.get('_otros', []):
        if h.startswith('En lugar del responsorio') and ls: p['en_lugar_del_responsorio'] = ls[0]
    return p


def importar(todos, cel_por_fecha):
    S, V = Votos(), Votos()
    dias = []
    for d in todos:
        p = partes(d, S)
        f = date.fromisoformat(d['fecha'])
        # sync no siempre rotula las del sábado: toda tarde de sábado es I Vísperas del domingo, salvo que diga «II»
        primeras = d.get('visperas') == 'I' or (f.weekday() == 5 and d.get('visperas') != 'II')
        if d['feria'] == 'Sábado Santo': primeras = False   # las Vísperas del Sábado Santo son propias del día
        ref = (f + timedelta(days=1)).isoformat() if primeras else d['fecha']      # el día al que pertenecen
        feria, tiempo, salt = (d['m_feria'], d['m_tiempo'], d['m_salterio']) if primeras else (d['feria'], d['tiempo'], d['salterio'])
        c = cel_por_fecha.get(ref) or {}
        cel = c.get('nombre') if c.get('grado') and (not primeras or c.get('grado') == 'Solemnidad' or dia_semana(ref) != 'domingo') else None
        if primeras and cel and c.get('grado') != 'Solemnidad': cel = cel if dia_semana(ref) != 'domingo' else None
        dia = 'domingo_1' if (primeras and dia_semana(ref) == 'domingo') else dia_semana(ref)
        kt = feria + (f' ({ciclo(ref)})' if dia_semana(ref) == 'domingo' else '') + (' · I Vísperas' if primeras else '')
        dias.append(dict(d=d, p=p, cel=(cel + (' · I Vísperas' if primeras else '')) if cel else None, sk=f'{salt}/{dia}', kt=kt, tiempo=tiempo, ref=ref, primeras=primeras, dia=dia, grado=c.get('grado'), comun=c.get('comun', '')))
        if d.get('conclusion'): S('conclusion', d['conclusion'], d['fecha'])
    dom = lambda x: x['dia'] in ('domingo', 'domingo_1')
    for x in dias:   # 1) salterio: Tiempo Ordinario sin celebración
        if x['cel'] or x['tiempo'] != 'Ordinario' or (x['primeras'] and x['dia'] != 'domingo_1'): continue
        for k in CAMPOS:
            if dom(x) and k in ('ant_magnificat', 'oracion'): continue
            if k in x['p']: V(f"salterio/{x['sk']}/{k}", x['p'][k], x['d']['fecha'])
    sal = lambda sk, k: V.ganador(f'salterio/{sk}/{k}')
    for x in dias:   # 2) tiempo
        if x['cel']: continue
        if x['tiempo'] == 'Ordinario' and not dom(x): continue
        for k in EXTRA:
            if k in x['p']: V(f"tiempo/{x['kt']}/{k}", x['p'][k] if x['p'][k] != sal(x['sk'], k) else '=', x['d']['fecha'])
    def base(x, k):
        t = V.ganador(f"tiempo/{x['kt']}/{k}")
        return sal(x['sk'], k) if t in (None, '=') else t
    fechas, info = collections.defaultdict(collections.Counter), {}
    for x in dias:   # 3) santoral
        if not x['cel']: continue
        fechas[x['cel']][x['ref'][5:]] += 1
        info.setdefault(x['cel'], collections.Counter())[(x['grado'], x['comun'])] += 1
        for k in EXTRA:
            if k in x['p']: V(f"santoral/{x['cel']}/{k}", x['p'][k] if x['p'][k] != base(x, k) else '=', x['d']['fecha'])
    return S, V, dias, fechas, info


def escribir_base(S, V, dias, fechas, info):
    G = V.ganador
    salterio = {}
    for s in '1234':
        salterio[f'semana_{s}'] = {}
        for dia in ['domingo_1', 'domingo'] + DIAS[:6]:
            e = {k: G(f'salterio/{s}/{dia}/{k}') for k in CAMPOS}
            e = {k: v for k, v in e.items() if v is not None}
            if e: salterio[f'semana_{s}'][dia] = e
    escribir(os.path.join(BASE, 'salterio', 'visperas.yaml'), salterio,
             'Salterio de Vísperas: cuatro semanas. domingo_1 = I Vísperas del domingo (se rezan el sábado); domingo = II Vísperas.\n'
             'En los domingos, la antífona del Magníficat y la oración son propias (base/tiempo/visperas.yaml).')
    def capa(pref):
        c = collections.OrderedDict()
        for clave in V.v:
            if clave.startswith(pref):
                nombre, k = clave[len(pref):].rsplit('/', 1); c.setdefault(nombre, {})[k] = G(clave)
        return c
    T = {n: {k: v for k, v in e.items() if v != '='} for n, e in capa('tiempo/').items()}
    T = {n: e for n, e in T.items() if e}
    # domingos: lo común a los tres ciclos pasa a la entrada sin ciclo
    grupos = collections.defaultdict(dict)
    for n in list(T):
        m = re.match(r'^(.*) \(([ABC])\)( · I Vísperas)?$', n)
        if m: grupos[m.group(1) + (m.group(3) or '')][m.group(2)] = n
    for b, cs in grupos.items():
        if len(cs) < 3: continue
        campos = set().union(*(T[n] for n in cs.values()))
        com = {k: T[cs['A']].get(k) for k in campos if len({json.dumps(T[n].get(k), ensure_ascii=False, sort_keys=True) for n in cs.values()}) == 1}
        if com:
            T[b] = com
            for n in cs.values():
                T[n] = {k: v for k, v in T[n].items() if k not in com}
                if not T[n]: del T[n]
    pos = {}
    for x in dias:
        f = date.fromisoformat(x['ref'])
        n = date(f.year, 12, 25); adv = n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
        if f < adv: n = date(f.year - 1, 12, 25); adv = n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
        b = re.sub(r' \([ABC]\)', '', x['kt']); bb = b.replace(' · I Vísperas', '')
        pos[bb] = min(pos.get(bb, 999), (f - adv).days)
    orden = sorted(T, key=lambda n: (pos.get(re.sub(r' \([ABC]\)| · I Vísperas', '', n), 999), 0 if 'I Vísperas' in n else 1, n))
    escribir(os.path.join(BASE, 'tiempo', 'visperas.yaml'), {n: T[n] for n in orden},
             'Propio del tiempo de Vísperas: por feria (nombre del Ordo). «· I Vísperas» = primeras vísperas (se rezan la tarde anterior);\n'
             'en los domingos, «(A)», «(B)» o «(C)» cuando cambia con el ciclo. Solo figura lo que cambia respecto del salterio.')
    Sa = capa('santoral/'); santoral = {}
    for nombre in sorted(Sa, key=lambda n: (fechas[n].most_common(1)[0][0], 0 if 'I Vísperas' in n else 1)):
        e = {k: v for k, v in Sa[nombre].items() if v != '='}
        (grado, comun), _ = info[nombre].most_common(1)[0]
        fe = fechas[nombre].most_common()
        santoral[nombre] = {'grado': grado, 'fecha': fe[0][0] if fe[0][1] > sum(c for _, c in fe) / 2 else 'variable', **({'comun': comun} if comun else {}), **e}
    escribir(os.path.join(BASE, 'santoral', 'visperas.yaml'), santoral,
             'Santoral de Vísperas (calendario de sync, a revisar con el ADF). «· I Vísperas» = primeras vísperas de la solemnidad.\n'
             'Solo figura lo que cambia respecto del salterio y del tiempo; «fecha: variable» = celebración movible.')
    himnos = {c[6:]: S.ganador(c) for c in sorted(S.v) if c.startswith('himno/')}
    escribir(os.path.join(BASE, 'himnos', 'visperas.yaml'), himnos, 'Himnos de Vísperas en español, por primer verso.')
    nuevos = 0
    for c in S.v:
        if c.startswith('salmo/'):
            ruta = os.path.join(BASE, 'salmos', c.split('/', 1)[1] + '.yaml')
            if os.path.exists(ruta): continue
            x = S.ganador(c); nuevos += 1
            escribir(ruta, x, f"{x['titulo']}. Texto de la Liturgia de las Horas en español; estrofas separadas por renglón en blanco.")
    return len(T), len(santoral), len(himnos), nuevos


def informe(S, V, todos):
    Ls = ['# Vísperas: variantes encontradas en sync', '', f'Se leyeron {len(todos)} Vísperas. En la base quedó la versión más frecuente de cada texto.', '']
    for W in (V, S):
        for clave, vs in W.variantes():
            if clave.startswith('himno/'): continue
            vs = [(v, f) for v, f in vs if v != '=']
            if len(vs) < 2: continue
            Ls.append(f'## {clave}')
            for i, (val, fs) in enumerate(vs[:5]):
                m = json.dumps(val, ensure_ascii=False); m = m[:240] + '…' if len(m) > 240 else m
                Ls.append(f'- {"**en la base**" if i == 0 else "variante"} · {len(fs)} veces · {", ".join(fs[:4])}{"…" if len(fs) > 4 else ""}')
                if i: Ls.append(f'  `{m}`')
            Ls.append('')
    open(os.path.join(BASE, 'informes', 'visperas.md'), 'w', encoding='utf-8').write(_aleluia('\n'.join(Ls)))


if __name__ == '__main__':
    cache = '/tmp/visperas_sync.json'
    if os.environ.get('CACHE') and os.path.exists(cache): todos = json.load(open(cache))
    else:
        todos = cargar(); json.dump(todos, open(cache, 'w'), ensure_ascii=False)
    lau = json.load(open('/tmp/laudes_sync.json'))      # celebración de cada fecha según sync (index.htm), ya leída para Laudes
    cel = {}
    for d in lau:
        if d['fecha'] not in cel or d['celebracion'].get('grado'): cel.setdefault(d['fecha'], d['celebracion'])
    IL.alias_salmos(todos)
    S, V, dias, fechas, info = importar(todos, cel)
    print(len(todos), 'Vísperas leídas;', 'tiempo: %d · santoral: %d · himnos: %d · salmos nuevos: %d' % escribir_base(S, V, dias, fechas, info))
    informe(S, V, todos)
