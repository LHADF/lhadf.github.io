#!/usr/bin/env python3
"""Pasa la base (base/*.yaml y base/gregoriano/*.gabc) a src/datos/base.js para la app.

    python3 tools/base_js.py      (lo llama tools/armar.py)
"""
import glob, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools', 'importar'))
from yaml_base import leer
import re
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
from normalizar_gabc import negrita

B = os.path.join(RAIZ, 'base')


def pares(lista):
    return [[x.strip() for x in s.split(' = ', 1)] for s in lista or []]


def gabc(nombre):
    s = open(os.path.join(B, 'gregoriano', nombre), encoding='utf-8').read()
    return s.replace('<v>\\greheightstar</v>', '*')   # asterisco de Gregorio → asterisco común


def invitatorio_gregoriano(I):
    """Invitatorio cantado: la antífona (sin el arranque «Ps.» del salmo, que va entero) y el Salmo 94 partido en estrofas."""
    ant = gabc(I['antifona']); cab, cuerpo = ant.split('%%', 1)
    cuerpo = re.split(r'<c><i>Ps\.', cuerpo)[0].replace('(Z)', '').rstrip()
    sal = gabc(I['salmo']).split('%%', 1)[1]
    trozos = [t.strip() for t in re.split(r'\(::Z?\)', sal) if t.strip()]
    assert len(trozos) == len(I['estrofas']), 'invitatorio: una traducción por estrofa'
    minus = lambda t: re.sub(r'^(\(f3\)\s*)VE\(', r'\1Ve(', t)   # «VEníte»: la capitular ya agranda la primera letra
    cuerpo, trozos = minus(cuerpo.lstrip()), [minus(t) for t in trozos]
    estrofas = [{'gabc': 'name:Psalmus 94;\n%%\n' + ('' if t.startswith('(f3)') else '(f3) ') + t + ' (::)', 'traduccion': pares(e['traduccion'])} for t, e in zip(trozos, I['estrofas'])]
    return {'ant': {'gabc': cab + '%%' + cuerpo, 'traduccion': pares(I['traduccion'])}, 'estrofas': estrofas}


def oraciones_oficio():
    O = leer(os.path.join(B, 'ordinario', 'oraciones-oficio.yaml'))
    for k in ('preparatoria', 'conclusiva'):
        for c, v in O[k].items():
            if isinstance(v, list): O[k][c] = pares(v)
    return O


def espanol():
    """Textos de la opción «Solo español» (base/ordinario/espanol.yaml), con lo que ya estaba en español en la base."""
    E = leer(os.path.join(B, 'ordinario', 'espanol.yaml'))
    OL = leer(os.path.join(B, 'ordinario', 'laudes.yaml'))
    OC = leer(os.path.join(B, 'ordinario', 'completas.yaml'))
    OO = leer(os.path.join(B, 'ordinario', 'oficio.yaml'))
    vr = lambda l: [[k, e[k]] for e in l for k in e if k in ('V', 'R')]   # sin las notas («texto: Of La Tr…»)
    return {**{k: v for k, v in E.items() if k not in ('conclusion_ministro', 'despedida')},
            'conclusion_ministro': vr(E['conclusion_ministro']), 'despedida': vr(E['despedida']),
            'invocacion': vr(OC['invocacion']), 'bendicion_completas': vr(OC['bendicion']),
            'antifona_simeon': OC['cantico_evangelico']['antifona'],
            'labia': [['V', OL['invitatorio']['V']], ['R', OL['invitatorio']['R']]],
            'benedictus': {k: OL['cantico_evangelico'][k] for k in ('titulo', 'subtitulo', 'ref', 'texto')},
            'conclusion': vr(OL['conclusion']), 'benedicamus': vr(OO['conclusion'])}


def repeticion(g):
    """Antífona repetida al final: la canta toda la asamblea (en negrita) y va sin asterisco."""
    return negrita(re.sub(r'\s*\*+\s*\(([,;:]*)\)', lambda m: f' ({m.group(1)})' if m.group(1) else '', g))


def primer_verso(g):
    """Solo el primer versículo (hasta la primera doble barra), para cánticos que siguen pautados."""
    cab, _, cuerpo = g.partition('%%')
    i = cuerpo.index('(::)') + 4
    return cab + '%%' + cuerpo[:i] + '\n'


