"""Clasifica cada pieza del libro según lo que hay que hacer con ella en `base/`.

    python3 extraccion/clasificar.py

Regla de prioridad: el texto de `sync` manda; el libro solo llena lo que falta y reemplaza lo que
se había cargado del libro a mano (`comunes/`, `santoral/libro.yaml`). Reusa los emparejamientos de
`comparar_base.py` (no los rehace): mira qué piezas del libro tocó la comparación, contra qué
archivo de la base y con qué veredicto. Sale en `informes/`: `clasificacion.md` y
`clasificacion.csv` (una fila por pieza). No toca ni `base/` ni la app.
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comparar_base as cb  # noqa: E402

INFORMES = AQUI / 'informes'

# archivos de la base que no vienen de sync sino del libro, cargados a mano
DEL_LIBRO = ('comunes/', 'santoral/libro.yaml', 'santoral/adf.yaml')
# veredictos que muestran un problema de estructura (texto cortado o reordenado), no de traducción
ESTRUCTURA = {'recorte', 'orden'}

# ─────────────── instrumentar la comparación ───────────────

CTX = {'archivo': None}
TOCADAS = defaultdict(lambda: {'archivos': set(), 'veredictos': Counter()})
PENDIENTES = []

_yml, _piezas, _comparar = cb.yml, cb.piezas, cb.INF.comparar


class JsonFijo:
    """json.loads que devuelve el mismo objeto para el mismo texto: así las piezas que mira
    comparar_base.py y las que recorre este script son las mismas y se reconocen por id()."""
    cache = {}

    def __getattr__(self, k):
        return getattr(json, k)

    def loads(self, texto):
        if texto not in self.cache:
            self.cache[texto] = json.loads(texto)
        return self.cache[texto]


def yml(ruta):
    CTX['archivo'] = ruta
    return _yml(ruta)


def piezas(nodos, hora, parte=None, tipo=None):
    out = _piezas(nodos, hora, parte, tipo)
    for pz, v in out:
        TOCADAS[id(pz)]['archivos'].add(CTX['archivo'])
        PENDIENTES.append(id(pz))
    return out


def comparar(ambito, clave, campo, base, libro, modo='lista'):
    v = _comparar(ambito, clave, campo, base, libro, modo)
    for i in set(PENDIENTES):
        if v:
            TOCADAS[i]['veredictos'][v] += 1
    PENDIENTES.clear()
    return v


_comparar_hora = cb.comparar_hora


def texto_base(x):
    if isinstance(x, dict):
        if x.get('vr'):
            return ' '.join(str(y[1]) if isinstance(y, list) else str(y) for y in x['vr'])
        return ' '.join(str(x.get(k) or '') for k in ('texto',))
    return str(x or '')


def comparar_hora(ambito, cl, b, e, h):
    """Lo de comparar_base.py, más las dos lecturas y los dos responsorios del Oficio de lectura,
    que comparar_base.py no mira. Para cada uno elige la pieza del libro más parecida."""
    _comparar_hora(ambito, cl, b, e, h)
    for campo, tipo in (('lectura1', 'lectura'), ('lectura2', 'lectura'), ('resp1', 'responsorio'),
                        ('resp2', 'responsorio')):
        if not b.get(campo):
            continue
        tb = texto_base(b[campo])
        cands = _piezas(e, h, None, tipo)
        if not cands:
            continue
        fb = cb.fuerte(tb)
        def txt(v):
            return ' '.join(str(x) for x in cb.texto_de(v, tipo)[1 if tipo == 'lectura' else 0:] if x)
        pz, v = max(cands, key=lambda c: cb.parecido(fb[:600], cb.fuerte(txt(c[1]))[:600]))
        TOCADAS[id(pz)]['archivos'].add(CTX['archivo'])
        PENDIENTES.append(id(pz))
        comparar(ambito, cl, campo, tb, txt(v))


cb.yml, cb.piezas, cb.INF.comparar, cb.comparar_hora = yml, piezas, comparar, comparar_hora
cb.json = JsonFijo()


def correr():
    cb.comparar_salmos()
    cb.comparar_himnos()
    cb.comparar_completas()
    cb.comparar_salterio()
    cb.comparar_comunes()
    cb.comparar_santoral()
    cb.comparar_tiempo()
    emparejar_resto()


ALIAS = {  # mismas celebraciones, nombradas distinto en la base y en el libro
    'nuestro-senor-jesucristo-rey-universal': 'jesucristo-rey-del-universo',
    'santa-maria-madre-de-dios': 'solemnidad-de-santa-maria-madre-de-dios',
}
SIN_PAR = []   # claves de la base que tampoco acá encuentran su lugar en el libro


def emparejar_resto():
    """Lo que comparar_base.py deja sin par y tiene par en el libro en otra sección: las
    solemnidades del Señor que la base guarda en el santoral y el libro en el Propio del tiempo, las
    ferias de Navidad nombradas por fecha y la salmodia de la Hora intermedia del Salterio."""
    import difflib
    import re
    _, por_nombre = cb.indice_tiempo()
    # 1. Hora intermedia del Salterio
    d = cb.js('salterio/salterio.json')
    idx = {(s['numero'], x['dia']): x for s in d['semanas'] for x in s['dias']}
    for sem_k, dias in (yml('salterio/intermedia.yaml') or {}).items():
        num = int(re.sub(r'\D', '', sem_k) or 0)
        for dk, b in (dias or {}).items():
            e = idx.get((num, dk.split('_')[0]))
            if e is not None and 'intermedia' in (e.get('horas') or {}):
                cb.comparar_hora('salterio', f'semana {num}/{dk}/intermedia', b, e, 'intermedia')
    # 2. y 3. claves del santoral y del tiempo que quedaron sin par
    sueltas = [(a, clave) for a, clave, donde, _ in cb.INF.faltantes
               if a in ('santoral', 'tiempo') and donde == 'no se pudo emparejar' and '/' in clave]
    for ambito, cl in sueltas:
        nom, arch = cl.rsplit('/', 1)
        if arch == 'libro.yaml':
            continue
        b = (yml(f'{ambito}/{arch}.yaml') or {}).get(nom)
        if not isinstance(b, dict):
            continue
        limpio = re.sub(r'\s*·.*$', '', nom).strip().strip('"')
        s = cb.slug(limpio)
        c = None
        m = re.match(r'(\d+) de enero', limpio)
        dia_ep = re.match(r'(lunes|martes|miercoles|jueves|viernes|sabado) despues de la epifania', cb.sin_tildes(limpio).lower())
        if s in ALIAS:
            c = por_nombre.get(ALIAS[s])
        elif m:
            c = next((x for k, x in por_nombre.items() if k.startswith(f'{m.group(1)}-de-enero')), None)
        elif dia_ep:
            c = next((x for k, x in por_nombre.items() if f'{dia_ep.group(1)}-despues-del-domingo-de-epifania' in k), None)
        else:
            mejor, pt = None, 0.0
            for k, x in por_nombre.items():
                r = difflib.SequenceMatcher(None, s, k, autojunk=False).ratio()
                if r > pt:
                    mejor, pt = x, r
            c = mejor if pt >= 0.8 else None
        h = cb.elegir_hora(arch, c, nom) if c else None
        if h is None:
            SIN_PAR.append((ambito, cl))
            continue
        cb.comparar_hora(ambito, cl, b, c, h)


# ─────────────── recorrer el libro ───────────────

def cargar(ruta):
    """El JSON de una sección, el mismo objeto que usa comparar_base (para que coincidan los id())."""
    return cb.js(ruta)


SECCIONES = [
    ('ordinario', 'ordinario/ordinario.json'),
    ('salterio', 'salterio/salterio.json'),
    ('completas', 'completas/completas.json'),
    ('tiempo', None),
    ('santoral', 'santoral/santoral.json'),
    ('comunes', 'comunes/comunes.json'),
    ('difuntos', 'difuntos/difuntos.json'),
    ('apendices', 'apendices/apendices.json'),
]


def nombre(n):
    for k in ('id', 'dia', 'titulo'):
        if n.get(k):
            return str(n[k])[:70]
    return '?'


def recorrer(nodo, camino, out):
    """Todas las piezas bajo `nodo`, con el camino de nodos que tienen `horas`."""
    if isinstance(nodo, list):
        for x in nodo:
            recorrer(x, camino, out)
        return
    if not isinstance(nodo, dict):
        return
    aca = camino
    if 'horas' in nodo or 'celebraciones' in nodo or 'dias' in nodo:
        aca = camino + [nombre(nodo)]
    for hora, partes in (nodo.get('horas') or {}).items():
        for p in partes or []:
            for pz in p.get('piezas') or []:
                out.append((aca, id(nodo), hora, p.get('parte'), pz))
    for k, v in nodo.items():
        if k != 'horas' and isinstance(v, (list, dict)):
            recorrer(v, aca, out)


def condiciones(pz):
    return [v.get('cuando') for v in pz.get('variantes') or [] if v.get('cuando')]


def clasificar(seccion, pz, tocada, hora_con_par, nodo_con_par):
    if seccion == 'ordinario':
        return 'fijo', 'Ordinario: queda en la app; se coteja aparte'
    if seccion in ('difuntos', 'apendices'):
        return 'falta', 'sección que la base no tiene'
    if tocada:
        archivos = {a for a in tocada['archivos'] if a}
        ver = tocada['veredictos']
        if archivos and all(a.startswith(DEL_LIBRO) for a in archivos):
            return 'reemplazar', 'la base la tiene cargada a mano del libro'
        if ESTRUCTURA & set(ver):
            return 'estructura', 'sync la tiene, cortada o en otro orden'
        extra = len(condiciones(pz))
        if extra and len(pz.get('variantes') or []) > 1:
            return 'variantes', 'sync la tiene; el libro suma variantes con condición'
        if ver.get('distinto') or ver.get('parecido'):
            return 'sync', 'sync la tiene, con otra traducción: queda la de sync'
        return 'sync', 'sync la tiene igual o casi igual'
    if pz.get('tipo') == 'rubrica':
        return 'rubrica', 'rúbrica del libro'
    if hora_con_par:
        return 'sin-cotejar', 'parte de una hora que la base tiene, que la comparación no mira'
    if nodo_con_par:
        return 'falta', 'hora que la base no tiene'
    return 'falta', 'celebración o día que la base no tiene'


GRUPOS = [
    ('sync', 'Queda la de sync', 'El libro no cambia nada: se descarta la pieza del libro.'),
    ('variantes', 'Sync + variantes del libro', 'Se mantiene el texto de sync y se suman las variantes por tiempo o día que trae el libro.'),
    ('estructura', 'Sync con error de estructura', 'Se mantiene el texto de sync y se corrige el corte o el orden mirando el libro.'),
    ('reemplazar', 'Reemplazar lo cargado a mano', 'Vino del libro sin la extracción limpia: se reemplaza por la extracción.'),
    ('falta', 'Falta en la base', 'Se agrega desde el libro (en su traducción).'),
    ('sin-cotejar', 'Sin cotejar', 'Está en una hora que la base tiene, pero la comparación no mira esa parte: hay que ver si falta.'),
    ('rubrica', 'Rúbricas', 'Indicaciones del libro: no son texto para rezar; sirven para las reglas.'),
    ('fijo', 'Ordinario', 'Lo que la app tiene fijo: se coteja aparte, a mano.'),
]


def main():
    correr()
    filas = []
    tiempo = sorted((AQUI / 'tiempo').glob('*/tiempo-*.json'))
    fuentes = [(s, r) for s, r in SECCIONES if r] + [('tiempo', str(p.relative_to(AQUI))) for p in tiempo]
    todas = []
    for seccion, ruta in fuentes:
        d = cargar(ruta)
        if d is None:
            continue
        out = []
        recorrer(d, [], out)
        todas += [(seccion, ruta, *x) for x in out]
    # qué (nodo, hora) y qué nodo tienen al menos una pieza emparejada con la base
    horas_par, nodos_par = set(), set()
    for seccion, ruta, camino, nid, hora, parte, pz in todas:
        if id(pz) in TOCADAS:
            horas_par.add((nid, hora))
            nodos_par.add(nid)
    for seccion, ruta, camino, nid, hora, parte, pz in todas:
        t = TOCADAS.get(id(pz))
        g, det = clasificar(seccion, pz, t, (nid, hora) in horas_par, nid in nodos_par)
        filas.append({
            'seccion': seccion, 'unidad': ' › '.join(camino[1:] or camino), 'hora': hora, 'parte': parte or '',
            'tipo': pz.get('tipo'), 'variantes': len(pz.get('variantes') or []),
            'grupo': g, 'detalle': det,
            'archivo_base': ', '.join(sorted(a for a in (t or {}).get('archivos', ()) if a)),
            'veredicto': ', '.join(f'{k} {v}' for k, v in sorted((t or {}).get('veredictos', {}).items())),
        })
    # bibliotecas: himnos y salmos que solo trae el libro
    for a, clave, donde, det in cb.INF.faltantes:
        if a in ('himnos', 'salmos') and donde == 'solo en el libro':
            filas.append({'seccion': f'biblioteca de {a}', 'unidad': clave, 'hora': '', 'parte': '',
                          'tipo': a[:-1], 'variantes': 1, 'grupo': 'falta', 'detalle': f'{a[:-1]} que la base no tiene'
                          if a == 'himnos' else 'salmo o cántico sin par por clave (puede ser el mismo con otro nombre)',
                          'archivo_base': '', 'veredicto': ''})
    escribir(filas)


def escribir(filas):
    INFORMES.mkdir(exist_ok=True)
    campos = list(filas[0])
    with open(INFORMES / 'clasificacion.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, campos)
        w.writeheader()
        w.writerows(filas)
    orden = [g for g, _, _ in GRUPOS]
    secs = list(dict.fromkeys(f['seccion'] for f in filas))
    c = Counter((f['seccion'], f['grupo']) for f in filas)
    tot = Counter(f['grupo'] for f in filas)
    L = ['# Clasificación del libro contra la base', '',
         'Una fila por pieza del libro en `clasificacion.csv`. **Regla:** el texto de `sync` manda; el libro '
         'llena lo que falta, suma variantes y reemplaza lo que se había cargado a mano del libro '
         '(`comunes/`, `santoral/libro.yaml`). La arma `extraccion/clasificar.py` sobre los emparejamientos '
         'de `comparar_base.py`. No toca ni `base/` ni la app.', '',
         '## Qué quiere decir cada grupo', '', '| Grupo | Qué se hace |', '|---|---|']
    for g, n, d in GRUPOS:
        L.append(f'| **{n}** ({tot[g]}) | {d} |')
    L += ['', '## Por sección', '',
          '| Sección | ' + ' | '.join(n for _, n, _ in GRUPOS) + ' | Total |',
          '|---|' + '---:|' * (len(GRUPOS) + 1)]
    for s in secs:
        L.append(f'| {s} | ' + ' | '.join(str(c[(s, g)] or '') for g in orden) +
                 f' | {sum(c[(s, g)] for g in orden)} |')
    L.append('| **Total** | ' + ' | '.join(f'**{tot[g]}**' for g in orden) + f' | **{len(filas)}** |')
    # detalle de lo que falta
    falta = [f for f in filas if f['grupo'] == 'falta']
    L += ['', '## Lo que falta, por qué', '', '| Sección | Motivo | Piezas |', '|---|---|---:|']
    for (s, d), n in sorted(Counter((f['seccion'], f['detalle']) for f in falta).items()):
        L.append(f'| {s} | {d} | {n} |')
    uni = Counter((f['seccion'], f['unidad'].split(' › ')[0]) for f in falta
                  if f['detalle'] == 'celebración o día que la base no tiene')
    L += ['', f'Celebraciones o días enteros que faltan: **{len(uni)}**.', '']
    for sec in dict.fromkeys(s for s, _ in uni):
        nombres = sorted(u for s, u in uni if s == sec)
        L.append(f'- **{sec}** ({len(nombres)}): ' + ', '.join(f'`{n}`' for n in nombres))
    L.append('')
    horas = Counter((f['seccion'], f['hora']) for f in falta if f['detalle'] == 'hora que la base no tiene')
    if horas:
        L += ['Horas que faltan dentro de lo que la base sí tiene:', '', '| Sección | Hora | Piezas |', '|---|---|---:|']
        for (s, h), n in sorted(horas.items()):
            L.append(f'| {s} | {h} | {n} |')
    sc = [f for f in filas if f['grupo'] == 'sin-cotejar']
    L += ['', '## Sin cotejar, por tipo', '',
          'Están en horas que la base tiene, pero `comparar_base.py` no compara ese campo o esa opción. '
          'Antes de agregarlas hay que ver si la base ya las tiene con otra forma.', '',
          '| Sección | Tipo | Piezas |', '|---|---|---:|']
    for (s, t), n in sorted(Counter((f['seccion'], f['tipo']) for f in sc).items(), key=lambda x: -x[1])[:30]:
        L.append(f'| {s} | {t} | {n} |')
    es = [f for f in filas if f['grupo'] == 'estructura']
    L += ['', '## Sync con error de estructura', '', '| Sección | Tipo | Piezas |', '|---|---|---:|']
    for (s, t), n in sorted(Counter((f['seccion'], f['tipo']) for f in es).items()):
        L.append(f'| {s} | {t} | {n} |')
    L += ['', '## Claves de la base que siguen sin par en el libro', '',
          'No quiere decir que falten en el libro: son fiestas propias, móviles o nombradas de otro modo. '
          'Las piezas del libro que les corresponderían pueden figurar arriba como «falta».', '']
    for a, n in sorted(Counter(a for a, _ in SIN_PAR).items()):
        L.append(f'- {a}: {n} — ' + ', '.join(sorted({c.rsplit("/", 1)[0] for x, c in SIN_PAR if x == a}))[:900])
    L += ['', '## Límites', '',
          '- El emparejamiento es el de `comparar_base.py` (por semana y día, o por parecido del nombre), más '
          'los arreglos de este script. Algunas claves pueden quedar mal emparejadas: en la lista de días '
          'que faltan, `jueves-santo-de-la-cena-del-senor`, `jueves-xv-semana-del-tiempo-ordinario` y '
          '`10-de-enero-o-jueves-…` hay que mirarlos a mano antes de agregar nada.',
          '- La base no tiene las ferias del 17 al 24 de diciembre: `sync` las juntó en una sola '
          '«Feria privilegiada de Adviento». Faltan, entonces, las antífonas «O» y los textos de cada día.',
          '- Una pieza «sin cotejar» puede estar ya en la base con otra forma: es lo primero que hay que revisar.',
          '- Las rúbricas no se cuentan como texto: sirven para escribir las reglas de la app.']
    (INFORMES / 'clasificacion.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L[:40]))


if __name__ == '__main__':
    main()
