#!/usr/bin/env python3
"""Pasa la base (base/*.yaml y base/gregoriano/*.gabc) a src/datos/base.js para la app.

    python3 tools/base_js.py      (lo llama tools/armar.py)
"""
import glob, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools', 'importar'))
from yaml_base import leer

B = os.path.join(RAIZ, 'base')


def pares(lista):
    return [[x.strip() for x in s.split(' = ', 1)] for s in lista or []]


def gabc(nombre):
    s = open(os.path.join(B, 'gregoriano', nombre), encoding='utf-8').read()
    return s.replace('<v>\\greheightstar</v>', '*')   # asterisco de Gregorio → asterisco común


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
                'invocacion': {'solemne': gabc(inv['solemne']), 'ferial': gabc(inv['ferial']), 'traduccion': pares(inv['traduccion'])},
                'antifona': {'gabc': gabc(ce['antifona']), 'traduccion': pares(ce['traduccion_antifona'])},
                'cantico': {'gabc': gabc(ce['cantico']), 'traduccion': pares(ce['traduccion_cantico'])},
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