def desde_asterisco(g):
    """Lo que canta la asamblea, en negrita: desde el primer asterisco (la entonación, no)."""
    cab, _, cuerpo = g.partition('%%')
    m = re.search(r'\*', re.sub(r'\([^)]*\)', lambda x: ' ' * len(x.group(0)), cuerpo))   # (el asterisco de la letra, no de las notas)
    return negrita(g, m.start()) if m else g


def gregoriano_propios():
    """Antífonas propias en gregoriano (base/gregoriano/propios.yaml): las «Oh» del Magníficat y las que van en lugar del
    responsorio breve (Christus factus est, Hæc dies). Cuándo: el comienzo del texto español de la base."""
    P = leer(os.path.join(B, 'gregoriano', 'propios.yaml'))
    def pieza(k, x, rep):
        g = gabc(x['partitura'])
        m = re.search(r'^mode:\s*(\d)', g, re.M)
        o = {'id': k, 'titulo': x['titulo'], 'cuando': x['cuando'], 'gabc': desde_asterisco(g), 'traduccion': pares(x['traduccion']),
             'modo': int(m.group(1)) if m else None}
        if rep: o['repeticion'] = repeticion(g)
        return o
    return {'magnificat': [pieza(k, x, True) for k, x in P['magnificat'].items()],
            'responsorio': [pieza(k, x, False) for k, x in P['responsorio'].items()]}



def latin():
    """«Solo latín» (26/11/2026): la extracción de Universalis (extraccion/latin/dias/) → src/carga/latin-AAAA-MM.js, uno por
    mes, que la app carga al abrir una hora en latín. Por día: celebración (c), datos (d) y horas (h), cada una con sus bloques
    (t: título, r: cita, s: subtítulos, a: alternativa, u: rúbricas; l: renglones [texto, marcas] o n: número en la tabla T de
    renglones repetidos). Marcas: 1 sangría, 2 empieza estrofa, 4 cursiva, 8 negrita, 16 párrafo. R: cita latina → clave de
    base/salmos (extraccion/latin/salmos.json). Devuelve los meses."""
    D = os.path.join(RAIZ, 'extraccion', 'latin')
    if not os.path.isdir(os.path.join(D, 'dias')): return []
    sal = json.load(open(os.path.join(D, 'salmos.json'), encoding='utf-8')) if os.path.exists(os.path.join(D, 'salmos.json')) else {}
    R = {v['ref']: k for k, v in sal.items() if v.get('ref')}
    meses = []
    os.makedirs(os.path.join(RAIZ, 'src', 'carga'), exist_ok=True)   # en un clon nuevo no existe (src/carga no va al repo)
    for f in sorted(glob.glob(os.path.join(D, 'dias', '*.json'))):
        mes = os.path.basename(f)[:-5]; T = {}; dias = {}
        for d in json.load(open(f, encoding='utf-8'))['dias']:
            hs = {}
            for h, bl in d['horas'].items():
                bb = []
                for b in bl:
                    ls = [[l['t'], (1 if l.get('sangria') else 0) | (2 if l.get('estrofa') else 0) | (4 if l.get('cursiva') else 0)
                           | (8 if l.get('negrita') else 0) | (16 if l.get('p') else 0)] for l in b['lineas']]
                    x = {k: v for k, v in {'t': b.get('titulo'), 'r': b.get('ref'), 's': b.get('sub'), 'a': b.get('alternativa'), 'u': b.get('rubricas')}.items() if v}
                    if len(ls) >= 6:
                        k = json.dumps(ls, ensure_ascii=False); T.setdefault(k, len(T)); x['n'] = T[k]
                    else: x['l'] = ls
                    bb.append(x)
                hs[h] = bb
            dias[d['fecha']] = {'c': d.get('celebracion', ''), 'd': d.get('de_die', []), 'h': hs}
        tab = [json.loads(k) for k, _ in sorted(T.items(), key=lambda kv: kv[1])]
        destino = os.path.join(RAIZ, 'src', 'carga', f'latin-{mes}.js')
        with open(destino, 'w', encoding='utf-8') as g:
            g.write('(window.LATIN=window.LATIN||{})[' + json.dumps(mes) + ']=' + json.dumps({'dias': dias, 'T': tab, 'R': R}, ensure_ascii=False, separators=(',', ':')) + ';\n')
        meses.append(mes)
    print(f'src/carga/latin-*.js: {len(meses)} meses ({meses[0]} a {meses[-1]})' if meses else 'sin latín')
    return meses

