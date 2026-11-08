#!/usr/bin/env python3
"""Calendario litúrgico ADF precalculado para la app (src/datos/calendario.js).

Usa el motor del Ordo ADF (repositorio lucasfelixjhs/ordo-telegram): precedencias, traslados,
I Vísperas y tiempos. Calcula Argentina (por defecto) y Paraguay; de Paraguay guarda solo los días
que difieren. Cubre desde el año anterior hasta dos años después del actual.

    ORDO=/ruta/a/ordo-telegram python3 tools/calendario.py
"""
import json, os, sys, tomllib
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDO = os.environ.get('ORDO') or next((p for p in (os.path.join(RAIZ, '..', 'ordo-telegram'),
                                                    os.path.join(RAIZ, '..', 'lucasfelixjhs', 'ordo-telegram'))
                                       if os.path.isdir(p)), None)
if not ORDO:
    sys.exit('Falta el Ordo: clonar lucasfelixjhs/ordo-telegram junto a este repositorio o indicar ORDO=/ruta')
sys.path.insert(0, ORDO)
from ordo.calendario import Ordo

REGIONES = {'ARG': 'Argentina', 'PGY': 'Paraguay'}


def motor(region):
    cfg = tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb'))
    cfg.setdefault('calendario', {})['regiones'] = [region]
    return Ordo(ORDO, cfg)


def ficha(dl):
    p = dl.principal
    nombre = p.nombre + (f', {p.titulo}' if p.titulo else '')
    octava = ''
    if p.temporal and p.grado == 'Octava' or dl.tiempo == 'Pascua' and (dl.semana == 1 or dl.semana == 2 and dl.es_domingo):
        octava = 'pascua'
    elif dl.tiempo == 'Navidad' and date(dl.fecha.year, 12, 25) < dl.fecha <= date(dl.fecha.year, 12, 31):
        octava = 'navidad'
    return {
        't': dl.tiempo, 'sem': dl.semana, 'sal': dl.salterio,
        'n': nombre, 'g': p.grado, 'c': p.color,
        'sol': 1 if p.es_solemnidad else 0,
        'dom': 1 if dl.es_domingo else 0,
        'fer': dl.feria.nombre,
        'pv': 1 if dl.primeras_visperas else 0,
        'oct': octava,
    }


def main():
    hoy = date.today()
    ini, fin = date(hoy.year - 1, 1, 1), date(hoy.year + 2, 12, 31)
    M = {r: motor(r) for r in REGIONES}
    dias, pgy = {}, {}
    d = ini
    while d <= fin + timedelta(days=1):
        a = ficha(M['ARG'].dia(d))
        p = ficha(M['PGY'].dia(d))
        k = d.isoformat()
        dias[k] = a
        if p != a: pgy[k] = p
        d += timedelta(days=1)
    # tabla de textos repetidos para achicar el archivo
    tabla, idx = [], {}
    def i(s):
        if s not in idx: idx[s] = len(tabla); tabla.append(s)
        return idx[s]
    def comp(f):
        return [i(f['t']), f['sem'] or 0, f['sal'] or 0, i(f['n']), i(f['g']), i(f['c']), f['sol'], f['dom'], i(f['fer']), f['pv'], i(f['oct'])]
    out = {
        'desde': ini.isoformat(), 'hasta': fin.isoformat(),
        'regiones': REGIONES,
        'campos': ['t', 'sem', 'sal', 'n', 'g', 'c', 'sol', 'dom', 'fer', 'pv', 'oct'],
        'tabla': tabla,
        'ARG': [comp(dias[k]) for k in sorted(dias)],
        'PGY': {k: comp(v) for k, v in sorted(pgy.items())},
    }
    destino = os.path.join(RAIZ, 'src', 'datos', 'calendario.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.CAL=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {ini} a {fin}, {len(dias)} días, {len(pgy)} con diferencias en Paraguay, '
          f'{os.path.getsize(destino) // 1024} KB')


if __name__ == '__main__':
    main()
