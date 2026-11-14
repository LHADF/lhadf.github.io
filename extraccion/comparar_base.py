"""Compara los textos de la app (base/, cargados del repositorio sync) con la extracción del libro.

    python3 extraccion/comparar_base.py [--html CARPETA]

Sale en extraccion/informes/: base-vs-libro.md (el informe), textos.csv (una fila por texto
comparado) y faltantes.csv (lo que tiene una fuente y no la otra). Con --html, además la página
para leer. No toca ni base/ ni la app.
"""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
BASE = REPO / 'base'
INFORMES = AQUI / 'informes'

DIAS = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
ROMANOS = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
           'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18,
           'XIX': 19, 'XX': 20, 'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25, 'XXVI': 26,
           'XXVII': 27, 'XXVIII': 28, 'XXIX': 29, 'XXX': 30, 'XXXI': 31, 'XXXII': 32, 'XXXIII': 33,
           'XXXIV': 34}
# los comunes se llaman distinto en la base y en la extracción
COMUNES = {'virgen-maria': 'virgen', 'varios-martires': 'martires-varios', 'un-martir': 'martires-uno',
           'varias-virgenes': 'virgenes-varias', 'una-virgen': 'virgenes-una'}


def sin_tildes(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def norm(s):
    """Normalización suave: comillas, guiones, espacios, puntuación final y la primera letra."""
    if s is None:
        return ''
    s = unicodedata.normalize('NFC', str(s))
    s = re.sub(r'[«»“”"„]', '"', s)
    s = re.sub(r"[’‘`´]", "'", s)
    s = re.sub(r'[—–‐‑-]', '-', s)
    s = re.sub(r'\s+', ' ', s).strip().rstrip('.,;: ')
    return s[:1].lower() + s[1:]


def fuerte(s):
    """Normalización dura: sin tildes, sin puntuación, en minúsculas. Para ver si la diferencia es de forma."""
    return re.sub(r'[^a-z0-9 ]', '', sin_tildes(norm(s)).lower()).strip()


def adf(s):
    """Como fuerte(), pero además con las normas de ADF que la base ya aplicó («aleluia» = «aleluya»)."""
    return re.sub(r'\baleluia\b', 'aleluya', fuerte(s))


def sin_padrenuestro(s):
    """La base no copia el «Padre nuestro.» con que el libro cierra la monición."""
    return re.sub(r'\s*padre nuestro\s*$', '', fuerte(s))


def sin_conclusion(s):
    """La oración sin su conclusión: la base la escribe entera y el libro la abrevia."""
    t = fuerte(s)
    return re.sub(r'\s*(por nuestro senor jesucristo|por cristo nuestro senor|por jesucristo|'
                  r'el que vive y reina|que vive y reina|por el mismo jesucristo)\b.*$', '', t)


def sin_gloria(xs):
    """Los renglones del responsorio breve sin el Gloria ni la repetición que lo sigue."""
    for i, x in enumerate(xs):
        if re.match(r'^gloria al ?padre', fuerte(x)):
            return list(xs[:i])
    return list(xs)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', sin_tildes(str(s)).lower()).strip('-')


def cita(s):
    """Referencia bíblica normalizada: «Jr 30, 21-22» = «Jr 30, 21. 22»."""
    s = sin_tildes(str(s or '')).lower()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', s).split())


def parecido(a, b):
    import difflib
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def yml(ruta):
    p = BASE / ruta
    return yaml.safe_load(p.read_text(encoding='utf-8')) if p.exists() else {}


def js(ruta):
    p = AQUI / ruta
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


# ─────────────────────────── la extracción, indexada ───────────────────────────

def piezas(nodos, hora, parte=None, tipo=None):
    """Variantes de una parte de una hora. «nodos» es una entrada, o varias: la celebración y el
    bloque que la contiene, porque el libro pone en el bloque lo que vale para todos sus días."""
    out = []
    for nodo in (nodos if isinstance(nodos, list) else [nodos]):
        for p in (nodo.get('horas', {}) or {}).get(hora, []):
            if parte is not None and p['parte'] != parte:
                continue
            for pz in p['piezas']:
                if tipo is not None and pz['tipo'] != tipo:
                    continue
                for v in pz['variantes']:
                    out.append((pz, v))
    return out


def horas_de(nodos):
    out = {}
    for nodo in (nodos if isinstance(nodos, list) else [nodos]):
        out.update(nodo.get('horas') or {})
    return out


def texto_de(v, tipo):
    """El texto comparable de una variante, como una lista de renglones."""
    if tipo in ('himno',):
        return ['\n'.join(x['texto'] for x in e) for e in v.get('estrofas') or []]
    if tipo == 'salmo':
        return [v.get('salmo')]
    if tipo in ('antifona', 'oracion', 'rubrica', 'texto'):
        return [v.get('texto')] if v.get('texto') else (v.get('parrafos') or [])
    if tipo == 'lectura_breve':
        return [v.get('cita'), v.get('texto')]
    if tipo == 'lectura':
        return [v.get('cita') or v.get('autor'), *(v.get('parrafos') or [])]
    if tipo == 'responsorio_breve':
        if v.get('secuencia'):
            return [x['texto'] for x in v['secuencia']]
        return [v.get('v1'), v.get('r1'), v.get('v2'), v.get('r2')]
    if tipo == 'versiculo':
        if v.get('secuencia'):
            return [x['texto'] for x in v['secuencia']]
        return [v.get('v'), v.get('r')]
    if tipo == 'responsorio':
        return [*(v.get('r') or []), v.get('v')]
    if tipo == 'preces':
        return [v.get('introduccion'), *[x['texto'] for x in v.get('respuesta') or []],
                *[x['primera'] for x in v.get('intenciones') or []],
                *[x['segunda'] for x in v.get('intenciones') or [] if x['segunda']], v.get('final')]
    return []


def sin_condicion(vs, tiempo=None):
    """Las variantes generales (sin condición) o las de un tiempo litúrgico."""
    out = []
    for pz, v in vs:
        c = v.get('cuando') or {}
        t = c.get('tiempo')
        t = [t] if isinstance(t, str) else (t or [])
        if tiempo is None and not c:
            out.append((pz, v))
        elif tiempo is not None and tiempo in t:
            out.append((pz, v))
    return out or [x for x in vs]


# ─────────────────────────── el informe ───────────────────────────

class Informe:
    def __init__(self):
        self.textos = []       # (ambito, clave, campo, veredicto, base, libro)
        self.faltantes = []    # (ambito, clave, donde, detalle)
        self.resueltas = Counter()   # horas que la base trae resueltas y el libro remite a otra sección

    def comparar(self, ambito, clave, campo, base, libro, modo='lista'):
        """Compara el texto de la base con el del libro y anota el veredicto.

        modo 'lista': las dos son listas que tienen que coincidir en orden (la salmodia, las preces).
        modo 'opciones': el libro da varias opciones y basta que una coincida (oraciones, antífonas,
        versículos: el libro suele traer varias y la base eligió una).
        modo 'cita': una referencia bíblica, donde la puntuación no cuenta.
        """
        b = [x for x in (base if isinstance(base, list) else [base]) if x not in (None, '')]
        l = [x for x in (libro if isinstance(libro, list) else [libro]) if x not in (None, '')]
        if not b and not l:
            return None
        if not b:
            self.textos.append((ambito, clave, campo, 'solo-libro', '', ' ¶ '.join(map(str, l))))
            return 'solo-libro'
        if not l:
            # la base trae el texto resuelto donde el libro remite a otra sección (el Salterio, un Común)
            self.textos.append((ambito, clave, campo, 'resuelve', ' ¶ '.join(map(str, b)), ''))
            return 'resuelve'
        if modo == 'cita':
            v = 'igual' if cita(b[0]) == cita(l[0]) else ('forma' if cita(b[0]).replace(' ', '') ==
                                                          cita(l[0]).replace(' ', '') else 'distinto')
            libro_txt = l[0]
        elif modo == 'opciones':
            bt = ' ¶ '.join(map(str, b))
            v, libro_txt = 'distinto', None
            mejor = 0.0
            for x in l:
                if norm(x) == norm(bt) or norm(x) in [norm(y) for y in b]:
                    v, libro_txt = 'igual', x
                    break
                if fuerte(x) == fuerte(bt) or fuerte(x) in [fuerte(y) for y in b]:
                    v, libro_txt = 'forma', x
                    break
                if adf(x) == adf(bt):
                    v, libro_txt = 'adf', x
                    break
                if sin_padrenuestro(x) == sin_padrenuestro(bt):
                    v, libro_txt = 'cierre', x
                    break
                if len(bt) > 60 and sin_conclusion(x) == sin_conclusion(bt):
                    v, libro_txt = 'conclusion', x
                    break
                r = parecido(fuerte(bt), fuerte(x))
                if r > mejor:
                    mejor, libro_txt = r, x
            if v == 'distinto' and mejor >= 0.9:
                v = 'parecido'        # casi igual: una palabra o dos
            b = [bt]
        else:
            nb, nl = [norm(x) for x in b], [norm(x) for x in l]
            libro_txt = ' ¶ '.join(map(str, l))
            if nb == nl:
                v = 'igual'
            elif [fuerte(x) for x in b] == [fuerte(x) for x in l]:
                v = 'forma'          # tildes, comillas, guiones, mayúsculas, puntuación
            elif [adf(x) for x in b] == [adf(x) for x in l]:
                v = 'adf'            # la base ya escribe «aleluia», como manda ADF
            elif [sin_padrenuestro(x) for x in b] == [sin_padrenuestro(x) for x in l]:
                v = 'cierre'         # la base no copia el «Padre nuestro.» final
            elif [sin_conclusion(x) for x in b] == [sin_conclusion(x) for x in l] and len(fuerte(b[0])) > 60:
                v = 'conclusion'     # la misma oración; la conclusión, escrita entera o abreviada
            elif sorted(nb) == sorted(nl):
                v = 'orden'
            else:
                j_b, j_l = fuerte(' '.join(map(str, b))), fuerte(' '.join(map(str, l)))
                if j_b and j_l and (j_b in j_l or j_l in j_b):
                    v = 'recorte'    # el mismo texto, cortado distinto
                elif parecido(j_b, j_l) >= 0.9:
                    v = 'parecido'
                else:
                    v = 'distinto'
        if v != 'igual':
            self.textos.append((ambito, clave, campo, v, ' ¶ '.join(map(str, b)), str(libro_txt or '')))
        else:
            self.textos.append((ambito, clave, campo, v, '', ''))
        return v

    def cuenta(self, ambito=None):
        c = Counter(t[3] for t in self.textos if ambito is None or t[0] == ambito)
        return c


INF = Informe()


# ─────────────────────────── 1. salmos y cánticos ───────────────────────────

def salmos_libro():
    """Todos los salmos de la extracción, por identificador (la primera vez que aparece)."""
    out = {}
    for f in sorted(AQUI.glob('**/salmos.json')):
        for s in json.loads(f.read_text(encoding='utf-8')):
            out.setdefault(s['id'], s)
    return out


def estrofas_salmo(s):
    return ['\n'.join(v['texto'] for v in e) for p in s['partes'] for e in p['estrofas']]


def comparar_salmos():
    base = {p.stem: yaml.safe_load(p.read_text(encoding='utf-8')) for p in sorted((BASE / 'salmos').glob('*.yaml'))}
    libro = salmos_libro()
    # los que no comparten identificador se emparejan por el texto
    por_texto = defaultdict(list)
    for i, s in libro.items():
        por_texto[fuerte(' '.join(estrofas_salmo(s)))[:400]].append(i)
    alias = {}
    for i, b in base.items():
        if i in libro:
            continue
        k = fuerte(' '.join(b.get('texto') or []))[:400]
        if k and k in por_texto:
            alias[i] = por_texto[k][0]
    for i, b in sorted(base.items()):
        j = i if i in libro else alias.get(i)
        if j is None:
            INF.faltantes.append(('salmos', i, 'solo en la base', (b.get('titulo') or '')[:120]))
            continue
        s = libro[j]
        clave = i if i == j else f'{i} = {j}'
        INF.comparar('salmos', clave, 'texto', b.get('texto') or [], estrofas_salmo(s))
        INF.comparar('salmos', clave, 'subtitulo', b.get('subtitulo'), s.get('titulo'))
    usados = set(base) | {alias[i] for i in alias}
    for j in sorted(set(libro) - usados):
        INF.faltantes.append(('salmos', j, 'solo en el libro', (libro[j].get('cita') or '')[:120]))
    return len(base), len(libro), len(alias)


# ─────────────────────────── 2. himnos ───────────────────────────

def comparar_himnos():
    libro = {}
    for f in sorted(AQUI.glob('**/himnos.json')):
        for h in json.loads(f.read_text(encoding='utf-8')):
            libro.setdefault(h['id'], h)
    base = {}
    for p in sorted((BASE / 'himnos').glob('*.yaml')):
        d = yaml.safe_load(p.read_text(encoding='utf-8')) or {}
        for titulo, estrofas in d.items():
            base.setdefault(slug(titulo), (p.stem, titulo, estrofas))
    for i, (hora, titulo, estrofas) in sorted(base.items()):
        h = libro.get(i)
        if h is None:
            INF.faltantes.append(('himnos', f'{hora}/{titulo}', 'solo en la base', ''))
            continue
        el = ['\n'.join(v['texto'] for v in e) for e in h['estrofas']]
        if h.get('amen') and el:
            el[-1] += ' Amén.'      # el libro lo guarda aparte; la base lo escribe en el último verso
        INF.comparar('himnos', titulo, 'estrofas', list(estrofas), el)
    for i in sorted(set(libro) - set(base)):
        INF.faltantes.append(('himnos', libro[i].get('primer_verso') or i, 'solo en el libro', ''))
    return len(base), len(libro)


# ─────────────────────────── 3. Completas del salterio ───────────────────────────

def comparar_completas():
    base = yml('salterio/completas.yaml')
    ord_b = yml('ordinario/completas.yaml')
    d = js('completas/completas.json')
    if d is None:
        return 0
    form = {e['id']: e for e in d['formularios']}
    # el sábado de la base es «después de las I Vísperas del domingo»
    pares = [('domingo', 'domingo-visperas2'), ('sabado', 'domingo-visperas1')] + \
            [(x, x) for x in ('lunes', 'martes', 'miercoles', 'jueves', 'viernes')]
    for bk, lk in pares:
        b, e = base.get(bk), form.get(lk)
        if b is None or e is None:
            INF.faltantes.append(('completas', bk, 'solo en el libro' if b is None else 'solo en la base', lk))
            continue
        cl = f'completas/{bk}'
        for campo, tiempo in (('salmodia', None), ('salmodia_pascua', 'pascua')):
            if not b.get(campo):
                continue
            ants_b = [x['ant'] for x in b[campo]]
            sal_b = [s for x in b[campo] for s in x['salmos']]
            vs = piezas(e, 'completas', 'salmodia')
            ants_l = [v.get('texto') for pz, v in sin_condicion([x for x in vs if x[0]['tipo'] == 'antifona'], tiempo)]
            sal_l = [v.get('salmo') for pz, v in [x for x in vs if x[0]['tipo'] == 'salmo']]
            INF.comparar('completas', cl, f'{campo}: antífonas', ants_b, ants_l)
            INF.comparar('completas', cl, f'{campo}: salmos', sal_b, sal_l)
        lec = piezas(e, 'completas', 'lectura_breve', 'lectura_breve')
        if b.get('lectura') and lec:
            INF.comparar('completas', cl, 'lectura: cita', b['lectura'].get('ref'), lec[0][1].get('cita'))
            INF.comparar('completas', cl, 'lectura', b['lectura'].get('texto'), lec[0][1].get('texto'))
        ora = [v for pz, v in piezas(e, 'completas', 'oracion', 'oracion')]
        if b.get('oracion'):
            INF.comparar('completas', cl, 'oración', b['oracion'], [v.get('texto') for v in ora])
    # ordinario de Completas: lo que no cambia con el día
    e = form.get('domingo-visperas2')
    if e and ord_b:
        vs = piezas(e, 'completas', 'introduccion', 'versiculo')
        if vs:
            INF.comparar('completas', 'ordinario', 'invocación',
                         [x.get('V') or x.get('R') for x in ord_b.get('invocacion') or []],
                         [vs[0][1].get('v'), vs[0][1].get('r')])
        nunc = piezas(e, 'completas', 'cantico_evangelico', 'antifona')
        if nunc:
            INF.comparar('completas', 'ordinario', 'antífona del Nunc dimittis',
                         ((ord_b.get('cantico_evangelico') or {}).get('antifona') or {}).get('ordinario'),
                         [v.get('texto') for pz, v in sin_condicion(nunc)])
        rb = [v for pz, v in piezas(e, 'completas', 'responsorio_breve', 'responsorio_breve')]
        if rb and isinstance(ord_b.get('responsorio'), dict):
            INF.comparar('completas', 'ordinario', 'responsorio breve',
                         [list(x.values())[0] for x in ord_b['responsorio']['ordinario']],
                         texto_de(rb[0], 'responsorio_breve'))
        ben = [v for pz, v in piezas(e, 'completas', 'bendicion', 'versiculo')]
        if ben and ord_b.get('bendicion'):
            INF.comparar('completas', 'ordinario', 'bendición',
                         [x.get('V') or x.get('R') for x in ord_b['bendicion']],
                         texto_de(ben[0], 'versiculo'))
    return len(pares)


# ─────────────────────────── 4. una hora, campo por campo ───────────────────────────

def ants_y_salmos(e, h, b, ambito, cl, campo='salmodia', tiempo=None):
    vs = piezas(e, h, 'salmodia')
    if not vs:
        vs = piezas(e, h, 'antifona') + piezas(e, h, 'salmo')
    ants = [v.get('texto') for pz, v in sin_condicion([x for x in vs if x[0]['tipo'] == 'antifona'], tiempo)]
    sal = [v.get('salmo') for pz, v in vs if pz['tipo'] == 'salmo']
    INF.comparar(ambito, cl, f'{campo}: antífonas', [x.get('ant') for x in b], ants)
    INF.comparar(ambito, cl, f'{campo}: salmos',
                 [s for x in b for s in ([x['salmo']] if x.get('salmo') else x.get('salmos') or [])], sal)


def vr(xs):
    """Los textos de una lista «- V: … / - R: …» o «[[V, …], [R, …]]» de la base."""
    out = []
    for x in xs or []:
        if isinstance(x, dict):
            out += list(x.values())
        elif isinstance(x, (list, tuple)):
            out.append(x[1] if len(x) > 1 else x[0])
        else:
            out.append(x)
    return out


def mejor_lectura(vs, ref, texto):
    """De las lecturas breves que trae el libro, la que corresponde a la de la base."""
    por_cita = [v for pz, v in vs if cita(v.get('cita')) == cita(ref)]
    if por_cita:
        return por_cita[0]
    mejor, pt = None, -1.0
    for pz, v in vs:
        r = parecido(fuerte(texto or ''), fuerte(v.get('texto') or ''))
        if r > pt:
            mejor, pt = v, r
    return mejor


def comparar_hora(ambito, cl, b, e, h):
    """Compara los campos que la base trae para una hora con las piezas del libro.

    Donde el libro da varias opciones (oraciones, antífonas, versículos, lecturas), basta que la de
    la base sea una de ellas: la base eligió una y la app resuelve el resto.
    """
    if b.get('salmodia'):
        ants_y_salmos(e, h, b['salmodia'], ambito, cl)
    if b.get('salmodia_pascua'):
        ants_y_salmos(e, h, b['salmodia_pascua'], ambito, cl, 'salmodia (Pascua)', 'pascua')
    if b.get('inv_ant'):
        inv = piezas(e, 'invitatorio', None, 'antifona')
        if inv:
            INF.comparar(ambito, cl, 'antífona del invitatorio', b['inv_ant'],
                         [v.get('texto') for pz, v in inv], 'opciones')
    if b.get('himno'):
        him = piezas(e, h, 'himno', 'himno')
        if him:
            INF.comparar(ambito, cl, 'himno (título)', slug(b['himno']),
                         [v.get('himno') for pz, v in him], 'opciones')
    if b.get('lectura'):
        vs = piezas(e, h, None, 'lectura_breve')
        v = mejor_lectura(vs, b['lectura'].get('ref'), b['lectura'].get('texto')) if vs else None
        if v is not None:
            citas = [x.get('cita') for pz, x in vs]
            if cita(b['lectura'].get('ref')) in [cita(x) for x in citas]:
                INF.comparar(ambito, cl, 'lectura: cita', b['lectura'].get('ref'),
                             b['lectura'].get('ref'), 'cita')
            else:
                INF.comparar(ambito, cl, 'lectura: cita', b['lectura'].get('ref'),
                             ' / '.join(str(x) for x in citas if x), 'cita')
            INF.comparar(ambito, cl, 'lectura', b['lectura'].get('texto'),
                         [x.get('texto') for pz, x in vs], 'opciones')
    if b.get('responsorio'):
        rb = piezas(e, h, None, 'responsorio_breve')
        if rb:
            INF.comparar(ambito, cl, 'responsorio breve', ' ¶ '.join(sin_gloria(vr(b['responsorio']))),
                         [' ¶ '.join(str(x) for x in texto_de(v, 'responsorio_breve') if x) for pz, v in rb],
                         'opciones')
    if b.get('versiculo'):
        vv = piezas(e, h, None, 'versiculo')
        if vv:
            INF.comparar(ambito, cl, 'versículo', ' ¶ '.join(vr(b['versiculo'])),
                         [' ¶ '.join(str(x) for x in texto_de(v, 'versiculo') if x) for pz, v in vv], 'opciones')
    for campo, nombre in (('ant_benedictus', 'antífona del Benedictus'), ('ant_magnificat', 'antífona del Magníficat')):
        if b.get(campo):
            ant = piezas(e, h, 'cantico_evangelico', 'antifona')
            if ant:
                INF.comparar(ambito, cl, nombre, b[campo], [v.get('texto') for pz, v in ant], 'opciones')
    if b.get('ant') and not b.get('salmodia'):
        ant = piezas(e, h, None, 'antifona')
        if ant:
            INF.comparar(ambito, cl, 'antífona', b['ant'], [v.get('texto') for pz, v in ant], 'opciones')
    if b.get('preces'):
        pr = [v for pz, v in piezas(e, h, 'preces', 'preces')]
        bp = b['preces']
        if pr:
            v = max(pr, key=lambda x: parecido(fuerte(bp.get('intro') or ''), fuerte(x.get('introduccion') or '')))
            INF.comparar(ambito, cl, 'preces: introducción', bp.get('intro'),
                         [x.get('introduccion') for x in pr], 'opciones')
            INF.comparar(ambito, cl, 'preces: respuesta', bp.get('respuesta'),
                         [t['texto'] for x in pr for t in x.get('respuesta') or []], 'opciones')
            INF.comparar(ambito, cl, 'preces: intenciones',
                         [t for par in bp.get('preces') or [] for t in (par if isinstance(par, list) else [par])],
                         [t for x in v.get('intenciones') or [] for t in (x['primera'], x['segunda']) if t])
    if b.get('padrenuestro_intro'):
        pr = [v for pz, v in piezas(e, h, 'preces', 'preces')]
        if pr:
            INF.comparar(ambito, cl, 'monición del Padre nuestro', b['padrenuestro_intro'],
                         [x.get('final') for x in pr], 'opciones')
    for campo in ('oracion', 'oraciones'):
        if b.get(campo):
            ora = [v.get('texto') for pz, v in piezas(e, h, 'oracion', 'oracion')]
            if ora:
                bo = b[campo] if isinstance(b[campo], list) else [b[campo]]
                bo = [x.get('texto') if isinstance(x, dict) else x for x in bo]
                for k, x in enumerate(bo):
                    INF.comparar(ambito, cl, 'oración' + (f' {k + 1}' if len(bo) > 1 else ''), x, ora, 'opciones')


# ─────────────────────────── 5. salterio ───────────────────────────

HORAS_BASE = [('laudes', {None: 'laudes'}), ('visperas', {'domingo_1': 'visperas1', None: 'visperas'}),
              ('oficio', {None: 'oficio'}), ('tercia', {None: 'tercia'}), ('sexta', {None: 'sexta'}),
              ('nona', {None: 'nona'})]


def hora_de(mapa, clave_dia, e):
    h = mapa.get(clave_dia, mapa.get(None))
    hs = horas_de(e)
    if h in hs:
        return h
    if h == 'visperas':
        for alt in ('visperas2', 'visperas1', 'visperas'):
            if alt in hs:
                return alt
    return h if h in hs else None


def elegir_hora(arch, nodos, clave=''):
    """Qué hora del libro corresponde al archivo de la base (y a su clave, que puede decir I Vísperas)."""
    hs = horas_de(nodos)
    if arch == 'visperas':
        pedida = visperas_de_clave(clave)
        orden = ([pedida] if pedida else []) + ['visperas', 'visperas2', 'visperas1']
        return next((x for x in orden if x in hs), None)
    if arch == 'intermedia':
        return next((x for x in ('intermedia', 'tercia', 'sexta', 'nona') if x in hs), None)
    return arch if arch in hs else None


def comparar_salterio():
    d = js('salterio/salterio.json')
    if d is None:
        return 0
    idx = {}
    for sem in d['semanas']:
        for dia in sem['dias']:
            idx[(sem['numero'], dia['dia'])] = dia
    n = 0
    for arch, mapa in HORAS_BASE:
        base = yml(f'salterio/{arch}.yaml')
        for sem_k, dias in (base or {}).items():
            num = int(re.sub(r'\D', '', sem_k) or 0)
            for dk, b in (dias or {}).items():
                dia = dk.split('_')[0]
                e = idx.get((num, dia))
                cl = f'semana {num}/{dk}/{arch}'
                if e is None:
                    INF.faltantes.append(('salterio', cl, 'solo en la base', ''))
                    continue
                h = hora_de(mapa, dk, e)
                if h is None:
                    INF.resueltas[('salterio', arch)] += 1
                    continue
                n += 1
                comparar_hora('salterio', cl, b, e, h)
    return n


# ─────────────────────────── 6. comunes ───────────────────────────

def comparar_comunes():
    d = js('comunes/comunes.json')
    if d is None:
        return 0
    libro = {c['id']: c for c in d['comunes']}
    vistos, n = set(), 0
    for arch, mapa in HORAS_BASE + [('intermedia', {None: 'intermedia'})]:
        base = yml(f'comunes/{arch}.yaml')
        for k, b in (base or {}).items():
            cid = COMUNES.get(k, k)
            e = libro.get(cid)
            cl = f'{k}/{arch}'
            if e is None:
                INF.faltantes.append(('comunes', cl, 'solo en la base', b.get('nombre') or ''))
                continue
            vistos.add(cid)
            h = elegir_hora(arch, e, k)
            if h is None:
                INF.resueltas[('comunes', arch)] += 1
                continue
            n += 1
            comparar_hora('comunes', cl, b, e, h)
    for cid, c in sorted(libro.items()):
        if cid not in vistos:
            INF.faltantes.append(('comunes', cid, 'solo en el libro', c.get('titulo') or ''))
    return n


# ─────────────────────────── 7. santoral ───────────────────────────

def indice_santoral():
    d = js('santoral/santoral.json')
    if d is None:
        return {}, {}
    por_fecha, por_nombre = defaultdict(list), {}
    for m in d['meses']:
        for c in m['celebraciones']:
            f = c.get('fecha')
            if f:
                por_fecha[(f['mes'], f['dia'])].append(c)
            por_nombre[slug(c['titulo'])] = c
    return por_fecha, por_nombre


def buscar(nombre, fecha, por_fecha, por_nombre):
    """Empareja una celebración de la base con la del libro, por fecha y por nombre."""
    s = slug(nombre)
    if s in por_nombre:
        return por_nombre[s], 'nombre'
    cand = []
    if fecha and re.fullmatch(r'\d{2}-\d{2}', str(fecha)):
        mes, dia = int(fecha[:2]), int(fecha[3:])
        cand = por_fecha.get((mes, dia)) or []
        if len(cand) == 1:
            return cand[0], 'fecha'
    pool = cand or list(por_nombre.values())
    mejor, puntaje = None, 0.0
    import difflib
    for c in pool:
        r = difflib.SequenceMatcher(None, s, slug(c['titulo']), autojunk=False).ratio()
        if r > puntaje:
            mejor, puntaje = c, r
    if puntaje >= 0.72:
        return mejor, f'parecido {puntaje:.2f}'
    return None, None


def comparar_santoral():
    por_fecha, por_nombre = indice_santoral()
    if not por_nombre:
        return 0, 0
    emparejadas, n = {}, 0
    for arch, mapa in HORAS_BASE + [('intermedia', {None: 'intermedia'})]:
        base = yml(f'santoral/{arch}.yaml')
        for nombre, b in (base or {}).items():
            if not isinstance(b, dict):
                continue
            c, como = buscar(nombre, b.get('fecha'), por_fecha, por_nombre)
            cl = f'{nombre}/{arch}'
            if c is None:
                INF.faltantes.append(('santoral', cl, 'no se pudo emparejar', str(b.get('fecha') or '')))
                continue
            emparejadas[nombre] = (c, como)
            h = elegir_hora(arch, c, nombre)
            if h is None:
                INF.resueltas[('santoral', arch)] += 1
                continue
            n += 1
            comparar_hora('santoral', cl, b, c, h)
            if b.get('grado') and c.get('tipo'):
                INF.comparar('santoral', cl, 'grado', b['grado'], c.get('tipo_literal') or c['tipo'])
    # libro.yaml: oración y remisión al común que se habían tomado del libro
    for nombre, b in (yml('santoral/libro.yaml') or {}).items():
        c, como = buscar(b.get('nombre_libro') or nombre, None, por_fecha, por_nombre)
        if c is None:
            INF.faltantes.append(('santoral', f'{nombre}/libro.yaml', 'no se pudo emparejar', ''))
            continue
        cl = f'{nombre}/oración'
        ora = [v.get('texto') for h in c['horas'] for pz, v in piezas(c, h, 'oracion', 'oracion')]
        if b.get('oracion'):
            INF.comparar('santoral', cl, 'oración', b['oracion'], ora)
    pend = [k for k, v in (yml('santoral/adf.yaml') or {}).items() if isinstance(v, dict) and v.get('pendiente')]
    return n, len(pend)


# ─────────────────────────── 8. Propio del tiempo ───────────────────────────

TIEMPOS = {'adviento': 'adviento', 'navidad': 'navidad', 'cuaresma': 'cuaresma',
           'semana santa': 'semana-santa', 'pascua': 'pascua', 'tiempo ordinario': 'ordinario'}


def indice_tiempo():
    """Cada celebración del Propio del tiempo, con el bloque que la contiene (el libro pone ahí lo
    que vale para todos sus días: versículos, lecturas breves, responsorios)."""
    idx, por_nombre = {}, {}
    for arch in sorted((AQUI / 'tiempo').glob('*/tiempo-*.json')):
        t = arch.parent.name
        d = json.loads(arch.read_text(encoding='utf-8'))
        for b in d['bloques']:
            for c in b['celebraciones']:
                nodos = [c, b]
                if c.get('dia') and c.get('semana'):
                    idx[(t, c['dia'], c['semana'])] = nodos
                por_nombre[slug(c['titulo'] or c['id'])] = nodos
    return idx, por_nombre


def visperas_de_clave(k):
    """«… · I Vísperas» → visperas1; «… · II Vísperas» → visperas2."""
    kk = sin_tildes(k).lower()
    if re.search(r'·\s*ii\s+visperas', kk):
        return 'visperas2'
    if re.search(r'·\s*i\s+visperas', kk):
        return 'visperas1'
    return None


def clave_base_tiempo(k):
    """«Lunes de la I semana de Adviento», «I Domingo de Adviento (A)» → (tiempo, día, semana, ciclo)."""
    ciclo = None
    m = re.search(r'\(([ABC])\)\s*$', k)
    if m:
        ciclo, k = m.group(1), k[:m.start()].strip()
    kk = sin_tildes(k).lower()
    t = next((v for nom, v in TIEMPOS.items() if nom in kk), None)
    dia = next((d for d in DIAS if d in kk), None)
    m = re.search(r'\b([ivx]+)\s+(semana|domingo)', kk)
    sem = ROMANOS.get((m.group(1) if m else '').upper())
    return t, dia, sem, ciclo


def comparar_tiempo():
    idx, por_nombre = indice_tiempo()
    if not por_nombre:
        return 0
    import difflib
    n = 0
    for arch, mapa in HORAS_BASE + [('intermedia', {None: 'intermedia'})]:
        base = yml(f'tiempo/{arch}.yaml')
        for k, b in (base or {}).items():
            if not isinstance(b, dict):
                continue
            t, dia, sem, ciclo = clave_base_tiempo(k)
            c = idx.get((t, dia, sem)) if (t and dia and sem) else None
            if c is None:
                s = slug(k)
                mejor, pt = None, 0.0
                for nom, x in por_nombre.items():
                    r = difflib.SequenceMatcher(None, s, nom, autojunk=False).ratio()
                    if r > pt:
                        mejor, pt = x, r
                c = mejor if pt >= 0.78 else None
            cl = f'{k}/{arch}'
            if c is None:
                INF.faltantes.append(('tiempo', cl, 'no se pudo emparejar', ''))
                continue
            h = elegir_hora(arch, c, k)
            if h is None:
                INF.resueltas[('tiempo', arch)] += 1
                continue
            n += 1
            comparar_hora('tiempo', cl, b, c, h)
    return n


# ─────────────────────────── 9. cobertura ───────────────────────────

def cobertura():
    """Qué trae cada fuente, sección por sección."""
    secciones = [
        ('Ordinario', 'ordinario/ordinario.json',
         ['ordinario/laudes.yaml', 'ordinario/oficio.yaml', 'ordinario/intermedia.yaml',
          'ordinario/antifonas-marianas.yaml', 'ordinario/oraciones-oficio.yaml']),
        ('Salterio', 'salterio/salterio.json',
         ['salterio/laudes.yaml', 'salterio/visperas.yaml', 'salterio/oficio.yaml',
          'salterio/tercia.yaml', 'salterio/sexta.yaml', 'salterio/nona.yaml']),
        ('Completas', 'completas/completas.json',
         ['salterio/completas.yaml', 'ordinario/completas.yaml', 'tiempo/completas-triduo-octava.yaml']),
        ('Propio del tiempo', 'tiempo/adviento/tiempo-adviento.json',
         ['tiempo/laudes.yaml', 'tiempo/visperas.yaml', 'tiempo/oficio.yaml', 'tiempo/tercia.yaml',
          'tiempo/sexta.yaml', 'tiempo/nona.yaml', 'tiempo/intermedia.yaml']),
        ('Propio de los santos', 'santoral/santoral.json',
         ['santoral/laudes.yaml', 'santoral/visperas.yaml', 'santoral/oficio.yaml', 'santoral/tercia.yaml',
          'santoral/sexta.yaml', 'santoral/nona.yaml', 'santoral/intermedia.yaml', 'santoral/libro.yaml',
          'santoral/adf.yaml']),
        ('Oficios comunes', 'comunes/comunes.json',
         ['comunes/laudes.yaml', 'comunes/visperas.yaml', 'comunes/oficio.yaml', 'comunes/intermedia.yaml']),
        ('Oficio de difuntos', 'difuntos/difuntos.json', []),
        ('Apéndices', 'apendices/apendices.json', []),
        ('Salmos y cánticos', 'salterio/salmos.json', ['salmos/ (313 archivos)']),
        ('Himnos', 'salterio/himnos.json', ['himnos/ (7 archivos)']),
    ]
    filas = []
    for nombre, arch, archivos in secciones:
        hay = [x for x in archivos if '(' in x or (BASE / x).exists()]
        filas.append((nombre, 'sí' if (AQUI / arch).exists() else 'no',
                      'sí' if hay else 'no', ', '.join(x.replace('.yaml', '') for x in hay)))
    return filas


# ─────────────────────────── el informe ───────────────────────────

GRUPOS = [('igual', 'iguales', ['igual']),
          ('forma', 'solo en la forma', ['forma', 'adf', 'cierre', 'conclusion', 'orden']),
          ('recorte', 'cortado distinto', ['recorte']),
          ('resuelve', 'la base lo resuelve', ['resuelve']),
          ('difieren', 'difieren', ['distinto', 'parecido']),
          ('solo-libro', 'solo en el libro', ['solo-libro'])]
DE_VEREDICTO = {v: g for g, _, vs in GRUPOS for v in vs}
DETALLE_FORMA = [('forma', 'tildes, comillas, guiones, mayúsculas o puntuación'),
                 ('adf', 'normas de ADF que la base ya aplicó («aleluia»)'),
                 ('cierre', 'la base no copia el «Padre nuestro.» final'),
                 ('conclusion', 'la conclusión de la oración, entera o abreviada'),
                 ('orden', 'los mismos textos en otro orden')]
ORDEN = ['salmos', 'himnos', 'completas', 'salterio', 'comunes', 'santoral', 'tiempo']
NOMBRE_AMBITO = {'salmos': 'Salmos y cánticos', 'himnos': 'Himnos', 'completas': 'Completas',
                 'salterio': 'Salterio', 'comunes': 'Oficios comunes', 'santoral': 'Propio de los santos',
                 'tiempo': 'Propio del tiempo'}


def resaltar(a, b):
    """Las dos versiones con las palabras distintas marcadas."""
    import difflib
    pa, pb = a.split(), b.split()
    sm = difflib.SequenceMatcher(None, [fuerte(x) for x in pa], [fuerte(x) for x in pb], autojunk=False)
    ra, rb = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            ra += pa[i1:i2]
            rb += pb[j1:j2]
        else:
            if i2 > i1:
                ra.append('<mark>' + ' '.join(pa[i1:i2]) + '</mark>')
            if j2 > j1:
                rb.append('<mark>' + ' '.join(pb[j1:j2]) + '</mark>')
    return ' '.join(ra), ' '.join(rb)


def escapar(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


def csvs():
    INFORMES.mkdir(exist_ok=True)
    with (INFORMES / 'textos.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ambito', 'clave', 'campo', 'veredicto', 'base', 'libro'])
        for t in INF.textos:
            if t[3] != 'igual':
                w.writerow(t)
    with (INFORMES / 'faltantes.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ambito', 'clave', 'donde', 'detalle'])
        w.writerows(INF.faltantes)