def main():
    G = leer(os.path.join(B, 'gregoriano', 'completas.yaml'))
    inv, ce, co = G['invocacion'], G['cantico_evangelico'], G['conclusion']
    # por ahora la app arma solo Completas: se exportan los salmos que usa (Laudes se cargará aparte)
    SC = leer(os.path.join(B, 'salterio', 'completas.yaml'))
    USADOS = {x for j in SC.values() for k in ('salmodia', 'salmodia_pascua') for g in (j.get(k) or []) for x in g['salmos']} | {'cantico-simeon'}
    base = {
        'completas': {
            'ordinario': leer(os.path.join(B, 'ordinario', 'completas.yaml')),
            'salterio': leer(os.path.join(B, 'salterio', 'completas.yaml')),
            'tiempo': leer(os.path.join(B, 'tiempo', 'completas-triduo-octava.yaml')),
            'himnos': leer(os.path.join(B, 'himnos', 'completas.yaml')),
            'latinos': himnos_latinos('completas'),
            'gregoriano': {
                'invocacion': {'solemne': gabc(inv['solemne']), 'festivo': gabc(inv['festivo']), 'ferial': gabc(inv['ferial']), 'cortes_gloria': inv['cortes_gloria'], 'traduccion': pares(inv['traduccion']), 'laus': pares(inv['laus'])},
                'antifona': {'gabc': gabc(ce['antifona']), 'repeticion': repeticion(gabc(ce['antifona'])), 'traduccion': pares(ce['traduccion_antifona'])},
                'cantico': {'gabc': primer_verso(gabc(ce['cantico'])), 'traduccion': pares(ce['traduccion_cantico']),
                            'tono': str(ce['tono_cantico']), 'versos': ce['versos'], 'traduccion_versos': [pares(v) for v in ce['traduccion_versos']],
                            'primer_verso': ce['primer_verso']},
                'himno': {'titulo': G['himno']['titulo'], 'gabc': gabc(G['himno']['partitura']), 'traduccion': pares(G['himno']['traduccion'])},
                'lectura_respuesta': pares(G['lectura_respuesta']),
                'lectura_respuesta_glosa': pares(G['lectura_respuesta_glosa']),
                'responsorio': {k: {'gabc': gabc(v['partitura']), 'traduccion': pares(v['traduccion'])} for k, v in G['responsorio'].items()},
                'marianas': {k: {'titulo': v['titulo'], 'gabc': gabc(v['partitura']), 'cortes': v.get('cortes'), 'traduccion': pares(v['traduccion'])} for k, v in G['marianas'].items()},
                'conclusion': {'gabc': gabc(co['partitura']), 'traduccion': pares(co['traduccion'])},
                'tonos': G['tonos_salmos'],
            },
        },
        'gregoriano_propios': gregoriano_propios(),
        'marianas': leer(os.path.join(B, 'ordinario', 'antifonas-marianas.yaml')),
        'latinos_cuando': leer(os.path.join(B, 'himnos', 'latinos_cuando.yaml')),
        'oraciones': oraciones_oficio(),
        'espanol': espanol(),
        'latin_meses': latin(),   # «Solo latín»: meses con la hora latina de Universalis (src/carga/latin-AAAA-MM.js)
        'salmos': {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in USADOS},
    }
    destino = os.path.join(RAIZ, 'src', 'datos', 'base.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.BASE=' + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB')
    laudes()
    visperas()
    oficio()
    intermedia()
    ilustraciones()


# ---------- Laudes: archivo aparte (src/carga/laudes.js), la app lo carga recién al abrir Laudes ----------
import unicodedata
from datetime import date, timedelta

VACIAS = set('''san santo santa santos santas beato beata beatos el la los las de del y e en a nuestra nuestro senor
  obispo obispos doctor doctores doctora iglesia presbitero presbiteros martir martires virgen virgenes apostol apostoles
  evangelista papa religioso religiosa abad monje diacono bienaventurada santisima companeros patrona patron'''.split())


def _tok(n):
    n = ''.join(c for c in unicodedata.normalize('NFD', n.lower()) if unicodedata.category(c) != 'Mn')
    return {w for w in re.findall(r'[a-z]+', n) if w not in VACIAS}


def _sim(a, b):
    """(coincidencias, proporción sobre el nombre más corto, jaccard)"""
    a, b = _tok(a), _tok(b)
    if not a or not b: return (0, 0, 0)
    c = len(a & b); return (c, c / min(len(a), len(b)), c / len(a | b))


def vincular_santoral(santoral_todo):
    """Celebraciones del calendario ADF (src/datos/calendario.js) → entrada del santoral de Laudes (de sync).
    Primero por fecha y nombre; las movibles, solo por nombre. Devuelve (mapa, sin_vincular)."""
    santoral = {k: v for k, v in santoral_todo.items() if not k.endswith(' · I Vísperas')}
    cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
    cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
    tab, ix, d0 = cal['tabla'], {c: i for i, c in enumerate(cal['campos'])}, date.fromisoformat(cal['desde'])
    filas = [(d0 + timedelta(days=k), r) for k, r in enumerate(cal['dias'])] + [(date.fromisoformat(f), v[2]) for f, vs in cal['var'].items() for v in vs]
    mapa, sin = {}, {}
    A = leer(os.path.join(B, 'santoral', 'adf.yaml')) if os.path.exists(os.path.join(B, 'santoral', 'adf.yaml')) else {}
    for f, r in filas:
        n, g, fer = tab[r[ix['n']]], tab[r[ix['g']]], tab[r[ix['fer']]]
        if n in mapa or n in sin: continue
        if n in (A or {}):                       # lo escrito a mano en santoral/adf.yaml manda sobre el parecido de nombres
            if A[n].get('es') in santoral: mapa[n] = A[n]['es']
            else: sin[n] = g
            continue
        md = f.strftime('%m-%d')
        mismo_dia = [(k, _sim(n, k)) for k, v in santoral.items() if v.get('fecha') == md]
        mejor = max(mismo_dia, key=lambda x: x[1][1:], default=(None, (0, 0, 0)))
        if not (mejor[1][0] >= 1 and mejor[1][1] >= 0.5):
            otro = max(((k, _sim(n, k)) for k in santoral), key=lambda x: x[1][1:], default=(None, (0, 0, 0)))
            mejor = otro if (otro[1][0] >= 2 and otro[1][1] >= 0.66 and otro[1][2] >= 0.4) or otro[1][2] == 1 else (None, 0)
        if n == fer and not (mejor[0] and _sim(n, mejor[0])[2] == 1): continue   # días del propio del tiempo: solo coincidencia exacta
        if mejor[0]: mapa[n] = mejor[0]
        elif n != fer: sin[n] = g
    return mapa, sin


def laudes():
    GL = leer(os.path.join(B, 'gregoriano', 'laudes.yaml'))
    SL = leer(os.path.join(B, 'salterio', 'laudes.yaml'))
    TL = leer(os.path.join(B, 'tiempo', 'laudes.yaml'))
    SaL = leer(os.path.join(B, 'santoral', 'laudes.yaml'))
    HL = leer(os.path.join(B, 'himnos', 'laudes.yaml'))
    OL = leer(os.path.join(B, 'ordinario', 'laudes.yaml'))
    usados = {g['salmo'] for capa in ([e for w in SL.values() for e in w.values()], TL.values(), SaL.values()) for e in capa for g in (e.get('salmodia') or [])}
    usados |= {'salmo-94'} | salmos_comunes('laudes')
    salmos = {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in usados}
    mapa, sin = vincular_santoral(SaL)
    bn = GL['benedictus']
    datos = {
        'salterio': SL, 'tiempo': TL, 'santoral': SaL, 'himnos': HL, 'latinos': himnos_latinos('laudes'), 'ordinario': OL, 'salmos': salmos,
        'mapa': mapa, 'sin_vincular': sin, 'adf': adf_y_comunes('laudes', SaL)[0], 'dos': dos_comunes(), 'comunes': adf_y_comunes('laudes', SaL)[1],
        'gregoriano': {
            'invitatorio': {'gabc': gabc(GL['invitatorio']['partitura']), 'traduccion': pares(GL['invitatorio']['traduccion'])},
            'invitatorio_to': invitatorio_gregoriano(GL['invitatorio_per_annum']),
            'cantico': {'titulo': bn['titulo'], 'ref': bn['ref'], 'versos': bn['versos'], 'traduccion_versos': [pares(v) for v in bn['traduccion_versos']]},
            **comunes_latin(GL),
            'himnos': himnos_gregorianos('laudes'),
            'conclusion': {'gabc': gabc(GL['conclusion']['partitura']), 'traduccion': pares(GL['conclusion']['traduccion'])},
        },
    }
    destino = os.path.join(RAIZ, 'src', 'carga', 'laudes.js')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.LAUDES=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


def dos_comunes():
    """Celebraciones que pueden tomar de dos (o tres) comunes (base/santoral/dos_comunes.yaml): {nombre: [claves]}."""
    return leer(os.path.join(B, 'santoral', 'dos_comunes.yaml')) or {}


def adf_y_comunes(hora, santoral):
    """Celebraciones sin propio en la base (base/santoral/adf.yaml) y los comunes que usan (del libro). El Oficio y la Hora
    intermedia no traen oraciones en el común («como en Laudes»): se les pasan las de Laudes."""
    A = leer(os.path.join(B, 'santoral', 'adf.yaml')) or {}
    C = leer(os.path.join(B, 'comunes', hora + '.yaml')) or {}
    CL = leer(os.path.join(B, 'comunes', 'laudes.yaml')) or {}
    for k, c in C.items():
        if not c.get('oraciones') and CL.get(k, {}).get('oraciones'): c['oraciones'] = CL[k]['oraciones']
    # Propio del libro (base/santoral/libro.yaml): la oración y lo que la celebración tenga de propio en esta hora
    LIB = leer(os.path.join(B, 'santoral', 'libro.yaml')) or {}
    claves = {'laudes': ['laudes'], 'visperas': ['visperas'], 'oficio': ['oficio'], 'intermedia': ['tercia', 'sexta', 'nona']}[hora]
    out = {}
    for n, a in A.items():
        if a.get('como') and a['como'] not in santoral: continue
        a = dict(a)
        if n in LIB:
            pr = {'oracion': LIB[n].get('oracion')} if LIB[n].get('oracion') else {}
            for k in claves:
                if LIB[n].get(k): pr.update(LIB[n][k]) if hora != 'intermedia' else pr.update({k: LIB[n][k]})
            if hora == 'laudes' and LIB[n].get('invitatorio', {}).get('inv_ant'): pr['inv_ant'] = LIB[n]['invitatorio']['inv_ant']
            if hora == 'visperas' and LIB[n].get('visperas1'): pr['primeras'] = LIB[n]['visperas1']
            if pr: a['propio'] = pr
        out[n] = a
    # Celebraciones con propio en Laudes pero sin entrada en esta hora (p. ej. memorias cuyas Vísperas el libro manda
    # tomar del común: Santa Isabel de Hungría): el común que dice su santoral de Laudes (o adf.yaml, o el libro) y
    # la oración de Laudes. Sin esto se rezaba la feria. Con «de» (adf.yaml), sin común: lo demás sale de esa celebración.
    if hora in ('visperas', 'oficio', 'intermedia'):
        SaL = leer(os.path.join(B, 'santoral', 'laudes.yaml')) or {}
        mapaL, _ = vincular_santoral(SaL)
        mapaH, _ = vincular_santoral(santoral)
        for n, k in list(mapaL.items()) + [(n, a['es']) for n, a in A.items() if a.get('es') in SaL]:
            a = dict(out.get(n) or {})
            if n in mapaH or a.get('como') or a.get('pendiente') or (a.get('es') and a['es'] in santoral): continue
            if not a.get('de'):
                if hora == 'intermedia' or a.get('es'): continue
                c = (A.get(n) or {}).get('comun') or comun_de_texto(SaL[k].get('comun')) or (LIB.get(n) or {}).get('comun_libro')
                if not c or c not in C: continue
                a['comun'] = c
            if SaL[k].get('oracion'): a['propio'] = {'oracion': SaL[k]['oracion'], **(a.get('propio') or {})}
            out[n] = a
    return out, C


def salmos_comunes(hora):
    """Salmos de los comunes y del propio del libro (base/santoral/libro.yaml) de esta hora."""
    C = leer(os.path.join(B, 'comunes', hora + '.yaml')) or {}
    LIB = leer(os.path.join(B, 'santoral', 'libro.yaml')) or {}
    claves = {'laudes': ['laudes'], 'visperas': ['visperas', 'visperas1'], 'oficio': ['oficio'], 'intermedia': ['tercia', 'sexta', 'nona']}[hora]
    partes = [p for c in C.values() for p in (c, c.get('primeras') or {})] + [e[k] for e in LIB.values() for k in claves if e.get(k)]
    return {g['salmo'] for p in partes for g in (p.get('salmodia') or [])} | {s for c in C.values() for s in (c.get('salmos') or [])}   # (Oficio de difuntos: salmos propios de la Hora intermedia)


def himnos_latinos(*horas):
    """Himnos latinos recitados (base/himnos/latinos.yaml) de estas horas, según latinos_cuando.yaml: título, estrofas en
    pares [latín, traducción literal] por verso, Amén y estrofas variantes por caso ({caso: {índice desde 0: estrofa}})."""
    H = leer(os.path.join(B, 'himnos', 'latinos.yaml'))['himnos']
    C = leer(os.path.join(B, 'himnos', 'latinos_cuando.yaml'))
    usados = set()
    for tabla in (*C['tiempo'].values(), *C['celebraciones'].values(), *C['comunes'].values(), *C.get('propios', {}).values()):
        for h, v in tabla.items():
            if h.rstrip('1') in horas: usados |= set(v if isinstance(v, list) else [v])
    for k in usados: assert k in H, f'latinos_cuando.yaml: falta el himno «{k}» en latinos.yaml'
    def est(t):
        out = []
        for l in t.split('\n'):
            la, _, es = l.partition(' = ')
            assert la.strip() and es.strip(), f'himnos/latinos.yaml: verso sin traducción: «{l}»'
            out.append([la.strip(), es.strip()])
        return out
    return {k: {'titulo': h['titulo'], 'amen': bool(h.get('amen')), 'estrofas': [est(e) for e in h['estrofas']],
                **({'variantes': {c: {int(i) - 1: est(e) for i, e in v.items()} for c, v in h['variantes'].items()}} if h.get('variantes') else {})}
            for k, h in H.items() if k in usados}


def himnos_gregorianos(hora):
    """Himnos en gregoriano de esta hora (base/gregoriano/himnos.yaml): cuándo va cada uno, partitura y traducción por frases
    (estrofas → versos → pares «latín = español»)."""
    H = leer(os.path.join(B, 'gregoriano', 'himnos.yaml'))
    C = H['cuando']
    M = {k: v for k, v in C['marianas'].items() if k != 'nombres'}
    tablas = [*C['ordinario'].values(), C['adviento'], *C['celebraciones'].values(), M]
    usados = {v for t in tablas for k, v in t.items() if (k == 'laudes') == (hora == 'laudes')}
    for v in {v for t in tablas for v in t.values()}: assert v in H['himnos'], f'himnos.yaml: falta el himno «{v}»'
    himnos = {k: {'titulo': h['titulo'], 'gabc': gabc(h['partitura']), 'estrofas': [[pares(v) for v in e] for e in h['estrofas']],
                  'amen': pares([h['amen']])[0], **({'rubrica': h['rubrica']} if h.get('rubrica') else {})} for k, h in H['himnos'].items() if k in usados}
    return {'cuando': C, 'himnos': himnos}


def comunes_latin(GL):
    """Partes en latín compartidas por Laudes y Vísperas."""
    return {'pater_noster': pares(GL['pater_noster']), 'pater_cortes': GL['pater_cortes'],
            'bendicion': {'simple': gabc(GL['bendicion']['simple']), 'solemne': gabc(GL['bendicion']['solemne']), 'traduccion': pares(GL['bendicion']['traduccion']), 'despedida': pares(GL['bendicion']['despedida'])},
            'conclusion': {'gabc': gabc(GL['conclusion']['partitura']), 'traduccion': pares(GL['conclusion']['traduccion'])}}


def visperas():
    GL = leer(os.path.join(B, 'gregoriano', 'laudes.yaml'))
    MG = leer(os.path.join(B, 'gregoriano', 'magnificat.yaml'))
    SV = leer(os.path.join(B, 'salterio', 'visperas.yaml'))
    TV = leer(os.path.join(B, 'tiempo', 'visperas.yaml'))
    SaV = leer(os.path.join(B, 'santoral', 'visperas.yaml'))
    HV = leer(os.path.join(B, 'himnos', 'visperas.yaml'))
    usados = {g['salmo'] for capa in ([e for w in SV.values() for e in w.values()], TV.values(), SaV.values()) for e in capa for g in (e.get('salmodia') or [])} | salmos_comunes('visperas')
    salmos = {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in usados}
    mapa, sin = vincular_santoral(SaV)
    datos = {'salterio': SV, 'tiempo': TV, 'santoral': SaV, 'himnos': HV, 'latinos': himnos_latinos('visperas'), 'salmos': salmos, 'mapa': mapa, 'sin_vincular': sin, 'adf': adf_y_comunes('visperas', SaV)[0], 'dos': dos_comunes(), 'comunes': adf_y_comunes('visperas', SaV)[1],
             'gregoriano': {**comunes_latin(GL), 'himnos': himnos_gregorianos('visperas'),
                            'cantico': {'titulo': MG['titulo'], 'ref': MG['ref'], 'versos': MG['versos'], 'traduccion_versos': [pares(v) for v in MG['traduccion_versos']]}}}
    destino = os.path.join(RAIZ, 'src', 'carga', 'visperas.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.VISPERAS=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


def _salmos(usados):
    return {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in usados}


def _usados(*capas):
    u = set()
    for c in capas:
        for e in c:
            for g in (e.get('salmodia') or []): u.add(g['salmo'])
            for x in (e.get('salmos') or []): u.add(x)
    return u


def oficio():
    """Oficio de lectura → src/carga/oficio.js (se carga al abrir la hora)."""
    SO, TO, SaO = (leer(os.path.join(B, c, 'oficio.yaml')) for c in ('salterio', 'tiempo', 'santoral'))
    HO, OO, GH = leer(os.path.join(B, 'himnos', 'oficio.yaml')), leer(os.path.join(B, 'ordinario', 'oficio.yaml')), leer(os.path.join(B, 'gregoriano', 'horas.yaml'))
    mapa, sin = vincular_santoral(SaO)
    A = leer(os.path.join(B, 'santoral', 'adf.yaml')) or {}
    datos = {'salterio': SO, 'tiempo': TO, 'santoral': SaO, 'himnos': HO, 'latinos': himnos_latinos('oficio'), 'ordinario': OO,
             'salmos': _salmos(_usados([e for w in SO.values() for e in w.values()], TO.values(), SaO.values()) | salmos_comunes('oficio')),
             'mapa': mapa, 'adf': adf_y_comunes('oficio', SaO)[0], 'dos': dos_comunes(), 'comunes': adf_y_comunes('oficio', SaO)[1],
             'gregoriano': {'benedicamus': pares(GH['benedicamus']['traduccion'])}}
    _escribir_carga('oficio', 'OFICIO', datos, mapa, sin)


def intermedia():
    """Tercia, Sexta y Nona → src/carga/intermedia.js: una salmodia del día y, por hora, himno, antífona, lectura, versículo y oración."""
    SI, TI, SaI = (leer(os.path.join(B, c, 'intermedia.yaml')) for c in ('salterio', 'tiempo', 'santoral'))
    OI, GH = leer(os.path.join(B, 'ordinario', 'intermedia.yaml')), leer(os.path.join(B, 'gregoriano', 'horas.yaml'))
    horas, todos = {}, dict(SaI)
    for h in ('tercia', 'sexta', 'nona'):
        horas[h] = {c: leer(os.path.join(B, c, f'{h}.yaml')) for c in ('salterio', 'tiempo', 'santoral', 'himnos')}
        for n, e in horas[h]['santoral'].items(): todos.setdefault(n, e)
    mapa, sin = vincular_santoral(todos)
    A = leer(os.path.join(B, 'santoral', 'adf.yaml')) or {}
    comp = [g for c in OI['complementaria'].values() for g in c]
    datos = {'salterio': SI, 'tiempo': TI, 'santoral': SaI, 'horas': horas, 'latinos': himnos_latinos('tercia', 'sexta', 'nona'), 'complementaria': OI['complementaria'],
             'salmos': _salmos(_usados([e for w in SI.values() for e in w.values()], TI.values(), SaI.values(), [{'salmodia': comp}]) | salmos_comunes('intermedia')),
             'mapa': mapa, 'adf': adf_y_comunes('intermedia', todos)[0], 'dos': dos_comunes(), 'comunes': adf_y_comunes('intermedia', todos)[1],
             'gregoriano': {'benedicamus': pares(GH['benedicamus']['traduccion'])}, 'mayores': mayores_sin_intermedia(mapa)}
    _escribir_carga('intermedia', 'INTERMEDIA', datos, mapa, sin)


def mayores_sin_intermedia(mapa_inter):
    """Celebraciones que en algún calendario son fiesta o solemnidad, con propio en el santoral de Laudes pero no en el de
    la Hora intermedia (p. ej. san Martín, solemnidad en Buenos Aires): su común (texto del santoral) y su oración."""
    SaL = leer(os.path.join(B, 'santoral', 'laudes.yaml'))
    mapaL, _ = vincular_santoral(SaL)
    cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
    cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
    tab, ix = cal['tabla'], {c: i for i, c in enumerate(cal['campos'])}
    filas = list(cal['dias']) + [v[2] for vs in cal['var'].values() for v in vs]
    out = {}
    for r in filas:
        n, g = tab[r[ix['n']]], tab[r[ix['g']]]
        if not re.match(r'(Fiesta|Solemnidad)', g) or n in mapa_inter or n not in mapaL: continue
        e = SaL[mapaL[n]]
        if e.get('comun') or e.get('oracion'): out[n] = {'comun': e.get('comun', ''), 'oracion': e.get('oracion', '')}
    return out


# ---------- Imágenes de la tarjeta del inicio (base/ilustraciones.yaml → src/datos/ilustraciones.js) ----------
COMUN_TEXTO = [('religios', 'religiosos'), ('educador', 'educadores'), ('misericordia', 'caridad'), ('virgen maría', 'virgen-maria'),
               ('dedicación', 'dedicacion'), ('apóstoles', 'apostoles'), ('para un mártir', 'un-martir'), ('varios mártires', 'varios-martires'),
               ('un márt', 'un-martir'), ('pastores', 'pastores'), ('doctores', 'doctores'), ('vírgenes', 'virgenes'),
               ('santas mujeres', 'santas-mujeres'), ('santos varones', 'santos-varones')]


def comun_de_texto(t):
    """«Del Común de pastores: para un santo obispo…» → «pastores» (el primero que nombra, salvo las variantes de santos varones)."""
    t = (t or '').lower()
    return next((k for p, k in COMUN_TEXTO if p in t), None)


def nombres_calendario():
    cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
    cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
    n = cal['campos'].index('n')
    return {cal['tabla'][r[n]] for r in cal['dias']} | {cal['tabla'][v[2][n]] for vs in cal['var'].values() for v in vs}


def ilustraciones():
    Y = leer(os.path.join(B, 'ilustraciones.yaml'))['imagenes']
    claves = list(Y)
    propias, domingos, comunes, tiempos, genericas = {}, {}, {}, {}, []
    for i, (k, e) in enumerate(Y.items()):
        if e.get('propia'): propias.setdefault(e['propia'], []).append(i)
        elif e.get('comun'): comunes.setdefault(e['comun'], []).append(i)
        elif e.get('tiempo'): tiempos.setdefault(e['tiempo'], []).append(i)
        elif e.get('generica'): genericas.append(i)
        for d in e.get('domingos') or []:
            m = re.fullmatch(r'(.+) \((A|B|C|ABC)\)', d)
            assert m, f'ilustraciones: «{d}» ({k}) no dice el ciclo'
            for c in m[2]: domingos.setdefault(m[1], {}).setdefault(c, []).append(i)
    # Común de cada celebración del calendario: lo escrito en santoral/adf.yaml, o lo que dice el santoral de la base o el libro
    SaL = leer(os.path.join(B, 'santoral', 'laudes.yaml'))
    A = leer(os.path.join(B, 'santoral', 'adf.yaml')) or {}
    LIB = leer(os.path.join(B, 'santoral', 'libro.yaml')) or {}
    mapa, _ = vincular_santoral(SaL)
    comun_de = {}
    for n, k in mapa.items():
        c = comun_de_texto(SaL[k].get('comun'))
        if c: comun_de[n] = c
    for n, l in LIB.items():
        if l.get('comun_libro') and n not in comun_de: comun_de[n] = l['comun_libro']
    for n, a in A.items():
        c = a.get('comun') or (a.get('es') in SaL and comun_de_texto(SaL[a['es']].get('comun'))) or (a.get('como') in SaL and comun_de_texto(SaL[a['como']].get('comun')))
        if c: comun_de[n] = c
    for n in nombres_calendario():   # imagen: las dedicaciones, la de la dedicación de una iglesia (aunque los textos sean de otro
        # común, como las Basílicas de san Pedro y san Pablo, del de apóstoles); Santa María la Mayor conserva la de la Virgen
        if n.startswith('Dedicación') and comun_de.get(n) != 'virgen-maria': comun_de[n] = 'dedicacion'
    datos = {'img': claves, 'd': [Y[k]['descripcion'] for k in claves], 'propias': propias, 'domingos': domingos,
             'comunes': comunes, 'tiempos': tiempos, 'genericas': genericas, 'comunDe': comun_de}
    destino = os.path.join(RAIZ, 'src', 'datos', 'ilustraciones.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.ILUS=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {len(claves)} imágenes · común conocido de {len(comun_de)} celebraciones')


def _escribir_carga(nombre, var, datos, mapa, sin):
    destino = os.path.join(RAIZ, 'src', 'carga', nombre + '.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(f'window.{var}=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


if __name__ == '__main__':
    main()
