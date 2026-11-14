"""Ciclo bienal de la primera lectura del Oficio, del libro, a `base/tiempo/oficio.yaml`.

    python3 extraccion/a_base_bienal.py

El libro (Ordinario): «En todos los demás días, se toma del Propio del tiempo: en los años impares, se toma la lectura
del año I; en los años pares, la del año II». El año es el litúrgico, que empieza el I domingo de Adviento (el Adviento
de 2026 es del año 2027: año I). La base de sync trae una sola lectura por día, a veces de un año y a veces del otro.

Para cada día del Propio del tiempo en la base, este script busca el mismo día en el libro, averigua de qué año es la
lectura que ya tiene (`anio: I` o `anio: II`) y agrega la del otro año (`otro_anio: {lectura1, resp1}`). No toca lo que
ya estaba: inserta esas dos claves debajo del nombre del día. La app elige según el año.
"""
import difflib
import re
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import a_base_comunes as AC  # noqa: E402
import comparar_base as cb  # noqa: E402

BASE = AC.BASE
ARCH = BASE / 'tiempo' / 'oficio.yaml'


ALIAS = {'Día V de la Octava de la Natividad': 'dia-v-dentro-de-la-octava-de-navidad',
         'Día VI de la Octava de la Natividad': 'dia-vi-dentro-de-la-octava-de-navidad',
         'Día VII de la Octava de la Natividad': 'dia-vii-dentro-de-la-octava-de-navidad',
         'II Domingo después de Navidad': 'domingo-segundo-despues-de-navidad',
         'Viernes Santo de la Pasión del Señor': 'viernes-santo-de-la-muerte-del-senor'}


def emparejar(k, idx, por_nombre):
    """El día del libro (nodos [celebración, bloque]) para una clave de la base."""
    k0 = re.sub(r'\s*\([ABC]\)\s*$', '', k)
    if k0 in ALIAS:
        return por_nombre.get(ALIAS[k0])
    m = re.fullmatch(r'(\d+) de (diciembre|enero)', k)
    if m:
        dia, mes = int(m.group(1)), m.group(2)
        for nom, x in por_nombre.items():
            c = x[0]
            f = c.get('fecha') or {}
            if f.get('dia') == dia and f.get('mes') == (12 if mes == 'diciembre' else 1) and \
                    (mes == 'diciembre' or 'despues-del-domingo-de-epifania' in nom):
                return x
        return None
    t, dia, sem, ciclo = cb.clave_base_tiempo(k)
    c = idx.get((t, dia, sem)) if (t and dia and sem) else None
    if c is not None:
        return c
    s = cb.slug(re.sub(r'\s*\([ABC]\)\s*$', '', k))
    m = re.match(r'(\d+) de enero', k)
    if m:
        return next((x for nom, x in por_nombre.items() if nom.startswith(f'{m.group(1)}-de-enero')
                     and 'epifania' not in nom), None)
    mejor, pt = None, 0.0
    for nom, x in por_nombre.items():
        d_b = next((d for d in cb.DIAS if d in s.split('-')), None)
        d_l = next((d for d in cb.DIAS if d in nom.split('-')), None)
        if d_b and d_l and d_b != d_l:
            continue
        r = difflib.SequenceMatcher(None, s, nom, autojunk=False).ratio()
        if r > pt:
            mejor, pt = x, r
    return mejor if pt >= 0.85 else None


def por_anio(nodos):
    """{'I': (lectura, responsorio), 'II': (…)} de la primera lectura del libro."""
    out = {}
    for tipo in ('lectura', 'responsorio'):
        for pz, v in cb.piezas(nodos, 'oficio', 'primera_lectura', tipo):
            a = (v.get('cuando') or {}).get('anio')
            if a in ('I', 'II'):
                out.setdefault(a, {}).setdefault(tipo, v)
    return {a: x for a, x in out.items() if 'lectura' in x}


def cita_de(ref):
    m = re.search(r'(\d+\s*,.*)$', ref or '')
    return cb.cita(m.group(1)) if m else ''


def que_anio(b, anios):
    """De qué año es la primera lectura que ya tiene la base."""
    ref, texto = cita_de((b.get('lectura1') or {}).get('ref')), cb.fuerte((b.get('lectura1') or {}).get('texto'))[:400]
    mejor, pt = None, 0.0
    for a, x in anios.items():
        v = x['lectura']
        if ref and cb.cita(v.get('cita')) == ref:
            return a, 1.0
        r = cb.parecido(texto, cb.fuerte(' '.join(v.get('parrafos') or []))[:400])
        if r > pt:
            mejor, pt = a, r
    return (mejor, pt) if pt >= 0.6 else (None, pt)


def main():
    base = AC.leer(ARCH) or {}
    idx, por_nombre = cb.indice_tiempo()
    nuevos, sin_par, dudosos = {}, [], []
    for k, b in base.items():
        if not isinstance(b, dict) or not b.get('lectura1') or re.search(r'antes del 24', k):
            continue
        nodos = emparejar(k, idx, por_nombre)
        if nodos is None:
            sin_par.append(k)
            continue
        anios = por_anio(nodos)
        if set(anios) != {'I', 'II'}:
            continue
        a, pt = que_anio(b, anios)
        if a is None:
            dudosos.append((k, round(pt, 2)))
            continue
        otro = 'II' if a == 'I' else 'I'
        x = anios[otro]
        o = {'lectura1': AC.lectura_larga(x['lectura'])}
        if x.get('responsorio'):
            o['resp1'] = AC.responsorio(x['responsorio'])
        nuevos[k] = AC.aleluia({'anio': a, 'otro_anio': o})
    # insertar debajo de cada clave (sin reescribir el archivo); antes, se borra lo que haya insertado una corrida anterior
    import yaml
    texto = ARCH.read_text(encoding='utf-8')
    texto = re.sub(r'\n  anio: (?:I|II)\n  otro_anio:\n(?:(?:    .*|)\n)*?(?=  \S|\S)', '\n', texto)
    lineas = texto.split('\n')
    res = []
    for l in lineas:
        res.append(l)
        if l and not l.startswith((' ', '#', '-')) and l.endswith(':'):
            k = yaml.safe_load(l)
            k = list(k)[0] if isinstance(k, dict) else None
            if k in nuevos:
                tmp = Path(tempfile.mkdtemp()) / 'b.yaml'
                AC.escribir(tmp, nuevos[k], '')
                res += ['  ' + x if x else x for x in tmp.read_text(encoding='utf-8').rstrip('\n').split('\n')]
    ARCH.write_text('\n'.join(res), encoding='utf-8')
    c = {'I': sum(1 for v in nuevos.values() if v['anio'] == 'I'), 'II': sum(1 for v in nuevos.values() if v['anio'] == 'II')}
    print(f'días con los dos años: {len(nuevos)} (la base tenía el año I en {c["I"]}, el II en {c["II"]})')
    print(f'sin par en el libro: {len(sin_par)}; no se pudo saber el año: {len(dudosos)}')
    for k, pt in dudosos[:40]:
        print('  dudoso:', k, pt)
    for k in sin_par[:40]:
        print('  sin par:', k)


if __name__ == '__main__':
    main()
