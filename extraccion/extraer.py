#!/usr/bin/env python3
"""Extracción del libro de la Liturgia de las Horas desde LH_completa.pdf.

Prueba: Común de la Santísima Virgen María (con la memoria de santa María en
sábado), de los cuatro tomos. Sigue «Extracción de la Liturgia de las Horas
desde el PDF: instrucciones para una IA» (13-11-2026):

- lee el PDF fragmento por fragmento con PyMuPDF (color, fuente, posición);
- clasifica cada fragmento por color y posición (rúbrica, rótulo, etiqueta,
  remisión, texto);
- arma horas → partes → piezas → variantes, cada variante con su etiqueta
  literal y su condición normalizada;
- extrae cada tomo por separado y después los unifica pieza por pieza;
- escribe virgen.json, salmos.json, himnos.json, dudas.csv, diferencias.csv
  y controles.txt.

Fiel al libro: no corrige ni aplica normas de ADF.

Uso:
    python3 extraccion/extraer.py RUTA/LH_completa.pdf [--revision CARPETA]

--revision además genera la página de revisión lado a lado (imágenes de las
páginas + piezas) en CARPETA. Las imágenes salen del PDF y no van al repo.
"""
import csv
import difflib
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

AQUI = Path(__file__).resolve().parent

# Páginas del PDF unido (contadas desde 1) de cada sección extraída.
SECCIONES = {
    # prueba aprobada: Común de la Santísima Virgen María + santa María en sábado
    'virgen': {'tomos': {1: (851, 869), 2: (2459, 2481), 3: (4104, 4141), 4: (5968, 6003)},
               'salida': AQUI / 'comunes' / 'virgen', 'archivo': 'virgen.json', 'seccion': 'comunes',
               'nombre': 'Común de la Santísima Virgen María'},
    # paso 2: todos los comunes (de la Dedicación hasta antes del Oficio de difuntos)
    'comunes': {'tomos': {1: (834, 1012), 2: (2438, 2642), 3: (4085, 4283), 4: (5950, 6150)},
                'salida': AQUI / 'comunes', 'archivo': 'comunes.json', 'seccion': 'comunes',
                'nombre': 'Oficios comunes'},
    # paso 3: Ordinario de la Liturgia de las Horas (desde la portada hasta antes del Salterio)
    'ordinario': {'tomos': {1: (401, 432), 2: (1865, 1898), 3: (3314, 3343), 4: (5073, 5101)},
                  'salida': AQUI / 'ordinario', 'archivo': 'ordinario.json', 'seccion': 'ordinario',
                  'nombre': 'Ordinario de la Liturgia de las Horas', 'modo': 'ordinario'},
}
TOMOS = SECCIONES['virgen']['tomos']
SALIDA = SECCIONES['virgen']['salida']

# Títulos de los comunes y de sus subsecciones → identificador
IDS_COMUN = [
    (r'^ORDINARIO', 'ordinario'),
    (r'DEDICACI', 'dedicacion'), (r'SÁBADO|SABADO', 'santa-maria-sabado'), (r'MAR[ÍI]A', 'virgen'),
    (r'AP[ÓO]STOLES', 'apostoles'), (r'VARIOS\s*M[ÁA]RTIRES', 'martires-varios'),
    (r'UN\s*M[ÁA]RTIR', 'martires-uno'), (r'M[ÁA]RTIRES', 'martires'), (r'PASTORES', 'pastores'),
    (r'DOCTORES', 'doctores'), (r'V[ÍI]RGENES', 'virgenes'), (r'VARONES', 'santos-varones'),
    (r'MUJERES', 'santas-mujeres'), (r'RELIGIOSOS', 'religiosos'), (r'CARITATIVA', 'caridad'),
    (r'EDUCADORES', 'educadores'), (r'DIFUNTOS', 'difuntos'),
]

ROJOS = {'ff0000', 'ff2600'}
AZULES = {'0000ff', '021eaa'}
VERDE = '023300'

HORAS = {
    'i vísperas': 'visperas1', 'ii vísperas': 'visperas2', 'vísperas': 'visperas',
    'invitatorio': 'invitatorio', 'oficio de lectura': 'oficio', 'laudes': 'laudes',
    'hora intermedia': 'intermedia', 'tercia': 'tercia', 'sexta': 'sexta',
    'nona': 'nona', 'completas': 'completas',
}
ROTULOS = [  # (prefijo en mayúsculas, parte, tipo de pieza)
    ('HIMNO', 'himno', 'himno'),
    ('SALMODIA', 'salmodia', None),
    ('LECTURA BREVE', 'lectura_breve', 'lectura_breve'),
    ('RESPONSORIO BREVE', 'responsorio_breve', 'responsorio_breve'),
    ('CÁNTICO EVANGÉLICO', 'cantico_evangelico', 'antifona'),
    ('PRECES', 'preces', 'preces'),
    ('PRIMERA LECTURA', 'primera_lectura', 'lectura'),
    ('SEGUNDA LECTURA', 'segunda_lectura', 'lectura'),
    ('CONCLUSIÓN', 'conclusion', None),
]
RE_ETIQUETA = re.compile(
    r'^(O bien\b.*|(En )?[Tt]iempo\b.*|Para (un|una|unos|unas|varios|varias)\b.*|'
    r'Antífona para .*|Año [IVXABC]+|Ciclo (anual|bienal)|España|[IVX]+)$')
RE_ETIQUETA_LARGA = re.compile(
    r'^(O bien\b|Para (un|una|unos|unas|varios|varias|los|las)\b|(En )?(el )?[Tt]iempo\b|'
    r'Cuando el Oficio se celebra\b|Versión\b|Si se trata de\b|Antífona para\b|'
    r'(Primera|Segunda|Tercera|Cuarta|Quinta) fórmula\b)')
RE_TP = re.compile(r'\s*\x01\s*\(\s*T\.?\s*\x02?\s*\x01?\s*P\.?\s*\x02?\s*Aleluya\.?\s*\x01?\s*\)\s*\.?\s*\x02?\s*\.?\s*$')
RE_GLORIA_V = re.compile(r'^Gloria al Padre, y al Hijo, y al Espíritu Santo\.?$')


# ───────────────────────────── utilidades de texto ──────────────────────────
def hexcolor(c):
    return '%06x' % c


def clase_color(c):
    h = hexcolor(c)
    r, g, b = c >> 16, (c >> 8) & 255, c & 255
    if h in ROJOS:
        return 'R', False
    if h in AZULES:
        return 'B', False
    if h == VERDE:
        return 'G', False
    if max(r, g, b) < 90:   # negros casi puros (0b0b0b, 323232, 474747…)
        return 'k', h not in ('000000', '0b0b0b', '323232', '474747', '1b150c', '030000')
    if r > g and r > b:
        return 'R', True          # rojo dudoso: se anota
    if b > r and b > g:
        return 'B', True
    if g > r and g > b:
        return 'G', True
    return 'k', True


def marcar(segs):
    """Texto con el rojo entre \x01…\x02 y el azul entre \x03…\x04."""
    out = []
    for s in segs:
        t = s['t']
        if s['c'] == 'R':
            out.append('\x01' + t + '\x02')
        elif s['c'] == 'B':
            out.append('\x03' + t + '\x04')
        else:
            out.append(t)
    return ''.join(out)


def plano(s):
    return re.sub(r'[\x01-\x04]', '', s)


def limpiar_marcas(s):
    """Quita marcas que solo encierran espacios y une marcas contiguas."""
    s = re.sub(r'\x01(\s*)\x02', r'\1', s)
    s = re.sub(r'\x03(\s*)\x04', r'\1', s)
    s = s.replace('\x02\x01', '').replace('\x04\x03', '')
    return s


def espacios(s):
    return re.sub(r'[ \t ]+', ' ', s).strip()


def unir_lineas(lineas, avisos=None):
    """Une renglones de prosa: espacio entre líneas; guion de corte sin espacio."""
    out = ''
    for l in lineas:
        l = l.strip()
        if not l:
            continue
        if not out:
            out = l
        elif re.search(r'\w-$', out) and l[:1].islower():
            out = out[:-1] + l
            if avisos is not None:
                avisos.append(out[-40:])
        else:
            out += ' ' + l
    return espacios(out)


