"""Pasa el Propio de los santos de la extracción del libro a `base/santoral/libro.yaml`.

    node extraccion/calendario_adf.mjs        # (después de tools/armar.py) las celebraciones del calendario
    python3 extraccion/a_base_santoral.py

Reemplaza el `libro.yaml` cargado a mano (tools/importar/propio_libro.py, desde el texto), que arrastraba rúbricas y
fechas pegadas a los textos, por la extracción limpia de los cuatro tomos. Regla: sync manda. Solo entran las
celebraciones del calendario que no tienen propio en la base de sync (las de `santoral/adf.yaml` con `comun` o
`pendiente`); de cada una, lo que el libro trae de propio (lo demás sale del común). Mismo formato que antes:
`nombre_libro`, `comun_libro`, `indicacion`, `oracion` y, por hora, sus campos (`invitatorio`, `oficio`, `laudes`,
`tercia`, `sexta`, `nona`, `visperas`, `visperas1`). Los himnos que la base no tenía se agregan a `base/himnos/`.
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import a_base_comunes as AC  # noqa: E402
from emparejar_santoral import buscar  # noqa: E402

BASE = AC.BASE
COMUN_DE = [(r'dedicaci', 'dedicacion'), (r'virgen mar|santa mar[íi]a virgen', 'virgen-maria'), (r'ap[óo]stol', 'apostoles'),
            (r'varios m[áa]rt', 'varios-martires'), (r'm[áa]rt', 'un-martir'), (r'pastores', 'pastores'),
            (r'doctores', 'doctores'), (r'v[íi]rgenes', 'virgenes'), (r'santos varones', 'santos-varones'),
            (r'santas mujeres', 'santas-mujeres')]


def comun_de(texto):
    t = (texto or '').lower()
    mejor, pos = None, 10 ** 9
    for rx, k in COMUN_DE:
        m = re.search(rx, t)
        if m and m.start() < pos:
            mejor, pos = k, m.start()
    return mejor


def rubricas(c):
    out = [v.get('texto') or '' for r in c.get('rubricas') or [] for v in r.get('variantes') or []]
    for partes in (c.get('horas') or {}).values():
        for p in partes:
            for pz in p['piezas']:
                if pz['tipo'] == 'rubrica':
                    out += [v.get('texto') or '' for v in pz['variantes']]
    return out


def nombre_libro(t):
    t = t.strip()
    pal = t.lower().split()
    menores = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'en', 'el'}
    return ' '.join(w if i and w in menores else w[:1].upper() + w[1:] for i, w in enumerate(pal))


def propio(c):
    H = c.get('horas') or {}
    out = {}
    ora = None
    for h in ('laudes', 'oficio', 'visperas', 'visperas2', 'visperas1'):
        o = AC.oraciones(H.get(h))
        if o:
            ora = o[0]['texto']
            break
    if ora:
        out['oracion'] = ora
    inv = next(AC.piezas(H.get('invitatorio'), 'antifona', 'antifona'), None)
    if inv:
        p, _, _ = AC.principal(inv['variantes'])
        if p:
            out['invitatorio'] = {'inv_ant': p['texto']}
            ps = AC.tp(p)
            if ps:
                out['invitatorio']['pascua'] = {'inv_ant': ps['texto']}
    for h, dest, kw in (('oficio', 'oficio', {'es_oficio': True}), ('laudes', 'laudes', {}),
                        ('visperas2', 'visperas', {'es_visperas': True}), ('visperas', 'visperas', {'es_visperas': True}),
                        ('visperas1', 'visperas1', {'es_visperas': True})):
        if H.get(h) and dest not in out:
            d = AC.hora_comun(H[h], f"{c['id']}/{h}", {}, **kw)
            d.pop('oraciones', None)
            if d:
                out[dest] = d
    I = AC.intermedia(c, {})
    for h, d in I.items():
        out[h] = d
    return out


def main():
    cal = json.loads((AQUI / 'informes' / 'calendario-adf.json').read_text(encoding='utf-8'))
    adf = AC.leer(BASE / 'santoral' / 'adf.yaml') or {}
    antes = AC.leer(BASE / 'santoral' / 'libro.yaml') or {}
    salida, sin_libro = {}, []
    en_cal = {e['n'] for e in cal}
    # las de adf.yaml que el calendario de estos años no muestra (p. ej. memorias que caen siempre en Cuaresma)
    cal = cal + [{'n': n, 'fechas': [], 'mapa': None} for n in adf if n not in en_cal]
    for e in cal:
        n = e['n']
        a = adf.get(n)
        if e['mapa'] or not isinstance(a, dict) or a.get('como') or a.get('es'):
            continue
        c, pt = buscar(n, e['fechas'])
        if c is None:
            sin_libro.append(n)
            continue
        rub = rubricas(c)
        ind = next((r for r in rub if re.search(r'^(del?|todo)\b.*\bcom[uú]n', r, re.I)), '') or \
            next((r for r in rub if re.search(r'com[uú]n', r, re.I)), '')
        ent = {'nombre_libro': nombre_libro(c['titulo']), 'comun_libro': comun_de(ind) or '', 'indicacion': ind}
        ent.update(propio(c))
        salida[n] = AC.aleluia(ent)
    cab = ('Propio de los santos tomado del libro (extracción limpia de los cuatro tomos; extraccion/a_base_santoral.py,\n'
           '11/2026), para las celebraciones del calendario que la base de sync no traía (base/santoral/adf.yaml). Clave: el\n'
           'nombre en el Ordo. «oracion»: la propia; por hora, lo que el libro trae de propio (lo demás sale del común).\n'
           '«comun_libro» e «indicacion»: lo que dice el libro. Desde ahora se corrige acá.')
    AC.escribir(BASE / 'santoral' / 'libro.yaml', salida, cab)
    AC.guardar_bibliotecas()
    print(f'libro.yaml: {len(salida)} celebraciones (antes {len(antes)}); nuevas: {len(set(salida) - set(antes))}; '
          f'se fueron: {sorted(set(antes) - set(salida))}')
    print('sin el libro:', len(sin_libro))
    for a in AC.AVISOS:
        print('aviso:', a)


if __name__ == '__main__':
    main()
