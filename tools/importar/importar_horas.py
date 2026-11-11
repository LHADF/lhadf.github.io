"""Carga única de la Hora intermedia (tercia, sexta, nona) y del Oficio de lectura desde sync a la base propia (base/).

  CACHE=1 SEPTIES_FUENTES=… ORDO=… python3 tools/importar/importar_horas.py [tercia sexta nona oficio]

Igual que importar_laudes.py: cada parte del oficio se reparte en tres capas
  1. salterio  (base/salterio/<hora>.yaml): las cuatro semanas, tomadas de las ferias del Tiempo Ordinario;
  2. tiempo    (base/tiempo/<hora>.yaml): por feria (y ciclo A/B/C en los domingos), solo lo que cambia respecto del salterio;
  3. santoral  (base/santoral/<hora>.yaml): por celebración, solo lo que cambia respecto de las dos capas anteriores.
En el Oficio de lectura, las lecturas, sus responsorios y la oración nunca van en el salterio (cambian cada semana).
Para cada texto queda la versión que más se repite; las demás, en base/informes/<hora>.md.
"""
import collections, json, os, re, sys, tomllib
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import laudes_sync as L
import horas_sync as H
import importar_laudes as IL
from importar_laudes import Votos, sin_gloria, dia_semana, escribir, _aleluia, DIAS, BASE, SYNC, ORDO, clave_tiempo
from importar_visperas import id_v as _id_v


ROMANOS = r'(?:VI{0,3}|IV|I{1,3})'


def id_v(h):
    """Como en Vísperas, y además: «Salmo 118, 81-88» sin subtítulo, «Salmo 58, 2-6a: ORACIÓN…» (dos puntos) y los salmos
    partidos en cualquier forma: «Salmo 54, 2-15. 17-24 I - …», «Salmo 34, II», «SALMO 9B I», «Salmo 88, 39-53 - IV: …», «Salmo 17 V»."""
    h = re.sub(r'\s+', ' ', h or '').strip().rstrip('.')
    h = re.sub(r'(?i)^(salmo\s+\d+)([AB])\b', r'\1 \2', h)        # «Salmo 9A» → «Salmo 9 A»
    m = re.match(r'(?i)^salmo\s+(\d+)\s*([AB])?\s*(?:,\s*(\d[\d\-.,abc ]*?))?\s*(?:[-,]\s*)?\b(' + ROMANOS + r')\b\s*(?:[-.:]+\s*(.*))?$', h)
    if m and m.group(4):
        num, ab, vv, rom, sub = m.group(1), (m.group(2) or '').upper(), (m.group(3) or '').strip(' ,.-'), m.group(4).upper(), (m.group(5) or '').strip(' -:')
        vv = re.sub(r'\s*-\s*', '-', re.sub(r'\s*\.\s*', '. ', vv)).strip()
        ident = '-'.join(['salmo', num] + ([ab.lower()] if ab else []) + re.findall(r'\d+[ab]?', vv) + [rom.lower()])
        return ident, f'Salmo {num}{" " + ab if ab else ""}' + (f', {vv}' if vv else '') + f' {rom}', sub
    h = re.sub(r'^((?i:salmo)\s+\d+[^:]*?\d[abc]?)\s*:\s*', r'\1 - ', h)
    if re.fullmatch(r'(?i)salmo\s+\d+(?:\s*[AB])?(?:\s*,\s*[\d\-.,abc ]+)?', h): h += ' -'
    return _id_v(h)

NOMBRE = {'tercia': 'Tercia', 'sexta': 'Sexta', 'nona': 'Nona', 'oficio': 'Oficio de lectura'}
CAMPOS = {
    'menor': ['himno', 'salmodia', 'lectura', 'versiculo', 'oracion'],
    'oficio': ['himno', 'salmodia', 'versiculo', 'lectura1', 'resp1', 'lectura2', 'resp2', 'te_deum', 'oracion'],
}
SOLO_TIEMPO = {'menor': set(), 'oficio': {'lectura1', 'resp1', 'lectura2', 'resp2', 'oracion'}}


def tipo(hora): return 'oficio' if hora == 'oficio' else 'menor'