def norm_item(s):
    s = unicodedata.normalize('NFC', plano(s))
    s = re.sub(r'[«»“”"„]', '"', s)
    s = re.sub(r"[’‘`´]", "'", s)
    s = re.sub(r'[—–‐‑-]', '-', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.rstrip('.,;: ')
    return s[:1].lower() + s[1:]


def norm_lista(xs):
    return ' | '.join(norm_item(x) for x in xs if x is not None)


def slug(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def id_salmo(cita):
    """«Salmo 112» → salmo-112; «Cántico Ef 1, 3-10» → cantico-ef-1-3-10."""
    m = re.match(r'(Salmo|Cántico)\s+(.*)', cita.strip(), re.I)
    if not m:
        return slug(cita)
    pref = 'salmo' if m.group(1).lower() == 'salmo' else 'cantico'
    return pref + '-' + slug(m.group(2))


# ─────────────────────────────── lectura del PDF ────────────────────────────
class Renglon:
    __slots__ = ('tomo', 'pdf', 'impresa', 'y', 'x', 'segs', 'gap', 'dueno',
                 'n', 'dudoso', 'es_et')

    def __init__(self, **k):
        for a in self.__slots__:
            setattr(self, a, k.get(a))

    @property
    def texto(self):
        return ''.join(s['t'] for s in self.segs)

    @property
    def m(self):
        return limpiar_marcas(marcar(self.segs))

    @property
    def vacio(self):
        return not self.texto.strip()

    def primer(self):
        for s in self.segs:
            if s['t'].strip():
                return s
        return self.segs[0]

    @property
    def c0(self):
        return self.primer()['c']

    @property
    def negrita(self):
        return 'Bold' in self.primer()['f']

    @property
    def talla(self):
        return round(self.primer()['s'])

    @property
    def solo(self):
        """Colores presentes (sin contar espacios)."""
        return {s['c'] for s in self.segs if s['t'].strip()}


def leer_tomo(doc, tomo, a, b):
    renglones, descartes = [], []
    n = 0
    for p in range(a - 1, b):
        pg = doc[p]
        crudos = []
        for bl in pg.get_text('dict')['blocks']:
            for l in bl.get('lines', []):
                segs = []
                for s in l['spans']:
                    if s['text'] == '':
                        continue
                    c, dud = clase_color(s['color'])
                    segs.append({'t': s['text'], 'c': c, 'f': s['font'], 's': s['size'],
                                 'hex': hexcolor(s['color']), 'dud': dud})
                if segs:
                    crudos.append([l['bbox'][1], l['bbox'][0], segs])
        crudos.sort(key=lambda t: (round(t[0], 0), t[1]))
        # unir fragmentos de la misma altura en un solo renglón
        lineas = []
        for y, x, segs in crudos:
            if lineas and abs(lineas[-1][0] - y) < 2.5:
                lineas[-1][2].extend(segs)
            else:
                lineas.append([y, x, segs])
        impresa = None
        prev_y = None
        for y, x, segs in lineas:
            texto = ''.join(s['t'] for s in segs).strip()
            f0 = segs[0]['f']
            es_pie = f0.startswith('Helvetica') and round(segs[0]['s']) <= 10 and segs[0]['c'] == 'k'
            if es_pie and re.fullmatch(r'-?\d+-?', texto):
                impresa = texto.strip('-')
                descartes.append(dict(tomo=tomo, pdf=p + 1, motivo='número de página', texto=texto))
                continue
            if texto.startswith('LITURGIA DE LAS HORAS') or (f0.startswith('Helvetica') and round(segs[0]['s']) <= 10 and y < 50):
                descartes.append(dict(tomo=tomo, pdf=p + 1, motivo='encabezado', texto=texto))
                continue
            gap = (y - prev_y) if prev_y is not None else max(14.0, y - 56.9 + 14)
            partes = [segs]
            s0 = segs[0]['t'].strip()
            if (segs[0]['c'] == 'R' and s0.endswith(':') and len(segs) > 1 and
                    (RE_ETIQUETA.match(s0[:-1].strip()) or RE_ETIQUETA_LARGA.match(s0)) and
                    any(x['c'] == 'k' and x['t'].strip() for x in segs[1:])):
                partes = [segs[:1], segs[1:]]   # «Tiempo de Cuaresma: texto…» → etiqueta + texto
            for j, sg in enumerate(partes):
                r = Renglon(tomo=tomo, pdf=p + 1, y=round(y, 1), x=round(x, 1), segs=sg,
                            gap=gap if j == 0 else 0.0, n=n,
                            dudoso=any(s['dud'] for s in sg if s['t'].strip()))
                n += 1
                renglones.append(r)
            prev_y = y
        for r in renglones:
            if r.pdf == p + 1:
                r.impresa = impresa
    return renglones, descartes


# ─────────────────────────────── estructura ────────────────────────────────
def nueva_variante(tipo, **campos):
    v = {'_tipo': tipo, '_raw': [], '_fuente': None}
    v.update(campos)
    return v


class Parser:
    """Recorre el flujo de un tomo y arma comunes → horas → partes → piezas."""

    def __init__(self, tomo, renglones, modo='comunes'):
        self.modo = modo
        self.tomo = tomo
        self.R = renglones
        self.i = 0
        self.comunes = []
        self.comun = None
        self.hora = None
        self.parte = None
        self.etiqueta = None      # etiqueta pendiente (renglones, texto)
        self.salmos = {}          # id → {cita, titulo, sentencia, partes}
        self.ultimo_salmo = None
        self.ult_antifona = None
        self.avisos = []          # (renglón, motivo)
        self.cortes = []

    # — consumo —
    def tomar(self, r, dueno):
        r.dueno = dueno
        if isinstance(dueno, dict) and '_raw' in dueno:
            dueno['_raw'].append(r)

    def actual(self):
        return self.R[self.i] if self.i < len(self.R) else None

    def sig(self, k=1):
        j = self.i + k
        return self.R[j] if j < len(self.R) else None

    # — clasificación de un renglón —
    def clase(self, r):
        k = self._clase_base(r)
        if self.modo != 'ordinario' or k in ('blanco', 'titulo', 'hora', 'separador'):
            return k
        t = r.texto.strip()
        if r.c0 == 'R' and re.fullmatch(r'[IVX]+', t):
            return 'romano'
        if r.c0 == 'k' and r.negrita and r.solo == {'k'} and k == 'negro':
            if self.hora is None and t.upper() == t:
                return 'subtitulo'
            prev = self.R[r.n - 1] if r.n > 0 else None
            nx = self.R[r.n + 1] if r.n + 1 < len(self.R) else None
            junto = lambda x, g: x is not None and x.c0 == 'k' and x.negrita and not x.vacio and g <= 16.5
            if len(t) < 60 and not junto(prev, r.gap) and not (nx is not None and junto(nx, nx.gap)):
                return 'subtitulo'
        if r.c0 == 'R' and re.match(r'^Versi[óo]n\b', t) and not t.endswith('.'):
            return 'etiqueta'
        if k in ('rubrica', 'mayusculas') and r.x < 70 and r.solo <= {'R'} and len(t.split()) <= 9 and \
                not t.endswith(('.', ':')) and (r.negrita or 'Bold' in ''.join(s['f'] for s in r.segs) or t.isupper()):
            return 'rotulo'
        return k

    def _clase_base(self, r):
        t = r.texto.strip()
        if r.vacio:
            return 'blanco'
        if re.fullmatch(r'\*(\s*\*){2}', t) and r.c0 == 'R':
            return 'separador'
        if r.c0 == 'R' and t.startswith('*'):
            return 'asterisco'
        if r.c0 == 'R' and r.talla >= 18 and re.fullmatch(r'\d+', t):
            return 'numero_seccion'
        if (r.talla >= 14 and t.upper() == t and (len(t) > 12 or r.talla >= 20) and re.search(r'[A-ZÁÉÍÓÚ]{4}', t) and
                (r.c0 == 'k' or r.talla >= 18)):
            return 'titulo'
        low = t.lower()
        if r.c0 == 'k' and r.negrita and re.match(r'^(En )?[Tt]iempo\b', t) and len(t.split()) <= 6:
            return 'bloque'
        if r.c0 == 'k' and low in HORAS and (r.negrita or t.isupper() or r.x > 150):
            return 'hora'
        if r.c0 == 'R':
            up = t.upper()
            for pref, parte, tipo in ROTULOS:
                if up.startswith(pref) and t.startswith(pref) and r.x < 70:
                    return 'rotulo'
            if t == 'Oración' or t == 'Oración.':
                return 'rotulo'
            if re.match(r'^Responsorio\b', t):
                return 'responsorio'
            if re.match(r'^Ant\.( ?\d\.)?', t):
                return 'ant'
            if re.fullmatch(r'Antífona( \d)?', t):
                return 'antifona_rotulo'
            if re.match(r'^V\.', t):
                return 'v'
            if re.match(r'^R\.', t):
                return 'r'
            if t.startswith('—'):
                return 'guion'
            if r.x > 100 and re.fullmatch(r'[IVX]+', t):
                return 'romano'
            if r.x > 100 and re.match(r'^(Salmo|Cántico)\b', t, re.I):
                return 'salmo'
            if r.solo == {'R'} and ':' not in t and not t.endswith('.') and len(t.split()) <= 6 and \
                    re.match(r'^(O bien\b|Para (un|una|unos|unas|varios|varias|los|las)\b|(Primera|Segunda|Tercera|Cuarta|Quinta) fórmula\b)', t):
                return 'etiqueta'
            if t.endswith(':') and r.solo == {'R'} and (RE_ETIQUETA.match(t[:-1].strip()) or RE_ETIQUETA_LARGA.match(t)):
                return 'etiqueta'
            if t.startswith('('):
                return 'fuente'
            if t.upper() == t and r.solo == {'R'}:
                return 'mayusculas'
            return 'rubrica'
        if r.c0 == 'B' and r.solo <= {'B', 'R'}:
            return 'remite'
        if r.c0 == 'G':
            return 'biografia'
        return 'negro'

    # — partes y piezas —
    def abrir_comun(self, titulo, r):
        up = re.sub(r'\s+', '', titulo.upper())
        cid = next((i for rx, i in IDS_COMUN if re.search(rx.replace('\\s*', ''), up)), slug(titulo))
        sub = re.match(r'^PARA\b', titulo.strip().upper())
        padre = None
        if sub and self.comun is not None and not titulo.upper().startswith('COMÚN'):
            padre = self.comun.get('_padre') or self.comun['titulo']
            if not self.comun['horas'] and not self.comun['rubricas'] and self.comun['id'] not in ('santa-maria-sabado',):
                # «COMÚN DE SANTOS MÁRTIRES» seguido de «PARA VARIOS MÁRTIRES»: un solo común
                self.comunes.remove(self.comun)
                padre = self.comun['titulo']
        self.comun = {'id': cid, 'titulo': espacios(titulo), 'rubricas': [], 'horas': {},
                      '_orden': [], '_pdf': r.pdf, '_impresa': r.impresa}
        if padre:
            self.comun['seccion'] = padre
            self.comun['_padre'] = padre
        self.comunes.append(self.comun)
        self.hora = None
        self.parte = None

    def abrir_hora(self, hid):
        if self.comun is None:
            self.abrir_comun('COMÚN DE LA SANTÍSIMA VIRGEN MARÍA', self.actual())
        self.hora = self.comun['horas'].setdefault(hid, [])
        if hid not in self.comun['_orden']:
            self.comun['_orden'].append(hid)
        self.hora_id = hid
        self.parte = None
        self.etiqueta = None
        self.bloque = None

    def abrir_parte(self, nombre, reusar=False):
        if self.hora is None:
            self.abrir_hora('antes_del_oficio' if self.modo == 'ordinario' else 'visperas1')
        if reusar:
            for p in reversed(self.hora):
                if p['parte'] == nombre:
                    self.parte = p
                    return p
        p = {'parte': nombre, 'piezas': [], '_raw': []}
        self.hora.append(p)
        self.parte = p
        return p

    def pieza(self, tipo, nueva=False):
        """Pieza a la que va la próxima variante de este tipo."""
        if self.parte is None:
            self.abrir_parte(tipo)
        if not nueva:
            for pz in reversed(self.parte['piezas']):
                if pz['tipo'] == tipo:
                    return pz
        pz = {'tipo': tipo, 'variantes': []}
        self.parte['piezas'].append(pz)
        return pz

    def agregar_variante(self, tipo, v, forzar_nueva=False):
        """Con etiqueta pendiente, la variante se suma a la última pieza del tipo."""
        et = self.etiqueta
        self.etiqueta = None
        bl = getattr(self, 'bloque', None)
        if bl is not None and tipo != 'rubrica':
            hay_b = [pz for pz in self.parte['piezas'] if pz['tipo'] == tipo] if self.parte else []
            if et is None and (not hay_b or id(hay_b[-1]) not in bl['piezas']):
                et = {'texto': bl['texto'], 'renglones': []}
                v['_et_bloque'] = True
            elif et is not None:
                v['_et_render'] = et['texto']
                if not condicion(et['texto'])[1]:
                    et = {'texto': bl['texto'] + ' ' + et['texto'], 'renglones': et['renglones']}
        if et is not None:
            v['etiqueta'] = et['texto']
            for rr in et['renglones']:
                self.tomar(rr, v)
        hay = [pz for pz in self.parte['piezas'] if pz['tipo'] == tipo] if self.parte else []
        if et is not None:
            c, es_op, _ = condicion(et['texto'])
            prev = hay[-1]['variantes'][-1] if hay and hay[-1]['variantes'] else None
            if es_op and prev is not None:
                base = {k: x for k, x in (prev.get('_cuando') or {}).items()}
                base.update(c)
                c = base
            v['_cuando'] = c
        if et is not None and et['renglones']:
            v['_et_n'] = et['renglones'][0].n
        if et is not None and hay and not forzar_nueva:
            pz = hay[-1]
        elif et is not None and not hay:
            pz = self.pieza(tipo, nueva=True)
        else:
            pz = self.pieza(tipo, nueva=True)
        if bl is not None:
            bl['piezas'].add(id(pz))
        pz['variantes'].append(v)
        v['_fuente'] = {'tomo': self.tomo}
        return pz

    # — consumidores —
    def continuacion(self, r, previo_m):
        """¿El renglón r sigue el texto anterior?"""
        if r is None or r.vacio:
            return False
        abierto = previo_m.count('(') > previo_m.count(')')
        if abierto and r.c0 == 'R':
            return True
        if self.clase(r) == 'asterisco':
            return True
        if r.c0 == 'R' and re.match(r'^\x01\s*\(\s*\x02', r.m) and 'k' in r.solo:
            return True    # «(de nosotros).» con paréntesis rojos al comienzo del renglón
        if r.c0 != 'k':
            return False
        if r.gap is not None and r.gap < 50 and not re.search(r'[.!?»)]\s*\x02?\s*$', previo_m):
            return True    # la frase sigue aunque el libro deje más espacio
        return r.gap is None or r.gap <= 16.5

    def leer_texto_simple(self, v, primero_m):
        """Junta el texto de un renglón y sus continuaciones (antífona, oración…)."""
        partes = [primero_m]
        while True:
            r = self.actual()
            if not self.continuacion(r, partes[-1]):
                break
            if self.clase(r) not in ('negro', 'ant', 'rubrica', 'v', 'r') and r.c0 != 'R':
                break
            if r.c0 == 'k' and self.clase(r) == 'negro' and r.x > 62 and len(partes) > 0 and self.es_parrafo(r):
                break
            self.tomar(r, v)
            partes.append(r.m)
            self.i += 1
        return unir_lineas(partes, self.cortes)

    def es_parrafo(self, r):
        return False

    def separar_tp(self, m):
        mm = RE_TP.search(m)
        if mm:
            return m[:mm.start()], True, plano(mm.group(0)).strip()
        mm = re.search(r'\s*\(T\.\s*P\.\s*Aleluya\.?\)\.?\s*$', plano(m))
        if mm and '\x01' in m:
            return plano(m)[:mm.start()], True, mm.group(0).strip()
        return m, False, None

    def texto_limpio(self, m, v, contexto):
        """Texto sin marcas; si queda rojo adentro, se anota."""
        m = limpiar_marcas(m)
        # paréntesis rojos con una palabra negra adentro: se dice o no según el caso
        m = re.sub(r'\x01([^\x02]*?)\(\s*\x02([^\x01\x02]+?)\x01\s*\)', lambda x: '\x01' + x.group(1) + '\x02[' + x.group(2).strip() + ']\x01', m)
        # N. rojo (nombre del santo)
        m = re.sub(r'\x01([^\x02]*?)\bN\.([,;:]?)', lambda x: '\x01' + x.group(1) + '\x02{N}' + x.group(2) + '\x01', m)
        m = limpiar_marcas(m)
        m = re.sub(r'\x01(\s*[.,;:]+\s*)\x02', r'\1', m)   # puntuación que quedó en rojo junto a un paréntesis
        if re.search(r'\x01\s*\+\s*\x02', m):   # «+» rojo dentro del texto: signo de la cruz
            v['signo_cruz'] = True
            v.setdefault('_signos', []).append('+')
            m = re.sub(r'\s*\x01\s*\+\s*\x02', '', m)
        quedan = [q for q in re.findall(r'\x01(.*?)\x02', m) if q.strip()]
        if quedan:
            v.setdefault('_rojo', []).extend(q.strip() for q in quedan)
            v['revisar'] = True
            v.setdefault('_notas', []).append(f'rojo dentro de {contexto}, sacado del texto: {quedan}')
            m = re.sub(r'\x01.*?\x02', ' ', m)
        return espacios(plano(m))

    # — bucle principal —
    def run(self):
        while self.i < len(self.R):
            r = self.actual()
            k = self.clase(r)
            getattr(self, 'c_' + k)(r)
        return self

    def c_blanco(self, r):
        self.tomar(r, 'blanco'); self.i += 1

    def c_separador(self, r):
        self.tomar(r, 'separador'); self.i += 1

    def c_numero_seccion(self, r):
        self.tomar(r, 'numero de sección'); self.i += 1

    def c_titulo(self, r):
        t = r.texto
        self.i += 1
        if r.talla >= 18 and r.c0 == 'k':   # tomo IV: espacios en otro cuerpo
            t = ' '.join(s['t'] for s in r.segs if s['t'].strip())
        extra = []
        while self.actual() is not None and self.actual().talla >= 14 and self.actual().texto.strip().isupper() and \
                self.actual().gap <= max(22, 1.7 * self.actual().talla) \
                and self.actual().c0 == r.c0 and not re.match(r'^(COMÚN|PARA|MEMORIA|OFICIO|ORDINARIO)', self.actual().texto.strip()):
            extra.append(self.actual()); t += ' ' + self.actual().texto; self.i += 1
        if self.comun is not None and espacios(t).upper() == self.comun['titulo'].upper():
            self.tomar(r, self.comun)
            for x in extra:
                self.tomar(x, self.comun)
            return
        self.abrir_comun(t, r)
        self.tomar(r, self.comun)
        for x in extra:
            self.tomar(x, self.comun)
        self.comun['_rawtitulo'] = r

    def c_hora(self, r):
        hid = HORAS[r.texto.strip().lower()]
        self.abrir_hora(hid)
        self.tomar(r, 'hora:' + hid)
        self.i += 1

    def c_biografia(self, r):
        self.avisos.append((r, 'texto verde (biografía) inesperado en un común'))
        self.tomar(r, 'biografia'); self.i += 1

    def c_etiqueta(self, r):
        t = espacios(r.texto)
        # «O bien:» después de la respuesta de las preces → otra respuesta
        if (self.parte and self.parte['parte'] == 'preces' and self.parte['piezas'] and
                self.parte['piezas'][-1]['variantes'] and
                not self.parte['piezas'][-1]['variantes'][-1].get('_cerrada') and
                not self.parte['piezas'][-1]['variantes'][-1]['intenciones']):
            v = self.parte['piezas'][-1]['variantes'][-1]
            self.tomar(r, v)
            self.i += 1
            rr = self.actual()
            self.tomar(rr, v)
            self.i += 1
            v['respuesta'].append({'etiqueta': t, 'texto': espacios(plano(rr.m))})
            return
        if self.etiqueta is not None:   # «En tiempo de cuaresma:» + «Para un santo:»
            self.etiqueta = {'texto': self.etiqueta['texto'] + ' ' + t,
                             'renglones': self.etiqueta['renglones'] + [r]}
        else:
            self.etiqueta = {'texto': t, 'renglones': [r]}
        self.i += 1

    def c_subtitulo(self, r):
        t = espacios(r.texto)
        self.i += 1
        j = self.i
        while j < len(self.R) and self.R[j].vacio:
            j += 1
        if j < len(self.R) and self.clase(self.R[j]) == 'hora' and self.comun is not None:
            # «Oración de la mañana» antes de «Laudes»: título que agrupa la hora siguiente
            hid = HORAS.get(self.R[j].texto.strip().lower())
            self.comun.setdefault('agrupacion', {})[hid] = t
            self.tomar(r, 'agrupación: ' + t)
            return
        if self.hora is None and self.comun is not None:
            self.comun['subtitulo'] = espacios((self.comun.get('subtitulo') or '') + ' ' + t)
            self.tomar(r, self.comun)
            return
        if self.hora is None:
            self.abrir_hora('antes_del_oficio')
        p = self.abrir_parte(slug(t).replace('-', '_'))
        p['titulo'] = t
        self.tomar(r, p)

    def leer_texto_generico(self, r):
        """Ordinario: texto fijo en prosa o en verso (Te Deum, cánticos, oraciones)."""
        v = nueva_variante('texto')
        lineas = []
        while True:
            r = self.actual()
            if r is None:
                break
            k = self.clase(r)
            if k == 'blanco':
                nx = self.sig()
                if lineas and nx is not None and self.clase(nx) == 'negro':
                    self.tomar(r, v); self.i += 1; lineas.append(None)
                    continue
                break
            cruz = re.match(r'^\x01\s*\+\s*\x02', r.m)
            if k not in ('negro', 'asterisco') and not cruz:
                break
            if lineas and lineas[-1] is not None and r.gap > 34:
                break
            lineas.append(r); self.tomar(r, v); self.i += 1
        reales = [x for x in lineas if x is not None]
        largos = sorted(len(x.texto.strip()) for x in reales)
        sangrado = len(reales) > 1 and reales[0].x < 62 and any(x.x > reales[0].x + 8 for x in reales[1:])
        verso = len(reales) >= 2 and (largos[len(largos) // 2] < 62 or sangrado)
        if verso:
            estrofas, actual, xs = [], [], []
            for j, x in enumerate(lineas):
                if x is None or (actual and x.gap > 18):
                    if actual:
                        estrofas.append(actual); actual = []
                    if x is None:
                        continue
                m = x.m
                extra = {}
                mm = re.match(r'^\x01\s*\+\s*\x02\s*', m)
                if mm:                       # «+» rojo: signo de la cruz
                    m = m[mm.end():]; extra['cruz'] = True
                partes_v = re.split(r'\x01\s*\*\s*\x02', m)      # «*» rojo: mediante(s) del verso
                partes_v = [self.texto_limpio(pv, v, 'un verso') for pv in partes_v]
                if actual and actual[-1].get('_sigue'):
                    # el verso anterior terminaba en «*»: este renglón es su segunda mitad
                    prev = actual[-1]
                    prev['mitades'][-1:] = [partes_v[0]] + partes_v[1:] if not prev['mitades'][-1] else prev['mitades'][-1:] + partes_v
                    prev['_sigue'] = partes_v[-1] == '' and len(partes_v) > 1
                    prev['texto'] = espacios(' '.join(x2 for x2 in prev['mitades'] if x2))
                    continue
                if len(partes_v) > 1:
                    extra['mitades'] = partes_v
                    extra['_sigue'] = partes_v[-1] == ''
                actual.append({'texto': espacios(' '.join(x2 for x2 in partes_v if x2)), '_x': x.x, **extra,
                               '_marcas': ('', '', '+' if extra.get('cruz') else '')})
                xs.append(x.x)
            if actual:
                estrofas.append(actual)
            base = min(xs)
            for e in estrofas:
                for vs in e:
                    vs.pop('_sigue', None)
                    if vs.get('mitades'):
                        vs['mitades'] = [x2 for x2 in vs['mitades'] if x2]
                    d = vs.pop('_x') - base
                    vs['sangria'] = 0 if d < 7 else (1 if d < 21 else 2)
            v['estrofas'] = estrofas
        else:
            pars, actual = [], []
            for x in lineas:
                if x is None or (actual and (x.x > 62 or x.gap > 18)):
                    if actual:
                        pars.append(actual); actual = []
                    if x is None:
                        continue
                actual.append(x.m)
            if actual:
                pars.append(actual)
            v['parrafos'] = [self.texto_limpio(unir_lineas(p, self.cortes), v, 'un texto') for p in pars]
        self.agregar_variante('texto', v)

    def c_bloque(self, r):
        """Encabezado negro «En tiempo de cuaresma»: condición de las partes que siguen."""
        self.bloque = {'texto': espacios(r.texto), 'piezas': set()}
        self.tomar(r, 'bloque: ' + espacios(r.texto))
        self.i += 1

    def c_romano(self, r):
        t = r.texto.strip()
        if self.parte and self.parte['parte'] == 'himno':
            self.etiqueta = {'texto': t, 'renglones': [r]}
            self.i += 1
            return
        if self.modo == 'ordinario' and (self.parte is None or self.parte['parte'] != 'salmodia'):
            # Ordinario: «I», «II»… numeran opciones (himnos de la Hora intermedia)
            if self.parte is None or self.parte['parte'] not in ('himno',):
                self.abrir_parte('himno', reusar=True)
            self.etiqueta = {'texto': t, 'renglones': [r]}
            self.i += 1
            return
        # parte de un salmo: «I», «II» rojo centrado → parte del último salmo
        self.i += 1
        self.leer_salmo(self.ultimo_salmo, parte=t, r_titulo=r)

    def c_rotulo(self, r):
        t = espacios(r.texto)
        up = t.upper()
        nombre, tipo = None, None
        for pref, parte, tp in ROTULOS:
            if up.startswith(pref):
                nombre, tipo, resto = parte, tp, t[len(pref):].strip()
                if nombre != 'lectura_breve':
                    resto = resto.strip(' ,.')
                break
        else:
            nombre, resto = 'oracion', ''
            if t.rstrip('.') != 'Oración':   # Ordinario: rótulos propios («LECTURA LARGA», «Oración conclusiva»…)
                nombre = slug(t).replace('-', '_')
        self.i += 1
        # rótulos de la hora intermedia y de las opciones del sábado
        reusar = (self.etiqueta is not None or getattr(self, 'bloque', None) is not None or (self.parte is not None and self.parte['parte'] == nombre) or
                  nombre == 'responsorio_breve' and self._pareja('lectura_breve', 'responsorio_breve'))
        if nombre == 'oracion' and self.hora_id in ('tercia', 'sexta', 'nona'):
            self.abrir_hora('intermedia')
        p = self.abrir_parte(nombre, reusar=reusar)
        if nombre == 'himno':
            if resto and ('Te Deum' in resto or 'Te Deum' in r.texto):
                self.parte['parte'] = 'te_deum'
                v = nueva_variante('rubrica', texto=t)
                self.tomar(r, v)
                self.agregar_variante('rubrica', v)
                return
            if resto:
                v = nueva_variante('rubrica', texto=t)
                self.tomar(r, v)
                self.agregar_variante('rubrica', v)
                return
            self.tomar(r, p)
            self.leer_himnos()
            return
        if nombre == 'lectura_breve':
            v = nueva_variante('lectura_breve', cita=resto)
            self.tomar(r, v)
            nx = self.actual()
            if not resto and nx is not None and nx.c0 == 'R' and nx.solo == {'R'}:
                mm = re.match(r'^((En )?[Tt]iempo (de \w+|pascual)|Para [^0-9]+?)\s+(\S.*)$', espacios(nx.texto))
                if mm:
                    self.etiqueta = {'texto': mm.group(1), 'renglones': [nx]}
                    v['cita'] = mm.group(4)
                    v['_cita_con_etiqueta'] = True
                    self.i += 1
            v['texto'] = self.leer_parrafos(v, uno=True)[0] if True else ''
            self.agregar_variante('lectura_breve', v)
            return
        if nombre == 'preces':
            self.tomar(r, p)
            return
        if nombre in ('primera_lectura', 'segunda_lectura'):
            self.tomar(r, p)
            return
        self.tomar(r, p)

    def _pareja(self, a, b):
        pa = next((p for p in (self.hora or []) if p['parte'] == a), None)
        pb = next((p for p in (self.hora or []) if p['parte'] == b), None)
        za = next((pz for pz in pa['piezas'] if pz['tipo'] == a), None) if pa else None
        zb = next((pz for pz in pb['piezas'] if pz['tipo'] == b), None) if pb else None
        if not za or not zb:
            return False
        return len(za['variantes']) > len(zb['variantes'])

    # himnos
    def leer_himnos(self):
        while True:
            r = self.actual()
            if r is None:
                return
            k = self.clase(r)
            if k in ('romano', 'etiqueta'):
                if self.etiqueta is not None:
                    self.etiqueta = {'texto': self.etiqueta['texto'] + ' ' + r.texto.strip(),
                                     'renglones': self.etiqueta['renglones'] + [r]}
                else:
                    self.etiqueta = {'texto': r.texto.strip(), 'renglones': [r]}
                self.i += 1
                continue
            if k in ('negro', 'blanco') and (k == 'negro' or self.etiqueta is None):
                if k == 'blanco':
                    self.tomar(r, 'blanco'); self.i += 1
                    continue
                v = nueva_variante('himno', estrofas=[], amen=False)
                self.agregar_variante('himno', v)
                self.leer_versos(v)
                continue
            return

    def leer_versos(self, v, dentro_salmo=False):
        """Versos hasta el próximo rojo al margen; estrofas por espacio vertical."""
        estrofas, actual, xs = [], [], []
        primero = True
        opcional = False
        while True:
            r = self.actual()
            if r is None:
                break
            k = self.clase(r)
            if k == 'blanco':
                if actual:
                    estrofas.append(actual); actual = []
                self.tomar(r, v); self.i += 1
                continue
            m = r.m
            cruz = bool(re.match(r'^\x01\s*†\s*\x02', m))
            if dentro_salmo and k == 'rubrica' and re.match(r'^Se (repite|recita)\b.*ant[íi]fona', r.texto.strip()):
                # salmo responsorial del Invitatorio: «Se repite la antífona» entre estrofas
                if actual:
                    estrofas.append(actual); actual = []
                v.setdefault('_rub', []).append({'despues_de_estrofa': len(estrofas), 'texto': espacios(r.texto)})
                self.tomar(r, v); self.i += 1
                continue
            if cruz:                            # «† Mi alma se consume…»: marca roja del salmo
                m = m[re.match(r'^\x01\s*†\s*\x02', m).end():]
                k = 'negro'
            signo = re.match(r'^\x01\s*\+\s*\x02', m)
            if signo:                           # «+ Bendito sea el Señor…»: signo de la cruz
                m = m[signo.end():]
                k = 'negro'
            corchete = re.match(r'^\x01\s*\[\s*\x02', m) and 'k' in r.solo
            estribillo = dentro_salmo and bool(re.match(r'^\x01\s*\(?\s*R\.', m))
            if k != 'negro' and not corchete and not estribillo:
                break
            if not primero and r.gap and r.gap > 18 and actual:
                estrofas.append(actual); actual = []
            primero = False
            extra = {}
            if corchete:                        # estrofas opcionales entre corchetes rojos
                m = m[re.match(r'^\x01\s*\[\s*\x02', m).end():]
                opcional = True
            if re.search(r'\x01\s*\]\s*\x02\s*$', m):
                m = re.sub(r'\x01\s*\]\s*\x02\s*$', '', m)
                extra['opcional'] = True
                extra['_cierra'] = True
                opcional = False
            elif opcional:
                extra['opcional'] = True
            if corchete:
                extra['_abre'] = True
            if cruz:
                extra['cruz'] = True
            if signo:
                extra['signo_cruz'] = True
            if estribillo:                      # «R. Aleluya, (aleluya).» / «(R. Aleluya.)» en el cántico
                mm = re.match(r'^\x01\s*(\()?\s*R\.\s*\x02?', m)
                m = m[mm.end():]
                extra['estribillo'] = True
                if mm.group(1):
                    m = re.sub(r'\x01\s*\)\s*\x02\s*$', '', m)
                    extra['opcional'] = True
                    extra['_paren'] = True
            txt = self.texto_limpio(m, v, 'un verso')
            actual.append({'texto': txt, '_x': r.x, **extra})
            xs.append(r.x)
            self.tomar(r, v)
            self.i += 1
        if actual:
            estrofas.append(actual)
        base = min(xs) if xs else 56.8
        for e in estrofas:
            for vs in e:
                par = vs.pop('_paren', False)
                vs['_marcas'] = ('[' if vs.pop('_abre', False) else '',
                                 (']' if vs.pop('_cierra', False) else '') + (')' if par else ''),
                                 (('(R.' if par else 'R.') if vs.get('estribillo') else '') + ('†' if vs.get('cruz') else '') +
                                 ('+' if vs.get('signo_cruz') else ''))
                d = vs.pop('_x') - base
                vs['sangria'] = 0 if d < 7 else (1 if d < 21 else 2)
        if not dentro_salmo and estrofas:
            ult = estrofas[-1][-1]
            mm = re.search(r'\s*Amén\.?\s*$', ult['texto'])
            if mm:
                v['amen'] = True
                v['_amen_raw'] = ult['texto'][mm.start():].strip()
                ult['texto'] = ult['texto'][:mm.start()].rstrip()
        v['estrofas'] = estrofas
        return estrofas

    # salmos
    def c_salmo(self, r):
        self.i += 1
        cita = espacios(r.texto)
        sid = id_salmo(cita)
        self.leer_salmo(sid, parte=None, r_titulo=r, cita=cita)

    def leer_salmo(self, sid, parte, r_titulo, cita=None):
        if self.parte is None or self.parte['parte'] != 'salmodia':
            self.abrir_parte('salmodia', reusar=True)
        v = nueva_variante('salmo', salmo=sid, parte=parte)
        self.tomar(r_titulo, v)
        self.agregar_variante('salmo', v, forzar_nueva=True)
        lib = self.salmos.setdefault(sid, {'id': sid, 'cita': cita, 'titulo': None,
                                           'sentencia': None, 'partes': {},
                                           'pdf': r_titulo.pdf, 'impresa': r_titulo.impresa,
                                           '_raw': []})
        lib['_raw'].append(r_titulo)
        # subtítulo y sentencia
        r = self.actual()
        es_sub = lambda x: (x is not None and x.c0 == 'R' and x.solo == {'R'} and x.texto.strip().isupper() and
                            len(x.texto.strip()) > 3 and not re.fullmatch(r'[IVX]+', x.texto.strip()))
        if es_sub(r):
            tit = [r.texto]
            self.tomar(r, lib); lib['_raw'].append(r); self.i += 1
            while es_sub(self.actual()) and self.actual().gap <= 16.5:   # subtítulo en dos renglones
                x = self.actual(); tit.append(x.texto); self.tomar(x, lib); lib['_raw'].append(x); self.i += 1
            lib['titulo'] = espacios(' '.join(tit))
        sent = []
        es_sent = lambda x: x is not None and ((self.clase(x) == 'remite' and x.x > 60) or
                                               (x.c0 == 'k' and 'Italic' in x.primer()['f'] and x.x > 150))
        for n_l in (1, 2, 3):
            # tomo IV: la sentencia va en negro, sangrada, con la cita entre paréntesis al final
            xs_ = self.R[self.i:self.i + n_l]
            sig_ = self.R[self.i + n_l] if self.i + n_l < len(self.R) else None
            if (len(xs_) == n_l and all(x.c0 == 'k' and x.solo == {'k'} and x.x > 60 for x in xs_) and
                    not es_sent(xs_[0]) and re.search(r'\([^()]+\)\.?\s*$', ' '.join(x.texto.strip() for x in xs_)) and
                    sig_ is not None and sig_.c0 == 'R'):
                for x0 in xs_:
                    sent.append(plano(x0.m)); self.tomar(x0, lib); lib['_raw'].append(x0); self.i += 1
                break
        while es_sent(self.actual()):
            rr = self.actual(); sent.append(plano(rr.m)); self.tomar(rr, lib); lib['_raw'].append(rr); self.i += 1
        if sent:
            st = unir_lineas(sent)
            mm = re.search(r'\s*\(([^()]*)\)\.?\s*$', st)
            lib['sentencia'] = {'texto': st[:mm.start()] if mm else st, 'cita': mm.group(1) if mm else None}
        tmp = {'_raw': []}
        estrofas = self.leer_versos(tmp, dentro_salmo=True)
        if tmp.get('_rub'):
            lib['rubricas'] = tmp['_rub']
        if estrofas and estrofas[-1] and estrofas[-1][0]['texto'].startswith('Gloria al Padre'):
            estrofas.pop()              # «Gloria al Padre…» al final del salmo: fórmula fija, no se copia
            lib['gloria'] = True
        for rr in tmp['_raw']:
            rr.dueno = lib
            lib['_raw'].append(rr)
        self.ultimo_salmo = sid
        nx = self.actual()
        if not estrofas and parte is None and nx is not None and self.clase(nx) == 'romano':
            # «Salmo 117» seguido de «I»: el título va a la biblioteca, las partes son las piezas
            pz = self.parte['piezas'][-1]
            if pz['variantes'] and pz['variantes'][-1] is v:
                self.parte['piezas'].pop()
            for rr in v['_raw']:
                rr.dueno = lib
            return
        lib['partes'][parte or ''] = estrofas
        v['_lib'] = lib

    # antífonas
    def c_ant(self, r):
        m = re.sub(r'^\s*(\x01\s*)', r'\1', r.m.lstrip())
        mm = re.match(r'^\x01\s*(Ant\.(?:\s*(\d)\.)?)\s*\x02?', m)
        if not mm:  # «Ant. 1. texto» todo en rojo
            mm = re.match(r'^\x01\s*(Ant\.(?:\s*(\d)\.)?)\s*', m)
        if not mm:
            self.avisos.append((r, f'«Ant.» con forma inesperada: {r.texto[:40]}'))
            self.c_rubrica(r)
            return
        rot = mm.group(1)
        num = int(mm.group(2)) if mm.group(2) else None
        resto = m[mm.end():]
        if resto.startswith('\x02'):
            resto = resto[1:]
        if not resto.startswith('\x01') and '\x02' in resto and '\x01' not in resto.split('\x02')[0]:
            # el texto también quedó en rojo: se marca
            pass
        self.i += 1
        # repetición de la antífona después del salmo
        if num is None and self.parte and self.parte['parte'] == 'salmodia' and self.ult_antifona is not None \
                and self.parte['piezas'] and self.parte['piezas'][-1]['tipo'] == 'salmo':
            rep = {'_raw': [r], '_tipo': 'repeticion'}
            r.dueno = rep
            if self.etiqueta is not None:   # «Tiempo pascual:» + «Ant. …» repetida
                for rr in self.etiqueta['renglones']:
                    rr.dueno = rep
                    rep['_raw'].append(rr)
                rep['_etiqueta'] = self.etiqueta['texto']
                self.etiqueta = None
            txt = self.leer_texto_simple(rep, resto)
            t2, tp, _ = self.separar_tp(txt)
            self.ult_antifona['_repeticion'] = espacios(plano(t2))
            self.ult_antifona.setdefault('_rep_raw', []).append(rep)
            return
        if self.parte is None or self.parte['parte'] in ('himno',) or (
                self.hora_id in ('tercia', 'sexta', 'nona') and self.parte['parte'] != 'salmodia'):
            self.abrir_parte('salmodia' if self.hora_id not in ('invitatorio',) else 'antifona')
        if self.hora_id == 'invitatorio' and self.parte['parte'] != 'antifona':
            self.abrir_parte('antifona')
        v = nueva_variante('antifona', numero=num, texto=None, tp_aleluya=False, _rotulo=rot)
        self.tomar(r, v)
        txt = self.leer_texto_simple(v, resto)
        mmc = re.search(r'\s*†\s*(\x02)?\s*$', txt)
        if mmc:                                 # «… ejércitos! †»: marca roja de la antífona
            txt = txt[:mmc.start()] + (mmc.group(1) or '')
            v['cruz'] = True
        t2, tp, tpraw = self.separar_tp(txt)
        v['texto'] = self.texto_limpio(t2, v, 'una antífona')
        v['tp_aleluya'] = tp
        v['_tp_raw'] = tpraw
        self.agregar_variante('antifona', v)
        self.ult_antifona = v

    def c_antifona_rotulo(self, r):
        self.i += 1
        if self.hora_id == 'invitatorio':
            self.abrir_parte('antifona')
        self.tomar(r, 'rótulo Antífona')
        self._rot_ant = r
        mm = re.search(r'(\d)$', r.texto.strip())
        self._rot_num = int(mm.group(1)) if mm else None

    def c_negro(self, r):
        """Texto negro suelto: según la parte en curso."""
        p = self.parte['parte'] if self.parte else None
        if self.modo == 'ordinario':
            if self.hora is None:
                self.abrir_hora('antes_del_oficio')
            if self.parte is None:
                self.abrir_parte('texto')
            self.leer_texto_generico(r)
            return
        en_salmodia = p == 'salmodia' and (getattr(self, '_rot_ant', None) is not None or self.etiqueta is not None)
        if p in ('cantico_evangelico', 'antifona') or en_salmodia or (p is None and self.hora_id == 'invitatorio'):
            if p is None:
                self.abrir_parte('antifona')
            num = None
            if en_salmodia:   # «Antífona 1» + «Tiempo de Cuaresma: …» / «Tiempo pascual: …»
                num = getattr(self, '_rot_num', None)
                if num is None:
                    ult = next((pz for pz in reversed(self.parte['piezas']) if pz['tipo'] == 'antifona'), None)
                    num = ult['variantes'][0].get('numero') if ult else None
            v = nueva_variante('antifona', numero=num, texto=None, tp_aleluya=False, _rotulo='')
            if getattr(self, '_rot_ant', None) is not None:
                v['_rotulo'] = self._rot_ant.texto.strip()
                self._rot_num = None
                v['_rot_n'] = self._rot_ant.n
                self._rot_ant.dueno = v
                v['_raw'].append(self._rot_ant)
                self._rot_ant = None
            self.tomar(r, v)
            self.i += 1
            txt = self.leer_texto_simple(v, r.m)
            t2, tp, tpraw = self.separar_tp(txt)
            v['texto'] = self.texto_limpio(t2, v, 'una antífona')
            v['tp_aleluya'] = tp
            v['_tp_raw'] = tpraw
            self.agregar_variante('antifona', v)
            self.ult_antifona = v
            return
        if p == 'himno':
            self.leer_himnos()
            return
        if p == 'preces':
            self.leer_preces()
            return
        if p in ('primera_lectura', 'segunda_lectura'):
            self.leer_lectura()
            return
        if self.hora_id == 'oficio' and re.match(r'^De(l| la| las| los)\b', r.texto.strip()) and \
                ('R' in r.solo or (self.sig() is not None and self.sig().c0 == 'R')):
            # el libro omite el rótulo PRIMERA/SEGUNDA LECTURA
            n = 'segunda_lectura' if any(x['parte'] == 'primera_lectura' for x in self.hora) else 'primera_lectura'
            self.abrir_parte(n, reusar=True)
            self.leer_lectura()
            v = self.parte['piezas'][-1]['variantes'][-1] if self.parte['piezas'] else None
            pz = next((x for x in self.parte['piezas'] if x['tipo'] == 'lectura'), None)
            if pz:
                pz['variantes'][-1]['revisar'] = True
                pz['variantes'][-1].setdefault('_notas', []).append('el libro no trae el rótulo de la lectura en este tomo')
            return
        if p == 'lectura_breve' and self.etiqueta is not None:
            # «O bien:» y otra lectura breve sin cita
            v = nueva_variante('lectura_breve', cita=None, _sin_rotulo=True)
            v['texto'] = self.texto_limpio(self.leer_parrafos(v, uno=True)[0], v, 'una lectura breve')
            self.agregar_variante('lectura_breve', v)
            return
        if p == 'oracion':
            v = nueva_variante('oracion')
            v['texto'] = self.texto_limpio(self.leer_parrafos(v, uno=True)[0], v, 'una oración')
            self.agregar_variante('oracion', v)
            return
        self.avisos.append((r, f'texto negro sin pieza (parte {p})'))
        v = nueva_variante('texto', texto=espacios(r.texto), revisar=True)
        self.tomar(r, v)
        self.i += 1
        self.agregar_variante('texto', v)

    def leer_parrafos(self, v, uno=False):
        """Párrafos de prosa hasta el próximo renglón que no sea negro."""
        pars, actual = [], []
        while True:
            r = self.actual()
            if r is None:
                break
            k = self.clase(r)
            if k == 'blanco':
                if actual and not uno:
                    pars.append(actual); actual = []
                self.tomar(r, v); self.i += 1
                continue
            if k != 'negro':
                break
            nuevo = r.x > 62 or (r.gap and r.gap > 18)
            if actual and nuevo:
                if uno and not (r.gap and r.gap > 30):
                    pass
                elif uno:
                    break
                else:
                    pars.append(actual); actual = []
            actual.append(r.m)
            self.tomar(r, v)
            self.i += 1
        if actual:
            pars.append(actual)
        out = [self.texto_limpio(unir_lineas(p, self.cortes), v, 'un párrafo') for p in pars]
        return out or ['']

    # V./R.
    def c_v(self, r):
        p = self.parte['parte'] if self.parte else None
        if p == 'responsorio_breve' or (p is None and False):
            self.leer_responsorio_breve()
            return
        if p in ('primera_lectura', 'segunda_lectura') and self.parte['piezas'] and \
                self.parte['piezas'][-1]['tipo'] == 'responsorio':
            pass
        # versículo inicial de la hora, versículo (oficio, hora intermedia), conclusión
        if p is None:
            self.abrir_parte('introduccion')
        elif p not in ('conclusion', 'introduccion'):
            self.abrir_parte('versiculo')
        v = nueva_variante('versiculo')
        self.tomar(r, v); self.i += 1
        v['v'] = self.leer_texto_simple(v, re.sub(r'^\x01\s*V\.\s*\x02?', '', r.m))
        rr = self.actual()
        if rr is not None and self.clase(rr) == 'r':
            self.tomar(rr, v); self.i += 1
            v['r'] = self.leer_texto_simple(v, re.sub(r'^\x01\s*R\.\s*\x02?', '', rr.m))
        else:
            v['r'] = None
            v['revisar'] = True
            v.setdefault('_notas', []).append('versículo sin R.')
        for c in ('v', 'r'):
            if v[c] is not None:
                t2, tp, tpraw = self.separar_tp(v[c])
                v[c] = self.texto_limpio(t2, v, 'un versículo')
                mm = re.search(r'\s*Gloria al Padre\. Como era\.( Amén\.)?', v[c])
                if mm:
                    v['gloria'] = True
                    v['_gloria_raw'] = mm.group(0)
                    resto = v[c][mm.end():].strip()
                    v[c] = v[c][:mm.start()].rstrip()
                    if resto:
                        v['despues_gloria'] = resto
                if tp:
                    v['tp_aleluya'] = True
                    v.setdefault('_tp_raw', {})[c] = tpraw
        self.agregar_variante('versiculo', v)

    def c_r(self, r):
        self.avisos.append((r, 'R. suelto'))
        v = nueva_variante('texto', texto=espacios(r.texto), revisar=True)
        self.tomar(r, v); self.i += 1
        self.agregar_variante('texto', v)

    def leer_vr(self, v):
        """Lista de pares (V|R, texto) consecutivos."""
        out = []
        while True:
            r = self.actual()
            if r is None or self.clase(r) not in ('v', 'r'):
                break
            letra = 'V' if self.clase(r) == 'v' else 'R'
            self.tomar(r, v); self.i += 1
            txt = self.leer_texto_simple(v, re.sub(r'^\x01\s*[VR]\.\s*\x02?', '', r.m))
            out.append((letra, txt))
        return out

    def leer_responsorio_breve(self):
        v = nueva_variante('responsorio_breve')
        pares = self.leer_vr(v)
        seq = [l for l, _ in pares]
        tx = [t for _, t in pares]
        notas = []
        if seq[:4] == ['V', 'R', 'V', 'R']:
            v['v1'], v['r1'], v['v2'], v['r2'] = [self.texto_limpio(t, v, 'el responsorio breve') for t in tx[:4]]
        else:
            notas.append(f'secuencia V/R inesperada: {seq}')
        v['gloria'] = False
        if len(tx) >= 6 and RE_GLORIA_V.match(plano(tx[4]).strip()):
            v['gloria'] = True
            v['_gloria_raw'] = [plano(tx[4]), plano(tx[5])]
            if norm_item(tx[5]) != norm_item(v.get('r1', '')):
                notas.append('el R. después del Gloria no repite el primer R.')
        elif len(tx) != 4:
            notas.append(f'{len(tx)} renglones V/R')
        if notas:
            v['revisar'] = True
            v.setdefault('_notas', []).extend(notas)
        if self.etiqueta is None and self._pareja('lectura_breve', 'responsorio_breve'):
            pz = next(pz for pz in self.parte['piezas'] if pz['tipo'] == 'responsorio_breve')
            v['_fuente'] = {'tomo': self.tomo}
            pz['variantes'].append(v)
        else:
            pz = self.agregar_variante('responsorio_breve', v)
        self._copiar_pareja('lectura_breve', pz, v)

    def _copiar_pareja(self, parte_a, pz, v):
        pa = next((p for p in self.hora if p['parte'] == parte_a), None)
        za = next((x for x in pa['piezas'] if x['tipo'] == parte_a), None) if pa else None
        if za:
            va = za['variantes']
            if len(va) > 1 and len(pz['variantes']) <= len(va):
                par = va[len(pz['variantes']) - 1]
                v['_par'] = par
                if 'etiqueta' in par and 'etiqueta' not in v:
                    v['etiqueta'] = par['etiqueta']
                    v['_etiqueta_heredada'] = True

    # lecturas del Oficio
    def leer_lectura(self):
        v = nueva_variante('lectura', orden=1 if self.parte['parte'] == 'primera_lectura' else 2)
        self.agregar_variante('lectura', v)
        enc = []
        while True:
            r = self.actual()
            if r is None or self.clase(r) != 'negro':
                break
            self.tomar(r, v); self.i += 1
            m = r.m
            if '\x01' in m:  # cita bíblica en rojo al final
                negro, _, rojo = m.partition('\x01')
                enc.append(negro)
                v['cita'] = espacios(plano(rojo))
                break
            enc.append(m)
            nx = self.actual()
            if nx is None or self.clase(nx) != 'negro' or nx.x > 62:
                break
        v['encabezado'] = espacios(plano(' '.join(enc)))
        fuente = []
        while self.actual() is not None and self.clase(self.actual()) in ('fuente', 'rubrica') and \
                (not fuente and self.clase(self.actual()) == 'fuente' or fuente and not fuente[-1].rstrip().endswith(')')):
            r = self.actual(); self.tomar(r, v); self.i += 1
            fuente.append(plano(r.m))
        if fuente:
            v['fuente'] = espacios(' '.join(fuente))
        tit = []
        while self.actual() is not None and self.clase(self.actual()) == 'mayusculas':
            r = self.actual(); self.tomar(r, v); self.i += 1
            tit.append(r.texto)
        v['titulo'] = espacios(' '.join(tit)) if tit else None
        v['parrafos'] = self.leer_parrafos(v)
        if not tit:
            v['revisar'] = True
            v.setdefault('_notas', []).append('lectura sin título')

    def c_responsorio(self, r):
        v = nueva_variante('responsorio', cita=espacios(r.texto.strip()[len('Responsorio'):]) or None)
        self.tomar(r, v); self.i += 1
        if self.etiqueta is not None:
            v['etiqueta'] = self.etiqueta['texto']
            v['_et_n'] = self.etiqueta['renglones'][0].n if self.etiqueta['renglones'] else None
            for rr in self.etiqueta['renglones']:
                self.tomar(rr, v)
            v['_cuando'] = condicion(self.etiqueta['texto'])[0]
            self.etiqueta = None
        pares = self.leer_vr(v)
        notas = []
        seq = [l for l, _ in pares]
        if seq[:3] == ['R', 'V', 'R']:
            r1 = pares[0][1]
            if '\x01*\x02' in r1.replace(' ', '') or '*' in plano(r1):
                a, _, b = plano(r1).partition('*')
                v['r'] = [self.texto_limpio(a, v, 'el responsorio'), self.texto_limpio(b, v, 'el responsorio')]
            else:
                v['r'] = [self.texto_limpio(r1, v, 'el responsorio'), None]
                notas.append('responsorio sin «*»')
            v['v'] = self.texto_limpio(pares[1][1], v, 'el responsorio')
            v['_rep'] = plano(pares[2][1])
            t2, tp, tpraw = self.separar_tp(v['r'][1] or '')
            rep2, tp2, _ = self.separar_tp(pares[2][1])
            sin_tp = lambda x: re.sub(r'\s*\(T\. ?P\.\s*Aleluya\.?\)\.?\s*$', '', plano(x))
            if norm_item(sin_tp(rep2)) != norm_item(sin_tp(t2)):
                notas.append('la repetición del R. no coincide con su segunda mitad')
        else:
            notas.append(f'secuencia R/V inesperada en el libro: {seq}; se guarda tal cual')
            v['secuencia'] = [{'rotulo': l + '.', 'texto': self.texto_limpio(t, v, 'el responsorio')} for l, t in pares]
        # (T. P. Aleluya.) al final de cada mitad
        if v.get('r') and v['r'][1]:
            t2, tp, tpraw = self.separar_tp('\x01' + v['r'][1] if False else v['r'][1])
            mm = re.search(r'\s*\(T\. ?P\. ?Aleluya\.?\)\.?\s*$', v['r'][1])
            if mm:
                v['_tp_raw'] = mm.group(0).strip()
                v['r'][1] = v['r'][1][:mm.start()].rstrip()
                v['tp_aleluya'] = True
        if notas:
            v['revisar'] = True
            v.setdefault('_notas', []).extend(notas)
        # pareja: la lectura a la que responde
        lec = next((pz for pz in reversed(self.parte['piezas']) if pz['tipo'] == 'lectura'), None) if self.parte else None
        hay = next((pz for pz in self.parte['piezas'] if pz['tipo'] == 'responsorio'), None) if self.parte else None
        if hay is None:
            pz = {'tipo': 'responsorio', 'variantes': []}
            self.parte['piezas'].append(pz)
        else:
            pz = hay
        v['_fuente'] = {'tomo': self.tomo}
        pz['variantes'].append(v)
        if lec is not None:
            par = lec['variantes'][-1]
            v['_par'] = par
            if 'etiqueta' in par and 'etiqueta' not in v:
                v['etiqueta'] = par['etiqueta']
                v['_etiqueta_heredada'] = True

    # preces
    def leer_preces(self):
        v = nueva_variante('preces', introduccion=None, respuesta=[], intenciones=[],
                           libres_despues_de=None, final=None)
        self.agregar_variante('preces', v)
        intro = []
        while True:
            r = self.actual()
            if r is None or self.clase(r) != 'negro':
                break
            self.tomar(r, v); self.i += 1
            intro.append(r.m)
            if plano(r.m).rstrip().endswith(':'):
                break
        v['introduccion'] = self.texto_limpio(unir_lineas(intro), v, 'la introducción de las preces')
        r = self.actual()
        if r is not None and self.clase(r) == 'negro':
            self.tomar(r, v); self.i += 1
            v['respuesta'].append({'etiqueta': None, 'texto': espacios(plano(r.m))})
        while True:
            r = self.actual()
            if r is None:
                break
            k = self.clase(r)
            if k == 'etiqueta' and not v['intenciones']:
                self.c_etiqueta(r)
                continue
            if k == 'blanco':
                self.tomar(r, v); self.i += 1
                continue
            if k == 'rubrica' and plano(r.texto).startswith('Se pueden añadir'):
                self.tomar(r, v); self.i += 1
                v['libres_despues_de'] = len(v['intenciones'])
                v['_libres_raw'] = espacios(r.texto)
                continue
            if k == 'negro':
                prim = [r.m]
                self.tomar(r, v); self.i += 1
                while self.actual() is not None and self.clase(self.actual()) == 'negro' and \
                        self.actual().gap <= 16.5:
                    rr = self.actual(); self.tomar(rr, v); self.i += 1; prim.append(rr.m)
                texto = self.texto_limpio(unir_lineas(prim), v, 'una intención')
                seg = None
                if self.actual() is not None and self.clase(self.actual()) == 'guion':
                    rr = self.actual(); self.tomar(rr, v); self.i += 1
                    sg = [re.sub(r'^\x01\s*—\s*\x02?', '', rr.m)]
                    while self.actual() is not None and self.clase(self.actual()) == 'negro' and \
                            self.actual().gap <= 16.5 and not re.search(r'[.!?»]\s*$', plano(sg[-1])):
                        r3 = self.actual(); self.tomar(r3, v); self.i += 1; sg.append(r3.m)
                    seg = self.texto_limpio(unir_lineas(sg), v, 'una intención')
                if seg is None and re.search(r'Padre\s+nuestro', texto):
                    v['final'] = texto
                    v['_cerrada'] = True
                    break
                v['intenciones'].append({'primera': texto, 'segunda': seg})
                if seg is None:
                    v['revisar'] = True
                    v.setdefault('_notas', []).append(f'intención sin segunda mitad: «{texto[:50]}»')
                continue
            break
        v['_cerrada'] = True

    # rúbricas
    def c_rubrica(self, r):
        t0 = espacios(r.texto)
        mm = re.match(r'^(O bien:|(?:En )?[Tt]iempo (?:de \w+|pascual):?)\s*(\S.*)$', t0)
        if mm and self.parte is not None and self.parte['parte'] == 'lectura_breve' and r.solo == {'R'}:
            # «O bien: Ag 2, 6a. 7.9» → otra lectura breve
            self.etiqueta = {'texto': mm.group(1), 'renglones': []}
            v = nueva_variante('lectura_breve', cita=mm.group(2), _cita_con_etiqueta=False, _et_linea=True)
            self.tomar(r, v); self.i += 1
            v['texto'] = self.leer_parrafos(v, uno=True)[0]
            self.agregar_variante('lectura_breve', v)
            return
        if mm and 'B' in r.solo and self.parte is not None and self.parte['parte'] == 'himno':
            # «O bien: Finísimo fue el lino.» → opción que remite a otro himno
            self.etiqueta = {'texto': mm.group(1), 'renglones': []}
            ref = espacios(''.join(s['t'] for s in r.segs if s['c'] == 'B'))
            v = nueva_variante('himno', estrofas=[], amen=False, remite='himnos/' + slug(ref), _ref=ref, _linea=t0, _et_linea=True)
            self.tomar(r, v); self.i += 1
            self.agregar_variante('himno', v)
            return
        lineas = [r]
        self.i += 1
        while True:
            nx = self.actual()
            if nx is None or nx.vacio:
                break
            ult = plano(lineas[-1].m).rstrip()
            sigue_minus = nx.c0 in ('R', 'B') and nx.texto.strip()[:1].islower()
            if nx.c0 in ('R', 'B') and self.clase(nx) in ('rubrica', 'remite', 'mayusculas', 'negro') and \
                    nx.gap <= 16.5 and (not re.search(r'[.:]$', ult) or sigue_minus):
                lineas.append(nx); self.i += 1
                continue
            if nx.c0 == 'k' and nx.gap <= 16.5 and plano(lineas[-1].m).rstrip().endswith(('el himno', 'Te')):
                lineas.append(nx); self.i += 1
                continue
            break
        m = ''.join(l.m if j == 0 else ' ' + l.m for j, l in enumerate(lineas))
        texto = espacios(plano(m))
        nx = self.actual()
        if (self.modo == 'ordinario' and texto.endswith(':') and nx is not None and self.clase(nx) == 'negro' and
                re.search(r'\b(se dice|Versi[óo]n|Cuando|[Tt]iempo|Adviento|Navidad|Cuaresma|Pascua|Semana Santa|[Ee]n lat[íi]n|'
                          r'Epifan[íi]a|diciembre|enero|[Dd]ía \d+|Triduo)\b', texto)):
            # «En el Oficio dominical y ferial del tiempo de Adviento, … se dice:» → condición del texto que sigue
            self.etiqueta = {'texto': texto, 'renglones': lineas}
            lineas[0].es_et = True
            return
        azules = [espacios(x) for x in re.findall(r'\x03(.*?)\x04', limpiar_marcas(m))]
        v = nueva_variante('rubrica', texto=texto)
        for l in lineas:
            self.tomar(l, v)
        v['_azul'] = azules
        destino = self.parte_de_rubrica(texto)
        if destino == 'comun':
            v['_fuente'] = {'tomo': self.tomo}
            self.comun['rubricas'].append(v)
            return
        if destino:
            if destino == 'intermedia_oracion':
                self.abrir_hora('intermedia')
                destino = 'oracion'
            self.abrir_parte(destino, reusar=destino in ('salmodia', 'oracion', 'segunda_lectura', 'lectura_breve'))
        self.agregar_variante('rubrica', v, forzar_nueva=True)

    def parte_de_rubrica(self, t):
        if self.hora is None and self.modo == 'ordinario':
            self.abrir_hora('antes_del_oficio')
            return 'texto'
        if self.modo == 'ordinario':
            return None          # en el Ordinario la rúbrica queda en la parte donde está
        if self.hora is None:
            return 'comun'
        h = self.hora_id
        if re.match(r'^(La )?[Oo]ración como en', t):
            return 'intermedia_oracion' if h in ('tercia', 'sexta', 'nona') else 'oracion'
        if re.match(r'^(Oración propia|Se dice (la oración|una de las siguientes oraciones))', t):
            return 'oracion'
        if 'Te Deum' in t:
            return 'te_deum'
        if re.match(r'^(El|Los) himnos?\b', t):
            return 'himno'
        if 'vigilia' in t:
            return 'vigilia'
        if h == 'invitatorio':
            return 'salmo'
        if t.startswith('El Oficio de Santa María en sábado'):
            return 'comun'
        if t.startswith('Después de la oración conclusiva') or t.startswith('Cuando preside'):
            return 'conclusion'
        if t.startswith('Las antífonas'):
            return 'salmodia'
        if t.startswith('La lectura breve y el responsorio breve'):
            return 'lectura_breve'
        if t.startswith('Cuando se celebra como solemnidad'):
            return 'salmodia'
        if h in ('tercia', 'sexta', 'nona') and 'salmodia complementaria' in t:
            return 'salmodia'
        return None

    def c_remite(self, r):
        """Línea solo azul: «Magnificat», «Benedictus»."""
        t = espacios(r.texto)
        pz = self.parte['piezas'][-1] if self.parte and self.parte['piezas'] else None
        if pz is not None:
            pz.setdefault('_remite_raw', []).append(t)
            pz['remite'] = remite_de(t)
            pz.setdefault('_raw_remite', []).append(r)
            r.dueno = {'_tipo': 'remite', '_raw': [r], 'texto': t}
        else:
            self.avisos.append((r, 'remisión azul sin pieza'))
            r.dueno = 'remite suelto'
        self.i += 1

    def c_fuente(self, r):
        self.c_rubrica(r)

    def c_mayusculas(self, r):
        self.c_rubrica(r)

    def c_asterisco(self, r):
        self.c_rubrica(r)

    def c_guion(self, r):
        self.avisos.append((r, '«—» fuera de las preces'))
        v = nueva_variante('texto', texto=espacios(r.texto), revisar=True)
        self.tomar(r, v); self.i += 1
        self.agregar_variante('texto', v)


# ──────────────────────────────── remisiones ────────────────────────────────
def remite_de(t, comun='virgen', hora=None):
    """Remisión normalizada a partir del texto de una rúbrica o de un azul."""
    tl = t.lower()
    out = []
    if re.search(r'\bmagn[ií]ficat\b', tl):
        out.append('ordinario/magnificat')
    if re.search(r'\bbenedictus\b', tl):
        out.append('ordinario/benedictus')
    if 'como en las ii vísperas' in tl or 'como en las ii vísperas' in tl:
        out.append(f'{comun}/visperas2/himno')
    if re.search(r'oración como en (las )?laudes', tl):
        out.append(f'{comun}/laudes/oracion')
    if 'apéndice iv' in tl:
        out.append('apendices/himnos-latinos')
    if 'te deum' in tl:
        out.append('ordinario/te-deum')
    if 'vigilia' in tl:
        out.append('apendices/vigilias/santa-maria-virgen')
    if 'salmo invitatorio' in tl or 'salmo del invitatorio' in tl:
        out.append('ordinario/invitatorio/salmodia')
        for n in re.findall(r'salmo (\d+)', tl):
            out.append(f'salmos/salmo-{n}')
    if 'aquí se dice el salmo 94' in tl:
        out.append('salmos/salmo-94')
    if 'domingo de la i semana' in tl:
        out.append('salterio/semana-1/domingo/laudes/salmodia')
    if 'salmodia complementaria' in tl:
        out.append('salterio/salmodia-complementaria')
        for n in re.findall(r'puede tomarse el salmo (\d+)', tl):
            out.append(f'salmos/salmo-{n}')
    if 'sábado correspondiente' in tl:
        out.append(f'salterio/sabado-correspondiente/{hora or ""}'.rstrip('/'))
    if 'común de santa maría virgen' in tl and 'segunda lectura' in tl:
        out.append('virgen/oficio/segunda_lectura')
    if re.search(r'proclo|guerrico|crisóstomo|lumen gentium', tl) and 'tomarse' in tl:
        out.append('santa-maria-sabado/oficio/segunda_lectura')
    if 'escoger de entre los siguientes' in tl:
        out.append('santa-maria-sabado/laudes/lectura_breve')
    for rx, cid in (('pastores', 'pastores'), ('santos varones', 'santos-varones'), ('santas mujeres', 'santas-mujeres'),
                    ('vírgenes', 'virgenes'), ('mártires', 'martires'), ('doctores', 'doctores'),
                    ('apóstoles', 'apostoles'), ('dedicación', 'dedicacion')):
        if re.search(r'com[úu]n de (santos |santas |la )?' + rx, tl):
            out.append(f'comunes/{cid}')
    if 'oficio de santa maría en sábado se encuentra' in tl:
        out.append('propio-del-tiempo/santa-maria-sabado')
    if 'ordinario' in tl and 'conclusión' in tl:
        out.append('ordinario/conclusion')
    if 'apéndice iii' in tl:
        out.append('apendices/apendice-iii')
    if not out:
        return None
    alias = {'ordinario/te-deum': 'ordinario/oficio/te_deum',
             'ordinario/magnificat': 'ordinario/visperas/cantico_evangelico',
             'ordinario/benedictus': 'ordinario/laudes/cantico_evangelico'}
    out = [alias.get(x, x) for x in out]
    out = list(dict.fromkeys(out))
    return out[0] if len(out) == 1 else out


# ─────────────────────────── condiciones (cuando) ───────────────────────────
TIEMPOS = [
    (r'^(En )?[Tt]iempo de Adviento', 'adviento'),
    (r'^(En )?[Tt]iempo de Navidad desde la Epifan', 'navidad-desde-epifania'),
    (r'^(En )?[Tt]iempo de Navidad hasta la Epifan', 'navidad-hasta-epifania'),
    (r'^(En )?[Tt]iempo de Navidad', 'navidad'),
    (r'^(En )?[Tt]iempo de [Cc]uaresma', 'cuaresma'),
    (r'^(En )?[Tt]iempo pascual', 'pascua'),
    (r'^(En )?[Tt]iempo [Oo]rdinario', 'ordinario'),
]


PARA = [  # (patrón, valores) del más largo al más corto; ampliado según el libro
    (r'papa u obispo', ['papa', 'obispo']), (r'(las )?m[áa]rtires v[íi]rgenes', ['martires-virgenes']),
    (r'las santas mujeres', ['varias-santas']), (r'fundador de una iglesia', ['fundador']),
    (r'varias santas v[íi]rgenes', ['varias-virgenes']), (r'virgen y m[áa]rtir|m[áa]rtir virgen', ['virgen', 'martir']),
    (r'varios m[áa]rtires', ['varios-martires']), (r'mujer m[áa]rtir|una m[áa]rtir', ['martir', 'mujer']),
    (r'un solo m[áa]rtir|un m[áa]rtir', ['martir']), (r'varias santas mujeres|varias santas', ['varias-santas']),
    (r'varios santos', ['varios-santos']), (r'santa virgen', ['virgen']),
    (r'actividad caritativa', ['caridad']), (r'obras de misericordia', ['misericordia']),
    (r'matrimonio', ['matrimonio']), (r'papa', ['papa']), (r'obispo', ['obispo']),
    (r'presb[íi]tero', ['presbitero']), (r'pastor', ['pastor']), (r'misionero', ['misionero']),
    (r'abad', ['abad']), (r'monja', ['monja']), (r'religiosa', ['religiosa']), (r'religioso', ['religioso']),
    (r'educadora', ['educadora']), (r'educador', ['educador']),
    (r'santa mujer|mujer santa|una santa', ['santa']), (r'un santo', ['santo']),
]
TIEMPOS_TXT = [(r'adviento', 'adviento'), (r'navidad desde (la )?epifan', 'navidad-desde-epifania'),
               (r'navidad hasta (la )?epifan', 'navidad-hasta-epifania'), (r'navidad', 'navidad'),
               (r'cuaresma', 'cuaresma'), (r'pascua', 'pascua'), (r'tiempo ordinario', 'ordinario')]


def condicion(etiqueta):
    """(cuando, es_opcion, conocida) a partir de la etiqueta roja literal."""
    if etiqueta is None:
        return {}, False, True
    e = etiqueta.rstrip(':').strip()
    if re.fullmatch(r'[IVX]+', e) or re.match(r'^(Primera|Segunda|Tercera|Cuarta|Quinta) fórmula$', e):
        return {}, True, True
    es_op = bool(re.match(r'^O bien\b', e, re.I))
    resto = re.sub(r'^O bien\b,?\s*(esta otra|estas otras)?,?\s*', '', e, flags=re.I).lower()
    if not resto:
        return {}, True, True
    c = {}
    if re.search(r'\btiempo\b', resto) or re.match(r'^(en )?tiempo', resto):
        ts = []
        for rx, val in TIEMPOS_TXT:
            if re.search(rx, resto) and not (val == 'navidad' and 'navidad-' in ' '.join(ts)):
                ts.append(val)
        if ts:
            c['tiempo'] = ts[0] if len(ts) == 1 else ts
    if re.search(r'\bpara\b|\bse trata de\b', resto):
        tx = resto
        vals = []
        for rx, vs in PARA:
            if re.search(rx, tx):
                vals += [x for x in vs if x not in vals]
                tx = re.sub(rx, ' ', tx)
        # «un santo», «una santa» solo cuentan si no hay otra categoría («un santo presbítero» → presbitero)
        neutras = {'matrimonio', 'caridad', 'misericordia'}   # aquí «santo»/«santa» sí distingue
        if any(x not in neutras | {'santo', 'santa'} for x in vals):
            vals = [x for x in vals if x not in ('santo', 'santa')]
        if vals:
            c['para'] = vals
    if re.search(r'am[ée]rica latina|latinoamericana', resto):
        c['region'] = 'america-latina'
    if re.search(r'espa[ñn](a|ol)', resto):
        c['region'] = 'espana'
    conocida = bool(c) and not re.search(r'cuando el oficio|especialmente', resto)
    return c, es_op, conocida


# ─────────────────────────────── unificación ────────────────────────────────
def clave(v):
    t = v['_tipo']
    if t == 'antifona':
        return norm_item(v.get('texto') or '')
    if t == 'salmo':
        return f"{v['salmo']}|{v.get('parte')}"
    if t == 'himno':
        return norm_lista(vs['texto'] for e in v['estrofas'] for vs in e)
    if t == 'lectura_breve':
        return norm_item(v.get('texto') or '')
    if t == 'responsorio_breve':
        return norm_lista([v.get('v1'), v.get('r1'), v.get('v2'), v.get('r2')])
    if t == 'versiculo':
        return norm_lista([v.get('v'), v.get('r')])
    if t == 'lectura':
        return norm_lista(v.get('parrafos') or [])
    if t == 'responsorio':
        return norm_lista((v.get('r') or []) + [v.get('v')])
    if t == 'preces':
        return norm_lista([v.get('introduccion')] + [i['primera'] for i in v['intenciones']] +
                          [i['segunda'] for i in v['intenciones']] + [v.get('final')])
    if t == 'texto' and v.get('estrofas'):
        return norm_lista(vs['texto'] for e in v['estrofas'] for vs in e)
    if t == 'texto' and v.get('parrafos'):
        return norm_lista(v['parrafos'])
    if t in ('oracion', 'rubrica', 'texto'):
        return norm_item(v.get('texto') or '')
    return json.dumps({k: x for k, x in v.items() if not k.startswith('_')}, ensure_ascii=False)


def parecido(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


CAMPOS_PUBLICOS = {
    'antifona': ['numero', 'texto', 'tp_aleluya', 'cruz'],
    'salmo': ['salmo', 'parte'],
    'himno': ['himno', 'remite'],
    'lectura_breve': ['cita', 'texto'],
    'responsorio_breve': ['v1', 'r1', 'v2', 'r2', 'gloria'],
    'versiculo': ['v', 'r', 'gloria', 'despues_gloria', 'tp_aleluya', 'signo_cruz'],
    'lectura': ['orden', 'cita', 'encabezado', 'fuente', 'titulo', 'parrafos'],
    'responsorio': ['cita', 'r', 'v', 'secuencia', 'tp_aleluya'],
    'preces': ['introduccion', 'respuesta', 'intenciones', 'libres_despues_de', 'final'],
    'oracion': ['texto'],
    'rubrica': ['texto', 'remite'],
    'texto': ['texto', 'parrafos', 'estrofas'],
}


def fuente_de(v):
    raw = v['_raw']
    if not raw:
        return {'tomo': v['_fuente']['tomo']}
    a, b = raw[0], raw[-1]
    f = {'tomo': a.tomo, 'pdf': a.pdf, 'impresa': a.impresa}
    if b.pdf != a.pdf:
        f.update({'pdf_fin': b.pdf, 'impresa_fin': b.impresa})
    return f


class Unificador:
    def __init__(self):
        self.diferencias = []   # filas de diferencias.csv
        self.himnos = {}        # id → entrada de himnos.json
        self.himno_por_clave = {}

    def dif(self, ident, tomos, textos, tipo, nota=''):
        textos = {str(k): ('' if v is None else str(v)) for k, v in textos.items()}
        self.diferencias.append({'identificador': ident, 'tomos': tomos, 'textos': textos,
                                 'tipo': tipo, 'nota': nota})

    def unir_comun(self, cid, por_tomo):
        """por_tomo: {tomo: comun extraído}. Devuelve el común unificado."""
        tomos = sorted(por_tomo)
        out = {'id': cid, 'titulo': None, 'fuentes': [], 'rubricas': [], 'horas': {}}
        titulos = {t: por_tomo[t]['titulo'] for t in tomos}
        out['titulo'] = Counter(titulos.values()).most_common(1)[0][0]
        subt = [{'tomo': t, 'texto': por_tomo[t]['subtitulo']} for t in tomos if por_tomo[t].get('subtitulo')]
        if subt:
            out['subtitulos'] = subt
        agr = {}
        for t in tomos:
            for h, x in (por_tomo[t].get('agrupacion') or {}).items():
                agr.setdefault(h, x)
        if agr:
            out['agrupacion'] = agr
        secc = [por_tomo[t].get('seccion') for t in tomos if por_tomo[t].get('seccion')]
        if secc:
            out['seccion'] = Counter(secc).most_common(1)[0][0]
        if len(set(titulos.values())) > 1:
            self.dif(f'{cid}/titulo', tomos, titulos, 'título distinto')
        for t in tomos:
            c = por_tomo[t]
            out['fuentes'].append({'tomo': t, 'pdf': c['_pdf'], 'impresa': c['_impresa']})
        # rúbricas generales del común
        rub = self.unir_piezas(f'{cid}/rubricas', [
            (t, [{'tipo': 'rubrica', 'variantes': [v]} for v in por_tomo[t]['rubricas']]) for t in tomos])
        out['rubricas'] = rub
        # horas en el orden del libro
        orden = []
        for t in tomos:
            prev = None
            for h in por_tomo[t]['_orden']:
                if h not in orden:
                    orden.insert(orden.index(prev) + 1 if prev in orden else 0, h)
                prev = h
        for h in orden:
            out['horas'][h] = self.unir_hora(f'{cid}/{h}', {t: por_tomo[t]['horas'].get(h) for t in tomos})
        return out

    def unir_hora(self, ident, por_tomo):
        if getattr(self, 'modo', '') == 'ordinario':
            return self.unir_hora_ordinario(ident, por_tomo)
        orden = []
        for t, partes in por_tomo.items():
            if not partes:
                continue
            prev = None
            for p in partes:
                n = p['parte']
                if n not in orden:
                    orden.insert(orden.index(prev) + 1 if prev in orden else 0, n)
                prev = n
        presentes = [t for t, p in por_tomo.items() if p]
        out = []
        for n in orden:
            listas = []
            for t in presentes:
                piezas = [pz for p in por_tomo[t] if p['parte'] == n for pz in p['piezas']]
                listas.append((t, piezas))
            piezas = self.unir_piezas(f'{ident}/{n}', listas)
            faltan = [t for t, pzs in listas if not pzs]
            parte = {'parte': n, 'piezas': piezas}
            if faltan and len(presentes) > 1:
                self.dif(f'{ident}/{n}', faltan, {}, 'omisión', f'la parte falta en el tomo {faltan}')
            out.append(parte)
        return out

    def unir_hora_ordinario(self, ident, por_tomo):
        """Ordinario: los tomos no traen los mismos rótulos, así que las piezas de la hora se alinean
        por su contenido en toda la hora y después se vuelven a agrupar en partes."""
        listas = []
        for t, partes in por_tomo.items():
            if not partes:
                continue
            piezas = []
            for p in partes:
                for pz in p['piezas']:
                    pz['_parte'] = p['parte']
                    piezas.append(pz)
            listas.append((t, piezas))
        self._por_contenido = True
        piezas = self.unir_piezas(ident, listas)
        self._por_contenido = False
        out = []
        for pz in piezas:
            nombre = pz.pop('_parte', None) or 'texto'
            if nombre in ('versiculo', 'texto', 'rubrica', 'introduccion') and pz['tipo'] != 'versiculo' and out:
                nombre = out[-1]['parte']     # tomo sin rótulo: la pieza sigue en la parte anterior
            if out and out[-1]['parte'] == nombre:
                out[-1]['piezas'].append(pz)
            else:
                out.append({'parte': nombre, 'piezas': [pz]})
        return out

    def unir_piezas(self, ident, listas):
        """Alinea las piezas de una parte por tipo y orden; une las variantes."""
        textos_vistos = []   # Ordinario: los textos fijos se alinean por su contenido, no por su lugar

        def claves(piezas):
            cnt = Counter()
            ks = []
            for pz in piezas:
                por_cont = pz['tipo'] == 'texto' or (getattr(self, '_por_contenido', False) and pz['tipo'] not in ('antifona', 'salmo'))
                if por_cont and pz['variantes']:
                    kc = pz['tipo'] + ':' + clave(pz['variantes'][0])
                    umbral_k = 0.75 if pz['tipo'] == 'rubrica' else 0.9
                    igual = next((x for x in textos_vistos if x.split(':')[0] == pz['tipo'] and
                                  parecido(x[:400], kc[:400]) >= umbral_k), None)
                    if igual is None:
                        textos_vistos.append(kc)
                        igual = kc
                    k = (pz['tipo'], igual[:70])
                elif pz['tipo'] == 'antifona' and pz['variantes'] and pz['variantes'][0].get('numero'):
                    k = ('antifona', pz['variantes'][0]['numero'])
                else:
                    cnt[pz['tipo']] += 1
                    k = (pz['tipo'], cnt[pz['tipo']])
                ks.append(k)
            return ks
        orden, por_clave = [], defaultdict(list)
        if getattr(self, '_por_contenido', False):
            # Ordinario: el orden lo da el tomo de referencia (III, IV, II, I); los demás se intercalan
            pref = {3: 0, 4: 1, 2: 2, 1: 3}
            listas = sorted(listas, key=lambda x: pref.get(x[0], 9))
        for t, piezas in listas:
            ks = claves(piezas)
            if getattr(self, '_por_contenido', False):
                vistos_t = Counter()       # el mismo texto dos veces en un tomo: dos lugares distintos
                ks2 = []
                for k in ks:
                    vistos_t[k] += 1
                    ks2.append(k if vistos_t[k] == 1 else (k[0], f'{k[1]}#{vistos_t[k]}'))
                ks = ks2
            prev = None
            for k, pz in zip(ks, piezas):
                if k not in orden:
                    orden.insert(orden.index(prev) + 1 if prev in orden else 0, k)
                prev = k
                por_clave[k].append((t, pz))
        tomos_presentes = [t for t, piezas in listas if piezas]
        out = []
        pares = {}   # id(variante de tomo) → variante unificada
        for k in orden:
            tipo = k[0]
            ent = por_clave[k]
            pid = f'{ident}/{tipo}{"" if k[1] == 1 else (k[1] if isinstance(k[1], int) else "")}'
            pieza = {'tipo': tipo, 'variantes': []}
            if ent and ent[0][1].get('_parte'):
                # la parte con rótulo propio gana a los contenedores genéricos de los tomos que no lo traen
                nombres = [pz.get('_parte') for _, pz in ent if pz.get('_parte')]
                buenos = [x for x in nombres if x not in ('versiculo', 'texto', 'rubrica', 'introduccion')]
                pieza['_parte'] = Counter(buenos or nombres).most_common(1)[0][0]
            remites = [(t, pz.get('remite')) for t, pz in ent if pz.get('remite')]
            if remites:
                pieza['remite'] = remites[0][1]
            uni = self.unir_variantes(pid, ent, pares)
            pieza['variantes'] = uni
            faltan = [t for t in tomos_presentes if t not in [t2 for t2, _ in ent]]
            if faltan and tipo != 'rubrica':
                self.dif(pid, faltan, {}, 'omisión', 'la pieza no está en estos tomos')
            if tipo == 'rubrica' and len(uni) > 1:
                # rúbricas distintas en el mismo lugar: piezas aparte, no variantes
                for v in uni:
                    out.append({'tipo': 'rubrica', 'variantes': [v], **({'_parte': pieza['_parte']} if '_parte' in pieza else {})})
                continue
            out.append(pieza)
        self._pares = getattr(self, '_pares', {})
        self._pares.update(pares)
        return out

    def unir_variantes(self, pid, entradas, pares):
        uni = []   # cada una: {'vars': [(tomo, v)], 'key':…}
        for t, pz in entradas:
            for v in pz['variantes']:
                k = clave(v)
                et = v.get('etiqueta')
                cuando, es_op, conocida = condicion(et)
                # emparejadas (responsorio de una lectura): condición de su lectura
                destino = None
                for u in uni:
                    if u['key'] == k:
                        destino = u
                        break
                if destino is None and v['_tipo'] not in ('salmo',):
                    cands = [(parecido(u['key'], k), u) for u in uni if t not in u['tomos']]
                    if cands:
                        pc, u = max(cands, key=lambda x: x[0])
                        misma = et and any(x.get('etiqueta') == et for _, x in u['vars'])
                        umbral = 0.5 if v['_tipo'] == 'rubrica' else (0.85 if misma else 0.965)
                        if v['_tipo'] == 'rubrica':
                            # misma rúbrica con otra redacción: comparten destino de remisión
                            def destinos(x):
                                d = remite_de(x.get('texto') or '')
                                return set(d if isinstance(d, list) else [d]) - {None}
                            if destinos(v) & destinos(u['vars'][0][1]):
                                pc = 1.0
                        if pc >= umbral:
                            destino = u
                            u['casi'] = True
                if destino is None:
                    destino = {'key': k, 'vars': [], 'tomos': [], 'casi': False}
                    uni.append(destino)
                destino['vars'].append((t, v))
                destino['tomos'].append(t)
        resultado = []
        for u in uni:
            resultado.append(self.componer(pid, u, len(resultado)))
        # números de opción dentro de cada condición
        grupos = defaultdict(list)
        for r in resultado:
            grupos[json.dumps({a: b for a, b in r['cuando'].items() if a != 'opcion'}, sort_keys=True)].append(r)
        for g in grupos.values():
            if g and g[0]['_tipo'] == 'rubrica':
                continue
            g = [r for r in g if not r.get('_desconocida')]   # condición fuera del vocabulario: no es una opción
            hay_opcion = len(g) > 1 or any(r.get('_es_opcion') for r in g)
            for n, r in enumerate(g, 1):
                if hay_opcion and len(g) > 1:
                    r['cuando']['opcion'] = n
        for r in resultado:
            r.pop('_es_opcion', None)
            if not r['cuando']:
                r.pop('cuando')
        # condición de la pareja (responsorio ↔ lectura, responsorio breve ↔ lectura breve)
        for u, r in zip(uni, resultado):
            for t, v in u['vars']:
                pares[id(v)] = r
        for u, r in zip(uni, resultado):
            for t, v in u['vars']:
                if '_par' in v and id(v['_par']) in pares:
                    par = pares[id(v['_par'])]
                    if 'cuando' in par:
                        r['cuando'] = dict(par['cuando'])
                    if par.get('etiqueta') and not r.get('etiqueta'):
                        r['etiqueta'] = par['etiqueta']
                    r['de'] = par.get('_ref')
                    break
        # la misma etiqueta de opción («I», «O bien:») con otro texto en otro tomo
        for i1, r1 in enumerate(resultado):
            for r2 in resultado[i1 + 1:]:
                e = r1.get('etiqueta')
                if e and e == r2.get('etiqueta') and condicion(e)[1] and not set(r1['_tomos']) & set(r2['_tomos']):
                    for rr in (r1, r2):
                        rr['revisar'] = True
                        rr.setdefault('nota', []).append(f'otro texto bajo la misma etiqueta «{e}» en otro tomo')
                    self.dif(pid, sorted(set(r1['_tomos']) | set(r2['_tomos'])),
                             {str(r1['_tomos']): r1['_resumen'], str(r2['_tomos']): r2['_resumen']},
                             'variante sin etiqueta', f'texto distinto bajo «{e}»')
        # sin etiqueta y distintas en sustancia
        sin = [r for r in resultado if not r.get('etiqueta') and not r.get('_heredada')]
        if len(sin) > 1 and resultado and resultado[0]['_tipo'] not in ('salmo', 'rubrica', 'texto'):
            for r in sin:
                r['revisar'] = True
                r.setdefault('nota', [])
                r['nota'].append('variante sin etiqueta distinta de la de otro tomo: no se inventa condición')
            self.dif(pid, sorted({t for r in sin for t in r['_tomos']}),
                     {str(r['_tomos']): r['_resumen'] for r in sin}, 'variante sin etiqueta')
        for r in resultado:
            for k in ('_tipo', '_tomos', '_resumen', '_heredada', '_desconocida'):
                r.pop(k, None)
            if r.get('nota'):
                r['nota'] = ' · '.join(dict.fromkeys(r['nota']))
            else:
                r.pop('nota', None)
        return resultado

    def componer(self, pid, u, idx):
        vars_ = u['vars']
        tomos = [t for t, _ in vars_]
        tipo = vars_[0][1]['_tipo']
        # texto: el que coincide en más tomos
        cuenta = Counter(clave(v) for _, v in vars_)
        mayor, n = cuenta.most_common(1)[0]
        empate = len(cuenta) > 1 and list(cuenta.values()).count(n) > 1
        base = next(v for _, v in vars_ if clave(v) == mayor)
        r = {'_tipo': tipo, '_tomos': tomos}
        notas = []
        # etiqueta: la general gana (regla de los tomos estacionales)
        etiquetas = {t: v.get('etiqueta') for t, v in vars_}
        sin_et = [t for t, e in etiquetas.items() if not e]
        con_et = {t: e for t, e in etiquetas.items() if e}
        cond_tiempo = {t: condicion(e)[0] for t, e in con_et.items() if set(condicion(e)[0]) == {'tiempo'}}
        if sin_et and cond_tiempo:
            et = None
            r['etiquetas_en_tomos'] = [{'tomo': t, 'etiqueta': e} for t, e in con_et.items()]
            self.dif(f'{pid}', sorted(etiquetas), {str(t): e or '(sin etiqueta)' for t, e in etiquetas.items()},
                     'etiqueta distinta', 'mismo texto: se deja como variante general')
        else:
            et = next((etiquetas[t] for t in tomos if etiquetas[t]), None)
            distintas = {e for e in con_et.values()}
            if len(distintas) > 1:
                r['etiquetas_en_tomos'] = [{'tomo': t, 'etiqueta': e} for t, e in con_et.items()]
                self.dif(pid, sorted(con_et), {str(t): e for t, e in con_et.items()}, 'etiqueta distinta')
            if sin_et and con_et and not cond_tiempo:
                r['etiquetas_en_tomos'] = [{'tomo': t, 'etiqueta': e or None} for t, e in etiquetas.items()]
        if et:
            r['etiqueta'] = et
        cuando, es_op, conocida = condicion(et)
        v_et = next((v for _, v in vars_ if v.get('etiqueta') == et), None)
        if v_et is not None and v_et.get('_cuando') is not None:
            cuando = v_et['_cuando']
        if et and not conocida:
            r['_desconocida'] = True
            r['revisar'] = True
            notas.append(f'etiqueta fuera del vocabulario: «{et}»')
        r['cuando'] = dict(cuando)
        r['_es_opcion'] = es_op
        if any(v.get('_etiqueta_heredada') for _, v in vars_):
            r['_heredada'] = True
        # campos
        for c in CAMPOS_PUBLICOS.get(tipo, []):
            if c in base:
                r[c] = base[c]
        if tipo == 'himno' and base['estrofas']:
            r['himno'] = self.registrar_himno(vars_, base)
        elif tipo == 'himno':
            r.pop('himno', None)
        if tipo == 'antifona':
            if r.get('numero') is None:
                r.pop('numero', None)
            tps = {t: v.get('tp_aleluya', False) for t, v in vars_}
            r['tp_aleluya'] = any(tps.values())
            if len(set(tps.values())) > 1:
                self.dif(f'{pid}', sorted(tps), {str(t): ('(T. P. Aleluya.)' if x else '—') for t, x in tps.items()},
                         'omisión', '«(T. P. Aleluya.)» solo en algunos tomos')
        if tipo in ('versiculo', 'responsorio'):
            tps = {t: bool(v.get('tp_aleluya')) for t, v in vars_}
            if any(tps.values()):
                r['tp_aleluya'] = True
                if len(set(tps.values())) > 1:
                    self.dif(f'{pid}', sorted(tps), {str(t): ('(T. P. Aleluya.)' if x else '—') for t, x in tps.items()},
                             'omisión', '«(T. P. Aleluya.)» solo en algunos tomos')
            else:
                r.pop('tp_aleluya', None)
        if tipo == 'rubrica':
            rem = remite_de(base['texto'], comun=pid.split('/')[0], hora=pid.split('/')[1] if '/' in pid else None)
            if rem:
                r['remite'] = rem
            elif base.get('_azul'):
                # remisión azul sin forma conocida: queda pendiente con su texto literal
                r['remite'] = ['texto-azul/' + slug(x) for x in base['_azul'] if slug(x)]
                notas.append('remisión azul sin destino normalizado: ' + '; '.join(base['_azul']))
            else:
                r.pop('remite', None)
            otras = {t: v['texto'] for t, v in vars_ if clave(v) != mayor}
            if otras:
                r['otras_redacciones'] = [{'tomo': t, 'texto': x} for t, x in otras.items()]
                self.dif(pid, sorted({t for t, _ in vars_}), {str(t): v['texto'] for t, v in vars_},
                         'rúbrica con otra redacción')
        elif len(cuenta) > 1:
            textos = {str(t): resumen(v) for t, v in vars_}
            if empate:
                r['revisar'] = True
                notas.append('diferencia de pocas letras entre tomos, sin mayoría: se tomó el primer tomo')
            self.dif(pid, sorted(tomos), textos, 'errata probable',
                     'se guardó el texto de la mayoría' if not empate else 'empate: revisar')
        for t, v in vars_:
            if v.get('_repeticion') is not None and norm_item(v['_repeticion']) != norm_item(v.get('texto') or ''):
                r['revisar'] = True
                notas.append(f'tomo {t}: la antífona repetida después del salmo no coincide: «{v["_repeticion"]}»')
        # revisar heredado
        for t, v in vars_:
            if v.get('revisar'):
                r['revisar'] = True
            notas.extend(v.get('_notas', []))
        if notas:
            r['nota'] = notas
        r['fuentes'] = sorted([fuente_de(v) for _, v in vars_], key=lambda f: (f['tomo'], f.get('pdf', 0)))
        r['_resumen'] = resumen(base)
        r['_ref'] = f'{pid}#{idx + 1}'
        return r

    def registrar_himno(self, vars_, base):
        k = clave(base)
        if k in self.himno_por_clave:
            hid = self.himno_por_clave[k]
            ent = self.himnos[hid]
        else:
            primero = base['estrofas'][0][0]['texto'] if base['estrofas'] else 'himno'
            hid = slug(re.sub(r'[¡!¿?]', '', primero))
            while hid in self.himnos:
                hid += '-2'
            ent = {'id': hid, 'primer_verso': primero, 'estrofas': base['estrofas'],
                   'amen': base.get('amen', False), 'fuentes': []}
            for k2, h2 in self.himno_por_clave.items():
                if parecido(k, k2) >= 0.85:
                    ent['revisar'] = True
                    ent['nota'] = f'casi igual a «{h2}»: ¿es el mismo himno con otra redacción?'
                    self.dif(f'himnos/{hid}', [t for t, _ in vars_], {'otro': h2}, 'errata probable',
                             f'casi igual a {h2}; se guardan los dos')
            self.himnos[hid] = ent
            self.himno_por_clave[k] = hid
        for t, v in vars_:
            f = fuente_de(v)
            if f not in ent['fuentes']:
                ent['fuentes'].append(f)
            if clave(v) != k:
                self.dif(f'himnos/{hid}', [t], {str(t): resumen(v)}, 'errata probable',
                         'el himno tiene diferencias menores en este tomo')
        return hid


def resumen(v):
    t = v['_tipo']
    if t == 'texto' and v.get('estrofas'):
        return ' / '.join(vs['texto'] for e in v['estrofas'] for vs in e)
    if t == 'texto' and v.get('parrafos'):
        return ' ¶ '.join(v['parrafos'])
    if t == 'himno':
        return ' / '.join(vs['texto'] for e in v['estrofas'] for vs in e)
    if t == 'lectura':
        return ' ¶ '.join(v.get('parrafos') or [])
    if t == 'responsorio':
        return f"R. {' * '.join(x or '' for x in v.get('r') or [])} V. {v.get('v')}"
    if t == 'responsorio_breve':
        return f"V. {v.get('v1')} R. {v.get('r1')} V. {v.get('v2')} R. {v.get('r2')}"
    if t == 'versiculo':
        return f"V. {v.get('v')} R. {v.get('r')}"
    if t == 'preces':
        return ' ¶ '.join([v.get('introduccion') or ''] + [f"{i['primera']} — {i['segunda']}" for i in v['intenciones']] + [v.get('final') or ''])
    if t == 'salmo':
        return v['salmo']
    return v.get('texto') or ''


# ───────────────────────────── salmos unificados ────────────────────────────
def unir_salmos(por_tomo, uni):
    out = {}
    ids = []
    for t in sorted(por_tomo):
        for sid in por_tomo[t]:
            if sid not in ids:
                ids.append(sid)
    textos_salmo = {}
    for sid in ids:
        ent = {t: por_tomo[t][sid] for t in sorted(por_tomo) if sid in por_tomo[t]}
        def k(e):
            return norm_lista(vs['texto'] for p in e['partes'].values() for es in p for vs in es)
        cuenta = Counter(k(e) for e in ent.values())
        mayor = cuenta.most_common(1)[0][0]
        base = next(e for e in ent.values() if k(e) == mayor)
        titulos = {t: e['titulo'] for t, e in ent.items()}
        titulo = next((x for x in titulos.values() if x), None)
        sal = {'id': sid, 'cita': base['cita'], 'titulo': titulo, 'sentencia': base['sentencia'],
               **({'gloria': True} if base.get('gloria') else {}),
               **({'rubricas': base['rubricas']} if base.get('rubricas') else {}),
               'partes': [{'numero': p or None, 'estrofas': es} for p, es in base['partes'].items()],
               'fuentes': [{'tomo': t, 'pdf': e['pdf'], 'impresa': e['impresa']} for t, e in ent.items()]}
        if len(cuenta) > 1:
            textos = {str(t): ' / '.join(vs['texto'] for p in e['partes'].values() for es in p for vs in es)
                      for t, e in ent.items()}
            uni.dif(f'salmos/{sid}', sorted(ent), textos, 'errata probable',
                    'el texto del salmo no coincide en todos los tomos; se guardó el de la mayoría')
            sal['revisar'] = True
            sal['nota'] = 'el texto no coincide en todos los tomos (ver diferencias.csv)'
        faltan = [t for t, x in titulos.items() if not x]
        if faltan and titulo:
            uni.dif(f'salmos/{sid}/titulo', faltan, {str(t): x or '—' for t, x in titulos.items()},
                    'omisión', 'el subtítulo del salmo falta en estos tomos')
        textos_salmo[sid] = len(cuenta) == 1
        out[sid] = sal
    return out, textos_salmo


# ─────────────────────────────── controles ──────────────────────────────────
def recorrer(comun):
    for r in comun.get('rubricas', []):
        for v in r['variantes']:
            yield 'rubricas', None, r, v
    for h, partes in comun['horas'].items():
        for p in partes:
            for pz in p['piezas']:
                for v in pz['variantes']:
                    yield h, p['parte'], pz, v


def textos_de(v):
    for k in ('texto', 'v', 'r', 'v1', 'r1', 'v2', 'r2', 'introduccion', 'final', 'titulo'):
        x = v.get(k)
        if isinstance(x, str):
            yield k, x
        elif isinstance(x, list):
            for y in x:
                if isinstance(y, str):
                    yield k, y
                elif isinstance(y, dict) and 'texto' in y:
                    yield k, y['texto']
    for p in v.get('parrafos') or []:
        yield 'parrafos', p
    for i in v.get('intenciones') or []:
        yield 'intenciones', i['primera']
        if i['segunda']:
            yield 'intenciones', i['segunda']


# «Para » y «como en» se buscan en su forma de rótulo o de remisión («Para un santo…»,
# «como en las II Vísperas»): el texto bíblico dice «como en los días…» y un versículo
# puede empezar «Para que…».
ROTULOS_PROHIBIDOS = re.compile(r'^(Ant\.|V\.|R\.|—|Para (un|una|unos|unas|varios|varias) |O bien|Tiempo de|Año )')
FRASES_PROHIBIDAS = re.compile(r'Se dice|Se pueden|como en (las?|el) (I|II|Laudes|Vísperas|Común|Ordinario|Propio|Oficio)|T\. ?P\.')


def controles(parsers, descartes, comunes, salmos, himnos, uni, textos_salmo):
    L = []
    ok_total = True

    def linea(ok, nombre, detalle):
        nonlocal ok_total
        ok_total &= ok
        L.append(f"[{'OK ' if ok else 'MAL'}] {nombre}: {detalle}")

    # 1. Cobertura
    por_pag = defaultdict(lambda: [0, 0])
    huerfanos = []
    for p in parsers:
        for r in p.R:
            c = por_pag[(p.tomo, r.pdf)]
            n = len([s for s in r.segs if s['t'].strip()]) or 1
            c[1] += n
            if r.dueno is not None:
                c[0] += n
            else:
                huerfanos.append(r)
    for d in descartes:
        c = por_pag[(d['tomo'], d['pdf'])]
        c[0] += 1; c[1] += 1
    tot_a = sum(a for a, b in por_pag.values()); tot_b = sum(b for a, b in por_pag.values())
    linea(not huerfanos, 'Cobertura',
          f'{tot_a}/{tot_b} fragmentos asignados ({100 * tot_a / tot_b:.1f} %); huérfanos: {len(huerfanos)}')
    for (t, pdf), (a, b) in sorted(por_pag.items()):
        L.append(f'      tomo {t} · pdf {pdf}: {100 * a / b:.0f} %')
    for r in huerfanos[:30]:
        L.append(f'      huérfano: tomo {r.tomo} pdf {r.pdf} y={r.y}: {r.texto[:70]}')

    # 2. Sin rojo en el texto / 3. Sin rótulos
    rojo, rotulos = [], []
    for c in comunes:
        for h, parte, pz, v in recorrer(c):
            if pz['tipo'] == 'rubrica':
                continue
            for campo, x in textos_de(v):
                if ROTULOS_PROHIBIDOS.match(x) or FRASES_PROHIBIDAS.search(x):
                    rotulos.append(f'{c["id"]}/{h}/{parte}: {x[:60]}')
    for p in parsers:
        for r in p.R:
            d = r.dueno
            if isinstance(d, dict) and d.get('_rojo'):
                rojo.append(f'tomo {p.tomo} pdf {r.pdf}: {d["_rojo"]}')
    linea(True, 'Sin rojo en el texto', f'ningún texto conserva rojo; {len(rojo)} fragmentos rojos sueltos dentro de un texto '
          '(†, corchetes…) se sacaron del texto y la pieza quedó marcada para revisar' + ''.join('\n      ' + x for x in rojo[:15]))
    linea(not rotulos, 'Sin rótulos en el texto', f'{len(rotulos)} casos' + ''.join('\n      ' + x for x in rotulos[:10]))

    # 4. Conteos
    malos, vacias = [], []
    for c in comunes:
        for h, partes in c['horas'].items():
            for p in partes:
                if p['parte'] == 'salmodia' and h in ('laudes', 'visperas1', 'visperas2', 'visperas'):
                    na = len([pz for pz in p['piezas'] if pz['tipo'] == 'antifona'])
                    ns = len([pz for pz in p['piezas'] if pz['tipo'] == 'salmo'])
                    rem = any(pz['tipo'] == 'rubrica' for pz in p['piezas'])
                    if na == 0 and ns == 0 and not rem:
                        vacias.append(f'{c["id"]}/{h}/salmodia')
                    elif not (na == 3 and (ns == 3 or rem)) and not (rem and na == 0):
                        malos.append(f'{c["id"]}/{h}/salmodia: {na} antífonas, {ns} salmos')
                for pz in p['piezas']:
                    for v in pz['variantes']:
                        if pz['tipo'] == 'responsorio_breve' and not all(v.get(k) for k in ('v1', 'r1', 'v2', 'r2')):
                            malos.append(f'{c["id"]}/{h}/responsorio_breve incompleto')
                            v['revisar'] = True
                        if pz['tipo'] == 'preces' and not (v.get('introduccion') and v.get('respuesta') and v.get('intenciones') and v.get('final')):
                            malos.append(f'{c["id"]}/{h}/preces incompletas')
                            v['revisar'] = True
    linea(not malos, 'Conteos', f'{len(malos)} fuera de norma' + ''.join('\n      ' + x for x in malos) +
          ''.join(f'\n      parte vacía en el libro (solo el rótulo): {x}' for x in vacias))

    # 5. Opciones: cada etiqueta roja del libro produjo una variante
    et_libro = Counter()
    for p in parsers:
        prev_et = False
        for r in p.R:
            if r.vacio:
                continue
            es = p.clase(r) == 'etiqueta' or (p.clase(r) == 'romano' and isinstance(r.dueno, dict) and r.dueno.get('_tipo') in ('himno', 'texto'))
            if es and isinstance(r.dueno, dict) and r.dueno.get('_tipo') == 'repeticion':
                es = False                  # etiqueta de una antífona repetida después del salmo
            es = es or bool(r.es_et)
            if es and not prev_et:          # etiquetas apiladas («En tiempo de cuaresma:» «Para un santo:») cuentan una vez
                et_libro[p.tomo] += 1
            prev_et = es
            d = r.dueno
            if isinstance(d, dict) and (d.get('_cita_con_etiqueta') or d.get('_et_linea')) and d['_raw'] and d['_raw'][0] is r:
                et_libro[p.tomo] += 1
    et_var = Counter()
    for p in parsers:
        for c in p.comunes:
            for h, partes in c['horas'].items():
                for pt in partes:
                    for pz in pt['piezas']:
                        for v in pz['variantes']:
                            if v.get('etiqueta') and not v.get('_etiqueta_heredada') and not v.get('_et_bloque'):
                                et_var[p.tomo] += 1
                            if pz['tipo'] == 'preces':
                                et_var[p.tomo] += len([x for x in v['respuesta'] if x['etiqueta']])
    ok = et_libro == et_var
    linea(ok, 'Opciones', ', '.join(f'tomo {t}: {et_libro[t]} etiquetas rojas → {et_var[t]} variantes' for t in sorted(et_libro)))

    # 6. Remisiones
    existentes = set()
    for c in comunes:
        existentes.add('comunes/' + c['id'])
        if c['id'].startswith('martires'):
            existentes.add('comunes/martires')
        for h, partes in c['horas'].items():
            for p in partes:
                existentes.add(f'{c["id"]}/{h}/{p["parte"]}')
                existentes.add(f'{c["id"]}/{p["parte"]}')     # «la conclusión como en el Ordinario»: parte de cualquier hora
    pendientes, rotas = set(), []
    for c in comunes:
        for h, parte, pz, v in recorrer(c):
            for rem in [pz.get('remite'), v.get('remite')]:
                for x in (rem if isinstance(rem, list) else [rem]):
                    if not x:
                        continue
                    if x.startswith('comunes/') or x.split('/')[0] in {c['id'] for c in comunes}:
                        if x not in existentes:
                            rotas.append(x)
                    elif x.startswith('?'):
                        rotas.append(x)
                    elif x.startswith('texto-azul/'):
                        pendientes.add(x)
                    else:
                        pendientes.add(x)
    linea(not rotas, 'Remisiones', f'{len(rotas)} rotas; {len(pendientes)} pendientes (fuera de esta sección)' +
          ''.join('\n      rota: ' + x for x in rotas) + ''.join('\n      pendiente: ' + x for x in sorted(pendientes)))

    # 7. Salmos
    nombrados = set()
    for c in comunes:
        for h, parte, pz, v in recorrer(c):
            if pz['tipo'] == 'salmo':
                nombrados.add(v['salmo'])
    faltan = nombrados - set(salmos)
    distintos = [s for s, ok in textos_salmo.items() if not ok]
    linea(not faltan, 'Salmos', f'{len(nombrados)} nombrados, todos en salmos.json' if not faltan else f'faltan {faltan}')
    linea(not distintos, 'Salmos iguales en todos los tomos',
          'sí' if not distintos else f'difieren: {", ".join(distintos)} (ver diferencias.csv)')

    # 8. Ida y vuelta
    total, malas = 0, []
    for p in parsers:
        vistos = set()
        for r in p.R:
            d = r.dueno
            if not isinstance(d, dict) or id(d) in vistos or d.get('_tipo') in (None,):
                continue
            vistos.add(id(d))
            if '_raw' not in d or d.get('_tipo') in ('remite',):
                continue
            total += 1
            crudo = ''.join(x.texto for x in sorted(d['_raw'], key=lambda x: x.n))
            for q in d.get('_rojo', []) + d.get('_signos', []):
                crudo = crudo.replace(q, '', 1)
            crudo = re.sub(r'\s+', '', crudo)
            vuelto = reescribir(d).replace('{N}', 'N.')
            vuelto = re.sub(r'\[([^\]]+)\]', r'(\1)', vuelto)
            vuelto = re.sub(r'\s+', '', vuelto)
            crudo, vuelto = crudo.translate(PARENTESIS), vuelto.translate(PARENTESIS)
            if crudo != vuelto:
                malas.append((p.tomo, d['_raw'][0].pdf, d.get('_tipo'), crudo, vuelto))
    linea(not malas, 'Ida y vuelta', f'{total - len(malas)}/{total} piezas reescritas igual al libro')
    for t, pdf, tp, a, b in malas[:25]:
        sm = difflib.SequenceMatcher(None, a, b)
        dif = [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
        L.append(f'      tomo {t} pdf {pdf} {tp}: {dif[:4]}')
    # rojos y azules dudosos
    dud = [(p.tomo, r.pdf, r.texto[:50], {s["hex"] for s in r.segs if s['dud']}) for p in parsers for r in p.R if r.dudoso]
    L.append(f'[INF] Colores dudosos clasificados por tono: {len(dud)}' + ''.join(f'\n      tomo {a} pdf {b}: {c} {d}' for a, b, c, d in dud[:20]))
    cortes = [x for p in parsers for x in p.cortes]
    L.append(f'[INF] Líneas unidas por guion de corte: {len(cortes)}' + ''.join('\n      …' + x for x in cortes))
    av = [(p.tomo, r.pdf, m, r.texto[:50]) for p in parsers for r, m in p.avisos]
    L.append(f'[INF] Avisos del análisis: {len(av)}' + ''.join(f'\n      tomo {a} pdf {b}: {c}: {d}' for a, b, c, d in av))
    return ok_total, L


PARENTESIS = str.maketrans({'[': '(', ']': ')'})


def reescribir(d):
    """Vuelve a escribir una variante con sus rótulos, en el orden del libro."""
    t = d.get('_tipo')
    et = (d.get('etiqueta') or '') if not d.get('_etiqueta_heredada') else ''
    if d.get('_et_bloque'):
        et = ''
    if d.get('_et_render') is not None:
        et = d['_et_render']
    if t == 'antifona':
        tp = (d.get('_tp_raw') or '') + ('†' if d.get('cruz') else '')
        rot = d.get('_rotulo') or ''
        if rot.startswith('Antífona') and d.get('_rot_n', -1) < (d.get('_et_n') or 10 ** 9):
            return rot + et + (d.get('texto') or '') + tp
        return et + rot + (d.get('texto') or '') + tp
    if t == 'repeticion':
        return ''.join(x.texto for x in sorted(d['_raw'], key=lambda x: x.n))
    if t == 'himno' and d.get('_linea'):
        return d['_linea']
    if t == 'lectura_breve' and (d.get('_et_linea') or d.get('_sin_rotulo')):
        return et + (d.get('cita') or '') + (d.get('texto') or '')
    if t == 'himno':
        return et + ''.join(vs['_marcas'][2] + vs['_marcas'][0] + vs['texto'] + vs['_marcas'][1]
                            for e in d['estrofas'] for vs in e) + (d.get('_amen_raw') or '')
    if t == 'salmo':
        return ''.join(x.texto for x in d['_raw'])
    if t == 'lectura_breve':
        if d.get('_cita_con_etiqueta'):
            return 'LECTURA BREVE' + et + (d.get('cita') or '') + (d.get('texto') or '')
        return et + 'LECTURA BREVE' + (d.get('cita') or '') + (d.get('texto') or '')
    if t == 'responsorio_breve':
        g = d.get('_gloria_raw') or []
        s = f"V.{d.get('v1')}R.{d.get('r1')}V.{d.get('v2')}R.{d.get('r2')}"
        if g:
            s += f'V.{g[0]}R.{g[1]}'
        return et + s
    if t == 'versiculo':
        tp = d.get('_tp_raw') or {}
        return f"{et}V.{d.get('v')}{tp.get('v', '')}R.{d.get('r')}{d.get('_gloria_raw') or ''}{d.get('despues_gloria') or ''}{tp.get('r', '')}"
    if t == 'lectura':
        return et + (d.get('encabezado') or '') + (d.get('cita') or '') + (d.get('fuente') or '') + \
            (d.get('titulo') or '') + ''.join(d.get('parrafos') or [])
    if t == 'responsorio' and d.get('secuencia'):
        return et + 'Responsorio' + (d.get('cita') or '') + ''.join(x['rotulo'] + x['texto'] for x in d['secuencia'])
    if t == 'responsorio':
        r = d.get('r') or ['', '']
        tp = d.get('_tp_raw') or ''
        return f"{et}Responsorio{d.get('cita') or ''}R.{r[0]}*{r[1] or ''}{tp}V.{d.get('v')}R.{d.get('_rep')}"
    if t == 'preces':
        s = et + (d.get('introduccion') or '')
        for j, x in enumerate(d['respuesta']):
            s += (x['etiqueta'] or '') + x['texto']
        for n, i in enumerate(d['intenciones']):
            if d.get('libres_despues_de') == n:
                s += d.get('_libres_raw', '')
            s += i['primera'] + ('—' + i['segunda'] if i['segunda'] else '')
        if d.get('libres_despues_de') == len(d['intenciones']):
            s += d.get('_libres_raw', '')
        return s + (d.get('final') or '')
    if t == 'oracion':
        return et + (d.get('texto') or '')
    if t == 'texto' and d.get('estrofas'):
        return et + ''.join(vs['_marcas'][2] + ('*'.join(vs['mitades']) if vs.get('mitades') else vs['texto'])
                            for e in d['estrofas'] for vs in e)
    if t == 'texto' and d.get('parrafos'):
        return et + ''.join(d['parrafos'])
    if t in ('rubrica', 'texto'):
        return et + (d.get('texto') or '')
    return ''.join(x.texto for x in d['_raw'])


# ─────────────────────────────── salida ─────────────────────────────────────
def limpiar_salida(x):
    if isinstance(x, dict):
        return {k: limpiar_salida(v) for k, v in x.items() if not k.startswith('_')}
    if isinstance(x, list):
        return [limpiar_salida(v) for v in x]
    return x


def dudas_csv(comunes, salmos, ruta, himnos=None):
    filas = []
    for c in comunes:
        for h, parte, pz, v in recorrer(c):
            if v.get('revisar'):
                f = (v.get('fuentes') or [{}])[0]
                filas.append({'seccion': 'comunes', 'identificador': f'{c["id"]}/{h}/{parte or ""}/{pz["tipo"]}',
                              'tomo': ' '.join(str(x.get('tomo')) for x in v.get('fuentes', [])),
                              'pagina_pdf': ' '.join(str(x.get('pdf')) for x in v.get('fuentes', [])),
                              'motivo': v.get('nota', ''), 'texto': resumen({**v, '_tipo': pz['tipo'],
                                                                              'intenciones': v.get('intenciones', []),
                                                                              'estrofas': []})[:300]})
    for s in salmos.values():
        if s.get('revisar'):
            filas.append({'seccion': 'salmos', 'identificador': s['id'],
                          'tomo': ' '.join(str(f['tomo']) for f in s['fuentes']),
                          'pagina_pdf': ' '.join(str(f['pdf']) for f in s['fuentes']),
                          'motivo': s.get('nota', ''), 'texto': s['cita'] or ''})
    for h in (himnos or {}).values():
        if h.get('revisar'):
            filas.append({'seccion': 'himnos', 'identificador': h['id'],
                          'tomo': ' '.join(str(f['tomo']) for f in h['fuentes']),
                          'pagina_pdf': ' '.join(str(f['pdf']) for f in h['fuentes']),
                          'motivo': h.get('nota', ''), 'texto': h['primer_verso']})
    with open(ruta, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['seccion', 'identificador', 'tomo', 'pagina_pdf', 'motivo', 'texto'])
        w.writeheader()
        w.writerows(filas)
    return filas


def diferencias_csv(uni, ruta):
    with open(ruta, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['identificador', 'tomos', 'tipo', 'nota', 'texto_tomo_I', 'texto_tomo_II',
                    'texto_tomo_III', 'texto_tomo_IV'])
        for d in uni.diferencias:
            tx = d['textos']
            fila = [d['identificador'], ' '.join(str(t) for t in d['tomos']), d['tipo'], d['nota']]
            for t in ('1', '2', '3', '4'):
                val = tx.get(t, '')
                if not val:
                    val = next((v for k, v in tx.items() if t in k.strip('[]').replace(',', ' ').split()), '')
                fila.append(val)
            w.writerow(fila)
    return len(uni.diferencias)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    pdf = args[0]
    global TOMOS, SALIDA
    sec = args[args.index('--seccion') + 1] if '--seccion' in args else 'comunes'
    cfg = SECCIONES[sec]
    TOMOS, SALIDA = cfg['tomos'], cfg['salida']
    revision = None
    if '--revision' in args:
        revision = Path(args[args.index('--revision') + 1])
    doc = pymupdf.open(pdf)
    parsers, descartes = [], []
    for t, (a, b) in TOMOS.items():
        R, D = leer_tomo(doc, t, a, b)
        descartes += D
        parsers.append(Parser(t, R, modo=cfg.get('modo', 'comunes')).run())
    # unificación
    uni = Unificador()
    uni.modo = cfg.get('modo', 'comunes')
    ids = []
    for p in parsers:
        for c in p.comunes:
            if c['id'] not in ids:
                ids.append(c['id'])
    comunes = []
    for cid in ids:
        por_tomo = {p.tomo: c for p in parsers for c in p.comunes if c['id'] == cid}
        comunes.append(uni.unir_comun(cid, por_tomo))
    salmos, textos_salmo = unir_salmos({p.tomo: p.salmos for p in parsers}, uni)
    ok, L = controles(parsers, descartes, comunes, salmos, uni.himnos, uni, textos_salmo)
    # escribir
    SALIDA.mkdir(parents=True, exist_ok=True)
    if cfg['seccion'] == 'comunes':
        datos = {'seccion': 'comunes', 'comunes': limpiar_salida(comunes)}
    else:
        datos = {'seccion': cfg['seccion'], cfg['seccion']: limpiar_salida(comunes[0] if len(comunes) == 1 else comunes)}
    (SALIDA / cfg['archivo']).write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (SALIDA / 'salmos.json').write_text(json.dumps(limpiar_salida(list(salmos.values())), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (SALIDA / 'himnos.json').write_text(json.dumps(limpiar_salida(list(uni.himnos.values())), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    dudas = dudas_csv(comunes, salmos, SALIDA / 'dudas.csv', uni.himnos)
    nd = diferencias_csv(uni, SALIDA / 'diferencias.csv')
    cab = [f'Controles — {cfg["nombre"]} (tomos I–IV) — {"todos pasan" if ok else "hay controles que no pasan"}',
           f'Piezas marcadas para revisar: {len(dudas)} · diferencias entre tomos: {nd}', '']
    (SALIDA / 'controles.txt').write_text('\n'.join(cab + L) + '\n', encoding='utf-8')
    print('\n'.join(cab + L[:12]))
    if revision:
        sys.path.insert(0, str(AQUI))
        import revision as rv
        rv.generar(doc, parsers, comunes, salmos, uni.himnos, revision, TOMOS,
                   resumen_html=resumen_html(comunes, dudas, uni, L, ok), uni=uni, nombre=cfg['nombre'])


def resumen_html(comunes, dudas, uni, L, ok):
    e = html.escape
    tiempos, opciones, piezas_op = [], 0, 0
    for c in comunes:
        for h, parte, pz, v in recorrer(c):
            cu = v.get('cuando') or {}
            if 'tiempo' in cu:
                tiempos.append((c['id'], h, parte, pz['tipo'], v.get('etiqueta'),
                                ' '.join(str(f['tomo']) for f in v['fuentes'])))
            if 'opcion' in cu:
                opciones += 1
        for h, partes in c['horas'].items():
            for p in partes:
                for pz in p['piezas']:
                    if any('opcion' in (v.get('cuando') or {}) for v in pz['variantes']):
                        piezas_op += 1
    s = '<h2>Controles</h2><table>' + ''.join(
        f'<tr><td>{e(x[:5])}</td><td>{e(x[6:].split(chr(10))[0])}</td></tr>' for x in L if x.startswith('[')) + '</table>'
    s += f'<h2>Variantes por tiempo ({len(tiempos)})</h2><table><tr><th>Común</th><th>Hora / parte</th><th>Etiqueta</th><th>Tomos</th></tr>'
    s += ''.join(f'<tr><td>{e(a)}</td><td>{e(b)} · {e(c or "")} · {e(d)}</td><td class="r">{e(et or "")}</td><td>{e(t)}</td></tr>'
                 for a, b, c, d, et, t in tiempos) + '</table>'
    s += f'<h2>Opciones</h2><p>{opciones} variantes de opción («O bien:», «I», «II»…) en {piezas_op} piezas.</p>'
    s += f'<h2>Marcado para revisar ({len(dudas)})</h2><table><tr><th>Pieza</th><th>Tomos</th><th>Motivo</th></tr>'
    s += ''.join(f'<tr><td>{e(d["identificador"])}</td><td>{e(d["tomo"])}</td><td>{e(d["motivo"])}</td></tr>' for d in dudas) + '</table>'
    cnt = Counter(d['tipo'] for d in uni.diferencias)
    s += '<h2>Diferencias entre tomos</h2><p>' + ' · '.join(f'{e(k)}: {n}' for k, n in cnt.most_common()) + ' (detalle en diferencias.csv)</p>'
    return s


if __name__ == '__main__':
    main()
