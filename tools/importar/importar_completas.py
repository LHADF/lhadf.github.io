"""Carga única de Completas desde sync a la base propia (base/).

Uso:
  SEPTIES_FUENTES=/ruta/a/fuentes ORDO=/ruta/a/ordo-telegram python3 tools/importar/importar_completas.py

Recorre todas las Completas de sync (2015 en adelante), etiqueta cada fecha con el motor del Ordo
(tiempo litúrgico) y por los salmos (juego semanal), y para cada texto se queda con la versión que
más se repite. Las demás versiones van a base/informes/completas.md para revisarlas a mano.
Después de esta carga, sync ya no hace falta: las correcciones se hacen en base/.
"""
import collections, json, os, re, sys, tomllib
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
sys.path.insert(0, AQUI)
import completas_sync as C
from yaml_base import escribir

FUENTES = os.environ.get('SEPTIES_FUENTES', os.path.join(RAIZ, '..', 'fuentes'))
SYNC = os.path.join(FUENTES, 'sync')
ORDO = os.environ.get('ORDO', os.path.join(RAIZ, '..', 'ordo-telegram'))
sys.path.insert(0, ORDO)
from ordo.calendario import Ordo

BASE = os.path.join(RAIZ, 'base')

# Juego semanal de Completas según el primer salmo
JUEGOS = {'4': 'sabado', '90': 'domingo', '85': 'lunes', '142': 'martes', '30': 'miercoles', '15': 'jueves', '87': 'viernes'}
ORDEN = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
NOMBRE_JUEGO = {
    'sabado': 'Después de las I Vísperas de los domingos y solemnidades',
    'domingo': 'Después de las II Vísperas de los domingos y solemnidades',
    'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles', 'jueves': 'Jueves', 'viernes': 'Viernes',
}
GLORIA = 'Gloria al Padre, y al Hijo, y al Espíritu Santo.\nComo era en el principio, ahora y siempre, por los siglos de los siglos. Amén.'


