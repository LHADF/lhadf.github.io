"""Completa el Propio del tiempo de la base con lo que le falta, del libro (sync manda: nunca reemplaza).

    node extraccion/fer_adf.mjs            # (después de tools/armar.py) las ferias del Ordo
    python3 extraccion/a_base_completar.py

Para cada feria del Ordo (los domingos y días del Propio del tiempo que la app busca en `base/tiempo/`), mira qué
tiene la base —la entrada del día y, en los domingos, la de cada ciclo («(A)», «(B)», «(C)»)— y agrega del libro lo
que falta en alguno de los ciclos que se rezan:

- Oficio: primera lectura y responsorio (con los dos años del ciclo bienal), segunda lectura y responsorio, oración.
- Laudes y Vísperas: antífona del cántico evangélico (en los domingos, la de cada ciclo) y oración.

Lo que vale para todos los ciclos va en la entrada del día; lo que cambia con el ciclo, en la del ciclo. Inserta las
claves que faltan sin reescribir el archivo, y deja una lista de lo agregado en informes/completar-tiempo.csv.
"""
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import a_base_comunes as AC  # noqa: E402
import comparar_base as cb  # noqa: E402
from a_base_bienal import emparejar  # noqa: E402

BASE = AC.BASE
CAMPOS = {'oficio': ['lectura1', 'resp1', 'lectura2', 'resp2', 'oracion'],
          'laudes': ['ant_benedictus', 'oracion'],
          'visperas': ['ant_magnificat', 'oracion']}


def de_libro(nodos, hora):
    """{campo: {ciclo o None: valor}} de lo que el libro trae para ese día y esa hora."""
    hs = cb.horas_de(nodos)
    h = hora if hora in hs else ('visperas2' if hora == 'visperas' and 'visperas2' in hs else None)
    if h is None:
        return {}
    out = {}

    def poner(campo, v, valor):
        c = (v.get('cuando') or {}).get('ciclo_dominical')
        out.setdefault(campo, {}).setdefault(c, valor)

    if hora == 'oficio':
        anios = {}
        for tipo in ('lectura', 'responsorio'):
            for pz, v in cb.piezas(nodos, h, 'primera_lectura', tipo):
                anios.setdefault((v.get('cuando') or {}).get('anio'), {}).setdefault(tipo, v)
        prin = anios.get('II') or anios.get(None) or anios.get('I')
        if prin and prin.get('lectura'):
            out['lectura1'] = {None: AC.lectura_larga(prin['lectura'])}
            if prin.get('responsorio'):
                out['resp1'] = {None: AC.responsorio(prin['responsorio'])}
            if anios.get('II') and anios.get('I', {}).get('lectura'):
                o = {'lectura1': AC.lectura_larga(anios['I']['lectura'])}
                if anios['I'].get('responsorio'):
                    o['resp1'] = AC.responsorio(anios['I']['responsorio'])
                out['_bienal'] = {None: {'anio': 'II', 'otro_anio': o}}
        for pz, v in cb.piezas(nodos, h, 'segunda_lectura', 'lectura')[:1]:
            out['lectura2'] = {None: AC.lectura_larga(v, True)}
        for pz, v in cb.piezas(nodos, h, 'segunda_lectura', 'responsorio')[:1]:
            out['resp2'] = {None: AC.responsorio(v)}
    else:
        campo = 'ant_benedictus' if hora == 'laudes' else 'ant_magnificat'
        for pz, v in cb.piezas(nodos, h, 'cantico_evangelico', 'antifona'):
            poner(campo, v, v.get('texto'))
    for hh in (h, 'laudes'):
        o = AC.oraciones([p for p in hs.get(hh) or [] if p['parte'] == 'oracion'])
        if o:
            out['oracion'] = {None: o[0]['texto']}
            break
    return out


def insertar(arch, cambios):
    """cambios: {clave: {campo: valor}}. Agrega los campos bajo la clave (o la clave nueva al final), sin reescribir."""
    texto = arch.read_text(encoding='utf-8')
    lineas = texto.split('\n')
    res, hechas = [], set()
    for l in lineas:
        res.append(l)
        if l and not l.startswith((' ', '#', '-')) and l.endswith(':'):
            k = yaml.safe_load(l)
            k = list(k)[0] if isinstance(k, dict) else None
            if k in cambios:
                tmp = Path(tempfile.mkdtemp()) / 'c.yaml'
                AC.escribir(tmp, AC.aleluia(cambios[k]), '')
                res += ['  ' + x if x else x for x in tmp.read_text(encoding='utf-8').rstrip('\n').split('\n')]
                hechas.add(k)
    nuevas = {k: v for k, v in cambios.items() if k not in hechas}
    if nuevas:
        tmp = Path(tempfile.mkdtemp()) / 'n.yaml'
        AC.escribir(tmp, AC.aleluia(nuevas), '')
        res = ('\n'.join(res).rstrip('\n') + '\n# ── Días del Propio del tiempo que la base no tenía, del libro (extraccion/a_base_completar.py) ──\n'
               + tmp.read_text(encoding='utf-8')).split('\n')
    arch.write_text('\n'.join(res), encoding='utf-8')


def main():
    ferias = json.loads((AQUI / 'informes' / 'ferias-adf.json').read_text(encoding='utf-8'))
    idx, por_nombre = cb.indice_tiempo()
    informe = []
    for hora, campos in CAMPOS.items():
        arch = BASE / 'tiempo' / f'{hora}.yaml'
        base = AC.leer(arch) or {}
        cambios = {}
        for e in ferias:
            k = e['fer']
            # (las solemnidades y fiestas que la base tiene en el santoral, como el Bautismo del Señor y Cristo Rey, no)
            if e['t'] in ('Triduo',) or re.search(r'de enero, del Tiempo de Navidad|Octava de la Natividad|^Bautismo del Señor$|^XXXIV Domingo', k):
                continue
            nodos = emparejar(k, idx, por_nombre)
            if nodos is None:
                continue
            lib = de_libro(nodos, hora)
            ciclos = e['ciclos'] if e['dom'] else [None]
            for campo in campos:
                if campo not in lib:
                    continue
                for c in ciclos:
                    tiene = any(campo in (base.get(x) or {}) for x in ([k, f'{k} ({c})'] if c else [k]))
                    if tiene:
                        continue
                    valor = lib[campo].get(c) if c in lib[campo] else lib[campo].get(None)
                    if valor is None:
                        continue
                    destino = k if (c is None or None in lib[campo]) else f'{k} ({c})'
                    if campo in (base.get(destino) or {}) or campo in cambios.get(destino, {}):
                        continue
                    cambios.setdefault(destino, {})[campo] = valor
                    if campo == 'lectura1' and '_bienal' in lib and 'anio' not in (base.get(destino) or {}):
                        cambios[destino].update(lib['_bienal'][None])
                    informe.append({'hora': hora, 'día': destino, 'campo': campo})
        if cambios:
            insertar(arch, cambios)
        print(hora, len(cambios), 'días')
    with open(AQUI / 'informes' / 'completar-tiempo.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['hora', 'día', 'campo'])
        w.writeheader()
        w.writerows(informe)
    print('campos agregados:', len(informe))


if __name__ == '__main__':
    main()
