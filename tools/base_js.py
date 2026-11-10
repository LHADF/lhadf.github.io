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
    base = {
        'completas': {
            'ordinario': leer(os.path.join(B, 'ordinario', 'completas.yaml')),
            'salterio': leer(os.path.join(B, 'salterio', 'completas.yaml')),
            'tiempo': leer(os.path.join(B, 'tiempo', 'completas-triduo-octava.yaml')),
            'himnos': leer(os.path.join(B, 'himnos', 'completas.yaml')),
            'gregoriano': {
                'invocacion': {'solemne': gabc(inv['solemne']), 'festivo': gabc(inv['festivo']), 'ferial': gabc(inv['ferial']), 'traduccion': pares(inv['traduccion']), 'laus': pares(inv['laus'])},
                'antifona': {'gabc': gabc(ce['antifona']), 'repeticion': repeticion(gabc(ce['antifona'])), 'traduccion': pares(ce['traduccion_antifona'])},
                'cantico': {'gabc': primer_verso(gabc(ce['cantico'])), 'traduccion': pares(ce['traduccion_cantico']),
                            'tono': str(ce['tono_cantico']), 'versos': ce['versos'], 'traduccion_versos': [pares(v) for v in ce['traduccion_versos']],
                            'primer_verso': ce['primer_verso']},
                'himno': {'titulo': G['himno']['titulo'], 'gabc': gabc(G['himno']['partitura']), 'traduccion': pares(G['himno']['traduccion'])},
                'lectura_respuesta': pares(G['lectura_respuesta']),
                'responsorio': {k: {'gabc': gabc(v['partitura']), 'traduccion': pares(v['traduccion'])} for k, v in G['responsorio'].items()},
                'marianas': {k: {'titulo': v['titulo'], 'gabc': gabc(v['partitura']), 'traduccion': pares(v['traduccion'])} for k, v in G['marianas'].items()},
                'conclusion': {'gabc': gabc(co['partitura']), 'traduccion': pares(co['traduccion'])},
                'tonos': G['tonos_salmos'],
            },
        },
        'marianas': leer(os.path.join(B, 'ordinario', 'antifonas-marianas.yaml')),
        'salmos': {os.path.basename(f)[:-5]: leer(f) for f in sorted(glob.glob(os.path.join(B, 'salmos', '*.yaml')))},
    }
    destino = os.path.join(RAIZ, 'src', 'datos', 'base.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.BASE=' + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB')


if __name__ == '__main__':
    main()
