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
LOCALES = sorted({c['calendario'] for c in LOC['cambios']} - set(NACIONALES))
PREC = {'Solemnidad': 8, 'Fiesta': 13, 'Memoria obligatoria': 16}   # propias, en la escala del Ordo (1 a 18; el domingo del T. O. es 10)
# calendarios que traen cada celebración del santoral (columna «calendarios» del Ordo)
SIGLAS = {(r['fecha'], r['nombre'].strip()): ', '.join(x.strip() for x in r['calendarios'].split(',') if x.strip())
          for r in csv.DictReader(open(os.path.join(ORDO, 'data', 'santoral.csv'), encoding='utf-8'))}


MOD = set()   # (calendario local, fecha, nombre) de lo que locales.yaml cambió
SIG_TODOS = {}   # (fecha, nombre) → siglas, de lo que locales.yaml cambió para todos los calendarios ('*')


def motor(cal):
    """Motor del Ordo para un calendario: '' (ADF, sin país), uno nacional o uno local (parte del de su país)."""
    cfg = tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb'))
    pais = LOC['padres'].get(cal, cal)
    cfg.setdefault('calendario', {})['regiones'] = [pais] if pais else []
    o = Ordo(ORDO, cfg)
    linaje = [cal] + ([pais] if pais != cal else [])     # un calendario local hereda los cambios de su país
    for c in LOC['cambios']:
        if c['calendario'] != '*' and c['calendario'] not in linaje: continue
        fila = next((x for x in o.santoral.get(c['fecha'], []) if x.nombre.startswith(c['celebracion'])), None)
        if not fila: sys.exit(f"locales.yaml: no encuentro «{c['celebracion']}» el {c['fecha']} en el Ordo")
        fila.grado, fila.precedencia, fila.nota = c['grado'], PREC[c['grado']], c.get('nota', fila.nota)
        if c['calendario'] == '*': SIG_TODOS[(c['fecha'], fila.nombre)] = c.get('siglas', '')
        else: MOD.add((c['calendario'], c['fecha'], fila.nombre))
    return o


# Notas del Calendario litúrgico ADF (base/calendario/notas.yaml): «MM-DD Nombre, título» o «movible Nombre»
NOTAS = yaml.safe_load(open(os.path.join(RAIZ, 'base', 'calendario', 'notas.yaml'), encoding='utf-8')) or {}
NOTA_LOCAL = {(c['calendario'], c['fecha'], c['celebracion']): c['nota'] for c in LOC['cambios'] if c.get('nota')}


def notas_de(p, origen, cal):
    """Notas de una celebración, una por renglón: «SIGLA<tab>texto»."""
    nombre = p.nombre + (f', {p.titulo}' if p.titulo else '')
    ns = NOTAS.get(f'{origen} {nombre}') or NOTAS.get(f'movible {nombre}') or []
    out = [f"{n['calendario']}\t{sin_html(n['texto'])}" for n in ns]
    for (c, f, ini), t in NOTA_LOCAL.items():
        if c == cal and f == origen and p.nombre.startswith(ini) and not any(t in x for x in out): out.insert(0, f'{c}\t{t}')
    return '\n'.join(out)


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
        'cal': next((x for x in (cal, LOC['padres'].get(cal)) if x and (x, p.clave, p.nombre) in MOD), '') or ('' if p.temporal else SIG_TODOS.get((origen, p.nombre)) or SIGLAS.get((p.clave, p.nombre), SIGLAS.get((origen, p.nombre), ''))),
        'bio': (getattr(p, 'biografia', '') or '').strip(),
        'nota': notas_de(p, origen, cal) or (f'CRG\t{sin_html(p.nota)}' if p.nota else ''),
    }


SABADO = 'Sancta María in sábbato'
NOTA_SABADO = ('CRG\tMemoria de Santa María en sábado. En los sábados feriales del Tiempo Ordinario en que no cae una solemnidad, fiesta o '
               'memoria obligatoria, puede celebrarse libremente la memoria de Santa María in sabbato, según una antigua tradición de dedicar el sábado a la Virgen.')
sin_sigla = lambda f: {k: v for k, v in f.items() if k != 'cal'}


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
        # En un día ferial con memorias libres, ADF celebra la memoria libre (no la feria): la del calendario más
        # propio (el local, su país), si no la de ADF, si no la del calendario general.
        def libre_de(c):
            ls = D[c].libres
            if not ls: return None
            sig = lambda m: SIGLAS.get((m.clave, m.nombre), '')
            for x in [c, LOC['padres'].get(c, ''), 'ADF', 'CRG']:
                m = next((m for m in ls if x and x in sig(m).replace(' ', '').split(',')), None)
                if m: return m
            return ls[0]
        F = {c: ficha(D[c], libre_de(c), cal=c) for c in CALS}
        dias[k] = F['']
        vs = []
        # variantes por calendario: cada uno se anota solo donde difiere del calendario del que parte
        for c in CALS[1:]:
            if sin_sigla(F[c]) == sin_sigla(F[padre(c)]): continue   # solo cambia la sigla: no es una variante
            igual = next((v for v in vs if v[0] == 'r' and v[2] == F[c]), None)
            if igual: igual[1].append(c)
            else: vs.append(['r', [c], F[c]])
        # memorias libres (optativas) de cualquiera de los calendarios
        vistos = {F[''].get('n')} | {v[2]['n'] for v in vs}
        for c in CALS:
            for m in D[c].libres:
                f = ficha(D[c], m, libre=True)
                if f['n'] in vistos: continue
                vistos.add(f['n'])
                vs.append(['l', [x.strip() for x in f['cal'].split(',') if x.strip()] or ['CRG'], f])
        # Día con memoria libre: también se puede celebrar la feria (opción «Feria»)
        if any(F[c]['g'] == 'Memoria libre' for c in CALS):
            fe = ficha(D[''], D[''].principal, libre=True)
            if fe['g'] == 'Feria' and fe['n'] not in vistos:
                vistos.add(fe['n']); vs.append(['l', ['Feria'], dict(fe, cal='')])
        # Sábado del Tiempo Ordinario sin memoria (o con una memoria libre): se puede celebrar Sancta María in sábbato (memoria libre, optativa)
        if d.weekday() == 5 and F['']['t'] == 'Ordinario' and F['']['g'] in ('Feria', 'Memoria libre'):
            vs.append(['l', ['CRG'], dict(F[''], n=SABADO, g='Memoria libre', c='Blanco', cal='CRG', nota=NOTA_SABADO, bio='', pv=0)])
        if vs: var[k] = vs
        d += timedelta(days=1)
    # tabla de textos repetidos para achicar el archivo
    tabla, idx = [], {}
    def i(s):
        if s not in idx: idx[s] = len(tabla); tabla.append(s)
        return idx[s]
    def comp(f):
        return [i(f['t']), f['sem'] or 0, f['sal'] or 0, i(f['n']), i(f['g']), i(f['c']), f['sol'], f['dom'], i(f['fer']), f['pv'], i(f['oct']), i(f['cal']), i(f['nota']), i(f['bio'])]
    out = {
        'desde': ini.isoformat(), 'hasta': fin.isoformat(),
        'calendarios': LOC['calendarios'], 'padres': LOC['padres'],
        'campos': ['t', 'sem', 'sal', 'n', 'g', 'c', 'sol', 'dom', 'fer', 'pv', 'oct', 'cal', 'nota', 'bio'],
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