def cargar():
    O = Ordo(ORDO, tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb')))
    out = []
    for fecha, var, f in C.archivos(SYNC):
        d = C.estructura(f)
        D = O.dia(date.fromisoformat(fecha))
        d.update(fecha=fecha, var=var, tiempo=D.tiempo, dia=D.feria.nombre,
                 juego=JUEGOS[re.match(r'Salmo (\d+)', d['salmodia'][0]['salmos'][0]['titulo']).group(1)])
        otros = d.get('_otros', [])
        d['ant_en_lugar_del_resp'] = otros[0][1][0] if otros and otros[0][1] else None
        out.append(d)
    return out


def clase(d):
    """ordinario | pascua | triduo_octava"""
    if d['ant_en_lugar_del_resp']: return 'triduo_octava'
    if d['tiempo'] == 'Pascua': return 'pascua'
    if d['tiempo'] == 'Triduo': return 'triduo_octava'
    return 'ordinario'


class Votos:
    """Cuenta versiones de cada texto y recuerda en qué fechas aparece cada una."""
    def __init__(self): self.v = collections.defaultdict(lambda: collections.defaultdict(list))
    def __call__(self, clave, valor, fecha):
        if valor is None: return
        k = json.dumps(valor, ensure_ascii=False, sort_keys=True)
        self.v[clave][k].append(fecha)
    def ganador(self, clave):
        c = self.v.get(clave)
        if not c: return None
        k = max(c, key=lambda x: len(c[x]))
        return json.loads(k)
    def variantes(self):
        for clave, c in sorted(self.v.items()):
            if len(c) > 1:
                orden = sorted(c, key=lambda x: -len(c[x]))
                yield clave, [(json.loads(k), c[k]) for k in orden]


def id_salmo(titulo):
    m = re.match(r'(Salmo|Cántico)\s+(.+?)\s+[-–]\s+(.*)$', titulo, re.I)
    if not m: return titulo, '', ''
    num = re.sub(r'\s*,\s*', ', ', m.group(2).strip())
    ident = 'salmo-' + re.sub(r'[^0-9]+', '-', num).strip('-')
    return ident, f'{m.group(1).capitalize()} {num}', m.group(3).strip().rstrip('.')


def sin_gloria(estrofas):
    est = [e for e in estrofas if not e.startswith('Gloria al Padre')]
    return est, len(est) != len(estrofas)


def resp(d):
    r = d.get('responsorio')
    return [[a, b] for a, b in r] if r else None


def importar(todos):
    V = Votos()
    for d in todos:
        f, j, c = d['fecha'], d['juego'], clase(d)
        cp = 'pascua' if c == 'pascua' else ('ordinario' if c == 'ordinario' else None)
        # ordinario de la hora
        inv = [[a, b] for a, b in d.get('invocacion', [])]
        if inv: inv[-1][1] = re.sub(r'\s*Aleluya\.?$', '', inv[-1][1])  # el aleluya se agrega fuera de Cuaresma
        V('invocacion', inv, f)
        V('examen', d.get('examen'), f)
        V('bendicion', [[a, b] for a, b in d.get('bendicion', [])], f)
        if c == 'ordinario':
            V('responsorio/ordinario', resp(d), f)
            V('ant_cantico/ordinario', d.get('ant_cantico'), f)
        elif c == 'pascua':
            V('responsorio/pascua', resp(d), f)
            V('ant_cantico/pascua', d.get('ant_cantico'), f)
        else:
            V(f"triduo_octava/{d['dia']}", {'juego': j, 'oracion': d.get('oracion'), 'en_lugar_del_responsorio': d['ant_en_lugar_del_resp'],
                                            'antifona_cantico': d.get('ant_cantico')}, f)
        # himnos y antífonas marianas: repertorio por tiempo
        if d.get('himno'):
            pool = {'Pascua': 'pascua', 'Triduo': 'cuaresma', 'Cuaresma': 'cuaresma', 'Adviento': 'adviento_navidad', 'Navidad': 'adviento_navidad'}.get(d['tiempo'], 'ordinario')
            V(f"himno/{pool}/{d['himno']['titulo']}", d['himno']['texto'], f)
        if d.get('mariana'):
            V(f"mariana/{'pascua' if d['tiempo']=='Pascua' else 'año'}/{d['mariana'][0].split(chr(10))[0]}", d['mariana'], f)
        # salterio de Completas
        V(f'{j}/lectura', d.get('lectura'), f)
        orac = d.get('oracion')
        if orac and orac.startswith('Visita, Señor'): V('oracion_solemnidad', orac, f)
        elif orac and not (j == 'sabado' and orac.startswith('Humildemente')): V(f'{j}/oracion', orac, f)
        estructura = []
        for g in d['salmodia']:
            ids = []
            for s in g['salmos']:
                ident, nombre, sub = id_salmo(s['titulo'])
                est, tenia = sin_gloria(s['texto'])
                V(f'salmo/{ident}', {'titulo': nombre, 'subtitulo': sub, 'texto': est}, f)
                ids.append(ident)
            estructura.append({'ant': g['ant'], 'salmos': ids, **({'ant_fin_distinta': g['ant_fin']} if g.get('ant_fin') and g['ant_fin'] != g['ant'] else {})})
        if cp: V(f'{j}/salmodia/{cp}', estructura, f)
        V('cantico_simeon', d.get('cantico_texto'), f)
    return V


def escribir_base(V):
    G = V.ganador
    os.makedirs(BASE, exist_ok=True)
    def reg(entradas):
        return [{(a.rstrip('.').strip() or 'texto'): b} for a, b in entradas]
    inv = G('invocacion')
    v1 = inv[0][1].rstrip('.') + '.'
    r1, _, glo = inv[1][1].partition(' Gloria al Padre')
    gloria = ('Gloria al Padre' + glo).strip() + '\n' + inv[2][1]
    ordinario = {
        'nombre': 'Completas',
        'aleluya_tras_gloria': 'siempre, salvo en Cuaresma (en la invocación inicial)',
        'subtitulo': 'Oración antes del descanso nocturno',
        'invocacion': [{'V': v1}, {'R': r1.strip()}],
        'gloria': gloria,
        'examen': G('examen'),
        'responsorio': {'ordinario': reg(G('responsorio/ordinario')), 'pascua': reg(G('responsorio/pascua'))},
        'cantico_evangelico': {
            'titulo': 'Cántico de Simeón', 'ref': 'Lc 2, 29-32',
            'antifona': {'ordinario': G('ant_cantico/ordinario'), 'pascua': G('ant_cantico/pascua')},
        },
        'oracion_solemnidad': G('oracion_solemnidad'),
        'bendicion': reg(G('bendicion')),
    }
    escribir(os.path.join(BASE, 'ordinario', 'completas.yaml'), ordinario,
             'Ordinario de Completas: partes que no cambian con el día de la semana.\n'
             'oracion_solemnidad: se usa en las solemnidades, con los salmos del sábado (I Vísperas) o del domingo (II Vísperas).')

    salterio = {}
    for j in ORDEN:
        salterio[j] = {
            'nombre': NOMBRE_JUEGO[j],
            'salmodia': G(f'{j}/salmodia/ordinario'),
            'salmodia_pascua': G(f'{j}/salmodia/pascua'),
            'lectura': G(f'{j}/lectura'),
            'oracion': G(f'{j}/oracion'),
        }
    escribir(os.path.join(BASE, 'salterio', 'completas.yaml'), salterio,
             'Salterio de Completas: un juego por día. Los salmos se citan por su clave (base/salmos/).\n'
             'salmodia_pascua: antífona del Tiempo pascual.')

    # Triduo y Octava de Pascua: antífona en lugar del responsorio
    ORD_DIAS = ['Jueves Santo', 'Viernes Santo de la Pasión del Señor', 'Sábado Santo', 'Lunes de la Octava de Pascua', 'Martes de la Octava de Pascua',
                'Miércoles de la Octava de Pascua', 'Jueves de la Octava de Pascua', 'Viernes de la Octava de Pascua', 'Sábado de la Octava de Pascua',
                'II Domingo de Pascua (de la Divina Misericordia)']
    tri = {}
    for dia in ORD_DIAS:
        c = V.v.get(f'triduo_octava/{dia}')
        if c and sum(len(x) for x in c.values()) >= 3:
            x = G(f'triduo_octava/{dia}')
            tri[dia] = {k: x[k] for k in ('juego', 'en_lugar_del_responsorio', 'antifona_cantico', 'oracion')}
    escribir(os.path.join(BASE, 'tiempo', 'completas-triduo-octava.yaml'), tri,
             'Completas del Triduo pascual y de la Octava de Pascua, día por día.\n'
             'juego: salmos de qué día (sabado = después de I Vísperas; domingo = después de II Vísperas).\n'
             'en_lugar_del_responsorio: antífona que reemplaza al responsorio breve.\n'
             'El Domingo de Pascua y el II Domingo de Pascua usan el juego del domingo con la antífona «Éste es el día».')

    # Himnos y antífonas marianas
    for pref, ruta, cab in (('himno/', ('himnos', 'completas.yaml'), 'Himnos de Completas, por tiempo. Se puede elegir cualquiera del tiempo que corresponde.'),
                            ('mariana/', ('ordinario', 'antifonas-marianas.yaml'), 'Antífonas finales de la Santísima Virgen. En Pascua, solo «Reina del cielo».')):
        rep = collections.defaultdict(list)
        for clave in V.v:
            if clave.startswith(pref):
                _, tiempo, titulo = clave.split('/', 2)
                rep[tiempo].append((len(sum(V.v[clave].values(), [])), {'titulo': titulo, 'texto': G(clave)}))
        out = {t: [x for _, x in sorted(rep[t], key=lambda z: -z[0]) if True] for t in sorted(rep)}
        # descartar apariciones aisladas fuera de su tiempo (errores de la fuente)
        out = {t: [x for x in lst if sum(len(v) for v in V.v[f"{pref}{t}/{x['titulo']}"].values()) >= 5] for t, lst in out.items()}
        escribir(os.path.join(BASE, *ruta), out, cab)

    escribir(os.path.join(BASE, 'salmos', 'cantico-simeon.yaml'), {'titulo': 'Cántico de Simeón', 'subtitulo': 'Lc 2, 29-32', 'texto': G('cantico_simeon')},
             'Cántico de Simeón (Nunc dimittis), texto de la Liturgia de las Horas en español.')
    # Salmos (solo los que usa la base)
    usados = {x for j in salterio.values() for k in ('salmodia', 'salmodia_pascua') for g in j[k] for x in g['salmos']}
    for clave in V.v:
        if clave.startswith('salmo/') and clave.split('/')[1] in usados:
            x = G(clave); s = {k: x[k] for k in ('titulo', 'subtitulo', 'texto')}
            escribir(os.path.join(BASE, 'salmos', clave.split('/')[1] + '.yaml'), s, f"{s['titulo']}. Texto de la Liturgia de las Horas en español; estrofas separadas por renglón en blanco.")


def informe(V, todos):
    L = ['# Completas: variantes encontradas en sync', '',
         f'Se leyeron {len(todos)} Completas ({todos[0]["fecha"]} a {todos[-1]["fecha"]}). '
         'Para cada texto quedó en la base la versión más frecuente. Abajo, las demás versiones con cuántas veces aparecen y algunas fechas, '
         'para revisarlas: casi siempre son erratas de la fuente o días con salmos de otro día.', '']
    for clave, vs in V.variantes():
        if clave.startswith(('himno/', 'mariana/')): continue
        L.append(f'## {clave}')
        for i, (val, fechas) in enumerate(vs):
            marca = '**en la base**' if i == 0 else 'variante'
            muestra = json.dumps(val, ensure_ascii=False)
            if len(muestra) > 300: muestra = muestra[:300] + '…'
            L.append(f'- {marca} · {len(fechas)} veces · {", ".join(fechas[:4])}{"…" if len(fechas) > 4 else ""}')
            if i: L.append(f'  `{muestra}`')
        L.append('')
    os.makedirs(os.path.join(BASE, 'informes'), exist_ok=True)
    open(os.path.join(BASE, 'informes', 'completas.md'), 'w', encoding='utf-8').write('\n'.join(L))


if __name__ == '__main__':
    cache = '/tmp/completas_sync.json'
    if os.environ.get('CACHE') and os.path.exists(cache):
        todos = json.load(open(cache))
    else:
        todos = cargar(); json.dump(todos, open(cache, 'w'), ensure_ascii=False)
    V = importar(todos)
    escribir_base(V)
    informe(V, todos)
    print(len(todos), 'Completas leídas; base escrita en', BASE)
