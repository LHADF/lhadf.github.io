"""Las ferias de fecha fija del Propio del tiempo, de la extracción del libro, a `base/tiempo/`.

    python3 extraccion/a_base_fechas.py

Del 7 al 12 de enero: ADF celebra la Epifanía el 6 de enero, así que las ferias que siguen van por fecha («7 de enero o
lunes después del domingo de Epifanía» → «7 de enero»). La base de sync las tiene con el nombre del día de la semana,
corridas (su «Jueves después de la Epifanía» es el 7 de enero del libro): la entrada por fecha manda.

Ferias del 17 al 24 de diciembre:

La base de sync junta esos ocho días en una sola «Feria privilegiada de Adviento» (con los textos de uno u otro día).
Este script agrega, sin tocar lo que ya estaba, una entrada por fecha («17 de diciembre», …, «24 de diciembre») en
`tiempo/{oficio,laudes,tercia,sexta,nona,visperas}.yaml`, con lo propio de cada día (lecturas, responsorios, antífonas
del cántico evangélico —las antífonas «O»—, preces y oración), y las antífonas de los salmos de Laudes y Vísperas
según el día de la semana («Lunes antes del 24 de diciembre», …), que el libro pone en la feria del Salterio. Lo común
del tramo (himnos, invitatorio, antífonas de la Hora intermedia) sigue saliendo de «Feria privilegiada de Adviento».

Primera lectura del Oficio: el libro da dos años; acá va la del año II y `a_base_bienal.py` (que se corre después) agrega la del año I.
"""
import json
import re
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import a_base_comunes as AC  # noqa: E402

BASE = AC.BASE
ANIO = 'II'
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
NOMBRE_DIA = {'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles', 'jueves': 'Jueves',
              'viernes': 'Viernes', 'sabado': 'Sábado'}


def de_anio(H):
    """En la primera lectura del Oficio, deja solo la serie elegida."""
    out = []
    for p in H or []:
        if p['parte'] == 'primera_lectura':
            def serie(vs):
                if any((v.get('cuando') or {}).get('anio') == ANIO for v in vs):    # (a veces el año I va sin etiqueta)
                    return [v for v in vs if (v.get('cuando') or {}).get('anio') == ANIO]
                return vs
            p = {**p, 'piezas': [{**pz, 'variantes': serie(pz['variantes'])} for pz in p['piezas']]}
            for pz in p['piezas']:
                for v in pz['variantes']:
                    v.pop('cuando', None)
        out.append(p)
    return out


def oracion(c):
    o = AC.oraciones(c['horas'].get('laudes'))
    return o[0]['texto'] if o else None


def dia(c):
    H = c['horas']
    ora = oracion(c)
    out = {}
    if H.get('oficio'):
        d = AC.hora_comun(de_anio(H['oficio']), f"{c['id']}/oficio", {}, es_oficio=True)
        out['oficio'] = d
    if H.get('laudes'):
        out['laudes'] = AC.hora_comun(H['laudes'], f"{c['id']}/laudes", {})
        ants = [AC.principal(pz['variantes'])[0] for pz in AC.piezas(H['laudes'], 'salmodia', 'antifona')]
        if ants and not out['laudes'].get('salmodia'):     # 24 de diciembre: antífonas propias, salmos del día
            out['laudes']['antifonas'] = [a['texto'] for a in ants if a]
    if H.get('visperas'):
        out['visperas'] = AC.hora_comun(H['visperas'], f"{c['id']}/visperas", {}, es_visperas=True)
    inv = next(AC.piezas(H.get('invitatorio'), 'antifona', 'antifona'), None)
    if inv and out.get('laudes') is not None:
        p, _, _ = AC.principal(inv['variantes'])
        if p:
            out['laudes']['inv_ant'] = p['texto']
    for h, d in AC.intermedia(c, {}).items():
        out[h] = d
    for d in out.values():
        d.pop('oraciones', None)
        if ora:
            d['oracion'] = ora
    return out


def antifonas_semana():
    """«Lunes antes del 24 de diciembre:» … en la feria del Salterio → {(hora, día): [ant1, ant2, ant3]}."""
    d = json.loads((AQUI / 'salterio' / 'salterio.json').read_text(encoding='utf-8'))
    out = {}
    for s in d['semanas']:
        for x in s['dias']:
            for h in ('laudes', 'visperas'):
                for p in x['horas'].get(h) or []:
                    if p['parte'] != 'salmodia':
                        continue
                    for pz in p['piezas']:
                        for v in pz['variantes']:
                            m = re.match(r'(\w+) antes del 24 de diciembre', AC.sin_tildes(v.get('etiqueta') or '').lower())
                            if m and pz['tipo'] == 'antifona':
                                lista = out.setdefault((h, m.group(1)), {})
                                lista.setdefault(v.get('numero') or len(lista) + 1, v['texto'])
    return {k: [v[n] for n in sorted(v)] for k, v in out.items()}


def agregar(hora, entradas, titulo):
    """Agrega entradas al final de base/tiempo/HORA.yaml (las que ya existen, se reemplazan)."""
    p = BASE / 'tiempo' / f'{hora}.yaml'
    texto = p.read_text(encoding='utf-8')
    marca = f'\n# ── {titulo} '
    viejo = '\n# ── Ferias del 17 al 24 de diciembre, del libro '
    for m in (marca, viejo):
        if m in texto:      # se vuelve a correr: se reemplaza el bloque agregado antes
            texto = texto[:texto.index(m)]
    tmp = Path(tempfile.mkdtemp()) / 't.yaml'
    AC.escribir(tmp, AC.aleluia(entradas), '')
    p.write_text(texto.rstrip('\n') + '\n' + marca.lstrip('\n') + '(extraccion/a_base_fechas.py) ──\n'
                 + tmp.read_text(encoding='utf-8'), encoding='utf-8')


def main():
    por_hora = {h: {} for h in ('oficio', 'laudes', 'tercia', 'sexta', 'nona', 'visperas')}
    # del 17 al 24 de diciembre
    d = json.loads((AQUI / 'tiempo' / 'adviento' / 'tiempo-adviento.json').read_text(encoding='utf-8'))
    bloque = next(b for b in d['bloques'] if b['titulo'].startswith('II.'))
    for c in bloque['celebraciones']:
        for h, x in dia(c).items():
            if h in por_hora and x:
                por_hora[h][f"{c['fecha']['dia']} de diciembre"] = x
    ants = antifonas_semana()
    for (h, dd), l in sorted(ants.items()):
        por_hora[h][f'{NOMBRE_DIA[dd]} antes del 24 de diciembre'] = {'antifonas': l}
    # del 7 al 12 de enero (después de la Epifanía, el 6)
    d = json.loads((AQUI / 'tiempo' / 'navidad' / 'tiempo-navidad.json').read_text(encoding='utf-8'))
    bloque = next(b for b in d['bloques'] if 'POSTERIORES A LA EPIFAN' in b['titulo'])
    for c in bloque['celebraciones']:
        if not c['id'][:1].isdigit():      # el Bautismo del Señor, que el libro pone en el mismo bloque
            continue
        for h, x in dia(c).items():
            if h in por_hora and x:
                por_hora[h][f"{int(c['id'].split('-')[0])} de enero"] = x
    for h, e in por_hora.items():
        agregar(h, e, 'Ferias de fecha fija (17 al 24 de diciembre, 7 al 12 de enero), del libro')
    AC.guardar_bibliotecas()
    print({h: len(e) for h, e in por_hora.items()})
    for a in AC.AVISOS:
        print('aviso:', a)


if __name__ == '__main__':
    main()
