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
        'salmos': {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in USADOS},
    }
    destino = os.path.join(RAIZ, 'src', 'datos', 'base.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.BASE=' + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB')
    laudes()


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


def vincular_santoral(santoral):
    """Celebraciones del calendario ADF (src/datos/calendario.js) → entrada del santoral de Laudes (de sync).
    Primero por fecha y nombre; las movibles, solo por nombre. Devuelve (mapa, sin_vincular)."""
    cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
    cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
    tab, ix, d0 = cal['tabla'], {c: i for i, c in enumerate(cal['campos'])}, date.fromisoformat(cal['desde'])
    filas = [(d0 + timedelta(days=k), r) for k, r in enumerate(cal['ARG'])] + [(date.fromisoformat(f), r) for f, r in cal['PGY'].items()]
    mapa, sin = {}, {}
    for f, r in filas:
        n, g, fer = tab[r[ix['n']]], tab[r[ix['g']]], tab[r[ix['fer']]]
        if n in mapa or n in sin: continue
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
    usados |= {'salmo-94'}
    salmos = {k: v for k, v in ((os.path.basename(f)[:-5], leer(f)) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))) if k in usados}
    mapa, sin = vincular_santoral(SaL)
    bn = GL['benedictus']
    datos = {
        'salterio': SL, 'tiempo': TL, 'santoral': SaL, 'himnos': HL, 'ordinario': OL, 'salmos': salmos,
        'mapa': mapa, 'sin_vincular': sin,
        'gregoriano': {
            'invitatorio': {'gabc': gabc(GL['invitatorio']['partitura']), 'traduccion': pares(GL['invitatorio']['traduccion'])},
            'benedictus': {'titulo': bn['titulo'], 'ref': bn['ref'], 'versos': bn['versos'], 'traduccion_versos': [pares(v) for v in bn['traduccion_versos']]},
            'pater_noster': pares(GL['pater_noster']), 'pater_cortes': GL['pater_cortes'],
            'bendicion': {'simple': gabc(GL['bendicion']['simple']), 'solemne': gabc(GL['bendicion']['solemne']), 'traduccion': pares(GL['bendicion']['traduccion']), 'despedida': pares(GL['bendicion']['despedida'])},
            'conclusion': {'gabc': gabc(GL['conclusion']['partitura']), 'traduccion': pares(GL['conclusion']['traduccion'])},
        },
    }
    destino = os.path.join(RAIZ, 'src', 'carga', 'laudes.js')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.LAUDES=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB · santoral vinculado: {len(mapa)} · sin propio en la base: {len(sin)}')


if __name__ == '__main__':
    main()