def cargar(hora):
    sys.path.insert(0, ORDO)
    from ordo.calendario import Ordo
    O = Ordo(ORDO, tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb')))
    est = H.estructura_oficio if hora == 'oficio' else H.estructura_menor
    out = []
    for fecha, var, f, idx in L.archivos(SYNC, hora):
        d = est(f); d['celebracion'] = L.celebracion(idx)
        D = O.dia(date.fromisoformat(fecha))
        d.update(fecha=fecha, var=var, tiempo=D.tiempo, semana=D.semana, salterio=D.salterio, feria=D.feria.nombre)
        d.pop('ruta', None)
        out.append(d)
    return out


def partes(d, S, hora):
    p = {}
    if d.get('himno') and d['himno'].get('texto'):
        pr = d['himno']['texto'][0].split('\n')[0].strip().rstrip('.,;:').strip()
        p['himno'] = pr; S('himno/' + pr, d['himno']['texto'], d['fecha'])
    if len(d['salmodia']) == 3:
        sal = []
        for g in d['salmodia']:
            ident, nombre, sub = id_v(g['salmo'] or '')
            if not ident: sal = None; break
            ident = IL.ALIAS.get(ident, ident)
            est, _ = sin_gloria(g['texto'])
            S('salmo/' + ident, {'titulo': nombre, 'subtitulo': sub, 'texto': est}, d['fecha'])
            x = {'salmo': ident}
            if g.get('ant'): x['ant'] = g['ant']
            if g.get('ant_fin') and g['ant_fin'] != g.get('ant'): x['ant_fin'] = g['ant_fin']
            sal.append(x)
        # una sola antífona para los tres salmos: va antes del primero y después del último
        if sal and 'ant' in sal[0] and not any('ant' in x for x in sal[1:]):
            fin = sal[2].pop('ant_fin', None)
            if fin and fin != sal[0]['ant']: sal[2]['ant_fin'] = fin
            sal[0]['unica'] = True
        if sal: p['salmodia'] = sal
    for k in ('lectura', 'versiculo', 'oracion'):
        if d.get(k): p[k] = d[k]
    # lecturas del Oficio: sin texto, no cuentan (ni su responsorio); fuera el «>» suelto que deja el HTML
    for k, r in (('lectura1', 'resp1'), ('lectura2', 'resp2')):
        x = d.get(k)
        if not x or not (x.get('texto') or '').strip(): continue
        p[k] = {c: re.sub(r'^\s*>\s*', '', v) if isinstance(v, str) else v for c, v in x.items()}
        if d.get(r) and d[r].get('vr'): p[r] = d[r]
    if hora == 'oficio': p['te_deum'] = bool(d.get('te_deum'))
    return p


def importar(todos, hora):
    IL.alias_salmos([{'salmodia': d['salmodia']} for d in todos])
    t = tipo(hora); C = CAMPOS[t]; ST = SOLO_TIEMPO[t]
    S, V = Votos(), Votos()
    dias = []
    for d in todos:
        p = partes(d, S, hora)
        cel = d['celebracion'].get('nombre') if d['celebracion'].get('grado') else None
        dias.append((d, p, cel))
        if d.get('conclusion'): S('conclusion', d['conclusion'], d['fecha'])
    # 1) salterio: ferias del Tiempo Ordinario sin celebración
    for d, p, cel in dias:
        if cel or d['tiempo'] != 'Ordinario': continue
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
        for k in C:
            if k in ST: continue
            if dia_semana(d['fecha']) == 'domingo' and k == 'oracion': continue
            if k in p: V(f'salterio/{sk}/{k}', p[k], d['fecha'])
    sal = lambda sk, k: None if k in ST else V.ganador(f'salterio/{sk}/{k}')
    # 2) tiempo
    for d, p, cel in dias:
        if cel: continue
        if d['tiempo'] == 'Ordinario' and dia_semana(d['fecha']) != 'domingo' and not (set(p) & ST): continue
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
        for k in C:
            if d['tiempo'] == 'Ordinario' and dia_semana(d['fecha']) != 'domingo' and k not in ST: continue
            if k in p and p[k] != sal(sk, k): V(f'tiempo/{clave_tiempo(d)}/{k}', p[k], d['fecha'])
            elif k in p: V(f'tiempo/{clave_tiempo(d)}/{k}', '=', d['fecha'])
    def base_dia(d):
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"; kt = clave_tiempo(d)
        def g(k):
            x = V.ganador(f'tiempo/{kt}/{k}')
            return sal(sk, k) if x in (None, '=') else x
        return g
    # 3) santoral
    fechas_cel = collections.defaultdict(collections.Counter); info = {}
    for d, p, cel in dias:
        if not cel: continue
        g = base_dia(d)
        fechas_cel[cel][d['fecha'][5:]] += 1
        info.setdefault(cel, collections.Counter())[(d['celebracion']['grado'], d['celebracion'].get('comun', ''))] += 1
        for k in C:
            if k in p and p[k] != g(k): V(f'santoral/{cel}/{k}', p[k], d['fecha'])
            elif k in p: V(f'santoral/{cel}/{k}', '=', d['fecha'])
    return S, V, dias, fechas_cel, info


def escribir_base(S, V, dias, fechas_cel, info, hora):
    G = V.ganador; C = CAMPOS[tipo(hora)]; nom = NOMBRE[hora]
    salterio = {}
    for s in '1234':
        salterio[f'semana_{s}'] = {}
        for dia in DIAS[6:] + DIAS[:6]:
            e = {k: G(f'salterio/{s}/{dia}/{k}') for k in C}
            salterio[f'semana_{s}'][dia] = {k: v for k, v in e.items() if v is not None}
    escribir(os.path.join(BASE, 'salterio', f'{hora}.yaml'), salterio,
             f'Salterio de {nom}: cuatro semanas (Tiempo Ordinario). Los salmos se citan por su clave (base/salmos/).'
             + ('\nLas lecturas, sus responsorios y la oración van en base/tiempo/oficio.yaml.' if hora == 'oficio' else ''))

    def capa(pref):
        out = collections.OrderedDict()
        for c in V.v:
            if c.startswith(pref):
                n, k = c[len(pref):].rsplit('/', 1)
                out.setdefault(n, {})[k] = G(c)
        return out
    T = capa('tiempo/')
    tiempo = collections.OrderedDict((n, {k: v for k, v in e.items() if v != '='}) for n, e in T.items())
    tiempo = collections.OrderedDict((n, e) for n, e in tiempo.items() if e)
    juntos = collections.defaultdict(dict)
    for n in list(tiempo):
        m = re.match(r'^(.*) \(([ABC])\)$', n)
        if m: juntos[m.group(1)][m.group(2)] = tiempo[n]
    for bn, cs in juntos.items():
        campos = set().union(*cs.values())
        com = {k: cs[next(iter(cs))].get(k) for k in campos if len(cs) == 3 and len({json.dumps(c.get(k), ensure_ascii=False, sort_keys=True) for c in cs.values()}) == 1}
        if com:
            tiempo[bn] = com
            for c in cs:
                resto = {k: v for k, v in tiempo[f'{bn} ({c})'].items() if k not in com}
                if resto: tiempo[f'{bn} ({c})'] = resto
                else: del tiempo[f'{bn} ({c})']
    from importar_laudes import date as _d
    def desde_adviento(f):
        from datetime import timedelta
        d = _d.fromisoformat(f)
        def adv(y):
            n = _d(y, 12, 25); return n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
        a = adv(d.year) if d >= adv(d.year) else adv(d.year - 1)
        return (d - a).days
    pos = {}
    for d, p, c in dias:
        if not c: pos[d['feria']] = min(pos.get(d['feria'], 999), desde_adviento(d['fecha']))
    orden = sorted(tiempo, key=lambda n: (pos.get(re.sub(r' \([ABC]\)$', '', n), 999), n))
    escribir(os.path.join(BASE, 'tiempo', f'{hora}.yaml'), {n: tiempo[n] for n in orden},
             f'Propio del tiempo de {nom}: por feria (nombre del Ordo); en los domingos, «(A)», «(B)» o «(C)» cuando cambia con el ciclo.\n'
             'Solo figura lo que cambia respecto del salterio.')
    Sa = capa('santoral/')
    santoral = collections.OrderedDict()
    for n in sorted(Sa, key=lambda n: fechas_cel[n].most_common(1)[0][0]):
        e = {k: v for k, v in Sa[n].items() if v != '='}
        (grado, comun), _ = info[n].most_common(1)[0]
        fe = [f for f, _ in fechas_cel[n].most_common()]
        santoral[n] = {'grado': grado, 'fecha': fe[0] if len(fe) == 1 or fechas_cel[n][fe[0]] > sum(fechas_cel[n].values()) / 2 else 'variable',
                       **({'comun': comun} if comun else {}), **e}
    escribir(os.path.join(BASE, 'santoral', f'{hora}.yaml'), dict(santoral),
             f'Santoral de {nom} (calendario de sync): por celebración. Solo lo que cambia respecto del salterio y del tiempo.')
    himnos = {c[6:]: S.ganador(c) for c in sorted(S.v) if c.startswith('himno/')}
    escribir(os.path.join(BASE, 'himnos', f'{hora}.yaml'), himnos, f'Himnos de {nom} en español, por primer verso.')
    nuevos = 0
    for c in S.v:
        if c.startswith('salmo/'):
            ruta = os.path.join(BASE, 'salmos', c.split('/', 1)[1] + '.yaml')
            if os.path.exists(ruta): continue
            x = S.ganador(c); nuevos += 1
            escribir(ruta, x, f"{x['titulo']}. Texto de la Liturgia de las Horas en español; estrofas separadas por renglón en blanco.")
    return len(tiempo), len(santoral), len(himnos), nuevos


def informe(S, V, todos, hora):
    L_ = [f'# {NOMBRE[hora]}: variantes encontradas en sync', '',
          f'Se leyeron {len(todos)} oficios ({todos[0]["fecha"]} a {todos[-1]["fecha"]}). Quedó la versión más frecuente de cada texto; abajo, las demás.', '']
    for W in (V, S):
        for clave, vs in W.variantes():
            if clave.startswith('himno/'): continue
            vs = [(v, f) for v, f in vs if v != '=']
            if len(vs) < 2: continue
            L_.append(f'## {clave}')
            for i, (val, fechas) in enumerate(vs[:4]):
                m = json.dumps(val, ensure_ascii=False)
                L_.append(f'- {"**en la base**" if i == 0 else "variante"} · {len(fechas)} veces · {", ".join(fechas[:4])}{"…" if len(fechas) > 4 else ""}')
                if i: L_.append(f'  `{m[:200]}{"…" if len(m) > 200 else ""}`')
            L_.append('')
    open(os.path.join(BASE, 'informes', f'{hora}.md'), 'w', encoding='utf-8').write(_aleluia('\n'.join(L_)))


# ---------- Hora intermedia: las tres horas juntas ----------
GRADUALES = {f'salmo-{n}' for n in range(119, 132)}
ids = lambda sal: [x['salmo'] for x in sal]
CAMPOS_M = ['himno', 'ant', 'lectura', 'versiculo', 'oracion']


def importar_intermedia(T):
    """T = {hora: [días]}. La salmodia del día (una sola) sale de la hora que no trae los graduales;
    la complementaria, de cada hora; himno, antífona propia (si la hay), lectura, versículo y oración, por hora."""
    todos = [d for h in T for d in T[h]]
    IL.alias_salmos([{'salmodia': d['salmodia']} for d in todos])
    S, V = Votos(), Votos()
    por_fecha = collections.defaultdict(dict)
    for h, ds in T.items():
        for d in ds: por_fecha[(d['fecha'], d['var'])][h] = d
    regs = []
    for (f, var), hs in sorted(por_fecha.items()):
        d0 = next(iter(hs.values()))
        cel = d0['celebracion'].get('nombre') if d0['celebracion'].get('grado') else None
        dia = {}
        P = {h: partes(d, S, h) for h, d in hs.items()}
        for h, p in P.items():
            sal = p.get('salmodia')
            e = {k: p[k] for k in ('himno', 'lectura', 'versiculo', 'oracion') if k in p}
            if sal: e['ant'] = sal[0]['ant'] if sal[0].get('unica') else ''   # '' = sin antífona propia de la hora (también vota)
            if sal and all(x['salmo'] in GRADUALES for x in sal):
                if not sal[0].get('unica') and all('ant' in x for x in sal) and not cel and d0['tiempo'] == 'Ordinario':
                    V(f'complementaria/{h}', sal, f)                                    # graduales con sus antífonas
                elif 'ant' not in e and sal[0].get('unica'): pass
            elif sal:
                dia['salmodia'] = [{k: v for k, v in x.items() if k != 'unica' and not (k == 'ant' and sal[0].get('unica'))} for x in sal]
            P[h] = e
        regs.append((d0, cel, dia, P))
        for h, d in hs.items():
            if d.get('conclusion'): S('conclusion', [x for x in d['conclusion'] if x[0]], f)
    def capas(nombre, campos, valor):
        """salterio / tiempo / santoral para un juego de campos; valor(reg) → dict de campos."""
        for d, cel, dia, P in regs:
            if cel or d['tiempo'] != 'Ordinario': continue
            v = valor(dia, P); sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
            for k in campos:
                if k in v: V(f'{nombre}/salterio/{sk}/{k}', v[k], d['fecha'])
        sal = lambda sk, k: V.ganador(f'{nombre}/salterio/{sk}/{k}')
        for d, cel, dia, P in regs:
            if cel or (d['tiempo'] == 'Ordinario' and dia_semana(d['fecha']) != 'domingo'): continue
            v = valor(dia, P); sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
            for k in campos:
                if k in v: V(f'{nombre}/tiempo/{clave_tiempo(d)}/{k}', '=' if v[k] == sal(sk, k) else v[k], d['fecha'])
        for d, cel, dia, P in regs:
            if not cel: continue
            v = valor(dia, P); sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
            t = lambda k: (lambda x: sal(sk, k) if x in (None, '=') else x)(V.ganador(f'{nombre}/tiempo/{clave_tiempo(d)}/{k}'))
            for k in campos:
                if k in v: V(f'{nombre}/santoral/{cel}/{k}', '=' if v[k] == t(k) else v[k], d['fecha'])
    capas('intermedia', ['salmodia'], lambda dia, P: dia)
    capas('intermedia_ids', ['salmos'], lambda dia, P: {'salmos': ids(dia['salmodia'])} if 'salmodia' in dia else {})
    for h in T: capas(h, CAMPOS_M, lambda dia, P, h=h: P.get(h, {}))
    return S, V, regs


def escribir_intermedia(S, V, regs, horas):
    G = V.ganador
    fechas_cel = collections.defaultdict(collections.Counter); info = {}
    for d, cel, dia, P in regs:
        if cel:
            fechas_cel[cel][d['fecha'][5:]] += 1
            info.setdefault(cel, collections.Counter())[(d['celebracion']['grado'], d['celebracion'].get('comun', ''))] += 1
    pos = {}
    for d, cel, dia, P in regs:
        if not cel: pos.setdefault(d['feria'], d['fecha'])
    def capa(pref):
        out = collections.OrderedDict()
        for c in V.v:
            if c.startswith(pref):
                n, k = c[len(pref):].rsplit('/', 1)
                x = G(c)
                if x != '=': out.setdefault(n, {})[k] = x
        return out
    def ordenar_t(t): return {n: t[n] for n in sorted(t, key=lambda n: (date.fromisoformat(pos.get(re.sub(r' \([ABC]\)$', '', n), '2099-01-01')).timetuple().tm_yday + (0 if pos.get(re.sub(r' \([ABC]\)$', '', n), '2099')[5:7] >= '11' and pos.get(re.sub(r' \([ABC]\)$', '', n), '2099')[5:10] >= '11-27' else 400), n))}
    def ordenar_s(t): return {n: {'grado': info[n].most_common(1)[0][0][0], 'fecha': fechas_cel[n].most_common(1)[0][0], **t[n]} for n in sorted(t, key=lambda n: fechas_cel[n].most_common(1)[0][0])}
    for nombre, nom, campos in [('intermedia', 'Hora intermedia (salmodia del día)', ['salmodia'])] + [(h, NOMBRE[h], CAMPOS_M) for h in horas]:
        sal = {f'semana_{s}': {dia: {k: G(f'{nombre}/salterio/{s}/{dia}/{k}') for k in campos if G(f'{nombre}/salterio/{s}/{dia}/{k}') not in (None, '')}
                               for dia in DIAS[6:] + DIAS[:6]} for s in '1234'}
        escribir(os.path.join(BASE, 'salterio', f'{nombre}.yaml'), sal,
                 f'Salterio de {nom}: cuatro semanas (Tiempo Ordinario).' + (' Una sola salmodia para Tercia, Sexta y Nona; las antífonas por salmo valen fuera de los tiempos con antífona propia de cada hora.' if nombre == 'intermedia' else ''))
        cn = 'intermedia_ids' if nombre == 'intermedia' else nombre      # salmodia del día: en tiempo y santoral, solo qué salmos
        escribir(os.path.join(BASE, 'tiempo', f'{nombre}.yaml'), ordenar_t(capa(f'{cn}/tiempo/')),
                 f'Propio del tiempo de {nom}: por feria; solo lo que cambia respecto del salterio.' + (' «ant»: antífona propia de la hora para los tres salmos.' if nombre != 'intermedia' else ''))
        escribir(os.path.join(BASE, 'santoral', f'{nombre}.yaml'), ordenar_s(capa(f'{cn}/santoral/')),
                 f'Santoral de {nom} (calendario de sync): por celebración; solo lo que cambia.')
    for h in horas:
        himnos = {}
        for d, cel, dia, P in regs:
            pass
        escribir(os.path.join(BASE, 'himnos', f'{h}.yaml'), {c[6:]: S.ganador(c) for c in sorted(S.v) if c.startswith('himno/') and any(c[6:] == P.get(h, {}).get('himno') for _, _, _, P in regs)},
                 f'Himnos de {NOMBRE[h]} en español, por primer verso.')
    comp = {h: G(f'complementaria/{h}') for h in horas}
    escribir(os.path.join(BASE, 'ordinario', 'intermedia.yaml'), {
        'nombre': 'Hora intermedia',
        'complementaria': comp,
        'conclusion': [{a: b} for a, b in (S.ganador('conclusion') or [])],
    }, 'Ordinario de la Hora intermedia: salmodia complementaria de cada hora (salmos graduales, con sus antífonas del Tiempo Ordinario)\n'
       'y conclusión. La complementaria se usa al rezar más de una hora, y en las solemnidades que no caen en domingo.')
    nuevos = 0
    for c in S.v:
        if c.startswith('salmo/'):
            ruta = os.path.join(BASE, 'salmos', c.split('/', 1)[1] + '.yaml')
            if os.path.exists(ruta): continue
            x = S.ganador(c); nuevos += 1
            escribir(ruta, x, f"{x['titulo']}. Texto de la Liturgia de las Horas en español; estrofas separadas por renglón en blanco.")
    return comp, nuevos


if __name__ == '__main__':
    pedidas = sys.argv[1:] or ['tercia', 'sexta', 'nona', 'oficio']
    menores = [h for h in pedidas if h != 'oficio']
    if menores:
        T = {}
        for hora in menores:
            cache = f'/tmp/{hora}_sync.json'
            if os.environ.get('CACHE') and os.path.exists(cache): T[hora] = json.load(open(cache))
            else: T[hora] = cargar(hora); json.dump(T[hora], open(cache, 'w'), ensure_ascii=False)
        S, V, regs = importar_intermedia(T)
        comp, nuevos = escribir_intermedia(S, V, regs, menores)
        print('intermedia:', len(regs), 'días;', nuevos, 'salmos nuevos; complementaria:', {h: [x['salmo'] for x in (c or [])] for h, c in comp.items()})
        pedidas = [h for h in pedidas if h == 'oficio']

    for hora in pedidas:
        cache = f'/tmp/{hora}_sync.json'
        if os.environ.get('CACHE') and os.path.exists(cache): todos = json.load(open(cache))
        else: todos = cargar(hora); json.dump(todos, open(cache, 'w'), ensure_ascii=False)
        S, V, dias, fc, info = importar(todos, hora)
        nt, ns, nh, nsal = escribir_base(S, V, dias, fc, info, hora)
        informe(S, V, todos, hora)
        conc = S.ganador('conclusion')
        print(f'{hora}: {len(todos)} leídas; tiempo {nt}; santoral {ns}; {nh} himnos; {nsal} salmos nuevos; conclusión {conc}')
