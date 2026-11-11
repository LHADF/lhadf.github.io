#!/usr/bin/env python3
"""Calendario litúrgico ADF precalculado para la app (src/datos/calendario.js).

Usa el motor del Ordo ADF (repositorio lucasfelixjhs/ordo-telegram): precedencias, traslados,
I Vísperas y tiempos. La base es el calendario ADF sin país; de los demás (nacionales del Ordo y
locales de base/calendario/locales.yaml) guarda solo los días que difieren, y las memorias libres
como celebraciones optativas. Cubre desde el año anterior hasta dos años después del actual.

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

import csv, re, yaml
LOC = yaml.safe_load(open(os.path.join(RAIZ, 'base', 'calendario', 'locales.yaml'), encoding='utf-8'))
NACIONALES = ['ARG', 'PGY', 'BRS']                 # los que el Ordo distingue con su columna «regiones»
LOCALES = sorted({c['calendario'] for c in LOC['cambios']})
PREC = {'Solemnidad': 4, 'Fiesta': 8, 'Memoria obligatoria': 11}   # propias, en la Tabla de los días litúrgicos
# calendarios que traen cada celebración del santoral (columna «calendarios» del Ordo)
SIGLAS = {(r['fecha'], r['nombre'].strip()): ', '.join(x.strip() for x in r['calendarios'].split(',') if x.strip())
          for r in csv.DictReader(open(os.path.join(ORDO, 'data', 'santoral.csv'), encoding='utf-8'))}


MOD = set()   # (calendario local, fecha, nombre) de lo que locales.yaml cambió


def motor(cal):
    """Motor del Ordo para un calendario: '' (ADF, sin país), uno nacional o uno local (parte del de su país)."""
    cfg = tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb'))
    pais = LOC['padres'].get(cal, cal)
    cfg.setdefault('calendario', {})['regiones'] = [pais] if pais else []
    o = Ordo(ORDO, cfg)
    for c in LOC['cambios']:
        if c['calendario'] != cal: continue
        fila = next((x for x in o.santoral.get(c['fecha'], []) if x.nombre.startswith(c['celebracion'])), None)
        if not fila: sys.exit(f"locales.yaml: no encuentro «{c['celebracion']}» el {c['fecha']} en el Ordo")
        fila.grado, fila.precedencia, fila.nota = c['grado'], PREC[c['grado']], c.get('nota', fila.nota)
        MOD.add((cal, c['fecha'], fila.nombre))
    return o


def sin_html(s):
    return re.sub(r'<[^>]+>', '', s or '').strip()


def ficha(dl, p=None, libre=False, cal=''):
    p = p or dl.principal
    nombre = p.nombre + (f', {p.titulo}' if p.titulo else '')
    octava = ''
    if p.temporal and p.grado == 'Octava' or dl.tiempo == 'Pascua' and (dl.semana == 1 or dl.semana == 2 and dl.es_domingo):
        octava = 'pascua'
    elif dl.tiempo == 'Navidad' and date(dl.fecha.year, 12, 25) < dl.fecha <= date(dl.fecha.year, 12, 31):
        octava = 'navidad'
    origen = (p.trasladada_de or dl.fecha).strftime('%m-%d')
    return {
        't': dl.tiempo, 'sem': dl.semana, 'sal': dl.salterio,
        'n': nombre, 'g': p.grado, 'c': p.color,
        'sol': 1 if p.es_solemnidad else 0,
        'dom': 1 if dl.es_domingo else 0,
        'fer': dl.feria.nombre,
        'pv': 0 if libre else (1 if dl.primeras_visperas else 0),
        'oct': octava,
        'cal': (cal if (cal, p.clave, p.nombre) in MOD else '') or ('' if p.temporal else SIGLAS.get((p.clave, p.nombre), SIGLAS.get((origen, p.nombre), ''))),
        'nota': sin_html(p.nota),
    }


def main():
    hoy = date.today()
    ini, fin = date(hoy.year - 1, 1, 1), date(hoy.year + 2, 12, 31)
    CALS = [''] + NACIONALES + LOCALES
    M = {c: motor(c) for c in CALS}
    padre = lambda c: LOC['padres'].get(c, '')
    dias, var = {}, {}
    d = ini
    while d <= fin + timedelta(days=1):
        k = d.isoformat()
        D = {c: M[c].dia(d) for c in CALS}
        F = {c: ficha(D[c], cal=c) for c in CALS}
        dias[k] = F['']
        vs = []
        # variantes por calendario: cada uno se anota solo donde difiere del calendario del que parte
        for c in CALS[1:]:
            if F[c] == F[padre(c)]: continue
            igual = next((v for v in vs if v[0] == 'r' and v[2] == F[c]), None)
            if igual: igual[1].append(c)
            else: vs.append(['r', [c], F[c]])
        # memorias libres (optativas) de cualquiera de los calendarios
        vistos = set()
        for c in CALS:
            for m in D[c].libres:
                if m.nombre in vistos: continue
                vistos.add(m.nombre)
                f = ficha(D[c], m, libre=True)
                vs.append(['l', [x.strip() for x in f['cal'].split(',') if x.strip()] or ['CRG'], f])
        if vs: var[k] = vs
        d += timedelta(days=1)
    # tabla de textos repetidos para achicar el archivo
    tabla, idx = [], {}
    def i(s):
        if s not in idx: idx[s] = len(tabla); tabla.append(s)
        return idx[s]
    def comp(f):
        return [i(f['t']), f['sem'] or 0, f['sal'] or 0, i(f['n']), i(f['g']), i(f['c']), f['sol'], f['dom'], i(f['fer']), f['pv'], i(f['oct']), i(f['cal']), i(f['nota'])]
    out = {
        'desde': ini.isoformat(), 'hasta': fin.isoformat(),
        'calendarios': LOC['calendarios'], 'padres': LOC['padres'],
        'campos': ['t', 'sem', 'sal', 'n', 'g', 'c', 'sol', 'dom', 'fer', 'pv', 'oct', 'cal', 'nota'],
        'tabla': tabla,
        'dias': [comp(dias[k]) for k in sorted(dias)],                                   # calendario ADF (sin país)
        'var': {k: [[t, ' '.join(s), comp(f)] for t, s, f in v] for k, v in sorted(var.items())},   # 'r': otro calendario; 'l': memoria libre
    }
    destino = os.path.join(RAIZ, 'src', 'datos', 'calendario.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.CAL=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    nr = sum(1 for v in var.values() if any(x[0] == 'r' for x in v)); nl = sum(1 for v in var.values() if any(x[0] == 'l' for x in v))
    print(f'{os.path.relpath(destino, RAIZ)}: {ini} a {fin}, {len(dias)} días; {nr} con diferencias entre calendarios, {nl} con memorias libres; '
          f'{os.path.getsize(destino) // 1024} KB')


if __name__ == '__main__':
    main()
