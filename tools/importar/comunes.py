"""Comunes de Laudes y Vísperas, deducidos del santoral de la base (que viene de sync).

sync no trae los comunes como tales: cada celebración ya viene armada. Acá, para cada familia de común
(«Del Común de pastores», etc.) y cada parte, queda el texto que más celebraciones comparten (al menos dos).
Es provisorio: sirve para las celebraciones propias de ADF hasta tener sus textos, y hay que cotejarlo con el libro.

  python3 tools/importar/comunes.py     →  base/comunes/laudes.yaml, base/comunes/visperas.yaml
"""
import collections, json, os, re, sys, unicodedata
import yaml
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from yaml_base import escribir
BASE = os.path.abspath(os.path.join(AQUI, '..', '..', 'base'))
FAMILIAS = [('virgen-maria', r'virgen maria'), ('apostoles', r'apostoles'), ('varios-martires', r'varios martires'), ('un-martir', r'un mart'),
            ('doctores', r'doctores'), ('pastores', r'pastores'), ('virgenes', r'virgenes'), ('santos-varones', r'santos varones'),
            ('santas-mujeres', r'santas mujeres'), ('dedicacion', r'dedicacion')]
NOMBRES = {'virgen-maria': 'Común de la Santísima Virgen María', 'apostoles': 'Común de apóstoles', 'varios-martires': 'Común de varios mártires',
           'un-martir': 'Común de un mártir', 'doctores': 'Común de doctores de la Iglesia', 'pastores': 'Común de pastores', 'virgenes': 'Común de vírgenes',
           'santos-varones': 'Común de santos varones', 'santas-mujeres': 'Común de santas mujeres', 'dedicacion': 'Común de la dedicación de una iglesia'}


def plano(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def familias(comun):
    """Un «Del Común de pastores… y del Común de doctores» pertenece a las dos; la primera manda."""
    c = plano(comun or '')
    return [f for f, pat in sorted(FAMILIAS, key=lambda x: c.find(x[1]) if x[1] in c else 9999) if re.search(pat, c)]


def deducir(hora):
    Sa = yaml.safe_load(open(os.path.join(BASE, 'santoral', hora + '.yaml'), encoding='utf-8'))
    ce = 'ant_benedictus' if hora == 'laudes' else 'ant_magnificat'
    votos = collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); n = collections.Counter()
    for nombre, e in Sa.items():
        fs = familias(e.get('comun'))
        if not fs: continue
        f = fs[0]; n[f] += 1
        for k in ('himno', 'lectura', 'responsorio', ce, 'preces', 'padrenuestro_intro', 'salmodia'):
            if e.get(k) is not None: votos[f][k][json.dumps(e[k], ensure_ascii=False, sort_keys=True)] += 1
    out = {}
    for f, _ in FAMILIAS:
        e = {'nombre': NOMBRES[f], 'celebraciones': n[f]}
        for k, c in votos[f].items():
            v, veces = c.most_common(1)[0]
            if veces >= 2: e[k] = json.loads(v)
        if len(e) > 2: out[f] = e
    return out


if __name__ == '__main__':
    for hora in ('laudes', 'visperas'):
        C = deducir(hora)
        escribir(os.path.join(BASE, 'comunes', hora + '.yaml'), C,
                 f'Comunes de {hora.capitalize()}, deducidos del santoral (tools/importar/comunes.py): de cada parte, el texto que más celebraciones\n'
                 'de ese común comparten. PROVISORIO, a cotejar con el libro. Se usan para las celebraciones propias de ADF sin textos propios\n'
                 '(base/santoral/adf.yaml).')
        print(hora, {f: [k for k in e if k not in ('nombre', 'celebraciones')] for f, e in C.items()})
