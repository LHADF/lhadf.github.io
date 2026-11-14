"""Empareja las celebraciones del calendario ADF (informes/calendario-adf.json) con el Propio de los santos del libro."""
import difflib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ALIAS = {'agata': 'agueda', 'sancta-maria-in-sabbato': None,
         'nombre-de-la-bienaventurada-virgen-maria': 'nombre-de-maria'}


def st(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', st(s)).strip('-')


def nucleo(s):
    s = st(s.split(',')[0])
    s = re.sub(r'^(la |el |los )?(santisimo |san |santa |santo |santos |santas |beato |beata |beatos |beatas |'
               r'bienaventurada virgen maria |nuestra senora |la bienaventurada virgen maria |nuestro senor )+', '', s)
    s = slug(s)
    for a, b in ALIAS.items():
        if b and s.startswith(a):
            s = b + s[len(a):]
    return s


def dist(f1, f2):
    """Días entre dos «MM-DD» (sin año)."""
    a, b = date(2001, int(f1[:2]), int(f1[3:])), date(2001, int(f2[:2]), int(f2[3:]))
    d = abs((a - b).days)
    return min(d, 365 - d)


def libro():
    d = json.loads((AQUI / 'santoral' / 'santoral.json').read_text(encoding='utf-8'))
    out = []
    for m in d['meses']:
        for c in m['celebraciones']:
            f = f"{c['fecha']['mes']:02d}-{c['fecha']['dia']:02d}" if c.get('fecha') else None
            out.append((c, f, nucleo(c['titulo'])))
    return out


LIBRO = libro()


def buscar(nombre, fechas):
    """(celebración del libro, puntaje) o (None, puntaje)."""
    n = nucleo(nombre)
    if not n:
        return None, 0
    best, pt = None, 0.0
    for c, f, nc in LIBRO:
        r = difflib.SequenceMatcher(None, n, nc, autojunk=False).ratio()
        if nc and (n.startswith(nc + '-') or nc.startswith(n + '-')):
            r = max(r, 0.8)       # «hilario» = «hilario-de-poitiers»
        cerca = f and fechas and min(dist(f, x) for x in fechas) <= 3
        s = r + (0.15 if cerca else 0)
        if (cerca and r >= 0.6 or r >= 0.88) and s > pt:
            best, pt = c, s
    return best, pt
