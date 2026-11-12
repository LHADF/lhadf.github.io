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


def repeticion(g):
    """Antífona repetida al final: la canta toda la asamblea (en negrita) y va sin asterisco."""
    return negrita(re.sub(r'\s*\*+\s*\(([,;:]*)\)', lambda m: f' ({m.group(1)})' if m.group(1) else '', g))


def primer_verso(g):
    """Solo el primer versículo (hasta la primera doble barra), para cánticos que siguen pautados."""
    cab, _, cuerpo = g.partition('%%')
    i = cuerpo.index('(::)') + 4
    return cab + '%%' + cuerpo[:i] + '\n'


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
            'gregoriano': {
                'invocacion': {'solemne': gabc(inv['solemne']), 'festivo': gabc(inv['festivo']), 'ferial': gabc(inv['ferial']), 'cortes_gloria': inv['cortes_gloria'], 'traduccion': pares(inv['traduccion']), 'laus': pares(inv['laus'])},
                'antifona': {'gabc': gabc(ce['antifona']), 'repeticion': repeticion(gabc(ce['antifona'])), 'traduccion': pares(ce['traduccion_antifona'])},
                'cantico': {'gabc': primer_verso(gabc(ce['cantico'])), 'traduccion': pares(ce['traduccion_cantico']),
                            'tono': str(ce['tono_cantico']), 'versos': ce['versos'], 'traduccion_versos': [pares(v) for v in ce['traduccion_versos']],
                            'primer_verso': ce['primer_verso']},
                'himno': {'titulo': G['himno']['titulo'], 'gabc': gabc(G['himno']['partitura']), 'traduccion': pares(G['himno']['traduccion'])},
                'lectura_respuesta': pares(G['lectura_respuesta']),
                'responsorio': {k: {'gabc': gabc(v['partitura']), 'traduccion': pares(v['traduccion'])} for k, v in G['responsorio'].items()},
                'marianas': {k: {'titulo': v['titulo'], 'gabc': gabc(v['partitura']), 'cortes': v.get('cortes'), 'traduccion': pares(v['traduccion'])} for k, v in G['marianas'].items()},
                'conclusion': {'gabc': gabc(co['partitura']), 'traduccion': pares(co['traduccion'])},
                'tonos': G['tonos_salmos'],
            },
        },
        'marianas': leer(os.path.join(B, 'ordinario', 'antifonas-marianas.yaml')),
        'oraciones': oraciones_oficio(),
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
        'salterio': SL, 'tiempo': TL, 'santoral': SaL, 'himnos': HL, 'ordinario': OL, 'salmos': salmos,
        'mapa': mapa, 'sin_vincular': sin, 'adf': adf_y_comunes('laudes', SaL)[0], 'comunes': adf_y_comunes('laudes', SaL)[1],
        'gregoriano': {
            'invitatorio': {'gabc': gabc(GL['invitatorio']['partitura']), 'traduccion': pares(GL['invitatorio']['traduccion'])},
            'invitatorio_to': invitatorio_gregoriano(GL['invitatorio_per_annum']),
            'cantico': {'titulo': bn['titulo'], 'ref': bn['ref'], 'versos': bn['versos'], 'traduccion_versos': [pares(v) for v in bn['traduccion_versos']]},
            **comunes_latin(GL),
            'conclusion': {'gabc': gabc(GL['conclusion']['partitura']), 'traduccion': pares(GL['conclusion']['traduccion'])},
        },
    }
    destino = os.path.join(RAIZ, 'src', 'carga', 'laudes.js')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.LAUDES=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


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
    return out, C


def salmos_comunes(hora):
    """Salmos de los comunes y del propio del libro (base/santoral/libro.yaml) de esta hora."""
    C = leer(os.path.join(B, 'comunes', hora + '.yaml')) or {}
    LIB = leer(os.path.join(B, 'santoral', 'libro.yaml')) or {}
    claves = {'laudes': ['laudes'], 'visperas': ['visperas', 'visperas1'], 'oficio': ['oficio'], 'intermedia': ['tercia', 'sexta', 'nona']}[hora]
    partes = [p for c in C.values() for p in (c, c.get('primeras') or {})] + [e[k] for e in LIB.values() for k in claves if e.get(k)]
    return {g['salmo'] for p in partes for g in (p.get('salmodia') or [])}


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
    datos = {'salterio': SV, 'tiempo': TV, 'santoral': SaV, 'himnos': HV, 'salmos': salmos, 'mapa': mapa, 'sin_vincular': sin, 'adf': adf_y_comunes('visperas', SaV)[0], 'comunes': adf_y_comunes('visperas', SaV)[1],
             'gregoriano': {**comunes_latin(GL),
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
    datos = {'salterio': SO, 'tiempo': TO, 'santoral': SaO, 'himnos': HO, 'ordinario': OO,
             'salmos': _salmos(_usados([e for w in SO.values() for e in w.values()], TO.values(), SaO.values()) | salmos_comunes('oficio')),
             'mapa': mapa, 'adf': adf_y_comunes('oficio', SaO)[0], 'comunes': adf_y_comunes('oficio', SaO)[1],
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
    datos = {'salterio': SI, 'tiempo': TI, 'santoral': SaI, 'horas': horas, 'complementaria': OI['complementaria'],
             'salmos': _salmos(_usados([e for w in SI.values() for e in w.values()], TI.values(), SaI.values(), [{'salmodia': comp}]) | salmos_comunes('intermedia')),
             'mapa': mapa, 'adf': adf_y_comunes('intermedia', todos)[0], 'comunes': adf_y_comunes('intermedia', todos)[1],
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


def _escribir_carga(nombre, var, datos, mapa, sin):
    destino = os.path.join(RAIZ, 'src', 'carga', nombre + '.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(f'window.{var}=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


if __name__ == '__main__':
    main()