def resumen():
    filas = []
    for a in ORDEN:
        c = Counter(DE_VEREDICTO.get(t[3], t[3]) for t in INF.textos if t[0] == a)
        filas.append([NOMBRE_AMBITO[a], sum(c.values())] + [c[g] for g, _, _ in GRUPOS])
    tot = ['Total'] + [sum(f[i] for f in filas) for i in range(1, 2 + len(GRUPOS))]
    return filas, tot


def difieren(a):
    return [t for t in INF.textos if t[0] == a and t[3] in ('distinto', 'parecido')]


def markdown():
    filas, tot = resumen()
    L = ['# La base de la app frente al libro', '',
         'Comparación automática entre `base/` —los textos que usa la app, cargados una sola vez del '
         'repositorio `sync`— y la extracción del libro impreso (`extraccion/`). La hace '
         '`extraccion/comparar_base.py`; el detalle está en `informes/textos.csv` (una fila por texto que no '
         'coincide) y en `informes/faltantes.csv`.', '',
         'Las dos fuentes no están armadas igual, y eso explica buena parte de las diferencias: `sync` '
         'guarda **cada día ya resuelto** (el salterio y el propio juntos, con una sola opción elegida), '
         'mientras que el libro imprime **solo lo que cambia** y deja varias opciones. Por eso la '
         'comparación separa seis resultados:', '',
         '- **iguales**: el mismo texto.',
         '- **solo en la forma**: tildes, comillas, guiones, mayúsculas, puntuación; las normas de ADF que '
         'la base ya aplicó («aleluia» por «Aleluya»); el «Padre nuestro.» con que el libro cierra la '
         'monición y la base no copia; y la conclusión de las oraciones, que la base escribe entera y el '
         'libro abrevia.',
         '- **cortado distinto**: el mismo texto repartido en otras estrofas o partes (el libro parte '
         'varios salmos en I, II y III).',
         '- **la base lo resuelve**: la base trae un texto donde el libro remite al Salterio o a un Común.',
         '- **difieren**: cambian las palabras. Acá está lo que hay que revisar.',
         '- **solo en el libro**: el libro trae algo que la base no tiene.', '',
         '| Ámbito | Comparados | ' + ' | '.join(n.capitalize() for _, n, _ in GRUPOS) + ' |',
         '|---' * (2 + len(GRUPOS)) + '|']
    for f in filas:
        L.append('| ' + ' | '.join(str(x) for x in f) + ' |')
    L.append('| **' + str(tot[0]) + '** | ' + ' | '.join(f'**{x}**' for x in tot[1:]) + ' |')
    L += ['', 'Detalle de «solo en la forma»: ' +
          ', '.join(f'{Counter(t[3] for t in INF.textos)[k]} {d}' for k, d in DETALLE_FORMA) + '.', '']
    if INF.resueltas:
        L += ['Además, en ' + str(sum(INF.resueltas.values())) + ' casos la base trae una hora entera que el '
              'libro no imprime en ese lugar porque la toma del Salterio o de un Común: ' +
              ', '.join(f'{NOMBRE_AMBITO.get(a, a)} {h} ({n})' for (a, h), n in INF.resueltas.most_common(8)) +
              '.', '']
    L += ['## Qué cubre cada fuente', '',
          '| Sección del libro | Extraída | En la base | Archivos de la base |', '|---|---|---|---|']
    for f in cobertura():
        L.append('| ' + ' | '.join(str(x) for x in f) + ' |')
    L += ['', '## Dónde difieren', '']
    for a in ORDEN:
        dis = difieren(a)
        if not dis:
            continue
        L += [f'### {NOMBRE_AMBITO[a]} ({len(dis)})', '',
              'Por campo: ' + ', '.join(f'{k} ({v})' for k, v in Counter(t[2] for t in dis).most_common()) + '.', '']
        for t in sorted(dis, key=lambda x: len(x[4]) + len(x[5]))[:10]:
            L += [f'- **{t[1]} · {t[2]}**', f'  - base: {t[4][:260]}', f'  - libro: {t[5][:260]}']
        if len(dis) > 10:
            L.append(f'- … y {len(dis) - 10} más en `informes/textos.csv`.')
        L.append('')
    f = Counter((x[0], x[2]) for x in INF.faltantes)
    if f:
        L += ['## Lo que tiene una fuente y no la otra', '',
              '| Ámbito | Dónde | Cuántos |', '|---|---|--:|']
        for (a, d), n in sorted(f.items()):
            L.append(f'| {NOMBRE_AMBITO.get(a, a)} | {d} | {n} |')
        L += ['', 'El detalle está en `informes/faltantes.csv`. «No se pudo emparejar» son claves de la base '
              'que no encontraron su celebración en el libro (fiestas móviles, nombres muy distintos): no '
              'quiere decir que falten.', '']
    (INFORMES / 'base-vs-libro.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def html(carpeta):
    filas, tot = resumen()
    cf = Counter(t[3] for t in INF.textos)
    P = ['<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         '<title>La base de la app frente al libro</title><style>',
         ':root{--tinta:#1b1b1f;--papel:#fbfaf7;--borde:#e4e1d9;--rojo:#9c2a1a;--suave:#6b6a66}',
         '*{box-sizing:border-box}body{margin:0;background:var(--papel);color:var(--tinta);',
         'font:16px/1.6 Charter,Georgia,"Times New Roman",serif;padding:2.5rem 1.25rem 5rem}',
         'main{max-width:64rem;margin:0 auto}h1{font-size:2rem;margin:0 0 .4rem;letter-spacing:-.015em}',
         'h2{font-size:1.3rem;margin:2.8rem 0 .8rem;padding-bottom:.35rem;border-bottom:1px solid var(--borde)}',
         'h3{font-size:1.02rem;margin:2rem 0 .3rem}p{margin:.6rem 0}',
         '.sub{color:var(--suave)}.intro{max-width:46rem}',
         'ul{margin:.6rem 0;padding-left:1.1rem}li{margin:.25rem 0}',
         'table{border-collapse:collapse;width:100%;font-size:.88rem;margin:.8rem 0 1.4rem}',
         'th,td{padding:.45rem .6rem;border-bottom:1px solid var(--borde);text-align:left;vertical-align:top}',
         'th{font-weight:600;font-size:.74rem;text-transform:uppercase;letter-spacing:.045em;color:var(--suave)}',
         'td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}',
         'tr.tot td{font-weight:700;border-top:2px solid var(--tinta)}',
         '.par{border:1px solid var(--borde);border-radius:.5rem;background:#fff;padding:.7rem .9rem;margin:.6rem 0}',
         '.par .cl{font-size:.76rem;color:var(--suave);margin-bottom:.4rem;font-family:ui-monospace,monospace}',
         '.par .l{display:grid;grid-template-columns:3.6rem 1fr;gap:.6rem;margin:.3rem 0;font-size:.93rem}',
         '.par .et{color:var(--suave);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;padding-top:.2rem}',
         'mark{background:#fdeac6;color:#7a3b00;padding:0 .12em;border-radius:.15em}',
         'code{font-family:ui-monospace,monospace;font-size:.86em}',
         '.tag{display:inline-block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;',
         'color:var(--rojo);border:1px solid var(--borde);border-radius:1rem;padding:.05rem .5rem;margin-left:.4rem}',
         '</style></head><body><main>',
         '<h1>La base de la app frente al libro</h1>',
         '<p class="sub">Qué dice <code>base/</code> —los textos de la app, cargados una vez del repositorio '
         '<code>sync</code>— y qué dice el libro impreso, según la extracción de <code>extraccion/</code>.</p>',
         '<div class="intro"><p>Las dos fuentes no están armadas igual, y eso explica buena parte de las '
         'diferencias: <code>sync</code> guarda <b>cada día ya resuelto</b> —el salterio y el propio juntos, '
         'con una sola opción elegida—, mientras que el libro imprime <b>solo lo que cambia</b> y deja varias '
         'opciones. Por eso la comparación separa seis resultados:</p><ul>',
         '<li><b>iguales</b>: el mismo texto.</li>',
         '<li><b>solo en la forma</b>: tildes, comillas, guiones, mayúsculas, puntuación; las normas de ADF '
         'que la base ya aplicó («aleluia» por «Aleluya»); el «Padre nuestro.» con que el libro cierra la '
         'monición; y la conclusión de las oraciones, que la base escribe entera y el libro abrevia.</li>',
         '<li><b>cortado distinto</b>: el mismo texto repartido en otras estrofas o partes.</li>',
         '<li><b>la base lo resuelve</b>: la base trae texto donde el libro remite al Salterio o a un Común.</li>',
         '<li><b>difieren</b>: cambian las palabras. Acá está lo que hay que revisar.</li>',
         '<li><b>solo en el libro</b>: el libro trae algo que la base no tiene.</li></ul></div>',
         '<h2>Resumen</h2><table><tr><th>Ámbito</th><th class="n">Comparados</th>' +
         ''.join(f'<th class="n">{n.capitalize()}</th>' for _, n, _ in GRUPOS) + '</tr>']
    for f in filas:
        P.append('<tr><td>' + f[0] + '</td>' + ''.join(f'<td class="n">{x}</td>' for x in f[1:]) + '</tr>')
    P.append('<tr class="tot"><td>Total</td>' + ''.join(f'<td class="n">{x}</td>' for x in tot[1:]) + '</tr></table>')
    P.append('<p class="sub">Dentro de «solo en la forma»: ' +
             ', '.join(f'{cf[k]} {d}' for k, d in DETALLE_FORMA) + '.</p>')
    if INF.resueltas:
        P.append('<p>Además, en <b>' + str(sum(INF.resueltas.values())) + '</b> casos la base trae una hora '
                 'entera que el libro no imprime ahí porque la toma del Salterio o de un Común: ' +
                 ', '.join(f'{NOMBRE_AMBITO.get(a, a)} {h} ({n})' for (a, h), n in INF.resueltas.most_common(8)) +
                 '.</p>')
    P.append('<h2>Qué cubre cada fuente</h2><table><tr><th>Sección del libro</th><th>Extraída</th>'
             '<th>En la base</th><th>Archivos de la base</th></tr>')
    for f in cobertura():
        P.append('<tr>' + ''.join(f'<td>{escapar(x)}</td>' for x in f) + '</tr>')
    P.append('</table>')
    P.append('<h2>Dónde difieren</h2><p class="sub">Las palabras marcadas son las que no coinciden. '
             'Se muestran los primeros veinte de cada ámbito; el resto está en '
             '<code>extraccion/informes/textos.csv</code>.</p>')
    for a in ORDEN:
        dis = difieren(a)
        if not dis:
            continue
        P.append(f'<h3>{NOMBRE_AMBITO[a]}<span class="tag">{len(dis)}</span></h3>')
        P.append('<p class="sub">' +
                 ', '.join(f'{escapar(k)} ({v})' for k, v in Counter(t[2] for t in dis).most_common(8)) + '.</p>')
        for t in sorted(dis, key=lambda x: len(x[4]) + len(x[5]))[:20]:
            ra, rb = resaltar(escapar(t[4])[:420], escapar(t[5])[:420])
            P.append(f'<div class="par"><div class="cl">{escapar(t[1])} · {escapar(t[2])}</div>'
                     f'<div class="l"><div class="et">base</div><div>{ra}</div></div>'
                     f'<div class="l"><div class="et">libro</div><div>{rb}</div></div></div>')
    f = Counter((x[0], x[2]) for x in INF.faltantes)
    if f:
        P.append('<h2>Lo que tiene una fuente y no la otra</h2><table>'
                 '<tr><th>Ámbito</th><th>Dónde</th><th class="n">Cuántos</th></tr>')
        for (a, d), n in sorted(f.items()):
            P.append(f'<tr><td>{NOMBRE_AMBITO.get(a, a)}</td><td>{d}</td><td class="n">{n}</td></tr>')
        P.append('</table><p class="sub">El detalle está en <code>extraccion/informes/faltantes.csv</code>. '
                 '«No se pudo emparejar» son claves de la base que no encontraron su celebración en el libro '
                 '(fiestas móviles, nombres muy distintos): no quiere decir que falten.</p>')
    P.append('</main></body></html>')
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / 'index.html').write_text('\n'.join(P), encoding='utf-8')
    return carpeta / 'index.html'


def main():
    nb, nl, alias = comparar_salmos()
    hb, hl = comparar_himnos()
    comparar_completas()
    comparar_salterio()
    comparar_comunes()
    comparar_santoral()
    comparar_tiempo()
    csvs()
    markdown()
    c = INF.cuenta()
    print(f'salmos: {nb} en la base, {nl} en el libro ({alias} emparejados por el texto); '
          f'himnos: {hb} / {hl}')
    print(f'textos comparados: {sum(c.values())} · iguales: {c["igual"]} · en la forma: {c["forma"]} · '
          f'difieren: {c["distinto"]} · faltantes: {len(INF.faltantes)}')
    if '--html' in sys.argv:
        print('página:', html(sys.argv[sys.argv.index('--html') + 1]))


if __name__ == '__main__':
    main()
