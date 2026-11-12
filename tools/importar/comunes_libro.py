"""Comunes y Santa María en sábado desde el libro (Liturgia de las Horas, tomo III, en texto) → base/comunes/.

Reemplaza los comunes provisorios que se habían deducido del santoral de sync. Se corre una sola vez; después
los comunes se corrigen en la base.

    pdftotext -layout LH_completa.pdf lh.txt
    python3 tools/importar/comunes_libro.py lh.txt
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import libro_lh as LB
from yaml_base import leer, escribir

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
B = os.path.join(RAIZ, 'base')
ORDO = os.environ.get('ORDO') or os.path.join(RAIZ, '..', 'lucasfelixjhs', 'ordo-telegram')
sys.path.insert(0, ORDO)
from importar_horas import id_v

# Tomo III (Tiempo Ordinario): renglones del texto de pdftotext -layout del PDF de los cuatro tomos
FAMILIAS = [
    ('dedicacion', 212802, 213784, 'Común de la dedicación de una iglesia'),
    ('virgen-maria', 213784, 214941, 'Común de la Santísima Virgen María'),
    ('santa-maria-sabado', 214941, 215754, 'Memoria de santa María en sábado'),
    ('apostoles', 215754, 216470, 'Común de apóstoles'),
    ('varios-martires', 216473, 217352, 'Común de mártires: para varios mártires'),
    ('un-martir', 217352, 218256, 'Común de mártires: para un mártir'),
    ('pastores', 218256, 219260, 'Común de pastores'),
    ('doctores', 219260, 219636, 'Común de doctores de la Iglesia'),
    ('virgenes', 219636, 220480, 'Común de vírgenes'),
    ('santos-varones', 220480, 221450, 'Común de santos varones'),
    ('santas-mujeres', 221450, 222542, 'Común de santas mujeres'),
]
ALIAS = {'cantico-ap-19-1-7': 'cantico-ap-19-1-2-5-7'}   # «Cf. Ap 19, 1-7»: el cántico de las II Vísperas del domingo
HEREDA = {'doctores': 'pastores'}    # el común de doctores trae solo algunas partes: el resto, del de pastores


def aleluia(x):
    if isinstance(x, str): return re.sub(r'(?i)(alel)uya', lambda m: m.group(1) + ('IA' if m.group(0).isupper() else 'uia'), x)
    if isinstance(x, list): return [aleluia(v) for v in x]
    if isinstance(x, dict): return {k: aleluia(v) for k, v in x.items()}
    return x


def main(txt):
    L = open(txt, encoding='utf-8').read().split('\n')
    SAL = {f[:-5] for f in os.listdir(os.path.join(B, 'salmos'))}
    out = {h: {} for h in ('laudes', 'visperas', 'oficio', 'intermedia')}
    himnos = {h: {} for h in ('laudes', 'visperas', 'oficio')}
    faltan = []
    for fam, a, b, nombre in FAMILIAS:
        H = {}
        for h, blk in LB.partir_horas(LB.limpiar(L, a, b)):
            if h: H[h] = LB.hora(h, blk, id_v)
        for h, d in H.items():
            for g in d.get('salmodia', []):
                g['salmo'] = ALIAS.get(g['salmo'], g['salmo'])
                if g['salmo'] not in SAL: faltan.append(f"{fam} · {h}: {g.get('_h')} → {g['salmo']}")
                g.pop('_h', None)
            for hh, dest in (('laudes', 'laudes'), ('visperas', 'visperas'), ('visperas1', 'visperas'), ('oficio', 'oficio')):
                if h == hh and d.get('himno') and d.get('_himno_texto'): himnos[dest][d['himno']] = d['_himno_texto']
            d.pop('_himno_texto', None)
        lau = dict(H.get('laudes', {}))
        if H.get('invitatorio', {}).get('inv_ant'): lau['inv_ant'] = H['invitatorio']['inv_ant']
        vis = dict(H.get('visperas', {}))
        if H.get('visperas1'): vis['primeras'] = H['visperas1']
        ofi = dict(H.get('oficio', {}))
        inter = {k: H[k] for k in ('tercia', 'sexta', 'nona') if H.get(k)}
        for h, d in (('laudes', lau), ('visperas', vis), ('oficio', ofi), ('intermedia', inter)):
            if d: out[h][fam] = {'nombre': nombre, **d}
    for fam, base in HEREDA.items():
        for h in out:
            if fam in out[h] and base in out[h]:
                m = {**{k: v for k, v in out[h][base].items() if k != 'nombre'}, **out[h][fam]}
                if out[h][base].get('primeras') and out[h][fam].get('primeras'): m['primeras'] = {**out[h][base]['primeras'], **out[h][fam]['primeras']}
                out[h][fam] = m
    cab = ('Comunes de {h}, del libro (Liturgia de las Horas, tomo III; tools/importar/comunes_libro.py).\n'
           'Se usan para las celebraciones sin textos propios en la base (base/santoral/adf.yaml) y para lo que les falte.\n'
           '«oraciones»: las que el libro da «en su defecto», con N. en lugar del nombre; «para» dice a quién corresponde cada una.\n'
           'El común de doctores trae solo algunas partes: el resto se copió del de pastores. Se corrigen acá.')
    out = aleluia(out); himnos = aleluia(himnos)   # ADF: «aleluia», no «aleluya»
    for h, d in out.items():
        escribir(os.path.join(B, 'comunes', f'{h}.yaml'), d, cab.format(h=h))
    # himnos que la base no tenía
    for h, nuevos in himnos.items():
        p = os.path.join(B, 'himnos', f'{h}.yaml'); H = leer(p)
        add = {k: v for k, v in nuevos.items() if k not in H}
        if add:
            with open(p, 'a', encoding='utf-8') as f:
                import yaml
                f.write(yaml.safe_dump(add, allow_unicode=True, width=10**6, sort_keys=False, default_style=None))
        print(f'himnos/{h}: {len(add)} nuevos', list(add)[:6])
    print({h: {k: sorted(v) for k, v in d.items()} for h, d in out.items()} if '-v' in sys.argv else {h: list(d) for h, d in out.items()})
    print('salmos que no están en la base:', faltan or 'ninguno')


if __name__ == '__main__':
    main(sys.argv[1])
